# Reaction Yield Prediction from Public HTE Data

This project builds a reaction-yield ML workflow using public Buchwald-Hartwig high-throughput experimentation records. I curated reaction component labels, cleaned yield values, built categorical one-hot features, trained baseline and tree-based models, and then tested whether the models still work when the validation split holds out reaction components instead of only shuffling rows.

The goal is to understand how much signal is available from component labels alone. This version is a categorical component-based benchmark: it uses ligand, additive, base, and aryl-halide labels, not structure-aware reaction descriptors. Structure-aware reaction features are documented as a future extension.

The workflow is supported by several validation, benchmarking, and decision-support layers: dataset selection, reaction cleaning, leakage-aware feature engineering, random and out-of-component splits, model benchmarking, uncertainty calibration, active-learning simulation over existing records, model interpretation, and existing-record ranking.

## Table of Contents

- [At a Glance](#at-a-glance)
- [Project Workflow](#project-workflow)
- [Current Snapshot](#current-snapshot)
- [Selected Model](#selected-model)
- [How To Read This](#how-to-read-this)
- [Scope and Limits](#scope-and-limits)
- [Reproduce](#reproduce)
- [Project Layout](#project-layout)
- [Useful Files](#useful-files)

## At a Glance

| Part | What it does |
|---|---|
| Dataset selection | Uses the public Buchwald-Hartwig HTE yield benchmark from the Ahneman/Dreher/Doyle lineage. |
| Cleaning | Standardizes yield percentages and reaction component labels. |
| Features | Builds categorical one-hot features from component labels. |
| Validation | Compares random validation with grouped and out-of-component splits. |
| Benchmarking | Trains mean, linear, random forest, and gradient boosting baselines. |
| Uncertainty | Checks empirical coverage and uncertainty/error behavior. |
| Active learning | Simulates budgeted selection strategies over existing records. |
| Ranking | Ranks existing public records with prediction and uncertainty context. |

## Project Workflow

The workflow starts from a public Buchwald-Hartwig HTE yield table. The target is reaction yield percentage, and the available component fields are ligand, additive, base, and aryl-halide labels.

Cleaning keeps the task intentionally narrow. The pipeline standardizes the target as a numeric percentage, normalizes component labels as strings, removes impossible target values, and removes exact duplicate component-target records.

Feature engineering is categorical by design. The primary feature family is one-hot encoding over reaction component labels. Molecular descriptors and fingerprints are skipped in this version because the selected workbook provides component labels but not component SMILES, so the benchmark stays honest about what information the model can actually see.

The validation design is the main point of the project. A random split tests interpolation across shuffled records. Grouped and out-of-component splits ask a harder and more useful question: whether a model can still make reasonable predictions when a ligand, additive, base, or aryl halide is held out.

The final workflow adds uncertainty diagnostics, a retrospective active-learning simulation, and an existing-record ranking table. These outputs are used to study model behavior over records already in the dataset, not to claim new experimental outcomes.

## Current Snapshot

| Check | Result |
|---|---:|
| Dataset | Buchwald-Hartwig HTE yield benchmark |
| Source mode | public_benchmark |
| Raw rows | 3,955 |
| Clean rows | 3,955 |
| Feature family | categorical one-hot |
| Feature count | 44 |
| Selected model | random forest |
| Primary split | Additive held-out grouped split |
| MAE | 10.7537 |
| RMSE | 14.2371 |
| R2 | 0.7262 |
| Spearman | 0.8597 |
| Top-10 percent enrichment | 7.3333 |
| Primary split empirical 90 percent coverage | 0.7978 |
| Existing-record ranking rows | 3,955 |
| Active-learning strategies | 6 strategies, 5 seeds |

## Selected Model

The selected model is `random_forest` on the additive held-out grouped split. In this dataset, the grouped split holds out additive values, so it uses the same held-out group design as the held-out additive split.

The model is intentionally simple because the available inputs are component labels. That makes the benchmark easy to audit: it can learn label-level patterns, but it cannot reason about molecular structure beyond what is implicit in the component names.

## How To Read This

Random-split performance is useful, but it is not the main generalization story. Public HTE tables often contain repeated component families, so shuffled rows can make the task easier than a real component-generalization setting.

The grouped and out-of-component splits are the important checks. They test whether the model can make useful predictions when one component family is held out from training.

The uncertainty analysis is diagnostic. It uses random-forest ensemble variance and split conformal intervals to ask whether low-confidence predictions and empirical coverage behave sensibly. On the primary additive-held-out split, the empirical 90 percent interval coverage is 0.7978. It should not be read as a guarantee of experimental uncertainty.

The active-learning simulation is retrospective. It compares selection strategies over records that already exist in the public table, including random selection, highest predicted yield, uncertainty sampling, diversity-aware selection, score plus uncertainty, and diverse high-score.

At the final simulated budget of 474 existing records, the component-diverse high-score strategy has mean best observed yield 100.0 and mean top-yield recovery 0.6762 across 5 seeds. The random baseline has mean best observed yield 98.7972 with an approximate 95 percent CI half-width of 1.066. These are retrospective selection curves over known public records only.

The existing-record ranking table is a decision-support artifact. It organizes known public records by predicted yield, confidence/model-agreement diagnostics, domain warnings, and component diversity.

## Scope and Limits

This is a retrospective public-data benchmark. It does not propose new reactions, generate reactants, or claim prospective experimental validation.

The current feature set is categorical. It does not use reaction SMILES, molecular structures, RDKit descriptors, Morgan fingerprints, graph neural networks, or mechanism-aware chemistry features.

Out-of-component validation carries the main interpretation. Random-split metrics should be read as interpolation evidence, not as proof of broad reaction generalization.

Existing-record ranking and active-learning curves are analysis tools over known records, not experimental recommendations.

## Reproduce

Full workflow:

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
make test
```

The small fixture is synthetic and exists to test code paths.
Fixture-mode outputs are smoke-test artifacts only and are not benchmark results.

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

## Useful Files

- `reports/final_project_report.md`
- `reports/model_benchmark_report.md`
- `reports/validation_design_report.md`
- `reports/uncertainty_calibration_report.md`
- `reports/active_learning_report.md`
- `reports/existing_record_ranking_report.md`
- `data/DATA_CARD.md`
- `docs/model_card.md`
- `docs/STRUCTURE_AWARE_REACTION_EXTENSION.md`

Machine-readable summaries are under `reports/metrics/`.
