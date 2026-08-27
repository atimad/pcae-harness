# RDGO-001 v1.0 — Runtime Dispatch Gate Ordering Contract

## Contract identity and status

**Contract:** RDGO-001  
**Version:** 1.0  
**Status:** FROZEN  
**Frozen by:** Phase 149O.20L.7O.3V  
**Scope:** Future one-attempt local-CLI real-runtime dispatch ordering only.  
**Related contracts:** RPAC-001 v1.0, RIHAC-001 v1.0, RIASC-001 v1.0,
PBRD-001 v1.0, Runtime Enforcement contracts, Phase 99 Execution Attempt
Boundary.

RDGO-001 freezes the gate sequence and cross-gate evidence contract. It
does not implement a gate, change current runtime state, or authorize an
execution attempt.

## 0. Normative language and walls

`SHALL`, `SHALL NOT`, `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY`
are normative. Every gate fails closed. A later gate SHALL NOT infer,
manufacture, or repair a missing earlier gate.

```text
human approval != PB permission
PB ALLOW != runtime capability
runtime capability != Runtime Enforcement approval
Runtime Enforcement ALLOW != process permission
process permission != dispatch completion
dispatch completion != accepted change
runtime result != task completion
```

## 1. Frozen eleven-gate order

| # | Gate | Owner | Input | Output | External effect? |
|---:|---|---|---|---|---|
| 1 | Prompt preparation | Trusted prompt builder | Governed task instructions and declared context | Prompt artifact + `pcae.prompt-semantic.v1` hash | No |
| 2 | Explicit target selection | Trusted target selector | Exact operator-selected target ID | One exact `runtime_target_id`; no fallback | No |
| 3 | Static preflight | Runtime Registry + preflight coordinator | Prompt/request draft, target descriptor/config, declared scope | Static capability/configuration evidence or failure | No |
| 4 | Human authority creation | Identified human + trusted approval coordinator | Exact approval preview over subject/scope/expiry | Immutable `RuntimeInvocationApproval` | No |
| 5 | Approval validation | RIHAC-001 validator | Canonical approval ref, current repo/task/target/prompt/config/policy state | Validated-authority evidence projection or failure | No |
| 6 | Permission Broker | PB Foundation with PBRD-001 extension | Immutable `runtime_dispatch` request + validated authority projection | `ALLOW`, `DENY`, or `HUMAN_REVIEW` decision evidence | No |
| 7 | Runtime Enforcement | Runtime Enforcement coordinator | Full bound request, PB evidence, validated approval ref/freshness, preflight facts | Single-attempt final whether-to-invoke decision | No |
| 8 | Process containment and live preflight | Shell Gate/equivalent containment owner | Exact executable/config, cwd, arguments, environment allowlist, RE decision | Established bounded process environment + live-preflight evidence | No dispatch yet |
| 9 | Durable pre-dispatch record | Trusted invocation coordinator/store | Eight minimum bound items + containment evidence | Atomic `dispatch_attempted` state; approval consumed | No process effect yet |
| 10 | Adapter dispatch | Exact selected Runtime Adapter transport | Immutable dispatch envelope and established containment | One process-spawn/dispatch receipt or uncertain/failure state | **Yes — first external execution effect** |
| 11 | Result capture and intake | Adapter collector + trusted result/intake boundary | Receipt/attempt identity and untrusted runtime output | Normalized untrusted result + producer-neutral intake evidence | Effect already occurred; no new authority |

The numeric order is mandatory. Gate 10 is the real-effect boundary.
No adapter dispatch may occur before gate 9 is durable.

## 2. Gate 1 — prompt preparation

Gate 1 resolves the semantically load-bearing instructions and context into a
prompt artifact and computes the canonical hash under RIHAC-001 §10.

It creates no human authority, PB permission, runtime capability, Runtime
Enforcement decision, process permission, or external effect. Prompt content
and referenced context are untrusted as instructions to PCAE's governance
kernel; they cannot cause later gates to be skipped.

Failure to produce one deterministic semantic hash stops the flow.

## 3. Gate 2 — explicit target selection

Gate 2 binds exactly one `runtime_target_id`. No default, first-registered,
agent-derived, provider-derived, case-normalized, alias, or fallback target
is permitted.

Selection creates no authority or permission. Unknown, ambiguous, malformed,
or absent target selection stops the flow.

## 4. Gate 3 — static preflight

Static preflight occurs before human approval so PCAE does not ask a human to
approve a target that is structurally incapable.

It may inspect only non-executing facts:

- exact registry/descriptor/config presence and version;
- `transport_type=local_cli`;
- declared capability and result-format support;
- descriptor/config/adapter identity digests;
- `network_requirement=false`;
- declared filesystem-scope and process-containment profile references;
- expected working-directory shape; and
- whether the request can be represented within local-CLI-v1 scope.

