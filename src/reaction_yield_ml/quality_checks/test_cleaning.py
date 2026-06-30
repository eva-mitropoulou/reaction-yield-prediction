import pandas as pd

from reaction_yield_ml.config import PROCESSED_DIR


def test_cleaned_reactions_have_numeric_bounded_target():
    path = PROCESSED_DIR / "clean_reactions.csv"
    assert path.exists()
    frame = pd.read_csv(path)
    assert frame.shape[0] > 50
    assert frame["yield_percent"].notna().all()
    assert frame["yield_percent"].between(0, 100).all()
    assert frame["record_id"].is_unique
