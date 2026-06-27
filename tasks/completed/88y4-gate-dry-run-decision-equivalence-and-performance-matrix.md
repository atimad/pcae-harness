# Task: Phase 88Y.4 — Gate Dry-Run Decision Equivalence and Performance Matrix

## Objective

Harden the 88Y.3 GateDryRunContext optimization by expanding decision-equivalence coverage, performance regression coverage, freshness/no-persistence checks, audit/redaction checks, and representative gate scenario coverage. Fix only narrow defects found in the shared evidence prototype.

## Allowed Files

- src/pcae/core/gate_dry_run_context.py
- src/pcae/core/gate_dry_run.py
- tests/test_gate_dry_run_context.py
- tests/test_gate_dry_run.py
- tests/test_phase87_integration.py
- docs/PHASE_88_GATE_DRY_RUN_DECISION_EQUIVALENCE_AND_PERFORMANCE_MATRIX.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active
- tasks/active/
- tasks/completed/

## Forbidden Files

- shell wrapper files
- shell config files
- .githooks/**
- backend invocation behavior implementation files
- prompt/capture/intake/adoption behavior implementation files
- advisory feature expansion files unless only impacted by runtime validation
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md
- README.md
- Phase 88Z task contract
- any phase beyond 88Y.4

## Acceptance Criteria

- Decision-equivalence matrix expanded
- All 15 gates still present
- Gate names unchanged
- Representative scenarios covered
- Audit/redaction behavior preserved
- Authorization/performed flags unchanged
- Per-invocation memoization verified
- Freshness across separate invocations verified
- No persistent cache verified
- No global cache verified
- No tests deleted/skipped/xfailed
- Assertions not weakened
- Source behavior unchanged except narrow bug fixes
- Targeted tests pass
- Related governance tests pass
- Fast-green passes
- Quick tier passes
- Full suite passes
- Documentation artifact exists
- PROJECT_STATUS.md updated
- CHANGELOG.md updated
- Final health/check/doctor/test-run/push clean

## Status

- [x] Created
- [x] In Progress
- [x] Complete
