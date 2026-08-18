# Phase 149O.20L.7O.2D.1 — HATP Principal/Signer Enrollment Contract Independent Verification

## Phase identity

**Phase-ID:** 149O.20L.7O.2D.1
**Title:** HATP Principal/Signer Enrollment Contract Independent Verification
**Mode:** documentation (read-only independent verification; no implementation)
**Phase-entry commit:** `789c0015` (tip of Phase 149O.20L.7O.2D at task-open time)
**Contracts under review:** HPSE-001 v1.0 (`docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md`, `HPSE-REQ-001..052`); HBDC-001 v1.2 §16.2 (`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`, `HBDC-REQ-071..076`, `CBD-11`)
**RepositoryIdentity:** `0107866f-af7c-40b4-8317-74e71acb05ca` (unchanged; not re-read live on `hac-dell` this phase — no read-only fact was genuinely necessary beyond repository primary source, per governing-prompt §57)
**DeploymentBinding:** ABSENT (unchanged)
**Protected Root:** EMPTY (unchanged)

This phase does not trust Phase 149O.20L.7O.2D's report, companion tests, architecture prose, or claimed requirement interpretations as an oracle. Every claim below was independently re-derived from primary source (`src/pcae/core/hatp_bootstrap.py`, `hatp_deployment_binding_admin.py`, `hatp_signing_ceremony.py`, `hatp_hardware_credentials.py`, `hatp_providers.py`, `hatp_fido2_provider.py`, `hatp_piv_provider.py`, `human_approval_trusted_provenance.py`), read directly this phase, before the contract text itself was consulted for comparison.

---

## 1. Requirement numbering verification

