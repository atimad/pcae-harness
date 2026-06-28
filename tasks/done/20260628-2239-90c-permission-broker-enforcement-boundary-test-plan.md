# Task Contract

## Task ID

20260628-2239-90c-permission-broker-enforcement-boundary-test-plan

## Title

90C — Permission Broker Enforcement Boundary Test Plan

## Status

done

## Mode

implementation

## Goal

Create a comprehensive test plan for the permission broker enforcement boundary designed in Phase 90A. Define test categories, fixtures, expected outcomes, and acceptance thresholds. No enforcement implementation.

## Allowed Files

- docs/PHASE_90_PERMISSION_BROKER_ENFORCEMENT_BOUNDARY_TEST_PLAN.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md

## Forbidden Files

- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md
- .githooks/**
- src/**
- tests/**

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

- No enforcement, blocking, shell interception, wrappers, shell config modification
- No command execution, backend invocation, prompt sending, output capture, intake/adoption
- No real authorization, persistent enforcement state, persistent cache
- No source or test file changes
- No raw git commit, raw git push, force push, --no-verify
- No starting 91A

## Acceptance Criteria

- Test plan document created covering all 12 sections
- Broker input/output model tests defined
- Hard-block invariant tests defined
- Human review and accepted-risk tests defined
- Fail-closed behavior tests defined
- Audit evidence tests defined
- Fixture strategy defined
- CLI test strategy defined
- Roadmap relationship documented
- No-go conditions stated
- Fast-green passes

## Acceptance Checks

- pcae health
- pcae check
- python -m pytest -m "fast_green" -n auto -ra --durations=100
- pcae doctor task-memory
- pcae push check
- git status --branch --short

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-28T22:39:50.844268+02:00
