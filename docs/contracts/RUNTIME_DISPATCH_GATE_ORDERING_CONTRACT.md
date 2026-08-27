# RDGO-001 v2.0 — Runtime Dispatch Gate Ordering Contract

## Contract identity and status

**Contract:** RDGO-001
**Version:** 2.0
**Status:** FROZEN
**Frozen by:** Phase 149O.20L.7O.3V (v1.0); repaired by Phase
149O.20L.7O.3V.1R (v2.0)
**Supersedes:** RDGO-001 v1.0 (frozen `2060ebd4`), whose gate 3/gate 4
relative order was independently found to contradict RPAC-REQ-042 by Phase
149O.20L.7O.3V.1 (Finding B-149O.20L.7O.3V.1-1).
**Scope:** Future one-attempt local-CLI real-runtime dispatch ordering only.
**Related contracts:** RPAC-001 v1.0, RIHAC-001 v1.0, RIASC-001 v1.0,
PBRD-001 v1.1, Runtime Enforcement contracts, Phase 99 Execution Attempt
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

## 1. Frozen eleven-gate order (v2.0 — RPAC-REQ-042-consistent)

| # | Gate | Owner | Input | Output | External effect? |
|---:|---|---|---|---|---|
| 1 | Prompt preparation | Trusted prompt builder | Governed task instructions and declared context | Prompt artifact + `pcae.prompt-semantic.v1` hash | No |
| 2 | Explicit target selection and request construction | Trusted target selector + invocation coordinator | Exact operator-selected target ID; fresh `invocation_id`/`attempt_id`/`idempotency_key` allocation | One exact `runtime_target_id`; no fallback; immutable request identity triple minted | No |
| 3 | Human authority creation | Identified human + trusted approval coordinator | Exact approval preview over subject/scope/expiry | Immutable `RuntimeInvocationApproval` | No |
| 4 | Static preflight | Runtime Registry + preflight coordinator | Prompt/request draft, target descriptor/config, declared scope | Static capability/configuration evidence or failure | No |
| 5 | Approval validation | RIHAC-001 validator | Canonical approval ref, current repo/task/target/prompt/config/policy state | Validated-authority evidence projection or failure | No |
| 6 | Permission Broker | PB Foundation with PBRD-001 extension | Immutable `runtime_dispatch` request (fourteen facts) + validated authority projection | `ALLOW`, `DENY`, or `HUMAN_REVIEW` decision evidence | No |
| 7 | Runtime Enforcement | Runtime Enforcement coordinator | Full bound request, PB evidence, validated approval ref/freshness, preflight facts | Single-attempt final whether-to-invoke decision | No |
| 8 | Process containment and live preflight | Shell Gate/equivalent containment owner | Exact executable/config, cwd, arguments, environment allowlist, RE decision | Established bounded process environment + live-preflight evidence | No dispatch yet |
| 9 | Durable pre-dispatch record | Trusted invocation coordinator/store | Eight minimum bound items + containment evidence | Atomic `dispatch_attempted` state; approval consumed | No process effect yet |
| 10 | Adapter dispatch | Exact selected Runtime Adapter transport | Immutable dispatch envelope and established containment | One process-spawn/dispatch receipt or uncertain/failure state | **Yes — first external execution effect** |
| 11 | Result capture and intake | Adapter collector + trusted result/intake boundary | Receipt/attempt identity and untrusted runtime output | Normalized untrusted result + producer-neutral intake evidence | Effect already occurred; no new authority |

The numeric order is mandatory. Gate 10 is the real-effect boundary.
No adapter dispatch may occur before gate 9 is durable. **v2.0 change:**
gates 3 and 4 are transposed relative to v1.0. Human authority creation is
now gate 3 and static preflight is now gate 4, matching RPAC-REQ-042's
frozen order (`... 3. obtain human InvocationApproval; 4. resolve
descriptor/config and perform fact-only status/capability preflight ...`).
No other gate's number, owner, or content changed. Gate count remains
eleven.

