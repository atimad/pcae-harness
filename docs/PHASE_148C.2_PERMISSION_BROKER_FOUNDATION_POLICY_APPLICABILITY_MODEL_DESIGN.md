# Phase 148C.2: Permission Broker Foundation Policy Applicability Model Design

**Phase ID:** 148C.2
**Mode:** Architecture/design only. No implementation, no `src/pcae/**`
modification, no Permission Broker Foundation behavior change, no
`POL-001..012` modification, no `POL-013+` addition, no `pcae push`
modification, no runtime capability change.
**Baseline:** PBPC-001 v1.1 (`docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`),
Finding B-1 **OPEN**.
**Predecessor:** Phase 148C.1 (commit `72a761d7`) — B-1 classified Category
C (Foundation/Autonomy-Contract scoping gap); recommended this phase.
**Date:** 2026-08-01

---

## 0. Authorization and Boundary

This phase is authorized to design — not implement — a Permission Broker
Foundation policy-applicability model. It may inspect the Foundation,
`POL-001..012`, Phase 108/109 architecture, PBPC-001 v1.1, and the
148C/148C.1 findings; derive candidate architectures; compare them; select
one; and specify the downstream contract work a future phase would need to
do. It must not modify `src/pcae/**`, change Permission Broker Foundation
or `POL-001..012` behavior, add `POL-013+`, change `pcae push`, close B-1
by declaration, set `approval_present=True`, add human approval, implement
policy filtering, add policy tags, add production request fields, modify
Runtime Enforcement, IWC, or Authority Evaluation/AESIC, introduce
execution, or start 148D.

### Bootstrap (initial inspection)

```
git status --short / --branch --short   -> clean, main, tracking origin/main
git log --oneline -25                   -> HEAD at 72a761d7 (148C.1 task-memory fix)
git rev-list --count origin/main..HEAD  -> 0
pcae health                              -> healthy
pcae check                               -> passed
pcae status coherence                    -> coherent
pcae doctor task-memory                  -> clean
pcae push check                          -> clean, nothing_to_push
pcae runtime inspect                     -> Observed / observe / unavailable, 0 plugins, 0 capabilities
pcae notify status                       -> Telegram configured, enabled, ready
pcae phase-report show --latest          -> 148C.1, recommended next 148C.2
pcae phase-report reconcile --phase-id 148C.1
    -> status: delivery_recorded_bookkeeping_incomplete; promoted generations: 2;
       marker: already_dispatched; checkpoint: completed_receipt_best_effort_incomplete;
       receipt: absent; mutation: none (inspection only)
```

Confirmed: repository clean, 0 unpushed commits, 148C.1 completed, B-1
remains open, 148D not authorized, runtime unchanged (`Observed` /
`observe` / `unavailable`).

### Primary sources independently inspected

- `src/pcae/core/permission_broker_foundation.py` (788 lines, read in full
  — request model, decision model, `PolicyRule`/`PolicyResult`,
  `PolicyRegistry.evaluate_all`, `_compose`, `PermissionBroker.evaluate`,
  `DEFAULT_POLICY_RULES`)
- `docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`
  (PBPC-001 v1.1, full — the downstream consumer contract)
