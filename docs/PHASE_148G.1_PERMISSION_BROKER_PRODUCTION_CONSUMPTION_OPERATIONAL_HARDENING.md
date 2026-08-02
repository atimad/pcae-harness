# Phase 148G.1 — Permission Broker Production Consumption Operational Hardening

## 0. Phase Type and Scope

**Phase type:** bounded production operational hardening. Closes the two
findings 148G carried forward from 148F: F-148F-3 (`REPAIR_REQUIRED_
BEFORE_CLOSURE`) and F-148F-1 (`REPAIR_RECOMMENDED_POST_CLOSURE`, folded
into this phase since it touches the same integration boundary). Does
not amend `PBPC-001` or `PBPA-001`, does not modify `POL-001..012`, does
not touch Runtime Enforcement/IWC/AESIC, and does not implement Prompt
Generation.

**Baseline commit:** `835d6d9a` (HEAD at phase start, tip of `Phase
148G: close out task lifecycle, open idle placeholder`).

**Governing contracts (both read directly, both unamended by this
phase):**
- `PBPC-001` v1.2 — `docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`
- `PBPA-001` v1.0 — `docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`

**148C-B-1:** CLOSED (unchanged by this phase).

---

## 1. Initial Inspection

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
| `pcae phase-report show --latest` | 148G: completed, complete ✅, pushed, `origin/main..HEAD: 0` |
| `pcae phase-report reconcile --phase-id 148G` | reconciled (bookkeeping-only status), mutation: none (inspection only) |

Confirmed at phase start: repository clean; `origin/main..HEAD = 0`;
148G complete; `PBPC-001` v1.2 unamended; `PBPA-001` v1.0 unamended;
`148C-B-1` CLOSED; F-148F-3 open/repair-required; runtime Observed /
observe / unavailable.

---

## 2. PBPC-REQ-059/060/061 — Requirement Table

| Requirement | Required fact | Source | Comparison target | Failure behavior |
|---|---|---|---|---|
| PBPC-REQ-059 | Re-observe, immediately before each dispatch site: local HEAD revision, local branch, unpushed-commit count, active task ID | `git rev-parse HEAD`, `read_git_branch()`, `_count_unpushed_commits()`, `find_latest_active_task()` — all pre-existing observation primitives, PBPC-REQ-056's four locally-bindable fields | value bound into the evaluated request at broker-evaluation time | n/a (observation only) |
| PBPC-REQ-060 | Any mismatch between a re-observed field and its bound value is material | direct comparison, no tolerance/threshold | — | mismatch → PBPC-REQ-061 |
| PBPC-REQ-061 | On material mismatch: existing `ALLOW` invalid, zero dispatch, fresh evaluation cycle required before any further attempt (no silent update, no automatic re-evaluation in place) | — | — | abort this attempt; caller reruns `pcae push` |

Independently re-derived from Section 17 (`docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md:793-807`)
and cross-checked against PBPC-REQ-056 (Section 16), which fixes the
locally-bindable field set: HEAD, branch, unpushed-commit count, active
task ID (remote name and force/non-force are fixed constants today, not
observed state — excluded by PBPC-REQ-056 itself).

---

## 3. Decision-Bound Fact Inventory and Snapshot Design

`_PushDecisionSnapshot` (`src/pcae/commands/push.py`, new frozen
dataclass): `head`, `branch`, `unpushed`, `task_id`. Populated by
`_observe_push_decision_state(root, task_id)`, a new private helper
combining a fresh `git rev-parse HEAD` with the existing
`read_git_branch` / `_count_unpushed_commits` primitives.

The snapshot is captured inside `_evaluate_push_permission`, immediately
alongside `PermissionBrokerRequest` construction — the same instant the
decision becomes bound to an operation identity — and attached to
`PushPermissionResult.decision_snapshot`. It is in-process only: no new
file, no schema change, no durable artifact (PBPC-REQ-035 unaffected).

---

## 4. Final Re-Observation Implementation

New helper `_validate_push_permission_freshness(root, snapshot) ->
(bool, list[str])`: re-observes the same four facts via
`_observe_push_decision_state` (task ID independently re-derived via
`find_latest_active_task`, not reused from the caller, so a genuine task
change is actually detected) and compares each against the snapshot.
Returns `(True, [])` when all four match; otherwise `(False,
[mismatch descriptions])`. Performs no dispatch and contains no `POL-`
policy logic — it is decision freshness, not a new permission judgment
(no `POL-013+` added).

