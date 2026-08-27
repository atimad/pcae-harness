# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R — Trusted Approval Presentation Evidence and HPAC Proof-Lifecycle Canonicalization Blocking Repair

## 1. Objective

Close exactly original B-3 and B-4 by completing the canonical contract for
trusted approval-presentation evidence and durable HPAC proof lifecycle/
atomic consumption. This phase is contract/schema/static-verification only.

## 2. Baseline

| Fact | Phase-entry result |
|---|---|
| Phase-entry SHA | `bd11deaebd6e7022cf68e0148ade96b2f7d4a1ba` |
| `origin/main` | same SHA |
| `origin/main..HEAD` | `0` |
| Working tree | clean |
| Release | `v0.4.3` at `63580893b1de4782a694ab802ff7bdebdf29b0e6` |
| Runtime | `Observed` / `observe` / `unavailable` |
| Registry | 0 plugins / 0 capabilities |
| Governance | healthy / passed / coherent |
| Task memory | historical `tasks/DONE.md` warnings only |

## 3. B-3 exact finding

> **B-3 — Blind touch can substitute for informed approval.** No
> non-forgeable confirmation evidence or trusted subject display is bound.

Affected original text: HPAC v1 §§14–16 and RIHAC v1.1 §§3/12. The
preceding repaired candidate still left the defect at HPAC v2 §§2/14/16/18,
RIHAC v2 §3, and RIASC v3 §7.

Attack: an agent displays “touch your key,” supplies authority-looking
presentation ID/digest values, and obtains valid UP+UV over hidden subject B
while the human never received a protected presentation of B.

## 4. B-4 exact finding

> **B-4 — Proof schema/store/reference contract is incomplete and internally
> inconsistent.** Canonical resolution cannot be implemented uniquely.

Affected original text: HPAC v1 §§17–19, RIHAC v1.1 §16, and RIASC v2
§§7/10–12. The preceding candidate still left the defect at HPAC v2
§§16–18/24, RIHAC v2 §16, RIASC v3 §§7/10–12, and RDGO v3 §§6/10.

Attack: Gate 5 must distinguish exact same-binding revalidation from a copied
or cross-bound lifecycle record, then Gate 9 must atomically consume proof
and approval. State names without binding fields/path/bytes cannot decide
either operation uniquely.

## 5. Reproduction

B-3 reproduced: HPAC v2.0 had only a `presentation_id`/
`presentation_digest` pair and prose “protected presentation store,” with no
schema, closed fields, canonical bytes/path, descriptor, protected-renderer
attestation, or lifecycle correlation.

B-4 reproduced: HPAC v2.0 defined exact proof JSON/path, but its adjacent
lifecycle had only state names. It lacked lifecycle schema/path/hash chain,
`approval_id`/digest, presentation/challenge/subject/attempt bindings, and a
single crash-safe Gate-9 consumption record.

Both contradictions are **REPRODUCED**. Contract edits began only afterward.

## 6. Scope sufficiency

| Question | Answer | Reason |
|---|---|---|
| Can B-3 be repaired with RIHAC/RIASC/HPAC/PBRD/RDGO only? | **YES** | HPAC owns presentation evidence; RIHAC consumes it. No approval-wire, PB-policy, or adapter change is needed. |
| Can B-4 be repaired with RIHAC/RIASC/HPAC/PBRD/RDGO only? | **YES** | HPAC owns proof lifecycle/consumption records; RIHAC validates; RDGO orders Gates 5/9. |

RPAC evolution, production source, runtime effects, hardware changes, and new
PB policy semantics are not required.

## 7. B-3 root cause

The prior candidate froze the security property but not its evidence. A
digest pair was resolvable only by an implementation-specific assumption.
Consequently, caller-created lookalikes could not be distinguished
contractually from protected display/election evidence.

## 8. Presentation evidence

HPAC §39 now owns `TrustedApprovalPresentationEvidence`, schema
`HPAC-PRESENTATION-EVIDENCE/2.0`, canonical ID `hpe-<32-hex>`, closed fields,
self-excluding digest, exact subject, mechanism reference, human-visible
facts, exact displayed-byte digest, trusted timestamps/election, and
mechanism attestation.

