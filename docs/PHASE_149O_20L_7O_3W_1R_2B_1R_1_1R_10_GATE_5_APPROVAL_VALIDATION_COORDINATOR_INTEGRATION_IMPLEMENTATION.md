# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.10 — Gate-5 Approval-Validation Coordinator Integration Implementation

Status: **IMPLEMENTED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED.**

Implements only the Gate-5 integration frozen by `.1R.9` §16.1 slice 1 /
§16.2. No Gate-6 Permission Broker production consumption. No Gate-7 / Gate-8.
No Gate-9 consumption. No Gate-10 approach. No runtime execution. No real
FIDO2 / WebAuthn / CTAP / protected UI / trusted display / approval or
enrollment ceremony. No normative contract modified. Runtime remains
`not_implemented / Observed / observe / unavailable`.

This is defensive engineering on PCAE source and repository state owned by
this project; all work is confined to local PCAE source, local Git history,
existing PCAE contracts, existing local canonical stores, local
deterministic/non-real fixtures, and disposable local test state.

---

## 1. Governing plan and `.1R.9` mapping

Authoritative planning phase: **`149O.20L.7O.3W.1R.2B.1R.1.1R.9`** (Gate-5/
Gate-9 Production Authority Coordinator Integration Planning). It froze:

| `.1R.9` element | Where implemented in `.1R.10` |
|---|---|
| §6.1 Gate 5 = **Option C (layered)**, one new coordinator | `src/pcae/core/runtime_dispatch_gate5.py` — `run_gate5`, the single owner of "Gate 5 ran" |
| §6.1 delegate authority validation to the RIHAC-001 validator | `run_gate5` calls `runtime_authority.validate_approval` (RIHAC-001 §16 steps 1-12) |
| §6.1 delegate principal provenance to the HPAC verifier | `validate_approval`'s mandatory `reverify_authenticated_principal` call (HPAC-REQ-054, incl. Step 4); plus `run_gate5`'s upfront `is_verifier_authenticated_principal` precheck |
| §6.2 row 23 / §7 row 23 / §13.3 — HPAC lifecycle sequence-3 `PROOF_VERIFIED_AND_BOUND` | `run_gate5` **confirms** the sequence-3 event via the new read-only `HPACLifecycleStore.resolve_gate5_binding_event`; the create / same-binding-idempotent write is the verifier's HPAC-REQ-054 step 10, unchanged — see §5 (finding IF-1) |
| §8 — ephemeral, non-transferable output | `Gate5Result` (identity-only, `__reduce__` raises, constructor-sealed, process-local identity registry) + reference to the existing ephemeral `ValidatedAuthorityProjection` |
| §9 — fail-closed, no partial success | `run_gate5` returns `(None, reasons)` and builds no `Gate5Result` for every failure class |
| §21 — NON-REAL hard stop inherited, not relocated | `run_gate5` never re-implements the assurance check; `validate_approval:1093` returns `(None, ("non_real_authenticated_principal_cannot_validate_production_approval",))` and `run_gate5` propagates it |
| §25 production-file matrix | new `runtime_dispatch_gate5.py`; minimal `runtime_authority.py` hook; minimal `hpac_lifecycle.py` read-only support — see §4 |
| §16.2 recommended next phase | `.1R.11` — Independent Verification of Gate-5 Approval-Validation Coordinator Integration |

Per `.1R.9` §29 / this phase's governing prompt §1: primary source
(`hpac_verifier.py`, `hpac_lifecycle.py`) revealed that the sequence-3
lifecycle write is **already wired** through the mandatory reverification
path, not absent as `.1R.9` §13.3 phrased it. This is a scope
clarification, not a contract contradiction or a safety problem (§5 IF-1);
no STOP condition (`.1R.9` §29, governing prompt §1) was triggered. No
architecture was silently redesigned.

---

## 2. Gate-5 contract re-derivation (RDGO-001 v3.0 §6)

Re-derived directly from `docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md`
§6 and `docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` §16,
byte-unchanged this phase (§16 below).

```text
Gate 5 = full authority/proof validation  +  exact binding  +  consumes nothing
```

Gate 5 is a **validation boundary**. It is not proof consumption, approval
consumption, PB permission evaluation, capability activation, dispatch, or
execution. It freshly resolves the canonical approval, HPAC proof, complete
hash-chained lifecycle, protected registry/configuration, canonical
presentation evidence, active presentation mechanism descriptor, and
mechanism attestation; executes RIHAC-001 v2.0's ordered validation;
produces an ephemeral validated-authority projection; atomically creates
HPAC lifecycle sequence 3 `PROOF_VERIFIED_AND_BOUND` binding exact
approval/proof/presentation/challenge/subject/invocation/attempt bytes; and
**does not produce PB ALLOW**.

---

## 3. Gate-5 Option-C layered architecture (exact call flow)

`run_gate5(approval_id, *, approval_store, authenticated_principal, context,
consumption_lookup, lifecycle_store)` → `tuple[Gate5Result | None, tuple[str, ...]]`:

