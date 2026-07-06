# Task Contract

## Task ID

20260706-2113-115u-advisory-provider-strategy-extension-point-review

## Title

115U: Advisory Provider Strategy & Extension Point Review

## Status

active

## Mode

implementation

## Goal

Decide whether PCAE needs a second advisory provider now while preserving the ability to add one later without architectural redesign. Review the current same-model default, evaluate second-provider need, define the decision (defer), preserve the extension point, define future provider criteria/multi-provider risks/disagreement handling/configuration posture, and define the roadmap outcome. Architecture/review only -- no second provider implemented.

## Allowed Files

- docs/PCAE_ADVISORY_PROVIDER_STRATEGY.md
- docs/PHASE_115U_ADVISORY_PROVIDER_STRATEGY_REVIEW.md
- tests/test_phase_115u_advisory_provider_strategy_review.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260706-2113-115u-advisory-provider-strategy-extension-point-review.md

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

- Second provider decision documented; same-model default retained; future provider extension point preserved; multi-provider risks documented; disagreement handling documented; no implementation added; execution capability remains unavailable

## Acceptance Checks

- python -m pytest tests/test_phase_115u_advisory_provider_strategy_review.py tests/test_advisory_provider_verification_115t.py tests/test_current_acting_model_advisory_provider_115s.py tests/test_advisory_repository_skills_prototype_115r.py -q -ra

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-06T21:13:12.392750+02:00
