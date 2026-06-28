# Model Card

## Intended Use

Retrospective public-data benchmark for reaction-yield modeling and existing-record ranking.

## Not Intended For

- Wet-lab protocol generation
- Operational condition recommendation
- Yield guarantees
- New chemistry generation

## Data And Features

- Dataset: Buchwald-Hartwig HTE yield benchmark (Ahneman/Dreher/Doyle lineage)
- Source mode: public benchmark
- Feature family: categorical one-hot component encoding
- Valid splits: Grouped component split, Held-out additive split, Held-out base split, Held-out ligand split, Held-out aryl halide split, Random split
- Primary selection split: Additive held-out grouped split

## Model

- Selected model: Random forest
- Selection split: Additive held-out grouped split

## Metrics

{'mae': 10.7537, 'r2': 0.7262, 'rmse': 14.2371, 'spearman': 0.8597, 'top_10pct_enrichment': 7.3333}

## Limitations

The model uses categorical component labels because component structures are not available in the selected workbook. Interpretability outputs describe model behavior, not chemical causality.
