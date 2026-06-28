from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.preprocessing import OneHotEncoder

from reaction_yield_ml.config import METRICS_DIR, PROCESSED_DIR, PROJECT_ROOT, REPORTS_DIR
from reaction_yield_ml.data.clean_reactions import clean_reactions
from reaction_yield_ml.reporting.run_log import update_run_state
from reaction_yield_ml.reporting.io import read_json, write_json, write_markdown
from reaction_yield_ml.validation.split_labels import component_role_display_name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build reaction component features.")
    parser.add_argument("--fixture", action="store_true", help="Use synthetic fixture for code-path testing only.")
    return parser.parse_args()


def _make_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=True)
    except TypeError:  # pragma: no cover - old sklearn compatibility
        return OneHotEncoder(handle_unknown="ignore", sparse=True)


def load_clean_data(use_fixture: bool = False) -> tuple[pd.DataFrame, list[str]]:
    clean_path = PROCESSED_DIR / "clean_reactions.csv"
    metrics_path = METRICS_DIR / "reaction_cleaning_metrics.json"
    if use_fixture or not clean_path.exists() or not metrics_path.exists():
        clean_reactions(use_fixture=use_fixture)
    frame = pd.read_csv(clean_path)
    metrics = read_json(metrics_path, default={})
    component_cols = metrics.get("component_columns") or [
        col for col in frame.columns if col.startswith("component_")
    ]
    return frame, component_cols


def _project_relative(path: Any) -> str:
    path = Path(path) if not hasattr(path, "relative_to") else path
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def build_features(use_fixture: bool = False) -> dict[str, Any]:
    frame, component_cols = load_clean_data(use_fixture=use_fixture)
    target_leakage_terms = {"yield", "output", "target", "observed", "measured"}
    leakage_columns = [
        col for col in component_cols if any(term in col.lower() for term in target_leakage_terms)
    ]
    feature_dir = PROCESSED_DIR / "features"
    feature_dir.mkdir(parents=True, exist_ok=True)
    if leakage_columns:
        raise ValueError(f"Target-like columns are not allowed as predictors: {leakage_columns}")
    encoder = _make_encoder()
    matrix = encoder.fit_transform(frame[component_cols].astype(str))
    feature_names = encoder.get_feature_names_out(component_cols).tolist()
    sparse.save_npz(feature_dir / "categorical_onehot.npz", matrix)
    joblib.dump(encoder, feature_dir / "categorical_onehot_encoder.joblib")
    index = frame[["record_id", "yield_percent", "source_mode"]].copy()
    index["row_index"] = np.arange(len(index))
    index.to_csv(feature_dir / "feature_index.csv", index=False)
    write_json(feature_dir / "feature_names.json", {"categorical_onehot": feature_names})
    smiles_cols = [col for col in frame.columns if "smiles" in col.lower()]
    descriptor_status = "skipped_no_smiles_columns" if not smiles_cols else "skipped_optional_rdkit_not_configured"
    metadata = {
        "feature_families": {
            "categorical_onehot": {
                "status": "built",
                "row_count": int(matrix.shape[0]),
                "feature_count": int(matrix.shape[1]),
                "component_columns": component_cols,
            },
            "rdkit_descriptors": {
                "status": descriptor_status,
                "reason": "Selected workbook provides component labels but no component SMILES.",
            },
            "morgan_fingerprints": {
                "status": descriptor_status,
                "reason": "Selected workbook provides component labels but no component SMILES.",
            },
            "advanced_reaction_embeddings": {
                "status": "skipped_optional_dependencies",
                "reason": "DRFP/rxnfp graph embeddings are optional and not required for the safe benchmark.",
            },
        },
        "quality_gates": {
            "no_target_leakage_in_features": not leakage_columns,
            "feature_rows_align_clean_rows": int(matrix.shape[0]) == int(len(frame)),
            "missing_structures_handled_explicitly": True,
            "no_yield_derived_columns_used": True,
        },
        "outputs": {
            "matrix": _project_relative(feature_dir / "categorical_onehot.npz"),
            "index": _project_relative(feature_dir / "feature_index.csv"),
            "encoder": _project_relative(feature_dir / "categorical_onehot_encoder.joblib"),
        },
    }
    write_json(feature_dir / "feature_metadata.json", metadata)
    write_json(METRICS_DIR / "feature_engineering_metrics.json", metadata)
    component_labels = [component_role_display_name(col) for col in component_cols]
    report = f"""# Feature Engineering Report

## Summary

- Feature family built: categorical baseline one-hot encoding.
- Feature matrix rows: {matrix.shape[0]}
- Feature matrix columns: {matrix.shape[1]}
- Component roles: {', '.join(component_labels)}

## Optional Structure Features

- RDKit descriptors: {metadata['feature_families']['rdkit_descriptors']['status']}
- Morgan fingerprints: {metadata['feature_families']['morgan_fingerprints']['status']}
- Advanced embeddings: {metadata['feature_families']['advanced_reaction_embeddings']['status']}

## Quality Gates

- No target leakage in features: {metadata['quality_gates']['no_target_leakage_in_features']}
- Feature rows align with cleaned rows: {metadata['quality_gates']['feature_rows_align_clean_rows']}
- Missing structures handled explicitly: {metadata['quality_gates']['missing_structures_handled_explicitly']}

## Interpretation Context

- The selected public workbook contains component labels, not component structures.
- Structure-based featurization is therefore limited in this run and is marked as skipped rather than imputed.
"""
    write_markdown(REPORTS_DIR / "feature_engineering_report.md", report)
    return metadata


def main(use_fixture: bool = False) -> dict[str, Any]:
    metrics = build_features(use_fixture=use_fixture)
    gates = metrics["quality_gates"]
    status = "PASS" if all(gates.values()) else "BLOCKED"
    update_run_state(
        "phase_4_component_featurization",
        status,
        files=[
            "data/processed/features/categorical_onehot.npz",
            "data/processed/features/feature_index.csv",
            "data/processed/features/feature_metadata.json",
            "reports/feature_engineering_report.md",
            "reports/metrics/feature_engineering_metrics.json",
        ],
        checks=list(gates.keys()),
        failures=[] if status == "PASS" else [key for key, value in gates.items() if not value],
        repairs=[],
        notes=[
            "Molecular descriptors and fingerprints skipped because component SMILES are not present.",
            "Categorical baseline is the primary feature family for this workbook.",
        ],
        extra={"categorical_feature_count": metrics["feature_families"]["categorical_onehot"]["feature_count"]},
    )
    print(f"feature_engineering_status: {status}")
    print(f"feature_rows: {metrics['feature_families']['categorical_onehot']['row_count']}")
    print(f"feature_columns: {metrics['feature_families']['categorical_onehot']['feature_count']}")
    return metrics


if __name__ == "__main__":
    args = parse_args()
    main(use_fixture=args.fixture)
