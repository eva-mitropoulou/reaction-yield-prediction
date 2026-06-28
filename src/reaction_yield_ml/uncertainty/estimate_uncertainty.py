from __future__ import annotations

import argparse
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from reaction_yield_ml.config import FIGURES_DIR, METRICS_DIR, PROCESSED_DIR, RANDOM_STATE, REPORTS_DIR
from reaction_yield_ml.features.build_features import load_clean_data
from reaction_yield_ml.models.train_models import train_and_evaluate
from reaction_yield_ml.reporting.run_log import update_run_state
from reaction_yield_ml.reporting.io import read_json, short_float, write_json, write_markdown
from reaction_yield_ml.uncertainty.calibration import empirical_coverage, uncertainty_error_summary
from reaction_yield_ml.validation.splits import make_splits
from reaction_yield_ml.validation.split_labels import split_display_name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Estimate uncertainty and calibration for reaction-yield models.")
    parser.add_argument("--fixture", action="store_true", help="Use synthetic fixture for code-path testing only.")
    return parser.parse_args()


def _encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:  # pragma: no cover
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def _rf(random_state: int = RANDOM_STATE) -> RandomForestRegressor:
    return RandomForestRegressor(
        n_estimators=180,
        min_samples_leaf=2,
        max_features="sqrt",
        n_jobs=-1,
        random_state=random_state,
    )


def _pipeline(random_state: int = RANDOM_STATE) -> Pipeline:
    return Pipeline([("onehot", _encoder()), ("model", _rf(random_state=random_state))])


def _tree_uncertainty(model: Pipeline, X: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    encoded = model.named_steps["onehot"].transform(X)
    forest = model.named_steps["model"]
    tree_preds = np.vstack([tree.predict(encoded) for tree in forest.estimators_])
    return np.clip(tree_preds.mean(axis=0), 0, 100), tree_preds.std(axis=0)


def _domain_flags(train: pd.DataFrame, test: pd.DataFrame, component_cols: list[str]) -> np.ndarray:
    allowed = {col: set(train[col].astype(str)) for col in component_cols}
    flags = []
    for _, row in test[component_cols].astype(str).iterrows():
        flags.append(any(row[col] not in allowed[col] for col in component_cols))
    return np.asarray(flags, dtype=bool)


def estimate_uncertainty(use_fixture: bool = False) -> dict[str, Any]:
    if not (METRICS_DIR / "model_benchmark_metrics.json").exists():
        train_and_evaluate(use_fixture=use_fixture)
    split_metrics = read_json(METRICS_DIR / "validation_design_metrics.json", default=None)
    if not split_metrics:
        split_metrics = make_splits(use_fixture=use_fixture)
    valid_splits = {name: payload for name, payload in split_metrics["splits"].items() if payload.get("is_valid")}
    model_metrics = read_json(METRICS_DIR / "model_benchmark_metrics.json", default={})
    primary = model_metrics.get("primary_selection_split") or next(iter(valid_splits))
    frame, component_cols = load_clean_data(use_fixture=use_fixture)
    frame = frame.set_index("record_id", drop=False)
    out_dir = PROCESSED_DIR / "uncertainty"
    out_dir.mkdir(parents=True, exist_ok=True)
    split_summaries: dict[str, Any] = {}
    primary_frame: pd.DataFrame | None = None
    for split_name, split in valid_splits.items():
        train = frame.loc[split["train_record_ids"]]
        test = frame.loc[split["test_record_ids"]]
        X_train = train[component_cols].astype(str)
        y_train = train["yield_percent"].to_numpy(dtype=float)
        X_test = test[component_cols].astype(str)
        y_test = test["yield_percent"].to_numpy(dtype=float)
        model = _pipeline()
        model.fit(X_train, y_train)
        y_pred, uncertainty = _tree_uncertainty(model, X_test)
        abs_error = np.abs(y_test - y_pred)
        domain_flags = _domain_flags(train, test, component_cols)
        low_conf_threshold = float(np.quantile(uncertainty, 0.80)) if len(uncertainty) else 0.0
        low_confidence = uncertainty >= low_conf_threshold

        if len(train) >= 80:
            fit_part, calib_part = train_test_split(train, test_size=0.2, random_state=RANDOM_STATE)
            conformal_model = _pipeline(random_state=RANDOM_STATE + 1)
            conformal_model.fit(fit_part[component_cols].astype(str), fit_part["yield_percent"].to_numpy(dtype=float))
            calib_pred = np.clip(conformal_model.predict(calib_part[component_cols].astype(str)), 0, 100)
            calib_resid = np.abs(calib_part["yield_percent"].to_numpy(dtype=float) - calib_pred)
            q90 = float(np.quantile(calib_resid, 0.90))
        else:
            q90 = float(np.quantile(abs_error, 0.90)) if len(abs_error) else 0.0
        lower = np.clip(y_pred - q90, 0, 100)
        upper = np.clip(y_pred + q90, 0, 100)
        result = pd.DataFrame(
            {
                "record_id": test["record_id"].to_numpy(),
                "y_true": y_test,
                "y_pred": y_pred,
                "abs_error": abs_error,
                "ensemble_std": uncertainty,
                "interval_lower_90": lower,
                "interval_upper_90": upper,
                "low_confidence_flag": low_confidence,
                "out_of_training_component_flag": domain_flags,
                "split": split_name,
            }
        )
        result.to_csv(out_dir / f"{split_name}_uncertainty.csv", index=False)
        summary = uncertainty_error_summary(y_test, y_pred, uncertainty)
        summary.update(
            {
                "test_size": int(len(test)),
                "mean_abs_error": short_float(abs_error.mean()),
                "mean_uncertainty": short_float(uncertainty.mean()),
                "interval_half_width_90": short_float(q90),
                "empirical_coverage_90": empirical_coverage(y_test, lower, upper),
                "low_confidence_fraction": short_float(np.mean(low_confidence)),
                "out_of_training_component_fraction": short_float(np.mean(domain_flags)),
                "out_of_training_component_mae": short_float(abs_error[domain_flags].mean()) if domain_flags.any() else None,
                "in_domain_mae": short_float(abs_error[~domain_flags].mean()) if (~domain_flags).any() else None,
            }
        )
        split_summaries[split_name] = summary
        if split_name == primary:
            primary_frame = result
    if primary_frame is None:
        primary_frame = result
    metrics = {
        "primary_split": primary,
        "method": "random_forest_tree_ensemble_std_plus_split_conformal_interval",
        "split_summaries": split_summaries,
        "quality_gates": {
            "uncertainty_evaluated_against_actual_errors": all(
                "mean_abs_error" in summary for summary in split_summaries.values()
            ),
            "empirical_coverage_reported": all(
                summary.get("empirical_coverage_90") is not None for summary in split_summaries.values()
            ),
            "low_confidence_predictions_flagged": all(
                summary.get("low_confidence_fraction") is not None for summary in split_summaries.values()
            ),
            "domain_distance_proxy_reported": all(
                "out_of_training_component_fraction" in summary for summary in split_summaries.values()
            ),
        },
        "limitations": [
            "Tree-ensemble variance is a heuristic uncertainty proxy.",
            "Conformal intervals are retrospective and depend on calibration residuals from the available public records.",
            "Uncertainty is evaluated against actual errors and reported with empirical coverage.",
        ],
    }
    write_json(METRICS_DIR / "uncertainty_calibration_metrics.json", metrics)
    _write_figures(primary_frame)
    _write_report(metrics)
    return metrics


def _write_figures(primary_frame: pd.DataFrame) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(6, 4))
    plt.scatter(primary_frame["ensemble_std"], primary_frame["abs_error"], s=12, alpha=0.55)
    plt.xlabel("Ensemble uncertainty proxy")
    plt.ylabel("Absolute error")
    plt.title("Uncertainty vs error")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "uncertainty_vs_error.png", dpi=180)
    plt.close()

    frame = primary_frame.copy()
    frame["uncertainty_bin"] = pd.qcut(frame["ensemble_std"].rank(method="first"), q=min(5, len(frame)), duplicates="drop")
    grouped = frame.groupby("uncertainty_bin", observed=False).agg(
        mean_uncertainty=("ensemble_std", "mean"),
        mean_abs_error=("abs_error", "mean"),
    )
    plt.figure(figsize=(6, 4))
    plt.plot(range(1, len(grouped) + 1), grouped["mean_abs_error"], marker="o", label="Mean absolute error")
    plt.plot(range(1, len(grouped) + 1), grouped["mean_uncertainty"], marker="o", label="Mean uncertainty")
    plt.xlabel("Uncertainty bin")
    plt.ylabel("Value")
    plt.title("Calibration bins")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "calibration_bins.png", dpi=180)
    plt.close()