## 2. Gate 1 — prompt preparation

Gate 1 resolves the semantically load-bearing instructions and context into a
prompt artifact and computes the canonical hash under RIHAC-001 §10.

It creates no human authority, PB permission, runtime capability, Runtime
Enforcement decision, process permission, or external effect. Prompt content
and referenced context are untrusted as instructions to PCAE's governance
kernel; they cannot cause later gates to be skipped.

Failure to produce one deterministic semantic hash stops the flow.

## 3. Gate 2 — explicit target selection and request construction

Gate 2 binds exactly one `runtime_target_id`. No default, first-registered,
agent-derived, provider-derived, case-normalized, alias, or fallback target
is permitted.

Gate 2 also mints the immutable request-identity triple required by
RPAC-REQ-025/064/065 before the approval preview is rendered: the logical
`invocation_id`, this attempt's unique `attempt_id`, and the canonical
`idempotency_key`. All three are allocated by the trusted PCAE invocation
coordinator from cryptographically strong random identity (`invocation_id`,
`attempt_id`) or by canonical content digest (`idempotency_key`); none is
chosen, supplied, or influenced by the adapter, runtime, caller payload, or
approval producer. See §10a for exact semantics.

Selection and request-identity minting create no authority or permission.
Unknown, ambiguous, malformed, or absent target selection, or failure to
mint a unique request-identity triple, stops the flow.

## 4. Gate 3 — human authority creation

Gate 3 presents the exact subject, scope, target, prompt identity, adapter
binding, HEAD/task snapshot, expiry, one-shot limit, and non-effect
statements. A distinct, non-defaultable human act creates the immutable
RIASC-001 approval artifact.

The artifact creates human authority only. It does not create PB permission,
capability, Runtime Enforcement approval, containment, dispatch, acceptance,
or completion. Approval creation certifies human intent for the exact bound
subject; it does not certify that the selected target is structurally
capable. That determination belongs to gate 4 and remains independent.

## 5. Gate 4 — static preflight

Static preflight now occurs after human authority creation, per
RPAC-REQ-042. It may inspect only non-executing facts:

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
create authority. A structurally incapable target now fails **after**
approval creation but strictly **before** Permission Broker and every later
gate; it is not asked of a human as a precondition for approval creation
under v2.0. This is a deliberate consequence of RPAC-REQ-042's fixed order:
an approval that never reaches gate 6 because gate 4 failed is unconsumed,
imposes no cost beyond an unused artifact, and grants no capability by
itself (RIHAC-001 §1, §20 — approval never implies capability). Structural
unavailability still fails before Permission Broker, Runtime Enforcement,
containment, and dispatch in every case.

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

Gate 6 evaluates PBRD-001's exact `runtime_dispatch` request (fourteen
immutable facts, including the gate-2-minted `attempt_id` and
`idempotency_key`) using current PB policy. `DENY`, PB failure, malformed
output, or unresolved `HUMAN_REVIEW` stops the flow.

PB ALLOW is policy permission to attempt the described action class only. It
does not create or replace human authority, capability, Runtime Enforcement,
process/network/filesystem/credential permission, dispatch, or acceptance.

## 8. Gate 7 — Runtime Enforcement

Runtime Enforcement receives:

1. the full immutable request and all fourteen PBRD-001 binding facts
   (including `attempt_id` and `idempotency_key`);
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

1. **Invocation identity:** `invocation_id`, this attempt's mandatory unique
   `attempt_id`, and the request's canonical `idempotency_key` — all three
   unconditional, never `attempt_id` "where used."
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

## 10a. Attempt identity and idempotency (repair of Finding B-2)

This section restores RPAC-REQ-025/064-072 semantics to the gate sequence.

