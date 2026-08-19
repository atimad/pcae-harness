# Phase 149O.20L.7O.2F — HATP Trust-Enrollment Implementation Capability

## 1. Entering state

- Phase-entry commit: `d11b8cd0` (`Phase 149O.20L.7O.2E.1: close task, transition to idle`), `origin/main..HEAD = 0`, working tree clean.
- Entering contracts: HPSE-001 v1.1 (74 requirements), HHCE-001 v1.0 (52 requirements, `FROZEN — READY FOR INDEPENDENT VERIFICATION`), HBDC-001 v1.2. Prior phase (149O.20L.7O.2E.1) verdict: **VERIFIED WITH NON-BLOCKING FINDINGS — IMPLEMENTATION-READY**, recording one Non-Blocking finding: HHCE-REQ-002 described `HardwareCredentialRecord.public_key` as "DER SubjectPublicKeyInfo," but `Fido2HardwareProvider.verify()` actually parses CBOR-encoded COSE_Key bytes.
- RepositoryIdentity `0107866f-af7c-40b4-8317-74e71acb05ca`. DeploymentBinding: ABSENT. Protected Root: EMPTY. Runtime: Observed/observe/unavailable. No hardware credential enrolled, no principal/signer enrolled, no writer existed for `hardware-credentials.json` or `registry.json`'s `principals`/`signers` sections.

## 2. Objective and scope

Implement one coherent Trust-Enrollment capability (Surfaces A-E) per the bundled implementation plan (`docs/PHASE_149O_20L_7O_2E_HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT_FREEZE_TRUST_ENROLLMENT_IMPLEMENTATION_PLAN.md`), entirely with synthetic/local/disposable fixtures. No real hardware provisioned. No real principal, signer, or hardware credential enrolled. No real `DeploymentBinding` created.

## 3. NBF-149O.20L.7O.2E.1-1 — fixed in passing

HHCE-001 bumped **v1.0 → v1.1** in place: `HHCE-REQ-002`'s text revised (same requirement identity, no renumbering, mirroring HPSE-001 v1.1's own precedent) to state `public_key` is "protocol-native public-key encoding — for FIDO2, CBOR-encoded COSE_Key bytes," matching `Fido2HardwareProvider.verify()`'s actual `CoseKey.parse(cbor.decode(record.public_key))` behavior. New §30 records the repair rationale. Requirement count unchanged (52). `Fido2HardwareProvider.enroll_credential()` (Surface A) is the first code that actually produces `public_key` bytes under this contract, and it produces exactly CBOR-encoded COSE_Key bytes.

## 4. Surface A — FIDO2 credential identity/enrollment

`src/pcae/core/hatp_fido2_provider.py`: added `Fido2HardwareProvider.enroll_credential(*, presence_timeout_s=30.0) -> EnrolledFido2Credential`, a real CTAP2 `makeCredential`-based ceremony (fresh random `client_data_hash`, `_HATP_RP` rp info, ES256-only `key_params`). Extracts `credential_id`/COSE public key from `AttestedCredentialData`; returns `credential_id_hex` (== `signer_key_id`, HPSE-REQ-061), `algorithm` (`type(cose_key).__name__`, fail-closed on unsupported algorithm via `_SUPPORTED_ENROLLMENT_ALGORITHMS`), `public_key_hex` (CBOR-encoded COSE_Key, hex), `provider_profile`. Errors mapped identically to `request_signature`'s existing discipline: no device → `HATPProviderUnavailableError`; cancel/timeout → `HATPProviderCancelledError`; transport/protocol fault or missing credential data → `HATPProviderDeviceError`. Never extracts a private key (CTAP2 `makeCredential` returns only a public key + credential ID).

**Deliberate non-redesign:** `credential_identity()` is left byte-unchanged (still unconditionally raises `HATPProviderUnavailableError`). It remains `_resolve_signer`'s (`hatp_signing_ceremony.py`) *discovery*-at-signing-time operation for an already-enrolled resident credential — a different operation from *minting* a fresh credential at enrollment time. HPSE-REQ-059 explicitly anticipates a distinct `enroll_credential()`-named method; conflating the two under one name would mean every signing-ceremony call silently mints a new credential, contradicting HHCE-REQ-012(b)'s stability requirement.

