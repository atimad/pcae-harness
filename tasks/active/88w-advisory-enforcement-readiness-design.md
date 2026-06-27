# Task Contract

## Task ID

20260627-88w-advisory-enforcement-readiness-design

## Title

88W — Advisory Enforcement Readiness Design

## Status

active

## Mode

design

## Goal

Design PCAE's advisory enforcement readiness layer. Define how PCAE can present broker + shell gate decisions as advisory warnings, recommendations, and dry-run enforcement guidance without blocking commands, intercepting shell execution, installing wrappers, mutating shell configuration, invoking backends, or granting real authorization.

This is a design-only phase. No source changes. No test changes. No implementation.

## Allowed Files

- docs/PHASE_88_ADVISORY_ENFORCEMENT_READINESS_DESIGN.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/DONE.md

## Forbidden Files

- src/**
- tests/**
- pyproject.toml
- README.md
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md
- shell wrapper files
- shell config files
- .githooks/**
- backend invocation implementation files
- prompt/capture/intake/adoption implementation files
- generated persistent broker/shell-gate/advisory storage/cache
- Phase 88X task contract
- Phase 88W.1 task contract
- any phase beyond 88W

## Acceptance Criteria

- Advisory enforcement readiness design artifact exists
- Identity block exists with version 0.1, draft_documented, not_started
- All 30 required sections documented
- Advisory mode definition and non-role documented
- Broker, shell gate, hard block, human approval, accepted risk relationships documented
- Secret redaction relationship documented
- Advisory output model and decision vocabulary documented
- Operator workflow documented
- Dry-run/no-execution guarantees documented
- Future CLI sketch documented
- Test requirements and readiness checklist documented
- No source changes, no test changes
- Fast-green passes
- Final health/check/doctor/test-run/push clean

## Acceptance Checks

- python -m pytest -m "fast_green" -n auto -ra --durations=50
- pcae health
- pcae check
- pcae doctor task-memory
- pcae doctor test-run --json
- pcae push check

## Documentation Requirements

- Create docs/PHASE_88_ADVISORY_ENFORCEMENT_READINESS_DESIGN.md
- Update PROJECT_STATUS.md
- Update CHANGELOG.md
- Update tasks/DONE.md

## Created Timestamp

2026-06-27T04:00:00.000000+02:00
