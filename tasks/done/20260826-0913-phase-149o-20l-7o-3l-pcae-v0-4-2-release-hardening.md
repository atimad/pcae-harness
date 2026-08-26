# Task Contract

## Task ID

20260826-0913-phase-149o-20l-7o-3l-pcae-v0-4-2-release-hardening

## Title

Phase 149O.20L.7O.3L: PCAE v0.4.2 Release Hardening

## Status

done

## Mode

implementation

## Goal

Prepare a frozen, verified v0.4.2 release candidate (attachment-only RI context in Advisory Mode); no true RI-backed reasoning, no F1 repair, no publication

## Allowed Files

- pyproject.toml
- src/pcae/__init__.py
- docs/RELEASE_NOTES_V0_4_2.md
- docs/PHASE_149O_20L_7O_3L_PCAE_V0_4_2_RELEASE_HARDENING.md
- README.md
- CHANGELOG.md
- PROJECT_STATUS.md
- tasks/TODO.md
- tasks/DONE.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/20260826-0913-phase-149o-20l-7o-3l-pcae-v0-4-2-release-hardening.md
- tasks/done/20260826-0900-phase-149o-20l-7o-3k-post-ri-attachment-architecture-and-release-decision.md

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

- No true RI-backed reasoning implemented; no F1 repair; no AdvisoryProvider modification; no publication (no tag/release/upload)
- Version bumped 0.4.1 -> 0.4.2 consistently across pyproject.toml and src/pcae/__init__.py
- Release notes and phase document created with required sections
- Two independent clean-clone builds produce byte-identical wheel/sdist
- Fast Green run with 0 attributable regressions

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-26T09:13:25.082733+02:00
