from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EXTERNAL_DIR = DATA_DIR / "external"
REPORTS_DIR = PROJECT_ROOT / "reports"
METRICS_DIR = REPORTS_DIR / "metrics"
FIGURES_DIR = REPORTS_DIR / "figures"
DOCS_DIR = PROJECT_ROOT / "docs"
NOTEBOOKS_DIR = DOCS_DIR / "notebooks"

DATASET_NAME = "Buchwald-Hartwig HTE yield benchmark (Ahneman/Dreher/Doyle lineage)"
DATASET_SOURCE = "https://github.com/rxn4chemistry/rxn_yields"
DATASET_RAW_URL = (
    "https://raw.githubusercontent.com/rxn4chemistry/rxn_yields/master/"
    "data/Buchwald-Hartwig/Dreher_and_Doyle_input_data.xlsx"
)
DATASET_RAW_FILENAME = "Dreher_and_Doyle_input_data.xlsx"
RAW_DATA_FILE = RAW_DIR / DATASET_RAW_FILENAME
TOY_FIXTURE_FILE = EXTERNAL_DIR / "toy_reaction_yield_fixture.csv"

CITATION_TEXT = (
    "Ahneman, D. T.; Estrada, J. G.; Lin, S.; Dreher, S. D.; Doyle, A. G. "
    "Predicting reaction performance in C-N cross-coupling using machine learning. "
    "Science 2018, 360, 186-190. DOI: 10.1126/science.aar5169. "
    "Public practical source: rxn_yields repository, Buchwald-Hartwig input workbook."
)

LICENSE_ACCESS_NOTE = (
    "The rxn_yields repository is public and includes a permissive repository license. "
    "The workbook is used as a public benchmark source; downstream redistribution should "
    "retain the original citation and source notes."
)

TARGET_COLUMN_CANDIDATES = {
    "yield",
    "yield_percent",
    "yield (%)",
    "% yield",
    "output",
    "measured_yield",
    "yield_perc",
}

LEAKAGE_KEYWORDS = {
    "yield",
    "output",
    "conversion",
    "selectivity",
    "ee",
    "score",
    "result",
    "measured",
    "observed",
}

COMPONENT_ROLE_KEYWORDS = {
    "aryl",
    "halide",
    "substrate",
    "electrophile",
    "nucleophile",
    "boronic",
    "ligand",
    "base",
    "additive",
    "catalyst",
    "solvent",
    "reagent",
}

RANDOM_STATE = 17
TEST_SIZE = 0.2

def ensure_directories() -> None:
    for path in [
        RAW_DIR,
        PROCESSED_DIR,
        EXTERNAL_DIR,
        PROCESSED_DIR / "features",
        PROCESSED_DIR / "splits",
        PROCESSED_DIR / "models",
        PROCESSED_DIR / "predictions",
        PROCESSED_DIR / "uncertainty",
        REPORTS_DIR,
        METRICS_DIR,
        FIGURES_DIR,
        DOCS_DIR,
        NOTEBOOKS_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)
