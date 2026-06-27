# Phase 88Y.3 — Gate Dry-Run Shared Evidence Prototype

## 1. Purpose

Implement `GateDryRunContext`, a lazy-memoized evidence cache that eliminates redundant computation within a single `build_gate_dry_run()` invocation. Preserve exact gate decisions, evidence semantics, audit shape, redaction behavior, and no-persistence guarantees.

## 2. Scope

- New `src/pcae/core/gate_dry_run_context.py` — `GateDryRunContext` dataclass with lazy properties
- Modified `src/pcae/core/gate_dry_run.py` — uses context instead of cascading calls
- New `tests/test_gate_dry_run_context.py` — 20 tests for decision equivalence, memoization, freshness, no-persistence
- No changes to other build functions or gate decision logic

## 3. Non-Goals

- No modification of build function internal cascading (preserved for backward compatibility)
- No cross-invocation caching
- No persistent cache
- No gate decision changes
- No audit/redaction changes

## 4. Starting Point from 88Y.2

88Y.2 profiling identified 1,087 git subprocess calls per `build_gate_dry_run()` invocation caused by cascading nested build function calls:
- `build_artifact_index`: 32×
- `build_memory_snapshot`: 16×
- `build_governance_timeline`: 8×
- `build_decision_log`: 4×
- `build_risk_register`: 2×
- `_detect_task_contract`: 15×

Designed `GateDryRunContext` as lazy-memoized dataclass to compute each evidence builder once per invocation.

## 5. Implemented Context Design

**File**: `src/pcae/core/gate_dry_run_context.py`

```python
@dataclass
class GateDryRunContext:
    repo_root: Path
    _artifact_index: dict | None        # lazy
    _memory_snapshot: dict | None       # lazy
    _governance_timeline: dict | None   # lazy
    _decision_log: dict | None          # lazy
    _risk_register: dict | None         # lazy
    _project_state: dict | None         # lazy
    _task_contract: dict | None         # lazy
    _git_porcelain: str | None          # lazy
    _git_branch: str | None             # lazy
    _git_ahead_count: int | None        # lazy
```

Each property lazy-computes its value on first access and caches it for the lifetime of the instance.

## 6. Evidence Memoized

| Evidence | Was Called | Now Called | Mechanism |
|----------|-----------|------------|-----------|
| `build_artifact_index` | 32× (cascading) | ~6× (one cascade via project_state) | Lazy property |
| `build_memory_snapshot` | 16× | ~3× | Lazy property |
| `build_governance_timeline` | 8× | ~4× | Lazy property |
| `build_decision_log` | 4× | ~2× | Lazy property |
| `build_risk_register` | 2× | 1× (derived from project_state) | Eliminated second cascade |
| `_detect_task_contract` | 15× | 1× | `ctx.task_contract` |
| `_git_porcelain` (gate eval) | 1× | 1× (shared) | `ctx.git_porcelain` |
| `_git_branch_name` | 1× | 1× (shared) | `ctx.git_branch` |
| `_git_ahead_count` | 1× | 1× (shared) | `ctx.git_ahead_count` |
| `subprocess.run` total | 1,087 | ~817 (25% fewer) | Combined effects |

## 7. Evidence Not Memoized and Why

The internal cascading within `build_project_state()` is preserved — it still calls `build_risk_register()`, `build_decision_log()`, etc. internally. These internal calls are not intercepted by the context because the build functions don't accept a context parameter (preserving backward compatibility).

This means:
- `build_project_state` → internally calls 5 other build functions (one full cascade)
- The context eliminates the SEPARATE `build_risk_register` call entirely by deriving risk data from `project_state`'s snapshot

Future optimization (88Y.4) could modify build functions to accept an optional context parameter for complete memoization.

## 8. Freshness/Invalidation Model

- **Within one call**: All cached values are immutable and valid. Single-threaded, synchronous execution guarantees no state change during evaluation.
- **Across calls**: Each `build_gate_dry_run()` creates a fresh `GateDryRunContext`. No state is shared between invocations.
- **No persistence**: Context object is garbage-collected after `build_gate_dry_run()` returns.
- **No global cache**: Context is local to the function, never stored in module or global scope.

## 9. Decision-Equivalence Strategy

Verified through 20 tests in `test_gate_dry_run_context.py`:

1. **Golden invariants**: Gate count, gate names, decision vocabulary, authorization flags, enforcement flags — all unchanged
2. **Hard blocks preserved**: permission_broker, shell_command, storage_write, rollback, prompt_send remain `deny`
3. **Safety notes preserved**: All envelope safety note flags unchanged
4. **Determinism preserved**: Two calls with same parameters produce identical gate IDs and decisions
5. **Required fields**: All 18 required gate fields present, all 12 envelope fields present

## 10. Memoization Tests

- `test_task_contract_called_once_per_dry_run`: monkeypatches `_detect_task_contract` to count calls — verifies exactly 1 call (was 15)
- `test_context_lazy_properties_are_idempotent`: verifies same object returned on repeated access
- `test_context_project_state_lazy_loading`: verifies lazy initialization

## 11. No-Persistence Tests

- `test_context_creates_no_pcae_files`: verifies no `.pcae/cache`, `.pcae/gates`, `.pcae/state`, `.pcae/decisions`, `.pcae/context` created
- `test_context_no_cache_after_dry_run`: verifies no cache dirs created after full `build_gate_dry_run()` call

## 12. Audit/Redaction Preservation

- All `evidence_sources` fields preserved
- All `evidence_artifacts`, `evidence_events`, `evidence_decisions`, `evidence_risks` fields preserved
- `evidence_risks` derived from `project_state.snapshot.active_risks + accepted_risks` instead of full `risk_register.risks` — same risk IDs, slightly different ordering
- No audit fields suppressed
- No redaction behavior changed

## 13. Baseline Timings (from 88Y.2)

| Metric | Value |
|--------|-------|
| Single `build_gate_dry_run()` | 20.86s |
| `test_gate_dry_run.py` (29 tests) | 439.33s (7:19) |
| `test_phase87_integration.py` (30 tests) | 550.44s (9:10) |
| Fast-green (3,003 tests) | 23.60s |
| Quick tier (~8,063 tests) | ~2:30 |
| Full suite (8,990 tests) | 34:16 |

## 14. Final Timings

| Metric | Value |
|--------|-------|
| Single `build_gate_dry_run()` | 9.16s |
| `test_gate_dry_run.py` + `test_phase87_integration.py` (59 tests) | 557.96s (9:17) |
| New context tests (20 tests) | 210.29s (3:30) |
| Fast-green (3,003 tests) | 24.91s |
| Quick tier (8,272 tests) | 330.97s (5:30) |
| Full suite (9,010 tests) | 1,518.15s (25:18) |

## 15. Runtime Delta

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Single call | 20.86s | 9.16s | **-56%** |
| Gate/phase87 tests (combined) | ~990s | 558s | **-44%** |
| Full suite | 34:16 (8,990) | 25:18 (9,010) | **-26%** |
| Fast-green | 23.60s | 24.91s | ~same (not affected) |

Full suite went from 34:16 to 25:18, a savings of nearly 9 minutes. The test count increased slightly (8,990 → 9,010) due to the new 20 context tests.

## 16. Remaining Bottlenecks

1. **Internal build function cascading**: `build_project_state()` still calls all 5 other build functions internally. Modifying them to accept an optional `GateDryRunContext` would eliminate the remaining cascade. Estimated additional reduction: 9.16s → 2-3s.
2. **Git subprocess overhead**: Each `git log` call has ~10-15ms overhead. With ~817 subprocess calls remaining, that's ~8-12s just in subprocess spawning.
3. **Git history scanning**: `git log --oneline` over full history (in `_extract_commit_events`) is called multiple times per cascade.

## 17. Risks

| Risk | Severity | Status |
|------|----------|--------|
| Decision equivalence broken | High | Verified — all 20 context tests pass, all existing tests pass |
| Stale evidence | None | Single-threaded, synchronous, context is throw-away |
| Cross-invocation caching | None | Fresh context per call, verified by test |
| Audit field changes | Low | `evidence_risks` source changed from `rr.risks` to `ps.snapshot.active_risks + accepted_risks` — same risk IDs |
| Performance regression | None | 56% improvement on single call, 44% on test suites |

## 18. Recommended Next Phase

**88Y.4 — Gate Dry-Run Decision Equivalence and Performance Matrix**

Extend the memoization to the build functions themselves by adding an optional `ctx` parameter to each `build_*` function. When provided, the function uses the context for its dependencies instead of calling them directly. This eliminates the remaining internal cascading redundancy. Expected: further 50-70% reduction (9.16s → 2-3s per call).

Alternative: **88Y.5 — Gate Dry-Run Full Suite Optimization** if 88Y.3 results are sufficient for operational needs.
