# Task Contract

## Task ID

20260706-2149-115x-advisory-context-package-prototype

## Title

115X: Advisory Context Package Prototype

## Status

active

## Mode

implementation

## Goal

Implement the AdvisoryContextPackage runtime object exactly as frozen in 115W: package object, validation, serialization, trust-boundary markers, size budgets, provenance, artifact references, redaction summary. No integration with Advisory Provider runtime, Repository Skills, Evidence Providers, Decision Evaluation, Repository Transition Validator, or lifecycle commands.

## Allowed Files

- src/pcae/core/advisory_context_package.py
- tests/test_advisory_context_package.py
- tests/test_phase_115v_advisory_evidence_enrichment_architecture.py
- tests/test_phase_115w_advisory_context_package_contract.py
- docs/PHASE_115X_ADVISORY_CONTEXT_PACKAGE_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260706-2149-115x-advisory-context-package-prototype.md

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

- AdvisoryContextPackage runtime implemented; trust boundaries represented; prompt-injection boundary represented; size/redaction/provenance rules enforced; serialization implemented; no provider/model/lifecycle integration; execution capability remains unavailable

## Acceptance Checks

- python -m pytest tests/test_advisory_context_package.py tests/test_phase_115w_advisory_context_package_contract.py tests/test_repository_skills.py tests/test_decision_evaluation.py -q -ra

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T21:49:11.430576+02:00
