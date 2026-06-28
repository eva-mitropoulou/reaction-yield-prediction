# Model Card

## Intended Use

Retrospective public-data benchmark for reaction-yield modeling and existing-record ranking.

## Project Role

- Retrospective public-data benchmark.
- Existing-record ranking and uncertainty diagnostics.
- Component-label modeling with categorical features.
- Structure-aware reaction modeling documented as future work.

## Data And Features

- Dataset: Buchwald-Hartwig HTE yield benchmark (Ahneman/Dreher/Doyle lineage)
- Source mode: fixture
- Feature family: categorical one-hot component encoding
- Valid splits: Grouped component split, Held-out additive split, Held-out base split, Held-out ligand split, Held-out aryl halide split, Random split
- Primary selection split: Ligand held-out grouped split

## Model

- Selected model: Elastic net
- Selection split: Ligand held-out grouped split

## Metrics

- MAE: 2.75
- RMSE: 3.9076
- R2: 0.8472
- Spearman: 0.909
- Top-10% enrichment: 6.9818

## Interpretation Context

The model uses categorical component labels because the selected workbook provides labels rather than component structures. Interpretability outputs describe model behavior for this component-label benchmark.
