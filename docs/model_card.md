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
- Source mode: public benchmark
- Raw rows: 3955
- Clean rows: 3955
- Feature family: categorical one-hot component encoding
- Valid splits: Grouped component split, Held-out additive split, Held-out base split, Held-out ligand split, Held-out aryl halide split, Random split
- Primary selection split: Additive held-out grouped split

## Model

- Selected model: Random forest
- Selection split: Additive held-out grouped split

## Metrics

- MAE: 10.7537
- RMSE: 14.2371
- R2: 0.7262
- Spearman: 0.8597
- Top-10% enrichment: 7.3333

## Interpretation Context

The model uses categorical component labels because the selected workbook provides labels rather than component structures. Interpretability outputs describe model behavior for this component-label benchmark.