Deterministic tests (no real hardware): monkeypatch `CtapHidDevice.list_devices`/`Ctap2`, mirroring `request_signature`'s own existing pattern, using real `fido2`/`cryptography` WebAuthn/COSE structures with a test-only in-memory ECDSA key.

PIV: unchanged, still an unconditional placeholder. No PKCS#11/smart-card dependency added.

## 5. Surface B — HHCE-001 writer

New `src/pcae/core/hatp_hardware_credential_admin.py`: `register_credential`/`revoke_credential`/`preview_register_credential`/`preview_revoke_credential`, mirroring `hatp_deployment_binding_admin.py`'s structure. `CredentialEnrollmentEvidence` input dataclass (protocol-neutral — this module never calls a hardware provider itself). Own error hierarchy rooted at `HATPHardwareCredentialAdminError`. Own lock `.hardware-credential-transition.lock` (`fcntl.flock`, `0o600`, blocking exclusive) via `hardware_credential_transition_lock()`, exported for Surface C's outer-lock reuse. Atomic write reuses the `_write_atomic` idiom (`mkstemp`/`fsync`/`os.replace`). Read-back verification via the shared document parser. Idempotent registration (`ALREADY_REGISTERED`); conflicting/differing-field or revoked-target registration fails closed (`CredentialConflictError`), never overwrites/reactivates. Revocation is monotonic and idempotent (`ALREADY_REVOKED`, original `revoked_at` preserved); never cascades to a referencing `SignerRecord` — instead emits an audit-metadata-only `referencing_active_signer=true/false` note via a lock-free read of the trust store (HHCE-REQ-043).

`hatp_hardware_credentials.py` (schema, Surface B continued): `HardwareCredentialRecord` widened with `revoked_at: Optional[str] = None` (HHCE-REQ-008); duplicated `_require_revoked_at_consistency`/strict timestamp grammar. New `_parse_credential_registry_document` (document-level: `schema_version` validated with backward-compatible default, unknown top-level/per-record fields rejected, non-dict entries now rejected rather than silently skipped) — reused by both the reader (`HATPHardwareCredentialStore`) and the writer, closing two previously-disclosed findings (B-149O.3-3, B-149O.3-4) as a side effect of implementing HHCE-REQ-003/024.

## 6. Surface C — Principal/Signer writer, the load-bearing continuous two-lock section

New `src/pcae/core/hatp_principal_signer_admin.py`: `enroll_principal`/`revoke_principal`/`enroll_signer`/`revoke_signer` + preview quartet. Shares `registry.json`'s existing `.deployment-binding-transition.lock` with the `DeploymentBinding` producer (HPSE-REQ-033, reusing `hatp_deployment_binding_admin`'s own lock/write/read-back primitives directly — a legitimate real import, not a data reference; two pre-existing "producer imported nowhere but itself" enforcement tests were updated to allow this named exception).

`enroll_signer` — HHCE-REQ-037's continuous two-lock critical section:

```
with hardware_credential_transition_lock(hw_store_root):        # OUTER
    credential = <read hardware-credentials.json>
    with _deployment_binding_transition_lock(binding_store_root):  # INNER
        <principal validation>
        <HPSE-REQ-056 precondition re-check>
        <signer write + read-back>
        <post-write cross-registry re-verification>
    # inner lock released here
# outer lock released here
```

Both locks are held continuously from the precondition check through write, read-back, and outcome classification — no release/reacquire between check and write. Verified structurally (source-order assertion that the outer-lock acquire textually precedes the inner-lock acquire) and at runtime (`fcntl.flock` instrumentation proving a strict nested `acquire, acquire, release, release` event sequence for one `enroll_signer` call — a release/reacquire would instead produce `acquire, release, acquire, release`). A 6-thread concurrent-`enroll_signer` test against the identical `signer_key_id` converges on exactly one `ENROLLED` outcome with the rest `ALREADY_ENROLLED`, never a corrupted registry.

