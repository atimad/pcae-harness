# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.9 — Gate-5/Gate-9 Production Authority Coordinator Integration Planning

Status: **PLANNING ONLY — NOT IMPLEMENTED.** No production source modified.
No contract modified. No coordinator code, store code, or Permission Broker
production-consumption code written. No runtime capability enabled. No real
FIDO2, WebAuthn, CTAP, protected UI, trusted display, approval/enrollment
ceremony. No Gate-9 consumption. No Gate-10 approach. Runtime remains
`not_implemented / Observed / observe / unavailable`.

This phase is architecture/planning only. It plans the exact safe
coordinator integration for RDGO-001 v3.0 Gate 5 (approval validation) and
Gate 9 (atomic one-shot authority consumption) that would consume the
independently verified B1/B7/N1/N2 production authority repair, freezes the
immediate next implementation and independent-verification phase IDs, and
records all no-go conditions and one contract-sequencing constraint
(§13.3, non-blocking) discovered during planning.

---

## 1. Current independently verified milestone

Re-derived from primary contracts, current `src/pcae/**`, and the
`.1R.8` primary verification document — not from summary prose.

### 1.1 HPAC foundation (verified, carried)

`.3.2.2.1`-family and `.1R.3.x` verification established, and `.1R.8`
reconfirmed by fixed-SHA regression (baseline `b85e903c` vs candidate,
identical pass/fail set, zero regression):

- principal-registry trust root (`HumanPrincipalRegistry` model /
  `hpac_foundation`); fixture non-upgradability (`HPACStoreAuthority.writer`
  raises unless `authority_class is FIXTURE_NON_REAL`; no `PRODUCTION`
  writer exists);
- protected-presentation provenance and `HPAC-PRESENTATION-EVIDENCE/2.0`;
- `HPAC-REQ-092` attestation schema; proof-writer provenance;
- authoritative lifecycle genesis (`hpac_lifecycle`,
  `_GENESIS_WRITER_ROLE = "hpac_challenge_coordinator"`); predecessor
  validation; fork rejection; canonical-store containment
  (`HPAC_PROTECTED_ROOT`, deployment-scoped, `production()` fails closed on
  this host).

### 1.2 Mechanism-neutral HPAC verifier (verified, carried)

`.1R.5.2.1` — **VERIFIED, F1 CLOSED**:

- `verify_human_authentication` / `reverify_authenticated_principal` verified;
- verifier-owned `AuthenticatedHumanPrincipal` provenance — `__eq__`/
  `__hash__` identity-only; provenance established solely by insertion into
  the process-local `_AUTHENTIC_PRINCIPAL_REGISTRY`; `__reduce__` raises
  (HPAC-REQ-058, non-serializable);
- `is_verifier_authenticated_principal` = `isinstance` **and** registry
  membership **and** verification-context membership — never type/shape/
  equality;
- deterministic NON-REAL assurance preserved (every obtainable verifier
  result is `FIXTURE_NON_REAL`);
- invocation binding preserved (`principal.invocation_id`);
- **zero unintended production consumers before the `.1R.7` repair.**

### 1.3 B1/B7/N1/N2 production authority repair (independently verified)

`.1R.8` — **INDEPENDENTLY VERIFIED COMPLETE, NON-BLOCKING FINDINGS O1–O4**,
confined to the *production authority implementation boundary*. All change
isolated in commit `3fc26199`; exactly three production files
(`runtime_authority.py`, `runtime_dispatch_permission.py`,
`hpac_verifier.py`), matching `.1R.6`'s frozen matrix; no contract drift.

```text
B1 — INDEPENDENTLY CONFIRMED CLOSED AT PRODUCTION AUTHORITY IMPLEMENTATION BOUNDARY
B7 — INDEPENDENTLY CONFIRMED CLOSED AT PRODUCTION AUTHORITY IMPLEMENTATION BOUNDARY
N1 — INDEPENDENTLY CONFIRMED CLOSED AT PRODUCTION AUTHORITY IMPLEMENTATION BOUNDARY
N2 — INDEPENDENTLY CONFIRMED CLOSED AT PRODUCTION AUTHORITY IMPLEMENTATION BOUNDARY
```

- **B1** — the copyable `_validator_seal` is gone; `ValidatedAuthorityProjection`
  is `@dataclass(frozen=True, eq=False)` (identity equality/hash);
  `is_trusted_validated_authority_projection(v)` requires
  `type(v) is ValidatedAuthorityProjection` **and** exact-object membership
  in the process-local `_VALIDATED_AUTHORITY_CONTEXTS` dict **and**
  `v._content_binding_digest == v.evidence_digest()` recomputed over every
  authority field. `copy` / `deepcopy` / `dataclasses.replace` /
  field-mutation / hand-built lookalike / cross-invocation transfer all
  rejected.
- **B7** — `RuntimeDispatchIdentityTracker.revalidate` re-reads the durable
  `.pcae/runtime-dispatch-identities/v1/**` invocation/idempotency/attempt
  records at request-build time and requires each decoded record to `==`
  the exact expected dict; deleted / changed / foreign-tracker identity
  fails closed. Called from
  `build_runtime_dispatch_permission_broker_request` at line 568.
- **N1** — `validate_approval(approval_id, ...)` takes an opaque ID, rejects
  caller objects unconditionally (`noncanonical_approval_reference:
  caller_supplied_object`), requires `type(approval_store) is
  RuntimeInvocationApprovalStore` (no duck typing), re-loads by ID,
  checks `approval.approval_id == approval_id`.
- **N2** — caller `approver_id` / `identity_evidence_kind` raise `TypeError`;
  provenance derives only from a freshly `reverify_authenticated_principal`-ed
  verifier-owned principal; forged / copied / pickled principals refused.

### 1.4 Option-A NON-REAL hard stop (verified central safety property)

Both `create_runtime_invocation_approval` (`runtime_authority.py:457`) and
`validate_approval` (`runtime_authority.py:1093`) reject unless
`principal.assurance_class is HPACAuthorityClass.PRODUCTION`. No
deterministically-writable HPAC store can carry `PRODUCTION` assurance, so
the full-strength deterministic chain still fails specifically on
`FIXTURE_NON_REAL` — **zero positive real-authority paths**. Consequently
`validate_approval` cannot emit a projection today (O1), and every gate
downstream of it is unreachable in production.

### 1.5 Exact O1–O4 text (read from `.1R.8` §26, verbatim — not summarized)

- **O1 — B1 positive-emission path is unreachable under Option-A.**
  `validate_approval` can never emit a projection today (NON-REAL stop), so
  B1's anti-transfer property is verified at the predicate and
  dispatch-consumer levels, not through a live positive emission. Inherent
  to the frozen Option-A staging (`.1R.6` §7–§9), not a defect. Will
  become end-to-end testable only once a real assurance mechanism exists.
- **O2 — N1 canonical-store trust is path + file integrity, not a writer
  seal.** `RuntimeInvocationApprovalStore` has no cryptographic
  writer-provenance marker on the persisted record; an actor with direct
  write access to the canonical directory (documented F7 same-process /
  same-account model) could plant a schema-valid record. Consistent with
  `.1R.6` §12 and F7; redirection (symlink/hardlink/traversal) *is*
  prevented. Non-blocking; a future writer-provenance / schema-migration
  chapter is the place to close it if ever required.
- **O3 — `test_*_detected_by_fresh_reverification` naming.** Minor
  over-promise of *which* stage rejects for the expiry/presentation/
  lifecycle cases (same class as F4). Fail-closed behaviour is real.
  Non-blocking.
- **O4 — `pcae doctor task-memory` historical `tasks/DONE.md` omissions.**
  Pre-existing governance-record hygiene debt, dozens of entries, unrelated
  to any code path or to `.1R.7`/`.1R.8`. Carry separately; do not repair
  here.

Additionally carried, not repaired (`.1R.8` §26 final bullet): Fast Green
baseline-resolver weakness; `xdist` random-UUID parametrization
instability; 23 pre-existing historical/contradiction-documentation test
failures in the HPAC/runtime selection.

---

## 2. Current unresolved integration boundary

The production authority *structures* now exist and are independently
verified. What is still absent, confirmed by source inspection this phase
(`grep -rn` for `Gate5|GATE_5|gate_5|Gate-9|GATE_9|coordinator` across
`src/pcae/core/**` returns only the unrelated design-only
`RuntimeEnforcementCoordinator` in `backend_invocations.py` and HPAC's
`hpac_challenge_coordinator` writer role):

- **Gate 5 coordinator wiring = 0.** No RDGO Gate-5 component exists.
  `runtime_dispatch_permission.py` calls
  `revalidate_validated_authority_projection` as a small currentness hook
  inside the pre-existing structural PB request builder — a check, not a
  coordinator, and it never creates HPAC lifecycle sequence 3.
- **Gate 9 coordinator wiring = 0.**
  `runtime_invocation_authority_consumption.py` is byte-unchanged since
  `b85e903c`, has **zero production importers**, creates no
  `<HPAC_PROTECTED_ROOT>/proofs/v2/<proof_id>/consumption.json`.
- **PB production consumption of the repaired authority = 0.** The only
  consumer of `ValidatedAuthorityProjection` is the structural
  `runtime_dispatch` request builder; a `simulation_only=False` request
  through it is still universally `DENY`ed by POL-005.
- **Runtime capability = 0** (`Observed / observe / unavailable`, registry
  empty).
- **Gate 10 = 0.** No dispatch, adapter invocation, subprocess, or external
  effect.

Also absent and **out of scope of this chapter** (larger, separately
unscheduled): Gate 6 policy is only structurally present (POL-005 DENY),
Gate 7 Runtime Enforcement is `not_implemented`, Gate 8 Shell Gate /
process containment is `not_implemented`.

This phase plans the exact safe coordinator integration for Gates 5 and 9,
and the sequencing of the Gate-6 PB production consumer relative to them.

---

## 3. Core RDGO semantics (re-derived directly from RDGO-001 v3.0)

Preserved without simplification. RDGO-001 v3.0 is FROZEN; byte-unchanged
since `b85e903c` (`.1R.8` §22).

### 3.1 Non-equivalence wall (RDGO-001 §0)

```text
human approval != PB permission
PB ALLOW != runtime capability
runtime capability != Runtime Enforcement approval
Runtime Enforcement ALLOW != process permission
process permission != dispatch completion
dispatch completion != accepted change
runtime result != task completion
```
Every gate fails closed. A later gate SHALL NOT infer, manufacture, or
repair a missing earlier gate.

### 3.2 Gate 5 — approval validation (RDGO-001 §6, HPAC-REQ-097, RIHAC-001 §16)

- **Owner:** RIHAC-001 v2.0 validator.
- **Input:** canonical approval ref + current repo/task/target/prompt/
  config/policy state.
- Freshly resolves the canonical approval, HPAC proof, complete
  hash-chained lifecycle, protected registry/configuration, canonical
  presentation evidence, active presentation mechanism descriptor, and
  mechanism attestation; then executes RIHAC-001 v2.0's ordered
  twelve-step validation.
- **Output:** an *ephemeral* validated-authority projection (RIHAC-001 §16
  step 12) — "trusted only through fresh canonical re-resolution, never a
  caller-copyable seal, boolean, or public digest".
- Atomically creates HPAC lifecycle **sequence 3 `PROOF_VERIFIED_AND_BOUND`**,
  binding exact approval/proof/presentation/challenge/subject/invocation/
  attempt bytes.
- **Consumes nothing** — not the approval, nonce, presentation, or proof.
- Repeating Gate 5 before Gate 9 is permitted **only** when sequence 3 is
  byte-identical to the same binding and all cryptographic / current-registry
  / descriptor / presentation / revocation / consumption checks re-run
  idempotently.
- Missing, stale, mismatched, expired, revoked, consumed, replayed,
  tampered, caller-constructed, or ambiguous evidence stops the flow.
- **Does not produce PB ALLOW.**

### 3.3 Gate 9 — durable pre-dispatch record / atomic consumption (RDGO-001 §10, HPAC-REQ-098/099/100, RIHAC-001 §17)

