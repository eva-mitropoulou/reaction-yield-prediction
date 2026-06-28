# Model Interpretability Report

## Summary

- Primary split: Ligand held-out grouped split
- Highest tree-importance component role: Ligand
- Held-out component role: Ligand
- Held-out split MAE for interpreted model: 4.0137

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

## Interpretation Context

- Importances describe model behavior, not chemical causality.
- One-hot categorical features cannot infer molecular mechanism.
- High-error component groups are anonymized in public reports.
