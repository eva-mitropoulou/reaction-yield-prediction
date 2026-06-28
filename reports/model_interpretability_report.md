# Model Interpretability Report

## Summary

- Primary split: Additive held-out grouped split
- Highest tree-importance component role: Aryl Halide
- Held-out component role: Additive
- Held-out split MAE for interpreted model: 10.7433

## Included Analyses

- Permutation importance by component role.
- Tree feature importance aggregated by component role.
- Error analysis by anonymized component group.
- Held-out component failure summary.

## Quality Gates

- Permutation importance included: True
- Component contribution summaries included: True
- Feature importance for tree model included: True
- Error analysis by component included: True
- Held out component failure cases summarized: True
- No causality overclaim: True

## Limitations

- Importances describe model behavior, not chemical causality.
- One-hot categorical features cannot infer molecular mechanism.
- High-error component groups are anonymized in public reports.