### Matrix A — B-3

| Requirement | Canonical owner | Evidence artifact | Trust source | Closure |
|---|---|---|---|---|
| Exact subject | HPAC §38 | `HPAC-APPROVAL-SUBJECT/2.0` | PCAE canonical RIASC facts | CLOSED |
| Protected display/election | HPAC §39 | `HPAC-PRESENTATION-EVIDENCE/2.0` | registered protected mechanism attestation | CLOSED |
| Human-usable facts | HPAC §39 | closed `human_visible_facts` | protected resolvers/renderer | CLOSED |
| Challenge binding | HPAC §§16/39 | presentation and subject digests | signed challenge | CLOSED |
| Later revalidation | HPAC §§18/40/41 | evidence + lifecycle + consumption path | protected resolver | CLOSED |
| Anti-forgery | HPAC §§3/39/43 | complete verification conjunction | no caller construction | CLOSED |

## 9. Presentation mechanism trust

`HPAC-PRESENTATION-MECHANISM/2.0` is stored below the deployment protected
root. Its closed descriptor binds mechanism/version/digest, protected verifier
configuration, deterministic renderer profile, protected output,
agent-substitution resistance, canonical rendering, explicit-election
support, and active/revoked status. Only the external protected administrator
may install or revoke it. Ordinary stdout/stdin cannot qualify.

## 10. Human-visible facts

### Matrix C — Presentation evidence

| Field/fact | Canonical source | Human-visible? | Challenge-bound? |
|---|---|---:|---:|
| Repository identity + usable label/fingerprint | RIASC subject + protected resolver | Yes | Yes |
| Task ID + usable active-task label | RIASC subject/task contract | Yes | Yes |
| Runtime target ID + descriptor label | RIASC subject/protected descriptor | Yes | Yes |
| Operation/effect/complete scope | RIASC approval scope | Yes | Yes |
| Prompt identity + recognizable fingerprint | RIASC prompt hash/protected renderer | Yes | Yes |
| Invocation identity/fingerprint | RIASC invocation ID | Yes | Yes |
| Expiry | canonical approval subject | Yes | Yes |
| One-shot notice | const attempt limit one | Yes | Yes |

Opaque digest-only display is forbidden. The descriptor's deterministic
renderer produces normalized exact displayed bytes; their digest is attested
and later rerendered/compared.

## 11. Blind-touch closure

Valid FIDO2 signature + UP + UV without resolved, attested canonical
presentation evidence cannot satisfy `PRINCIPAL_VERIFIED_INTENT`. Blind touch
therefore yields no authenticated approval authority.

## 12. Presentation/challenge binding

The protected attestation binds presentation ID, reserved approval ID,
canonical subject digest, exact displayed-byte digest, descriptor digest,
election, and presentation time. The challenge binds the same subject and
presentation digests. The proof cites the exact presentation ID/digest. A
presentation for A plus challenge for B fails digest, subject, and lifecycle
binding independently.

## 13. Presentation evidence lifecycle

An immutable evidence artifact is intrinsically `PRESENTED`.
`BOUND_TO_CHALLENGE` is derived from lifecycle sequence 0;
`USED` is derived from the Gate-9 consumption record. Expiry/invalidation is
derived from trusted time, descriptor/configuration status, or linked trust
state. No mutable caller-set status is trusted.

## 14. Presentation store

Canonical path:

```text
<HPAC_PROTECTED_ROOT>/presentations/v2/<presentation_id>/presentation.json
```

Create-only, atomic, read-back-verified resolution checks protected
ownership/ACL/path, canonical bytes/digest, active descriptor/configuration,
attestation, subject/display equality, election ordering, and expiry.
Corruption, ambiguity, symlinks, traversal, or duplicate identity fails
closed.

## 15. Repository isolation

Repository/task/agent/cwd/environment/stdin state cannot register a
mechanism, select or redirect stores, mark stdout trusted, supply labels,
mint evidence, weaken the renderer, or alter attestation verification.

## 16. B-4 root cause

