# Phase 149O.20L.7O.3V.1R — Local-CLI Runtime Dispatch Authority and Permission Contract Reconciliation and Repair

## Objective

Repair exactly the two BLOCKING contract defects independently identified by
Phase 149O.20L.7O.3V.1 against the four contracts frozen by Phase
149O.20L.7O.3V — without redesigning the architecture, without implementing
any source, and without activating real dispatch. This is a bounded contract
reconciliation and repair, not a second 3U.

## Baseline

| Fact | Value |
|---|---|
| Phase-entry `HEAD` / `origin/main` | `6933f6e033ba89647889ad1a6343faf37609c26c` |
| `origin/main..HEAD` at entry | `0` |
| Worktree | Clean before governed phase startup |
| `v0.4.3` release commit | `63580893b1de4782a694ab802ff7bdebdf29b0e6` (unchanged) |
| Runtime | `Observed` / `observe` / `unavailable`; registry 0/0 |
| Health/check/coherence | healthy / passed / coherent |
| Push check | clean; nothing to push |
| Telegram | configured / enabled / outbound-ready |
| `pcae doctor task-memory` | only pre-existing historical `tasks/DONE.md` sync warnings, unrelated to this phase |

## 3V.1 blocker recovery (verbatim substance)

Recovered directly from
`docs/PHASE_149O_20L_7O_3V_1_INDEPENDENT_VERIFICATION_LOCAL_CLI_RUNTIME_DISPATCH_AUTHORITY_PERMISSION_CONTRACT_FREEZE.md`,
not from summary prose:

**BLOCKING B-149O.20L.7O.3V.1-1 — RDGO gate order contradicts RPAC.**
RPAC-REQ-042 freezes step 3 = "obtain human InvocationApproval" and step 4 =
"resolve descriptor/config and perform fact-only status/capability
preflight." RDGO-001 v1.0 froze gate 3 = static preflight and gate 4 = human
authority creation — a direct relative-order reversal. RPAC-REQ-093 requires
a new major version for any changed gate order; neither an RPAC amendment
nor a major migration existed. Required repair: choose and normatively
reconcile one order, version the authoritative contract consistently, update
EAB mapping if needed, and independently reverify.

**BLOCKING B-149O.20L.7O.3V.1-2 — PB/durable request identity is
incomplete.** RPAC-REQ-025 requires every canonical `InvocationRequest` to
carry `invocation_id`, unique `attempt_id`, and `idempotency_key`.
RPAC-REQ-044 names the missing idempotency binding as part of the gap to
close. RPAC-REQ-064–068 make attempt identity/idempotency central to
collision, resume, and ambiguous-dispatch safety. PBRD-001 v1.0's twelve
facts contained `invocation_id` but neither `attempt_id` nor
`idempotency_key`; RDGO-001 v1.0 durable item 1 weakened attempt identity to
`attempt_id where used` and never bound idempotency. Required repair: restore
unconditional attempt identity and canonical idempotency binding across the
PBRD request, RDGO durable/RE projection, and identifier matrices; update the
declared count honestly if it changes from twelve.

## RPAC-REQ-042 (exact authority for the gate-order repair)

Quoted verbatim from `docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md`:

```text
1. resolve authoritative repository/task/session and create PromptArtifact;
2. construct immutable request and explicit target selection;
3. obtain human InvocationApproval;
4. resolve descriptor/config and perform fact-only status/capability preflight;
5. obtain Permission Broker permission for adapter dispatch and each requested
   effect class;
6. revalidate mutable status/config/HEAD facts for freshness;
7. obtain the final Runtime Enforcement decision immediately before dispatch;
8. durably create the attempt record and atomically mark dispatch intent;
9. call the one selected adapter;
10. capture result and submit any proposed changes through generic intake.
```

Required gate sequence: approval strictly precedes fact-only preflight, both
strictly precede Permission Broker, which strictly precedes Runtime
Enforcement, which strictly precedes the durable record and dispatch.
Effect-boundary placement (RPAC-REQ-042 step 9) is unaffected by the repair.
Durability implication (RPAC-REQ-087): a durable pre-dispatch record and a
one-attempt authority envelope must exist before the effect boundary.

## Related RPAC requirements inspected

- **Attempt identity:** RPAC-REQ-064 — opaque, cryptographically strong
  `invocation_id`, never timestamp-derived; each dispatch try has a unique
  `attempt_id` linked to the logical invocation.
- **Idempotency:** RPAC-REQ-065 — SHA-256 digest of canonical, versioned
  request content excluding timestamps and attempt-specific mutable
  observations.
- **Collision/resume:** RPAC-REQ-066 — same invocation ID + identical
  canonical content resumes without redispatch; same invocation ID +
  different content is a hard collision that fails closed.
- **Approval:** RPAC-REQ-022/023 — approval binds prompt digest,
  repository/task, target/config digest, effect profiles, budget, expiry,
  and attempt limit — not a specific `attempt_id`.
