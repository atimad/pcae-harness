# Phase 88N.4 Full Suite Bottleneck Elimination

## 1. Purpose

Reduce the practical cost of full validation by identifying and addressing the main
full-suite runtime bottlenecks, while preserving coverage and keeping the full-suite
baseline green. The 88N.3 full suite ran in 29 minutes (1,693s) on M5 Pro — too slow
for practical governed development before shell-gate design/implementation expands the
suite further.

## 2. Scope

Phase 88N.4 delivers:

- Module-scoped fixture optimization in 4 bottleneck test files:
  - `tests/test_project_state.py`
  - `tests/test_risk_register.py`
  - `tests/test_decision_log.py`
  - `tests/test_governance_timeline.py`
- This documentation artifact.
- Updates to `PROJECT_STATUS.md` and `CHANGELOG.md`.

No new CLI commands. No new source files. No schema changes. No storage.
No test cases deleted. No tests weakened.

## 3. Non-Goals

- Permission broker implementation.
- Shell gate implementation (88O, deferred).
- Changes to any PCAE source files (core, commands, cli).
- Weakening test assertions.
- Deleting meaningful test coverage.
- Marking tests as slow/xfail solely to reduce runtime.
- Optimizing test_agent.py 44c capability-discovery tests (capsys-bound; lower priority
  given gains already achieved).

## 4. Baseline Before Optimization

### 4.1 Full Suite

```
python -m pytest -n auto
7,719 passed in 1,693s (0:28:13)
```

### 4.2 Quick Tier

```
python -m pytest -m "not slow and not phase_closure" -n auto
7,012 passed in 327.60s (0:05:27)
```

## 5. Profiling Method

1. `python -m pytest -m "not slow and not phase_closure" -n auto -ra --durations=100`
   with output teed to `/tmp/pcae-quick-88n4.log`.
2. Inspection of `--durations` output to identify slowest tests by file and test name.
3. Grep-based analysis of subprocess patterns in bottleneck files.
4. Targeted run of the four bottleneck files in isolation (no -n auto) with `--durations=20`
   to confirm fixture behavior before/after.

## 6. Slowest Tests / Files Before Optimization

| File | Tests | Avg duration (per test) | Total est. |
|------|-------|-------------------------|-----------|
| test_project_state.py | 34 | 13–30s | ~580s |
| test_risk_register.py | 31 | 9–18s | ~400s |
| test_decision_log.py | 28 | 10–16s | ~340s |
| test_governance_timeline.py | 22 | 10–11s | ~220s |

Combined: ~115 tests, ~1,540s sequential equivalent — each was an individual subprocess
call taking 7–30s regardless of what field it was checking.

## 7. Subprocess-Heavy Hotspots

All four files shared the same anti-pattern: a private `_run_<command>_json()` helper
function that each test called independently, spawning a fresh Python subprocess per
assertion:

```python
def _run_project_state_json() -> dict:
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "project-state", "--json"],
        capture_output=True, text=True, cwd=...,
    )
    assert result.returncode == 0, ...
    return json.loads(result.stdout)

def test_project_state_schema_version():
    data = _run_project_state_json()   # fresh subprocess
    assert data["schema_version"] == "0.1"
```

For tests only checking a single field of the JSON envelope, starting a full Python
process (~1–2s overhead) plus running a command that scans docs, git history, and
governance artifacts (~5–15s per command) per assertion is the core inefficiency.

In addition, determinism tests (e.g., `test_risk_register_risks_are_deterministic`)
called the helper **twice** per test — six subprocess calls for three determinism tests
that could share two runs.

## 8. Fixture / Setup Hotspots

The commands themselves are slow because they are comprehensive read-only governance
scans:

| Command | Why slow |
|---------|----------|
| `pcae project-state` | Reads artifact-index, governance-timeline, decision-log, risk-register, memory-snapshot, git history |
| `pcae risk-register` | Reads artifact-index, governance-timeline, decision-log, memory-snapshot |
| `pcae decision-log` | Reads artifact-index, governance-timeline, memory-snapshot |
| `pcae governance-timeline` | Reads artifact-index, memory-snapshot |

These are inherently expensive governance scans. The fix is not to change them but to
run each once per test session worker rather than once per test.

## 9. Optimizations Performed

### 9.1 Module-Scoped Fixture per Command

Each bottleneck file now has a `@pytest.fixture(scope="module")` that runs its command
once per worker and caches the result. All field-checking tests use the fixture:

```python
@pytest.fixture(scope="module")
def _project_state() -> dict:
    """Run project-state once per worker; all field-checking tests share the result."""
    return _run_project_state_json()

def test_project_state_schema_version(_project_state) -> None:
    assert _project_state["schema_version"] == "0.1"
```

### 9.2 Determinism Fixture Pair

Determinism tests that previously called the helper twice each now share a second
module-scoped fixture `_<name>_data2()`. Three determinism tests that previously made
six subprocess calls (2 each) now make two total per worker:

```python
@pytest.fixture(scope="module")
def _risk_data2() -> dict:
    """Second independent run for determinism tests."""
    return _run_risk_register_json()

def test_risk_register_risks_are_deterministic(_risk_data, _risk_data2) -> None:
    ids1 = [r["risk_id"] for r in _risk_data["risks"]]
    ids2 = [r["risk_id"] for r in _risk_data2["risks"]]
    assert ids1 == ids2
```

