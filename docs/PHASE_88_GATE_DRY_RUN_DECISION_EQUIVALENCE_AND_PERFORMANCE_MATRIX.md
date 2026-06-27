# Phase 88Y.4 — Gate Dry-Run Decision Equivalence and Performance Matrix

## 1. Purpose

Harden the 88Y.3 `GateDryRunContext` optimization by expanding decision-equivalence coverage, performance regression coverage, freshness/no-persistence checks, audit/redaction checks, and representative gate scenario coverage. Fix only narrow defects found in the shared evidence prototype.

## 2. Scope

- Fix the `None`-sentinel memoization bug in `GateDryRunContext` (properties that can return `None` were recomputed on every access)
- Expand `test_gate_dry_run_context.py` from 20 to 55 tests
- Decision-equivalence coverage across 8 representative scenarios
- Memoization call-count tests for all context-cached evidence
- Freshness tests for separate invocations
- No-persistence structural tests
- Audit/redaction preservation tests
- Authorization/enforcement flag invariants across all scenarios
- Performance structural assertions (lazy loading, idempotency)

## 3. Non-Goals

- No implementation of enforcement
- No shell interception or shell wrappers
- No backend invocation
- No prompt sending or output capture
- No intake/adoption behavior
- No real authorization grants
- No persistent gate evidence
- No global cache
- No cross-CLI-invocation caching
- No gate removal or skipping
- No governance weakening
- No test deletion/skipping/xfail
- No assertion weakening
- No further optimization beyond the sentinel fix

## 4. Starting Point from 88Y.3

88Y.3 implemented `GateDryRunContext` as a lazy-memoized dataclass that reduced per-call runtime from ~20.86s to ~9.16s (56% reduction). The context memoizes evidence builders and git metadata within a single `build_gate_dry_run()` invocation.

88Y.3 completion state:
- 20 tests in `test_gate_dry_run_context.py`
- Single call: 9.16s
- Fast-green: 3,003 passed in 24.91s
- Quick tier: 8,272 passed in 330.97s
- Full suite: 9,010 passed in 25:18

## 5. Decision-Equivalence Matrix

### 5.1 Invariants Verified Across All Scenarios

| Invariant | Assertion | Status |
|-----------|-----------|--------|
| Gate count == 15 | `result["gate_count"] == 15` | ✓ |
| Gate IDs preserved | Exact match against `EXPECTED_GATE_IDS` | ✓ |
| Gate names preserved | Exact match against `EXPECTED_GATE_NAMES` | ✓ |
| Gate order preserved | IDs in canonical order | ✓ |
| No gate allows | All `decision != "allow"` | ✓ |
| Authorization never true | All `authorization_granted == False` | ✓ |
| Enforcement never true | All `enforcement_performed == False` | ✓ |
| Dry run flag true | All `dry_run == True` | ✓ |
| Schema version 0.1 | All `schema_version == "0.1"` | ✓ |
| Hard blocks deny | 5 hard-blocked gates always deny | ✓ |
| Reason codes non-empty | All `len(reason_codes) > 0` | ✓ |
| Required gate fields | 18 fields present on every gate | ✓ |
| Required envelope fields | 11 fields present on envelope | ✓ |

### 5.2 Scenario Coverage

| # | Scenario | Parameters | Verified |
|---|----------|------------|----------|
| 1 | Idle repository | `{}` (default) | ✓ |
| 2 | Source mutation | `action="source_mutation"`, `files=["src/pcae/core/gate_dry_run.py"]` | ✓ |
| 3 | Forbidden file mutation | `action="source_mutation"`, `files=["tasks/active/some-task.md"]` | ✓ |
| 4 | Policy-forbidden mutation | `action="source_mutation"`, `files=[".pcae/cache/state.json"]` | ✓ |
| 5 | Backend invocation (known) | `action="backend_invocation"`, `backend="claude"`, `prompt_present=True` | ✓ |
| 6 | Backend invocation (unknown) | `action="backend_invocation"`, `backend="unknown-llm"`, `prompt_present=True` | ✓ |
| 7 | Adoption | `action="adoption"`, `files=["src/example.py"]`, `adoption_artifact_present=True` | ✓ |
| 8 | Commit | `action="commit"`, `commit_message_present=True` | ✓ |
| 9 | Push | `action="push"`, `push_target="origin/main"` | ✓ |
| 10 | All-flags stress test | All flags set, `human_approved=True` | ✓ |
| 11 | Authorization never true | 7 distinct scenarios | ✓ |
| 12 | Enforcement never true | 6 distinct scenarios | ✓ |
| 13 | Gate count in 6 scenarios | 6 parameter combinations | ✓ |
| 14 | Gate IDs in 6 scenarios | 6 parameter combinations | ✓ |

