# RDGO-001 v3.1 — Runtime Dispatch Gate Ordering Contract

## Contract identity and status

**Contract:** RDGO-001
**Version:** 3.1
**Status:** FROZEN
**Frozen by:** Phase 149O.20L.7O.3W.1R.2B.1R.1 — Cross-Contract Runtime
Invocation Human-Principal Authentication Freeze Repair
**Correctively completed by:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R —
Trusted Approval Presentation Evidence and HPAC Proof-Lifecycle
Canonicalization Blocking Repair. V3.0 is retained because the eleven gates,
their order, and bind-at-5/consume-at-9 state machine are unchanged; this
correction supplies the canonical records those gates already required (§21).
**Normalized to v3.1 by:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 —
Runtime-Dispatch Contract Normalization Implementation. **v3.1 is a MINOR
clarification** (§21): it re-states verified behaviour and does not reorder
a gate, move the first-effect boundary, merge authority/permission/
enforcement/containment, weaken freshness, or widen effect scope. It
normalizes §4/§6/§16 sequence-3 *creation* narration to the verified
architecture (the HPAC-001 verifier's assurance-independent HPAC-REQ-054
step 10 creates the event at Gate 3; Gate 5 re-confirms it read-only —
finding V-2/V-3), adds the §8 Gate-6-owns-PB-policy clarifying sentence
(V-13-3-1), the §9 three-layer Gate-8 containment model (V-13-5-1), and the
§10 Gate-9 create-only-linearization + zero-I/O authority-generation-token
re-check model with its durable `HPAC-AUTHORITY-CONSUMPTION/2.1`
`authority_generation_binding` representation (V-15-1, after the
independently verified `.1R.15.2`/`.1R.15.3` Gate-9 repair).
**Supersedes:** RDGO-001 v1.0, v2.0, and v3.0-narration of sequence-3
creation. V2 proof verification/consumption lifecycle is incompatible with
v3 and has no migration. V1's gate 3/gate 4 relative order was
independently found to contradict RPAC-REQ-042 by Phase 149O.20L.7O.3V.1
(Finding B-149O.20L.7O.3V.1-1).
**Scope:** Future one-attempt local-CLI real-runtime dispatch ordering only.
**Related contracts:** RPAC-001 v1.0, RIHAC-001 v2.0, RIASC-001 v3.0,
HPAC-001 v2.1, PBRD-001 v2.1, Runtime Enforcement contracts, Phase 99 Execution Attempt
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

## 1. Frozen eleven-gate order (v3.0 — RPAC-REQ-042-consistent)

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

Gate 3 resolves canonical repository/task/invocation/prompt/target/effect/
scope/expiry/one-shot facts, presents their human-usable representation
through HPAC-001 v2.1's protected channel, persists and verifies exact
`HPAC-PRESENTATION-EVIDENCE/2.0`, and cryptographically binds its digest and
the identical `HPAC-APPROVAL-SUBJECT/2.0` digest into a fresh v2 challenge.
The trusted coordinator reserves approval/proof identities before the
ceremony. A distinct, non-defaultable act with mandatory UP and UV produces
an assertion; successful preliminary verification creates canonical
`HPAC-PROOF/2.0` plus lifecycle sequence 2 `PROOF_VERIFIED`. Only then may
the coordinator create the immutable RIASC-001 v3.0 approval.

**Sequence-3 creation (v3.1 normalization — V-2/V-3).** The HPAC-001 v2.1
verifier's assurance-independent HPAC-REQ-054 step 10 (`bind_gate5_canonical`)
creates HPAC lifecycle sequence 3 `PROOF_VERIFIED_AND_BOUND` at gate 3
(approval creation) time, binding the `HPAC-APPROVAL-SUBJECT/2.0` digest to
the proof/presentation/challenge. Gate 5 does **not** create this event;
gate 5 freshly **re-confirms** the current, byte-exact sequence-3 event
read-only (state, genesis binding triple, bound invocation, event digest)
and fails closed on any divergence (HPAC-REQ-097 — an already-present
byte-identical same-binding event is accepted idempotently). The
*assurance* decision — whether this authenticated principal may validate a
production approval — is gate 5's and gate 5's alone. The sequence-3 event
binds the `HPAC-APPROVAL-SUBJECT/2.0` subject digest fixed at gate 3, **not**
the completed RIASC-001 v3.0 approval `record_digest`; that record digest is
a separate commitment carried in the RIHAC-001 v2.0 validated-authority
projection and consumed at gate 9 (§10 item 5).

