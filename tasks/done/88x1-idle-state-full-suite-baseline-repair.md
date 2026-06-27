# Task Contract

## Task ID

20260627-88x1-idle-state-full-suite-baseline-repair

## Title

88X.1 — Idle-State Full Suite Baseline Repair

## Status

done

## Mode

implementation

## Goal

Make the full suite pass in the normal post-phase idle repository state by decoupling task-active tests from live REPO_ROOT active-task state. Tests requiring active-task behavior must use isolated temp task roots instead of depending on the live repository having an active task contract.

## Allowed Files

- Failing test files (as identified from baseline run)
- tests/conftest.py (if a shared fixture is justified)
- docs/PHASE_88_IDLE_STATE_FULL_SUITE_BASELINE_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/DONE.md

## Forbidden Files

- Production source files (unless genuine non-test defect proven and reported first)
- Advisory feature files (unless directly involved in actual failing test)
- shell wrapper files, shell config files, .githooks/**
- backend/prompt/capture/intake/adoption implementation files
- docs/LINKEDIN_ARTICLE_DRAFT.md, docs/REAL_CAPTURED_TASKS.md
- README.md
- Phase 88Y task contract, test optimization phase task contract

## Acceptance Criteria

- Baseline full-suite failures reproduced and documented
- Failing files identified and root cause confirmed
- Tests requiring task-active behavior use isolated active-task fixture
- Idle/no-task behavior tests remain intact
- No tests deleted, skipped, or xfailed
- Assertions not weakened
- Production source behavior unchanged
- All existing test tiers pass
- Full suite passes in idle repo state
- Documentation artifact exists

## Acceptance Checks

- python -m pytest -n auto -ra --durations=200 (full suite)
- python -m pytest -m "fast_green" -n auto -ra --durations=100
- python -m pytest -m "not slow and not phase_closure" -n auto
- pcae health, check, doctor task-memory, doctor test-run, push check

## Documentation Requirements

- Create docs/PHASE_88_IDLE_STATE_FULL_SUITE_BASELINE_REPAIR.md
- Update PROJECT_STATUS.md, CHANGELOG.md, tasks/DONE.md

## Created Timestamp

2026-06-27T05:30:00.000000+02:00
