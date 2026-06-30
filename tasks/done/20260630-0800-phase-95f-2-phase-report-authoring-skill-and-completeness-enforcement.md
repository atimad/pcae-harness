# Task Contract

## Task ID

20260630-0800-phase-95f-2-phase-report-authoring-skill-and-completeness-enforcement

## Title

Phase 95F.2 — Phase Report Authoring Skill and Completeness Enforcement

## Status

done

## Mode

implementation

## Goal

Phase 95F.2 — Phase Report Authoring Skill and Completeness Enforcement

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/core/phase_reports.py
- tests/test_phase_reports.py
- .pcae/skills/phase-finalization
- docs/PHASE_95F2_PHASE_REPORT_AUTHORING_SKILL_AND_COMPLETENESS_ENFORCEMENT.md

## Forbidden Files

- TBD

## Override Protected Files

- pyproject.toml


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

2026-06-30T08:00:16.426811+02:00
