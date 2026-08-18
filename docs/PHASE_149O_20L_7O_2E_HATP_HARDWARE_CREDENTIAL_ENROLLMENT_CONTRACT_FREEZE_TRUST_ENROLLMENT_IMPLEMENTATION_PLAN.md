# Phase 149O.20L.7O.2E — HATP Hardware Credential Enrollment Contract Freeze + Trust-Enrollment Implementation Plan

Phase type: **CONTRACT FREEZE + IMPLEMENTATION PLAN ONLY.** No production source (`src/pcae/**`, `scripts/**`) modified. No FIDO2 implementation. No PIV implementation. No `hardware-credentials.json` written. No principal, signer, or hardware credential enrolled, provisioned, or registered. No `DeploymentBinding` created. No election initiated. No CHGR published. No certification performed. No Dell host mutated. No HMIC amendment.

## 1. Baseline / Confirmed Position (Entering State)

- True phase-entry commit: `e99afdd3` (`Phase 149O.20L.7O.2D.3: close task, transition to idle`), `origin/main..HEAD = 0`, working tree clean.
- Latest completed phase: **149O.20L.7O.2D.3 — HATP Principal/Signer Enrollment Contract Repair Independent Verification.** Verdict: **VERIFIED WITH NON-BLOCKING FINDINGS — HPSE-001 v1.1 CONTRACT REPAIR COMPLETE.** Former Blocking findings B-149O.20L.7O.2D.1-1 and B-149O.20L.7O.2D.1-2: **INDEPENDENTLY CONFIRMED CLOSED AT CONTRACT-REPAIR BOUNDARY** (by HPSE-REQ-056/HPI-7 for B-1, HPSE-REQ-011/059/060 for B-2). HHCE-001 disposition verdict from that phase: **(A) sufficiently defined** as a named prerequisite interface — HPSE-REQ-054 already bounds nearly every architectural decision HHCE-001's own correctness depends on. Two new Non-Blocking findings recorded: **NBF-1** (continuous-lock-hold requirement across `enroll_signer`'s check→write critical section, only cross-derivable from HPSE-REQ-057+HPSE-REQ-058(C)) and **NBF-2** (HPSE-REQ-054 does not explicitly freeze `HardwareCredentialRecord` revocation-timestamp semantics). Both closed by HHCE-001 v1.0 this phase (§16/§7 of that contract).
- Entering contract state: **HPSE-001 v1.1** (74 requirements, HPSE-REQ-001..074, sequential, no gaps), **HBDC-001 v1.2**, both re-read directly this phase (not merely narrated) at `docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md` and `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`.
- RepositoryIdentity `0107866f-af7c-40b4-8317-74e71acb05ca`: INDEPENDENTLY VERIFIED (prior phases). DeploymentBinding: ABSENT. Protected Root: EMPTY. Runtime: Observed / observe / unavailable.
- No hardware credential is currently enrolled. No Principal/Signer enrollment writer exists. No HHCE implementation exists. `Fido2HardwareProvider.credential_identity()` and `PivHardwareProvider.credential_identity()` remain unavailable placeholders (confirmed by direct read this phase, `hatp_fido2_provider.py:270-276`, `hatp_piv_provider.py:93-94`).

## 2. Contract State Produced This Phase

| Contract | Version | Status | Byte-changed by this phase? |
|---|---|---|---|
| HHCE-001 | 1.0 | FROZEN — READY FOR INDEPENDENT VERIFICATION | Yes — new document created |
| HPSE-001 | 1.1 | FROZEN — PENDING SECOND INDEPENDENT VERIFICATION (unchanged) | No |
| HBDC-001 | 1.2 | (unchanged) | No |
| HATP-001 | 1.0 | FROZEN, unamended | No |
| HMIC-001 | 1.4 | FROZEN, unamended (§10 below records the future source-scope consequence; no amendment made) | No |

`docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md` — new file, HHCE-001 v1.0, 52 requirements (`HHCE-REQ-001`..`052`, sequential, no gaps, mechanically reconfirmed by regex extraction). This document (the implementation plan) is the second deliverable of this phase, per the "one bundled implementation plan" strategic instruction (governing prompt §2/§33) — it is a companion planning document, not contract text, mirroring `docs/PHASE_149O_11_HATP_SIGNING_CEREMONY_EVIDENCE_STORE_IMPLEMENTATION_PLAN.md`'s existing precedent for a "contract freeze elsewhere → separate implementation plan doc" phase structure.

## 3. Primary-Source Reconstruction (Read Directly This Phase, Not Assumed)

- `src/pcae/core/hatp_hardware_credentials.py` — `HardwareCredentialRecord` (5 fields: `signer_key_id`, `provider_profile`, `protocol_name`, `algorithm`, `public_key`, `status`), `HATPHardwareCredentialStore` (read-only, `.production()`/`.lookup_credential()`), fixed platform roots (macOS `/Library/Application Support/PCAE/HATP/hardware-credentials`, Linux `/etc/pcae/hatp/hardware-credentials`), `_reject_symlink`, `_reject_duplicate_keys`, `inspect_credential_store_environment`. Module docstring explicitly defers enrollment to "a future Human/Admin-only administrative surface" — this phase's HHCE-001 is that surface's contract.
- `src/pcae/core/hatp_fido2_provider.py` — `Fido2HardwareProvider.credential_identity()` (`:270-276`) is a single unconditional `raise HATPProviderUnavailableError(...)`. `capabilities()` reports `CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS`, `device_attestation=False`. `verify()` (`:359-362`) fail-closes on `record is None or record.status != "active"`.
- `src/pcae/core/hatp_piv_provider.py` — `PivHardwareProvider.credential_identity()` (`:93-94`) is likewise a single unconditional `raise`. `capabilities()` reports `NOT_CONFORMANT`. No PKCS#11/smart-card dependency exists anywhere in this codebase.
- `src/pcae/core/hatp_providers.py` — `HATP_HARDWARE_PROVIDER_V1` (sole closed profile string), `HATPHardwareSigner`/`HATPProofVerifierProvider` Protocols, `create_production_hardware_provider` (FIDO2 attempted first, PIV only if `allow_piv_fallback=True`), error hierarchy (`HATPProviderUnavailableError`, `HATPProviderCancelledError`, `HATPProviderDeviceError`).
- `src/pcae/core/hatp_signing_ceremony.py:534-542` — `_resolve_signer` already calls `provider.credential_identity()` on the *verification* side's identity-exchange path; this is the existing mechanism HPSE-REQ-010 requires reuse of for *enrollment*.
- `src/pcae/core/hatp_bootstrap.py` — `PrincipalRecord` (2 fields, no `revoked_at` — HPSE-REQ-008's disclosed gap), `SignerRecord` (5 fields, has `revoked_at`), `HATPTrustStore` (read-only), fixed Protected Root (`/Library/Application Support/PCAE/HATP/trust-store` / `/etc/pcae/hatp/trust-store`), `_parse_registry_document`'s closed-schema/duplicate-rejection discipline, `_require_revoked_at_consistency`.
- `src/pcae/core/hatp_deployment_binding_admin.py` — the closest existing *writer* precedent: `_write_atomic`-idiom reuse (`_atomic_write_registry`), `_read_back_and_verify`, `.deployment-binding-transition.lock` (`fcntl.flock`, `0o600`, blocking exclusive), `create`/`rotate`/`revoke` + preview quartet, `AuthorityEvidence` (election-reference-as-audit-metadata-only), audit ordering (validate → mutate under lock → read back → audit → return), disclosed audit-after-write-failure limitation. This is the module HHCE-001's future writer and this plan's Surface B most directly mirror.
- `src/pcae/core/human_approval_trusted_provenance.py` — `verify_hatp_proof` independently re-derives/cross-checks `signer`/`principal.status`/`authority.status`/`DeploymentBinding` fields live on every call (confirmed via grep this phase: no `HATPHardwareCredentialStore` import — the *provider's own* `verify()` method is the only caller of the hardware-credential registry, never `verify_hatp_proof` directly, exactly as `hatp_hardware_credentials.py`'s own module docstring states).
- `docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md` v1.1 — read in full this phase (all 52 sections, `HPSE-REQ-001`..`074`). §27-§48 (the v1.1 repair amendment) are this phase's direct primary source for HHCE-001's minimum bounded scope, lock ordering, partial-failure matrix, and error-vocabulary additions.
- `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` v1.2 — read for Protected Root ownership/mode discipline (HBDC-REQ-013..021), reused unchanged for the hardware-credential-store root's own ownership model (HHCE-REQ-022).

## 4. HHCE-001 Freeze Summary

See `docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md` for full text. Highlights:

- **Schema (§5, §7):** `HardwareCredentialRecord` reuses `hatp_hardware_credentials.py`'s existing 5 fields unwidened, plus one new field this contract adds: `revoked_at: Optional[str]` (closes NBF-2), with identical `_require_revoked_at_consistency` discipline and the identical strict timestamp grammar (`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$`) HBDC-REQ-067/HPSE-REQ-052 already fix. Document level adds `schema_version` (mirrors `registry_version`).
- **Storage (§12):** Canonical path is `hatp_hardware_credentials.py`'s own existing fixed production root — no alternate path invented.
- **Credential identity semantics (§8-§9):** Target output requirements reuse HPSE-REQ-059's frozen semantics exactly (unique, stable, non-extractable, provider-bound, persistable); current-state disclosure restated precisely, not obscured — both providers unconditionally raise today.
- **Writer API (§11):** `register_credential`, `revoke_credential`, plus `preview_register_credential`/`preview_revoke_credential` — the exact HPSE-REQ-054 minimum, no more. Idempotent registration; fail-closed conflict.
- **Locking (§14-§16):** New `.hardware-credential-transition.lock`, `fcntl.flock`, `0o600`, blocking exclusive. HPSE-REQ-057's outer/inner ordering restated as this contract's own obligation. **NBF-1 closed**: HHCE-REQ-037 states explicitly, as one sentence, that both locks remain held continuously across `enroll_signer`'s entire check→write critical section, no release/reacquire between check and write.
- **Cross-registry invariant (§17):** HPSE-REQ-056/HPI-7 restated symmetrically from the credential-registry side.
- **Revocation (§18):** Revoked credential fails closed at verification time (already implemented, unchanged). Explicit, non-cascading disposition: `revoke_credential` records whether a referencing active `SignerRecord` exists (audit-metadata only, read-only check), does not auto-revoke it — chosen because live verification-time re-checking (already implemented) is the security-relevant checkpoint, mirroring HPSE-REQ-067/069's identical rationale.
- **Error vocabulary (§19):** `PROVIDER_UNAVAILABLE`, `CREDENTIAL_IDENTITY_UNAVAILABLE`, `CREDENTIAL_ALREADY_REGISTERED`, `CREDENTIAL_CONFLICT`, `CREDENTIAL_REVOKED`, `CROSS_REGISTRY_MISMATCH` (reserved, unreachable through this writer), `LOCK_FAILURE`, `WRITE_FAILURE`, `READBACK_MISMATCH`, `AUDIT_INCOMPLETE`.
- **Security invariants HHI-1..6 (§25).**

## 5. Bundled Implementation Architecture (Surfaces A-E)

Per the governing prompt's strategic principle (§1/§2): one coherent implementation phase, not fragmented, because the five surfaces below are tightly coupled by HPSE-REQ-056's cross-registry precondition and cannot be independently implementation-ready — `enroll_signer` (Surface C) cannot function without Surface B existing; Surface B's `register_credential` cannot function without Surface A producing a real `signer_key_id`; the composite readiness gate (HPSE-REQ-072) already names all of them jointly. No primary-architecture evidence surfaced this phase requires splitting them into separate implementation phases.

| Surface | Module (proposed, follows repo convention — final naming decided at implementation time) | Owns |
|---|---|---|
| **A** | `src/pcae/core/hatp_fido2_provider.py` (MODIFY) | Selected-provider `credential_identity()` real implementation satisfying HPSE-REQ-059 (§7 below: FIDO2 selected) |
| **B** | `src/pcae/core/hatp_hardware_credential_admin.py` (NEW), `scripts/hatp_hardware_credential_admin.py` (NEW) | HHCE-001's writer: `register_credential`/`revoke_credential`/preview pair |
| **C** | `src/pcae/core/hatp_principal_signer_admin.py` (NEW), `scripts/hatp_principal_signer_admin.py` (NEW) | HPSE-001's writer: `enroll_principal`/`revoke_principal`/`enroll_signer`/`revoke_signer`/preview quartet |
| **D** | `src/pcae/core/hatp_bootstrap.py` (MODIFY, narrowly — `PrincipalRecord`/`_parse_principal`/`_require_revoked_at_consistency` call site only) | `PrincipalRecord.revoked_at` schema/parser widening (HPSE-REQ-008) |
| **E** | `src/pcae/core/hatp_deployment_binding_admin.py` (MODIFY, narrowly — `create_deployment_binding`/`rotate_deployment_binding` validation only) | Cross-validation against Principal/Signer/hardware-credential registries (HPSE-REQ-047/048) |

No other production file is touched. Explicitly **not** modified by the future bundled implementation: `human_approval_trusted_provenance.py`, `hatp_providers.py` (Protocol/error-class definitions only — reused, not amended, unless Surface A needs a narrowly-scoped new capability field, TBD at implementation time), `hatp_piv_provider.py` (PIV remains an unconditional placeholder this phase and the next, per §7 below), `hatp_signing_ceremony.py` (consumed read-only), HPSE-001, HHCE-001, HBDC-001, HATP-001 contract text (no contract amendment; only production code implements already-frozen text).

## 6. Surface A — Selected Provider Credential Identity/Enrollment Implementation

- **Target:** `Fido2HardwareProvider.credential_identity()` (or a renamed/`enroll_credential()`-named successor per HPSE-REQ-059's deliberate non-freezing of a call signature) implements a real CTAP2 `makeCredential`-based ceremony producing a fresh, resident-or-non-resident `credential_id` satisfying HPSE-REQ-059(a)-(f)/HHCE-REQ-012(a)-(f).
- **Mechanics (design-level, not implemented this phase):** `Ctap2.make_credential(...)` against `_HATP_RP_ID`/a fresh random `client_data_hash` (mirroring `request_signature`'s existing `Ctap2.get_assertion` call pattern for symmetry); extract `credential_id` and the COSE public key from the resulting `AttestedCredentialData`; serialize the public key identically to `request_signature`'s existing evidence-serialization convention (hex-encoded, matching `hardware-credentials.json`'s own `public_key_hex` convention, HPSE-REQ-012).
- **Error mapping:** no device attached → `HATPProviderUnavailableError` (unchanged exception class, now genuinely conditional on device presence rather than unconditional); user cancels/times out during the presence ceremony → `HATPProviderCancelledError` (mirrors `request_signature`'s existing `CtapError.ERR.ACTION_TIMEOUT`/`USER_ACTION_TIMEOUT` handling); transport/protocol fault → `HATPProviderDeviceError`.

## 7. First Provider Implementation Choice — FIDO2 Selected

| Criterion | FIDO2 | PIV |
|---|---|---|
| Existing source readiness | `Fido2HardwareProvider` already fully implements `request_signature`/`verify`; only `credential_identity()` is a placeholder | `PivHardwareProvider` is a complete structural placeholder — every method unconditionally fails |
| Library availability | `fido2`/`cryptography` already declared as the `pcae-harness[hatp-hardware]` extra, already imported and used by `request_signature`/`verify` | No PKCS#11/smart-card library (`pyscard`, `python-pkcs11`) present in this codebase at all |
| Deterministic testability | `TestHATPProofVerifierProvider` pattern already proven for FIDO2-adjacent Wave-4 tests; `Ctap2.make_credential` is a well-documented CTAP2 primitive symmetrical to the already-implemented `get_assertion` | No equivalent groundwork exists |
| Real hardware availability | Not exercised in this development environment (documented limitation, unchanged) — identical to PIV | Identical: none |
| HATP proof-path compatibility | Already proven end-to-end for `request_signature`/`verify` (149O.2 spike, `hatp_fido2_provider.py` docstring) | Undemonstrated for any operation |
| Portability | CTAP2 HID is broadly supported across authenticator vendors | PIV/PKCS#11 middleware is platform- and vendor-fragmented |
| Implementation scope | Narrow: one new method on an already-mostly-implemented class, reusing existing imports/constants | Broad: an entire protocol binding from zero, plus a new third-party dependency |

**Selected: FIDO2**, per this phase's governing prompt §10 ("choose the fastest safe first provider... do not require parity before first-use"). PIV remains contractually supported (HHCE-001/HPSE-001 are protocol-neutral, HPSE-REQ-064) but operationally unavailable — no PIV implementation work is planned in the immediately-next bundled implementation phase (149O.20L.7O.2F) unless a future primary-architecture finding requires it.

## 8. Surface B — HHCE-001 Writer (Hardware Credential Registry Administration)

Mirrors `hatp_deployment_binding_admin.py`'s structure directly: `AuthorityEvidence`-analogous input dataclass (`election_reference` required, no `principal_id`/`signer_key_id`-mismatch fields since this writer has no principal concept); `register_credential(*, credential: ProviderAssertion-derived-identity, election_reference: str, _store_root: Optional[Path])`; `revoke_credential(*, signer_key_id: str, election_reference: str, ...)`; `preview_register_credential`/`preview_revoke_credential`; `_hardware_credential_transition_lock` (new `.hardware-credential-transition.lock`, mirrors `_deployment_binding_transition_lock` exactly); `_atomic_write_credential_registry` (reuses the `_write_atomic` idiom); `_read_back_and_verify_credential` (reuses `HATPHardwareCredentialStore.lookup_credential` as the verification read path). Audit ordering identical to `hatp_deployment_binding_admin.py`'s own (validate → lock → mutate → read back → audit → return).

## 9. Surface C — Principal/Signer Enrollment Writer

Implements HPSE-001 v1.1's already-fully-specified writer contract (§11-§18, §26-§45 of that contract). Structure: `enroll_principal`/`revoke_principal`/`enroll_signer`/`revoke_signer` + preview quartet, on `src/pcae/core/hatp_principal_signer_admin.py`, invoked only via `scripts/hatp_principal_signer_admin.py` (mirrors HPSE-REQ-028/029). `enroll_signer` is the operation that implements HPSE-REQ-056/HHCE-REQ-036/037's cross-registry precondition and continuous two-lock hold: it acquires the hardware-credential-store lock (outer, calling into Surface B's read path or a shared internal check function — TBD at implementation time whether Surface C imports Surface B's module directly or duplicates a narrow read-only check, mirroring this codebase's existing per-module small-helper-duplication convention) then `.deployment-binding-transition.lock` (inner), and holds both continuously through validation, write, read-back, and outcome classification, exactly as HHCE-REQ-037 requires. `enroll_signer` calls the selected provider's `credential_identity()` (Surface A) live during the enrollment ceremony (HPSE-REQ-010), never accepting a caller-supplied `signer_key_id`.

## 10. Surface D — `PrincipalRecord.revoked_at` Implementation Plan

`src/pcae/core/hatp_bootstrap.py::PrincipalRecord` widens from `(principal_id: str, status: str)` to add `revoked_at: Optional[str] = None`. `_parse_principal`'s `allowed` field set widens from `{"principal_id", "status"}` to `{"principal_id", "status", "revoked_at"}`; a new call to the existing `_require_revoked_at_consistency` helper (already used identically by `_parse_signer`/`_parse_authority`/`_parse_deployment_binding`) is added to `_parse_principal`. **Accepted field set:** identical three fields, no others. **Active/null semantics:** `status == "active"` requires `revoked_at is None`. **Revoked/timestamp semantics:** `status == "revoked"` requires a non-null, grammar-valid `revoked_at`. **Strict timestamp grammar:** the identical `_parse_iso_timestamp`-permissive-read / HBDC-REQ-067-strict-write split already governing every other record's `revoked_at` field. **Backwards compatibility:** an existing on-disk `principal` record with no `revoked_at` key parses identically to today (the field defaults to absent/`None`, and `status == "active"` already requires exactly that) — this is a strictly additive, non-breaking widening, since `hardware-credentials.json`/`registry.json` are both currently empty in every real deployment (no existing data to migrate). This is a change to `hatp_bootstrap.py`, an HMIC-bound file (§10 below).

## 11. Surface E — `DeploymentBinding` Producer Amendments

`create_deployment_binding`/`rotate_deployment_binding` (`hatp_deployment_binding_admin.py`) gain a new validation step, inserted after `_validate_authority_evidence` and before the existing lock-acquisition, per HPSE-REQ-047/048: resolve `principal_id` via `HATPTrustStore.production().lookup_principal` — must exist, `status == "active"`; resolve `signer_key_id` via `.lookup_signer` — must exist, `status == "active"`, and `signer.principal_id == authority.principal_id`; resolve the hardware credential via `HATPHardwareCredentialStore.production().lookup_credential(signer_key_id)` — must exist, `status == "active"`; `provider_profile` is derived from the resolved `SignerRecord.provider_profile` (HPSE-REQ-048), not accepted as independent `AuthorityEvidence` input — `AuthorityEvidence.provider_profile` is therefore removed as free-form input and replaced by this derivation (a breaking signature change to `AuthorityEvidence`, planned and accepted here since no real `DeploymentBinding` has ever been created — `DeploymentBinding: ABSENT`, confirmed this phase's entering state); `authority_scope` continues to be validated against HBDC-001's own canonical Class-B allowlist (unchanged, HBDC-REQ-058 scope). Preview (`preview_create_deployment_binding`/`preview_rotate_deployment_binding`) shares this identical validation path (never a separate, potentially-drifting copy).

## 12. Proof-Verifier Compatibility

`verify_hatp_proof` (`human_approval_trusted_provenance.py`) is not modified by this bundled implementation. It already independently re-derives/cross-checks `signer`/`principal.status`/`authority.status`/binding fields live on every call (HPSE-REQ-067, confirmed this phase). Future enrollment state (real `PrincipalRecord`/`SignerRecord`/`HardwareCredentialRecord`/`DeploymentBinding`) is directly consumable by this existing, unmodified verification path, subject only to Surface A's provider implementation actually producing valid signatures — no verifier-side regression is planned or required.

## 13. Composite Readiness Mapping (HPSE-REQ-072)

| HPSE-REQ-072 condition | Closed by (post-149O.20L.7O.2F, if implemented + independently verified) |
|---|---|
| (a) provider supports HPSE-REQ-059 semantics | Surface A |
| (b) HHCE-001 exists, verified, writer implemented+verified | This phase (contract) + 149O.20L.7O.2E.1 (verification) + Surface B (writer) + its own IV |
| (c) matching active hardware credential registered for a specific attempt | Surface B, runtime fact per attempt |
| (d) target `principal_id` active | Surface C / Surface D (schema prerequisite) |
| (e) `provider_profile` allowlist consistency | Surface C, unchanged HPSE-REQ-020 check |

Real-host enrollment readiness additionally requires actual physical FIDO2 credential provisioning on the target Dell host — not performed, not authorized, this phase or the next.

## 14. Error Vocabulary (Consolidated)

HHCE-001's own (§19 of that contract): `PROVIDER_UNAVAILABLE`, `CREDENTIAL_IDENTITY_UNAVAILABLE`, `CREDENTIAL_ALREADY_REGISTERED`, `CREDENTIAL_CONFLICT`, `CREDENTIAL_REVOKED`, `CROSS_REGISTRY_MISMATCH`, `LOCK_FAILURE`, `WRITE_FAILURE`, `READBACK_MISMATCH`, `AUDIT_INCOMPLETE`. HPSE-001's own (HPSE-REQ-034/071, unchanged by this phase): principal/signer not found, duplicate principal/signer, signer/principal mismatch, unsupported provider profile, revoked principal/signer, malformed registry, read-back mismatch, `HARDWARE_PROVIDER_UNIMPLEMENTED`, `HARDWARE_CREDENTIAL_NOT_REGISTERED`, `HARDWARE_CREDENTIAL_CONFLICT`, `CREDENTIAL_IDENTITY_UNAVAILABLE` (shared name, HPSE-001's own enrollment-time-facing use). No redundant synonym is introduced across the two contracts.

## 15. Runtime Neutrality Proof

Grep-confirmed this phase: no `src/pcae/core/hatp_*` module references `claude`, `codex`, `deepseek`, or any runtime-adapter identifier. `provider_profile`/`protocol_name` name hardware security-property classes only (`HATP_HARDWARE_PROVIDER_V1`, `"FIDO2"`/`"PIV"`), never a runtime. Both HHCE-001 (§21) and HPSE-001 (§24, §45) state this as a standing normative rule the bundled implementation must not violate; this plan introduces no new module that couples provider selection to runtime identity.

## 16. Security Model (Summary)

Threat classes named by HHCE-001 §23 and HPSE-001 §32 (mandatory attack matrix): malformed registry (either file); symlinked root/registry file; duplicate credentials/signers; credential-ID collision; principal/signer mismatch; provider mismatch; revoked credential/principal/signer; stale read (TOCTOU); concurrent writer; check/write race across the two-lock boundary; partial durable state (six-case HPSE-REQ-058 matrix); audit failure; replay; unknown fields. All are addressed by contract text (this phase) with no residual open item requiring further contract work before implementation planning proceeds.

## 17. Testing Architecture — Parallel Lanes (Governing Prompt §34)

- **Lane 1 (focused, parallel-safe):** provider tests (Surface A — deterministic evidence-format/signature-crypto tests, no live device, mirroring `request_signature`'s existing test discipline); HHCE tests (Surface B — schema round-trip, idempotency, conflict, lock ordering, revocation-disclosure); Principal/Signer tests (Surface C — cross-registry precondition, continuous-lock-hold, six-case matrix); cross-registry tests (both registries together); `DeploymentBinding` validation tests (Surface E — active/inactive principal/signer/credential combinations).
- **Lane 2 (affected regressions, concurrent with implementation/documentation):** existing HATP test suite; HBDC tests; HMIC-related source-identity tests (once HMIC re-certification is separately performed, §10); `verify_hatp_proof` regression tests; trust-store (`hatp_bootstrap.py`) regression tests; governance-path tests unaffected by these five surfaces.
- **Lane 3 (authoritative convergence gate, before implementation-phase closure):** focused serial/adversarial verification wherever concurrency matters (the two-lock ordering, the continuous-hold discipline); affected broad regression; Fast Green; full serial suite only if unexplained failures remain or trust-boundary changes warrant it — not run reflexively after every intermediate edit, per the governing prompt's explicit instruction.

This phase (149O.20L.7O.2E) performs none of this testing itself — it is contract/plan-only. This section is the plan the eventual implementation phase (149O.20L.7O.2F) must follow.

## 18. Independent Implementation Verification (Required Follow-On)

Per the governing prompt §35, the bundled implementation (149O.20L.7O.2F) must be followed by one strong IV phase (149O.20L.7O.2F.1) that independently attacks: provider semantics (does Surface A's ceremony actually satisfy HPSE-REQ-059, re-derived from the installed `fido2` library's own source, not from this plan's prose); actual credential identity (uniqueness/stability, re-tested); hardware registry (Surface B's atomicity/lock/conflict/idempotency, re-tested against real concurrent-process scenarios); signer identity durability (HPSE-REQ-061's equivalence, re-checked); cross-registry locking (HHCE-REQ-036/037's continuous-hold claim, re-derived from the actual implementation's code, not merely re-reading this plan); partial failures (all six HPSE-REQ-058 cases, re-attacked against the real implementation); replay; revocation (§18 of HHCE-001, re-attacked for whether the disclosed non-cascade disposition remains acceptable once real state exists); `DeploymentBinding` cross-validation (Surface E, re-tested); proof verification (no regression, re-confirmed); no authority leakage (HHI-1..6 and HPI-1..8, re-attacked against the real, implemented surfaces, not contract text alone).

## 19. HMIC Source-Scope Consequence (Named, Not Performed This Phase)

Per HPSE-REQ-073 (already named) and HHCE-REQ-051 (this phase's own restatement): a future HMIC-001 source-scope analysis MUST include, before any positive authority consumption from these surfaces: `hatp_fido2_provider.py` (Surface A change — already HMIC-bound, so any change mechanically triggers re-certification by the existing digest mechanism); `hatp_hardware_credential_admin.py` + its companion script (Surface B, new files, not yet bound); `hatp_principal_signer_admin.py` + its companion script (Surface C, new files, not yet bound); `hatp_bootstrap.py` (Surface D change — already HMIC-bound); `hatp_deployment_binding_admin.py` (Surface E change — already HMIC-bound). This phase performs no HMIC-001 amendment; the fresh transitive source-scope analysis is required after 149O.20L.7O.2F's implementation lands, before that implementation's authority is treated as certified.

## 20. Public-First Confirmation

This contract, this implementation plan, and the eventual implementation/tests/verification evidence remain public by default. Neither document contains private keys, tokens, PINs, real credential secrets, sensitive deployment secrets, or exploitable zero-day detail — confirmed by direct re-read of both files produced this phase before phase completion.

## 21. Parallel DeepSeek Research Track (Confirmation, Not Executed This Phase)

Per the governing prompt §38, the DeepSeek comparative research track is authorized to proceed in parallel with this trust-contract phase and its eventual bundled implementation. It is independent of this phase's own scope; this phase does not modify trust kernel architecture on the basis of any research finding (none was consulted), and this phase does not execute or advance that research track — it is noted here only as authorized-to-proceed, per the governing prompt's own instruction not to actually run it in this phase.

## 22. Governance Results This Phase

- `pcae check`: passed (recorded at phase completion, §"Required final report" of the governing prompt).
- `pcae health`: healthy.
- No raw `git commit`/`git push`. No `--no-verify`. No force push. No governance bypass.
- Zero production `.py` file (`src/pcae/**`, `scripts/**`) bytes modified. Zero hardware provisioning. Zero credential registration. Zero principal/signer enrollment. Zero `DeploymentBinding` creation/rotation/revocation. Zero election initiated. Zero CHGR published. Zero certification performed. Zero Dell mutation.

## 23. Implementability Verdict

**HHCE-001 CONTRACT FROZEN + TRUST-ENROLLMENT IMPLEMENTATION PLAN READY FOR INDEPENDENT VERIFICATION.**

## 24. Next Phase

**149O.20L.7O.2E.1 — HHCE-001 + Trust-Enrollment Implementation Plan Independent Verification.** Narrow and fast: re-derive HHCE-001's schema/locking/cross-registry/revocation/error-vocabulary claims against primary source; attack NBF-1/NBF-2 structural closure; attack the FIDO2-first selection rationale; attack the Surface A-E bundling decision itself (should any surface be split out). If it passes: **149O.20L.7O.2F — HATP Trust-Enrollment Implementation Capability**, then **149O.20L.7O.2F.1 — HATP Trust-Enrollment Implementation Capability Independent Verification**. Do not fragment 7O.2F further without a demonstrated need (governing prompt §42).

## Strategic Breakpoint (Restated, Unchanged)

The parallel DeepSeek track continues. The trust path and competitive/product path proceed concurrently. After eventual real credential provisioning, principal/signer enrollment, `DeploymentBinding` creation, independent real-host verification, and intended HBDC clean state: pause before Boundary C for the strategic architecture convergence decision. Not reached this phase.