The previous state machine was semantically ordered but not persistently
defined. It could not prove the exact approval/proof/presentation/challenge/
attempt binding at Gate 5 or make Gate-9 consumption one crash-safe fact.

## 17. Canonical proof record

`HPAC-PROOF/2.0` remains unchanged. HPAC §40 adds canonical immutable
`HPAC-PROOF-LIFECYCLE-EVENT/2.0` records and HPAC §41 adds one
`HPAC-AUTHORITY-CONSUMPTION/2.0` record. Together they make proof state
durable and revalidatable.

## 18. Raw assertion vs proof

```text
raw authenticator assertion
!= canonical HPAC proof
!= verified/bound lifecycle state
!= ephemeral AuthenticatedHumanPrincipal
```

An unverified response may produce only `ASSERTION_RECEIVED`. `proof.json`
is created only after preliminary verification. Gate 5 reruns verification
and creates the final bound event. Object shape never creates trust.

## 19. Proof record fields

Every lifecycle event closes schema/version, event identity/digest, sequence,
previous digest, proof ID, state/time, exact common binding, staged assertion/
proof/approval/registry digests, verifier version, and terminal reason.
Common binding is exactly approval, invocation, attempt, principal,
credential, mechanism, subject digest, presentation ref, and challenge
digest.

## 20. Gate 5

Gate 5 reloads canonical approval, presentation/descriptor/attestation,
challenge, proof and complete lifecycle, registry/credential/mechanism,
freshness, revocation, and consumption path. Success creates lifecycle
sequence 3 `PROOF_VERIFIED_AND_BOUND` and the ephemeral trusted principal/
projection. It consumes nothing.

## 21. Gate-5 persistence

Sequence 3 records final `approval_digest` and every common binding field.
A repeated Gate 5 is permitted only for byte-identical same-binding state
after all live checks rerun. Different bytes or bindings fail as a fork/
cross-binding. Crash after Gate 5 leaves bound but unconsumed authority.

## 22. Gate 9

Gate 9 revalidates current trust and atomically compare-and-creates exactly
one `RuntimeInvocationAuthorityConsumption` before Gate 10. Its existence is
simultaneously the durable `dispatch_attempted` marker and consumption of the
approval, presentation, challenge, and proof.

## 23. Atomicity

The single protected same-filesystem file is written to a protected temporary
sibling, durably flushed, atomically installed only if absent, parent-durable,
and read-back verified. Recovery accepts only absent/not-consumed or complete
valid/consumed. Partial, corrupt, conflicting, or uncertain state is never
reusable and permits no effect.

## 24. Consumption artifact

The canonical path is:

```text
<HPAC_PROTECTED_ROOT>/proofs/v2/<proof_id>/consumption.json
```

Its eight closed objects exactly encode RDGO's invocation, repository/task,
target, prompt, authority, PB, Runtime Enforcement, and dispatch bindings.
The authority object additionally binds presentation, challenge, subject,
proof, approval, projection, validation, and registry digests.

## 25. Crash windows

| Window | Contract result |
|---|---|
| Gate 5 succeeds; crash before Gate 9 | Bound/unconsumed; full same-binding revalidation may resume |
| Gate 9 interrupted before atomic install | Final absent; no effect; full revalidation required |
| Gate 9 atomic artifact valid/present | Consumed; retry/replay rejected even if Gate 10 not proven |
| Partial/corrupt/durability-uncertain | Fail closed; manual recovery; never reusable |

## 26. TOCTOU/revalidation

Gate 9 holds the protected evidence-store serialization boundary while
rechecking registry/credential, descriptor/configuration, presentation,
challenge/proof/lifecycle, approval/expiry, PB, Runtime Enforcement, and
absence of consumption. The commit compares the exact current registry-state
digest and Gate-5 event.

## 27. Revocation/expiry

Principal or credential revocation, descriptor revocation, presentation
invalidation/expiry, proof expiry, approval expiry, or policy/RE drift after
Gate 5 and before Gate 9 fails closed. Gate-5 success is not a cached license.

## 28. Attempt binding