### 9.3 Tests Preserved with Own Subprocess

Tests with specific pre/post state-checking requirements keep their own subprocess calls.
These tests verify behavioral properties (no repo mutation, no cache creation) that
require running the command in an instrumented context:

- `test_*_no_cache_files_created` — checks directory existence before and after
- `test_*_no_repository_files_created` — checks git porcelain status before and after

### 9.4 Cross-Command Smoke Tests Unchanged

"Still works" cross-command smoke tests at the end of each file (e.g., `test_artifact_index_still_works`
in `test_project_state.py`) retain their own subprocess calls since they test different
commands and cannot share the primary module fixture.

### 9.5 Module-Level Constant for Repository Root

Replaced repeated `Path(__file__).resolve().parent.parent` calls in each test with a
module-level `_REPO_ROOT` constant to avoid repeated Path resolution.

## 10. Coverage Preservation Statement

- No test cases deleted.
- No assertions weakened or removed.
- No tests marked slow, skip, or xfail for speed.
- All field-checking tests continue to verify the same fields in the same way — they
  now receive their input from a module-scoped cached result instead of a per-test
  subprocess.
- No-mutation and no-cache tests retain independent subprocess calls so they continue
  to verify behavioral invariants correctly.
- Determinism tests still compare two independent command runs — they now share
  module-scoped runs rather than creating per-test runs.

## 11. Before / After Runtime Comparison

### Quick Tier

| Metric | Before | After |
|--------|--------|-------|
| Total time | 5:27 (327s) | 2:21 (142s) |
| Speedup | — | **2.3×** |
| test_project_state top test | 30s/test | fixture once per worker |
| test_risk_register top test | 18s/test | fixture once per worker |
| test_decision_log top test | 16s/test | fixture once per worker |
| test_governance_timeline top test | 11s/test | fixture once per worker |

### Full Suite

| Metric | Before (88N.3) | After (88N.4) |
|--------|----------------|---------------|
| Total time | 28:13 (1,693s) | 23:20 (1,401s) |
| Passed | 7,719 | 7,719 |
| Failures | 0 | 0 |
| Improvement | — | **−5 min (17%)** |

## 12. Remaining Bottlenecks

### 12.1 test_agent.py — 44c Capability Discovery Tests

23 tests (`test_44c_capability_discovery_*`, `test_44c1_*`) call
`main(["capability-discovery"])` in-process, which probes for external agents via real
subprocesses (~4–5s per test). These tests use `capsys` (function-scoped fixture) which
prevents the module-scoped fixture pattern without restructuring.

These tests contribute ~23 × 4.5s = ~103s sequential. With -n auto parallelism they
distribute across workers, so their per-suite contribution is lower. Low priority given
the larger wins already achieved.

### 12.2 Cross-Command Smoke Tests

Each file has 2–5 "still works" tests that run separate commands (artifact-index,
memory-snapshot, governance-timeline, decision-log, risk-register). These 15 tests
(spread across four files) call commands that take 1–5s each. These could be
deduplicated across files since the same commands are tested in their own dedicated
files. However, removing them would weaken integration verification that shows one
command doesn't break another. Deferred.

### 12.3 test_*_no_files_created and test_*_no_repository_files_created

8 tests (2 per file × 4 files) must run their own subprocess calls by design. Each
takes 7–11s. Total: ~75s sequential. These verify behavioral invariants that cannot
be asserted from cached fixture data. No further optimization possible without
changing the behavior being tested.

### 12.4 test_scope_preflight_review.py (63 slow tests)

63 tests all marked `slow` and `integration`. Each calls `python -m pcae preflight scope`
as a subprocess. These tests are excluded from the quick tier. They run in the full
suite at ~37s total (with -n auto parallelism). Not a significant bottleneck.

## 13. Full Suite Policy After 88N.4

- Full suite must be preceded by `pcae doctor test-run --json` confirming `clear_to_run: true`.
- Run with: `python -m pytest -n auto -ra --durations=150`
- Do not run more than one full suite at a time.
- Quick tier command: `python -m pytest -m "not slow and not phase_closure" -n auto`
- Quick tier target: under 3 minutes on M5 Pro.

## 14. Recommended Next Phase

**88O — Shell Gate Design Reconciliation**

With the full-suite runtime materially reduced, 88O can proceed. 88O should reconcile
the Phase 87 shell gate architecture with the concrete Phase 88 explicit preflight layer,
define how a future shell gate interacts with scope preflight results, and document the
boundary between read-only preflight and execution control — without implementing the
gate.

---

bottleneck_elimination_name=phase_88n4_full_suite_bottleneck_elimination
bottleneck_elimination_version=0.1
bottleneck_elimination_status=implemented
baseline_full_suite_runtime_before=1693s
baseline_full_suite_runtime_after=1401s
full_suite_improvement=292s_17pct
quick_tier_before=327s
quick_tier_after=142s
quick_tier_speedup=2.3x
optimizations=module_scoped_fixtures
test_files_changed=4
tests_deleted=0
tests_skipped_or_xfail_for_speed=0
coverage_weakened=false
recommended_next_phase=88O_shell_gate_design_reconciliation
backend_invocation_performed=false
source_mutation_authorized=false
test_mutation_authorized=true_for_runtime_optimization_only
execution_authorized=false
