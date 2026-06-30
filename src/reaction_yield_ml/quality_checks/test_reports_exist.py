from pathlib import Path

from reaction_yield_ml.config import PROJECT_ROOT


def test_required_reports_and_figures_exist():
    required = [
        "reports/final_project_report.md",
        "reports/model_benchmark_report.md",
        "reports/uncertainty_calibration_report.md",
        "reports/active_learning_report.md",
        "reports/existing_record_ranking_report.md",
        "reports/model_interpretability_report.md",
        "reports/figures/model_comparison_by_split.png",
        "reports/figures/predicted_vs_observed.png",
        "reports/figures/error_by_yield_bin.png",
        "reports/figures/uncertainty_vs_error.png",
        "reports/figures/calibration_bins.png",
        "reports/figures/active_learning_budget_curve.png",
        "reports/figures/top_yield_recovery_curve.png",
        "reports/figures/feature_importance.png",
        "reports/figures/error_by_component.png",
    ]
    for rel in required:
        assert (PROJECT_ROOT / rel).exists(), rel


def test_reports_avoid_unsupported_claims():
    banned = [
        "production-ready",
        "synthesis protocol",
        "lab-ready recommendation",
        "autonomous chemistry agent",
        "guaranteed yield optimization",
        "drug-candidate synthesis route",
    ]
    for path in Path(PROJECT_ROOT / "reports").glob("*.md"):
        text = path.read_text(encoding="utf-8").lower()
        for phrase in banned:
            assert phrase not in text
