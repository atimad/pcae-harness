# Task Contract

## Task ID

20260717-2105-phase-136ad-stage-3-typed-authority-model-request-and-readiness-implementation

## Title

Phase 136AD: Stage 3 Typed Authority Model Request and Readiness Implementation

## Status

active

## Mode

implementation

## Goal

Implement Typed Model Implementation Group 3 (CutoverRequest, ReadinessPackage only) per the frozen 136Y plan; frozen, immutable, schema-backed, lossless typed representations only; no authorization/readiness/evaluation/persistence/resolution logic.

## Allowed Files

- src/pcae/cltr/authority/request_readiness.py
- src/pcae/cltr/authority/__init__.py
- tests/test_cltr_authority_136ad_request_readiness.py
- tests/test_cltr_authority_136z_shared_core.py
- tests/test_cltr_authority_136aa_shared_core_independent.py
- tests/test_cltr_authority_136ab_authority_core.py
- tests/test_cltr_authority_136ac_authority_core_independent.py
- docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_REQUEST_READINESS_IMPLEMENTATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json

## Forbidden Files

- src/pcae/cltr/authority/authorization_candidate.py
- src/pcae/cltr/authority/publication.py
- src/pcae/cltr/authority/recovery.py
- src/pcae/cltr/authority/bindings.py
- src/pcae/cltr/authority/compatibility_quarantine.py


## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

## Forbidden Changes

- TBD

## Acceptance Criteria

- Exactly two new record-family models implemented: CutoverRequest, ReadinessPackage
- No later record-family model (HumanAuthorization/CutoverCandidate/Certification/PublicationAttempt/PublicationEvidence/ConcurrencyConflict/RecoveryJournalEntry/NotificationAuthorityBinding/MarkerAuthorityBinding/FinalizationReceiptAuthorityBinding/CompatibilityState/QuarantineRecord) introduced
- No semantic validator, repository, persistence, or authority resolver introduced
- No production runtime import into pcae.cltr.authority
- Absent-vs-null preserved distinctly per field, including the one contractually named Sec.6.3 relaxation scoped to CutoverRequest.reason_code only

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest tests/test_cltr_authority_136ad_request_readiness.py -v passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-17T21:05:13.200332+02:00
