# Phase 148C.1 — Permission Broker Production Consumption Contract Clarification and Repair

**Phase ID:** 148C.1
**Mode:** Contract clarification and repair only (no implementation, no
`src/pcae/**` modification, no runtime change, no new `POL-013+` policy,
no `pcae push` modification, no Permission Broker Foundation behavior
change)
**Baseline:** PBPC-001 v1.0 (`docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`)
**Predecessor:** Phase 148C (commit `d45d9fd8`) — verdict **NOT VERIFIED —
BLOCKING CONTRACT FINDING**, Finding B-1
**Date:** 2026-08-01

---

## 0. Authorization and Boundary

This phase is authorized to independently re-derive Finding B-1 from
primary contracts and source — not to trust Phase 148C's own prose as an
oracle — and to repair PBPC-001 narrowly if a legitimate repair exists. It
must not modify `src/pcae/**`, change Permission Broker Foundation
behavior, change `POL-001..012` (absent a genuinely unavoidable
amendment, which this phase does not make), introduce `POL-013+`,
modify `pcae push`, add CLI behavior, add audit persistence, create a new
approval system, reinterpret Interactive Workflow Confirmation or
Authority Evaluation/AESIC as approval, change `HUMAN_REVIEW` semantics,
change runtime capability, or begin 148D/148C.2 planning or
implementation.

### Bootstrap

```
git status --short / --branch --short   -> clean, main, tracking origin/main
git log --oneline -25                    -> HEAD at b29c0021 (148C idle placeholder removal)
git rev-list --count origin/main..HEAD   -> 0
pcae health                              -> healthy
pcae check                               -> passed
pcae status coherence                    -> coherent
pcae doctor task-memory                  -> clean
pcae push check                          -> clean, nothing_to_push
pcae runtime inspect                     -> Observed / observe / unavailable
pcae notify status                       -> Telegram configured, enabled, ready
pcae phase-report show --latest          -> 148C, recommended next 148C.1
pcae phase-report reconcile --phase-id 148C
    -> status: reconciled; promoted generations: 2; marker: already_dispatched;
       checkpoint: completed; receipt: finalized; mutation: none (inspection only)
```

Confirmed: repository clean, 0 unpushed commits, 148C completed with
Finding B-1 open, 148D not authorized, runtime unchanged (`Observed` /
`observe` / `unavailable`).

### Independent source inventory (read in full or targeted, as noted)

