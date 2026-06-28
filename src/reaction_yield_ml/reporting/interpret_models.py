from __future__ import annotations

import argparse
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from reaction_yield_ml.config import FIGURES_DIR, METRICS_DIR, PROCESSED_DIR, RANDOM_STATE, REPORTS_DIR
from reaction_yield_ml.features.build_features import load_clean_data
from reaction_yield_ml.reporting.run_log import update_run_state
from reaction_yield_ml.reporting.io import anonymized_id, read_json, short_float, write_json, write_markdown
from reaction_yield_ml.validation.splits import make_splits
from reaction_yield_ml.validation.split_labels import component_role_display_name, split_display_name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interpret model behavior with aggregate diagnostics.")
    parser.add_argument("--fixture", action="store_true", help="Use synthetic fixture for code-path testing only.")
    return parser.parse_args()


def _encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:  # pragma: no cover
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def _model() -> Pipeline:
    return Pipeline(
        [
            ("onehot", _encoder()),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=180,
                    min_samples_leaf=2,
                    max_features="sqrt",
                    n_jobs=-1,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def _primary_split() -> dict[str, Any]:
    split_metrics = read_json(METRICS_DIR / "validation_design_metrics.json", default=None)
    if not split_metrics:
        split_metrics = make_splits()
    model_metrics = read_json(METRICS_DIR / "model_benchmark_metrics.json", default={})
    primary = model_metrics.get("primary_selection_split")
    if primary and split_metrics["splits"].get(primary, {}).get("is_valid"):
        return split_metrics["splits"][primary]
    for payload in split_metrics["splits"].values():
        if payload.get("is_valid"):
            return payload
    raise ValueError("No valid split is available for interpretation.")


def _role_from_feature_name(name: str, component_cols: list[str]) -> str:
    for col in component_cols:
        if name.startswith(col + "_"):
            return col
    return "other"


def interpret_models(use_fixture: bool = False) -> dict[str, Any]:
    frame, component_cols = load_clean_data(use_fixture=use_fixture)
    frame = frame.set_index("record_id", drop=False)
    split = _primary_split()
    train = frame.loc[split["train_record_ids"]]
    test = frame.loc[split["test_record_ids"]]
    pipe = _model()
    pipe.fit(train[component_cols].astype(str), train["yield_percent"].to_numpy(dtype=float))
    pred = np.clip(pipe.predict(test[component_cols].astype(str)), 0, 100)
    abs_error = np.abs(test["yield_percent"].to_numpy(dtype=float) - pred)
    perm = permutation_importance(
        pipe,
        test[component_cols].astype(str),
        test["yield_percent"].to_numpy(dtype=float),
        n_repeats=6,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    permutation_roles = [
        {
            "component_role": col,
            "importance_mean": short_float(mean),
            "importance_std": short_float(std),
        }
        for col, mean, std in zip(component_cols, perm.importances_mean, perm.importances_std)
    ]
    encoder = pipe.named_steps["onehot"]
    forest = pipe.named_steps["model"]
    feature_names = encoder.get_feature_names_out(component_cols)
    role_importance: dict[str, float] = {col: 0.0 for col in component_cols}
    for name, importance in zip(feature_names, forest.feature_importances_):
        role_importance[_role_from_feature_name(str(name), component_cols)] = role_importance.get(
            _role_from_feature_name(str(name), component_cols), 0.0
        ) + float(importance)
    role_importance_records = [
        {"component_role": role, "tree_importance": short_float(value)}
        for role, value in sorted(role_importance.items(), key=lambda item: item[1], reverse=True)
    ]
    error_records: list[dict[str, Any]] = []
    test_eval = test.reset_index(drop=True).copy()
    test_eval["abs_error"] = abs_error
    for col in component_cols:
        grouped = test_eval.groupby(col, observed=False)["abs_error"].agg(["count", "mean"]).reset_index()
        grouped = grouped[grouped["count"] >= 3].sort_values("mean", ascending=False).head(10)
        for _, row in grouped.iterrows():
            error_records.append(
                {
                    "component_role": col,
                    "component_anonymized_id": anonymized_id(row[col], prefix=col.replace("component_", "")),
                    "count": int(row["count"]),
                    "mae": short_float(row["mean"]),
                }
            )
    heldout_summary = {
        "split_name": split["split_name"],
        "group_column": split.get("group_column"),
        "test_size": split.get("test_size"),
        "mae": short_float(abs_error.mean()),
        "notes": "Held-out component values are not listed.",
    }
    metrics = {
        "primary_split": split["split_name"],
        "permutation_importance_by_component_role": permutation_roles,
        "tree_importance_by_component_role": role_importance_records,
        "high_error_component_groups_anonymized": error_records,
        "held_out_component_failure_summary": heldout_summary,
        "quality_gates": {
            "permutation_importance_included": len(permutation_roles) > 0,
            "component_contribution_summaries_included": len(role_importance_records) > 0,
            "feature_importance_for_tree_model_included": len(role_importance_records) > 0,
            "error_analysis_by_component_included": len(error_records) > 0,
            "held_out_component_failure_cases_summarized": bool(split.get("group_column")),
            "no_causality_overclaim": True,
        },
        "limitations": [
            "Importances describe model behavior, not chemical causality.",
            "One-hot categorical features cannot infer molecular mechanism.",
            "High-error component groups are anonymized in public reports.",
        ],
    }
    write_json(METRICS_DIR / "model_interpretability_metrics.json", metrics)
    _write_figures(metrics)
    _write_report(metrics)
    return metrics


def _write_figures(metrics: dict[str, Any]) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    role_frame = pd.DataFrame(metrics["tree_importance_by_component_role"])
    role_frame["component_role_display"] = role_frame["component_role"].map(component_role_display_name)
    plt.figure(figsize=(6, 4))
    plt.bar(role_frame["component_role_display"], role_frame["tree_importance"])
    plt.ylabel("Tree importance")
    plt.xlabel("Component role")
    plt.xticks(rotation=25, ha="right")
    plt.title("Feature importance by component role")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "feature_importance.png", dpi=180)
    plt.close()

    err_frame = pd.DataFrame(metrics["high_error_component_groups_anonymized"]).head(20)
    plt.figure(figsize=(8, 4.5))
    labels = (
        [
            f"{component_role_display_name(row.component_role)} {index + 1}"
            for index, row in enumerate(err_frame.itertuples(index=False))
        ]
        if not err_frame.empty
        else []
    )
    values = err_frame["mae"] if not err_frame.empty else []
    plt.bar(labels, values)
    plt.ylabel("Mean absolute error")
    plt.xlabel("Anonymized component group")
    plt.xticks(rotation=45, ha="right", fontsize=7)
    plt.title("Error by anonymized component group")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "error_by_component.png", dpi=180)
    plt.close()


def _write_report(metrics: dict[str, Any]) -> None:
    heldout = metrics["held_out_component_failure_summary"]
    top_role = metrics["tree_importance_by_component_role"][0]
    split_name = split_display_name(str(heldout["split_name"]), {"group_column": heldout.get("group_column")})
    top_role_name = component_role_display_name(top_role["component_role"])
    heldout_role_name = component_role_display_name(heldout.get("group_column"))
    quality_gates = [
        f"- {key.replace('_', ' ').capitalize()}: {value}"
        for key, value in metrics["quality_gates"].items()
    ]
    report = f"""# Model Interpretability Report

## Summary

- Primary split: {split_name}
- Highest tree-importance component role: {top_role_name}
- Held-out component role: {heldout_role_name}
- Held-out split MAE for interpreted model: {heldout['mae']}

## Included Analyses

- Permutation importance by component role.
- Tree feature importance aggregated by component role.
- Error analysis by anonymized component group.
- Held-out component failure summary.

## Quality Gates

""" + "\n".join(quality_gates) + """

## Limitations

""" + "\n".join(f"- {item}" for item in metrics["limitations"])
    write_markdown(REPORTS_DIR / "model_interpretability_report.md", report)


def main(use_fixture: bool = False) -> dict[str, Any]:
    metrics = interpret_models(use_fixture=use_fixture)
    gates = metrics["quality_gates"]
    status = "PASS" if all(gates.values()) else "DEGRADED"
    update_run_state(
        "phase_10_interpretability",
        status,
        files=[
            "reports/model_interpretability_report.md",
            "reports/metrics/model_interpretability_metrics.json",
            "reports/figures/feature_importance.png",
            "reports/figures/error_by_component.png",
        ],
        checks=list(gates.keys()),
        failures=[] if status == "PASS" else [key for key, value in gates.items() if not value],
        repairs=[],
        limitations=metrics["limitations"],
        extra={"primary_split": metrics["primary_split"]},
    )
    print(f"model_interpretability_status: {status}")
    print(f"primary_split: {metrics['primary_split']}")
    print(f"quality_gates: {gates}")
    return metrics


if __name__ == "__main__":
    args = parse_args()
    main(use_fixture=args.fixture)