Cross-registry invariant (HPSE-REQ-056/HHI-5/HPI-7): `enroll_signer` re-reads `hardware-credentials.json` for an `active` record matching `signer_key_id` and `provider_profile` immediately before writing, and again immediately after (post-write re-verification), both under the still-held lock pair. No active `SignerRecord` can be produced through this writer without a corresponding durable, active `HardwareCredentialRecord`.

`enroll_signer` never accepts a caller-supplied `signer_key_id` — it is exactly the value the caller already obtained from Surface A's `enroll_credential()` and already registered via Surface B.

Idempotency/conflict/revocation follow the identical `hatp_deployment_binding_admin.py`-derived discipline (idempotent-preserve on exact match, fail-closed on differing/revoked, monotonic revocation, never cascades to the hardware credential).

## 7. Surface D — `PrincipalRecord.revoked_at`

`hatp_bootstrap.py`: `PrincipalRecord` widened with `revoked_at: Optional[str] = None`; `_parse_principal`'s allowed-field set widened to `{"principal_id", "status", "revoked_at"}`; `_require_revoked_at_consistency` now applied. Backward compatible for existing `active` records with no `revoked_at` key. **Not** backward compatible for a `revoked` record with no `revoked_at` key — that shape is now (correctly) malformed; two historical test fixtures that hand-authored a revoked-without-`revoked_at` principal were updated to supply `revoked_at`.

## 8. Surface E — `DeploymentBinding` producer cross-validation

`hatp_deployment_binding_admin.py`: `AuthorityEvidence.provider_profile` **removed** (breaking change, accepted because `DeploymentBinding: ABSENT` — no real binding has ever existed). New `_resolve_and_validate_authority()`, shared identically by `create_deployment_binding`, `rotate_deployment_binding`, and both preview functions: validates `authority_scope` against HBDC-001 v1.2's closed vocabulary (`CLASS_B_DEPLOYMENT`, the sole member); resolves `principal_id` (must exist, active) and `signer_key_id` (must exist, active, `principal_id` match) via `registry.json` (reusing this module's own existing raw-document read path, not a raw `HATPTrustStore(...)` construction — an existing enforced convention); resolves the hardware credential (must exist, active) via `HATPHardwareCredentialStore`; cross-checks `SignerRecord.provider_profile == HardwareCredentialRecord.provider_profile`; derives `provider_profile` from the resolved signer (HPSE-REQ-048), never from caller input. New typed errors: `InvalidAuthorityScopeError`, `AuthorityPrincipalNotFoundError`, `AuthorityPrincipalRevokedError`, `AuthoritySignerNotFoundError`, `AuthoritySignerRevokedError`, `AuthoritySignerPrincipalMismatchError`, `AuthorityHardwareCredentialNotRegisteredError`, `AuthorityProviderProfileMismatchError`.

`scripts/hatp_deployment_binding_admin.py` (the standalone admin CLI): `--provider-profile` flag removed; `_authority_from_args` updated to match.

## 9. Proof-verification regression

