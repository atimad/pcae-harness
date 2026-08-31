# PBRD-001 v3.0 — Permission Broker Runtime Dispatch Extension Contract

## Contract identity and status

**Contract:** PBRD-001  
**Version:** 3.0
**Status:** FROZEN  
**Frozen by:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 — N-16-3 Narrow-Eligibility
Policy and Contract Implementation.
**v3.0 is a MAJOR** (§16): §16 lists *"weakening POL-005 eligibility"* as a
change that "requires a new MAJOR plus explicit migration and independent
verification." The new §12a defines the `RUNTIME_DISPATCH_LOCAL_CLI_V1`
narrow-eligibility rule §12 anticipated, and that rule narrows POL-005's
categorical hard-block match domain. The migration semantics are stated
inline in §16; the mandated independent verification is Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.23. The narrow profile ships **unsatisfiable in
production** (the N-16-6 supply-chain admission binding has no admitting
implementation), so v3.0 introduces no shipped behaviour change: every
truthful non-simulation request that is not the (unsatisfiable) narrow
profile still receives POL-005's unconditional `DENY`.
**Prior MAJOR line (superseded):** PBRD-001 v2.1 (and v2.0). v2.1 was a MINOR
clarification adding the §4 fact 14 representation-equivalence clause; v2.0
changed the mandatory meaning of `human_authority_binding`.
**Supersedes:** PBRD-001 v1.0, v1.1, and **v2.x**. v1.x human-authority
binding semantics are not valid for v2 requests and have no migration; v2.x
request shapes remain parseable under v3.0 but are categorically DENIED
because they carry no `RUNTIME_DISPATCH_LOCAL_CLI_V1` classification (see
§16). The original v1.0 twelve-fact request was independently found
incomplete against RPAC-REQ-025/044/064–068 by Phase 149O.20L.7O.3V.1
(Finding B-149O.20L.7O.3V.1-2): it lacked mandatory `attempt_id` and
`idempotency_key` binding.  
**Scope:** Contract + policy Permission Broker extension for one future real
local-CLI runtime dispatch. v3.0 defines the narrow-eligibility rule and its
companion policy `POL-013` (see PBNDE-001 v1.0); the production policy
semantics live in the Permission Broker Foundation policy registry
(`permission_broker_foundation.py`).  
**Related contracts:** Permission Broker Foundation, PBNDE-001 v1.0,
PBPA-001 v1.1, PBPC-001 v1.2, RPAC-001 v1.0, RIHAC-001 v2.0, RIASC-001 v3.0,
HPAC-001 v2.1, RDGO-001 v3.1.

PBRD-001 v3.0 defines a future PB request/action contract, the
`RUNTIME_DISPATCH_LOCAL_CLI_V1` narrow-eligibility rule (§12a), and the two
additive internal derived fields that carry its trusted evidence. It does not
launch a process, invoke an external runtime, access credentials, or enable
network/execution. POL-005 continues to deny every non-eligible non-simulation
request, and the narrow profile is unsatisfiable in production, so real
dispatch remains denied.

## 0. Normative language and non-equivalence

`SHALL`, `SHALL NOT`, `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY`
are normative. Unknown, missing, conflicting, or unverifiable facts fail
closed.

```text
human approval != PB permission
PB ALLOW != runtime capability
runtime capability != Runtime Enforcement approval
Runtime Enforcement ALLOW != process permission
process permission != dispatch completion
dispatch completion != accepted change
runtime result != task completion
```

## 1. Additive action and execution class

The future PB action is exactly:

```text
action_type = runtime_dispatch
execution_class = adapter
```

The existing `adapter` execution class is reused. No new execution class is
needed: local-CLI runtime dispatch remains a mediated adapter operation, so
PBPA-001's existing `POL-004` applicability to `adapter` remains correct.

`runtime_dispatch` is additive. Existing action types and their mappings are
unchanged.

## 2. Exact action semantics

An `ALLOW` decision for `runtime_dispatch` means only:

