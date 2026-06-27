# Phase 88Y.2 — Gate Dry-Run Performance Profiling and Optimization Design

## 1. Purpose

Profile `build_gate_dry_run()` and its dependency chain to identify the root causes of ~17s per-call runtime. Document the call graph, measure per-operation costs, and propose a safe optimization strategy that preserves governance correctness.

## 2. Scope

- **Profiling**: cProfile-based measurement of `build_gate_dry_run()` and all transitive calls
- **Call graph mapping**: Full dependency chain from entry point through all 6 build functions and 15 gate evaluators
- **Subprocess analysis**: Count, type, and redundancy analysis of all `subprocess.run` calls
- **Optimization design**: Propose memoization/caching strategy with safety analysis
- **Decision-equivalence testing**: Design a strategy to verify optimizations don't change gate outcomes

## 3. Non-Goals

- No production code changes in this phase (design-only)
- No gate behavior changes
- No enforcement/advisory changes
- No test deletion/skipping/xfail
- No persistence of gate evidence across commands
- No caching across separate CLI invocations

## 4. Starting Point from 88Y.1

Phase 88Y.1 reduced subprocess overhead in tests by having them call `build_gate_dry_run()` directly instead of spawning a `pcae gate-dry-run` subprocess. This eliminated the Python interpreter startup cost per test (~0.3s → 0s) but revealed that `build_gate_dry_run()` itself dominates at ~17s per call.

## 5. `build_gate_dry_run()` Call Graph

### 5.1 Entry Point

**File**: `src/pcae/core/gate_dry_run.py:860`
**Function**: `build_gate_dry_run(repo_root, requested_action, requested_files, ...)`

### 5.2 Direct Dependencies (lines 875-880)

```
build_gate_dry_run(repo_root)
  ├── build_artifact_index(repo_root)         # line 875
  ├── build_memory_snapshot(repo_root)        # line 876
  ├── build_governance_timeline(repo_root)    # line 877
  ├── build_decision_log(repo_root)           # line 878
  ├── build_risk_register(repo_root)          # line 879
  ├── build_project_state(repo_root)          # line 880
  └── _evaluate_gate() × 15 gates            # lines 882-889
```

### 5.3 Cascading Nested Dependencies

Each function transitively imports and calls ALL previous functions:

```
build_artifact_index(repo_root)
  └── _get_commit_ref() × 14 artifacts       # git log per artifact

build_memory_snapshot(repo_root)
  ├── build_artifact_index(repo_root)         # DUPLICATE #2
  ├── _git_head_commit()                      # git rev-parse HEAD
  ├── _git_branch()                           # git branch --show-current
  ├── _git_origin_count()                     # git rev-list --count origin/main..HEAD
  ├── _detect_active_task()                   # scans tasks/active/
  ├── _detect_latest_completed_phase()        # scans tasks/completed/
  └── _read_first_line_match()                # reads PROJECT_STATUS.md

build_governance_timeline(repo_root)
  ├── build_artifact_index(repo_root)         # DUPLICATE #3
  ├── build_memory_snapshot(repo_root)        # DUPLICATE #2 (with all git calls again)
  ├── _extract_phase_events() × 11 phases     # 2× git log per phase = 22 calls
  ├── _extract_commit_events()                # git log --oneline (ALL history)
  └── _extract_test_events()                  # 2× git log

build_decision_log(repo_root)
  ├── build_artifact_index(repo_root)         # DUPLICATE #4
  ├── build_memory_snapshot(repo_root)        # DUPLICATE #3
  ├── build_governance_timeline(repo_root)    # DUPLICATE #2 (all sub-calls again!)
  └── _extract_phase_decisions() × 12         # 2× git log per phase = 24 calls

build_risk_register(repo_root)
  ├── build_artifact_index(repo_root)         # DUPLICATE #5
  ├── build_memory_snapshot(repo_root)        # DUPLICATE #4
  ├── build_governance_timeline(repo_root)    # DUPLICATE #3
  └── build_decision_log(repo_root)           # DUPLICATE #2

build_project_state(repo_root)
  ├── build_artifact_index(repo_root)         # DUPLICATE #6
  ├── build_memory_snapshot(repo_root)        # DUPLICATE #5
  ├── build_governance_timeline(repo_root)    # DUPLICATE #4
  ├── build_decision_log(repo_root)           # DUPLICATE #3
  ├── build_risk_register(repo_root)          # DUPLICATE #2
  ├── _git_status_clean()                     # git status --porcelain
  ├── _git_branch()                           # git branch --show-current
  ├── _git_origin_count()                     # git rev-list --count
  └── _git_head_commit()                      # git rev-parse HEAD

Per-gate evaluation (_evaluate_gate × 15):
  ├── _detect_task_contract(repo_root)        # scans tasks/active/, reads .md file
  ├── _evaluate_scope()                       # [scope_check_gate, mutation gates, adoption gate]
  ├── _evaluate_backend()                     # [backend_invocation_gate]
  ├── _evaluate_adoption()                    # [adoption_approval_gate]
  ├── _evaluate_mutation()                    # [source_mutation_gate, test_mutation_gate]
  ├── _evaluate_commit()                      # [commit_gate]
  │   └── _git_porcelain()                    # git status --porcelain
  └── _evaluate_push()                        # [push_gate]
      ├── _git_branch_name()                  # git branch --show-current
      └── _git_ahead_count()                  # git rev-list --count
```

