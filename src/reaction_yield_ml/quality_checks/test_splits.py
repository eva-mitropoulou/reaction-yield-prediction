from reaction_yield_ml.config import METRICS_DIR
from reaction_yield_ml.reporting.io import read_json


def test_grouped_splits_have_no_group_overlap():
    metrics = read_json(METRICS_DIR / "validation_design_metrics.json")
    assert metrics["quality_gates"]["random_split_available"] is True
    assert metrics["quality_gates"]["grouped_or_out_of_component_available"] is True
    for payload in metrics["splits"].values():
        if payload.get("is_valid") and payload.get("group_column"):
            assert payload["group_overlap_count"] == 0
