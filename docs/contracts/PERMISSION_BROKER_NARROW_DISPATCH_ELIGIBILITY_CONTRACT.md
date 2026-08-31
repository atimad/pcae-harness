# PBNDE-001 v1.0 — Permission Broker Narrow Local-CLI Dispatch Eligibility Contract

## Contract identity and status

**Contract:** PBNDE-001
**Version:** 1.0
**Status:** FROZEN
**Frozen by:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 — N-16-3 Narrow-Eligibility
Policy and Contract Implementation.
**Independent verification:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.23.
**Scope:** the production Permission Broker policy semantics for the single
trusted-derived `RUNTIME_DISPATCH_LOCAL_CLI_V1` execution profile — the
versioned amendment to `POL-005`'s canonical statement, the new companion
policy `POL-013`, the profile's trusted-derivation requirement, and the
N-16-6 supply-chain admission interface obligation.
**Related contracts:** PBRD-001 v3.0 (§12a — the normative rule text this
contract's policies implement), PBPA-001 v1.1 (`POL-013` applicability),
RDGO-001 v3.1, RIHAC-001 v2.0, RPAC-001 v1.0,
`docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` (NG-025 annotation),
`docs/PHASE_108_PERMISSION_BROKER_POLICY_RULE_FRAMEWORK.md`.

PBNDE-001 freezes policy semantics only. It does not launch a process, invoke
an external runtime, register an adapter, access credentials, or enable
network/execution. The `RUNTIME_DISPATCH_LOCAL_CLI_V1` profile is
**unsatisfiable in production** — the only production N-16-6 admission
resolver admits nothing.

## 0. Normative language

`SHALL`, `SHALL NOT`, `MUST`, `MUST NOT`, `MAY` are normative. Unknown,
missing, conflicting, malformed, or unverifiable facts fail closed to `DENY`.

## 1. Selected architecture (Option C + D)

Per `.1R.21` §10.6, implemented unchanged:

- **Option C** — `RUNTIME_DISPATCH_LOCAL_CLI_V1` is a distinct trusted-derived
  execution profile that is **not within** POL-005's historical hard-block
  match domain. POL-005's canonical statement gets a versioned amendment
  naming exactly this one carve-out.
- **Option D** — a dedicated conjunctive policy `POL-013` that requires every
  narrow-profile predicate, fails closed on any gap, and **never emits
  `ALLOW` or `HUMAN_REVIEW`**.

Options A (POL-005 semantics become taxonomy-dependent), B (an ALLOW policy
cannot override a POL-005 DENY — `_compose` has no specificity tier / weight /
override channel, code-proven), and E (the rule is contract-expressible now)
are rejected.

## 2. POL-005 canonical-statement amendment (v2 semantics)

`POL-005` (`ExecutionDisabledRule`) **retains its policy ID** — every prior
`causing_policy_ids=("POL-005",)` decision stays interpretable, and NG-025
references need no dual mapping. Its canonical statement is amended under this
versioned change:

> **v1 (superseded statement):** POL-005 is triggered exactly when
> `request.simulation_only is False`; when triggered it returns an
> unconditional `DENY` citing NG-025 / INV-001 / COMP-002, for every
> `action_type` and `execution_class`; unconditionally active by
> construction.
>
> **v2 (current statement):** POL-005 is triggered exactly when
> `request.simulation_only is False` **and** the request is **not** the
> trusted-derived `RUNTIME_DISPATCH_LOCAL_CLI_V1` profile (§3). When
> triggered it returns the identical unconditional `DENY` (NG-025 / INV-001 /
> COMP-002 — the `PolicyResult` body is byte-unchanged). For a
> `RUNTIME_DISPATCH_LOCAL_CLI_V1`-classified request POL-005 returns
> *not-triggered*, meaning ONLY that POL-005 does not categorically preclude
> ordinary Permission Broker evaluation — it is **not** an `ALLOW`. POL-005
> SHALL NOT be deleted, SHALL remain universally applicable (its
> `applicable_execution_classes` stays `None`), and SHALL continue to return
> the unconditional `DENY` for every other non-simulation request of every
> action type and execution class.

The amendment is **MAJOR-class in substance** (it stops matching one class)
and is carried with explicit migration (PBRD-001 v3.0 §16) and independent
verification (`.1R.23`), without a new policy ID.

**The carve-out predicate reads only the trusted-derived marker.** The
production predicate `_is_trusted_narrow_local_cli_dispatch_v1(request)` SHALL
read ONLY `request.runtime_dispatch_context.profile_classification` (equal to
the exact literal) and the construction seal — never a caller field, never a
shape/field inference. The trusted structural validator
(`_valid_runtime_dispatch_request`) runs first (in `_structural_request_failure`)
and has already proven the marker consistent with the bound facts by the time
this predicate is reached.

## 3. `RUNTIME_DISPATCH_LOCAL_CLI_V1` — trusted-derived classification

The marker `RUNTIME_DISPATCH_LOCAL_CLI_V1` SHALL be:

- **derived**, not caller-declared — produced only by the trusted PB
  runtime-dispatch request builder
  (`runtime_dispatch_permission.build_runtime_dispatch_permission_broker_request`)
  from the bound request facts, computed **last**, after every other fact is
  validated and the N-16-6 admission binding resolves;
- **all-or-nothing** — the marker holds only if **every** predicate P1–P21
  (`.1R.21` §7) holds; there is no fuzzy matching, partial credit, or "close
  enough";
- **committed into the request canonical digest** (PBRD-001 v3.0 §5) and
  **recomputed-and-rejected** by `_valid_runtime_dispatch_request`: a marker
  set without a complete profile, or a **complete profile that lacks the
  trusted marker** (a post-construction admission-field forgery), both fail
  closed as a structural `DENY` before POL-005 / POL-013 evaluate;
- **`""` on every legacy request** — a v2.x-shaped request, or any request
  the builder could not fully classify, carries `profile_classification ==
  ""` and receives POL-005's unconditional `DENY`.

There SHALL be no caller-visible self-classification field and no
manufacture-and-escape path: `RuntimeDispatchRequestFacts` is constructible
only behind `_RUNTIME_DISPATCH_REQUEST_SEAL`; the generic
`build_permission_broker_request` rejects any `runtime_dispatch` action or
`runtime_dispatch_context`.

## 4. `POL-013` — Narrow Local-CLI Dispatch Eligibility

A new policy `POL-013` SHALL be registered in the Permission Broker Foundation
policy registry.

**Applicability (PBPA-001 v1.1).** `applicable_execution_classes ==
frozenset({EXECUTION_CLASS_ADAPTER})` — scoped. Within the `adapter` class
its **trigger** is further restricted, inside `evaluate()`, to
`action_type == runtime_dispatch` **and** `request.simulation_only is False`
**and** `runtime_dispatch_context is not None` — mirroring POL-005's own
domain. PBPA-REQ-034 forbids `action_type` as an *applicability* input, so
this narrowing is a **trigger condition, not an applicability filter**;
`POL-013` is a no-op (`not-triggered`) for the dry `adapter_invocation` /
`simulation_only=true` path and for any non-`runtime_dispatch` adapter
request.

**Result vocabulary.**

| Input | `POL-013` result |
|---|---|
| every narrow-profile predicate holds | `triggered=False` (*not-triggered* — contributes nothing; ordinary evaluation of every other policy proceeds) |
| any predicate missing / malformed / unknown-state / unresolvable / of a broader effect class | `triggered=True`, `decision == DENY`, `decision_reason == "narrow_local_cli_dispatch_profile_incomplete"`, `matched_no_go_ids == ("NG-025",)`, `matched_invariants == ("INV-001",)`, `matched_component_ids == ("COMP-002",)`; the remediation string names the unsatisfied predicate id(s) |
| not a truthful, sealed, non-simulation `runtime_dispatch` request | `triggered=False` |

`POL-013` SHALL NOT return `ALLOW` or `HUMAN_REVIEW` under any input. This is
statically verifiable: `NarrowLocalCliDispatchEligibilityRule.evaluate` has
exactly two return shapes — `_not_triggered(...)` and a `DECISION_DENY`
`PolicyResult`. A `POL-013` `DENY` **reinforces** POL-005 (POL-005 also keeps
its `DENY` match — the classification was not achieved); it does not compete
with it.

**Predicate conjunction.** The single authoritative implementation is
`permission_broker_foundation._narrow_local_cli_dispatch_v1_failed_predicates(request,
*, check_marker)` — pure, fail-closed, reads only trusted-derived /
seal-protected request state. Predicate ids: `P_trusted_builder_seal`,
`P_action_runtime_dispatch`, `P_execution_class_adapter`,
`P_runtime_dispatch_context`, `P_transport_local_cli`,
`P_network_prohibited`, `P_supply_chain_admission`,
`P_human_authority_present`, `P_human_authority_binding_valid`,
`P_attempt_identity`, `P_runtime_target`, `P_filesystem_scope`,
`P_trusted_profile_classification`. The credential / provider / model / shell
/ command-string predicates hold by construction (PBRD-001 §6 defines no such
field) and are structural, not runtime checks.

## 5. Precedence and no-go preservation

- `_compose` precedence `DENY > HUMAN_REVIEW > ALLOW`, fail-closed, with **no**
  specificity tier / weight / override, is unchanged. `POL-013` can only
  contribute nothing or a `DENY`; it can never move the outcome toward
  `ALLOW` beyond "not blocking".
- A `RUNTIME_DISPATCH_LOCAL_CLI_V1` request that clears POL-005 and `POL-013`
  is still subject to POL-001, POL-003, POL-004, POL-006, POL-007, the
  structural request validator, every RE-NOGO-*, and the full composition —
  exactly as today. POL-004 (`adapter` ∈ its applicable set) still emits
  `HUMAN_REVIEW` if `approval_present` is false, and `HUMAN_REVIEW` dominates
  `ALLOW`.
- Human approval is **one predicate among the fourteen checked**, necessary
  and never sufficient, and it does not touch POL-005's match logic or
  `_compose`. The models `if human_approved: ignore POL-005` and `if
  principal in TRUSTED: return ALLOW` are explicitly rejected and not
  expressible in the code.

## 6. N-16-6 supply-chain admission interface

`predicate P_supply_chain_admission` requires `adapter_descriptor_binding` to
carry a resolvable canonical supply-chain admission binding of class
`local_fixed_argv` (`admission_class == ADMISSION_CLASS_LOCAL_FIXED_ARGV`) with
a SHA-256 `admission_record_digest`.

- The admission binding is resolved **only** by the trusted request builder,
  via a `SupplyChainAdmissionResolver` (interface). The resolved values are
  stamped onto the adapter binding by the builder; a caller that pre-sets the
  admission sub-fields on the construction input is rejected
  (`_validate_construction_inputs`).
- The **only production implementation** is
  `_NonAdmittingSupplyChainAdmissionResolver` — it admits nothing for any
  adapter (`admitted=False`, `admission_class == "unadmitted"`). N-16-6's real
  admission store, record schema, and verification are N-16-6 deliverables.
- `_resolve_supply_chain_admission` fail-closes a non-resolver, an exception,
  a non-`SupplyChainAdmissionResult`, or a malformed / admitting-but-wrong-
  shape result to `unadmitted`.

**Test-boundary isolation.** A test may substitute a synthetic admitting
resolver ONLY via the underscore-private, documented-test-only
`_supply_chain_admission_resolver` keyword argument on
`build_runtime_dispatch_permission_broker_request` /
`new_runtime_dispatch_identity` / `canonical_runtime_dispatch_projection`. No
public production parameter can flip an adapter to `admitted`. The synthetic
positive path proves only that the classification *can* be derived
structurally, that POL-005 does not categorically apply to the exact profile,
and that `POL-013` returns *not-triggered* when every predicate holds — the
final composition is still decided by every other policy, and no real
execution occurs.

## 7. Downstream-gate independence

- `POL-013` produces PB eligibility only. It MUST NOT read, reference, or
  carry any Gate-7 (Runtime Enforcement) result or expectation. Gate 7
  receives the PB decision as an input and independently re-validates.
- `POL-013` does not re-authenticate the human, parse FIDO2, or read HPAC
  registries (that is Gate 5's job). It reads `approval_present` and the
  validated projection as inputs. Today `validate_approval` hard-stops on a
  NON_REAL lineage, so no valid `human_authority_binding` for a real request
  can be produced — the production narrow profile is not satisfiable through
  deterministic NON_REAL human authentication.
- A future PB `ALLOW` for such a request still produces **no external effect**
  while `Execution Availability: unavailable` — RDGO-001 v3.1 §11 item 5
  re-reads current capability at Gate 10 entry.

## 8. Attempt-count and decision-lifetime semantics

`one consumed authority → one attempt identity → at-most-once dispatch
attempt` (RDGO-001 §10a / §18; Slice B). A PB narrow-eligible decision is
bound to the exact request digest (14 facts incl. `attempt_id` /
`idempotency_key`) and expires on any change. `POL-013` requires `attempt_id`
and `idempotency_key` present; their consumption is Gate 9's job. `POL-013`
creates no reusable permission — it never emits `ALLOW`.

## 9. NG-025 annotation

`docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` NG-025 ("Execution Boundary
Unavailable") receives an additive canonical-statement annotation (schema
unchanged; parallels the schema-1.1 V-13-3-2 precedent): NG-025 is
unconditionally active for every non-simulation request **except the single
trusted-derived `RUNTIME_DISPATCH_LOCAL_CLI_V1` profile** (PBRD-001 v3.0
§12a; this contract), which is productionally unsatisfiable pending
N-16-4..7. Human override remains `no`. `.1R.21` §38's target
(`RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md`) is a planning-document location
error — that file is the `RE-NOGO-NNN` registry and contains no NG-025; no
`RE-NOGO-*` entry is created to match the mistaken path.

## 10. Versioning and freeze verdict

PBNDE-001 uses contract `MAJOR.MINOR`. v1.0 is the initial freeze. A change to
POL-005's carve-out semantics, to `POL-013`'s result vocabulary (in
particular any path that could emit `ALLOW` or `HUMAN_REVIEW`), to the
predicate conjunction's trust requirements, or to the "no human-approval
override" invariant is incompatible and requires a new MAJOR plus explicit
migration and independent verification. Unknown versions fail closed.

**PBNDE-001 v1.0: FROZEN. POL-005 retains its ID. `POL-013` never emits
`ALLOW` or `HUMAN_REVIEW`. `RUNTIME_DISPATCH_LOCAL_CLI_V1` is unsatisfiable in
production. No execution. Independent verification: Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.23.**
