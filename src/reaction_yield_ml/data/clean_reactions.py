from __future__ import annotations

import argparse
from typing import Any

import pandas as pd

from reaction_yield_ml.config import METRICS_DIR, PROCESSED_DIR, REPORTS_DIR
from reaction_yield_ml.data.load_dataset import load_raw_dataset
from reaction_yield_ml.reporting.run_log import update_run_state
from reaction_yield_ml.reporting.io import slugify, write_json, write_markdown
from reaction_yield_ml.validation.split_labels import component_role_display_name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean reaction-yield dataset for retrospective ML.")
    parser.add_argument("--fixture", action="store_true", help="Use synthetic fixture for code-path testing only.")
    return parser.parse_args()


def clean_reactions(use_fixture: bool = False) -> tuple[pd.DataFrame, dict[str, Any]]:
    bundle = load_raw_dataset(use_fixture=use_fixture)
    raw = bundle.frame.copy()
    renamed_components = {col: f"component_{slugify(col)}" for col in bundle.component_columns}
    frame = raw.rename(columns=renamed_components | {bundle.target_column: "yield_percent"})
    component_cols = list(renamed_components.values())
    frame["yield_percent"] = pd.to_numeric(frame["yield_percent"], errors="coerce")
    for col in component_cols:
        frame[col] = frame[col].astype("string").str.strip()
        frame[col] = frame[col].fillna("MISSING_COMPONENT")
        frame.loc[frame[col] == "", col] = "MISSING_COMPONENT"
    frame.insert(0, "record_id", [f"rxn_{idx:06d}" for idx in range(len(frame))])
    frame["source_mode"] = bundle.source_mode
    missing_target = int(frame["yield_percent"].isna().sum())
    impossible_mask = frame["yield_percent"].notna() & ~frame["yield_percent"].between(0, 100)
    impossible_count = int(impossible_mask.sum())
    before_filter = len(frame)
    frame = frame[frame["yield_percent"].notna() & frame["yield_percent"].between(0, 100)].copy()
    before_dedup = len(frame)
    dedup_subset = component_cols + ["yield_percent"]
    frame = frame.drop_duplicates(subset=dedup_subset, keep="first").reset_index(drop=True)
    duplicate_removed = before_dedup - len(frame)
    output_path = PROCESSED_DIR / "clean_reactions.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    metrics = {
        "source_mode": bundle.source_mode,
        "raw_row_count": int(len(raw)),
        "rows_before_filtering": int(before_filter),
        "missing_target_removed": missing_target,
        "impossible_yield_removed": impossible_count,
        "duplicate_records_removed": int(duplicate_removed),
        "clean_row_count": int(len(frame)),
        "target_column": "yield_percent",
        "component_columns": component_cols,
        "yield_min": float(frame["yield_percent"].min()) if len(frame) else None,
        "yield_max": float(frame["yield_percent"].max()) if len(frame) else None,
        "missing_structure_features": True,
        "limitations": [
            "Component strings are standardized as categorical labels; missing chemistry is not invented.",
            "No component SMILES are available in the selected workbook, so molecular descriptors are skipped unless external structures are supplied.",
            "Rows outside 0-100 percent yield are excluded rather than clipped.",
        ],
    }
    write_json(METRICS_DIR / "reaction_cleaning_metrics.json", metrics)
    component_labels = [component_role_display_name(col) for col in component_cols]
    report = f"""# Reaction Cleaning Report

## Summary

- Source mode: {metrics['source_mode']}
- Raw row count: {metrics['raw_row_count']}
- Clean row count: {metrics['clean_row_count']}
- Missing target rows removed: {metrics['missing_target_removed']}
- Impossible yield rows removed: {metrics['impossible_yield_removed']}
- Duplicate records removed: {metrics['duplicate_records_removed']}
- Target: reaction yield percentage
- Component roles: {', '.join(component_labels)}

## Standardization

- Target yield is numeric percentage.
- Component columns are stripped strings.
- Missing component values are explicitly labeled.
- Duplicate exact component-target records are removed.

## Limitations

""" + "\n".join(f"- {item}" for item in metrics["limitations"])
    write_markdown(REPORTS_DIR / "reaction_cleaning_report.md", report)
    return frame, metrics


def main(use_fixture: bool = False) -> dict[str, Any]:
    _, metrics = clean_reactions(use_fixture=use_fixture)
    status = "PASS" if metrics["clean_row_count"] > 50 else "DEGRADED"
    update_run_state(
        "phase_3_reaction_cleaning",
        status,
        files=[
            "data/processed/clean_reactions.csv",
            "reports/reaction_cleaning_report.md",
            "reports/metrics/reaction_cleaning_metrics.json",
        ],
        checks=[
            "numeric target standardized",
            "component strings standardized",
            "duplicates removed",
            "impossible yields excluded",
        ],
        failures=[] if status == "PASS" else ["clean dataset is small"],
        repairs=[],
        limitations=metrics["limitations"],
        extra={"clean_row_count": metrics["clean_row_count"]},
    )
    print(f"reaction_cleaning_status: {status}")
    print(f"clean_row_count: {metrics['clean_row_count']}")
    print(f"component_columns: {metrics['component_columns']}")
    return metrics


if __name__ == "__main__":
    args = parse_args()
    main(use_fixture=args.fixture)
