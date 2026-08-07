# Task Contract

## Task ID

20260807-1254-phase-149o-4-hatp-wave-6-rae-integration

## Title

Phase 149O.4: HATP Wave 6, RAE Integration

## Status

done

## Mode

implementation

## Goal

Wave 6 RAE/HATP integration: gate approval_present on RAE-001 pass AND HATP VALID AND activation readiness (HATP-REQ-095/096/101-104)

## Allowed Files

- src/pcae/core/rollback_approval_evidence.py
- tests/test_phase_149o_4_hatp_rae_integration.py
- tests/test_hatp_verification_engine.py
- tests/test_phase_149o_1j_hatp_verification_engine_independent_verification.py
- docs/PHASE_149O_4_HATP_RAE_INTEGRATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active
- tasks/active/20260807-1254-phase-149o-4-hatp-wave-6-rae-integration.md
- tasks/done/20260807-1254-phase-149o-4-hatp-wave-6-rae-integration.md
- tasks/done/20260807-0814-idle-awaiting-next-governed-phase-post-149o-3.md
- tasks/DONE.md
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

advisory

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

2026-08-07T12:54:14.952797+02:00
