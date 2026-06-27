# Phase 88Y.5 — Project State Shared Evidence Optimization

## 1. Purpose

Eliminate the remaining internal build-function cascade inside `build_project_state()` by extending the 88Y.3/88Y.4 shared evidence model to all five upstream build functions. Reduces per-call runtime from ~9.16s to ~3.2s without changing any gate decision, governance rule, output schema, or audit behavior.

## 2. Scope

- Add optional `ctx=None` parameter to `build_memory_snapshot`, `build_governance_timeline`, `build_decision_log`, `build_risk_register`, and `build_project_state`
- Update `GateDryRunContext` property methods to pass `ctx=self` when invoking each build function
- 24 new tests in `tests/test_project_state_context.py`
- Fix one pre-existing test in `tests/test_gate_dry_run_context.py` to handle the new `ctx` keyword argument
- No changes to gate decision logic, output schema, governance rules, or audit behavior

## 3. Non-Goals

- No cross-invocation caching
- No persistent cache
- No global cache
- No gate decision changes
- No gate removal or skipping
- No enforcement implementation
- No shell interception or shell wrappers
- No backend invocation
- No prompt sending or output capture
- No intake/adoption behavior
- No real authorization grants
- No test deletion, skipping, or xfail
- No assertion weakening

## 4. Starting Point from 88Y.4

88Y.4 validated `GateDryRunContext` across 55 tests and 14 scenario combinations. After 88Y.3, `build_gate_dry_run()` had been reduced from ~20.86s to ~9.16s per call (56% reduction). The remaining bottleneck was the internal cascade inside `build_project_state()`, which still called all five upstream build functions directly without receiving the shared context.

88Y.4 completion state:
- 55 tests in `test_gate_dry_run_context.py`
- Single `build_gate_dry_run()` call: ~9.16s
- Fast-green: 3,003 passed in ~24s
- Context tests baseline (88Y.5 start): 55 tests in 803.70s (~10s/test)
- Gate+phase87 baseline (88Y.5 start): 59 tests in 538.75s (~10s/test)

## 5. Project-State Cascade Findings

### 5.1 The Remaining Cascade

After 88Y.3/88Y.4, `build_project_state()` was called once via `ctx.project_state`. However, internally it still triggered the full cascade:

```
ctx.project_state → build_project_state(repo_root)
  ├── build_artifact_index(repo_root)           # direct call (1st of many)
  ├── build_memory_snapshot(repo_root)
  │     └── build_artifact_index(repo_root)     # duplicate
  ├── build_governance_timeline(repo_root)
  │     ├── build_artifact_index(repo_root)     # duplicate (unused result)
  │     └── build_memory_snapshot(repo_root)    # duplicate (unused result)
  │           └── build_artifact_index(...)     # duplicate
  ├── build_decision_log(repo_root)
  │     ├── build_artifact_index(repo_root)     # duplicate (unused result)
  │     ├── build_memory_snapshot(repo_root)    # duplicate (unused result)
  │     └── build_governance_timeline(repo_root) # duplicate (unused result)
  │           └── ... (full cascade again)
  └── build_risk_register(repo_root)
        ├── build_artifact_index(repo_root)     # duplicate (unused result)
        ├── build_memory_snapshot(repo_root)    # duplicate (unused result)
        ├── build_governance_timeline(repo_root) # duplicate (unused result)
        └── build_decision_log(repo_root)       # duplicate (unused result)
              └── ... (full cascade again)
```

### 5.2 Key Finding: Unused Upstream Results

Investigation revealed that `build_governance_timeline`, `build_decision_log`, and `build_risk_register` each call their upstream build functions but **never use the returned values** — the results are assigned to underscore-prefixed local variables (`_artifact_data`, `_snapshot_data`, etc.) and discarded. These were vestigial cascade calls.

This means: when ctx is provided, these calls can be skipped entirely — not merely replaced with ctx lookups, but omitted outright.

### 5.3 Git Subprocess Redundancy in project_state

`build_project_state` contains local git subprocess calls (`_git_status_clean`, `_git_branch`, `_git_origin_count`, `_git_head_commit`) that duplicate git evidence already computed in `ctx.git_porcelain`, `ctx.git_branch`, `ctx.git_ahead_count`, and the memory snapshot's `last_verified_commit`. These are also eliminated when ctx is provided.

## 6. Evidence Optimized