- **PB:** RPAC-REQ-025/044 — canonical `InvocationRequest` must carry
  `attempt_id`/`idempotency_key`; existing PB vocabulary is insufficient
  until this gap is closed.
- **Runtime Enforcement:** RPAC-REQ-045/046 — final whether-to-invoke gate,
  evaluating the complete bound request including identity facts.
- **Durable-before-effect:** RPAC-REQ-067/087 — persistent
  `RuntimeInvocationRecord` conceptually includes invocation and attempt IDs
  and idempotency key before any effect.
- **Dispatch/retry:** RPAC-REQ-068/071/072 — restart before dispatch resumes
  validation without dispatch; every retry requires a new attempt ID, fresh
  PB/RE decisions, and human authorization when the prior approval does not
  cover it; a changed prompt/target/provider/model/repository/task/effects/
  budget requires a new logical invocation and approval.

## PBRD omission analysis (pre-repair)

PBRD-001 v1.0's twelve facts bound `invocation_id`, `repository_identity`,
`task_id`, `lifecycle_context`, `runtime_target_id`,
`adapter_descriptor_binding`, `prompt_hash`, `requested_capability`,
`transport_type`, `network_requirement`, `filesystem_scope_ref`, and
`human_authority_binding`. Neither `attempt_id` nor `idempotency_key` existed
as independent fields, as derived values, or as references — they were
simply absent, unconditionally required by RPAC-REQ-025 but never
represented.

## `attempt_id` semantics (frozen)

`attempt_id` identifies exactly **one concrete dispatch try** under one
logical invocation. It is distinct from:

- `invocation_id` — the stable logical invocation spanning possibly multiple
  attempts;
- `approval_id` — the human-authority artifact's own identity;
- the durable dispatch record's own identity — RPAC-REQ-067 does not mint a
  separate record ID; the record is keyed by `(invocation_id, attempt_id)`;
- `task_id` — the PCAE task, unrelated to dispatch-try granularity; and
- `idempotency_key` — the logical-content identity (below), not the
  concrete-try identity.

No ambiguous synonymy exists among these five identifiers.

## `attempt_id` ownership

`attempt_id` is minted exclusively by the trusted PCAE invocation
coordinator (RDGO-001 gate 2), from cryptographically strong random
identity, using the convention `att-<32-hex>`. It SHALL NOT be selected,
echoed back, or overwritten by the adapter, runtime, provider, or task
content — the same construction-time trust rule PBRD-001 already applied to
its other eleven facts.

## `attempt_id` binding

`attempt_id` binds to: the invocation (via `invocation_id`), the PB request
(new PBRD field 2), the Runtime Enforcement projection (carries all
fourteen PBRD facts), the durable pre-dispatch record (RDGO item 1,
unconditional), and the dispatch envelope/receipt (RPAC-REQ-029/031). It does
not bind to the human-authority subject itself (RIHAC/RIASC unchanged — see
below) and does not bind to the repo/task identity beyond the existing
`invocation_id`/`task_id` bindings.

## `idempotency_key` semantics (frozen)

`idempotency_key` identifies **which logically identical dispatch request**
is being deduplicated or replay-protected — not which concrete attempt. It is
a pure function of canonical, versioned request content (repository
fingerprint/base commit, `task_id`, `prompt_hash`, `runtime_target_id`,
adapter/descriptor/config digests, requested effect profiles, approval
scope) excluding timestamps and attempt-specific mutable observations, per
RPAC-REQ-065 exactly. It is not confused with attempt identity: two attempts
of the same unchanged logical request share one `idempotency_key` but each
has its own unique `attempt_id`.

## `idempotency_key` derivation/ownership

Generated (SHA-256 digest), not caller-supplied, computed by the trusted
PCAE invocation coordinator at RDGO-001 gate 2 — PCAE-owned semantics only,
with no external-runtime authority over its value.

## `attempt_id` vs `idempotency_key` (frozen distinction)

```text
attempt_id:        identifies one concrete dispatch try
idempotency_key:   identifies the logical dispatch operation whose
                    canonical content this attempt (and any safe retry
                    of it) shares
```

This matches RPAC-REQ-064/065/072 exactly; no invented wording was needed.

## Retry relationship (frozen)

A genuine retry of the same logical invocation (unchanged repository/task/
base, prompt, target, effects, budget; still within the prior approval's
`attempt_limit`/expiry) mints a **new `attempt_id`** at a fresh gate-2 pass
while the **`idempotency_key` remains identical** (canonical content
unchanged). Any change to prompt, target, provider/model, repository/task,
effects, or budget mints **both** a new `invocation_id` and a new
`idempotency_key`, and requires a fresh human approval; `attempt_id` is new
by construction in either case. There is no path in which only
`idempotency_key` changes while `invocation_id`/approval remain the same.

## Crash/uncertain relationship (frozen)

