# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.8 — Independent Verification of B1/B7/N1/N2 Production Authority Repair Implementation

Status: **INDEPENDENTLY VERIFIED — B1/B7/N1/N2 PRODUCTION AUTHORITY REPAIR
COMPLETE (with non-blocking observations).** Real FIDO2, real protected UI,
Gate-5/Gate-9 coordinator wiring, Permission Broker production integration,
runtime capability, and execution all remain unbuilt and unavailable. This
verdict is confined to the production authority *implementation boundary*.

RE-DERIVE, DO NOT TRUST. Every property below was re-derived from primary
contracts and current production source and re-exercised with an
independently authored adversarial suite. Nothing was accepted merely
because it appears in the `.1R.7` report, `.1R.7` documentation, `.1R.7`
tests, an aggregate count, a type name, a digest, or a canonical-looking
object.

---

## 1. Phase identity and verification-entry state

- Phase ID: `149O.20L.7O.3W.1R.2B.1R.1.1R.8`.
- Title: Independent Verification of B1/B7/N1/N2 Production Authority Repair
  Implementation.
- Verification-entry commit: `96f7d3ec` (`.1R.7: disambiguate idle lifecycle
  identity`), the tip of `main` at phase start.
- Entry Git state: clean; `main...origin/main`; `origin/main..HEAD = 0`.
- Latest completed phase at entry: `149O.20L.7O.3W.1R.2B.1R.1.1R.7`
  (report completeness: complete). Confirmed independently.
- Entry runtime state: `not_implemented / Observed / observe / unavailable`;
  zero runtime plugins; zero runtime capabilities. Confirmed via
  `pcae runtime inspect` and `pcae.core.runtime_introspection` constants
  (`CURRENT_RUNTIME_STATE == "Observed"`,
  `CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"`,
  `EXECUTION_AVAILABILITY == "unavailable"`).
- `pcae health` healthy; `pcae check` passed; `pcae status coherence`
  coherent; `pcae push check` clean (`nothing_to_push`).
- `pcae doctor task-memory`: warning-only historical `tasks/DONE.md`
  omissions (pre-existing governance-record hygiene debt, unrelated to any
  code path); no current-phase error.

No active governed phase existed before startup (the entry task was the
idle placeholder awaiting explicit human authorization for `.1R.8`).

---

## 2. Exact `.1R.7` implementation range (immutable SHAs)

`.1R.7` spans `b85e903c..96f7d3ec`. Every commit was inspected individually
by content, not by subject line:

| Commit | Class | Content |
|---|---|---|
| `b85e903c` | **pre-`.1R.7` fixed baseline** | `.1R.6` push-state trust-field repair; last commit before any `.1R.7` source change. |
| `3fc26199` | **sole implementation-bearing commit** | The only commit touching `src/pcae/**`. 3 production files + test surface + doc + status. |
| `58e83b98` | lifecycle only | Close implementation task (`tasks/DONE.md`, task file). |
| `81b22e2f` | report/metadata staging only | `.pcae/phase-completion-*`, `PROJECT_STATUS.md`, task file. |
| `408f27a8` | push-state reconciliation only | `.pcae/phase-completion-metadata.json` trust fields. |
| `e324238f` | lifecycle only | Close governed finalization task. |
| `5d0ec529` | lifecycle only | Create post-completion idle placeholder. |
| `96f7d3ec` | lifecycle only | Disambiguate idle lifecycle identity. |

`git rev-parse 3fc26199^` = `b85e903c…` confirms the baseline. The `.1R.7`
report cites `3fc26199, 58e83b98, 81b22e2f`; the four later commits are
post-report finalization/idle lifecycle and carry no source or test
change. **All production and test-source change is isolated in
`3fc26199`.**

---

## 3. Primary contracts and source inspected

Read against the current tree, not derived from `.1R.7` prose:

- Contracts: RIHAC-001 v2.0, RIASC-001 v3.0, HPAC-001 v2.0, PBRD-001 v2.0,
  RDGO-001 v3.0, RPAC-001 v1.0, PBPA-001 / POL-005.
- `.1R.6` planning document (frozen Option-A repair, §5/§8/§9/§12/§13/§14,
  F1–F4/F7 and HPAC-REQ-054 Step-4 adjudications, frozen production-file
  matrix).
- `.1R.7` implementation diff and implementation document.
- `.1R.5.2.1` verifier independent verification (F1 CLOSED, F7 disclosed);
  `.1R.5.2` verifier provenance repair; `.3.2.2.1`-family HPAC foundation
  verification.
- B1/B7/N1/N2 original finding material (`.1R` / `.1R.1` independent
  verification).
- Production modules: `runtime_authority.py`, `runtime_dispatch_permission.py`,
  `runtime_invocation_approval_store.py`,
  `runtime_invocation_authority_consumption.py` (inert Gate-9),
  `hpac_verifier.py`, `hpac_foundation.py`, `hpac_lifecycle.py`,
  `approval_presentation*.py`, `human_authenticator*.py`,
  `permission_broker_foundation.py`.

Where contract or source gave the authoritative answer, `.1R.7` prose was
not used as authority.

---

## 4. Independent B1 reconstruction and current rejection evidence

### 4.1 Pre-repair defect (re-derived from fixed baseline `b85e903c`)

`git show b85e903c:src/pcae/core/runtime_authority.py` contains:

