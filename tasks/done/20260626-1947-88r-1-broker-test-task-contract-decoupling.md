# Task Contract

## Task ID

20260626-1947-88r-1-broker-test-task-contract-decoupling

## Title

88R.1 — Broker Test Task-Contract Decoupling

## Status

done

## Mode

implementation

## Goal

Repair tests/test_permission_broker.py so tests requiring active-task behavior use an isolated temporary task root instead of live REPO_ROOT. Restore fast-green and quick tier to green.

## Allowed Files

- tests/test_permission_broker.py
- tests/conftest.py
- docs/PHASE_88_BROKER_TEST_TASK_CONTRACT_DECOUPLING.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**
- tasks/DONE.md

## Forbidden Files

- src/pcae/core/permission_broker.py
- src/pcae/core/shell_gate.py
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md
- README.md


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

- tests/test_permission_broker.py passes in idle repo state (no live active task)
- Isolated tmp_task_root fixture exists and used for task-active test groups
- No-active-task blocking tests remain intact
- Broker decision priority unchanged (no source behavior changes)
- No tests deleted, skipped, or xfailed
- Documentation artifact docs/PHASE_88_BROKER_TEST_TASK_CONTRACT_DECOUPLING.md exists
- PROJECT_STATUS.md and CHANGELOG.md updated

## Acceptance Checks

- python -m pytest tests/test_permission_broker.py -q --tb=no -m fast_green
- python -m pytest -m fast_green -n auto --tb=no -q

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-26T19:47:29.550595+02:00
