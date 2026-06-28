# Task Contract

## Task ID

20260628-2259-91a-permission-broker-simulation-prototype

## Title

91A — Permission Broker Simulation Prototype

## Status

done

## Mode

implementation

## Goal

Implement a simulation-only permission broker prototype that evaluates proposed governed actions and returns structured decisions (allow, deny, human_review, more_evidence) with hard_block, reason codes, messages, and audit payloads. No enforcement, shell interception, wrappers, backend invocation, or command execution.

## Allowed Files

- src/pcae/core/permission_broker.py
- tests/test_permission_broker.py
- docs/PHASE_91_PERMISSION_BROKER_SIMULATION_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md

## Forbidden Files

- .githooks/**
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md
- src/pcae/core/enforcement_*.py (no enforcement changes)
- src/pcae/core/shell_gate.py (no shell gate changes)

## Allowed Zones

- core
- tests
- docs
- tasks

## Forbidden Zones

- commands
- cli
- hooks
- config
- session
- policy
- package
- scripts

## Enforcement Mode

advisory

## Forbidden Changes

- No shell interception, wrappers, shell config modification
- No command execution, backend invocation, prompt sending, output capture, intake/adoption
- No real enforcement, real blocking
- No real authorization
- No Telegram inbound control
- No weakening tests
- No raw git commit, raw git push, force push, --no-verify
- No starting 91B
- Human approval + accepted risk must never override hard blocks

## Acceptance Criteria

- evaluate_permission_broker() function implemented with 4-outcome decision model
- All hard-block categories covered (12 minimum)
- Hard-block non-overridability invariant preserved
- Fail-closed behavior for malformed/missing inputs
- Audit payload for every decision
- Reason codes for every decision
- Comprehensive tests covering all outcomes and invariants
- Documentation artifact created
- Fast-green passes
- Existing broker (build_permission_broker) unchanged

## Acceptance Checks

- pcae health
- pcae check
- python -m pytest tests/test_permission_broker.py -q -ra --durations=100
- python -m pytest -m "fast_green" -n auto -ra --durations=100
- pcae doctor task-memory
- pcae push check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-28T22:59:42.311416+02:00