**Ordinary path** (`run_push`): called immediately before `subprocess.run(["git", "push"], ...)`
(`src/pcae/commands/push.py`), after the `EXECUTING REAL PUSH` banner.
On mismatch: prints a `Push blocked: decision-bound state changed before
dispatch (...)` diagnostic, returns exit code `1`, zero dispatch.

**Staged-file-aware path** (`_run_push_staged_file_aware`): the same
shared helper called immediately before `subprocess.run(["git", "push",
"origin", "main"], ...)`. On mismatch: `stale_decision` status appended
to the existing blocked-result shape, zero dispatch.

**Ordering** (verified both by source inspection and by
`test_final_validation_ordering_present_in_source`): broker evaluation <
final re-observation < `git push` dispatch, for both paths.

**Residual TOCTOU:** the window between final re-observation succeeding
and the `subprocess.run(["git", "push"], ...)` call is a single
statement transition with no intervening I/O, subprocess call, task
lookup, or mutable-state transformation on either path — matching
PBPC-REQ-057/058's explicit, documented limitation (remote-state races
remain outside what this contract closes; `git push`'s own
non-fast-forward rejection remains the safety net for that specific
race).

---

## 5. F-148F-1 Repair — Broker Construction Failure Handling

`_evaluate_push_permission`'s `try:` block now wraps both
`PermissionBroker()` construction and `.evaluate(request)`, following
the existing `command_path_observation.observe()` precedent
(`src/pcae/core/command_path_observation.py:70-84`, which already wraps
construction and evaluation together for its own broker touchpoint).
Construction failure now produces the same `broker_failure_reason`-
populated `PushPermissionResult` and the same `"Push blocked: Permission
Broker evaluation failed (...)"` diagnostic / exit code `1` that
evaluation failure already produced — no new failure category, no
traceback escapes through normal CLI usage. `evaluate()`-raises and
invalid/malformed-result handling are unchanged (still inside the same
`try`/`isinstance` check as before).

---

## 6. Test Changes

