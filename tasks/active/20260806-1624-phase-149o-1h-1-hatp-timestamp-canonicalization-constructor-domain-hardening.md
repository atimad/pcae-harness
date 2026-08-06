# Task Contract

## Task ID

20260806-1624-phase-149o-1h-1-hatp-timestamp-canonicalization-constructor-domain-hardening

## Title

Phase 149O.1H.1: HATP Timestamp Canonicalization + Constructor-Domain Hardening

## Status

active

## Mode

implementation

## Goal

Repair Blocking findings B-149O.1H-1 (timestamp canonicalization non-injective) and B-149O.1H-2 (public constructor domain bypasses parser invariants) in the Wave-3 HATP proof models module, narrowly, without implementing Wave 4 or touching Wave 1/2/RAE/Permission Broker/agent/contract files.

## Allowed Files

- src/pcae/core/human_approval_trusted_provenance.py
- tests/test_phase_149o_1h_hatp_proof_models_canonical_serialization_independent_verification.py
- tests/test_phase_149o_1h_1_hatp_timestamp_constructor_domain_hardening.py
- docs/PHASE_149O_1H_1_HATP_TIMESTAMP_CANONICALIZATION_CONSTRUCTOR_DOMAIN_HARDENING.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/*.md
- tasks/done/*.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json

## Forbidden Files

- docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md
- src/pcae/core/repository_identity.py
- src/pcae/core/hatp_bootstrap.py
- src/pcae/core/rollback_approval_evidence.py
- src/pcae/core/permission_broker.py
- src/pcae/core/permission_broker_foundation.py
- src/pcae/core/mutation_permission.py
- src/pcae/core/agent.py
- src/pcae/commands/agent.py


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

- B-149O.1H-1 closed: timestamp canonicalization injective over accepted semantic domain
- B-149O.1H-2 closed: public constructor domain equivalent to or stricter than parser semantic domain
- Wave-3 pre-existing suites (100 tests) pass unchanged
- Fast Green unchanged at 4531 passed

## Acceptance Checks

- python -m pytest tests/test_hatp_proof_models.py tests/test_hatp_canonical_serialization.py tests/test_phase_149o_1g_hatp_proof_models_canonical_serialization.py tests/test_phase_149o_1h_hatp_proof_models_canonical_serialization_independent_verification.py tests/test_phase_149o_1h_1_hatp_timestamp_constructor_domain_hardening.py -q

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-06T16:24:24.686602+02:00