Lifecycle common binding and consumption record both carry exact
`invocation_id` and `attempt_id`; consumption also carries the
`idempotency_key`. Presentation carries reserved `approval_id` and canonical
invocation subject. No evidence transfers to another attempt.

## 29. Retry

Before Gate 9, exact same binding may be revalidated if still fresh and
unconsumed. After Gate 9, every retry needs fresh invocation, attempt,
presentation, challenge, proof, and approval. Existing consumption is a
replay rejection, never permission to re-enter Gate 10.

## 30. Proof-store trust

Proof, lifecycle, and consumption paths are under the deployment protected
root, independently resolved, repository-unredirectable, owner/ACL checked,
canonical, and fail closed on ambiguity or tamper.

## 31. Store relationships

The smallest coherent model uses one HPAC protected root with distinct
mechanism, presentation, proof, lifecycle-event, and consumption record
families linked by exact IDs/digests. RIHAC approvals remain immutable in the
repository governance store; their consumption truth is solely the protected
HPAC consumption record. Any repository dispatch record is a mirror/ref.

## 32. HATP separation

Every new schema/path belongs to HPAC's protected root and v2 namespace.
HATP registry, presentation/signing ceremony, proof, or audit records cannot
substitute by structural similarity. The challenge domain remains
`pcae.hpac.runtime-invocation-approval.v2`.

## 33. Versioning

| Contract | Before | After | Reason |
|---|---|---|---|
| RIHAC | 2.0 rejected candidate | **2.0 corrected/frozen** | No approval/projection/authority meaning changes; required HPAC evidence is now defined |
| RIASC | 3.0 | **3.0 unchanged** | Sixteen fields, subject, provenance, proof ref unchanged |
| HPAC | 2.0 rejected candidate | **2.0 corrected/frozen** | First definitions of already-required companion records; challenge/proof wire schemas unchanged |
| PBRD | 2.0 | **2.0 unchanged** | PB still receives only RIHAC projection |
| RDGO | 3.0 rejected candidate | **3.0 corrected/frozen** | Eleven gates/order and bind-5/consume-9 semantics unchanged; persistence completed |
| RPAC | 1.0 | **1.0 unchanged** | Provider-neutral order/transport remains sufficient |

No pre-correction B-3/B-4 evidence could conform to an absent schema. There
is therefore no valid artifact to migrate or silently upgrade. A minor bump
would falsely imply a usable compatible predecessor; this phase corrects the
unverified freeze in place and requires independent verification.

## 34. RIHAC impact

RIHAC v2 validation now names HPAC §§38–41 exact subject, presentation,
lifecycle, and consumption resolution. The coordinator reserves approval ID
before ceremony. Gate-9 revalidation/consumption is exact. No RIHAC subject,
approval validity meaning, projection field, or one-shot rule changes.

## 35. RIASC impact

None. `authentication_proof_ref` transitively resolves the proof's canonical
presentation/lifecycle chain. Adding presentation/proof-internal fields to
the approval would duplicate HPAC ownership and create drift. RIASC remains
byte-identical v3.0.

## 36. HPAC impact

HPAC is the primary owner of canonical subject representation, protected
presentation mechanism/evidence, lifecycle events, proof creation states,
and atomic authority consumption.

## 37. PBRD impact

None. PB continues receiving only typed RIHAC projection evidence. It does
not parse presentation, FIDO2, proof, lifecycle, or consumption internals.
PBRD remains byte-identical v2.0 and POL-005 remains hard DENY.

## 38. RDGO impact

Gate 3 now names exact presentation/proof-creation records. Gate 5 creates
the final bound lifecycle event without consumption. Gate 9 creates the one
consumption record after live revalidation. Gate count/order remains 11;
Gate 10 remains first effect.

## 39. RPAC result

RPAC-001 v1.0 is byte-identical and compatible. It already requires PCAE-
owned authority, approval before PB/RE/effect, explicit attempt identity,
durable-before-effect, and provider-neutral transport. No new adapter or
authority meaning enters RPAC.

## 40. B-3 closure

**CLOSED.** All eight criteria are frozen: canonical evidence, trusted
creator/resolver, exact subject binding, human-visible facts, qualified
mechanism, challenge correlation, later revalidation, and caller-lookalike
non-authority.

