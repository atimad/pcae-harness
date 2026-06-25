# Phase 88N.2 Full Suite Runtime Optimization and Test-Run Lock

## 1. Purpose

Profile PCAE test suite runtime, identify hotspots, clarify validation tier
definitions, and add `pcae doctor test-run` — a read-only preflight that detects
active expensive pytest (xdist) runs to prevent overlapping full-suite executions.

## 2. Scope

Phase 88N.2 delivers:

- `pcae doctor test-run` command (read-only preflight, no test execution).
- 14 tests in `tests/test_doctor_test_run.py`.
- Runtime profiling findings.
- Validated and updated validation tier definitions.
- This documentation artifact.
- Updates to `PROJECT_STATUS.md` and `CHANGELOG.md`.

## 3. Non-Goals

- Permission broker implementation.
- Shell gate implementation.
- Shell interception.
- Backend invocation.
- Broad test optimization refactor (targeted improvements only).
- Modifying task-finish behavior beyond the fix already in 88N.1.
- Starting, killing, or managing test processes.
- Persistent lock files.
- Test marking changes (existing `slow` / `integration` / `phase_closure` markers retained).

## 4. Problem Statement

During Phase 88M, multiple overlapping `pytest -n auto` runs produced contaminated
results. A background run from a previous invocation was still active when a new full
suite was started. The overlap caused one run to see incorrect results because both
runs competed for shared resources, timing, and process slots.

PCAE had no mechanism to detect or prevent such overlap. The operator had to guess
whether a run was active, and tests from a clean run could not be reliably distinguished
from a contaminated run.

Additionally, quick-tier runtime grew to ~4 minutes at 6,998 tests. The sequential
(non-parallel) runtime for the same tier is ~18 minutes, which risks accidental
slow iteration if `-n auto` is omitted.

## 5. 88M Overlapping Full-Suite Incident

During Phase 88N.2 profiling, the overlapping run problem recurred:

1. A background quick-tier profiling run (`-m "not slow and not phase_closure" --durations`)
   was started without `-n auto`, running sequentially for ~18 minutes.
2. While that run was active, a second background invocation was inadvertently started.
3. `pcae doctor test-run` was used to check for active xdist processes and confirmed
   the environment before the next governed test run.

This confirmed both the need for the preflight and a subtle edge case: runs without
`-n` are not detected by `pcae doctor test-run` (which targets xdist parallel runs),
because they do not use the `-n <count>` flag. The current implementation is conservative
for xdist runs specifically.

## 6. Current Validation Tiers

Defined in `pyproject.toml` (Phase 88D.1 comment block):

| Tier | Command | Tests | Approx. Time (parallel) |
|------|---------|-------|------------------------|
| targeted | `python -m pytest tests -k <pattern> -q` | varies | seconds |
| quick | `python -m pytest -m "not slow and not phase_closure" -n auto` | 6,998 | ~4 minutes |
| governance | `python -m pytest -m "integration or slow" -n auto` | 707 | ~2-4 minutes |
| full | `python -m pytest -n auto` | 7,705 | ~4-6 minutes |

Note: without `-n auto`, quick tier runs sequentially and takes ~18 minutes.
Always use `-n auto` for quick tier and full suite unless specifically debugging.

## 7. Proposed Validation Tiers

Refined tier guidance for Phase 88 and beyond:

| Tier | When to use | Blocking? |
|------|-------------|-----------|
| **targeted** | After a narrow source/test change; run only directly affected tests | no |
| **quick** | After any source change; fast sanity check | yes (required before commit) |
| **governance** | After lifecycle/preflight/check/health/doctor changes; slow+integration | preferred |
| **integration** | When testing CLI subprocess behavior, multi-command scenarios | preferred |
| **full** | After changes to shared source; before `pcae push` on source-modifying phases | preferred |

**Full suite policy:**
- Run once, foreground, non-overlapping.
- Always preceded by `pcae doctor test-run` to confirm no active run.
- If deferred, the report must state: source changed yes/no, targeted result,
  quick result, reason for deferral, prior clean full-suite baseline.