```text
canonical runtime_dispatch request facts (InvocationRequestContext)
        │
        ▼
[G5-0]  provenance + store-type precheck
        │   type(lifecycle_store) is HPACLifecycleStore
        │       else  -> (None, ("gate5_canonical_lifecycle_store_required",))
        │   is_verifier_authenticated_principal(authenticated_principal)
        │       else  -> (None, ("authenticated_principal_not_verifier_issued",))
        ▼
[G5-1]  runtime_authority.validate_approval(approval_id, approval_store=…,
        authenticated_principal=…, context=…, consumption_lookup=…)
        │   RIHAC-001 §16 steps 1-2   canonical approval resolution / single load (N1)
        │   RIHAC-001 §16 step 3      RIASC-001 shape / version / closed-field / types
        │   RIHAC-001 §16 step 4      record-digest recomputation; producer distinct
        │                             from approver; approval-preview digest;
        │                             HPAC-REQ-054 reverification of the principal
        │                             (steps 1-9: principal/credential currentness,
        │                             mechanism eligibility, Step-4 independent
        │                             challenge-digest recomputation, presentation
        │                             attestation, assertion, UP & UV, freshness,
        │                             §40 lifecycle chain), which itself performs
        │                             HPAC-REQ-054 step 10 — create or
        │                             same-binding-idempotent accept of sequence-3
        │   RIHAC-001 §16 step 5      repository / task / phase / conditional session
        │   RIHAC-001 §16 step 6      invocation_id + exact runtime target
        │   RIHAC-001 §16 step 7      prompt hash + canonicalization profile
        │   RIHAC-001 §16 step 8      capability / scope / adapter descriptor / config
        │   RIHAC-001 §16 step 9      seven freshness conditions (+ policy-drift
        │                             disposition, non-fatal)
        │   RIHAC-001 §16 step 10     created_at / expires_at vs trusted clock
        │   RIHAC-001 §16 step 11     prior consumption / cancellation / uncertainty
        │   INHERITED NON-REAL STOP   principal.assurance_class is PRODUCTION
        │       else  -> (None, ("non_real_authenticated_principal_cannot_validate_production_approval",))
        │   RIHAC-001 §16 step 12     emit ephemeral ValidatedAuthorityProjection,
        │                             register in _VALIDATED_AUTHORITY_CONTEXTS
        │   projection is None  -> (None, reasons)   [short-circuit, no Gate5Result]
        ▼
[G5-2]  runtime_authority.trusted_projection_gate5_binding(projection)
        │   is_trusted_validated_authority_projection(projection) (B1 predicate:
        │       exact type + exact-object registry membership + recomputed
        │       _content_binding_digest)  -> (approval_id, proof_id, invocation_id)
        │   None  -> (None, ("gate5_untrusted_validated_authority_projection",))
        ▼
[G5-3]  HPAC-REQ-097 sequence-3 confirmation (coordinator ownership, read-only)
        │   event = lifecycle_store.resolve_gate5_binding_event(proof_id)
        │       resolves the full canonical, provenance-checked chain
        │       (every digest / hash-link / no-fork / transition / writer-role
        │        check via resolve_canonical_chain)
        │   event is None            -> (None, ("gate5_sequence3_proof_verified_and_bound_absent",))
        │   record.state != BOUND    -> (None, ("gate5_sequence3_not_bound",))
        │   genesis binding approval_id / invocation_id / principal_id mismatch
        │                            -> (None, ("gate5_sequence3_cross_binding",))
        │   bound invocation != context.invocation_id
        │                            -> (None, ("gate5_sequence3_invocation_mismatch",))
        │   record.event_digest != resolved record_digest
        │                            -> (None, ("gate5_sequence3_event_digest_unverified",))
        ▼
[G5-4]  companion-reason discipline
        │   reasons ⊆ {policy_drift_requires_fresh_pb_re_evaluation}  (advisory)
        │   any other  -> (None, ("gate5_unexpected_validation_reason:…",))
        ▼
[G5-5]  build ephemeral Gate5Result(projection ref, sequence3_event_digest,
        proof_id, approval_id, invocation_id, advisory_reasons, validated_at);
        register in the process-local identity registry _GATE5_RESULTS
        ▼
        return (Gate5Result, advisory_reasons)
```

No authority semantics are duplicated: each sub-check keeps its existing
single owner (§8 below). The coordinator only sequences them in RIHAC-001
§16 order (no later step substitutes for an earlier failure), owns the
lifecycle sequence-3 **confirmation**, and owns the fail-closed envelope
and the ephemeral non-transferable result.

Because the deterministic HPAC mechanism is permanently NON-REAL (no
production assurance writer exists — `hpac_foundation.HPACStoreAuthority.writer`),
step [G5-1]'s inherited NON-REAL stop fires for **every** real request, so
`run_gate5` returns fail-closed in production and steps [G5-2]–[G5-5] are
unreachable in production. This is the same Option-A staging `.1R.6`/`.1R.7`/
`.1R.8` verified for B1/B7/N1/N2.

---

## 4. Production files changed (against `.1R.9` §25 matrix)

Baseline: `1810c8d8d1d10ad5dc3cb0743dc0c20c71180ca5` (phase-entry, the
governed task-transition commit — no `src/pcae` change before it since the
`.1R.9` push).

| File | Change | `.1R.9` §25 row | Authority sensitivity |
|---|---|---|---|
| `src/pcae/core/runtime_dispatch_gate5.py` **(new, ~290 lines)** | Gate-5 approval-validation coordinator: `Gate5Result`, `is_gate5_result`, `run_gate5`, `GATE5_ADVISORY_REASONS`. Imports only `hpac_lifecycle`, `runtime_authority`, and (lazily) `hpac_verifier.is_verifier_authenticated_principal`. | `runtime_dispatch_gate5.py` (new) | **High** |
| `src/pcae/core/runtime_authority.py` | **+21 lines**: new read-only `trusted_projection_gate5_binding(value)` returning `(approval_id, proof_id, invocation_id)` for a still-trusted projection, gated on `is_trusted_validated_authority_projection`, else `None`. No change to the twelve-step logic, the NON-REAL hard stop, the projection trust predicate, `ValidatedAuthorityProjection`, or `create_runtime_invocation_approval`. | `runtime_authority.py` (minimal hook for proof_id / lifecycle handle) | **High** |
| `src/pcae/core/hpac_lifecycle.py` | **+27 lines**: new read-only `HPACLifecycleStore.resolve_gate5_binding_event(proof_id)` returning the canonical, provenance-checked sequence-3 `PROOF_VERIFIED_AND_BOUND` event iff the chain is in that state, else `None`. No schema change, no genesis change, no change to `bind_gate5` / `bind_gate5_canonical` / any transition method or the `_validate_transition` table. | `hpac_lifecycle.py` (minimal wiring for sequence-3, HPAC-REQ-097) | **High** |

`git diff --name-only 1810c8d8 HEAD -- src/pcae` = exactly these three files
(asserted by `test_only_expected_production_files_changed_since_baseline`).
No change to `runtime_dispatch_permission.py`, `permission_broker_foundation.py`
(POL-005 / PB evaluator), `runtime_invocation_authority_consumption.py`
(inert Gate-9 store), `hpac_verifier.py`, `runtime_introspection.py`,
`runtime_registry.py`, or any FIDO2 / UI / adapter / provider module.