## 41. B-4 closure

**CLOSED.** All eight criteria are frozen: canonical lifecycle record,
verification/binding state, exact multi-artifact linkage, Gate-5 semantics,
Gate-9 atomicity, deterministic crash/retry, revocation/expiry, and replay
rejection.

### Matrix B — B-4

| Lifecycle event | Durable state | Gate | Atomicity/replay rule |
|---|---|---:|---|
| Challenge allocated | `0000 CHALLENGE_CREATED` | 3 | create-only; presentation/subject/attempt bound |
| Assertion received | `0001 ASSERTION_RECEIVED` | 3 | raw assertion remains untrusted |
| Proof preliminarily verified | `0002 PROOF_VERIFIED` + proof JSON | 3 | approval may now be created; not final authority |
| Proof bound to final approval | `0003 PROOF_VERIFIED_AND_BOUND` | 5 | same-binding idempotent; no consumption |
| Authority consumed | `consumption.json` -> derived `PROOF_CONSUMED_WITH_APPROVAL` | 9 | one atomic create; replay rejected |
| Terminal invalidity | next `EXPIRED`/`REVOKED`/`REJECTED` or current derived state | 3/5/9 | no later authority state |

## 42. N2 re-evaluation

**N2 CONTRACT GAP: CLOSED.** Caller-created principal, mechanism,
presentation, lifecycle, proof, approval, or projection shapes cannot satisfy
protected path/descriptor/attestation/signature/hash-chain/current-state/
atomic-consumption validation. Without the canonical ceremony, authority is
zero.

## 43. Previously closed blockers

| Original blocker | Previous status | Post-repair |
|---|---|---|
| B-1 protected registry/bootstrap root | CLOSED | **STILL CLOSED** |
| B-2 UP-only overclaim | CLOSED | **STILL CLOSED** |
| B-5 stale revocation | CLOSED | **STILL CLOSED; strengthened at Gate 9** |
| B-6 stale companion pins | CLOSED | **STILL CLOSED** |
| B-7 Gate-5 consumption contradiction | CLOSED | **STILL CLOSED; persistence now exact** |

## 44. MUST-FIX regression

M-1 remains closed: RIHAC is major v2 and v1.x does not migrate. M-2 remains
closed: new section references resolve; no live stale/mistargeted citation is
introduced.

## 45. Cross-contract trace

| Transition | Owner | Canonical artifact / validation |
|---|---|---|
| Enrollment -> principal registry | HPAC | protected ceremony + registry records/provenance |
| Registry + invocation -> presentation | HPAC/RIHAC | canonical subject + protected descriptor/evidence/attestation |
| Presentation -> challenge | HPAC | lifecycle sequence 0 + challenge binding both digests/domain/nonce |
| Challenge -> assertion | HPAC mechanism | signed response with UP+UV |
| Assertion -> proof | HPAC | sequences 1/2 + canonical proof JSON |
| Proof -> authenticated principal | HPAC | Gate-5 full revalidation + sequence 3 |
| Principal/proof -> approval | RIHAC/RIASC | immutable v3 approval using reserved approval ID |
| Approval -> projection | RIHAC | canonical approval + current HPAC chain |
| Projection -> PBRD/PB | PBRD | typed `human_authority_binding`; PB policy only |
| PB/RE/containment -> consumption | RDGO/HPAC | one Gate-9 protected consumption artifact |
| Consumption -> effect | RDGO/RPAC | valid durable record required; Gate 10 first effect |

### Matrix E — Cross-contract ownership

| Concept | HPAC | RIHAC | RIASC | PBRD | RDGO |
|---|---|---|---|---|---|
| Presentation/mechanism evidence | Primary | Requires | Proof ref only | None | Orders Gate 3/5 |
| Proof/lifecycle | Primary | Validates conjunction | Proof ref | None | Orders Gate 5/9 |
| Approval authority | Evidence supplier | Primary | Wire shape | Projection only | Gate order |
| Atomic consumption | Record schema/store | Authority semantics | Immutable approval | Never consumes | Gate-9 timing/eight items |

## 46. New attack sweep

