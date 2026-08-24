# Task Contract

## Task ID

20260824-1140-phase-149o-20l-7o-2v-1-v0-3-0-final-release-preparation

## Title

Phase 149O.20L.7O.2V.1: v0.3.0 final release preparation

## Status

active

## Mode

documentation

## Goal

Transition v0.3.0-rc1 to stable v0.3.0: version/doc consistency, clean build, ALLOW/DENY/quickstart re-verification, freeze candidate SHA, stop for publication authorization

## Allowed Files

- README.md
- CHANGELOG.md
- pyproject.toml
- src/pcae/__init__.py
- PROJECT_STATUS.md
- docs/QUICKSTART_V0_3.md
- docs/RELEASE_NOTES_V0_3_0.md
- docs/RELEASE_NOTES_V0_3_0_RC1.md
- docs/PHASE_149O_20L_7O_2V_1_V0_3_0_FINAL_RELEASE_PREPARATION.md
- tasks/active/20260824-0919-idle-awaiting-next-governed-phase-post-149o-20l-7o-2v.md
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

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- Stable version metadata consistent
- Zero attributable regressions
- Clean wheel/sdist build and install verified

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-24T11:40:02.674641+02:00