def _write_report(metrics: dict[str, Any]) -> None:
    primary_summary = metrics["split_summaries"][metrics["primary_split"]]
    primary_split_name = split_display_name(metrics["primary_split"])
    method = metrics["method"].replace("_", " ")
    report = f"""# Uncertainty And Calibration Report

## Summary

- Method: {method}
- Primary split: {primary_split_name}
- Primary split uncertainty-error Spearman: {primary_summary['spearman_abs_error_vs_uncertainty']}
- Primary split empirical 90% interval coverage: {primary_summary['empirical_coverage_90']}
- Primary split low-confidence fraction: {primary_summary['low_confidence_fraction']}
- Primary split out-of-training-component fraction: {primary_summary['out_of_training_component_fraction']}

## Quality Gates

""" + "\n".join(f"- {key}: {value}" for key, value in metrics["quality_gates"].items()) + """

## Interpretation Context

""" + "\n".join(f"- {item}" for item in metrics["limitations"])
    write_markdown(REPORTS_DIR / "uncertainty_calibration_report.md", report)


def main(use_fixture: bool = False) -> dict[str, Any]:
    metrics = estimate_uncertainty(use_fixture=use_fixture)
    gates = metrics["quality_gates"]
    status = "PASS" if all(gates.values()) else "DEGRADED"
    update_run_state(
        "phase_7_uncertainty_calibration",
        status,
        files=[
            "reports/uncertainty_calibration_report.md",
            "reports/metrics/uncertainty_calibration_metrics.json",
            "reports/figures/uncertainty_vs_error.png",
            "reports/figures/calibration_bins.png",
            "data/processed/uncertainty/*_uncertainty.csv",
        ],
        checks=list(gates.keys()),
        failures=[] if status == "PASS" else [key for key, value in gates.items() if not value],
        repairs=[],
        notes=metrics["limitations"],
        extra={"primary_split": metrics["primary_split"]},
    )
    print(f"uncertainty_calibration_status: {status}")
    print(f"primary_split: {metrics['primary_split']}")
    print(f"quality_gates: {gates}")
    return metrics


if __name__ == "__main__":
    args = parse_args()
    main(use_fixture=args.fixture)
