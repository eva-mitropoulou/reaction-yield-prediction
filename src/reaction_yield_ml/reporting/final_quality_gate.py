from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from reaction_yield_ml.config import METRICS_DIR, PROJECT_ROOT, REPORTS_DIR
from reaction_yield_ml.reporting.run_log import update_run_state
from reaction_yield_ml.reporting.io import read_json, write_json, write_markdown


def parse_args() -> argparse.Namespace:
    return argparse.ArgumentParser(description="Run final project checks.").parse_args()


def _file_exists(path: str) -> bool:
    return (PROJECT_ROOT / path).exists()


def _scan_reports_for_banned_claims() -> dict[str, Any]:
    banned_phrases = [
        "production-ready",
        "synthesis protocol",
        "lab-ready recommendation",
        "autonomous chemistry agent",
        "guaranteed yield optimization",
        "drug-candidate synthesis route",
        "step-by-step wet-lab",
        "gram-scale",
        "mmol",
    ]
    hits: list[str] = []
    for path in list(REPORTS_DIR.glob("*.md")) + list((PROJECT_ROOT / "docs").glob("*.md")):
        text = path.read_text(encoding="utf-8").lower()
        for phrase in banned_phrases:
            if phrase in text:
                hits.append(f"{path.relative_to(PROJECT_ROOT)}:{phrase}")
    return {"banned_claim_hits": hits, "passes": len(hits) == 0}


def _scan_reports_for_large_tables() -> bool:
    raw_row_markers = [
        "| ligand |",
        "| additive |",
        "| base |",
        "| aryl halide |",
        "component_ligand",
        "component_additive",
        "component_base",
        "component_aryl_halide",
        "yield_percent",
    ]
    for path in REPORTS_DIR.glob("*.md"):
        lines = path.read_text(encoding="utf-8").splitlines()
        table_like = [line for line in lines if line.strip().startswith("|")]
        table_text = "\n".join(table_like).lower()
        if len(table_like) > 5 and any(marker in table_text for marker in raw_row_markers):
            return False
        if any(len(line) > 1000 for line in lines):
            return False
    return True


def run_quality_gate() -> dict[str, Any]:
    dataset = read_json(PROJECT_ROOT / "data" / "dataset_manifest.json", default={})
    cleaning = read_json(METRICS_DIR / "reaction_cleaning_metrics.json", default={})
    validation = read_json(METRICS_DIR / "validation_design_metrics.json", default={})
    model = read_json(METRICS_DIR / "model_benchmark_metrics.json", default={})
    active = read_json(METRICS_DIR / "active_learning_metrics.json", default={})
    ranking = read_json(METRICS_DIR / "existing_record_ranking_metrics.json", default={})
    final_summary = read_json(METRICS_DIR / "final_summary.json", default={})
    pytest_marker = read_json(METRICS_DIR / "pytest_status.json", default={})
    banned_scan = _scan_reports_for_banned_claims()
    source_modes = {
        "dataset": dataset.get("source_mode"),
        "cleaning": cleaning.get("source_mode"),
        "model": model.get("source_mode"),
        "active_learning": active.get("source_mode"),
        "final_summary": final_summary.get("source_mode"),
    }
    checks = {
        "dataset_source_and_license_documented": bool(dataset.get("source") and dataset.get("license_access_note")),
        "no_raw_row_dumps_in_reports": _scan_reports_for_large_tables(),
        "no_wet_lab_protocol_instructions": banned_scan["passes"],
        "existing_record_scope_documented": "existing-record ranking" in " ".join(final_summary.get("safe_scope", [])).lower(),
        "mean_baseline_included": model.get("quality_gates", {}).get("mean_baseline_included") is True,
        "random_and_grouped_validation_included_where_possible": (
            validation.get("quality_gates", {}).get("random_split_available") is True
            and validation.get("quality_gates", {}).get("grouped_or_out_of_component_available") is True
        ),
        "metrics_saved": all(
            _file_exists(path)
            for path in [
                "reports/metrics/model_benchmark_metrics.json",
                "reports/metrics/uncertainty_calibration_metrics.json",
                "reports/metrics/active_learning_metrics.json",
                "reports/metrics/final_summary.json",
            ]
        ),
        "active_learning_existing_records_only": active.get("quality_gates", {}).get("selected_records_existing_only") is True,
        "ranking_clearly_retrospective": ranking.get("quality_gates", {}).get("ranking_contains_existing_records_only") is True,
        "interpretation_context_section_exists": "## 11. Interpretation Context" in (REPORTS_DIR / "final_project_report.md").read_text(encoding="utf-8"),
        "real_public_workflow_completed": all(mode == "public_benchmark" for mode in source_modes.values()),
        "fixture_metrics_not_used_for_benchmark": all(
            mode not in {"fixture", "fixture_after_download_failure"} for mode in source_modes.values()
        ),
        "tests_pass": pytest_marker.get("status") == "PASS",
        "readme_exists": _file_exists("README.md"),
        "ci_workflow_exists": _file_exists(".github/workflows/reaction-yield-ml.yml"),
        "no_unsupported_claims": banned_scan["passes"],
    }
    status = "PASS" if all(checks.values()) else "DEGRADED"
    payload = {
        "status": status,
        "checks": checks,
        "banned_claim_hits": banned_scan["banned_claim_hits"],
        "source_mode": dataset.get("source_mode"),
        "source_modes": source_modes,
        "manual_review_notes": [
            "Manual source-license review is still recommended before redistributing the raw workbook.",
            "Keep public wording focused on the current categorical component-based benchmark.",
        ],
    }
    write_json(METRICS_DIR / "final_quality_gate_report.json", payload)
    report = "# Final Project Check Report\n\n" + "\n".join(
        f"- {key}: {value}" for key, value in checks.items()
    ) + f"\n\n## Status\n\n{status}\n\n## Remaining Manual Review\n\n" + "\n".join(
        f"- {item}" for item in payload["manual_review_notes"]
    )
    write_markdown(REPORTS_DIR / "final_quality_gate_report.md", report)
    update_run_state(
        "phase_16_final_quality_gate",
        status,
        files=["reports/final_quality_gate_report.md", "reports/metrics/final_quality_gate_report.json"],
        checks=list(checks.keys()),
        failures=[] if status == "PASS" else [key for key, value in checks.items() if not value],
        repairs=[],
        notes=payload["manual_review_notes"],
        extra={"source_mode": dataset.get("source_mode")},
    )
    return payload


def main() -> dict[str, Any]:
    payload = run_quality_gate()
    print(f"final_quality_gate_status: {payload['status']}")
    print(f"failed_checks: {[key for key, value in payload['checks'].items() if not value]}")
    return payload


if __name__ == "__main__":
    parse_args()
    main()
