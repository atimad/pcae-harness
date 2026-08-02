# Phase 148D — Permission Broker Production Consumption Implementation Plan

## Status

**Phase type:** production implementation planning only. No production
source under `src/pcae/**` is modified by this phase (verified: `git diff
--name-only 169ff20a..HEAD -- src/pcae/` is empty, checked again at
finalization).

**Baseline commit:** `169ff20a` (HEAD at phase start, tip of
`Phase 148C.10: close out task lifecycle, open idle placeholder`).

**Governing contracts (both read directly, both unamended by this phase):**
- `PBPC-001` v1.2 — `docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`
- `PBPA-001` v1.0 — `docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`

**148C-B-1:** CLOSED (unchanged by this phase; independently re-confirmed
during initial inspection, Section 1).

**Verdict of this phase:** Implementation planning **complete**. **Zero
Blocking findings.** A bounded production implementation phase (148E) is
recommended, followed by a mandatory independent implementation
verification phase (148F).

---

## 0. Objective

Answer, exactly and boundedly, per the phase prompt:

> Exactly how should both real `pcae push` dispatch paths consume one
> centralized Permission Broker decision boundary without weakening
> existing push safety, duplicating permission authority, or
> reclassifying mechanical validations as policy decisions?

PBPC-001 v1.2 already answers most of the architectural "what" (it is
itself an independently-reconstructed, frozen contract). This plan's job
is the implementation-level "how": exact insertion points, exact adapter
shape, exact test inventory, exact file budget, exact commit/rollback
strategy — bound to the contract's requirements (`PBPC-REQ-###`), not a
re-derivation of them. Where this plan states a design choice, it cites
the `PBPC-REQ-###` that controls it.

---

## 1. Initial Inspection (read-only, reproduced results)

Run at phase start, from `~/repos/pcae-harness`:

| Check | Result |
|---|---|
| `git status --short` | clean |
| `git status --branch --short` | `## main...origin/main` (no divergence markers) |
| `git rev-list --count origin/main..HEAD` | `0` |
| `pcae health` | healthy; active task at start: idle placeholder `20260802-1849-idle-awaiting-next-governed-phase-post-148c-10` (retired via `pcae task transition` before any planning work — Section 10) |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae doctor task-memory` | clean, no inconsistencies |
| `pcae push check` | `nothing_to_push` (clean, 0 unpushed, phase-report trust/identity both passed) |
| `pcae runtime inspect` | State: Observed; Maximum capability: observe; Execution capability: unavailable; Registry: empty, 0 plugins |
| `source ~/.config/pcae/telegram.env && pcae notify status` | Telegram configured, enabled, ready; notify-on-`phase complete` gated by `PCAE_NOTIFY_ENABLED=1` |
| `pcae phase-report show --latest` | Phase 148C.10 report: status completed, complete ✅, Pushed: pushed, origin/main..HEAD: 0, verdict VERIFIED |
| `pcae phase-report reconcile --phase-id 148C.10` | read-only inspection: status `conflict` (`payload_conflict` / checkpoint-identity conflict against already-promoted 148C.10 artifacts) — **pre-existing state of an already-finalized phase's stored reconciliation snapshot, not something 148D produced or needs to correct**; the same `--latest` phase report (above) independently confirms 148C.10's canonical report content is complete, correctly identified, and already pushed. Reconciliation ran strictly read-only (mutation: none), as required. Treated as a pre-existing Observation, not a 148D blocker — see Section 20. |

Confirmed against the prompt's required checklist:
- repository clean — yes
- `origin/main..HEAD` = 0 — yes
- 148C.10 complete — yes
- PBPC-001 v1.2 independently (re-)confirmed present and unamended — yes (Section 2)
- PBPA-001 v1.0 independently (re-)confirmed present and unamended — yes (Section 2)
- 148C-B-1 CLOSED — yes (Section 2)
- production push unwired — yes, re-confirmed by direct source inspection (Section 3): zero references to `PermissionBroker`/`permission_broker_foundation` in `src/pcae/commands/push.py`
- runtime Observed / observe / unavailable — yes

---

## 2. Contract State Re-Confirmation

- `docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md` header: **Contract PBPC-001, Version 1.2, Status FROZEN (amended; Finding B-1 is CLOSED)**. Frozen by Phase 148B; amended by 148C.1 (did not close B-1); further amended by 148C.9 (ratifies 148C.8's closure).
- `docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`: PBPA-001 v1.0, single commit since freeze (`234fce06`, Phase 148C.3) — unamended.
- 148C-B-1 status (Section 8.1 of PBPC-001): **CLOSED**. `POL-004`'s `applicable_execution_classes = {SHELL, BACKEND, ADAPTER, ROLLBACK}` (PBPA-REQ-063) excludes `EXECUTION_CLASS_MUTATION` (`pcae push`'s fixed value, PBPC-REQ-034) — `POL-004` is not applicable, not applicability-voting-ALLOW; the canonical push request reaches `ALLOW` via `_compose`'s "nothing triggered among the applicable set" path.
- Canonical verified push-shaped decision (re-derivable from the live, unmodified Foundation; not re-executed as a new claim by this planning-only phase, since 148C.10 already did so fresh): `decision=ALLOW`, `POL-004` in `non_applicable_policy_ids`, `causing_policy_ids=()`.

This phase performs no new contract amendment and no new empirical broker
execution — it is bound by, and cites, the already-independently-verified
148C.10 findings rather than re-deriving them a third time.

---

## 3. Reconstructed Current Push Control Flow

Source: `src/pcae/commands/push.py` (895 lines), read directly, current
line numbers as of baseline `169ff20a`.

```
pcae push [--staged-file-aware] [--dry-run] [--json]
      |
run_push(args)                                            push.py:398
      |
      +-- staged_file_aware? ---------------------------> _run_push_staged_file_aware()  push.py:490
      |         (dispatched BEFORE assess_push_readiness() is ever called)
      |
      +-- (ordinary path) assess_push_readiness(root)     push.py:406, :208
              |  - read_git_changes / read_git_branch (git_status.py)
              |  - _count_unpushed_commits (git rev-list, push.py:874)
              |  - build_health_data / is_healthy (health.py)
              |  - run_checks (check.py)
              |  - diagnose_task_memory (tasks.py)
              |  - _assess_phase_report_trust (push.py:166; Phase 105D content-completeness gate)
              |  - _detect_phase_report_gap (push.py:74; Phase 137F.1 stale/wrong-phase gate)
              |  - lifecycle_review_status (review.py) + load_policy (policy.py)
              |  - _determine_mode(...) -> nothing_to_push | active_task | post_finish_closure | not_ready
              v
        readiness.ready? --no--> not-ready output, exit 1 (or reconcile-post-push if nothing_to_push)
              |
             yes
              |
        dry_run? --yes--> print "Dry run: push skipped.", exit 0 (no dispatch)
              |
             no
              |
        print "EXECUTING REAL PUSH: ..." banner                       push.py:446-451
              |
        subprocess.run(["git", "push"], ...)          <-- PATH A DISPATCH   push.py:454-460
              |
        _reconcile_post_push(root)                                    push.py:473, :353
              |
        print result / JSON, exit 0
