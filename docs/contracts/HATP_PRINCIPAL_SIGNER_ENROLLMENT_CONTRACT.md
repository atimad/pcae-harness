# HATP Principal/Signer Enrollment Contract

## Contract identity and status

**Contract:** HPSE-001
**Version:** 1.0
**Status:** FROZEN — PENDING INDEPENDENT VERIFICATION (architecture-only; not yet independently verified; recommended next phase 149O.20L.7O.2D.1)
**Frozen by:** Phase 149O.20L.7O.2D — HATP Principal/Signer Enrollment Contract Architecture
**Depends on:** HATP-001 v1.0 (`HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`, unamended — HATP-REQ-014/019-022/028/036-041 are this contract's own primary source), HBDC-001 v1.2 (`HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` — this contract shares its Protected Root and `registry.json` document, and its own §16.2 amendment governs `DeploymentBinding.authority_scope`, a field this contract does not touch), HMIC-001 v1.4 (unamended by this contract; §19 below names required future binding)
**Architecture basis:** `docs/PHASE_149O_20L_7O_2C_DEPLOYMENTBINDING_FIRST_USE_FIELD_RESOLUTION_ARCHITECTURE.md` (149O.20L.7O.2C, §6-§9, §20 — the field-resolution investigation that first proved `principal_id`/`signer_key_id`/`provider_profile` converge on one missing enrollment artifact); `docs/PHASE_149O_20L_7O_2D_HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT_ARCHITECTURE.md` (this phase's own report — full primary-source re-derivation, rejected alternatives, and rationale for every requirement below).

This is a contract-freeze document. It formalizes HATP-REQ-036/037's conceptual enrollment procedure into concrete, testable requirements for a Principal/Signer enrollment writer. It is not an implementation, creates no real protected state, authorizes no real enrollment, provisioning, election, or certification, and does not modify `hatp_bootstrap.py`, `hatp_deployment_binding_admin.py`, or any other production module byte-for-byte.

---

## 0. Normative Language

The key words "SHALL", "SHALL NOT", "MUST", "MUST NOT", "MAY", and "SHOULD" are to be interpreted per RFC 2119 conventions used throughout this repository's other bound contracts. Every normative sentence carries a unique requirement ID, `HPSE-REQ-###`, sequential from 001, no gaps, no duplicates (§20). This contract's own numbering namespace is independent of `HATP-REQ-*`/`HBDC-REQ-*`/`HMIC-REQ-*`/`HSCE-REQ-*`, mirroring HSCE-001's own precedent of a separate namespace for a companion contract.

## 1. Purpose

`hatp_bootstrap.py` already defines `PrincipalRecord` and `SignerRecord` (Wave 2, 149O.1E) as read-only lookup targets, and `hatp_signing_ceremony.py::_resolve_signer` already *consumes* enrolled signer records for the signing-ceremony proof path. No writer has ever existed to populate either registry section — HATP-REQ-036/037 describe the enrollment procedure only in prose. Phase 149O.20L.7O.2C independently proved that three of the four unresolved `DeploymentBinding` first-use fields (`principal_id`, `signer_key_id`, `provider_profile`) converge on exactly this one missing artifact. This contract answers, in testable terms: what does `principal_id` and `signer_key_id` mean, what is the enrollment writer's exact operation/error/atomicity/audit contract, and what must change elsewhere (`hatp_bootstrap.py`, `hatp_deployment_binding_admin.py`, HMIC-001) before a real enrollment, and a real `DeploymentBinding` built on it, may exist.

## 2. Scope and Relationship to Other Contracts

HPSE-001 governs the `principals` and `signers` sections of the existing `registry.json` document (`hatp_bootstrap.PrincipalRecord`/`SignerRecord`) exclusively. It does **not** govern:

- `AuthorityRecord`/`authorities` (the AG3/AG5 rollback-authority registry section) — untouched, unamended.
- `DeploymentBinding`/`deployment_bindings` or `authority_scope` — HBDC-001's exclusive scope (§16, §16.1, §16.2).
- The Wave-5 `hardware-credentials.json` cryptographic registry (`hatp_hardware_credentials.py`) — a separate, sibling protected artifact this contract references but does not amend.
- HATP proof production/verification, human presence, or hardware attestation — HATP-001's model, unchanged.

This contract is additive to HATP-001 and HBDC-001; it amends neither, and neither requires amendment to be consumed by this contract, mirroring HSCE-001's own "additive, not amending" relationship to HATP-001/RAE-001.

## 3. Terminology

- **Enrolled human approver / principal.** A human identified by a `principal_id` per HATP-REQ-014 — categorically distinct from any OS account, including the Agent OS principal and the Human/Admin OS principal (HATP-REQ-028's own two-principal topology names *OS* principals; `principal_id` names a *registry* identity layered on top, never collapsed into either).
- **Signer / signing credential.** A hardware credential identified by `signer_key_id`, enrolled under exactly one `principal_id` and one `provider_profile`.
- **Enrollment.** The act of writing a new, or revoking an existing, `PrincipalRecord`/`SignerRecord` via this contract's writer. Enrollment establishes who may approve (HATP-REQ-038); it does not itself approve anything.
- **Admin execution principal.** The Class-B Protected Administrator OS principal (HBDC-REQ-066) who runs the writer — a role, not necessarily distinct from the enrolled human principal as a physical person, but distinct as a matter of this contract's own discipline (§13).

## 4. `principal_id` Semantics

- **HPSE-REQ-001.** `principal_id` denotes an enrolled human approver (HATP-REQ-014), restated normatively for this writer: it is never an OS account identifier, never the Agent OS principal, never a process/runtime identity, and never a bare human-readable display name.
- **HPSE-REQ-002.** `principal_id` SHALL be assigned by the Human/Admin bootstrap authority at enrollment time (HATP-REQ-037). It SHALL NOT be derived from, and SHALL NOT be required to equal, any OS-level username, UID, GECOS field, or process identity of the host it is enrolled on — this closes, as a normative rule rather than a one-time proof, the exact gap 149O.20L.7O.2C's §6 independently demonstrated by disproving `principal_id == "pcae"`.
- **HPSE-REQ-003.** `principal_id` grammar is exactly the existing schema's non-empty-string constraint (`hatp_bootstrap._require_nonempty_str`); this contract adds no new grammar. Global uniqueness within `registry.json` is required and is already mechanically enforced (`_parse_registry_document`'s duplicate-key rejection) — this contract adds no new uniqueness rule, only requires that the existing one continue to apply.
- **HPSE-REQ-004.** `principal_id` SHALL NOT change across signer-key rotation or revocation (HATP-REQ-014).
- **HPSE-REQ-005.** Principal lifecycle is exactly the existing two-value `{"active", "revoked"}` vocabulary (`hatp_bootstrap._STATUS_VALUES`); no third state is introduced.
- **HPSE-REQ-006.** Principal revocation is monotonic: the first-recorded revocation's audit evidence (§16) is authoritative; a later revocation of an already-revoked principal is an idempotent no-op that does not alter the originally recorded revocation evidence, mirroring `revoke_deployment_binding`'s "first-recorded revocation always wins" discipline exactly.

## 5. `PrincipalRecord` Schema

- **HPSE-REQ-007.** `PrincipalRecord`'s schema (`principal_id: str`, `status: str`) — already defined by `hatp_bootstrap.py`, unchanged since Wave 2 — is sufficient for this contract's v1.0 enrollment writer and is not widened by this contract. No new field (`schema_version`, `principal_type`, `display metadata`, `enrolled_at`, `enrollment_reference`, or signer linkage) is added: `registry_version` already exists at the document level (not per-record); `principal_type` has no source-supported second value under the frozen two-principal, human-approver-only topology (HATP-REQ-028); display/reference metadata is deliberately excluded to keep personally identifying data minimal (§37 of the governing prompt); `enrolled_at`/`enrollment_reference` are instead carried as audit-event metadata only (§16), exactly mirroring `AuthorityEvidence.election_reference`'s existing HBDC-REQ-065 disposition; signer linkage is the *inverse* direction already captured by `SignerRecord.principal_id` and needs no duplicate forward field.
- **HPSE-REQ-008 (disclosed schema-symmetry gap).** Unlike `SignerRecord`/`AuthorityRecord`/`DeploymentBinding`, `PrincipalRecord` today has **no `revoked_at` field at all** — `_parse_principal`'s allowed-field set is exactly `{"principal_id", "status"}`, and no `_require_revoked_at_consistency` call exists for it. A future implementation phase SHALL widen `PrincipalRecord` to add an optional `revoked_at: Optional[str] = None` field, with the identical `_require_revoked_at_consistency` discipline `SignerRecord`/`AuthorityRecord`/`DeploymentBinding` already use, before `revoke_principal` (§16) may be implemented as a production writer operation. This is a prerequisite `hatp_bootstrap.py` schema amendment — a file already bound into HMIC-001's frozen `implementation_scope_digest` set (`_FROZEN_SRC_PCAE_RELATIVE_FILES`) — and is therefore explicitly out of scope for this architecture-only phase; it SHALL be completed, and independently verified, before this contract's `revoke_principal` operation is implemented. Until then, a principal's revocation timestamp is authoritative only in the audit trail (§16), not in the registry record itself — a disclosed, intentional limitation, not an oversight.

## 6. `signer_key_id` Semantics

- **HPSE-REQ-009.** `signer_key_id` denotes a canonical enrolled signing-credential identity (HATP-REQ-019(d)). It is never a GitHub deploy key, an SSH host key, an arbitrary GPG key, the current PCAE agent runtime's identity, or an OS account identity — mirroring 149O.20L.7O.2C's own §8 non-equivalence proof, restated here as a standing rule rather than a one-time finding.
- **HPSE-REQ-010.** `signer_key_id` SHALL be obtained via the enrolling hardware provider's own `credential_identity()` method, called live during the enrollment ceremony (`HATPHardwareSigner.credential_identity()`, `hatp_providers.py`) — the identical provider-identity-exchange mechanism `hatp_signing_ceremony.py::_resolve_signer` already uses for the *verification* side, applied here to *enrollment*. `signer_key_id` is never independently invented, never human-typed, and never accepted as free-form caller input to the enrollment writer.
- **HPSE-REQ-011.** `signer_key_id` SHALL be durably recorded at enrollment time. A conformant provider implementation MAY be unable to re-derive it from the physical device alone at a later time — `hatp_fido2_provider.py`'s own current `credential_identity()` implementation already documents exactly this for a non-resident FIDO2 credential ("established at enrollment time... and is not re-derivable from the device alone"). `signer_key_id` is therefore enrollment-ceremony *output*, captured once and persisted, never a pure function of live device state computable on demand at arbitrary later times.
- **HPSE-REQ-012.** `signer_key_id` SHALL be encoded as lowercase hexadecimal of the provider's raw credential-identity bytes — identical to `hardware-credentials.json`'s own existing `public_key_hex` encoding convention (`hatp_hardware_credentials.py::_parse_credential`). No new encoding is invented.

## 7. `SignerRecord` Schema

- **HPSE-REQ-013.** `SignerRecord`'s schema (`signer_key_id`, `principal_id`, `provider_profile`, `status`, `revoked_at`) — already defined by `hatp_bootstrap.py`, already symmetric with `DeploymentBinding`/`AuthorityRecord`'s revocation-timestamp discipline — is unchanged by this contract at v1.0.
- **HPSE-REQ-014.** `SignerRecord` SHALL carry no private-key material, PIN, or secret device state, mirroring `HardwareCredentialRecord`'s own existing discipline (`hatp_hardware_credentials.py` §"item 73") exactly.

## 8. Principal ↔ Signer Relationship

- **HPSE-REQ-015.** Cardinality is exactly one principal → zero or more signers; each `SignerRecord` names exactly one `principal_id` (already structurally guaranteed by the existing single-valued field).
- **HPSE-REQ-016.** Signer rotation (replacing a principal's credential with a new physical device) SHALL be modeled as two separate writer operations — `enroll_signer` for the new credential (new `signer_key_id`, same `principal_id`) followed by `revoke_signer` for the old one — never a single in-place field overwrite of an existing `signer_key_id` record. This deliberately departs from `rotate_deployment_binding`'s in-place-overwrite model: `signer_key_id` is itself the credential's stable identity (HPSE-REQ-009), and overwriting it in place would silently reassign what a still-referenced record's primary key denotes, which `DeploymentBinding`'s own idempotency/rotation model never has to worry about (its `repository_id` never changes under rotation).
- **HPSE-REQ-017.** A principal MAY have more than one concurrently active signer (e.g. during an overlapping rotation window); this contract does not require a single-active-signer-per-principal invariant.

## 9. `provider_profile` Semantics and Vocabulary

- **HPSE-REQ-018.** `HATP_HARDWARE_PROVIDER_V1` is affirmed as the sole `provider_profile` vocabulary value, exactly as already fixed by `hatp_providers.py::_PRODUCTION_HARDWARE_PROVIDER_PROFILES` (a closed one-member tuple). No new value is introduced by this contract.
- **HPSE-REQ-019.** `provider_profile` is fixed, compile-time contract vocabulary, not a runtime-configurable or registry-backed value. A future new protocol requires its own contract-version amendment explicitly naming it (mirrors HATP-REQ-020's own "no protocol interchangeability without proof" discipline) — never a pluggable or dynamically-registered profile list. A plugin-style provider registry is deliberately not designed here: with exactly one closed value and an existing amendment-gated extension mechanism, a runtime registry would add indirection without adding capability.
- **HPSE-REQ-020.** `SignerRecord.provider_profile` SHALL be captured from the enrolling provider's own `capabilities().provider_profile` field (`HardwareProviderCapabilities.provider_profile`, `hatp_providers.py`) at enrollment time, and validated against the closed allowlist (`_PRODUCTION_HARDWARE_PROVIDER_PROFILES`) before the write. Enrollment against a provider outside the allowlist fails closed (`UnsupportedProviderProfileError`).

## 10. Registry Architecture

- **HPSE-REQ-021.** The Principal/Signer enrollment writer operates on the identical `registry.json` document, `principals`/`signers` sections, already defined and parsed by `hatp_bootstrap.py`. No new registry file or document is introduced.
- **HPSE-REQ-022.** `principal_id` and `signer_key_id` are each globally unique within `registry.json` — already mechanically enforced by `_parse_registry_document`'s existing duplicate-key rejection; this contract adds no new uniqueness rule.
- **HPSE-REQ-023.** Every registry write SHALL preserve every other top-level section (`deployment_bindings`, `authorities`, and whichever of `principals`/`signers` is not the target of the current write) byte-for-byte unchanged except the one record being enrolled or revoked — mirroring `_registry_document_with_binding`'s existing discipline exactly.
- **HPSE-REQ-024.** List entries SHALL be sorted by their key field (`principal_id` for `principals`, `signer_key_id` for `signers`) on every write, mirroring the existing `deployment_bindings` sort-by-`repository_id` discipline, for deterministic byte-identical serialization.
- **HPSE-REQ-025.** Unknown fields and malformed documents SHALL be rejected exactly as already implemented by `_parse_principal`/`_parse_signer`/`_parse_registry_document` — no relaxation of the existing closed-schema discipline.

## 11. Enrollment Writer Contract

- **HPSE-REQ-026.** The writer SHALL expose exactly these mutating operations: `enroll_principal`, `revoke_principal`, `enroll_signer`, `revoke_signer` — plus read-only preview variants for each (§12). No `rotate_principal` operation exists (`principal_id` never rotates, HPSE-REQ-004); no single-call `rotate_signer` operation exists (HPSE-REQ-016).
- **HPSE-REQ-027.** `enroll_signer` SHALL require an existing, `active` `PrincipalRecord` for the supplied `principal_id`. Enrolling a signer against a missing or `revoked` principal fails closed.
- **HPSE-REQ-028.** The writer SHALL be a separate, non-agent-writable admin tool — never a subcommand of the ordinary agent-reachable `pcae` CLI, mirroring HBDC-REQ-056 exactly.
- **HPSE-REQ-029.** The writer SHALL be invocable only by the admin OS principal, out of band from any PCAE-agent-invoked code path — never agent-invocable, directly or indirectly, mirroring HBDC-REQ-066 exactly.

## 12. Preview Semantics

- **HPSE-REQ-030.** Every mutating operation SHALL have a corresponding read-only preview variant (`preview_enroll_principal`, `preview_enroll_signer`, `preview_revoke_principal`, `preview_revoke_signer`) that never writes, mirroring `preview_create_deployment_binding`'s exact discipline ("never writes," `hatp_deployment_binding_admin.py:828-833`). Preview SHALL classify would-enroll / already-enrolled (idempotent) / conflict / would-revoke / already-revoked / not-found outcomes, mirroring `DeploymentBindingPreviewKind`'s existing enum shape.

## 13. Atomicity and Locking

- **HPSE-REQ-031.** Registry writes SHALL reuse `repository_identity.py::_write_atomic`'s exact idiom (`mkstemp` in the same directory, `fsync`, `os.replace`, symlink rejection before and after the write race window) — identical to `hatp_deployment_binding_admin.py`'s own reuse of that idiom. No new idiom is invented.
- **HPSE-REQ-032.** Every write SHALL be read back from disk and verified byte-for-byte against the intended record before the operation reports success, mirroring `_read_back_and_verify` exactly — never reporting success on a rename alone.
- **HPSE-REQ-033.** The Principal/Signer enrollment writer and the `DeploymentBinding` writer SHALL acquire the identical, single, whole-registry-document transition lock — the existing fixed `.deployment-binding-transition.lock` path directly under the Protected Root — not a second, section-scoped lock of its own. Both writers mutate the same `registry.json` document; a second, independently-named lock would permit two concurrent writer processes to race on the same underlying file (a split-brain registry write), defeating the very TOCTOU discipline `hatp_deployment_binding_admin.py`'s own module docstring already establishes for its own writes. This requires no change to `hatp_deployment_binding_admin.py` itself — both modules simply reference the identical fixed lock-file-name constant as "the one whole-registry-document transition lock," a shared convention, not a new mechanism.

## 14. Error Vocabulary

- **HPSE-REQ-034.** The writer SHALL raise a distinct, closed exception hierarchy rooted at `HATPPrincipalSignerAdminError`, distinguishing at minimum: principal not found, signer not found, duplicate principal, duplicate signer, signer/principal mismatch, unsupported provider profile, revoked principal, revoked signer, malformed registry (reusing the existing `HATPTrustStoreMalformedError`, not reinvented), and read-back mismatch. No outcome in this list SHALL be represented by a bare `ValueError` or other untyped exception.

## 15. Fail-Closed Behavior

- **HPSE-REQ-035.** An absent `registry.json` SHALL be treated as EMPTY (zero enrolled principals/signers), not as an error — mirroring the existing `_load_raw_registry_document`/`HATPTrustStore._load_registry` convention (`None` return, not an exception) exactly.
- **HPSE-REQ-036.** A malformed `registry.json` SHALL be treated as INVALID and fail closed on every operation that would need to read it — never partially accepted, never silently treated as empty.
- **HPSE-REQ-037.** Enrollment against a missing or revoked principal, or a duplicate `principal_id`/`signer_key_id`, SHALL fail closed with the specific typed error named in HPSE-REQ-034 — never silently coerced into a different outcome (e.g. never silently treated as an idempotent success when the candidate record actually differs).

## 16. Audit Discipline

- **HPSE-REQ-038.** Every writer operation, including idempotent no-ops, SHALL emit exactly one `pcae.core.provenance.append_provenance_event` record against the target repository's own tree, mirroring HBDC-REQ-062 exactly. `enrolled_at`/`enrollment_reference`/`election_reference` (HPSE-REQ-007's own disposition) are carried as audit-event metadata, not as registry-record fields.
- **HPSE-REQ-039.** Audit ordering SHALL be: validate → mutate the registry atomically under the shared lock (HPSE-REQ-033) → read back and verify → emit audit record → return. An audit-emission failure occurring *after* a successful, read-back-verified write SHALL propagate uncaught rather than being silently swallowed. This is a disclosed, known limitation shared identically with `hatp_deployment_binding_admin.py` (composing two independently atomic storage systems without a real two-phase commit) — not resolved by this contract. A future reconciliation-scan tool, not built here, is the only mitigation available short of inventing a new transactional mechanism this architecture-only phase does not introduce; the alternative ordering (audit-before-state) was considered and rejected because it merely relocates the same fundamental risk to the opposite failure mode (an audit record claiming an enrollment that never durably wrote), without closing it.

## 17. Enrollment Authority

- **HPSE-REQ-040.** Three roles SHALL remain distinct and SHALL NOT be collapsed, even when the same physical person occupies all three under the frozen two-principal v1 topology (HATP-REQ-028): the human decision authority (who elects/authorizes the enrollment), the admin execution principal (who runs the writer under the Class-B Protected Administrator OS principal), and the enrolled human principal (the subject of the resulting `principal_id`).
- **HPSE-REQ-041.** No operation permits an entity to enroll or expand its own signing authority without the same fresh-election evidence required to enroll any other principal — this extends HATP-REQ-040's self-enrollment prohibition explicitly to the admin's own enrollment case; the admin enrolling themselves as `principal_id` is not exempt from HPSE-REQ-042.

## 18. Election / CHGR Requirements

- **HPSE-REQ-042.** `enroll_principal`, `enroll_signer`, `revoke_principal`, and `revoke_signer` SHALL each require explicit evidence of a fresh, separate human election authorizing that specific enrollment/revocation, exactly mirroring HBDC-REQ-064. An unverified boolean or free-form "approved" string is never sufficient authority.
- **HPSE-REQ-043.** The election-evidence reference SHALL be recorded as audit metadata only, exactly mirroring HBDC-REQ-065 — never cryptographically verified by this writer.

## 19. Hardware Credential Requirement and Provisioning Sequence

- **HPSE-REQ-044.** The first production `enroll_signer` operation SHALL require a live, hardware-backed credential satisfying `HATP_HARDWARE_PROVIDER_V1` (HATP-REQ-019/021). No software-key substitution is permitted absent a future contract version/profile explicitly naming one. This contract does not weaken HATP-REQ-021 merely to allow enrollment progress on a host currently lacking compliant hardware (149O.20L.7O.2C §7/§16 independently confirmed no FIDO2/PIV device is present on the target Dell host today).
- **HPSE-REQ-045.** Credential provisioning (making a compliant physical device usable on the target host) is a distinct, prerequisite step to signer enrollment, outside this contract's own scope. `enroll_signer` fails closed (`UnsupportedProviderProfileError`/the provider's own `HATPProviderUnavailableError`) when no compliant device is present, exactly as the current FIDO2 (`hatp_fido2_provider.py::credential_identity`) and PIV (`hatp_piv_provider.py`, an unconditional placeholder) implementations already do.
- **HPSE-REQ-046.** The first-use sequence is: (1) physical credential provisioning; (2) principal enrollment; (3) signer enrollment, bound to the enrolled principal; (4) independent verification of the resulting registry state; (5) `DeploymentBinding` proposition referencing the enrolled `principal_id`/`signer_key_id`; (6) election + CHGR for the `DeploymentBinding` itself (HBDC-REQ-064 — a separate election from HPSE-REQ-042's own enrollment elections); (7) `DeploymentBinding` creation; (8) independent real-host verification. No step may be skipped or reordered.

## 20. Requirement Inventory

**Requirement count:** HPSE-001 v1.0 defines **52** requirements, `HPSE-REQ-001` through `HPSE-REQ-052` inclusive, sequential, no gaps, no duplicates (§21-§26 continue the numbering below).

## 21. `DeploymentBinding` Producer Amendment (Named for a Future Phase, Not Implemented Here)

- **HPSE-REQ-047.** A future HBDC-001 amendment SHALL require `create_deployment_binding`/`rotate_deployment_binding` to cross-validate the supplied `principal_id` and `signer_key_id` against the Principal/Signer registry this contract establishes: both records SHALL exist and be `active`, the signer's `principal_id` SHALL equal the supplied `principal_id`, and `provider_profile` SHALL be derived from the enrolled signer's own registry value rather than accepted as independent, potentially-mismatched caller input (§22 below). This requirement names required future contract text; it does not create or alter `hatp_deployment_binding_admin.py` or HBDC-001 §16.1 itself.

## 22. `provider_profile` Derivation for `DeploymentBinding`

- **HPSE-REQ-048.** A future `DeploymentBinding` producer amendment SHALL derive `provider_profile` from the referenced `signer_key_id`'s own `SignerRecord.provider_profile`, not accept it as independent `AuthorityEvidence` input that could silently mismatch the enrolled signer's true provider — closing the caller-supplied-mismatch risk 149O.20L.7O.2C's §9 named as the sole remaining gap for this field.

## 23. Revocation Cascading (Disclosed Gap, HBDC-001 Scope)

- **HPSE-REQ-049.** Revoking a `PrincipalRecord` or `SignerRecord` SHALL NOT automatically alter any already-created `DeploymentBinding` that copied the now-revoked `principal_id`/`signer_key_id` at creation time — `DeploymentBinding` stores field *copies*, not live references (§4 of the architecture report). Closing this gap, if desired, is a future HBDC-001 conformance-check amendment (extending HBDC-REQ-042 to cross-check live principal/signer status) — a decision this contract does not make and does not require, and which HPSE-001 has no authority to make since it does not govern `DeploymentBinding` or HBDC-REQ-042.
- **HPSE-REQ-050.** `_resolve_signer` (`hatp_signing_ceremony.py`) checks only `SignerRecord.status`, never the referenced principal's own status, when resolving a signer for *proof production*. `human_approval_trusted_provenance.py`'s proof *verification* path does separately check `PrincipalRecord.status` (via `trust_store.lookup_principal`). This is an intentional, already-existing asymmetry, not a defect this contract introduces or is required to close: production can succeed against a revoked principal's still-active signer, but the resulting proof fails at the verification boundary, which is the security-relevant checkpoint (HATP-REQ-016-018's fresh-presence-then-verify model).

## 24. Runtime / Provider Separation

- **HPSE-REQ-051.** `provider_profile` denotes the signing-hardware security-property class only (HATP-REQ-019(a)-(e)); it SHALL NOT be interpreted as, derived from, or coupled to the identity of any PCAE agent runtime (Claude, Codex, DeepSeek Harness, or any future runtime adapter). The Principal/Signer enrollment writer SHALL remain reachable only via a standalone, non-agent-invocable script (mirrors HPSE-REQ-028/029), never through any runtime-adapter code path.

## 25. Timestamp Semantics

- **HPSE-REQ-052.** Every timestamp this contract's writer produces (`SignerRecord.revoked_at` today; `PrincipalRecord.revoked_at` once HPSE-REQ-008's schema widening lands) SHALL use the identical strict grammar already fixed by HBDC-REQ-067 (`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$`) — no new grammar is invented.

## 26. HMIC Source-Scope Consequence (Future, Not Performed Here)

This contract's own future implementation module and companion script are, by their authority-bearing nature, expected candidates for HMIC-001's frozen `implementation_scope_digest` file set — mirroring the exact precedent `hatp_deployment_binding_admin.py` set at HMIC-001 v1.4 (Phase 149O.20L.7K, limb (c)'s widened third anchor). This section names that expectation; it performs no HMIC-001 amendment.

## 27. Security Invariants (HPI-1 .. HPI-6)

- **HPI-1.** No production, agent-reachable API exposes `enroll_principal`/`enroll_signer`/`revoke_principal`/`revoke_signer` (HPSE-REQ-028/029).
- **HPI-2.** No self-enrollment: an entity cannot expand its own signing authority without independent, fresh election evidence (HPSE-REQ-041, extending HATP-REQ-040).
- **HPI-3.** `principal_id` is never derived from, or required to equal, OS-level identity (HPSE-REQ-002).
- **HPI-4.** The Principal/Signer registry and the `DeploymentBinding` registry share one whole-document transition lock; no split-brain concurrent write is possible by construction (HPSE-REQ-033).
- **HPI-5.** No software-key substitution for a hardware signer absent an explicit future contract amendment naming one (HPSE-REQ-044, restating HATP-REQ-021).
- **HPI-6.** Signer identity (`signer_key_id`) is never reassigned in place; rotation is always enroll-new-then-revoke-old (HPSE-REQ-016).

## 28. Contract Self-Consistency Statement

This contract adds zero fields to `PrincipalRecord`/`SignerRecord` beyond what `hatp_bootstrap.py` already defines (HPSE-REQ-007/013), reuses every atomicity/locking/audit/error-handling idiom already established by `hatp_deployment_binding_admin.py` rather than inventing a parallel one, and names — without implementing — every schema widening (HPSE-REQ-008), producer amendment (HPSE-REQ-047/048), and HMIC binding (§26) a future phase must complete before real enrollment can occur. No `DeploymentBinding` was created, no election was initiated, no CHGR was published, no certification was performed, and no Dell host was mutated in the production of this contract text.

## 29. Expected Contract Verdict

```
HATP PRINCIPAL/SIGNER ENROLLMENT CONTRACT:
HPSE-001 v1.0 — FROZEN
— PENDING INDEPENDENT VERIFICATION
— REAL ENROLLMENT NOT AUTHORIZED
— REAL PROVISIONING NOT AUTHORIZED
— NO ENROLLMENT WRITER IMPLEMENTED
```

## 30. Recommended Next Phase

**149O.20L.7O.2D.1 — HATP Principal/Signer Enrollment Contract Independent Verification.** That phase must independently attack principal semantics, signer semantics, provider profile, the registry schema (including the disclosed `PrincipalRecord.revoked_at` gap, HPSE-REQ-008), the enrollment writer's operation/error/atomicity/audit/locking design, enrollment authority separation, hardware-credential assumptions, the `DeploymentBinding` cross-validation requirements this contract names for a future phase (§21-§22), and HBDC-001 §16.2's `authority_scope` vocabulary decision — before any implementation phase builds against either. It must not implement anything.
