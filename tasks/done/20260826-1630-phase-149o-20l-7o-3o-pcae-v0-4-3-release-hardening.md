# Task Contract

## Task ID

20260826-1630-phase-149o-20l-7o-3o-pcae-v0-4-3-release-hardening

## Title

Phase 149O.20L.7O.3O: PCAE v0.4.3 Release Hardening

## Status

done

## Mode

implementation

## Goal

Prepare a frozen, verified v0.4.3 release candidate surfacing the already-computed rollback file plan and divergence evidence in terminal rollback outcomes (observability/debuggability/usability hardening only); no new rollback automation, no Permission Broker change, no publication

## Allowed Files

- pyproject.toml
- src/pcae/__init__.py
- docs/RELEASE_NOTES_V0_4_3.md
- docs/PHASE_149O_20L_7O_3O_PCAE_V0_4_3_RELEASE_HARDENING.md
- README.md
- QUICKSTART_V0_3.md
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/TODO.md
- tasks/DONE.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/20260826-1630-phase-149o-20l-7o-3o-pcae-v0-4-3-release-hardening.md
- tasks/done/20260826-1612-phase-149o-20l-7o-3n-1-mature-capability-consumer-edge-investigation.md
- .pcae/fast-green-attribution/*.json

## Override Protected Files

- pyproject.toml

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

- No new rollback automation, readiness, authority, Permission Broker behavior, or execution capability introduced
- Version bumped 0.4.2 -> 0.4.3 consistently across pyproject.toml and src/pcae/__init__.py
- Release notes and phase document created with required sections, preserving the already-automatic-before-v0.4.3 rollback preparation framing
- Two independent clean-clone builds produce byte-identical wheel/sdist
- Fast Green run with 0 attributable functional regressions
- No tag, no push tag, no GitHub Release, no PyPI upload

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-26T16:30:00.146088+02:00
