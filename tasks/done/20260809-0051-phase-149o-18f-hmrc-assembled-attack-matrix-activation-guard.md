# Task Contract

## Task ID

20260809-0051-phase-149o-18f-hmrc-assembled-attack-matrix-activation-guard

## Title

Phase 149O.18F: HMRC Assembled Attack Matrix + Activation Guard

## Status

done

## Mode

implementation

## Goal

Assemble and attack-harden the HMRC-001 mandatory rollback consumption implementation (Waves A-E): implement the HMRC-REQ-054/055 activation-readiness/activation-guard additions to hatp_mandatory_cutover.py, independently re-extract and mechanically represent all 45 HMRC-001 Sec.29 attacks against the assembled production code, prove zero bypass, prove current POL-005 DENY truthfulness, leave real HATP production activation untouched, and hand off to 149O.19 for independent verification.

## Allowed Files

- src/pcae/core/hatp_mandatory_cutover.py
- tests/test_phase_149o_18a_hatp_mandatory_cutover_state_foundation.py
- tests/test_hatp_mandatory_activation_guard.py
- tests/test_hatp_mandatory_consumption_assembled.py
- tests/test_phase_149o_18f_hmrc_assembled_attack_matrix.py
- docs/PHASE_149O_18F_HMRC_ASSEMBLED_ATTACK_MATRIX_ACTIVATION_GUARD.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/done/20260808-2342-idle-awaiting-next-governed-phase-post-149o-18e.md
- tasks/active/20260809-0051-phase-149o-18f-hmrc-assembled-attack-matrix-activation-guard.md
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

2026-08-09T00:51:26.555906+02:00
