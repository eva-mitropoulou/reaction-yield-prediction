from __future__ import annotations

import argparse
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from reaction_yield_ml.config import FIGURES_DIR, METRICS_DIR, PROCESSED_DIR, RANDOM_STATE, REPORTS_DIR
from reaction_yield_ml.features.build_features import build_features, load_clean_data
from reaction_yield_ml.models.evaluate_models import regression_metrics, yield_bin_errors
from reaction_yield_ml.reporting.run_log import update_run_state
from reaction_yield_ml.reporting.io import read_json, write_json, write_markdown
from reaction_yield_ml.validation.splits import make_splits
from reaction_yield_ml.validation.split_labels import (
    equivalent_grouped_split_note,
    model_display_name,
    split_display_name,
)


class MeanRegressor(BaseEstimator, RegressorMixin):
    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "MeanRegressor":
        self.mean_ = float(np.mean(y))
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.full(shape=(len(X),), fill_value=self.mean_, dtype=float)


@dataclass(frozen=True)
class ModelSpec:
    name: str
    estimator: Any
    uses_dense_onehot: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train and evaluate baseline and ML models.")
    parser.add_argument("--fixture", action="store_true", help="Use synthetic fixture for code-path testing only.")
    return parser.parse_args()


def _encoder(sparse_output: bool) -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=sparse_output)
    except TypeError:  # pragma: no cover
        return OneHotEncoder(handle_unknown="ignore", sparse=sparse_output)


def model_specs() -> tuple[list[ModelSpec], dict[str, str]]:
    specs = [
        ModelSpec("mean_baseline", MeanRegressor(), uses_dense_onehot=False),
        ModelSpec("onehot_ridge", Ridge(alpha=1.0), uses_dense_onehot=False),
        ModelSpec("onehot_elastic_net", ElasticNet(alpha=0.005, l1_ratio=0.15, max_iter=10000, random_state=RANDOM_STATE), uses_dense_onehot=True),
        ModelSpec(
            "random_forest",
            RandomForestRegressor(
                n_estimators=160,
                min_samples_leaf=2,
                max_features="sqrt",
                n_jobs=-1,
                random_state=RANDOM_STATE,
            ),
            uses_dense_onehot=True,
        ),
        ModelSpec("gradient_boosting", GradientBoostingRegressor(random_state=RANDOM_STATE), uses_dense_onehot=True),
    ]
    optional = {}
    optional["xgboost"] = "available" if importlib.util.find_spec("xgboost") else "skipped_not_installed"
    optional["lightgbm"] = "available" if importlib.util.find_spec("lightgbm") else "skipped_not_installed"
    optional["neural_baseline"] = "skipped_scope_controlled_reproducibility"
    return specs, optional


def _build_pipeline(spec: ModelSpec) -> Any:
    if spec.name == "mean_baseline":
        return spec.estimator
    return Pipeline(
        [
            ("onehot", _encoder(sparse_output=not spec.uses_dense_onehot)),
            ("model", spec.estimator),
        ]
    )


def _load_valid_splits() -> dict[str, dict[str, Any]]:
    split_metrics = read_json(METRICS_DIR / "validation_design_metrics.json", default=None)
    if not split_metrics:
        split_metrics = make_splits()
    return {
        name: payload
        for name, payload in split_metrics["splits"].items()
        if payload.get("is_valid")
    }


def _primary_split(valid_splits: dict[str, dict[str, Any]]) -> str:
    reliability_order = [
        "grouped_high_cardinality_component",
        "out_of_substrate",
        "out_of_ligand",
        "out_of_base",
        "out_of_additive",
        "random_split",
    ]
    for split in reliability_order:
        if split in valid_splits:
            return split
    return next(iter(valid_splits))