- `docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md` (1021 lines, full — PBPC-001 v1.0, the object of repair)
- `docs/verification/PHASE_148C_PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT_INDEPENDENT_VERIFICATION.md` (full — read for context, not trusted as an oracle)
- `src/pcae/core/permission_broker_foundation.py` (full — `PermissionBrokerRequest`, `MissingHumanApprovalRule`/POL-004, `PolicyRegistry.evaluate_all`, `PermissionBroker.evaluate`, `_compose`, `DEFAULT_POLICY_RULES`)
- `src/pcae/core/permission_broker.py` (targeted — `HARD_BLOCK_REGISTRY`, all 12 entries, read directly)
- `docs/V0_2_AUTONOMY_CONTRACT.md` (targeted — INV-003, INV-008, COMP-002, COMP-003, canonical execution lifecycle)
- `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` (targeted — NG-008 full entry, document scope statement)
- `docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md` (full — §5 Approval Model, §7 Governance Mapping, §8 Future Integration; **the decisive primary source for this phase's verdict**)
- `docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md` (targeted — Git lifecycle command-category table, "POL-004 approval where applicable")
- `docs/PHASE_108_PERMISSION_BROKER_FOUNDATION.md` (full — request model, fail-closed priority order, `approval_present` caller-supplied statement, COMP-mapping table)
- `docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md` (targeted — IWC-REQ-029 verbatim)
- `src/pcae/aesic/__init__.py`, `src/pcae/authority_evaluation/__init__.py` (module docstrings)
- `src/pcae/commands/push.py` (targeted — existing `observe()` touchpoint, lines 295-315)
- Live execution against the actual, unmodified `PermissionBroker`/`PolicyRegistry`/`build_permission_broker_request` (no reimplementation) to independently reproduce B-1 and test the repair's empirical effect

---

## 1. Executive Summary

**Verdict: B-1 REMAINS OPEN — BLOCKING CONTRACT CONFLICT.**

This phase independently re-derived Finding B-1 (confirmed exact, §2),
independently re-derived the normative meaning of `approval_present`
(§3) and `POL-004` (§4), and evaluated all four repair categories the
governing brief defines (§5). It closes two of Phase 148C's own
Non-Blocking findings honestly (the Section 8 traceability gap, §9 below;
the Section 8 "deferred design, not MVP-active" mischaracterization of
POL-004, §8 below) and versions PBPC-001 to **v1.1** to record these
corrections. It does **not** close Finding B-1, because every repair path
available within this phase's authorization either requires fabricating
an approval that no authoritative source establishes (Category A,
foreclosed — §6), or requires a policy-applicability decision that no
*existing* Permission Broker Foundation mechanism supports and that this
phase is not authorized to invent unilaterally (Category B, foreclosed as
a within-phase repair — §7). The honest classification is **Category C —
Foundation contract gap**: `POL-004` (`MissingHumanApprovalRule`), via
its own upstream lineage (`NG-008` → `INV-003` → `COMP-003`), was
designed exclusively for the not-yet-implemented, generic "mediated
execution action" lifecycle (`PLANNED -> READY -> AWAITING_HUMAN_APPROVAL
-> AUTHORIZED -> EXECUTING`, `docs/V0_2_AUTONOMY_CONTRACT.md`) — a
lifecycle `pcae push` structurally never enters, because `pcae push` is
governed by **Git approval** (branch protection / PR review / the
Owner's transitional direct-push exemption), which
`docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md` §5 (Phase
107E, frozen, predating the Permission Broker Foundation itself) freezes
as explicitly, permanently **non-interchangeable** with "execution
approval." Yet the Permission Broker Foundation's rule-evaluation model
(`PolicyRegistry.evaluate_all`, `permission_broker_foundation.py:649-659`)
has no structural way to express "this policy does not apply to this
request's operation class" — every registered rule evaluates
unconditionally on every request, confirmed independently live (§2). This
is the exact upstream gap Category C describes, and PBPC-001 alone —
bound to consume the Foundation's existing, unmodified vocabulary
(PBPC-REQ-032) without creating a second decision taxonomy — cannot close
it without either fabricating an approval PBPC-REQ-077 already forbids,
or exceeding this phase's own boundary against changing Foundation
behavior or beginning implementation.

Because B-1 remains open, 148D remains not recommended and **148C.2
(Repair Independent Verification) is also not recommended**, since no
repair exists yet to verify. §14 recommends a narrowly-scoped design
phase instead.

---

## 2. Independent Reproduction of Finding B-1

Constructed exactly the PBPC-REQ-046-conformant request and evaluated it
live against the actual, unmodified `PermissionBroker`:

```python
req = build_permission_broker_request(
    action_type=ACTION_PUSH, execution_class=EXECUTION_CLASS_MUTATION,
    requested_component="COMP-001", requested_capability="pcae_push",
    task_id="some-active-task", evidence_available=True,
    approval_present=False, simulation_only=True,
)
PermissionBroker().evaluate(req)
# -> decision=HUMAN_REVIEW, decision_reason="missing_human_approval",
#    causing_policy_ids=('POL-004',), requires_human=True
```

Independently confirmed exact — identical to Phase 148C's own table (§4,
row 1). With `approval_present=True` (not authorized by v1.0), the same
request returns `ALLOW`, `decision_reason="policy_would_allow_if_execution_existed"`
— confirming the *entire* gap between "conformant push request" and "push
succeeds via the broker" is exactly this one field. Per PBPC-001 §15
(PBPC-REQ-052), `HUMAN_REVIEW` aborts — v1.0 has no interactive
resolution (PBPC-REQ-077, Section 3). B-1 is independently reproduced
exact, not merely trusted from 148C's prose.

Independently confirmed structural root, reading `PolicyRegistry.evaluate_all`
and `PermissionBroker.evaluate` directly (`permission_broker_foundation.py:649-659,
766-786`): every rule in the fixed `DEFAULT_POLICY_RULES` tuple runs on
every request, unconditionally, with no `action_type`/`execution_class`
gating anywhere in `evaluate_all`, `_compose`, or any individual rule
except by the rule's own internal field check. This is independently
confirmed to be the exact, sole mechanism by which `POL-004` fires — not
a bug in `_compose`'s precedence, not a malformed request, not a
fail-closed edge case, but the Foundation's ordinary, correct,
by-design behavior for the fields PBPC-001 fixes.

---

## 3. Re-Derived Semantics — `approval_present`

**`approval_present` means:** a boolean, caller-supplied assertion that
some component asserts an explicit, affirmative human approval action
has been recorded for the specific proposed execution action, sufficient
to resolve `POL-004`/`NG-008`'s remediation requirement ("obtain and
record an explicit human approval action before the action can move to
`AUTHORIZED`," `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md:183-184`).

Independently derived from primary source, not the field name alone:

- The dataclass itself (`permission_broker_foundation.py:161`) carries no
  semantics beyond `bool` — the *meaning* comes entirely from
  `MissingHumanApprovalRule`'s docstring and its upstream citations
  (`NG-008`, `INV-003`).
- `docs/PHASE_108_PERMISSION_BROKER_FOUNDATION.md:176-178` (frozen, Phase
  108A-C): *"Human Approval Gate (`COMP-003`): once implemented, will
  formally record the human action that resolves a `HUMAN_REVIEW`
  decision. **Today, `approval_present` is supplied directly on the
  request by the caller; there is no gate implementation to record
  it.**"* This is decisive: the Foundation's own frozen text
  affirmatively delegates the determination of what counts as a valid
  `approval_present=True` assertion to the **caller**, because `COMP-003`
  does not exist. It does not define a universal, caller-independent
  meaning.
- `docs/V0_2_AUTONOMY_CONTRACT.md:251-256` (`COMP-003`, frozen, Phase
  107B): *"Purpose: Require and record an explicit human approval before
  an action can move from `AWAITING_HUMAN_APPROVAL` to `AUTHORIZED`."*
  `AWAITING_HUMAN_APPROVAL` and `AUTHORIZED` are states in the canonical
  **execution lifecycle** (`PLANNED -> READY -> AWAITING_HUMAN_APPROVAL
  -> AUTHORIZED -> EXECUTING -> {COMPLETED|FAILED|ABORTED}`), not states
  any Git operation passes through.
- `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md:20-24` (frozen, Phase
  107C): *"`NG-` gates are scoped specifically to the execution readiness
  decision point — the moment just before a proposed action would move
  from `READY` to `AWAITING_HUMAN_APPROVAL` in the execution
  lifecycle."* This is an explicit, textual scope boundary on `NG-008`
  (and therefore on `POL-004`, which implements it) to the generic
  mediated-execution lifecycle specifically.
- `docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md` §5 (frozen,
  Phase 107E, **predates** the Permission Broker Foundation, Phase
  108A-C): freezes **Git Approval** ("approval that a proposed change to
  the repository's version-controlled content... is correct and should
  be merged... granted by a Human Reviewer (PR review) or, in the
  current transitional posture, the Owner via a governed push... does
  not authorize any runtime action, execution, shell command, backend
  invocation, or mutation outside version control") as categorically
  distinct from **Execution Approval** ("approval that a specific,
  proposed execution action... may proceed... granted (future) by the
  Human Approval Gate component, after a Permission Broker
  `allow`/`human_review` decision... **not implemented**... **These are
  never interchangeable.**").

**Conclusion:** `approval_present`, as `POL-004` uses it, means execution
approval per `COMP-003`/`NG-008`/`INV-003` — a concept the Autonomy
Contract itself, by explicit and controlling design, restricts to the
generic mediated-execution lifecycle and explicitly separates from Git
approval. It does not apply to `pcae push` unless `pcae push` is itself a
mediated execution action within that lifecycle — which §4 below shows it
is not.

- **Whether it is human approval:** yes, specifically — not evidence
  presence (that is `POL-003`), not lifecycle authorization in the phase
  sense (`PBPC-REQ-006`'s "Authorized"), not runtime capability.
- **Whether it applies to simulation-only requests:** the rule's own
  condition (`if request.approval_present: not_triggered`) has no
  dependency on `simulation_only` — it fires identically regardless.
  `simulation_only` and `approval_present` are independent axes in the
  request model; `POL-004` does not read `simulation_only`.
- **Whether it is required for all Permission Broker operations or only
  some profiles:** per `NG-008`'s own scope statement above, it is
  intended to apply only to operations that are mediated execution
  actions within the Autonomy Contract's lifecycle. The Foundation's
  *code*, however, applies it to every request regardless of profile
  (§2) — this divergence between intended scope and coded scope is
  exactly Finding B-1's root cause.

---

## 4. Re-Derived Semantics — `POL-004`

- **Exact trigger:** `not request.approval_present` (`permission_broker_foundation.py:428`).
- **Exact decision:** `HUMAN_REVIEW`, `decision_reason="missing_human_approval"`,
  `matched_no_go_ids=("NG-008",)`, `matched_invariants=("INV-003",)`,
  `matched_component_ids=("COMP-003",)`, `requires_human=True`.
- **Exact policy purpose (per its own docstring):** *"Routes to
  `HUMAN_REVIEW`, not a hard deny, per `NG-008`'s own remediation path —
  the human's approval is the resolution, not an override."*
- **Conditional on operation type?** No — the rule's own `evaluate()`
  method contains no `action_type`/`execution_class` check. It is
  structurally unconditional (§2).
- **Conditional on simulation mode?** No (§3).
- **A universal policy, or one expressing generic human-review
  requirements for mediated execution specifically?** By its own upstream
  citation chain (`NG-008` → `INV-003` → `COMP-003`), it expresses a
  requirement specific to the generic mediated-execution lifecycle
  (§3). It is coded as universal (evaluated on every request), but its
  *intended scope*, per the frozen documents that define what `NG-008`
  means, is narrower than its coded scope.
- **Intended to gate real mutation generically, or only execution-attempt
  flows specifically?** Only execution-attempt flows within the Autonomy
  Contract's own lifecycle — `docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md`
  §8 ("Permission Broker... Attaches after `AWAITING_HUMAN_APPROVAL` is
  reached in the execution lifecycle — never substitutes for, and is
  never substituted by, PR review") is explicit that Git mutations
  (commits, pushes) are governed by an entirely separate approval
  mechanism (Git approval), not by `POL-004`'s target concept.

**This does not mean `POL-004` should be weakened.** No evidence found
anywhere that `NG-008`'s underlying concern (an action must not proceed
without some legitimate, recorded human approval act) is wrong for its
actual intended domain (mediated execution actions once `COMP-002`/`COMP-004`/
`COMP-005`/`COMP-006` exist). The finding is narrower: `pcae push` is not
in that domain, and the Foundation's rule-evaluation code cannot express
that distinction today.

---

## 5. Repair Category Determination

Evaluated against all four categories the governing brief defines, in
the brief's own stated preference order (§12 of the brief: correct
interpretation → clarify applicability → correct request binding → only
if unavoidable, upstream amendment).

### Category A — PBPC request-shape bug (existing approval source)

**Foreclosed.** §6 below inventories every candidate approval source in
the repository. None legitimately establishes `POL-004`'s execution
approval for `pcae push`. The one candidate that superficially fits
(Git approval, already satisfied today for every real `pcae push` via
branch protection / the Owner's transitional exemption / `pcae push
check`) is explicitly and controllingly declared **non-interchangeable**
with execution approval by `docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md`
§5 — a frozen document that predates the Permission Broker Foundation and
exists specifically to prevent this exact conflation. Treating Git
approval as satisfying `POL-004` would fabricate an equivalence the
authoritative source explicitly forbids ("these are never
interchangeable"), which PBPC-REQ-077 and this phase's own Repair
Principle prohibit.

### Category B — POL-004 applicability bug (existing Foundation
mechanism excludes it)

**Foreclosed as a within-phase repair.** The brief requires this category
to be "already supported by existing Permission Broker semantics." Two
readings were tested:

1. **A per-request applicability mechanism** (the registry evaluates
   `POL-004` only for requests matching some execution-lifecycle
   profile). None exists — `evaluate_all` iterates the full fixed
   `DEFAULT_POLICY_RULES` tuple unconditionally for every request (§2,
   confirmed live). No `action_type`/`execution_class`-based rule
   filtering exists anywhere in the Foundation.
2. **A per-consumer registry-construction mechanism.** `PermissionBroker.__init__`
   and `PolicyRegistry.__init__` do accept an optional custom `rules`
   tuple (`permission_broker_foundation.py:640, 763`), and the module's
   own Phase 108B comment states: *"Future rule addition means
   constructing a new `PolicyRegistry` with an extended rule tuple — the
   broker itself never needs to change."* This is a genuine, existing,
   unmodified Foundation mechanism. It was considered as a candidate
   repair: a future `pcae push` Decision Consumption Point could
   construct `PermissionBroker(PolicyRegistry(rules=<POL-001..012 minus
   POL-004>))`.

   **This phase declines to adopt reading 2 as a 148C.1 repair**, for
   three independent reasons, each sufficient alone: (a) the module's own
   text anticipates this mechanism for *future rule addition*, not
   per-consumer *subtraction* for applicability-scoping purposes — using
   it this way is a novel application never contemplated by Phase 108B,
   not something "already supported" in the sense the brief requires;
   (b) constructing a push-specific rule subset is, in substance, the
   creation of a decision taxonomy specific to `pcae push`, which
   PBPC-REQ-032 explicitly forbids ("This contract SHALL NOT create...
   a second decision taxonomy specific to `pcae push`"); and (c) deciding
   *whether* per-consumer policy-set customization is the correct,
   general interpretation of "policy applicability" is a real
   architectural question this phase is not authorized to resolve
   unilaterally inside a narrow repair phase (the brief's own §17: "Do
   not create a new generic policy-selection architecture in
   148C.1"). Adopting it here — however narrowly framed — would produce
   exactly the outcome-forcing this phase's Repair Principle prohibits:
   choosing the interpretation that happens to make push succeed,
   through a mechanism whose applicability to this exact question was
   never settled by any prior authorized phase. It is recorded instead
   as an **Observation** (§10) for a future, explicitly authorized design
   phase to evaluate on its own merits.

### Category C — Foundation contract gap

**This is the correct classification.** The Foundation's rule-evaluation
model has no structural way to express "this policy does not apply to
this request's operation profile" (confirmed, §2/§5-B). The upstream
Autonomy Contract/No-Go Gates design (Phase 107B/107C) clearly intended
`NG-008` to be scoped to the execution-readiness lifecycle only (§3/§4),
and the PR-Compatible Workflow design (Phase 107E) clearly intended Git
operations to be governed by a wholly separate approval concept — but
none of these upstream, frozen intentions were ever encoded into the
Permission Broker Foundation's actual rule-evaluation *mechanism* when it
was built (Phase 108A-C). PBPC-001, consuming the Foundation exactly as
frozen (PBPC-REQ-011/032), inherits this gap unmodified. **PBPC-001 alone
cannot repair this** — closing it requires either (i) a Permission Broker
Foundation amendment introducing a genuine, general policy-applicability
mechanism (a design decision affecting all 12 `POL-` rules and every
future consumer, not just `pcae push`), or (ii) accepting that `pcae
push`'s Permission Broker integration is deferred until `COMP-003`
(Human Approval Gate) is genuinely implemented and a real execution
approval exists. Both are out of scope for a "clarification and repair"
phase authorized only to repair PBPC-001's own text.

### Category D — Push genuinely requires human approval

**Partially applicable as an honest characterization, not as the primary
finding.** Under a maximally literal reading of the coded Foundation
(ignore upstream intent, take `POL-004`'s unconditional firing at face
value), one could say push "genuinely requires" execution approval
because the code says so. This phase does not adopt that framing as
primary, because it would contradict the strong, controlling, textual
evidence (§3/§4) that `NG-008`/`POL-004` was never *intended* to govern
Git operations at all — the correct diagnosis is not "push needs an
approval mechanism it lacks," but "PBPC-001's Section 26/30 compatibility
claims about push were premised on a coverage question (Section 8) that
turned out to have a Blocking answer, and no legitimate way exists today
to supply what the coded rule demands without fabricating an equivalence
the repository's own frozen sources forbid."

---

## 6. Approval Source Inventory

| Candidate | Classification | Basis |
|---|---|---|
| Interactive Workflow Confirmation (IWC) / Decision Session | NOT POL-004 APPROVAL | `IWC-REQ-029` (verbatim, unchanged, §12 below): no Decision Session state may trigger any runtime capability change. Confirmation ≠ approval by the Autonomy Contract's own terminology (PBPC-REQ-006/007). |
| `IWC-REQ-029` neighbors / Confirmation generally | NOT POL-004 APPROVAL | Same as above; IWC governs Publication readiness, not Permission Broker decisions. |
| Human Governance Record / CHGR | UNRELATED | Governs publication-authority disclosure for a separate domain (Chapter 147/CHGR-001); no code path connects it to `push.py` or `permission_broker_foundation.py` (confirmed no references in either file). |
| Publication authorization (`PublicationApplicationService`, 145F) | UNRELATED | Governs `governance-record publish`, a distinct CLI noun; no relationship to `pcae push`'s git-mutation capability. |
| Task authorization (active task contract) | NOT POL-004 APPROVAL (already `POL-001`'s domain) | `task_id` presence is already the exact field `POL-001` (`MissingActiveTaskRule`) evaluates — a different rule with a different, already-correctly-bound semantics (PBPC-001 Section 13). Conflating it with `POL-004` would double-count one signal for two unrelated policy questions. |
| Phase authorization (phase lifecycle) | NOT POL-004 APPROVAL | Phase completion/authorization governs governance bookkeeping (`pcae phase complete`), not a specific mediated execution action; `docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md` §7 explicitly classifies phase completion as "governance-level phase bookkeeping, not a Git or execution approval." |
| **Git approval** (branch protection / PR review / Owner's transitional direct-push exemption) | **AMBIGUOUS, RESOLVED NOT POL-004 APPROVAL** | This is the only candidate that governs the *exact* operation (`git push`) `pcae push` performs, and it is already, today, a real, recorded, verifiable approval mechanism (GitHub branch protection enforcement; `pcae push check`'s own existing readiness gate). It is explicitly, controllingly declared non-interchangeable with execution approval by `docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md` §5 (§3/§5-A above). Resolved: real and relevant to push, but not `POL-004`'s approval. |
| Command readiness (`assess_push_readiness`, `readiness.ready`) | NOT POL-004 APPROVAL | Existing push-owned readiness logic (health/check/doctor/lifecycle/phase-report trust); no field represents a human approval act distinct from Git approval already covered above. |
| Existing `observe()` touchpoint for `push check` (`approval_present=True`, discarded) | NOT POL-004 APPROVAL (not authoritative) | Read-only, `action_type="read"`, decision explicitly discarded per its own code comment and `PBPC-REQ-015` ("SHALL NOT be treated as prior art for `pcae push`'s own consumption"). Setting `approval_present=True` here has zero real effect and establishes no approval fact — it is circumstantial evidence someone previously encountered this trigger, not an authoritative source. |
| Authority Evaluation / AESIC | NOT POL-004 APPROVAL | Both packages' own frozen docstrings: disclosure/citation-only, "never grants, blocks, or conditions Confirmation, Readiness, Authorization, or Publication." §13 below confirms independently. |
| Any explicit human approval artifact (e.g. a recorded approve/deny decision) | NOT PRESENT | No such artifact exists in this repository for `pcae push` specifically; `COMP-003` (the only component designed to produce one) is not implemented (`docs/V0_2_AUTONOMY_CONTRACT.md:256`, "Not implemented. Enforcement of this gate is Phase 111A"). |
| Runtime approval plugin or record | NOT PRESENT | `pcae runtime inspect` confirms zero registered plugins, zero capabilities, `Registry status: empty` (bootstrap, §0). |

**Result: no existing, authoritative source legitimately satisfies
`POL-004`'s execution-approval semantics for `pcae push`.** Category A is
foreclosed on the evidence, not by assumption.

---

## 7. Category B Detail — Why "Already Supported" Fails

Restated from §5 for traceability: the brief's Category B instructs
"show it is already supported by existing Permission Broker semantics."
Tested exhaustively:

- Per-request rule filtering by `action_type`/`execution_class`: does not
  exist (§2, §5).
- Per-consumer registry customization (`PolicyRegistry(rules=...)`):
  exists mechanically, but was never intended for applicability-scoping
  and adopting it for that purpose here would itself be an unauthorized
  architectural decision (§5-B), not a use of "already supported"
  semantics in the sense the brief requires (an *applicability rule*,
  not merely an available Python constructor argument).
- A `PolicyResult.triggered=False` "not applicable" outcome distinct from
  "not triggered because the condition didn't fire": the `PolicyResult`
  dataclass (`permission_broker_foundation.py:322-344`) has exactly one
  boolean, `triggered`; there is no third state distinguishing
  "evaluated, condition false" from "not evaluated because inapplicable."
  §17 of the brief's own text anticipated this exact possibility:
  *"If current Foundation cannot express non-applicability, that may
  reveal an upstream contract gap."* Confirmed: it cannot, and it does.

No existing mechanism closes B-1 without either fabricating approval
(Category A) or making a new architectural decision this phase is not
authorized to make (Category B in substance). §5's Category C
classification stands.

---

## 8. Correction to Section 8's POL-004 Disposition

PBPC-001 v1.0 Section 8's table (row "Missing human approval") disposed
of `POL-004` as: *"Deferred design, not MVP-active. Section 11 addresses
the state this maps to; no interactive resolution mechanism is authorized
in v1.0."* Phase 148C already found this factually incorrect (`POL-004`
is live and universally triggering, not inert) but did not itself amend
the contract text. This phase corrects it in PBPC-001 v1.1 (§13) to state
plainly: `POL-004` is implemented and evaluates unconditionally on every
`pcae push` request; because `approval_present` is fixed `False` by
PBPC-REQ-046 with no authorized mechanism to set it `True`, `POL-004`
determines every conformant request's outcome (`HUMAN_REVIEW`) — this is
not deferred, and it is not compatible with push ever completing under
this contract as currently scoped.

---

## 9. Section 8 Coverage-Table Traceability Gap — Closed

Independently re-enumerated all 12 `HARD_BLOCK_REGISTRY` entries against
PBPC-001 §8's table (source read directly, §0 above), reproducing Phase
148C's own §9 finding exactly:

| # | `HARD_BLOCK_REGISTRY` entry | Named in PBPC-001 §8? | Disposition (this phase) |
|---|---|---|---|
| 1 | `blocked_by_raw_git_commit` | No | Out of scope, not push-relevant (commit, not push) |
| 2 | `blocked_by_raw_git_push` | Yes | — |
| 3 | `blocked_by_force_push` | Yes | — |
| 4 | `blocked_by_no_verify` | Yes | — |
| 5 | `blocked_by_destructive_filesystem` | No | Out of scope, not push-relevant (filesystem-scoped) |
| 6 | `blocked_by_unknown_command_class` | No | Out of scope, not push-relevant (generic command classification, shell-gate layer) |
| 7 | `blocked_by_out_of_scope` | No | Out of scope, not push-relevant (path-scoped) |
| 8 | `blocked_by_policy_forbidden_file` | No | Out of scope, not push-relevant (path-scoped) |
| 9 | `blocked_by_forbidden_path` | No | Out of scope, not push-relevant (path-scoped) |
| 10 | `blocked_by_missing_task` | Yes | — |
| 11 | `blocked_by_enforcement_not_ready` | No | Out of scope, not push-relevant (generic enforcement-readiness gate, shell-gate layer) |
| 12 | `blocked_by_enforcement_not_authorized` | No | Out of scope, not push-relevant (generic enforcement-authorization gate, shell-gate layer) |

All 12 entries operate at the shell-gate/hook layer (outside any
command's own control flow), a different enforcement layer from both
`push.py`'s readiness logic and the Foundation's `POL-` rules — consistent
with Phase 148B's own Section 6 observation and Phase 148C's independent
confirmation. This phase's PBPC-001 v1.1 (§13) adds an explicit
"out of scope, not push-relevant" disposition for entries 1, 5-9, 11-12,
closing the traceability gap Phase 148C identified as Non-Blocking.

---

## 10. Findings

| ID | Finding | Classification |
|---|---|---|
| B-1 | Independently re-derived and reproduced exact (§2). Repair evaluated against all four categories (§5); Category A foreclosed by the frozen Git-approval/execution-approval separation (§3, §6); Category B foreclosed because no existing Foundation applicability mechanism supports it without an unauthorized architectural decision (§5-B, §7); correct classification is Category C — a Foundation contract gap this phase cannot close without exceeding its own authorization. | **BLOCKING — REMAINS OPEN** |
| §8 | PBPC-001 v1.0 Section 8's "Deferred design, not MVP-active" characterization of `POL-004` is corrected. | Non-Blocking, corrected in v1.1 |
| §9 | Section 8's coverage-table traceability gap (8 of 12 `HARD_BLOCK_REGISTRY` entries not explicitly disposed of) is closed. | Non-Blocking, corrected in v1.1 |
| §5-B | A technically-available Foundation mechanism (`PolicyRegistry(rules=...)` per-consumer customization) could, in principle, be used by a future, separately authorized phase to implement a genuine policy-applicability model — but this phase declines to adopt it unilaterally. | Observation, deferred |
| — | `simulation_only=True` diagnostic-honesty risk (Phase 148C §8.4) | Independently reconfirmed Non-Blocking; unaffected by this phase (§11) |
| — | IWC-REQ-029, AESIC independence, HUMAN_REVIEW non-ALLOW semantics | Independently reconfirmed correct, unchanged (§12, §13) |

No new Blocking finding beyond B-1 itself was identified. B-1's
classification is refined (root cause now precisely located as a
Foundation applicability gap, not merely "no approval source exists"),
but its practical status — every conformant `pcae push` request under
PBPC-001 returns `HUMAN_REVIEW`, which the contract requires to abort —
is unchanged from Phase 148C.

---

## 11. `simulation_only` Recheck

Independently re-read the Foundation's own docstring
(`permission_broker_foundation.py:145-148`): `simulation_only` describes
whether the broker's own execution boundary (`COMP-002`) is being asked
to carry out the action — structurally never, since `push.py`'s
subprocess call is external to and predates the Foundation. This reading
is unaffected by anything found in this phase. `simulation_only` and
`approval_present` are independent fields (§3) — this phase's findings
about `POL-004`'s applicability do not change `POL-005`'s
(`ExecutionDisabledRule`) analysis or Phase 148C's Non-Blocking
diagnostic-honesty observation about it. No second Blocking defect is
introduced or discovered here.

---

## 12. Interactive Workflow Confirmation Protection

`IWC-REQ-029` re-read verbatim (`docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md:1063-1065`):
*"No Decision Session state, before or after `Confirmed`, SHALL be
visible to, consumable by, or capable of triggering any runtime
capability change."* Unchanged by this phase. No code path in
`push.py` or `permission_broker_foundation.py` references Decision
Session/Confirmation state (independently confirmed, `grep` clean).
Confirmation is not repurposed as `POL-004` approval anywhere in this
document's analysis (§6 explicitly classifies it NOT POL-004 APPROVAL).
No amendment to `IWC-REQ-029` is made or required.

---

## 13. Authority Evaluation / AESIC Protection

Both `src/pcae/authority_evaluation/__init__.py` and `src/pcae/aesic/__init__.py`
independently re-read: both remain disclosure/citation-only by their own
frozen module docstrings ("never grants, blocks, or conditions
Confirmation, Readiness, Authorization, or Publication"). `grep` of
`push.py` and `permission_broker_foundation.py` for `authority_evaluation`/
`aesic` returns nothing (confirmed live). AESIC is not repurposed as
`POL-004` approval anywhere in this document's analysis (§6). Chapter 147
is not reopened.

---

## 14. `HUMAN_REVIEW` Semantics

Unchanged. `HUMAN_REVIEW` remains a non-`ALLOW` decision value; PBPC-001
§15 (PBPC-REQ-052) already requires it to abort in v1.0, and this phase
neither invents an implicit-approval path, an auto-resolution mechanism,
a CLI yes/no prompt, nor a fallback `ALLOW`. Because B-1 remains open, a
conformant `pcae push` request continues to reach `HUMAN_REVIEW` and
continues to abort — this phase changes nothing about that outcome; it
only corrects the contract's own description of why.

---

## 15. Compatibility Matrix (Re-Run)

| Predecessor | Classification |
|---|---|
| Permission Broker Foundation (`POL-001..012`) | UNCHANGED. No rule modified; no rule added. |
| `docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md` (Phase 109A) | CLARIFIED. Its own "`POL-004` approval where applicable" language (line 163) is independently confirmed to have anticipated exactly this conditionality; this phase makes that conditionality explicit rather than assumed. |
| `docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md` (Phase 107E) | CONSUMED, UNCHANGED. This phase's central finding rests on this document's own frozen Git-approval/execution-approval separation; no amendment to it is made or needed. |
| `docs/V0_2_AUTONOMY_CONTRACT.md` / `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` (Phase 107B/107C) | UNCHANGED. `NG-008`/`INV-003`/`COMP-003` are read, not amended. |
| `HARD_BLOCK_REGISTRY` / legacy `permission_broker.py` | UNCHANGED. Not consolidated, not modified. |
| `pcae push` (`src/pcae/commands/push.py`) | UNCHANGED. No modification; no `src/pcae/**` diff (§16). |
| Task/phase lifecycle | UNCHANGED. |
| Interactive Workflow Confirmation / `IWC-REQ-029` | UNCHANGED, not amended (§12). |
| Authority Evaluation / AESIC-001 | UNCHANGED, not reopened (§13). |
| Runtime Enforcement Decision Engine/Coordinator | UNCHANGED, orthogonal (unaffected by this phase's findings, which concern the Permission Broker Foundation's policy layer, not the Runtime Enforcement layer). |
| PBPC-001 itself | **UPSTREAM AMENDMENT REQUIRED (deferred, not made by this phase)** to actually resolve B-1; PBPC-001 v1.1 (this phase) corrects its own descriptive/traceability errors but cannot, alone, produce a satisfiable contract. |

---

## 16. Production Source Boundary

```
git diff --name-only 69f9c12e..HEAD -- src/pcae/
```
(pre-148B baseline through this phase's own work) is confirmed empty —
this phase's own changes are limited to this document, PBPC-001's
version bump, `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/**`, and
finalization artifacts. No `src/pcae/**` file was modified by this
phase.

---

## 17. B-1 Closure Criteria — Evaluated

Per the governing brief's §21, all ten must hold for closure:

1. `approval_present` semantics explicitly re-derived — **done (§3)**.
2. `POL-004` applicability explicit — **done (§4)**.
3. No approval fabricated — **held (§5-A, §6)**.
4. IWC Confirmation not repurposed — **held (§12)**.
5. AESIC not repurposed — **held (§13)**.
6. `HUMAN_REVIEW` remains non-`ALLOW` — **held (§14)**.
7. Repaired PBPC request profile can produce a non-`HUMAN_REVIEW` outcome
   where existing Permission Broker semantics legitimately permit it —
   **FAILS.** No repair produces this outcome without fabricating
   approval or exceeding this phase's authorization (§5, §7). Verified
   empirically: re-running §2's live evaluation against the corrected
   contract's own request shape (still `approval_present=False`, since no
   legitimate value to set it `True` was found) still returns
   `HUMAN_REVIEW`.
8. Current push policy semantics not broadened — held (nothing broadened; nothing repaired).
9. No upstream frozen contract contradiction remains hidden — **this
   phase surfaces the contradiction explicitly (§3-§5) rather than
   hiding it**, satisfying the spirit of this criterion even though B-1
   itself is not closed.
10. No production implementation required to make the contract logically
    satisfiable — not evaluated as met, since the contract is not yet
    logically satisfiable (criterion 7 fails).

**Criterion 7 fails. B-1 remains open per the brief's own closure rule.**

---

## 18. Verdict

**B-1 REMAINS OPEN — BLOCKING CONTRACT CONFLICT.**

This is not a failure to make progress: this phase definitively rules out
Category A (no approval source exists or may be fabricated) and Category
B (no existing Foundation mechanism supports applicability-scoping
without an unauthorized architectural decision), definitively locates the
defect as a Category C upstream Foundation/Autonomy-Contract gap, and
corrects two real, independently-confirmed errors in PBPC-001's own text
(§8, §9). What remains is a genuine architectural question — whether and
how the Permission Broker Foundation should express policy applicability
by operation profile — that exceeds a "clarification and repair" phase's
authorization and requires its own, separately authorized design phase.

---

## 19. PBPC-001 Versioning

PBPC-001 is versioned to **v1.1**. Changes (all in
`docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`,
§20 below for the exact diff description):

- Contract identity/status header: version `1.0` → `1.1`, "Frozen by"
  updated to record this phase's amendment.
- Section 4 (Terminology): a sixth concept added — **Git Approval** —
  explicitly frozen as distinct from and non-substitutable for
  Confirmed/Authorized/Permitted/Capable/Executed, citing
  `docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md` §5.
- Section 8's `POL-004` table row: corrected from "Deferred design, not
  MVP-active" to an accurate description (§8 above) and the 8
  previously-unnamed `HARD_BLOCK_REGISTRY` entries given explicit
  "out of scope, not push-relevant" dispositions (§9 above).
- A new Section 8.1 (Finding B-1 status) added, summarizing this phase's
  analysis and pointing to this phase document for full detail.
- Section 26 (Compatibility Review) and Section 30 (Verdict) corrected:
  the prior "no Blocking finding," "existing push behavior remains
  compatible for the common already-permitted case" language is replaced
  with an explicit statement that **no `pcae push` request can currently
  reach `ALLOW` under this contract**, pending either a Foundation-level
  policy-applicability amendment or a genuine `COMP-003` implementation
  (both out of scope for PBPC-001 itself).
- Section 27 preconditions unchanged in substance; a new precondition
  added: "Finding B-1 (or its successor) is closed" before 148D may be
  authorized.

No requirement ID is renumbered or reused; new requirements (if any) are
appended.

---

## 20. Requirement Repair — Affected Requirements

- **Section 8's `POL-004` disposition row** — corrected (§8, §19).
- **PBPC-REQ-016** (the Section 8 table itself) — table content
  corrected; requirement ID unchanged (the table is the same requirement,
  now with accurate content and full 12-entry disposition, §9).
- **Section 26 (PBPC-REQ-087) compatibility table, "Canonical
  finalization / phase reporting" and general verdict rows** — corrected
  to state the true current non-satisfiability (§19).
- **Section 30 verdict prose (PBPC-REQ tied to no specific number — Section
  30 is narrative, not itself a `PBPC-REQ`)** — corrected to disclose
  Finding B-1 rather than claim none exists.
- No other requirement is affected. Section 14 (Request Construction),
  Section 15 (Decision Semantics), Section 9 (Non-Bypassability), Section
  13 (Operation Identity), Sections 16-25 (TOCTOU, failure ownership,
  diagnostics, replay, IWC/AESIC/Runtime independence) are all
  independently reconfirmed accurate and unaffected by this phase's
  findings — B-1 is narrowly located in Section 8's coverage claim and
  Section 26/30's compatibility/verdict claims, not in the broader
  architecture.

---

## 21. Recommended Next Phase

Not 148D (implementation — B-1 open, per Category C not resolvable by
implementation alone). Not 148C.2 as originally anticipated ("Repair
Independent Verification") — there is no repair yet to verify.

**Recommended: 148C.2 — Permission Broker Foundation Policy Applicability
Model Design.** Scope (for a future, separately authorized phase to
define precisely, not pre-authorized here): determine, with explicit
authorization, whether and how the Permission Broker Foundation should
express that a given `POL-` rule does not apply to a given operation
profile — evaluating, at minimum, the two candidate mechanisms this phase
identified but declined to adopt unilaterally (§5-B, §7): (a) a genuine,
general per-rule applicability predicate added to the Policy Rule
Framework itself (a `POL-004`-only or general amendment, requiring
explicit Foundation-contract authorization), or (b) a documented,
authorized convention for per-consumer `PolicyRegistry` construction,
with an explicit ruling on whether that is consistent with
PBPC-REQ-032's "no second decision taxonomy" prohibition. This design
phase does not, itself, authorize implementation, and should explicitly
re-examine whether `pcae push`'s Permission Broker consumption should
instead simply remain deferred until `COMP-003` (Human Approval Gate,
Phase 111A) is genuinely implemented, rather than repaired around.

This phase does not begin that design work. Do not begin 148C.2 without
separate authorization.

---

## 22. Confirmations

No `src/pcae/**` production file was modified (§16). No `pcae push`
production behavior was changed. No Permission Broker Foundation
behavior was changed — every `POL-` rule, including `POL-004`, is
exactly as Phase 108B froze it. No new Permission Broker policy
(`POL-013+`) was introduced. No approval was fabricated — Category A was
explicitly, evidentially foreclosed (§5-A, §6), and PBPC-001 v1.1 still
fixes `approval_present=False` for every `pcae push` request, unchanged
from v1.0 (PBPC-REQ-046 unchanged in substance). Interactive Workflow
Confirmation was not reinterpreted as Permission Broker approval (§12).
Authority Evaluation/AESIC was not reinterpreted as Permission Broker
approval (§13). `HUMAN_REVIEW` remains non-`ALLOW` and cannot dispatch
push (§14). No Runtime Enforcement behavior was changed. No runtime
capability was elevated. Runtime remains Observed, maximum capability
remains observe, and execution availability remains unavailable,
confirmed live both at bootstrap (§0) and at the close of this phase
(§23).

---

## 23. Governance Results (this phase)

- `pcae_check`: passed
- `pcae_health`: healthy
- `pcae_status_coherence`: coherent
- `pcae_doctor_task_memory`: clean
- `pcae_push_check`: clean, nothing_to_push
- `pcae_runtime_inspect`: Observed / observe / unavailable — unchanged before and after this phase
- `telegram_runtime`: loaded, configured, enabled
- `production_source_diff`: `git diff --name-only -- src/pcae/` empty before this phase's own commits (§16)
- `b1_live_reproduction`: independently reproduced exact against the actual, unmodified `PermissionBroker` (§2)
