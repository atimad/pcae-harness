# Task Contract

## Task ID

20260803-2129-phase-149f-repository-wide-mutation-permission-coverage-wave-1-implementation

## Title

Phase 149F: Repository-Wide Mutation Permission Coverage Wave 1 Implementation

## Status

done

## Mode

implementation

## Goal

Implement RWMPC-001 v1.0 Wave 1: broker-wire AG1, AG2, AG4, PH1; canonically route PH2, PH3 through AG2's shared dispatcher; add mutation inventory guard and focused tests

## Allowed Files

- src/pcae/core/mutation_permission.py
- src/pcae/core/agent.py
- src/pcae/commands/phase.py
- tests/test_mutation_permission_core.py
- tests/test_mutation_permission_commit_integration.py
- tests/test_mutation_permission_promotion_integration.py
- tests/test_mutation_permission_push_routing_integration.py
- tests/test_repository_wide_mutation_inventory_guard.py
- tests/test_task_finish_permission_non_interference.py
- tests/test_agent.py
- tests/test_phase.py
- tests/test_permission_broker_observation_verification.py
- tests/test_permission_broker_verification_compatibility.py
- tests/test_phase_148f_permission_broker_production_consumption_independent_verification.py
- tests/test_phase_149d_rwmpc_contract_independent_verification.py
- docs/PHASE_149F_REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_WAVE_1_IMPLEMENTATION.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json

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

strict

## Forbidden Changes

- TBD

## Acceptance Criteria

- AG1, AG2, AG4, PH1 broker-wired; PH2, PH3 routed through AG2's shared dispatcher
- No POL-001..012 change, no POL-013+, no contract amendment
- AG3, AG5, TK1-3 unchanged

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -m fast_green -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-03T21:29:25.909766+02:00
