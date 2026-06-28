# Feature Engineering Report

## Summary

- Feature family built: categorical baseline one-hot encoding.
- Feature matrix rows: 3955
- Feature matrix columns: 44
- Component roles: Ligand, Additive, Base, Aryl Halide

## Optional Structure Features

- RDKit descriptors: skipped_no_smiles_columns
- Morgan fingerprints: skipped_no_smiles_columns
- Advanced embeddings: skipped_optional_dependencies

## Quality Gates

- No target leakage in features: True
- Feature rows align with cleaned rows: True
- Missing structures handled explicitly: True

## Limitations

- The selected public workbook contains component labels, not component structures.
- Structure-based featurization is therefore limited in this run and is marked as skipped rather than imputed.
