# Task Contract

## Task ID

20260706-2037-115s-first-advisory-provider-integration-current-acting-model

## Title

115S: First Advisory Provider Integration (Current Acting Model)

## Status

active

## Mode

implementation

## Goal

Integrate the first real (non-mock) AdvisoryProvider using the current acting model as a stateless, one-shot evidence producer for exactly one bounded pilot question (repository consistency review). Reuse 115R's unmodified Normalizer and Evidence Builder. No backend selection, no model configuration, no provider registry, no multi-model mode, no execution capability, no lifecycle integration.

## Allowed Files

- src/pcae/core/current_acting_model_advisory_provider.py
- tests/test_current_acting_model_advisory_provider_115s.py
- docs/PHASE_115S_FIRST_ADVISORY_PROVIDER_INTEGRATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260706-2037-115s-first-advisory-provider-integration-current-acting-model.md

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

- First real Advisory Provider integrated; current acting model used only as advisory evidence producer; pilot limited to repository consistency review; no lifecycle authority; no execution capability; no backend-specific coupling; failure handling safe; evidence remains probabilistic/advisory/model-produced

## Acceptance Checks

- python -m pytest tests/test_current_acting_model_advisory_provider_115s.py tests/test_advisory_repository_skills_prototype_115r.py tests/test_repository_skills.py tests/test_decision_evaluation.py -q -ra

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T20:37:29.666708+02:00
