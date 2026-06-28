from __future__ import annotations

import argparse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from reaction_yield_ml.config import (
    CITATION_TEXT,
    DATA_DIR,
    DATASET_NAME,
    DATASET_RAW_URL,
    DATASET_SOURCE,
    EXTERNAL_DIR,
    LICENSE_ACCESS_NOTE,
    PROJECT_ROOT,
    RAW_DATA_FILE,
    RAW_DIR,
    TARGET_COLUMN_CANDIDATES,
    TOY_FIXTURE_FILE,
    ensure_directories,
)
from reaction_yield_ml.reporting.run_log import update_run_state
from reaction_yield_ml.reporting.io import short_float, slugify, write_json, write_markdown

PRIMARY_SHEET = "Plates1-3"
COMPONENT_COLUMNS = ["Ligand", "Additive", "Base", "Aryl halide"]
TARGET_COLUMN = "Output"


@dataclass(frozen=True)
class DatasetBundle:
    frame: pd.DataFrame
    source_mode: str
    source_path: Path
    sheet_name: str | None
    target_column: str
    component_columns: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select and prepare the public reaction-yield dataset.")
    parser.add_argument("--fixture", action="store_true", help="Use synthetic fixture for code-path testing only.")
    return parser.parse_args()


def download_public_dataset(force: bool = False) -> tuple[Path, str | None]:
    ensure_directories()
    if RAW_DATA_FILE.exists() and not force:
        return RAW_DATA_FILE, None
    try:
        request = urllib.request.Request(DATASET_RAW_URL, headers={"User-Agent": "reaction-yield-ml/0.1"})
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read()
        if len(payload) < 1000:
            return RAW_DATA_FILE, "Downloaded payload was unexpectedly small."
        RAW_DATA_FILE.write_bytes(payload)
        return RAW_DATA_FILE, None
    except Exception as exc:  # pragma: no cover - network-specific branch
        return RAW_DATA_FILE, f"{type(exc).__name__}: {exc}"


def ensure_toy_fixture() -> Path:
    ensure_directories()
    if TOY_FIXTURE_FILE.exists():
        return TOY_FIXTURE_FILE
    rows: list[dict[str, Any]] = []
    ligands = [f"fixture_ligand_{idx}" for idx in range(1, 7)]
    additives = [f"fixture_additive_{idx}" for idx in range(1, 5)]
    bases = [f"fixture_base_{idx}" for idx in range(1, 4)]
    aryls = [f"fixture_aryl_halide_{idx}" for idx in range(1, 5)]
    for l_idx, ligand in enumerate(ligands):
        for a_idx, additive in enumerate(additives):
            for b_idx, base in enumerate(bases):
                for h_idx, aryl in enumerate(aryls):
                    value = 8 + l_idx * 7 + a_idx * 4 + b_idx * 5 + h_idx * 6
                    value += ((l_idx + h_idx) % 3) * 3
                    rows.append(
                        {
                            "Ligand": ligand,
                            "Additive": additive,
                            "Base": base,
                            "Aryl halide": aryl,
                            "Output": min(98, float(value)),
                        }
                    )
    pd.DataFrame(rows).to_csv(TOY_FIXTURE_FILE, index=False)
    return TOY_FIXTURE_FILE


def load_raw_dataset(use_fixture: bool = False) -> DatasetBundle:
    ensure_directories()
    if use_fixture:
        path = ensure_toy_fixture()
        frame = pd.read_csv(path)
        return DatasetBundle(frame, "fixture", path, None, TARGET_COLUMN, COMPONENT_COLUMNS)

    path, error = download_public_dataset()
    if error or not path.exists():
        path = ensure_toy_fixture()
        frame = pd.read_csv(path)
        return DatasetBundle(frame, "fixture_after_download_failure", path, None, TARGET_COLUMN, COMPONENT_COLUMNS)

    sheet = choose_sheet(path)
    frame = pd.read_excel(path, sheet_name=sheet, usecols=COMPONENT_COLUMNS + [TARGET_COLUMN])
    return DatasetBundle(frame, "public_benchmark", path, sheet, TARGET_COLUMN, COMPONENT_COLUMNS)


def choose_sheet(path: Path) -> str:
    workbook = pd.ExcelFile(path)
    if PRIMARY_SHEET in workbook.sheet_names:
        return PRIMARY_SHEET
    scored: list[tuple[int, str]] = []
    for sheet in workbook.sheet_names:
        cols = pd.read_excel(path, sheet_name=sheet, nrows=0).columns.astype(str).tolist()
        score = sum(col in cols for col in COMPONENT_COLUMNS + [TARGET_COLUMN])
        scored.append((score, sheet))
    scored.sort(reverse=True)
    if not scored or scored[0][0] < 3:
        raise ValueError("No workbook sheet contained the expected reaction component and target columns.")
    return scored[0][1]


