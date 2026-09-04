# Task Contract

## Task ID

20260904-1243-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-5r-2-1r-1r-2-production-protected-root-protected-presentation-helper-deployment-preparation

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2 — Production Protected-Root / Protected-Presentation Helper Deployment Preparation

## Status

done

## Mode

independent verification

## Goal

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2 — Production Protected-Root / Protected-Presentation Helper Deployment Preparation

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2_F5_DEPLOYMENT_PREPARATION_BLOCKED.md

## Forbidden Files

- src/pcae/**
- scripts/**
- pyproject.toml
- docs/contracts/**


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
- No raw git commit or raw git push; governed PCAE lifecycle only
- No rollback

## Acceptance Criteria

- CPIPC accepts the requested phase identifier.
- Mandatory pre-deployment regressions run before protected host mutation.
- A current blocking regression stops deployment without repair or evasion.
- F-5 host state remains unchanged when a precondition blocks.
- N-16-5 remains NOT CLOSED; runtime/effect/N-16-6/N-16-7 boundaries remain unchanged.

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Outcome

BLOCKED before host mutation by F-6: the completed F-4-IV
`test_43_no_protected_root_mutation_is_in_iv_diff` derives a historical IV fact
from moving `V..HEAD` filenames and rejects this legitimate successor's task
filename. The exact node passes at immutable finalized F-4-IV head `7124c019`
and fails after governed task opening. No protected-root/helper deployment or
administrator interaction occurred; F-5 remains OPEN / UNCHANGED and N-16-5
remains NOT CLOSED.

## Created Timestamp

2026-09-04T12:43:48.343490+02:00