Once gate 9 durably records `dispatch_attempted` for a given `attempt_id`,
that attempt is consumed regardless of whether gate 10 is later proven never
to have started (`DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER`) or remains
unprovable (`DISPATCH_UNCERTAIN`). Neither state permits reuse of that
`attempt_id`. A same-`idempotency_key` retry after an uncertain or
not-started attempt still requires a brand-new `attempt_id` minted through a
fresh gate-2 pass and a fresh human approval — the surviving
`idempotency_key` never by itself authorizes redispatch.

## PBRD repair

PBRD-001 is repaired to **v1.1**. Two new mandatory facts are added:
`attempt_id` (`att-<32-hex>`, PCAE-coordinator-owned) and `idempotency_key`
(64-lowercase-hex SHA-256, PCAE-coordinator-owned, RPAC-REQ-065-derived). No
existing fact's meaning, type, source, or trust owner changed. A new §4a
freezes their construction point (gate 2, before approval) and ownership. §15
(security invariants) gained rows for caller-attempted tampering and
attempt/idempotency collision. §13 explicitly excludes the dry
`adapter_invocation` path from carrying these new facts (they are
runtime-dispatch-specific).

## PB field cardinality

```text
PRE-REPAIR COUNT:  12
POST-REPAIR COUNT: 14
WHY CHANGED: attempt_id and idempotency_key are unconditionally mandatory
  under RPAC-REQ-025/064/065 and were simply absent from the v1.0 table;
  Finding B-2 requires restoring them, not inventing new semantics.
```

The old twelve-fact count is explicitly superseded; every "twelve facts"
reference in PBRD-001 now reads "fourteen facts."

## RIHAC impact

**RIHAC-001 remains v1.0, UNCHANGED in substance.** Justification: the
approval subject is exactly the five-member
`(invocation_id, runtime_target_id, prompt_hash, repository_identity,
task_id)` tuple; RIHAC's one-shot rule already caps consumption to at most
one attempt via `attempt_limit`/`dispatch_limit = 1` (§4), without needing to
name a specific `attempt_id` in advance — the human approves *that one
invocation gets one attempt*, and the coordinator mints the concrete
`attempt_id` for that attempt at gate 2/9. Binding approval directly to a
pre-minted `attempt_id` would be a widening of the subject not required by
RPAC (RPAC-REQ-022 lists what an `InvocationApproval` binds, and it does not
list `attempt_id`). Only the header's cross-reference line (`Related
contracts:` version numbers) was updated to point at PBRD-001 v1.1 /
RDGO-001 v2.0, plus one reference note explaining why RIHAC itself did not
change. This is a citation correction, not a semantic RIHAC change, and
required no version bump.

## RIASC impact

**RIASC-001 remains v1.0, UNCHANGED in substance.** The sixteen required
fields, exact five-member `subject`, and `attempt_limit: {"const": 1}`
already correctly express one-invocation/one-attempt-slot binding without
needing `attempt_id`/`idempotency_key` in the schema: those are
dispatch-layer identifiers that belong in the PBRD-001 request and future
`RuntimeInvocationRecord`, not in the human-authority artifact. Adding them
to RIASC would be unnecessary schema widening the two findings do not
require. Only a reference note was added near the header explaining this
determination; no version bump.

## RDGO impact / repair

RDGO-001 is repaired to **v2.0** (MAJOR, per its own v1.0 §21 rule that
reordering requires a new major version). Gates 3 and 4 are transposed:
gate 3 is now human authority creation, gate 4 is now static preflight —
an exact, minimal, single-swap match to RPAC-REQ-042's steps 3/4. No other
gate's number, owner, content, or the eleven-gate count changed. Durable
item 1 was enriched (not counted as a new item) to bind `attempt_id` and
`idempotency_key` unconditionally alongside `invocation_id`, replacing the
weaker "`attempt_id` where used" language. A new §10a freezes attempt/
idempotency semantics, ownership, binding, and retry/crash behavior in one
place, cross-referenced by PBRD.

## Contract versioning (repository-precedent-based determination)

RDGO-001 v1.0 §21 states verbatim: *"Reordering, merging authority/
permission/enforcement/containment, moving the durable marker after effect,
weakening freshness, or widening effect scope is incompatible and requires
a new MAJOR with explicit migration and independent verification."* The
gate 3/4 transposition is exactly a reordering. Repository precedent (e.g.
RIHAC-001 §21, PBRD-001 §16) uniformly treats a contract's own declared
versioning rule as authoritative for that contract's evolution. Therefore
**RDGO-001 -> v2.0** is the only repository-correct choice; a silent v1.0
edit or a v1.1 minor bump would both violate the contract's own frozen
compatibility rule.

PBRD-001 v1.0 §16 states: *"Additive request evidence may increment MINOR
only when existing meanings, action behavior, and precedence remain
unchanged."* Adding `attempt_id`/`idempotency_key` as new mandatory facts
changes no existing fact's meaning, does not widen action semantics, does
not change the execution class, does not weaken POL-005 eligibility, and
does not alter DENY > HUMAN_REVIEW > ALLOW precedence. This is exactly the
additive case PBRD's own rule reserves for a MINOR bump. Therefore
**PBRD-001 -> v1.1** is the repository-correct choice.

RIHAC-001 §21 and RIASC-001 §1 both gate a MAJOR bump on subject-member
removal/widening, required-field removal, or authority/scope broadening.
Neither occurred; both remain **v1.0**.

## Pre-repair RDGO (11 gates, as frozen by 3V)

```text
1  Prompt preparation
2  Explicit target selection
3  Static preflight                <- conflicted with RPAC-REQ-042
4  Human authority creation        <- conflicted with RPAC-REQ-042
5  Approval validation
6  Permission Broker
7  Runtime Enforcement
8  Process containment + live preflight
9  Durable pre-dispatch record
10 Adapter dispatch (first external effect)
11 Result capture and intake
```

## RPAC-compliant ordering (derived)

RPAC-REQ-042's ten steps map onto RDGO's eleven gates by splitting step 3
("obtain human InvocationApproval") into creation (gate 3) and validation
(gate 5, additive detail RPAC does not forbid), and step 2 ("construct
immutable request and explicit target selection") into target selection plus
request-identity minting (gate 2, now also responsible for `attempt_id`/
`idempotency_key`). The derived, RPAC-consistent order is:

```text
1  Prompt preparation
2  Explicit target selection and request construction (mints invocation_id,
   attempt_id, idempotency_key)
