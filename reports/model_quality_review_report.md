# Model quality review

Status: PASS

This review summarizes the real public Buchwald-Hartwig benchmark rerun. It does not include raw dataset rows, reaction recipes, operational synthesis instructions, or generated chemistry claims.

## Source and integrity

- Source mode: public_benchmark
- Selected sheet: Plates1-3
- Raw rows: 3955
- Clean rows: 3955
- Removed rows: 0
- Missing target rows removed: 0
- Impossible yield rows removed: 0
- Duplicate records removed: 0
- Missing component counts: {'Additive': 0, 'Aryl halide': 0, 'Base': 0, 'Ligand': 0}
- Component cardinalities: {'Additive': 22, 'Aryl halide': 15, 'Base': 3, 'Ligand': 4}

## Target distribution

- Count: 3955
- Min / median / mean / max yield: 0.0000 / 28.7617 / 33.0853 / 100.0000
- Zero-yield records: 236
- Near-zero records, <=1%: 412
- High-yield records, >=80%: 280 (0.0708 fraction)

### Train/test target distribution by split

| Split | Train mean | Test mean | Abs gap | Train std | Test std | Large mean shift |
| --- | --- | --- | --- | --- | --- | --- |
| Random split | 32.9821 | 33.4978 | 0.5157 | 27.1371 | 27.9128 | False |
| Primary grouped split: additive held out | 32.9393 | 33.5806 | 0.6413 | 27.3136 | 27.2242 | False |
| Held-out additive split | 32.9393 | 33.5806 | 0.6413 | 27.3136 | 27.2242 | False |
| Held-out base split | 34.2083 | 30.8357 | 3.3726 | 28.4471 | 24.6714 | False |
| Held-out ligand split | 31.5924 | 37.5624 | 5.9700 | 26.6368 | 28.7180 | True |
| Held-out aryl-halide split | 33.9227 | 29.7355 | 4.1872 | 28.1811 | 23.1097 | False |

## Full model benchmark

The primary selection split is additive-held-out grouped validation. In this dataset, `grouped_high_cardinality_component` and `out_of_additive` use the same held-out additive design, so those two rows are equivalent rather than independent evidence.

