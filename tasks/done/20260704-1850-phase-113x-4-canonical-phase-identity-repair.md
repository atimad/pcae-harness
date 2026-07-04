# Task Contract

## Task ID

20260704-1850-phase-113x-4-canonical-phase-identity-repair

## Title

Phase 113X.4: Canonical Phase Identity Repair

## Status

done

## Mode

implementation

## Goal

Repair 113X Finding 3 fully: remove regex-derived phase identity from free-text --summary entirely. Canonical phase_id/phase_name/recommended_next_phase must originate from one authoritative source, in precedence order: active task contract, explicit phase-completion metadata, active lifecycle context (PROJECT_STATUS.md current phase, if genuinely in-progress), explicit --phase-id/--phase-name CLI argument. Fail closed (refuse finalization, no report written) if none resolve. Supersedes 113X.2's narrower CLI-vs-metadata conflict check, which is retired since there is no more CLI/summary-derived value to conflict with.

## Allowed Files

- src/pcae/core/phase_reports.py
- src/pcae/commands/phase.py
- src/pcae/cli.py
- tests/test_canonical_phase_identity_repair.py
- tests/test_canonical_phase_identity_source_repair.py
- tests/test_phase_identity.py
- tests/test_finalization_notification_guarantee.py
- docs/PHASE_113X4_CANONICAL_PHASE_IDENTITY_REPAIR.md
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

- No phase identity derived from free text (--summary)
- Canonical source precedence implemented and documented: active task contract > phase-completion metadata > active lifecycle context > explicit CLI argument
- PhaseReport.phase_id, phase_name, and recommended_next_phase originate from the same canonical resolution
- Fail-closed when no source resolves a phase identity
- Regression tests cover the exact forensic scenario (summary mentioning other phases)
- Existing lifecycle commands remain backward compatible
- Execution capability remains unavailable; no Advisory Runtime/Runtime Snapshot/Runtime Context/Runtime Registry/Runtime Inspect/Permission Broker/execution/authorization/plugin/Telegram-inbound/REST/Web UI/Dashboard/Architecture-Status changes

## Acceptance Checks

- python -m pytest tests/test_canonical_phase_identity_source_repair.py -n auto -q
- python -m pytest tests/test_phase_reports.py tests/test_phase_reports_cli.py tests/test_phase_identity.py tests/test_finalization_gate_enforcement.py tests/test_finalization_notification_guarantee.py -n auto -q
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-04T18:50:14.553587+02:00
