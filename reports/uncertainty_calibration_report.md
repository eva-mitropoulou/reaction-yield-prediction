# Uncertainty And Calibration Report

## Summary

- Method: random forest tree ensemble std plus split conformal interval
- Primary split: Grouped component split
- Primary split uncertainty-error Spearman: 0.6296
- Primary split empirical 90% interval coverage: 0.7978
- Primary split low-confidence fraction: 0.2
- Primary split out-of-training-component fraction: 1.0

## Quality Gates

- uncertainty_evaluated_against_actual_errors: True
- empirical_coverage_reported: True
- low_confidence_predictions_flagged: True
- domain_distance_proxy_reported: True

## Limitations

- Tree-ensemble variance is a heuristic uncertainty proxy.
- Conformal intervals are retrospective and depend on calibration residuals from the available public records.
- Uncertainty is evaluated against actual errors but is not claimed to be perfect.