| Split family | Split | Model | Train | Test | MAE | RMSE | R2 | Spearman | Top-10 pct enrichment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random | Random split | Mean baseline | 3164 | 791 | 23.7803 | 27.8999 | -0.0003 | NA | 0.9888 |
| random | Random split | One-hot ridge | 3164 | 791 | 11.2112 | 14.1438 | 0.7429 | 0.8711 | 6.3033 |
| random | Random split | One-hot elastic net | 3164 | 791 | 11.5122 | 14.4390 | 0.7321 | 0.8705 | 6.4269 |
| random | Random split | Random forest | 3164 | 791 | 8.9717 | 11.6171 | 0.8266 | 0.9262 | 7.4156 |
| random | Random split | Gradient boosting | 3164 | 791 | 10.6531 | 13.4250 | 0.7684 | 0.9120 | 7.2920 |
| held-out/grouped | Primary grouped split: additive held out | Mean baseline | 3055 | 900 | 22.9984 | 27.2166 | -0.0006 | NA | 0.6667 |
| held-out/grouped | Primary grouped split: additive held out | One-hot ridge | 3055 | 900 | 13.0612 | 16.4078 | 0.6364 | 0.8197 | 6.4444 |
| held-out/grouped | Primary grouped split: additive held out | One-hot elastic net | 3055 | 900 | 13.3276 | 16.5884 | 0.6283 | 0.8194 | 6.7778 |
| held-out/grouped | Primary grouped split: additive held out | Random forest | 3055 | 900 | 10.7537 | 14.2371 | 0.7262 | 0.8597 | 7.3333 |
| held-out/grouped | Primary grouped split: additive held out | Gradient boosting | 3055 | 900 | 12.8921 | 15.9802 | 0.6551 | 0.8421 | 6.8889 |
| held-out/grouped | Held-out additive split | Mean baseline | 3055 | 900 | 22.9984 | 27.2166 | -0.0006 | NA | 0.6667 |
| held-out/grouped | Held-out additive split | One-hot ridge | 3055 | 900 | 13.0612 | 16.4078 | 0.6364 | 0.8197 | 6.4444 |
| held-out/grouped | Held-out additive split | One-hot elastic net | 3055 | 900 | 13.3276 | 16.5884 | 0.6283 | 0.8194 | 6.7778 |
| held-out/grouped | Held-out additive split | Random forest | 3055 | 900 | 10.7537 | 14.2371 | 0.7262 | 0.8597 | 7.3333 |
| held-out/grouped | Held-out additive split | Gradient boosting | 3055 | 900 | 12.8921 | 15.9802 | 0.6551 | 0.8421 | 6.8889 |
| held-out/grouped | Held-out base split | Mean baseline | 2638 | 1317 | 21.2365 | 24.8916 | -0.0187 | NA | 0.6803 |
| held-out/grouped | Held-out base split | One-hot ridge | 2638 | 1317 | 10.3444 | 13.2617 | 0.7108 | 0.8742 | 5.5177 |
| held-out/grouped | Held-out base split | One-hot elastic net | 2638 | 1317 | 10.4689 | 13.3614 | 0.7065 | 0.8735 | 5.5177 |
| held-out/grouped | Held-out base split | Random forest | 2638 | 1317 | 9.4873 | 12.4574 | 0.7449 | 0.8886 | 5.4421 |
| held-out/grouped | Held-out base split | Gradient boosting | 2638 | 1317 | 11.0617 | 14.2150 | 0.6678 | 0.8758 | 5.2154 |
| held-out/grouped | Held-out ligand split | Mean baseline | 2966 | 989 | 25.0174 | 29.3177 | -0.0433 | NA | 1.0091 |
| held-out/grouped | Held-out ligand split | One-hot ridge | 2966 | 989 | 12.5580 | 15.8987 | 0.6932 | 0.8850 | 6.4581 |
| held-out/grouped | Held-out ligand split | One-hot elastic net | 2966 | 989 | 12.9886 | 16.3442 | 0.6758 | 0.8862 | 6.5590 |
| held-out/grouped | Held-out ligand split | Random forest | 2966 | 989 | 10.7548 | 13.8694 | 0.7665 | 0.9419 | 7.3663 |
| held-out/grouped | Held-out ligand split | Gradient boosting | 2966 | 989 | 12.1438 | 15.4146 | 0.7116 | 0.9025 | 6.6599 |
| held-out/grouped | Held-out aryl-halide split | Mean baseline | 3164 | 791 | 19.5146 | 23.4716 | -0.0329 | NA | 0.6180 |
| held-out/grouped | Held-out aryl-halide split | One-hot ridge | 3164 | 791 | 15.8844 | 20.0053 | 0.2497 | 0.5317 | 3.0898 |
| held-out/grouped | Held-out aryl-halide split | One-hot elastic net | 3164 | 791 | 15.8730 | 19.9355 | 0.2549 | 0.5321 | 3.2134 |
| held-out/grouped | Held-out aryl-halide split | Random forest | 3164 | 791 | 15.4660 | 19.9274 | 0.2555 | 0.5791 | 3.3370 |
| held-out/grouped | Held-out aryl-halide split | Gradient boosting | 3164 | 791 | 16.4972 | 20.6033 | 0.2041 | 0.5426 | 3.4606 |

## Random split versus held-out components

Selected model: random_forest

