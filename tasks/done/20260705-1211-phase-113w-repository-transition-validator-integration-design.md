# Task Contract

## Task ID

20260705-1211-phase-113w-repository-transition-validator-integration-design

## Title

Phase 113W: Repository Transition Validator Integration Design

## Status

done

## Mode

implementation

## Goal

Design how the Repository Transition Validator will integrate into PCAE
lifecycle commands so inconsistent agents can propose work but cannot make
invalid repository state canonical. Design only; no integration
implementation.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/PCAE_REPOSITORY_TRANSITION_VALIDATOR_INTEGRATION.md
- docs/PHASE_113_REPOSITORY_TRANSITION_VALIDATOR_INTEGRATION_DESIGN.md
- tests/test_repository_transition_validator_integration_design.py
- tests/test_bootstrap_todo_consistency.py
- tests/test_rc_audit_findings_repair.py
- .pcae/phase-completion-metadata.json

## Forbidden Files

- src/**


## Allowed Zones

- docs
- tests
- tasks
- config

## Forbidden Zones

- TBD

## Allowed Dependencies

- tests -> docs
- tests -> cli
- tests -> commands
- tests -> core
- tasks -> docs

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

## Forbidden Changes

- No runtime invocation
- No prompt execution
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No raw git commit
- No raw git push
- No rollback
- No lifecycle command behavior changes
- No Advisory Runtime changes
- No execution, authorization, Permission Broker enforcement, plugin,
  Telegram inbound, REST, Web UI, or Dashboard implementation

## Acceptance Criteria

- Integration design complete
- DeepSeek containment scenarios documented
- Canonical promotion path designed with no alternate promotion path
- Implementation order defined
- No integration implemented
- Execution capability remains unavailable
- Focused, governance/autonomy, release/lifecycle, fast_green, and full-suite
  validation results recorded in the phase report

## Acceptance Checks

- pcae health
- pcae check
- pcae doctor task-memory
- python -m pytest tests/test_repository_transition_validator_integration_design.py -q
- pcae push check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-05T12:11:00.027893+02:00
