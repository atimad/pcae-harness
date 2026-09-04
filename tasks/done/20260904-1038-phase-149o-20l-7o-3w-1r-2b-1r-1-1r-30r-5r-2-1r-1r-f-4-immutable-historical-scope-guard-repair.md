# Task Contract

## Task ID

20260904-1038-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-5r-2-1r-1r-f-4-immutable-historical-scope-guard-repair

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R — F-4 Immutable Historical-Scope Guard Repair

## Status

done

## Mode

verification-infrastructure repair

## Goal

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R — F-4 Immutable Historical-Scope Guard Repair

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_4r_contract_reconciliation.py
- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_f4_immutable_scope_repair.py
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_F4_IMMUTABLE_HISTORICAL_SCOPE_GUARD_REPAIR.md
- .pcae/phase-completion-metadata.json

## Forbidden Files

- src/pcae/**
- scripts/**
- pyproject.toml
- docs/contracts/**
- /Library/Application Support/PCAE/HPAC/protected-root/**


## Allowed Zones

- tests
- docs
- tasks

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
- No raw commit or push; governed PCAE lifecycle only
- No rollback

## Acceptance Criteria

- F-4 binds the `.30R.4R.1` scope to immutable `a727dbf4..5b6b4013`.
- The exact eight-file historical implementation scope remains enforced.
- Current and future successors cannot alter the historical result.
- No test weakening, production/contract/dependency change, or F-5 mutation.
- N-16-5 remains NOT CLOSED; no human or hardware ceremony occurs.

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- Relevant deterministic no-xdist suites pass with fixed-SHA attribution.

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-04T10:38:55.691206+02:00