## 6. Gate List and Responsibilities

| # | Gate ID | Category | Risk | Decision Logic |
|---|---------|----------|------|----------------|
| 1 | task_start_gate | planning | medium | Lifecycle state check |
| 2 | scope_check_gate | scope | medium | File scope matching against task contract |
| 3 | backend_invocation_gate | backend | critical | Backend request evaluation |
| 4 | prompt_send_gate | prompt | critical | Always deny (not authorized) |
| 5 | capture_acceptance_gate | capture | high | Requires more evidence |
| 6 | intake_review_gate | review | high | Requires more evidence |
| 7 | adoption_approval_gate | review | critical | Adoption scope + artifact + approval eval |
| 8 | source_mutation_gate | mutation | high | Scope + mutation evaluation |
| 9 | test_mutation_gate | test | medium | Scope + mutation evaluation |
| 10 | commit_gate | commit | high | Task contract + repo porcelain + message |
| 11 | push_gate | push | high | Task contract + branch + ahead count |
| 12 | rollback_gate | rollback | high | Always deny |
| 13 | storage_write_gate | storage | high | Always deny (not authorized) |
| 14 | permission_broker_gate | broker | critical | Always deny (not implemented) |
| 15 | shell_command_gate | shell | critical | Always deny (not implemented) |

All 15 gates are evaluated on every dry run regardless of the requested action.

## 7. Baseline Timings

### 7.1 Single `build_gate_dry_run()` Call

**Method**: cProfile instrumented call from Python
**Result**: **17.17 seconds**
**Subprocess calls**: **1,087**

### 7.2 Test Suite Timings

| Test File | Tests | Time | Slowest Test |
|-----------|-------|------|--------------|
| test_phase87_integration.py | 30 | 485s (8:05) | test_no_cache_or_state_created: 52.45s |
| test_gate_dry_run.py | 29 | 459s (7:39) | test_gate_dry_run_shell_gate_not_implemented: 21.66s |
| test_scope_preflight.py | 66 | 45s | test_existing_intelligence_commands_still_work: 19.32s |

Per-test times:
- Most gate_dry_run tests: **17-22s** each (one `build_gate_dry_run()` call via subprocess)
- Multi-call tests: **35-52s** (multiple `build_gate_dry_run()` calls)
- Scope preflight tests: **0.12-0.16s** each (lighter, no full cascade)

## 8. Per-Gate Timing Findings

Gate evaluation itself is **trivially cheap**:

| Operation | ncalls | cumtime |
|-----------|--------|---------|
| _evaluate_gate (all 15 gates) | 15 | **0.030s** |
| _evaluate_push | 1 | 0.016s |
| _evaluate_commit | 1 | 0.013s |
| _git_porcelain (gate eval) | 1 | 0.013s |

**Finding**: Gate decision logic accounts for < 0.2% of total runtime. The bottleneck is entirely in the 6 build function cascades.

## 9. Repeated Evidence Computations

### 9.1 Function Call Multiplicity

