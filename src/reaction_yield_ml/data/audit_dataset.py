from __future__ import annotations

import argparse
from typing import Any

import pandas as pd

from reaction_yield_ml.config import METRICS_DIR, REPORTS_DIR
from reaction_yield_ml.data.load_dataset import load_raw_dataset
from reaction_yield_ml.reporting.run_log import update_run_state
from reaction_yield_ml.reporting.io import short_float, write_json, write_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit reaction-yield dataset without printing raw rows.")
    parser.add_argument("--fixture", action="store_true", help="Use synthetic fixture for code-path testing only.")
    return parser.parse_args()


def audit_dataset(use_fixture: bool = False) -> dict[str, Any]:
    bundle = load_raw_dataset(use_fixture=use_fixture)
    frame = bundle.frame.copy()
    target = pd.to_numeric(frame[bundle.target_column], errors="coerce")
    duplicate_rows = int(frame.duplicated().sum())
    component_availability = {col: col in frame.columns for col in bundle.component_columns}
    missing_components = {
        col: int(frame[col].isna().sum() + (frame[col].astype(str).str.strip() == "").sum())
        for col in bundle.component_columns
        if col in frame.columns
    }
    invalid_identifiers = {
        col: int(frame[col].map(lambda value: not isinstance(value, str) or not str(value).strip()).sum())
        for col in bundle.component_columns
        if col in frame.columns
    }
    cardinalities = {
        col: int(frame[col].astype(str).nunique(dropna=True))
        for col in bundle.component_columns
        if col in frame.columns
    }
    trainable_mask = target.notna()
    for col in bundle.component_columns:
        if col in frame.columns:
            trainable_mask &= frame[col].notna() & (frame[col].astype(str).str.strip() != "")
        else:
            trainable_mask &= False
    metrics = {
        "source_mode": bundle.source_mode,
        "raw_row_count": int(len(frame)),
        "raw_column_count": int(frame.shape[1]),
        "raw_columns": [str(col) for col in frame.columns],
        "duplicate_row_count": duplicate_rows,
        "missing_target_count": int(target.isna().sum()),
        "target_min": short_float(target.min()),
        "target_max": short_float(target.max()),
        "target_mean": short_float(target.mean()),
        "component_column_availability": component_availability,
        "invalid_component_identifier_counts": invalid_identifiers,
        "missing_component_counts": missing_components,
        "categorical_cardinalities": cardinalities,
        "trainable_row_count": int(trainable_mask.sum()),
        "limitations": [
            "Audit reports aggregate counts only.",
            "Invalid component identifiers are string-presence checks, not chemical-validity checks.",
        ],
    }
    return metrics


def write_audit_outputs(metrics: dict[str, Any]) -> None:
    write_json(METRICS_DIR / "data_audit_metrics.json", metrics)
    report = f"""# Data Audit Report

## Summary

- Source mode: {metrics['source_mode']}
- Raw row count: {metrics['raw_row_count']}
- Raw column count: {metrics['raw_column_count']}
- Duplicate row count: {metrics['duplicate_row_count']}
- Missing target count: {metrics['missing_target_count']}
- Target range: {metrics['target_min']} to {metrics['target_max']}
- Trainable row count: {metrics['trainable_row_count']}

## Component Availability

""" + "\n".join(
        f"- {col}: available={available}, missing={metrics['missing_component_counts'].get(col, 'n/a')}, cardinality={metrics['categorical_cardinalities'].get(col, 'n/a')}"
        for col, available in metrics["component_column_availability"].items()
    ) + """

## Interpretation Context

""" + "\n".join(f"- {item}" for item in metrics["limitations"])
    write_markdown(REPORTS_DIR / "data_audit_report.md", report)


def main(use_fixture: bool = False) -> dict[str, Any]:
    metrics = audit_dataset(use_fixture=use_fixture)
    write_audit_outputs(metrics)
    status = "PASS" if metrics["trainable_row_count"] > 50 else "DEGRADED"
    update_run_state(
        "phase_2_data_audit",
        status,
        files=["reports/data_audit_report.md", "reports/metrics/data_audit_metrics.json"],
        checks=[
            "raw row count computed",
            "duplicate count computed",
            "missing target count computed",
            "component cardinalities computed",
        ],
        failures=[] if status == "PASS" else ["trainable row count is small"],
        repairs=[],
        notes=metrics["limitations"],
        extra={"trainable_row_count": metrics["trainable_row_count"]},
    )
    print(f"data_audit_status: {status}")
    print(f"raw_row_count: {metrics['raw_row_count']}")
    print(f"trainable_row_count: {metrics['trainable_row_count']}")
    print(f"columns: {metrics['raw_columns']}")
    return metrics


if __name__ == "__main__":
    args = parse_args()
    main(use_fixture=args.fixture)