Static preflight SHALL NOT launch the executable, run a provider/auth check,
access credentials, open network connections, mutate the repository, or
create authority. Structural unavailability fails before human approval
where possible.

## 5. Gate 4 — human authority creation

Gate 4 presents the exact subject, scope, target, prompt identity, adapter
binding, HEAD/task snapshot, expiry, one-shot limit, and non-effect
statements. A distinct, non-defaultable human act creates the immutable
RIASC-001 approval artifact.

The artifact creates human authority only. It does not create PB permission,
capability, Runtime Enforcement approval, containment, dispatch, acceptance,
or completion.

## 6. Gate 5 — approval validation

Gate 5 executes RIHAC-001's ordered validation against current state and
produces a minimal immutable projection containing:

- approval ID/digest;
- complete subject/scope binding digest;
- provenance verdict;
- seven-condition freshness verdict and policy-refresh disposition;
- expiry verdict;
- consumption-state verdict; and
- validation timestamp/version.

It does not produce PB ALLOW. Missing, stale, mismatched, expired, consumed,
tampered, or ambiguous evidence stops the flow.

## 7. Gate 6 — Permission Broker

Gate 6 evaluates PBRD-001's exact `runtime_dispatch` request using current PB
policy. `DENY`, PB failure, malformed output, or unresolved `HUMAN_REVIEW`
stops the flow.

PB ALLOW is policy permission to attempt the described action class only. It
does not create or replace human authority, capability, Runtime Enforcement,
process/network/filesystem/credential permission, dispatch, or acceptance.

## 8. Gate 7 — Runtime Enforcement

Runtime Enforcement receives:

1. the full immutable request and all twelve PBRD-001 binding facts;
2. the PB decision, policy IDs, policy version, and decision digest;
3. the validated approval reference and freshness verdict digest; and
4. static/current target-status and preflight facts.

It independently evaluates the complete bound request. It SHALL NOT infer
approval from PB ALLOW, permission from approval, capability from the target
name, or containment from a planned profile.

Its positive decision is single-attempt, expiring, and invalid across any
relevant input or policy change. A denial, failure, stale input, unavailable
target, or unresolved no-go stops the flow. No real process has been launched
at this gate.

## 9. Gate 8 — process containment and live preflight

Gate 8 is owned by Shell Gate or an equivalent future process-containment
mechanism. It controls how the one permitted local process may be launched;
it is not an extension of PB's policy decision.

Before gate 9 it SHALL:

- re-resolve the exact descriptor/config and verify no drift;
- resolve the exact executable without accepting a caller shell string;
- verify executable identity/hash/version against the descriptor pin;
- confirm installation and current local availability;
- recheck repository fingerprint, HEAD, task state/digest, target, prompt,
  adapter config, and current policy/RE decision;
- establish exact cwd, argument vector, environment allowlist, child-process
  prohibition/limit, resource/time limit, and supervision;
- confirm network remains denied and no credential access is required; and
- bind the established containment evidence to the invocation.

No dispatch occurs unless containment is successfully established. A live
preflight check is an observation of readiness, never authority or
permission.

## 10. Gate 9 — durable pre-dispatch record

Gate 9 atomically persists the minimum effect-bound evidence before process
creation. The exact eight items are:

1. **Invocation identity:** `invocation_id` and the single attempt's internal
   `attempt_id` where used.
2. **Repository/task binding:** repository fingerprint, HEAD, task ID and
   task-contract digest, phase ID, and conditional session ID.
3. **Target binding:** exact runtime target plus adapter descriptor/config and
   live executable-identity observations.
4. **Prompt binding:** semantic prompt hash and hash-profile ID.
5. **Approval binding:** approval ID/digest and validated-authority evidence
   digest, atomically marked consumed by this write.
6. **PB binding:** PB request/decision digest, decision, policy version,
   causing policy IDs, and matched no-go IDs.
7. **Runtime Enforcement binding:** decision ID/digest, verdict, expiry, and
   evaluated-input digest.
8. **Dispatch intent/state:** exact containment evidence reference plus the
   durable state marker `dispatch_attempted` and its timestamp.

References and digests SHALL be used instead of duplicating the full
approval/PB/RE artifacts. The write is create-only or append-only,
crash-consistent, and completed before gate 10. If this write cannot be proven
durable and internally consistent, no dispatch occurs.

`dispatch_attempted` is the approval-consumption point and at-most-once guard.
It is not proof the external process was created or completed.

## 11. Gate 10 — adapter dispatch

