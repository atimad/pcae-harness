# Task Contract

## Task ID

20260705-1847-phase-114a-canonical-artifact-promotion-quarantine-hardening

## Title

Phase 114A: Canonical Artifact Promotion & Quarantine Hardening

## Status

done

## Mode

implementation

## Goal

Implement a reusable canonical artifact promotion pipeline for phase reports only, preserving accepted lifecycle behavior and preventing rejected/quarantined artifacts from becoming latest canonical artifacts.

## Allowed Files

- src/pcae/core/canonical_artifact_promotion.py
- src/pcae/core/phase_reports.py
- src/pcae/core/repository_transition_validator.py
- src/pcae/core/repository_transition_integration.py
- src/pcae/commands/phase.py
- src/pcae/commands/task.py
- tests/test_canonical_artifact_promotion.py
- tests/test_phase_reports.py
- tests/test_phase_reports_cli.py
- tests/test_repository_transition_validator_phase_complete_integration.py
- tests/test_repository_transition_validator_task_finish_integration.py
- tests/test_task_finish_notification_ordering.py
- docs/PCAE_CANONICAL_ARTIFACT_PROMOTION.md
- docs/PHASE_114_CANONICAL_ARTIFACT_PROMOTION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active/**
- .pcae/phase-completion-metadata.json

## Forbidden Files

- src/pcae/commands/push.py
- src/pcae/commands/notifications.py
- src/pcae/core/runtime_snapshot.py
- src/pcae/core/permission_broker.py
- src/pcae/core/advisory_runtime.py


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

- Canonical artifact promotion implemented for phase reports
- Only Certified artifacts become canonical
- Rejected and quarantined artifacts never promote
- Successful lifecycle behavior remains compatible
- Reusable future artifact promotion structure exists
- Execution capability remains unavailable

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Validation Evidence

- Focused promotion/report compatibility: 172 passed
- Phase lifecycle/report suite: 1039 passed
- Governance/autonomy/runtime/advisory/plugin group: 3830 passed
- Release/lifecycle regression: 1571 passed
- fast_green: 4390 passed
- pcae health: healthy
- pcae check: passed
- pcae doctor task-memory: clean
- pcae push check: nothing_to_push
- pcae runtime inspect --json: execution unavailable, Observed, observe

## Created Timestamp

2026-07-05T18:47:12.628119+02:00
