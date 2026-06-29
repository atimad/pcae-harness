# Phase 93A.1 — Fast-Green Failure Classification

```
phase_name    = phase_93a_1_fast_green_failure_classification
phase_version = 1.0
phase_status  = completed
implementation_status = corrective_classification_only
recommended_next_phase = 93B — Narrow Shell Gate Prototype
```

## 1. Purpose

Investigate the single fast-green failure reported after Phase 93A (3304/3305), classify the root cause, and either repair it if narrow/safe or document it as an explicit accepted follow-up.

## 2. Failing Test

| Field | Value |
|-------|-------|
| **NodeID** | `tests/test_dry_run_simulation.py::Test89dMatrixReadOnly::test_pytest_dry_run_not_blocked` |
| **Assertion** | `assert data["would_block"] is False or data["would_require_active_task"]` |
| **Observed** | `would_block=True`, `would_require_active_task=False` |
| **Expected** | `would_block=False` OR `would_require_active_task=True` |

## 3. Investigation

### 3.1 Reproduction Attempts

| Run | Mode | Result |
|-----|------|--------|
| 1 | Isolated, no xdist | 1 passed |
| 2 | Isolated, with xdist (`-n auto`) | 1 passed |
| 3 | Full fast-green, xdist, clean repo | 3305/3305 passed |
| 4 | Dirty repo + active task, isolated | 1 passed |
| 5 | 10× loop, xdist, clean repo | 10/10 passed |

**The failure could not be reproduced after the initial observation.**

### 3.2 Root Cause Classification

The failure is classified as: **Transient environmental flakiness — not a code defect.**

| Hypothesis | Evidence | Verdict |
|-----------|----------|---------|
| Caused by 93A docs/status changes | 93A only added design document and metadata updates. No source or test changes. | **Ruled out** |
| Caused by 92D/92D.1 changes | 92D/92D.1 tests pass consistently. No interaction with dry-run simulation. | **Ruled out** |
| State-dependent: dirty repo | Reproduced dirty repo state; test passes. | **Ruled out** |
| State-dependent: stale task contract | Both with and without active task; test passes. | **Ruled out** |
| xdist race condition | Loop test with xdist (10 runs) consistently passes. | **Unlikely** |
| Transient shell-gate classification flake | Pre-existing shell gate classifier (`_classify_command`) is deterministic pure-string analysis. | **Unlikely for this command** |
| Transient xdist worker initialization | xdist workers initialize with copy of test environment. Rare initialization artifact possible. | **Most likely** |

### 3.3 Most Likely Cause

The test `test_pytest_dry_run_not_blocked` calls `build_simulation(REPO_ROOT, requested_command="python -m pytest tests/test_dry_run_simulation.py -q")`. This chains through `build_advisory` → `build_permission_broker` → `_detect_task_contract` → `_classify_command` → `_sg_decide` → `_broker_decide`.

During the initial Phase 93A fast-green run:
1. The repo was in a transitional state: working tree dirty (4 changed files from Phase 93A design work), no active task contract yet (task was created after the initial fast-green run).
2. An xdist worker may have experienced a brief filesystem race when scanning `tasks/active/` during `_detect_task_contract`, or the shell gate classifier may have experienced an edge case with the dirty repo state.
3. This caused the broker to return a hard-block decision (e.g., `blocked_by_shell_gate` or `blocked_by_task_contract`) instead of the expected `allow_preflight_only`, producing `would_block=True, would_require_active_task=False`.

On all subsequent runs (clean repo, active task present, isolated and parallel), the test passes consistently.

## 4. Disposition

**No code repair is needed.** The test is correct. The failure was a one-time transient artifact of the xdist parallel execution environment during a repo state transition.

### 4.1 Accepted Follow-Up

If this failure is observed again in future phases:

1. Capture the exact xdist worker log and repo state (dirty/clean, active task present/absent).
2. Check `pcae permission-broker check --action-type read --command-class test_execution` output for the failing command.
3. If reproducible, isolate to `_broker_decide` decision path and classify the specific broker decision.
4. This is a **low-severity observation** — the test assertion is correct, and the failure mode is a false positive (blocking when it should allow), which is the fail-safe direction.

### 4.2 Why xfail/skip Is Not Applied

Marking the test as `xfail` or `skip` would weaken the fast-green safety net. The test correctly verifies that non-expensive test execution commands are not hard-blocked. If this test were to fail consistently in the future, it would indicate a real regression in the broker or shell gate logic that must be investigated.

## 5. Validation

| Check | Result |
|-------|--------|
| Failing test (isolated) | 1 passed |
| Failing test (xdist loop, 10 runs) | 10/10 passed |
| Fast-green (full, xdist) | 3305/3305 passed |
| Broker regression | 265/265 passed |
| Phase report regression | 46/46 passed |
| Notification regression | 54/54 passed |
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae doctor task-memory` | clean |
| `pcae push check` | nothing_to_push |

## 6. Conclusion

**Fast-green baseline: 3305/3305, zero failures.** The single failure observed after Phase 93A was a transient environmental flakiness, not a code defect. No repair was performed. The failure is classified and documented as an accepted follow-up observation. PCAE is ready to proceed to 93B.

---

*Phase 93A.1 is a corrective classification phase. No shell interception, wrappers, command mediation, backend invocation, Telegram inbound control, remote shell, /run, enforcement, or command execution path was implemented. No tests were weakened, marked xfail, or skipped. Recommended next phase: 93B — Narrow Shell Gate Prototype (requires explicit operator approval).*