```python
_VALIDATED_AUTHORITY_SEAL = object()
...
_validator_seal: object | None = field(default=None, repr=False, compare=False)
...
return (type(value) is ValidatedAuthorityProjection
        and value._validator_seal is _VALIDATED_AUTHORITY_SEAL)
```

Trust was: "this object's `_validator_seal` field is identical to one
module-level sentinel." Because the field is `compare=False`,
`dataclasses.replace(projection, approval_id=..., record_digest=...)`
copies the sentinel verbatim onto arbitrary content. Trust was
**identity-only, not content-bound, transferable, and copyable**. No
canonical re-resolution occurred at validation. This is the same root
cause `.1R.1` found OPEN; confirmed bit-for-bit at the baseline this phase.

### 4.2 Current replacement (re-derived from current source)

- The sentinel and the `_validator_seal` field are gone from source
  (grep confirms absence).
- `ValidatedAuthorityProjection` is now `@dataclass(frozen=True, eq=False)`
  → identity hashing / identity equality.
- Trust is `is_trusted_validated_authority_projection(value)` =
  `type(value) is ValidatedAuthorityProjection`
  **and** `value in _VALIDATED_AUTHORITY_CONTEXTS` (exact-object identity
  membership in a process-local dict)
  **and** `value._content_binding_digest == value.evidence_digest()`
  (recomputed over every authority field, including
  principal/proof/mechanism/assurance/invocation).
- The registered object is the post-`replace` instance carrying the
  content-binding digest; `_VALIDATED_AUTHORITY_CONTEXTS[projection]`
  additionally stores the revalidation context (store, principal, context,
  consumption lookup).

### 4.3 B1 decisive property — copy/lookalike rejection

Independent tests (`test_b1_*`):

- A hand-built `ValidatedAuthorityProjection` reproducing every field and
  a self-consistent `evidence_digest()` but never registered by
  `validate_approval` → `is_trusted_validated_authority_projection` **False**.
- `copy.copy`, `copy.deepcopy`, and `dataclasses.replace` of a genuinely
  registered projection → **False** (new object identity, not in the
  registry).
- `object.__setattr__` field mutation on a registered projection →
  **False** (recomputed content binding no longer matches).
- `dataclasses.replace(..., invocation_id=other, _content_binding_digest="")`
  then recompute the digest → self-consistent but **False** (never
  registered).
- `runtime_dispatch_permission.project_human_authority_binding` with a
  lookalike projection → `RuntimeDispatchConstructionError:
  untrusted_validated_authority_projection`.

Rejection is because provenance/binding is absent, not because the object
is malformed.

### 4.4 B1 anti-transfer — observation O1

Under Option-A the `validate_approval` positive emission path is
**unreachable** (the deterministic mechanism is permanently `FIXTURE_NON_REAL`;
§7), so a "legitimate structurally valid production-authority projection
obtained through the intended path up to the NON-REAL boundary" cannot be
produced end-to-end today. The B1 anti-transfer property is therefore
verified at:

1. the predicate level (`is_trusted_validated_authority_projection`), using
   the same registration shape `validate_approval` would emit; and
2. the consumer level (`project_human_authority_binding` /
   `build_runtime_dispatch_permission_broker_request`), which additionally
   calls `revalidate_validated_authority_projection` and re-checks
   subject/scope and invocation binding.

This is inherent to Option-A, not a test weakness — see O1 in §26.

**B1 rejection evidence and anti-transfer evidence: PASS.**

---

## 5. Independent B7 reconstruction and canonical revalidation evidence

### 5.1 Pre-repair defect (fixed baseline)

`git show b85e903c:src/pcae/core/runtime_dispatch_permission.py` has **no**
`RuntimeDispatchIdentityTracker.revalidate` method. `RuntimeDispatchIdentity`
is a digest over `(invocation_id, attempt_id, idempotency_key)` — all
public, caller-reproducible facts.
`build_runtime_dispatch_permission_broker_request` checked the identity
seal and recomputed the digest but **never re-read** the durable
`.pcae/runtime-dispatch-identities/v1/**` registry at request-build time.

### 5.2 Current call graph (re-derived)

`build_runtime_dispatch_permission_broker_request`:

1. exact-type + registration-digest check on the identity;
2. `type(identity._identity_tracker) is not RuntimeDispatchIdentityTracker`
   → `runtime_dispatch_identity_tracker_missing`;
3. id / idempotency-key checks;
4. **`identity._identity_tracker.revalidate(identity)`** — the B7 reread:
   - `identity._identity_tracker is self` and
     `identity._registration_digest == _identity_registration_digest(identity)`;
   - `_require_directory` walks each existing component with `lstat`, no
     symlink, no creation;
   - re-reads the invocation, idempotency, and attempt records and requires
     each decoded record to `==` the exact closed expected dict
     (`identity_registry_mismatch:<dir>` otherwise);
   - `FileNotFoundError` → `identity_store_record_missing`;
5. `project_human_authority_binding(..., current_time=authority_current_time)`
   which calls `revalidate_validated_authority_projection` and raises
   `stale_validated_authority_projection` if `current_time is None` or
   revalidation fails.

### 5.3 B7 tests (independent)

- Valid registry → request builds; `approval_present == False` (no
  authority supplied).
- Delete `invocations/<id>.json` after mint → `identity_store_record_missing`
  / `identity_registry_mismatch`.