> Under the evaluated PCAE Permission Broker policy version, PCAE policy
> permits attempting the one bounded external local-CLI runtime dispatch
> exactly described by this immutable request, subject to every independent
> human-authority, capability, Runtime Enforcement, containment, durable-
> state, and freshness gate.

It SHALL NOT mean or imply:

- a human authorized the invocation;
- the target is available or capable;
- Runtime Enforcement allowed dispatch;
- arbitrary process execution or child-process creation is permitted;
- network egress is permitted;
- filesystem mutation is permitted;
- credential access is permitted;
- output is trusted;
- a change is accepted, promoted, committed, or pushed; or
- the task is complete.

## 3. Local-CLI-v1 effect model

`runtime_dispatch` v1 covers one bounded local external process invocation
for one exact invocation identity, one exact attempt identity, and target.
The external process shall be created only after RDGO-001 gates 1–9
succeed.

It excludes API calls, provider SDKs, network permission, unrestricted shell,
arbitrary child-process trees, multiple dispatches, parallel invocation,
automatic retry, background/unattended work, multi-repository execution, and
credential access.

`network_requirement` SHALL be `false`. The flag is a bound fact, not a
permission. If a target needs network egress, it is not eligible for this
contract.

## 4. Base PB envelope and fourteen immutable binding facts

The future request retains the Foundation envelope/control fields generated
or fixed by the trusted integration point: `request_id`, `timestamp`,
`action_type`, `execution_class`, `requested_component`,
`evidence_available`, `approval_present`, and `simulation_only`.
`requested_resource` and any existing compatible diagnostic fields remain
subject to the Foundation contract. They are not counted among the fourteen
runtime-dispatch subject facts.

For a real local-CLI request, `simulation_only=false`; until POL-005 is
safely evolved under §12, that truthfully produces `DENY`.

**v1.1 change:** two facts, `attempt_id` and `idempotency_key`, are added to
the twelve facts selected in 3U to close Finding B-149O.20L.7O.3V.1-2. This
is an additive, honestly recounted change: the twelve-fact claim from v1.0
is superseded and every reference to "twelve facts" in this contract family
now reads "fourteen facts." No existing fact's meaning, type, source, or
trust owner changed.

| # | Field | Source | Type | Required? | Trust owner | Meaning |
|---:|---|---|---|---|---|---|
| 1 | `invocation_id` | Trusted invocation coordinator | `inv-<32-hex>` | Yes | PCAE coordinator | Exact logical invocation; never runtime-chosen |
| 2 | `attempt_id` | Trusted invocation coordinator | `att-<32-hex>` | Yes | PCAE coordinator | Exact one concrete dispatch try under the logical invocation; never runtime-chosen; new on every retry (RDGO-001 §10a) |
| 3 | `idempotency_key` | Trusted invocation coordinator, per RPAC-REQ-065 | 64-lowercase-hex SHA-256 | Yes | PCAE coordinator | Canonical-content digest of the logical dispatch request, excluding timestamps/attempt-specific facts; identical across safe retries of the same logical request (RDGO-001 §10a) |
| 4 | `repository_identity` | Existing git-root fingerprint helper | 64-lowercase-hex SHA-256 | Yes | Repository context resolver | Repository lineage binding; never a path |
| 5 | `task_id` | Active task contract | non-empty string | Yes | Task lifecycle | Exact task; task A cannot authorize task B |
| 6 | `lifecycle_context` | Active governed lifecycle/session state | closed object: required `phase_id`, conditional `session_id` | Yes; session conditional | Lifecycle/session owner | Phase context and session only when actually session-scoped |
| 7 | `runtime_target_id` | Explicit target selection | exact non-empty ID | Yes | Target selector + registry | No alias or fallback |
| 8 | `adapter_descriptor_binding` | Registry/config preflight | closed object: `adapter_id`, descriptor version/digest, target-config digest. **v3.0:** two additive **internal** sub-fields `admission_record_digest` / `admission_class` carry the N-16-6 supply-chain admission binding — populated ONLY by the trusted request builder from the N-16-6 admission resolver, default empty, never caller input (§12a). | Yes | Runtime Registry/config owner; admission sub-fields: N-16-6 admission resolver via the trusted builder | Stable adapter and configuration identity; plus supply-chain admission evidence |
| 9 | `prompt_hash` | `pcae.prompt-semantic.v1` canonicalizer | 64-lowercase-hex SHA-256 | Yes | Prompt builder | Exact semantic instruction identity |
| 10 | `requested_capability` | Governed invocation request | non-empty capability ID | Yes | Integration contract/coordinator | Capability requested, not capability possessed |
| 11 | `transport_type` | Contract-fixed integration point | const `local_cli` | Yes | PBRD-001 integration | Excludes API/provider transports |
| 12 | `network_requirement` | Target descriptor + static preflight | const `false` | Yes | Registry/preflight owner | Declared lack of network need; grants none |
| 13 | `filesystem_scope_ref` | Governed isolated-worktree/scope owner | immutable ID/digest reference | Yes | Filesystem-scope owner | Declared scope for audit/containment; grants no mutation |
| 14 | `human_authority_binding` | RIHAC-001 v2 validator | closed object; the seven *logical* fields are `approval_id`, `approval_digest`, `authority_projection_id`, `authority_projection_digest`, `authority_contract_version` const `RIHAC-001/2.0`, `proof_validation_digest`, and `request_binding_digest`. **v2.1 (V-4):** a normative equivalent compact representation is permitted — see §4a. | Yes | Human-authority validator | Canonical approval plus freshly validated authority projection; not raw proof, caller claim, seal, or boolean |