| Function | Called | Should be called |
|----------|--------|-----------------|
| build_artifact_index | **32×** | 1× |
| build_memory_snapshot | **16×** | 1× |
| build_governance_timeline | **8×** | 1× |
| build_decision_log | **4×** | 1× |
| build_risk_register | **2×** | 1× |
| build_project_state | **1×** | 1× |
| _detect_task_contract | **15×** | 1× |

### 9.2 Root Cause

The cascading import structure causes exponential duplication:

```
project_state imports risk_register
  risk_register imports decision_log
    decision_log imports governance_timeline
      governance_timeline imports memory_snapshot
        memory_snapshot imports artifact_index
```

Each function calls all its transitive dependencies at the top of its body, without checking whether they've already been computed in the current call chain.

## 10. Git Subprocess Findings

### 10.1 Total Count

**1,087 subprocess calls** per `build_gate_dry_run()` invocation — all `git` commands.

### 10.2 Breakdown by Type

| Git Command | Approx Calls | In Which Functions |
|-------------|-------------|-------------------|
| `git log -1 --format=%H -- <path>` | ~570 | _get_commit_ref, _git_log_commit_hash |
| `git log -1 --format=%aI -- <path>` | ~430 | _git_log_commit_date |
| `git log --oneline --format=%H %aI %s` | 8 | _extract_commit_events (full history!) |
| `git rev-parse HEAD` | 17 | _git_head_commit |
| `git branch --show-current` | 17 | _git_branch, _git_branch_name |
| `git rev-list --count origin/main..HEAD` | 17 | _git_origin_count, _git_ahead_count |
| `git status --porcelain` | 2 | _git_status_clean, _git_porcelain |

### 10.3 Most Expensive Single Operation

`git log --oneline` over the full repository history (called 8× via `_extract_commit_events`) processes the entire commit log each time. Each call takes ~0.15-0.20s.

## 11. Filesystem Scan Findings

| Operation | ncalls | Notes |
|-----------|--------|-------|
| Path.is_file() | 752 | Artifact existence checks × 32 build_artifact_index calls |
| tasks/active/ scan | 31 | 16× memory_snapshot + 15× _detect_task_contract |
| tasks/completed/ scan | 16 | _detect_latest_completed_phase in memory_snapshot |
| PROJECT_STATUS.md read | 16 | _read_first_line_match in memory_snapshot |
| Task contract .md read | 15 | _detect_task_contract in _evaluate_gate |

Filesystem operations are individually cheap (< 0.001s) but accumulate to ~0.5-0.8s total due to the 752+ calls.

## 12. Active Task Parsing Findings

`_detect_task_contract(repo_root)` (gate_dry_run.py:140-172):
- Called **15 times** (once per gate evaluation)
- Each call: scans `tasks/active/` directory, reads the first `.md` file found, parses "Allowed Files" and "Forbidden Files" sections
- Individual call cost: negligible (~0.001s)
- Cumulative cost: ~0.015s — not a bottleneck, but redundant
- **Safety note**: Could change if a new task is started during evaluation, but within a single `build_gate_dry_run()` call, this is immutable

## 13. Scope/Backend/Mutation/Adoption/Commit/Push Evidence Findings

The per-gate evaluators (_evaluate_scope, _evaluate_backend, etc.) are individually cheap:
- _evaluate_scope: called 3-5× per dry run, each < 0.001s
- _evaluate_backend: called 1×, < 0.001s
- _evaluate_adoption: called 1×, < 0.001s
- _evaluate_mutation: called 2×, < 0.001s
- _evaluate_commit: called 1×, ~0.013s (includes git status subprocess)
- _evaluate_push: called 1×, ~0.016s (includes two git subprocesses)

**Finding**: The commit/push evaluators are the only gate-level functions with non-trivial cost, and only because they run git subprocesses.

## 14. Cache/Shareability Analysis

### 14.1 Immutable Within One `build_gate_dry_run()` Call

These can be safely computed once and shared:

| Evidence | Computed By | Safe to Cache? |
|----------|------------|----------------|
| Artifact index records | build_artifact_index | ✅ Yes — filesystem state is read once |
| Memory snapshot | build_memory_snapshot | ✅ Yes — derived from artifact index + git |
| Governance timeline events | build_governance_timeline | ✅ Yes — derived from artifact index + git log |
| Decision log entries | build_decision_log | ✅ Yes — derived from timeline |
| Risk register entries | build_risk_register | ✅ Yes — derived from decision log |
| Project state snapshot | build_project_state | ✅ Yes — derived from all above |
| Task contract | _detect_task_contract | ✅ Yes — tasks/active/ doesn't change mid-call |
| Git HEAD commit | _git_head_commit | ✅ Yes — doesn't change mid-call |
| Git branch name | _git_branch | ✅ Yes — doesn't change mid-call |
| Git origin count | _git_origin_count | ✅ Yes — doesn't change mid-call |
| Git porcelain status | _git_porcelain | ✅ Yes — doesn't change mid-call |

### 14.2 Must NOT Be Cached

| Evidence | Reason |
|----------|--------|
| Nothing identified | Within a single synchronous function call, no external state can change |

### 14.3 Cross-Invocation Caching

**Forbidden** by design. Each `build_gate_dry_run()` invocation must reflect current repo state. No persistence between CLI invocations.

## 15. Evidence Freshness and Invalidation Risks

### 15.1 Within a Single Call

**Risk: None.** `build_gate_dry_run()` is synchronous and single-threaded. No external process can modify the repo between the first and last subprocess call within one invocation. Evidence computed at the start of the call is valid for the entire call duration.

### 15.2 Across Separate Commands

**Risk: High.** Repo state can change between CLI invocations (git operations, file edits). Caching across commands is forbidden.

### 15.3 During Long-Running Operations

**Risk: Very Low.** The current 17s duration is the window. With optimization reducing this to ~1-2s, the window shrinks proportionally. No practical risk.

## 16. Audit/Redaction Implications

### 16.1 Current State

Each gate result includes `evidence_sources` listing which files contributed to the evaluation. Currently, each gate independently records its evidence sources (typically the task contract path).

### 16.2 After Optimization

If evidence is computed once and shared:
- Each gate should still record which shared evidence it consumed
- The shared evidence object should record its computation timestamp and source inputs
- The audit trail should include a `shared_evidence_id` referencing the snapshot
- This is **more auditable**, not less, because all gates reference the same evidence snapshot

### 16.3 Redaction

No change. Evidence computation doesn't involve secrets. Output redaction is handled at the CLI layer, not in evidence building.

## 17. Proposed Optimization Design

### Design C (Profiling-First) → Design A (GateDryRunContext)

**Recommended approach**: Two-phase implementation.

#### Phase 1 (88Y.3): Shared Evidence Context

Introduce a `GateDryRunContext` dataclass that:

1. Is created once at the start of `build_gate_dry_run()`
2. Lazily computes and caches all 6 build function results
3. Is passed to each `_evaluate_gate()` call
4. Contains pre-computed task_contract, git porcelain, branch, ahead_count

```python
@dataclass
class GateDryRunContext:
    repo_root: Path
    _artifact_index: dict | None = None
    _memory_snapshot: dict | None = None
    _governance_timeline: dict | None = None
    _decision_log: dict | None = None
    _risk_register: dict | None = None
    _project_state: dict | None = None
    _task_contract: dict | None = None
    _git_porcelain: str | None = None
    _git_branch: str | None = None
    _git_ahead_count: int | None = None
    
    @property
    def artifact_index(self) -> dict: ...
    @property
    def project_state(self) -> dict: ...
    # etc. — each property lazily computes once
```

#### Safety Properties

1. **Immutable within call**: Once computed, each property returns the same value
2. **No cross-call persistence**: Context is created fresh per `build_gate_dry_run()` invocation
3. **Decision equivalence**: Same inputs → same outputs; just computed once instead of 32×
4. **Auditability preserved**: Each gate still references its evidence sources; context records computation timestamp

#### Implementation Strategy

1. Extract each `build_*` function call into the context's lazy properties
2. Pass context to `_evaluate_gate()` instead of individual data structures
3. `_evaluate_gate()` accesses `ctx.task_contract` instead of calling `_detect_task_contract()`
4. `_evaluate_commit()` accesses `ctx.git_porcelain` instead of calling `_git_porcelain()`
5. `_evaluate_push()` accesses `ctx.git_branch` and `ctx.git_ahead_count` instead of calling helpers