3  Human authority creation                              <- moved up
4  Static preflight                                       <- moved down
5  Approval validation
6  Permission Broker
7  Runtime Enforcement
8  Process containment + live preflight
9  Durable pre-dispatch record
10 Adapter dispatch (first external effect)
11 Result capture and intake
```

Gate count is preserved at eleven; the minimal one-swap change resolves the
contradiction without merging, splitting, or removing any other gate.

## Contradiction root cause

3U/3V explicitly reasoned that static preflight should precede human
approval "so PCAE does not ask a human to approve a target that is
structurally incapable" — an efficiency/UX rationale. RPAC-001 v1.0,
frozen earlier, fixes the opposite order (approval before preflight) and
RPAC-REQ-093 requires a major version for any gate-order change. 3U/3V did
not amend RPAC or declare a migration; they simply froze RDGO with the
efficiency-motivated order, producing a direct, undetected contradiction
with the still-controlling RPAC-001 text. The root cause is authority
precedence: RDGO cannot silently redefine an order RPAC already fixed.

## RDGO repair (applied)

Only gates 3 and 4 were transposed. Gates 1, 2, 5, 6, 7, 8, 9, 10, and 11
retain their exact number, owner, input, output, and content. The gate-3
section now states explicitly that approval creation does not certify
capability, so a target that later fails gate-4 static preflight simply
never reaches gate 9 (its approval is unconsumed, at no security cost). The
gate-4 section's rationale sentence was rewritten to remove the
"before approval" framing and describe the RPAC-mandated post-approval
placement instead.

## Gate cardinality

```text
PRE-REPAIR:  11
POST-REPAIR: 11
WHY UNCHANGED: the repair is a minimal transposition of two adjacent gates,
  not a merge, split, or removal. RPAC-REQ-042 itself enumerates ten steps
  that already accommodate RDGO's finer eleven-gate split; no additional
  gate was required to restore compliance.
