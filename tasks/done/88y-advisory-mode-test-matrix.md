# Task Contract

## Task ID

20260627-88y-advisory-mode-test-matrix

## Title

88Y — Advisory Mode Test Matrix and CLI Stability Review

## Status

done

## Mode

implementation

## Goal

Harden advisory mode by expanding the advisory command matrix, CLI JSON stability tests, human-readable output tests, redaction regression tests, decision vocabulary tests, false-positive/false-negative review, and broker/shell-gate mapping consistency checks. Fix only narrow advisory defects exposed by these tests.

## Allowed Files

- src/pcae/core/advisory.py (only for narrow defects)
- src/pcae/commands/advisory.py (only for CLI output defects)
- src/pcae/cli.py (only if CLI registration defect)
- tests/test_advisory_mode.py
- docs/PHASE_88_ADVISORY_MODE_TEST_MATRIX.md
- PROJECT_STATUS.md, CHANGELOG.md
- pyproject.toml (only if marker metadata needed)
- tasks/active/**, tasks/DONE.md

## Forbidden Files

- shell/system config files, .githooks/**
- backend/prompt/capture/intake/adoption files
- docs/LINKEDIN_ARTICLE_DRAFT.md, docs/REAL_CAPTURED_TASKS.md
- README.md
- Phase 88Y.1/88Z task contracts

## Acceptance Criteria

- Advisory command matrix expanded
- CLI JSON stability, human-readable output, decision vocabulary reviewed
- Hard-block preservation, secret redaction, broker/shell-gate consistency reviewed
- False positives/false negatives documented
- No enforcement, shell interception, wrappers, backend invocation
- All tiers green
- Documentation artifact exists

## Acceptance Checks

- python -m pytest tests/test_advisory_mode.py -q
- python -m pytest tests/test_permission_broker.py -q
- python -m pytest tests -k "shell_gate" -q
- python -m pytest -m "fast_green" -n auto -ra --durations=100
- python -m pytest -m "not slow and not phase_closure" -n auto
- python -m pytest -n auto -ra --durations=200 (full suite)
- pcae health, check, doctor task-memory, doctor test-run, push check

## Documentation Requirements

- Create docs/PHASE_88_ADVISORY_MODE_TEST_MATRIX.md
- Update PROJECT_STATUS.md, CHANGELOG.md, tasks/DONE.md

## Created Timestamp

2026-06-27T06:30:00.000000+02:00
