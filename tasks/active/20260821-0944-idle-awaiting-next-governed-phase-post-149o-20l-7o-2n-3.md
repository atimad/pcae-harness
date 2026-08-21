# Task Contract

## Task ID

20260821-0944-idle-awaiting-next-governed-phase-post-149o-20l-7o-2n-3

## Title

Idle: awaiting next governed phase (post-149O.20L.7O.2N.3)

## Status

active

## Mode

documentation

## Goal

Idle: awaiting next governed phase (post-149O.20L.7O.2N.3)

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/authority-evaluation/records/pointers/prp-930a0c3f49b045ea8c5ae45f88585d33.json
- .pcae/authority-evaluation/records/records/prp-930a0c3f49b045ea8c5ae45f88585d33*
- .pcae/decision-sessions/CDS-905edcf1-58b0-40e5-8459-59c41464076a.json
- .pcae/decision-sessions/orchestration/CDS-905edcf1-58b0-40e5-8459-59c41464076a.json
- .pcae/decision-sessions/pending-packages/consumed/prp-930a0c3f49b045ea8c5ae45f88585d33.json
- .pcae/publication-execution/attempts/pubexec-6059a395e91a43dba5b58521288777e5.json
- .pcae/publication-execution/published/prp-930a0c3f49b045ea8c5ae45f88585d33.json
- .pcae/publication-execution/records/chgr-e0dfb3e752e6430089ca1ee02636ec7e.json
- .pcae/publication-execution/records/chgrconf-5bbbb20b59874bf186f45598d0e77f8e.json
- .pcae/publication-execution/records/chgrintg-dd83c5ac92074ffba0c986f48293afcb.json
- .pcae/publication-execution/records/chgrprov-3643c543e7bc46bfada47b95ebb49047.json

## Forbidden Files

- TBD


## Allowed Zones

- config
- tasks
- docs

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

2026-08-21T09:44:00.509054+02:00
