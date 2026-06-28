from __future__ import annotations

import argparse
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, train_test_split

from reaction_yield_ml.config import METRICS_DIR, PROCESSED_DIR, RANDOM_STATE, REPORTS_DIR, TEST_SIZE
from reaction_yield_ml.features.build_features import build_features, load_clean_data
from reaction_yield_ml.reporting.run_log import update_run_state
from reaction_yield_ml.reporting.io import read_json, short_float, write_json, write_markdown
from reaction_yield_ml.validation.split_labels import equivalent_grouped_split_note, split_display_name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create leakage-aware validation splits.")
    parser.add_argument("--fixture", action="store_true", help="Use synthetic fixture for code-path testing only.")
    return parser.parse_args()


def _target_summary(values: pd.Series) -> dict[str, float | None]:
    return {
        "count": int(values.shape[0]),
        "mean": short_float(values.mean()),
        "std": short_float(values.std()),
        "min": short_float(values.min()),
        "max": short_float(values.max()),
    }


def _write_split(name: str, payload: dict[str, Any]) -> None:
    split_dir = PROCESSED_DIR / "splits"
    split_dir.mkdir(parents=True, exist_ok=True)
    write_json(split_dir / f"{name}.json", payload)


def _make_random_split(frame: pd.DataFrame) -> dict[str, Any]:
    train_idx, test_idx = train_test_split(
        np.arange(len(frame)),
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        shuffle=True,
    )
    return _split_payload(frame, train_idx, test_idx, "random_split", "random", None, None)


def _split_payload(
    frame: pd.DataFrame,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    name: str,
    strategy: str,
    group_column: str | None,
    holdout_groups: list[str] | None,
) -> dict[str, Any]:
    train = frame.iloc[train_idx]
    test = frame.iloc[test_idx]
    overlap: list[str] = []
    if group_column:
        overlap = sorted(set(train[group_column].astype(str)).intersection(set(test[group_column].astype(str))))
    return {
        "split_name": name,
        "strategy": strategy,
        "group_column": group_column,
        "train_record_ids": train["record_id"].astype(str).tolist(),
        "test_record_ids": test["record_id"].astype(str).tolist(),
        "train_size": int(train.shape[0]),
        "test_size": int(test.shape[0]),
        "train_target_summary": _target_summary(train["yield_percent"]),
        "test_target_summary": _target_summary(test["yield_percent"]),
        "holdout_group_values_count": len(holdout_groups or []),
        "group_overlap_count": int(len(overlap)),
        "is_valid": len(test) > 0 and (not group_column or len(overlap) == 0),
        "is_unreliable_small_split": bool(len(train) < 50 or len(test) < 20),
        "notes": "Group values are omitted from the report to avoid long chemical lists.",
    }


def _make_group_split(frame: pd.DataFrame, group_column: str, name: str, strategy: str) -> dict[str, Any]:
    unique_count = int(frame[group_column].nunique(dropna=True))
    if unique_count < 3:
        return {
            "split_name": name,
            "strategy": strategy,
            "group_column": group_column,
            "is_valid": False,
            "unavailable_reason": "fewer than three unique group values",
            "unique_group_count": unique_count,
        }
    splitter = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    train_idx, test_idx = next(splitter.split(frame, groups=frame[group_column].astype(str)))
    holdout_groups = sorted(frame.iloc[test_idx][group_column].astype(str).unique().tolist())
    return _split_payload(frame, train_idx, test_idx, name, strategy, group_column, holdout_groups)