**New:** `tests/test_permission_broker_push_operational_hardening.py`
(9 tests) — validation ordering; no-drift control (both paths implied,
ordinary path asserted directly, staged path covered by the drift
tests' contrast); HEAD drift (ordinary + staged); branch drift; task-ID
drift; multiple simultaneous drift; genuine `ALLOW` + drift still fails
closed (the central F-148F-3 closure proof, using a real
`PermissionBrokerDecision(ALLOW)` instance, not a duck-typed fake); no
stale-`ALLOW`-reuse-but-fresh-rerun-succeeds (proves PBPC-REQ-061's
"fresh evaluation cycle required" — `evaluate()` is called again on the
second attempt, not skipped).

**Repaired (stale pre-148E invariant, item 38):**
`tests/test_phase_148c10_pbpc_v12_independent_verification.py::test_push_module_does_not_import_permission_broker`
renamed to `test_push_module_is_the_authorized_pbpc_production_consumer`
and rewritten: push.py now must reference `PermissionBroker`/
`permission_broker_foundation` (it is the intentional, 148E-established
production consumer); `pcae.commands.agent` and `pcae.commands.phase`
(148F/148G's independently inventoried unrelated dispatch sites) must
not — preserving the invariant's actual purpose (wiring-boundary
guarding) against the current, intentional architecture.

**Repaired (encoded the pre-repair F-148F-1 bug as expected behavior):**
`tests/test_phase_148f_permission_broker_production_consumption_independent_verification.py::test_ordinary_path_broker_construction_failure_does_not_dispatch`
and `::test_staged_file_aware_broker_construction_failure_does_not_dispatch`
— both previously asserted `pytest.raises(RuntimeError, ...)` around
`main([...])`, i.e. asserted the *bug*. Both docstrings explicitly
predicted this rewrite ("it will fail loudly ... once a bounded repair
phase closes this gap ... at which point it should be rewritten to
assert a clean exit code 1"). Rewritten to assert exit code `1` and the
graceful diagnostic instead.

---

## 7. Production Diff

**Production file changed (exactly one):** `src/pcae/commands/push.py`.
No other `src/pcae/**` file touched. `git diff --name-only
835d6d9a..HEAD -- src/pcae/` confirms this.

Every production hunk maps to F-148F-1 (widened `try:` boundary) or
F-148F-3 (`_PushDecisionSnapshot`, `_observe_push_decision_state`,
`_validate_push_permission_freshness`, and the two call sites
immediately before each dispatch).

**Contract boundary:** `git diff --name-only 835d6d9a..HEAD --
docs/contracts/` — empty. `PBPC-001` remains v1.2; `PBPA-001` remains
v1.0.

**Foundation boundary:** `git diff --name-only 835d6d9a..HEAD --
src/pcae/core/permission_broker_foundation.py
src/pcae/core/permission_broker.py` — empty. No policy semantics
changed. `HARD_BLOCK_REGISTRY` unchanged (12 entries).

**Canonical request fields unchanged:** `action_type=push`,
`execution_class=mutation`, `requested_component=COMP-001`,
`requested_capability=pcae_push`, `approval_present=False`,
`simulation_only=True` — verified unmodified in
`_evaluate_push_permission`.

---

## 8. Regression Results

- `tests/test_permission_broker_push_production_consumption.py` +
  `tests/test_phase_148f_permission_broker_production_consumption_independent_verification.py`:
  31/31 passed (2 rewritten as above).
- `tests/test_phase_148c10_pbpc_v12_independent_verification.py`: 20/20
  passed (1 rewritten as above).
- New `tests/test_permission_broker_push_operational_hardening.py`:
  9/9 passed.
- `tests/test_permission_broker.py`, `test_permission_broker_foundation.py`,
  `test_permission_broker_policy_applicability.py`,
  `test_phase_148c7_permission_broker_policy_applicability_independent_verification.py`,
  `test_phase_148c8_permission_broker_production_consumption_b1_reevaluation.py`:
  455/455 passed — no PBPA/Foundation drift.
- `tests/test_runtime_inspect_cli.py`, `test_runtime_snapshot.py`,
  `test_runtime_context.py`: 186/186 passed — runtime remains Observed /
  observe / unavailable, no coupling introduced.
- Push suites (`test_push.py`, `test_staged_file_aware_push.py`,
  `test_commit_push_gate.py`, `test_push_phase_report_identity_137f1.py`,
  `test_post_push_canonicalization.py`, `test_push_state_reconciliation.py`,
  `test_commit_push_preflight.py`, `test_commit_push_preflight_review.py`):
  see Section 9.
- Fast Green (`-m fast_green -n auto`): see Section 9.

---

## 9. Findings Classification

| Finding | Prior status | 148G.1 disposition |
|---|---|---|
| F-148F-3 | REPAIR_REQUIRED_BEFORE_CLOSURE | **CLOSED** — PBPC-REQ-059/060/061 implemented on both dispatch paths, fail-closed, no stale-`ALLOW` reuse, focused tests pass |
| F-148F-1 | REPAIR_RECOMMENDED_POST_CLOSURE | **CLOSED** — construction failure now fails closed with the same controlled diagnostic as evaluation failure |
| F-148F-2 | CLOSE (chapter debt) / TRACK_POST_CHAPTER (repository-wide mutation governance) | unchanged — untouched by this phase, `core/agent.py` and `commands/phase.py` remain outside scope |
| REPOSITORY_TEST_HYGIENE_DEBT (148C.10 item) | TRACK_POST_CHAPTER | this repository's 148C.10 sub-item repaired; broader item (`tasks/TODO.md` staleness, `-m "not slow"` pollution) remains untouched, out of scope |

**Security invariants reconfirmed:** no `git push` without `ALLOW`;
`DENY`/`HUMAN_REVIEW`/broker-construction-failure/broker-evaluation-
failure/malformed-result all still produce zero dispatch;
decision-bound state drift now also produces zero dispatch; no stale
`ALLOW` reuse; both `pcae push` paths broker-gated; `execution_class`
remains `mutation`; `approval_present` remains `False`;
`simulation_only` remains `True`; `POL-004`/`POL-005` unchanged.

**Runtime/governance invariants preserved:** IWC Confirmation ≠
approval; AESIC ≠ permission; Runtime Enforcement unchanged; Prompt
Generation (Phase 45F) remains deferred, untouched — no prompt
generation, dispatch, or agent-invocation capability added; no new
durable Permission Broker artifact; no runtime capability elevation;
runtime remains Observed / observe / unavailable.

---

## 10. Recommended Next Phase

**148G.2 — Permission Broker Production Consumption Operational
Hardening Independent Verification** — independently re-derive and
verify F-148F-1 and F-148F-3 closure without trusting this phase's own
tests, docstrings, or claims, before Chapter 148 certification proceeds.
Do not move directly to certification on self-tests alone.
