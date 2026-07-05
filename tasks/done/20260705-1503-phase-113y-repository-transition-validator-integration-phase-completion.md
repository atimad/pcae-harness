# Task Contract

## Task ID

20260705-1503-phase-113y-repository-transition-validator-integration-phase-completion

## Title

Phase 113Y: Repository Transition Validator Integration: Phase Completion

## Status

done

## Mode

implementation

## Goal

Implement Repository Transition Validator enforcement for pcae phase complete only. Do not integrate task finish, report promotion outside phase complete, notifications, push check, runtime, Permission Broker, REST, or execution.

## Allowed Files

- src/pcae/commands/phase.py
- src/pcae/core/repository_transition_validator.py
- src/pcae/core/phase_reports.py
- tests/test_repository_transition_validator_phase_complete_integration.py
- tests/test_phase.py
- tests/test_phase_reports.py
- tests/test_task_finish_notification_ordering.py
- tests/test_task_finish_report_trust_notification.py
- docs/PHASE_113_REPOSITORY_TRANSITION_VALIDATOR_PHASE_COMPLETE_INTEGRATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active/**

## Forbidden Files

- src/pcae/commands/task.py
- src/pcae/commands/notifications.py
- src/pcae/commands/push.py
- src/pcae/core/advisory_runtime.py
- src/pcae/core/runtime_snapshot.py
- src/pcae/core/permission_broker.py


## Allowed Zones

- docs
- commands
- tests
- tasks
- config

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

advisory

## Forbidden Changes

- Do not integrate `pcae task finish --commit`.
- Do not integrate `pcae push check`.
- Do not change notification dispatch internals.
- Do not modify Runtime Snapshot, Runtime Inspect, Advisory Runtime, or Permission Broker.
- Do not add execution capability.

## Acceptance Criteria

- Repository Transition Validator is mandatory for pcae phase complete
- Reject blocks canonical phase report promotion
- Quarantine writes quarantine artifacts only
- Human review blocks canonical promotion
- No other lifecycle command is integrated
- Execution capability remains unavailable

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-05T15:03:41.442389+02:00