### Matrix F — Failure scenarios

| Scenario | Required outcome | Contract result |
|---|---|---|
| Fake presentation evidence | reject | protected path/descriptor/attestation/canonical bytes required |
| Fake mechanism descriptor | reject | protected admin path/config; repo cannot register |
| Presentation A + challenge B | reject | subject/presentation digest and lifecycle mismatch |
| Valid proof without presentation | reject | cannot reach proof verification or assurance floor |
| Copied proof/lifecycle | reject | path, hash chain, exact binding, current state required |
| Gate-5 stale binding | reject | current checks rerun; Gate 9 revalidates again |
| Gate-9 partial write | no effect/no replay | absent or valid-present only; uncertainty fails closed |
| Proof consumed without approval | impossible as authority state | single combined artifact |
| Approval consumed without proof | impossible as authority state | single combined artifact |
| Revocation after Gate 5 | reject | serialized Gate-9 current-state compare/create |
| Retry after Gate 9 | reject | existing consumption record; fresh full authority required |
| Cross-attempt transfer | reject | invocation/attempt bound in lifecycle and consumption |

No new BLOCKING or MUST-FIX finding was identified by this repair sweep.

## 47. Static verification

Fresh test:
`tests/test_trusted_approval_presentation_hpac_proof_lifecycle_canonicalization_repair_3w1r2b1r111r.py`.

It independently checks exact B-3/B-4 recovery, unchanged active versions,
byte-identical RIASC/PBRD/RPAC, gapless HPAC requirements, exact subject,
mechanism/evidence/attestation/store semantics, blind-touch rejection,
unchanged challenge/proof identity, lifecycle fields/transitions, Gate-5
non-consumption, Gate-9 record/atomicity/TOCTOU/crash/retry, eleven gates,
N2 anti-forgery, PB separation, POL-005, and no implementation claim.

Result: **23 passed**.

## 48. Findings

- **BLOCKING:** none open.
- **MUST-FIX:** none open.
- **NON-BLOCKING:** none.
- **OBSERVATION:** exact UI/FIDO2/store implementation remains deliberately
  unspecified while all trust-relevant inputs/outputs are frozen.
- **DEFERRED-IMPLEMENTATION:** registry, protected presentation, FIDO2,
  proof/lifecycle/consumption stores, B1/B7/N1/N2 source repair, PB/RE/Shell
  Gate integration, and runtime activation.

## 49. Freeze verdict

```text
TRUSTED APPROVAL PRESENTATION / HPAC PROOF LIFECYCLE REPAIR: COMPLETE
B-3: CLOSED
B-4: CLOSED
OTHER ORIGINAL BLOCKING: 5 / 5 REMAIN CLOSED
MUST-FIX: 2 / 2 REMAIN CLOSED
NEW BLOCKING: 0
TRUSTED PRESENTATION: CANONICAL EVIDENCE SPECIFIED
BLIND TOUCH: INSUFFICIENT
PRESENTATION / CHALLENGE: EXACTLY BOUND
HPAC PROOF: CANONICAL / DURABLE / REVALIDATABLE
GATE 5: VALIDATION + BINDING; NON-CONSUMING
GATE 9: ATOMIC PROOF + APPROVAL + PRESENTATION CONSUMPTION
GATE 10: FIRST EFFECT
N2 CONTRACT GAP: CLOSED
```

## 50. Implementation readiness

**CROSS-CONTRACT HUMAN AUTHENTICATION/AUTHORITY FREEZE — IMPLEMENTATION
READY: YES**, subject first to the required independent verification of this
repair. This is not real-runtime readiness or implementation authorization.

## 51. Current production status

```text
HumanPrincipalRegistry: NOT IMPLEMENTED
trusted presentation: NOT IMPLEMENTED
HPAC proof lifecycle store: NOT IMPLEMENTED
FIDO2 mechanism: NOT IMPLEMENTED
B1/B7/N1/N2 source repair: NOT IMPLEMENTED
Runtime Enforcement: NOT READY
Real runtime: UNAVAILABLE
Production source modified: NO
Hardware touched: NO
Execution activated: NO
POL-005: UNCHANGED HARD DENY
Runtime: Observed / observe / unavailable
Release: v0.4.3 unchanged
Article: STOPPED / UNTOUCHED
Private research: UNTOUCHED
```