## 18. Decision-Equivalence Test Strategy

### 18.1 Golden File Approach

1. Before optimization: run `build_gate_dry_run()` with all ~30 parameter combinations from existing tests
2. Serialize full output to JSON golden files
3. After optimization: run same parameter combinations
4. Assert bit-for-bit identical output (except `generated_at` timestamps)

### 18.2 Existing Test Preservation

All existing tests in `test_gate_dry_run.py`, `test_phase87_integration.py`, and related files must continue to pass with unchanged assertions.

### 18.3 Specific Equivalence Tests

```python
def test_optimized_context_produces_same_results():
    """build_gate_dry_run with and without shared context must match."""
    # Compare: direct call vs context-wrapped call
    # Strip timestamps, compare all gate decisions and reason codes

def test_context_lazy_properties_are_idempotent():
    """Each context property must return the same value on repeated access."""

def test_context_is_not_persisted():
    """Context must not write to disk or survive across calls."""

def test_all_gates_reference_shared_evidence():
    """Each gate output must include shared_evidence_id."""
```

## 19. Expected Runtime Reduction

| Metric | Current | After Optimization | Reduction |
|--------|---------|-------------------|-----------|
| build_artifact_index calls | 32 | 1 | 97% |
| build_memory_snapshot calls | 16 | 1 | 94% |
| build_governance_timeline calls | 8 | 1 | 87% |
| build_decision_log calls | 4 | 1 | 75% |
| build_risk_register calls | 2 | 1 | 50% |
| _detect_task_contract calls | 15 | 1 | 93% |
| Total subprocess calls | ~1,087 | ~18 | 98% |
| **Per-call runtime** | **~17s** | **~1-2s** | **88-94%** |

With optimization:
- `test_gate_dry_run.py` (29 tests): 459s → ~50-60s
- `test_phase87_integration.py` (30 tests): 485s → ~50-60s
- Slowest test (test_no_cache_or_state_created): 52s → ~5-8s

## 20. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Lazy property caching introduces statefulness | Low | Context is throwaway — created per call, garbage collected after |
| Cached git porcelain could be stale if repo changes mid-call | None | Single-threaded synchronous call; no state change possible |
| Different gates might need different evidence freshness | Low | All evidence is read-only within one call; no gate modifies state |
| Context object could grow unbounded | Low | Fixed set of properties; no accumulation |
| Optimization could mask bugs in build functions | Low | All existing tests continue to pass; golden-file comparison added |
| Context could be accidentally persisted | Low | Design explicitly forbids persistence; tests verify |

## 21. Deferred Items

- **Cross-invocation caching**: Explicitly deferred. Too risky. Each CLI command must see fresh state.
- **Parallel gate evaluation**: Not needed. Gate evaluation is < 0.2% of runtime. Parallelism adds complexity with no measurable benefit.
- **Git data caching daemon**: Future direction, not in scope.
- **Incremental timeline updates**: Governance timeline could be incrementally updated instead of recomputed from scratch, but this would require persistent state — deferred until storage infrastructure exists.
- **permission_broker_gate implementation**: Deferred per existing roadmap.
- **shell_command_gate implementation**: Deferred per existing roadmap.

## 22. Recommended Next Phase

**88Y.3 — Gate Dry-Run Shared Evidence Prototype**

Implement the `GateDryRunContext` as a lazy-loading dataclass in `src/pcae/core/gate_dry_run.py`. Modify `build_gate_dry_run()` and `_evaluate_gate()` to use the shared context. All 6 build functions remain callable standalone (backward compatible). Add golden-file decision equivalence tests. Expected: reduce per-call runtime from ~17s to ~1-2s without changing any gate decision.

If profiling had shown that optimization is unsafe (which it did not), the alternative would have been:

88Y.3 — Gate Dry-Run Profiling Tooling (add optional --profile flag, collect per-gate timing, no runtime optimization)

But the profiling results clearly show that the optimization is safe: the cascading calls compute **identical** data 32×, and memoizing within a single call carries zero risk of staleness.
