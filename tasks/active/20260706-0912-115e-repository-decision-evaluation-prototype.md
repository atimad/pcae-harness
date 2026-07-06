# Task Contract

## Task ID

20260706-0912-115e-repository-decision-evaluation-prototype

## Title

115E: Repository Decision Evaluation Prototype

## Status

active

## Mode

implementation

## Goal

Implement the deterministic Repository Decision Evaluation pipeline: EvaluationContext, InvariantResult, EvaluationResult, and six evidence-only invariant families. Not validator/lifecycle integration.

## Allowed Files

- src/pcae/core/decision_evaluation.py
- tests/test_decision_evaluation.py
- docs/PHASE_115E_REPOSITORY_DECISION_EVALUATION_PROTOTYPE.md
- tasks/active/20260706-0912-115e-repository-decision-evaluation-prototype.md

## Forbidden Files

- TBD


## Allowed Zones

- core
- docs
- tests
- tasks

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

- EvaluationContext/InvariantResult/EvaluationResult implemented; deterministic evidence-only invariant evaluation; UNKNOWN never silently passes; conflicting evidence preserved; no validator/lifecycle integration

## Acceptance Checks

- python -m pytest tests/test_decision_evaluation.py -n auto -q -ra --durations=100

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T09:12:06.435149+02:00