```

Staged-file-aware path (`_run_push_staged_file_aware`, `push.py:490-654`):

```
_run_push_staged_file_aware(root, args, dry_run)
      |
      +-- _assess_phase_report_trust(root)      -- fails closed if "failed" (push.py:507-520)
      +-- _detect_phase_report_gap(root)         -- fails closed if "failed" (push.py:522-532)
      |    (Phase 137F.1V — closes the gap where this path bypassed the ordinary
      |     path's phase-report gates entirely)
      |
      +-- _staged_file_snapshot(root.path)   -- protected staged-file hashes, before
      +-- _unpushed_commit_lines(root.path)  -- unpushed_count == 0? --> nothing_to_push, exit 0
      +-- _files_in_unpushed_range(root.path)
      +-- protected_in_commits check          -- blocks if protected staged file appears in unpushed range
      +-- force-push-required check (`git merge-base --is-ancestor origin/main HEAD`)
      |
      dry_run? --yes--> "ready (dry run)", exit 0 (no dispatch)
              |
             no
              |
        subprocess.run(["git", "push", "origin", "main"], ...)  <-- PATH B DISPATCH  push.py:604-612
              |
        post-push protected-file preservation check, exit 0
```

`observe()` (`command_path_observation.py`) is called only from
`run_push_check()` (`push.py:303-313`, `pcae push check`, read-only), with
its decision explicitly discarded (`except Exception: pass`, no branching
on the return value). It is **not** called from `run_push()` or
`_run_push_staged_file_aware()` today — PBPC-REQ-015 confirms this
observation touchpoint is unaffected by and not prior art for PBPC-001's
production consumption.

---

## 4. Both Real Dispatch Sites (re-derived)

Re-derivation confirms PBPC-REQ-013/014 exactly, against current source:

| | Path A — ordinary push | Path B — `--staged-file-aware` push |
|---|---|---|
| Function | `run_push()` | `_run_push_staged_file_aware()` |
| Dispatch line | `push.py:454-460` | `push.py:604-612` |
| Dispatch command | `subprocess.run(["git", "push"], cwd=root.path, check=True, capture_output=True, text=True)` | `subprocess.run(["git", "push", "origin", "main"], cwd=root.path, check=True, capture_output=True, text=True, timeout=60)` |
| Pre-dispatch conditions | `readiness.ready` (full `assess_push_readiness`: clean tree, health, check, doctor, lifecycle review, phase-report trust, phase-report identity) AND `not dry_run` | phase-report trust passed AND phase-report identity passed AND `unpushed_count > 0` AND no protected-staged-file-in-unpushed-range conflict AND no force-push-required condition AND `not dry_run` — **narrower**, never checks `health_ok`/`check_ok`/`doctor_ok`/lifecycle review |
| Post-dispatch behavior | `_reconcile_post_push(root)` (canonicalization/notification reuse), print/JSON output, exit 0 | protected-staged-file preservation re-check, print/JSON output, exit 0 (no `_reconcile_post_push` call on this path today — unchanged by this plan) |

Both counts and line ranges match PBPC-REQ-013 exactly against the current
tree (no drift since 148C.10). **This plan reconfirms exactly two real
`git push` dispatch sites; no third exists** (Section 15 below,
exhaustive-search re-confirmation).

---

## 5. Mandatory Consumption Point

Per PBPC-REQ-040/041, the Decision Consumption Point is fixed **immediately
before each dispatch site**, not at a single pre-branch call. Rationale,
evaluated against the three options the phase prompt lists:

- **Single pre-branch broker call** (before the `staged_file_aware`
  branch in `run_push()`): rejected. Path B's readiness computation is
  itself branch-specific (protected-file snapshot, force-push-required
  check) and happens *after* dispatch selection; a single upfront call
  cannot yet observe Path-B-specific identity facts (Section 7), and
  `dry_run` short-circuits before dispatch on both paths — a pre-branch
  call would evaluate the broker even for `--dry-run` invocations that
  never push, which PBPC-REQ-051 ("exactly once per push attempt")
  reads naturally as *per dispatch attempt*, not per CLI invocation.
- **Shared helper invoked by both dispatch paths**: **selected**. A single
  `evaluate_push_permission(...)`-shaped helper (Section 12) is called
  from two call sites — immediately before `push.py:454` and immediately
  before `push.py:604` — so there is exactly one implementation of
  request construction + broker call + decision consumption, invoked
  twice (once per actual dispatch attempt), never duplicated logic.
- **One decision construction + two mandatory consumption checks**:
  rejected as a separate design — it would require binding one decision
  across two dispatch sites, which contradicts PBPC-REQ-051's "one
  decision per push attempt" and PBPC-REQ-072's "no stale decision reuse"
  (Section 15/20 below); a push attempt dispatches through exactly one of
  Path A or Path B, never both, so there is never a scenario where one
  decision needs to authorize two dispatches.

This is the least-bypassable design available: the shared helper is the
single code path capable of returning "authorized," and it sits directly
adjacent to (not decoupled from) each dispatch call, closing the gap
PBPC-REQ-019/020 identify (no alternate path may dispatch without
consuming a matching `ALLOW`).

---

## 6. Decision Construction vs. Decision Consumption — Explicit Separation

Two conceptually and (per Section 12) physically separate steps inside the
shared helper, never merged into subprocess code:

```
push facts (readiness state, already gathered by existing code)
      |
[CONSTRUCTION]  build_permission_broker_request(...)   -- pure, no I/O
      |
PermissionBrokerRequest
      |
PermissionBroker().evaluate(request)                    -- pure, no I/O, no execution
      |
PermissionBrokerDecision
      |
[CONSUMPTION]  branch on decision.decision (ALLOW / DENY / HUMAN_REVIEW)
      |
authorize-to-continue (bool) + diagnostics
```

The helper itself never calls `subprocess.run` and never touches `git` —
it returns a structured result; the existing dispatch call remains the
only place `git push` is ever invoked (unchanged call sites, only a new
guard placed immediately before each).

---

## 7. Canonical Request Construction — Field-by-Field Provenance

| Field | Value | Source fact | Owner | Derivation | Validation | PBPC requirement |
|---|---|---|---|---|---|---|
| `action_type` | `ACTION_PUSH` (`"push"`) | fixed literal, trusted integration code | push integration adapter | not user-selectable | must be in `KNOWN_ACTION_TYPES` (POL-006 already enforces) | PBPC-REQ-033, PBPC-REQ-046 |
| `execution_class` | `EXECUTION_CLASS_MUTATION` (`"mutation"`) | fixed literal, trusted integration code | push integration adapter | not user-selectable, no `--execution-class` flag (Section 8) | must be in `KNOWN_EXECUTION_CLASSES` | PBPC-REQ-034, PBPC-REQ-046 |
| `requested_component` | `"COMP-001"` | fixed literal | push integration adapter | Permission Broker's own component ID | must be in `COMPONENT_IDS` (POL-007) | PBPC-REQ-035, PBPC-REQ-046 |
| `requested_capability` | `"pcae_push"` (new literal, distinct from `"pcae_push_check"`) | fixed literal | push integration adapter | distinguishes real dispatch consumption from the existing INT-004 observation touchpoint | no `POL-` rule currently inspects this field; diagnostic-only | PBPC-REQ-046 |
| `task_id` | live | `find_latest_active_task(root)` (existing call, `push.py:242-243` pattern reused) | existing task lookup | already computed by `assess_push_readiness` today | drives `POL-001` | PBPC-REQ-042 identity table, PBPC-REQ-046 |
| `phase_id` | optional, omitted or derived from active task title if trivially available | existing task lookup | push integration adapter | no `POL-` rule inspects it; diagnostic-only | n/a | PBPC-REQ-047 analog (optional field) |
| `requested_resource` | e.g. `"refs/heads/<branch>"` (optional) | `read_git_branch(root)` (existing) | push integration adapter | diagnostic clarity only | absence must not change decision | PBPC-REQ-047 |
| `evidence_available` | `True` | the adapter is only ever called after `assess_push_readiness()` / Path B's own checks have already gathered readiness evidence | push integration adapter | never fabricated — the adapter, by construction, is unreachable before evidence exists | drives `POL-003` | PBPC-REQ-046 |
| `approval_present` | `False` | fixed, honest — no execution-approval artifact exists (`COMP-003` not implemented) | push integration adapter | never mapped from IWC confirmation, AESIC, or task state (Section 9) | drives `POL-004` (currently non-applicable to `mutation`, PBPA-001 §37/PBPA-REQ-063) | PBPC-REQ-046, Section 8.1 |
| `simulation_only` | `True` | truthful given no execution boundary (`COMP-002` not implemented) exists yet — see Section 9 | push integration adapter | fixed; never toggled by any caller-reachable path | drives `POL-005`; must remain `True` or `ALLOW` becomes structurally impossible (F-148C.8-1, Section 10) | PBPC-REQ-036, PBPC-REQ-046 |
| `request_id`, `timestamp` | generated | `build_permission_broker_request`'s existing UUID/ISO-8601 generation, unmodified | Foundation constructor | no alternate identity scheme | n/a | PBPC-REQ-049 |

No field is fabricated to obtain `ALLOW`: `evidence_available=True` and
`approval_present=False` are both true statements about the actual state
of the world at request-construction time, not values chosen for their
effect on the decision.

---

## 8. Request Classification Authority — `execution_class`

`execution_class=EXECUTION_CLASS_MUTATION` is a fixed literal set by
trusted push-integration code, never a CLI-exposed choice. The
implementation plan explicitly prohibits:

- `--execution-class` (or any other flag letting the caller choose the
  policy profile),
- any code path where `execution_class` is derived from user input, task
  metadata the user controls, or environment variables.

This preserves PBPC-REQ-034 (fixed) and Section 18 of the phase prompt
(no user CLI option to select execution class). `pcae push --help`'s
existing flag surface (`--staged-file-aware`, `--dry-run`, `--json`)
requires **zero** additions for this reason (Section 18, API change
assessment).

---

## 9. `approval_present` Semantics

Fixed `False`. Explicitly, this plan does **not**:

- map `--staged-file-aware`'s "confirmation" semantics (there is none
  today — no interactive prompt exists on this path) to `approval_present`;
- map Interactive Workflow Confirmation (IWC) state to `approval_present`
  (PBPC-REQ-074/075/077 — IWC and Permission Broker approval are frozen as
  non-interchangeable);
- map Authority Evaluation / AESIC disclosure state to `approval_present`
  (PBPC-REQ-078/079/080 — AESIC is disclosure-only, never a permission
  input);
- infer approval from active-task state, lifecycle-review approval, or any
  other existing "looks approved" signal.

`POL-004`'s non-applicability to `execution_class=mutation` (Section 2, PBPA-001
§37/PBPA-REQ-063) is what allows the canonical request to reach `ALLOW`
— not a fabricated `approval_present=True`. This is precisely Section 8.1's
"applicability is not a permission vote" distinction, and the plan
preserves it by never touching `approval_present`'s fixed `False` value.

---

## 10. `simulation_only` Semantics and F-148C.8-1 Implementation Consequence

`simulation_only=True` is fixed for every `pcae push` request the
adapter constructs, per PBPC-REQ-036: this Foundation has no execution
boundary (`COMP-002` is `not_implemented`), so **every** request the
broker evaluates today — including this one — is inherently a policy
simulation, never a literal execution attempt as the broker itself models
"execution." This is truthful even though, downstream of a `PermissionBroker`
`ALLOW`, `push.py`'s own, already-existing `subprocess.run(["git", "push"], ...)`
call *does* perform a real, non-simulated mutation of remote state — but
that mutation is `pcae push`'s pre-existing capability (Section 23,
PBPC-REQ-081/083), not something the broker itself is being asked to
carry out. The broker's `simulation_only` field describes whether *this
evaluation call* represents an executable authorization within the
Foundation's own execution model — it does not, and cannot yet, because
`COMP-002` does not exist.

**F-148C.8-1 implementation consequence:** the single most important
adapter-correctness invariant this plan enforces is that no code path,
now or by future accidental edit, ever constructs the canonical push
request with `simulation_only=False`. Doing so flips `POL-005`
(`ExecutionDisabledRule`) to unconditional `DENY`
(`execution_boundary_unavailable`), since `POL-005` is universal
(`applicable_execution_classes = None`) and evaluates on every request
regardless of `execution_class`. Section 17 (test plan) makes this a
first-class, explicitly named regression test
(`test_adapter_never_passes_simulation_only_false`), not an incidental
assertion buried in a broader test.

---

## 11. Mechanical vs. Permission-Bearing Classification

Applying PBPC-REQ-018's framework to every current push check
(`assess_push_readiness` and Path B's own checks):

| Condition | Classification | Rationale |
|---|---|---|
| Working tree clean (`changes` empty) | MECHANICAL | structural git-state fact, not a normative judgment |
| Unpushed commit count | MECHANICAL / OBSERVATIONAL | drives `mode`, not a permission question |
| `health_ok` | MECHANICAL | derived diagnostic state (`build_health_data`) |
| `check_ok` | STRUCTURAL | governance-check pass/fail is itself a scope/contract-shape validation, not a "may this specific push proceed" judgment |
| `doctor_ok` | MECHANICAL | task-memory diagnostic |
| Lifecycle review required-and-passed | PERMISSION_BEARING (candidate) | answers "may this push proceed given review policy" — but has **no** existing Foundation `POL-` representation (Section 13); remains push-owned per PBPC-REQ-016/017 |
| Phase-report trust (105D) | STRUCTURAL | content-completeness of an artifact, not a push-specific permission judgment |
| Phase-report identity (137F.1) | STRUCTURAL | artifact-identity correctness, same category |
| Protected-staged-file preservation (Path B) | MECHANICAL | git-state bookkeeping around the push, not a permission gate on whether push may occur |
| Force-push-required detection (Path B) | STRUCTURAL/MECHANICAL | detects an operation shape (`--force` would be needed) `pcae push` never performs; not itself a policy judgment since force is never attempted |
| Active task presence | PERMISSION_BEARING | directly maps to `POL-001` (`MissingActiveTaskRule`) — the one condition PBPC-REQ-016's table calls "newly bound" |
| `--dry-run` | OBSERVATIONAL | caller intent flag, not a condition of the repository or task state |

Only **one** existing push condition (active-task presence) has both a
direct Foundation `POL-` representation and answers "may this push
proceed" rather than "can this operation be structurally formed" — this
matches PBPC-REQ-016's table exactly (`POL-001` "newly bound", every
other row "remains push-owned" or "out of scope, not push-relevant").
**No blanket migration of all 12 `HARD_BLOCK_REGISTRY` entries into the
Foundation is planned or warranted** — 9 of 12 are shell-gate/hook-layer
conditions entirely outside `pcae push`'s own control flow (raw git
push/commit, force push, `--no-verify`, destructive filesystem, unknown
command class, out-of-scope path, policy-forbidden file, forbidden path,
enforcement-not-ready/not-authorized), 2 map onto conditions `push.py`
itself has never enforced as hard blocks (`blocked_by_missing_task`
partially, addressed via `POL-001` binding), and the remaining
push-owned mechanical/structural conditions (health/check/doctor/
lifecycle-review/phase-report-trust/phase-report-identity) correctly stay
where they are per PBPC-REQ-017's "no weaker, no broader, no silent
removal" instruction.

---

## 12. `HARD_BLOCK_REGISTRY` Reconstruction (12 entries, re-verified)

Re-read `src/pcae/core/permission_broker.py:744-829` directly (import
count independently re-confirmed: `len(HARD_BLOCK_REGISTRY) == 12`).

| Condition | Current check | Mechanical/permission-bearing | Current owner | Future owner |
|---|---|---|---|---|
| `blocked_by_raw_git_commit` | shell-gate/hook layer | out of `pcae push` scope (commit, not push) | shell-gate | unchanged |
| `blocked_by_raw_git_push` | shell-gate/hook layer | out of `pcae push`'s own control flow (governs raw shell invocation, not the `pcae push` command) | shell-gate | unchanged |
| `blocked_by_force_push` | shell-gate/hook layer | n/a to this MVP — neither dispatch call ever passes `--force` | shell-gate | unchanged |
| `blocked_by_no_verify` | shell-gate/hook layer | n/a — neither dispatch call passes `--no-verify` | shell-gate | unchanged |
| `blocked_by_destructive_filesystem` | shell-gate/hook layer | out of scope (filesystem-scoped) | shell-gate | unchanged |
| `blocked_by_unknown_command_class` | shell-gate/hook layer | out of scope (generic classification layer) | shell-gate | unchanged |
| `blocked_by_out_of_scope` | shell-gate/hook layer | out of scope (path-scoped) | shell-gate | unchanged |
| `blocked_by_policy_forbidden_file` | shell-gate/hook layer | out of scope (path-scoped) | shell-gate | unchanged |
| `blocked_by_forbidden_path` | shell-gate/hook layer | out of scope (path-scoped) | shell-gate | unchanged |
| `blocked_by_missing_task` | not directly enforced by `push.py` today | PERMISSION_BEARING, maps to `POL-001` | (legacy registry only; not actually wired into `push.py`) | Foundation (`POL-001`, via the new adapter's `task_id` binding) |
| `blocked_by_enforcement_not_ready` | shell-gate/hook layer | out of scope (generic enforcement-readiness gate) | shell-gate | unchanged |
| `blocked_by_enforcement_not_authorized` | shell-gate/hook layer | out of scope (generic enforcement-authorization gate) | shell-gate | unchanged |

Semantics unchanged for every row — this plan does not touch
`permission_broker.py` or its registry at all (Section 19, file budget).

---

## 13. Existing `POL-` Mapping

| Push fact | Foundation policy | Request field | Decision behavior |
|---|---|---|---|
| Active task presence | `POL-001` `MissingActiveTaskRule` | `task_id` | `DENY` if falsy |
| (n/a — no push-specific evidence gap) | `POL-002` (stub, `Task Outside Scope`) | n/a | never triggers |
| Evidence gathered before request construction | `POL-003` `MissingEvidenceRule` | `evidence_available` | `DENY` if `False`; adapter always passes `True` truthfully |
| Human approval for mediated-execution classes | `POL-004` `MissingHumanApprovalRule` | `approval_present`, gated by `execution_class` applicability | non-applicable for `mutation` (Section 2/9); no `HUMAN_REVIEW` from this rule for `pcae push` |
| Execution boundary availability | `POL-005` `ExecutionDisabledRule` | `simulation_only` | `DENY` if `False`; adapter always passes `True` (Section 10) |
| Recognized `action_type`/`execution_class` | `POL-006` `UnknownCapabilityRule` | `action_type`, `execution_class` | `DENY` if either unrecognized; both fixed to known values |
| Recognized `requested_component` | `POL-007` `UnknownComponentRule` | `requested_component` | `DENY` if unrecognized; fixed to `"COMP-001"` |
| (stubs, never trigger) | `POL-008..012` | n/a | never trigger — registered placeholders only |

**No Blocking gap found.** Re-derived independently for 148D (not merely
cited from 148C.8): every permission-bearing push condition that has a
Foundation policy representation is accounted for above; the one
permission-bearing condition without a Foundation representation
(lifecycle-review-required-and-passed) is correctly classified
PERMISSION_BEARING but is explicitly *push-owned by design*
(PBPC-REQ-016/017 — "remains push-owned," not a coverage gap, because it
answers a `pcae`-lifecycle-policy question the Foundation's `POL-`
vocabulary was never scoped to represent, and PBPC-REQ-018 explicitly
disclaims full push-condition coverage as a contract goal).

---

## 14. Adapter Design

A narrow helper, conceptually:

```python
def evaluate_push_permission(
    *,
    root: HarnessPath,
    task_id: str | None,
    requested_resource: str | None = None,
) -> PushPermissionResult:
    ...
```

Responsibilities (and explicit non-responsibilities):

- accepts canonical facts already gathered by existing readiness code
  (`task_id` from the existing active-task lookup; nothing new is
  scanned or computed beyond what `assess_push_readiness`/Path B already
  gather, aside from `requested_resource`'s optional branch name reuse);
- constructs one `PermissionBrokerRequest` via
  `build_permission_broker_request(...)` (unmodified constructor,
  PBPC-REQ-045);
- calls `PermissionBroker().evaluate(request)` exactly once
  (PBPC-REQ-051);
- returns a small structured result (decision, diagnostics fields per
  Section 16) — **does not** dispatch `git push`, **does not** mutate the
  repository, **does not** duplicate any `POL-` logic, **does not**
  construct its own `PolicyRegistry` (Section 15).

Naming follows the repository's existing lower_snake_case
`evaluate_*`/`assess_*`/`build_*` conventions already used throughout
`push.py` (`assess_push_readiness`, `build_permission_broker_request`) and
`permission_broker_foundation.py`.

---

## 15. Adapter Placement

**Selected: `src/pcae/commands/push.py`**, as a new private module-level
function (e.g. `_evaluate_push_permission`), colocated with
`assess_push_readiness` and the other existing push-only helpers,
**not** a new module under `src/pcae/core/`.

Rationale: the helper's only job is translating `push.py`'s own
already-gathered readiness facts into a `PermissionBrokerRequest` and
consuming the result — it has no reusable logic a second command would
import (PBPC-001's MVP scope, PBPC-REQ-004/005, is `pcae push` only; no
other command is in scope). Creating a new `src/pcae/core/...permission...`
module for a single caller would violate Section 60's "unnecessary
module" warning and Section 59's narrow file-budget goal (Section 19
below) without any offsetting reuse benefit. If a second production
consumer of the Permission Broker is authorized in a future phase, that
phase is the correct point to extract a shared module — not 148D/148E
speculatively.

---

## 16. Foundation Construction

The adapter constructs `PermissionBroker()` with **no arguments** —
`PermissionBroker.__init__(self, registry: PolicyRegistry | None = None)`
already defaults to `PolicyRegistry()`, which defaults to
`DEFAULT_POLICY_RULES` (the canonical `POL-001..012` tuple,
`permission_broker_foundation.py:620-633`). The adapter never:

- constructs a custom `PolicyRegistry` with a reduced or reordered rule
  tuple,
- accepts a caller-supplied registry/broker instance from any CLI-
  reachable code path,
- rebuilds policy logic locally.

Test-only dependency injection (Section 22) is confined to test code that
imports the adapter and passes an explicit `PermissionBroker` instance
directly to a *test-only* parameter or via monkeypatching the module-level
constructor call — never something a production caller (a real `pcae
push` invocation) can influence.

---

## 17. No Caller Policy Selection

Explicitly prohibited, matching Section 18 of the phase prompt and
PBPC-REQ-038 (single owner, no dual authority):

- `exclude_policies`
- `selected_policy_ids`
- `skip_policy`
- `policy_profile`
- any equivalent flag, environment variable, or config key reachable from
  a `pcae push` invocation.

`PermissionBroker.evaluate(self, request)`'s existing public signature
(confirmed by 148C.10's own `inspect.signature` check, re-confirmed by
direct source read here) takes exactly one parameter; the adapter must
not widen that surface or route around it.

---

## 18. Decision Consumption Semantics

Frozen, per PBPC-REQ-052:

```
ALLOW           -> continue to final pre-dispatch validation (Section 21), then dispatch
DENY            -> abort; zero git push; surface decision_reason + matched_no_go_ids
HUMAN_REVIEW    -> abort; zero git push; no interactive resolution (v1.0 has none, PBPC-REQ-052)
```

No `HUMAN_REVIEW` continuation path, no automatic review resolution, no
"proceed anyway" override. This applies identically on both Path A and
Path B — there is no path-specific relaxation of this table.

---

## 19. Failure Handling (Fail-Closed)

| Failure | Required behavior |
|---|---|
| `PermissionBroker.evaluate()` raises | caught at the adapter boundary; treated as non-ALLOW; abort, zero dispatch |
| Malformed `PermissionBrokerRequest` (e.g. construction fails) | fails closed before `evaluate()` is even called; abort |
| Unknown `execution_class`/`action_type` | already fails closed inside the Foundation via `POL-006` (`DECISION_DENY`) — the adapter's fixed literals (Section 8) make this practically unreachable, but the composition path is still fail-closed if it ever occurred |
| Missing/duplicate policy at `PolicyRegistry` construction | already fails closed via `PolicyRegistry.__init__`'s existing `ValueError` (`permission_broker_foundation.py:690-703`) — since the adapter never constructs a custom registry, this can only occur if the canonical `DEFAULT_POLICY_RULES` itself is malformed, which is a Foundation-level invariant this plan does not touch |
| `evaluate()` returns something other than `DECISION_ALLOW`/`DENY`/`HUMAN_REVIEW`, or an invalid object | already fails closed inside the Foundation via `_sanitize_result` (converts to `DENY`, `decision_reason="invalid_policy_result"`) before the adapter ever sees it |
| Any of the above | dispatch is never reached |

**Required invariant, restated and enforced by construction:** the broker
cannot produce a trustworthy `ALLOW` → push cannot dispatch. The adapter's
consumption logic treats "anything other than a literal `DECISION_ALLOW`
value on a successfully-returned `PermissionBrokerDecision`" as
non-authorizing, with no default-permissive branch anywhere in the
consumption code.

---

## 20. User-Facing Diagnostics

On `DENY`/`HUMAN_REVIEW`/broker-failure, surface (reusing existing
`PermissionBrokerDecision` fields, PBPC-REQ-054/064):

- `decision.decision` (`DENY` / `HUMAN_REVIEW`)
- `decision.decision_reason`
- `decision.causing_policy_ids`
- `decision.matched_no_go_ids`
- optionally, on request: `applicable_policy_ids` / `non_applicable_policy_ids`
  / `evaluated_policy_ids` for deeper diagnostic/audit explanation
  (PBPC-REQ-054, "internal/diagnostic" use — not required in the default
  terse CLI output)

Diagnostics distinguish four categories cleanly, per PBPC-REQ-066:

1. **Permission denied** — `decision.decision == DECISION_DENY` with
   `causing_policy_ids` non-empty and traceable to a real `POL-` rule.
2. **Human review required** — `decision.decision == DECISION_HUMAN_REVIEW`.
3. **Broker failure** — an exception was caught at the adapter boundary,
   or `_sanitize_result`'s `"invalid_policy_result"` reason is present —
   surfaced distinctly from case 1 so an operator does not mistake a
   broker malfunction for an intentional policy denial.
4. **Mechanical validation failure** — the existing `not readiness.ready`
   path (Path A) or existing `bl` blocker list (Path B), entirely
   unchanged, occurring *before* the broker is ever consulted (Section 21
   ordering) — these retain their current, already-existing diagnostic
   output verbatim.

No internal broker state is dumped beyond the fields above (PBPC-REQ-065
— no credentials/tokens/secret material is ever part of a
`PermissionBrokerDecision` to begin with, so this is satisfied by
construction, not by redaction logic).

---

## 21. Exit Codes

Current `pcae push` conventions (unchanged, re-confirmed from source):
`0` on success/nothing-to-push/dry-run, `1` on `not_ready`/mechanical
failure/git error.

Planned PBPC outcome mapping (additive to the existing table, no existing
mapping altered):

| Outcome | Exit code | Rationale |
|---|---|---|
| Mechanical validation failure (existing) | `1` (unchanged) | existing behavior, occurs before broker consultation |
| Broker `DENY` | `1` | consistent with existing "push blocked" convention |
| Broker `HUMAN_REVIEW` | `1` | consistent with existing "push blocked" convention (no distinct exit code introduced — the phase prompt's "distinguish these" requirement is satisfied by diagnostic *text*/`decision` field, not by exit-code fragmentation, since no existing `pcae push` caller/script currently branches on exit code beyond 0-vs-nonzero) |
| Broker failure (exception/invalid result) | `1` | fail-closed, same "push blocked" convention |
| `ALLOW` + successful dispatch | `0` (unchanged) | existing success path |
| `ALLOW` but subsequent `git push` itself fails (existing `CalledProcessError` handling) | `1` (unchanged) | existing behavior, untouched |

No new/inconsistent exit code is introduced. `0` remains reserved
exclusively for "no push was blocked and no push was attempted-and-failed."

---

## 22. Ordinary Push Path Integration (exact insertion)

```python
readiness = assess_push_readiness(root)          # unchanged (push.py:406)
if not readiness.ready:
    ...                                            # unchanged existing not-ready handling
if dry_run:
    ...                                            # unchanged existing dry-run handling (no broker call)

# NEW: Decision Consumption Point, immediately before the existing banner/dispatch
permission_result = _evaluate_push_permission(root=root, task_id=<active task id>, requested_resource=f"refs/heads/{readiness.branch}")
if not permission_result.authorized:
    ...                                            # print diagnostics (Section 20), return 1 -- no dispatch
# existing "EXECUTING REAL PUSH" banner                              (push.py:446-451, unchanged)
# existing subprocess.run(["git", "push"], ...)     <-- PATH A DISPATCH (push.py:454-460, unchanged)
```

Insertion point: strictly between the existing `dry_run` check
(`push.py:426-436`) and the existing "EXECUTING REAL PUSH" banner
(`push.py:446`) — i.e., replacing nothing, only inserting a new guard.
`--dry-run` continues to skip the broker entirely (a dry run performs no
mutation and requests no permission for one — consistent with the broker
never being consulted for `pcae push check` either being extended into
mutation authority, PBPC-REQ-015).

---

## 23. Staged-File-Aware Push Integration (exact insertion)

```python
phase_report_trust = _assess_phase_report_trust(root)   # unchanged (push.py:507)
...                                                       # unchanged existing gates
# ... protected-file snapshot, unpushed-commit check, protected-in-commits check,
#     force-push-required check  -- all unchanged (push.py:534-588)

if dry_run:
    ...                                                   # unchanged existing dry-run handling (no broker call)

# NEW: Decision Consumption Point, immediately before the existing dispatch
permission_result = _evaluate_push_permission(root=root, task_id=<active task id>, requested_resource="refs/heads/main")
if not permission_result.authorized:
    ...                                                   # print diagnostics (Section 20), return 1 -- no dispatch
# existing subprocess.run(["git", "push", "origin", "main"], ...)  <-- PATH B DISPATCH (push.py:604-612, unchanged)
```

Insertion point: strictly between the existing `dry_run` check
(`push.py:590-601`) and the existing dispatch call (`push.py:604`) — same
shared helper as Path A, called a second time with Path-B-specific
`requested_resource`. No early return anywhere in
`_run_push_staged_file_aware` between this insertion point and the
dispatch call may be added or exist that skips the new guard — the
existing early returns (`nothing_to_push`, `protected_in_commits`,
`force_push_required`) all occur **before** this insertion point, so none
of them constitute a bypass; they already prevent dispatch through
mechanical means, exactly as PBPC-REQ-017 requires them to continue doing.

---

## 24. Non-Bypassability

Both dispatch call sites are the *only* two `git push` invocations in
`push.py` (Section 4, re-confirmed) and both receive the identical
Decision Consumption Point pattern (same shared helper, same
ALLOW-required-else-abort branch). Section 15's exhaustive search
(below) confirms no third route exists. There is no flag, environment
variable, or code path in either function that can reach the `subprocess.run`
dispatch call without first passing through the new guard — the guard
is inserted directly above each dispatch line, not behind any
conditionally-skippable branch.

---

## 25. Shared Decision vs. Separate Evaluations — TOCTOU Analysis

**Selected: separate evaluations at each dispatch path's own final
boundary** (not one decision shared across both paths), per Section 5's
reasoning and PBPC-REQ-050/058.

A single `pcae push` invocation dispatches through exactly one of Path A
or Path B (mutually exclusive branch at `push.py:403-404`), so "sharing"
a decision across both paths is never actually needed — each invocation
only ever needs one evaluation, for whichever path it took. This
sidesteps the TOCTOU question of "could Path A's decision be reused for
Path B" (it never needs to be) while still satisfying PBPC-REQ-051
("exactly once per push attempt").

**TOCTOU windows identified** (per PBPC-REQ-055/056/057/058):
- Between broker evaluation and `git push` dispatch, local repository
  state could in principle change (e.g. a concurrent commit) if another
  process mutated the repo between the two lines. PCAE's existing
  single-agent-lock session model (unchanged by this plan) is the
  existing mitigation for concurrent local mutation generally, and this
  plan introduces no new exposure beyond what already exists between
  `assess_push_readiness()` and the current dispatch call today.
- Remote Git state (what `origin/main` looks like at the instant `git
  push` actually runs) can never be transactionally bound locally
  (PBPC-REQ-057) — this is an accepted, documented limitation, not a
  defect this plan can or should close; `git push`'s own atomic
  fast-forward-or-reject semantics remain the actual safety mechanism
  for remote-state races, unchanged.

**Decision freshness:** the broker call happens synchronously,
immediately before the dispatch it authorizes, within the same CLI
process invocation — no cross-invocation caching, no background
evaluation, no persisted decision reused later (Section 26). This
satisfies PBPC-REQ-050's "freshness enforced structurally by binding
evaluation and dispatch within the same synchronous CLI invocation."

**Residual risk (documented, not engineered away):** a local commit
landing in the narrow window between the guard and the dispatch call
could in theory change what gets pushed after `POL-001`'s `task_id`
check already passed. This window is no different in kind from the
window that already exists today between `assess_push_readiness()` and
`push.py`'s existing dispatch call — this plan does not widen it, and
PBPC-REQ-055/056 do not require new locking to close it (over-engineering
locking is explicitly discouraged by the phase prompt, Section 28).

---

## 26. Operation Identity

Facts that must remain stable between broker evaluation and dispatch
(reusing PBPC-REQ-042's identity table, Section 13 above):

- repository root (implicit — same process, same `HarnessPath.cwd()`)
- branch/ref (`readiness.branch` / Path B's fixed `"main"`)
- remote (`"origin"`, fixed, unchanged)
- staged-file-aware mode (fixed by which function is executing — cannot
  change mid-invocation)
- active task/session state (`task_id`, re-observed at guard time, not
  cached from an earlier point in the invocation beyond what
  `assess_push_readiness`/Path B already captured moments earlier)
- relevant readiness state (`readiness.ready` / Path B's own blocker list,
  both already re-checked immediately before this insertion point by
  existing code)

No new field is introduced beyond what PBPC-REQ-042 already lists;
Section 27 (below) enumerates the minimal Section-17 pre-dispatch
revalidation this plan adopts.

---

## 27. Retry / Restart and No Stale Decision Reuse

**Strong default: no reuse.** Every push attempt (a fresh CLI invocation
of `pcae push` or `pcae push --staged-file-aware`) performs a fresh
`_evaluate_push_permission(...)` call — there is no persisted decision
artifact (Section 28) to reuse, and no in-process cache keyed by
task/branch/commit that a second invocation could hit. Per PBPC-REQ-072,
this is not merely the default but the *only* authorized behavior: no
mechanism to intentionally reuse a prior `ALLOW` is introduced.

Covers all five PBPC-REQ-067..072 replay/restart scenarios identically to
the contract's own analysis (decision-obtained-then-crash;
local-op-changes-before-push; push-fails-before-remote-mutation;
push-succeeds-but-local-persistence-fails; process-crashes-during-`git
push`) — none of them are given a bypass path by this plan; every retry
is a brand-new CLI invocation that re-runs the entire control flow from
the top, including a fresh broker evaluation.

---

## 28. No Durable Broker Artifact

Per PBPC-REQ-084 (Option A selected) and Section 30 of the phase prompt,
this plan does **not** introduce `permission_decision.json` or any new
durable, canonical-lifecycle artifact. The `PermissionBrokerDecision`
object is consumed immediately, in-process, and discarded once the
dispatch decision (authorize / abort) has been made — at most it is
rendered into the existing stdout/JSON diagnostic output (Section 20),
never persisted to a new file.

---

## 29. Existing Logging / Observation Integration

`src/pcae/core/command_path_observation.py`'s `observe()` and its
`INTEGRATION_REGISTRY` (INT-001..004) remain **entirely independent** of
this plan's adapter. `_evaluate_push_permission` is a new, separate call
site — it does not call `observe()`, and `observe()`'s existing INT-004
touchpoint (`run_push_check()`, `push.py:303-313`) is not modified,
extended, or repurposed. The new adapter may optionally add a **new**
registry entry (e.g. `INT-005`, `command="pcae push"`,
`integration_type="production-consumption"`,
`implementation_status` distinct from `"observation_only"`) purely as
architectural bookkeeping — this is additive documentation, not a change
to `observe()`'s contract, and is left to 148E's discretion since it is
not required by PBPC-001 for conformance. Observational infrastructure
(`observe()`, `INTEGRATION_REGISTRY`) is never made the decision
authority for `pcae push`'s real dispatch — the adapter calls
`PermissionBroker` directly, mirroring but not reusing `observe()`'s
internal pattern (since `observe()` is contractually observation-only and
swallows exceptions into `None`, which is exactly the fail-open behavior
Section 19 prohibits for the production consumption path).

---

## 30. IWC / AESIC / Runtime Enforcement Independence

- **IWC:** no confirmation lookup is added anywhere in the adapter or
  either dispatch path merely to satisfy the Permission Broker.
  `IWC-REQ-029` is untouched; IWC Confirmation remains conceptually and
  code-path-distinct from Permission Broker approval (PBPC-REQ-074/075/076).
- **AESIC:** Authority Evaluation is not inserted into request
  construction or dispatch eligibility anywhere in this plan
  (PBPC-REQ-078/079/080). `approval_present` is never derived from AESIC
  disclosure state (Section 9).
- **Runtime Enforcement:** `pcae push` remains a direct command-path
  integration; this plan introduces **no** new Runtime Enforcement
  dependency (PBPC-REQ-085/086). `pcae runtime inspect` is expected to
  continue reporting Observed / observe / unavailable unchanged after a
  148E implementation, because this plan governs `pcae push`'s existing
  mutation path — it does not create a new one, and it does not route
  push through the Runtime Enforcement Decision Engine.

---

## 31. Runtime Capability Boundary

`PermissionBroker` `ALLOW` ≠ runtime capability elevation (PBPC-REQ-081).
`pcae push` already possesses its existing `git push` mutation capability
today, independent of this plan — this plan governs *when* that
already-existing capability may be exercised, it does not grant a new
one. After a 148E implementation, `pcae runtime inspect` must continue to
report:

```
State: Observed
Maximum Capability: observe
Execution Availability: unavailable
```

unchanged — because Permission Broker consumption is a policy-decision
gate placed in front of an existing, already-authorized command-path
mutation capability (`pcae push`'s own `git push` calls), not a grant of
new execution capability through the Runtime/Plugin system
(`src/pcae/core/runtime_registry.py` et al., entirely untouched by this
plan).

---

## 32. Existing Push Semantics Preservation Inventory

| Behavior | Current source | Planned change |
|---|---|---|
| `--dry-run` | `push.py:426-436` (Path A), `:590-601` (Path B) | none — broker not consulted on dry runs (Section 22/23) |
| `--staged-file-aware` | `push.py:490-654` | none to its own gates; only a new guard added before dispatch |
| Branch/remote handling | `readiness.branch`, fixed `"origin"` | none |
| Force restrictions | Path B's `merge-base --is-ancestor` check | none |
| Task readiness | `assess_push_readiness` | none — `task_id` additionally feeds the new request, not replacing existing logic |
| Phase-report checks | `_assess_phase_report_trust`, `_detect_phase_report_gap` | none |
| Other hard blocks | protected-staged-file preservation, etc. | none |

**Zero semantic change** to any of the above — the only behavioral
addition is: an `ALLOW`-required guard placed immediately before each
existing dispatch call, which is a strict narrowing (adds a condition
that must additionally hold) never a broadening or relaxation of any
existing gate.

---

## 33. No Push Policy Expansion

No `POL-013+` is introduced. Section 13's mapping shows every relevant
permission-bearing condition already has a Foundation representation;
Section 11 shows the one condition without one
(lifecycle-review-required-and-passed) is intentionally push-owned, not a
Blocking gap (PBPC-REQ-016/018 already disclaim full coverage as a goal).
**No unavoidable need for a new policy was found during this planning
phase.**

---

## 34. Test Change Surface

Existing test files inspected for required updates:

| File | Expected update |
|---|---|
| `tests/test_push.py` | add/adjust cases so existing dispatch-path tests account for the new guard (e.g. monkeypatch/mock the broker to `ALLOW` in existing "push succeeds" tests, so pre-existing assertions about dispatch continue to pass unmodified in intent) |
| `tests/test_commit_push_gate.py` | review for any assumption that `pcae push`'s dispatch is unconditional once `readiness.ready` — update if such an assumption exists |
| `tests/test_staged_file_aware_push.py` | same as `test_push.py`, for Path B |
| `tests/test_push_phase_report_identity_137f1.py` | review only — this file tests phase-report-identity gating, which occurs strictly before the new guard (Section 23); expected to require no change, but must be re-run to confirm |
| `tests/test_permission_broker_foundation.py`, `tests/test_permission_broker_policy_applicability.py`, `tests/test_permission_broker_policy_composition_hardening.py`, `tests/test_permission_broker_policy_rule_framework.py`, `tests/test_phase_148c7_permission_broker_policy_applicability_independent_verification.py`, `tests/test_phase_148c8_permission_broker_production_consumption_b1_reevaluation.py` | no change expected — Foundation/PBPA layer is not modified by 148E; re-run as regression |
| `tests/test_permission_broker.py`, `tests/test_permission_broker_cli.py`, `tests/test_permission_broker_command_path_design.py`, `tests/test_permission_broker_command_path_prototype.py`, `tests/test_permission_broker_observation_hardening.py`, `tests/test_permission_broker_observation_verification.py`, `tests/test_permission_broker_verification_compatibility.py` | no change expected — legacy broker / observation-only INT-001..004 paths untouched |
| `tests/test_post_push_canonicalization.py`, `tests/test_push_state_reconciliation.py` | review only — `_reconcile_post_push` occurs strictly after successful dispatch; expected no change |

Search performed (grep) across `tests/` for `git push`, `push command`,
`HARD_BLOCK_REGISTRY`, `PermissionBroker` confirms the above inventory is
exhaustive for the current test tree; no additional file references these
symbols in a way requiring anticipated changes.

---

## 35. New PBPC Integration Test File (planned, not implemented)

`tests/test_permission_broker_push_production_consumption.py` — planned
contents (148E to implement):

### 36. ALLOW tests
- eligible canonical push (Path A) → mocked `subprocess.run` for `git
  push` → asserts `dispatch_count == 1`, broker call observed with the
  canonical request shape (Section 7).
- same for Path B.

### 37. DENY tests
- construct a request-shape state that resolves `DENY` (e.g. simulate
  missing active task → `POL-001`) → assert `dispatch_count == 0` for
  both paths.

### 38. HUMAN_REVIEW tests
- construct an applicable-`POL-004` state (would require
  `execution_class` other than `mutation`, which the adapter never
  produces — so this is exercised by directly testing the shared helper
  against a *synthetic* request/broker rather than by finding a real
  `pcae push` state that naturally triggers `HUMAN_REVIEW`; the helper's
  own consumption logic is unit-tested against all three
  `PermissionBrokerDecision.decision` values independent of whether
  `pcae push`'s canonical request can itself reach `HUMAN_REVIEW` today)
  → assert `dispatch_count == 0` for both paths.

### 39. Broker failure tests
- inject an exception (monkeypatch `PermissionBroker.evaluate` to raise),
  an invalid decision object, and a registry-construction failure →
  assert `dispatch_count == 0` for both paths in every case.

### 40. Canonical request tests
- assert exact field values: `action_type="push"`,
  `execution_class="mutation"`, `approval_present=False`,
  `simulation_only=True`, plus `requested_component="COMP-001"`,
  `requested_capability="pcae_push"`, and `task_id` bound to the live
  active task — first-class integration contract test, not incidental.

### 41. POL-004 regression
- assert the canonical request's `non_applicable_policy_ids` contains
  `POL-004` and that no fabricated `approval_present=True` value is ever
  observed on the constructed request.

### 42. POL-005 regression
- assert `simulation_only=True` is always passed; add an explicit
  adversarial test that would fail if a future edit accidentally flips it
  to `False` (F-148C.8-1 protection, Section 10) — e.g. directly inspect
  the constructed `PermissionBrokerRequest` object the adapter builds,
  not just the end-to-end decision.

### 43. Applicable-policy explainability tests
- assert `applicable_policy_ids`/`non_applicable_policy_ids`/
  `evaluated_policy_ids`/`causing_policy_ids` remain present and
  internally consistent on the returned decision, without pinning exact
  formatting of any rendered diagnostic string.

### 44. Non-bypassability tests
- monkeypatch/spy on the actual `subprocess.run` git-push call for both
  Path A and Path B; for every non-`ALLOW` broker outcome,
  `dispatch_count == 0`; for eligible `ALLOW`, `dispatch_count` equals
  the existing expected count (1 per successful push).

### 45. Staged-file-aware adversarial coverage
- specifically construct a `--staged-file-aware` invocation and confirm
  it cannot reach `subprocess.run(["git", "push", "origin", "main"], ...)`
  through any existing early-return branch without first passing the new
  guard — i.e., re-run the existing "protected file in unpushed range"
  and "force push required" blocking tests and confirm they still block
  (mechanically, before the broker is even reached) and add a new test
  where those mechanical checks pass but the broker denies, confirming
  the broker guard independently also blocks.

### 46. Existing mechanical failure tests
- re-run and confirm unchanged: mechanical failures (phase-report trust,
  phase-report identity, protected-file conflicts, force-push-required)
  continue to abort exactly as today, without ever reaching the broker
  call (broker call is not exercised — not merely "still blocks" but
  "blocks via the same pre-existing code path, before construction of
  any `PermissionBrokerRequest`").

### 47. Ordering tests
- assert relative order: mechanical validation → broker evaluation →
  (Section 51 freshness) → dispatch, via call-order spies on the relevant
  functions.

### 48. Single-evaluation / exactly-once semantics
- assert `PermissionBroker.evaluate` `call_count == 1` per successful
  dispatch attempt (mock/spy the broker instance construction or the
  `evaluate` method).

### 49. No stale decision reuse
- attempt 1 → `ALLOW` → dispatch; simulate a state change (e.g. active
  task changes) → attempt 2 must independently re-evaluate (assert
  `evaluate` called again with a request reflecting the new state, not a
  cached decision reused).

Per the phase prompt's own instruction (Section 40 of the prompt,
"Do not implement tests in 148D unless lifecycle convention requires
planning artifacts only") — **this section is planning only.** No test
file is created by 148D; `tests/test_permission_broker_push_production_consumption.py`
does not exist yet and is 148E's deliverable.

---

## 50. Direct Dispatch Bypass Search (148D re-confirmation)

Searched `src/pcae/commands/push.py` for every invocation capable of
performing `git push`:

```
grep -n "git.*push\|subprocess.run" src/pcae/commands/push.py
```

Result: exactly the two dispatch lines already inventoried (`push.py:454`,
`push.py:605` — for `subprocess.run` calls containing `"push"`), plus
non-dispatch `subprocess.run` calls for `git diff --cached`, `git
rev-parse`, `git diff --name-only`, `git log --oneline`, `git
merge-base`, `git diff-tree`, `git rev-list` — none of which invoke `git
push`. No shell wrapper, alias, or indirect helper exists anywhere in the
module that constructs and executes a `git push` command by any other
means (e.g. via `os.system`, `Popen`, string-formatted shell commands, or
a generically-named "run git command" helper that could be called with
`push` as an argument — no such generic helper exists in this file). This
re-confirms PBPC-REQ-013's exhaustiveness claim independently for 148D
rather than merely citing it.

---

## 51. Dependency Injection / Testability

The adapter constructs `PermissionBroker()` internally by default
(Section 16). For testability, 148E may add a keyword-only, defaulted
parameter (e.g. `broker: PermissionBroker | None = None`) to the adapter
function itself — **not** to `run_push`/`_run_push_staged_file_aware`'s
public CLI-facing signature, and not exposed through any `argparse`
flag. This lets tests substitute a broker with a monkeypatched/mocked
`evaluate()` without touching production callers, which always invoke the
adapter with its default (`broker=None` → construct the canonical
`PermissionBroker()`). This mirrors the existing pattern already used
elsewhere in the codebase for internal testability seams, without
creating a caller-reachable weaker-configuration path (Section 17).

---

## 52. Default Broker Integrity

Production code paths (`run_push`, `_run_push_staged_file_aware`) always
call the adapter with its default broker construction — never pass a
custom `PermissionBroker(custom_rules)` derived from CLI/user data. If a
test-only injection seam exists (Section 51), it is reachable only from
test code that directly imports and calls the adapter function with an
explicit `broker=` argument — never from any code path reachable via the
`pcae` CLI's `argparse` surface.

---

## 53. API Change Assessment

| Change | Classification |
|---|---|
| New private helper `_evaluate_push_permission(...)` in `push.py` | INTERNAL_ONLY |
| New guard call before each dispatch site | INTERNAL_ONLY (no new CLI flags, no new public function signatures) |
| `pcae push` / `pcae push --staged-file-aware` CLI syntax | UNCHANGED |
| `pcae push --json` output schema | ADDITIVE at most (new diagnostic fields on `DENY`/`HUMAN_REVIEW`/broker-failure outcomes; existing fields/keys unchanged) — BACKWARD_COMPATIBLE |
| New `INT-005` registry entry (optional, Section 29) | ADDITIVE |
| Any change to `PermissionBrokerRequest`/`PermissionBrokerDecision`/`PolicyRule`/`PolicyRegistry`/`PermissionBroker` shapes | **MUST_NOT_CHANGE** — none planned |

No BREAKING change is planned anywhere in this design. `pcae push`'s CLI
syntax remains unchanged, as the phase prompt requires.

---

## 54. File Change Budget

| File | Classification |
|---|---|
| `src/pcae/commands/push.py` | MUST_CHANGE (new adapter function + two guard insertions) |
| `src/pcae/core/permission_broker_foundation.py` | MUST_NOT_CHANGE (reused unmodified) |
| `src/pcae/core/permission_broker.py` (legacy, `HARD_BLOCK_REGISTRY`) | MUST_NOT_CHANGE |
| `src/pcae/core/command_path_observation.py` | MAY_CHANGE (only if the optional `INT-005` bookkeeping entry from Section 29 is added; not required for conformance) |
| Any other `src/pcae/**` module | MUST_NOT_CHANGE |
| `tests/test_permission_broker_push_production_consumption.py` (new) | MUST_CHANGE (created) |
| `tests/test_push.py`, `tests/test_staged_file_aware_push.py` | MAY_CHANGE (Section 34) |
| `docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`, `.../PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md` | MUST_NOT_CHANGE |

**Target production file count: one (`src/pcae/commands/push.py`), plus
at most one optional bookkeeping touch
(`command_path_observation.py`).** This is narrower than the phase
prompt's own "at most one existing core/helper file if architecture
requires it" allowance — no core/helper file is required at all under
this design (Section 15).

---

## 55. Production File Budget Warning Assessment

No architecture smell found: the design does not require touching
numerous unrelated modules. If a future 148E implementation discovers it
needs to change more than the one file identified above (plus the
optional bookkeeping touch), that is itself a signal the design has
drifted from this plan and should be re-examined against Section 15's
placement rationale before proceeding, not silently expanded.

---

## 56. Safe Intermediate Commit Strategy

If 148E lands in multiple commits, no intermediate commit may leave one
dispatch path broker-gated while the other still bypasses. Concretely:

- **Unsafe intermediate state (prohibited):** a commit that adds the
  guard to Path A only, or Path B only, and is independently mergeable/
  pushable/usable in that state.
- **Safe strategy:** land the shared adapter function first (inert — not
  yet called from either dispatch path; a commit adding
  `_evaluate_push_permission` alone, with no call sites wired, changes no
  behavior and is safe standalone), then wire both call sites
  **together in the same commit** (or, if split further, wire Path A and
  Path B in immediate sequential commits where the *first* of the two
  wiring commits is never pushed/released standalone — i.e., the actual
  governed `pcae push`/`pcae commit` sequence for 148E should treat
  "helper landed, zero call sites wired" and "helper landed, both call
  sites wired" as the only two acceptable steady states reachable via a
  finished task-contract cycle; "helper landed, one call site wired" must
  never be the state left at task/phase completion).
- Test file landing may occur in the same commit as the wiring, or in a
  clearly-sequenced follow-up within the same governed task — never
  merged as "tests deferred to a later phase."

---

## 57. Atomic Wiring Preference

Preferred: activate both dispatch paths' broker consumption atomically,
in the same commit that wires the guard into `push.py`. This is entirely
practical here (both insertions are a few lines each, in the same file,
Sections 22-23) — no phased/partial wiring is needed, so Section 56's
"unreachable intermediate state" fallback should not be necessary in
practice for this specific, narrow change.

---

## 58. Rollback Plan

Rollback of the 148E implementation restores the exact pre-148D `push.py`
(revert the commit(s) that added `_evaluate_push_permission` and its two
call sites). No schema migration exists to reverse (Section 28 — no
durable artifact was ever created). No durable-artifact cleanup is
required. Test file
`tests/test_permission_broker_push_production_consumption.py` is deleted
or reverted alongside. `PermissionBroker`/`PolicyRegistry`/`push.py`'s
other existing logic requires no separate rollback step, since none of it
is touched.

---

## 59. Security Invariants (frozen for 148E)

- Both push dispatch paths broker-gated.
- No non-`ALLOW` dispatch.
- Broker failure fails closed.
- No caller-selected policy set.
- Canonical, fixed `execution_class`.
- `approval_present` remains truthful (`False`, never fabricated).
- `simulation_only` remains contract-correct (`True`, never flipped).
- `POL-004` not weakened.
- `POL-005` not weakened.
- Mechanical checks remain enforced, unchanged, in addition to the broker
  gate.
- No dual permission authority (broker owns the one new permission
  judgment it is given; existing mechanical/structural checks retain
  their existing, distinct ownership — Section 11).
- No stale decision reuse.
- No new runtime capability.

---

## 60. Implementation Acceptance Criteria (for 148E)

148E may be considered complete only if:

1. both actual `git push` paths consume PBPC;
2. canonical request shape exactly matches PBPC v1.2 (Section 7);
3. PBPA applicability used unchanged;
4. canonical Foundation policy registry used (Section 16);
5. permission-bearing judgment centralized (Section 11/13);
6. mechanical checks preserved (Section 32);
7. `ALLOW` is required before dispatch (Section 18);
8. `DENY` blocks (Section 18);
9. `HUMAN_REVIEW` blocks (Section 18);
10. broker failure blocks (Section 19);
11. ordinary path cannot bypass (Section 22/24);
12. staged-file-aware path cannot bypass (Section 23/24);
13. no caller-selected policy set exists (Section 17);
14. no approval fabricated (Section 9);
15. `simulation_only` uses the contract-correct value (Section 10);
16. `POL-004` behavior unchanged (Section 2/9);
17. `POL-005` behavior unchanged (Section 10);
18. no `POL-013+` added (Section 33);
19. no IWC permission dependency (Section 30);
20. no AESIC permission dependency (Section 30);
21. no Runtime Enforcement semantic change (Section 30);
22. no durable broker artifact added (Section 28);
23. runtime remains Observed / observe / unavailable (Section 31);
24. focused push/PB tests pass (Section 34-49);
25. Fast Green passes;
26. independent implementation verification is performed afterward (148F,
    Section 61).

---

## 61. Independent Verification Plan (148F, mandatory)

A dedicated, independent post-implementation verification phase must
attack, at minimum:

- both dispatch paths (re-derive independently, not cite 148E's own
  claims);
- direct bypass search (re-run Section 50's search against the
  post-148E tree);
- request-shape truthfulness (re-inspect the constructed
  `PermissionBrokerRequest` directly, not trust 148E's test assertions
  alone);
- `ALLOW`/`DENY`/`HUMAN_REVIEW` consumption correctness;
- broker exceptions (independently inject failures, confirm zero
  dispatch);
- `POL-004` (independently re-confirm non-applicability, not weakened);
- `POL-005` (independently re-confirm `simulation_only=True` is what
  is actually constructed, not merely what tests assert);
- mechanical checks (confirm unchanged);
- stale decision reuse (confirm none introduced);
- exactly-once dispatch (independently spy on `subprocess.run` and
  `PermissionBroker.evaluate`);
- no new caller policy-selection mechanism;
- no policy meaning drift (`POL-001..012` semantics identical to
  pre-148E);
- no runtime capability change (`pcae runtime inspect` unchanged).

148F must not rely only on 148E's own implementation tests — it must
independently re-derive findings from source, mirroring how 148C.7/148C.8/
148C.10 each independently re-derived rather than cited prior phases'
work.

---

## 62. Prompt Generation Boundary (preserved, unchanged)

Prompt Generation / Prompt Creation (Phase 45F) remains
**DEFERRED STRATEGIC OBSERVATION** for post-Chapter-148 reassessment.
Nothing in this plan relates Permission Broker production consumption to
Prompt Generation beyond the general architectural principle, unchanged:

> generated ≠ approved ≠ dispatched ≠ executed

No Prompt Generation, Prompt Dispatch, or agent-invocation capability is
designed, planned, or implemented by this phase.

---

## 63. Planning Findings

**BLOCKING:** none.

**NON-BLOCKING:** none.

**OBSERVATION:**

- **O-148D-1.** `pcae phase-report reconcile --phase-id 148C.10` (initial
  inspection, Section 1) reports `status: conflict` against 148C.10's
  already-promoted, already-pushed canonical report artifacts. This is a
  pre-existing state of a *finalized prior phase's* stored reconciliation
  snapshot — independently corroborated as immaterial by `pcae
  phase-report show --latest`, which reports 148C.10 as `completed`,
  `complete ✅`, `Pushed: pushed`, `origin/main..HEAD: 0`. Reconciliation
  ran strictly read-only, as required, and mutated nothing. Not
  actionable within 148D's planning-only scope (148D holds no allowed
  file for touching 148C.10's finalized artifacts); noted for awareness
  only, does not affect this plan's conclusions or 148E's readiness.

**DEFERRED:** Prompt Generation (Phase 45F), unchanged (Section 62).

---

## 64. Recommended Next Phase

**148E — Permission Broker Production Consumption Implementation**, bounded
strictly to the file budget in Section 54 (target: `src/pcae/commands/push.py`
plus, optionally, `src/pcae/core/command_path_observation.py`), implementing
exactly the design in Sections 5-33 of this plan against PBPC-001 v1.2 and
PBPA-001 v1.0, unamended.

**148F — Permission Broker Production Consumption Independent Implementation
Verification** (mandatory, Section 61) must follow 148E before Chapter 148
can move toward closure.
