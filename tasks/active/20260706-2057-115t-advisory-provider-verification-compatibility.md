# Task Contract

## Task ID

20260706-2057-115t-advisory-provider-verification-compatibility

## Title

115T: Advisory Provider Verification & Compatibility

## Status

active

## Mode

implementation

## Goal

Verify 115S's first real Advisory Provider integration is safely contained, behavior-compatible, failure-isolated, and portable to future providers: behavioral containment, pipeline boundaries, failure isolation, nondeterminism containment, backend portability (test-only stand-ins), pilot scope enforcement, no hidden configuration, no execution capability. Verification only -- no new provider implemented.

## Allowed Files

- tests/test_advisory_provider_verification_115t.py
- docs/PHASE_115T_ADVISORY_PROVIDER_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260706-2057-115t-advisory-provider-verification-compatibility.md

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

- Advisory provider containment verified; provider/normalizer/evidence boundaries verified; failure isolation verified; nondeterminism contained; backend portability documented; pilot scope enforced; no hidden config added; execution capability remains unavailable

## Acceptance Checks

- python -m pytest tests/test_advisory_provider_verification_115t.py tests/test_advisory_repository_skills_prototype_115r.py tests/test_current_acting_model_advisory_provider_115s.py -q -ra

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T20:57:28.563329+02:00