- Rewrite the invocation record content after mint →
  `identity_registry_mismatch`.
- Rebind a foreign tracker onto the frozen identity →
  `RuntimeDispatchConstructionError`.

A previously valid dispatch identity fails once current durable registry
state no longer matches. **No stale public identity remains sufficient.**

**B7 canonical revalidation evidence: PASS.**

---

## 6. Independent HPAC-REQ-054 Step-4 challenge recomputation analysis

### 6.1 Canonical construction re-derived

From HPAC/RIHAC/RIASC and `HPACLifecycleStore.open_challenge_canonical`,
the canonical challenge body is exactly the ordered field set:
`domain_separator, challenge_version, proof_schema_version, principal_id,
credential_id, approval_subject_digest, trusted_presentation_digest, nonce,
issued_at, expires_at`, digested with `hpac_foundation.canonical_digest`
(sorted-key, compact-separator, NFC JSON).

### 6.2 `.1R.7` implementation

`verify_human_authentication` now:

- requires `type(challenge) is Challenge` (exact ephemeral state, not a
  digest or a lookalike);
- builds `challenge_body` from exactly the 10 fields above and computes
  `recomputed_challenge_digest = canonical_digest(challenge_body)`;
- rejects if `recomputed_challenge_digest != challenge.challenge_digest`
  (`"independently recomputed challenge state"`);
- rejects if `challenge.challenge_digest != proof.challenge_digest`
  (`"canonical proof"`);
- rejects if challenge `principal_id / credential_id /
  approval_subject_digest / trusted_presentation_digest` disagree with the
  canonical proof binding.

Step order is literal: Step 3 mechanism eligibility → **Step 4 challenge
recomputation** → Step 5 presentation → Step 6 assertion → Step 7 UP/UV →
Step 8 chronological freshness → Step 9 lifecycle.

### 6.3 Challenge substitution results (independent)

| Case | Result |
|---|---|
| Invocation A + recomputed Challenge A | structural success **up to** the NON-REAL stop (assurance `FIXTURE_NON_REAL`) |
| Invocation A + caller-supplied Challenge B (nonce changed, digest not recomputed) | rejected: `independently recomputed` |
| Self-consistent substituted challenge (nonce changed **and** digest recomputed) | rejected: `canonical proof` |
| Invocation A verified with Invocation B's challenge | rejected |
| Changed canonical parameter (`approval_subject_digest`) → recomputed digest differs | verified: digest is a function of invocation state |

Caller-supplied challenge value is not trusted; the challenge is
independently recomputed; the copied challenge value alone cannot
establish authority. **PASS.**

---

## 7. Independent N1 reconstruction and results

### 7.1 Pre-repair (fixed baseline)

`def validate_approval(approval: RuntimeInvocationApproval | None, *, ...)`
— accepted a caller object; checked shape/constants/digest; **no**
lookup-by-ID against `RuntimeInvocationApprovalStore`.
`create_runtime_invocation_approval` is public; nothing prevented
hand-constructing `RuntimeInvocationApproval` / `ApprovalProvenance`.

### 7.2 Current call graph

`def validate_approval(approval_id: object, *, approval_store=None,
authenticated_principal=None, context, consumption_lookup)`:

- `approval_id is None` → `no_valid_approval:missing_or_unresolvable`;
- caller `RuntimeInvocationApproval` object → kept only for fail-closed
  diagnostics, then **unconditionally** `noncanonical_approval_reference:
  caller_supplied_object` before any HPAC trust or projection;
- non-`RuntimeInvocationApproval`, invalid ID shape → `noncanonical_approval_id`;
- `type(approval_store) is not RuntimeInvocationApprovalStore` →
  `canonical_approval_store_required` (exact type, no duck typing);
- `approval_store.load(approval_id)`; `None` → `no_valid_approval`;
- `approval.approval_id != approval_id` → `canonical_approval_identity_mismatch`;
- then ordered RIASC structural / binding / freshness / expiry /
  consumption checks, then HPAC provenance, then the NON-REAL stop.

### 7.3 N1 results (independent)

| Case | Result |
|---|---|
| External well-formed approval **object** | `noncanonical_approval_reference:caller_supplied_object` |
| Duck-typed lookalike store (delegates to the real store) | `canonical_approval_store_required` |
| Malformed approval ID | `noncanonical_approval_id` |
| Valid-shaped but unresolvable canonical ID | `no_valid_approval:*` |
| Canonical ID + concrete store + persisted record | resolves, reaches HPAC stage, stops at NON-REAL boundary (`non_real_authenticated_principal_cannot_validate_production_approval`) |
| Validation side-effects | canonical `approval.json` bytes unchanged; no `runtime-invocation-authority-consumption` directory created |

`validate_approval` genuinely re-reads the store (monkeypatched `load`
observed to be called once with the exact ID) and does not mutate it.

**N1 external-valid-approval rejection: PASS. Canonical approval
resolution: PASS. Validation-only (no consumption): PASS.**

### 7.4 Path-vs-writer provenance — observation O2