## 8. Profiling Method

Profiling was performed using:

```
python -m pytest -m "not slow and not phase_closure" --durations=30 -q
```

This produces the 30 slowest test durations without starting a separate full suite.
The command was run sequentially (no `-n auto`) to measure per-test times without
parallel scheduling effects.

Note: this sequential profiling command took ~18 minutes — confirming that always
using `-n auto` is critical for practical development speed.

## 9. Runtime Findings

Top hotspot by file: `test_project_state.py`

| File | Tests | Avg duration (sequential) | Total (est.) | Root cause |
|------|-------|--------------------------|--------------|------------|
| `test_project_state.py` | 21 | ~8.4s | ~176s | Subprocess CLI; `pcae project-state` invokes many intelligence commands |
| `test_risk_register.py` | multiple | ~8.5-8.8s | ~50s+ | Subprocess CLI; determinism/ordering checks across full runs |

Slowest individual tests (sequential, no xdist):
- `test_project_state_next_safe_actions_present` — 8.97s
- `test_risk_register_risk_ids_stable` — 8.80s
- `test_risk_register_risks_are_deterministic` — 8.77s
- `test_risk_register_risks_ordered_deterministically` — 8.64s

These are all already marked `slow` and excluded from the quick tier. With `-n auto`,
they are distributed across workers and do not dominate wall-clock time.

## 10. Subprocess-Heavy Hotspots

Files with the most subprocess calls (proxy for slowness):

| File | Subprocess calls | Tests |
|------|-----------------|-------|
| `test_agent.py` | 33 | 4,236 |
| `test_task.py` | 18 | 135 |
| `test_lifecycle_regression.py` | 14 | ~20 |
| `test_push.py` | 13 | 34 |
| `test_commit_push_preflight.py` | 13 | ~35 |

`test_agent.py` is by far the largest file (4,236 tests) and uses 33 subprocess
invocations. Most of its tests use direct function calls rather than subprocess, so
the 33 subprocess calls are spread across the entire file and not per-test.

## 11. Optimization Changes Made

Phase 88N.2 makes targeted improvements rather than a broad refactor:

| Change | Rationale |
|--------|-----------|
| Add `pcae doctor test-run` | Detect overlapping xdist runs before starting new full suite |
| 14 tests covering clear/busy/no-mutate/error-handling/shell-filter | Ensure preflight behavior is governed |
| Refine tier documentation in `docs/` | Reduce ambiguity about when to use which tier |

No existing tests were deleted. No test marks were changed. The quick tier test count
(6,998) is unchanged.

## 12. Test-Run Lock/Preflight Behavior

`pcae doctor test-run` is a read-only diagnostic preflight:

| Property | Value |
|----------|-------|
| Command | `pcae doctor test-run [--json]` |
| Read-only | yes |
| Detects | Active `python -m pytest -n <count>` or `pytest -n auto` processes via `ps aux` |
| Does not detect | Sequential pytest runs (no `-n` flag); this is a known limitation |
| Does not kill | Any process |
| Does not start | Any test |
| Does not write | Any file |
| Conservative | false positive (busy when clear) is acceptable; false negative is more dangerous |
| On ps failure | Reports `clear_to_run=true` (cannot detect, so cannot block) |

**JSON output fields:**

| Field | Type | Description |
|-------|------|-------------|
| `check` | string | `"test_run_preflight"` |
| `clear_to_run` | boolean | `true` if no active xdist process detected |
| `active_pytest_process_count` | integer | Count of matching processes |
| `active_pytest_processes` | list[string] | Command lines of matching processes |
| `policy` | string | Human-readable policy description |