def infer_target_column(columns: list[str]) -> str | None:
    normalized = {slugify(col): col for col in columns}
    for candidate in TARGET_COLUMN_CANDIDATES:
        key = slugify(candidate)
        if key in normalized:
            return normalized[key]
    for col in columns:
        if "yield" in slugify(col) or slugify(col) == "output":
            return col
    return None


def summarize_dataset(bundle: DatasetBundle) -> dict[str, Any]:
    frame = bundle.frame
    target_numeric = pd.to_numeric(frame[bundle.target_column], errors="coerce")
    return {
        "dataset_name": DATASET_NAME,
        "source": DATASET_SOURCE,
        "raw_url": DATASET_RAW_URL,
        "citation_text": CITATION_TEXT,
        "license_access_note": LICENSE_ACCESS_NOTE,
        "source_mode": bundle.source_mode,
        "source_path": _public_safe_source_path(bundle.source_path),
        "selected_sheet": bundle.sheet_name,
        "row_count": int(len(frame)),
        "raw_columns": [str(col) for col in frame.columns],
        "selected_target_column": bundle.target_column,
        "component_columns": bundle.component_columns,
        "target_min": short_float(target_numeric.min()),
        "target_max": short_float(target_numeric.max()),
        "redistribution_allowed": "review_source_license_before_redistributing_raw_workbook",
        "limitations": [
            "Retrospective public-data benchmark only.",
            "The selected workbook provides component labels; structure-aware features require an external public component-to-SMILES mapping.",
            "The workflow ranks existing public records.",
        ],
    }


def _public_safe_source_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return path.name


def write_dataset_selection_outputs(bundle: DatasetBundle) -> dict[str, Any]:
    metrics = summarize_dataset(bundle)
    write_json(DATA_DIR / "dataset_manifest.json", metrics)
    data_card = f"""# Data Card

## Dataset

{metrics['dataset_name']}

## Source

- Repository: rxn4chemistry/rxn_yields
- Selected sheet: {metrics['selected_sheet']}
- Source mode: {metrics['source_mode']}

## Citation

Public Buchwald-Hartwig high-throughput reaction-yield benchmark.

## License And Access

{LICENSE_ACCESS_NOTE}

Redistribution note: {metrics['redistribution_allowed']}.

## Fields

- Row count: {metrics['row_count']}
- Raw columns: {', '.join(metrics['raw_columns'])}
- Target column: {metrics['selected_target_column']}
- Component columns: {', '.join(metrics['component_columns'])}

## Project Role

This is a retrospective public-data benchmark for component-label reaction-yield modeling and existing-record ranking.

## Interpretation Context

""" + "\n".join(f"- {item}" for item in metrics["limitations"])
    write_markdown(DATA_DIR / "DATA_CARD.md", data_card)
    selection_report = f"""# Dataset Selection Report

## Status

Selected public Buchwald-Hartwig HTE reaction-yield workbook for reaction-yield modeling.

## Selection Rationale

- Public benchmark lineage with reaction components and measured yield.
- Suitable for random and out-of-component validation.
- Contains component columns and a measured target column.
- No private credentials required for the public repository source.

## Manifest Summary

- Dataset name: {metrics['dataset_name']}
- Source mode: {metrics['source_mode']}
- Row count: {metrics['row_count']}
- Target column: {metrics['selected_target_column']}
- Component columns: {', '.join(metrics['component_columns'])}
- Redistribution note: {metrics['redistribution_allowed']}

## Safety Scope

This project supports retrospective public-data benchmarking and existing-record ranking.
"""
    write_markdown(REPORT_PATHS["selection"], selection_report)
    write_json(REPORT_PATHS["selection_metrics"], metrics)
    return metrics


REPORT_PATHS = {
    "selection": Path("reports/dataset_selection_report.md"),
    "selection_metrics": Path("reports/metrics/dataset_selection_metrics.json"),
}


def main(use_fixture: bool = False) -> dict[str, Any]:
    bundle = load_raw_dataset(use_fixture=use_fixture)
    metrics = write_dataset_selection_outputs(bundle)
    status = "PASS" if bundle.source_mode == "public_benchmark" else "DEGRADED"
    update_run_state(
        "phase_1_dataset_selection",
        status,
        files=[
            "data/DATA_CARD.md",
            "data/dataset_manifest.json",
            "reports/dataset_selection_report.md",
            "reports/metrics/dataset_selection_metrics.json",
        ],
        checks=[
            "public source reachable" if bundle.source_mode == "public_benchmark" else "fixture mode selected",
            "component columns present",
            "target column present",
            "row count recorded",
        ],
        failures=[] if status == "PASS" else ["public benchmark validation failed"],
        repairs=[],
        notes=metrics["limitations"],
        extra={"source_mode": bundle.source_mode, "row_count": metrics["row_count"]},
    )
    print(f"dataset_selection_status: {status}")
    print(f"source_mode: {bundle.source_mode}")
    print(f"row_count: {metrics['row_count']}")
    print(f"columns: {metrics['raw_columns']}")
    return metrics


if __name__ == "__main__":
    args = parse_args()
    main(use_fixture=args.fixture)
