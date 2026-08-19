# Task Contract

## Task ID

20260819-1005-phase-149o-20l-7o-2f-4-durable-registry-signer-cross-record-consistency-and-toctou-repair

## Title

Phase 149O.20L.7O.2F.4: Durable-Registry Signer Cross-Record Consistency and TOCTOU Repair

## Status

active

## Mode

implementation

## Goal

Repair the Model-B signing consumer so DeploymentBinding, SignerRecord,
PrincipalRecord, HardwareCredentialRecord, repository/root, and provider
relationships fail closed before hardware interaction and are revalidated
before evidence publication, without reopening BF-1/BF-2.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/PHASE_149O_20L_7O_2F_4_DURABLE_REGISTRY_SIGNER_CROSS_RECORD_CONSISTENCY_AND_TOCTOU_REPAIR.md
- docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md
- src/pcae/core/hatp_signing_ceremony.py
- tests/test_phase_149o_20l_7o_2f_4_durable_registry_signer_repair.py
- tests/test_phase_149o_20l_7o_2f_2_hatp_fido2_signing_time_credential_resolution_repair.py
- tests/test_phase_149o_20l_7o_2f_3_independent_verification.py
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- src/pcae/core/hatp_fido2_provider.py
- src/pcae/core/hatp_hardware_credential_admin.py
- src/pcae/core/hatp_principal_signer_admin.py
- src/pcae/core/hatp_deployment_binding_admin.py
- src/pcae/core/hatp_bootstrap.py
- src/pcae/core/human_approval_trusted_provenance.py
- scripts/**


## Allowed Zones

- core
- tests
- docs
- config
- governance
- tasks

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

## Forbidden Changes

- No authenticator discovery or required credential_identity() use
- No resident-credential redesign or signer-selection CLI
- No real hardware provisioning or trust enrollment
- No Dell, Protected Root, HMIC, certification, activation, runtime, Permission Broker, PIV, or Stream-B mutation
- No unrelated repair
- No raw git commit or push, hook bypass, force push, or rollback

## Acceptance Criteria

- Both B-149O.20L.7O.2F.3-1 and B-149O.20L.7O.2F.3-2 fail before hardware touch and publication.
- All contract-required authority relationships are represented in an immutable resolution snapshot and revalidated before publication.
- Material authority-state changes discard the signed candidate and publish nothing.
- Valid coherent non-resident FIDO2 Model-B signing remains functional with no credential_identity() caller.
- Registry state alone cannot create valid signed evidence.
- Fixed-entry/current FAILED/ERROR node-ID delta is independently attributed.
- Canonical phase report records repair pending independent verification.

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- Focused repair tests pass serially
- Surfaces B-E bounded regressions pass
- Affected signing/FIDO2 regressions pass or every failure is attributed
- Fast Green exact-node comparison has no unexplained net-new failure

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-19T10:05:58.544242+02:00
