import pandas as pd
from scipy import sparse

from reaction_yield_ml.config import PROCESSED_DIR
from reaction_yield_ml.reporting.io import read_json


def test_feature_matrix_aligns_with_index():
    feature_dir = PROCESSED_DIR / "features"
    matrix = sparse.load_npz(feature_dir / "categorical_onehot.npz")
    index = pd.read_csv(feature_dir / "feature_index.csv")
    metadata = read_json(feature_dir / "feature_metadata.json")
    assert matrix.shape[0] == index.shape[0]
    assert matrix.shape[1] == metadata["feature_families"]["categorical_onehot"]["feature_count"]
    assert metadata["quality_gates"]["feature_rows_align_clean_rows"] is True