**`attempt_id`** identifies exactly one concrete dispatch try under one
logical invocation. It is distinct from `invocation_id` (the stable logical
invocation across attempts), `approval_id` (the human-authority artifact
identity), `task_id` (the PCAE task), and `idempotency_key` (below). It is
minted at gate 2 by the trusted invocation coordinator from cryptographically
strong random identity, using the convention `att-<32-hex>`. It SHALL NOT be
selected, echoed back, or overwritten by the adapter, runtime, provider, or
task content. Every gate from 2 through 11 that references invocation
identity SHALL carry the same `attempt_id` unchanged.

**`idempotency_key`** identifies the logical dispatch operation's canonical
content — not one concrete attempt — so that safe retries and replay
detection are possible. It is a SHA-256 digest, minted at gate 2 by the
trusted invocation coordinator, over canonical versioned request content
excluding timestamps and attempt-specific mutable observations: repository
fingerprint/base commit, `task_id`, `prompt_hash`, `runtime_target_id`,
adapter/descriptor/config digests, requested effect profiles, and approval
scope, exactly per RPAC-REQ-065. It SHALL NOT be supplied or influenced by
the adapter, runtime, or caller.

**Distinction:** `attempt_id` answers "which concrete try is this," and
`idempotency_key` answers "which logical dispatch request is this a
(possibly repeated) attempt of." Two attempts of the same unchanged logical
request share the same `idempotency_key` but each has its own unique
`attempt_id`.

**Retry relationship (RPAC-REQ-072):** a genuine retry of the same logical
invocation — same repository/task/base, prompt, target, effects, and budget,
still covered by the prior approval's `attempt_limit`/expiry — mints a new
`attempt_id` at a fresh pass through gate 2 while the `idempotency_key`
remains identical (the canonical content did not change). Any change to
prompt, target, provider/model, repository/task, effects, or budget mints
both a new `invocation_id` and, consequently, a new `idempotency_key`, and
requires a fresh human approval; the `attempt_id` is new by construction in
either case. There is no case in which only the `idempotency_key` changes
while `invocation_id`/approval remain the same, because `idempotency_key` is
a pure function of the same canonical fields that gate the invocation's
validity.

**Crash/uncertainty relationship:** once gate 9 durably records
`dispatch_attempted` for a given `attempt_id`, that attempt is consumed
regardless of whether gate 10 is later proven to have started
(`DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER`) or remains unprovable
(`DISPATCH_UNCERTAIN`). Neither state permits reuse of the same
`attempt_id`. A same-`idempotency_key` retry after an uncertain or
not-started attempt still requires a brand-new `attempt_id` minted through a
fresh gate 2 pass and, per RPAC-REQ-072/RIHAC-001 §19, a fresh human
approval — the existing `idempotency_key` does not by itself authorize
redispatch. This closes the gap: RDGO v1.0's `attempt_id where used` could
not by itself prevent an implementer from treating a post-crash resume as
requiring no new identity; v2.0 makes both identifiers unconditional and
durably bound at gate 9 item 1.

## 13. Static versus live preflight

| Fact | Static preflight (gate 4) | Live preflight (gate 8) |
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

Under v2.0, a structurally unavailable target fails after human authority
creation (gate 3) but strictly before Permission Broker (gate 6) and every
later gate — it can no longer fail *before* approval is created, because
RPAC-REQ-042 fixes approval at gate 3 and preflight at gate 4. Approval
creation never certifies capability (RIHAC-001 §1, §20); an approval whose
target later fails static preflight is simply never consumed at gate 9.
Dynamic availability and mutable executable facts must still be revalidated
immediately before effect at gate 8.

## 14. Execution Attempt Boundary mapping

RDGO-001 extends but does not redefine Phase 99 or COMP-002:

- Gates 1–6 occur before the governed execution-attempt decision point.
- Gate 7 is the final whether-to-invoke execution-attempt decision point.
- Gates 8–9 are post-decision, pre-effect attempt preparation.
- Gate 10 is the first external execution effect.
- Gate 11 observes/captures the result and remains outside acceptance.