- **Owner:** trusted invocation coordinator / protected evidence store.
- One create-only, crash-consistent, read-back-verified commit of the
  closed eight-item record (`HPAC-AUTHORITY-CONSUMPTION/2.0` at
  `<HPAC_PROTECTED_ROOT>/proofs/v2/<proof_id>/consumption.json`), completed
  **before** Gate 10.
- **Atomic one-shot consumption:** `dispatch_attempted` is "the single
  atomic presentation/challenge/proof/approval consumption point and
  at-most-once guard." Proof **and** approval (and presentation and
  challenge) are consumed **together** by this one write. PB evaluation
  consumes none of them.
- **In-boundary revalidation (HPAC-REQ-099, mandatory):** immediately
  before compare-and-create, while holding the protected evidence-store
  serialization boundary, Gate 9 reruns current principal/credential/
  descriptor status, presentation attestation and expiry, challenge/proof/
  lifecycle chain, approval freshness/expiry, exact Gate-5 binding,
  PB/Runtime-Enforcement freshness, and absence of a consumption record.
  "Gate-5 validation is never a substitute for this gate-9 revalidation."
- **Crash semantics (HPAC-REQ-100):** only two recoverable outcomes —
  final artifact absent (**not consumed**; no Gate-10 effect permitted) or
  one complete valid final artifact present (**consumed**; replay
  rejected). Temporary / partial / corrupt / duplicate / conflicting /
  durability-uncertain → no dispatch, never reusable authority. A
  byte-identical existing record means "already consumed", **not** an
  idempotent licence to enter Gate 10 again.

### 3.4 Gate 10 — first external effect (RDGO-001 §11)

The first external execution effect. At most one exact local process
through the selected adapter and already-established containment. Argument
vector, not shell string. Cannot widen scope. **No effect of any kind is
permitted before Gate 10.**

### 3.5 Crash/recovery states (RDGO-001 §17, RIHAC-001 §19, HPAC-REQ-101)

`PRE_APPROVAL_CONSUMPTION` → `APPROVAL_VALIDATED` → `PB_EVALUATED` →
`RE_EVALUATED` → `DISPATCH_ATTEMPTED` (approval consumed) →
{`DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER` | `DISPATCH_UNCERTAIN`} →
`RESULT_CAPTURED_UNTRUSTED`. After Gate 9, absence of a result is never
proof dispatch did not occur. Exactly-once execution is not promised;
at-most-once attempt is enforced where durable state proves it. Every
post-Gate-9 retry requires a fresh invocation, attempt, presentation,
challenge, proof, and approval.

---

## 4. Primary source material read in full for this phase

- `PROJECT_STATUS.md`, `CHANGELOG.md` (current tree).
- `.1R.8` verification document (O1–O4, F2/F3/F4/F7, HPAC-REQ-054 Step-4,
  regression attribution, isolation proofs).
- `.1R.7` production authority repair implementation document.
- `.1R.6` B1/B7/N1/N2 integration planning document (Option-A staging §7–§9,
  F1–F4/F7 adjudication §3.1, frozen production-file matrix §12, forward
  gate architecture §10, packaging §17, frozen IDs §18).
- Contracts, mapped to their repository filenames:
  | Contract | File | Status |
  |---|---|---|
  | RDGO-001 v3.0 | `docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md` | FROZEN |
  | RIHAC-001 v2.0 | `docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` | FROZEN |
  | RIASC-001 v3.0 | `docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md` | FROZEN |
  | HPAC-001 v2.0 | `docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` | FROZEN |
  | PBRD-001 v2.0 | `docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` | FROZEN |
  | RPAC-001 v1.0 | `docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md` | FROZEN |
  | POL-005 / PBPA | `permission_broker_foundation.py` `ExecutionDisabledRule`; `docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md` | FROZEN |
- `.1R.5.2.1` verifier verification; `.3.2.2.1` foundation verification.
- Production modules: `runtime_authority.py` (1167 lines),
  `runtime_dispatch_permission.py` (603 lines),
  `runtime_invocation_authority_consumption.py` (214 lines, inert Gate-9),
  `permission_broker_foundation.py` (POL-005 / PB evaluator),
  `runtime_invocation_approval_store.py`, `hpac_verifier.py`,
  `hpac_lifecycle.py`, `hpac_foundation.py`, `runtime_introspection.py`,
  `runtime_invocation.py`.
- `PBPC-001 v1.2` (`PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`) —
  inspected and found **not** applicable: it governs exactly one production
  consumer, `pcae push` (PBPC-REQ-004), not runtime dispatch.

---

## 5. Reconstructed current coordinator call graph (source-level, not name-inferred)

### 5.1 What exists today

```text
(trusted caller / test harness resolves all facts)
        │
        ▼
runtime_invocation.new_invocation_id / new_attempt_id / compute_runtime_dispatch_idempotency_key
        │   ── gate-2 identity triple ──
        ▼
runtime_dispatch_permission.new_runtime_dispatch_identity(inputs, identity_tracker)
        │   ── RuntimeDispatchIdentityTracker.register(): append-only create-exclusive
        │      records under .pcae/runtime-dispatch-identities/v1/{invocations,idempotency,attempts}
        ▼
hpac_verifier.verify_human_authentication(...)  ── NON-REAL; emits ephemeral
        │      AuthenticatedHumanPrincipal (registry-tracked, process-local)
        │      [ gate-3 territory: challenge seq 0/1, proof seq 2 PROOF_VERIFIED ]
        ▼
runtime_authority.create_runtime_invocation_approval(subject, ..., authenticated_principal)
        │      ── reverify_authenticated_principal; NON-REAL hard stop at :457
        │         (returns fail-closed today) ── would produce immutable
        │         RuntimeInvocationApproval; persisted via RuntimeInvocationApprovalStore
        ▼
runtime_authority.validate_approval(approval_id, approval_store, authenticated_principal,
                                    context: InvocationRequestContext, consumption_lookup)
        │      ── RIHAC-001 §16 twelve-step ordered validation
        │      ── NON-REAL hard stop at :1093 (returns (None, reason) today)
        │      ── on success WOULD: build ValidatedAuthorityProjection,
        │         replace(_content_binding_digest=evidence_digest()),
        │         register in _VALIDATED_AUTHORITY_CONTEXTS
        │      ── DOES NOT create HPAC lifecycle sequence 3 (gap — §13.3)
        ▼
runtime_dispatch_permission.build_runtime_dispatch_permission_broker_request(
        identity, inputs, validated_authority, authority_current_time, simulation_only)
        │      ── re-validates identity seal + registration digest
        │      ── identity._identity_tracker.revalidate(identity)   [B7 dispatch-time reread]
        │      ── project_human_authority_binding():
        │           is_trusted_validated_authority_projection() +
        │           revalidate_validated_authority_projection(current_time) +
        │           subject_scope_binding_digest match  →  approval_present
        ▼
permission_broker_foundation._build_runtime_dispatch_permission_broker_request(...)
        │      ── PermissionBrokerRequest with RuntimeDispatchRequestFacts (14 facts)
        ▼
Permission Broker evaluation (existing evaluator)
        │      ── simulation_only=False  →  POL-005 ExecutionDisabledRule  →  DENY / NG-025
        ▼
[ nothing further — no Gate 7, 8, 9, 10 ]
```

### 5.2 Where each RDGO gate is currently represented — or missing

| RDGO gate | Current representation in source | Status |
|---|---|---|
| 1 Prompt preparation | `runtime_authority.compute_prompt_semantic_hash` / `PromptSemanticComponent` | partial (hash primitive only; no coordinator) |
| 2 Target selection + identity triple | `runtime_invocation.*` + `new_runtime_dispatch_identity` + `RuntimeDispatchIdentityTracker` | present (structural), no coordinator |
| 3 Human authority creation | `hpac_verifier.verify_human_authentication` + `create_runtime_invocation_approval` (NON-REAL hard stop) | present (structural), no coordinator; challenge seq 0–2 in `hpac_lifecycle` |
| 4 Static preflight | `runtime_registry.py` primitives | partial; not wired into a flow |
| **5 Approval validation** | `validate_approval` + `revalidate_validated_authority_projection` (predicate + currentness check) | **NO coordinator; sequence-3 creation MISSING (§13.3)** |
| 6 Permission Broker | `build_runtime_dispatch_permission_broker_request` + PB evaluator (structural request builder only) | structural request path exists; **no production consumer wires a validated projection through it** |
| 7 Runtime Enforcement | `RuntimeEnforcementCoordinator` in `backend_invocations.py` — **design-only, non-executing, non-authorizing** | **NOT implemented** |
| 8 Process containment / live preflight | `shell_gate.py` | **NOT implemented as a gate** |
| **9 Durable pre-dispatch record / consumption** | `runtime_invocation_authority_consumption.py` — inert store, zero importers | **NO coordinator; no caller; no consumption write** |
| 10 Adapter dispatch | `mock_runtime_adapter.py` / `runtime_adapter.py` (dry/mock only) | no real dispatch path |
| 11 Result capture / intake | existing producer-neutral intake governance | unchanged; out of scope |

**Conclusion:** Gate 5 has validation *logic* but no coordinator and an
incomplete lifecycle side-effect; Gate 9 has an inert store but no
coordinator and no caller; Gate 6 has a structural request path but no
production consumer. Gates 7 and 8 do not exist. This bounds what a
Gate-5/Gate-9 chapter can safely do now (§13, §15).

---

## 6. Gate-5 ownership (frozen)

### 6.1 Decision — Option C (layered), one owner

**Gate-5 validation is owned by one new trusted coordinator component
("the Gate-5 approval-validation coordinator", to live in a new
`src/pcae/core/runtime_dispatch_gate5.py` or equivalent), which delegates
authority validation to the RIHAC-001 validator (`validate_approval`) and
delegates principal provenance to the HPAC verifier
(`reverify_authenticated_principal` / `is_verifier_authenticated_principal`).**

- **Not Option A alone** (coordinator calls the mechanism-neutral HPAC
  verifier directly): the verifier authenticates a *human*; it does not
  validate an *approval* against current repo/task/target/prompt/config
  state. RIHAC-001 §16 explicitly owns that ordered twelve-step check.
- **Not Option B alone** (coordinator consumes only the `.1R.7` repaired
  abstraction): the repaired abstraction *is* `validate_approval` +
  `ValidatedAuthorityProjection`; consuming it is correct, but the
  coordinator must additionally own the RDGO-001 §6 responsibilities that
  live *outside* `validate_approval` today — most importantly creating HPAC
  lifecycle **sequence 3 `PROOF_VERIFIED_AND_BOUND`** (HPAC-REQ-097),
  which `validate_approval` does not do (§13.3).
- **Option C (layered):** the coordinator is the single owner of "Gate 5
  ran"; it composes `validate_approval` (RIHAC) + `reverify_authenticated_principal`
  (HPAC) + `hpac_lifecycle` sequence-3 creation, and emits exactly one
  ephemeral result. No authority semantics are duplicated: each sub-check
  keeps its existing single owner; the coordinator only sequences them and
  owns the lifecycle side-effect and the fail-closed envelope.

### 6.2 Component-of-record for each canonical resolution

| Canonical fact | Resolving component (frozen) |
|---|---|
| canonical principal state | `HumanPrincipalRegistry` via `hpac_verifier.reverify_authenticated_principal` (HPAC-REQ-054 steps 1–2) |
| canonical proof | `hpac_lifecycle` / protected proof store via `reverify_authenticated_principal` (HPAC-REQ-054 step 4 + §40 chain) |
| canonical presentation | protected presentation store via `reverify_authenticated_principal` (HPAC-REQ-054 step 5, §39) |
| approval validation (RIASC shape, binding, freshness, expiry, consumption) | `runtime_authority.validate_approval` (RIHAC-001 §16 steps 3–11) |
| RIHAC projection construction / trust predicate | `runtime_authority.validate_approval` (step 12) + `is_trusted_validated_authority_projection` |
| assurance class check (NON-REAL hard stop) | `runtime_authority.validate_approval` `:1093` (relocated from §8 of `.1R.6`, per RDGO-001 §6 anticipation — the coordinator *invokes* it, does not re-implement it) |
| freshness / revocation | `validate_approval` steps 9–11 + `reverify_authenticated_principal` (fresh HPAC re-check) |
| exact invocation binding | `validate_approval` steps 5–8 (`context.invocation_id`, target, prompt, scope, adapter) + `principal.invocation_id` bind |
| HPAC lifecycle sequence-3 `PROOF_VERIFIED_AND_BOUND` | **`hpac_lifecycle` writer, invoked by the Gate-5 coordinator** (new wiring; HPAC-REQ-097) |