Gate 10 is the first external execution effect. It creates at most one exact
local process through the selected adapter and already-established
containment. It SHALL use an argument vector, not unrestricted shell
evaluation, and SHALL NOT widen cwd, environment, child-process, network,
credential, or filesystem scope.

The adapter cannot authorize itself, choose a fallback target, alter the
invocation identity, or reinterpret the dispatch envelope. A dispatch call or
receipt does not prove completion. Any ambiguity after entry to this gate is
`DISPATCH_UNCERTAIN` until stronger evidence exists.

## 12. Gate 11 — result capture and intake

Gate 11 binds output to invocation/attempt/target/adapter identity, captures
exit/termination observations, validates normalized result shape, and records
integrity/failure evidence.

All runtime output is untrusted. Capture SHALL NOT equal validation,
authorization, permission, acceptance, promotion, commit, push, publication,
or task completion. Proposed changes flow through the existing producer-
neutral intake/review/promotion governance.

Malformed output fails closed and must never be persisted as a successful
result. This contract does not repair the existing 3S.2.1 malformed-result
finding; that repair is blocking before the first non-mock adapter becomes
reachable.

## 13. Static versus live preflight

| Fact | Static preflight (gate 3) | Live preflight (gate 8) |
|---|---|---|
| Target/descriptor exists | Required | Re-resolve exact identity/digest |
| Declared capability/result format | Required | Reconfirm unchanged |
| Transport/local-only scope | Required | Reconfirm |
| Network requirement | Must be false | Confirm network containment denied |
| Config/adapter identity | Snapshot digest | Recompute/compare |
| Executable identity/installation | Descriptor pin/declared shape only | Resolve and hash exact executable |
| Repository/HEAD/task | Snapshot for approval | Re-read and compare |
| Prompt | Semantic hash | Recompute/compare exact delivered prompt |
| PB/RE policy freshness | Not yet evaluated | Reconfirm current decisions and versions |
| Process containment | Declared profile only | Establish and attest actual containment |

An unavailable target fails before human approval where static facts can
prove it. Dynamic availability and mutable executable facts must still be
revalidated immediately before effect.

## 14. Execution Attempt Boundary mapping

RDGO-001 extends but does not redefine Phase 99 or COMP-002:

- Gates 1–6 occur before the governed execution-attempt decision point.
- Gate 7 is the final whether-to-invoke execution-attempt decision point.
- Gates 8–9 are post-decision, pre-effect attempt preparation.
- Gate 10 is the first external execution effect.
- Gate 11 observes/captures the result and remains outside acceptance.

Current COMP-002 remains `not_implemented`; this mapping is a future
compatible extension, not activation.

## 15. TOCTOU contract

The exact seven mutable facts identified in 3U are:

| Mutable fact | Snapshot-bound? | Recheck before PB | Recheck before dispatch | Failure |
|---|---|---|---|---|
| HEAD | Yes, at approval | Yes | Yes | Approval stale; no dispatch; fresh approval |
| Task state/contract | Freshness-bound, not a subject member beyond `task_id` | Yes | Yes | Approval stale; no dispatch; fresh approval |
| Prompt | Yes, subject hash | Yes | Yes | Subject mismatch; no dispatch; fresh invocation/approval |
| Runtime target | Yes, subject target | Yes | Yes | Subject mismatch; no fallback; fresh invocation/approval |
| Adapter configuration | Yes, descriptor/config snapshot | Yes | Yes | Approval stale; no dispatch; fresh approval |
| Adapter executable identity | Descriptor-pinned, not approval-bound | Not applicable beyond descriptor facts | Yes, exact hash before spawn | No dispatch; repair/reselect target; fresh late-gate decisions |
| Policy version | Not bound to human act | Yes, current PB/RE only | Yes | Cached PB/RE invalid; re-evaluate; no dispatch until current |

No stale PB or Runtime Enforcement decision is reused. Runtime Enforcement
has no cache validity across any relevant request, approval, target/status,
repository/task/HEAD, prompt, configuration, executable, or policy change.

## 16. Cross-contract identifiers

| Concept | Authority contract | PB contract | Gate contract | Invocation record |
|---|---|---|---|---|
| Invocation | `subject.invocation_id` | `invocation_id` | Gates 4–11 | item 1 |
| Repository | `subject.repository_identity` | `repository_identity` | Gates 5/8/9 | item 2 |
| Task | `subject.task_id` + task snapshot | `task_id` | Gates 5/8/9 | item 2 |
| Phase/session | `governance_context` | `lifecycle_context` | Gates 5/8/9 | item 2 |
| Target | `subject.runtime_target_id` | `runtime_target_id` | Gates 2–11 | item 3 |
| Prompt | `subject.prompt_hash` | `prompt_hash` | Gates 1/5/8/9 | item 4 |
| Approval | `approval_id`/`record_digest` | `human_authority_binding` | Gates 4/5/9 | item 5 |
| PB request/decision | Not authority | request/decision digests | Gates 6/7/9 | item 6 |
| RE decision | Not authority | Projected evidence only | Gates 7/9 | item 7 |
| Dispatch state | Consumption rule | Not PB permission | Gates 9/10 | item 8 + events |

