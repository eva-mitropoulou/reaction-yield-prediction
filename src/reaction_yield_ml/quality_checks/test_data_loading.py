from reaction_yield_ml.data.load_dataset import COMPONENT_COLUMNS, TARGET_COLUMN, load_raw_dataset


def test_public_or_fixture_dataset_loads_with_required_columns():
    bundle = load_raw_dataset(use_fixture=False)
    assert bundle.frame.shape[0] > 50
    assert bundle.target_column == TARGET_COLUMN
    for col in COMPONENT_COLUMNS:
        assert col in bundle.frame.columns