## 6. Gate Count/Name Validation

All 15 gates verified across all scenarios:

| # | Gate ID | Gate Name | Category |
|---|---------|-----------|----------|
| 1 | task_start_gate | Task Start Gate | planning_gate |
| 2 | scope_check_gate | Scope Check Gate | scope_gate |
| 3 | backend_invocation_gate | Backend Invocation Gate | backend_gate |
| 4 | prompt_send_gate | Prompt Send Gate | prompt_gate |
| 5 | capture_acceptance_gate | Capture Acceptance Gate | capture_gate |
| 6 | intake_review_gate | Intake Review Gate | review_gate |
| 7 | adoption_approval_gate | Adoption Approval Gate | review_gate |
| 8 | source_mutation_gate | Source Mutation Gate | mutation_gate |
| 9 | test_mutation_gate | Test Mutation Gate | test_gate |
| 10 | commit_gate | Commit Gate | commit_gate |
| 11 | push_gate | Push Gate | push_gate |
| 12 | rollback_gate | Rollback Gate | rollback_gate |
| 13 | storage_write_gate | Storage Write Gate | storage_gate |
| 14 | permission_broker_gate | Permission Broker Gate | broker_gate |
| 15 | shell_command_gate | Shell Command Gate | shell_gate |

Gate count before 88Y.4: 15
Gate count after 88Y.4: 15
Gate names changed: No

## 7. Memoization Validation

### 7.1 Context-Provided Memoization

| Evidence | Property | Verified | Calls |
|----------|----------|----------|-------|
| `_detect_task_contract` | `ctx.task_contract` | ✓ | 1× (was 15×) |
| `_git_porcelain_raw` | `ctx.git_porcelain` | ✓ | ≤3× (shared) |
| `_git_branch_raw` | `ctx.git_branch` | ✓ | ≤3× (shared) |
| `_git_ahead_count_raw` | `ctx.git_ahead_count` | ✓ | ≤3× (shared) |
| `build_project_state` | `ctx.project_state` | ✓ | 1× (was ~1× via cascade) |

### 7.2 Idempotency

All 10 context properties verified to return the same value on repeated access within a single `GateDryRunContext` instance.

### 7.3 Lazy Loading

All 10 context properties verified to remain unset after `__init__()` and only compute on first access.

## 8. Freshness Validation

- **Separate invocations**: Each `build_gate_dry_run()` creates a fresh `GateDryRunContext` — verified by tracking `__init__` calls
- **Git evidence recomputed**: Separate calls recompute git porcelain (verified by call counting)
- **Task contract recomputed**: Separate calls recompute task contract (verified by call counting)
- **No cross-instance sharing**: After accessing `ctx1` properties, `ctx2` starts with unset caches
- **Changed state observable**: A second call observes current repo state, not stale cached state

## 9. No-Persistence Validation

- **No module-level mutable cache**: Module namespace checked for any dict/list cache attributes
- **No `.pcae` cache files**: All `.pcae` subdirectories checked for new files after dry-run
- **No cache dirs created**: `.pcae/cache`, `.pcae/gates`, `.pcae/state`, `.pcae/decisions`, `.pcae/context` verified non-existent
- **No context cache after full dry-run**: `.pcae/cache`, `.pcae/gates`, `.pcae/broker`, `.pcae/shell`, `.pcae/state` verified clean

## 10. Audit/Redaction Preservation

