# Task Contract

## Task ID

20260628-1922-90a-permission-broker-enforcement-boundary-design

## Title

90A — Permission Broker Enforcement Boundary Design

## Status

done

## Mode

implementation

## Goal

Design the boundary between the existing permission broker / advisory / shell-gate / dry-run simulation layers and any future enforcement path. Define what the permission broker may decide, what it may not decide, where enforcement boundaries would sit, what inputs/outputs are stable, what audit/rollback/approval evidence is required, and what must remain simulation-only until readiness gates are satisfied.

## Allowed Files

- docs/PHASE_90_PERMISSION_BROKER_ENFORCEMENT_BOUNDARY_DESIGN.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260628-1922-90a-permission-broker-enforcement-boundary-design.md

## Forbidden Files

- src/**
- tests/**
- .githooks/**
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md

## Allowed Zones

- docs
- tasks

## Forbidden Zones

- core
- commands
- cli
- tests
- hooks
- config
- session
- policy
- package
- scripts

## Enforcement Mode

advisory

## Forbidden Changes

- No real enforcement implementation
- No real blocking implementation
- No shell interception
- No shell wrapper installation
- No shell configuration modification
- No command text execution
- No backend invocation
- No prompt sending
- No output capture
- No intake/adoption
- No real authorization
- No persistent advisory/broker/shell-gate/dry-run/enforcement state
- No persistent cache
- No human approval or accepted risk overriding hard blocks
- No advisory, shell-gate, permission-broker, dry-run, audit, approval, readiness, or lifecycle behavior changes
- No full-suite failure repair
- No raw git commit
- No raw git push
- No force push

## Acceptance Criteria

- Boundary design document created (docs/PHASE_90_PERMISSION_BROKER_ENFORCEMENT_BOUNDARY_DESIGN.md)
- Current readiness state recorded
- Known full-suite baseline issue recorded
- 90B repair plan recorded
- Layer responsibilities defined
- Permission broker responsibility defined
- Advisory responsibility defined
- Shell gate responsibility defined
- Dry-run simulation responsibility defined
- Audit responsibility defined
- Rollback responsibility defined
- Approval/risk responsibility defined
- Readiness reporter responsibility defined
- Future enforcement boundary defined
- Broker input model defined
- Broker output model defined
- Hard-block non-overridable model defined
- Human-review model defined
- Accepted-risk model defined
- Operator-approval model defined
- Audit/rollback evidence model defined
- Fail-closed behavior defined
- No-go conditions defined
- No source files changed
- No test files changed
- Fast-green passes
- Final health/check/doctor/task-memory/push clean

## Acceptance Checks

- pcae health
- pcae check
- python -m pytest -m "fast_green" -n auto -ra --durations=100
- pcae doctor task-memory
- pcae doctor test-run --json
- pcae push check
- git status --branch --short
- git log --oneline origin/main..HEAD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-28T19:22:30.596169+02:00
