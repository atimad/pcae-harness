# Task Contract

## Task ID

20260706-1209-115g-repository-decision-evaluation-verification-compatibility

## Title

115G: Repository Decision Evaluation Verification & Compatibility

## Status

active

## Mode

implementation

## Goal

Verify 115F's Repository Decision Evaluation integration is fully behavior-preserving, deterministic, reproducible, and compatible with existing Repository Transition Validator behavior via focused compatibility tests and full regression; no architectural redesign, no new runtime capability, no new Repository Skills, no execution capability, no lifecycle behavior changes.

## Allowed Files

- tests/test_repository_transition_validator_verification_115g.py
- docs/PHASE_115G_DECISION_EVALUATION_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260706-1209-115g-repository-decision-evaluation-verification-compatibility.md

## Forbidden Files

- TBD


## Allowed Zones

- core
- docs
- tests
- tasks

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

- Validator verdicts unchanged; decision explanations verified (valid Evidence IDs, correct bucketing); determinism verified; evidence integrity verified (unique IDs, no dangling refs, UNKNOWN never silently ignored); lifecycle compatibility verified; backward compatibility verified; no hidden dependencies; execution capability remains unavailable

## Acceptance Checks

- python -m pytest tests/test_repository_transition_validator_verification_115g.py tests/test_decision_evaluation.py tests/test_repository_transition_validator*.py -n auto -q -ra --durations=100

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T12:09:16.282088+02:00
