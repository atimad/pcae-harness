# Task Contract

## Task ID

20260706-2137-115w-advisory-context-package-contract

## Title

115W: Advisory Context Package Contract

## Status

done

## Mode

implementation

## Goal

Freeze the AdvisoryContextPackage contract: 15 required sections, four trust-boundary classes, the prompt-injection boundary, size limits, redaction/secrets policy, provenance rules, the artifact-reference model, and the one allowed advisory question. Contract/design only -- no AdvisoryContextPackage runtime implemented.

## Allowed Files

- docs/PCAE_ADVISORY_CONTEXT_PACKAGE_CONTRACT.md
- docs/PHASE_115W_ADVISORY_CONTEXT_PACKAGE_CONTRACT.md
- tests/test_phase_115w_advisory_context_package_contract.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260706-2137-115w-advisory-context-package-contract.md

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

- Advisory Context Package contract frozen; trust boundaries frozen; prompt-injection boundary frozen; size/redaction/provenance rules frozen; allowed advisory question frozen; no implementation added; execution capability remains unavailable

## Acceptance Checks

- python -m pytest tests/test_phase_115w_advisory_context_package_contract.py tests/test_phase_115v_advisory_evidence_enrichment_architecture.py tests/test_phase_115q_advisory_repository_skills_contract_freeze.py -q -ra

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T21:37:45.459265+02:00
