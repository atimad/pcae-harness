# Task Contract

## Task ID

20260824-2310-phase-149o-20l-7o-2z-post-v0-3-1-release-candidate-final-verification

## Title

Phase 149O.20L.7O.2Z: Post-v0.3.1 Release Candidate Final Verification

## Status

done

## Mode

validation

## Goal

Prepare and independently verify the v0.3.1 release candidate from a fixed committed tree; version bump, packaged artifact build/checksum/install verification, documentation truth, regression baseline, publication checklist. No publication. Includes one narrow bounded repair: extend the 2Y malformed-agent-lock fail-closed handling to cover well-formed-JSON-but-wrong-type lock payloads (AgentLock.agent_id property + derive_producer_provenance), independently found during release-candidate verification to crash pcae intake from-files and pcae session bootstrap.

## Allowed Files

- pyproject.toml
- src/pcae/__init__.py
- src/pcae/core/intake.py
- src/pcae/core/agent.py
- README.md
- docs/QUICKSTART_V0_3.md
- docs/RELEASE_NOTES_V0_3_1.md
- docs/PHASE_149O_20L_7O_2Z_RELEASE_CANDIDATE_FINAL_VERIFICATION.md
- tests/test_phase_149o_20l_7o_2z_release_candidate.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

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

2026-08-24T23:10:05.695193+02:00