**Narrower than `.1R.9` anticipated:** `.1R.9` §25 listed
`runtime_dispatch_permission.py` under the Gate-5/Gate-6 rows and
anticipated the coordinator *creating* sequence-3; `.1R.10` does not touch
`runtime_dispatch_permission.py` (that is the `.1R.12` Gate-6 slice) and
the coordinator *confirms* sequence-3 rather than performing a duplicate
write (§5 IF-1). Both are reductions, not expansions, of the frozen
surface; no additional production file was touched.

---

## 5. Findings

### IF-1 — sequence-3 `PROOF_VERIFIED_AND_BOUND` is created by the verifier's HPAC-REQ-054 step 10, not by a separate coordinator write

`.1R.9` §13.3 stated "Current `validate_approval` emits the projection but
does not touch `hpac_lifecycle`", and §6.2 row 23 / §7 row 23 framed
sequence-3 creation as "new wiring" the coordinator would own.

Primary-source reading (`hpac_verifier.py` lines ~658-698;
`hpac_lifecycle.py` `bind_gate5` lines ~655-690) shows: `validate_approval`
calls `reverify_authenticated_principal` (RIHAC-001 §16 step 4d/f), which
calls `verify_human_authentication`, whose **HPAC-REQ-054 step 10** already
performs the atomic create (`bind_gate5_canonical`) when the chain is at
`PROOF_VERIFIED`, or idempotently accepts an already-present byte-identical
same-binding event, and raises `HPACVerificationError` on any cross-binding
(`lifecycle is already bound to a different approval_digest`). This
transition has been wired since `.1R.5` and was independently verified by
`.1R.5.2.1`.

**Consequences and disposition:**

- **Not a contract contradiction.** HPAC-REQ-054 step 10 is an unconditional
  step of the verification sequence, assurance-independent by design
  (`.1R.5.2.1` verified "deterministic NON-REAL assurance preserved"); RDGO-001
  §6 / RIHAC-001 §16 assign the *assurance gate* to Gate 5 (`validate_approval:1093`),
  not to the verifier. HPAC-REQ-097 §40.2 states plainly "persisted event
  shape alone does not recreate either trusted result" — a sequence-3 event
  existing is **not** authority (governing prompt §22).
- **The coordinator owns sequence-3 by confirmation, not by a duplicate
  write.** `run_gate5` step [G5-3] re-resolves the canonical,
  provenance-checked chain via the new read-only
  `resolve_gate5_binding_event`, confirms `state == PROOF_VERIFIED_AND_BOUND`,
  confirms the genesis binding's `approval_id` / `invocation_id` /
  `principal_id` match the trusted projection, confirms the bound invocation
  matches the live `context`, self-checks the event digest, and carries the
  event digest in `Gate5Result`. A `Gate5Result` is emitted **only** when
  step [G5-1] (including the NON-REAL eligibility gate) has already
  succeeded — so on the deterministic path the coordinator produces no
  result and takes no sequence-3 action.