The coordinator SHALL NOT itself resolve any canonical store; it SHALL call
the components above and fail closed on any of their failures, in the
RIHAC-001 §16 order (no later step substitutes for an earlier failure).

---

## 7. Gate-5 revalidation matrix (what Gate 5 must re-resolve at the moment it runs)

Gate 5 SHALL NOT rely on any prior successful verifier or validator output.
Every row below is re-resolved from its authoritative store at Gate-5 run
time. (Column "already enforced by `validate_approval` today" is a fact
about the `.1R.7` implementation; the coordinator adds only the lifecycle
side-effect and the sequencing envelope.)

| # | Fact re-resolved at Gate 5 | Owner check | Already in `validate_approval`? | Failure reason (representative) |
|---:|---|---|---|---|
| 1 | principal currentness / `status == active` | HPAC-REQ-054 step 1 via `reverify_authenticated_principal` | yes (`:1076`) | `authenticated_principal_reverification_failed:*` |
| 2 | credential currentness / not revoked | HPAC-REQ-054 step 2 | yes | `authenticated_principal_reverification_failed:*` |
| 3 | mechanism eligibility / assurance floor | HPAC-REQ-054 step 3 | yes | `authenticated_principal_reverification_failed:*` |
| 4 | independent challenge-digest recomputation | HPAC-REQ-054 step 4 (F2 repair, `.1R.7`) | yes | `independently recomputed challenge state` |
| 5 | trusted-presentation validity / attestation | HPAC-REQ-054 step 5 | yes | reverification failure |
| 6 | assertion signature / UP / UV | HPAC-REQ-054 steps 6–7 | yes | reverification failure |
| 7 | proof freshness / challenge not expired | HPAC-REQ-054 step 8 | yes | reverification failure |
| 8 | lifecycle chain (§40) fresh or same-binding | HPAC-REQ-054 step 9 | yes | reverification failure |
| 9 | approval canonicality (store re-resolve by ID) | RIHAC §16 steps 1–2 | yes (`:951`–`:960`) | `canonical_approval_store_required` / `no_valid_approval` / `canonical_approval_identity_mismatch` |
| 10 | RIASC schema / version / contract version | RIHAC §16 step 3 | yes | `riasc_schema_invalid:*` / `unknown_*_version` |
| 11 | record-digest recomputation | RIHAC §16 step 4 | yes | `record_digest_mismatch` |
| 12 | producer / approver provenance distinctness | RIHAC §16 step 4 | yes | `untrusted_producer_component` / `producer_identity_not_distinct_from_approver` |
| 13 | approval-preview digest | RIHAC §16 step 4 | yes | `approval_preview_digest_mismatch` |
| 14 | repository / task / phase / session binding | RIHAC §16 step 5 | yes | `subject_mismatch:*` / `governance_context_mismatch:*` |
| 15 | invocation identity + exact target | RIHAC §16 step 6 | yes | `subject_mismatch:invocation_id` / `:runtime_target_id` |
| 16 | prompt hash + profile | RIHAC §16 step 7 | yes | `subject_mismatch:prompt_hash` / `unsupported_prompt_hash_profile` |
| 17 | requested capability / effect scope / adapter descriptor / target config | RIHAC §16 step 8 | yes | `scope_mismatch:*` / `adapter_binding_mismatch:*` |
| 18 | seven freshness conditions (HEAD, task contract, task state, …) + policy-drift disposition | RIHAC §16 step 9 (§13 disposition) | yes | `stale_approval:*` (+ `policy_drift_requires_fresh_pb_re_evaluation` non-fatal) |
| 19 | `created_at`/`expires_at` vs trusted clock | RIHAC §16 step 10 | yes | `invalid_expiry_ordering` / `expired` |
| 20 | prior consumption / cancellation / uncertainty / completion | RIHAC §16 step 11 (`consumption_lookup` → HPAC §41 path + durable invocation state) | yes | `already_bound:*` / `unrecognized_consumption_state:*` |
| 21 | RIHAC projection binding intact (`_content_binding_digest == evidence_digest()`) | `is_trusted_validated_authority_projection` | yes | not trusted |
| 22 | assurance class `is PRODUCTION` (NON-REAL hard stop) | `validate_approval:1093` | yes | `non_real_authenticated_principal_cannot_validate_production_approval` |
| 23 | **HPAC lifecycle sequence-3 `PROOF_VERIFIED_AND_BOUND` creation / same-binding idempotency** | `hpac_lifecycle` writer via coordinator (HPAC-REQ-097) | **NO — new wiring (§13.3)** | cross-binding fork → fail closed |
| 24 | dispatch-identity registry currentness (B7) — *at the PB-request choke point, a separate call site* | `RuntimeDispatchIdentityTracker.revalidate` | yes (`:568`) | `identity_registry_mismatch:*` / `identity_store_record_missing` |

**Only rows 23 (and its idempotent-repeat rule) are new work for the
Gate-5 coordinator slice.** Everything else is invocation of already-verified
`.1R.7` logic in the RIHAC-001 §16 order.

---

## 8. Gate-5 output model (frozen)

Gate 5 emits exactly one **ephemeral, non-transferable** result:

- The existing `ValidatedAuthorityProjection` (`@dataclass(frozen=True,
  eq=False)`), trusted only via `is_trusted_validated_authority_projection`
  (exact-type + exact-object membership in the process-local
  `_VALIDATED_AUTHORITY_CONTEXTS` + recomputed `_content_binding_digest`).
- Plus a coordinator-level `Gate5Result` value that carries: the projection
  reference, the sequence-3 lifecycle event digest, the `proof_id`, and a
  fail-closed reason tuple. `Gate5Result` MUST be `eq=False` (identity
  equality) and MUST NOT be persisted, serialized, or reconstructable from
  fields — same discipline as `AuthenticatedHumanPrincipal` and
  `ValidatedAuthorityProjection`.

Prohibitions (frozen):

- **NOT** a boolean, and **NOT** a caller-copyable `validated=true` object
  used as a trust root (RIHAC-001 §16 step 12; RDGO-001 §6; the exact B1
  defect class).
- **NOT** a bearer token: possession of a `Gate5Result` or projection is
  never sufficient downstream. Every consumer (PB request builder today;
  Gate 9 later) MUST re-check `is_trusted_validated_authority_projection`
  **and** call `revalidate_validated_authority_projection` at its own point
  of use (this is already how `project_human_authority_binding` behaves —
  `runtime_dispatch_permission.py:504`–`:509`).
- **Consumes nothing.** No approval / proof / presentation / challenge /
  nonce state changes. Verified by a validation-only assertion (canonical
  `approval.json` bytes unchanged; no `proofs/v2/<id>/consumption.json`
  created) — `.1R.8` §7.3 already exercises this shape.

Repeat semantics: a second Gate-5 run before Gate 9 MUST produce a
byte-identical sequence-3 binding and re-run every check idempotently
(RDGO-001 §6; HPAC-REQ-097). A different approval/proof/presentation/
challenge/subject/invocation/attempt/principal/credential/mechanism digest
is cross-binding → fail closed.

---

## 9. Gate-5 failure model (fail-closed, no partial success)

The Gate-5 coordinator returns `(None, reasons)` and creates **no**
sequence-3 event for any of:

| Failure class | Representative reason (frozen source string family) |
|---|---|
| missing canonical authority | `no_valid_approval:missing_or_unresolvable` / `canonical_approval_store_required` |
| stale authority | `stale_approval:head_commit` / `stale:task_contract_digest` / `stale:task_state` |
| revoked principal | `authenticated_principal_reverification_failed:*` |
| revoked credential | `authenticated_principal_reverification_failed:*` |
| expired proof / challenge | `authenticated_principal_reverification_failed:*` |
| expired approval | `expired` |
| invalid invocation binding | `subject_mismatch:invocation_id` / `authenticated_principal_invocation_mismatch` / `approval_provenance_principal_mismatch` |
| invalid RIHAC projection | `is_trusted_validated_authority_projection` → False |
| NON_REAL assurance | `non_real_authenticated_principal_cannot_validate_production_approval` |
| unsupported mechanism | `authenticated_principal_reverification_failed:*` |
| internal resolver failure | `canonical_approval_resolution_failed:<ExcType>` / sequence-3 write failure → fail closed, no event |
| caller-supplied object / lookalike store | `noncanonical_approval_reference:caller_supplied_object` / `canonical_approval_store_required` |

No "best-effort", no auto-refresh, no fallback target, no permissive
default, no authority inference (RIHAC-001 §18).

---

## 10. Gate-9 ownership (frozen)

### 10.1 Decision — single owner: the Gate-9 atomic-consumption coordinator, backed by the protected evidence store's serialization boundary

