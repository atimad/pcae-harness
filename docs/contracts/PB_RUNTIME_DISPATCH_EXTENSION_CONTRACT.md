# PBRD-001 v1.1 — Permission Broker Runtime Dispatch Extension Contract

## Contract identity and status

**Contract:** PBRD-001  
**Version:** 1.1  
**Status:** FROZEN  
**Frozen by:** Phase 149O.20L.7O.3V (v1.0); repaired by Phase
149O.20L.7O.3V.1R (v1.1)  
**Supersedes:** PBRD-001 v1.0 (frozen `2060ebd4`), whose twelve-fact request
was independently found incomplete against RPAC-REQ-025/044/064–068 by
Phase 149O.20L.7O.3V.1 (Finding B-149O.20L.7O.3V.1-2): it lacked mandatory
`attempt_id` and `idempotency_key` binding.  
**Scope:** Contract-only, additive Permission Broker extension for one future
real local-CLI runtime dispatch.  
**Related contracts:** Permission Broker Foundation, PBPA-001 v1.0,
PBPC-001 v1.2, RPAC-001 v1.0, RIHAC-001 v1.0, RDGO-001 v2.0.

PBRD-001 freezes a future PB request/action contract. It does not add source
constants, policies, request fields, a production consumer, or execution.
POL-005 remains unchanged and therefore real dispatch remains denied.

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
| 8 | `adapter_descriptor_binding` | Registry/config preflight | closed object: `adapter_id`, descriptor version/digest, target-config digest | Yes | Runtime Registry/config owner | Stable adapter and configuration identity |
| 9 | `prompt_hash` | `pcae.prompt-semantic.v1` canonicalizer | 64-lowercase-hex SHA-256 | Yes | Prompt builder | Exact semantic instruction identity |
| 10 | `requested_capability` | Governed invocation request | non-empty capability ID | Yes | Integration contract/coordinator | Capability requested, not capability possessed |
| 11 | `transport_type` | Contract-fixed integration point | const `local_cli` | Yes | PBRD-001 integration | Excludes API/provider transports |
| 12 | `network_requirement` | Target descriptor + static preflight | const `false` | Yes | Registry/preflight owner | Declared lack of network need; grants none |
| 13 | `filesystem_scope_ref` | Governed isolated-worktree/scope owner | immutable ID/digest reference | Yes | Filesystem-scope owner | Declared scope for audit/containment; grants no mutation |
| 14 | `human_authority_binding` | RIHAC validator | closed object containing approval ID/digest and validation-evidence digest | Yes | Human-authority validator | Reference plus validated evidence projection; not raw authority or a boolean |

`lifecycle_context` and `human_authority_binding` are each one immutable
binding fact despite their closed subfields, exactly as in v1.0. This
preserves that convention while honestly recounting the total as fourteen.

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
2. a minimal validation-evidence projection digest proving that gate 5
   validated the exact subject/scope/freshness facts now in the PB request.

PB SHALL NOT receive or trust raw approval prose or a caller assertion that
approval exists. It SHALL verify that the validator-owned projection binds to
the same request digest and approval reference.

Only successful RIHAC-001 validation may cause the trusted request builder to
set `approval_present=true`. The boolean is a derived Foundation input for
POL-004; it is not itself authority and is not caller-settable. Missing,
stale, mismatched, consumed, expired, tampered, or unverifiable approval
evidence yields `approval_present=false` or request-construction failure and
can never produce dispatch.

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
3. RIHAC-001/RIASC-001 approval creation, storage, validation, expiry, and
   one-shot consumption;
4. current-policy PB evaluation with no precedence weakening;
5. a real, positive, single-attempt Runtime Enforcement gate over the full
   RDGO-001 v2.0 projection;
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

PBRD-001 uses contract `MAJOR.MINOR`. Additive request evidence may increment
MINOR only when existing meanings, action behavior, and precedence remain
unchanged. The v1.0→v1.1 change fits exactly this rule: `attempt_id` and
`idempotency_key` are new mandatory facts, but no existing fact's meaning,
type, source, or trust owner changed, no action semantics widened, the
execution class is unchanged, POL-005 eligibility is unchanged, and
precedence is unchanged. Widening action semantics, weakening a required
fact, changing the execution class, weakening POL-005 eligibility, or
altering precedence remains incompatible and requires a new MAJOR plus
explicit migration and independent verification.

Unknown contract/request versions fail closed. Existing actions are never
retrospectively reclassified by a PBRD revision.

## 17. Non-goals and freeze verdict

This contract does not modify `src/pcae`, tests, PB source, Runtime
Enforcement, adapters, runtime inspect, session/bootstrap, schema packages,
or version/build configuration. It does not launch a process, invoke an
external runtime, access credentials, or enable network/execution.

**PBRD-001 v1.1: FROZEN for local-CLI-v1 contract purposes.**  
**POL-005 production behavior: UNCHANGED.**  
**Real execution: UNAVAILABLE.**
