# Model Benchmark Report

## Summary

- Models evaluated: Mean baseline, Ridge regression, Elastic net, Random forest, Gradient boosting
- Primary reliability split for model selection: Additive held-out grouped split
- Selected model: Random forest
- Selected model MAE on primary split: 10.7537
- Selected model RMSE on primary split: 14.2371
- Selected model R2 on primary split: 0.7262
- Selected model Spearman correlation on primary split: 0.8597
- Selected model top-10% enrichment on primary split: 7.3333

## Optional Models

- Xgboost: skipped not installed
- Lightgbm: skipped not installed
- Neural Baseline: skipped scope controlled reproducibility

## Quality Gates

- Mean baseline included: True
- Grouped or out of component split included: True
- Random split not sole evidence: True
- Best model selected by reliability split: True
- All metrics saved as json: True

## Interpretation Boundary

Random split performance is not presented as sole evidence. Grouped and out-of-component splits are included where possible. Model selection prioritizes the reliability-oriented grouped split.
In this dataset, the grouped split holds out additive values, so it uses the same held-out group design as Held-out additive split.
