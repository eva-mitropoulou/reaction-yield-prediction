from __future__ import annotations

import argparse
from typing import Any

from reaction_yield_ml.config import DATA_DIR, DOCS_DIR, METRICS_DIR, REPORTS_DIR
from reaction_yield_ml.reporting.run_log import update_run_state
from reaction_yield_ml.reporting.io import read_json, write_json, write_markdown
from reaction_yield_ml.validation.split_labels import model_display_name, split_display_name, strategy_display_name


def parse_args() -> argparse.Namespace:
    return argparse.ArgumentParser(description="Build final project report and cards.").parse_args()


def _load_metrics() -> dict[str, Any]:
    names = [
        "dataset_selection_metrics",
        "data_audit_metrics",
        "reaction_cleaning_metrics",
        "feature_engineering_metrics",
        "validation_design_metrics",
        "model_benchmark_metrics",
        "uncertainty_calibration_metrics",
        "active_learning_metrics",
        "existing_record_ranking_metrics",
        "model_interpretability_metrics",
    ]
    return {name: read_json(METRICS_DIR / f"{name}.json", default={}) for name in names}


def build_final_report() -> dict[str, Any]:
    metrics = _load_metrics()
    dataset = metrics["dataset_selection_metrics"]
    cleaning = metrics["reaction_cleaning_metrics"]
    features = metrics["feature_engineering_metrics"]
    validation = metrics["validation_design_metrics"]
    models = metrics["model_benchmark_metrics"]
    uncertainty = metrics["uncertainty_calibration_metrics"]
    active = metrics["active_learning_metrics"]
    ranking = metrics["existing_record_ranking_metrics"]
    interp = metrics["model_interpretability_metrics"]
    best = models.get("best_model_primary_split_metrics", {})
    uncertainty_primary = uncertainty.get("split_summaries", {}).get(uncertainty.get("primary_split"), {})
    valid_split_labels = [split_display_name(name, validation.get("splits", {}).get(name, {})) for name in validation.get("valid_splits", [])]
    active_strategy_labels = [strategy_display_name(name) for name in active.get("strategies", [])]
    best_model_label = model_display_name(models.get("best_model", ""))
    primary_split_label = models.get("primary_selection_split_display") or split_display_name(
        models.get("primary_selection_split", ""),
        validation.get("splits", {}).get(models.get("primary_selection_split", ""), {}),
    )
    dataset_name = str(dataset.get("dataset_name") or "").replace("Ahneman/Dreher/Doyle", "Ahneman, Dreher, and Doyle")
    source_mode = str(dataset.get("source_mode") or "").replace("_", " ")
    final_summary = {
        "dataset_name": dataset.get("dataset_name"),
        "source_mode": dataset.get("source_mode"),
        "raw_row_count": dataset.get("row_count"),
        "clean_row_count": cleaning.get("clean_row_count"),
        "feature_family": "categorical_onehot",
        "feature_count": features.get("feature_families", {}).get("categorical_onehot", {}).get("feature_count"),
        "valid_splits": validation.get("valid_splits"),
        "best_model": models.get("best_model"),
        "primary_selection_split": models.get("primary_selection_split"),
        "primary_selection_split_display": models.get("primary_selection_split_display"),
        "primary_split_equivalence_note": models.get("primary_split_equivalence_note"),
        "best_model_metrics": best,
        "uncertainty_primary": uncertainty_primary,
        "active_learning_seed_count": active.get("seed_count"),
        "active_learning_strategies": active.get("strategies"),
        "active_learning_strategy_labels": active_strategy_labels,
        "ranking_row_count": ranking.get("row_count"),
        "interpretability_primary_split": interp.get("primary_split"),
        "safe_scope": [
            "retrospective public-data benchmark",
            "retrospective public-data benchmark",
            "existing-record ranking",
            "component-label modeling",
            "existing-record ranking",
        ],
    }
    write_json(METRICS_DIR / "final_summary.json", final_summary)
    report = f"""# Final Project Report

## 1. Executive Summary

Reaction Yield Prediction from Public HTE Component Labels is a retrospective public-data benchmark for reaction-yield modeling. It covers data curation, categorical component featurization, leakage-aware validation, uncertainty-aware prioritization, active-learning simulation, and existing-record ranking.

Project role: public HTE component-label modeling, retrospective validation, and existing-record ranking.

## 2. Why Reaction-Yield Prediction Matters

Reaction-yield modeling helps evaluate whether machine-learning workflows can learn from historical high-throughput reaction records under validation designs that reflect component generalization rather than only random interpolation.

## 3. Dataset

- Dataset: {dataset_name}
- Source mode: {source_mode}
- Raw row count: {final_summary['raw_row_count']}
- Clean row count: {final_summary['clean_row_count']}
- Target: reaction yield percentage
- Components: ligand, additive, base, aryl halide labels

## 4. Cleaning And Standardization

The pipeline standardizes the target as numeric percentage, normalizes component labels as strings, removes impossible target values, and removes exact duplicate component-target records.

## 5. Feature Engineering

- Primary feature family: categorical one-hot component encoding
- Feature count: {final_summary['feature_count']}
- Molecular descriptors and fingerprints: skipped because the selected workbook provides labels but no component SMILES
- Leakage audit: yield-derived columns are excluded from predictors

## 6. Validation Strategy

Valid splits: {', '.join(valid_split_labels)}

The benchmark includes random validation and grouped/out-of-component validation where possible. Out-of-component validation carries the main generalization interpretation.

## 7. Model Benchmark

- Selected model: {best_model_label}
- Primary selection split: {primary_split_label}
- MAE: {best.get('mae')}
- RMSE: {best.get('rmse')}
- R2: {best.get('r2')}
- Spearman: {best.get('spearman')}
- Top-10% enrichment: {best.get('top_10pct_enrichment')}

Validation note: {final_summary.get('primary_split_equivalence_note') or 'No equivalent grouped split note was recorded.'}

## 8. Uncertainty And Calibration

- Method: random-forest ensemble variance plus split conformal interval
- Primary split coverage: {uncertainty_primary.get('empirical_coverage_90')}
- Uncertainty-error Spearman: {uncertainty_primary.get('spearman_abs_error_vs_uncertainty')}

Uncertainty is evaluated against actual errors and low-confidence predictions are flagged.

## 9. Active-Learning Simulation

The active-learning simulation is a budgeted selection workflow over existing public records. It uses multiple seeds, includes a random baseline, and compares {', '.join(active_strategy_labels)}.

## 10. Existing-Record Ranking

The ranking table contains existing records. It includes predicted yield, confidence/model-agreement diagnostics, domain warnings, and component-diversity score.

## 11. Interpretation Context

- Component structures are unavailable in the selected workbook.
- Categorical features support component-label benchmarking.
- Out-of-component validation is more reliable than random split performance for generalization claims.
- Active-learning curves are retrospective simulations over existing records.
- Existing-record ranking is decision-support analysis.

## 12. Reproducibility

```bash
make setup
make data
make features
make train
make evaluate
make active-learning
make report
make test
```

Small fixture smoke test:

```bash
make reproduce-small
```

The fixture is synthetic and supports code-path checks.

## 13. Working Summary

This repository keeps a retrospective public-data HTE reaction-yield modeling workflow with reaction cleaning, categorical component featurization, random and out-of-component validation, uncertainty diagnostics, active-learning simulation, and existing-record ranking.
"""
    write_markdown(REPORTS_DIR / "final_project_report.md", report)
    _write_cards(final_summary)
    return final_summary