`RuntimeInvocationApprovalStore.load` establishes trust by: canonical
fixed path derived only from an `^ria-[0-9a-f]{32}$`-validated ID;
directory-relative `O_NOFOLLOW` opens; `S_ISREG` + `st_nlink == 1`;
duplicate-key rejection; RIASC schema shape; `data["approval_id"] ==
approval_id`. There is **no separate cryptographic writer-provenance
seal** on the persisted record. An actor with direct write access to
`.pcae/runtime-invocation-approvals/v1/**` (i.e. the documented
same-account / same-process F7 threat model) could plant a
schema-valid record that `load` would return. This is consistent with
`.1R.6` §12 ("no structural change required" to the store) and with F7;
it is **non-blocking** (O2, §26). "CANONICAL LOCATION != TRUSTED ORIGIN"
is preserved against *redirection* (symlink/hardlink/traversal) but not
against an attacker who already has write access to the canonical
directory — the same boundary B1's own precedent has.

---

## 8. Independent N2 reconstruction and results

### 8.1 Pre-repair (fixed baseline)

`create_runtime_invocation_approval(..., approver_id: str,
identity_evidence_kind: str, ...)` — both plain caller strings, validated
only for enum membership and inequality with `producer_component`. Nothing
bound `approver_id` to an authenticated principal.

### 8.2 Current

`create_runtime_invocation_approval(..., authenticated_principal=None,
approver_id=None, identity_evidence_kind=None, ...)`:

- `approver_id is not None or identity_evidence_kind is not None` →
  `TypeError("caller-supplied approver_id/identity_evidence_kind cannot
  establish human authority")`;
- `not is_verifier_authenticated_principal(authenticated_principal)` →
  `authenticated_principal_not_verifier_issued`
  (`is_verifier_authenticated_principal` = `isinstance` **and** registry
  membership **and** verification-context membership — never type/shape/
  equality);
- `reverify_authenticated_principal(...)` reruns the full ordered verifier
  against the retained canonical stores + exact `Challenge`; failure →
  `authenticated_principal_reverification_failed`;
- `principal.invocation_id != subject.invocation_id` →
  `authenticated_principal_invocation_mismatch`;
- `principal.assurance_class is not HPACAuthorityClass.PRODUCTION` →
  `non_real_authenticated_principal_cannot_create_production_approval`;
- provenance is then derived: `approver_id = principal.principal_id`,
  `approval_id = principal.approval_id`.

The same fresh verifier-owned check (`reverify_authenticated_principal`)
runs in `validate_approval`, plus
`approval.provenance.approver_id == principal.principal_id`.

### 8.3 N2 results (independent)

| Case | Result |
|---|---|
| Caller `approver_id="ceo@example.com"` + valid `identity_evidence_kind` | `TypeError: cannot establish human authority` |
| `object.__new__` slot-cloned principal shape | `is_verifier_authenticated_principal` False; `ValueError: not_verifier_issued` |
| `copy.copy` / `copy.deepcopy` / `pickle.dumps` of a real principal | `TypeError` — `AuthenticatedHumanPrincipal.__reduce__` refuses (HPAC-REQ-058); a copy-forgery cannot even be built |
| Legitimate verifier principal, wrong invocation on the approval | `authenticated_principal_invocation_mismatch` |
| **Legitimate verifier principal, matching binding** | provenance **recognized** (`is_verifier_authenticated_principal` True) **and** real authority still refused: `non_real_authenticated_principal_cannot_create_production_approval` |

**Caller human-ID gives no authority: PASS. Legitimate verifier provenance
recognized: PASS. Real production authority still NON-REAL-rejected: PASS.**

---

## 9. Deterministic NON-REAL hard-rejection result (central safety property)

Re-derived from `hpac_foundation.py`:

- `HPACStoreAuthority.production()` requires `resolve_hpac_protected_root()`
  and `_validate_production_boundary()` (root not writable by the agent,
  ancestor chain safe). On this host it fails closed (independently
  confirmed — construction/`_ensure_root` raises).
- `HPACStoreAuthority.writer(...)` raises `HPACAuthorityError("no production
  HPAC writer is implemented in this foundation phase")` unless
  `authority_class is FIXTURE_NON_REAL`. **No canonical record can be
  written with `authority_class = PRODUCTION`.**
- `_authority_class_of(*resolved)` requires all resolved records to agree;
  with no PRODUCTION writer, the only reachable value is `FIXTURE_NON_REAL`.
- Therefore `verify_human_authentication` (and
  `reverify_authenticated_principal`) can only ever yield
  `assurance_class = FIXTURE_NON_REAL`.
- Both `create_runtime_invocation_approval` and `validate_approval` check
  `principal.assurance_class is not HPACAuthorityClass.PRODUCTION` and
  reject. `source.count("HPACAuthorityClass.PRODUCTION") >= 2`; both
  reason strings present.

Independent full-strength deterministic path — canonical principal,
credential, presentation, valid deterministic attestation, canonical
proof, valid lifecycle, `UP=True`, `UV=True`, verifier provenance valid,
canonical approval, exact invocation binding, all intended checks passing
— still fails **specifically** with
`non_real_authenticated_principal_cannot_create_production_approval`.
`require_real_assurance=True` independently rejects with `FIXTURE_NON_REAL`.

### 9.1 No accidental real-authority positive path

Behavioural search across `src/pcae/**` and `tests/**`: across multiple
deterministic rig configurations, every verifier-issued, registry-passing
principal is `FIXTURE_NON_REAL` and `is_real_runtime_eligible is False`;
no path yields a real-eligible production authority object. The `.1R.7`
`test_hpac_verifier_independent_verification_*` "forged … would report
real_runtime_eligible" cases are *data-shape* observations on **non**-
verifier-authenticated forgeries (they fail
`is_verifier_authenticated_principal`), not real-authority paths.