```

## Approval creation/validation ordering (verified against RIHAC)

Gate 3 (create) still immediately precedes gate 5 (validate), with static
preflight (gate 4) interposed between them. RIHAC-001 §16's validation order
is unaffected: it still executes after an approval artifact exists,
regardless of whether static preflight has already run. No approval is
consumed before gate 9 in either ordering.

## PB ordering (verified against PBRD)

Gate 6 (Permission Broker) still receives the complete, now-fourteen-fact
immutable request, including the validated-authority projection from gate 5
and the `attempt_id`/`idempotency_key` minted at gate 2. PBRD's gate
independence rules (§10) are unaffected by the gate 3/4 transposition, since
neither gate is between gate 5 and gate 6.

## Runtime Enforcement ordering (verified against RPAC-045/046 and RE)

Runtime Enforcement remains the final whether-to-invoke gate (gate 7),
strictly after human approval, target facts (now gate 4, still before gate
7), and Permission Broker (gate 6), and strictly before any adapter effect
(gate 10). No missing authority inference is introduced; RE still evaluates
the complete bound request including all fourteen PBRD facts.

## Containment ordering

Shell Gate/equivalent process containment remains gate 8, strictly after
Runtime Enforcement (gate 7) and strictly before the durable record (gate 9)
and dispatch (gate 10). No external effect precedes containment in either
the pre- or post-repair ordering.

## Durable-before-effect ordering

Gate 9 remains the exclusive durable-before-effect boundary, still strictly
before gate 10 (first external effect). Item 1 is enriched (unconditional
`attempt_id`/`idempotency_key`), all other items and their position are
unchanged.

## Approval consumption point (reconfirmed)

Approval consumption still occurs exactly at gate 9's atomic
`dispatch_attempted` transition (RIHAC-001 §17, unchanged; RDGO-001 §10,
unchanged position). The gate 3/4 transposition does not move consumption:
gate 3 (create) is even further from gate 9 than before in gate-count terms,
but consumption remains defined solely by reaching gate 9, not by gate
distance. No contradiction between RIHAC and RDGO was created.

## First external effect

Gate 10 (adapter dispatch) remains the sole first-external-effect gate
across RPAC (step 9 of 10), RDGO (§1, §11), PBRD (§3, "external process
shall be created only after RDGO-001 gates 1–9 succeed"), and RIHAC
(consumption model, §17). All four artifacts agree.

## At-most-once consistency (re-run under repaired ordering)

No exactly-once claim exists. `DISPATCH_ATTEMPTED`,
`DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER`, and `DISPATCH_UNCERTAIN` remain
the three post-gate-9 states (RDGO §17, unchanged). The repaired
`attempt_id`/`idempotency_key` semantics (§10a) now make the safety
argument sound: a crash after gate 9 can be reasoned about in terms of one
uniquely identified `attempt_id`, and any safe retry is provably a new
`attempt_id` under the same or a fresh `idempotency_key` per the retry rule
above — closing the exact gap RPAC-REQ-066/072 required and 3V.1 found open.

## Cross-contract identifier reconciliation

Required concepts and consistency after repair:

| Concept | RPAC | RIHAC | RIASC | PBRD | RDGO |
|---|---|---|---|---|---|
| `invocation_id` | REQ-025 | `subject.invocation_id` | `subject.invocation_id` | field 1 | gates 2–11 |
| `attempt_id` | REQ-025/064 | not a subject member (by design) | not present (by design) | field 2 | gates 2–11 (§10a) |
| `idempotency_key` | REQ-025/065 | not a subject member (by design) | not present (by design) | field 3 | gates 2–11 (§10a) |
| `repository_identity` | REQ-025 | `subject.repository_identity` | `subject.repository_identity` | field 4 | gates 5/8/9 |
| `task_id` | REQ-025 | `subject.task_id` | `subject.task_id` | field 5 | gates 5/8/9 |
| `prompt_hash` | REQ-021 | `subject.prompt_hash` | `subject.prompt_hash` | field 9 | gates 1/5/8/9 |
| `runtime_target_id` | REQ-025 | `subject.runtime_target_id` | `subject.runtime_target_id` | field 7 | gates 2–11 |
| approval reference | REQ-022 | `approval_id`/digest | `approval_id`/`record_digest` | field 14 | gates 3/5/9 |
| PB decision | REQ-025 | not authority | absent | request/decision digests | gates 6/7/9 |
| RE decision | REQ-045 | not authority | absent | projection only | gates 7/9 |

Consistent. No naming drift, no duplicated authority meaning.

## Terminology reconciliation

`invocation` (logical, spans attempts), `attempt` (one concrete dispatch
try), `dispatch` (the gate-10 external effect), `execution` (informal
synonym for dispatch effect, not separately defined), `retry` (a new
`attempt_id` under RPAC-REQ-072 rules), `replay` (an attacker or
implementation error presenting stale/duplicate identity — always rejected,
never a legitimate retry path), `idempotency` (the `idempotency_key`-based
deduplication of logically identical requests) are used consistently across
all five contracts with no collision.

## HUMAN_REVIEW/POL-005 boundary

PBRD §8 (HUMAN_REVIEW semantics) and §12 (POL-005 evolution boundary) are
unchanged in substance; §12's numbered prerequisite list was updated only to
say "all fourteen request facts" and "RDGO-001 v2.0 projection" instead of
twelve/v1.0. POL-004/HUMAN_REVIEW and POL-005/`ExecutionDisabledRule`
production behavior is unaffected — confirmed by rerunning the existing
direct-source PB tests referenced below.

## Dry compatibility

PBRD §13 explicitly states the dry path SHALL NOT be required to carry
`attempt_id`/`idempotency_key`: those are runtime-dispatch-specific facts
that do not apply to `adapter_invocation`'s existing shape. The production
dry consumer (`src/pcae/core/runtime_adapter.py`) is untouched — verified by
`git diff --stat` showing zero changes under `src/pcae/`.

## Existing PB compatibility

Rollback, push, publication, and other mutation-root PB actions are
unaffected: PBRD's fourteen facts are scoped to the future `runtime_dispatch`
action only (§1, §13). No other action gained new required fields.

## Shared request-shape optionality

If a future implementation represents `runtime_dispatch` and other actions
through one shared `PermissionBrokerRequest` shape, `attempt_id`/
`idempotency_key` (like the other twelve runtime-dispatch facts) should be
represented as an optional, action-specific nested payload (e.g. a
`runtime_dispatch_binding` sub-object) rather than universal optional top-
level fields on every action. This is a freeze of expectation for a future
implementer, not an implementation.

## Existing MUST-FIX findings (pre-existing, not caused by 3V.1 or 3V.1R)

Recovered again, unrepaired, unaffected by this contract-only repair:

1. Malformed adapter result crashes uncaught instead of failing closed
   cleanly (`simulate_invocation` / `store.write_result`). **BLOCKING BEFORE
   the first non-mock adapter implementation or registration/availability
   claim.**
2. `RuntimeInvocationStore` does not sanitize `invocation_id` against path
   traversal. **BLOCKING BEFORE any externally influenced invocation-ID,
   resume, retry, or storage-lookup surface, and no later than real-
   invocation persistence hardening.**

## Runtime inspect limitation

Disposition remains `TRUTHFUL_WITH_LIMITATION`, unchanged. This repair adds
no field to `pcae runtime inspect` and does not touch the dry consumer's
transient registry/persisted-registry disconnect.

## API/network boundary

Remains `NOT FROZEN` / `NOT READY`. This repair does not address Network
Egress Permission Architecture.

## Security invariants (revalidated)

All prior invariants (RIHAC §20, PBRD §15, RDGO §19) hold under the repaired
ordering and identifiers. Two new rows were added to PBRD §15 and three to
RDGO §19 covering caller-attempted `attempt_id`/`idempotency_key` tampering
and duplicate/replayed identity — see the Replay threat model below for the
adversarial cases these rows close.

## Replay threat model

| Scenario | Required result | Contract mechanism |
|---|---|---|
| Same `attempt_id`, modified payload | Reject | RPAC-REQ-066 hard collision; PBRD §15 "same `attempt_id` with different canonical content" |
| Same `idempotency_key`, new target | Reject as new logical invocation | `idempotency_key` is a function of `runtime_target_id`; a new target necessarily produces a different key, so a caller claiming the same key with a new target fails digest recomputation |
| Same `idempotency_key`, new prompt | Reject as new logical invocation | Same mechanism; `prompt_hash` is a digest input |
| New `attempt_id` with stale approval | Reject | RIHAC/RDGO freshness rules (gate 5); a new attempt does not refresh a stale approval |
| Replay of old PB ALLOW | Reject | PBRD §10/RDGO §15 — PB decisions expire with any relevant drift, including a changed `attempt_id` |
| Replay after uncertain dispatch | Reject; new attempt/approval required | RDGO §10a crash/uncertainty rule; no automatic retry |

## TOCTOU reconciliation

`attempt_id`/`idempotency_key` are explicitly **not** added as new TOCTOU
mutable facts: both are minted once at gate 2 and held immutable through
gate 11 (RDGO §10a), so they are identity, not drifting state. The seven
TOCTOU facts are therefore unchanged in count and content; RDGO §15 states
this exclusion explicitly to prevent future ambiguity.

```text
TOCTOU FACTS — PRE-REPAIR: 7  POST-REPAIR: 7  WHY UNCHANGED: attempt/
idempotency identity is immutable per-request identity, not mutable
environmental state subject to drift.
```

## Durable-item reconciliation

```text
DURABLE ITEMS — PRE-REPAIR: 8  POST-REPAIR: 8  WHY UNCHANGED: item 1 was
enriched (invocation_id + unconditional attempt_id + idempotency_key)
rather than split into a new item; this closes Finding B-2's durable-record
gap without inventing a ninth item.
```

## Cardinality reset (mandatory full re-derivation)

| Contract set | Pre-repair | Post-repair | Reason |
|---|---:|---:|---|
| PB request facts | 12 | 14 | Finding B-2: `attempt_id`, `idempotency_key` added |
| RDGO gates | 11 | 11 | Minimal transposition of gates 3/4; no merge/split/removal |
| Durable-before-effect items | 8 | 8 | Item 1 enriched, not split |
| TOCTOU facts | 7 | 7 | Attempt/idempotency identity is immutable, excluded by design |
| RIASC required fields | 16 | 16 | RIASC unchanged — attempt/idempotency belong to PBRD/RDGO, not the approval schema |
| RIASC subject fields | 5 | 5 | Unchanged — approval binds invocation, not attempt |
| Approval-subject fields | 5 | 5 | Unchanged, same as RIASC subject |

## RIASC revalidation

Fresh static schema tests were rerun against the unchanged embedded schema:
schema validity, one positive canonical instance, rejection of every missing
required field, rejection of unknown fields, rejection of authority-shortcut
fields, and independent mismatch detection for each of the five subject
members. All pass (see Testing below); the schema text itself did not
change, so this is a revalidation, not a new result.

## Contract consistency suite

`tests/test_phase_149o_20l_7o_3v_1r_contract_repair.py` (21 tests, all
passing) proves: PBRD completeness (14 facts, correct order, ownership
rules); RDGO/RPAC compatibility (gates 3/4 transposed to match
RPAC-REQ-042 literally); RIHAC/RIASC compatibility (unchanged, cross-
references updated); identifier consistency (cross-contract matrix rows);
dry compatibility (dry path excluded from new facts); PB vocabulary
compatibility (no production source touched); and that no new contradictions
were introduced (semantic walls, POL-005, gate 10 first-effect boundary,
no-go statements all still present).

## Cross-contract matrix

| Concept | RPAC | RIHAC | RIASC | PBRD | RDGO | Consistent? |
|---|---|---|---|---|---|---|
| `invocation_id` | Yes | Yes | Yes | Yes | Yes | Yes |
| `attempt_id` | Yes | N/A by design | N/A by design | Yes | Yes | Yes |
| `idempotency_key` | Yes | N/A by design | N/A by design | Yes | Yes | Yes |
| `repository_identity` | Yes | Yes | Yes | Yes | Yes | Yes |
| `task_id` | Yes | Yes | Yes | Yes | Yes | Yes |
| `runtime_target_id` | Yes | Yes | Yes | Yes | Yes | Yes |
| `prompt_hash` | Yes | Yes | Yes | Yes | Yes | Yes |
| Approval reference | Yes | Yes (native) | Yes (native) | Yes | Yes | Yes |
| PB decision | Yes | Not authority | Absent | Native | Yes | Yes |
| RE decision | Yes | Not authority | Absent | Projection | Native | Yes |
| Gate-3/4 order | Fixed (REQ-042) | N/A | N/A | N/A | Now matches | Yes |

## Gate matrix (repaired, final)

| # | Gate | RPAC basis | Owner | Input | Output | External effect? |
|---:|---|---|---|---|---|---|
| 1 | Prompt preparation | step 1 | Trusted prompt builder | Task instructions/context | Prompt artifact + hash | No |
| 2 | Target selection + request construction | steps 2 | Target selector + invocation coordinator | Operator target selection | `runtime_target_id`; `invocation_id`/`attempt_id`/`idempotency_key` | No |
| 3 | Human authority creation | step 3 | Identified human + approval coordinator | Approval preview | `RuntimeInvocationApproval` | No |
| 4 | Static preflight | step 4 | Registry + preflight coordinator | Target descriptor/config | Static capability evidence | No |
| 5 | Approval validation | implicit (before step 5) | RIHAC validator | Approval ref + current state | Validated-authority projection | No |
| 6 | Permission Broker | step 5 | PB Foundation + PBRD | Fourteen-fact request + projection | ALLOW/DENY/HUMAN_REVIEW | No |
| 7 | Runtime Enforcement | step 7 | RE coordinator | Full bound request + PB/approval/preflight evidence | Single-attempt decision | No |
| 8 | Process containment + live preflight | step 6 (freshness) + implicit | Shell Gate/equivalent | Executable/config/cwd/args/env | Established containment | No dispatch yet |
| 9 | Durable pre-dispatch record | step 8 | Invocation coordinator/store | Eight bound items | `dispatch_attempted`; approval consumed | No process effect yet |
| 10 | Adapter dispatch | step 9 | Selected adapter | Dispatch envelope + containment | Process spawn/receipt | **Yes** |
| 11 | Result capture and intake | step 10 | Adapter collector + intake | Receipt + untrusted output | Normalized result + intake evidence | Effect already occurred |

## PB request matrix (repaired, final)

| Field | RPAC basis | Source | Required/conditional | Trust owner |
|---|---|---|---|---|
| `invocation_id` | REQ-025/064 | Invocation coordinator | Required | PCAE coordinator |
| `attempt_id` | REQ-025/064 | Invocation coordinator | Required | PCAE coordinator |
| `idempotency_key` | REQ-025/065 | Invocation coordinator | Required | PCAE coordinator |
| `repository_identity` | REQ-025 | Git-root fingerprint helper | Required | Repository context resolver |
| `task_id` | REQ-025 | Active task contract | Required | Task lifecycle |
| `lifecycle_context` | REQ-025 | Governed lifecycle/session state | Required; session conditional | Lifecycle/session owner |
| `runtime_target_id` | REQ-025 | Explicit target selection | Required | Target selector + registry |
| `adapter_descriptor_binding` | REQ-025 | Registry/config preflight | Required | Runtime Registry/config owner |
| `prompt_hash` | REQ-021 | Prompt canonicalizer | Required | Prompt builder |
| `requested_capability` | REQ-025 | Governed invocation request | Required | Integration contract/coordinator |
| `transport_type` | REQ-025 | Contract-fixed integration point | Required (const) | PBRD-001 integration |
| `network_requirement` | REQ-027 | Target descriptor + static preflight | Required (const false) | Registry/preflight owner |
| `filesystem_scope_ref` | REQ-061 | Isolated-worktree/scope owner | Required | Filesystem-scope owner |
| `human_authority_binding` | REQ-022 | RIHAC validator | Required | Human-authority validator |

## Attempt/idempotency matrix

| Concept | Meaning | Created by | Bound to | Reuse rule | Failure behavior |
|---|---|---|---|---|---|
| `attempt_id` | One concrete dispatch try | PCAE invocation coordinator, gate 2 | invocation, PB request, RE projection, durable record, dispatch envelope | Never reused; new on every retry | Duplicate/mismatched content -> hard collision, fail closed |
| `idempotency_key` | Logical dispatch operation's canonical content | PCAE invocation coordinator, gate 2 (SHA-256, RPAC-REQ-065) | invocation, PB request, durable record | Identical across a safe retry of the same logical request | Mismatch with recomputed canonical content -> fail closed |

## Replay scenarios matrix

(See "Replay threat model" above — reproduced here per required section
name.)

| Scenario | Expected result | Contract mechanism |
|---|---|---|
| Same `attempt_id`, modified payload | Reject | RPAC-REQ-066; PBRD §15 |
| Same `idempotency_key`, new target | Reject | Digest recomputation mismatch |
| Same `idempotency_key`, new prompt | Reject | Digest recomputation mismatch |
| New `attempt_id`, stale approval | Reject | RIHAC/RDGO freshness (gate 5) |
| Replay of old PB ALLOW | Reject | PBRD §10; decision expiry |
| Replay after uncertain dispatch | Reject; new attempt/approval required | RDGO §10a |

## Cardinality matrix

| Contract set | Pre-repair | Post-repair | Reason |
|---|---:|---:|---|
| PB request facts | 12 | 14 | Finding B-2 closed |
| RDGO gates | 11 | 11 | Minimal transposition |
| Durable-before-effect items | 8 | 8 | Item 1 enriched |
| TOCTOU facts | 7 | 7 | Attempt/idempotency excluded by design (immutable identity) |
| RIASC required fields | 16 | 16 | Unchanged |
| Approval-subject fields | 5 | 5 | Unchanged |

## Version matrix

| Contract | Pre-repair version | Post-repair version | Why |
|---|---|---|---|
| RIHAC-001 | 1.0 | 1.0 | No subject/authority change; reference-only update |
| PBRD-001 | 1.0 | 1.1 | Additive mandatory facts; own §16 rule permits MINOR |
| RDGO-001 | 1.0 | 2.0 | Gate reorder; own §21 rule requires MAJOR |
| RIASC-001 | 1.0 | 1.0 | No schema change; reference-only note |

## Independent-verification readiness

```text
Are the repaired contracts ready for a new independent verification without
implementation?