`lifecycle_context` and `human_authority_binding` are each one immutable
binding fact despite their closed subfields, exactly as in v1.0. This
preserves that convention while honestly recounting the total as fourteen.

### 4a. `human_authority_binding` representation equivalence (v2.1 — V-4)

The **logical** requirement is unchanged: `human_authority_binding` commits
approval provenance, the authority projection identity and digest, the
`RIHAC-001/2.0` contract version, the proof-validation semantics, and the
request binding. The *permitted canonical representation* is normalized:

> The production `human_authority_binding` MAY be represented as the closed
> 3-tuple `(approval_id, approval_record_digest, validation_evidence_digest)`
> where `validation_evidence_digest` is a single collision-resistant SHA-256
> commitment over the complete RIHAC-001 v2.0 validated-authority projection
> payload, PROVIDED that: (1) `approval_id` and the approval record digest
> are carried directly; (2) every other logical field is deterministically
> committed inside `validation_evidence_digest`, OR structurally enforced
> more strongly than a string (exact-object registry membership for the
> projection identity — `is_trusted_validated_authority_projection`), OR a
> zero-entropy constant (`authority_contract_version` — the RIHAC v2.0 path
> is the only code path); and (3) the request-binding semantic is
> independently re-enforced by recomputation at request-construction time
> (`_expected_subject_scope_binding_digest` + `invocation_id` equality).
> Two authority contexts that differ in any logical field MUST NOT collapse
> to the same 3-tuple — the projection payload keys guarantee this (a
> difference in any logical semantic necessarily changes ≥1 payload key and
> therefore `validation_evidence_digest`).

The logical seven-field security meaning is NOT weakened by production
using a compact representation. The substantive §7 property
(`approval_present=true` set only by successful RIHAC-001 v2.0 validation,
never caller-settable) is preserved: the digest-collapsed form has a single
population path.

## 4a. Attempt/idempotency ownership and construction point

`attempt_id` and `idempotency_key` are minted at RDGO-001 gate 2 (explicit
target selection and request construction), alongside `invocation_id`,
strictly before gate 3 (human authority creation). Both are exclusively
PCAE-owned: the trusted invocation coordinator allocates `attempt_id` from
cryptographically strong random identity and derives `idempotency_key` as a
canonical-content SHA-256 digest per RPAC-REQ-065. Neither may be selected,
overwritten, echoed back, or influenced by the adapter, runtime, provider,
caller payload, or approval producer — the same construction-time trust
rule that already governs the other twelve facts in §5.

