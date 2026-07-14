# Task Contract

## Task ID

20260714-1956-phase-135s-atomic-publication-rehearsal-implementation

## Title

Phase 135S: Atomic Publication Rehearsal Implementation

## Status

done

## Mode

implementation

## Goal

Implement Stage 2 (Atomic Publication Rehearsal, Legacy Authority) per the 135Q contract as verified by 135R

## Allowed Files

- src/pcae/cltr/migration/rehearsal/*.py
- src/pcae/cltr/migration/*.py
- src/pcae/cltr/*.py
- src/pcae/core/finalization_transaction.py
- src/pcae/commands/cltr_migration.py
- src/pcae/cli.py
- tests/test_cltr_rehearsal_*.py
- tests/test_cltr_migration_*.py
- tests/conftest.py
- docs/PHASE_135_ATOMIC_PUBLICATION_REHEARSAL_IMPLEMENTATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/*.md
- tasks/done/*.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json

## Forbidden Files

- TBD


## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- Legacy lifecycle remains sole production authority; Stage 2 rehearsal generation and pointer remain non-authoritative
- F-135P-1, F-135P-3, F-135P-4, and EXPECTED_REPRESENTATION_DIFFERENCE half of F-135P-2 resolved with regression tests
- No production pointer, marker, receipt, or notification dispatch touched by Stage 2 code

## Acceptance Checks

- python -m pytest tests/ -k cltr -q
- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-14T19:56:19.133939+02:00
