# Task Contract

## Task ID

20260706-2219-115y-advisory-context-package-verification-compatibility

## Title

115Y: Advisory Context Package Verification & Compatibility

## Status

active

## Mode

implementation

## Goal

Verify 115X's AdvisoryContextPackage prototype is deterministic, bounded, prompt-safe, serialization-compatible, and ready to be consumed by the advisory pipeline: determinism, required sections, trust boundaries, prompt-injection boundary, size budgets, redaction/secrets policy, provenance, artifact references, allowed advisory question, JSON compatibility, no hidden integration. Verification only -- no integration added.

## Allowed Files

- tests/test_advisory_context_package_verification_115y.py
- docs/PHASE_115Y_ADVISORY_CONTEXT_PACKAGE_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260706-2219-115y-advisory-context-package-verification-compatibility.md

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

- AdvisoryContextPackage verified deterministic; trust boundaries verified; prompt-injection boundary verified; size/redaction/provenance rules verified; serialization compatibility verified; no hidden integration; execution capability remains unavailable

## Acceptance Checks

- python -m pytest tests/test_advisory_context_package_verification_115y.py tests/test_advisory_context_package.py -q -ra

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T22:19:35.172511+02:00