| Evidence | Before (internal cascade) | After (ctx provided) | Mechanism |
|----------|--------------------------|----------------------|-----------|
| `build_artifact_index` | Called 6+ times | Called 1× | `ctx.artifact_index` via `build_memory_snapshot(ctx=ctx)` |
| `build_memory_snapshot` | Called 4+ times | Called 1× | `ctx.memory_snapshot` in `build_project_state(ctx=ctx)` |
| `build_governance_timeline` | Called 2+ times | Called 1× | `ctx.governance_timeline` in `build_project_state(ctx=ctx)` |
| `build_decision_log` | Called 2+ times | Called 1× | `ctx.decision_log` in `build_project_state(ctx=ctx)` |
| `build_risk_register` | Called 2× | Called 1× | `ctx.risk_register` in `build_project_state(ctx=ctx)` |
| `_git_status_clean` in project_state | 1× per cascade | 0× when ctx | Derived from `ctx.git_porcelain` |
| `_git_branch` in project_state | 1× per cascade | 0× when ctx | `ctx.git_branch` |
| `_git_origin_count` in project_state | 1× per cascade | 0× when ctx | `ctx.git_ahead_count` |
| `_git_head_commit` in project_state | 1× per cascade | 0× when ctx | `mem.get("last_verified_commit")` from ctx.memory_snapshot |

## 7. Evidence Not Optimized and Why

| Evidence | Not optimized because |
|----------|-----------------------|
| `build_artifact_index` internal git log calls | These are the work within the function itself; the function is still called once and these cannot be eliminated without deeper restructuring of artifact_index internals |
| `build_governance_timeline` git log calls | Internal to the function; still called once — just not redundantly |
| `build_decision_log` git log calls | Same — internal to function; called once |
| Git subprocess calls within each build function | Each function's internal subprocesses are irreducible (they fetch per-artifact and per-phase git history); optimization stops at eliminating redundant full-function re-invocations |

## 8. Freshness Model

- **Within one `build_gate_dry_run()` call**: All ctx properties are immutable for the duration of the call. Single-threaded, synchronous execution guarantees no state changes. Each property is computed once on first access and cached.
- **Across calls**: Each `build_gate_dry_run()` creates a fresh `GateDryRunContext`. No state is shared between invocations.
- **git data in project_state**: `head_commit` is extracted from `ctx.memory_snapshot` (which calls `_git_head_commit` internally). `repo_clean` is derived from `ctx.git_porcelain`. `branch` and `origin_count` come from `ctx.git_branch` and `ctx.git_ahead_count`. All are per-invocation fresh.
- **No cross-invocation caching**: Context is garbage-collected after each `build_gate_dry_run()` returns.

## 9. No-Persistence Model

- No module-level mutable state added in any build function
- No `.pcae` files written during project-state construction with ctx
- No temp cache files written
- Build functions remain pure read-only operations
- Verified by `test_project_state_ctx_no_pcae_files_created` and `test_build_project_state_with_ctx_no_pcae_cache_dirs`

## 10. Decision-Equivalence Strategy

Decision equivalence verified at two levels:

**Gate level** (existing 88Y.4 tests, all still pass):
- All 14 scenario combinations preserved
- 15 gates, same IDs, same names, same order
- No gate allows, no authorization granted, no enforcement performed

**Project-state level** (new 88Y.5 tests):
- `schema_version`, `snapshot` keys, `layer_summary`, authorization flags, safety notes, risk counts, repository_root — all identical between `build_project_state(ctx=ctx)` and `build_project_state(repo_root)` standalone
- `snapshot_id` format preserved (`pstate-` prefix + 16 hex chars)

## 11. Memoization Tests (24 new in `test_project_state_context.py`)

| Test | Assertion |
|------|-----------|
| `test_build_memory_snapshot_with_ctx_uses_artifact_index_once` | `build_artifact_index` called 1× when ctx provided |
| `test_build_governance_timeline_with_ctx_skips_unused_calls` | 0 artifact_index + 0 memory_snapshot calls when ctx provided |
| `test_build_decision_log_with_ctx_skips_all_upstream_calls` | 0 artifact_index + 0 memory_snapshot + 0 governance_timeline calls |
| `test_build_risk_register_with_ctx_skips_all_upstream_calls` | 0 of all 4 upstream calls when ctx provided |
| `test_build_project_state_with_ctx_artifact_index_called_once` | artifact_index called exactly 1× across full ctx.project_state path |
| `test_build_project_state_with_ctx_all_builders_called_once` | Each of the 5 build functions called exactly 1× |
| `test_project_state_ctx_idempotent_on_repeated_access` | `ctx.project_state` returns same object on repeated access |