**Deterministic NON-REAL hard rejection: PASS. Positive deterministic
real-authority paths: 0.**

---

## 10. Approval-intent separation and invocation-binding results

- Valid NON-REAL authentication + **no** persisted canonical approval →
  `validate_approval` returns `no_valid_approval:*`. Authentication alone
  never creates approval authority. **PASS.**
- `create_runtime_invocation_approval` binds `principal.invocation_id ==
  subject.invocation_id`; a mismatched invocation →
  `authenticated_principal_invocation_mismatch`. **PASS.**
- `validate_approval` binds `principal.approval_id == approval.approval_id`,
  `principal.invocation_id == approval.subject.invocation_id`,
  `approval.provenance.approver_id == principal.principal_id`, and
  `context.invocation_id` against the resolved subject
  (`subject_mismatch:invocation_id` on mismatch). No copied approval
  authority transfers across invocation/challenge/subject. **PASS.**

---

## 11. RIHAC projection provenance and anti-transfer

- The projection is built only inside `validate_approval` on full success;
  it is registered in the module-level, identity-keyed
  `_VALIDATED_AUTHORITY_CONTEXTS` dict; it is never persisted, never
  serialized, never reconstructed from fields.
- Downstream trust (`is_trusted_validated_authority_projection`) requires
  exact type + exact-object registry membership + intact recomputed
  content binding.
- A valid-looking projection reproducing every public field without the
  registration path → not authoritative (§4.3).
- `revalidate_validated_authority_projection` re-runs `validate_approval`
  from the stored context and returns `False` on a copied projection, a
  stale approval, a revoked credential, an expired proof/approval, a
  changed consumption state, or lost process-local provenance.

The projection is not a bearer seal. **PASS.**

---

## 12. Restart / re-authentication result

`_AUTHENTIC_PRINCIPAL_REGISTRY` (set) and `_AUTHENTIC_PRINCIPAL_CONTEXTS`
(dict) are process-local, identity-keyed, never persisted.
`AuthenticatedHumanPrincipal.__reduce__` raises — the result is
non-serializable by contract (HPAC-REQ-058). Independent test: discarding
the principal from both registries (simulated restart) and re-submitting
it to `validate_approval` →
`authenticated_principal_not_verifier_issued`. Persisted approval/proof
fields alone cannot recreate provenance; a stale pre-restart verifier
result is unusable after restart. The `.1R.6` restart model is preserved.
**PASS.**

---

## 13. Freshness / revocation matrix (independent, fresh)

Changes applied *between* authentication and authority construction:

| Case | Result |
|---|---|
| Principal revoked | `authenticated_principal_reverification_failed:*` (fail closed) |
| Credential revoked | `authenticated_principal_reverification_failed:*` (fail closed) |
| Proof / challenge expiry | rejected at fresh reverification (`.1R.7` case reproduced) |
| Approval expiry | rejected after fresh HPAC reverification |
| Presentation invalidated | rejected at fresh reverification |
| Lifecycle state changed | rejected at fresh reverification |
| Invocation identity changed | `subject_mismatch:invocation_id` / `authenticated_principal_invocation_mismatch` |
| Lost registry membership (restart) | `authenticated_principal_not_verifier_issued` |
| Replayed / non-`none` consumption state | rejected (`unrecognized_consumption_state:*` / consumption reason) |

All fail closed and do not depend on a future Gate-9 revalidation.
**PASS.**

---

## 14. HPAC-REQ-054 Step-4 disposition

`.1R.6` §3.2 made F2 / Step-4 a **prerequisite before production
consumption** (independent challenge-digest recomputation, not merely a
lifecycle-genesis cross-check). `.1R.7` implemented exactly that (§6).
Independently verified as implemented and effective.

- **F2 / HPAC-REQ-054 Step 4: REPAIRED — independently confirmed
  implemented. Not self-closed by `.1R.7`; confirmed here.**

---

## 15. F2 / F3 / F4 / F7 dispositions

| Finding | `.1R.6` decision | `.1R.8` independent disposition |
|---|---|---|
| F2 (Step 4) | prerequisite for `.1R.7` | Implemented and verified (§6, §14). |
| F3 (`.1R.4` "eight-step" label debt) | deferred, doc-only | Unchanged. Production trust semantics unaffected. No repair required. |
| F4 (`test_caller_constructed_verifier_result_rejected` name overclaim) | deferred, cosmetic | Unchanged. Functionally covered by accurately-named siblings and by this phase's suite. |
| F7 (registry resists caller-supplied-data forgery, not same-process arbitrary code) | non-blocking observation, carried | Unchanged and **not broadened** by `.1R.7`. The repaired plumbing is assessed under the documented trusted-process assumption; `.1R.7` claims no process isolation. Observation O2 (§7.4) is the same boundary, not an expansion. |

Production consumption does not change F3/F4 severity. F7 remains
non-blocking; the threat model is not broadened.

---

## 16. Gate-5 / Gate-9 / Gate-10 isolation

- **Gate-5 coordinator production wiring = 0.** No RDGO coordinator
  component exists in `src/pcae/**` (no `Gate5`/`GATE_5`/coordinator
  symbol). `runtime_dispatch_permission.py` calls
  `revalidate_validated_authority_projection` as the tiny `.1R.6` B1
  consumption hook inside the pre-existing structural PB request builder —
  this is a currentness check, not a coordinator.