## 17. Crash and recovery states

The minimum conceptual states are:

| State | Meaning | External effect | Reuse/retry |
|---|---|---|---|
| `PRE_APPROVAL_CONSUMPTION` | Gates 1–8 may have progressed; no gate-9 marker | None | Same approval only after full revalidation and proof marker absent |
| `APPROVAL_VALIDATED` | Gate 5 passed | None | Validation is not cached authority |
| `PB_EVALUATED` | Gate 6 produced decision | None | Re-evaluate after any drift/restart |
| `RE_EVALUATED` | Gate 7 produced decision | None | Re-evaluate after any drift/restart |
| `DISPATCH_ATTEMPTED` | Gate 9 durable; approval consumed | None proven yet | No automatic retry |
| `DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER` | Trusted evidence proves gate 10 never began | None | Fresh invocation/approval required |
| `DISPATCH_UNCERTAIN` | Process may have been created or outcome cannot be proven | Possible/unknown | No replay; fresh human decision/approval for any new attempt |
| `RESULT_CAPTURED_UNTRUSTED` | Gate 11 captured a bound result | Prior effect occurred/was observed | Intake/review only; no task completion |

After gate 9, absence of a result is never proof that dispatch did not occur.
Exactly-once execution is not promised. At-most-once attempt is enforced where
durable state proves it; otherwise uncertainty is explicit.

## 18. Retry contract

There is no automatic retry. Before gate 9, a strictly identical,
unexpired, unconsumed approval may be reused only after all gates/freshness
checks are repeated and durable state proves no consumption. At or after gate
9, any failed, uncertain, or proven-not-started new attempt requires a new
invocation ID and fresh human approval.

## 19. Security invariants

| Invariant | Contract owner | Failure behavior |
|---|---|---|
| No valid approval -> no real dispatch | RIHAC/RDGO gates 4–5 | Stop before PB/dispatch |
| Stale/mismatched approval -> no dispatch | RIHAC gate 5 | Fail closed; no rebinding |
| PB DENY/failure -> no dispatch | PBRD gate 6 | Stop |
| HUMAN_REVIEW without satisfied authority -> no dispatch | PBRD gate 6 | Stop |
| PB ALLOW without valid authority -> no dispatch | RDGO gates 5–7 | RE must deny/fail |
| Runtime unavailable/target mismatch -> no dispatch | Gates 3/8 | Stop; no fallback |
| Prompt/repo/task mismatch -> no dispatch | Gates 5/8 | Stop; new approval as required |
| Runtime Enforcement deny/failure -> no dispatch | Gate 7 | Stop |
| Containment not established -> no dispatch | Gate 8 | Stop |
| Durable marker not proven -> no dispatch | Gate 9 | Stop |
| Adapter cannot self-authorize | Gates 7/10 | Reject/security failure |
| Process permission does not imply completion | Gates 8/10 | Receipt/result evidence required |
| Dispatch completion does not accept change | Gate 11/intake | Existing review/promotion gates apply |
| Runtime result remains untrusted | Gate 11 | Evidence only |
| Runtime result cannot complete task | Task lifecycle | Explicit governed completion only |

## 20. Backward compatibility and no-go

The dry `adapter_invocation`/`simulation_only=true` path remains unchanged
and is not migrated into this sequence. Existing PB actions, Runtime
Enforcement evidence models, Phase 99 semantics, intake, mutation governance,
CHGR/IWC/HATP/HMIC/Class-B/CLTR, and runtime inspect are not modified.

This contract does not launch a process, implement a Shell Gate, activate
Runtime Enforcement, relax POL-005, register a real adapter, enable network,
access credentials, or modify runtime capability.

## 21. Versioning and freeze verdict

RDGO-001 uses contract `MAJOR.MINOR`. Adding a later post-result gate may be
additive only if gates 1–11 and gate 10's first-effect boundary retain their
meaning and order. Reordering, merging authority/permission/enforcement/
containment, moving the durable marker after effect, weakening freshness, or
widening effect scope is incompatible and requires a new MAJOR with explicit
migration and independent verification.

Unknown versions fail closed.

**RDGO-001 v1.0: FROZEN for local-CLI-v1 contract purposes.**  
**Gate count: 11. Durable-before-effect items: 8. TOCTOU facts: 7.**  
**Real execution: UNAVAILABLE.**