**Detection logic:**
For each line in `ps aux` output:
1. Exclude lines containing `ps aux` or `grep` (avoid self-detection).
2. Extract the COMMAND field (column 10 from `split(None, 10)`) — the executable and its arguments.
3. Exclude lines whose COMMAND starts with a shell interpreter (`/bin/sh`, `/bin/bash`, `/bin/zsh`, etc.) — these are shell wrappers that may have pytest in their `eval` args but are not themselves running pytest. Prevents false positives when pcae doctor test-run is invoked as `pcae doctor test-run && python -m pytest -n auto` in a shell eval.
4. Check for `pytest` or `py.test` in the COMMAND field (is it a pytest run?).
5. Check for `-n\s*(auto|\d+)` regex in COMMAND (is it an xdist parallel run?).
6. If both: include in matches.

## 13. Safety Policy

1. `pcae doctor test-run` never starts tests.
2. `pcae doctor test-run` never kills processes.
3. `pcae doctor test-run` never writes files.
4. `pcae doctor test-run` never mutates the repository.
5. `pcae doctor test-run` never invokes backends.
6. If `ps` fails, report `clear_to_run=true` (cannot detect → cannot block).
7. False positives (busy-when-clear) are acceptable; they cause the operator to wait.
8. False negatives (clear-when-busy) are more dangerous; they allow overlap.
9. The operator decides whether to proceed, wait, or stop existing runs.
10. Automatic test execution is forbidden.

## 14. Full-Suite Policy

**Before running full suite:**
```
pcae doctor test-run
```
Verify `clear_to_run=true` before starting `python -m pytest -n auto`.

**Full suite command:**
```
python -m pytest -n auto
```

**Rules:**
- Run once, foreground, non-overlapping.
- Do not run multiple full suites concurrently.
- Always use `-n auto` for practical speed (~4-6 min vs ~18+ min sequential).
- If full suite is deferred, document: source changed, targeted result, quick result, reason, prior baseline.

**Prior clean full-suite baseline:** 7,640 passed (from Phase 88L.1, pre-88M changes).

## 15. False-Positive/False-Negative Policy

| Scenario | Risk | `pcae doctor test-run` behavior |
|----------|------|--------------------------------|
| No active xdist run | none | `clear_to_run=true` ✓ |
| Active xdist run detected | overlap risk | `clear_to_run=false`, shows process details ✓ |
| Active sequential run (no `-n`) | overlap risk | `clear_to_run=true` (not detected) — known gap |
| `ps` fails | unknown | `clear_to_run=true` — conservative degradation |
| Stale process entry in ps | false positive | `clear_to_run=false` — operator must check |

The gap for sequential runs (no `-n`) is documented and acceptable: sequential runs
are slower and less common in practice; the primary concern is xdist parallel runs.

## 16. Remaining Limitations

- Sequential pytest runs (no `-n`) are not detected. This is by design — `ps` detection
  is focused on expensive parallel runs. A future improvement could detect any pytest run.
- `ps aux` output format varies across OS (macOS vs Linux). The current implementation
  is tested on macOS (`ps aux` format). Linux `ps aux` produces a similar format.
- No persistent lock file: the preflight is stateless. If `ps` is unavailable, no
  lock can be checked. A future improvement could use a pid-file approach.
- The preflight does not block execution: it reports a recommendation. The operator
  must act on it. A future shell gate integration could enforce the policy.

## 17. Recommended Next Phase

**88O — Shell Gate Design Reconciliation**

Following 88N (broker design reconciliation), 88N.1 (task-finish robustness), and 88N.2
(test-run lock), the next strategic step is reconciling the Phase 87 shell gate
architecture with the explicit Phase 88 preflight and broker models. The shell gate
is the enforcement layer that complements the broker's policy decisions.

---

full_suite_runtime_optimization_name=phase_88_full_suite_runtime_optimization
full_suite_runtime_optimization_version=0.1
full_suite_runtime_optimization_status=implemented
implementation_status=complete
new_command=pcae_doctor_test_run
tests_added=14
subprocess_hotspot_files=test_project_state.py,test_risk_register.py,test_agent.py
quick_tier_count=6998
full_suite_count=7705
slow_tier_count=707
profiling_sequential_duration_s=1064
recommended_next_phase=88O_shell_gate_design_reconciliation
backend_invocation_performed=false
execution_authorized=false
permission_broker_implemented=false
shell_gate_implemented=false
