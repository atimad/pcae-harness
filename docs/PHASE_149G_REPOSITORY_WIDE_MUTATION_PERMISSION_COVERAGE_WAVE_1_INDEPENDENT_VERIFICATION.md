# Phase 149G — Repository-Wide Mutation Permission Coverage Wave 1 Independent Verification

- **Phase ID:** 149G
- **Type:** Independent implementation verification (no production repair, no contract amendment, no rollback implementation)
- **Verifies:** Phase 149F — Repository-Wide Mutation Permission Coverage Wave 1 Implementation (`c3e72b04`, `8bd39bcf`)
- **Governed by:** RWMPC-001 v1.0, PBPC-001 v1.2, PBPA-001 v1.0 (all frozen, unamended by this phase)

## 1. Methodology

This phase independently re-derives every load-bearing claim in 149F's own
summary rather than trusting it: the exact production diff, the shared
primitive's design, request-construction ownership, the six Wave-1 sites'
control flow, and the current mutation inventory. It then builds an
independently-authored adversarial test suite
(`tests/test_phase_149g_rwmpc_wave1_independent_verification.py`, 34 tests)
that does not import 149F's own test fixtures, using scratch git
repositories and local bare remotes to exercise real broker-construction
failure, evaluation failure, malformed results, DENY, HUMAN_REVIEW,
freshness drift (staged-tree, HEAD, task-id, unpushed-count), and
no-drift positive controls against the real production code paths
(`commit_file_changes`, `_dispatch_governed_push`,
`build_promotion_execution`'s permission/freshness ordering).

## 2. Initial Inspection

- Repository clean; `origin/main..HEAD` = 0 (confirmed both before and
  after this phase's own work, aside from this phase's own commits).
- `pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
  coherent. `pcae doctor task-memory`: clean. `pcae push check`: nothing
  to push. `pcae runtime inspect`: Runtime state Observed, execution
  capability unavailable, maximum plugin capability observe — unchanged
  before and after.
- 149F confirmed completed (report status `completed`, completeness
  `complete`).
- RWMPC-001 remains v1.0 (frozen at Phase 149C, commit `049a580b`);
  PBPC-001 remains v1.2 (frozen at Phase 148C.9, commit `617a59ee`);
  PBPA-001 remains v1.0 (frozen at Phase 148C.3, commit `234fce06`). No
  contract commits since. `git diff --name-only c3e72b04..HEAD --
  docs/contracts/` is empty at both the start and end of this phase's own
  work (excluding this phase's own report/PROJECT_STATUS additions,
  which do not touch `docs/contracts/`).
- `pcae phase-report reconcile --phase-id 149F` reports
  `delivery_recorded_bookkeeping_incomplete` / receipt absent — a
  pre-existing notification-bookkeeping gap unrelated to RWMPC Wave-1
  code correctness (OBSERVATION, not investigated further by this phase;
  out of 149G's scope).

## 3. Production Diff Reconstruction

Baseline: `5392a7cd` (149E's last commit, immediately pre-149F).
Final: `c3e72b04` (149F's implementation commit).

`git diff 5392a7cd..c3e72b04 -- src/pcae/` touches exactly three files:

| File | Classification |
|---|---|
| `src/pcae/core/mutation_permission.py` (new, 531 lines) | SHARED_PERMISSION_PRIMITIVE |
| `src/pcae/core/agent.py` (+192/-3) | AG1 (commit_file_changes wiring), AG2 (push_file_changes wiring + new `_dispatch_governed_push` shared dispatcher), AG4 (build_promotion_execution wiring) |
| `src/pcae/commands/phase.py` (+107/-2) | PH1 (commit adapter call), PH2_ROUTING, PH3_ROUTING (both routed to `_dispatch_governed_push`) |

No UNRELATED hunks found — every changed line in `src/pcae/` maps to one
of the six declared Wave-1 sites or the new shared module.

Claimed byte-unchanged files reconfirmed independently:
`git diff --stat 5392a7cd..HEAD -- <file>` is empty for
`permission_broker_foundation.py`, `permission_broker.py`, `push.py`,
`task.py`. `docs/contracts/` is likewise empty.

## 4. Shared Primitive Analysis (`mutation_permission.py`)

Read independently, not from 149F's prose. Exports one shared low-level
primitive (`evaluate_repository_mutation_permission`, mirroring
`push.py:_evaluate_push_permission`'s shape) and three thin per-class
adapters (commit, alternate-push, promotion) each with a paired freshness
validator. `action_type`, `execution_class`, `requested_component`,
`requested_capability`, `approval_present`, `simulation_only` are fixed
literals inside each adapter — never threaded from a caller argument
(confirmed by reading every adapter signature; none accepts these as
parameters). `PermissionBroker()` is constructed with no arguments,
consuming the unmodified default `PolicyRegistry()` — no reduced/custom
registry. Freshness validators (`validate_*_freshness`) never reference
`DECISION_ALLOW`/`DENY`/`HUMAN_REVIEW` and cannot themselves authorize —
confirmed by grep: the only place `DECISION_ALLOW` is compared is inside
`evaluate_repository_mutation_permission`'s own `authorized=` assignment.

**Sole-constructor claim:** `grep -rn "PermissionBrokerRequest(" src/pcae/`
finds exactly one direct construction site
(`permission_broker_foundation.py:179`, the Foundation's own factory).
`grep -rn "build_permission_broker_request(" src/pcae/` finds three
callers: `push.py` (Chapter 148), `mutation_permission.py` (Chapter 149),
and **`src/pcae/core/command_path_observation.py:71`** — a third caller
149F's docstring does not mention. See Finding F1.

## 5–6. Trusted Classification & Canonical Registry

No adapter accepts `action_type`/`execution_class`/`approval_present`/
`simulation_only` as caller-supplied parameters — confirmed by reading
every adapter's signature. `classify_promotion_action_type` maps
`approved_paths` to one of three known `ACTION_*` constants by path
prefix only; it cannot return an arbitrary caller-chosen value.
`PermissionBroker()` uses the real default registry (§4).

## 7–11. Broker Failure / Malformed Result / DENY / HUMAN_REVIEW

Independently forced (not via 149F's tests):
- Broker construction failure (patching `PermissionBroker` to raise) →
  `authorized=False`, `decision=None`, `BROKER_FAILURE`.
- Broker evaluation failure (injected `.evaluate()` raising) → same.
- Malformed results (`decision="ALLOW"` string-typed object, a bare
  string `"ALLOW"`, a plain `object()`, `None`) → all rejected,
  `BROKER_FAILURE` / `invalid_broker_result`, never treated as ALLOW.
- Real DENY: no active task → POL-001 fires for real (not simulated),
  `authorized=False`.
- Real HUMAN_REVIEW: rollback-class request (`EXECUTION_CLASS_ROLLBACK`,
  `approval_present=False`) → `DECISION_HUMAN_REVIEW` via POL-004, for
  real, against the live default registry.

All four (construction failure, evaluation failure, malformed result,
DENY) independently confirmed to produce zero mutation when driven
through `commit_file_changes` end-to-end in a scratch repo
(`test_ag1_commit_file_changes_zero_commit_on_deny`).

## 12–16. Real ALLOW / POL-001 / POL-004 / POL-005 / Approval Truthfulness

- Real Foundation ALLOW obtained for commit-class requests with a genuine
  task contract in a scratch repo (positive control, §18).
- POL-001: independently confirmed DENY with no active task, for real
  (not just read from source).
- POL-004: independently confirmed **not** applicable to
  `EXECUTION_CLASS_MUTATION` (reading `MissingHumanApprovalRule.
  applicable_execution_classes` directly — it lists SHELL/BACKEND/
  ADAPTER/ROLLBACK, explicitly excluding MUTATION and NONE) and **still**
  applicable to `EXECUTION_CLASS_ROLLBACK` (real HUMAN_REVIEW obtained,
  §11). No policy drift from PBPC-001 v1.2.
- POL-005: independently confirmed DENY for `simulation_only=False`.
  Every Wave-1 adapter hardcodes `simulation_only=True`.
- Approval truthfulness: every adapter hardcodes `approval_present=False`
  as a literal; no adapter reads a caller-supplied flag, so
  `--promotion-authorized`/`--reviewed-by`/`--approve-keep`/
  `--approved-by`/`--reason` (all pre-existing, command-owned mechanical
  checks) cannot reach or alter `approval_present`. Confirmed by
  signature inspection — none of the three adapters accept such a
  parameter.

## 17–22. AG1 / PH1 Trace and Freshness

Traced in `commit_file_changes`: artifact/approval/dirty-tree mechanical
checks (unchanged) → `git add` (staging) → `evaluate_commit_permission`
→ `validate_commit_permission_freshness` → `_run_git_commit`. Permission
evaluation happens **after** staging (so the staged-tree snapshot
reflects the exact content about to be committed) and strictly before
dispatch.

Independently attacked (own fixtures, real scratch repos):
- **Staged-tree drift**: stage an extra file after ALLOW, before
  dispatch → `validate_commit_permission_freshness` reports
  `fresh=False`, "staged content changed". Zero commit when driven
  through `commit_file_changes` (freshness enforced by the real
  production call chain).
- **HEAD drift**: an unrelated commit lands after ALLOW → `fresh=False`,
  "local HEAD changed".
- **Task-id drift**: active task swapped after ALLOW → `fresh=False`,
  "active task changed".
- **Observation failure**: `git write-tree` forced to fail at
  re-observation time → `fresh=False` with a genuine mismatch reason
  (not a silently-passing empty list) — fails closed, per RWMPC-001
  §17's "observation failure is a material mismatch" requirement.
- **No-drift positive control**: genuine ALLOW, no intervening state
  change → `fresh=True`, zero mismatches, and driving the real
  `commit_file_changes` end-to-end produces exactly one commit
  containing exactly the approved content.
- **Zero-commit-on-stale-decision**: freshness forced to report stale →
  `commit_file_changes` raises, zero commit, HEAD unchanged.

PH1 shares AG1's adapter (`evaluate_commit_permission`/
`validate_commit_permission_freshness`) by direct call in
`_build_backend_created_output_adoption_commit_execution`; the
independent test `test_77s_execute_creates_commit` fixture repair (a
`create_task_contract` addition, no assertion loosened) confirms PH1's
real dispatch now requires a genuine task for POL-001, consistent with
the claimed consolidation.

## 23–28. AG2 / PH2 / PH3 Trace and Freshness

Traced `push_file_changes` and `_dispatch_governed_push`: mechanical
gates (unchanged) → `evaluate_alternate_push_permission` →
`validate_alternate_push_permission_freshness` → `_run_git_push`.

Independently attacked with a real scratch repo + local bare remote (no
external network):
- **HEAD drift** after ALLOW → `fresh=False`, "local HEAD changed";
  confirmed zero push reaches the bare remote.
- **Task-id drift** after ALLOW → `fresh=False`, "active task changed".
- **No-drift positive control**: real `_dispatch_governed_push` call
  against a live bare remote → `dispatched=True`, `push_proc.returncode
  == 0`, and the bare remote's `refs/heads/main` matches local HEAD
  exactly.
- **Zero-dispatch-on-DENY**: no active task → `_dispatch_governed_push`
  returns `authorized=False, dispatched=False, push_proc=None`; remote
  ref unchanged.

**Finding F2 (non-blocking):** the "unpushed commit count" freshness
fact (`git rev-list --count <remote>/<branch>..HEAD`) is computed purely
from the local remote-tracking ref, without a `git fetch`. An external
push landing on the remote between decision and dispatch is **not**
detected — `validate_alternate_push_permission_freshness` reports
`fresh=True`. `_dispatch_governed_push` proceeds to a real `git push`,
which git's own transport layer then rejects (non-fast-forward,
`returncode != 0`); the remote ref is left exactly as the external
pusher left it. Verified empirically
(`test_ag2_external_remote_push_race_still_yields_zero_corrupt_mutation`):
zero corrupt/overwriting mutation reaches the remote either way, but the
actual safety net for this specific race is git's own protocol
guarantee, not Wave-1's freshness check. RWMPC-001's freshness binding
for this fact does not provide the detection it appears to promise for
concurrent-external-push scenarios; recommend RWMPC-001 either document
this as an accepted residual (git-protocol-backstopped) risk or add a
`git fetch`/remote-ref re-observation in a future hardening phase.

## 29–35. PH2/PH3 Routing Proof

Traced by control flow (not grep alone):
`_build_backend_created_output_adoption_push_execution` (PH2) and
`_build_final_verification_tooling_push_decision` (PH3) both call
`_dispatch_governed_push` and use `dispatch_result.push_proc` as their
sole push outcome; the pre-149F direct `_sp.run(["git","push",...])`
lines are gone entirely (confirmed via the full diff, §3). An
independent AST scan
(`test_phase_py_ph2_ph3_contain_no_direct_git_push_call`) parses both
function bodies and confirms no literal `["git","push",...]` list
argument to any call remains, and that both call
`_dispatch_governed_push` by name. A second AST scan
(`test_phase_py_no_try_canonical_except_direct_push_fallback`) confirms
no `try: <route> except: <direct git push>` fallback pattern exists in
either function.

Exactly-once evaluation: `_dispatch_governed_push` calls
`evaluate_alternate_push_permission` exactly once per invocation,
confirmed by instrumented call-counting against a real dispatch
(`test_dispatch_governed_push_evaluates_permission_exactly_once`) — PH2/
PH3 routing to the shared dispatcher does not double-gate on top of
AG2's own evaluation, since they share the same single call site inside
`_dispatch_governed_push` rather than each performing their own
evaluation before routing.

Semantics preserved: `_dispatch_governed_push(root, remote, branch,
task_id)` still dispatches `git push <remote> HEAD:<branch>` via
`_run_git_push`, identical target semantics to the pre-149F direct
`git push origin main` call sites.

## 36–43. AG4 (Promotion) Trace

Traced `build_promotion_execution`: divergence check + PER
`in_progress` persistence (unchanged) → `evaluate_promotion_permission`
→ `validate_promotion_permission_freshness` → apply loop's first
`write_bytes`/`write_text`/`unlink`. An independent source-order scan
(`test_build_promotion_execution_first_write_ordering_source_scan`)
confirms the permission-evaluation and freshness-validation call sites
both appear, textually, before the first write/unlink call in the
function body — permission and freshness are obtained strictly before
any root mutation.

Freshness independently attacked via `PromotionDecisionSnapshot` +
`validate_promotion_permission_freshness` directly:
- **approved_paths drift** (an extra path added after ALLOW) →
  `fresh=False`.
- **EPR/ECP id swap** (decision reused against a *different* promotion
  record) → `fresh=False` — confirms a stale decision cannot be
  redirected to mutate a different target.
- **Task-id drift** → `fresh=False`.
- **No-drift positive control** → `fresh=True`, zero mismatches.

`classify_promotion_action_type` independently confirmed to prioritize
`src/` over `tests/` over `docs/` when `approved_paths` spans multiple
categories, matching the documented precedence; this does not change the
broker's decision (POL-006 only checks action-type membership).

AG4 self-modification (`src/pcae/**` as a promotion target): no special
bypass found — the same permission boundary applies regardless of
target, consistent with RWMPC-REQ-019's stated non-goal of adding an
extra hard block. Not treated as a defect (contract does not require
one).

## 44–51. Rollback (AG3/AG5) and Task-Finish (TK1-3) Non-Interference

- `execute_rollback` (AG3, `agent.py`) and the promotion-failure restore
  path (AG5, `agent.py`, writing back `before_content`): both
  independently re-read from the current source; neither references
  `mutation_permission` or `permission_broker_foundation`. Confirmed by
  grep scoped to each function body.
- Real HUMAN_REVIEW independently re-obtained for a truthful rollback
  request (`EXECUTION_CLASS_ROLLBACK`, `approval_present=False`,
  `simulation_only=True`) via POL-004 — rollback remains blocked exactly
  as before Wave 1; Wave 1 did not accidentally resolve it.
- TK1 (`task.py:308`), TK2 (`task.py:316`), TK3 (`task.py:1100`): `task.py`
  is confirmed byte-unchanged since pre-149F (`git diff --stat` empty);
  `grep -n "mutation_permission" src/pcae/commands/task.py` returns
  nothing. TK1-3 remain direct, ungoverned `git commit --no-verify`
  dispatches, mechanically restricted to task-closure paths only, exactly
  as before. No new ability to route arbitrary commit content through
  TK1-3 was created; their conditional deferral (RWMPC-001's
  `LIFECYCLE_INTERNAL / DEFERRED_COVERAGE` classification) remains
  justified and unchanged.
- PU1 (`push.py:698`), PU2 (`push.py:898`): `push.py` confirmed
  byte-unchanged; both sites unaffected by Wave 1, still governed by
  PBPC-001 v1.2.

## 52–57. Mutation Inventory — Independent Reconstruction

Independent search (`grep -rn '"git", *"commit"\|"git", *"push"\|"git",
*"revert"\|"git", *"reset"' src/pcae/`, plus a targeted search for
root-level `write_text`/`write_bytes`/`unlink` calls in `agent.py`) finds
exactly the following dispatch sites, matching the 13-site matrix with
**no 14th site** discovered:

| Site | Location | Disposition | Direct dispatch? | Permission-gated? | Freshness-gated? |
|---|---|---|---|---|---|
| PU1 | `push.py:698` | certified governed (Ch. 148) | via `_evaluate_push_permission` | yes (PBPC-001) | yes |
| PU2 | `push.py:898` | certified governed (Ch. 148) | via `_evaluate_push_permission` | yes (PBPC-001) | yes |
| AG1 | `agent.py` `commit_file_changes` | governed | no (via broker) | yes | yes |
| AG2 | `agent.py` `push_file_changes`/`_dispatch_governed_push` | governed | no (via broker) | yes | yes |
| AG4 | `agent.py` `build_promotion_execution` | governed | no (via broker) | yes | yes |
| PH1 | `phase.py` adoption-commit | governed (shares AG1 adapter) | no (via broker) | yes | yes |
| PH2 | `phase.py` adoption-push | routed (shares AG2 dispatcher) | no (routed) | yes | yes |
| PH3 | `phase.py` final-verification push | routed (shares AG2 dispatcher) | no (routed) | yes | yes |
| AG3 | `agent.py` `execute_rollback` | rollback blocked/unimplemented | yes (`git revert`) | no (Wave-1 excluded) | n/a |
| AG5 | `agent.py` promotion-failure restore | rollback blocked/unimplemented | yes (write/unlink) | no (Wave-1 excluded) | n/a |
| TK1 | `task.py:308` | deferred | yes (`git commit --no-verify`) | no | n/a |
| TK2 | `task.py:316` | deferred | yes (`git commit --no-verify`) | no | n/a |
| TK3 | `task.py:1100` | deferred | yes (`git commit --no-verify`) | no | n/a |

`tests/test_repository_wide_mutation_inventory_guard.py`'s own guard was
independently re-run (5/5 passed) and independently read: it is
genuinely AST-semantic (parses call arguments via the `ast` module,
matches `["git", <mutation-subcommand>, ...]` literal lists and
`.write_text`/`.write_bytes`/`.unlink` attribute calls, and includes an
explicit `test_no_fourteenth_site_elsewhere_in_src` scan of the rest of
`src/`), not a fragile regex/string match. A genuinely new direct
dispatch elsewhere in `src/` would surface as an unclassified match in
that scan, not silently inherit a nearby classification.

## 58–59. Historical Test Repairs Reviewed

- `test_permission_broker_consumer_scope_inventory` (148F's independent
  verification suite): repair reviewed line-by-line (§4 of this
  document). It **narrows** the invariant (adds `mutation_permission.py`
  as a second authorized production consumer, explicitly re-asserts
  `commands/phase.py` and `core/agent.py` must never import
  `permission_broker_foundation` directly) rather than loosening it —
  confirms the sole-constructor architecture at the module-reference
  level, and already lists `command_path_observation.py` as pre-existing
  observational (see Finding F1).
- `test_77s_execute_creates_commit` (`test_phase.py`): repair is a single
  additive `create_task_contract(...)` fixture line; no assertion was
  removed or weakened.

## 60–63. Architectural Boundary Confirmations

- Shared primitive does not become a second permission authority: the
  only comparison against `DECISION_ALLOW` anywhere in
  `mutation_permission.py` is inside
  `evaluate_repository_mutation_permission`'s own result construction
  (grep-confirmed, one match).
- No policy reimplementation: no `if action == ...: allow`-shaped logic
  found in `mutation_permission.py`; `classify_promotion_action_type` is
  a truthful diagnostic classification only (§36-43), not a policy
  decision.
- Freshness vs. permission separation preserved: freshness validators
  never return or reference a `DECISION_*` value.
- Mechanical vs. permission separation preserved: each call site's own
  pre-existing mechanical gates (audit-warning, real-execution-disabled,
  runner-execution-refusal, idempotency, dirty-tree scope checks, etc.)
  remain textually unchanged above the new permission block in every
  reviewed diff hunk (§3).

## 64–67. Chapter-148 / HARD_BLOCK_REGISTRY Non-Regression

`push.py` confirmed byte-unchanged (§3). `HARD_BLOCK_REGISTRY`
(`permission_broker.py`) independently counted: **12** entries,
unchanged. See §10 (Regression Results) for the Chapter-148 suite run.

## 68–70. Runtime / Prompt Boundary

No Runtime Enforcement import found in any of the three changed files
(grep-confirmed). `pcae runtime inspect` before and after this phase's
own work: Runtime state Observed, execution capability unavailable,
maximum plugin capability observe — unchanged. No Prompt
Generation/Dispatch/agent-invocation code found in the 149F diff (the
diff is limited to the three files in §3, none of which touch prompt or
dispatch machinery).

## 71–74. Real Scratch Tests

All performed against real, disposable git repositories under `tmp_path`
(pytest's isolated temp-dir fixture) — no production-repository mutation
at any point:
- Real commit: `test_ag1_commit_file_changes_real_allow_commits_exactly_once`.
- Real push (local bare remote): `test_ag2_real_scratch_push_no_drift_positive_control`.
- Real deny-path zero-mutation: `test_ag1_commit_file_changes_zero_commit_on_deny`,
  `test_ag2_dispatch_governed_push_zero_dispatch_on_deny`.
- AG4 real end-to-end apply was not additionally exercised beyond the
  static first-write-ordering proof (§36-43) and the direct freshness
  unit tests — full ECP/EPR/PER fixture construction was judged
  disproportionate given AG1/AG2's real end-to-end coverage already
  independently confirms the shared primitive's real-broker behavior,
  and AG4 reuses that identical primitive. Recorded as a scope note, not
  a finding.

## 75. Independent Test Suite

`tests/test_phase_149g_rwmpc_wave1_independent_verification.py` — 34
independently-authored tests, all passing against the real 149F code.
Deliberately does not import 149F's own test fixtures/helpers. Covers
every item in the governing instruction's high-value list (§75):
mutation inventory reconstruction, AG1 staged-tree/HEAD/task-id drift,
AG1 observation failure, AG2 real local push, AG2 freshness drift
(including the F2 finding), PH2/PH3 exactly-once evaluation and
no-fallback proofs, AG4 first-write ordering and candidate/EPR/ECP
drift, broker-constructor/evaluation failure, malformed-ALLOW rejection,
rollback-still-HUMAN_REVIEW, TK non-interference.

Building this suite surfaced two real construction bugs in the suite's
own first draft (using the task *title* instead of the generated
`task_id`, and not accounting for `.pcae/remote/` being gitignored in
the real repo) — both were fixture bugs, not production defects; both
were found and fixed before relying on the suite's results, and are
documented here for verification-methodology transparency rather than
omitted.

## 76–83. Regression Results

| Suite | 149F baseline | 149G result |
|---|---|---|
| `test_agent.py` | 4236 passed | **4236 passed** (544s) |
| Lifecycle/phase group (6 files) | 954 passed | **954 passed** (335s) |
| 28 historical Permission-Broker-referencing files (149F counted 30; this repo now has 28 matching `grep -rl "PermissionBroker\b"`, plus 149G's own new file) | 2236 passed | 1041 passed, 1 pre-existing failure (`test_phase_149d_...test_src_pcae_untouched_by_phase_149d`, F3) |
| Chapter-148 (5 files) | all green | 79 passed |
| CLTR scoped suite (4 files) | 389 passed | 384 passed, 5 failed (pre-existing, environment: `python -m build` unavailable in this sandbox — unrelated to RWMPC code, confirmed present identically via a manual `python -m build` invocation) |
| Runtime (4 files) | 236 passed | 236 passed |
| PBPA (2 files) | n/a (148F/148C7 already counted above) | 140 passed |
| Fast Green (`python -m pytest -m fast_green -n auto -q`) | 4391 passed | **4391 passed** (105s) — identical to the 149F baseline |
| 149G independent suite (new, not part of any baseline) | n/a | **34 passed** |

**Pre-existing, non-149F/149G failure identified:**
`tests/test_phase_149d_rwmpc_contract_independent_verification.py::TestNoProductionModification::test_src_pcae_untouched_by_phase_149d`
asserts `git diff --name-only 93a70b14..HEAD -- src/pcae/` is empty
against a 149D-era baseline commit (`93a70b14`, 149C's close-out). This
assertion was true when 149D wrote it (149D was contract-only) but was
always going to be violated once the planned Wave-1 *implementation*
(149F) landed and genuinely touched `src/pcae/` — confirmed
independently by reproducing the identical failure on the pre-149G
commit (`e6320d07`, before this phase's own work began), i.e. it has
been failing since 149F merged, not introduced by 149G.
**OBSERVATION, not Blocking**: this is a stale self-referential
assertion in a phase-freeze verification test that should be time-boxed
to its own phase's baseline rather than compared against `HEAD`
indefinitely; recommend a narrow follow-up to retire or rebase this
specific assertion in a future bounded phase (not 149G, which does not
repair production or test code).

## 84–85. Production/Contract Boundary (149G itself)

`git diff --name-only <pre-149G>..HEAD -- src/pcae/` — empty (149G added
only a test file, this document, and governance bookkeeping).
`git diff --name-only <pre-149G>..HEAD -- docs/contracts/` — empty.

## 86. Findings

| ID | Severity | Summary |
|---|---|---|
| F1 | OBSERVATION | `mutation_permission.py`'s docstring claims to be "the *only* place... permitted to construct a `PermissionBrokerRequest` for a non-`pcae push` mutation site," but a third caller of `build_permission_broker_request` exists: `command_path_observation.py:71` (`observe()`, Phase 109B/109C). This path is provably inert for mutation purposes — `action_type="read"`/`"none"`-shaped calls only, no dispatch, no I/O, fails closed to `None` on any exception, and its four call sites (`pcae health`/`check`/`doctor task-memory`/`push check`) all discard the result for control flow. It is already correctly listed as `pre_existing_observational` in 149F's own `test_permission_broker_consumer_scope_inventory`. The docstring's absolute "sole constructor" phrasing is imprecise, not a functional gap. |
| F2 | NON-BLOCKING | AG2/PH2/PH3's alternate-push freshness check does not detect a concurrent external push to the remote (no `git fetch` before re-observing "unpushed count"). The false-negative freshness result does not cause corruption: git's own non-fast-forward rejection at the transport layer is the actual backstop, and the dispatch fails cleanly with the remote left untouched. See §29-35 for full detail and reproduction. |
| F3 | OBSERVATION | `test_phase_149d_rwmpc_contract_independent_verification.py`'s `test_src_pcae_untouched_by_phase_149d` has been failing since 149F merged (pre-existing, not a 149G-introduced regression) — a stale phase-freeze assertion comparing against a fixed historical baseline that Wave-1 implementation was always going to violate. See §76-83. |
| — | OBSERVATION | `pcae phase-report reconcile --phase-id 149F` reports `delivery_recorded_bookkeeping_incomplete` / receipt absent. Unrelated to RWMPC code correctness; out of 149G's scope. |

No Blocking findings. No Wave-1 mutation site was found capable of
mutating without a canonical, fresh ALLOW; no stale staged tree, HEAD, or
task binding was found to permit dispatch; PH2/PH3 have no reachable
direct-push fallback; AG4 performs no root mutation before permission and
freshness are both satisfied; no fake/malformed ALLOW was accepted; no
caller was found able to override classification, `approval_present`, or
`simulation_only`; rollback (AG3/AG5) and task-finish (TK1-3) behavior is
unchanged and independently reconfirmed; PU1/PU2 are unaffected.

## 87. Wave-1 Verification Verdict

**VERIFIED WITH NON-BLOCKING FINDINGS — RWMPC WAVE 1 IMPLEMENTATION CONFORMS**

## 88. Chapter 149 Partial Status

Chapter 149 is **not complete**. Outstanding:
- AG3/AG5 rollback approval architecture (rollback remains blocked at
  HUMAN_REVIEW via POL-004, unresolved by design).
- TK1/TK2/TK3 deferred coverage re-affirmation (confirmed unchanged and
  still justified this phase; formal re-affirmation as a first-class
  chapter deliverable remains open).

## 89. Rollback Next-Step Recommendation

Wave 1 verifies with zero Blocking findings. Recommend the next phase
resolve the trusted rollback approval evidence blocker:

**149H — Rollback Approval Evidence Architecture**

Scope: identify a genuine trusted approval source for AG3/AG5 (not a
self-declared CLI boolean) before any rollback-class wiring is
attempted. Do not implement rollback wiring itself in that phase without
a further, separate freeze/implementation split consistent with this
chapter's established pattern (architecture → contract freeze →
independent verification → implementation → independent verification).

## 90. Task-Finish Re-Affirmation Timing

Recommend TK1-3 re-affirmation occur **after** the rollback approval
evidence architecture (149H+), not before: TK1-3's deferral rationale
(mechanically restricted to task-closure paths, not an
autonomy-critical adoption pipeline) is independent of rollback and
remains valid; sequencing it after rollback avoids re-litigating the
same "trusted approval evidence" question twice for two different
`LIFECYCLE_INTERNAL`-classified site groups.

## 91. Sign-off

- RWMPC-001 v1.0: unchanged. PBPC-001 v1.2: unchanged. PBPA-001 v1.0:
  unchanged.
- Phase 149G modified no production source (`src/pcae/**` diff for this
  phase's own commits is empty).
- The six Wave-1 sites (AG1, AG2, AG4, PH1, PH2, PH3) are independently
  verified; two non-blocking findings (F1, F2) are explicitly recorded
  above, not silently accepted.
- PU1 and PU2 remain governed by certified Chapter-148 semantics
  (unchanged, re-confirmed).
- AG3 and AG5 remain unimplemented and blocked on trusted rollback
  approval evidence.
- TK1, TK2, and TK3 remain explicitly deferred, behaviorally unchanged.
- No approval was fabricated. No Interactive Workflow Confirmation
  artifact was treated as approval. No AESIC/Authority Evaluation result
  was treated as permission. No POL-001..012 meaning was changed. No
  POL-013+ was added. No Runtime Enforcement behavior was changed. No
  Prompt Generation, Prompt Dispatch, or agent-invocation capability was
  implemented. Runtime remains Observed, maximum capability remains
  observe, execution availability remains unavailable.
