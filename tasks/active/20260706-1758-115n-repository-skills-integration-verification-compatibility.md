# Task Contract

## Task ID

20260706-1758-115n-repository-skills-integration-verification-compatibility

## Title

115N: Repository Skills Integration Verification & Compatibility

## Status

active

## Mode

implementation

## Goal

Verify that 115M's Repository Skills integration is fully behavior-preserving: evidence equivalence per skill, Decision Evaluation compatibility, Repository Transition Validator compatibility, lifecycle compatibility, registry determinism, compatibility path, isolation, AI boundary, execution boundary. Classify the 115M fast_green discrepancy (test_dry_run_simulation.py::test_pytest_dry_run_not_blocked). Verification only -- no Repository Skill, Evidence Provider, Decision Evaluation, Repository Transition Validator, lifecycle command, Notification Policy, Canonical Artifact Promotion, Push-State Reconciliation, or Post-Push Canonicalization modified.

## Allowed Files

- tests/test_repository_skills_integration_verification_115n.py
- docs/PHASE_115N_REPOSITORY_SKILLS_INTEGRATION_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260706-1758-115n-repository-skills-integration-verification-compatibility.md

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

- Repository Skills path verified equivalent to provider path; Decision Evaluation unchanged; Transition Validator unchanged; lifecycle unchanged; registry deterministic; old compatibility path preserved; AI boundary verified; execution capability remains unavailable; fast_green discrepancy classified

## Acceptance Checks

- python -m pytest tests/test_repository_skills_integration_verification_115n.py tests/test_repository_skills_integration_115m.py tests/test_repository_skills.py tests/test_repository_transition_validator.py -q -ra

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T17:58:21.807540+02:00