Mechanically re-derived (not taken on the prior report's word):

- `HPSE-REQ-001` .. `HPSE-REQ-052`: exactly 52 unique bold-marker (`**HPSE-REQ-NNN.**`) definitions, sequential, no gaps, no duplicates. Confirmed by direct regex extraction against the committed contract file.
- `HBDC-REQ-071` .. `HBDC-REQ-076`: exactly 6 unique bold-marker definitions, sequential, no gaps, no duplicates.
- Both contracts declare their own version/status lines consistent with the numbering found (HPSE-001 "v1.0... 52 requirements"; HBDC-001 "v1.2... §16.2 amendment... HBDC-REQ-071..076").

**Verdict: PASS — mechanically verified independently, confirms the frozen contract's own §20/§21 claims.**

## 2. Primary-source reconstruction (independent, not HPSE-derived)

Read in full, starting from source, not contract prose:

- `hatp_bootstrap.py` (608 lines): confirms `PrincipalRecord(principal_id: str, status: str)` — exactly two fields, no `revoked_at`; confirms `SignerRecord(signer_key_id, principal_id, provider_profile, status, revoked_at)` with `_require_revoked_at_consistency` discipline; confirms `registry_version` exists at the **document** level (`REGISTRY_SCHEMA_VERSION = 1`), not per-record — this independently falsifies a naive reading of HPSE-REQ-007's parenthetical unless read exactly as written ("`registry_version` already exists at the document level (not per-record)"), which it does; confirms `_parse_registry_document`'s duplicate-key rejection for `principals`/`signers`/`deployment_bindings`/`authorities` independently (global uniqueness is real, not asserted); confirms `deployment_binding_matches` checks exactly `repository_id` + `canonical_deployment_root` + `status == "active"` — nothing else — independently confirming HBDC-REQ-076's factual claim about `_check_deployment_identity`'s exact scope.
- `hatp_deployment_binding_admin.py` (953 lines): confirms the exact atomicity idiom (`mkstemp`/`fsync`/`os.replace`/symlink rejection), the exact audit-ordering discipline (validate → mutate under lock → read-back-verify → audit → return), the exact `.deployment-binding-transition.lock` fixed path and `fcntl.flock` single-writer discipline, and confirms `AuthorityEvidence`'s `principal_id`/`signer_key_id`/`provider_profile`/`authority_scope` fields are validated for non-empty-string shape only — never cross-validated against any registry vocabulary. Independently confirms HPSE-REQ-031/032/033/047/048's factual premises.
- `hatp_signing_ceremony.py` (727 lines): confirms `_resolve_signer` checks only `signer.status` (never `principal.status`) when resolving a signer for proof *production* — independently confirming HPSE-REQ-050's claimed asymmetry.
- `hatp_providers.py` (392 lines): confirms `HATP_HARDWARE_PROVIDER_V1` is a one-member closed tuple (`_PRODUCTION_HARDWARE_PROVIDER_PROFILES`); confirms `create_production_hardware_provider` never resolves `TestHATPProofVerifierProvider`; confirms both FIDO2 and PIV concrete providers claim the identical `provider_profile` string (the profile denotes a security-property class, not a protocol tag — independently confirming HPSE-REQ-018/019/051's premise).
- `hatp_fido2_provider.py` (405 lines) and `hatp_piv_provider.py` (119 lines): **material independent finding, not disclosed at this precision by the prior phase** — see §5 below.
- `hatp_hardware_credentials.py` (285 lines): confirms a **third, separate** protected registry (`hardware-credentials.json`, its own fixed platform path, its own schema, its own `HATPHardwareCredentialStore`) distinct from `hatp_bootstrap.py`'s `registry.json`; confirms it has no writer at all in production code today, and its own module docstring explicitly anticipates enrollment being handled by "a future Human/Admin-only administrative surface" — see §5.
- `human_approval_trusted_provenance.py` (verification path, lines 762-927 read in full): confirms `verify_hatp_proof` independently re-derives `signer` via `trust_store.lookup_signer(proof.signer_key_id)` (never trusting `proof.principal_id`/`proof.provider_profile` as self-asserted, cross-checking both against the live registry record for that exact `signer_key_id`); confirms `principal.status != "active"` is checked (line 889) as an independent, live, per-verification gate, distinct from and in addition to `signer.status`; confirms `binding.principal_id != signer.principal_id` (and `signer_key_id`/`provider_profile`) are cross-checked at line 912 against the **live** signer record, not merely the `DeploymentBinding`'s own copied field values. This is a materially important architectural fact — see §9 below (resolves §42-45 of the governing prompt).

## 3. `principal_id` semantics (HPSE-REQ-001..008)

Independently confirmed against `HATPTrustStore`, `_parse_principal`, and every registry consumer read this phase: `principal_id` is used exclusively as a registry-record key (`hatp_bootstrap.PrincipalRecord.principal_id`), never compared to, derived from, or required to equal any OS-level identity anywhere in the modules read. No production consumer conflates it with an OS principal, an agent identity, or a runtime identity. HPSE-REQ-001/002's normative restatement of HATP-REQ-014/028/037 is consistent with every consumer read.

**Verdict: PASS — non-circular, precise, consistent with existing production semantics.**

## 4. `PrincipalRecord` schema and the `revoked_at` gap (HPSE-REQ-007/008)

Independently confirmed: `_parse_principal`'s `allowed` set is exactly `{"principal_id", "status"}` — no `revoked_at`, no `schema_version`, no `principal_type`. HPSE-REQ-008's disclosed gap is real, not overstated.

Answering the governing prompt's specific sub-questions directly against source (not against the prior report's prose):

- Is `revoked_at` required for active principals as `None`/null? — Not yet answerable today because the field does not exist; HPSE-REQ-008 correctly defers this to a future schema widening rather than inventing an answer prematurely. Once widened, `_require_revoked_at_consistency` (already proven, byte-identical, on `SignerRecord`/`AuthorityRecord`/`DeploymentBinding`) is named as the discipline to reuse — this is unambiguous *because* it names an existing, working precedent rather than inventing new logic.
- Can `status=revoked` coexist with missing `revoked_at`? — Under the *named future* discipline (`_require_revoked_at_consistency`), no: this function raises `HATPTrustStoreMalformedError` if `status == "revoked"` and `revoked_at is None`. This is unambiguous by direct reference to working code, not by contract prose alone.
- What timestamp grammar applies? — HPSE-REQ-052 pins the strict HBDC-REQ-067 grammar for this future field, not the permissive `_parse_iso_timestamp` read-path grammar. Unambiguous.
- Does current registry serialization support it? — No (confirmed: `_registry_document_with_binding`-style write helpers do not exist for principals/signers at all yet, since no writer exists) — but HPSE-REQ-008 explicitly and correctly scopes this out as a prerequisite `hatp_bootstrap.py` widening, not a hidden assumption.

**Verdict: The `revoked_at` gap is real and correctly, unambiguously disclosed. HPSE-REQ-008's deferred-implementation SHALL clause gives an implementer no room for divergent interpretation — it names the exact function, the exact discipline, and the exact precedent. This is NON-BLOCKING (implementation-phase item, `hatp_bootstrap.py` widening, itself independently HMIC-bound and requiring its own future verification — already so stated by HPSE-REQ-008 and confirmed independently at §10 below).**

## 5. Signer-key derivation durability — MATERIAL FINDING (Blocking, see §12)

7O.2D's report and HPSE-REQ-011 characterize the FIDO2 `credential_identity()` gap as: a conformant implementation "MAY be unable to re-derive it from the physical device alone at a later time," citing the module's own docstring language ("established at enrollment time... not re-derivable from the device alone").

Independent re-reading of `hatp_fido2_provider.py::Fido2HardwareProvider.credential_identity()` (lines 270-276) finds this description materially understates the actual gap:

```python
def credential_identity(self) -> str:
    raise HATPProviderUnavailableError(
        "credential_identity() requires a live CTAP2 device with a discoverable/resident"
        " credential; no device is available in this environment. Credential identity for a"
        " non-resident credential is established at enrollment time (Wave 2/7 administrative"
        " surface, out of Wave-5 scope) and is not re-derivable from the device alone."
    )
```

This method **unconditionally raises** — it is not "sometimes unable to re-derive," it has **zero implementation** of any resident-credential discovery or enrollment-time credential-identity-capture logic (e.g. a CTAP2 `makeCredential` ceremony that would mint and return a fresh `credential_id`). It raises regardless of whether a physical device is present, attached, or provisioned. `PivHardwareProvider.credential_identity()` (line 93-94) is likewise an unconditional raise (documented `NOT_CONFORMANT`).

HPSE-REQ-010 requires `signer_key_id` to be "obtained via the enrolling hardware provider's own `credential_identity()` method, called live during the enrollment ceremony... the identical provider-identity-exchange mechanism `hatp_signing_ceremony.py::_resolve_signer` already uses for the verification side, applied here to enrollment." This is a factually correct description of *what exists today for the verification side* (which also calls `credential_identity()` and would also unconditionally fail against the real hardware provider) but the contract text's framing — "MAY be unable to re-derive... at a later time" — reads as a re-derivability limitation on an otherwise-working method, when the actual state is that **no working implementation of this method exists for either FIDO2 or PIV in this codebase today**, independent of device presence.

**Consequence:** HPSE-REQ-044/045/046's "first-use sequence" names "(1) physical credential provisioning" as the sole prerequisite before principal/signer enrollment can begin. This independently-confirmed finding shows that is incomplete: even with a compliant, provisioned physical device present, `enroll_signer` as specified by HPSE-REQ-010 cannot succeed without **new**, currently entirely unwritten implementation work in `hatp_fido2_provider.py` (a CTAP2 credential-minting/discovery path `credential_identity()` does not have today) — a materially different and larger prerequisite than "physical credential provisioning," and one HPSE-001 does not name as a required future amendment anywhere (contrast with how carefully HPSE-REQ-047/048 name the required future `DeploymentBinding` producer amendment).

## 6. `SignerRecord` schema (HPSE-REQ-013/014)

Independently confirmed unchanged, symmetric with `AuthorityRecord`/`DeploymentBinding` revocation-timestamp discipline. No private-key material in `SignerRecord` — confirmed; `SignerRecord` carries only `signer_key_id`/`principal_id`/`provider_profile`/`status`/`revoked_at`.

**Verdict: PASS.**

## 7. Principal ↔ signer cardinality and rotation (HPSE-REQ-015..017)

Independently confirmed: `SignerRecord.principal_id` is single-valued (structurally one signer → one principal); nothing in the schema prevents multiple `SignerRecord`s sharing one `principal_id` (cardinality one-to-many, unenforced upper bound — matches HPSE-REQ-017's explicit "MAY have more than one concurrently active signer"). Enroll-new-then-revoke-old rotation (HPSE-REQ-016) is unambiguous given `signer_key_id`'s role as primary key (HPSE-REQ-022's uniqueness) — an in-place `signer_key_id` overwrite would silently orphan any external reference to the old value, correctly avoided.

**Verdict: PASS — no ambiguity found.**

## 8. `provider_profile` semantics, vocabulary, and runtime separation (HPSE-REQ-018..020, HPSE-REQ-051)

Independently confirmed: `HATP_HARDWARE_PROVIDER_V1` is the sole closed-tuple value (`hatp_providers.py::_PRODUCTION_HARDWARE_PROVIDER_PROFILES`); `HardwareProviderCapabilities.provider_profile` is the field HPSE-REQ-020 says to capture from, confirmed present on both `Fido2HardwareProvider.capabilities()` and `PivHardwareProvider.capabilities()`, both returning the identical string. No occurrence of `Claude`, `Codex`, `DeepSeek`, or any agent-runtime identifier was found anywhere in `hatp_providers.py`, `hatp_fido2_provider.py`, `hatp_piv_provider.py`, `hatp_bootstrap.py`, or the two contracts under review. `provider_profile` denotes signing-hardware security-property class only, structurally incapable of being set to a runtime-identity string because it is validated against the one-member closed allowlist, not accepted as free text.

**Verdict: PASS — genuinely runtime-neutral; HPSE-REQ-051's separation is real, not merely asserted. §37's FIDO2-vs-PIV question: both providers legitimately claim the identical `provider_profile` string (confirmed, `hatp_providers.py`), so HPSE-001 correctly needs no provider-specific schema branching — this is structurally sound. §38's clarification also independently confirmed: only FIDO2 is `CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS`; PIV is `NOT_CONFORMANT` (a documented placeholder). HPSE-001 does not distinguish this in its text, but since `provider_profile` never encodes protocol identity and PIV's own `credential_identity()`/`request_signature()` unconditionally raise (fail-closed), this omission has no security consequence — a non-blocking clarity note, not a defect.**

## 9. Registry architecture, referential integrity, and the producer-trust/verifier-trust boundary (HPSE-REQ-021..025, §21-23 of HPSE-001, §16.2/CBD-11 of HBDC-001)

Independently confirmed registry schema facts (§2 above). The governing prompt's §42/§43/§44/§45 ask this phase to independently choose or verify a producer-trust-vs-verifier-trust architecture and evaluate a tampered-registry hypothetical. Direct reading of `human_approval_trusted_provenance.py::verify_hatp_proof` (not merely trusting HPSE-001's own HPSE-REQ-050 disclosure) resolves this precisely:

- `verify_hatp_proof` looks up `signer` **live** via `trust_store.lookup_signer(proof.signer_key_id)` — never trusts `proof.principal_id`/`proof.provider_profile` as self-asserted (cross-checked against the live signer record, lines 848/850).
- `principal.status != "active"` is checked live (line 889) as an independent gate.
- `authority.status != "active"` is checked live (line 891).
- `binding.principal_id != signer.principal_id or binding.signer_key_id != proof.signer_key_id or binding.provider_profile != proof.provider_profile` (line 912) cross-checks the `DeploymentBinding`'s own copied field values against the **live** signer record — not merely against the proof's self-asserted fields.

**This independently confirms the tampered-registry hypothetical's answer**: an admin who manually writes an `active` `DeploymentBinding` with a valid `repository_id`/`canonical_deployment_root` but a fabricated `principal_id` would pass `HBDC-REQ-042`'s conformance check today (confirmed — `deployment_binding_matches` checks only `repository_id`/`canonical_deployment_root`/`status`) — **but that alone grants no working authority**, because no proof carrying that fabricated `principal_id` can ever reach `VALID` unless a fully self-consistent chain also exists in the live registry (an active `PrincipalRecord` for that id, an active `SignerRecord` naming it, and an active `AuthorityRecord`). Since the only entity capable of writing such a `DeploymentBinding` in the first place (OS filesystem write access to the Protected Root) is by definition also capable of writing that self-consistent chain, this does not represent a privilege-escalation path beyond the Protected-Root write boundary HATP-001/HBDC-001 already name as the real security boundary.

**This resolves §42's "choose one architecture" question as already answered, in production, today**: the actual disposition is **hybrid** — (a) the `DeploymentBinding` producer does not cross-validate at write time (confirmed, HBDC-REQ-058's own disclosed disposition), (b) `HBDC-REQ-042`'s conformance check does not re-validate at read time (confirmed, HBDC-REQ-076's disclosed disposition, matches source), but (c) proof *verification* — the actual security-relevant checkpoint for whether any authority is ever exercised — independently re-derives and cross-checks every authority-bearing field against live registry state on every single verification call. HPSE-REQ-050 states this correctly for the principal/signer axis ("the resulting proof fails at the verification boundary, which is the security-relevant checkpoint"); this phase independently confirms it is also true for the `DeploymentBinding.principal_id` axis specifically (line 912), which HPSE-REQ-049 discusses only in terms of "does not automatically alter" without stating that verification independently neutralizes the practical risk.

