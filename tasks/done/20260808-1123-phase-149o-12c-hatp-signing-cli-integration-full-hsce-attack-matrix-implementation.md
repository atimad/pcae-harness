# Task Contract

## Task ID

20260808-1123-phase-149o-12c-hatp-signing-cli-integration-full-hsce-attack-matrix-implementation

## Title

Phase 149O.12C: HATP Signing CLI Integration + Full HSCE Attack-Matrix Implementation

## Status

done

## Mode

implementation

## Goal

Phase 149O.12C: HATP Signing CLI Integration + Full HSCE Attack-Matrix Implementation

## Allowed Files

- src/pcae/commands/hatp.py
- src/pcae/cli.py
- tests/test_hatp_cli.py
- tests/test_phase_149o_12c_hsce_attack_matrix.py
- tests/test_phase_149o_12b_hatp_signing_ceremony_implementation.py
- tests/test_phase_149o_12a_signed_evidence_model_store_implementation.py
- tests/test_phase_149o_8_hatp_ag3_ag5_production_consumption_signing_ceremony_architecture.py
- tests/test_phase_149o_9_hatp_signing_ceremony_evidence_store_contract_freeze.py
- tests/conftest.py
- docs/PHASE_149O_12C_HATP_SIGNING_CLI_INTEGRATION_FULL_HSCE_ATTACK_MATRIX_IMPLEMENTATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/done/20260808-0948-idle-awaiting-next-governed-phase-post-149o-12b.md
- tasks/active/20260808-1123-phase-149o-12c-hatp-signing-cli-integration-full-hsce-attack-matrix-implementation.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- TBD


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

- No runtime invocation
- No prompt execution
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No commit
- No push
- No rollback

## Acceptance Criteria

- TBD

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-08T11:23:00.301466+02:00
