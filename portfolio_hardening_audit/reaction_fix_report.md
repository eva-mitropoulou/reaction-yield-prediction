# Reaction-Yield Hardening Fix Report

Branch: `portfolio-hardening-final`

## Summary

- Replaced synthesis-aware wording with public HTE component-label wording.
- Improved the model card metric formatting.
- Added a structure-aware extension note as future work only.
- Clarified existing-record ranking as retrospective decision-support analysis without operational condition guidance.

## Checks Run

- `make reproduce-small PYTHON=/usr/bin/python3` in a temporary copy: pass.
- `make test PYTHON=/usr/bin/python3` after `make reproduce-small` in the same temporary copy: pass, 8 tests.
- Unsupported-claim keyword scan: pass for public-facing claim terms.
- `git diff --check`: pass.

## Remaining Manual Review

- A plain `make test` on a checkout without generated processed artifacts expects the documented `make reproduce-small` setup path first.
- Manual source-license review remains recommended before redistributing the raw workbook.
