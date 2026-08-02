# Phase 148E — Permission Broker Production Consumption Implementation

## 0. Phase Type and Scope

**Phase type:** bounded production implementation of `PBPC-001` v1.2 for
`pcae push`. Implements exactly the design in `docs/PHASE_148D_PERMISSION_BROKER_PRODUCTION_CONSUMPTION_IMPLEMENTATION_PLAN.md`
Sections 5-33 against `PBPC-001` v1.2 and `PBPA-001` v1.0, both unamended
by this phase.

**Baseline commit:** `21a35087` (HEAD at phase start, tip of `Phase 148D:
close out task lifecycle, open idle placeholder`).

**Governing contracts (both read directly, both unamended by this
phase):**
- `PBPC-001` v1.2 — `docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`
- `PBPA-001` v1.0 — `docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`

**148C-B-1:** CLOSED (unchanged by this phase).

**Verdict:** Implementation **complete**. **Zero Blocking findings.**
`148F — Permission Broker Production Consumption Independent
Implementation Verification` is recommended next, per 148D Section 61.

---

## 1. Initial Inspection (read-only, reproduced results)

| Check | Result |
|---|---|
| `git status --short` | clean |
| `git status --branch --short` | `## main...origin/main` (no divergence) |
| `git rev-list --count origin/main..HEAD` | `0` |
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae doctor task-memory` | clean |
| `pcae push check` | `nothing_to_push` |
| `pcae runtime inspect` | Observed / observe / unavailable |
| `pcae phase-report show --latest` | 148D: completed, complete ✅, pushed, `origin/main..HEAD: 0` |
| `pcae phase-report reconcile --phase-id 148D` | reconciled, mutation: none (inspection only) |

Confirmed: repository clean; `origin/main..HEAD = 0`; 148D complete;
`PBPC-001` v1.2 unamended; `PBPA-001` v1.0 unamended; `148C-B-1` CLOSED;
`pcae push` production unwired before this phase (zero references to
`permission_broker_foundation` in `src/pcae/commands/push.py` at baseline);
runtime Observed / observe / unavailable.

---

## 2. Production Diff

**Production file changed (exactly one, matching 148D's file budget):**
`src/pcae/commands/push.py` — no other `src/pcae/**` file touched.

**Test files changed:**
- `tests/test_permission_broker_push_production_consumption.py` (new, 20 tests)
- `tests/test_staged_file_aware_push.py` (fixture updated: an active task
  contract is now created, since the Permission Broker's `POL-001`
  correctly requires one to reach `ALLOW`)
- `tests/test_permission_broker_observation_verification.py` (108D/109D-era
  invariant narrowed: `push.py` is now the one explicitly authorized
  exception per `PBPC-001` v1.2)
- `tests/test_permission_broker_verification_compatibility.py` (same
  narrowing, plus a new test asserting the exception stays scoped to
  `push.py` alone)

**Docs/bookkeeping:** this document; `PROJECT_STATUS.md`; `CHANGELOG.md`;
`tasks/DONE.md`; task-lifecycle artifacts.

`docs/contracts/` diff: empty (`git diff --name-only -- docs/contracts/`).
`src/pcae/core/permission_broker_foundation.py` diff: empty.
`src/pcae/core/permission_broker.py` diff: empty. `HARD_BLOCK_REGISTRY`
count re-derived: still `12`.

---

## 3. Control-Flow Re-Derivation (independently re-derived, not cited from 148D)

Re-read `src/pcae/commands/push.py` directly at phase start. Confirmed
against 148D's own Section 4 table with zero drift:

| | Path A — ordinary push | Path B — `--staged-file-aware` push |
|---|---|---|
| Function | `run_push()` | `_run_push_staged_file_aware()` |
| Dispatch line (pre-148E) | `push.py:454` | `push.py:604-612` |
| Dispatch command | `subprocess.run(["git", "push"], ...)` | `subprocess.run(["git", "push", "origin", "main"], ...)` |

**Direct dispatch bypass search** (repeated independently):
`grep -n "subprocess.run\|os\.system\|Popen\|shell=True" src/pcae/commands/push.py`
returns exactly the two dispatch lines plus non-dispatch calls for `git
diff --cached`, `git rev-parse`, `git diff --name-only`, `git log
--oneline`, `git merge-base`, `git diff-tree`, `git rev-list` — none of
which invoke `git push`. No shell wrapper, alias, `os.system`, `Popen`,
or generic "run git command" helper exists. **Exactly two real `git
push` dispatch sites confirmed, both pre- and post-implementation.**

---

## 4. Helper / Adapter Implementation

Added `_evaluate_push_permission(*, root, task_id, requested_resource=None,
broker=None) -> PushPermissionResult` in `src/pcae/commands/push.py`, as a
new private module-level function colocated with the other push-only
helpers (not a new `src/pcae/core/` module — per 148D Section 15, no
second production consumer exists to justify one).

Responsibilities (verified by direct source inspection):
1. Accepts canonical facts already gathered by the calling code
   (`task_id`, `requested_resource`).
2. Constructs exactly one `PermissionBrokerRequest` via the unmodified
   `build_permission_broker_request(...)` constructor.
3. Calls `PermissionBroker().evaluate(request)` (canonical default
   registry — `PermissionBroker(registry=None)` defaults to
   `PolicyRegistry()`, which defaults to `DEFAULT_POLICY_RULES`) exactly
   once.
4. Returns a structured `PushPermissionResult` (`authorized: bool`,
   `request`, `decision`, `broker_failure_reason`).
5. Performs **no** `git push` dispatch, **no** repository mutation, and
   duplicates **no** `POL-` logic — verified: the function body contains
   no `subprocess` call and no policy conditional.

A keyword-only, defaulted `broker` parameter exists solely for test
substitution (Section 51 of the 148D plan); every production call site
(`run_push`, `_run_push_staged_file_aware`) invokes the adapter with its
default (`broker=None` → canonical `PermissionBroker()`), never a
CLI-reachable custom registry.

---

## 5. Canonical Request — Field-by-Field, as Actually Constructed

Directly re-inspected (`_capture_requests` test spy, and manual
interactive verification):

| Field | Value | Provenance |
|---|---|---|
| `action_type` | `"push"` (`ACTION_PUSH`) | fixed literal, not user-selectable |
| `execution_class` | `"mutation"` (`EXECUTION_CLASS_MUTATION`) | fixed literal; no `--execution-class` flag exists |
| `requested_component` | `"COMP-001"` | fixed literal |
| `requested_capability` | `"pcae_push"` | fixed literal, distinct from the existing `"pcae_push_check"` INT-004 touchpoint |
| `task_id` | live | `find_latest_active_task(root)`, called at the guard site in both `run_push()` and `_run_push_staged_file_aware()` |
| `requested_resource` | `f"refs/heads/{readiness.branch}"` (Path A) / `"refs/heads/main"` (Path B) | existing readiness/branch facts |
| `evidence_available` | `True` | truthful — the adapter is only ever called after existing readiness/mechanical checks have already gathered evidence |
| `approval_present` | `False` | fixed; never derived from IWC, AESIC, task state, or any other "looks approved" signal |
| `simulation_only` | `True` | fixed; F-148C.8-1 protected by a dedicated regression test |

No field is fabricated to obtain `ALLOW`. Verified interactively against
the live, unmodified Foundation:

```
authorized: True
decision: ALLOW
non_applicable_policy_ids: ('POL-004',)
applicable_policy_ids: ('POL-001', 'POL-002', 'POL-003', 'POL-005',
  'POL-006', 'POL-007', 'POL-008', 'POL-009', 'POL-010', 'POL-011', 'POL-012')
request: action_type=push execution_class=mutation approval_present=False
  simulation_only=True
```

`POL-004` is `non_applicable` (per `PBPA-001` — `applicable_execution_classes`
excludes `mutation`), not applicability-voting-`ALLOW`. `approval_present`
remains `False` throughout.

---

## 6. Decision Consumption

Implemented exactly the 148D-specified table, verified by test and by
direct code inspection of both call sites:

```
ALLOW           -> continue to dispatch
DENY            -> abort; zero git push; diagnostics surfaced
HUMAN_REVIEW    -> abort; zero git push; no interactive resolution
broker failure  -> abort; zero git push; distinguished as BROKER_FAILURE
```

`_permission_denial_details()` distinguishes four categories cleanly:
`DENY` (with `causing_policy_ids`), `HUMAN_REVIEW` (same), `BROKER_FAILURE`
(exception message or `"invalid_broker_result"`), and pre-existing
mechanical/structural failures (unchanged, occur before the broker is
ever constructed).

---

## 7. Fail-Closed Behavior (verified interactively and by test)

| Failure injected | Result |
|---|---|
| `PermissionBroker.evaluate()` raises | `authorized=False`, `decision=None`, `broker_failure_reason=<message>` — zero dispatch |
| `evaluate()` returns a non-`PermissionBrokerDecision` object | `authorized=False`, `broker_failure_reason="invalid_broker_result"` — zero dispatch |
| Missing `task_id` (`POL-001`) | `DENY`, `causing_policy_ids=('POL-001',)` — zero dispatch |

No default-permissive branch exists anywhere in `_evaluate_push_permission`
or either call site's consumption logic.

---

## 8. Ordinary Path Wiring (`run_push()`)

Guard inserted strictly between the existing `dry_run` check and the
existing "EXECUTING REAL PUSH" banner / dispatch call — replacing
nothing, only inserting a new guard immediately before the real dispatch.
`--dry-run` continues to skip the broker entirely (no permission is
requested for an operation that never dispatches).

## 9. Staged-File-Aware Path Wiring (`_run_push_staged_file_aware()`)

Guard inserted strictly between the existing `dry_run` check and the
existing dispatch call — the identical shared helper, called a second
time with Path-B-specific `requested_resource`. All of this function's
existing early returns (`nothing_to_push`, `protected_file_in_unpushed_commits`,
`force_push_required`) occur **before** this insertion point; none of
them bypass the guard, since they already block dispatch mechanically.

---

## 10. Non-Bypassability

Both dispatch call sites are the *only* two `git push` invocations in
`push.py` (Section 3, re-confirmed post-implementation). Both receive the
identical Decision Consumption Point pattern. `test_ordinary_path_non_bypassable_for_every_non_allow_outcome`
and `test_staged_file_aware_non_bypassable_for_every_non_allow_outcome`
force both `DENY` and `HUMAN_REVIEW` against a real CLI invocation with a
`subprocess.run` spy and assert `dispatch_count == 0` in every case.
`test_staged_file_aware_mechanical_checks_still_block_before_broker`
additionally proves the pre-existing phase-report-identity mechanical
gate still blocks *before* any `PermissionBrokerRequest` is ever
constructed (`len(captured) == 0`).

---

## 11. Mechanical Checks, Hard-Block Registry, No Dual Authority

- All pre-existing mechanical/structural push checks (health, check,
  doctor, lifecycle review, phase-report trust, phase-report identity,
  protected-staged-file preservation, force-push-required detection)
  remain entirely unchanged and unconverted — none of them were
  reclassified as broker decisions.
- `HARD_BLOCK_REGISTRY` re-counted directly: still `12` entries,
  untouched.
- The Permission Broker owns exactly one new permission judgment (the
  canonical push request); existing mechanical/structural checks retain
  their existing, distinct ownership. No condition is judged twice by two
  independent authorities.

---

## 12. Diagnostics and Exit Codes

`DENY`/`HUMAN_REVIEW`/`BROKER_FAILURE` surface `decision`, `decision_reason`
(as `permission_reason`), and `causing_policy_ids` (JSON: additive keys
`permission_decision`, `permission_reason`, `permission_causing_policy_ids`;
text: `"Push blocked: ..."` plus a causing-policy-id line when present).
No internal broker state or secret material is included (none exists on
`PermissionBrokerDecision` to begin with). Exit codes unchanged: `0` on
success/nothing-to-push/dry-run, `1` on any not-ready/DENY/HUMAN_REVIEW/
broker-failure/git-error outcome — no new exit-code contract introduced.

---

## 13. Tests Added / Changed

**New:** `tests/test_permission_broker_push_production_consumption.py`
(20 tests): canonical request shape (both paths); ALLOW dispatches
exactly once (both paths); DENY blocks (both paths); HUMAN_REVIEW blocks
(both paths); broker exception blocks (both paths); invalid broker result
blocks; `POL-004` non-applicability regression; `POL-005`
`simulation_only=True` regression plus a Foundation-level
`simulation_only=False → DENY` regression; non-bypassability for every
non-ALLOW outcome (both paths); mechanical checks still block before the
broker is ever constructed; exactly-once broker evaluation (both paths);
no stale decision reuse across two logical push attempts.

**Changed:**
- `tests/test_staged_file_aware_push.py` — fixture (`_init_with_remote`)
  now creates an active task contract, since `POL-001` correctly denies
  a push with no active task; this is intentional, contract-correct
  behavior surfacing a pre-existing test gap, not a regression.
- `tests/test_permission_broker_observation_verification.py`,
  `tests/test_permission_broker_verification_compatibility.py` — the
  108D/109D-era invariant "no lifecycle command module ever imports the
  broker" is narrowed to exclude `push.py`, which `PBPC-001` v1.2
  explicitly and exclusively authorizes as of this phase.
  `commit.py`/`task.py`/`phase.py` remain asserted unwired.
  `test_broker_wiring_remains_scoped_to_push_only` (new) guards against
  silent future expansion of this one exception.

---

## 14. Test Results

- `tests/test_permission_broker_push_production_consumption.py`: 20/20 passed.
- `tests/test_push.py`, `tests/test_staged_file_aware_push.py`,
  `tests/test_commit_push_gate.py`,
  `tests/test_push_phase_report_identity_137f1.py`,
  `tests/test_permission_broker_foundation.py`,
  `tests/test_permission_broker_policy_applicability.py`,
  `tests/test_permission_broker_policy_composition_hardening.py`,
  `tests/test_permission_broker_policy_rule_framework.py`,
  `tests/test_phase_148c7_permission_broker_policy_applicability_independent_verification.py`,
  `tests/test_phase_148c8_permission_broker_production_consumption_b1_reevaluation.py`,
  `tests/test_permission_broker.py`, `tests/test_permission_broker_cli.py`,
  `tests/test_permission_broker_command_path_design.py`,
  `tests/test_permission_broker_command_path_prototype.py`,
  `tests/test_permission_broker_observation_hardening.py`,
  `tests/test_permission_broker_observation_verification.py`,
  `tests/test_permission_broker_verification_compatibility.py`,
  `tests/test_post_push_canonicalization.py`,
  `tests/test_push_state_reconciliation.py`: **1016/1016 passed**
  (full combined run, after the two intentional test-invariant updates
  in Section 13).
- Fast Green: `python -m pytest -m fast_green -n auto -q` — **4391
  passed, 0 failed** (identical to the pre-148E baseline count reported
  by 148D).
- `pcae runtime inspect`: Observed / observe / unavailable, unchanged
  before and after this phase.

---

## 15. Direct Dispatch Bypass Search (post-implementation re-confirmation)

Repeated Section 3's search after implementation:

```
grep -n "subprocess.run\|os\.system\|Popen\|shell=True" src/pcae/commands/push.py
```

Result: unchanged from Section 3 — exactly the same two `git push` lines
(now each immediately preceded by the broker guard), plus the same set of
non-dispatch `subprocess.run` calls. No third dispatch path was
introduced by this phase's changes.

---

## 16. Push Dispatch Inventory (final)

| Dispatch path | Source site | Broker evaluation | Required decision | Ungated path? |
|---|---|---|---|---|
| ordinary (`run_push`) | `push.py` (`["git", "push"]`) | yes, immediately before dispatch | `ALLOW` | no |
| staged-file-aware (`_run_push_staged_file_aware`) | `push.py` (`["git", "push", "origin", "main"]`) | yes, immediately before dispatch | `ALLOW` | no |

**Ungated dispatch site count: 0.**

---

## 17. Contract and Policy Boundary

- `git diff --name-only -- docs/contracts/`: empty. `PBPC-001` remains
  v1.2; `PBPA-001` remains v1.0.
- `git diff --name-only -- src/pcae/core/permission_broker_foundation.py
  src/pcae/core/permission_broker.py`: both empty. No `POL-001..012`
  evaluator meaning changed; no `POL-013+` added.
- `HARD_BLOCK_REGISTRY`: still 12 entries, unmodified.
- No caller-selectable policy set was introduced (`exclude_policies`,
  `selected_policy_ids`, `skip_policy`, `--execution-class`, or
  equivalent do not exist anywhere reachable from the `pcae` CLI).

---

## 18. IWC / AESIC / Runtime Enforcement Independence

- **IWC:** no confirmation lookup was added anywhere in the adapter or
  either dispatch path. `approval_present` is never derived from task
  state, review status, or any "looks approved" signal.
- **AESIC:** Authority Evaluation is not referenced anywhere in request
  construction or dispatch eligibility.
- **Runtime Enforcement:** `pcae push` remains a direct command-path
  integration; `pcae runtime inspect` confirmed Observed / observe /
  unavailable, unchanged before and after this phase. No new Runtime
  Enforcement dependency was introduced.
- **No durable broker artifact:** no `permission_decision.json` or
  equivalent was added; the `PermissionBrokerDecision` is consumed
  in-process and rendered only into existing stdout/JSON diagnostic
  output.
- **No stale decision reuse:** `test_ordinary_path_no_stale_decision_reuse`
  performs two logical push attempts (ALLOW, then forced DENY) and
  confirms the second attempt independently re-evaluates and blocks —
  no persisted or cached decision is reused.
- **Exactly-once evaluation and dispatch:** `test_ordinary_path_evaluates_broker_exactly_once`
  and `test_staged_file_aware_evaluates_broker_exactly_once` confirm
  `PermissionBroker.evaluate` `call_count == 1` per attempt;
  `test_ordinary_path_allow_dispatches_exactly_once` and
  `test_staged_file_aware_allow_dispatches_exactly_once` confirm exactly
  one real `git push` invocation per successful attempt.

---

## 19. Prompt Generation — Deferred Strategic Observation (unchanged)

Prompt Generation / Prompt Creation (Phase 45F) remains recorded as
`status = partially_ready`, **DEFERRED STRATEGIC OBSERVATION** for
post-Chapter-148 reassessment. Nothing in this phase's implementation
relates to Prompt Generation, Prompt Dispatch, or agent invocation. The
principle `generated ≠ approved ≠ dispatched ≠ executed` is preserved
unchanged.

---

## 20. Findings

**BLOCKING:** none.

**NON-BLOCKING:** none — see Observation below for a plan-coverage gap
that was fully resolved within this phase's own scope, not deferred.

**OBSERVATION:**

- **O-148E-1.** 148D's Section 34 test-change-surface inventory did not
  identify two pre-existing Phase 108D/109D-era invariant tests
  (`test_lifecycle_command_modules_never_import_broker_directly` in
  `tests/test_permission_broker_observation_verification.py`, and
  `test_broker_not_imported_by_lifecycle_command_modules` in
  `tests/test_permission_broker_verification_compatibility.py`) that
  asserted `push.py` never imports `permission_broker_foundation` at
  all — an invariant `PBPC-001` v1.2 explicitly supersedes for `push.py`
  specifically. Both were discovered by running the actual regression
  suite (not caught by static review of 148D's inventory) and were
  updated within this phase to narrow the invariant to `commit.py`/
  `task.py`/`phase.py` (which correctly remain unwired), with a new
  guard test (`test_broker_wiring_remains_scoped_to_push_only`) added to
  prevent the one authorized exception from silently expanding. This is
  an implementation-time discovery fully resolved before completion, not
  a residual gap for 148F.

**DEFERRED:** Prompt Generation (Phase 45F), unchanged (Section 19).

---

## 21. Security Invariants — Final Confirmation

All hold:

- No `git push` without `ALLOW`. ✅
- `DENY` never dispatches. ✅
- `HUMAN_REVIEW` never dispatches. ✅
- Broker failure never dispatches. ✅
- Both dispatch sites gated; 0 ungated sites. ✅
- No policy-selection input from caller. ✅
- `execution_class` fixed to `mutation`. ✅
- `approval_present` remains `False`. ✅
- `simulation_only` remains `True`. ✅
- `POL-004` unchanged (non-applicable to `mutation`, per `PBPA-001`). ✅
- `POL-005` unchanged (still denies `simulation_only=False`). ✅
- Mechanical checks preserved. ✅
- No stale `ALLOW` reuse. ✅
- No new runtime capability; runtime remains Observed / observe /
  unavailable. ✅

---

## 22. Governance Validation

```
pcae health                 -> healthy
pcae check                  -> passed
pcae status coherence       -> coherent
pcae doctor task-memory     -> clean
pcae push check             -> nothing_to_push
pcae runtime inspect        -> Observed / observe / unavailable
pcae notify status          -> Telegram configured, enabled, ready
```

---

## 23. No-Go Confirmations

`PBPC-001` v1.2 production consumption is implemented for both real
`pcae push` dispatch paths. `PBPA-001` v1.0 remains unchanged. `148C-B-1`
remains CLOSED. No real `git push` dispatch path remains ungated by the
Permission Broker. No new push policy was introduced. No approval was
fabricated. `approval_present` remains `False`. `execution_class` remains
`mutation`. `simulation_only` remains `True`. No `POL-001..012` meaning
was changed. `POL-004` retains its existing behavior. `POL-005` retains
its existing behavior. `DENY` cannot dispatch. `HUMAN_REVIEW` cannot
dispatch. Broker failure cannot dispatch. No caller-selectable policy set
was introduced. Mechanical/structural push checks remain enforced.
Interactive Workflow Confirmation remains independent. Authority
Evaluation / AESIC remains disclosure-only. No Runtime Enforcement
behavior was changed. No durable Permission Broker decision artifact was
added. Prompt Generation remains design-only / `partially_ready` and
DEFERRED for post-Chapter-148 reassessment. No Prompt Generation, Prompt
Dispatch, or agent invocation capability was implemented. Runtime remains
Observed, maximum capability remains observe, and execution availability
remains unavailable.

---

## 24. Recommended Next Phase

**148F — Permission Broker Production Consumption Independent
Implementation Verification**, per 148D Section 61. 148F must not trust
this phase's own tests or summary; it must independently re-derive: both
dispatch paths; the direct bypass search; canonical request truthfulness
(re-inspecting the constructed `PermissionBrokerRequest` directly);
`ALLOW`/`DENY`/`HUMAN_REVIEW`/broker-failure consumption; `POL-004`/
`POL-005` non-drift; mechanical-check preservation; no stale decision
reuse; exactly-once behavior; absence of caller policy injection;
contract/runtime-capability non-drift.

Chapter 148 should not be certified directly from 148E.