## 52. Recommended next phase

Exactly:

**149O.20L.7O.3W.1R.2B.1R.1.1R.1 — Independent Verification of Trusted
Approval Presentation Evidence and HPAC Proof-Lifecycle Canonicalization
Repair**

Do not proceed directly to implementation planning.

## 53. Human decision required

Stop after this phase. Independent verification requires explicit human
authorization. Do not begin implementation automatically.

## Matrix D — Proof lifecycle

| State | Entry condition | Exit condition | Reusable? |
|---|---|---|---|
| `CHALLENGE_CREATED` | attested presentation + exact challenge | assertion or terminal | challenge once |
| `ASSERTION_RECEIVED` | exact challenge response | verified proof or terminal | No |
| `PROOF_VERIFIED` | preliminary full verification | approval creation/Gate 5 | No |
| `PROOF_VERIFIED_AND_BOUND` | Gate-5 final approval binding | Gate 9 or terminal | Same-binding revalidation only |
| `PROOF_CONSUMED_WITH_APPROVAL` | valid consumption record | terminal historical state | No |
| `EXPIRED`/`REVOKED`/`REJECTED` | current invalidity | none | No |

## Canonical phase-report facts

- **Phase ID:** `149O.20L.7O.3W.1R.2B.1R.1.1R`
- **Status:** complete — contract-only repair
- **Completeness:** complete
- **Phase-entry SHA:** `bd11deaebd6e7022cf68e0148ade96b2f7d4a1ba`
- **Runtime:** `Observed` / `observe` / `unavailable`
- **v0.4.3:** unchanged at `63580893b1de4782a694ab802ff7bdebdf29b0e6`
- **B-3 exact finding:** preserved in §3; CLOSED
- **B-4 exact finding:** preserved in §4; CLOSED
- **Presentation artifact/schema:** `HPAC-PRESENTATION-EVIDENCE/2.0`
- **Presentation mechanism trust:** protected registered descriptor + verifier configuration + attestation
- **Human-visible fields:** repository, task, target, effect/scope, prompt, invocation, expiry, one-shot
- **Blind touch:** insufficient
- **Presentation/challenge:** exact subject and evidence digests bound
- **Presentation store:** deployment protected root; repository-unredirectable
- **Proof record/schema:** `HPAC-PROOF/2.0` + `HPAC-PROOF-LIFECYCLE-EVENT/2.0`
- **Lifecycle:** hash-chained create-only events; Gate 5 binds
- **Gate 9:** one `HPAC-AUTHORITY-CONSUMPTION/2.0` atomic record
- **Crash/retry:** absent or complete-valid; ambiguity fails closed; consumed replay rejected
- **Revocation/expiry:** revalidated inside Gate-9 protected commit boundary
- **Attempt binding:** invocation/attempt/approval/presentation/challenge/proof exact
- **HATP:** separate namespace/stores/domain/authority
- **RIHAC:** v2.0 corrected/frozen
- **RIASC:** v3.0 unchanged
- **HPAC:** v2.0 corrected/frozen
- **PBRD:** v2.0 unchanged
- **RDGO:** v3.0 corrected/frozen; 11 gates unchanged
- **RPAC:** v1.0 unchanged/compatible
- **Other blockers:** 5/5 remain closed
- **MUST-FIX:** 2/2 remain closed
- **N2:** contract gap closed
- **New BLOCKING:** 0
- **Implementation readiness:** YES, pending independent verification
- **Production source modified:** NO
- **Hardware touched:** NO
- **Execution activated:** NO
- **POL-005:** unchanged hard DENY
- **Article:** stopped/untouched
- **Private research:** untouched
- **Tests:** fresh static suite, 23 passed
- **Exact next:** `149O.20L.7O.3W.1R.2B.1R.1.1R.1 — Independent Verification of Trusted Approval Presentation Evidence and HPAC Proof-Lifecycle Canonicalization Repair`
- **Human decision:** required