| Held-out split | Random MAE | Held-out MAE | Random RMSE | Held-out RMSE | Random R2 | Held-out R2 | Random much better |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Primary grouped split: additive held out | 8.9717 | 10.7537 | 11.6171 | 14.2371 | 0.8266 | 0.7262 | False |
| Held-out additive split | 8.9717 | 10.7537 | 11.6171 | 14.2371 | 0.8266 | 0.7262 | False |
| Held-out base split | 8.9717 | 9.4873 | 11.6171 | 12.4574 | 0.8266 | 0.7449 | False |
| Held-out ligand split | 8.9717 | 10.7548 | 11.6171 | 13.8694 | 0.8266 | 0.7665 | False |
| Held-out aryl-halide split | 8.9717 | 15.4660 | 11.6171 | 19.9274 | 0.8266 | 0.2555 | True |

Assessment: not random-only, but aryl-halide held-out performance is substantially weaker.

## Baseline improvement on primary split

- Selected model: random_forest
- Primary split: Additive held-out grouped split
- Selected MAE/RMSE: 10.7537 / 14.2371
- Mean baseline MAE/RMSE: 22.9984 / 27.2166
- Absolute MAE/RMSE improvement: 12.2447 / 12.9795
- Relative MAE/RMSE improvement: 0.5324 / 0.4769
- Barely beats baseline: False

## Leakage check

- Feature columns: ['component_ligand', 'component_additive', 'component_base', 'component_aryl_halide']
- Encoder feature names: ['component_ligand', 'component_additive', 'component_base', 'component_aryl_halide']
- Feature count: 44
- Target-like feature columns found: []
- OneHotEncoder handle_unknown: ignore
- Feature quality gates: {'feature_rows_align_clean_rows': True, 'missing_structures_handled_explicitly': True, 'no_target_leakage_in_features': True, 'no_yield_derived_columns_used': True}

## Uncertainty quality

- Primary split: grouped_high_cardinality_component
- Empirical 90% interval coverage: 0.7978
- Coverage gap versus 90%: -0.1022
- Uncertainty-error Spearman: 0.6296
- Low-confidence fraction: 0.2000
- Assessment: useful but undercalibrated

## Active-learning simulation quality

This is a retrospective budgeted selection simulation over existing public records only.

- Final budget: 474
- Seeds: 5
- Random baseline final best-yield mean: 98.7972
- Random baseline approximate 95% CI half-width: 1.0660
- Best strategy by top-yield recovery: component_diverse_high_score
- Best strategy by average selected yield: component_diverse_high_score
- Curve interpretation: final best-yield values saturate for several strategies, so top-yield recovery and average selected yield are more informative

| Strategy | Final best-yield mean | Top-yield recovery | Avg selected yield | Diversity coverage | Beats random top recovery |
| --- | --- | --- | --- | --- | --- |
| component_diverse_high_score | 100.0000 | 0.6762 | 67.9103 | 1.0000 | True |
| diversity_aware_selection | 93.9052 | 0.1081 | 35.9262 | 1.0000 | False |
| exploitation_plus_uncertainty | 100.0000 | 0.5818 | 62.3116 | 1.0000 | True |
| highest_predicted_yield | 100.0000 | 0.6212 | 66.2892 | 1.0000 | True |
| random_selection | 98.7972 | 0.1232 | 32.8094 | 1.0000 | False |
| uncertainty_sampling | 98.8965 | 0.1944 | 35.8786 | 1.0000 | True |

## Artifact consistency

| Artifact | Public source | Real row count | No fixture metrics | Categorical scope |
| --- | --- | --- | --- | --- |
| README.md | True | True | True | True |
| reports/final_project_report.md | True | True | True | True |
| data/DATA_CARD.md | True | True | True | True |
| docs/model_card.md | True | True | True | True |

## Final judgment

PASS: ready for portfolio use with conservative wording. The strongest evidence is the additive-held-out primary split and other held-out component splits where the selected model improves over the mean baseline. The aryl-halide held-out split is the weakest generalization case and should remain visible. The project should be described as a retrospective public-data benchmark using categorical component-label one-hot features, not as structure-aware reaction modeling or operational reaction optimization.
