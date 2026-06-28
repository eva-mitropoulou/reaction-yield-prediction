# Reaction Yield Prediction from Public HTE Data

I use this repository to keep a reproducible reaction-yield modeling workflow on public high-throughput experimentation (HTE) data. The main goal is to test how far simple component-label models can go when the validation split holds out reaction components instead of only shuffling rows.

The current dataset is the public Buchwald-Hartwig HTE yield benchmark from the Ahneman/Dreher/Doyle lineage. The selected workbook provides reaction component labels but not component structures, so this version is intentionally a categorical component-based benchmark rather than a structure-aware reaction model.

What this repo does:

- cleans and audits public HTE reaction-yield records
- builds categorical one-hot component features
- compares random and out-of-component validation splits
- trains mean, linear, random forest, and gradient boosting baselines
- evaluates uncertainty/error diagnostics and empirical coverage
- runs a retrospective active-learning simulation over existing records
- ranks existing public records for analysis, without generating new chemistry

Scope boundaries:

- This is not a wet-lab protocol.
- This is not a guarantee of experimental success.
- This project does not generate new chemistry.
- Ranked outputs are retrospective existing-record rankings only.
- Reports avoid operational synthesis instructions, raw row dumps, long chemical lists, and recipe-style output.

## Reproduction

```bash
make setup
make data
make features
make train
make evaluate
make active-learning
make report
make test
```

Small fixture path for fast checks:

```bash
make reproduce-small
```

The small fixture is synthetic and exists only to test code paths. It is not used to claim benchmark performance.

## Project Layout

```text
data/                 raw, processed, external fixtures, and dataset documentation
src/reaction_yield_ml package code
scripts/              executable workflow stages
reports/              metrics, figures, reports, and run logs
tests/                reproducibility and project-check tests
docs/                 model and data cards
notebooks/            walkthrough notebook
```

## Dataset

Primary target dataset: public Buchwald-Hartwig HTE yield data distributed in the IBM rxn_yields repository as `Dreher_and_Doyle_input_data.xlsx`, derived from the Ahneman/Dreher/Doyle high-throughput C-N cross-coupling benchmark.

The workflow records source, citation, access notes, row count, columns, and limitations in:

- `data/DATA_CARD.md`
- `data/dataset_manifest.json`
- `reports/dataset_selection_report.md`
