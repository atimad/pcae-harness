# Task Contract

## Task ID

20260705-1751-phase-113z-repository-transition-validator-integration-task-finish

## Title

Phase 113Z: Repository Transition Validator Integration: Task Finish

## Status

done

## Mode

implementation

## Goal

Integrate Repository Transition Validator enforcement into pcae task finish --commit only, reusing the phase-complete canonical validation path. Do not integrate push check, notification enforcement, runtime, Permission Broker, REST, or execution.

## Allowed Files

- src/pcae/commands/task.py
- src/pcae/commands/phase.py
- src/pcae/core/repository_transition_validator.py
- src/pcae/core/phase_reports.py
- src/pcae/core/repository_transition_integration.py
- .pcae/phase-completion-metadata.json
- tests/test_repository_transition_validator_task_finish_integration.py
- tests/test_repository_transition_validator_phase_complete_integration.py
- tests/test_task_finish_report_trust_notification.py
- tests/test_task_finish_notification_ordering.py
- tests/test_task.py
- tests/test_phase.py
- tests/test_phase_reports.py
- tests/test_canonical_phase_identity_source_repair.py
- tests/test_phase_report_trust_hard_fail.py
- docs/PHASE_113_REPOSITORY_TRANSITION_VALIDATOR_TASK_FINISH_INTEGRATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active/**

## Forbidden Files

- src/pcae/commands/push.py
- src/pcae/commands/notifications.py
- src/pcae/core/advisory_runtime.py
- src/pcae/core/runtime_snapshot.py
- src/pcae/core/permission_broker.py


## Allowed Zones

- core
- commands
- tests
- docs
- tasks
- config

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

- task finish --commit uses Repository Transition Validator
- task finish --commit cannot bypass canonical validation
- stale metadata cannot overwrite canonical reports
- valid task finish --commit flows remain compatible
- no notification or push-check integration added
- execution capability remains unavailable

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Validation Evidence

- Focused task/phase validator integration and task-finish report suites: 60 passed
- Repository-transition/task/report focused group: 713 passed
- Governance/autonomy/runtime/advisory/plugin group: 3830 passed
- Release/lifecycle regression: 1571 passed
- fast_green: 4390 passed
- pcae health: healthy
- pcae check: passed
- pcae doctor task-memory: clean
- pcae push check: nothing_to_push
- pcae runtime inspect --json: execution unavailable, Observed, observe

## Created Timestamp

2026-07-05T17:51:11.659602+02:00