## 5. Request construction and immutability

Only a trusted, contract-fixed PCAE integration point may construct this
request. Adapter, runtime, prompt content, environment variables, CLI payload,
or result content SHALL NOT set `execution_class`, `action_type`,
`approval_present`, `evidence_available`, or any of the fourteen facts except
through the explicitly owned source in the table.

Every request SHALL have a canonical digest over the complete Foundation
envelope plus all fourteen facts. A change creates a different request and
invalidates any prior PB or Runtime Enforcement decision. Requests and
decisions are immutable evidence; neither is an authority artifact.

**v3.0 — derived commitments.** Two derived, non-caller commitments are added
inside the runtime-dispatch subject facts and are covered by this canonical
digest: the N-16-6 admission sub-fields on `adapter_descriptor_binding`
(fact 8) are part of the canonical-content digest that produces
`idempotency_key` (fact 3), so a post-construction mutation of the admission
binding yields a different `idempotency_key` and a construction-time rejection;
and `profile_classification` — the `RUNTIME_DISPATCH_LOCAL_CLI_V1` marker
(§12a) — is bound by a stronger mechanism than digest inclusion: the trusted
structural validator recomputes it from the bound facts and fails closed on
any inconsistency (marker present without a complete profile, or a complete
profile without the trusted marker). Neither is a fifteenth logical fact;
both are derived from the existing facts.

## 6. Request exclusions

The v1 request SHALL NOT contain:

- raw credentials, tokens, private keys, secrets, or environment values;
- credential material disguised as a generic resource field;
- mandatory provider or model fields;
- universal provider/model abstractions;
- mandatory budget fields;
- untrusted executable or shell command strings;
- caller-supplied `approved`, `authorized`, `permission`, `pb_allow`, or
  equivalent authority shortcuts; or
- raw approval-artifact content.

Local executable identity is descriptor/config referenced and live-preflight
verified; it is not an arbitrary caller command string in the PB request.

## 7. Approval reference and `approval_present`

PB receives both parts necessary to preserve independent validation:

1. the immutable approval reference (`approval_id`, `record_digest`); and
2. the exact RIHAC-001 v2 validated-authority projection reference/digest and
   its proof/request-binding digests proving gate 5 freshly resolved canonical
   approval and HPAC state for the exact request.

PB SHALL NOT authenticate humans, parse FIDO2 assertions, read HPAC registries,
receive raw proof material, or trust raw approval prose, a caller assertion,
`approval_present`, a public digest, or a copyable object seal. It validates
only the typed projection/reference shape and exact binding to the request;
RIHAC owns fresh authority validation.

Only successful RIHAC-001 v2.0 validation may cause the trusted request builder to
set `approval_present=true`. The boolean is a derived Foundation input for
POL-004; it is not itself authority and is not caller-settable. Missing,
stale, mismatched, consumed, expired, tampered, or unverifiable approval
evidence yields `approval_present=false` or request-construction failure and
can never produce dispatch.

PB evaluation never consumes an approval or HPAC proof. Consumption remains
the RDGO-001 v3.1 gate-9 atomic dispatch-attempt transition; a PB decision is
permission evidence only and is invalidated when its authority projection is
revoked or fails current revalidation.

## 8. HUMAN_REVIEW semantics

Because `execution_class=adapter`, POL-004 remains applicable.

- With a valid `RuntimeInvocationApproval`, gate 5 supplies the only trusted
  basis for `approval_present=true`; POL-004's
  `MissingHumanApprovalRule` is not triggered. PB HUMAN_REVIEW is therefore
  not an automatic second human-approval ceremony for that same valid
  request.
- Without valid approval, POL-004 may produce `HUMAN_REVIEW`. No real
  dispatch occurs. `HUMAN_REVIEW` is not authorization and v1 defines no PB
  mechanism that converts it into dispatch permission.