Agent-controlled stdout/stdin, caller-created evidence, and
blind touch are insufficient.

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
under v3.0. This is a deliberate consequence of RPAC-REQ-042's fixed order:
an approval that never reaches gate 6 because gate 4 failed is unconsumed,
imposes no cost beyond an unused artifact, and grants no capability by
itself (RIHAC-001 §1, §20 — approval never implies capability). Structural
unavailability still fails before Permission Broker, Runtime Enforcement,
containment, and dispatch in every case.

## 6. Gate 5 — approval validation

Gate 5 freshly resolves the canonical approval, HPAC proof, complete
hash-chained lifecycle, protected registry/configuration, canonical
presentation evidence, active presentation mechanism descriptor, and
mechanism attestation; then
executes RIHAC-001 v2.0's ordered validation and produces an ephemeral
validated-authority projection containing:

- approval ID/digest;
- complete subject/scope binding digest;
- authority projection ID/digest and `RIHAC-001/2.0`;
- proof-validation/request-binding/current-registry digests;
- provenance, UP, UV, trusted-presentation, domain, and replay verdicts;
- seven-condition freshness verdict and policy-refresh disposition;
- expiry verdict;
- consumption-state verdict; and
- validation timestamp/version.

It re-confirms (read-only) the current HPAC lifecycle sequence 3
`PROOF_VERIFIED_AND_BOUND` event created by the HPAC-001 v2.1 verifier's
HPAC-REQ-054 step 10 (§4), checking exact approval/proof/presentation/
challenge/subject/invocation binding, and does not consume the
approval, nonce, presentation, or proof. Repeating gate 5 before gate 9 is
permitted only when sequence 3 is byte-identical to the same binding and
repeats cryptographic/current-registry/descriptor/presentation/revocation/
consumption checks idempotently. Missing, stale, mismatched, expired,
revoked, consumed, replayed, tampered, caller-constructed, or ambiguous
evidence stops the flow. It does not produce PB ALLOW.

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

**PB policy ownership (v3.1 clarification — V-13-3-1).** PB policy
evaluation is owned exclusively by gate 6. Gate 7 (and gate 9) revalidate
*authority currentness and runtime-enforcement posture* — principal /
credential / proof / approval revocation, expiry, consumption state;
execution-availability and safety flags — using the PB decision, policy
IDs, policy version, and decision digest of item 2 as **inputs**. Neither
gate 7 nor gate 9 re-runs PB policy. A stale PB `policy_version` detected
after gate 6 is resolved by **re-entering gate 6**, not by any later gate;
a later gate MAY surface `policy_drift_requires_fresh_pb_re_evaluation` as
an **advisory reason only** — never a licence to skip a check and never a
basis for a positive decision. The reserved reason id
`gate7_pb_decision_stale_policy_version` marks a future-`Gate6Decision`-shape
concern and is not a prerequisite for any gate.

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

**Three-layer containment model (v3.1 normalization — V-13-5-1).** Gate 8's
containment establishment is layered:

(a) *direct validation* of executable identity/hash, argv, descriptor/config
digest, runtime target, repository-scope of the working directory,
environment-allowlist name well-formedness, the containment profile
(child-process policy, bounded resource/time/supervision references, network
denied, no credentials), and refusal of any caller-supplied shell/command
string;

(b) *canonical commitment* of the complete established launch environment —
including working-directory and environment-value bytes and the
contract-fixed `transport_type=local_cli` — into a single
`containment_evidence_digest` bound to the invocation;

(c) *gate-9 recomputation* — gate 9 independently re-derives the entire
containment evidence over freshly re-resolved inputs and fails closed on
any digest mismatch before consumption.

The effect plan handed to gate 8 is assembled by the trusted invocation
coordinator from the descriptor/config and never from caller input; there
is therefore no separate caller-supplied cwd / environment / transport
"reference" to diff against, and none is required. Working-directory and
environment substitution are caught by layer (c)'s full recomputation, not
by a direct reference diff.

## 10. Gate 9 — durable pre-dispatch record

Gate 9 atomically persists the minimum effect-bound evidence before process
creation. The exact nine items are (v3.1 — item 9 added; items 1–8
unchanged):

1. **Invocation identity:** `invocation_id`, this attempt's mandatory unique
   `attempt_id`, and the request's canonical `idempotency_key` — all three
   unconditional, never `attempt_id` "where used."
2. **Repository/task binding:** repository fingerprint, HEAD, task ID and
   task-contract digest, phase ID, and conditional session ID.
3. **Target binding:** exact runtime target plus adapter descriptor/config and
   live executable-identity observations.
4. **Prompt binding:** semantic prompt hash and hash-profile ID.
5. **Approval binding:** approval ID/digest, RIHAC v2 authority-projection
   ID/digest, HPAC proof ID/digest, presentation ID/digest, challenge and
   approval-subject digests, and proof-validation/current-registry digests,
   with approval, presentation, challenge, and bound proof atomically
   consumed by this write.
