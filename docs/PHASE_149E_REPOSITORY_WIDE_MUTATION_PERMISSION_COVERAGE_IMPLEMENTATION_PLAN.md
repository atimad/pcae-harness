# Phase 149E — Repository-Wide Mutation Permission Coverage Implementation Plan

**Phase ID:** 149E
**Type:** Implementation planning only (no `src/pcae/**` change, no
`docs/contracts/**` change, no runtime capability change)
**Predecessor:** 149D (Repository-Wide Mutation Permission Coverage
Contract Independent Verification — completed; verdict: VERIFIED WITH
NON-BLOCKING FINDINGS, RWMPC-001 v1.0 CONFORMS; implementation-planning
readiness: PARTIALLY READY)
**Governs implementation of:** RWMPC-001 v1.0
(`docs/contracts/REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md`),
unamended
**Depends on (unamended):** PBPC-001 v1.2, PBPA-001 v1.0, Permission Broker
Foundation (`src/pcae/core/permission_broker_foundation.py`)

Runtime posture, unaffected by this phase:

- State: **Observed**
- Maximum capability: **observe**
- Execution availability: **unavailable**

---

## 0. Method

This plan was produced by direct re-reading of RWMPC-001 v1.0 in full and
current primary source (`src/pcae/commands/push.py`,
`src/pcae/core/agent.py`, `src/pcae/commands/task.py`,
`src/pcae/commands/phase.py`,
`src/pcae/core/permission_broker_foundation.py`), not by trusting 149D's
summary prose. Every line reference below was independently re-grepped
against the current tree (commit `674df97a`, `origin/main..HEAD` = 0)
rather than copied from RWMPC-001's own table. All 13 sites' line numbers
match the contract's table exactly, confirming no source drift since
149C/149D.

The canonical, already-certified `pcae push` implementation
(`push.py:428-732`, PBPC-001 v1.2 / Chapter 148) is used throughout as the
reference precedent: `PushPermissionResult`, `_evaluate_push_permission`,
`_PushDecisionSnapshot`, `_validate_push_permission_freshness`,
`_permission_denial_details` / `_print_permission_denial`. Wave 1
generalizes this proven pattern rather than inventing a new one.

---

## 1. Initial Inspection (confirmed live)

```
git status --short                    -> clean
git status --branch --short           -> ## main...origin/main
git rev-list --count origin/main..HEAD -> 0
pcae health                           -> healthy, check passed
pcae check                            -> passed
pcae status coherence                 -> coherent
pcae doctor task-memory               -> clean
pcae push check                       -> nothing_to_push
pcae runtime inspect                  -> Observed / observe / unavailable
pcae notify status                    -> telegram configured/enabled
pcae phase-report show --latest       -> 149D, completed, complete, pushed
pcae phase-report reconcile --phase-id 149D
                                       -> delivery_recorded_bookkeeping_incomplete
                                          (informational; receipt absent,
                                          marker already_dispatched — no
                                          mutation, inspection only)
```

RWMPC-001 v1.0 verified frozen and unamended. PBPC-001 v1.2 and PBPA-001
v1.0 verified unamended. Rollback-class coverage confirmed blocked
(Section 12.1 of RWMPC-001). Task-finish (TK1-TK3) confirmed deferred.
Runtime confirmed unchanged.

---

## 2. Independent 13-Site Reconstruction (re-verified against current source)

| ID | File:line (confirmed live) | Function | Disposition |
|---|---|---|---|
| PU1 | `push.py:698` | `run_push()` | Already `BROKER_WIRE`, certified (PBPC-001 v1.2) |
| PU2 | `push.py:898` | `_run_push_staged_file_aware()` | Already `BROKER_WIRE`, certified |
| AG1 | `agent.py:4572` (`_run_git_commit`, called from `commit_file_changes`, def at `agent.py:4580`) | `commit_file_changes` | `BROKER_WIRE` — Wave 1 |
| AG2 | `agent.py:4732` (`_run_git_push`, called from `push_file_changes`, def at `agent.py:4755`) | `push_file_changes` | `BROKER_WIRE` — Wave 1 |
| AG3 | `agent.py:5099` (`_run_git_revert`, called from `execute_rollback`, def at `agent.py:5107`) | `execute_rollback` | `BROKER_WIRE` — **blocked** (rollback approval-evidence gap) |
| AG4 | `agent.py:93407-93416` (apply loop inside `build_promotion_execution`, def at `agent.py:93265`) | `build_promotion_execution` | `BROKER_WIRE`, highest priority — Wave 1 |
| AG5 | `agent.py:93832-93841` (restore loop inside `build_rollback_execution`, def at `agent.py:93705`) | `build_rollback_execution` | `BROKER_WIRE` — **blocked** (rollback approval-evidence gap) |
| TK1 | `task.py:308` | `run_task_finish` (staged-file-aware branch) | `LIFECYCLE_INTERNAL / DEFERRED_COVERAGE` |
| TK2 | `task.py:316` | `run_task_finish` (repo-wide branch) | `LIFECYCLE_INTERNAL / DEFERRED_COVERAGE` |
| TK3 | `task.py:1100` | task-finish recover path | `LIFECYCLE_INTERNAL / DEFERRED_COVERAGE` |
| PH1 | `phase.py:18457` | backend-created-output-adoption commit | `BROKER_WIRE`, consolidated with AG1 — Wave 1 |
| PH2 | `phase.py:19563` | backend-created-output-adoption push | `ROUTE_TO_CANONICAL_COMMAND` — Wave 1 |
| PH3 | `phase.py:20295` | final-verification-tooling push | `ROUTE_TO_CANONICAL_COMMAND` — Wave 1 |