This mapping is unchanged by the v2.0 gate 3/4 transposition: gates 3 and 4
are both still within the "gates 1–6, before the execution-attempt decision"
band regardless of their relative order. Current COMP-002 remains
`not_implemented`; this mapping is a future compatible extension, not
activation.

## 15. TOCTOU contract

The exact seven mutable facts identified in 3U/3V remain unchanged in
substance by the gate reorder:

| Mutable fact | Snapshot-bound? | Recheck before PB | Recheck before dispatch | Failure |
|---|---|---|---|---|
| HEAD | Yes, at approval | Yes | Yes | Approval stale; no dispatch; fresh approval |
| Task state/contract | Freshness-bound, not a subject member beyond `task_id` | Yes | Yes | Approval stale; no dispatch; fresh approval |
| Prompt | Yes, subject hash | Yes | Yes | Subject mismatch; no dispatch; fresh invocation/approval |
| Runtime target | Yes, subject target | Yes | Yes | Subject mismatch; no fallback; fresh invocation/approval |
| Adapter configuration | Yes, descriptor/config snapshot | Yes | Yes | Approval stale; no dispatch; fresh approval |
| Adapter executable identity | Descriptor-pinned, not approval-bound | Not applicable beyond descriptor facts | Yes, exact hash before spawn | No dispatch; repair/reselect target; fresh late-gate decisions |
| Policy version | Not bound to human act | Yes, current PB/RE only | Yes | Cached PB/RE invalid; re-evaluate; no dispatch until current |

`attempt_id` and `idempotency_key` are not TOCTOU-mutable facts: both are
minted once at gate 2 and held immutable through gate 11 (§10a). They are
identity, not state subject to drift, so they are intentionally excluded from
this table; the count remains seven.

No stale PB or Runtime Enforcement decision is reused. Runtime Enforcement
has no cache validity across any relevant request, approval, target/status,
repository/task/HEAD, prompt, configuration, executable, or policy change.

## 16. Cross-contract identifiers

| Concept | Authority contract | PB contract | Gate contract | Invocation record |
|---|---|---|---|---|
| Invocation | `subject.invocation_id` | `invocation_id` | Gates 2–11 | item 1 |
| Attempt | Not a subject member (approval binds one attempt via `attempt_limit=1`, not a specific `attempt_id`) | `attempt_id` | Gates 2–11 | item 1 |
| Idempotency | Not a subject member | `idempotency_key` | Gates 2–11 | item 1 |
| Repository | `subject.repository_identity` | `repository_identity` | Gates 5/8/9 | item 2 |
| Task | `subject.task_id` + task snapshot | `task_id` | Gates 5/8/9 | item 2 |
| Phase/session | `governance_context` | `lifecycle_context` | Gates 5/8/9 | item 2 |
| Target | `subject.runtime_target_id` | `runtime_target_id` | Gates 2–11 | item 3 |
| Prompt | `subject.prompt_hash` | `prompt_hash` | Gates 1/5/8/9 | item 4 |
| Approval | `approval_id`/`record_digest` | `human_authority_binding` | Gates 3/5/9 | item 5 |
| PB request/decision | Not authority | request/decision digests | Gates 6/7/9 | item 6 |
| RE decision | Not authority | Projected evidence only | Gates 7/9 | item 7 |
| Dispatch state | Consumption rule | Not PB permission | Gates 9/10 | item 8 + events |