6. **PB binding:** PB request/decision digest, decision, policy version,
   causing policy IDs, and matched no-go IDs.
7. **Runtime Enforcement binding:** decision ID/digest, verdict, expiry, and
   evaluated-input digest.
8. **Dispatch intent/state:** exact containment evidence reference plus the
   durable state marker `dispatch_attempted` and its timestamp.
9. **Authority-generation binding (v3.1 — V-15-1):** the closed
   `HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0` object (HPAC-001 v2.1
   HPAC-REQ-098) — the monotonic principal / credential / approval /
   lifecycle / consumption generation tokens that gate 9 captured after the
   in-boundary revalidation battery (`S1`) and verified unchanged at the
   final zero-effectful-I/O re-read (`S2`) immediately before the atomic
   create. Each token is a digest/marker over durable state, restart-
   reconstructible, carrying no wall clock / nonce / process identity. It is
   **verification evidence, not execution authority** — possession or
   reconstruction grants nothing; a future gate 10 MUST re-read current
   canonical generation state and compare it against this durable snapshot
   (§10 last ¶; §11).

References and digests SHALL be used instead of duplicating the full
approval/PB/RE artifacts. These exact nine items are the closed objects of
HPAC-001 v2.1 §41's `HPAC-AUTHORITY-CONSUMPTION/2.1` (nine closed binding
objects; the eight of `/2.0` byte-unchanged plus `authority_generation_binding`),
canonically stored at the bound proof's protected `consumption.json` path.
A `/2.0` record (no `authority_generation_binding`) remains readable
historical/test data but is **not** eligible for a future gate 10; gate 9
writes only `/2.1`. It is one create-only, crash-consistent,
read-back-verified commit completed before gate 10; a repository-side
invocation record is a non-authoritative mirror/reference. If the protected
write cannot be proven durable and internally consistent, no dispatch
occurs.

**Gate-9 linearization semantics (v3.1 normalization — V-15-1).** The
per-`proof_id` create-only atomic primitive (`O_EXCL` temporary sibling +
atomic link-if-absent) **is** the linearization point and the single
transaction mechanism; there is no second global lock, advisory-lock
object, or transaction system (`.1R.9` §18). Immediately before that create:

- gate 9 re-runs the full revalidation battery — current registry,
  credential, descriptor/configuration, presentation, proof/lifecycle,
  approval/expiry, exact gate-5 sequence-3 binding, PB, Runtime Enforcement,
  and containment state (recomputed) — and fails closed on any divergence;
- gate 9 then captures a monotonic authority-generation snapshot `S1` (item
  9), and re-reads it as `S2` with **zero intervening effectful I/O**
  immediately before the create;
- any `S2 != S1` — a principal/credential revocation, a lifecycle
  invalidation, an approval-record change, or a consumption record appearing
  — fails closed with **no** `consumption.json` written.