- **Gate-9 writes = 0; proof consumption = 0; approval consumption = 0.**
  `runtime_invocation_authority_consumption.py` is byte-unchanged since
  `b85e903c` and has zero production importers (the only textual reference
  is a docstring in `hpac_verifier.py`). No
  `runtime-invocation-authority-consumption` directory is created by any
  validation path.
- **Gate-10: 0.** No runtime dispatch, adapter invocation, backend call,
  or external effect. Gate 10 untouched.

---

## 17. Permission Broker isolation

- `permission_broker_foundation.py` byte-identical to baseline
  (sha256 unchanged; also unchanged at `.1R.5.2.1`/`7b1f5b56`).
- No PB policy evaluation, no PB ALLOW/DENY driven by repaired authority,
  no POL change, no new production PB consumer.
- The only projection consumer remains the pre-existing structural
  `runtime_dispatch` request builder. A `simulation_only=False` request
  built through it is still universally denied by POL-005 (independently
  reproduced: `decision == "DENY"`, `"POL-005" in causing_policy_ids`).

---

## 18. POL-005 result

`ExecutionDisabledRule` (`policy_id = "POL-005"`) byte-identical to
baseline: on `simulation_only` False it returns
`DECISION_DENY` / `execution_boundary_unavailable` /
`matched_no_go_ids=("NG-025",)`, unconditionally, non-overridable
(`pcae permission-broker hard-blocks`: override/approval/risk all False).
No repaired authority can override it. **Hard DENY preserved.**

---

## 19. Runtime capability result

`pcae runtime inspect`: `not_implemented / Observed / observe /
unavailable`; registry empty; 0 plugins; 0 capabilities; PB status
`execution_unavailable`; posture `non-executing`. Even if a future real
authority could pass every repaired primitive, runtime capability
`unavailable` independently prevents execution (RPAC-001). Unchanged by
this phase.

---

## 20. Consumer inventory (post-`.1R.7`)

AST-level import inspection over `src/pcae/**`:

| Consumed | Production consumers | Classification |
|---|---|---|
| `hpac_verifier` (`is_verifier_authenticated_principal`, `reverify_authenticated_principal`) | `runtime_authority.py` only | intended `.1R.7` consumer |
| `AuthenticatedHumanPrincipal` | `runtime_authority.py` (via `hpac_verifier` import); `human_authenticator.py` docstring only | intended / benign |
| canonical approval store (`RuntimeInvocationApprovalStore`) | `runtime_authority.validate_approval`; `runtime_invocation_approval_store.py` | intended |
| repaired projection (`ValidatedAuthorityProjection`, `revalidate_validated_authority_projection`) | `runtime_dispatch_permission.py` only | intended `.1R.7` consumer |
| Gate-9 consumption module | none | — (stays unwired) |

`enforcement_approval.py` matches the substring `validate_approval` only
via its own unrelated `validate_approval_record` / `_dict` functions
(different subsystem, byte-unchanged since baseline) — **not** a consumer
of the repaired path. No unexpected authority-bearing consumer.

---

## 21. Production-file traceability

`git diff --name-only b85e903c HEAD -- src/pcae` = exactly:

```
src/pcae/core/hpac_verifier.py
src/pcae/core/runtime_authority.py
src/pcae/core/runtime_dispatch_permission.py
```

Identical to `.1R.6` §12's frozen "Modification required: Yes" matrix.
Every hunk traces to B1 (`runtime_authority.py`), B7
(`runtime_dispatch_permission.py`), N1 (`runtime_authority.py`), N2
(`runtime_authority.py`), or the HPAC-REQ-054 Step-4 prerequisite
(`hpac_verifier.py`). No file expansion. `runtime_invocation_approval_store.py`
and `runtime_invocation_authority_consumption.py` byte-unchanged.

---

## 22. Contract-byte identity

sha256 of all seven contracts + `permission_broker_foundation.py`
recomputed independently and compared to the bytes at `b85e903c` and at
`.1R.5.2.1` (`7b1f5b56`):

| File | sha256 | Drift |
|---|---|---|
| RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md | `38d98e9b…04d0` | none |
| RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md | `a47869ba…f608` | none |
| HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md | `24fd6fac…67b` | none |
| PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md | `e0799d46…ffef` | none |
| RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md | `24e1eefa…f5ab` | none |
| RUNTIME_PROVIDER_ADAPTER_CONTRACT.md | `395f6b9d…0c89` | none |
| PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md (PBPA) | `6daf404b…02b2` | none |
| permission_broker_foundation.py (POL-005) | `2eb7c106…39d1` | none |

`git diff --name-only b85e903c HEAD -- docs/contracts` = empty. **No
contract drift.**

---

## 23. Fresh independent test suite

`tests/test_b1_b7_n1_n2_production_authority_repair_independent_verification_3w1r2b1r1_1r8.py`
— 47 independently authored cases, **47 passed**. Coverage (all §39
minimum cases of the governing prompt, expanded):

1. B1 pre-repair behaviour reconstructed from fixed source (2 tests).
2. Copy / deepcopy / `replace` of a registered projection rejected.
3. Field-mutation breaks recomputed binding; hand-built lookalike rejected;
   invocation-transfer rejected; dispatch binding rejects untrusted
   projection.
