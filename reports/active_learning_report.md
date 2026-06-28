# Active-Learning Simulation Report

## Summary

- Workflow: retrospective budgeted selection over existing public records.
- Row count: 288
- Strategies: Random selection, Highest predicted yield, Uncertainty sampling, Diversity-aware, Score plus uncertainty, Diverse high-score
- Seed count: 3
- Initial seed size: 24
- Batch size: 24
- Rounds: 4
- Shared initial labeled set per seed: True
- Random baseline final best-yield mean: 84.3333
- Random baseline approximate 95% CI half-width: 5.1027

## Quality Gates

- random_baseline_included: True
- multiple_seeds_used: True
- shared_initial_labeled_set_per_seed: True
- no_future_target_leakage: True
- selected_records_existing_only: True
- limitations_stated: True

## Safety Scope

This is an active-learning simulation over existing dataset records.

## Interpretation Context

- Retrospective active-learning simulation over existing public records only.
- The simulation evaluates budgeted selection over existing records.
- Candidate component labels are known as public records; target yields are revealed only after simulated acquisition.
- All strategies share the same initial labeled set for a given random seed.
