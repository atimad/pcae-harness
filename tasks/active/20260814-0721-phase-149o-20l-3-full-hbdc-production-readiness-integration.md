# Task Contract

## Task ID

20260814-0721-phase-149o-20l-3-full-hbdc-production-readiness-integration

## Title

Phase 149O.20L.3: Full-HBDC Production Readiness Integration

## Status

active

## Mode

implementation

## Goal

Wire the independently-verified HMRC-001 v1.1 eighth Class-B readiness prerequisite (HMRC-REQ-086-100) into the single existing production readiness assessment path: assess_hatp_mandatory_activation_readiness and the lock-held re-check inside _write_cutover_transition. Call verify_class_b_deployment_conformance(), map only COMPLIANT to satisfied via a pure closed-enum helper, preserve all seven existing checks, remain fail-closed, no caller override, no parallel gate. Update pre-existing current-production readiness tests (not historical-pinned ones) whose live seven-term assertions are now stale, to the new eight-term vector -- never weakening or deleting their original intent. Production integration only -- no HMRC/HMIC/HBDC contract amendment, no Class-B verifier semantic change, no provisioning, no certification/activation, CBV-S10 stays OPEN.

## Allowed Files

- src/pcae/core/hatp_mandatory_cutover.py
- tests/test_phase_149o_20l_3_full_hbdc_production_readiness_integration.py
- tests/test_phase_149o_19_5f_hmic_activation_readiness_integration.py
- tests/test_phase_149o_19_5g_hmic_assembled_attack_matrix_hardening.py
- tests/test_phase_149o_19_hmrc_mandatory_consumption_independent_verification.py
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/*.md
- tasks/done/*.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md

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

- pcae status coherence passes
- pcae health passes
- pcae check passes
- fast_green passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-14T07:21:26.545513+02:00
