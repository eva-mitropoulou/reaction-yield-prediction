# Data Card

## Dataset

Buchwald-Hartwig HTE yield benchmark (Ahneman/Dreher/Doyle lineage)

## Source

- Repository: https://github.com/rxn4chemistry/rxn_yields
- Raw file URL: https://raw.githubusercontent.com/rxn4chemistry/rxn_yields/master/data/Buchwald-Hartwig/Dreher_and_Doyle_input_data.xlsx
- Selected sheet: Plates1-3
- Source mode: public_benchmark

## Citation

Ahneman, D. T.; Estrada, J. G.; Lin, S.; Dreher, S. D.; Doyle, A. G. Predicting reaction performance in C-N cross-coupling using machine learning. Science 2018, 360, 186-190. DOI: 10.1126/science.aar5169. Public practical source: rxn_yields repository, Buchwald-Hartwig input workbook.

## License And Access

The rxn_yields repository is public and includes a permissive repository license. The workbook is used as a public benchmark source; downstream redistribution should retain the original citation and source notes.

Redistribution note: review_source_license_before_redistributing_raw_workbook.

## Fields

- Row count: 3955
- Raw columns: Ligand, Additive, Base, Aryl halide, Output
- Target column: Output
- Component columns: Ligand, Additive, Base, Aryl halide

## Project Frame

This is a retrospective public-data benchmark for component-label reaction-yield modeling and existing-record ranking.

## Limitations

- Retrospective public-data benchmark.
- The selected workbook provides component labels; structure-aware features require an external public component-to-SMILES mapping.
- The workflow ranks existing public records.
