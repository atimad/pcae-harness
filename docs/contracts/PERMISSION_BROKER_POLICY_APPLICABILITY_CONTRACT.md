# Permission Broker Policy Applicability Contract

## Contract identity and status

**Contract:** PBPA-001
**Version:** 1.1
**Status:** FROZEN (normative contract text; does not close Finding B-1 —
see Section 22, Section 38)
**Frozen by:** Phase 148C.3 — Permission Broker Foundation Policy
Applicability Contract Freeze
**Amended to v1.1 by:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 — N-16-3
Narrow-Eligibility Policy and Contract Implementation. **v1.1 is an additive
amendment** (Section 29 / PBPA-REQ-087 — the first exercise of that clause):
the new canonical policy `POL-013` ("Narrow Local-CLI Dispatch Eligibility",
PBNDE-001 v1.0) is added to the POL-001..012 applicability matrix (now
POL-001..013) with `applicable_execution_classes ==
frozenset({EXECUTION_CLASS_ADAPTER})` (scoped), and PBPA-REQ-062's count is
updated from one to two currently-implemented scoped policies. No existing
row's applicability class is changed; no other contract text changes.
Independent re-verification of the amendment is Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.23.
**Predecessor:** Phase 148C.2 — Permission Broker Foundation Policy
Applicability Model Design (`docs/PHASE_148C.2_PERMISSION_BROKER_FOUNDATION_POLICY_APPLICABILITY_MODEL_DESIGN.md`,
commits `506cd88a`, `a53b0fe9`) — architectural recommendation only, not
binding.

PBPA-001 v1.0 is the sole authoritative contract governing which
registered Permission Broker Foundation `POL-` rules are normatively
applicable to a given canonical `PermissionBrokerRequest`, before those
rules are evaluated. It amends the Permission Broker Foundation contract
(Phase 108A-C) additively. Future implementation phases SHALL cite
PBPA-001 and SHALL NOT reinterpret 148C.2's design prose, or the
Foundation's own frozen design principles, locally.

This is contract text only. **It does not implement the applicability
layer, does not modify `src/pcae/core/permission_broker_foundation.py` or
any other `src/pcae/**` file, does not change current Permission Broker
Foundation behavior, does not change `pcae push` behavior, and does not
close Finding B-1 (148C, Section 8.1 of PBPC-001 v1.1).** Section 43 fixes
the exact preconditions a future implementation phase must satisfy before
implementation is authorized.

Runtime posture, unaffected by this contract:

- State: **Observed**
- Maximum capability: **observe**
- Execution availability: **unavailable**

## 0. Normative language

The key words **SHALL**, **SHALL NOT**, **MUST**, **MUST NOT**, and **MAY**
are normative, with the same meanings PBPC-001 §0 already fixes for this
repository's contract corpus. This contract does not use `SHOULD`: every
mandatory behavior is stated as `SHALL`/`SHALL NOT`.

Every mandatory behavior receives a unique, sequential, stable,
non-reused, independently traceable requirement identifier of the form
`PBPA-REQ-###`. Identifiers are never renumbered or reused across
revisions.

## 1. Purpose

PBPA-REQ-001: This contract SHALL govern deterministic selection of which
registered Permission Broker Foundation policies (`POL-001..012`) are
**applicable** to a valid canonical `PermissionBrokerRequest`, prior to
and independent of those policies' own evaluation of that request's
evidence fields.

PBPA-REQ-002: Applicability, as governed by this contract, SHALL NOT
decide `ALLOW`, SHALL NOT decide `DENY`, SHALL NOT decide `HUMAN_REVIEW`,
SHALL NOT create approval, SHALL NOT create authorization, SHALL NOT
create capability, and SHALL NOT execute anything. It determines only
whether a given policy governs a given request at all — **"policy
applies"** or **"policy does not apply"** — nothing about what that
policy would decide if it did apply.

PBPA-REQ-003: Conformance with PBPA-001, alone, SHALL NOT authorize
implementation, and SHALL NOT close Finding B-1. Section 43 states the
complete precondition set for a future implementation phase; Section 38
states the complete precondition set for B-1's closure.

## 2. Independent Reconstruction Methodology