- Other applicable policies remain free to produce `DENY` or
  `HUMAN_REVIEW`; valid human authority does not suppress them.

Interactive Workflow/CHGR confirmation evidence SHALL NOT be projected into
`approval_present`; only RIHAC-001 validation can satisfy this
runtime-dispatch use.

## 9. Decision composition and precedence

The existing deterministic precedence is unchanged:

```text
DENY > HUMAN_REVIEW > ALLOW
```

All applicable policies are evaluated under PBPA-001. `POL-006` continues to
reject unknown/inconsistent action and class. The decision SHALL preserve
`causing_policy_ids`, `matched_no_go_ids`, applicable/non-applicable policy
IDs, request digest, and policy-version evidence.

PB failure, malformed output, empty/ambiguous composition, unsupported
action/class/version, `DENY`, or unresolved `HUMAN_REVIEW` all mean no real
dispatch.

## 10. Gate independence

PB evaluates policy only after human-authority validation and before Runtime
Enforcement. It SHALL NOT infer any missing gate.

- Valid approval without PB ALLOW -> no dispatch.
- PB ALLOW without valid approval -> no dispatch.
- PB ALLOW with an unavailable target -> no dispatch.
- PB ALLOW without Runtime Enforcement ALLOW -> no dispatch.
- PB ALLOW without established process containment -> no dispatch.

PB decisions expire with any relevant request, approval, repository/task,
target/configuration, prompt, or policy change and SHALL NOT be cached across
such drift. A changed `attempt_id` (a fresh retry pass through gate 2) always
invalidates any prior PB decision even when `idempotency_key` is unchanged.

## 11. Process, filesystem, network, and credential distinctions

`runtime_dispatch ALLOW` is not arbitrary process permission. Executable
identity, arguments, environment, cwd, child-process policy, resource limits,
and supervision belong to Shell Gate or equivalent process containment.

`runtime_dispatch ALLOW` is not filesystem-mutation permission. Existing
mutation governance and isolated-worktree scope remain separately binding.

`runtime_dispatch ALLOW` grants no network permission. Local-CLI v1 requires
`network_requirement=false`; API/provider dispatch remains blocked pending a
Network Egress Permission Architecture.

`runtime_dispatch ALLOW` grants no credential access. Credential architecture
is future work and is not a hidden subfield of this action.

## 12. POL-005 evolution boundary

POL-005 (`ExecutionDisabledRule`) is unchanged in production by this freeze.
It remains universal and denies every truthful non-simulation request,
including `runtime_dispatch`.

A future implementation may make `runtime_dispatch` eligible only after all
of the following are separately implemented and independently verified:

1. the `runtime_dispatch` action and the exact `adapter` classification;
2. trusted construction and digest binding of all fourteen request facts,
   including `attempt_id` and `idempotency_key`;
3. RIHAC-001 v2.0 / RIASC-001 v3.0 / HPAC-001 v2.1 approval creation,
   protected proof/registry resolution, validation, expiry, and
   one-shot consumption;
4. current-policy PB evaluation with no precedence weakening;
5. a real, positive, single-attempt Runtime Enforcement gate over the full
   RDGO-001 v3.1 projection;
6. local executable supply-chain identity and live preflight;
7. Shell Gate/equivalent process containment with network denied;
8. atomic durable-before-effect state and uncertainty recovery;
9. the two 3S.2.1 prerequisite repairs at their required reachability point;
10. runtime-inspect repair before any real adapter availability claim; and
11. independent verification of this contract freeze.

The future change SHALL be a narrowly scoped eligibility rule for the exact
local-CLI `runtime_dispatch` profile, not deletion of POL-005, a universal
non-simulation bypass, or an inference that `simulation_only=false` is itself
permission. Every non-eligible non-simulation request remains denied.

**v3.0:** that narrowly scoped eligibility rule is now defined — §12a. It is
the only rule by which `runtime_dispatch` becomes eligible; POL-005 is not
deleted and denies every other non-simulation request.

