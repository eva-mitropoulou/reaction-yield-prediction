from reaction_yield_ml.config import METRICS_DIR
from reaction_yield_ml.reporting.io import read_json


def test_model_and_uncertainty_metrics_schema():
    model = read_json(METRICS_DIR / "model_benchmark_metrics.json")
    assert "mean_baseline" in model["models_evaluated"]
    assert model["best_model"]
    assert {"mae", "rmse", "r2", "spearman", "top_10pct_enrichment"}.issubset(
        model["best_model_primary_split_metrics"]
    )
    uncertainty = read_json(METRICS_DIR / "uncertainty_calibration_metrics.json")
    assert uncertainty["quality_gates"]["uncertainty_evaluated_against_actual_errors"] is True
    active = read_json(METRICS_DIR / "active_learning_metrics.json")
    assert active["quality_gates"]["random_baseline_included"] is True
    ranking = read_json(METRICS_DIR / "existing_record_ranking_metrics.json")
    assert ranking["quality_gates"]["ranking_contains_existing_records_only"] is True