The "Approval" row's gate references change from v1.0 (`Gates 4/5/9`) to
`Gates 3/5/9` because approval creation is now gate 3, not gate 4. The
"Invocation" row's gate reference changes from v1.0 (`Gates 4–11`) to
`Gates 2–11` because `invocation_id` is minted at gate 2 alongside
`attempt_id`/`idempotency_key`, consistent with RPAC-REQ-025's canonical
`InvocationRequest` construction preceding approval. This is a necessary
consistency correction, not scope creep: it flows directly from repairing
Finding B-2, since all three identifiers are minted together at the same
gate.

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
`attempt_id` minted through a fresh gate 2 pass and, per RPAC-REQ-072, a new
invocation ID and fresh human approval whenever the prior approval's
attempt limit/expiry does not cover the retry (see §10a).

## 19. Security invariants

| Invariant | Contract owner | Failure behavior |
|---|---|---|
| No valid approval -> no real dispatch | RIHAC/RDGO gates 3/5 | Stop before PB/dispatch |
| Stale/mismatched approval -> no dispatch | RIHAC gate 5 | Fail closed; no rebinding |
| PB DENY/failure -> no dispatch | PBRD gate 6 | Stop |
| HUMAN_REVIEW without satisfied authority -> no dispatch | PBRD gate 6 | Stop |
| PB ALLOW without valid authority -> no dispatch | RDGO gates 5–7 | RE must deny/fail |
| Runtime unavailable/target mismatch -> no dispatch | Gates 4/8 | Stop; no fallback |
| Prompt/repo/task mismatch -> no dispatch | Gates 5/8 | Stop; new approval as required |
| Runtime Enforcement deny/failure -> no dispatch | Gate 7 | Stop |
| Containment not established -> no dispatch | Gate 8 | Stop |
| Durable marker not proven -> no dispatch | Gate 9 | Stop |
| Adapter cannot self-authorize | Gates 7/10 | Reject/security failure |
| Process permission does not imply completion | Gates 8/10 | Receipt/result evidence required |
| Dispatch completion does not accept change | Gate 11/intake | Existing review/promotion gates apply |
| Runtime result remains untrusted | Gate 11 | Evidence only |
| Runtime result cannot complete task | Task lifecycle | Explicit governed completion only |
| Duplicate/replayed `attempt_id` | Gate 9 | Hard collision; fail closed (RPAC-REQ-066) |
| Same `idempotency_key`, different canonical content presented | Gate 2/6 | Hard collision; fail closed (RPAC-REQ-066) |
| Reuse of a consumed `attempt_id` for a new try | Gates 2/9 | Rejected; new `attempt_id` and, where required, new approval mandatory |

## 20. Backward compatibility and no-go

The dry `adapter_invocation`/`simulation_only=true` path remains unchanged
and is not migrated into this sequence. Existing PB actions, Runtime
Enforcement evidence models, Phase 99 semantics, intake, mutation governance,
CHGR/IWC/HATP/HMIC/Class-B/CLTR, and runtime inspect are not modified.

This contract does not launch a process, implement a Shell Gate, activate
Runtime Enforcement, relax POL-005, register a real adapter, enable network,
access credentials, or modify runtime capability.

## 21. Versioning and freeze verdict

RDGO-001 uses contract `MAJOR.MINOR`. Per v1.0 §21, reordering gates is
incompatible and requires a new MAJOR with explicit migration and
independent verification — this is exactly why the gate 3/4 transposition
required by Finding B-149O.20L.7O.3V.1-1 is released as **v2.0**, not a
patch or minor revision, even though gate content, ownership, and count are
otherwise unchanged. Adding a later post-result gate may be additive only if
gates 1–11 and gate 10's first-effect boundary retain their meaning and
order. Merging authority/permission/enforcement/containment, moving the
durable marker after effect, weakening freshness, or widening effect scope
remains incompatible and requires a further new MAJOR with explicit
migration and independent verification.

Unknown versions fail closed.

**RDGO-001 v2.0: FROZEN for local-CLI-v1 contract purposes.**
**Gate count: 11 (unchanged). Durable-before-effect items: 8 (unchanged;
item 1 enriched, see §10a). TOCTOU facts: 7 (unchanged).**
**Real execution: UNAVAILABLE.**
