# Validation Design Report

## Summary

- Rows available: 288
- Valid split count: 6
- Valid splits: Ligand held-out grouped split, Held-out additive split, Held-out base split, Held-out ligand split, Held-out aryl halide split, Random split

## Split Status

- Random split: valid, train=230, test=58
- Held-out aryl halide split: valid, train=216, test=72, held-out groups omitted
- Held-out ligand split: valid, train=192, test=96, held-out groups omitted
- Held-out base split: valid, train=192, test=96, held-out groups omitted
- Held-out additive split: valid, train=216, test=72, held-out groups omitted
- Ligand held-out grouped split: valid, train=192, test=96, held-out groups omitted

## Split Equivalence Note

In this dataset, the grouped split holds out ligand values, so it uses the same held-out group design as Held-out ligand split.

## Quality Gates

- Random split available: True
- Grouped or out of component available: True
- No group overlap for grouped splits: True
- Split sizes reported: True
- Target distribution reported: True

Held-out group values are not listed to avoid long component lists.
