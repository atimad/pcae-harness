# Task Contract

## Task ID

20260626-1533-88q-shell-gate-test-matrix-and-false-positive-review

## Title

88Q Shell Gate Test Matrix and False-Positive Review

## Status

done

## Mode

implementation

## Goal

Systematically harden the shell gate classifier from 88P by adding a broader command-category matrix, idle-vs-active behavior checks, false-positive review, false-negative review, and specific regressions for compound commands, pipes, tee, redirection chains, backend/network/secret/environment detection, and policy-forbidden file mutations.

## Allowed Files

- src/pcae/core/shell_gate.py
- tests/test_shell_gate_matrix.py
- tests/conftest.py
- docs/PHASE_88_SHELL_GATE_TEST_MATRIX.md
- PROJECT_STATUS.md
- CHANGELOG.md
- pyproject.toml
- tasks/active/**
- tasks/DONE.md

## Forbidden Files

- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md
- README.md


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

- 23 command categories covered or explicitly documented
- Compound command behavior tested
- Pipe/tee write behavior tested
- Backend/secret/environment detection tested
- Performed flags always false
- Classifier-only boundary preserved

## Acceptance Checks

- python -m pytest tests/test_shell_gate_matrix.py tests/test_shell_gate.py -q
- python -m pytest -m fast_green -n auto -q

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-26T15:33:52.938730+02:00