- **Evidence shape**: All `evidence_artifacts`, `evidence_events`, `evidence_decisions`, `evidence_risks` are lists
- **No redaction applied**: Gate output contains no `[REDACTED]` or `***` markers
- **Safety notes**: All 18 required safety note keys present in envelope
- **Authorization flags**: `authorization_granted` always `False` across all scenarios
- **Enforcement flags**: `enforcement_performed` always `False` across all scenarios

## 11. Performance Regression Checks

Structural assertions (no fragile timing thresholds):

| Assertion | Test |
|-----------|------|
| Lazy loading (not eager at init) | `test_context_properties_lazy_not_eager` |
| Idempotent property access | `test_context_properties_are_idempotent_all` |
| `_detect_task_contract` reduction (15→1) | `test_task_contract_detection_materially_reduced` |
| `build_project_state` called once | `test_build_project_state_called_once_per_dry_run` |
| Git evidence memoized per invocation | `test_git_porcelain_called_once_per_dry_run` |
| Git branch memoized per invocation | `test_git_branch_called_once_per_dry_run` |
| Git ahead count memoized per invocation | `test_git_ahead_count_called_once_per_dry_run` |

## 12. Defects Found

### 12.1 None-Sentinel Memoization Bug

**Severity**: Medium
**Location**: `src/pcae/core/gate_dry_run_context.py`, properties: `task_contract`, `git_porcelain`, `git_branch`, `git_ahead_count`
**Description**: Properties that can legitimately return `None` used `None` as the "not yet computed" sentinel. When the actual value was `None`, the guard `if self._X is None` re-triggered computation on every access, defeating the cache.
**Impact**: In idle repos (no active task), `_detect_task_contract` was called 15 times instead of 1. In error conditions where git commands fail, the git properties would similarly recompute.
**Discovery**: Pre-existing test `test_task_contract_called_once_per_dry_run` failed with count 15 instead of 1.

## 13. Defects Fixed

### 13.1 None-Sentinel Memoization Fix

**Fix**: Introduced module-level `_UNSET = object()` sentinel. Changed the four `None`-capable fields (`_task_contract`, `_git_porcelain`, `_git_branch`, `_git_ahead_count`) to use `_UNSET` as default and `is _UNSET` as the guard condition. Fields that always return dicts (`_artifact_index`, `_memory_snapshot`, etc.) continue using `None` sentinel since they never return `None`.

**Files changed**: `src/pcae/core/gate_dry_run_context.py`

**Verification**: `test_task_contract_called_once_per_dry_run` now passes with 1 call. `test_none_value_is_properly_cached` added to explicitly verify the fix — `_detect_task_contract` called once even when returning `None`.

## 14. Validation Results

### 14.1 Targeted Tests

| Test File | Tests | Result |
|-----------|-------|--------|
| test_gate_dry_run_context.py | 55 | All passed |

### 14.2 Baseline vs Final Timing

Timing comparison for context tests:
- 88Y.3: 20 tests in 193.81s
- 88Y.4: 55 tests in ~759s (12:39)

The increase is proportional to test count (2.75× more tests, ~3.9× runtime due to scenario matrix tests that make multiple build_gate_dry_run calls each).

## 15. Remaining Bottlenecks

1. **Internal build function cascading**: `build_project_state()` still calls all 5 other build functions internally. Modifying them to accept an optional `GateDryRunContext` parameter would eliminate the remaining cascade. Estimated additional reduction: 9.16s → 2-3s per call.
2. **Git subprocess overhead**: Each `git log` call has ~10-15ms overhead. With ~817 subprocess calls remaining, that's ~8-12s just in subprocess spawning.
3. **Git history scanning**: `git log --oneline` over full history is called multiple times per cascade.

## 16. Recommended Next Phase

**88Z — Advisory Operator UX and Workflow Design**

The GateDryRunContext optimization is now thoroughly validated. Decision equivalence is confirmed across 14 scenario combinations. All memoization, freshness, no-persistence, and audit/redaction invariants hold. The next phase should focus on the advisory operator experience and workflow design as specified in the roadmap.

Alternative: **88Y.5 — Gate Dry-Run Full Suite Optimization** if further performance work is desired before moving to 88Z. This would modify the build functions to accept an optional context parameter for complete internal memoization, potentially reducing per-call runtime from 9s to 2-3s.
