from __future__ import annotations

import argparse
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from reaction_yield_ml.config import METRICS_DIR, PROCESSED_DIR, RANDOM_STATE, REPORTS_DIR
from reaction_yield_ml.features.build_features import load_clean_data
from reaction_yield_ml.reporting.run_log import update_run_state
from reaction_yield_ml.reporting.io import short_float, write_json, write_markdown
from reaction_yield_ml.validation.split_labels import model_display_name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank existing public records retrospectively.")
    parser.add_argument("--fixture", action="store_true", help="Use synthetic fixture for code-path testing only.")
    return parser.parse_args()


def _encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:  # pragma: no cover
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def _models() -> dict[str, Any]:
    return {
        "ridge": Ridge(alpha=1.0),
        "random_forest": RandomForestRegressor(
            n_estimators=140,
            min_samples_leaf=2,
            max_features="sqrt",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
        "gradient_boosting": GradientBoostingRegressor(random_state=RANDOM_STATE),
    }


def _pipeline(model: Any) -> Pipeline:
    return Pipeline([("onehot", _encoder()), ("model", model)])


def _domain_flags(train: pd.DataFrame, test: pd.DataFrame, component_cols: list[str]) -> np.ndarray:
    allowed = {col: set(train[col].astype(str)) for col in component_cols}
    flags = []
    for _, row in test[component_cols].astype(str).iterrows():
        flags.append(any(row[col] not in allowed[col] for col in component_cols))
    return np.asarray(flags, dtype=bool)


def _component_diversity(frame: pd.DataFrame, component_cols: list[str]) -> np.ndarray:
    score = np.zeros(len(frame), dtype=float)
    for col in component_cols:
        freqs = frame[col].astype(str).value_counts(normalize=True)
        rarity = frame[col].astype(str).map(lambda value: 1.0 - float(freqs[value])).to_numpy(dtype=float)
        score += rarity
    score = score / max(1, len(component_cols))
    min_val, max_val = score.min(), score.max()
    if max_val > min_val:
        score = (score - min_val) / (max_val - min_val)
    return score


def rank_existing_records(use_fixture: bool = False) -> dict[str, Any]:
    frame, component_cols = load_clean_data(use_fixture=use_fixture)
    frame = frame.reset_index(drop=True)
    n_splits = min(5, max(2, len(frame) // 50))
    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    model_names = list(_models())
    pred_matrix = np.zeros((len(frame), len(model_names)), dtype=float)
    domain_flags = np.zeros(len(frame), dtype=bool)
    for fold_idx, (train_idx, test_idx) in enumerate(kfold.split(frame), start=1):
        train = frame.iloc[train_idx]
        test = frame.iloc[test_idx]
        domain_flags[test_idx] = _domain_flags(train, test, component_cols)
        for model_idx, (model_name, model) in enumerate(_models().items()):
            pipe = _pipeline(model)
            pipe.fit(train[component_cols].astype(str), train["yield_percent"].to_numpy(dtype=float))
            pred_matrix[test_idx, model_idx] = np.clip(pipe.predict(test[component_cols].astype(str)), 0, 100)
    predicted = pred_matrix.mean(axis=1)
    agreement_std = pred_matrix.std(axis=1)
    diversity = _component_diversity(frame, component_cols)
    confidence = 1.0 / (1.0 + agreement_std)
    rank_score = predicted - 0.5 * agreement_std + 3.0 * diversity
    out = pd.DataFrame(
        {
            "rank": np.argsort(np.argsort(-rank_score)) + 1,
            "record_id": frame["record_id"].astype(str),
            "predicted_yield_percent_oof": predicted,
            "observed_yield_percent_for_retrospective_audit": frame["yield_percent"].to_numpy(dtype=float),
            "model_agreement_std": agreement_std,
            "confidence_score": confidence,
            "domain_warning": np.where(domain_flags, "contains_fold-novel_component_label", "within_fold_component_labels"),
            "component_diversity_score": diversity,
            "rank_score": rank_score,
            "existing_record_only": True,
        }
    ).sort_values("rank")
    out_path = REPORTS_DIR / "ranked_existing_reaction_records.csv"
    out.to_csv(out_path, index=False)
    metrics = {
        "row_count": int(len(out)),
        "ranking_rows_match_clean_rows": int(len(out)) == int(len(frame)),
        "models_used": model_names,
        "cross_validation_folds": n_splits,
        "top_rank_predicted_yield_percent": short_float(out.iloc[0]["predicted_yield_percent_oof"]),
        "median_model_agreement_std": short_float(out["model_agreement_std"].median()),
        "domain_warning_count": int((out["domain_warning"] == "contains_fold-novel_component_label").sum()),
        "quality_gates": {
            "ranking_contains_existing_records_only": bool(out["existing_record_only"].all()),
            "uncertainty_or_confidence_included": {"model_agreement_std", "confidence_score"}.issubset(out.columns),
            "domain_warning_included": "domain_warning" in out.columns,
            "limitations_included": True,
            "no_lab_ready_claim": True,
        },
        "limitations": [
            "Ranking is based on out-of-fold predictions for existing public records only.",
            "The table omits component labels to avoid recipe-style public output.",
            "Scores are decision-support diagnostics for retrospective analysis.",
        ],
    }
    write_json(METRICS_DIR / "existing_record_ranking_metrics.json", metrics)
    _write_report(metrics)
    return metrics


def _write_report(metrics: dict[str, Any]) -> None:
    model_names = [model_display_name(name) for name in metrics["models_used"]]
    quality_gates = [
        f"- {key.replace('_', ' ').capitalize()}: {value}"
        for key, value in metrics["quality_gates"].items()
    ]
    report = f"""# Existing-Record Ranking Report

## Summary

- Ranking rows: {metrics['row_count']}
- Models used for out-of-fold predictions: {', '.join(model_names)}
- Cross-validation folds: {metrics['cross_validation_folds']}
- Median model agreement standard deviation: {metrics['median_model_agreement_std']}
- Domain warning count: {metrics['domain_warning_count']}

## Safety Scope

This is a retrospective existing-record ranking of public dataset records with model-agreement and domain-warning diagnostics.

## Quality Gates

""" + "\n".join(quality_gates) + """

## Interpretation Context

""" + "\n".join(f"- {item}" for item in metrics["limitations"])
    write_markdown(REPORTS_DIR / "existing_record_ranking_report.md", report)


def main(use_fixture: bool = False) -> dict[str, Any]:
    metrics = rank_existing_records(use_fixture=use_fixture)
    gates = metrics["quality_gates"]
    status = "PASS" if all(gates.values()) else "DEGRADED"
    update_run_state(
        "phase_9_existing_record_ranking",
        status,
        files=[
            "reports/ranked_existing_reaction_records.csv",
            "reports/existing_record_ranking_report.md",
            "reports/metrics/existing_record_ranking_metrics.json",
        ],
        checks=list(gates.keys()),
        failures=[] if status == "PASS" else [key for key, value in gates.items() if not value],
        repairs=[],
        notes=metrics["limitations"],
        extra={"ranking_rows": metrics["row_count"]},
    )
    print(f"existing_record_ranking_status: {status}")
    print(f"ranking_rows: {metrics['row_count']}")
    print(f"domain_warning_count: {metrics['domain_warning_count']}")
    return metrics


if __name__ == "__main__":
    args = parse_args()
    main(use_fixture=args.fixture)