## 12a. `RUNTIME_DISPATCH_LOCAL_CLI_V1` narrow-eligibility rule (v3.0)

When, and only when, all eleven §12 conditions are separately implemented and
independently verified, `runtime_dispatch` becomes eligible for ordinary
Permission Broker evaluation under the following rule and no other. The
companion policy semantics (`POL-005` amendment and the new `POL-013`) are
frozen by **PBNDE-001 v1.0**.

1. **Trusted-derived classification.** The trusted PB runtime-dispatch request
   builder SHALL derive a closed profile classification
   `RUNTIME_DISPATCH_LOCAL_CLI_V1` from the bound request facts. The
   classification SHALL hold only if: the request is seal-constructed;
   `action_type == runtime_dispatch`; `execution_class == adapter`;
   `transport_type == local_cli`; `network_requirement == false`; no
   credential, secret, provider, or model field is present; no shell or
   command string is present; `adapter_descriptor_binding` carries a
   resolvable canonical supply-chain admission binding of class
   `local_fixed_argv`; `human_authority_binding` is a valid RIHAC-001 v2.0
   validated-authority projection bound to the exact `invocation_id` with a
   real (non-deterministic, non-NON_REAL) assurance verdict; `attempt_id` and
   `idempotency_key` are coordinator-minted and present; exactly one
   `runtime_target_id` is bound; `filesystem_scope_ref` is present and
   digest-bound; and the durable dispatch-attempt lifecycle is wired. The
   classification SHALL NOT be a caller-supplied field, SHALL be committed
   into the request canonical digest (§5), and SHALL be recomputed and
   rejected for any inconsistency by the trusted structural validator (a
   marker set without a complete profile, or a complete profile that lacks
   the trusted marker, both fail closed as a structural DENY).

2. **POL-005 for a classified request.** For a
   `RUNTIME_DISPATCH_LOCAL_CLI_V1`-classified request, POL-005 SHALL return
   *not-triggered*, meaning ONLY that POL-005 does not categorically preclude
   ordinary Permission Broker evaluation. It is NOT an `ALLOW`.