**Confirmation:** independent re-grep of `"git"` subprocess dispatch across
all four files found exactly these 13 real mutation-dispatch call sites (plus,
for AG4/AG5, the direct `write_text`/`write_bytes`/`unlink` calls RWMPC-001
already scoped in). No 14th site found. Count matches RWMPC-001 and 149D
exactly — independently reproduced, not assumed.

AG5 clarification (149D, non-blocking, carried forward per instruction):
`build_rollback_execution` is a standalone, explicitly invoked command
(`pcae rollback --per-id`, gated on `PER.status in {"completed","partial"}`
and `rollback_payload_available=True` — **no `rollback_approval_state`
check exists in this function**, confirmed by direct reading,
`agent.py:93705-93739`), not an automatic promotion-failure restore. This
plan uses the corrected interpretation throughout and does not propagate
the stale wording.

### 2.1 The exact eight satisfiable `EXECUTION_CLASS_MUTATION` sites

Per RWMPC-001 §25's freeze verdict: PU1, PU2 (already implemented) + AG1,
AG2, AG4, PH1, PH2, PH3 (Wave 1 scope — **six sites**, all `MUTATION`
class). Table below captures every field Wave 1 must construct truthfully,
independently derived from current source (not category-level):

| Site | `action_type` | `execution_class` | `requested_component` | `requested_capability` | `task_id` source | `evidence_available` | `approval_present` | `simulation_only` | Existing mechanical gates (unchanged) | Dispatch expression |
|---|---|---|---|---|---|---|---|---|---|---|
| AG1 | `ACTION_COMMIT` | `EXECUTION_CLASS_MUTATION` | `COMP-001` | `pcae_remote_commit` | active task lookup (`find_latest_active_task`) | `True` (adapter invoked only after `scope_validation.valid` + `change_approval_state=="approved"` + working-tree match already passed) | `False` (POL-004 not applicable to MUTATION) | `True` | `scope_validation.valid`, `change_approval_state=="approved"`, working-tree/expected-files match (`agent.py:4595-4646`) | `_run_git_commit` (`agent.py:4567-4577`) |
| AG2 | `ACTION_PUSH` | `EXECUTION_CLASS_MUTATION` | `COMP-001` | `pcae_remote_push` | active task lookup | `True` (adapter invoked only after commit-SHA ancestry check already passed) | `False` | `True` | commit-SHA ancestry check (`_check_commit_is_ancestor`, `agent.py:4740-4752`) | `_run_git_push` (`agent.py:4727-4737`) |
| AG4 | `ACTION_SOURCE_MUTATION` / `ACTION_DOCS_MUTATION` / `ACTION_TEST_MUTATION` (selected per target path's category, never caller-selected) | `EXECUTION_CLASS_MUTATION` | `COMP-001` | `pcae_promotion_apply` | active task lookup, plus EPR/ECP task/prompt identity for cross-check | `True` (adapter invoked only after `review_state`, `promotion_authorized`, `capture_outcome`, divergence-check-non-blocking, and in-progress-duplicate guard already passed) | `False` | `True` | EPR `review_state`/`promotion_authorized`, ECP `capture_outcome`/`git_commit_detected`, divergence check, in-progress duplicate guard (`agent.py:93280-93336`) | per-file write/unlink loop (`agent.py:93393-93430`) |
| PH1 | `ACTION_COMMIT` (same adapter as AG1) | `EXECUTION_CLASS_MUTATION` | `COMP-001` | `pcae_remote_commit` (shared with AG1 — same capability, same adapter) | active task lookup | `True` (adapter invoked only after audit-warning/real-execution-disabled/runner-execution-refusal/idempotency gates already passed) | `False` | `True` | audit-warning gate, real-execution-disabled gate, runner-execution-refusal gate, already-committed idempotency guard (`phase.py` context around `18345-18471`) | `_sp.run(["git","commit",...])` (`phase.py:18457`) |
| PH2 | `ACTION_PUSH` (routed to AG2's adapter, not a second construction) | `EXECUTION_CLASS_MUTATION` | `COMP-001` | `pcae_remote_push` (shared with AG2) | active task lookup | `True` | `False` | `True` | audit-warning gate, real-execution-disabled gate, runner-execution-refusal gate, already-pushed idempotency guard (`phase.py` context around `19418-19488`) | routed — see §7 |
| PH3 | `ACTION_PUSH` (routed to AG2's adapter) | `EXECUTION_CLASS_MUTATION` | `COMP-001` | `pcae_remote_push` (shared with AG2) | active task lookup | `True` | `False` | `True` | `--approve-keep`/`--approved-by`/`--reason` presence check, working-tree/commit-freshness pre-checks (`phase.py` context around `19799-19867`) | routed — see §7 |

`requested_capability` strings are new literals, each distinct from
`pcae push`'s existing `"pcae_push"` and `"pcae_push_check"` — following
PBPC-REQ-046's own precedent of distinct capability strings per production
consumer, never reused across classes.

### 2.2 The two blocked rollback sites — explicit, individual

| Site | Function | Gate | `IMPLEMENTATION_STATUS` |
|---|---|---|---|
| AG3 | `execute_rollback` (`agent.py:5107`) | `rollback_approval_state=="approved"` (bare flag, not trusted evidence — RWMPC-REQ-024) | `BLOCKED — NO TRUSTED APPROVAL EVIDENCE` |
| AG5 | `build_rollback_execution` (`agent.py:93705`) | `PER.status in {"completed","partial"}` + `rollback_payload_available=True` (mechanical, not approval — and per the AG5 clarification above, no approval flag exists in this function at all today) | `BLOCKED — NO TRUSTED APPROVAL EVIDENCE` |

A truthful `EXECUTION_CLASS_ROLLBACK` request for either site carries
`approval_present=False`, which POL-004 correctly routes to
`HUMAN_REVIEW`. Wave 1 plans no seam that fabricates `approval_present`.
§13 below defines the future seam conceptually only — no provider is
designed or implemented here.

### 2.3 The three deferred task-finish sites — explicit, individual

| Site | Function | Exact commit pathspec | Why lifecycle-internal | Why currently deferred | Future re-affirmation criterion |
|---|---|---|---|---|---|
| TK1 | `run_task_finish`, staged-file-aware branch (`task.py:308`) | `["git","commit","--no-verify","-m",commit_message,"--"] + stageable_paths` where `stageable_paths` is mechanically derived from `active_task_path` + `result.updated_files` + `completed_task.destination_path` only (`task.py:254-278`) | Commit target set is computed by task-lifecycle closure logic, not caller-selectable | Not an autonomy-critical adoption pipeline; pathspec restriction is a real, re-verified mechanical bound (149D) | Re-affirm at implementation time: does a canonical commit-permission path exist that TK1 could route through as a bypass? If yes without becoming covered, it must enter coverage (RWMPC-REQ-054 item 1). |
| TK2 | `run_task_finish`, repo-wide branch (`task.py:316`) | `["git","commit","--no-verify","-m",commit_message]` (no `--`, but preceded by the same mechanically restricted `git add -- <stageable_paths>` at `task.py:296-303`, so the working tree at commit time contains only the staged closure files) | Same restriction, enforced via staging rather than pathspec | Same rationale | Same criterion |
| TK3 | task-finish recover path (`task.py:1093-1100`) | `["git","commit","--no-verify","-m",plan.commit_message or ""]`, preceded by `git add -- <stageable>` where `stageable` is derived from the recovery plan's own closure-file computation | Recovery-plan-derived closure files only | Same rationale — recovery is a repair of TK1/TK2's own interrupted closure, not a new capability | Same criterion |

**Wave 1 explicitly does not broker-wire these three sites.** §11 below
plans a regression test proving this.

---

## 3. Wave-1 Scope Freeze

```
WAVE 1 — SATISFIABLE MUTATION-CLASS COVERAGE
In scope:  AG1, AG2, AG4, PH1, PH2, PH3  (6 sites; PU1/PU2 already done)
Out of scope (explicit, not silent):
  - AG3, AG5           (rollback — approval-evidence gap, RWMPC-001 §12.1)
  - TK1, TK2, TK3       (task-finish — LIFECYCLE_INTERNAL/DEFERRED_COVERAGE)
  - Prompt Creation / Prompt Dispatch / agent invocation (separately gated,
    Phase 45F deferred)
  - Runtime Enforcement, runtime capability activation
  - Canonical artifact publication (Chapter 114/144-146 authority)
  - `.pcae/**` lifecycle-state writes (task-lifecycle/phase-reporting
    contracts, not RWMPC-001)
```

---

## 4. Shared Permission Integration Primitive — Architecture

**Rejected framing (per the phase's own critical boundary):** "add
`PermissionBroker.evaluate()` to six places" independently. This would
multiply integration patterns and directly recreate the "eight distinct
error-handling implementations" anti-pattern the phase prohibits.

**Adopted framing:**

```
shared canonical mutation-permission integration primitive
  (src/pcae/core/mutation_permission.py — new)
        |
thin per-class adapters (commit / alternate-push / source-mutation)
  (same new module — three small functions, not three modules)
        |
existing mechanical validation (unchanged, stays in agent.py/phase.py)
        |
operation-specific freshness snapshot (same new module, per-class dataclasses)
        |
existing dispatch (unchanged call sites in agent.py/phase.py)
```

One shared low-level function does request construction, broker
construction/evaluation, and ALLOW-only result consumption — mirroring
`push.py:_evaluate_push_permission`'s exact shape, but parameterized on
`action_type`/`execution_class`/`requested_capability`/`requested_resource`
instead of being push-specific:

```python
# src/pcae/core/mutation_permission.py  (conceptual signature only — not
# implemented by this phase)

@dataclass(frozen=True)
class MutationPermissionResult:
    authorized: bool
    request: "permission_broker_foundation.PermissionBrokerRequest"
    decision: "permission_broker_foundation.PermissionBrokerDecision | None"
    broker_failure_reason: str | None = None

def evaluate_repository_mutation_permission(
    *,
    root: HarnessPath,
    action_type: str,
    execution_class: str,
    requested_component: str,
    requested_capability: str,
    task_id: str | None,
    requested_resource: str | None,
    evidence_available: bool,
    approval_present: bool,
    simulation_only: bool,
    broker: "permission_broker_foundation.PermissionBroker | None" = None,
) -> MutationPermissionResult:
    ...
```

This is the **only** function in the codebase that constructs a
`PermissionBrokerRequest` for a non-`pcae push` mutation. Every Wave-1 call
site (commit adapter, alternate-push adapter, source-mutation adapter) goes
through it — no call site builds its own `PermissionBrokerRequest`.

### 4.1 Fields fixed by trusted adapter code (RWMPC-REQ-016)

`action_type`, `execution_class`, `requested_component`,
`requested_capability` are hardcoded literals inside each per-class
adapter function's body — never a parameter threaded from CLI args, env,
or config. No Wave-1 command gains a flag resembling `--execution-class`,
`--policy-profile`, `exclude_policies`, or `skip_policy` (§12 tests this
explicitly).

### 4.2 Result consumption — one rule, reused everywhere

```
ALLOW           -> operation may proceed to final freshness validation
DENY            -> abort, zero dispatch
HUMAN_REVIEW    -> abort, zero dispatch
broker exception -> abort, zero dispatch (authorized=False, broker_failure_reason set)
malformed result  -> abort, zero dispatch (authorized=False, broker_failure_reason="invalid_broker_result")
```

Implemented once, inside `evaluate_repository_mutation_permission`, exactly
as `push.py:496-522` already does it. No per-adapter reimplementation.

### 4.3 Diagnostics API

`MutationPermissionResult` returns the canonical `PermissionBrokerDecision`
object unmodified (mirroring `PushPermissionResult`) — commands read
`decision.decision_reason` / `decision.causing_policy_ids` directly for
user-facing diagnostics, exactly as `push.py:_permission_denial_details`
does. No second decision vocabulary is created.

---

## 5. Helper Location Decision

**Chosen:** new module `src/pcae/core/mutation_permission.py`.

Evaluated alternatives:

- `permission_broker.py` — **rejected**: this is the legacy/prototype
  broker (`HARD_BLOCK_REGISTRY`), explicitly NOT to be modified or
  reinterpreted (PBPC-REQ-012); placing new logic there would conflate two
  vocabularies PBPC-001 §6 keeps deliberately separate.
- `permission_broker_foundation.py` — **rejected**: this is the frozen
  Foundation itself; RWMPC-001 depends on it unamended (§6). Adding
  consumer-side request-construction logic here would blur the
  Foundation/consumer boundary the contract's layering diagram (§19)
  keeps distinct.
- Command-local helper inside `agent.py` or `phase.py` — **rejected**: AG1
  and PH1 must share one commit adapter; AG2 and PH2/PH3 must share one
  push adapter. A command-local helper in either file would force the
  other file to import command internals, or would duplicate the adapter
  — exactly the "eight distinct integration patterns" anti-pattern this
  phase must avoid.
- `push.py` — **rejected explicitly** (per §31/§47 below): generic
  repository-wide mutation-permission logic does not belong in the
  single-purpose, already-certified `pcae push` command module.
- **New `src/pcae/core/mutation_permission.py`** — **chosen**: narrowest
  reusable architectural location; a `core/` module (like
  `permission_broker_foundation.py` itself) that both `core/agent.py` and
  `commands/phase.py` can import without either depending on the other,
  and that does not touch the Foundation or the legacy broker.

---

## 6. Foundation and Policy Boundaries

`permission_broker_foundation.py` — **MUST_NOT_CHANGE.** Wave 1 consumes
`PermissionBroker`, `build_permission_broker_request`,
`PermissionBrokerDecision`, `ACTION_COMMIT`, `ACTION_PUSH`,
`ACTION_SOURCE_MUTATION`/`ACTION_DOCS_MUTATION`/`ACTION_TEST_MUTATION`,
`EXECUTION_CLASS_MUTATION`, `DECISION_ALLOW` — all already exist as frozen
constants (confirmed live: `permission_broker_foundation.py:96-125`). No
new action type, execution class, or policy rule is required for any of
the six Wave-1 sites.

`POL-001..012` — **MUST_NOT_CHANGE.** No `POL-013` is added. Wave 1 needs
no new policy: every Wave-1 request resolves under the existing registry
exactly as RWMPC-001 §12's satisfiability matrix already demonstrates.

---

## 7. Alternate Push Routing (AG2, PH2, PH3)

RWMPC-REQ-035: PH2/PH3 "SHALL... invoke the same adapter `pcae push`/AG2
use." Independent reading of PH2 (`phase.py:19563`,
`push_command = ["git","push","origin","main"]`) and PH3
(`phase.py:20295`, `pr = _sp.run(["git","push","origin","main"],...)`)
confirms both are shaped identically to AG2's own dispatch
(`git push <remote> HEAD:<branch>` with `remote="origin"`,
target-branch `"main"`) — not to `pcae push`'s Path A/B (which push the
current branch to its own upstream, not unconditionally to `origin/main`).

**Decision:** PH2 and PH3 stop performing independent `git push` dispatch
and instead call `push_file_changes`-equivalent logic — specifically, a
new small internal function `_dispatch_governed_push(root, remote, branch,
task_id)` colocated with AG2 in `agent.py`, extracted from
`push_file_changes`'s existing body so AG2's own call site and PH2/PH3's
call sites share one dispatcher, itself calling
`evaluate_repository_mutation_permission` exactly once. This is
**routing to AG2's adapter**, per RWMPC-REQ-035's literal text — not
routing into `pcae push`'s own Chapter-148 machinery (which governs a
structurally different operation: pushing the active branch to its own
upstream, gated by `assess_push_readiness`, not "push HEAD to
`origin/main`" gated by commit-SHA ancestry).

**Chapter-148 push (`push.py`) is not touched and is not the routing
target.** `pcae push`'s own freshness/readiness machinery remains fully
separate; RWMPC-001 additive, not overlapping (§19). No refactor of
`push.py` is required for this routing decision (§13 below).

PH2/PH3 retain their own existing mechanical gates (audit-warning,
real-execution-disabled, runner-execution-refusal, idempotency,
`--approve-keep`/`--approved-by`/`--reason` presence) unchanged — only the
final `git push` dispatch line is replaced by a call into the shared
dispatcher. `--approve-keep`/`--approved-by`/`--reason` remain command-owned
mechanical presence checks; none is read by
`evaluate_repository_mutation_permission` or mapped to `approval_present`.

---

## 8. Commit-Class Design (AG1, PH1)

### 8.1 Shared adapter

One function, `evaluate_commit_permission(root, task_id) ->
(MutationPermissionResult, _CommitDecisionSnapshot)`, in
`mutation_permission.py`, called identically by `commit_file_changes`
(AG1) and PH1's adoption-commit path. Both already compute their own
target file set via mechanically restricted logic before reaching this
call (`changed_files`/`scope_validation` for AG1; adoption-specific
tracked-file detection for PH1) — the adapter does not need to know which
caller invoked it; it evaluates permission for "commit the currently
staged content," truthfully, once mechanical gates already passed.

### 8.2 Commit freshness / operation binding

Decision-bound facts (RWMPC-001 §17): `HEAD`, staged-content identity,
`task_id`.

**Staged-content identity:** `git write-tree` (existing git primitive,
zero new dependency) computed immediately at decision time and re-observed
immediately before dispatch. A tree SHA changing between decision and
dispatch means the index changed — the exact "stale permission" risk RWMPC
flags (§15 of the phase's own numbered spec). `git diff --cached`
digesting is rejected in favor of `write-tree` because `write-tree`
produces one canonical, git-native object identity for the exact staged
content rather than a derived hash this repo would need to define and
maintain itself.

**Commit message identity:** non-binding. Per RWMPC's own request-model
framing, permission governs "commit these staged files," not specific
commit-message prose; message drift alone (with identical staged tree)
is not treated as material.

```python
@dataclass(frozen=True)
class _CommitDecisionSnapshot:
    head: str
    staged_tree: str   # `git write-tree`
    task_id: str | None
```

### 8.3 Commit dispatch ordering

```
mechanical validation (unchanged, existing)
  -> evaluate_commit_permission()  [broker ALLOW required]
  -> final freshness re-observation (HEAD, staged_tree, task_id)
  -> git commit  (existing _run_git_commit / phase.py's existing commit call)
```

Immediately before the `git commit` call is the last statement executed
after final validation — matching `push.py:696-703`'s existing pattern of
zero intervening I/O between freshness re-check and dispatch.

---

## 9. Promotion-Apply Design (AG4)

### 9.1 Request construction

`action_type` selected per target path's existing category classification
(`ACTION_SOURCE_MUTATION` / `ACTION_DOCS_MUTATION` / `ACTION_TEST_MUTATION`
— all three already exist as Foundation constants, confirmed live). The
category classifier is not built by this phase; RWMPC-001 assumes it
exists as adapter logic to be written in the implementation phase, derived
from the same path-prefix logic PCAE already uses elsewhere for
docs/tests/src classification (to be located and reused at implementation
time — no new invented taxonomy).

`requested_resource`: the approved-paths set (or a stable joined
representation) for diagnostic purposes only — no `POL-` rule inspects it
(RWMPC-REQ-047 precedent).

### 9.2 Promotion freshness / operation binding

Reuses the **existing** ECP/EPR/PER integrity model — no new digest
invented (RWMPC-REQ-043's explicit instruction). Bound facts: EPR id, ECP
id, `approved_paths` set identity, and the divergence-check result
(`_pxr_check_divergence`, already computed at `agent.py:93342` before the
apply loop) at decision time, re-verified as still non-blocking immediately
before the first file write.

### 9.3 First-mutation boundary and operation identity

`build_promotion_execution`'s existing control flow already computes
`divergence` and persists the PER as `in_progress` (`agent.py:93336-93362`,
confirmed live) strictly before the apply loop's first `write_text`/
`write_bytes`/`unlink` at `agent.py:93393+`. The Permission Broker
`ALLOW` decision SHALL be obtained in that same window: after divergence
check, after PER `in_progress` persistence, and before the loop's first
`full_path.unlink()`/`full_path.write_bytes()`/`full_path.write_text()`
call. One broker decision covers the entire bounded apply operation (all
files in `approved_paths`) — RWMPC-001 does not require per-file
re-evaluation, and the existing partial-outcome semantics
(`status: partial/failed/completed/aborted_divergence`) already handle
mid-loop failure without inventing new transaction semantics
(RWMPC-REQ-041).

### 9.4 Self-modification (AG4 targeting `src/pcae/**`)

**Decision: Wave 1 does not add a new mechanical protected-path hard
block.** RWMPC-REQ-019 explicitly forbids gating AG4 more strictly via
misclassification, and RWMPC-001 §16 states AG4's `BROKER_WIRE` coverage
*is* the required mitigation for this threat, deferring any further
mechanical hard block to a future phase "if evidence supports it." No
evidence gathered in 149D or this phase shows AG4 is unsafe once truthful
`BROKER_WIRE` coverage exists — the permission decision, freshness
binding, and existing EPR authorization gate (`promotion_authorized`)
together are the frozen contract's complete Wave-1 answer. This is a
tracked, not silently dropped, boundary (§16 below records it as an
Observation finding, not a Blocking one).

---

## 10. Production Change Matrix

| File | Function(s) touched | Planned change | Contract requirement | Risk |
|---|---|---|---|---|
| `src/pcae/core/mutation_permission.py` (**new**) | n/a | Shared primitive + three per-class adapters + three snapshot types | RWMPC-REQ-013/016/029/030 | Low — new, additive, no existing behavior touched |
| `src/pcae/core/agent.py` | `commit_file_changes` (AG1) | Insert permission check + freshness before `_run_git_commit` call | RWMPC-REQ-020/033/037/040 | Medium — touches a production dispatch path |
| `src/pcae/core/agent.py` | `push_file_changes` (AG2); new `_dispatch_governed_push` extraction | Insert permission check + freshness before `_run_git_push`; extract dispatcher for PH2/PH3 reuse | Same + RWMPC-REQ-035 | Medium |
| `src/pcae/core/agent.py` | `build_promotion_execution` (AG4) | Insert permission check + freshness before apply loop's first write | RWMPC-REQ-033/037/040, highest priority | High — highest-risk site; most scrutiny required at implementation time |
| `src/pcae/commands/phase.py` | adoption-commit path (PH1) | Call shared commit adapter (§8) before existing commit dispatch | RWMPC-REQ-033 (consolidated with AG1) | Medium |
| `src/pcae/commands/phase.py` | adoption-output push (PH2), final-verification push (PH3) | Replace direct `git push origin main` with call into `agent.py`'s `_dispatch_governed_push` | RWMPC-REQ-035 (routing) | Medium — must prove no direct-dispatch fallback remains |

`src/pcae/commands/push.py` — **MUST_NOT_CHANGE** unless a routing
decision genuinely requires it (§13 finds it does not — PH2/PH3 route to
AG2, not to `pcae push`).
`src/pcae/commands/task.py` — **MUST_NOT_CHANGE** (TK1-3 deferred).
`src/pcae/core/permission_broker_foundation.py`,
`src/pcae/core/permission_broker.py` — **MUST_NOT_CHANGE**.
`docs/contracts/**` — **MUST_NOT_CHANGE**.

---

## 11. Test Change Matrix

| Test file | New/updated | Purpose |
|---|---|---|
| `tests/test_mutation_permission_core.py` (new) | new | Shared primitive: ALLOW-only consumption; DENY/HUMAN_REVIEW/exception/malformed-result all fail closed; POL-001 (missing `task_id`) DENY; POL-005 direct-Foundation control case (`simulation_only=False` -> DENY, Foundation-level only, never reachable via any adapter); no caller-selectable `action_type`/`execution_class`/policy set. |
| `tests/test_mutation_permission_commit_integration.py` (new) | new | AG1/PH1: ALLOW dispatches commit; DENY/HUMAN_REVIEW/broker-failure block with zero commit; stale decision (staged tree changes after ALLOW, before dispatch) blocks; commit-message-only drift does not block. |
| `tests/test_mutation_permission_promotion_integration.py` (new) | new | AG4: ALLOW required before first file write; stale decision (candidate digest/target/approved_paths changes after ALLOW) blocks with zero mutation; divergence-conflict path unaffected; self-modification target (`src/pcae/**`) still requires ALLOW but is not specially blocked (per §9.4). |
| `tests/test_mutation_permission_push_routing_integration.py` (new) | new | AG2 broker-wired directly; PH2/PH3 no longer construct their own `PermissionBrokerRequest` and no longer dispatch `git push` directly — both reach `_dispatch_governed_push`; Chapter-148 freshness pattern reproduced for the new snapshot type; no fallback to legacy direct dispatch on routing failure. |
| `tests/test_repository_wide_mutation_inventory_guard.py` (new) | new | AST-based (not substring) enumeration of every `subprocess.run(["git", ...])` and direct `write_text`/`write_bytes`/`unlink` call in the four in-scope files; classifies each as `BROKER_GATED` / `CANONICALLY_ROUTED` / `ROLLBACK_BLOCKED` / `TASK_FINISH_DEFERRED`; fails on any `UNKNOWN` or newly appeared, unclassified site. |
| `tests/test_task_finish_permission_non_interference.py` (new, small, focused — not folded into `test_agent.py`) | new | TK1/TK2/TK3 regression: behavior byte-identical pre/post Wave 1; no broker consumption on these paths. |
| `tests/test_agent.py` (existing, 65k lines) | updated (narrow) | Existing `commit_file_changes`/`push_file_changes`/`execute_rollback`/`build_promotion_execution`/`build_rollback_execution` tests must continue passing unmodified in behavior; any test asserting the *old* no-broker-consultation shape for AG1/AG2/AG4 needs principled narrowing (§14.1) — not deletion. |
| `tests/test_cltr_authority_136at_quarantine_record.py`, `tests/test_cltr_authority_136au_quarantine_record_independent.py`, `tests/test_cltr_rehearsal_rollback.py`, `tests/test_cltr_rehearsal_135u_independent_verification.py` | regression (unchanged expected) | These cover `commit_file_changes`/`execute_rollback`/promotion paths; must remain green — rollback paths untouched, commit paths behaviorally equivalent under ALLOW. |
| `tests/test_permission_broker_push_production_consumption.py`, `tests/test_permission_broker_push_operational_hardening.py`, `tests/test_phase_148f_permission_broker_production_consumption_independent_verification.py`, `tests/test_phase_148g2_permission_broker_operational_hardening_independent_verification.py`, `tests/test_phase_148c10_pbpc_v12_independent_verification.py` | regression (unchanged expected) | Chapter-148 push semantics must remain fully intact — PH2/PH3 route to AG2, never to `push.py`, so these should be unaffected; run as a direct check of that claim. |
| Fast Green (`python -m pytest -m fast_green -n auto -q`) | regression | Current confirmed baseline: **4391 passed** (re-verified live, this phase, via `--co` collection count — matches the spec's cited figure exactly). Future implementation phase reports the actual post-change count. |

Deliberately **not** one 1000-line monolithic new test file (§78 of the
governing instruction) — four focused new files by concern
(core/commit/promotion/push-routing) plus one inventory-guard file plus one
narrow task-finish non-interference file.

---

## 12. No-Caller-Policy-Selection Tests (planned, RWMPC-REQ-016/022)

Explicit test assertions planned for implementation:

- No Wave-1 CLI command (`pcae remote changes commit/push`, `pcae
  promote`) gains a flag or env var that reaches `action_type`,
  `execution_class`, `approval_present`, `simulation_only`, or a
  policy-id list.
- Argument-parser inspection (mirroring RWMPC-REQ-016's own methodology)
  for all six Wave-1 CLI entry points, confirming no such flag exists
  before and after implementation.
- Agent-authored/backend-authored job-artifact fields (e.g. an AI-written
  `"approved": true` inside a job JSON) are never read by
  `evaluate_repository_mutation_permission` — only trusted, PCAE-owned
  code paths populate its parameters.

---

## 13. Canonical Push Reuse — Decision

`_dispatch_governed_push` (new, `agent.py`, extracted from
`push_file_changes`'s existing dispatch tail) is the single reusable
lower-level push service AG2/PH2/PH3 share. **This is not a refactor of
`push.py`.** `push.py`'s own `run_push()`/`_run_push_staged_file_aware()`
are structurally different operations (current-branch-to-its-own-upstream,
governed by `assess_push_readiness`) from `git push origin main`
(AG2/PH2/PH3's shape) — routing PH2/PH3 into `push.py` would require
either faking readiness state or bypassing `assess_push_readiness`
entirely, which is a larger and riskier change than extracting AG2's own
already-correct dispatcher. Per §47's stated preference, `push.py` is
**not** refactored; its Chapter-148-certified behavior is preserved
byte-for-byte, and no Chapter-148 regression test is expected to change.

---

## 14. Historical Guard Search (planning-level; verified live)

`grep -rl "PermissionBroker\|permission_broker_foundation" tests/` (run
live, this phase) found 30 test files. None of them contains a string
pattern resembling "only push.py imports PermissionBroker" or "agent.py
must never consume broker" (checked directly against the two push-specific
suites most likely to carry such an assumption:
`test_permission_broker_push_production_consumption.py`,
`test_permission_broker_push_operational_hardening.py` — no match). This
is an **Observation, not a completed guarantee**: the implementation
phase must still run the full search (item 100 of the governing
instruction) against the entire test suite, not just these two files,
before wiring AG1/AG2/AG4, since a broader assumption could exist
elsewhere (e.g. in `test_agent.py`'s 65k lines, not exhaustively
searchable within this planning phase's read budget).

### 14.1 `test_agent.py` narrowing risk

`test_agent.py` (65,734 lines) is the primary existing regression surface
for `commit_file_changes`/`push_file_changes`/`build_promotion_execution`/
`build_rollback_execution`. Its sheer size means a full manual review of
every assertion is not feasible within this planning phase; the
implementation phase must run it under Wave-1 changes and triage any new
failure individually rather than assume none exist. This plan does not
claim `test_agent.py` requires zero changes — only that no changes to it
are made *by this planning phase* (which makes no `src/pcae/**` or
`tests/**` change at all).

---

## 15. Migration Sequencing

Dependency-ordered:

```
1. Shared primitive + snapshot types (mutation_permission.py) + its own
   unit tests (test_mutation_permission_core.py) — no other file depends
   on anything but this existing first.
2. Commit-class integration (AG1 + PH1, shared adapter) — lowest-risk
   Wave-1 site (existing mechanical gates already fully restrict the
   commit target; PBPC-001's push precedent is directly analogous).
3. Alternate-push routing (AG2 direct wire, then PH2/PH3 routing) —
   depends on step 1 only; independent of step 2.
4. Promotion-apply (AG4) — highest risk, done last, after the pattern is
   proven twice (commit, push) on lower-risk sites.
5. Repository-wide inventory guard + full regression sweep.
```

This is chosen (not the phase-numbering-implied alternative of "commit,
promotion, push, verification") because AG4 is explicitly the
highest-risk site (can target `src/pcae/**`) and should be implemented
with the most accumulated confidence in the shared primitive's behavior,
not the least.

---

## 16. Atomic Commit Strategy

```
commit 1: shared permission primitives + unit tests (mutation_permission.py,
          test_mutation_permission_core.py) — zero behavior change to any
          existing command; safe to land alone.
commit 2: commit-path integration (AG1 + PH1) + integration tests +
          task-finish non-interference regression test.
commit 3: alternate-push routing (AG2 + PH2 + PH3) + integration tests +
          Chapter-148 unaffected-regression evidence.
commit 4: promotion-apply integration (AG4) + integration tests +
          rollback-non-interference regression test.
commit 5: repository-wide mutation inventory guard + full fast_green run
          + historical-guard-search results.
```

Each commit leaves the repository in a state where no ready site is
"helper exists but direct bypass still reachable" — commits 2-4 each
complete one site-family's dispatch-call-site edit in the same commit as
the shared-adapter wiring for that family, never split across a commit
boundary where a push/finalize could land between "helper added" and
"direct dispatch removed."

---

## 17. Implementation Stop Conditions (unchanged from governing instruction, restated for traceability)

The future implementation phase (149F) SHALL stop and escalate, not
improvise, if any of:

1. Production request semantics differ from RWMPC-001 once real code is
   written (e.g. a Wave-1 site turns out not to be truly restricted to
   `MUTATION`-class semantics on closer inspection).
2. A ready site actually needs rollback-class approval on closer
   inspection.
3. A 9th mutation dispatch site is discovered that this plan's inventory
   (§2) missed.
4. Canonical routing (§7, §13) cannot preserve PH2/PH3's existing
   mechanical semantics.
5. Promotion freshness (§9.2) cannot be made truthfully operation-bound
   using only the existing ECP/EPR/PER model.
6. The existing policy registry proves insufficient for any Wave-1
   request (none is expected, per §12 of RWMPC-001's satisfiability
   matrix, but this is not to be papered over if found false).

No stop condition triggered during this planning phase's own inspection.

---

## 18. Explicit Scope-Creep Prohibitions (restated, binding on 149F)

- No rollback wiring with a fabricated or default `approval_present`.
- No broker-wiring of TK1/TK2/TK3.
- No touching Prompt Creation / Prompt Dispatch / agent invocation.
- No routing any Wave-1 site through Runtime Enforcement.
- No new `POL-013+`.
- No amendment of RWMPC-001, PBPC-001, or PBPA-001.
- No runtime-capability elevation.

---

## 19. Findings

| ID | Classification | Finding |
|---|---|---|
| F-149E-1 | OBSERVATION | The historical-guard search (§14) was necessarily partial (2 of 30 relevant test files checked by pattern match within this planning phase's read budget); 149F must run the full search before wiring AG1/AG2/AG4, particularly against `test_agent.py`'s 65,734 lines. |
| F-149E-2 | OBSERVATION | `test_agent.py`'s size (65,734 lines) is itself a pre-existing structural risk for future maintainability, unrelated to RWMPC-001; noted, not remediated — out of this phase's and 149F's scope. |
| F-149E-3 | OBSERVATION | AG4's self-modification threat (`pcae promote` targeting `src/pcae/**`) is deliberately left without a new mechanical hard block in Wave 1, per RWMPC-REQ-019's explicit instruction not to over-gate via misclassification; this is a tracked, contract-sanctioned decision (§9.4), not an oversight. |
| F-149E-4 | OBSERVATION | PH2/PH3's routing target is AG2's adapter, not `pcae push`'s own Chapter-148 machinery, because the two are structurally different operations (§7, §13); a literal reading of RWMPC-REQ-035's phrase "the same adapter `pcae push`/AG2 use" is satisfied since AG2 itself will be the one shared, broker-wired push adapter both `pcae push` (informally, by analogy) and PH2/PH3 (literally, by routing) exist alongside. |

**No BLOCKING finding.** No unresolved architecture question prevents
Wave-1 implementation from proceeding as scoped.

---

## 20. Wave-1 Completion Criteria (bound to RWMPC-REQ-054, restated for 149F/149G)

The future implementation may be considered complete only when all of:
every one of the six Wave-1 sites migrated per its frozen disposition; no
Wave-1 site retains an ungated direct mutation bypass; every broker
request truthful (§2.1's table, verbatim); no caller-selectable
classification (§12); `ALLOW`-only continuation (§4.2); operation
freshness enforced per class (§8.2, §9.2, Chapter-148-shape for §7); stale
`ALLOW` cannot mutate; all existing mechanical checks intact; Chapter-148
push semantics intact and unaffected; AG3/AG5 behavior byte-identical;
TK1-3 behavior byte-identical; mutation inventory guard passes with zero
`UNKNOWN`; all new and existing regression suites pass; Fast Green passes
with the then-current count reported (not assumed); runtime remains
`Observed`/`observe`/`unavailable`.

---

## 21. Plan Verdict

**IMPLEMENTATION PLAN COMPLETE — WAVE 1 READY.**

All eight `EXECUTION_CLASS_MUTATION` sites (2 already implemented, 6
planned here) have a concrete, traceable, minimal-duplication design.
No architectural question remains open at BLOCKING severity. Rollback
(AG3, AG5) and task-finish (TK1-3) are explicitly, individually excluded
with re-affirmation criteria recorded, not silently dropped.

---

## 22. Recommended Next Phase

**149F — Repository-Wide Mutation Permission Coverage Wave 1
Implementation**, scoped exactly to the six sites in §3 (AG1, AG2, AG4,
PH1, PH2, PH3), following §15's sequencing and §16's atomic commit
boundaries, subject to §17's stop conditions and §18's scope-creep
prohibitions. 149F does not touch AG3, AG5, or TK1-3. A subsequent
**149G — Wave-1 Independent Verification** phase (mirroring the
149B/149C/149D pattern already used for the contract itself) should
follow 149F before Chapter 149 makes any completion claim, per RWMPC-REQ-054.

---

## 23. Explicit Confirmations

- RWMPC-001 v1.0 remains unchanged by this phase.
- PBPC-001 v1.2 remains unchanged by this phase.
- PBPA-001 v1.0 remains unchanged by this phase.
- No production source (`src/pcae/**`) was modified by Phase 149E.
- No new Permission Broker production consumer was implemented.
- No mutation path was modified or activated.
- Rollback coverage (AG3, AG5) remains blocked pending trusted approval
  evidence; no approval was fabricated; no evidence source was designed
  beyond the conceptual future-seam placeholder in §2.2 (no provider, no
  default `True`).
- The three task-finish commit paths (TK1-TK3) remain explicitly deferred.
- No `POL-001..012` meaning was changed. No `POL-013+` was added.
- Interactive Workflow Confirmation remains distinct from approval;
  Authority Evaluation / AESIC remains disclosure-only — neither is
  touched by this plan.
- No Runtime Enforcement behavior was changed.
- No Prompt Generation, Prompt Dispatch, or agent-invocation capability
  was implemented.
- Runtime remains `Observed`, maximum capability remains `observe`,
  execution availability remains `unavailable`.

---

## 24. Production and Contract Diff Verification

```
git diff --name-only 674df97a..HEAD -- src/pcae/          -> (expected: empty)
git diff --name-only 674df97a..HEAD -- docs/contracts/     -> (expected: empty)
```

To be re-verified at phase-completion time (§ governance finalization),
immediately before staging the phase-completion report.
