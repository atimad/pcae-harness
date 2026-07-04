# Task Contract

## Task ID

20260704-1929-phase-113x-5-architecture-status-canonicalization

## Title

Phase 113X.5: Architecture Status Canonicalization

## Status

done

## Mode

implementation

## Goal

Repair 113X Finding 4: build_architecture_status()'s _series_label() hardcodes a static, full-scope maturity label per series (e.g. 'Advisory Runtime (Architecture, Contract, Prototype)') regardless of which specific phases within that series have actually completed -- over-claiming completion. Replace with a canonical, evidence-driven derivation: milestone labels computed dynamically from which specific phases have completed (never inferred/extrapolated), completed/in_progress/planned each independently sourced from PROJECT_STATUS.md evidence, deterministic sorting independent of file ordering, and structured phase-ID fields added so consistency validation no longer relies on fragile substring-matching of display labels.

## Allowed Files

- src/pcae/core/phase_reports.py
- tests/test_phase_identity.py
- tests/test_architecture_status_canonicalization.py
- docs/PHASE_113X5_ARCHITECTURE_STATUS_CANONICALIZATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/**

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

- Hardcoded maturity labels (_series_label SERIES_MAP) eliminated
- Architecture Status derived from canonical repository state, never inferred/extrapolated
- Partial completion correctly represented (only-A, A+B, A+B+C progressive cases)
- Impossible combinations prevented/flagged (prototype-planned-while-complete, contract-gap-while-later-complete, execution-available-while-observed)
- Completed/in_progress/planned each independently derived from evidence
- Deterministic derivation (repeated runs over identical state produce identical output, independent of file section ordering)
- Regression tests reproduce and prevent Finding 4
- Execution capability remains unavailable; no Advisory Runtime/Runtime Snapshot/Runtime Context/Runtime Registry/Runtime Inspect/Permission Broker/execution/authorization/plugin/Telegram-inbound/REST/Web UI/Dashboard changes; no changes to Canonical Phase Identity, Finalization Gate, or Mobile Notification Guarantee mechanisms

## Acceptance Checks

- python -m pytest tests/test_architecture_status_canonicalization.py -n auto -q
- python -m pytest tests/test_phase_identity.py tests/test_phase_reports.py tests/test_phase_reports_cli.py -n auto -q
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-04T19:29:34.864315+02:00