4. B7 pre-repair "no dispatch-time reread" reconstructed.
5. B7 valid reread passes; deleted record / changed record / foreign
   tracker fail closed.
6. Step-4 independent recomputation (source + behaviour).
7. Caller-supplied challenge ignored/rejected; self-consistent
   substitution rejected; cross-invocation challenge rejected.
8. Changed invocation parameter changes the recomputed digest.
9. N1 external valid approval object rejected; duck-typed store rejected;
   noncanonical / unresolvable IDs rejected.
10. Canonical ID path resolves and reaches the HPAC stage.
11. Path-vs-writer (O2) documented; no store mutation verified.
12. N2 caller `approver_id` rejected (`TypeError`).
13. Legitimate verifier provenance recognized; still NON-REAL-rejected.
14. Deterministic NON-REAL hard rejection in creation and validation; no
    fixture store at PRODUCTION assurance; full-strength chain still
    rejected; `require_real_assurance` rejects.
15. Missing approval rejected despite valid authentication.
16. Approval invocation-binding mismatch rejected.
17. Copied / lookalike RIHAC projection rejected.
18. Projection cannot transfer to another invocation.
19–22. Principal revocation / credential revocation / proof expiry /
    approval expiry fail closed.
23. Restart loses verifier provenance.
24. Forged `AuthenticatedHumanPrincipal` (`object.__new__`, copy, pickle)
    rejected — F1 regression preserved.
25. Zero Gate-5 coordinator consumer.
26. Zero Gate-9 consumption wiring.
27. Zero PB authority effect; POL-005 DENY on execution claim.
28. Runtime state `unavailable`; contract bytes unchanged; three-file
    allowlist; test-only fixture not importable by production; repaired
    modules import nothing effectful.

---

## 24. `.1R.7` test-quality review

All 41 `.1R.7` cases in `test_runtime_authority_production_repair_3w1r2b1r1117.py`
were classified after independent derivation:

- **Normative trust/provenance:** Step-4 tamper/substitution; N1 caller
  object / copy / noncanonical ID / fake store / store-reread-no-mutation;
  N2 caller strings / copied principal / NON-REAL creation+validation;
  invocation substitution; lost-provenance; revocation/expiry/lifecycle/
  presentation reverification; B1 copy/mutation/invocation-transfer; B7
  reread cases. (majority)
- **No-go / scope:** test-only fixture isolation, frozen production-file
  allowlist, contract + POL-005 byte identity, consumer inventory + Gate-9
  unwired, forbidden-import check, "no PB authority + POL-005 DENY".
- **Regression/helper:** `_fixture_authority`, `_creation_kwargs`,
  `full_chain` (now asserts the NON-REAL rejection).

Observations on naming (do not affect the verdict):

- The `test_*_detected_by_fresh_reverification` family: for
  principal/credential revocation the assertion *does* prove fresh
  reverification (`authenticated_principal_reverification_failed:*` fires
  before the assurance stop). For `expired_approval` /
  `changed_presentation` / `changed_lifecycle`, the reason string can be
  either the reverification failure or the NON-REAL stop depending on
  ordering; the tests assert `projection is None` and accept the
  documented set — the *name* slightly over-promises which stage rejects,
  but the fail-closed outcome is real. Aligned with F4's class of issue;
  non-blocking.
- The `test_b1_*` cases exercise the `is_trusted_validated_authority_projection`
  predicate against a manually seeded registry entry (necessary — the
  positive `validate_approval` emission path is unreachable under
  Option-A). This is a faithful unit-level check of the decisive property,
  not an overclaim, but it is not an end-to-end emission test (O1).

Passing `.1R.7` implementation tests were treated as **not** independent
evidence; every claim above is backed by the fresh `.1R.8` suite and/or
direct source/contract re-derivation.

---

## 25. Regression attribution (fixed-SHA, independent)

Baseline SHA `b85e903c` (pre-`.1R.7`) vs candidate (current verification
tree). Affected selection: `-k "hpac or runtime_authority or
runtime_dispatch"`, `-p no:randomly`, full collection.

| Run | passed | failed |
|---|---|---|
| Baseline `b85e903c` | 760 | 23 |
| Candidate (HEAD + `.1R.8` suite excluded from the `-k` match) | 802 | 23 |

- Candidate-only nonpassing nodes: **0** (`comm -23` of sorted failing
  node-ID lists is empty).
- Baseline-only nonpassing nodes: **0**.
- Common failing nodes: **23**, byte-for-byte identical set — all
  `test_hpac_foundation_independent_verification_3w1r2b1r111r31.py`,
  `test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py`,
  `test_hpac_verifier_independent_verification_3w1r2b1r1115a1.py` (2), and
  `test_runtime_human_principal_contract_freeze_verification_3w1r2b1.py`
  (blocking-reproduction / contract-contradiction documentation tests).
  They reproduce identically with all `.1R.7` changes removed.
- The +42 candidate passes are `.1R.7`'s own new/updated cases
  (`test_runtime_authority_production_repair_3w1r2b1r1117.py` + adapted
  historical cases) that assert the repaired API.

**UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS = 0.**

### 25.1 Report/notification "historical failure" attribution