3. **`POL-013`.** A dedicated policy (`POL-013`, "Narrow Local-CLI Dispatch
   Eligibility") SHALL evaluate the full predicate conjunction and SHALL
   return `DENY` (never `ALLOW`, never `HUMAN_REVIEW`) on any missing,
   malformed, unknown-state, unresolvable, or broader predicate, with reason
   `narrow_local_cli_dispatch_profile_incomplete`. When every predicate holds
   it is *not-triggered*. `POL-013` is applicable only to the
   runtime-dispatch / `adapter` policy surface (PBPA-001 v1.1).

4. **No precedence weakening; no other-policy suppression; no ALLOW by
   itself.** Eligibility SHALL NOT weaken the `DENY > HUMAN_REVIEW > ALLOW`
   precedence, SHALL NOT suppress any other policy, and SHALL NOT by itself
   produce `ALLOW`. Every other non-simulation request of every action type
   and execution class SHALL continue to receive POL-005's unconditional
   `DENY`.

5. **`ALLOW` still means only §2's bounded statement.** Gates 7–10 each
   independently gate the effect; runtime execution availability, Runtime
   Enforcement, containment, and the durable pre-dispatch record remain
   separate mandatory gates.

The rule is **contract-expressible and defined now** but remains
**unsatisfiable in production** until N-16-4..7 close: the N-16-6
supply-chain admission binding has no admitting production implementation, so
predicate (1)'s admission requirement always fails and no production request
can be classified.

## 13. Backward and simulation compatibility

This extension SHALL NOT change behavior for rollback, push, publication,
source/docs mutation, backend invocation, existing adapter actions, or any
other known action.

The existing dry path remains exactly:

```text
action_type = adapter_invocation
execution_class = adapter
simulation_only = true
```

It SHALL NOT be migrated to `runtime_dispatch`. The production entry
`pcae session bootstrap --compact --dry-runtime --runtime-target <id>` and
its mock/dry approval, coordinator, PB behavior, and output remain unchanged.
The dry path SHALL NOT be required to carry `attempt_id` or `idempotency_key`:
those are runtime-dispatch-specific facts and do not apply to
`adapter_invocation`'s existing shape.

## 14. Runtime Enforcement projection

The future coordinator projects to Runtime Enforcement:

- the full immutable PB request including all fourteen facts;
- PB decision, causing/matched policy IDs, policy version, and decision
  digest;
- validated approval reference plus validation/freshness verdict digest; and
- static and current live-preflight target/status facts.

The raw approval and PB internals SHALL NOT be duplicated wholesale when
references/digests suffice. Runtime Enforcement independently evaluates the
complete projection; it does not rubber-stamp PB or approval.

## 15. Security invariants

| Invariant | Failure behavior |
|---|---|
| Invalid/missing approval | No request eligible for real dispatch |
| Caller sets `approval_present` | Reject request construction |
| Caller sets/influences `attempt_id` or `idempotency_key` | Reject request construction |
| PB DENY | No dispatch |
| PB failure | No dispatch |
| HUMAN_REVIEW without satisfied authority | No dispatch |
| PB ALLOW without valid authority | No dispatch |
| Target/prompt/repo/task mismatch | No dispatch |
| Runtime unavailable | No dispatch |
| Runtime Enforcement deny/failure | No dispatch |
| Containment missing | No dispatch |
| Network/credential need appears | Out of v1 scope; no dispatch |
| Adapter attempts self-authorization | Reject and record integrity/security failure |
| Same `attempt_id` with different canonical content | Hard collision; reject (RPAC-REQ-066) |
| Same `idempotency_key`, different `invocation_id` presented as a retry | Reject; distinct logical invocations never share an idempotency key by construction |
| Result returned | Remains untrusted and non-completing |

## 16. Versioning

PBRD-001 uses contract `MAJOR.MINOR`. Additive request evidence or an
additive representation-equivalence clarification may increment MINOR only
when existing meanings, action behavior, and precedence remain unchanged.
V2 changed the mandatory meaning and closed shape of the existing
`human_authority_binding`: a v1.1 request could carry a pre-HPAC RIHAC v1.0
validation digest, whereas v2 requires a freshly resolved RIHAC-001 v2.0
authority projection with proof/request binding. Because an old valid request
is no longer valid under the new required meaning, that was a MAJOR, not an
additive minor.

**v2.1 (Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4) — MINOR.** §4a adds a
normative representation-equivalence clause: the seven *logical*
`human_authority_binding` fields, their meanings, the `runtime_dispatch`
action behaviour, and `DENY > HUMAN_REVIEW > ALLOW` precedence are
unchanged; only a documented equivalent compact 3-tuple representation is
newly permitted (the independently verified lossless production form —
finding V-4). No request fact is added, removed, or re-typed; no old valid
request becomes invalid; the closed *shape* argument is not load-bearing
because §4a proves the compact form commits every logical semantic without
a distinguishable collision. This is not a "closed shape" MAJOR.

Widening action semantics, weakening a required fact, changing the
execution class, weakening POL-005 eligibility, or altering precedence
remains incompatible and requires a new MAJOR plus explicit migration and
independent verification.

**v3.0 (Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22) — MAJOR.** §12a defines the
`RUNTIME_DISPATCH_LOCAL_CLI_V1` narrow-eligibility rule, which **narrows
POL-005's categorical hard-block match domain** — the exact change this
section lists as requiring "a new MAJOR plus explicit migration and
independent verification." The `.1R.21` planning artifact provisionally
adjudicated this as a v2.2 MINOR on the ground that §12 already anticipated a
future narrow-eligibility rule; on primary-source review that was corrected
(the operative contract meaning still changes, so this section controls) and
the human operator authorized the v3.0 MAJOR path. `DENY > HUMAN_REVIEW >
ALLOW` precedence, POL-005's universal applicability to every non-eligible
request, POL-005's policy ID, the fourteen logical facts, and the fail-closed
principle are all unchanged; `POL-013` never emits `ALLOW` or `HUMAN_REVIEW`.

**v3.0 explicit migration semantics.**

1. **PBRD-001 v2.1 is the superseded prior MAJOR line;** PBRD-001 v3.0 is the
   new canonical contract. v1.x / v2.x authority-binding semantics have no
   migration.
2. **Existing v2.x request shapes remain parseable.** A v2.x-shaped
   `runtime_dispatch` request carries no `profile_classification` and no
   N-16-6 admission sub-fields; it is structurally valid and **categorically
   DENIED** — POL-005 keeps its hard-DENY match (the classification was never
   achieved) and `POL-013` DENYs on the missing predicates.
3. **No silent auto-upgrade.** No v2.x request is ever reclassified as
   `RUNTIME_DISPATCH_LOCAL_CLI_V1`; the marker is derived by the trusted
   builder only, from a complete predicate set. Legacy callers of the generic
   `build_permission_broker_request` still cannot construct any
   `runtime_dispatch` request.
4. **Classification absence ⇒ the old POL-005 domain.** There is no
   compatibility default to the narrow profile.
5. **Sibling-contract version cross-references SHALL be refreshed to
   `PBRD-001 v3.0`.** The `runtime_dispatch_permission.py` trusted-builder
   module docstring is updated in this phase. The mechanical "Related
   contracts" line edits in RDGO-001 v3.1, RIHAC-001 v2.0, and their siblings
   are performed under a dedicated contract-normalization pass — the same
   mechanism by which `.1R.15.4` last refreshed those cross-references —
   because each of those contracts is byte-frozen by ~50 point-in-time
   verification assertions in the RIHAC/HPAC contract-freeze suites, and a
   cross-reference bump there is out of `.1R.22`'s authorized scope (phase
   prompt §66 / §67). Until that pass, a sibling's "Related contracts" line
   naming `PBRD-001 v2.1` is a stale reference only; each contract is
   individually versioned and RDGO-001 / RIHAC-001's normative content does
   not depend on PBRD's version. RDGO-001's normative gate semantics are
   unchanged: a non-triggered POL-005 for `…_V1` is not a `DENY`, so RDGO-001
   §7's "`DENY` … stops the flow" and §21's "does not … relax POL-005" are
   unaffected in substance (the categorical block is made *more precise*, not
   relaxed for any production request).