## 12. Freshness Tests

| Test | Assertion |
|------|-----------|
| `test_project_state_separate_ctx_instances_are_independent` | Two ctx instances produce different objects |
| `test_project_state_ctx2_recomputes_after_ctx1_accessed` | `build_project_state` called 2× for 2 separate ctx instances |

## 13. No-Persistence Tests

| Test | Assertion |
|------|-----------|
| `test_project_state_ctx_no_pcae_files_created` | No new files under `.pcae` after `ctx.project_state` |
| `test_build_project_state_with_ctx_no_pcae_cache_dirs` | Specific cache dirs (cache, gates, state, decisions, context) not created |

## 14. Baseline Timings (88Y.4 end / 88Y.5 start)

| Metric | Value |
|--------|-------|
| Single `build_gate_dry_run()` call | ~9.16s |
| `test_gate_dry_run_context.py` (55 tests) | 803.70s (~10s/test) |
| `test_gate_dry_run.py` + `test_phase87_integration.py` (59 tests) | 538.75s (~10s/test) |
| Fast-green (3,003 tests) | ~24s |

## 15. Final Timings

| Metric | Value |
|--------|-------|
| Single `build_gate_dry_run()` call | 3.22s |
| Single `build_project_state(ctx=ctx)` call | 3.28s |
| `test_gate_dry_run_context.py` (55 tests) | ~266s (~4.5s/test, measured before fix) |
| `test_gate_dry_run.py` + `test_phase87_integration.py` (59 tests) | 253.13s (~4.3s/test) |
| `test_project_state_context.py` (24 new tests) | 119s (~5s/test, in slow tier post-correction) |
| Fast-green (3,003 tests, post-marker correction) | ~25s |

## 16. Runtime Delta

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Single `build_gate_dry_run()` call | 9.16s | 3.22s | **-65%** |
| Gate+phase87 tests (59 tests) | 538.75s | 253.13s | **-53%** |
| Context tests (55 tests) | 803.70s | ~266s (estimated) | **-67%** |
| Cumulative from original (88Y.2) | 20.86s | 3.22s | **-85%** |

## 17. Remaining Bottlenecks

1. **`build_artifact_index` internal git log calls**: Each artifact requires 2 git subprocess calls (`git log -1 --format=%H` and `git log -1 --format=%aI`). With ~15-20 artifacts that currently exist in the repo, this accounts for ~30-40 subprocess calls at ~10-15ms each = ~0.3-0.6s. Growing the artifact index will increase this proportionally.

2. **`build_governance_timeline` git log calls**: Phase events (`_extract_phase_events`), commit events (`_extract_commit_events`), and test events (`_extract_test_events`) each involve git log calls. These run once per dry-run invocation but cannot be shared further without deeper restructuring.

3. **`build_decision_log` git log calls**: Phase decision extraction involves git log calls per phase. Same analysis as above.

4. **Python interpreter startup overhead**: ~0.2-0.3s for import and module initialization, irreducible without caching.

5. **Total irreducible floor**: Approximately 2-3s due to the minimum number of git subprocess calls required per invocation (each build function's internal git calls, once each).

## 18. Post-Completion Marker Correction

After 88Y.5 completion, a post-push inspection found that `tests/test_project_state_context.py`
had `pytestmark = pytest.mark.fast_green` set at module level, causing fast-green runtime to
inflate from ~25s (88Y.4 baseline) to ~119s. Root cause: the 24 new tests call real git
subprocesses via `GateDryRunContext` and build functions; under 15-worker parallelism, git I/O
contention causes individual tests to take 1–24s each.

Correction: marker changed to `pytest.mark.slow`. Fast-green reverts to 3,003 tests / ~25s.
The 24 tests remain in the `slow` (governance/full) tier where subprocess-heavy tests belong.

## 19. Recommended Next Phase

**88Z — Advisory Operator UX and Workflow Design**

The performance optimization series (88Y.1–88Y.5) is complete. Per-call runtime has been reduced from ~20.86s (88Y.2 baseline) to ~3.22s (after 88Y.5), an 85% total reduction. The remaining bottleneck (~3s floor) is dominated by the minimum-necessary git subprocess calls per invocation and cannot be reduced further without persistent caching or daemon-based architecture — both explicitly out of scope.

The next phase should focus on the advisory operator experience and workflow design as specified in the roadmap.