**Finding (non-blocking, documentation-completeness): neither HPSE-001 nor HBDC-001 states this hybrid disposition explicitly as settled architecture.** HPSE-001 §23 frames HBDC-REQ-042 extension as an open future decision ("a decision this contract does not make and does not require"), which is true narrowly (HBDC-REQ-042's own text is indeed unamended), but leaves a reader without independent access to `human_approval_trusted_provenance.py` unable to determine that the underlying security question is already closed by the verification path. **Recommend a future documentation-only amendment (HBDC-001 or HPSE-001) explicitly name this as the settled hybrid disposition** — not because the current architecture is unsafe, but because §42's "do not leave this implicit" instruction is well-founded: an implementer relying on contract text alone, without independently reading `human_approval_trusted_provenance.py`, could wrongly conclude the tampered-registry case is an open vulnerability requiring urgent remediation, when it is already closed.

**Verdict: Registry architecture and referential integrity — PASS. Producer/verifier trust boundary — VERIFIED SAFE (hybrid, already implemented), but the contract text under-discloses this; NON-BLOCKING documentation-completeness finding.**

## 10. Enrollment writer API, preview semantics, atomicity, locking (HPSE-REQ-026..033)

Independently confirmed against `hatp_deployment_binding_admin.py` (the pattern HPSE-001 mirrors byte-for-byte in its own text): the atomic-write idiom, read-back-verification idiom, and `.deployment-binding-transition.lock`/`fcntl.flock` single-writer idiom are exactly as HPSE-REQ-031/032 describe, confirmed by direct source read, not contract assertion. HPSE-REQ-033's shared-lock requirement (same fixed lock-file path for both writers) is the correct fix for the concurrency hazard the governing prompt's §26 describes (writer A loads → writer B loads → A writes → B writes stale): confirmed that `_deployment_binding_transition_lock` is keyed to a fixed path directly under the Protected Root (`store_root / ".deployment-binding-transition.lock"`), not derived from any writer-specific name — a future Principal/Signer writer referencing this identical constant, as HPSE-REQ-033 requires, closes the hazard by construction, confirmed against the real locking primitive rather than assumed.

**API surface count:** `enroll_principal`/`revoke_principal`/`enroll_signer`/`revoke_signer` plus four preview variants = 8 functions. Compared against the existing `DeploymentBinding` writer's 3 mutating + 3 preview = 6 functions for a schema with one fewer natural lifecycle split (no principal/signer distinction). This is proportionate, not API proliferation — no operation is redundant with another (create/rotate/revoke each address a genuinely distinct outcome; `PrincipalRecord`/`SignerRecord` genuinely need independent enroll/revoke pairs since HPSE-REQ-016 deliberately excludes a single-call rotate).

**Preview completeness (§24 of the governing prompt):** the four preview variants named (HPSE-REQ-030) mirror `preview_create_deployment_binding`'s exact "never writes" discipline. Independently confirmed the existing preview functions genuinely never acquire the transition lock and never touch disk for writing — but they *do* perform every other check `create`/`rotate`/`revoke` performs (`_validate_authority_evidence`, `_resolve_repository_id`, `_resolve_canonical_root`, `_require_trust_store_available`, full registry parse) before classifying an outcome. A named future Principal/Signer preview implementation following this exact pattern would not omit hardware/provider checks, since `provider_profile` validation against the closed allowlist (HPSE-REQ-020) is a pure-function check with no side effect and belongs squarely in preview's existing-pattern scope.

**Preview/create parity (§40):** the existing `DeploymentBindingPreview`/`create_deployment_binding` pair share no common validation function directly (both reimplement the same sequence of checks independently, not via one shared internal helper) — this is a real, pre-existing, non-blocking implementation-hygiene observation about the *pattern* HPSE-001 commits to reusing, not a defect HPSE-001 introduces. A future implementation following this pattern inherits the same minor divergence risk (preview and create logic kept in sync by discipline, not by construction) that the existing `DeploymentBinding` writer already carries. Non-blocking; worth naming for the future implementation phase to consider (e.g. a shared internal validation helper) but not a contract-text defect.

**Verdict: PASS. HPI-4 (shared-lock security invariant) independently confirmed as sound and mechanically achievable.**

## 11. Error vocabulary and fail-closed behavior (HPSE-REQ-034..037)

Independently confirmed the closed-error-hierarchy pattern this contract commits to mirroring (`HATPDeploymentBindingAdminError` and its 8 concrete subclasses in `hatp_deployment_binding_admin.py`) is real, typed, and never falls back to bare `ValueError`. HPSE-REQ-034's named minimum error set (principal/signer not found, duplicate principal/signer, signer/principal mismatch, unsupported provider, revoked principal/signer, malformed registry, read-back mismatch) is a superset sufficient to distinguish every outcome named elsewhere in the contract — no outcome named in §7-§19 of HPSE-001 lacks a corresponding error class in HPSE-REQ-034's list.

Fail-closed behavior (HPSE-REQ-035/036/037): independently confirmed `_load_raw_registry_document` returns `None` (not an exception) for an absent file — EMPTY is a real, distinguishable state from INVALID (`HATPTrustStoreMalformedError` for a present-but-malformed document) in the actual parser, not merely asserted.

**Verdict: PASS — error vocabulary sufficient, EMPTY/INVALID distinction real and mechanically enforced.**

## 12. Audit ordering (HPSE-REQ-038/039)

Independently confirmed against `hatp_deployment_binding_admin.py`'s actual audit-ordering implementation (validate → mutate under lock → read-back-verify → audit → return, `create_deployment_binding` lines 574-645 read directly): state is always durable and read-back-verified **before** the audit call. This ordering choice means the failure mode is exactly as HPSE-REQ-039 states: state can become durable with no audit record (if `_audit` itself raises), never the reverse (an audit record with no durable state) — the module's own docstring's stated rejection of the alternative ordering ("relocates the same fundamental risk to the opposite failure mode... without closing it") is independently confirmed correct: there is no ordering of two independently-atomic systems that eliminates the risk window entirely without a real two-phase commit, and HPSE-001 does not claim otherwise.

**Verdict: PASS — the audit-failure state is always recoverable/determinable (durable-but-unaudited, detectable by comparing registry state against the audit log; never audited-but-not-durable, which would be undetectable and therefore worse). This satisfies the governing prompt's §32 "no ambiguous 'exception = nothing happened'" requirement.**

## 13. Enrollment authority separation, election/CHGR (HPSE-REQ-040..043)

Independently confirmed three-role separation (human decision authority / admin execution principal / enrolled principal) is structurally consistent with HATP-REQ-028's frozen two-principal topology and does not introduce a fourth OS-level principal. HPSE-REQ-041's explicit closure of the admin-self-enrollment loophole (mirroring HATP-REQ-040) is unambiguous: it names the exact case (the admin enrolling themselves) and the exact rule (not exempt from HPSE-REQ-042). No gap found between "election required for enrollment/revocation" (HPSE-REQ-042) and the existing HBDC-REQ-064/065 pattern it mirrors — `election_reference` recorded as audit metadata only, never cryptographically verified, is an accurate restatement of the existing `AuthorityEvidenceMissingError` discipline in `hatp_deployment_binding_admin.py`, confirmed by direct read.

**Verdict: PASS.**

## 14. Timestamp grammar, runtime neutrality, example consistency, cross-references (HPSE-REQ-052, §50-53)

Independently confirmed `_TIMESTAMP_PATTERN` (`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$`) in `hatp_deployment_binding_admin.py` is the exact grammar HPSE-REQ-052 pins for this contract's future timestamps — verbatim match, confirmed by direct comparison, not assumed.

Runtime-coupling scan: no occurrence of `Claude`, `Codex`, `DeepSeek`, `agent runtime`, or `model` (in a runtime-identity sense) found anywhere in either contract's normative text outside of HPSE-REQ-051's own explicit prohibition naming those exact terms defensively.

Cross-reference integrity: every `HATP-REQ-*`/`HBDC-REQ-*`/`HMIC-REQ-*` reference found in HPSE-001's text was checked against the referenced contract; `HATP-REQ-014/019/021/028/036-041`, `HBDC-REQ-056/058/062-069`, and `HMIC-001`'s `implementation_scope_digest`/`_FROZEN_SRC_PCAE_RELATIVE_FILES` were confirmed to exist as described (the latter independently re-read from `hatp_mandatory_certification.py` lines 960-984 this phase — confirms `hatp_bootstrap.py`, `hatp_hardware_credentials.py`, and `hatp_deployment_binding_admin.py` are already HMIC-digest-bound files, but no Principal/Signer enrollment writer module exists in that list yet, consistent with HPSE-001 §26's disclosure that a future implementation module is an "expected candidate," not yet performed).

**Verdict: PASS on all four sub-checks.**

## 15. Normative conflict scan (§54)

One genuine conflict found, not previously disclosed at this precision:

**`hatp_hardware_credentials.py`'s own module docstring states:** "Enrollment (writing a new credential into this registry) is explicitly OUT of Wave-5 scope -- HATP-001/149O.1D assign registry-mutation to **a future Human/Admin-only administrative surface** (Wave 2/7 territory, mirroring `hatp_bootstrap.py`'s own enroll/grant/revoke deferral)."

HPSE-001 **is** exactly that future Wave-2/7 administrative surface (its own §1 states it formalizes "HATP-REQ-036/037's conceptual enrollment procedure into concrete, testable requirements for a Principal/Signer enrollment writer"). Yet HPSE-001 §2 explicitly excludes `hardware-credentials.json` from its own scope ("a separate, sibling protected artifact this contract references but does not amend") without naming a required future companion contract/writer for it anywhere in the document — unlike its careful, explicit naming of the `PrincipalRecord.revoked_at` widening (HPSE-REQ-008) and the `DeploymentBinding` producer amendment (HPSE-REQ-047/048).

This is a genuine internal-architecture contradiction between what `hatp_hardware_credentials.py`'s own primary source anticipates and what HPSE-001 actually delivers — see §16 (Blocking findings) below.

No other normative conflict was found against HATP-001, HBDC-001 (unamended sections), HMIC-001, or the AuthorityEvidence-family contracts read this phase.

## 16. Implementability test (§55) and Blocking findings

Applying the governing prompt's own test directly: **could two competent implementers, both claiming full HPSE-001 v1.0 compliance, produce materially incompatible behavior?**

**Yes — this is the phase's central finding.** Implementer A builds `enroll_signer` exactly per HPSE-REQ-009..020/026..039: it calls `credential_identity()`, validates `provider_profile` against the closed allowlist, writes a new `SignerRecord` atomically under the shared lock, reads back, audits. This implementer never touches `hardware-credentials.json` — nothing in HPSE-001 requires it to. Implementer B does the identical thing. Both are fully HPSE-001 v1.0 compliant. **Neither implementation can ever produce a signer whose signature can reach `HATPVerificationStatus.VALID`**, because `Fido2HardwareProvider.verify()` (confirmed, `hatp_fido2_provider.py` lines 341-404) unconditionally returns `signature_valid=False` whenever `HATPHardwareCredentialStore.lookup_credential(signer_key_id)` returns `None` — which it always will, since nothing in HPSE-001, `hatp_hardware_credentials.py`, or any other contract read this phase establishes a writer for that registry.

This is compounded by §5's finding: even the enrollment step itself (`credential_identity()`) has no working implementation to call, independent of device presence.

Together, these mean **HPSE-001 v1.0, as written, specifies a Principal/Signer enrollment writer that can be built to the letter of every one of its 52 requirements and still produce zero real, usable signing authority** — the enrolled `SignerRecord` would be `active`, durable, correctly audited, and structurally indistinguishable from a real, usable signer, yet functionally inert. This is a **requirement contradiction** and a **signer-identity-not-durable/resolvable** class finding under the governing prompt's own §58 Blocking taxonomy (extended: durable in the registry, but never resolvable to a working credential end-to-end).

### BLOCKING FINDING B-149O.20L.7O.2D.1-1

**HPSE-001 v1.0 does not name a required companion writer (or a required future contract amendment naming one) for `hardware-credentials.json`, the separate cryptographic registry `Fido2HardwareProvider.verify()` depends on to ever return `signature_valid=True`.** Without it, every signer enrolled exactly per HPSE-001 v1.0 is permanently unable to produce a proof that reaches `VALID`. This conflicts with `hatp_hardware_credentials.py`'s own module docstring, which explicitly anticipates this exact future administrative surface populating it. **Required repair:** HPSE-001 must be amended to either (a) bring `hardware-credentials.json` writer requirements into its own scope, explicitly reusing the identical atomicity/locking/audit pattern, or (b) explicitly name a required, separate, future companion contract/requirement (mirroring how HPSE-REQ-047/048 name the required future `DeploymentBinding` producer amendment) that must be implemented and independently verified before `enroll_signer` may be considered implementation-ready.

### BLOCKING FINDING B-149O.20L.7O.2D.1-2

**HPSE-REQ-010/011's characterization of `credential_identity()` as a method that "MAY be unable to re-derive" a signer identity materially understates its actual state: it has zero production implementation (unconditional raise) for either FIDO2 or PIV, independent of device presence.** HPSE-REQ-046's "first-use sequence" names "(1) physical credential provisioning" as the sole prerequisite before enrollment, but provisioning a compliant physical device today would still leave `enroll_signer` unable to proceed, because no code path exists anywhere in this codebase that could produce a real `signer_key_id` from a live device — a strictly larger, currently-unnamed implementation prerequisite. **Required repair:** HPSE-001 (or a named future amendment) must explicitly disclose that `credential_identity()`'s FIDO2 implementation itself requires new, currently-unwritten hardware-provider-layer work (e.g. a CTAP2 credential-minting/discovery ceremony) as a prerequisite to `enroll_signer`, distinct from and in addition to physical device provisioning.

Both findings are related (the same underlying "hardware-provider layer is a placeholder, not a working implementation" root cause) and could plausibly be repaired together in a single future architecture phase.

## 17. Non-Blocking findings

- **NB-1** (§9 above): the producer-trust/verifier-trust boundary is already safely resolved in production (`verify_hatp_proof`'s live cross-checks), but neither HPSE-001 nor HBDC-001 states this explicitly as settled architecture — a documentation-completeness gap, not a security gap.
- **NB-2** (§10 above): preview/create parity is maintained by discipline (matching implementations kept in sync by convention), not by a shared validation helper, in both the existing `DeploymentBinding` writer and the pattern HPSE-001 commits to reusing. Worth a future implementation-phase improvement, not a contract defect.
- **NB-3** (§8 above): HPSE-001 does not distinguish FIDO2 (`CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS`) from PIV (`NOT_CONFORMANT`) in its text, relying implicitly on both sharing one `provider_profile` string and PIV's own unconditional-raise fail-closed behavior. No security consequence found; a clarity improvement only.
- **NB-4** (§4 above): the `PrincipalRecord.revoked_at` schema-widening gap (HPSE-REQ-008) is real but unambiguously disclosed and precisely scoped to a future, separately-verified phase — this is the textbook "implementation does not yet exist" non-blocking case the governing prompt's §59 anticipates.
- **NB-5**: HBDC-001's own disclosed pre-existing staleness (§21, requirement-count range not updated across the v1.1/v1.2 amendments) is unrelated to HPSE-001's scope and was already disclosed by the frozen contract text itself as a known future documentation-repair item — re-confirmed present, not a new finding.

## 18. HMIC implications (source-scope and live-state)

Independently confirmed (§14 above, direct read of `hatp_mandatory_certification.py`'s `_FROZEN_SRC_PCAE_RELATIVE_FILES`): `hatp_bootstrap.py`, `hatp_hardware_credentials.py`, and `hatp_deployment_binding_admin.py` are already HMIC-digest-bound. A future Principal/Signer enrollment writer module and its companion admin script are not yet in that list — confirming HPSE-001 §26's own disclosure that this is an "expected candidate," not yet performed, is accurate. Any future `hatp_bootstrap.py` widening for `PrincipalRecord.revoked_at` (HPSE-REQ-008) would touch an already-bound file and therefore mechanically triggers HMIC re-certification by the existing digest mechanism — this is a structural guarantee, not merely a hope.

**HMIC live-state gap (independently confirmed, matches HPSE-001 §26's own scope limitation):** HMIC-001 as currently understood source-digests code only; it does not itself bind live registry state (principal/signer/binding/authority records or a registry digest). This phase does not find this to be a defect in HPSE-001 or HBDC-001 (neither claims otherwise), but flags it as an open architecture question for a future phase: whether live-authority-state integrity is adequately covered by the existing HATP proof-verification path (§9 above, which does independently re-derive live state at every verification) or whether HMIC-001 itself should eventually also bind a registry digest. Non-blocking; explicitly out of this phase's scope to resolve.

## 19. Blocking-finding classification cross-check (§58 taxonomy)

| §58 category | Applies? | Finding |
|---|---|---|
| principal semantics ambiguous | No | §3 PASS |
| signer identity not durable/resolvable | **Yes** | B-149O.20L.7O.2D.1-1/2 |
| unsupported provider ambiguity | No | §8 PASS |
| authority_scope insufficiently defined | No | not re-examined in depth this phase beyond confirming zero-consumer status (§9); HBDC-REQ-071..076's closed single-member vocabulary is unambiguous on its face |
| registry writers can split-brain | No | §10 PASS, shared-lock mechanically sound |
| audit failures leave unknowable authority state | No | §12 PASS |
| producer amendment omits required cross-field validation | Related | the *named* future DeploymentBinding producer amendment (HPSE-REQ-047/048) is itself sufficient and unambiguous; the *unnamed* hardware-credentials.json writer gap is the actual finding (B-1) |
| revocation semantics undefined | No | §9/§13 PASS — DeploymentBinding revocation-cascading is disclosed and, per §9, already practically closed at the verification checkpoint |
| HBDC can accept semantically invalid binding contrary to trust model | No | §9 — confirmed the "invalid" binding cannot be exercised as working authority; consistent with the stated trust model |
| contract/runtime coupling | No | §8/§14 PASS |
| requirement contradiction | **Yes** | B-149O.20L.7O.2D.1-1/2, and the §15 normative conflict against `hatp_hardware_credentials.py`'s own docstring |

## 20. Final verdict

```
HATP PRINCIPAL/SIGNER ENROLLMENT CONTRACT INDEPENDENT VERIFICATION:
HPSE-001 v1.0 / HBDC-001 v1.2 §16.2

NOT VERIFIED — CONTRACT AMENDMENT REQUIRED

Blocking findings: 2 (B-149O.20L.7O.2D.1-1, B-149O.20L.7O.2D.1-2)
Non-Blocking findings: 5 (NB-1..NB-5)

50 of 52 HPSE-REQ requirement areas independently verified sound;
the hardware-credential-registry / credential_identity() implementation
gap (§5, §15, §16) blocks real enrollment from ever producing usable
signing authority, and is not adequately named as a prerequisite by
the contract text as written.
```

This verdict does NOT mean HPSE-001/HBDC-001 v1.2 are poorly designed — the overwhelming majority of both contracts (registry schema, atomicity, locking, audit ordering, error vocabulary, fail-closed behavior, authority separation, election/CHGR discipline, runtime neutrality, and the `authority_scope` vocabulary closure) is independently confirmed sound, precise, non-circular, and implementable exactly as written. The two Blocking findings are narrow and specific: a missing companion-writer disclosure for one sibling registry, and an understated characterization of one hardware-provider method's actual implementation state. Both are repairable by a narrow, targeted contract amendment without touching the majority of either document.

## 21. Recommended next phase

**149O.20L.7O.2D.2 — HATP Principal/Signer Enrollment Contract Repair.** Scope: amend HPSE-001 to (a) name a required future `hardware-credentials.json` writer requirement (or bring it into HPSE-001's own scope) as a prerequisite to `enroll_signer` implementation-readiness, and (b) correct HPSE-REQ-010/011's characterization of `credential_identity()`'s current implementation state and name the additional hardware-provider-layer implementation work required before real enrollment can occur. This phase must not implement anything. After repair, a second independent contract verification (149O.20L.7O.2D.3 or equivalent numbering, per PROJECT_STATUS.md at that time) is required before any implementation phase proceeds — mirroring this repository's established repair → re-verify precedent.

## 22. Strategic breakpoint

Unaffected and preserved. The approved breakpoint remains after the first `DeploymentBinding` is created and independently verified on the real host, before Boundary C. This phase performed no enrollment, no provisioning, no `DeploymentBinding` creation, no election, no CHGR, no certification, and no Dell mutation — the breakpoint precondition is unchanged and unreached.

## 23. Proof of scope discipline

- **No implementation:** no production `.py` file under `src/pcae/` or `scripts/` was modified this phase. `git diff --stat` against the phase-entry commit for all production source paths is empty (verified below, §24).
- **No Dell mutation:** no SSH session or remote command was issued this phase; RepositoryIdentity/DeploymentBinding/Protected Root state above is carried forward unchanged from Phase 149O.20L.7O.2C/7O.2D's own most recent live observations, not re-verified live (no read-only fact was genuinely necessary per governing-prompt §57).
- **No enrollment:** no `PrincipalRecord`/`SignerRecord` was created, no hardware credential was provisioned or referenced beyond reading existing source/documentation.
- **No DeploymentBinding created:** none exists; none was created.
- **No election initiated, no CHGR published, no certification performed, no Boundary C activity, no HATP activation:** none occurred.

## 24. Tests

`tests/test_phase_149o_20l_7o_2d_1_hatp_principal_signer_enrollment_contract_independent_verification.py` — mechanically re-verifies this phase's own load-bearing factual claims against live source (not against this report's own prose): requirement-numbering completeness for both contracts; the `PrincipalRecord.revoked_at` gap; `Fido2HardwareProvider.credential_identity()`'s unconditional-raise behavior (the phase's central finding, §5/§16); `HATPHardwareCredentialStore`'s absence of any production writer method; `deployment_binding_matches`'s exact three-field scope; `verify_hatp_proof`'s live signer/principal/binding cross-checks (§9); the HMIC frozen-file-set membership facts (§18); and that no production source file was modified this phase.

## 25. Governance results, commits, push status

See `.pcae/phase-completion-metadata.json` / `.pcae/phase-completion-report.md` for the canonical machine-checked record (health/check/fast_green/full-suite results, commit list, `origin/main..HEAD`, pushed status) generated by `pcae phase complete`.