def train_and_evaluate(use_fixture: bool = False) -> dict[str, Any]:
    if not (PROCESSED_DIR / "features" / "feature_metadata.json").exists():
        build_features(use_fixture=use_fixture)
    if not (METRICS_DIR / "validation_design_metrics.json").exists():
        make_splits(use_fixture=use_fixture)
    frame, component_cols = load_clean_data(use_fixture=use_fixture)
    frame = frame.set_index("record_id", drop=False)
    valid_splits = _load_valid_splits()
    specs, optional_status = model_specs()
    prediction_dir = PROCESSED_DIR / "predictions"
    model_dir = PROCESSED_DIR / "models"
    prediction_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    all_metrics: list[dict[str, Any]] = []
    representative_predictions: dict[str, pd.DataFrame] = {}
    for split_name, split in valid_splits.items():
        train = frame.loc[split["train_record_ids"]]
        test = frame.loc[split["test_record_ids"]]
        X_train = train[component_cols].astype(str)
        y_train = train["yield_percent"].to_numpy(dtype=float)
        X_test = test[component_cols].astype(str)
        y_test = test["yield_percent"].to_numpy(dtype=float)
        for spec in specs:
            model = _build_pipeline(spec)
            model.fit(X_train, y_train)
            y_pred = np.clip(model.predict(X_test), 0, 100)
            metrics = regression_metrics(y_test, y_pred)
            row = {
                "split": split_name,
                "model": spec.name,
                **metrics,
                "train_size": int(len(train)),
                "test_size": int(len(test)),
            }
            all_metrics.append(row)
            pred_frame = pd.DataFrame(
                {
                    "record_id": test["record_id"].to_numpy(),
                    "y_true": y_test,
                    "y_pred": y_pred,
                    "split": split_name,
                    "model": spec.name,
                }
            )
            pred_frame.to_csv(prediction_dir / f"{split_name}__{spec.name}.csv", index=False)
            representative_predictions[f"{split_name}::{spec.name}"] = pred_frame
    metrics_frame = pd.DataFrame(all_metrics)
    primary = _primary_split(valid_splits)
    primary_display = split_display_name(primary, valid_splits[primary])
    primary_equivalence_note = equivalent_grouped_split_note(primary, valid_splits)
    eligible = metrics_frame[(metrics_frame["split"] == primary) & (metrics_frame["model"] != "mean_baseline")]
    best_row = eligible.sort_values(["mae", "rmse"]).iloc[0].to_dict()
    best_model_name = str(best_row["model"])
    best_spec = next(spec for spec in specs if spec.name == best_model_name)
    final_model = _build_pipeline(best_spec)
    final_model.fit(frame[component_cols].astype(str), frame["yield_percent"].to_numpy(dtype=float))
    joblib.dump({"model": final_model, "model_name": best_model_name, "component_columns": component_cols}, model_dir / "best_model.joblib")
    metrics_payload = {
        "source_mode": frame["source_mode"].iloc[0] if "source_mode" in frame.columns else "unknown",
        "models_evaluated": [spec.name for spec in specs],
        "optional_models": optional_status,
        "primary_selection_split": primary,
        "primary_selection_split_display": primary_display,
        "primary_split_equivalence_note": primary_equivalence_note,
        "best_model": best_model_name,
        "best_model_primary_split_metrics": {key: best_row[key] for key in ["mae", "rmse", "r2", "spearman", "top_10pct_enrichment"]},
        "metrics": all_metrics,
        "quality_gates": {
            "mean_baseline_included": "mean_baseline" in metrics_frame["model"].unique(),
            "grouped_or_out_of_component_split_included": any(name != "random_split" for name in valid_splits),
            "random_split_not_sole_evidence": len(valid_splits) > 1,
            "best_model_selected_by_reliability_split": primary != "random_split" or len(valid_splits) == 1,
            "all_metrics_saved_as_json": True,
        },
    }
    write_json(METRICS_DIR / "model_benchmark_metrics.json", metrics_payload)
    _write_figures(metrics_frame, representative_predictions, primary, best_model_name)
    _write_report(metrics_payload)
    return metrics_payload