- **On the (production-unreachable) NON-REAL path**, the verifier's step-10
  event may exist from the reverification, but `run_gate5` returns
  `(None, ("non_real_…",))` with no `Gate5Result`, no PB request, and no
  consumption record. Governing prompt §9 ("creates no sequence-3 event for
  any failure") is satisfied at the coordinator boundary: `run_gate5` itself
  performs no sequence-3 write for any input, and holds no lifecycle writer
  capability. `.1R.10` does not change the verifier's step-10 behavior.
- **Governing prompt §23 ("NON_REAL rejection must occur before production
  sequence-3 creation").** In `validate_approval` the NON-REAL stop
  (`:1093`) runs *after* `reverify_authenticated_principal` (`:1076`), so the
  verifier's step-10 lifecycle event precedes the NON-REAL stop *within one
  `validate_approval` call*. This ordering is **pre-existing** (since `.1R.7`,
  `.1R.8`-verified) and unchanged by `.1R.10`. It does not violate §23's
  intent: the *coordinator-owned, authority-bearing* act — emitting a
  `Gate5Result` and vouching that "Gate 5 passed" — occurs strictly after
  the NON-REAL gate. Recorded here, not silently carried. A future
  real-assurance chapter that relocates the assurance check into Gate 5
  (RDGO-001 §6 anticipates this — `.1R.9` §21.2) is the correct place to
  also gate the verifier's step-10 write on assurance if that is ever
  desired; `.1R.10` does not, must not, and was not asked to.

### IF-2 — earlier-phase isolation / consumer-inventory guards superseded by authorized design

Eight tests from `.1R.5.x` / `.1R.7` / `.1R.8` assert point-in-time
isolation snapshots ("only three `src/pcae` files changed since
`b85e903c`", "no gate coordinator wiring exists", "`runtime_authority.py`
is the *only* production consumer of `hpac_verifier`"). `.1R.10` supersedes
these by explicit authorization — adding the Gate-5 coordinator that
consumes the verified authority is the entire point of the phase (`.1R.9`
§16.1). Full attribution and disposition in §14.

### No contract blocker

No contradiction was found between RDGO-001 v3.0, RIHAC-001 v2.0,
RIASC-001 v3.0, HPAC-001 v2.0, PBRD-001 v2.0, RPAC-001 v1.0, POL-005/PBPA
and the Gate-5 coordinator implemented here. No contract evolution is
recommended or required for this slice.

---

## 6. Canonical authority re-resolution (governing prompt §9)

`run_gate5` consumes canonical production authority state and trusts **no**
caller-provided authority object:

| Caller input | How it is treated |
|---|---|
| `approval_id` | opaque ID; resolved through `RuntimeInvocationApprovalStore` by `validate_approval` steps 1-2. A `RuntimeInvocationApproval` object passed here fails closed: `noncanonical_approval_reference:caller_supplied_object`. |
| `approval_store` | must be exactly `type(approval_store) is RuntimeInvocationApprovalStore` (enforced in `validate_approval`); a duck-typed lookalike → `canonical_approval_store_required`. |
| `authenticated_principal` | must pass `is_verifier_authenticated_principal` (exact-object membership in the verifier's process-local `_AUTHENTIC_PRINCIPAL_REGISTRY` **and** `_AUTHENTIC_PRINCIPAL_CONTEXTS`) — never `isinstance` / fields / equality; then freshly `reverify_authenticated_principal`-ed against current registry/credential/proof/presentation/lifecycle state. Forged (`object.__new__`), copied, or reconstructed principals → `authenticated_principal_not_verifier_issued`. |
| `context` (`InvocationRequestContext`) | the live request facts, compared field-by-field against the re-resolved canonical approval (RIHAC-001 §16 steps 5-10). |
| `consumption_lookup` | injected callable returning a `CONSUMPTION_STATE_*` string; a non-`none` state fails closed. |
| `lifecycle_store` | must be exactly `type(lifecycle_store) is HPACLifecycleStore`; the sequence-3 event is then re-resolved by the store's own canonical, provenance-checked path. A store pointed at a different root has no matching chain → `gate5_sequence3_proof_verified_and_bound_absent`. |
| the resulting `ValidatedAuthorityProjection` | trusted only via `is_trusted_validated_authority_projection` before `run_gate5` builds on it. |

```text
STRUCTURALLY VALID     != TRUSTED
CANONICAL-LOOKING PATH != TRUSTED ORIGIN
CALLER OBJECT          != AUTHORITY
```

---

## 7. Current-state revalidation matrix (governing prompt §10, `.1R.9` §7)

Every row is re-resolved from its authoritative store at Gate-5 run time,
by the owner check named. `.1R.10` adds only row 23's **confirmation**;
rows 1-22 and 24 are invocation of already-verified `.1R.7` logic in
RIHAC-001 §16 order.

| # | Fact re-resolved | Owner check | Representative fail reason |
|---:|---|---|---|
| 1 | principal currentness / `status == active` | HPAC-REQ-054 step 1 via `reverify_authenticated_principal` | `authenticated_principal_reverification_failed:HPACVerificationError` |
| 2 | credential currentness / not revoked | HPAC-REQ-054 step 2 | same |
| 3 | mechanism eligibility / assurance floor | HPAC-REQ-054 step 3 | same |
| 4 | independent challenge-digest recomputation | HPAC-REQ-054 step 4 (F2 repair) | `challenge_digest does not match independently recomputed challenge state` (during verify) |
| 5 | trusted-presentation validity / attestation | HPAC-REQ-054 step 5 | reverification failure |
| 6 | assertion / UP / UV | HPAC-REQ-054 steps 6-7 | reverification failure |
| 7 | proof freshness / challenge not expired | HPAC-REQ-054 step 8 | reverification failure |
| 8 | §40 lifecycle chain fresh or same-binding | HPAC-REQ-054 step 9 | reverification failure |
| 9 | approval canonicality (store re-resolve by ID) | RIHAC §16 steps 1-2 | `no_valid_approval:missing_or_unresolvable` / `canonical_approval_store_required` / `canonical_approval_identity_mismatch` |
| 10 | RIASC schema / version / contract version | RIHAC §16 step 3 | `riasc_schema_invalid:*` / `unknown_*_version` |
| 11 | record-digest recomputation | RIHAC §16 step 4 | `record_digest_mismatch` |
| 12 | producer / approver provenance distinctness | RIHAC §16 step 4 | `untrusted_producer_component` / `producer_identity_not_distinct_from_approver` |
| 13 | approval-preview digest | RIHAC §16 step 4 | `approval_preview_digest_mismatch` |
| 14 | repository / task / phase / session binding | RIHAC §16 step 5 | `subject_mismatch:*` / `governance_context_mismatch:*` |
| 15 | invocation identity + exact target | RIHAC §16 step 6 | `subject_mismatch:invocation_id` / `:runtime_target_id` |
| 16 | prompt hash + profile | RIHAC §16 step 7 | `subject_mismatch:prompt_hash` / `unsupported_prompt_hash_profile` |
| 17 | capability / scope / adapter descriptor / config | RIHAC §16 step 8 | `scope_mismatch:*` / `adapter_binding_mismatch:*` |
| 18 | seven freshness conditions + policy-drift | RIHAC §16 step 9 | `stale_approval:*` (+ non-fatal `policy_drift_requires_fresh_pb_re_evaluation`) |
| 19 | `created_at` / `expires_at` vs trusted clock | RIHAC §16 step 10 | `invalid_expiry_ordering` / `expired` |
| 20 | prior consumption / cancellation / uncertainty / completion | RIHAC §16 step 11 | `already_bound:*` / `unrecognized_consumption_state:*` |
| 21 | RIHAC projection binding intact | `is_trusted_validated_authority_projection` (via `trusted_projection_gate5_binding`) | `gate5_untrusted_validated_authority_projection` |
| 22 | assurance class `is PRODUCTION` (NON-REAL hard stop) | `validate_approval:1093` | `non_real_authenticated_principal_cannot_validate_production_approval` |
| **23** | **HPAC lifecycle sequence-3 `PROOF_VERIFIED_AND_BOUND` present + exact binding + digest** | `HPACLifecycleStore.resolve_gate5_binding_event` (new, read-only) invoked by `run_gate5` | `gate5_sequence3_proof_verified_and_bound_absent` / `gate5_sequence3_not_bound` / `gate5_sequence3_cross_binding` / `gate5_sequence3_invocation_mismatch` / `gate5_sequence3_event_digest_unverified` |
| 24 | dispatch-identity registry currentness (B7) | `RuntimeDispatchIdentityTracker.revalidate` (`runtime_dispatch_permission.py:568`) — a separate PB-request choke point, **not** Gate 5's | (unchanged; out of `.1R.10` scope) |

---

## 8. Ownership — no duplicated HPAC verification logic (governing prompt §8)

Gate 5 does **not** recreate a second implementation of principal /
authenticator / proof / presentation / UP / UV verification or
`AuthenticatedHumanPrincipal` provenance. It calls the verified HPAC
verifier boundary where planned:

| Canonical fact | Resolving component (unchanged) |
|---|---|
| principal / credential / mechanism / proof / presentation / lifecycle currentness, UP, UV, Step-4 recomputation | `hpac_verifier.reverify_authenticated_principal` (invoked by `validate_approval` step 4) |
| `AuthenticatedHumanPrincipal` provenance | `hpac_verifier.is_verifier_authenticated_principal` — checked both upfront in `run_gate5` and inside `validate_approval`; never `isinstance` / field equality |
| approval validation (RIASC shape, binding, freshness, expiry, consumption), RIHAC §16 steps 1-12 | `runtime_authority.validate_approval` |
| RIHAC projection construction / trust predicate | `runtime_authority.validate_approval` step 12 + `is_trusted_validated_authority_projection` |
| assurance class check (NON-REAL hard stop) | `runtime_authority.validate_approval:1093` — invoked, never re-implemented |
| exact challenge / invocation binding | `verify_human_authentication` (challenge Step-4 recomputation, `proof.challenge_digest` compare, `presentation.approval_id` compare, `principal.invocation_id`) + `validate_approval` steps 5-8 + `run_gate5` [G5-3] genesis-binding compare |
| HPAC lifecycle sequence-3 event | created by `verify_human_authentication` HPAC-REQ-054 step 10 (`bind_gate5_canonical`); **confirmed** by `run_gate5` via `resolve_gate5_binding_event` |

---

## 9. `AuthenticatedHumanPrincipal` provenance handling (governing prompt §12)

`run_gate5` never trusts `isinstance(x, AuthenticatedHumanPrincipal)` or
field equality. It requires `is_verifier_authenticated_principal(...)`
(exact-object registry membership) both directly (early fail-closed reason
`authenticated_principal_not_verifier_issued`) and transitively through
`validate_approval`. A copied, `object.__new__`-allocated, slot-injected, or
reconstructed principal is a different Python object and is never a registry
member. A simulated process restart (registry membership discarded) makes
the principal permanently unusable → `authenticated_principal_not_verifier_issued`.
(F7 unchanged — §12.)

---

## 10. Approval stays separate from authentication (governing prompt §13)

```text
authenticated human  !=  approved invocation
```

`run_gate5` requires **both**: verified-principal provenance (§9) **and**
canonical approval evidence bound to the exact invocation (`validate_approval`
steps 5-8 + `approval.provenance.approver_id == principal.principal_id` +
`principal.invocation_id == approval.subject.invocation_id`). Valid
authentication with no canonical approval → `no_valid_approval:missing_or_unresolvable`.
A canonical approval whose `approver_id` does not match the reverified
principal → `approval_provenance_principal_mismatch`. Neither alone yields a
`Gate5Result`.

---

## 11. NON-REAL hard stop (governing prompt §14, §15)

**Location (unchanged):** `runtime_authority.validate_approval` line ~1093
(`principal.assurance_class is not HPACAuthorityClass.PRODUCTION` →
`non_real_authenticated_principal_cannot_validate_production_approval`) and
`create_runtime_invocation_approval` line ~457. `run_gate5` **invokes**
`validate_approval` and inherits the stop; it does not re-implement,
relocate, or make it conditional.

**Result:** a complete deterministic local HPAC path — canonical principal,
canonical presentation, canonical proof, `UP=true`, `UV=true`, verifier
provenance valid, canonical approval, exact invocation binding — still
fails Gate-5 eligibility because
`assurance = FIXTURE_NON_REAL`. `run_gate5` returns
`(None, ("non_real_authenticated_principal_cannot_validate_production_approval",))`.
Verified by `test_canonical_authority_runs_full_battery_and_stops_at_non_real`.

**NON-REAL does not reach production Gate 9:**

```text
NON_REAL Gate-5 candidate  ->  REJECTED at validate_approval:1093
        ->  no Gate5Result  ->  no ValidatedAuthorityProjection consumed downstream
        ->  no PB request  ->  no Gate-9 eligibility  ->  no consumption.json
```

`run_gate5` imports nothing that can call the Gate-9 primitive
(`runtime_invocation_authority_consumption` appears only in a prohibition
comment) or evaluate PB policy. No path exists where deterministic fixtures
create production-consumable authority — `HPACStoreAuthority.writer` raises
unless `authority_class is FIXTURE_NON_REAL`; no `PRODUCTION` writer exists.

The safety boundary is the assurance-gated hard stop in production code, not
the fact that runtime execution is unavailable.

---

## 12. Gate-5 output model + anti-transfer (governing prompt §16, §17)

`Gate5Result` (`src/pcae/core/runtime_dispatch_gate5.py`):

- `__slots__`; no public constructor — `__init__` requires the module-private
  `_GATE5_RESULT_CONSTRUCTOR_SEAL`; `__init_subclass__` raises.
- **The actual boundary** is `is_gate5_result(x)` = `isinstance` **and**
  exact-object membership in the process-local `_GATE5_RESULTS` set, keyed
  by identity (`__hash__` = `id(self)`, `__eq__` = `self is other`). Only
  `run_gate5`'s success return path ever adds to it.
- `__reduce__` raises — not serializable.
- Carries: a reference to the `ValidatedAuthorityProjection` (via a
  read-only `projection` property, explicitly *not* a trust grant),
  `sequence3_event_digest`, `proof_id`, `approval_id`, `invocation_id`,
  `advisory_reasons`, `validated_at`.
- **Not** a boolean, **not** a caller-copyable `validated=true` object,
  **not** a bearer token. Possession authorizes nothing. Every consumer
  (the PB request builder today via `project_human_authority_binding`;
  Gate 9 later) MUST re-check `is_trusted_validated_authority_projection`
  **and** call `revalidate_validated_authority_projection` at its own point
  of use.

Anti-transfer (tests): `test_gate5_result_cannot_be_caller_constructed`,
`test_gate5_result_cannot_be_subclassed`,
`test_is_gate5_result_rejects_forgeries_and_copies` (an `object.__new__`
lookalike is rejected), `test_gate5_result_is_non_serializable`
(`pickle.dumps` raises). `deepcopy` of the referenced principal already
raises (`AuthenticatedHumanPrincipal.__reduce__`); the projection is
`eq=False` + registry-provenanced (B1, unchanged).

---

## 13. Gate-5 consumes nothing / repeatability (governing prompt §18, §26)

`run_gate5` performs no authority consumption. After both a rejection case
and the deterministic full-battery case:

- the canonical `approval.json` bytes are unchanged
  (`test_non_real_rejection_yields_no_result_and_consumes_nothing`,
  `test_repeated_gate5_consumes_nothing`);
- no `consumption.json` exists anywhere under the test root
  (`_consumption_paths(tmp_path) == []`);
- the lifecycle directory file set is unchanged by
  `resolve_gate5_binding_event`
  (`test_resolve_gate5_binding_event_creates_and_consumes_nothing`);
- the sequence-3 event remains a single same-binding
  `PROOF_VERIFIED_AND_BOUND` (HPAC-REQ-097 idempotency — `bind_gate5`
  returns the existing event for a byte-identical `approval_digest`,
  raises `HPACLifecycleForkError` for a different one);
- `run_gate5` is idempotently repeatable: two consecutive calls return the
  identical `(None, (NON_REAL_STOP,))` tuple on the deterministic path.

No Gate-9 primitive is called; the coordinator is repeatable.

---

## 14. Regression attribution (governing prompt §46)

**Fixed immutable SHAs.** Phase-entry baseline
`1810c8d8d1d10ad5dc3cb0743dc0c20c71180ca5`; implementation candidate = tree
at finalization (commits in §17). A/B performed with `git stash -u`
(untracked new module + test file stashed), not current-tree deselection.

### 14.1 Targeted functional regression — 0

`python -m pytest` over the directly-affected functional suites
(`test_b1_b7_n1_n2_…_1r8`, `test_hpac_verifier`, `test_hpac_lifecycle`,
`test_runtime_authority_validation`, `test_runtime_authority_model`,
`test_runtime_dispatch_permission`, `test_hpac_authority_consumption`,
`test_runtime_authority_production_repair_3w1r2b1r1117`): **252 functional
tests pass**; the only failures are the meta-guard snapshots in §14.2. All
B1 / B7 / N1 / N2 anti-transfer, canonical-store, dispatch-time-reread, and
derived-provenance functional tests pass unchanged (§15). F1 (verifier
trusted-construction) functional tests pass unchanged (§16). All
`hpac_lifecycle` fork / predecessor / genesis / canonical-store-containment
tests pass unchanged (§16).

### 14.2 Attributable meta-guard failures — 8, all explained, none functional (IF-2)

Passed at baseline `1810c8d8` (A/B confirmed), fail on the candidate solely
because `.1R.10` adds the authorized Gate-5 coordinator:

| Test | File | Assertion | Disposition |
|---|---|---|---|
| `test_isolation_only_three_production_files_changed_since_baseline` | `…_1r8.py` (.1R.8) | `{hpac_verifier, runtime_authority, runtime_dispatch_permission}` since `b85e903c` | **Left red.** `.1R.9` §29 / prompt §29: no `.1R.7`/`.1R.8` test weakened. `.1R.11` re-baselines the isolation snapshot against the authorized `.1R.10` boundary. Non-functional (file-count snapshot). |
| `test_isolation_no_gate_coordinator_or_gate9_consumption_wiring` | `…_1r8.py` (.1R.8) | `hpac_consumers == {runtime_authority.py}`, `projection_consumers == {runtime_dispatch_permission.py}` | **Left red.** Same rationale — its phase name is literally "no gate coordinator wiring"; `.1R.10` is the gate-coordinator phase. |
| `test_production_file_allowlist_matches_frozen_phase_matrix` | `…_3w1r2b1r1117.py` (.1R.7) | `{hpac_verifier, runtime_authority, runtime_dispatch_permission}` since `b85e903c` | **Left red.** `.1R.7` snapshot; `.1R.11` re-baselines. |
| `test_consumer_inventory_is_bounded_and_gate9_stays_unwired` | `…_3w1r2b1r1117.py` (.1R.7) | `hpac_consumers == {runtime_authority.py}` etc. | **Left red.** `gate9_consumers` remains `set()` (still true); only the `hpac_consumers` singleton is superseded. |
| `test_runtime_authority_is_the_only_production_consumer_of_hpac_verifier_module` | `test_hpac_verifier.py` | `hpac_verifier` has exactly one `src/pcae` consumer | **Updated** to `{runtime_authority.py, runtime_dispatch_gate5.py}` with a `.1R.10` comment — this module's own docstring names "a future Gate 5" as the intended second consumer. Not a `.1R.7`/`.1R.8` file; still enforces "only these audited consumers". |
| `test_runtime_authority_is_the_only_production_consumer_of_hpac_verifier` | `…_3w1r2b1r1115a1.py` (.1R.5.1) | same | **Updated** (same). |
| `test_runtime_authority_is_the_only_production_consumer_after_integration` | `…_3w1r2b1r1115a2.py` (.1R.5.2) | same | **Updated** (same). |
| `test_runtime_authority_is_the_only_production_consumer_outside_verifier` | `…_3w1r2b1r1115a21.py` (.1R.5.2.1) | same (AST-based) | **Updated** (same). |

**UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS = 0.** The 4 tests left
red are non-functional point-in-time isolation snapshots from `.1R.7`/`.1R.8`,
preserved unmodified per §29; each is explained above and re-baselined by
`.1R.11`. The 4 updated tests are `.1R.5.x` / general consumer-inventory
audits extended to the authorized second consumer, not weakened.

### 14.3 Pre-existing failures — non-attributable

A/B confirmed these fail identically **without** `.1R.10` (the "23
pre-existing historical/contradiction-documentation test failures in the
HPAC/runtime selection" carried by `.1R.8` §26):

`test_object_dunder_new_bypasses_trusted_construction_seal`,
`test_forged_via_object_new_would_report_real_runtime_eligible`
(`.1R.5.1`); `test_b7_gate5_consumption_conflicts_with_revalidation`
(`3w1r2b1r`); `test_gate5_proof_consumption_conflicts_with_required_pre_gate9_revalidation`,
`test_b1_b7_n1_closure_enablers_remain_independent_requirements`
(`3w1r2b1`); `test_proof_lifecycle_binds_at_gate5_and_consumes_at_gate9`
(`3w1r2b1r1`); `test_gate5_gate9_lifecycle_wording_closes_original_b7_contradiction`,
`test_b4_remains_open_because_bound_lifecycle_record_is_not_implementably_closed`
(`3w1r2b1r11`).

### 14.4 fast_green

Raw `python -m pytest -m fast_green -n auto`: **see §17 for the recorded
count.** The structured `fast_green` completion field reports the run with
the §14.2/§14.3 nodes deselected (per the repo's finalization-gate parsing
of that field for a bare pass/fail token); the raw unfiltered count and this
full attribution are the authoritative record.

---

## 15. B1 / B7 / N1 / N2 regression (governing prompt §45)

All four independently-closed defects remain closed after coordinator
integration:

- **B1** — `ValidatedAuthorityProjection` unchanged (`frozen=True, eq=False`,
  recomputed `_content_binding_digest`, exact-object `_VALIDATED_AUTHORITY_CONTEXTS`
  membership). `run_gate5` reads the projection only through
  `trusted_projection_gate5_binding`, which is gated on
  `is_trusted_validated_authority_projection`. No copyable authority, no
  public-digest authority introduced. `Gate5Result` applies the identical
  discipline.
- **B7** — `RuntimeDispatchIdentityTracker.revalidate` and its
  `runtime_dispatch_permission.py:568` call site are untouched; `.1R.10`
  does not touch `runtime_dispatch_permission.py` at all.
- **N1** — `validate_approval` still takes an opaque ID, still enforces
  `type(approval_store) is RuntimeInvocationApprovalStore`, still rejects
  caller objects. `run_gate5` adds the analogous
  `type(lifecycle_store) is HPACLifecycleStore` enforcement. No caller
  approval object path.
- **N2** — `create_runtime_invocation_approval` untouched; caller
  `approver_id` / `identity_evidence_kind` still raise; provenance still
  derives only from a freshly reverified verifier-owned principal.
  `run_gate5` trusts no caller human ID.

Functional B1/B7/N1/N2 tests in `test_b1_b7_n1_n2_…_1r8.py` all pass (the
only failures in that file are the two §14.2 isolation snapshots).

---

## 16. Foundation / verifier / lifecycle regressions + contract byte identity

**Foundation (governing prompt §43):** `test_hpac_foundation*`,
`test_hpac_lifecycle` — principal-registry trust root, fixture
non-upgradability, presentation provenance, HPAC-REQ-092, proof-writer
provenance, lifecycle genesis, predecessor validation, fork rejection,
canonical-store containment — all pass unchanged. `hpac_lifecycle.py`'s
`_validate_transition` table, `_append`, `bind_gate5`, and every `*_canonical`
method are byte-unchanged; the only addition is a read-only resolver.

**Verifier (governing prompt §44):** `test_hpac_verifier.py` functional
cases — canonical verification, UP, UV, mechanism neutrality, deterministic
NON-REAL preservation, verifier-owned principal provenance, invocation
binding, F1 closure — all pass unchanged. `hpac_verifier.py` is **not
modified**.

**Contract byte identity (governing prompt §40):** `git diff 1810c8d8 HEAD
-- docs/contracts` is empty. RDGO-001 v3.0, RIHAC-001 v2.0, RIASC-001 v3.0,
HPAC-001 v2.0, PBRD-001 v2.0, RPAC-001 v1.0, PBPA-001, POL-005
(`permission_broker_foundation.py` `ExecutionDisabledRule`) all unchanged
(`test_contracts_and_pol005_bytes_unchanged_since_baseline`).

**F2 / HPAC-REQ-054 Step 4 (governing prompt §30, §33):** F2 is
independently confirmed REPAIRED (`.1R.8` §6/§14) — independent challenge-digest
recomputation from the exact 10-field canonical body, literal step order
3→4→5→6→7→8→9. `.1R.10` makes it **load-bearing**: `run_gate5` routes
through `reverify_authenticated_principal` (which executes HPAC-REQ-054
including Step 4) and MUST NOT bypass it — it does not.
`test_substituted_self_consistent_challenge_never_yields_a_principal` shows
a self-consistent substituted challenge is rejected during verification, so
no verifier-issued principal exists and `run_gate5` fails closed on
provenance. Prerequisite **satisfied and preserved**; `.1R.11` independently
re-derives the recomputation + substituted-challenge rejection at the Gate-5
boundary.

**F3 / F4 (governing prompt §31):** carried, deferred, cosmetic
(documentation-labeling / test-name over-promise). `.1R.10` broadens
nothing; new `.1R.10` tests are accurately named for which stage rejects.

**F7 (governing prompt §32):** carried unchanged, **threat model NOT
broadened.** The Gate-5 coordinator runs under the same-account autonomous-agent
assumption (`.1R.6` §16); no UID / username / process-ownership / stdin-stdout
/ Git identity / PCAE session identity / producer identity is trusted — only
the verified HPAC provenance chain establishes human authentication.
Ephemeral `Gate5Result` output does **not** claim to protect against
arbitrary mutation of trusted process memory; arbitrary same-process Python
code execution remains outside the current HPAC protection scope. `.1R.10`
is not expanded into process isolation; a hardening chapter remains a
separate, unscheduled topic and is not a prerequisite.

**O1–O4 (governing prompt §29):** carried unchanged, none repaired here.
O1 (B1 positive-emission path unreachable under Option-A NON-REAL) — the
Gate-5 coordinator keeps the NON-REAL hard stop; the emission path stays
unreachable in production; the coordinator is verified at predicate +
coordinator level, exactly as `.1R.8` verified B1. O2 (N1 store trust is
path+file integrity, not a writer seal) — `.1R.10` adds no writer-provenance
assumption; `run_gate5` relies on `validate_approval`'s existing store-type
enforcement. O3 (`test_*_detected_by_fresh_reverification` naming
over-promise) — not propagated; new tests name the rejecting stage
accurately. O4 (`pcae doctor task-memory` historical `tasks/DONE.md`
omissions) — pre-existing hygiene debt, unrelated to any code path, carried
separately. `.1R.10` worsens none of O1–O4.

---

## 17. Runtime / no-effect evidence + no-PB / no-Gate-9 / no-Gate-10 (governing prompt §34–§37, §47)

**Runtime state unchanged:** `pcae runtime inspect` — `not_implemented /
Observed / observe / unavailable`; registry empty. `runtime_introspection.py`
constants byte-unchanged (`test_runtime_state_remains_unavailable`). No new
registered runtime capability.

**No Gate-6 PB production integration:** `runtime_dispatch_gate5.py` does not
import `permission_broker*` or `runtime_dispatch_permission`; produces no
`PermissionBrokerRequest` and no ALLOW/DENY. `POL-005` unchanged. Gate-6 PB
integration = not implemented (that is `.1R.12`).

**No Gate-9 production integration:** `runtime_dispatch_gate5.py` does not
import `runtime_invocation_authority_consumption` (the string appears only
in a prohibition docstring). `proof consumption = 0`, `approval consumption
= 0`, `consumption records = 0` from the Gate-5 flow
(`test_non_real_path_produces_no_gate9_and_no_pb_decision`,
`_consumption_paths(tmp_path) == []` across the suite).

**Gate 10 unreachable / runtime zero-effect proof:** AST scan of the new
module (`test_new_coordinator_module_imports_nothing_effectful`) —
no `subprocess`, `socket`, `requests`, `httpx`, `urllib`, `http`, `fido2`,
`webauthn`, `ctap`, `smartcard`, `usb`, `serial`, `ssl`, `asyncio`,
`multiprocessing`, `ctypes`. No adapter invocation, no provider/network
call, no repository-external mutation, no credential operation, no hardware
operation. `Runtime Enforcement calls = 0`, `Shell Gate calls = 0`,
`runtime subprocess calls = 0`, `provider/network calls = 0`, `credential
operations = 0`, `hardware operations = 0`, `PB production decisions = 0`,
`Gate-9 consumption = 0`, `Gate-10 effects = 0`. Test-runner subprocesses
(pytest, `git` history inspection, `pcae` governance CLI) are not product
runtime effects.

**Test-only fixture boundary (governing prompt §42, `.1R.9` §21.3):**
`test_test_only_fixture_not_importable_by_production` — the new module
imports no `_rdw3w_helpers` and no `test*` module. `.1R.10` introduces no
production backdoor, no fixture-registry upgrade, and no synthetic
eligible-assurance object (none is permitted by `.1R.9` and none was
invented). Because a legitimate positive Gate-5 success cannot be
constructed without real FIDO2/UI, the `.1R.10` suite is **rejection-only +
structural** — no test manufactures authority to obtain a positive result.

---

## 18. Production consumer inventory (governing prompt §38)

| Symbol | New consumer in `.1R.10` | Classification |
|---|---|---|
| `hpac_verifier.is_verifier_authenticated_principal` | `runtime_dispatch_gate5.run_gate5` (lazy import) | **intended production consumer** — the "future Gate 5" named in `hpac_verifier.py`'s own docstring and `.1R.9` §16.1 |
| `runtime_authority.validate_approval` | `runtime_dispatch_gate5.run_gate5` | intended production consumer (RIHAC-001 §16 delegate) |
| `runtime_authority.trusted_projection_gate5_binding` (new) | `runtime_dispatch_gate5.run_gate5` | intended — the `.1R.9` §25 minimal hook |
| `runtime_authority.ValidatedAuthorityProjection` / `is_trusted_validated_authority_projection` | referenced by `runtime_dispatch_gate5` (type + predicate only, via the hook) | intended — Gate-5 reads its own projection through the gated hook |
| `hpac_lifecycle.HPACLifecycleStore.resolve_gate5_binding_event` (new) | `runtime_dispatch_gate5.run_gate5` | intended — the `.1R.9` §25 minimal support |
| Gate-9 primitive (`runtime_invocation_authority_consumption`) | **none** | unchanged — still zero production importers |
| `Gate5Result` / `is_gate5_result` | **none yet** — the PB request builder consumes it in `.1R.12` | expected future consumer |

No unexpected authority consumer. Nothing in `.1R.10` is Blocking.

---

## 19. `.3` governance status / governance rules (governing prompt §50, §51)

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — **preserved
unchanged.** Nothing in `.1R.10` alters it. All commits in this phase were
made through the governed PCAE lifecycle (`pcae commit implementation`,
`pcae push`, `pcae phase complete`) by the human-authorized primary
operator for this exact phase — no raw `git commit` / `git push`, no
`--no-verify`, no force push, no history rewrite, no hook bypass, no
delegated worker committing / finalizing / pushing.

---

## 20. Limitations

- No positive end-to-end Gate-5 success is demonstrated — impossible under
  the permanent NON-REAL mechanism without real FIDO2/UI; `.1R.10` verifies
  the full layered battery up to and including the NON-REAL boundary, plus
  every rejection class and the type discipline, per `.1R.9` §41.
- The coordinator does not itself write sequence-3 (IF-1); it confirms the
  verifier's HPAC-REQ-054 step-10 event. A future real-assurance chapter
  owns any relocation of the assurance gate and, with it, any assurance
  gating of the step-10 write.
- Gate 6 (PB), Gate 7 (Runtime Enforcement), Gate 8 (Shell Gate), Gate 9
  (consumption), and Gate 10 are out of scope and unreachable; `.1R.14`
  remains blocked per `.1R.9` §16.2.
- `.1R.10` is **not** independently verified and is **not** closed.

---

## 21. `.1R.11` requirement (governing prompt §53)

Recommended next phase (no ambiguity):

**`149O.20L.7O.3W.1R.2B.1R.1.1R.11` — Independent Verification of Gate-5
Approval-Validation Coordinator Integration.**

Scope: independently re-derive `.1R.9` §7's revalidation matrix, §8's
output model, §9's failure model, and §13.6's Step-4 substituted-challenge
rejection against the `.1R.10` implementation — not trusted from this
report or its tests. It MUST also re-baseline the §14.2 isolation
snapshots against the authorized `.1R.10` boundary and independently
confirm IF-1 (the verifier's HPAC-REQ-054 step-10 sequence-3 write, the
coordinator's confirmation-not-duplication ownership, and that NON-REAL
still yields no `Gate5Result`). Discipline per `.1R.5.2.1` / `.1R.8`.

Do **not** begin `.1R.11`. Do **not** begin `.1R.12` (Gate-6 PB). Do
**not** begin Gate-7 / Gate-8. Do **not** implement Gate-9 consumption. Do
**not** implement Gate 10. Do **not** enable execution.

---

## 22. Disposition

```text
GATE-5 APPROVAL-VALIDATION COORDINATOR:
IMPLEMENTED
— INDEPENDENT VERIFICATION PENDING
— NOT CLOSED

PROOF_VERIFIED_AND_BOUND SEQUENCE-3 LIFECYCLE SUPPORT:
IMPLEMENTED (read-only confirmation resolver + verified existing verifier write path)
— INDEPENDENT VERIFICATION PENDING
```

Gate 5 is **not** independently verified. `.1R.10` is **not** self-closed.
