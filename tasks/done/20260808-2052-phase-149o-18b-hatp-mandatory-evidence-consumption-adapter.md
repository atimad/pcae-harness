# Task Contract

## Task ID

20260808-2052-phase-149o-18b-hatp-mandatory-evidence-consumption-adapter

## Title

Phase 149O.18B: HATP Mandatory Evidence Consumption Adapter

## Status

done

## Mode

implementation

## Goal

Implement HATP Mandatory Evidence Consumption Adapter (149O.18B): explicit evidence-ID consumption, RAE/HATP-gated approval derivation, truthful PB request construction, typed non-persistent result. No effect, no cutover write, no CLI/agent wiring.

## Allowed Files

- src/pcae/core/hatp_rollback_consumption.py
- tests/test_hatp_rollback_consumption.py
- tests/test_phase_149o_18b_hatp_mandatory_evidence_consumption_adapter.py
- docs/PHASE_149O_18B_HATP_MANDATORY_EVIDENCE_CONSUMPTION_ADAPTER.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/done/20260808-2010-idle-awaiting-next-governed-phase-post-149o-18a.md
- tasks/active/20260808-2052-phase-149o-18b-hatp-mandatory-evidence-consumption-adapter.md
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

2026-08-08T20:52:58.778373+02:00