def _write_figures(
    metrics_frame: pd.DataFrame,
    representative_predictions: dict[str, pd.DataFrame],
    primary_split: str,
    best_model_name: str,
) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plot_frame = metrics_frame.copy()
    plot_frame["Validation split"] = plot_frame["split"].map(split_display_name)
    plot_frame["Model"] = plot_frame["model"].map(model_display_name)
    split_order = [split_display_name(name) for name in metrics_frame["split"].drop_duplicates()]
    model_order = [model_display_name(name) for name in metrics_frame["model"].drop_duplicates()]
    plot_frame["Validation split"] = pd.Categorical(plot_frame["Validation split"], split_order, ordered=True)
    plot_frame["Model"] = pd.Categorical(plot_frame["Model"], model_order, ordered=True)
    pivot = plot_frame.pivot_table(index="Validation split", columns="Model", values="mae", aggfunc="mean", observed=False)
    ax = pivot.plot(kind="bar", figsize=(11, 5))
    ax.set_xlabel("Validation split")
    ax.set_ylabel("Mean absolute error")
    ax.set_title("Reaction yield model comparison")
    ax.legend(title="Model", loc="best", fontsize=8)
    ax.tick_params(axis="x", labelrotation=25)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "model_comparison_by_split.png", dpi=180)
    plt.close()

    pred = representative_predictions[f"{primary_split}::{best_model_name}"]
    plt.figure(figsize=(5.5, 5))
    plt.scatter(pred["y_true"], pred["y_pred"], s=12, alpha=0.55)
    plt.plot([0, 100], [0, 100], color="black", linewidth=1)
    plt.xlabel("Observed yield (%)")
    plt.ylabel("Predicted yield (%)")
    plt.title("Predicted vs observed yields")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "predicted_vs_observed.png", dpi=180)
    plt.close()

    bins = yield_bin_errors(pred["y_true"].to_numpy(), pred["y_pred"].to_numpy())
    bin_frame = pd.DataFrame(bins)
    plt.figure(figsize=(7, 4))
    plt.bar(bin_frame["yield_bin"], bin_frame["mae"])
    plt.ylabel("MAE")
    plt.xlabel("Observed yield bin")
    plt.xticks(rotation=30, ha="right")
    plt.title("Error by yield bin")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "error_by_yield_bin.png", dpi=180)
    plt.close()


def _write_report(metrics: dict[str, Any]) -> None:
    best = metrics["best_model_primary_split_metrics"]
    equivalence_note = metrics.get("primary_split_equivalence_note") or "No equivalent grouped split note was recorded."
    model_names = [model_display_name(name) for name in metrics["models_evaluated"]]
    optional_models = [
        f"- {name.replace('_', ' ').title()}: {status.replace('_', ' ')}"
        for name, status in metrics["optional_models"].items()
    ]
    quality_gates = [
        f"- {key.replace('_', ' ').capitalize()}: {value}"
        for key, value in metrics["quality_gates"].items()
    ]
    lines = [
        "# Model Benchmark Report",
        "",
        "## Summary",
        "",
        f"- Models evaluated: {', '.join(model_names)}",
        f"- Primary reliability split for model selection: {metrics.get('primary_selection_split_display', metrics['primary_selection_split'])}",
        f"- Selected model: {model_display_name(metrics['best_model'])}",
        f"- Selected model MAE on primary split: {best['mae']}",
        f"- Selected model RMSE on primary split: {best['rmse']}",
        f"- Selected model R2 on primary split: {best['r2']}",
        f"- Selected model Spearman correlation on primary split: {best['spearman']}",
        f"- Selected model top-10% enrichment on primary split: {best['top_10pct_enrichment']}",
        "",
        "## Optional Models",
        "",
        *optional_models,
        "",
        "## Quality Gates",
        "",
        *quality_gates,
        "",
        "## Interpretation Boundary",
        "",
        "Random split performance is not presented as sole evidence. Grouped and out-of-component splits are included where possible. Model selection prioritizes the reliability-oriented grouped split.",
        equivalence_note,
    ]
    report = "\n".join(lines) + "\n"
    write_markdown(REPORTS_DIR / "model_benchmark_report.md", report)


def main(use_fixture: bool = False) -> dict[str, Any]:
    metrics = train_and_evaluate(use_fixture=use_fixture)
    gates = metrics["quality_gates"]
    status = "PASS" if all(gates.values()) else "DEGRADED"
    update_run_state(
        "phase_6_model_benchmark",
        status,
        files=[
            "reports/model_benchmark_report.md",
            "reports/metrics/model_benchmark_metrics.json",
            "reports/figures/model_comparison_by_split.png",
            "reports/figures/predicted_vs_observed.png",
            "reports/figures/error_by_yield_bin.png",
            "data/processed/models/best_model.joblib",
        ],
        checks=list(gates.keys()),
        failures=[] if status == "PASS" else [key for key, value in gates.items() if not value],
        repairs=[],
        notes=["Categorical component labels are the primary predictors in this public workbook."],
        extra={
            "best_model": metrics["best_model"],
            "primary_selection_split": metrics["primary_selection_split"],
            "best_metrics": metrics["best_model_primary_split_metrics"],
        },
    )
    print(f"model_benchmark_status: {status}")
    print(f"best_model: {metrics['best_model']}")
    print(f"primary_selection_split: {metrics['primary_selection_split']}")
    print(f"best_model_metrics: {metrics['best_model_primary_split_metrics']}")
    return metrics


if __name__ == "__main__":
    args = parse_args()
    main(use_fixture=args.fixture)
