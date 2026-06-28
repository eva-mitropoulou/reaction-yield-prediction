# Structure-Aware Reaction Extension

This note records the evidence needed before the current component-label benchmark can be extended into a structure-aware reaction model.

## Current Scope

The current project uses public Buchwald-Hartwig HTE component labels and categorical one-hot features. The selected workbook provides component labels, so the public benchmark should be described as reaction-yield ML on public HTE component labels.

## Required Inputs

- Public component-to-SMILES mapping for ligand, additive, base, and aryl halide labels.
- Source and license notes for any external structure mapping.
- A reproducible validation check that every mapped structure corresponds to the intended component label.
- A public artifact that records unmapped, ambiguous, or conflicting component labels.

## Candidate Features

- RDKit molecular descriptors for individual components.
- Morgan fingerprints for individual components.
- Concatenated component descriptors or fingerprints.
- Reaction fingerprints built from mapped reactant and condition components.
- Categorical component-label baseline retained as the reference model.

## Validation Plan

- Keep the existing random split only as a baseline.
- Add leave-one-component-out validation for ligand, additive, base, and aryl halide groups.
- Compare structure-aware features against the current categorical baseline on the same splits.
- Track whether structure-aware features improve out-of-component performance, not just random-split performance.

## Optional Later Work

- Chemprop or reaction-GNN baselines after lightweight RDKit features are reproducible.
- Uncertainty analysis repeated under leave-one-component-out validation.
- Existing-record ranking rerun with structure-aware applicability-domain checks.

## Extension Criteria

Structure-aware claims should wait until the mapped structures, feature pipeline, validation results, and reports are committed.
