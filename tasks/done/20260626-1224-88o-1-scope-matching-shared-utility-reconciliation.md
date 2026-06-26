# Task Contract

## Task ID

20260626-1224-88o-1-scope-matching-shared-utility-reconciliation

## Title

88O.1 — Scope Matching Shared Utility Reconciliation

## Status

done

## Mode

implementation

## Goal

Centralize scope file-pattern matching behavior into one shared utility. Update gate_dry_run.py::_evaluate_scope to use _match_file instead of divergent inline logic. Preserve 88N.6 policy-forbidden enforcement. Add regression tests proving identical classification across scope preflight, gate dry-run, mutation preflight, and backend preflight.

## Allowed Files

- src/pcae/core/scope_preflight.py
- src/pcae/core/gate_dry_run.py
- src/pcae/core/mutation_preflight.py
- src/pcae/core/backend_preflight.py
- src/pcae/core/scope_utils.py
- tests/test_scope_matching_consistency.py
- docs/PHASE_88_SCOPE_MATCHING_SHARED_UTILITY_RECONCILIATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/DONE.md
- tasks/done/**

## Forbidden Files

- README.md
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md
- .githooks/**


## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

advisory

## Forbidden Changes

- TBD

## Acceptance Criteria

- gate_dry_run._evaluate_scope uses _match_file, not inline matching
- Regression tests prove identical classification across all four callers
- Policy-forbidden files remain blocked_by_scope
- Full suite passes green

## Acceptance Checks

- python -m pytest -m fast_green -n auto -q
- pcae health
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-26T12:24:18.696515+02:00