def make_splits(use_fixture: bool = False) -> dict[str, Any]:
    if not (PROCESSED_DIR / "features" / "feature_metadata.json").exists():
        build_features(use_fixture=use_fixture)
    frame, component_cols = load_clean_data(use_fixture=use_fixture)
    splits: dict[str, dict[str, Any]] = {}
    splits["random_split"] = _make_random_split(frame)
    role_map = {
        "out_of_substrate": ["component_aryl_halide", "component_substrate", "component_electrophile"],
        "out_of_ligand": ["component_ligand"],
        "out_of_base": ["component_base"],
        "out_of_additive": ["component_additive"],
    }
    for split_name, candidates in role_map.items():
        col = next((candidate for candidate in candidates if candidate in component_cols), None)
        if col:
            splits[split_name] = _make_group_split(frame, col, split_name, split_name)
        else:
            splits[split_name] = {
                "split_name": split_name,
                "strategy": split_name,
                "is_valid": False,
                "unavailable_reason": "required component column absent",
            }
    highest = max(component_cols, key=lambda col: frame[col].nunique(dropna=True))
    splits["grouped_high_cardinality_component"] = _make_group_split(
        frame, highest, "grouped_high_cardinality_component", "grouped_high_cardinality_component"
    )
    equivalence_note = equivalent_grouped_split_note("grouped_high_cardinality_component", splits)
    for name, payload in splits.items():
        _write_split(name, payload)
    valid_splits = {name: payload for name, payload in splits.items() if payload.get("is_valid")}
    metrics = {
        "row_count": int(frame.shape[0]),
        "component_columns": component_cols,
        "split_count": len(splits),
        "valid_split_count": len(valid_splits),
        "valid_splits": sorted(valid_splits.keys()),
        "splits": splits,
        "split_equivalence_notes": [equivalence_note] if equivalence_note else [],
        "quality_gates": {
            "random_split_available": bool(splits["random_split"].get("is_valid")),
            "grouped_or_out_of_component_available": any(
                payload.get("is_valid") and payload.get("group_column")
                for payload in splits.values()
            ),
            "no_group_overlap_for_grouped_splits": all(
                payload.get("group_overlap_count", 0) == 0
                for payload in splits.values()
                if payload.get("is_valid") and payload.get("group_column")
            ),
            "split_sizes_reported": all(
                "train_size" in payload and "test_size" in payload
                for payload in valid_splits.values()
            ),
            "target_distribution_reported": all(
                "train_target_summary" in payload and "test_target_summary" in payload
                for payload in valid_splits.values()
            ),
        },
    }
    write_json(METRICS_DIR / "validation_design_metrics.json", metrics)
    lines = [
        "# Validation Design Report",
        "",
        "## Summary",
        "",
        f"- Rows available: {metrics['row_count']}",
        f"- Valid split count: {metrics['valid_split_count']}",
        f"- Valid splits: {', '.join(split_display_name(name, valid_splits[name]) for name in sorted(valid_splits))}",
        "",
        "## Split Status",
        "",
    ]
    for name, payload in splits.items():
        if payload.get("is_valid"):
            label = split_display_name(name, payload)
            design_note = ", held-out groups omitted" if payload.get("group_column") else ""
            lines.append(f"- {label}: valid, train={payload['train_size']}, test={payload['test_size']}{design_note}")
        else:
            lines.append(f"- {split_display_name(name, payload)}: unavailable, reason={payload.get('unavailable_reason', 'not valid')}")
    if equivalence_note:
        lines.extend(["", "## Split Equivalence Note", "", equivalence_note])
    quality_gate_lines = [
        f"- {key.replace('_', ' ').capitalize()}: {value}"
        for key, value in metrics["quality_gates"].items()
    ]
    lines.extend(
        [
            "",
            "## Quality Gates",
            "",
            *quality_gate_lines,
            "",
            "Held-out group values are not listed to avoid long component lists.",
        ]
    )
    write_markdown(REPORTS_DIR / "validation_design_report.md", "\n".join(lines))
    return metrics


def main(use_fixture: bool = False) -> dict[str, Any]:
    metrics = make_splits(use_fixture=use_fixture)
    gates = metrics["quality_gates"]
    status = "PASS" if all(gates.values()) else "DEGRADED"
    update_run_state(
        "phase_5_validation_design",
        status,
        files=[
            "data/processed/splits/*.json",
            "reports/validation_design_report.md",
            "reports/metrics/validation_design_metrics.json",
        ],
        checks=list(gates.keys()),
        failures=[] if status == "PASS" else [key for key, value in gates.items() if not value],
        repairs=[],
        limitations=["Small grouped splits are flagged when applicable.", "Held-out group values are not printed."],
        extra={"valid_splits": metrics["valid_splits"]},
    )
    print(f"validation_design_status: {status}")
    print(f"valid_split_count: {metrics['valid_split_count']}")
    print(f"valid_splits: {metrics['valid_splits']}")
    return metrics


if __name__ == "__main__":
    args = parse_args()
    main(use_fixture=args.fixture)