`human_approval_trusted_provenance.py::verify_hatp_proof` is byte-unchanged. New end-to-end tests build real enrolled state (credential registered → principal enrolled → signer enrolled → `DeploymentBinding` created, all via this phase's own writers) and confirm the producer correctly rejects a missing principal and a revoked signer, and correctly accepts a fully valid chain — proving the new writers' output is consumable by the existing, unmodified verification/producer paths with no regression.

## 10. Six-case partial-failure matrix (HPSE-REQ-058)

- **(A) Credential write fails** — `enroll_signer` never begins its own write attempt until the precondition check already observed a durable active credential; a failed credential write never reaches the signer-write step.
- **(B) Credential write succeeds, signer write fails** — the credential record remains durable, inert (`test_enroll_signer_without_registered_credential_fails_closed_HPSE_REQ_056` and the idempotency test together demonstrate re-entry safety: a retried `enroll_signer` re-checks the precondition, still satisfied, and proceeds).
- **(C) Signer write succeeds, credential missing** — structurally unreachable through this writer (proven by the continuous-lock test above; the precondition is re-checked inside the same held lock pair immediately before the write).
- **(D) Audit fails after durable write(s)** — propagates uncaught (disclosed, matches HPSE-REQ-039/`hatp_deployment_binding_admin.py`'s own precedent; not resolved here).
- **(E) Read-back mismatch** — each write is independently read-back-verified before the next dependent step proceeds (`_read_back_and_verify_credential`, `_read_back_signer`).
- **(F) Concurrent enrollment** — prevented by the fixed lock ordering; the 6-thread concurrency test demonstrates convergence on exactly one durable outcome.

## 11. Idempotency and audit

Every mutating operation (register/revoke credential, enroll/revoke principal, enroll/revoke signer), including every idempotent no-op, emits exactly one `pcae.core.provenance.append_provenance_event` record with a distinct, separately-attributable `event_type` (`hardware_credential_registered`/`_register_noop`, `hardware_credential_revoked`/`_revoke_noop`, `principal_enrolled`/`_enroll_noop`, `principal_revoked`/`_revoke_noop`, `signer_enrolled`/`_enroll_noop`, `signer_revoked`/`_revoke_noop`). Audit ordering: validate → mutate under lock → read back → emit audit → return. An audit-emission failure after a successful, read-back-verified write propagates uncaught rather than reporting false success or silently swallowing the failure — the disclosed, known limitation this codebase already carries for composing independently-atomic storage systems without two-phase commit.

## 12. Revocation

Hardware-credential revocation fails closed at live verification time regardless of whether the referencing `SignerRecord` was separately revoked (HHCE-REQ-042/044, reconfirmed against a real registry entry produced by this phase's own writer, not a hand-authored fixture). No automatic cascade in either direction (HHCE-REQ-043, HPSE-REQ-049/069's existing disposition) — verification-time re-checking is the security-relevant checkpoint, not producer-time cascade.

## 13. Error vocabulary

Both new writer modules root their errors at a distinct hierarchy (`HATPHardwareCredentialAdminError`, `HATPPrincipalSignerAdminError`) — no bare `ValueError` for a normative failure condition. Covers: provider/credential-identity unavailable, duplicate/conflicting credential or signer, revoked credential/principal/signer, missing principal/signer/credential, signer/principal mismatch, provider-profile mismatch (both at Surface C's enrollment boundary and Surface E's `DeploymentBinding` boundary), invalid scope, lock/write/read-back failures.

## 14. Security / adversarial coverage

Symlinked store root (both hardware-credential and trust-store roots), symlinked lock file, malformed/duplicate-key registry documents, non-dict credential entries, unknown top-level/per-record fields, credential-ID/signer-ID collision, provider-profile mismatch, revoked-entry reuse, concurrent writers (6-thread and, in the pre-existing `DeploymentBinding` suite, 6-OS-process tests), lock-inversion structural proof, credential disappearance/revocation mid-lifecycle, partial write (interrupted `os.replace`), replay (idempotency), audit failure after durable write. All covered by `tests/test_hatp_trust_enrollment_capability.py` (46 tests) plus the updated `tests/test_hatp_deployment_binding_admin.py` (54 tests).

## 15. Runtime neutrality / non-agent-reachability

Both new modules grep-confirmed to reference no runtime-adapter identifier (`claude`/`codex`/`deepseek`/`anthropic`/`openai`). Neither is imported by `cli.py` or `core/agent.py`. `provider_profile`/`protocol_name` continue to name hardware security-property classes only.

## 16. Test lanes and results

- **Focused (Lane 1):** `tests/test_hatp_trust_enrollment_capability.py` — 46/46 passed. `tests/test_hatp_deployment_binding_admin.py` (rewritten for Surface E's mandatory prerequisites) — 54/54 passed.
- **Affected regression (Lane 2):** full `-k hatp` sweep (`tests/ -k hatp`) and full `-m fast_green -n auto` sweep, each diffed node-for-node against an isolated phase-entry worktree baseline (`git worktree add` at commit `d11b8cd0`, not `git stash`, per this repo's own test-isolation discipline).
  - `-k hatp`: baseline 186 failed/2 errors → after-fix 190 failed/2 errors, all 4 net-new failures individually confirmed as the expected byte-identity/no-production-source-modified family.
  - `-m fast_green -n auto`: baseline 292 failed → after-fix 327 failed, 35 net-new. Every net-new failure individually inspected: the overwhelming majority are the same expected byte-identity/no-src-pcae-changed family (inevitable consequence of touching HMIC-bound files — `hatp_bootstrap.py`, `hatp_fido2_provider.py`, `hatp_hardware_credentials.py`, `hatp_deployment_binding_admin.py`); `test_parse_principal_allowed_fields_excludes_revoked_at` (×2) correctly asserts the OLD disclosed-gap state Surface D intentionally closes; `test_finding_7l_2_hmic_depends_header_now_matches_hbdc` and `test_scratch_tree_reproduces_the_live_repository_digest` independently reproduced as failing on the CLEAN baseline worktree too (pre-existing, unrelated to this phase); `test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli` passes in isolation (confirmed `-n auto`-only flake, unrelated).
  - Genuine regressions found and fixed during this phase (not left as "expected"): two AST/textual "producer imported nowhere but itself" enforcement tests updated to name the new, contract-required legitimate importer; one raw-constructor-convention test's violation fixed in production code (Surface E's validator no longer constructs `HATPTrustStore(_test_only_root=...)` directly, reusing the raw-document read path instead); two verification-engine tests' hand-authored revoked-principal fixtures updated for Surface D; two Wave-5 "disclosed, not repaired" finding tests rewritten to assert the now-CLOSED behavior; the admin CLI script (`scripts/hatp_deployment_binding_admin.py`) updated for the `AuthorityEvidence` signature change.
- **Fast Green:** `python -m pytest -m fast_green -n auto` — 8,433 passed (8,111 baseline-equivalent + 322 delta from this phase's own new/updated tests), 327 failed (all individually explained above), 4 skipped, 9 errors (pre-existing, HMIC digest-fixture-count tests unrelated to this phase).
- **Full serial suite:** not run — Lane 3's "only if unexplained failures remain" condition was not met; every failure above was individually explained against primary source, not merely asserted.

## 17. HMIC transitive source-scope consequence (named, not performed)

Per the governing prompt §39, a future HMIC-001 source-scope analysis MUST include, before any positive authority consumption from these surfaces: `hatp_fido2_provider.py` (already HMIC-bound — this phase's change mechanically triggers re-certification); `hatp_hardware_credential_admin.py` (new, not yet bound); `hatp_principal_signer_admin.py` (new, not yet bound); `hatp_bootstrap.py` (already HMIC-bound); `hatp_hardware_credentials.py` (schema widened this phase — verify current binding status); `hatp_deployment_binding_admin.py` (already HMIC-bound); `scripts/hatp_deployment_binding_admin.py` (already bound/named). This phase performs no HMIC-001 amendment. Positive authority consumption from these surfaces remains prohibited until HMIC alignment is independently completed.

## 18. Public-first / no-mutation confirmation

All production source, contracts, and tests remain public. No private key, PIN, bearer token, or real credential secret committed — every fixture uses synthetic hex strings and test-only in-memory ECDSA keys. `hac-dell` untouched. No real FIDO2 credential provisioned. No human operator enrolled. No real Protected Root state written (all tests use disposable `tmp_path` roots via `_store_root`/`_protected_root`/`_hardware_store_root` test-only overrides). No real `DeploymentBinding` created. Runtime remains Observed/observe/unavailable — implementation existence is not execution availability.

## 19. Limitations / deferred

- PIV: still an unconditional placeholder, deliberately deferred (no primary-architecture finding required it this phase).
- Audit-after-durable-write remains a disclosed, unresolved limitation (no two-phase commit).
- `CROSS_REGISTRY_MISMATCH` (HHCE-001's reserved error) remains unraised by any operation this phase implements — the underlying condition is structurally unreachable through these writers, per HHCE-REQ-037.
- HMIC-001 source-scope alignment for the two new modules is named, not performed (§17).

## 20. Final verdict

**HATP TRUST-ENROLLMENT IMPLEMENTATION COMPLETE — INDEPENDENT VERIFICATION PENDING.**

## 21. Recommended next phase

**149O.20L.7O.2F.1 — HATP Trust-Enrollment Implementation Capability Independent Verification.** Not performed by this phase.