This makes the validity check and the atomic consumption serialized with
respect to each other — the "no TOCTOU allowance" guarantee — to the
practical limit, without a second lock. A residual instruction-level
micro-window between the `S2 == S1` decision and the create is the
acknowledged practical limit; it produces no external effect (gate 10
absent; gate 10's mandatory re-read and re-validation re-close it — §11),
and the consumption race itself is fully closed (`O_EXCL` → duplicate →
deterministic `already_consumed`). Gate-5 validation is never a substitute
for this gate-9 revalidation.

`dispatch_attempted` is the single atomic presentation/challenge/proof/
approval consumption point and at-most-once guard. PB evaluation does not
consume any of them. It is not proof the external process was created or
completed.

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

**Gate-10 forward read-back prerequisite (v3.1 — prerequisite semantics
only; no gate-10 design, no phase ID).** `is_gate9_result(x) == True` is
**insufficient**. A future gate 10 MUST at minimum require, all together:

1. a trusted `Gate9Result` (`is_gate9_result`);
2. `x.status == "consumed"` (not `already_consumed`, not provenance alone);
3. a fresh re-read of the durable canonical `consumption.json`
   (`HPAC-AUTHORITY-CONSUMPTION/2.1`) + containment evidence, byte-verified
   against `x.record_digest`, with `authority_generation_binding` present
   and valid;
4. exact lineage / binding: `invocation_id` / `attempt_id` /
   `idempotency_key` / `proof_id` / `approval_id` match the durable record
   and the live request;
5. runtime capability eligible (execution availability, adapter
   registration, containment re-established) at gate-10 entry;
6. re-validation of all mutable authority (principal / credential / proof /
   approval / lifecycle) as-of gate-10 entry, **and** re-derivation of the
   current authority-generation vector and comparison against the durable
   `authority_generation_binding` snapshot — the V-15-1 second line of
   defence. Later principal / credential / approval / lifecycle changes do
   not erase the historical gate-9 consumption record, but they DO
   invalidate gate-10 eligibility and are detected here.

The durable authority-generation snapshot is data, not a bearer token:
possessing or reconstructing it grants no capability; gate 10 must re-read
current canonical state and compare.

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
| Authority-generation snapshot (v3.1) | Not authority — verification evidence | Not a PB fact | Gate 9 captures + commits; Gate 10 re-reads + compares | item 9 |

The "Approval" row's `Gates 3/5/9` references mean: sequence-3
`PROOF_VERIFIED_AND_BOUND` is **created** at gate 3 by the HPAC-001 v2.1
verifier's HPAC-REQ-054 step 10 (§4), **re-confirmed read-only** at gate 5,
and **consumed** at gate 9 (v3.1 — V-2/V-3). The gate references change from
v1.0 (`Gates 4/5/9`) to `Gates 3/5/9` because approval creation is now gate
3, not gate 4. The
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
| `PRE_APPROVAL_CONSUMPTION` | Gates 1–8 may have progressed; no canonical HPAC consumption record | None | Same approval only after full revalidation and consumption path absent |
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
9, the presence of one valid HPAC-001 §41 consumption record rejects replay;
any failed, uncertain, or proven-not-started new attempt requires a new
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

RDGO-001 uses contract `MAJOR.MINOR`. V3 retains the eleven gates and their
order, but incompatibly changes load-bearing gate 3/5/9 semantics: v2 can
consume the HPAC nonce at gate 5, while v3 binds/revalidates at gate 5 and
atomically consumes approval plus proof only at gate 9. A v2 implementation
cannot conform without state-machine change, so a MAJOR is required and no
migration exists. Adding a later post-result gate may be additive only if
gates 1–11 and gate 10's first-effect boundary retain their meaning and
order. Merging authority/permission/enforcement/containment, moving the
durable marker after effect, weakening freshness, or widening effect scope
remains incompatible and requires a further new MAJOR with explicit
migration and independent verification.

Unknown versions fail closed.

**Corrective v3.0 completion:** this phase does not add, remove, reorder, or
reassign a gate and does not move the first-effect boundary. It defines the
previously missing HPAC lifecycle and the single gate-9 record needed to
implement v3's already-mandatory bind-at-5/consume-at-9 semantics. No
conforming pre-correction v3 lifecycle artifact existed, so there is no
artifact migration or compatible predecessor to preserve. Retaining v3.0 is
the repository-correct repair of the rejected candidate rather than a new
state machine.

**v3.1 normalization (Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4) — MINOR.**
v3.1 does not add, remove, reorder, or reassign a gate, does not move the
first-effect boundary, does not merge authority/permission/enforcement/
containment, does not weaken freshness, and does not widen effect scope.
It re-states verified behaviour: §4/§6/§16 sequence-3 *creation* narration
(the verifier's HPAC-REQ-054 step 10 creates the event at gate 3, gate 5
re-confirms — V-2/V-3; the state machine and event bytes are unchanged,
HPAC-001 v2.1 HPAC-REQ-095/097 already accommodate the idempotent-accept
path); the §8 Gate-6-owns-PB-policy sentence (V-13-3-1 — a restatement of
the existing §7/§15 division); the §9 three-layer Gate-8 containment model
(V-13-5-1 — codifies verified repo-scope + digest-commitment + gate-9
recomputation); and the §10 Gate-9 create-only-linearization + zero-I/O
authority-generation-token re-check model with its durable
`HPAC-AUTHORITY-CONSUMPTION/2.1` item-9 representation (V-15-1 — a
*strengthening* that matches the independently verified `.1R.15.2`/`.1R.15.3`
repaired code, not a weakening). Durable-before-effect items go 8 → 9
(item 9 added; items 1–8 byte-unchanged). No conforming pre-normalization
consumption artifact carrying the old sequence-3-creation narration or a
`/2.0` record with a durable generation snapshot ever existed, so there is
nothing to migrate; a `/2.0` record without `authority_generation_binding`
is readable historical/test data and gate-10-ineligible. A change that
alters external trust semantics, the required authority shape
incompatibly, or consumption-record compatibility fundamentally still
requires a new MAJOR.

**RDGO-001 v3.1: NORMALIZED AND FROZEN; v2 proof-lifecycle semantics and
v3.0 sequence-3-creation narration have no migration.**
**Gate count: 11 (unchanged). Durable-before-effect items: 9 (v3.1 — item
9 added; item 1 enriched, see §10a). TOCTOU facts: 7 (unchanged).**
**Real execution: UNAVAILABLE.**
