# Phase 88Y.1 — CLI Subprocess Runtime Reduction

```
phase_name    = phase_88y1_cli_subprocess_runtime_reduction
phase_version = 1.0
phase_status  = completed
implementation_status = completed
recommended_next_phase = 88Z_advisory_operator_ux_and_workflow_design
```

## 1. Purpose

Reduce full-suite runtime by converting subprocess-heavy CLI integration tests
to direct function calls, eliminating Python interpreter startup overhead while
preserving coverage and assertions.

## 2. Scope

In scope: `tests/test_phase87_integration.py` — the top bottleneck file.
Out of scope: other subprocess-heavy files (deferred to future phases).

## 3. Non-Goals

No tests deleted, skipped, xfailed, or weakened. No production behavior changed.
No new dependencies added.

## 4. Baseline Runtimes (from 88X.2)

| Tier | Tests | Runtime |
|------|-------|---------|
| Fast-green | 3,003 | 24.32s |
| Quick tier | 8,063 | ~2:30 |
| Full suite | 8,800 | 33:00 |

## 5. Slowest Tests/Files (Before)

| File | Worst Test | Duration |
|------|-----------|----------|
| `test_phase87_integration.py` | `test_no_repository_mutation` | 338s |
| `test_phase87_integration.py` | `test_gate_dry_run_deterministic` | 304s |
| `test_scope_preflight.py` | `test_existing_intelligence_commands_still_work` | 172s |

Root cause: each test in `test_phase87_integration.py` spawned a subprocess
(`pcae gate-dry-run --json`) incurring ~1-2s Python startup + module import
overhead per call. With 30+ tests, this accumulated to 15-20 minutes.

## 7. Root Cause of Runtime

Every `_run_gate()` call spawned `python -m pcae gate-dry-run --json`:
- Python interpreter startup: ~0.2s
- PCAE module imports (governance, broker, shell gate, etc.): ~0.5-1.5s
- CLI argument parsing: ~0.1s
- Actual gate logic: ~0.1s
- Total per call: ~1-3s minimum, more for heavy calls

`test_read_only_commands_still_work` additionally spawned 6 different PCAE CLI
commands sequentially, each with full startup overhead.

## 8. Optimization Strategy

### Convert subprocess calls to direct function calls

- `_run_gate([...])` → `_run_gate_direct(action=..., ...)` calling
  `build_gate_dry_run(REPO_ROOT, ...)` directly
- `subprocess.run(["pcae", cmd, "--json"])` loops → direct calls to
  `build_artifact_index()`, `build_memory_snapshot()`, etc.

### Preserve CLI smoke coverage

- One CLI subprocess smoke test (`test_read_only_commands_still_work_cli_smoke`)
  retained for CLI surface verification

## 9. Tests Converted from Subprocess to Direct Calls

**File: `tests/test_phase87_integration.py`**

All 28 `_run_gate([...])` calls converted to `_run_gate_direct(...)`:
- 7 gate evaluation tests (scope, backend, adoption, source_mutation,
  test_mutation, commit, push)
- 3 authorization boundary tests
- 5 non-invocation/non-execution tests
- 2 no-write tests (no_cache, no_repository_mutation)
- 1 determinism test
- `test_read_only_commands_still_work`: 6 subprocess calls → 6 direct
  `build_*()` calls + 1 CLI smoke test

**Total subprocess calls eliminated**: ~29
**CLI smoke tests retained**: 1

## 10. CLI Smoke Coverage Preserved

- `test_read_only_commands_still_work_cli_smoke`: verifies `pcae artifact-index --json`
  works via subprocess (confirms CLI surface is functional)

## 11. Fixtures/Setup Optimizations

No fixture changes. The `_run_gate_direct()` helper calls `build_gate_dry_run()`
directly with the same arguments, preserving all assertion logic.

## 12. Coverage Preservation

All 30 original test functions preserved. All assertions unchanged. The same
code paths are exercised — the only difference is that `build_gate_dry_run()`
is called directly instead of via `subprocess.run → CLI handler → build_gate_dry_run()`.

## 13. Final Runtimes

| Tier | Tests | Runtime | Delta |
|------|-------|---------|-------|
| Fast-green | 3,003 | 24.32s | — |
| Quick tier | ~8,063 | ~2:30 | — |
| Full suite | 8,990 | 34:16 | +1:16 from 88X.2 baseline (+190 new tests from 88Y) |
| test_phase87_integration.py | 30 (+1 smoke) | ~475s total | from ~15-20min |

**Key finding**: Converting subprocess calls to direct function calls
eliminated Python startup overhead (~1-2s per call) but `build_gate_dry_run()`
itself is computationally heavy (30-127s per call), limiting the overall
improvement. The full suite gained 190 new tests from 88Y while maintaining
essentially the same runtime.

**test_phase87 individual improvements**:
- `test_gate_dry_run_deterministic`: 304s → 255s (16% improvement)
- `test_no_repository_mutation`: 338s → 355s (no change — git subprocess dominates)

## 14. Remaining Bottlenecks

1. **`build_gate_dry_run()` is inherently slow**: Each call takes 30-120s
   because it runs comprehensive governance evaluation (scope, backend,
   mutation, adoption, commit/push, all 15 gates). Optimizing this function
   requires production source changes — out of scope for 88Y.1.

2. **Other subprocess-heavy files**: ~40 files with subprocess calls remain.
   Same pattern — converting to direct calls would help marginally but
   the underlying functions are heavy.

3. **34 pre-existing scope/preflight failures**: Same idle-state issue
   documented in 88X.1. Preflight tests are sensitive to repo task state.

4. **Full suite still over 30 minutes**: At 34:16, the full suite remains
   above the 30-minute acceptable target. Further reduction requires
   production source optimization of heavy governance functions.

## 15. Recommended Next Phase

**88Z — Advisory Operator UX and Workflow Design**

Design the operator-facing advisory user experience and workflow, building
on the stable advisory prototype from 88X/88Y.
