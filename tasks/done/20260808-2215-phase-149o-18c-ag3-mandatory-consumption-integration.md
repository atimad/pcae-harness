# Task Contract

## Task ID

20260808-2215-phase-149o-18c-ag3-mandatory-consumption-integration

## Title

Phase 149O.18C: AG3 Mandatory Consumption Integration

## Status

done

## Mode

implementation

## Goal

Phase 149O.18C: AG3 Mandatory Consumption Integration

## Allowed Files

- src/pcae/core/agent.py
- src/pcae/core/hatp_mandatory_cutover.py
- tests/test_hatp_mandatory_cutover.py
- tests/test_ag3_hatp_mandatory_consumption.py
- tests/test_phase_149o_18c_ag3_mandatory_consumption_integration.py
- docs/PHASE_149O_18C_AG3_MANDATORY_CONSUMPTION_INTEGRATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/20260808-2215-phase-149o-18c-ag3-mandatory-consumption-integration.md
- tasks/done/20260808-2215-phase-149o-18c-ag3-mandatory-consumption-integration.md
- tasks/DONE.md
- tasks/done/20260808-2056-idle-awaiting-next-governed-phase-post-149o-18b.md
- tasks/active/20260808-2300-idle-awaiting-next-governed-phase-post-149o-18c.md
- tasks/done/20260808-2300-idle-awaiting-next-governed-phase-post-149o-18c.md

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

2026-08-08T22:15:18.710247+02:00
