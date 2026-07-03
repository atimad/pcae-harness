# Task Contract

## Task ID

20260703-2220-fix-112b-contract-test-false-positive-after-task-archival

## Title

Fix 112B contract test false positive after task archival

## Status

done

## Mode

implementation

## Goal

Fix test_task_contract_excludes_src_pcae to check only the Allowed Files section of the archived task contract, not the whole document -- the acceptance criterion text 'No file under src/pcae/ touched' created a false-positive substring match once the 112B task contract was moved to tasks/done/.

## Allowed Files

- tests/test_runtime_context_contract.py
- tasks/active/**
- tasks/DONE.md
- CHANGELOG.md

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

- TBD

## Acceptance Checks

- python -m pytest tests/test_runtime_context_contract.py -q

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-03T22:20:36.952296+02:00