YES:
- both original blockers are closed with textual evidence, not assertion;
- no new contradiction was found across the four artifacts plus RPAC;
- all counts/references are reconciled and honestly re-derived, not
  preserved by default;
- versioning follows each contract's own pre-existing compatibility rule.
```

## Final verdict

```text
LOCAL-CLI AUTHORITY/PERMISSION CONTRACT REPAIR: COMPLETE
3V.1 BLOCKING 1 (RDGO/RPAC gate order): CLOSED
3V.1 BLOCKING 2 (PBRD/RDGO attempt/idempotency omission): CLOSED
PBRD-001: v1.0 -> v1.1, REPAIRED, attempt_id BOUND, idempotency_key BOUND
RDGO-001: v1.0 -> v2.0, RPAC-REQ-042 CONSISTENT
RIHAC-001: v1.0, UNCHANGED (reference-only)
RIASC-001: v1.0, UNCHANGED (reference-only)
AUTHORITY != PERMISSION: PRESERVED
PB ALLOW != CAPABILITY: PRESERVED
POL-005: UNCHANGED
DRY PATH: UNCHANGED
REAL EXECUTION: UNAVAILABLE
NEW BLOCKING: 0
IMPLEMENTATION: NOT STARTED
PRODUCTION SOURCE MODIFIED: NO
EXECUTION ACTIVATED: NO
EXTERNAL RUNTIME: NONE
RELEASE v0.4.3: UNCHANGED
ARTICLE: STOPPED
PRIVATE RESEARCH: UNTOUCHED
```

## Recommended next phase

**149O.20L.7O.3V.1R.1 — Independent Verification of Repaired Local-CLI
Runtime Dispatch Authority and Permission Contracts.**

## Human decision required

**YES.** This phase repairs contract text only. It does not authorize
independent verification acceptance, implementation planning, source
changes, POL-005 evolution, Runtime Enforcement/Shell Gate activation,
adapter registration, execution, API/network architecture, article work, or
private-research access. Stop after 3V.1R.