def _write_cards(summary: dict[str, Any]) -> None:
    data_card = (DATA_DIR / "DATA_CARD.md").read_text(encoding="utf-8") if (DATA_DIR / "DATA_CARD.md").exists() else ""
    write_markdown(DOCS_DIR / "data_card.md", data_card)
    metric_labels = {
        "mae": "MAE",
        "rmse": "RMSE",
        "r2": "R2",
        "spearman": "Spearman",
        "top_10pct_enrichment": "Top-10% enrichment",
    }
    metric_lines = "\n".join(
        f"- {label}: {summary.get('best_model_metrics', {}).get(key)}"
        for key, label in metric_labels.items()
        if summary.get("best_model_metrics", {}).get(key) is not None
    )
    model_card = f"""# Model Card

## Intended Use

Retrospective public-data benchmark for reaction-yield modeling and existing-record ranking.

## Project Role

- Retrospective public-data benchmark.
- Existing-record ranking and uncertainty diagnostics.
- Component-label modeling with categorical features.
- Structure-aware reaction modeling documented as future work.

## Data And Features

- Dataset: {summary.get('dataset_name')}
- Source mode: {str(summary.get('source_mode') or '').replace('_', ' ')}
- Raw rows: {summary.get('raw_row_count')}
- Clean rows: {summary.get('clean_row_count')}
- Feature family: categorical one-hot component encoding
- Valid splits: {', '.join(split_display_name(name) for name in summary.get('valid_splits') or [])}
- Primary selection split: {summary.get('primary_selection_split_display') or split_display_name(summary.get('primary_selection_split') or '')}

## Model

- Selected model: {model_display_name(summary.get('best_model') or '')}
- Selection split: {summary.get('primary_selection_split_display') or split_display_name(summary.get('primary_selection_split') or '')}

## Metrics

{metric_lines}

## Interpretation Context

The model uses categorical component labels because the selected workbook provides labels rather than component structures. Interpretability outputs describe model behavior for this component-label benchmark.
"""
    write_markdown(DOCS_DIR / "model_card.md", model_card)


def main() -> dict[str, Any]:
    summary = build_final_report()
    update_run_state(
        "phase_11_final_report",
        "PASS" if summary.get("best_model") else "DEGRADED",
        files=[
            "reports/final_project_report.md",
            "reports/metrics/final_summary.json",
            "docs/model_card.md",
            "docs/data_card.md",
        ],
        checks=["final report sections written", "safe-scope phrases included", "model and data cards written"],
        failures=[] if summary.get("best_model") else ["model summary missing"],
        repairs=[],
        notes=["Final report inherits dataset and categorical-feature limitations."],
        extra={"best_model": summary.get("best_model")},
    )
    print("final_report_status: PASS" if summary.get("best_model") else "final_report_status: DEGRADED")
    print(f"best_model: {summary.get('best_model')}")
    print(f"primary_selection_split: {summary.get('primary_selection_split')}")
    return summary


if __name__ == "__main__":
    parse_args()
    main()
