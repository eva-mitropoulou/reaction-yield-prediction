# Reaction Cleaning Report

## Summary

- Source mode: public_benchmark
- Raw row count: 3955
- Clean row count: 3955
- Missing target rows removed: 0
- Impossible yield rows removed: 0
- Duplicate records removed: 0
- Target: reaction yield percentage
- Component roles: Ligand, Additive, Base, Aryl Halide

## Standardization

- Target yield is numeric percentage.
- Component columns are stripped strings.
- Missing component values are explicitly labeled.
- Duplicate exact component-target records are removed.

## Limitations

- Component strings are standardized as categorical labels; missing chemistry is not invented.
- No component SMILES are available in the selected workbook, so molecular descriptors are skipped unless external structures are supplied.
- Rows outside 0-100 percent yield are excluded rather than clipped.
