# Final Project Report

## 1. Executive Summary

Reaction Yield Prediction from Public HTE Component Labels is a retrospective public-data benchmark for reaction-yield modeling. It covers data curation, categorical component featurization, leakage-aware validation, uncertainty-aware prioritization, active-learning simulation, and existing-record ranking.

Project role: public HTE component-label modeling, retrospective validation, and existing-record ranking.

## 2. Why Reaction-Yield Prediction Matters

Reaction-yield modeling helps evaluate whether machine-learning workflows can learn from historical high-throughput reaction records under validation designs that reflect component generalization rather than only random interpolation.

## 3. Dataset

- Dataset: Buchwald-Hartwig HTE yield benchmark (Ahneman, Dreher, and Doyle lineage)
- Source mode: public benchmark
- Raw row count: 3955
- Clean row count: 3955
- Target: reaction yield percentage
- Components: ligand, additive, base, aryl halide labels

## 4. Cleaning And Standardization

The pipeline standardizes the target as numeric percentage, normalizes component labels as strings, removes impossible target values, and removes exact duplicate component-target records.

## 5. Feature Engineering

- Primary feature family: categorical one-hot component encoding
- Feature count: 44
- Molecular descriptors and fingerprints: skipped because the selected workbook provides labels but no component SMILES
- Leakage audit: yield-derived columns are excluded from predictors

## 6. Validation Strategy

Valid splits: Additive held-out grouped split, Held-out additive split, Held-out base split, Held-out ligand split, Held-out aryl halide split, Random split

The benchmark includes random validation and grouped/out-of-component validation where possible. Out-of-component validation carries the main generalization interpretation.

## 7. Model Benchmark

- Selected model: Random forest
- Primary selection split: Additive held-out grouped split
- MAE: 10.7537
- RMSE: 14.2371
- R2: 0.7262
- Spearman: 0.8597
- Top-10% enrichment: 7.3333

Validation note: In this dataset, the grouped split holds out additive values, so it uses the same held-out group design as Held-out additive split.

## 8. Uncertainty And Calibration

- Method: random-forest ensemble variance plus split conformal interval
- Primary split coverage: 0.7978
- Uncertainty-error Spearman: 0.6296

Uncertainty is evaluated against actual errors and low-confidence predictions are flagged.

## 9. Active-Learning Simulation

The active-learning simulation is a budgeted selection workflow over existing public records. It uses multiple seeds, includes a random baseline, and compares Random selection, Highest predicted yield, Uncertainty sampling, Diversity-aware, Score plus uncertainty, Diverse high-score.

## 10. Existing-Record Ranking

The ranking table contains existing records. It includes predicted yield, confidence/model-agreement diagnostics, domain warnings, and component-diversity score.

## 11. Interpretation Context

- Component structures are unavailable in the selected workbook.
- Categorical features support component-label benchmarking.
- Out-of-component validation is more reliable than random split performance for generalization claims.
- Active-learning curves are retrospective simulations over existing records.
- Existing-record ranking is decision-support analysis.

## 12. Reproducibility

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

Small fixture smoke test:

```bash
make reproduce-small
```

The fixture is synthetic and supports code-path checks.

## 13. Working Summary

This repository keeps a retrospective public-data HTE reaction-yield modeling workflow with reaction cleaning, categorical component featurization, random and out-of-component validation, uncertainty diagnostics, active-learning simulation, and existing-record ranking.