**One new trusted coordinator component ("the Gate-9 atomic-consumption
coordinator", `src/pcae/core/runtime_dispatch_gate9.py` or equivalent)
owns the serialization/locking, the in-boundary revalidation, and the
compare-and-create call. It delegates the atomic create-only durable commit
to the already-existing
`RuntimeInvocationAuthorityConsumptionStore.create` (HPAC-REQ-100). It
delegates the in-boundary re-checks to the same components Gate 5 uses.**

No split ownership between coordinator and store: the store owns *only*
the atomic filesystem primitive (temp-sibling write → fsync → atomic link
if absent → fsync parent → read-back verify) and duplicate rejection
(`HPACDuplicateError`). The coordinator owns *everything else* —
serialization boundary acquisition, the HPAC-REQ-099 revalidation battery,
building the closed eight-item record, outcome encoding, and crash/replay
disposition.

| Gate-9 responsibility | Owner (frozen) |
|---|---|
| serialization / locking | Gate-9 coordinator (holds the protected evidence-store transaction/serialization boundary for `<HPAC_PROTECTED_ROOT>/proofs/v2/<proof_id>/`) |
| current-state revalidation (HPAC-REQ-099) | Gate-9 coordinator, invoking `reverify_authenticated_principal` + `validate_approval` + Gate-5 binding compare + `consumption_lookup` |
| proof consumption | the single `consumption.json` create (store primitive) — proof `consumed` is implied by record presence, no mutable field |
| approval consumption | same single create — approval ID/digest recorded in `authority_binding`; RIHAC repository store is *not* mutated (HPAC-REQ-102: "consumed solely by the protected §41 record") |
| atomic commit | `RuntimeInvocationAuthorityConsumptionStore.create` (HPAC-REQ-100) |
| retry status / already-consumed | Gate-9 coordinator, via `RuntimeInvocationAuthorityConsumptionStore.resolve` (returns `None` = absent, raises `...DurabilityUncertainError` = fail closed, returns record = already consumed) |
| crash recovery | Gate-9 coordinator, per HPAC-REQ-100/101 two-outcomes rule |

### 10.2 Gate-9 canonical primitive — how the coordinator uses the inert store

`runtime_invocation_authority_consumption.py` is used **unchanged in this
chapter** (no store code written — §17, §19). The coordinator calls:

| Operation | API (frozen, current) | Identity inputs |
|---|---|---|
| build record | `new_inert_consumption_record(...)` → replaced by a coordinator-owned `build_consumption_record(...)` that populates the *same* eight closed binding dicts from **real** Gate-1..8 evidence (the inert constructor stays test-only) | see below |
| commit | `RuntimeInvocationAuthorityConsumptionStore(root).create(proof_id, record)` | `proof_id` (from the bound proof) |
| resolve / already-consumed check | `RuntimeInvocationAuthorityConsumptionStore(root).resolve(proof_id)` | `proof_id` |

Closed record field-set the coordinator MUST populate (HPAC-REQ-098;
already encoded in `_BINDING_FIELD_SETS`):

- `request_identity`: `invocation_id`, `attempt_id`, `idempotency_key`
- `repository_task_binding`: `repository_identity`, `head_commit`, `task_id`,
  `task_contract_digest`, `phase_id`, `session_id`
- `target_binding`: `runtime_target_id`, `adapter_id`, `descriptor_version`,
  `descriptor_digest`, `target_config_digest`, `executable_identity_digest`
- `prompt_binding`: `prompt_hash`, `prompt_hash_profile`
- `authority_binding`: `approval_id`, `approval_digest`,
  `authority_projection_id`, `authority_projection_digest`,
  `authority_contract_version` (`RIHAC-001/2.0`), `proof_id`, `proof_digest`,
  `proof_validation_digest`, `registry_state_digest`, `approval_subject_digest`,
  `trusted_presentation_ref`, `challenge_digest`
- `pb_binding`: `request_digest`, `decision_digest`, `decision`,
  `policy_version`, `causing_policy_ids`, `matched_no_go_ids`
- `runtime_enforcement_binding`: `decision_id`, `decision_digest`, `verdict`,
  `expires_at`, `evaluated_input_digest`
- `dispatch_binding`: `containment_evidence_ref`, `state`
  (`dispatch_attempted`), `consumed_at`

**Transaction / invocation / proof / approval / RIHAC identity, predecessor
state, outcome encoding** are all defined by the record above +
HPAC-REQ-100's two-outcome rule. The store is **not changed** in this
planning phase and its implementation phase (§16) modifies it only if
independent verification of that phase finds a concrete gap (none is
anticipated — the inert store already provides create-only atomicity,
duplicate rejection, symlink rejection, digest self-check, and
durability-uncertain classification).

### 10.3 Hard dependency discovered during planning (§13.1)

`pb_binding` and `runtime_enforcement_binding` and
`dispatch_binding.containment_evidence_ref` are **required closed fields**
of the consumption record. Therefore **Gate 9 cannot be wired to a
production dispatch without Gate 6 (PB decision), Gate 7 (Runtime
Enforcement decision), and Gate 8 (containment evidence) each producing
their evidence first.** Gate 7 and Gate 8 do not exist. This constrains the
Gate-9 implementation slice (§16): it is either (a) blocked until Gate-7/8
chapters exist, or (b) explicitly scoped as *structural coordinator +
in-boundary revalidation + atomic-consumption + crash/replay/concurrency
semantics exercised through a test-only harness that supplies synthetic
Gate-6/7/8 evidence*, with the production path unreachable (Gate-5 NON-REAL
hard stop). This planning phase recommends (b) with explicit human
authorization, and freezes the ID accordingly (§16).

---

## 11. Gate-9 atomicity model (frozen)

The plan demonstrates one atomic authority transition:

```text
proof becomes consumed  +  approval becomes consumed  +  presentation consumed  +  challenge consumed
        ≡  exactly one successful RuntimeInvocationAuthorityConsumptionStore.create(proof_id, record)
```

- **Single write.** There is no separate mutable `consumed` field anywhere
  (HPAC-REQ-098). "Consumed" ≡ "one complete valid `consumption.json`
  exists at the proof's protected path". The RIHAC repository approval
  store is never mutated to mark consumption (HPAC-REQ-102).
- **No state where only one of {proof, approval} is consumed** — they share
  one record; a partial/corrupt record is `...DurabilityUncertainError` →
  no dispatch, not "half consumed" (HPAC-REQ-100).
- **No external effect before the record is durable and read-back
  verified** (RDGO-001 §10; Gate 10 is strictly after Gate 9).
- **No double consumption on retry** — `create` uses
  `write_atomic_create_only`; a second attempt hits `FileExistsError` →
  `HPACDuplicateError`; a byte-identical existing record is "already
  consumed", not a re-entry licence (HPAC-REQ-100).

---

## 12. Revalidation inside the serialization boundary (mandatory — HPAC-REQ-099)

Inside the protected Gate-9 serialization boundary, immediately before
compare-and-create, the coordinator re-runs (fail closed on any):

| Re-check | Mechanism |
|---|---|
| principal revocation / currentness | `reverify_authenticated_principal(now=<gate9 time>)` |
| credential revocation / currentness | same |
| proof expiry / currentness / lifecycle chain | same + `hpac_lifecycle` resolve |
| approval expiry / currentness / freshness | `validate_approval(approval_id, ..., context=<refreshed current_time>)` |
| exact Gate-5 sequence-3 binding | compare current sequence-3 event digest to the one recorded at Gate 5 |
| invocation binding | `context.invocation_id` / `principal.invocation_id` / `approval.subject.invocation_id` / identity triple |
| lifecycle state | `hpac_lifecycle` sequence == 3, not terminal |
| PB / RE freshness | `pb_binding.decision_digest` / `runtime_enforcement_binding.decision_digest` still current for the exact request |
| already-consumed state | `RuntimeInvocationAuthorityConsumptionStore.resolve(proof_id)` is `None` |
| registry / descriptor / configuration state digest | recompute `registry_state_digest`; compare |

This closes the Gate-5 → Gate-9 stale-state window. Revocation, expiry,
invalidation, or drift after Gate 5 but before the atomic create fails
closed with **no** TOCTOU allowance (RDGO-001 §10; RIHAC-001 §17;
HPAC-REQ-099).

> **Erratum — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4.** "Inside the
> protected Gate-9 serialization boundary" here means: inside the window
> whose linearization point is the per-`proof_id` create-only atomic
> primitive (there is no separate held lock — see the §13.5 erratum). The
> battery re-runs immediately before the create; the `.1R.15.2` V-15-1
> repair adds a final zero-effectful-I/O authority-generation-token re-check
> (`S1`/`S2`) between the battery and the create. RDGO-001 v3.1 §10 /
> HPAC-001 v2.1 HPAC-REQ-099 are the normalized statement.

---

## 13. Findings and blockers discovered during planning

### 13.1 Non-blocking sequencing constraint — Gate 9 depends on Gates 6/7/8 evidence

See §10.3. The consumption record's closed field set requires PB, Runtime
Enforcement, and containment evidence. **Not a contract contradiction** —
RDGO-001 §10 item 6/7/8 explicitly lists these as Gate-9 inputs, and the
gate order already places 6/7/8 before 9. It *is* a scoping constraint on
the implementation packaging (§16). Recorded, not silently carried.

### 13.2 Non-blocking — Gate 7 (Runtime Enforcement) and Gate 8 (Shell Gate) are unbuilt

`RuntimeEnforcementCoordinator` is "design-only, non-executing,
non-authorizing"; `shell_gate.py` is not wired as a gate. These are the
"distinct, unscheduled later chapter" referenced in `.1R.8` §33. This
planning phase does **not** invent IDs for them. A full production Gate-9 →
Gate-10 path is blocked on both; that is expected and is not a regression.

### 13.3 Non-blocking gap — `validate_approval` does not create HPAC lifecycle sequence 3

RDGO-001 §6 and HPAC-REQ-097 require Gate 5 to atomically create
`3 PROOF_VERIFIED_AND_BOUND`. Current `validate_approval` emits the
projection but does not touch `hpac_lifecycle`. Because the NON-REAL hard
stop makes the emission path unreachable (O1), nothing is currently broken.
**This is frozen as a prerequisite inside the Gate-5 implementation slice
(§16), not a separate finding** — the Gate-5 coordinator owns the
sequence-3 write (§6.2 row 23, §7 row 23).

### 13.4 O1–O4 adjudication for coordinator integration

| Finding | Exact issue (§1.5) | Current severity | Does Gate-5/9 consumption change its consequence? | Prerequisite? | Repair in this chapter? | Disposition |
|---|---|---|---|---|---|---|
| **O1** | B1 positive-emission path unreachable under Option-A NON-REAL | non-blocking, inherent | **No** — Gate-5/9 wiring keeps the NON-REAL hard stop; the emission path stays unreachable in production. It *does* make the predicate/consumer-level verification the coordinator relies on the correct verification level. | No | No | **Carried unchanged.** Becomes end-to-end testable only with a real assurance mechanism (out of chapter). The Gate-5/9 slices are verified at predicate + coordinator level, exactly as `.1R.8` verified B1. |
| **O2** | N1 store trust is path+file integrity, not a cryptographic writer seal | non-blocking (documented F7 boundary) | **Marginally.** Gate 9 reads `approval_digest`/`proof_id` from Gate-5 output, and re-resolves the approval by ID inside the serialization boundary (§12). A planted schema-valid record in the canonical approval dir is still the F7 same-account threat model — unchanged. Gate 9's `consumption.json` lives under `HPAC_PROTECTED_ROOT` whose `production()` fails closed on any agent-writable root, which is a *stronger* boundary than the approval store's. | No | No | **Carried unchanged.** A future writer-provenance / schema-migration chapter closes it if ever required. The Gate-9 coordinator MUST NOT assume the approval store has writer provenance it does not have; it relies on the protected-root boundary for its own record. |
| **O3** | `test_*_detected_by_fresh_reverification` naming over-promise (F4 class) | non-blocking, cosmetic | **No** | No | No | **Carried unchanged.** The Gate-5/9 verification phases (§16) MUST name their own reverification tests accurately (which stage rejects), so O3's class is not propagated into new code. |
| **O4** | `pcae doctor task-memory` historical `tasks/DONE.md` omissions | non-blocking, hygiene | **No** — unrelated to any code path | No | No | **Carried separately.** Not repaired in a coordinator-integration phase. Eligible for a dedicated governance-record hygiene task at any time. |

### 13.5 F2 / F3 / F4 / F7 adjudication for coordinator integration

Re-checked against the `.1R.8` verifier line (§15) and `.1R.7` §10.

| Finding | Exact status (verified) | Does coordinator consumption change severity? | Disposition for this chapter |
|---|---|---|---|
| **F2 / HPAC-REQ-054 Step 4** | REPAIRED, independently confirmed implemented and effective (`.1R.8` §6, §14). Independent challenge-digest recomputation from the exact 10-field canonical body; literal step order Step 3→4→5→6→7→8→9 preserved. | It becomes *load-bearing*: the Gate-5 coordinator relies on Step 4 to reject a substituted/replayed ceremony. It is already implemented, so no new prerequisite. | **Confirmed prerequisite already satisfied.** The Gate-5 slice MUST route through `reverify_authenticated_principal` (which executes HPAC-REQ-054 including Step 4); a Gate-5 verification test MUST include a self-consistent substituted-challenge rejection case. |
| **F3** (`.1R.4` "eight-step" planning-doc label debt) | NON-BLOCKING, unchanged; documentation-labeling only; production trust semantics unaffected. | **No.** | **Carried, deferred.** No repair required. |
| **F4** (`test_caller_constructed_verifier_result_rejected` name overclaim) | NON-BLOCKING, unchanged; cosmetic; functionally covered by accurately-named siblings. | **No.** | **Carried, deferred.** New coordinator tests MUST be accurately named (§13.4 O3). |
| **F7** (registry resists caller-supplied-data forgery, not same-process arbitrary code execution) | NON-BLOCKING observation, **not broadened** by `.1R.7` (`.1R.8` §15). | **No — must remain accurately scoped.** Anything previously harmless with zero consumers (the inert Gate-9 store, `revalidate_validated_authority_projection`) now gains a real consumer. The threat model is **not** upgraded: the Gate-5/9 coordinators run under the same-account autonomous-agent assumption (`.1R.6` §16); no UID / username / process-ownership / stdin-stdout / Git identity / PCAE session identity / producer identity is trusted. Only the verified HPAC provenance chain establishes human authentication. | **Carried unchanged, threat model NOT broadened.** The planning and both verification phases MUST state F7's boundary verbatim: HPAC/coordinator integration is not asked to solve arbitrary in-process compromise; a process-isolation/hardening chapter remains a legitimate, separate, unscheduled later topic and is **not** a prerequisite for Gate-5/Gate-9 wiring. |

### 13.6 HPAC-REQ-054 Step 4 — mandatory before Gate 5?

**Yes — and it is already implemented (F2, `.1R.7`, `.1R.8`-verified).**
The Gate-5 coordinator's dependency on Step 4 is satisfied by calling
`reverify_authenticated_principal`. **Frozen as a satisfied prerequisite:**
the Gate-5 implementation slice (§16, `.1R.10`) MUST NOT bypass
`reverify_authenticated_principal`, and its verification slice (`.1R.11`)
MUST independently re-derive the Step-4 recomputation and prove a
self-consistent substituted-challenge is rejected at Gate 5.

### 13.7 No contract blocker

No contradiction was found between RDGO-001 v3.0, RIHAC-001 v2.0,
RIASC-001 v3.0, HPAC-001 v2.0, PBRD-001 v2.0, RPAC-001 v1.0, POL-005/PBPA,
and the coordinator integration planned here. §13.1's sequencing
constraint is an ordering consequence the contracts already state
(RDGO-001 §10), not a contradiction. **No contract evolution is
recommended or required for the Gate-5 slice.** (A future real-assurance
mechanism, real FIDO2/UI, and the Gate-7/Gate-8 chapters will each require
their own contract review; that is out of scope here.)

If any implementation slice's own planning later reveals a contradiction,
the governing rule stands: **STOP and record a contract blocker; recommend
contract evolution before implementation; do not silently reinterpret.**

---

## 14. Restart / recovery model

| State at restart | Persisted? | Recovery behavior (frozen) |
|---|---|---|
| verifier provenance (`AuthenticatedHumanPrincipal` registry membership) | **No** (process-local, `__reduce__` raises) | Re-authentication is **mandatory**. A pre-restart principal fails `is_verifier_authenticated_principal` → `authenticated_principal_not_verifier_issued`. No coordinator may treat a principal as valid across a restart. |
| `ValidatedAuthorityProjection` / `_VALIDATED_AUTHORITY_CONTEXTS` | **No** (process-local dict) | Gate-5 result loss → re-run Gate 5 from scratch. A projection cannot be rebuilt from caller/public fields (B1). |
| `Gate5Result` | **No** (identity-only, non-serializable) | Re-run Gate 5. |
| persisted approval (`RuntimeInvocationApprovalStore`) | Yes | Still requires full Gate-5 re-validation; persisted fields alone are not authority (N1). |
| persisted proof / lifecycle (`HPAC_PROTECTED_ROOT`) | Yes | Re-resolved fresh at Gate 5 and again in-boundary at Gate 9; sequence-3 must still be same-binding. |
| dispatch-identity registry (`.pcae/runtime-dispatch-identities/v1/**`) | Yes | `revalidate` re-reads and exact-matches; mismatch fails closed (B7). |
| Gate-9 pre-commit state (boundary held, record not yet created) | **No** (crash loses the boundary) | HPAC-REQ-100: final artifact absent → **not consumed**, no Gate-10 effect; only full revalidation permits another create attempt. |
| Gate-9 committed state (`consumption.json` present, valid) | Yes | **Consumed.** `resolve(proof_id)` returns the record → "already consumed"; dispatch/retry with that authority prohibited. Every retry needs fresh invocation/attempt/presentation/challenge/proof/approval. |
| Gate-9 ambiguous / corrupt / partial | n/a | `...DurabilityUncertainError` → fail closed, manual recovery, **never replay** (HPAC-REQ-100/101). |
| PB decision / RE decision | evidence only | Never cached across restart or any drift; re-evaluate (PBRD-001 §10; RDGO-001 §15). |

**No transient authority is ever reconstructed from caller or public
fields.**

---

## 15. Coordinator state machine (pre-Gate-5 → Gate-10 boundary)

Using RDGO-001 §17 / RIHAC-001 §19 / HPAC-REQ-101 terminology.

```text
        ┌─────────────────┐
        │  UNVALIDATED    │  (identity triple minted at gate 2; principal authenticated at gate 3;
        │ (PRE_APPROVAL_  │   approval created at gate 3 — NON-REAL hard stop today)
        │  CONSUMPTION)   │
        └───────┬─────────┘
                │ Gate-5 coordinator runs §7 revalidation battery in RIHAC-001 §16 order
                │  success ⇒ create HPAC lifecycle seq 3 PROOF_VERIFIED_AND_BOUND;
                │            emit ephemeral ValidatedAuthorityProjection + Gate5Result
                ▼
        ┌─────────────────┐   repeat Gate 5 (same-binding only) ─┐
        │ GATE5_VALIDATED │ <───────────────────────────────────┘  (idempotent; consumes nothing)
        │ (APPROVAL_      │
        │  VALIDATED)     │
        └───────┬─────────┘
                │ Gate 6 (PB) evaluates the 14-fact runtime_dispatch request
                │  DENY / HUMAN_REVIEW / PB failure ⇒ STOP (fail closed)
                ▼
        ┌─────────────────┐
        │  PB_EVALUATED   │   (POL-005 ⇒ DENY today; state reachable only in test-path-first scope)
        └───────┬─────────┘
                │ Gate 7 (Runtime Enforcement) — NOT IMPLEMENTED (blocked)
                ▼
        ┌─────────────────┐
        │  RE_EVALUATED   │   (unreachable until Gate-7 chapter)
        └───────┬─────────┘
                │ Gate 8 (containment) — NOT IMPLEMENTED (blocked)
                ▼
        ┌─────────────────┐
        │ CONTAINMENT_    │   (unreachable until Gate-8 chapter)
        │ ESTABLISHED     │
        └───────┬─────────┘
                │ Gate-9 coordinator: acquire protected serialization boundary;
                │  §12 in-boundary revalidation battery; build closed 8-item record;
                │  RuntimeInvocationAuthorityConsumptionStore.create(proof_id, record)
                │  any failure / drift / uncertainty ⇒ STOP (fail closed, nothing consumed
                │  unless a complete valid record exists)
                ▼
        ┌─────────────────┐
        │ GATE9_CONSUMED  │   proof + approval + presentation + challenge consumed together;
        │ (DISPATCH_      │   dispatch_attempted durable + read-back verified
        │  ATTEMPTED)     │
        └───────┬─────────┘
                │ Gate 10 — first external effect (OUT OF THIS CHAPTER; never approached)
                ▼
        ┌─────────────────┐
        │ READY_FOR_GATE10│  → { DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER | DISPATCH_UNCERTAIN }
        └─────────────────┘     → RESULT_CAPTURED_UNTRUSTED
```

**Forbidden transitions (frozen):**

- `UNVALIDATED → PB_EVALUATED` (skipping Gate 5) — PB request builder
  yields `approval_present=False` with no projection; no later gate infers
  approval.
- `GATE5_VALIDATED → GATE9_CONSUMED` (skipping Gates 6/7/8) — the
  consumption record's closed fields cannot be populated.
- any `* → GATE9_CONSUMED` without holding the serialization boundary and
  passing §12.
- `GATE9_CONSUMED → GATE9_CONSUMED` for the same authority (one-shot).
- any `* → READY_FOR_GATE10` before `GATE9_CONSUMED` is durable and
  read-back verified.
- `GATE9_PENDING (crash) → GATE9_CONSUMED` on restart without a complete
  valid on-disk record.
- reconstructing `GATE5_VALIDATED` from persisted fields after a restart
  (process-local provenance is gone).

**Repeatable vs one-shot:** `UNVALIDATED ↔ GATE5_VALIDATED` (Gate 5) is
idempotently repeatable (same-binding). `GATE5_VALIDATED → GATE9_CONSUMED`
(Gate 9) is strictly one-shot. They MUST NOT be conflated.

---

## 16. Implementation packaging and exact frozen phase IDs

### 16.1 Packaging decision (frozen)

**Four slices, each trust-bearing, each followed by an independent
verification phase.** Not over-fragmented (Gate 5's sub-checks are not
independently meaningful); not over-bundled (Gate 5 / PB / Gate 9 have
distinct trust and atomicity boundaries — Gate 5 consumes nothing, PB is
policy-only, Gate 9 is the atomic one-shot consumption point).

| Order | Slice | Trust boundary | Independent verification |
|---:|---|---|---|
| 1 | **Gate-5 approval-validation coordinator** — new coordinator component; owns RIHAC-001 §16 sequencing, `reverify_authenticated_principal` provenance, **HPAC lifecycle sequence-3 creation (§13.3)**, ephemeral non-transferable output (§8), fail-closed model (§9). NON-REAL hard stop unchanged. No PB, no Gate 9, no store change. | approval validation orchestration + lifecycle sequence-3 | required |
| 2 | **Gate-6 Permission Broker production consumption** — wire a real `runtime_dispatch` `PermissionBrokerRequest` carrying the Gate-5 validated projection (PBRD-001 §7 `human_authority_binding`, §14) through the current PB evaluator; preserve `DENY > HUMAN_REVIEW > ALLOW`; POL-005 still DENYs `simulation_only=False`. No PB policy/evaluator change; no POL-005 change. | policy permission after trusted authority exists | required |
| 3 | **Gate-9 atomic authority-consumption coordinator** — new coordinator component; owns the protected serialization boundary, §12 in-boundary revalidation, closed 8-item record construction, `RuntimeInvocationAuthorityConsumptionStore.create` call, crash/replay/concurrency disposition (§11, §17, §18). **Precondition: either Gate-7 and Gate-8 chapters exist, OR explicit human authorization for a test-path-first scope** where synthetic Gate-6/7/8 evidence drives the coordinator through a non-production-reachable harness (production path stays unreachable via the Gate-5 NON-REAL hard stop). Store code unchanged unless its own verification finds a concrete gap. | atomic one-shot consumption boundary | required |
| — | **Gate 7 (Runtime Enforcement), Gate 8 (Shell Gate / containment)** | distinct, larger, **unscheduled** chapters — **no ID invented here** (no-invent-an-ID discipline). Each needs its own planning phase under explicit human authorization. |

### 16.2 Frozen phase IDs (immediate next steps — no ambiguity)

Per this project's no-invent-an-ID discipline and this numbering family:

- **`149O.20L.7O.3W.1R.2B.1R.1.1R.10`** — **Gate-5 Approval-Validation
  Coordinator Integration Implementation.** Scope: slice 1 above +
  §13.3 sequence-3 prerequisite, confined to a new
  `runtime_dispatch_gate5.py` (or equivalent) plus minimal wiring in
  `runtime_authority.py` / `hpac_lifecycle.py` as §6.2 row 23 requires.
  Requires separate explicit human authorization to start.
- **`149O.20L.7O.3W.1R.2B.1R.1.1R.11`** — **Independent Verification of
  Gate-5 Approval-Validation Coordinator Integration.** Scope:
  independently re-derive §7's revalidation matrix, §8's output model,
  §9's failure model, and §13.6's Step-4 substituted-challenge rejection,
  against the `.1R.10` implementation — not trusted from `.1R.10`'s own
  report or tests. Discipline per `.1R.5.2.1` / `.1R.8`.
- **`149O.20L.7O.3W.1R.2B.1R.1.1R.12`** — **Gate-6 Permission Broker
  Production Consumption Integration Implementation.** Scope: slice 2
  above. Requires separate explicit human authorization.
- **`149O.20L.7O.3W.1R.2B.1R.1.1R.13`** — **Independent Verification of
  Gate-6 Permission Broker Production Consumption Integration.**
- **`149O.20L.7O.3W.1R.2B.1R.1.1R.14`** — **Gate-9 Atomic Authority
  Consumption Coordinator Integration Implementation.** Scope: slice 3
  above. **Blocked** until Gate-7/Gate-8 chapters exist *or* an explicit
  human authorization records the test-path-first scope of §16.1 row 3.
  Requires separate explicit human authorization regardless.
- **`149O.20L.7O.3W.1R.2B.1R.1.1R.15`** — **Independent Verification of
  Gate-9 Atomic Authority Consumption Coordinator Integration.**

The Gate-7 and Gate-8 chapters are **not** frozen with IDs here.

---

## 17. Gate-9 crash / retry / replay semantics (frozen)

### 17.1 Crash before atomic commit

Process stops before `consumption.json` is durably created and read-back
verified. Required outcome:

```text
proof = unconsumed
approval = unconsumed
external effect = none
```

`RuntimeInvocationAuthorityConsumptionStore.resolve(proof_id)` returns
`None` (final path absent). Retry MAY restart, but MUST re-run the full
Gate-5 validation, Gates 6/7/8, and the §12 in-boundary battery before a
new `create` attempt (RIHAC-001 §19; HPAC-REQ-100/101).

### 17.2 Crash after atomic commit, before Gate 10

```text
proof = consumed
approval = consumed
external effect = none
```

Retry MUST detect the existing valid record via `resolve(proof_id)` and
report **already consumed**; it MUST NOT consume again and MUST NOT
continue to effect. An ambiguous restart state (`...DurabilityUncertainError`)
MUST fail closed — never silently continue to Gate 10 (RDGO-001 §17;
RIHAC-001 §19; HPAC-REQ-100/101). A new attempt requires a fresh
invocation and approval.

### 17.3 Replay rejection (all fail closed)

| Replay vector | Rejected by |
|---|---|
| same proof + same approval | existing `consumption.json` at `proofs/v2/<proof_id>/` → `HPACDuplicateError` |
| same proof + different approval | §12 in-boundary approval re-resolution + Gate-5 binding compare; also `proof_id` already has a record |
| different proof + consumed approval | §12: `consumption_lookup(approval_id)` / durable invocation state shows prior binding → `already_bound:*` |
| copied consumption record (planted at a different `proof_id`) | `record_digest` self-check + `authority_binding` cross-digests + `resolve` durability checks; and the proof/lifecycle chain for that `proof_id` will not match |
| stale consumption request (Gate-5 result older than current state) | §12 in-boundary revalidation (`reverify_authenticated_principal` / `validate_approval` with current time) |
| cross-invocation consumption | `request_identity` triple + `authority_binding.approval_id` + `principal.invocation_id` all bound and compared in §12 |

---

## 18. Gate-9 concurrency model (frozen)

Two concurrent requests for the same proof/approval:

- **At most one Gate-9 consumption succeeds.** `write_atomic_create_only`
  installs the final path only if absent (`O_EXCL` on the temp sibling +
  atomic link-if-absent); the loser gets `FileExistsError` →
  `HPACDuplicateError`.
- The loser receives a **deterministic already-consumed / conflict
  result** — the coordinator maps `HPACDuplicateError` to a stable
  `gate9_already_consumed` outcome, never a ret--able error.
- **No split-brain, no double effect.** The serialization boundary is the
  per-`proof_id` protected directory; the coordinator acquires it before
  the §12 battery so two racers cannot both pass revalidation and both
  create.
- **Lock scope:** exactly `<HPAC_PROTECTED_ROOT>/proofs/v2/<proof_id>/`.
  **Lock ordering:** single lock per Gate-9 invocation, acquired after
  Gate-5/6/7/8 evidence is assembled and before the §12 battery; released
  after `create` returns or raises. **Deadlock:** impossible with a single
  per-proof lock and no nested acquisition. **Crash while held:** the OS
  releases it; on-disk state is governed by HPAC-REQ-100's two-outcome
  rule, not by lock state. **Stale lock:** if an advisory lock file is
  used, it MUST carry no authority and MUST be safe to break after a
  bounded timeout with a fresh full revalidation — it is a contention
  hint, never a consumption fact.

**Reuse existing PCAE primitives:** the atomic create-only /
duplicate-detecting / symlink-rejecting / digest-self-checking machinery in
`hpac_foundation` (`write_atomic_create_only`, `reject_symlink`,
`read_canonical_json_document`, `canonical_digest`) already backs the inert
store. **Do not invent a new lock** — the protected create-only commit is
itself the atomic transaction; an added advisory lock (if any) is only a
contention optimizer. This is frozen: the Gate-9 implementation slice
SHALL reuse `RuntimeInvocationAuthorityConsumptionStore` +
`hpac_foundation` primitives and SHALL NOT introduce a second transaction
mechanism.

> **Erratum — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 (V-15-1
> normalization).** §13.5's "**Lock scope** … **Lock ordering:** single
> lock per Gate-9 invocation, acquired … before the §12 battery; released
> after `create`" language is **internally contradicted** by the immediately
> following "**Do not invent a new lock** — the protected create-only commit
> is itself the atomic transaction … SHALL NOT introduce a second
> transaction mechanism." Finding V-15-1 (`.1R.15.1` §12) recorded this. The
> `.1R.15.2` / `.1R.15.3` independently verified implementation, and RDGO-001
> **v3.1** §10 / HPAC-001 **v2.1** HPAC-REQ-099, resolve it to the
> **create-only-linearization** model: there is **no** held lock. The
> per-`proof_id` create-only atomic primitive (`write_atomic_create_only`)
> IS the serialization boundary and the sole transaction mechanism. The §12
> revalidation battery runs immediately before it, followed by a monotonic
> authority-generation snapshot `S1` re-read as `S2` with zero intervening
> effectful I/O; any `S2 != S1` fails closed. This is the "no TOCTOU
> allowance" guarantee to the practical limit without a second lock. The
> "Lock scope / Lock ordering" bullet is superseded; the "Do not invent a
> new lock" bullet and §18 are the correct, frozen model.

---

## 19. Gate-9 receipt / result semantics (frozen)

Gate-9 success returns an **internal ephemeral consumed-authority marker**
(`Gate9Result`, `eq=False`, non-serializable, process-local), carrying the
`proof_id`, the `consumption.json` `record_digest`, and the
`dispatch_binding.state`.

- It is **NOT a reusable bearer token.** Possession does not authorize
  anything. Gate 10 (out of chapter) would re-read the durable
  `consumption.json` and the containment evidence, not trust an in-memory
  marker.
- If a transaction receipt is surfaced for audit, it is a **reference to
  the durable record**, and it **MUST NOT itself authorize future
  execution independently** (HPAC-REQ-100: a byte-identical record is
  "already consumed", not a re-entry licence).
- The RIHAC repository approval store is **not** written by Gate 9
  (HPAC-REQ-102). Any repository-side dispatch record is a non-authoritative
  mirror.

---

## 20. Gate-10 boundary (frozen — identified, not touched)

Gate 10 is the first external execution effect (RDGO-001 §11). The exact
existing source location that will *eventually* represent Gate 10 is the
**Runtime Adapter transport dispatch call** — today only
`src/pcae/core/mock_runtime_adapter.py` (mock/dry) and the
`runtime_adapter.py` protocol exist; a real local-CLI adapter transport
does not. **This planning phase does not modify or invoke it.**

Frozen invariant, all slices in this chapter:

```text
no subprocess
no provider / network call
no adapter invocation (real or mock, beyond existing unrelated tests)
no repository-external mutation
no credential access
no hardware access
```

before Gate 10, and Gate 10 is never approached.

---

## 21. Deterministic NON-REAL hard stop (frozen)

### 21.1 Can structural Gate-5/Gate-9 coordinator wiring be implemented before real FIDO2/UI?

**Yes for Gate 5 and Gate 6** — same Option-A logic `.1R.6` §7 verified for
B1/B7/N1/N2: the defects being addressed (missing coordinator, missing
lifecycle side-effect, missing PB consumer) are **structural wiring gaps**,
not "premature positive authority" risks. The NON-REAL hard stop in
`validate_approval:1093` is assurance-gated and unconditionally active, so
the fully wired Gate-5 coordinator **still returns fail-closed in
production** for every real request until a real assurance mechanism
exists.

**Yes for Gate 9 only under the test-path-first scope of §16.1 row 3** —
because production Gate 9 is unreachable anyway (Gate 5 never emits a
projection), and Gates 6/7/8 evidence is required for a production record.

### 21.2 Hard-stop owner

**Unchanged:** `runtime_authority.validate_approval` at line 1093
(`principal.assurance_class is not HPACAuthorityClass.PRODUCTION` →
`non_real_authenticated_principal_cannot_validate_production_approval`), and
`create_runtime_invocation_approval` at line 457. RDGO-001 §6 anticipates
this check moving *into* Gate 5's responsibilities; the Gate-5 coordinator
**invokes** `validate_approval` and therefore inherits the stop — it does
**not** re-implement or relocate it in this chapter. Relocation happens
only when a real assurance mechanism and a real Gate 5 make it meaningful.

### 21.3 Guarantee that deterministic fixtures cannot be consumed as real production authority

- `HPACStoreAuthority.writer` raises unless `authority_class is
  FIXTURE_NON_REAL`; no `PRODUCTION` writer exists → every verifier result
  is `FIXTURE_NON_REAL`.
- Both authority construction points reject non-`PRODUCTION` assurance.
- The test-only inert record constructor (`new_inert_consumption_record`)
  and the test-only approval fixture path (`.1R.6` §9) remain
  **non-importable from production modules**, enforced by the existing
  AST-based forbidden-import check (`.1R.8` §23 case 28). The Gate-5 and
  Gate-9 coordinator slices MUST extend that check to cover the new
  coordinator modules (frozen requirement).

### 21.4 Should NON-REAL reach Gate 9? — **NO.**

Default safety expectation upheld. In production, NON-REAL never reaches
Gate 9 because Gate 5 never emits a projection. Any deterministic-fixture
Gate-9 exercise MUST be a **wholly separate test-only path** that:

- constructs its own inert `RuntimeInvocationAuthorityConsumption` records
  (or synthetic Gate-5/6/7/8 evidence) via test-only constructors;
- never routes through `validate_approval`'s emission path;
- is proven non-importable from any production module by the AST check;
- writes only to a test-scoped temporary root, never `HPAC_PROTECTED_ROOT`
  as resolved in production.

**This is not a development bypass** — it exercises the store's and
coordinator's atomicity/crash/replay/concurrency behavior against a
structurally correct payload shape, exactly as `.1R.3` did for the inert
store, and it cannot produce production authority.

---

## 22. Permission Broker sequencing (frozen)

### 22.1 Decision — PB production consumption is a **subsequent, independently verified slice** (`.1R.12` / `.1R.13`), not the same slice as Gate-5, and before Gate-9

Assessment:

| Criterion | Finding |
|---|---|
| authority risk | Gate 5 establishes trusted authority; PB only evaluates policy *after* it. Bundling would mix "is this authority valid" with "does policy permit the class" — distinct trust boundaries. |
| testability | PB consumption is independently testable: a Gate-5 projection in, a `DENY`/`ALLOW`/`HUMAN_REVIEW` decision out, POL-005 regression. |
| atomicity | PB evaluation consumes nothing (PBRD-001 §7); no atomicity concern — unlike Gate 9. |
| scope | PB slice touches the PB request-builder wiring and (possibly) a thin production consumer; no PB policy/evaluator change, no POL-005 change. |
| PBRD-001 v2.0 | fully governs this consumer already (§7 approval reference, §10 gate independence, §14 RE projection). **No fresh planning phase required** — `.1R.12` implements directly against PBRD-001. |
| POL-005 | unchanged; `simulation_only=False` still DENY (PBRD-001 §12). |

**Order: Gate 5 (`.1R.10`) → verify (`.1R.11`) → PB (`.1R.12`) → verify
(`.1R.13`) → Gate 9 (`.1R.14`) → verify (`.1R.15`).** Gate 9 is last
because its consumption record needs `pb_binding` (and
`runtime_enforcement_binding`, `containment_evidence_ref`).

### 22.2 PB's role (preserved verbatim from PBRD-001 §7, §10)

```text
PB does not authenticate humans.
PB does not parse FIDO2 assertions, read HPAC registries, or receive raw proof material.
PB does not establish approval.
PB evaluates permission only AFTER trusted human authority exists, and BEFORE Runtime Enforcement.
```

PB's exact input (PBRD-001 §4 fact 14 + §7):

- the immutable approval reference (`approval_id`, `approval_digest`);
- the exact RIHAC-001 v2.0 validated-authority projection reference/digest
  (`authority_projection_id`, `authority_projection_digest`,
  `authority_contract_version` const `RIHAC-001/2.0`,
  `proof_validation_digest`, `request_binding_digest`) — i.e. the Gate-5
  output, never Gate-9 consumed-authority state (PB runs before Gate 9).

Only successful RIHAC-001 v2.0 validation may set `approval_present=true`;
it is a derived POL-004 input, not authority, not caller-settable
(PBRD-001 §7). Contract order: **Gate 5 → Gate 6 (PB) → Gate 7 (RE) → …**
(RDGO-001 §1, §7, §10).

---

## 23. POL-005 (frozen — hard DENY preserved)

`ExecutionDisabledRule` (`policy_id = "POL-005"`,
`permission_broker_foundation.py`) is **not modified** by any slice in this
chapter. It is universal, non-overridable
(`override/approval/risk` all False), and returns `DECISION_DENY` /
`execution_boundary_unavailable` / `matched_no_go_ids=("NG-025",)` for
every `simulation_only=False` request. The Gate-5/Gate-6/Gate-9 coordinator
integration **cannot bypass or weaken POL-005**:

- Gate 5 emits validation evidence, not permission — POL-005 is a PB-side
  rule Gate 5 never touches.
- Gate 6 runs the *unmodified* evaluator; POL-005 fires first by
  `DENY > HUMAN_REVIEW > ALLOW` precedence.
- Gate 9 is downstream of a `DENY` and is unreachable in production.

A future narrowly-scoped POL-005 eligibility rule for the exact local-CLI
`runtime_dispatch` profile (PBRD-001 §12) is **out of scope** and would
require all eleven PBRD-001 §12 preconditions + its own independent
verification.

---

## 24. Runtime capability (frozen — independent, unchanged)

Even after a future successful Gate 5, Gate 9, and PB ALLOW, the runtime
capability check remains **independent** (RPAC-001 §"execution
availability" is independent of PB ALLOW). Current state
(`runtime_introspection.py`): `CURRENT_RUNTIME_STATE = "Observed"`,
`CURRENT_MAXIMUM_PLUGIN_CAPABILITY = "observe"`, `EXECUTION_AVAILABILITY =
"unavailable"`; registry empty; PB status `execution_unavailable`; posture
`non-executing`. **No phase in this chapter may imply capability
elevation.** `runtime inspect` repair (PBRD-001 §12 item 10) is a separate
precondition for any real adapter availability claim and is not addressed
here.

---

## 25. Production file matrix (anticipated — minimize modification)

| File | Current role | Proposed change | Gate affected | Authority sensitivity | Tests required | Slice |
|---|---|---|---|---|---|---|
| `runtime_dispatch_gate5.py` **(new)** | — | Gate-5 approval-validation coordinator: sequences `validate_approval` + `reverify_authenticated_principal`; owns HPAC lifecycle seq-3 creation; emits ephemeral `Gate5Result` | 5 | **High** | forged/copied/mutated projection rejected; each §7 revalidation row; substituted-challenge (Step 4) rejected; seq-3 same-binding idempotency; cross-binding fork fail-closed; consumes-nothing assertion; NON-REAL hard stop | `.1R.10` |
| `runtime_authority.py` | `validate_approval`, `ValidatedAuthorityProjection`, `create_runtime_invocation_approval` | **Minimal**: expose a hook so the Gate-5 coordinator can obtain the `proof_id`/lifecycle handle for seq-3; no change to the twelve-step logic, the NON-REAL hard stop, or the projection trust predicate | 5 | **High** | regression: all `.1R.7`/`.1R.8` B1/N1/N2 cases still pass unchanged | `.1R.10` |
| `hpac_lifecycle.py` | challenge/proof lifecycle events, seq 0–3 model | **Wiring only**: a callable path for the Gate-5 coordinator to create seq-3 `PROOF_VERIFIED_AND_BOUND` with exact-byte binding + same-binding idempotency (HPAC-REQ-097). No schema/genesis change. | 5 | **High** | seq-3 created on success; byte-identical repeat idempotent; cross-binding rejected; not created on any Gate-5 failure | `.1R.10` |
| `runtime_dispatch_permission.py` | `build_runtime_dispatch_permission_broker_request`, B7 `revalidate`, `project_human_authority_binding` | **PB slice**: add/adjust the production consumer that feeds a Gate-5 projection + `authority_current_time` through the existing builder for a real (`simulation_only=False`) `runtime_dispatch` request; no change to the 14-fact shape or B7 reread | 6 | **High** | `approval_present` only via Gate-5 projection; POL-005 DENY regression; PB receives no authority when Gate 5 fails; `DENY > HUMAN_REVIEW > ALLOW` preserved | `.1R.12` |
| `permission_broker_foundation.py` | POL-005, PB evaluator, `RuntimeDispatchRequestFacts` | **None** (POL-005 & evaluator untouched); read-only consumption | 6 | N/A (unchanged) | regression: POL-005 byte-identical; DENY on `simulation_only=False` | `.1R.12` |
| `runtime_dispatch_gate9.py` **(new)** | — | Gate-9 atomic-consumption coordinator: serialization boundary, §12 in-boundary revalidation, closed 8-item record build, `...ConsumptionStore.create`, crash/replay/concurrency disposition, ephemeral `Gate9Result` | 9 | **Critical** | §17 crash-before/after; §18 concurrency one-winner; §17.3 replay matrix; §12 in-boundary drift; partial-consumption impossible; copied receipt = no authority; NON-REAL never reaches production Gate 9 | `.1R.14` |
| `runtime_invocation_authority_consumption.py` | inert Gate-9 model/store | **None anticipated** (create-only atomicity, duplicate/symlink rejection, digest self-check, durability-uncertain classification already present). Modify only if `.1R.15` verification finds a concrete gap. | 9 | **Critical** | regression: existing inert-store tests unchanged | `.1R.14` |
| `runtime_registry.py` | descriptor/config/preflight primitives | **None** (Gate-4 static preflight is out of chapter) | 4 | N/A | — | — |
| RIHAC projection consumer (`project_human_authority_binding`) | reads only `ValidatedAuthorityProjection` | **None** (already the correct single consumer, PBRD-001 §7) | 6 | High | regression | `.1R.12` |
| runtime capability checker (`runtime_introspection.py`) | frozen `Observed/observe/unavailable` constants | **None** — no capability elevation | independent | N/A | regression: constants unchanged | all |

**Contracts:** zero changes (§39). `git diff docs/contracts` MUST be empty
for every slice.

---

## 26. Contract traceability (every planned change maps to a requirement)

| Planned change | RDGO | HPAC | RIHAC / RIASC | PBRD | RPAC |
|---|---|---|---|---|---|
| Gate-5 coordinator sequences validation in §16 order | §6, §1 | HPAC-REQ-054 (via reverify) | RIHAC §16 steps 1–12 | — | — |
| Gate-5 creates lifecycle seq-3 `PROOF_VERIFIED_AND_BOUND` | §6 | HPAC-REQ-097, §40.2 seq 3 | RIHAC §16 step 12 | — | — |
| Gate-5 ephemeral non-transferable output | §6 (“never a caller-copyable seal”) | §40.2 (“ephemeral … persisted event shape alone does not recreate”) | RIHAC §16 step 12 | §7 (“not … a copyable object seal”) | — |
| Gate-5 NON-REAL hard stop inherited | §6 | fixture non-upgradability §17/§18 | RIHAC §20 | §12 | RPAC §"execution availability" |
| Gate-6 PB consumes Gate-5 projection only | §7 | — | RIHAC §16 step 12 | §4 fact 14, §7, §10 | — |
| Gate-6 preserves `DENY > HUMAN_REVIEW > ALLOW`; POL-005 DENY | §7 | — | — | §9, §12 | — |
| Gate-9 serialization boundary + §12 in-boundary revalidation | §10 | HPAC-REQ-099 | RIHAC §17 | — | — |
| Gate-9 atomic one-shot consumption (one create) | §10, §17, §18 | HPAC-REQ-098/100 | RIHAC §17, §19 | §7 (“Consumption remains the RDGO-001 gate-9 atomic transition”) | — |
| Gate-9 crash/replay/concurrency disposition | §17, §18, §19 | HPAC-REQ-100/101/102 | RIHAC §19 | §15 | — |
| Gate-9 closed 8-item record fields | §10 | HPAC-REQ-098 | — | §4, §14 | — |
| Gate-10 untouched, invariant frozen | §11 | — | RIHAC §17 | §3 | RPAC §"mock/dry … SHALL NOT change canonical execution availability" |
| No POL-005 change | §20 | — | — | §12 | — |
| No capability elevation | §14 mapping | — | RIHAC §1/§20 | §2 | RPAC §"capability … independent of PB ALLOW" |

**No undocumented coordinator semantics.**

---

## 27. Defensive validation matrix (planned for the implementation / verification phases)

Defensive terminology throughout (verify rejection / validate provenance /
confirm fail-closed behavior / stale-state case / replay case /
substitution case / coordinator boundary / atomic consumption boundary).

| # | Case | Slice(s) | Expected |
|---:|---|---|---|
| 1 | valid canonical authority reaches Gate 5 (test-path fixture) | `.1R.10`/`.1R.11` | Gate-5 revalidation battery runs; **stops at NON-REAL boundary** (`non_real_authenticated_principal_cannot_validate_production_approval`); no seq-3 event; consumes nothing |
| 2 | NON_REAL assurance rejected before production consumption | `.1R.10`–`.1R.15` | hard stop at `validate_approval:1093`; no projection, no PB `approval_present`, no Gate-9 record |
| 3 | stale principal (registry membership lost / simulated restart) | `.1R.10`/`.1R.11` | `authenticated_principal_not_verifier_issued`; verify rejection |
| 4 | revoked credential | `.1R.10`/`.1R.11` | `authenticated_principal_reverification_failed:*` |
| 5 | expired proof / challenge | `.1R.10`/`.1R.11` | reverification failure at Gate 5 |
| 6 | expired approval | `.1R.10`/`.1R.11` | `expired` |
| 7 | invocation mismatch (approval A presented for invocation B) | `.1R.10`–`.1R.15` | `subject_mismatch:invocation_id` / `authenticated_principal_invocation_mismatch` — substitution case |
| 8 | RIHAC projection mismatch / copied / mutated / hand-built lookalike | `.1R.10`/`.1R.11` | `is_trusted_validated_authority_projection` → False; `untrusted_validated_authority_projection` at the consumer |
| 9 | repeated Gate-5 validation consumes nothing | `.1R.10`/`.1R.11` | second run = byte-identical seq-3 binding; approval bytes unchanged; no consumption dir |
| 10 | Gate-9 first consumption succeeds **only** in the test-only eligible model | `.1R.14`/`.1R.15` | one valid `consumption.json`; production path proven unreachable |
| 11 | duplicate Gate-9 request rejected | `.1R.14`/`.1R.15` | `HPACDuplicateError` → deterministic `gate9_already_consumed`; replay case |
| 12 | concurrent Gate-9 requests — one winner | `.1R.14`/`.1R.15` | exactly one `create` succeeds; loser gets deterministic conflict; no split-brain |
| 13 | crash before commit consumes nothing | `.1R.14`/`.1R.15` | `resolve` → `None`; proof & approval unconsumed; stale-state case → full revalidation required |
| 14 | crash after commit reports consumed on retry | `.1R.14`/`.1R.15` | `resolve` → record; `already consumed`; no re-consume, no continue-to-effect |
| 15 | partial proof/approval consumption impossible | `.1R.14`/`.1R.15` | partial record → `...DurabilityUncertainError` → fail closed |
| 16 | copied consumption receipt provides no authority | `.1R.14`/`.1R.15` | `Gate9Result` non-serializable; planted record at foreign `proof_id` fails digest/lifecycle cross-checks |
| 17 | PB not invoked / receives no authority when upstream fails | `.1R.12`/`.1R.13` | `validated_authority is None` → `approval_present=False`; regression check |
| 18 | POL-005 hard DENY preserved | `.1R.12`–`.1R.15` | `decision == "DENY"`, `"POL-005"` in `causing_policy_ids`, `NG-025` matched; byte-identical rule |
| 19 | unavailable runtime capability prevents effect | all | `Observed/observe/unavailable` unchanged; regression check |
| 20 | Gate 10 remains first external effect; untouched | all | AST scan: no `subprocess/socket/requests/httpx/urllib/fido2/webauthn/ctap/smartcard/usb` in new coordinator modules; zero adapter invocation |
| 21 | substituted self-consistent challenge rejected at Gate 5 (Step 4) | `.1R.10`/`.1R.11` | `canonical proof` / `independently recomputed challenge state` |
| 22 | §12 in-boundary drift (revocation after Gate 5, before Gate 9) | `.1R.14`/`.1R.15` | fail closed inside the boundary; no `consumption.json` created |
| 23 | new coordinator modules non-importable test-only fixtures | `.1R.10`, `.1R.14` | AST forbidden-import check extended and passing |

---

## 28. No-go conditions (frozen — true and unchanged by this planning phase)

- Gate 5, Gate 6, Gate 9 coordinator wiring: **not begun.** No coordinator
  code, store code, or PB production-consumption code written.
- No approval / proof / presentation / challenge consumption; no
  `consumption.json` created anywhere.
- No Permission Broker policy, evaluator, or POL-005 modification.
- No Runtime Enforcement (Gate 7) or Shell Gate (Gate 8) activation; no ID
  invented for them.
- No Gate-10 dispatch, adapter invocation, subprocess, provider/network,
  credential, or hardware access.
- No runtime capability elevation — `Observed / observe / unavailable`
  unchanged; `runtime_introspection.py` constants unchanged.
- No real FIDO2, WebAuthn, CTAP, physical authenticator, device
  enumeration, attestation, enrollment; no protected UI, trusted display,
  approval/enrollment CLI, human ceremony.
- No normative contract modified (RDGO-001, RIHAC-001, RIASC-001,
  HPAC-001, PBRD-001, RPAC-001, POL-005/PBPA all byte-unchanged).
- No deterministic `FIXTURE_NON_REAL` creation or validation of production
  authority.
- No `.1R.7` / `.1R.8` test weakened.
- No Dell deployment target, third-party system, external account, or
  external credential accessed.
- The `.10`–`.15` implementation/verification phases each require separate
  explicit human authorization before they may begin; **this document
  grants none of them.**
- The `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` governance
  incident is preserved unchanged.
- Governed PCAE lifecycle only: no raw `git commit` / `git push`,
  `--no-verify`, force push, history rewrite, or hook bypass. Delegated
  workers may assist only within explicit bounded scope and may not
  autonomously commit, finalize, or push.

---

## 29. Explicit no-go / STOP conditions for the implementation phases

Each implementation slice (`.1R.10`, `.1R.12`, `.1R.14`) SHALL STOP and
record a **contract blocker** (recommending contract evolution before
implementation, never a silent reinterpretation) if its own detailed
planning reveals:

- a contradiction between RDGO-001 / RIHAC-001 / RIASC-001 / HPAC-001 /
  PBRD-001 / RPAC-001 / POL-005 and the required wiring;
- that Gate-5 sequence-3 creation cannot be done without mutating the HPAC
  lifecycle genesis or schema (it must not);
- that Gate-9 atomic consumption cannot be done without a second
  transaction mechanism (it must reuse `RuntimeInvocationAuthorityConsumptionStore`);
- that the NON-REAL hard stop would have to be weakened, relocated, or
  made conditional to wire any slice (it must not);
- that any slice requires touching POL-005, the PB evaluator, Gate 7, or
  Gate 8.

`.1R.14` SHALL additionally STOP if neither (a) the Gate-7 and Gate-8
chapters exist nor (b) an explicit human authorization has recorded the
test-path-first scope of §16.1 row 3.

---

## 30. Final report

- **Phase ID / title:** `149O.20L.7O.3W.1R.2B.1R.1.1R.9` — Gate-5/Gate-9
  Production Authority Coordinator Integration Planning.
- **Status / completeness:** COMPLETE — planning only. All 45 governing
  prompt items addressed. No production source, contract, store, PB, or
  coordinator code modified.
- **Files changed:** this planning document; `PROJECT_STATUS.md`;
  `CHANGELOG.md`; task lifecycle artifacts; `.pcae/phase-completion-*`.
  (Exact commit hashes recorded by the governed finalization sequence in
  `PROJECT_STATUS.md` / `.pcae/phase-completion-metadata.json`.)
- **Contracts / source inspected:** RDGO-001 v3.0, RIHAC-001 v2.0,
  RIASC-001 v3.0, HPAC-001 v2.0, PBRD-001 v2.0, RPAC-001 v1.0,
  POL-005/PBPA, PBPC-001 v1.2 (found N/A); `.1R.8`/`.1R.7`/`.1R.6`/
  `.1R.5.2.1`/`.3.2.2.1` docs; `runtime_authority.py`,
  `runtime_dispatch_permission.py`, `runtime_invocation_authority_consumption.py`,
  `permission_broker_foundation.py`, `hpac_verifier.py`, `hpac_lifecycle.py`,
  `hpac_foundation.py`, `runtime_introspection.py`, `runtime_invocation.py`,
  `runtime_registry.py`, `backend_invocations.py` (coordinator search).
- **Current coordinator call graph:** §5 — Gate 5 has validation logic but
  no coordinator and no lifecycle seq-3 side-effect; Gate 6 has a
  structural request path but no production consumer; Gate 9 has an inert
  store with zero importers; Gates 7 and 8 do not exist; Gate 10 has only
  mock/dry.
- **Gate-5 ownership decision:** §6 — Option C (layered); one new
  coordinator delegating to the RIHAC validator + HPAC verifier + HPAC
  lifecycle writer; no duplicated authority semantics.
- **Gate-5 revalidation matrix:** §7 — 24 rows, all re-resolved from
  authoritative stores; only lifecycle seq-3 creation (row 23) is new
  work.
- **Gate-5 output model:** §8 — ephemeral `ValidatedAuthorityProjection` +
  identity-only non-serializable `Gate5Result`; never a boolean, bearer
  token, or caller-copyable seal; consumes nothing.
- **Gate-9 ownership decision:** §10 — one new coordinator owns
  serialization/locking + in-boundary revalidation + record build +
  outcome; the existing store owns only the atomic filesystem primitive.
- **Gate-9 transaction model:** §10.2, §11, §18 — single create-only atomic
  commit at `<HPAC_PROTECTED_ROOT>/proofs/v2/<proof_id>/consumption.json`;
  reuse `RuntimeInvocationAuthorityConsumptionStore` + `hpac_foundation`
  primitives; no second transaction mechanism; per-`proof_id` lock scope.
- **Atomic proof+approval consumption model:** §11 — one record ≡ proof +
  approval + presentation + challenge consumed together; no mutable
  `consumed` field; no half-consumed state.
- **Gate-9 revalidation model:** §12 — full HPAC-REQ-099 battery inside the
  serialization boundary, immediately before compare-and-create; closes
  the Gate-5→Gate-9 stale-state window with no TOCTOU allowance.
- **Crash / retry / replay semantics:** §17 — crash-before = unconsumed;
  crash-after = consumed, retry detects "already consumed", never
  continues to effect; ambiguous = fail closed; six replay vectors all
  rejected.
- **Concurrency semantics:** §18 — at most one winner via atomic
  create-if-absent; deterministic conflict for the loser; no split-brain;
  single per-proof lock, no deadlock.
- **Gate-10 exact boundary:** §20 — the Runtime Adapter transport dispatch
  call (today only mock/dry exists); identified, not modified, not
  invoked; pre-Gate-10 zero-effect invariant frozen.
- **Deterministic NON-REAL disposition:** §21 — Gate-5 and Gate-6 wiring
  is safe before real FIDO2/UI (Option-A, hard stop unconditionally
  active); Gate-9 only under an explicit test-path-first scope; NON-REAL
  MUST NOT reach production Gate 9; hard-stop owner unchanged
  (`validate_approval:1093`, `create_runtime_invocation_approval:457`).
- **PB sequencing decision:** §22 — PB production consumption is a
  **separate slice** (`.1R.12`/`.1R.13`), after Gate-5 verification and
  before Gate-9; PBRD-001 v2.0 fully governs it, so no fresh planning
  phase; PB authenticates no humans, establishes no approval, evaluates
  policy only after trusted authority and before Runtime Enforcement.
- **POL-005 result:** §23 — hard DENY preserved; not modified; cannot be
  bypassed or weakened by any slice.
- **Runtime capability boundary:** §24 — independent and unchanged
  (`Observed / observe / unavailable`); no slice implies elevation.
- **O1–O4 adjudication:** §13.4 — all carried unchanged, none a
  prerequisite, none repaired in this chapter; O1 confirms the correct
  verification level (predicate + coordinator), O2 unchanged (protected
  root is a stronger boundary for the Gate-9 record), O3 must not
  propagate into new test names, O4 carried separately.
- **F2 / F3 / F4 / F7 adjudication:** §13.5 — F2 (HPAC-REQ-054 Step 4)
  REPAIRED and confirmed as a satisfied prerequisite (Gate-5 must route
  through `reverify_authenticated_principal`); F3/F4 carried, deferred,
  cosmetic; F7 carried unchanged, **threat model NOT broadened** —
  same-account autonomous-agent assumption, no process-isolation claim, a
  hardening chapter remains separate and non-prerequisite.
- **HPAC-REQ-054 Step-4 result:** §13.6 — mandatory before Gate 5, already
  implemented; frozen that `.1R.10` must not bypass it and `.1R.11` must
  independently re-derive the recomputation + substituted-challenge
  rejection.
- **Restart / recovery model:** §14 — process-local provenance
  (principal, projection, `Gate5Result`, `Gate9Result`) never persisted or
  reconstructed from public fields; persisted stores always re-validated
  fresh; Gate-9 committed state is durable and authoritative.
- **Coordinator state machine:** §15 — `UNVALIDATED → GATE5_VALIDATED
  (repeatable) → PB_EVALUATED → RE_EVALUATED → CONTAINMENT_ESTABLISHED →
  GATE9_CONSUMED (one-shot) → READY_FOR_GATE10`; forbidden transitions
  enumerated; Gate-5 repeatable vs Gate-9 one-shot never conflated.
- **Validation matrix:** §27 — 23 cases mapped to slices.
- **Production-file matrix:** §25 — 2 new coordinator files; minimal
  wiring in `runtime_authority.py` / `hpac_lifecycle.py` /
  `runtime_dispatch_permission.py`; POL-005, PB evaluator, inert store,
  capability constants unchanged; zero contract change.
- **Selected implementation packaging:** §16 — four trust-bearing slices,
  each with its own independent verification.
- **Exact next implementation phase ID / title:**
  **`149O.20L.7O.3W.1R.2B.1R.1.1R.10` — Gate-5 Approval-Validation
  Coordinator Integration Implementation.**
- **Exact verification phase ID / title:**
  **`149O.20L.7O.3W.1R.2B.1R.1.1R.11` — Independent Verification of Gate-5
  Approval-Validation Coordinator Integration.**
  (Further frozen: `.1R.12`/`.1R.13` PB production consumption + verification;
  `.1R.14`/`.1R.15` Gate-9 + verification, `.1R.14` blocked per §16.2.
  Gate-7 and Gate-8 chapters: no ID invented.)
- **Contract blocker:** **none.** One non-blocking sequencing constraint
  (§13.1: Gate 9 depends on Gate 6/7/8 evidence — an ordering consequence
  the contracts already state, not a contradiction) and one non-blocking
  implementation gap (§13.3: Gate-5 lifecycle seq-3 creation, folded into
  `.1R.10` as a prerequisite).
- **Runtime state:** remains **`not_implemented / Observed / observe /
  unavailable`.**
- **`.3` governance incident:** remains **UNAUTHORIZED**, preserved
  unchanged.
- **Commits / pushed status / `origin/main..HEAD`:** recorded by the
  governed finalization sequence; `origin/main..HEAD = 0` after the
  governed push.

---

## 31. Stop condition

This phase completes only
`149O.20L.7O.3W.1R.2B.1R.1.1R.9`. The canonical planning report above is
returned for human review. No coordinator implementation is begun. No PB
production permission is integrated. No real FIDO2 / UI is implemented. No
execution is enabled.
