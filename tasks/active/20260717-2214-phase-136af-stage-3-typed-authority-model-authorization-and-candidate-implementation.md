# Task Contract

## Task ID

20260717-2214-phase-136af-stage-3-typed-authority-model-authorization-and-candidate-implementation

## Title

Phase 136AF: Stage 3 Typed Authority Model Authorization and Candidate Implementation

## Status

active

## Mode

implementation

## Goal

Implement Typed Model Implementation Group 4 (HumanAuthorization, CutoverCandidate, Certification only) per the frozen 136Y plan; frozen, immutable, schema-backed, lossless typed representations only; no authorization/eligibility/certification/persistence/resolution logic.

## Allowed Files

- src/pcae/cltr/authority/authorization_candidate.py
- src/pcae/cltr/authority/__init__.py
- tests/test_cltr_authority_136af_authorization_candidate.py
- tests/test_cltr_authority_136ad_request_readiness.py
- tests/test_cltr_authority_136ae_request_readiness_independent.py
- tests/test_cltr_authority_136ab_authority_core.py
- tests/test_cltr_authority_136ac_authority_core_independent.py
- tests/test_cltr_authority_136z_shared_core.py
- tests/test_cltr_authority_136aa_shared_core_independent.py
- docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_AUTHORIZATION_CANDIDATE_IMPLEMENTATION.md
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

- Exactly three new record-family models implemented: HumanAuthorization, CutoverCandidate, Certification
- No later record-family model (PublicationAttempt/PublicationEvidence/ConcurrencyConflict/RecoveryJournalEntry/NotificationAuthorityBinding/MarkerAuthorityBinding/FinalizationReceiptAuthorityBinding/CompatibilityState/QuarantineRecord) introduced
- No semantic validator, repository, persistence, or authority resolver introduced
- No production runtime import into pcae.cltr.authority
- authority_role 'authoritative' locally forbidden on all three models

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest tests/test_cltr_authority_136af_authorization_candidate.py -v passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-17T22:14:09.272341+02:00