`.1R.7`'s report cites `report_notification_tests: 54 passed, 1 historical
failure`. Not inherited: the failing-node set is present and identical in
the fixed baseline `b85e903c` and unrelated to any `.1R.7`
finalization/report implementation change (`3fc26199` touches no
`phase_reports`/notification module). Classified pre-existing.

---

## 26. New findings (`.1R.8`)

All non-blocking. No blocking finding.

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
- **Tooling/infrastructure debt carried, not repaired:** Fast Green
  baseline-resolver weakness; `xdist` random-UUID parametrization
  instability; the 23 pre-existing historical/contradiction-documentation
  test failures in the HPAC/runtime selection. None prevented verification.

---

## 27. Runtime / zero-effect proof

For this phase's verification work:

```text
Runtime Enforcement calls   = 0
Shell Gate calls            = 0
runtime subprocess calls    = 0
provider / network calls    = 0
credential operations       = 0
hardware operations         = 0
Gate-9 consumption          = 0
Gate-10 external effects    = 0
```

Subprocesses invoked by this phase were: `git show` / `git diff`
(read-only history inspection) and `python -m pytest` (the local test
runner, including one isolated baseline worktree at `b85e903c`). These are
disclosed here and are distinct from any product/runtime execution path —
no runtime, adapter, or provider subprocess was invoked.

---

## 28. Real authentication / UI exclusion

Independently confirmed absent from the repaired modules and the repo
delta: real FIDO2, WebAuthn, CTAP, physical authenticator, real
enrollment, real hardware attestation, protected UI, trusted display,
approval CLI ceremony, enrollment CLI. AST import scan of the three
repaired modules shows none of `subprocess, socket, requests, httpx,
urllib, fido2, webauthn, ctap, smartcard, usb`. Real production human
authority remains unavailable.

---

## 29. Foundation and verifier regression reconfirmation

- **Foundation** (principal provenance, fixture non-upgradeability,
  presentation provenance, HPAC-REQ-092, proof writer provenance,
  authoritative genesis, predecessor validation, fork rejection,
  canonical-store containment): the governing HPAC foundation suites run
  identically pass/fail at baseline and candidate (§25) — no regression.
- **Verifier** (HPAC-REQ-054 verified semantics, UP, UV, mechanism
  neutrality, deterministic NON-REAL, F1 closure, invocation binding,
  fail-closed ordering): `test_hpac_verifier.py` and the
  `.1R.5.x` verification suites pass identically at baseline and candidate;
  F1 forgery vectors independently re-confirmed rejected (§8.3, §23 case
  24). No regression.

Any regression would be Blocking; none found.

---

## 30. Finding adjudication

Closure requires independent evidence at the production implementation
boundary. Each is met (§4–§13):

```text
B1 — INDEPENDENTLY CONFIRMED CLOSED AT PRODUCTION AUTHORITY IMPLEMENTATION BOUNDARY
B7 — INDEPENDENTLY CONFIRMED CLOSED AT PRODUCTION AUTHORITY IMPLEMENTATION BOUNDARY
N1 — INDEPENDENTLY CONFIRMED CLOSED AT PRODUCTION AUTHORITY IMPLEMENTATION BOUNDARY
N2 — INDEPENDENTLY CONFIRMED CLOSED AT PRODUCTION AUTHORITY IMPLEMENTATION BOUNDARY
```

This does **not** mean: real FIDO2 complete; real protected UI complete;
Gate-5/Gate-9 wiring complete; PB integrated; runtime capable; execution
ready. All of those remain unbuilt and unavailable.

---

## 31. Final verdict

```text
INDEPENDENTLY VERIFIED — B1/B7/N1/N2 PRODUCTION AUTHORITY REPAIR COMPLETE
(VERIFIED WITH NON-BLOCKING FINDINGS: O1, O2, O3, O4)
```

- No blocking finding.
- Deterministic NON-REAL cannot create or validate real authority
  (no NON-REAL assurance escalation defect).
- No integration leaked into deferred runtime / PB / Gate-5 / Gate-9 /
  Gate-10 boundaries (no production authority scope boundary violation).
- No contract drift; frozen production-file matrix matched exactly.
- Zero attributable functional regressions.

---

## 32. `.3` governance incident — preserved

```text
DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED
```

Nothing in `.1R.8` changes this. This phase's finalization/commit/push is
performed by the primary operator under the explicit human authorization
for `.1R.8` only, through the governed `pcae` lifecycle. No raw git
commit/push, no `--no-verify`, no force push, no hook bypass, no history
rewrite was used.

---

## 33. Next-phase status

B1/B7/N1/N2 independently close, so control returns to `.1R.6` and the
current `PROJECT_STATUS.md`. Per `.1R.6` §10.4 / §18, Gate-5/Gate-9
coordinator wiring is explicitly a **distinct, later, unscheduled
chapter** and, per this project's no-invent-an-ID discipline, has **no
phase ID**. No authoritative planning or state assigns one now.

```text
NEXT CANONICAL PHASE ID: none exists.
```

No coordinator wiring, no PB production permission integration, no real
FIDO2, no protected UI, no execution enablement is begun. Stop.

---

## 34. Commits, push status, `origin/main..HEAD`

- `.1R.8` commits: recorded in `PROJECT_STATUS.md` / `CHANGELOG.md` and the
  final `.pcae/phase-completion-metadata.json` at finalization.
- Pushed status: recorded at finalization.
- `origin/main..HEAD`: `0` after the governed push.

*(This section is completed by the governed finalization sequence; see
`PROJECT_STATUS.md` and `.pcae/phase-completion-metadata.json`.)*