This contract was authored by direct inspection of primary sources, not
by trusting Phase 148C.2's own design-document prose as an oracle. Every
source below was independently re-read during this phase:
`src/pcae/core/permission_broker_foundation.py` (788 lines, read in full
— request model, decision model, `PolicyRule`/`PolicyResult`,
`PolicyRegistry.evaluate_all`, `_compose`, `PermissionBroker.evaluate`,
`DEFAULT_POLICY_RULES`); `docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`
(PBPC-001 v1.1, full); `docs/PHASE_148C.2_PERMISSION_BROKER_FOUNDATION_POLICY_APPLICABILITY_MODEL_DESIGN.md`
(full — the design this contract freezes or amends); `docs/PHASE_148C.1_PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT_CLARIFICATION_AND_REPAIR.md`
(full — B-1's Category A/B/C/D re-derivation); `docs/verification/PHASE_148C_PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT_INDEPENDENT_VERIFICATION.md`
(full — B-1's original independent verification); `docs/PHASE_108_PERMISSION_BROKER_FOUNDATION.md`,
`docs/PHASE_108_PERMISSION_BROKER_POLICY_RULE_FRAMEWORK.md`,
`docs/PHASE_108_PERMISSION_BROKER_POLICY_COMPOSITION_HARDENING.md`,
`docs/PHASE_108_PERMISSION_BROKER_VERIFICATION_COMPATIBILITY.md` (targeted
— `POL-001..012` origin, composition/precedence design); `docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md`
(full — canonical command-category table, including the "`POL-004`
approval where applicable" text at line 163); `docs/V0_2_AUTONOMY_CONTRACT.md`
(targeted — `INV-001..010`, the canonical execution lifecycle,
`COMP-001..010`); `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md`
(targeted — `NG-008`'s exact condition text at lines 177-190, and the
document's own execution-readiness-decision-point scope statement at
lines 27-32); `docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md`
§5 (lines 278-317, full — Git Approval / Execution Approval separation).

PBPA-REQ-004: Where 148C.2's design prose and these primary frozen
sources conflict, primary evidence SHALL govern this contract's text.
Independent re-verification (Section 3 below) found **no such conflict**
— every claim in 148C.2 §3-§21 checked against primary source in this
phase (the Foundation's module docstring and design principles; `NG-008`'s
exact condition text; the Phase 109 command-category table; PR-compatible
workflow §5's Git/Execution Approval separation) matched the primary text
verbatim or in substance. This contract therefore freezes 148C.2's
selected architecture as normative, not as an unexamined inheritance —
Section 3 records the independent check performed, not merely a citation
of 148C.2's own claim to have performed one.

## 3. Independent Re-Verification of 148C.2's Load-Bearing Claims

PBPA-REQ-005: Before freezing any requirement below, this phase
independently re-confirmed, against primary source, each of the following
claims 148C.2 made. None is accepted merely because 148C.2 asserted it.

| 148C.2 claim | Primary source re-checked this phase | Result |
|---|---|---|
| `PolicyRegistry.evaluate_all` runs all twelve rules unconditionally, no `execution_class` gate | `permission_broker_foundation.py:647-659` (`evaluate_all`), read directly | **Confirmed.** The loop iterates `self._rules` with no request-classification branch. |
| The Foundation's own design principles do not assert "every rule is universal" | `permission_broker_foundation.py:1-34` (module docstring, principles 1-3) | **Confirmed.** Principle 3 ("single source of authorization... no duplicated authorization logic") is about there being one *decision point*, not about every registered rule binding every request; nothing in the docstring states or implies universal applicability. |
| `NG-008`'s own text scopes it to the execution-readiness decision point | `V0_2_EXECUTION_READINESS_NO_GO_GATES.md:27-32` ("`NG-` gates are scoped specifically to the execution readiness decision point — the moment just before a proposed action would move from `READY` to `AWAITING_HUMAN_APPROVAL`") and `:177-190` (`NG-008` condition text: "The action has reached `AWAITING_HUMAN_APPROVAL`") | **Confirmed**, verbatim. |
| Phase 109's command-category table already anticipated conditional `POL-004` applicability | `V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md:163` ("`POL-004` approval where applicable"), and the Git-lifecycle row's "Git approval... not execution approval" text at `:164-167` | **Confirmed**, verbatim; also independently confirmed the Documentation-mutation and Source-mutation rows (`:122-125`, `:137-138`) state the same "Git approval only" disposition. |
| Git Approval and Execution Approval are frozen as non-interchangeable | `V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md:278-317` (§5, "Approval Model") | **Confirmed**, verbatim — "These are never interchangeable" (`:310`). |
| `MissingHumanApprovalRule.evaluate()`'s condition reads only `approval_present`, no `execution_class`/`action_type` check | `permission_broker_foundation.py:416-443`, condition at `:428` (`if request.approval_present:`) | **Confirmed.** No other field is read. |
| `execution_class` is a required, non-optional dataclass field | `permission_broker_foundation.py:141-162` (`PermissionBrokerRequest`) | **Confirmed.** No default value; construction fails (`TypeError`) if omitted. |
| `POLICY_IDS`/`DEFAULT_POLICY_RULES` is a fixed, in-memory tuple, not externally configurable | `permission_broker_foundation.py:577-592` | **Confirmed.** No file/network/environment loading path exists anywhere in the module. |
| An empty registry composes to `DENY` | `permission_broker_foundation.py:680-691` (`_compose`, `if not results:` branch) | **Confirmed.** |
| A malformed/erroring rule result fails closed to `DENY` | `permission_broker_foundation.py:598-629` (`_sanitize_result`) | **Confirmed.** |

PBPA-REQ-006: This independent re-verification finds 148C.2's factual
substrate accurate. This contract's amendments to 148C.2 (Section 5,
Section 21) are therefore refinements of representation and normative
force, not corrections of a primary-source error.

## 4. Scope

PBPA-REQ-007: This contract SHALL apply to the Permission Broker
Foundation's policy-selection mechanism generally (`PolicyRegistry`,
`PolicyRule`, `PermissionBroker.evaluate`) — it is not scoped to `pcae
push` or to any single consumer. Any future consumer of the Foundation
inherits this contract's applicability semantics identically.

PBPA-REQ-008: This contract SHALL NOT: modify `src/pcae/**`; implement the
applicability layer; change current Permission Broker Foundation runtime
behavior; change `pcae push` behavior; close Finding B-1; fabricate or add
approval; change `HUMAN_REVIEW` semantics; add `POL-013+`; introduce
execution; authorize Chapter 148D; or amend any other frozen contract
beyond the additive relationship Section 40 states.

## 4A. Applicability vs. Evaluation

PBPA-REQ-009: This contract SHALL freeze the following two questions as
categorically distinct and SHALL NOT permit any future implementation to
merge them:

- **Applicability:** *Does this policy govern this operation profile at
  all?* A function of the request's structural classification only
  (Section 8).
- **Evaluation:** *Given that the policy governs the operation, what
  decision does it produce?* A function of the request's evidence fields
  (`approval_present`, `evidence_available`, `simulation_only`, etc.),
  exactly as each `PolicyRule.evaluate()` already computes it today,
  unmodified by this contract (Section 25).

PBPA-REQ-010: The following inference is INVALID and SHALL NOT appear in
any conforming implementation, diagnostic, or future contract amendment:

```
approval missing -> therefore POL-004 is not applicable
```

PBPA-REQ-011: The following ordering is the only VALID conceptual
sequence and SHALL be preserved by any conforming implementation:

```
operation classification
      |
does POL-004 apply? (a function of execution_class alone)
      |
     yes
      |
is approval present? (a function of approval_present alone)
      |
   decision
```

PBPA-REQ-012: Evidence fields (`approval_present`, `evidence_available`)
SHALL NOT determine whether a policy's requirement exists (applicability);
they SHALL only be read once applicability has already been resolved
(evaluation). This is the governing anti-inversion rule Section 19
restates specifically for `POL-004`.

## 5. Applicability Result Model

PBPA-REQ-013: This contract SHALL NOT add a fourth value to the broker's
top-level `PermissionBrokerDecision.decision` enumeration. `DECISION_ALLOW`,
`DECISION_DENY`, and `DECISION_HUMAN_REVIEW` (`permission_broker_foundation.py:46-50`)
remain the only three values, consistent with PBPC-001 §10
(PBPC-REQ-032)'s existing prohibition on a second decision taxonomy — a
new broker-level `NOT_APPLICABLE` value would risk exactly the taxonomy
drift that prohibition exists to prevent, and no primary source
demonstrates a need for it that a per-policy field cannot satisfy.

PBPA-REQ-014: The applicability distinction SHALL instead be represented
at the **per-policy** level, one layer below the broker decision: a
`PolicyResult`-level field, `applicable: bool`, distinct from and
evaluated strictly before `triggered`. The canonical values are
`APPLICABLE` (`applicable=True`) and `NOT_APPLICABLE` (`applicable=False`).

PBPA-REQ-015: A policy with `applicable=False` SHALL NOT be passed to its
own `evaluate()` method for this request — applicability filtering SHALL
occur in the registry (`PolicyRegistry.evaluate_all`), before any
non-applicable rule's `evaluate()` is invoked (Section 24). A
non-applicable rule therefore never produces a `triggered=True/False`
judgment about a request it was never meant to judge, and `triggered` for
a non-applicable policy SHALL always read as the registry's own default
`not-run` state, never as a synthesized `False`.

PBPA-REQ-016: `NOT_APPLICABLE` SHALL NOT be treated as, collapsed into, or
diagnostically presented as equivalent to `ALLOW`. A non-applicable policy
has expressed no permission opinion about the request; it is silent, not
permissive. `PermissionBrokerDecision`'s existing `ALLOW` semantics
(`_compose`'s "nothing triggered" branch, `permission_broker_foundation.py:727-736`)
are unaffected in meaning — only in which policies were candidates for
triggering it (Section 25).

## 6. Selected Hybrid Architecture

PBPA-REQ-017: This contract freezes 148C.2's selected architecture — a
hybrid of Candidate A (policy-owned applicability) and Candidate B
(declarative applicability metadata) — as normative, having independently
re-verified (Section 3) that no primary-source basis exists to select a
different candidate among the four 148C.2 compared.

PBPA-REQ-018: Each `PolicyRule` SHALL declare a frozen class-level
attribute:

```
applicable_execution_classes: frozenset[str] | None
```

with default `None`, meaning **universal** (applicable to every
`execution_class`) — the value every one of today's twelve rules would
carry unless this contract explicitly scopes it narrower (Section 17).

PBPA-REQ-019: **Declarative metadata** (Candidate B's representation)
defines the frozen domain a policy's applicability predicate may draw
from — in this contract's scope, exactly the `execution_class` dimension,
no other. **Policy-owned predicate** (Candidate A's ownership principle)
means the applicability question is answered by logic that lives with the
policy's own class, not by an external table maintained separately from
the rule it describes; under this hybrid, that "logic" is the trivial,
frozen set-membership test defined once by this contract (Section 14),
not an arbitrary per-rule method body.

PBPA-REQ-020: This design combines Candidate A's encapsulation and
backward-compatible default with Candidate B's superior auditability and
contract clarity (148C.2 §18's comparison table, independently confirmed
in Section 3 above as resting on accurately re-derived facts).

## 7. Applicability Authority

PBPA-REQ-021: The **policy** declares its own applicability metadata
(`applicable_execution_classes`); the **`PolicyRegistry`** — never the
caller, never the request, never the command layer, never a
per-consumer parameter — is the sole component that reads and enforces
that metadata during `evaluate_all`.

PBPA-REQ-022: No conforming implementation SHALL expose, on
`PermissionBroker`, `PolicyRegistry`, or any future Command Evidence
Adapter, a caller-supplied exclusion parameter of the shape:

```
broker.evaluate(request, exclude_policies=["POL-004"])
```

or any semantically equivalent mechanism (an allow-list parameter, a
policy-tag filter, an environment variable, a request field naming
specific policies to skip). A caller MAY only ever influence applicability
indirectly, by supplying a truthful `execution_class` value — and
`execution_class` is not caller-discretionary per request under this
contract; it is fixed per integration point by the consuming contract
(e.g. PBPC-REQ-034 fixes `pcae push`'s `execution_class` to
`EXECUTION_CLASS_MUTATION`), not chosen ad hoc by the calling code at
request-construction time (Section 9).

PBPA-REQ-023: The applicability owner for the purposes of this contract
is: **Foundation-declared, registry-enforced.** No caller-owned
applicability model is authorized.

## 8. `execution_class` Contract

PBPA-REQ-024: The field bound by this contract is exactly
`PermissionBrokerRequest.execution_class`
(`permission_broker_foundation.py:154`) — no new request field is
introduced or required.

PBPA-REQ-025: Valid values are exactly `KNOWN_EXECUTION_CLASSES`
(`permission_broker_foundation.py:127-134`): `EXECUTION_CLASS_NONE`
(`"none"`), `EXECUTION_CLASS_MUTATION` (`"mutation"`),
`EXECUTION_CLASS_SHELL` (`"shell"`), `EXECUTION_CLASS_BACKEND`
(`"backend"`), `EXECUTION_CLASS_ADAPTER` (`"adapter"`),
`EXECUTION_CLASS_ROLLBACK` (`"rollback"`). This contract adds no seventh
value.

PBPA-REQ-026: Current meaning, unchanged by this contract: the structural
category of capability an action requires — a closed, six-value
vocabulary already validated by `POL-006` (`UnknownCapabilityRule`,
`permission_broker_foundation.py:478-522`) independent of any
applicability concern.

PBPA-REQ-027: Source of truth: the request's own `execution_class` field,
as constructed by the calling Command Evidence Adapter (or equivalent) at
request-construction time. This contract does not introduce a second,
independently-derived source of `execution_class` truth.

PBPA-REQ-028: Normalization: none beyond existing membership validation
(`POL-006`) — values are compared by exact string equality against
`KNOWN_EXECUTION_CLASSES`; no case-folding, aliasing, or fuzzy matching is
authorized.

PBPA-REQ-029: `execution_class` is REQUIRED on every `PermissionBrokerRequest`
(the dataclass field carries no default — `permission_broker_foundation.py:154`);
"absent" is therefore not a runtime-reachable state — construction itself
fails before any policy runs. This contract does not change that.

PBPA-REQ-030: Unknown-value and compatibility behavior for
`execution_class` are governed by Section 10 and Section 11 respectively.

## 9. Classification Authenticity

PBPA-REQ-031: This contract's applicability mechanism SHALL NOT be
defeatable by a caller labeling a dangerous operation with a weaker
`execution_class` to reduce its applicable policy set. The following
threat is explicitly in scope: `dangerous operation -> caller labels it
as a weaker class -> fewer policies run`.

PBPA-REQ-032: Responsibility for establishing `execution_class` truthfully
is **not** unconditionally caller-discretionary. It is governed by the
same trust boundary the Foundation already relies on for every other
request-classification field (`action_type`, `task_id`,
`evidence_available` — none of which is independently re-verified by the
broker beyond structural membership checks, PBPC-001 §2/§28 reconfirmed).
Concretely: a conforming production consumer's `execution_class` value
SHALL be **fixed by the consuming contract that governs that integration
point** (the PBPC-001 precedent: PBPC-REQ-034 fixes `pcae push`'s value as
a normative requirement, not a per-request caller choice), not supplied
ad hoc by the command implementation at invocation time. A future
integration that has no such governing contract fixing its
`execution_class` value does not conform to this contract's classification-
authenticity requirement and SHALL NOT be authorized to consume the
Foundation until one exists.

PBPA-REQ-033: This is a combination of contract-fixed classification (the
primary mechanism, PBPA-REQ-032) and trusted-adapter derivation (the
existing Command Evidence Adapter pattern, PBPC-001 §11/§14) — not raw,
unconstrained caller declaration. It is not validated against
"operation facts" by any new independent mechanism in this contract;
Section 10 defines the one cross-field consistency check this contract
does require.

## 10. Classification Binding

PBPA-REQ-034: This contract freezes the following relationship: a
request's `execution_class` determines `POL-004` applicability
(Section 17); a request's `simulation_only` determines nothing about
applicability (Section 20); a request's `action_type` is a finer-grained
classification than `execution_class` and is not itself an applicability
input under this contract (148C.2 §6 found it unnecessary — `execution_class`
alone already suffices and is the smaller, already-validated dimension).

PBPA-REQ-035: If a future contract or implementation ever introduces a
request whose `action_type` and `execution_class` combination is
inconsistent with any contract-fixed mapping that governs that action
type (e.g. an `action_type` that a governing contract fixes to one
`execution_class` appearing with a different one), that request SHALL
fail closed — treated as a structurally invalid request under `POL-006`'s
existing validation scope, not silently accepted with either field's
value trusted. This contract does not itself define an
`action_type -> execution_class` mapping table (no primary source
requires or would benefit from one beyond what PBPC-REQ-033/034 already
fix for `pcae push` specifically); it fixes the fail-closed principle a
future mapping-bearing contract SHALL follow if one is introduced.

## 11. Unknown, Missing, or Malformed Classification

PBPA-REQ-036: An unknown `execution_class` value (not a member of
`KNOWN_EXECUTION_CLASSES`) is already, and remains, a `POL-006` DENY
(`permission_broker_foundation.py:506-521`) — `POL-006` is itself
universal (Section 15) and always runs before applicability resolution is
meaningful for any other rule (Section 24), so no other rule's
applicability is ever resolved against an unvalidated `execution_class`.

PBPA-REQ-037: A missing `execution_class` is not a runtime-reachable state
(PBPA-REQ-029); no applicability behavior is defined for it because
construction fails first.

PBPA-REQ-038: Malformed applicability *metadata* (a value in a policy's
`applicable_execution_classes` set that is not itself a member of
`KNOWN_EXECUTION_CLASSES`) SHALL be treated, for that policy, as if
`applicable_execution_classes` were `None` (universal) — malformed
metadata SHALL fail toward evaluating **more** policies, never fewer.

PBPA-REQ-039: An empty `applicable_execution_classes` frozenset (a policy
declaring itself applicable to no class at all) is a DEGENERATE and
SUSPICIOUS configuration SHALL be treated identically to malformed
metadata (PBPA-REQ-038) — universal, not "never applicable" — since a
legitimately unconditional non-applicability is better expressed by
removing the policy's registration entirely (out of this contract's
scope) than by an empty-set sentinel that could be mistaken for an
authoring error. This is the general fail-closed principle
(PBPA-REQ-070) applied to the degenerate-empty-set case specifically.

## 12. Backward-Compatible Legacy Requests

PBPA-REQ-040: No existing or future consumer that lacks
applicability-aware classification SHALL silently receive a weaker
policy set merely because this contract's applicability layer exists.

PBPA-REQ-041: The canonical mechanism achieving PBPA-REQ-040 is
PBPA-REQ-018's default: every policy's `applicable_execution_classes`
defaults to `None` (universal) unless this contract explicitly narrows it
(Section 17 narrows exactly one: `POL-004`). A rule that is not
explicitly scoped continues to evaluate on every request, identically to
today's `PolicyRegistry.evaluate_all` behavior, for every consumer,
classified or not.

PBPA-REQ-042: No production Permission Broker consumption currently
exists (PBPC-001, reconfirmed 148B/148C/148C.1/148C.2: "No production
Permission Broker consumption was implemented"). This contract therefore
changes **zero observed production behavior** as of this phase — the
"legacy consumer" scenario PBPA-REQ-040 protects against is, today,
hypothetical; the requirement is frozen prophylactically for the first
real consumer(s), not because any currently-running consumer would be
affected.

## 13. Policy Metadata

PBPA-REQ-043: The minimum applicability metadata this contract requires
per policy is exactly:

```
applicable_execution_classes: frozenset[str] | None
```

No `policy_id` duplication is required in the metadata (the owning class
already carries `policy_id`, `permission_broker_foundation.py:355`); no
separate `applicability_version` field is introduced (Section 29 — it
travels with the Foundation contract version, no separate artifact).

PBPA-REQ-044: **Absent metadata** (a `PolicyRule` subclass that does not
override the base class's `applicable_execution_classes = None`) means
universal — identical, not merely similar, to the explicit `None` case.

PBPA-REQ-045: **Malformed metadata** is governed by PBPA-REQ-038/039.

PBPA-REQ-046: **Duplicate metadata** is not structurally reachable: one
frozen class attribute belongs to exactly one `PolicyRule` subclass; there
is no separate, independently mutable mapping in which two conflicting
definitions for the same `policy_id` could exist (Section 23 addresses
duplicate *policy registration*, a different failure mode).

PBPA-REQ-047: **Unknown class in metadata** is governed by PBPA-REQ-038.

PBPA-REQ-048: **Empty applicability set** is governed by PBPA-REQ-039.

PBPA-REQ-049: A canonical representation for "genuinely, permanently
universal, explicitly stated rather than merely defaulted" is NOT
introduced as a separate value from `None` in this contract — 148C.2's
own finding (§20, restated and re-verified Section 3) is that eleven of
twelve rules are universal via the unexercised default, and no primary
source demonstrates a need to distinguish "universal by default" from
"universal by explicit declaration." A future amendment MAY introduce an
explicit `ALL` sentinel if a demonstrated need for that distinction
arises; none exists today.

## 14. Policy-Owned Predicate

PBPA-REQ-050: The conceptual interface this contract freezes is:

```
resolve_applicability(policy: PolicyRule, request: PermissionBrokerRequest) -> bool
    # returns True (APPLICABLE) iff
    #   policy.applicable_execution_classes is None
    #   or request.execution_class in policy.applicable_execution_classes
```

This is a specification of behavior, not implementation syntax; a future
implementation phase chooses the exact code shape.

PBPA-REQ-051: The predicate SHALL be pure: a deterministic function of
`(policy.applicable_execution_classes, request.execution_class)` only.

PBPA-REQ-052: The predicate SHALL be side-effect free: no mutation of
`request`, `policy`, the registry, or any external state.

PBPA-REQ-053: The predicate SHALL be request-bound: it reads only fields
of the specific request being resolved, never global or ambient state.

PBPA-REQ-054: The predicate SHALL be policy-version-bound: its behavior
for a given policy is entirely determined by that policy's own frozen
`applicable_execution_classes`, not by any other policy's state or by
evaluation order.

PBPA-REQ-055: The predicate SHALL be independently testable: callable and
assertable against a `(policy, request)` pair in isolation, without
constructing a full `PolicyRegistry` or `PermissionBroker`.

PBPA-REQ-056: The predicate SHALL NOT depend on: environment state
unrelated to the request; the current clock (no contract-authorized
temporal applicability input exists in this contract); network access;
random values; or mutable global configuration.

## 15. Universal Policies

PBPA-REQ-057: A policy is **universal** under this contract when its
`applicable_execution_classes` is `None`. Section 17 identifies which of
the twelve currently-registered policies are universal.

PBPA-REQ-058: Universal policies are NOT required to enumerate every
current or future `execution_class` value manually. `None` is the
canonical universal representation; requiring explicit enumeration would
create an unsafe default under which a newly introduced `execution_class`
(Section 30) could silently fall outside every universal policy's
enumerated set — exactly the "new class receives no policies" danger
Section 30 forbids.

## 16. Scoped Policies

PBPA-REQ-059: A policy is **scoped** under this contract when its
`applicable_execution_classes` is a non-`None`, non-empty frozenset. For
each scoped policy, this contract SHALL record: the allowed execution
classes; the applicability rationale; the contract/primary-source
justification; and, per PBPA-REQ-030/Section 30, that new execution
classes do NOT automatically become applicable to a scoped policy merely
by being introduced (a scoped policy's applicability set is a frozen,
explicit enumeration — extending it to cover a new class requires an
explicit contract amendment, not silent inclusion). This is the
security-sensitive default PBPA-REQ-095 states generally: new operation
classes are never silently exempted from a policy that would otherwise
need to consider them; whether a *scoped* policy needs to consider a
*new* class is a judgment a future amendment SHALL make explicitly, not
one this contract pre-answers by default inclusion.

## 17. `POL-001..012` Applicability Matrix

PBPA-REQ-060: The following matrix is normative. Every row was
independently re-derived from primary source during this phase (Section
3), not copied from 148C.2's own table without re-verification.

| Policy | Frozen meaning | Applicability class | `applicable_execution_classes` | Universal/scoped | Source justification |
|---|---|---|---|---|---|
| POL-001 | Missing Active Task (`MissingActiveTaskRule`, `permission_broker_foundation.py:367-389`) | Any action requiring an active task contract | `None` | **Universal** | `evaluate()` reads only `request.task_id`; no `execution_class`/`action_type` condition anywhere in the rule (confirmed by direct reading, Section 3). `NG-001`'s own text carries no operation-class exception. |
| POL-002 | Task Outside Scope (stub, not implemented) | Any action requiring task-scope validation | `None` | Universal (moot; `StubPolicyRule`, never triggers) | No field checked yet; no basis to scope a rule that performs no check. |
| POL-003 | Missing Evidence (`MissingEvidenceRule`, `:392-413`) | Any action a decision is requested for at all | `None` | **Universal** | `evaluate()` reads only `request.evidence_available`; no operation-class condition. `INV-009` ("missing evidence results in denial") carries no operation-class exception. |
| POL-004 | Missing Human Approval (`MissingHumanApprovalRule`, `:416-443`) | Mediated-execution actions specifically | `{EXECUTION_CLASS_SHELL, EXECUTION_CLASS_BACKEND, EXECUTION_CLASS_ADAPTER, EXECUTION_CLASS_ROLLBACK}` | **Scoped** — see Section 18 | `NG-008`'s own condition text ("the action has reached `AWAITING_HUMAN_APPROVAL`") ties it to the generic mediated-execution lifecycle (`COMP-003`); the Phase 109 command-category table's "`POL-004` approval where applicable" and its Git-lifecycle row's "Git approval... not execution approval" independently corroborate this scope (Section 3). |
| POL-005 | Execution Disabled (`ExecutionDisabledRule`, `:446-475`) | Whether the request claims the Foundation's own execution boundary would carry it out | `None` | **Universal** (self-limiting *trigger* condition, not narrowed *applicability* — see Section 20) | `evaluate()` reads only `request.simulation_only`; every request is a candidate for this question regardless of operation class — it asks "does this claim execution capability the Foundation lacks," a question meaningful for every request. |
| POL-006 | Unknown Capability (`UnknownCapabilityRule`, `:478-522`) | Structural validity of `action_type`/`execution_class` themselves | `None` | **Universal, and never subject to applicability filtering by any future rule scoped on `execution_class`** (Section 24) | Must run before `execution_class` can be trusted for any other rule's applicability resolution — a precondition for applicability to be meaningful at all. |
| POL-007 | Unknown Component (`UnknownComponentRule`, `:525-548`) | Structural validity of `requested_component` | `None` | **Universal** | Same structural-precondition reasoning as `POL-006`; reads `requested_component` only. |
| POL-008 | Emergency Stop Active (stub) | Would gate every action once `COMP-009` exists | `None` | Universal (moot; stub) | `INV-007` ("overrides every other authorization") is definitionally global — an emergency stop cannot be operation-class-scoped without contradicting its own invariant. |
| POL-009 | Audit Unavailable (stub) | Would gate any action requiring a durable audit artifact | `None` | Likely universal once implemented (moot; stub) | `INV-005` ("every execution decision produces an audit artifact") states no operation-class exception. |
| POL-010 | Rollback Unavailable (stub) | Would gate actions requiring rollback readiness | **UNRESOLVED** — plausibly scoped, not decided | Moot; stub; **out of scope for this contract** | `INV-006` plausibly implies a read has nothing to roll back, but designing this policy's eventual applicability is explicitly deferred to whatever future phase implements `COMP-008` — this contract does not decide it now (consistent with 148C.2 §2, re-affirmed). |
| POL-011 | Unknown Backend (stub) | Would gate `execution_class=backend` requests specifically | **UNRESOLVED** — plausibly scoped to `{EXECUTION_CLASS_BACKEND}`, not decided | Moot; stub; **out of scope for this contract** | The rule's own name implies a backend-identity check has no meaning outside `execution_class=backend`; deferred to the implementing phase per PBPA-REQ-061. |
| POL-012 | Unknown Adapter (stub) | Would gate `execution_class=adapter` requests specifically | **UNRESOLVED** — plausibly scoped to `{EXECUTION_CLASS_ADAPTER}`, not decided | Moot; stub; **out of scope for this contract** | Same reasoning as `POL-011`, for `adapter`. |
| POL-013 *(v1.1 — Phase ...1R.22, N-16-3)* | Narrow Local-CLI Dispatch Eligibility (`NarrowLocalCliDispatchEligibilityRule`, PBNDE-001 v1.0) — the conjunctive companion to POL-005's `RUNTIME_DISPATCH_LOCAL_CLI_V1` carve-out | The runtime-dispatch / `adapter` policy surface | `frozenset({EXECUTION_CLASS_ADAPTER})` | **Scoped** | PBNDE-001 v1.0 §4. Applicability is on `execution_class == adapter`; within that class the *trigger* is further restricted inside `evaluate()` to `action_type == runtime_dispatch` **and** `simulation_only is False` **and** `runtime_dispatch_context is not None` — a trigger condition, not an applicability filter (PBPA-REQ-034 forbids `action_type` as an applicability input). `POL-013` is a no-op (`not-triggered`) for the dry `adapter_invocation` / `simulation_only=true` path and for any non-`runtime_dispatch` adapter request. It never emits `ALLOW` or `HUMAN_REVIEW`. |

PBPA-REQ-061: `POL-010`, `POL-011`, and `POL-012` are stub rules
(`POLICY_STATUS_NOT_IMPLEMENTED`) that cannot currently trigger regardless
of applicability (`StubPolicyRule.evaluate` always returns
`triggered=False`, `permission_broker_foundation.py:566-567`). This
contract explicitly declines to freeze their eventual
`applicable_execution_classes` value now — that decision belongs to
whatever future phase implements each stub, informed by this contract's
mechanism but not pre-bound by it. Marking a policy's future scope
"unresolved" here is not a Blocking finding for this contract (Section
45) because no currently-reachable request is affected by an unresolved
stub's eventual scope.

PBPA-REQ-062: **v1.0:** exactly one currently-implemented policy, `POL-004`,
is scoped; the remaining five (`POL-001`, `POL-003`, `POL-005`, `POL-006`,
`POL-007`) are universal. **v1.1 (Phase ...1R.22, N-16-3):** exactly **two**
currently-implemented policies are scoped — `POL-004`
(`{SHELL, BACKEND, ADAPTER, ROLLBACK}`) and `POL-013`
(`{ADAPTER}`, PBNDE-001 v1.0). The five universal policies are unchanged.
POL-005 stays universal (`applicable_execution_classes` remains `None`) — its
`RUNTIME_DISPATCH_LOCAL_CLI_V1` carve-out is a self-limiting *trigger*
condition, not a narrowed *applicability* (Section 20), exactly as the v1.0
matrix already recorded.

## 18. POL-004 Applicability

PBPA-REQ-063: `POL-004`'s frozen applicability set is:

```
POL-004.applicable_execution_classes = frozenset({
    EXECUTION_CLASS_SHELL,
    EXECUTION_CLASS_BACKEND,
    EXECUTION_CLASS_ADAPTER,
    EXECUTION_CLASS_ROLLBACK,
})
```

`EXECUTION_CLASS_MUTATION` and `EXECUTION_CLASS_NONE` are excluded.

PBPA-REQ-064: This scope is derived from a GENERAL rule — "`POL-004`
applies to execution classes that represent mediated execution actions
under the canonical execution lifecycle `NG-008`/`INV-003`/`COMP-003`
govern" — applied uniformly to every `execution_class` value, not from a
push-specific carve-out. No conforming implementation, diagnostic, or
future contract text SHALL encode the inverted, prohibited form:

```
POL-004 does not apply to push
```

as a special case keyed on `action_type` or `requested_capability`. The
general rule (PBPA-REQ-063's frozenset) is the sole authorized mechanism;
any request bearing `execution_class=EXECUTION_CLASS_MUTATION` is
non-applicable to `POL-004` as one instance of that general rule, whether
or not it happens to be a `pcae push` request (Section 32).

PBPA-REQ-065: If a future, independently authorized re-examination of
`POL-004`'s intended domain reaches a different scope conclusion than
PBPA-REQ-063 (a genuine possibility Section 43 requires 148C.4 to
adversarially test, not merely ratify), that re-examination amends this
contract explicitly (Section 41, Section 29) — it does not silently
override PBPA-REQ-063 by implementation fiat.

## 19. Applicability Cannot Depend on Approval Presence

PBPA-REQ-066: `POL-004`'s applicability (whether it runs at all) SHALL be
resolved from `execution_class` alone, before `request.approval_present`
is read for any purpose. This restates PBPA-REQ-011/012 specifically for
`POL-004`, the one rule to which it currently has practical effect.

PBPA-REQ-067: The following inversion is explicitly prohibited (restating
PBPA-REQ-010): using `approval_present`'s value, directly or indirectly,
to determine whether `POL-004` is in the applicable set for a request.
Such an inversion would let a caller who cannot supply approval evade the
rule that exists precisely to require it — the opposite of the rule's own
purpose.

## 20. `simulation_only`

PBPA-REQ-068: `simulation_only` SHALL NOT influence applicability under
this contract, for any policy. It remains exactly what Phase 108A and
PBPC-001 §10.1 already establish: a statement about whether the
Foundation's own execution boundary (`COMP-002`) is being asked to carry
out the action, not a statement about the requested operation's own
mutating character.

PBPA-REQ-069: `POL-005` (`ExecutionDisabledRule`) is universal in the
applicability sense this contract defines (`applicable_execution_classes
= None`, Section 17) — it is a candidate to trigger on every request. Its
*triggering condition* (`if request.simulation_only:` — a not-triggered
branch, `permission_broker_foundation.py:459-460`) is self-limiting but
this is an evaluation-time fact, not an applicability-time exclusion:
`POL-005` is still asked, and still answers, its real question ("does
this request claim execution capability the Foundation doesn't have?")
for every request; it merely almost always answers "no" today because
every real consumer sets `simulation_only=True` (PBPC-REQ-036). This
contract does not treat `POL-005`'s self-limiting trigger as precedent for
narrowing any policy's *applicability* via `simulation_only` — a request
carrying `execution_class=mutation` and `simulation_only=True` and a
request carrying `execution_class=mutation` and `simulation_only=False`
have identical applicability under this contract; only their evaluation
outcomes may differ.

## 21. Actual Operation vs. Broker Execution

PBPA-REQ-070: This contract distinguishes two facts that SHALL NOT be
conflated by any conforming implementation or diagnostic surface:

- **"The broker itself executes nothing"** — a statement about the
  Permission Broker Foundation's own implementation status (`COMP-002`
  `not_implemented`); this is what `simulation_only=True` currently means
  for every request, structurally, because no execution boundary exists.
- **"The requested operation is non-mutating"** — a statement about the
  semantics of the action being requested, independent of whether any
  broker component would carry it out.

PBPA-REQ-071: `execution_class` (an applicability input, Section 8)
answers the second question. `simulation_only` (never an applicability
input, Section 20) answers the first. A conforming implementation SHALL
NOT infer one from the other, and SHALL NOT allow a caller to weaken
applicability by manipulating `simulation_only` while the operation's real
`execution_class` remains unchanged. This distinction is load-bearing for
any future `pcae push`-equivalent integration, where the broker itself
never executes (`simulation_only=True`, PBPC-REQ-036) while the
*requested* operation (`execution_class=mutation`) is a real, executing
git mutation performed entirely outside the broker by `push.py` — these
are not in tension under this contract; they are the two distinct facts
this section names.

## 22. Required Policy Set

PBPA-REQ-072: This contract does NOT freeze a per-`execution_class`
minimum required policy set as a normative requirement of v1.0. 148C.2's
own text raised this as a candidate (§20 brief reference) but did not
adopt it as part of the selected architecture, and no primary source
demonstrates it is required to achieve this contract's core guarantee
(Section 24's ordering, Section 12's backward-compatibility guarantee,
Section 30's new-class handling). Introducing a required-policy-set
invariant is identified as a candidate future enhancement (Section 41),
not adopted here, to avoid freezing a mechanism beyond demonstrated need.

PBPA-REQ-073: **Missing policy** (the canonical `POLICY_IDS` set,
`permission_broker_foundation.py:592`, is not fully represented in a
constructed `PolicyRegistry`'s rule tuple) SHALL fail closed. A future
implementation SHALL validate, at `PolicyRegistry` construction time, that
every canonical `POLICY_IDS` member is present in the constructed rule
tuple; absence of any canonical ID is a missing-policy condition,
extending today's empty-registry-composes-to-`DENY` behavior
(`_compose`, `permission_broker_foundation.py:680-691`) to "any canonical
ID absent from an otherwise non-empty registry," not only "the whole
registry is empty."

PBPA-REQ-074: **Missing policy** is distinct from, and SHALL NOT be
confused with, **non-applicable policy** (a policy present in the
registry whose applicability predicate returned `False` for this
request's `execution_class`, Section 5). The former is a registry-
construction defect; the latter is an expected, deterministic outcome of
a correctly-configured registry evaluating a specific request. Neither
SHALL be silently dropped from diagnostic output (Section 26).

## 23. Duplicate Applicable Policy

PBPA-REQ-075: If a future `PolicyRegistry` construction were ever given a
rule tuple containing two entries sharing the same `policy_id`, this is a
registry-construction defect, and SHALL fail deterministically —
specifically, a future implementation SHALL reject such a registry at
construction time (extending PBPA-REQ-073's construction-time validation)
rather than silently picking the first, silently picking the last, or
merging their results. This contract does not authorize any of those
three permissive resolutions.

## 24. Applicability Selection Ordering

PBPA-REQ-076: The following ordering is normative and SHALL be preserved
by any conforming implementation:

```
1. validate request (structural type check — already exists, PermissionBroker.evaluate)
2. validate operation classification (POL-006: action_type, execution_class)
3. validate requested_component (POL-007)
4. validate policy registry (canonical POLICY_IDS completeness, PBPA-REQ-073)
5. determine applicability (per-rule applicable_execution_classes resolution, Section 14)
6. verify required applicable policy set (not adopted in v1.0, PBPA-REQ-072 — reserved step)
7. evaluate applicable policies (existing per-rule evaluate(), unmodified, Section 25)
8. aggregate decisions (existing _compose, unmodified, Section 25)
```

PBPA-REQ-077: `POL-006` and `POL-007` (steps 2-3) are themselves universal
(Section 15/17) and are NEVER subject to applicability filtering by any
other rule's scope — their own `execution_class` validity is what makes
step 5's resolution for every other rule meaningful, so they SHALL always
be evaluated, and SHALL always run logically before applicability is
resolved for any rule whose scope depends on `execution_class`.

PBPA-REQ-078: No conforming implementation SHALL evaluate any rule
(step 7) before that rule's applicability (step 5) and the registry's
structural validity (steps 2-4) are resolved.

## 25. Decision Aggregation

PBPA-REQ-079: `PermissionBrokerDecision`'s existing decision values
(`ALLOW`/`DENY`/`HUMAN_REVIEW`) and existing precedence
(`DENY > HUMAN_REVIEW > ALLOW`, `_compose`, `permission_broker_foundation.py:662-736`)
are UNCHANGED by this contract. Only applicable policies' results SHALL
participate in aggregation — a non-applicable policy's absence from
`evaluate()` (Section 5) means it structurally cannot contribute a
`triggered` result to `_compose`'s precedence computation, which is
sufficient to achieve this without any change to `_compose`'s own logic.

PBPA-REQ-080: This contract does NOT redesign broker decision aggregation.
`_compose`'s existing behavior for `DENY`/`HUMAN_REVIEW`/`ALLOW` selection
among triggered rules remains exactly as frozen by Phase 108B/108C.

## 26. Explainability

PBPA-REQ-081: A future implementation's `PermissionBrokerDecision" SHALL
be extended, additively, with fields sufficient to answer "why did
`POL-004` not participate?" without reading source code:

- `applicable_policy_ids: tuple[str, ...]` — every policy resolved
  applicable for this request.
- `non_applicable_policy_ids: tuple[str, ...]` — every policy resolved
  not applicable for this request.
- The existing `evaluated_policy_ids` (`permission_broker_foundation.py:249`)
  SHALL be redefined, by this contract, to mean "every policy that was
  actually passed to `evaluate()`" — i.e. exactly `applicable_policy_ids`
  going forward, since non-applicable policies are never evaluated
  (Section 5) — a clarification of existing terminology, not a removal of
  the field.
- `decision_contributing_policy_ids` — already exists as
  `causing_policy_ids` (`:252`); no rename required.

PBPA-REQ-082: A policy's non-applicability reason SHALL be
deterministically reconstructable from `non_applicable_policy_ids` plus
the policy's own frozen `applicable_execution_classes` and the request's
`execution_class` — no separate free-text `applicability_reason_by_policy`
field is required by this contract, since the reason is always exactly
"`request.execution_class` not in `POLICY.applicable_execution_classes`,"
computable from data already present, and 148C.2's own preference
(§29) was minimal representation, re-affirmed here.

## 27. Auditability

PBPA-REQ-083: Applicability data (PBPA-REQ-081's fields) is **decision
audit data** — part of the returned `PermissionBrokerDecision` object,
consumed synchronously by the calling code within the same process — and
is distinct from a **durable audit artifact** (a persisted record
surviving process exit).

PBPA-REQ-084: This contract does NOT authorize introducing a durable audit
artifact for applicability data. Whether `PermissionBrokerDecision`'s
existing dataclass shape can carry the new fields (PBPA-REQ-081) or
requires additive fields is an implementation-phase decision (Section 43);
either is additive to the existing dataclass, not a breaking change to
any existing field.

## 28. Determinism

PBPA-REQ-085: Given identical Foundation module version, identical
`PolicyRegistry` construction, an identical request, and this contract's
applicability version (frozen with the Foundation contract, Section 29),
the resolved applicable policy set SHALL be identical every time.
Applicability resolution is a pure function of
`(request.execution_class, {rule.applicable_execution_classes for rule in
registry})` with no heuristic, probabilistic, environment-dependent, or
evaluation-order-dependent component. No candidate architecture
considered by 148C.2 or this contract introduces any such dependency.

## 29. Versioning

PBPA-REQ-086: Applicability metadata versions WITH the Permission Broker
Foundation contract itself. No separate applicability-profile-version
artifact, and no separate request-schema version, is introduced by this
contract.

PBPA-REQ-087: Any future change to any policy's `applicable_execution_classes`
value SHALL be treated as a normative Foundation-contract amendment
(a change to this contract, PBPA-001, requiring its own version increment
and — per PBPA-REQ-098 — independent re-verification), not as a routine
implementation detail a future phase may adjust without governance.

PBPA-REQ-088: This satisfies PBPC-001's own established preference ("do
not create a separate artifact/version domain without demonstrated
need," restated from 148C.2 §22) — no such need is demonstrated for a
twelve-rule registry with (currently) exactly one scoped rule and three
unresolved stubs.

PBPA-REQ-089 *(v1.1 — Phase ...1R.22, N-16-3)*: The first exercise of
PBPA-REQ-087. Adding `POL-013` with `applicable_execution_classes ==
frozenset({EXECUTION_CLASS_ADAPTER})` is a versioned amendment (PBPA-001
v1.0 → v1.1) with its own independent re-verification (`.1R.23`), not an
implementation detail. It is **additive**: it registers a new canonical
policy id (POL-013) and its scoped applicability; it changes no existing
row's applicability class, alters no existing behaviour, and touches no
other clause. The Section 17 matrix now covers POL-001..013; PBPA-REQ-062's
count is updated to two currently-implemented scoped policies. The
`PolicyRegistry` construction-time completeness check (PBPA-REQ-073) now
requires POL-013 to be present in any conforming registry.

## 30. New Execution Classes

PBPA-REQ-089: If a future phase introduces a new `execution_class` value
(a seventh member of `KNOWN_EXECUTION_CLASSES`), the following dangerous
default is explicitly REJECTED by this contract: `new class -> not
listed in any scoped policy's set -> no policies apply to it beyond the
universal ones`.

PBPA-REQ-090: This danger is already structurally bounded, not
eliminated, by this contract's architecture: because every currently-
universal policy defaults to `None` (Section 15), a new `execution_class`
automatically remains subject to every currently-universal policy
(`POL-001`, `POL-003`, `POL-005`, `POL-006`, `POL-007`, and the moot
stubs) with no amendment required — only a *scoped* policy's
applicability to a new class is undefined by default (Section 16).

PBPA-REQ-091: A conforming future amendment introducing a new
`execution_class` SHALL, as part of that same amendment, either (a)
explicitly state which currently-scoped policies (in v1.0, `POL-004`)
apply to the new class, or (b) explicitly state that none do, with
justification. Silence on this point in an amendment that adds a new
`execution_class` SHALL be treated as a Blocking gap in that amendment,
not as an implicit "no policies apply."

## 31. Caller Spoofing Threat and Operation-Class Mapping

PBPA-REQ-092: The caller-spoofing threat (a caller chooses
`execution_class` deliberately to reduce its applicable policy set) is
mitigated by PBPA-REQ-032's classification-authenticity requirement:
`execution_class` is contract-fixed per integration point, not
per-request caller discretion. This contract does not introduce a second,
independent mitigation mechanism (e.g. a validator cross-checking
`execution_class` against a general `action_type` mapping) because no
primary source demonstrates today's ten-`action_type`/six-`execution_class`
combination space requires one beyond the per-integration-point contract
fixing already required (PBPC-REQ-033/034 is the existing precedent for
`pcae push` specifically).

PBPA-REQ-093: This contract does NOT define a general, normative
`action_type -> execution_class` mapping covering all ten known action
types. Section 10 (PBPA-REQ-035) states the fail-closed principle a
future mapping-bearing contract SHALL follow if one is introduced; this
contract does not itself introduce that mapping, consistent with 148C.2's
own scope boundary (no new request field, no new validation mechanism
beyond what already exists).

## 32. Push Classification (Non-Binding Illustrative Note)

PBPA-REQ-094: `pcae push` is governed by PBPC-001, not by this contract.
This section is illustrative only and creates no new normative
requirement beyond what Sections 17-19 already state generally. Under
PBPC-001's existing, unamended fixed values (`action_type=ACTION_PUSH`,
`execution_class=EXECUTION_CLASS_MUTATION`, PBPC-REQ-033/034), and under
this contract's Section 18 general rule, a future `pcae push` request
would find `POL-004` non-applicable — not because this contract
special-cases `pcae push`, but because `EXECUTION_CLASS_MUTATION` is
outside `POL-004`'s frozen applicability set (PBPA-REQ-063) as one
instance of that general rule, applied identically to any other request
sharing that `execution_class`. This illustrative note does NOT amend
PBPC-001, does NOT close Finding B-1 (Section 38), and does NOT authorize
any `src/pcae/**` change.

## 33. Security Threat Model

PBPA-REQ-095: The following threats are analyzed; each mitigation SHALL
hold in any conforming implementation.

| Threat | Mitigation |
|---|---|
| **Class spoofing** (caller claims a weaker `execution_class` than the true operation) | PBPA-REQ-032: `execution_class` is contract-fixed per integration point, the same trust boundary already relied on for `action_type`/`task_id`/`evidence_available`. |
| **Action spoofing** (declared `action_type` conflicts with actual operation semantics) | PBPA-REQ-035: any future contract-fixed `action_type <-> execution_class` mapping conflict fails closed under `POL-006`'s existing structural-validity scope. |
| **Simulation spoofing** (`simulation_only` toggled to weaken applicability) | Section 20/21: `simulation_only` is never an applicability input; toggling it has zero effect on the applicable policy set. |
| **Applicability metadata tampering** (`applicable_execution_classes` changed without contract/version update) | PBPA-REQ-087: any such change is itself a normative PBPA-001 amendment, subject to the same code-review/contract-freeze governance as any other Foundation change — not a runtime-mutable value (no dynamic loading mechanism exists, confirmed Section 3). |
| **Missing policies** (a required applicable policy absent from the registry) | PBPA-REQ-073: canonical `POLICY_IDS` completeness check at construction, fails closed. |
| **Duplicate policies** (ambiguous `policy_id` in the registry) | PBPA-REQ-075: rejected at construction, deterministically. |
| **Unknown future classes** (a new `execution_class` accidentally receives no policies) | PBPA-REQ-089/090/091: universal policies remain applicable by default; any amendment introducing a new class must explicitly resolve scoped-policy applicability, silence is Blocking for that amendment. |
| **Downgrade** (an older applicability version used) | PBPA-REQ-086: no separate applicability-version artifact exists to downgrade — it is inseparable from the Foundation module's own version, which is not independently downgradable at runtime. |
| **Direct Foundation invocation** (caller bypasses a higher-level adapter's classification) | Same trust boundary as every other request field today (Section 3's confirmation that no field is independently re-verified beyond structural membership) — this contract introduces no *new* attack surface beyond what already exists for every other request field. |
| **Partial applicability failure** (one policy's applicability predicate errors or cannot classify) | Section 34: fails toward MORE scrutiny (applicability unresolved), never toward silent `NOT_APPLICABLE`. |

PBPA-REQ-096: All threats above have deterministic, fail-closed
resolutions. None is left undefined by this contract.

## 34. Predicate Failure

PBPA-REQ-097: If a policy's applicability predicate (Section 14) raises an
exception, returns a non-boolean value, or otherwise cannot resolve a
determination for a given request, this SHALL NOT silently produce
`NOT_APPLICABLE`. The required behavior is:

```
applicability unresolved
      |
broker evaluation for this request is invalid
      |
no ALLOW
```

Concretely: a future implementation SHALL treat predicate failure using
the Foundation's existing error-vocabulary pattern for rule failures
(`_sanitize_result`, `permission_broker_foundation.py:598-629`) —
converted into a fail-closed `DENY`-equivalent outcome for the whole
evaluation, labeled with the failing policy's own `policy_id`, never
silently treated as if that policy simply did not apply.

## 35. Unknown Policy

PBPA-REQ-098: Applicability metadata referencing a `policy_id` not present
in the canonical `POLICY_IDS` set, or a registry containing an
unsupported/unrecognized policy version, SHALL NOT receive a permissive
fallback. This extends PBPA-REQ-073's construction-time validation: an
unknown policy reference is a registry-construction defect, fails closed.

## 36. Applicability Metadata Integrity

PBPA-REQ-099: Applicability metadata (`applicable_execution_classes`) is
compiled directly into each `PolicyRule` subclass's frozen class
attribute in `src/pcae/core/permission_broker_foundation.py` — the same
file, and the same code-review/contract-freeze governance, as the rule's
own evaluation logic. This contract does NOT authorize storing
applicability metadata in a separately mutable configuration file,
environment variable, database row, or any other external, runtime-
mutable location.

PBPA-REQ-100: No untrusted runtime caller SHALL be able to mutate
applicability metadata. No external mutable configuration dependency is
authorized to weaken any policy's applicable set outside this contract's
own governed amendment process (Section 29, Section 41).

## 37. Human Approval Policy Integrity

PBPA-REQ-101: When `POL-004` **is** applicable (any request with
`execution_class` in `{shell, backend, adapter, rollback}`), it SHALL
behave exactly as `MissingHumanApprovalRule.evaluate()` already behaves
today, unmodified — `HUMAN_REVIEW` if `approval_present` is falsy,
not-triggered otherwise (`permission_broker_foundation.py:427-443`).
Applicability under this contract MAY scope which requests `POL-004`
considers; it SHALL NOT weaken, soften, or auto-resolve `POL-004`'s
behavior for a request it does consider.

## 38. Finding B-1 Status

PBPA-REQ-102: **Finding B-1 (Phase 148C, Blocking; PBPC-001 §8.1) remains
OPEN.** This contract freezes normative text only; it implements nothing.
Freezing this contract does not, by itself, change the actual, currently-
running `PermissionBroker`'s behavior in any way — `POL-004` continues to
evaluate unconditionally on every real request until a future,
independently-authorized implementation phase (Section 43) actually
modifies `src/pcae/core/permission_broker_foundation.py`.

PBPA-REQ-103: The remaining B-1 closure path, restated and made precise
by this contract:

```
148C.2 (design, complete)
      |
148C.3 (this contract, frozen -- normative text only)
      |
148C.4 -- independent adversarial verification of this contract
      |
Foundation implementation (separately authorized -- Section 43)
      |
independent implementation verification
      |
PBPC-001 v1.2 re-evaluation against the implemented Foundation
      |
B-1 independent re-verification and closure
```

No step beyond "148C.3, frozen" is performed or authorized by this
document.

## 39. 12-Hard-Block Coverage

PBPA-REQ-104: This contract answers *which of the twelve `POL-` rules run
for a given request*. It does NOT address, help, or complicate the
separate, larger problem PBPC-001 §8/§18 already discloses: the eleven
`HARD_BLOCK_REGISTRY` conditions with no `POL-` counterpart at all operate
entirely at the shell-gate/hook layer, outside the `POL-` registry and
outside this contract's scope. Freezing an applicability layer over the
*existing* twelve `POL-` rules is neutral to that centralization
problem — it neither closes nor worsens it, and this contract makes no
claim that Chapter 148 is closer to implementation-readiness on that
separate axis.

## 40. Compatibility Review

PBPA-REQ-105: Compatibility classification against every relevant
existing contract/architecture, independently assessed this phase:

| Predecessor | Classification |
|---|---|
| Permission Broker Foundation contract (Phase 108A-C, module docstring/design principles) | **NORMATIVE AMENDMENT (additive).** This contract adds the applicability layer (`applicable_execution_classes`, registry-side filtering, `PolicyResult.applicable`, `PermissionBrokerDecision.applicable_policy_ids`/`non_applicable_policy_ids`) as a genuine, additive extension. No existing Foundation design principle is contradicted (Section 3, PBPA-REQ-005). |
| Autonomy Contract (`docs/V0_2_AUTONOMY_CONTRACT.md`) | **CLARIFICATION.** No `INV-` invariant text changes; this contract makes `NG-008`/`COMP-003`'s already-stated scope explicit in a Foundation-governing contract — it does not alter what `INV-003` requires. |
| `POL-004` itself (rule evaluation logic) | **NO CHANGE.** `MissingHumanApprovalRule.evaluate()`'s own condition (`permission_broker_foundation.py:427-443`) is untouched; only a sibling applicability attribute is added (PBPA-REQ-101). |
| Request schema (`PermissionBrokerRequest`) | **NO CHANGE.** Reuses `execution_class`; no new field. |
| Result model (`PolicyResult`, `PermissionBrokerDecision`) | **NORMATIVE AMENDMENT (additive fields only)** — `PolicyResult.applicable`, `PermissionBrokerDecision.applicable_policy_ids`/`non_applicable_policy_ids` (Section 5, Section 26). No existing field removed or repurposed. |
| PBPC-001 v1.1 | **NOT AMENDED by this contract.** Remains v1.1, Finding B-1 OPEN (Section 38). A future PBPC-001 v1.2 re-evaluation is required only after Foundation implementation (Section 43), not by this contract. |
| Phase 109 command-path integration design | **NO CHANGE; fulfilled.** Already anticipated exactly this ("`POL-004` approval where applicable," independently re-confirmed Section 3) — this contract fulfills that anticipation rather than contradicting it. |
| Interactive Workflow Contract / `IWC-REQ-029` | **NO CHANGE.** Nothing in this contract touches Confirmation/Decision Session state. |
| Authority Evaluation / AESIC-001 | **NO CHANGE.** Nothing in this contract touches either package. |
| Runtime Enforcement Decision Engine/Coordinator | **NO CHANGE.** Applicability resolution is entirely internal to the Permission Broker Foundation (`PolicyRule`/`PolicyRegistry`); independently reconfirmed via source inspection that neither module references Runtime Enforcement (`src/pcae/core/backend_invocations.py`), consistent with PBPC-001 §25's orthogonality finding. |

## 41. Contract Amendment Inventory

PBPA-REQ-106: Artifacts that a future implementation phase will need to
change, beyond this contract itself:

- `src/pcae/core/permission_broker_foundation.py` — add
  `applicable_execution_classes` to `PolicyRule`/`MissingHumanApprovalRule`;
  add registry-side filtering to `PolicyRegistry.evaluate_all`; add the
  additive `PolicyResult`/`PermissionBrokerDecision` fields (Section 5,
  Section 26); add the canonical-`POLICY_IDS`-completeness check at
  registry construction (Section 22, Section 35).
- `docs/PHASE_108_PERMISSION_BROKER_FOUNDATION.md` and sibling Phase 108
  documents — a documentation update reflecting the implemented
  applicability layer (not a normative amendment; those documents are
  historical phase records, not live contracts, per this repository's
  convention).
- `docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`
  (PBPC-001) — a future v1.2, only after Foundation implementation and its
  independent verification (Section 38), re-evaluating whether a
  conformant `pcae push` request now reaches `ALLOW`.

PBPA-REQ-107: No other frozen contract requires amendment. This contract
does not amend more contracts than the minimum Section 40 identifies.

## 42. Requirement Traceability

PBPA-REQ-108: Every normative requirement above traces to one or more of:
Finding B-1 (148C, PBPC-001 §8.1); the 148C.1 Category C
scoping-gap classification; the 148C.2 selected architecture (independently
re-verified, Section 3); Phase 108A-C's Foundation design principles;
`NG-008`/`INV-003`/`COMP-003`; the Phase 109 command-category design; the
PR-compatible workflow §5 Git/Execution Approval separation; a security
requirement (Section 33); or a backward-compatibility requirement
(Section 12). No requirement in this contract lacks a stated source.

## 43. Verification Requirements (for 148C.4)

PBPA-REQ-109: An independent verification phase (148C.4) attacking this
contract SHALL, at minimum, adversarially re-examine, not merely ratify:

- Every entry in the `POL-001..012` applicability matrix (Section 17),
  especially `POL-004`'s scope (Section 18) — 148C.4 SHALL independently
  re-derive whether `{shell, backend, adapter, rollback}` is correct or
  find a different boundary, per this contract's own instruction
  (PBPA-REQ-065).
- Whether `execution_class` is the correct, sufficient applicability
  dimension (Section 8) or whether a different/additional dimension is
  required.
- `execution_class` classification authenticity and the caller-spoofing
  mitigation (Section 9, Section 31, Section 33).
- Action/class mismatch handling (Section 10).
- Simulation spoofing and the broker-execution/operation-semantics
  distinction (Section 20, Section 21).
- Universal/scoped policy semantics and defaults (Section 15, Section
  16).
- Missing-policy and duplicate-policy fail-closed behavior (Section 22,
  Section 23).
- Unknown/future `execution_class` handling (Section 11, Section 30).
- Predicate-failure fail-closed behavior (Section 34).
- Deterministic selection (Section 28).
- Explainability sufficiency (Section 26).
- Backward compatibility for unclassified/legacy consumers (Section 12).
- Decision-vocabulary preservation — confirming no fourth broker-level
  value was introduced (Section 5).
- `HUMAN_REVIEW` preservation (Section 37).
- Compatibility with every contract in Section 40's table, independently
  re-checked, not re-cited.
- Whether `pcae push`'s Permission Broker consumption should instead
  remain deferred until `COMP-003` is genuinely implemented, rather than
  proceeding via this applicability layer at all (148C.1 §21's original
  question, explicitly not foreclosed by this contract).

PBPA-REQ-110: 148C.4 does not itself authorize implementation; a further,
separately authorized implementation and verification sequence (Section
38) remains required before B-1 can close.

## 44. Future Implementation Acceptance Criteria

PBPA-REQ-111: Before an implementation conforming to this contract may be
authorized, and once built, it SHALL demonstrate:

1. Existing consumers (currently: none in production) retain equivalent
   or stricter safe behavior — no observed behavior weakens.
2. Policies are selected deterministically (Section 28).
3. No caller can exclude policies via any parameter or mechanism (Section
   7, PBPA-REQ-022).
4. No caller can weaken the applicable policy set by supplying a false
   `execution_class`, subject to the classification-authenticity trust
   boundary (Section 9).
5. A missing required/canonical policy fails closed (Section 22, Section
   35).
6. Applicability-predicate failure fails closed (Section 34).
7. `NOT_APPLICABLE` is never treated as `ALLOW` (Section 5, PBPA-REQ-016).
8. No implemented policy's evaluation *meaning* changes when it is
   applicable (Section 25, Section 37) — only which requests it is asked
   about changes.
9. `POL-004` still returns `HUMAN_REVIEW` for every applicable request
   lacking `approval_present` (Section 37).
10. An unknown/new `execution_class` cannot yield a weaker-than-today
    policy set for any currently-universal policy (Section 30).
11. All current Permission Broker Foundation tests remain valid, or are
    normatively updated consistent with this contract's additive changes
    only (no test SHALL be weakened to accommodate an implementation that
    does not conform).
12. No runtime capability change accompanies the implementation (Section
    "Contract identity and status," runtime posture).
13. No execution is introduced — the Foundation continues to only decide,
    never execute (unchanged module-level design principle).

## 45. Findings

PBPA-REQ-112: The following findings are recorded by this phase.

| ID | Finding | Classification |
|---|---|---|
| F-1 | Independent re-verification (Section 3) confirmed every load-bearing factual claim in 148C.2's design without finding a primary-source discrepancy. | Observation |
| F-2 | Three stub policies (`POL-010`, `POL-011`, `POL-012`) have plausible but explicitly UNRESOLVED future applicability scope; this contract declines to pre-decide it (Section 17). | Non-Blocking (moot while stub; a future implementing phase for any of these must resolve applicability before, or as part of, implementing the rule itself) |
| F-3 | No trustworthy, general `action_type -> execution_class` mapping is frozen by this contract (Section 31); classification authenticity instead relies on per-integration-point contract-fixing (the existing PBPC-001 precedent). | Observation — sufficient for the currently-known integration point (`pcae push`); a future integration lacking an equivalent fixing contract does not conform (PBPA-REQ-032). |
| F-4 | This contract, alone, does not and cannot close B-1 — it is normative text only, unimplemented, and unverified (Section 38). | **BLOCKING for 148D and for B-1 closure; NOT BLOCKING for this phase's own completion** — this phase's deliverable is the frozen contract, not B-1's closure. |
| F-5 | No caller-selectable exclusion mechanism is introduced by this contract; applicability is registry-enforced from policy-owned, frozen metadata (Section 7, Section 33). | Observation |
| F-6 | The 12-hard-block coverage gap (PBPC-001 §8/§18) is unaffected by this contract — neutral, neither helped nor complicated (Section 39). | Non-Blocking, unaffected |

PBPA-REQ-113: No Blocking architectural or contract conflict was found
between this contract and any other frozen contract (Section 40). F-4 is
Blocking only for B-1's closure and for Chapter 148D, exactly as 148C.2
§37's F-6 was — not for this contract's own successful completion.

## 46. Contract Verdict

**POLICY APPLICABILITY CONTRACT FROZEN — READY FOR INDEPENDENT
VERIFICATION.**

PBPA-001 v1.0 freezes the normative applicability model 148C.2 designed,
independently re-verified against primary source rather than accepted on
148C.2's own authority (Section 3), with zero unresolved Blocking design
findings against the contract's own internal coherence (Section 45).

This verdict does NOT mean:

- Finding B-1 is closed (it is not — Section 38).
- Implementation is authorized (it is not — Section 43).
- `POL-004`'s scope (Section 18) is beyond challenge (148C.4 SHALL
  adversarially re-examine it, per Section 43's explicit instruction, not
  merely ratify it).
- Chapter 148D is recommended (it is not — see below).

## 47. Confirmations

Finding B-1 remains **OPEN**. No Permission Broker Foundation behavior was
changed. No `POL-001..012` meaning was weakened — `POL-004`'s own
evaluation logic is byte-for-byte unmodified (Section 37); only a sibling
applicability attribute is specified, unimplemented. No caller-selectable
policy exclusion was introduced (Section 7). No approval was fabricated.
No `pcae push` behavior was modified (Section 32 is illustrative only,
non-binding on PBPC-001). No PBPC production implementation occurred.
`HUMAN_REVIEW` remains non-`ALLOW` (Section 25). Interactive Workflow
Confirmation remains independent (Section 40). Authority Evaluation/AESIC
remains disclosure-only (Section 40). No Runtime Enforcement behavior
changed (Section 40). No runtime capability was elevated. Runtime remains
Observed, maximum capability remains observe, and execution availability
remains unavailable.

## 48. No Production Source Changes

PBPA-REQ-114: This phase's changes SHALL be limited to: this contract
file (`docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`);
the Phase 148C.3 phase document
(`docs/PHASE_148C.3_PERMISSION_BROKER_FOUNDATION_POLICY_APPLICABILITY_CONTRACT_FREEZE.md`);
`PROJECT_STATUS.md`; `CHANGELOG.md`; `tasks/DONE.md`; the active task
contract; and finalization artifacts
(`.pcae/phase-completion-report.md`, `.pcae/phase-completion-metadata.json`).
No file under `src/pcae/**` SHALL be modified by this phase. This SHALL be
confirmed by `git diff --name-only <pre-148C.3-baseline>..HEAD --
src/pcae/` before this phase is reported complete.

## 49. Recommended Next Phase

**148C.4 — Permission Broker Foundation Policy Applicability Contract
Independent Verification.** 148C.4 SHALL independently re-derive the
applicability model and attack it adversarially per Section 43 — not
accepting this contract's own text as an oracle, following this
repository's established adversarial-verification discipline (148C.1's
methodology, restated by 148C.2 §40, now restated again here). 148C.4
does not itself authorize implementation.

**148D remains NOT recommended** while Finding B-1 remains open.

## 50. Version History

- **v1.0** (Phase 148C.3, this contract). Initial freeze. Independently
  re-verified 148C.2's design against primary source (Section 3); found no
  discrepancy; froze the selected hybrid architecture as normative
  contract text with `PBPA-REQ-001..114`. Does not close Finding B-1.
  Recommended next phase: 148C.4 (independent verification).
