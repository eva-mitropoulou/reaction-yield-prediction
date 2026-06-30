# Validation Design Report

## Summary

- Rows available: 3955
- Valid split count: 6
- Valid splits: Additive held-out grouped split, Held-out additive split, Held-out base split, Held-out ligand split, Held-out aryl halide split, Random split

## Split Status

- Random split: valid, train=3164, test=791
- Held-out aryl halide split: valid, train=3164, test=791, held-out groups omitted
- Held-out ligand split: valid, train=2966, test=989, held-out groups omitted
- Held-out base split: valid, train=2638, test=1317, held-out groups omitted
- Held-out additive split: valid, train=3055, test=900, held-out groups omitted
- Additive held-out grouped split: valid, train=3055, test=900, held-out groups omitted

## Split Equivalence Note

In this dataset, the grouped split holds out additive values, so it uses the same held-out group design as Held-out additive split.

## Quality Gates

- Random split available: True
- Grouped or out of component available: True
- No group overlap for grouped splits: True
- Split sizes reported: True
- Target distribution reported: True

Held-out group values are not listed to avoid long component lists.