6. **Independent verification is mandatory** — Phase
   149O.20L.7O.3W.1R.2B.1R.1.1R.23.

Unknown contract/request versions fail closed. Existing actions are never
retrospectively reclassified by a PBRD revision.

## 17. Non-goals and freeze verdict

**v2.1 non-goal (historical):** the v2.1 normalization did not modify
`src/pcae`, tests, or PB source.

**v3.0:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 implements §12a in
`permission_broker_foundation.py` (POL-005 carve-out + `POL-013` + the two
derived fields) and `runtime_dispatch_permission.py` (the N-16-6 admission
interface + fail-closed non-admitting stub + the trusted-builder
classification derivation), and adds the `.1R.21` §37 defensive test matrix.
It does **not** modify Runtime Enforcement, adapters, runtime inspect,
session/bootstrap, schema packages, or version/build configuration; it does
**not** launch a process, invoke an external runtime, register an adapter,
access credentials, or enable network/execution; and it does **not** add an
`adapter.dispatch()` call site or change runtime capability. The narrow
profile is unsatisfiable in production.

**PBRD-001 v3.0: FROZEN (MAJOR); explicit migration in §16; independent
verification is Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.23. v1.x / v2.x authority
bindings have no migration; v2.x request shapes are parseable but
categorically DENIED.**
**POL-005 production behaviour for every non-eligible non-simulation request:
UNCHANGED (unconditional `DENY`). The single `RUNTIME_DISPATCH_LOCAL_CLI_V1`
carve-out is unsatisfiable in production.**  
**Real execution: UNAVAILABLE.**