- `docs/PHASE_148C.1_PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT_CLARIFICATION_AND_REPAIR.md`
  (full — B-1's re-derivation, Category A/B/C/D determination, §5-B/§7's
  two declined mechanisms, §21's scope sketch for this phase)
- `docs/PHASE_108_PERMISSION_BROKER_FOUNDATION.md`,
  `docs/PHASE_108_PERMISSION_BROKER_POLICY_RULE_FRAMEWORK.md`,
  `docs/PHASE_108_PERMISSION_BROKER_POLICY_COMPOSITION_HARDENING.md`,
  `docs/PHASE_108_PERMISSION_BROKER_VERIFICATION_COMPATIBILITY.md`
  (targeted — POL-001..012 table, composition/precedence design, request
  vocabulary origin)
- `docs/PHASE_109_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION_DESIGN.md`,
  `docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md` (full —
  canonical command categories, integration points, and the decisive
  precedent "would be consulted (`POL-001`, `POL-003` evidence, `POL-004`
  approval **where applicable**)")
- `docs/V0_2_AUTONOMY_CONTRACT.md` (targeted — INV-001..010, the canonical
  execution lifecycle, COMP-001..010)
- `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` (targeted — NG-008's exact
  condition/rationale text, NG-008's own scope statement)
- `docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md` (targeted —
  §5 Git Approval / Execution Approval separation)
- Live execution against the actual, unmodified `PermissionBroker`/
  `PolicyRegistry`/`build_permission_broker_request` to re-confirm B-1's
  reproduction and to test each candidate architecture's effect on the
  same request, without modifying source.

---

## 1. Executive Summary

This phase designs, but does not implement or freeze as a binding
contract, a Permission Broker Foundation policy-applicability model
answering the governing question: **given a Permission Broker request,
which frozen `POL-` rules are normatively applicable to it, and why?**

The Foundation's actual mechanism today (`PolicyRegistry.evaluate_all`)
runs all twelve registered rules, unconditionally, on every request — a
fact independently reconfirmed live (§5). Phase 108's own design
principle ("single source of authorization... no duplicated authorization
logic") never distinguished this from "all twelve rules are normatively
universal"; the two claims were conflated at the point the Foundation was
built. Phase 109's own command-category design already anticipated the
gap this conflation would eventually produce — its Git-lifecycle category
table entry reads **"`POL-004` approval where applicable"** (§8) — but
that conditional was never encoded into the Foundation's evaluation
mechanism.

Independent re-derivation of each of the twelve `POL-` rules' intended
domain (§9) finds eleven are legitimately universal (structural
sanity/evidence/task checks that should gate every request regardless of
operation) and exactly one, `POL-004` (Missing Human Approval), is not: its
own upstream lineage (`NG-008` → `INV-003` → `COMP-003`) scopes it,
textually and controllingly, to the generic mediated-execution lifecycle
(`AWAITING_HUMAN_APPROVAL` → `AUTHORIZED`) — a lifecycle git-tracked
content mutations (`commit`, `push`, `docs_mutation`, `source_mutation`,
`test_mutation`) structurally never enter, because those are governed by
**Git Approval** instead (§10, restating 148C.1 §3-§4's finding, not
re-litigating it).

The selected architecture (§18) is a **hybrid of Candidate A (policy-owned
applicability) and Candidate B (declarative applicability metadata)**:
each `PolicyRule` optionally declares a frozen `applicable_execution_classes`
set; the registry, not the caller, resolves and enforces it during
`evaluate_all`, using the Permission Broker Foundation's own existing
`execution_class` field (§11-§12) — no new request field, no new decision
value, no caller-selectable exclusion mechanism. Applied to the one rule
that needs it, `POL-004` would become scoped to
`{EXECUTION_CLASS_SHELL, EXECUTION_CLASS_BACKEND, EXECUTION_CLASS_ADAPTER,
EXECUTION_CLASS_ROLLBACK}` — the mediated-execution classes its own
lineage governs — and would not apply to `EXECUTION_CLASS_MUTATION`
(git-tracked content changes, including `pcae push`) or
`EXECUTION_CLASS_NONE` (reads). Under this design, `pcae push`'s
`execution_class=EXECUTION_CLASS_MUTATION` (already fixed by
PBPC-REQ-034) would make `POL-004` non-applicable to it — not because
push was special-cased, but because push was never in `POL-004`'s
governed domain to begin with (§19).

**This design does not close B-1.** It is not implemented, not frozen as
a normative contract, and not independently verified. §22 states the
remaining closure path. **Recommended next phase: 148C.3 — Permission
Broker Foundation Policy Applicability Contract Freeze** (§29). This
document freezes an architectural recommendation only.

---

## 2. Scope

In scope: independent reconstruction of the Foundation's original
purpose and every `POL-` rule's intended domain; inventory of existing
request-classification fields; determination of whether applicability is
already implicit in frozen upstream contracts; four candidate
architectures, compared and one selected; `NOT_APPLICABLE` semantics;
missing-vs-non-applicable distinction; determinism, fail-closed, and
security analysis; contract-impact assessment; B-1 closure path;
recommended next phase.

Out of scope: any `src/pcae/**` change; any `POL-001..012` modification;
any `POL-013+` addition; any `pcae push` change; declaring B-1 closed;
`approval_present=True`; a caller-selectable policy-exclusion mechanism;
a normative contract freeze (that is 148C.3's job); 148D planning.

---

## 3. Re-Deriving the Foundation's Original Purpose

`permission_broker_foundation.py`'s own module docstring (lines 1-33)
states the Foundation is **"the single policy decision point for future
execution"** — a generic policy registry and evaluator, not
execution-specific in the sense of being restricted to one kind of
action. Its three frozen design principles are (1) fail closed on
anything unknown/unavailable/unsupported, (2) policy separated from
execution, (3) single source of authorization ("no duplicated
authorization logic"). None of the three principles states or implies
that every registered policy rule must apply to every request — "single
source of authorization" means there is exactly one place authorization
questions are asked (`PermissionBroker.evaluate()`), not that every
question it can ask is relevant to every request.

Answering the brief's specific questions:

- **Universal policy engine, or policy registry-and-evaluator?** The
  latter. `PolicyRegistry` (108B) is explicitly generic infrastructure —
  "Future rule addition means constructing a new `PolicyRegistry` with an
  extended rule tuple" (`permission_broker_foundation.py:635-637`) — built
  to hold whatever rules are registered, not to assert those rules share
  one domain.
- **Execution-specific, or generic across action classes?** Generic. The
  request model (`PermissionBrokerRequest`) already carries `action_type`
  and `execution_class` as first-class fields with ten and six known
  values respectively (lines 96-134), explicitly modeling that requests
  come in different, distinguishable classes. A Foundation that only
  cared about one class would not need this vocabulary.
- **Does it assume human approval for certain operation families?**
  Yes — `POL-004` exists exactly because some operation families need it.
  The Foundation's request vocabulary already anticipates that not every
  family needs the same policies; it never built the mechanism to encode
  that anticipation into evaluation order or scope.
- **Was `DEFAULT_POLICY_RULES` intended as universal policy, or the
  initial policy inventory?** The initial inventory. Six of its twelve
  entries are `StubPolicyRule` placeholders — "a registered,
  always-evaluated placeholder for a policy this foundation cannot yet
  check" (lines 551-559) — registered for identifier stability across
  phases, not because every future consumer will need all twelve. The
  registry's own comment ("Future rule addition means constructing a new
  `PolicyRegistry`... the broker itself never needs to change") already
  anticipates growth; nothing in it asserts every rule, once added, binds
  every consumer identically forever.

**Conclusion:** the Foundation is a generic, extensible policy
registry-and-evaluator whose current single-registry, evaluate-everything
mechanism is an implementation simplification from Phase 108B (108B's own
stated concern was eliminating *duplicated* authorization logic across
rules, not establishing that all rules are normatively universal), not a
frozen design principle that forbids ever introducing per-rule
applicability. Introducing an applicability layer clarifies an
under-specified mechanism; it does not contradict a stated invariant.

---

## 4. Complete POL-001..012 Inventory

| Policy | Purpose | Inputs | Decision | Intended domain | Universal? | Evidence |
|---|---|---|---|---|---|---|
| POL-001 | Missing Active Task | `task_id` | DENY | Any action requiring an active task contract (`INV-002`, `NG-001`) — no operation-class exception exists in `NG-001`'s own text | **Universal** | `MissingActiveTaskRule` (foundation, lines 367-389); no `action_type`/`execution_class` condition |
| POL-002 | Task Outside Scope | (stub — no field checked yet) | n/a | Any action requiring task-scope validation | Universal (moot; stub) | `StubPolicyRule`, never triggers |
| POL-003 | Missing Evidence | `evidence_available` | DENY | Any action a decision is being requested for at all (`INV-009`) — evidence-of-readiness is a structural precondition, not tied to one operation family | **Universal** | `MissingEvidenceRule` (lines 392-413); no operation-class condition |
| POL-004 | Missing Human Approval | `approval_present` | HUMAN_REVIEW | Mediated execution actions specifically — `NG-008`'s own condition text: "The action **has reached `AWAITING_HUMAN_APPROVAL`**" (`docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md:179`), a state only the generic execution lifecycle defines | **Not universal** — scoped to the mediated-execution lifecycle; see §9-§10 | `MissingHumanApprovalRule` (lines 416-443); coded unconditionally (§5), but its own upstream citation chain (`NG-008`→`INV-003`→`COMP-003`) textually restricts its condition to a lifecycle state most operation classes never enter |
| POL-005 | Execution Disabled | `simulation_only` | DENY | Any request claiming the Foundation's own execution boundary (`COMP-002`) would carry it out — the condition is about the Foundation's implementation status, not about one operation family | **Universal** (but self-limiting: only requests with `simulation_only=False` ever trigger it — see §17 on why this differs from an applicability question) | `ExecutionDisabledRule` (lines 446-475); "Unconditionally active by construction (NG-025)" |
| POL-006 | Unknown Capability | `action_type`, `execution_class` | DENY | Structural validity of every request's classification fields — a precondition for any other rule to reason about those fields at all | **Universal** | `UnknownCapabilityRule` (lines 478-522); explicitly must run before any applicability logic could trust `execution_class` (§20-fail-closed) |
| POL-007 | Unknown Component | `requested_component` | DENY | Structural validity of the component identity — same reasoning as POL-006 | **Universal** | `UnknownComponentRule` (lines 525-548) |
| POL-008 | Emergency Stop Active | (stub) | n/a | Would gate every action once `COMP-009` exists — an emergency stop is definitionally global, not operation-class-scoped (`INV-007`: "overrides every other authorization") | Universal (moot; stub) | `StubPolicyRule`; `INV-007` text |
| POL-009 | Audit Unavailable | (stub) | n/a | Would gate any action requiring a durable audit artifact (`INV-005`) — likely universal once `COMP-007` exists, since `INV-005` states "every execution decision produces an audit artifact" without an operation-class exception | Likely universal once implemented (moot; stub) | `StubPolicyRule`; `INV-005` text |
| POL-010 | Rollback Unavailable | (stub) | n/a | Would gate actions requiring rollback readiness (`INV-006`) — plausibly scoped to mutating/execution classes only (a read has nothing to roll back), an applicability question for a **future** phase to design when `COMP-008` is implemented, not this phase | Plausibly scoped, undetermined (moot; stub, out of scope here) | `StubPolicyRule`; `INV-006` text |
| POL-011 | Unknown Backend | (stub) | n/a | Would gate `execution_class=backend` requests specifically — a natural applicability candidate once implemented (a backend-identity check has no meaning for a `mutation` or `read` request) | Plausibly scoped to `EXECUTION_CLASS_BACKEND` once implemented (moot; stub) | `StubPolicyRule`; name itself ("Unknown Backend") |
| POL-012 | Unknown Adapter | (stub) | n/a | Same reasoning as POL-011, for `execution_class=adapter` | Plausibly scoped to `EXECUTION_CLASS_ADAPTER` once implemented (moot; stub) | `StubPolicyRule`; name itself |

**Finding:** exactly one implemented rule, `POL-004`, has a textually
demonstrable, non-universal intended domain. Two not-yet-implemented stub
rules (`POL-011`, `POL-012`) are plausible future applicability
candidates by their own names, and a third (`POL-010`) is plausibly
scoped — but designing their eventual applicability is explicitly
deferred to whatever future phase implements them (§2, out of scope);
this phase does not decide it now. This is not an assumption that all
twelve belong to one applicability class merely because they share a
registry — each was independently assessed on its own textual evidence.

---

## 5. POL-004 Deep Re-Derivation

Restated from Phase 148C.1 §3-§4 (independently re-confirmed here, not
re-litigated, since 148C.1 already performed this analysis exhaustively
and this phase found no basis to reach a different conclusion):

- **Exact trigger:** `not request.approval_present`
  (`permission_broker_foundation.py:428`) — unconditional; no
  `action_type`/`execution_class` check anywhere in
  `MissingHumanApprovalRule.evaluate()`.
- **Protected boundary:** the `AWAITING_HUMAN_APPROVAL -> AUTHORIZED`
  transition in the canonical execution lifecycle (`docs/V0_2_AUTONOMY_CONTRACT.md`),
  per `NG-008`'s own condition text ("The action has reached
  `AWAITING_HUMAN_APPROVAL`").
- **What "approval" means:** execution approval (`COMP-003`, "Human
  Approval Gate") — categorically distinct from **Git Approval**
  (`docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md` §5, "these
  are never interchangeable").
- **Tied to execution?** Yes, specifically to the generic
  mediated-execution lifecycle, not to "mutation" generically —
  `commit`/`push` mutate the repository without ever entering that
  lifecycle (they are governed by Git Approval instead, a wholly separate
  mechanism that predates the Permission Broker Foundation, Phase 107E).
- **Tied to autonomous operation?** Tied to *mediated* operation
  specifically — operations that would, if executed, pass through
  `COMP-002`/`COMP-004`/`COMP-005`/`COMP-006`/`COMP-008`. Git mutation via
  `pcae commit`/`pcae push` has never gone through any of those
  boundaries and is not designed to (Phase 109's own integration-point
  table: "zero broker references in `commit.py` or `push.py`," confirmed
  108D).
- **Does simulation matter?** No — `POL-004`'s condition does not read
  `simulation_only`; the two fields are independent axes (148C.1 §3, §11,
  reconfirmed §17 below).
- **Intended to apply to command paths such as `pcae push`?** No.
  Phase 109's own command-category design (§8 below) is explicit that Git
  lifecycle operations require "Git approval... not execution approval,"
  and its integration-point table's own language — **"`POL-004` approval
  where applicable"** — already anticipates that `POL-004` would not
  apply to every future consumer unconditionally, one phase before the
  Foundation's mechanism was even frozen.

**Classification: SPECIFIC_OPERATION_CLASS** (from the brief's own
vocabulary, §3 of the brief) — specifically, the mediated-execution
operation classes (`execution_class ∈ {shell, backend, adapter,
rollback}`), not `UNIVERSAL`, not `UNDER-SPECIFIED` (its scope is
textually clear from primary sources; what was missing was a mechanism to
encode that scope, not the scope itself).

This does not weaken `POL-004`. Nothing in this analysis, or in 148C.1's,
found `NG-008`'s underlying concern wrong for its actual domain
(mediated execution once `COMP-002`/`COMP-004`/`COMP-005`/`COMP-006`
exist). The finding is narrower: `pcae push` was never in that domain.

---

## 6. Existing Request-Classification Field Inventory

`PermissionBrokerRequest` (`permission_broker_foundation.py:141-162`),
inspected field by field for applicability-scoping potential:

| Field | Current normative meaning | Valid values | Inspected by any rule today? | Could legitimately scope applicability? | Backward-compatible if used for scoping? |
|---|---|---|---|---|---|
| `action_type` | The specific operation being requested (10 known values) | `KNOWN_ACTION_TYPES` (line 107) | Yes — `POL-006` validates membership | Yes, but finer-grained than needed for `POL-004` (would require enumerating 10 values' mediated-vs-mutation status individually) | Yes, but §12 prefers `execution_class` as the smaller, already-sufficient dimension |
| `execution_class` | The structural category of capability the action requires (6 known values: `none`, `mutation`, `shell`, `backend`, `adapter`, `rollback`) | `KNOWN_EXECUTION_CLASSES` (line 127) | Yes — `POL-006` validates membership | **Yes — this is the natural dimension.** It already partitions exactly along the Git-Approval/Execution-Approval boundary (§10-§12) | Yes — existing values, no schema change |
| `task_id` | Active task contract binding | task-contract ID string or `None` | Yes — `POL-001` | No — orthogonal to which policies apply; it is itself a policy input | n/a |
| `phase_id` | Active phase binding | phase ID string or `None` | No rule reads it today | No — same reasoning as `task_id` | n/a |
| `requested_component` | Which `COMP-NNN` is asked to decide | `COMPONENT_IDS` | Yes — `POL-007` | No — identifies the decider, not the operation's domain | n/a |
| `requested_capability` | Free-text capability label (e.g. `"pcae_push"`) | unconstrained string | No rule reads it today | No — not a frozen, closed vocabulary; using it for applicability would require validating an open string set, weakening determinism | n/a |
| `requested_resource` | Optional diagnostic target (e.g. a ref) | unconstrained string or `None` | No rule reads it today (PBPC-REQ-047: "its absence SHALL NOT change the decision") | No | n/a |
| `evidence_available` | Whether readiness evidence was gathered | bool | Yes — `POL-003` | No — orthogonal, itself a policy input | n/a |
| `approval_present` | Caller-asserted execution approval | bool | Yes — `POL-004` | **No — this is exactly the field the brief's §19 forbids using for applicability** ("Invalid logic: if approval_present: POL-004 applies... Applicability must precede evidence evaluation") | n/a |
| `simulation_only` | Whether the Foundation's own execution boundary would carry this out | bool (defaults `True`) | Yes — `POL-005` | No — see §17; using it would let a caller weaken `POL-004`'s applicability by claiming simulation | n/a |

**Result:** `execution_class` is the only existing field that is (a)
already a closed, validated, six-value vocabulary, (b) already
structurally independent of the evidence fields (`approval_present`,
`evidence_available`) the brief requires applicability to precede, and
(c) already partitions requests exactly along the boundary `POL-004`'s
own lineage cares about (§10). No new request field is required.

---

## 7. Is Applicability Already Implicit in Frozen Contracts?

Searched frozen contracts for applicability language (per the brief's
§5 instruction). Found, verbatim:

- `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md:20-24` (Phase 107C,
  frozen): *"`NG-` gates are scoped specifically to the execution
  readiness decision point — the moment just before a proposed action
  would move from `READY` to `AWAITING_HUMAN_APPROVAL` in the execution
  lifecycle."* — an explicit textual scope boundary on `NG-008` (and
  therefore `POL-004`) to the mediated-execution lifecycle.
- `docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md:163` (Phase
  109A, frozen): **"`POL-004` approval where applicable"** — the word
  "applicable" appears in the frozen design text itself, one phase before
  the Foundation's evaluate-everything mechanism was built (Phase 108).
- Same document, Documentation/Source mutation categories (§8 above,
  lines ~118-134): *"no execution approval concept applies, since this is
  a Git-tracked content change, not a mediated execution action."*

**Conclusion: applicability already exists normatively in frozen upstream
text and was omitted from the Foundation's implementation.** Per the
brief's own instruction, this is classified **implementation/model
incompleteness**, not newly invented semantics (§5 of the brief). This
also directly answers the brief's alternative concern ("If contracts
truly say every rule applies to every request... Chapter 148's push
integration premise conflicts with the Foundation"): they do not say
that: NG-008's own scope statement predates and contradicts an
unconditional reading, and Phase 109 already flagged the conditional
explicitly. The Foundation's *code* is what is universal; the frozen
*contracts it implements* were never claimed to be.

---

## 8. Live Reproduction — Confirming the Mechanism Gap (Restated, Not Re-Litigated)

Re-ran 148C.1 §2's live evaluation against the actual, unmodified
`PermissionBroker` (read-only; no source modified):

```python
req = build_permission_broker_request(
    action_type=ACTION_PUSH, execution_class=EXECUTION_CLASS_MUTATION,
    requested_component="COMP-001", requested_capability="pcae_push",
    task_id="some-active-task", evidence_available=True,
    approval_present=False, simulation_only=True,
)
PermissionBroker().evaluate(req)
# -> decision=HUMAN_REVIEW, causing_policy_ids=('POL-004',)
```

Identical to 148C.1's result. `PolicyRegistry.evaluate_all`
(lines 647-659) iterates the full fixed `DEFAULT_POLICY_RULES` tuple with
no `action_type`/`execution_class` gate anywhere in the loop, in
`_compose`, or in any rule besides the rule's own internal field check —
independently reconfirmed by direct reading, not merely trusted from
148C.1's prose.

---

## 9. Design Requirements (Restated as Constraints on Every Candidate)

Every candidate below is assessed against: explicit, deterministic,
inspectable, contract-defined, fail-closed, versionable, auditable,
testable, operation-profile aware, independent of desired decision
outcome; and must not rely on policy-name parsing, rule-ordering
accidents, caller-selected exclusions, command-specific `if push`
branches, hidden environment variables, mutable global configuration
without contract, or "skip `POL-004`" flags.

---

## 10. Candidate Architecture A — Policy-Owned Applicability Predicate

```
for policy in registry:
    if policy.applies_to(request):
        evaluate(policy)
```

Each `PolicyRule` would define `applies_to(request) -> bool` alongside
`evaluate(request) -> PolicyResult`.

- **Determinism:** high — a pure function of the request and the
  policy's own frozen logic.
- **Policy encapsulation:** high — the applicability question lives with
  the same class that owns the policy's meaning, avoiding a
  split-brain where meaning and scope are defined in different places.
- **Auditability:** medium — if `applies_to` is an arbitrary method body,
  "why did `POL-004` not apply?" requires reading code, not data; harder
  to inspect or render in a diagnostic surface than a declarative
  structure.
- **Contract traceability:** medium — a contract can describe the
  *intended* predicate in prose, but verifying an implementation matches
  requires reading the method, not comparing against a frozen table.
- **Backward compatibility:** high if the base class defaults
  `applies_to` to `return True` (universal, matching today's behavior
  for every rule that does not override it).
- **Risk of hidden policy exemptions:** medium — an arbitrary method body
  could, in principle, encode a caller-specific carve-out
  (`if request.requested_capability == "pcae_push": return False`) that
  is much harder to audit for absence of "no push-specific escape hatch"
  (brief §33) than a declarative structure would be.
- **Ease of independent verification:** medium — requires code review of
  each override, not a data-diff against a frozen table.

---

## 11. Candidate Architecture B — Declarative Applicability Metadata

```
policy_id: POL-004
applies_to:
  execution_classes: [shell, backend, adapter, rollback]
```

(Conceptual; not a schema this phase implements.)

- **Are existing request dimensions sufficient?** Yes — `execution_class`
  alone (§6). No new request dimension is needed.
- **Contract/version implications:** small — a per-rule frozen attribute,
  versioned alongside the Foundation contract itself (no separate
  artifact/version domain needed, §24).
- **Risk of caller manipulation:** none directly — the metadata is
  attached to the *policy*, at registration time, by the Foundation's own
  code, never by the calling command. (The request's `execution_class`
  value itself is a separate spoofing question, addressed in §21 — this
  is about who can alter the *mapping*, not who supplies the *request*.)
- **Registry validation:** straightforward — a frozen set attribute can
  be validated once at import time (every listed value is a member of
  `KNOWN_EXECUTION_CLASSES`), independent of any specific request.
- **Deterministic matching:** yes — a set-membership test.
- **Auditability:** high — "why did `POL-004` not apply?" has a
  one-line, data-legible answer: `request.execution_class not in
  POL-004's applicable_execution_classes`.

---

## 12. Candidate Architecture C — Frozen Policy Profiles

```
PROFILE_EXECUTION = {POL-001, POL-003, POL-004, POL-005, POL-006, POL-007, ...}
PROFILE_COMMAND_MUTATION = {POL-001, POL-003, POL-006, POL-007, ...}
PROFILE_SIMULATION = {...}
```

- **Understandable policy sets:** yes, at first — a named profile is easy
  to reason about informally.
- **Excessive coupling / profile proliferation:** real risk. With twelve
  rules and (eventually) ten action types and six execution classes, the
  number of profiles needed to represent every legitimate combination
  either grows unmanageably or is under-specified (forcing many requests
  into an approximate "closest" profile — exactly the kind of
  imprecision Finding B-1 already demonstrated is dangerous). Today,
  exactly one rule needs scoping; defining named profiles for a
  one-rule problem is more taxonomy than the evidence justifies.
- **Caller-selected authority:** a request would need a `profile` field
  (new addition) or a mapping from `execution_class` to profile — the
  latter collapses back into Candidate B with an unnecessary
  intermediate layer.
- **Hidden weakening risk:** a profile is a set of *included* policies;
  an engineer extending a profile for one legitimate new consumer could
  silently include that consumer under a profile that omits a rule it
  should have — profiles obscure the per-rule reasoning that declarative
  per-rule metadata (Candidate B) keeps explicit.

**Assessment: rejected as the primary mechanism.** Profile proliferation
and an unnecessary new intermediate abstraction are not justified when
`execution_class` already provides the exact partition needed (§6, §11).
Not ruled out for a much later phase if the number of rules requiring
distinct, overlapping scoping grows enough to justify it — that
evidence does not exist today.

---

## 13. Candidate Architecture D — Universal Policies with Conditional Logic Inside Each Rule

```
if request.operation_class not in protected_classes:
    return NOT_APPLICABLE
```

This is closest to *today's* actual code shape (each rule already
inspects its own relevant field), formalized with an explicit
`NOT_APPLICABLE` result.

- **Assessment:** inferior to A/B for this specific gap, for two reasons.
  First, it requires touching every individual rule's `evaluate()` body
  each time an applicability boundary needs adjusting, rather than
  centralizing the concept once in the registry (`PolicyRegistry.evaluate_all`)
  — the exact "duplicated logic" failure mode Phase 108B's original
  refactor (moving from ad hoc broker logic to a `PolicyRule`/`PolicyRegistry`
  split) already eliminated once, this candidate risks reintroducing at
  the applicability layer. Second, folding applicability into
  `evaluate()`'s own return value make "not triggered because the
  condition was false" and "not applicable to this operation" the same
  code path unless a genuinely new result value (`NOT_APPLICABLE`,
  distinct from `triggered=False`) is introduced — which raises exactly
  the decision-vocabulary-expansion question §14 addresses, and this
  candidate cannot avoid it the way A/B can (A/B filter *before* calling
  `evaluate()` at all, so `evaluate()`'s own return shape never needs a
  third state).

**Assessment: not selected**, but its core observation (per-rule logic
already exists for the *triggering* condition) is preserved by A/B: the
new applicability layer runs *before*, not instead of, each rule's
existing `evaluate()` logic.

---

## 14. `NOT_APPLICABLE` Semantics

**Determination: no new broker-level decision value is needed.**
`ALLOW`/`DENY`/`HUMAN_REVIEW` remain the only three `PermissionBrokerDecision.decision`
values (per the brief's own preference, §12: "Prefer not to expand
decision vocabulary unnecessarily," and per PBPC-REQ-032's prohibition on
a second decision taxonomy — a fourth *broker*-level value would risk the
same kind of taxonomy drift).

What *is* needed is a **per-policy** status, one level below the broker
decision: a `PolicyResult.applicable: bool = True` field, distinct from
`triggered`. Applicability filtering (Candidate A/B) happens in
`PolicyRegistry.evaluate_all`, *before* a non-applicable rule's
`evaluate()` is even called — so a non-applicable rule never produces a
`triggered=True/False` judgment about a request it was never meant to
judge. This is exactly the brief's own preferred resolution (§12, second
bullet): "applicability filtering happens before evaluation" — no broker
decision expansion, a `PolicyResult`-level distinction only.

---

## 15. Missing vs. Non-Applicable Policy

**Missing policy** (registry corruption / incomplete registry): the
canonical twelve-`POL-NNN` identifier set is itself frozen
(`POLICY_IDS`, `permission_broker_foundation.py:592`). A future
implementation would validate, at `PolicyRegistry` construction time,
that every canonical ID is present in the constructed rule tuple; absence
of a canonical ID is a missing-policy condition and fails closed exactly
as today's empty-registry branch already does (`_compose`'s
`if not results` DENY, lines 680-691) — extended conceptually to "any
canonical ID absent," not only "the whole registry is empty."

**Non-applicable policy** (present in the registry, its
`applicable_execution_classes` predicate returned false for this
request's `execution_class`): recorded, not silently dropped —
`PermissionBrokerDecision` would gain a `non_applicable_policy_ids: tuple[str, ...]`
field (additive, alongside the existing `evaluated_policy_ids`/
`triggered_policy_ids`), so "why did `POL-004` not run?" always has a
deterministic, inspectable answer distinct from "why didn't `POL-004`
trigger" and distinct from "why is `POL-004` missing."

**Neither is spoofable by the caller:** the canonical ID set and each
rule's `applicable_execution_classes` are both frozen at the Foundation
code level, not supplied by the request or by any command-layer caller
(§21).

---

## 16. Policy-Selection Determinism (Frozen as an Invariant)

Given identical broker version, policy registry, request, and
`execution_class`, the applicable policy set is identical, by
construction: applicability resolution is a pure function
(`request.execution_class in rule.applicable_execution_classes or
rule.applicable_execution_classes is None`) with no heuristic,
probabilistic, environment-dependent, or evaluation-order-dependent
component. No design considered here introduces any such dependency.

---

## 17. Why `POL-005`/`simulation_only` Is Not an Applicability Precedent

`POL-005` (`ExecutionDisabledRule`) is universal in the applicability
sense defined here (it runs on every request), but its *triggering
condition* happens to be self-limiting (`if request.simulation_only:
not_triggered`). This is different from "not applicable": `POL-005` is
still asking a real, universal question ("does this request claim
execution capability the Foundation doesn't have?") of every request —
it merely almost always answers "no" today because every real consumer
sets `simulation_only=True` (PBPC-REQ-036). Distinguishing this from
`POL-004`'s case matters for §21's threat model: `simulation_only` must
remain irrelevant to applicability (a caller cannot narrow its policy set
by toggling it), whereas `execution_class` is precisely the field this
design uses for `POL-004`'s applicability, because — unlike
`simulation_only` — `execution_class` is fixed per integration point by
contract (PBPC-REQ-034), not caller-discretionary per request.

---

## 18. Candidate Comparison and Selected Architecture

| Criterion | A (policy-owned predicate) | B (declarative metadata) | C (frozen profiles) | D (conditional-in-rule) |
|---|---|---|---|---|
| Deterministic | Yes | Yes | Yes | Yes |
| Fail-closed (default = universal) | Yes, if base defaults `True` | Yes, if default = `None` (universal) | Requires explicit inclusion in every profile — risk of accidental omission | Yes, but duplicated per rule |
| Caller-spoof resistant | Yes | Yes | Yes (but needs a new `profile` field, itself a spoof surface) | Yes |
| Contract clarity | Medium (method body) | **High** (frozen data, diffable) | Medium (named profile obscures per-rule reasoning) | Medium |
| Policy encapsulation | **High** | High (data lives with the rule class) | Low (membership lives in an external table) | High |
| Auditability | Medium | **High** | Medium | Low (folded into existing return value) |
| Backward compatibility | High | **High** | Medium (migration must define profiles for every existing implicit consumer) | High |
| Extensibility | High | High | Low (proliferation risk, §12) | Medium |
| Minimal semantic change | Medium | **High** (reuses `execution_class` exactly) | Low (new taxonomy) | Medium |
| Implementation simplicity | Medium | **High** | Low | Medium |

**Selected: a hybrid of A and B.** Each `PolicyRule` gets a frozen class
attribute, `applicable_execution_classes: frozenset[str] | None = None`
(default `None` = universal, preserving current behavior for eleven of
twelve rules unchanged). This is Candidate A's principle (the policy
owns its applicability) realized through Candidate B's representation
(declarative, frozen, diffable data, not an arbitrary method body) —
combining A's encapsulation and backward-compatible default with B's
superior auditability and contract clarity. `PolicyRegistry.evaluate_all`
(not the caller, not a per-consumer parameter) reads this attribute and
enforces it uniformly for every request, for every consumer, with no
`exclude_policies=[...]` parameter anywhere in the public interface
(§21, §33 of the brief).

---

## 19. Applicability Authority

**Registry-enforced, policy-declared.** The policy class declares its own
applicability metadata (encapsulation, traceability to the rule's own
docstring/citations); the registry (`PolicyRegistry.evaluate_all`), not
the request, not the caller, not the command layer, is the sole component
that reads and enforces it. This directly forecloses the brief's
explicit prohibited shape:

```
broker.evaluate(request, exclude_policies=["POL-004"])
```

No such parameter exists in this design, on the broker, the registry, or
any future Command Evidence Adapter. A caller can only ever influence
applicability indirectly, by supplying a truthful `execution_class` —
and `execution_class` is not caller-discretionary per request; it is
fixed per integration point by contract (§21).

---

## 20. Fail-Closed Behavior

| Scenario | Behavior |
|---|---|
| Unknown `execution_class` | Already DENY today via `POL-006` (`UnknownCapabilityRule`), which must and does run before any applicability question is meaningful — `POL-006` itself is universal (§4) and is never subject to applicability filtering. |
| Missing classification (`execution_class` absent) | Not possible — `PermissionBrokerRequest.execution_class` is a required, non-optional dataclass field; construction fails before any policy runs. |
| Unsupported profile | Not applicable — this design has no "profile" concept (Candidate C rejected, §12). |
| Policy with no applicability metadata | Default `None` = universal — evaluated for every request, matching today's behavior exactly. Absence of metadata never narrows applicability. |
| Malformed applicability metadata (e.g., a value not in `KNOWN_EXECUTION_CLASSES`) | Fails toward **more** scrutiny, not less: a malformed/unrecognized value is treated as if the metadata were absent (`None`, universal), never silently narrowing the applicable set. |
| Duplicate policy applicability definition | Not structurally possible — one frozen class attribute per rule class, not a separately mutable mapping. |
| Conflicting policy metadata | Not applicable — no cross-rule metadata exists; each rule's applicability is self-contained. |
| Unknown policy (not in canonical `POLICY_IDS`) | Rejected at registry construction (extends today's design, §15). |
| Registry mismatch (wrong rule tuple loaded) | A future implementation would validate the canonical `POLICY_IDS` set at construction, exactly as it validates request shape today (`PermissionBroker.evaluate`'s existing structural check, lines 774-784). |
| Version mismatch | See §24 — applicability travels with the Foundation contract's own version; a mismatch is a Foundation-contract-version mismatch, not a separate failure mode. |

**Design invariant restated:** the default always evaluates *more*
policies, never fewer, when anything is unknown or malformed.

---

## 21. Security Threat Model

| Threat | Mitigation |
|---|---|
| **Profile spoofing** (caller claims a profile with fewer policies) | No profile concept exists (§12, §18) — nothing to spoof. |
| **Action spoofing** (caller labels real mutation as advisory/simulation) | Applicability keys on `execution_class`, never on `simulation_only` (§17) — toggling `simulation_only` has zero effect on which policies apply. `execution_class` itself is fixed per integration point by contract (e.g. PBPC-REQ-034 fixes `pcae push`'s `execution_class=EXECUTION_CLASS_MUTATION` as a normative requirement, not a per-request caller choice) — the same trust boundary the Foundation already relies on for `action_type` today (a conformant Command Evidence Adapter is trusted to populate fields truthfully; PBPC-REQ-045/046 already assume this for every other field). |
| **Applicability downgrade** (policy metadata altered to make a rule non-applicable) | `applicable_execution_classes` is a frozen class attribute in `src/pcae/core/permission_broker_foundation.py`, changeable only by a code change to that file — subject to the same code-review/contract-freeze governance as any other Foundation change, not a runtime-mutable value. |
| **Registry substitution** (different applicability registry loaded) | `PolicyRegistry`'s constructor already accepts an explicit rule tuple (existing mechanism, `permission_broker_foundation.py:640`) for legitimate testing/composition; production consumption is bound to `DEFAULT_POLICY_RULES` by contract (PBPC-REQ-011), not by runtime discovery — no dynamic loading mechanism exists to substitute. |
| **Policy omission** (required policy absent) | Canonical `POLICY_IDS` completeness check at construction (§15, §20) — fails closed. |
| **New consumer ambiguity** (unknown future command accidentally receives weak policy set) | Impossible to receive a *weaker* set than today's universal baseline unless a rule explicitly declares a narrower `applicable_execution_classes` — and only `POL-004` would (§18); every other rule's default `None` continues applying universally regardless of which command constructs the request. |
| **Version downgrade** (older applicability version chosen) | No separate applicability-version artifact exists to downgrade (§24) — it is inseparable from the Foundation module's own version. |
| **Direct broker invocation** (caller constructs an intentionally under-classified request) | Same trust boundary as today's `action_type`/`task_id`/`evidence_available` fields — a malicious caller who can already fabricate any request field can already misrepresent them all; this design introduces no *new* attack surface beyond what already exists for every other request field, and does not weaken `POL-006`'s existing structural validation. |

---

## 22. Policy Applicability Versioning

**Smallest coherent model: applicability metadata versions with the
Permission Broker Foundation contract itself.** No separate applicability-
profile-version artifact, no separate request-schema version. Each
`PolicyRule`'s `applicable_execution_classes` is defined in the same
frozen module (`permission_broker_foundation.py`) and would be reviewed,
frozen, and versioned exactly as `POL-001..012`'s own semantics already
are — through a Foundation-contract amendment phase (148C.3, this
document's recommendation), not a new artifact/version domain. This
satisfies the brief's explicit preference ("do not create a separate
artifact/version domain without demonstrated need") — no such need is
demonstrated for a twelve-rule registry with (initially) exactly one
scoped rule.

---

## 23. Relationship to `POL-001..012` Meaning

**Preferred outcome achieved: `POL-004`'s meaning is unchanged;
`POL-004`'s applicability is made explicit.** `MissingHumanApprovalRule.evaluate()`'s
own logic (`if request.approval_present: not_triggered; else:
HUMAN_REVIEW`) is untouched by this design — applicability filtering
happens entirely in the registry, *before* `evaluate()` is ever called
for a non-applicable request. When `POL-004` *is* applicable, it behaves
byte-for-byte as it does today. This is achieved without amending
`POL-004`'s own text or condition — only by adding a sibling
applicability attribute alongside it, which future implementation, not
this design phase, would add.

---

## 24. Contract Impact Assessment

| Artifact | Classification |
|---|---|
| Permission Broker Foundation contract (Phase 108A-C, module docstring/design principles) | **NORMATIVE AMENDMENT.** Adds the applicability layer (`applicable_execution_classes`, registry-side filtering, `PolicyResult.applicable`, `PermissionBrokerDecision.non_applicable_policy_ids`) — a genuine, additive extension to the frozen Foundation contract, to be authored by 148C.3, not this phase. |
| Autonomy Contract (`docs/V0_2_AUTONOMY_CONTRACT.md`) | **CLARIFICATION.** No `INV-` invariant changes; this makes `NG-008`/`COMP-003`'s already-stated scope (§7) explicit in code — it does not alter what `INV-003` requires. |
| `POL-004` itself (rule text/condition) | **NO CHANGE** to its evaluation logic (§23); a new sibling attribute is additive, not an amendment to the rule's own meaning. |
| Request schema (`PermissionBrokerRequest`) | **NO CHANGE.** Reuses `execution_class`; no new field (§6, §11). |
| Result model (`PolicyResult`, `PermissionBrokerDecision`) | **NORMATIVE AMENDMENT** (additive fields only: `PolicyResult.applicable`, `PermissionBrokerDecision.non_applicable_policy_ids`) — no existing field removed or repurposed. |
| PBPC-001 | **NORMATIVE AMENDMENT (future, not made here).** Once the Foundation applicability layer is frozen and implemented, PBPC-001 would need a v1.2 re-evaluating §8.1's B-1 status against the new Foundation behavior. |
| Phase 109 integration design (`docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md`) | **NO CHANGE.** Already anticipated exactly this ("POL-004 approval where applicable," §7) — this design fulfills that anticipation rather than contradicting it. |
| Interactive Workflow Contract / `IWC-REQ-029` | **NO CHANGE.** Nothing in this design touches Confirmation/Decision Session state (§26). |
| Authority Evaluation / AESIC | **NO CHANGE.** Nothing in this design touches either package (§27). |
| Runtime Enforcement Decision Engine/Coordinator | **NO CHANGE.** Confirmed orthogonal (§28). |

---

## 25. B-1 Closure Path

B-1 is **not** closed by this design. The remaining path:

1. **148C.2 (this phase)** — architectural recommendation frozen as a
   design document. Not a normative contract.
2. **148C.3 — Permission Broker Foundation Policy Applicability Contract
   Freeze** — independently author and freeze the normative contract
   text for the applicability layer (the frozen `applicable_execution_classes`
   values per rule, the `PolicyResult`/`PermissionBrokerDecision`
   additive fields, the fail-closed defaults of §20, the threat model of
   §21) — adversarially reviewed, not accepting this document's own
   claims as an oracle, per this repository's established phase
   discipline (148C.1's own methodology).
3. **Independent verification of the frozen contract** (a 148C.4-
   equivalent phase) — challenging the frozen text before any
   implementation is authorized.
4. **Foundation implementation** (a separately authorized, out-of-scope-
   here phase) — the actual `src/pcae/core/permission_broker_foundation.py`
   change: add `applicable_execution_classes` to `PolicyRule`/
   `MissingHumanApprovalRule`, add registry-side filtering to
   `PolicyRegistry.evaluate_all`, add the two additive result fields,
   add the canonical-`POLICY_IDS`-completeness check at construction.
5. **Independent implementation verification** — live re-evaluation
   confirming the other eleven rules' behavior is byte-for-byte
   unchanged, and `POL-004` now correctly scopes to
   `execution_class ∈ {shell, backend, adapter, rollback}`.
6. **PBPC-001 re-evaluated (v1.2)** against the implemented Foundation —
   re-run the exact request from §8 above against the *new* Foundation;
   confirm whether it now reaches `ALLOW` (given all other applicable
   rules pass) rather than `HUMAN_REVIEW`.
7. **B-1 re-verification** — only after step 6, an explicit phase
   confirms B-1's closure criteria (148C.1 §17) are now met, specifically
   criterion 7 ("repaired PBPC request profile can produce a
   non-`HUMAN_REVIEW` outcome where existing Permission Broker semantics
   legitimately permit it"), which 148C.1 found failing and this design,
   if implemented and verified, would satisfy.

**B-1 remains open until step 7 completes.** Nothing in this document
performs or authorizes any of steps 2-7.

---

## 26. 12-Hard-Block Coverage Implication

This applicability model answers *which of the 12 `POL-` rules run for a
given request*. It does not address, help, or complicate the separate,
larger problem PBPC-001 §8 already disclosed: the other **eleven**
`HARD_BLOCK_REGISTRY` conditions with no `POL-` counterpart at all
operate entirely at the shell-gate/hook layer, outside the `POL-`
registry and outside this design's scope. Those conditions never entered
the Foundation's rule set to begin with, so an applicability layer over
the *existing* twelve `POL-` rules is **neutral** to that centralization
problem — it neither closes nor worsens it. Any future effort to bring
those eleven conditions into the Foundation (`POL-013+`, explicitly out
of scope here and for 148C.2 by the brief) would need its own
applicability classification, for which this design's mechanism (a
frozen `applicable_execution_classes`-style attribute) would be directly
reusable, but that is future work, not claimed as solved here.

---

## 27. Runtime Enforcement Relationship

This applicability design belongs entirely inside the Permission Broker
Foundation (`PolicyRule`/`PolicyRegistry`). No dependency on Runtime
Enforcement (`RuntimeEnforcementDecision`/`RuntimeEnforcementCoordinator`,
`src/pcae/core/backend_invocations.py`) is introduced or required —
independently reconfirmed via `grep`, neither module references the
other, consistent with PBPC-001 §25's existing orthogonality finding.
Runtime Enforcement remains unchanged by this phase.

---

## 28. Confirmation and Authority Boundaries (Preserved)

Preserved unmodified by this design: confirmation ≠ approval; approval ≠
authorization; authorization ≠ permission; permission ≠ capability;
capability ≠ execution; AESIC ≠ approval; AESIC ≠ permission.
`IWC-REQ-029` is not touched — no code path in this design makes Decision
Session state visible to, or consumable by, the Permission Broker, and
none makes a `PermissionBrokerDecision` visible to or consumable by a
Decision Session. Authority Evaluation/AESIC remain disclosure-only;
nothing in this design routes their output into applicability
resolution. No amendment to Chapter 147 or `IWC-REQ-029` is made or
required.

---

## 29. Design Decision (Frozen Recommendation, Not a Normative Contract)

- **Applicability owner:** each `PolicyRule` declares its own frozen
  `applicable_execution_classes` (default `None` = universal); the
  `PolicyRegistry` is the sole enforcement point (§19).
- **Applicability representation:** declarative frozen class attribute,
  a `frozenset[str] | None` over `KNOWN_EXECUTION_CLASSES` values (§11,
  §18).
- **Request classification:** the existing `execution_class` field — no
  new request field (§6, §12).
- **Selection ordering:** applicability resolved before any rule's
  `evaluate()` is called; `POL-006`/`POL-007` (structural validity) are
  themselves universal and always run first in registry order, so
  `execution_class`'s own validity is confirmed before it is ever used to
  resolve another rule's applicability (§20).
- **Evaluation ordering:** unchanged — registry order remains
  `POL-001..012` numeric order for tie-breaking among triggered rules of
  the same decision value (existing `_compose` behavior, untouched).
- **Missing/unknown behavior:** fails toward universal, never toward
  fewer applicable policies (§20).
- **Audit representation:** `PermissionBrokerDecision.non_applicable_policy_ids`
  (additive), alongside existing `evaluated_policy_ids`/
  `triggered_policy_ids` (§15).
- **Versioning:** travels with the Foundation contract itself; no
  separate artifact (§22).
- **Backward compatibility:** every rule except `POL-004` retains
  `applicable_execution_classes = None` (universal) — no existing
  consumer's observed behavior changes except future `pcae push`
  requests' `POL-004` applicability, which is exactly the intended,
  narrowly-scoped effect.
- **Security constraints:** no caller-selectable exclusion mechanism;
  applicability keys on a contract-fixed field (`execution_class`), never
  on caller-discretionary evidence fields (§17, §21).

**Conceptual pipeline this design recommends** (not implemented here):

```
canonical request
      |
validate action_type / execution_class (POL-006) and requested_component (POL-007)
      |
resolve frozen applicable policy set (per-rule applicable_execution_classes)
      |
validate canonical POLICY_IDS completeness (missing-policy fail-closed)
      |
evaluate applicable policies (existing per-rule evaluate())
      |
aggregate decisions (existing _compose, DENY > HUMAN_REVIEW > ALLOW, unchanged)
      |
ALLOW / DENY / HUMAN_REVIEW
```

---

## 30. Push Classification Under This Design

Only after deriving the general model (§3-§20): `pcae push` has, by
contract, `action_type=ACTION_PUSH`, `execution_class=EXECUTION_CLASS_MUTATION`
(PBPC-REQ-033/034) — an existing command-specific mutation (git-tracked
content change), not runtime execution, exactly as PBPC-001's own
Section 4 terminology already frames it ("Git Approval," not "Execution
Approval"). Under the recommended architecture, `POL-004`'s
`applicable_execution_classes = {shell, backend, adapter, rollback}`
would **not** include `mutation` — so `POL-004` would be non-applicable
to `pcae push`, **not because push is push**, but because `POL-004`'s
own governed domain (mediated execution actions reaching
`AWAITING_HUMAN_APPROVAL`) was never the domain git-tracked content
mutation occupies (§5, §7). This is the general rule stated once,
applied to push as one instance of it — not a push-specific carve-out
(§33 of the brief; no `if action_type == "push"` branch appears anywhere
in this design). If a future, independently authorized contract freeze
(148C.3) reached a *different* conclusion about `POL-004`'s intended
domain than this document's re-derivation, `POL-004` would remain
applicable to push and B-1 would remain open under the new model too —
this document does not assume its own conclusion will be adopted
unchallenged.

---

## 31. `simulation_only` Role (Restated)

`simulation_only` should **not**, and under this design does **not**,
influence applicability (§17, §21). It remains exactly what Phase 108A
and PBPC-001 §10.1 already established: a statement about whether the
Foundation's own execution boundary (`COMP-002`) is being asked to carry
out the action — structurally always `True` today, since no such
boundary exists. A real push and a simulated push carry identical
`execution_class=mutation` and therefore reach identical applicability
under this design; no caller gains a weaker policy set by manipulating
`simulation_only`.

---

## 32. Approval Applicability (Restated as the Governing Rule)

```
operation's execution_class is mediated-execution
    (shell / backend / adapter / rollback)?
        |
       yes                              no
        |                                |
POL-004 applies                  POL-004 does not apply
        |
approval present?
   yes / no
```

Applicability is resolved from `execution_class` alone, before
`approval_present` is ever read (§21's "applicability before evidence"
invariant) — never the inverted, prohibited logic ("if approval_present:
POL-004 applies").

---

## 33. `HUMAN_REVIEW` Preservation

Unaffected. When `POL-004` **is** applicable (any real future
`execution_class ∈ {shell, backend, adapter, rollback}` request lacking
approval), it fires exactly as today, producing `HUMAN_REVIEW`, which
remains non-`ALLOW` and continues to abort per PBPC-001 §15
(PBPC-REQ-052) — this design invents no auto-resolution path, no
implicit approval, and no fallback `ALLOW`.

---

## 34. Fail-Closed Design (Cross-Reference)

See §20 for the complete enumerated table. Summary invariant: every
unknown, missing, or malformed condition this design introduces resolves
toward evaluating **more** policies (or, for a missing canonical
`POL-` ID, toward a hard `DENY`), never toward silently evaluating fewer.

---

## 35. Backward Compatibility (Cross-Reference)

See §29's "Backward compatibility" bullet and §20. Every existing
`DEFAULT_POLICY_RULES` rule except `POL-004` retains universal
applicability (`None`) unchanged. No existing consumer's observed
decisions change under this design except a future `pcae push`
integration's `POL-004` outcome — and that integration does not exist in
production today (PBPC-001, 148B/148C/148C.1: "No production Permission
Broker consumption was implemented"), so this design changes zero
observed production behavior as of this phase.

---

## 36. Design Invariants (Frozen)

1. **Applicability before evidence** — whether a policy applies never
   depends on whether its required evidence (`approval_present`,
   `evidence_available`) is present (§17, §32).
2. **Caller cannot weaken policy set** — no `exclude_policies` parameter
   exists anywhere; applicability is registry-enforced from a
   contract-fixed field, never a caller-selectable one (§19, §21).
3. **Unknown fails conservative** — unknown/malformed classification
   never silently produces fewer applicable policies (§20).
4. **Policy semantics unchanged** — applicability does not alter what a
   rule decides when it does apply (§23).
5. **Deterministic selection** — identical broker version + registry +
   request + `execution_class` yields an identical applicable set (§16).
6. **Explainability** — every included/excluded policy has a
   deterministic, inspectable reason (`applicable_execution_classes`
   membership, plus the new `non_applicable_policy_ids` field, §15,
   §29).
7. **No authority synthesis** — applicability cannot create approval,
   authorization, permission, capability, or execution evidence; it only
   determines which existing, unmodified rule questions are asked (§28).

---

## 37. Findings

| ID | Finding | Classification |
|---|---|---|
| F-1 | The Foundation's evaluate-everything mechanism (`PolicyRegistry.evaluate_all`) conflates "single source of authorization" with "every rule is universal" — a Phase 108B implementation simplification, not a frozen design invariant (§3). | Observation |
| F-2 | Exactly one implemented rule, `POL-004`, has a textually demonstrable non-universal intended domain among the twelve; the other five implemented rules are legitimately universal (§4). | Observation |
| F-3 | Applicability is already implicit in frozen upstream text (`NG-008`'s own scope statement, Phase 109's "POL-004 approval where applicable") and was never encoded into the Foundation's mechanism when built — implementation/model incompleteness, not new semantics (§7). | Observation |
| F-4 | `execution_class` is an existing, sufficient, already-validated classification field for `POL-004`'s applicability — no new request field is required (§6, §11). | Observation |
| F-5 | No caller-selectable exclusion mechanism is introduced or required by the selected design; applicability is registry-enforced from policy-owned, frozen metadata (§19, §21). | Observation |
| F-6 | This design, alone, does not and cannot close B-1 — it is architecture only, unimplemented, unfrozen as a normative contract, and unverified (§25). | **BLOCKING for 148D; NOT BLOCKING for this phase's own completion** — this phase's own deliverable is the design, not B-1's closure. |
| F-7 | The 12-hard-block coverage gap (PBPC-001 §8, eleven `HARD_BLOCK_REGISTRY` entries with no `POL-` counterpart) is unaffected — neutral, neither helped nor complicated (§26). | Non-Blocking, unaffected |

No Blocking architectural conflict was found with any frozen contract.
Category C's diagnosis (148C.1) is confirmed, not contradicted: the gap
is a genuine Foundation-mechanism incompleteness, closable by a
principled, narrowly-scoped, additive amendment — not evidence that
Chapter 148's push-integration premise conflicts with the Foundation.

---

## 38. Confirmations

Finding B-1 was **not** closed merely by this design. No Permission
Broker Foundation behavior was changed. No `POL-001..012` policy was
changed. No new push policy was introduced. No caller-selectable policy
bypass was introduced. No approval was fabricated. No `pcae push`
behavior was modified. Interactive Workflow Confirmation remains
independent (§28). Authority Evaluation / AESIC remains disclosure-only
(§28). `HUMAN_REVIEW` remains non-`ALLOW` (§33). No Runtime Enforcement
behavior was changed (§27). Runtime remains Observed, maximum capability
remains observe, and execution availability remains unavailable
(confirmed live, §0 and §39).

---

## 39. Governance Results (This Phase)

```
pcae check              -> passed
pcae health              -> healthy
pcae status coherence    -> coherent
pcae doctor task-memory  -> clean
pcae push check          -> clean, nothing_to_push
pcae runtime inspect      -> Observed / observe / unavailable, 0 plugins, 0 capabilities
                             (unchanged before and after this phase)
telegram runtime          -> loaded, configured, enabled
production source diff    -> git diff --name-only -- src/pcae/ empty
                             (confirmed before this phase's own commits; no src/pcae/**
                             file touched by this phase)
```

---

## 40. Recommended Next Phase

**148C.3 — Permission Broker Foundation Policy Applicability Contract
Freeze.** Independently author and freeze the normative contract text
for the applicability layer this document designs — not accepting this
document's own conclusions as an oracle, per this repository's
established adversarial-verification discipline. At minimum, 148C.3
should: independently re-derive whether `execution_class` is the correct
scoping dimension (§6, §11-§12) or challenge it; independently
re-evaluate whether `POL-004`'s domain is correctly identified as
`{shell, backend, adapter, rollback}` (§5, §30) or find a different
boundary; freeze the exact `PolicyResult`/`PermissionBrokerDecision`
additive field shapes (§15); freeze the fail-closed and security
requirements (§20-§21) as normative `PBPC`-style requirement IDs; and
explicitly re-examine, as 148C.1 §21 already flagged, whether `pcae
push`'s Permission Broker consumption should instead simply remain
deferred until `COMP-003` is genuinely implemented, rather than repaired
around via an applicability layer at all. 148C.3 does not itself
authorize implementation; a further independently-authorized
implementation and verification sequence (§25, steps 4-7) remains
required before B-1 can close. **148D remains not recommended** while
B-1 remains open.
