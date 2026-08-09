# Task Contract

## Task ID

20260809-0114-phase-149o-18f-hmrc-assembled-attack-matrix-activation-guard-follow-up

## Title

Phase 149O.18F: HMRC Assembled Attack Matrix + Activation Guard (follow-up)

## Status

done

## Mode

implementation

## Goal

Fix repo-wide raw-constructor/call-site boundary tests tripped by the activation-readiness addition, and repair further stale phase-boundary snapshot assertions (149O.5-F-3) discovered during Fast Green/broad-sweep A/B attribution.

## Allowed Files

- src/pcae/core/hatp_mandatory_cutover.py
- tests/test_hatp_mandatory_activation_guard.py
- tests/test_phase_149o_18f_hmrc_assembled_attack_matrix.py
- tests/test_phase_149o_15_hatp_mandatory_production_consumption_contract_freeze.py
- tests/test_phase_149o_1j_hatp_verification_engine_independent_verification.py
- tests/test_phase_149o_18c_ag3_mandatory_consumption_integration.py
- tests/test_phase_149o_18d_ag5_mandatory_consumption_integration.py
- tests/test_phase_149o_18e_cli_legacy_authority_migration_integration.py
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- docs/PHASE_149O_18F_HMRC_ASSEMBLED_ATTACK_MATRIX_ACTIVATION_GUARD.md
- tasks/done/20260809-0102-idle-awaiting-next-governed-phase-post-149o-18f.md
- tasks/active/20260809-0114-phase-149o-18f-hmrc-assembled-attack-matrix-activation-guard-follow-up.md
- tasks/DONE.md

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

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-09T01:14:56.167423+02:00
