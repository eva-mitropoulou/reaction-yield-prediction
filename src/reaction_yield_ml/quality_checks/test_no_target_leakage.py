from reaction_yield_ml.config import PROCESSED_DIR
from reaction_yield_ml.reporting.io import read_json


def test_feature_metadata_reports_no_target_leakage():
    metadata = read_json(PROCESSED_DIR / "features" / "feature_metadata.json")
    gates = metadata["quality_gates"]
    assert gates["no_target_leakage_in_features"] is True
    assert gates["no_yield_derived_columns_used"] is True
    component_cols = metadata["feature_families"]["categorical_onehot"]["component_columns"]
    forbidden = ("yield", "output", "target", "observed", "measured")
    assert not any(any(term in col.lower() for term in forbidden) for col in component_cols)
