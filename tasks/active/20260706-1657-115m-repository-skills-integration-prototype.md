# Task Contract

## Task ID

20260706-1657-115m-repository-skills-integration-prototype

## Title

115M: Repository Skills Integration Prototype

## Status

active

## Mode

implementation

## Goal

Add a narrowly scoped Repository Skills evidence-acquisition adapter (Stage 3 of 115L's frozen migration strategy) that produces an EvidenceCollection equivalent to the existing Evidence Provider path, without changing Decision Evaluation, the Repository Transition Validator, or any lifecycle command behavior. Preserve the old provider path unmodified; prove evidence/decision/validator equivalence with tests.

## Allowed Files

- src/pcae/core/repository_skills_integration.py
- tests/test_repository_skills_integration_115m.py
- tests/test_phase_115l_repository_skills_integration_design.py
- docs/PHASE_115M_REPOSITORY_SKILLS_INTEGRATION_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260706-1657-115m-repository-skills-integration-prototype.md

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

- Repository Skills can produce the evidence used by Decision Evaluation; old Evidence Provider path remains available; skill path and provider path are equivalent; Decision Evaluation results unchanged; Repository Transition Validator verdicts unchanged; no lifecycle behavior change; no AI/SLM/DeepSeek integration; execution capability remains unavailable

## Acceptance Checks

- python -m pytest tests/test_repository_skills_integration_115m.py tests/test_repository_skills.py tests/test_repository_skills_verification_115k.py tests/test_decision_evaluation.py tests/test_repository_transition_validator.py -q -ra

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T16:57:40.161080+02:00
