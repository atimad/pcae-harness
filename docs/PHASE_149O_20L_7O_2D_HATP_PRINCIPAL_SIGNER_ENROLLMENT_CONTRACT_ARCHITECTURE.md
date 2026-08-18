# Phase 149O.20L.7O.2D — HATP Principal/Signer Enrollment Contract Architecture

## 0. Status

Architecture / contract-freeze only. Read-only against Dell. No enrollment writer implemented, no `PrincipalRecord`/`SignerRecord` written, no credential provisioned, no `DeploymentBinding` created, no election initiated, no CHGR published, no HMIC certification performed, no Dell mutation of any kind. This phase freezes two contract artifacts: a new companion contract, `docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md` (HPSE-001 v1.0), and a narrow amendment to `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001 v1.1 → v1.2, new §16.2). Governed by HATP-001, HBDC-001, HSCE-001, HMIC-001 (all unamended except HBDC-001's own narrow §16.2 addition).

## 1. Phase-Entry Commit

`ec4250edff8496e79880bc4b41007d8326a6bedb` — "Phase 149O.20L.7O.2C: close task, transition to idle". Working tree clean at entry; `origin/main` up to date.

## 2. RepositoryIdentity (Unchanged, Not Re-Touched This Session)

- `repository_instance_id`: `0107866f-af7c-40b4-8317-74e71acb05ca` — value only, re-stated from 149O.20L.7O.2C's own independently re-confirmed reading; this phase performs no new SSH session against Dell and no new read of this value, since nothing in this phase's scope depends on live Dell state (this is a pure contract-text/architecture phase over already-verified source and already-verified Dell facts from the immediately preceding phase).
- `DeploymentBinding`: ABSENT (unchanged).
- Protected Root (`/etc/pcae/hatp/trust-store`): EMPTY (unchanged).
- Canonical HBDC status: NON_COMPLIANT, sole residual `HBDC-REQ-042`, reason `no_active_deployment_binding_matches_repository_and_root` (unchanged).
- Runtime: Observed / observe / unavailable (unchanged).

## 3. Primary-Source Reconstruction (This Session, Not 7O.2C Prose)

Read directly this session, not inherited from 149O.20L.7O.2C's own report text:

- `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` §7-§15 (HATP-REQ-013..041), verbatim, lines 160-359.
- `src/pcae/core/hatp_bootstrap.py`, full file (607 lines) — `PrincipalRecord`/`SignerRecord`/`AuthorityRecord`/`DeploymentBinding` dataclasses, `_parse_principal`/`_parse_signer`/`_parse_registry_document`, `HATPTrustStore`'s read-only interface.
- `src/pcae/core/hatp_deployment_binding_admin.py`, full file (953 lines) — the `DeploymentBinding` producer, reused as this contract's structural precedent for atomicity, locking, audit ordering, error hierarchy, and preview semantics.
- `src/pcae/core/hatp_signing_ceremony.py` lines 490-557 — `_resolve_signer`, the one real, wired, production consumer of `SignerRecord`.
- `src/pcae/core/hatp_hardware_credentials.py`, full file (285 lines) — the sibling Wave-5 cryptographic registry, its encoding conventions (`public_key_hex`), and its own explicit "enrollment is out of Wave-5 scope" disposition.
- `src/pcae/core/hatp_providers.py` lines 160-300 — `HATP_HARDWARE_PROVIDER_V1`, `_PRODUCTION_HARDWARE_PROVIDER_PROFILES`, `HATPHardwareSigner.credential_identity()`'s own docstring.
- `src/pcae/core/hatp_fido2_provider.py` lines 255-277, `src/pcae/core/hatp_piv_provider.py` lines 60-105 — both providers' current `credential_identity()` implementations (FIDO2: documented non-re-derivability; PIV: unconditional placeholder failure).
- `src/pcae/core/human_approval_trusted_provenance.py` lines 860-1040 — the two real production call sites of `trust_store.lookup_authority`/`lookup_principal`, confirmed to check only `.status`, never the content of `authority_scope`.
- `src/pcae/core/hatp_mandatory_certification.py` lines 925-1024 — HMIC-001's frozen `_FROZEN_SRC_PCAE_RELATIVE_FILES`/`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`, confirming `hatp_bootstrap.py` is already bound and `hatp_deployment_binding_admin.py` was added at v1.4 (the direct precedent for this phase's own §26/HPSE-REQ future-binding expectation).
- `scripts/hatp_deployment_binding_admin.py` lines 1-50 — the standalone-script precedent this contract's future implementation surface (§40) mirrors.
- `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` §16-§16.1 (HBDC-REQ-042, HBDC-REQ-056..070), read fresh this session before amendment.
- `docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md` lines 1-40 — the contract-identity-header structure and "additive, not amending" relationship-to-HATP-001 precedent this phase's own new HPSE-001 contract mirrors.
- `docs/PHASE_149O_20L_7O_2C_DEPLOYMENTBINDING_FIRST_USE_FIELD_RESOLUTION_ARCHITECTURE.md` — read as the *entering-state fact record* (§21's own readiness-gate classification, §27's own recommended-next-phase text), not as a substitute for the primary-source reconstruction above; every normative claim below traces to the source files listed above, independently re-derived, not copied from that report's prose.

This phase adds zero new fields to any existing production dataclass, zero new production modules, and modifies zero production `.py` bytes — only two contract-text artifacts (one new file, one amended section) and this report.

## 4. `principal_id` — Semantics, Frozen (HPSE-REQ-001..006)

Independently re-derived, not assumed from 7O.2C: HATP-REQ-014 ("Each enrolled human approver SHALL be identified by a stable `principal_id`, distinct from any human-readable display name... SHALL NOT change across key rotation") and HATP-REQ-037 ("the Human/Admin principal... assigns a `principal_id`") together establish `principal_id` as a registry identity for an enrolled human approver, assigned by the Human/Admin bootstrap authority at enrollment time — never an OS account, never a display name, never derivable from host state. HPSE-001 §4 (HPSE-REQ-001..006) freezes this exactly, adding one normative rule 7O.2C's own investigation only *proved by example* (the `"pcae"` disproof): HPSE-REQ-002 makes it a standing rule, not a one-time finding, that `principal_id` SHALL NOT be derived from or required to equal any OS-level username/UID/GECOS/process identity of the enrollment host.

Grammar: unchanged from the existing schema (non-empty string, `hatp_bootstrap._require_nonempty_str`) — no new grammar invented (HPSE-REQ-003). Global uniqueness is already mechanically enforced by `_parse_registry_document`'s duplicate-key rejection. Lifecycle: the existing closed two-value `{"active", "revoked"}` vocabulary, no third state (HPSE-REQ-005); revocation is monotonic, first-recorded evidence wins, mirroring `revoke_deployment_binding`'s own precedent exactly (HPSE-REQ-006).

## 5. `PrincipalRecord` Schema (HPSE-REQ-007..008)

A `PrincipalRecord` **already exists** in `hatp_bootstrap.py` (`principal_id: str`, `status: str`) — this phase does not design one from nothing; it evaluates whether the existing two-field schema is *sufficient*. Against the governing prompt's own candidate field list (`schema_version`, `principal_type`, display/reference metadata, `enrolled_at`, `revoked_at`, `enrollment_reference`, signer linkage): `schema_version` already exists at the document level; `principal_type` has no source-supported second value under HATP-REQ-028's frozen two-principal, human-approver-only topology; display metadata is deliberately excluded (PII minimization); `enrolled_at`/`enrollment_reference` are assigned to the audit trail instead (mirroring `AuthorityEvidence.election_reference`'s own HBDC-REQ-065 disposition — evidentiary metadata, not a registry field); signer linkage is already captured in the inverse direction by `SignerRecord.principal_id`. HPSE-REQ-007 freezes: no widening for these.

**A genuine, freshly-derived gap was found and is not papered over**: `PrincipalRecord` has **no `revoked_at` field at all** — confirmed by direct inspection of `_parse_principal`'s `allowed = {"principal_id", "status"}` set (no `revoked_at` member, unlike `SignerRecord`/`AuthorityRecord`/`DeploymentBinding`, all three of which carry `revoked_at: Optional[str] = None` plus a `_require_revoked_at_consistency` call). This is an asymmetry in the *existing, already-frozen* schema, not something this phase's own design introduces. HPSE-REQ-008 freezes the resolution: a future implementation phase SHALL widen `PrincipalRecord` to add `revoked_at`, symmetric with its three sibling records, before `revoke_principal` is implemented — an explicitly named, out-of-scope-for-this-phase `hatp_bootstrap.py` schema amendment (a file already bound into HMIC-001's `implementation_scope_digest`), requiring its own future contract text and independent verification. Until that lands, principal revocation timestamps live only in the audit trail.

## 6. `signer_key_id` — Semantics and Derivation (HPSE-REQ-009..012)

HATP-REQ-019(d) requires "a stable key/credential identity usable for enrollment." `_resolve_signer` (`hatp_signing_ceremony.py:528-556`) already establishes the live mechanism: `signer_key_id = provider.credential_identity()`, cross-checked against `trust_store.lookup_signer`. HPSE-REQ-010 reuses this exact mechanism for *enrollment* rather than *verification* — the provider's own live credential-identity exchange, never caller-invented, never human-typed.

**A load-bearing derivation detail was independently traced, not assumed from the governing prompt's own §28 suggestion** ("prefer cryptographic derivation... if compatible"): `hatp_fido2_provider.py::credential_identity()` (lines 270-276) **unconditionally raises** `HATPProviderUnavailableError`, with an explicit docstring: "Credential identity for a non-resident credential is established at enrollment time... and is not re-derivable from the device alone." This directly informs HPSE-REQ-011: `signer_key_id` is not a pure function of device state re-computable on demand — it is enrollment-ceremony *output*, captured once (during the one live moment the device is present and the ceremony runs) and durably persisted thereafter. `hatp_piv_provider.py`'s `PivHardwareProvider.credential_identity()` (lines 93-94) is an unconditional placeholder failure — PIV is not implemented at all yet, structurally present only so a future phase can complete it without changing any caller.

Encoding (HPSE-REQ-012): lowercase hexadecimal of the provider's raw credential-identity bytes, reusing `hardware-credentials.json`'s own existing `public_key_hex` convention (`hatp_hardware_credentials.py::_parse_credential`) rather than inventing a new one.

## 7. `SignerRecord` Schema (HPSE-REQ-013..014)

Already exists, unchanged: `signer_key_id`, `principal_id`, `provider_profile`, `status`, `revoked_at` — already symmetric with `DeploymentBinding`/`AuthorityRecord`'s revocation-timestamp discipline (unlike `PrincipalRecord`, §5's finding). No private-key material, PIN, or secret device state, mirroring `HardwareCredentialRecord`'s existing discipline exactly (HPSE-REQ-014).

## 8. Principal ↔ Signer Cardinality (HPSE-REQ-015..017)

One principal → zero or more signers; one signer → exactly one principal (already structurally guaranteed). **A genuinely-derived design decision, not copied from the `DeploymentBinding` rotation precedent**: signer rotation is modeled as two separate writer operations (`enroll_signer` for the new credential, then `revoke_signer` for the old), never a single in-place field overwrite — because `signer_key_id` *is* the credential's stable identity (§6); overwriting it in place would silently reassign what an already-referenced record's own primary key denotes, a failure mode `DeploymentBinding`'s in-place rotation never risks (its `repository_id` key never changes under rotation). This is HPSE-REQ-016, and it is the one place this phase explicitly rejected blindly copying the nearest existing precedent after checking why that precedent doesn't transfer.

## 9. `provider_profile` — Semantics and Vocabulary Decision (HPSE-REQ-018..020)

`HATP_HARDWARE_PROVIDER_V1` (`hatp_providers.py:183`) is affirmed as the sole vocabulary value, unchanged — 149O.20L.7O.2C already established this is the one real, closed, single-valued production constant; this phase's own independent re-read of `_PRODUCTION_HARDWARE_PROVIDER_PROFILES` confirms it is still exactly a one-member tuple. HPSE-REQ-019 freezes it as fixed, compile-time contract vocabulary, not registry-backed: a plugin/versioned provider registry was considered and rejected (§10 of the governing prompt explicitly warns against premature plugin architecture) — with exactly one closed value and an existing contract-amendment-gated extension path (HATP-REQ-020's own "no protocol interchangeability without proof" discipline), a runtime registry would add indirection without adding real capability. HPSE-REQ-020 closes the "unwired" gap 149O.20L.7O.2C named — at the *enrollment* layer: `SignerRecord.provider_profile` is captured from the enrolling provider's own `capabilities().provider_profile` and validated against the allowlist once, at enrollment time, rather than re-validated at every later `DeploymentBinding` creation.

## 10. Provider Profile Registry Decision

Resolved above (§9): fixed compile-time vocabulary, not registry-backed, not a versioned descriptor system. No provider configuration file distinct from the source-level constant exists anywhere in the codebase or on Dell (re-confirmed, matching 149O.20L.7O.2C's own §9 finding) — there is nothing host-specific to provision for the *profile itself*; only the physical hardware backing it is host-provisioned (§19 below).

## 11. `authority_scope` Architecture (HBDC-001 §16.2, HBDC-REQ-071..076)

149O.20L.7O.2C's own §20 concluded `authority_scope` does not fold into the Principal/Signer enrollment artifact — it has no vocabulary anywhere, conceptual or implemented, unlike the other three fields. This phase re-confirms that conclusion independently this session (fresh grep, fresh read of `hatp_bootstrap.py`/`hatp_deployment_binding_admin.py`/the HATP-001/HBDC-001 contract texts — no vocabulary, enum, or allowlist for `authority_scope` exists anywhere) and, per the governing prompt's own §44 instruction ("If authority_scope can be frozen in the same contract architecture without coupling it to signer enrollment, do so"), resolves it as a **narrow HBDC-001 amendment (§16.2, v1.1→v1.2)** rather than folding it into HPSE-001 — because `DeploymentBinding.authority_scope` is HBDC-001's own field (§16, §16.1), and HPSE-001 has no authority over a schema it does not own.

**A previously-unrecorded, independently-traced fact materially informs this decision**: `human_approval_trusted_provenance.py`'s two real production consumers of `AuthorityRecord` (lines ~881-891, ~1029-1034) check **only `authority.status == "active"`** — the *content* of `authority_scope` is never read, compared, or branched on by any code path in this repository, for either `AuthorityRecord.authority_scope` (the AG3/AG5 rollback-authority field) or, by the pre-existing 7O.2C finding, `DeploymentBinding.authority_scope`. This means the "minimum Class-B scope" question (§12 below) has an unusually clean answer: no existing consumer differentiates by value, so the vocabulary decision is bounded only by HBDC-001's own text, not by any hidden downstream branching logic that might require a richer or different literal.

## 12. Minimum Class-B Scope (HBDC-REQ-072)

`CLASS_B_DEPLOYMENT` — a single-member closed vocabulary, never `*`/`all`/`global`/`root`/`unrestricted` (HBDC-REQ-072, CBD-11). Selected because it names exactly the one authority a `DeploymentBinding` currently exists to express (Class-B deployment topology authority, HBDC-001 §1-§2) and no source evidence supports any narrower or differently-scoped literal — there is nothing to narrow further than "this is a Class-B deployment binding" given zero consumers branch on scope content (§11).

## 13. Scope Vocabulary Design (HBDC-REQ-071..076)

Token grammar: `^[A-Z][A-Z0-9_]*$` (all-caps snake case), mirroring `HATP_HARDWARE_PROVIDER_V1`'s own existing naming convention — no new grammar style invented (HBDC-REQ-072). Versioning: fixed, compile-time contract text, extensible only by a future HBDC-001 amendment — never runtime-configurable (HBDC-REQ-073), mirroring `_PRODUCTION_HARDWARE_PROVIDER_PROFILES`'s closed-tuple discipline exactly. Validation: a **named, not-yet-implemented** future producer amendment (HBDC-REQ-074) — additive to, not a replacement for, HBDC-REQ-058's existing non-empty-string check. Extensibility: strictly amendment-gated, matching every other closed vocabulary this codebase already uses (`_STATUS_VALUES`, `_PROTOCOL_VALUES`, `_PRODUCTION_HARDWARE_PROVIDER_PROFILES`).

## 14. Cross-Field Invariants (HPSE-REQ-047..048, HBDC-REQ-074)

Derived, not copied from 7O.2C's own (accurate, but purely descriptive) §11 cross-field table:

- **Signer must belong to principal.** Enforced at *enrollment* time (`enroll_signer` requires an existing active principal, HPSE-REQ-027) — a single point of validation, not re-checked at every later `DeploymentBinding` write.
- **Signer provider must equal binding provider_profile.** Closed by deriving `DeploymentBinding.provider_profile` from the enrolled `SignerRecord.provider_profile` at `DeploymentBinding`-creation time (HPSE-REQ-048/HBDC-REQ future work, §21-§22 below), rather than accepting it as independent caller input that could silently diverge.
- **Signer/principal must both be active.** Named as a required future `DeploymentBinding`-producer cross-check (HPSE-REQ-047), not implemented here.
- **Revoked signer/principal invalidates create/rotate.** Same future producer amendment; see §21 below for exactly what changes.
- **`authority_scope` must be permitted.** HBDC-001's own future producer amendment (HBDC-REQ-074), a distinct amendment from the Principal/Signer ones above since `authority_scope` is not part of the enrollment registry sections at all.

These are frozen as **required future work, explicitly not producer conventions left implicit** — the governing prompt's own §14 instruction ("do not leave these only as producer conventions") is satisfied by naming them as normative HPSE-REQ/HBDC-REQ text rather than leaving them as this report's prose alone.

## 15. Registry Architecture (HPSE-REQ-021..025)

No new registry: `registry.json`'s existing `{"registry_version": 1, "principals": [...], "signers": [...], "deployment_bindings": [...], "authorities": [...]}` shape (`hatp_bootstrap.py:406-455`) already has both `principals` and `signers` sections defined and parsed — this phase's writer populates two *already-specified* sections, it does not design a new document. Uniqueness (global, per-section, by `principal_id`/`signer_key_id`) is already mechanically enforced. Ordering: sort by key field on every write, mirroring `_registry_document_with_binding`'s existing `sort(key=lambda entry: entry["repository_id"])` convention exactly, applied to `principal_id`/`signer_key_id` respectively (HPSE-REQ-024). Unknown-field/corruption handling: already implemented by the existing closed-schema parser, reused unchanged (HPSE-REQ-025).

## 16. Enrollment Writer Contract (HPSE-REQ-026..029)

Exactly four mutating operations: `enroll_principal`, `revoke_principal`, `enroll_signer`, `revoke_signer` (HPSE-REQ-026) — no `rotate_principal` (principal_id never rotates), no single-call `rotate_signer` (§8's own two-operation rotation model). Standalone, non-agent-writable admin tool, invocable only by the admin OS principal, mirroring HBDC-REQ-056/066 exactly (HPSE-REQ-028/029).

## 17. Preview Semantics (HPSE-REQ-030)

Every mutating operation has a read-only preview counterpart, mirroring `preview_create_deployment_binding`'s "never writes" discipline and `DeploymentBindingPreviewKind`'s classification-enum shape exactly: would-enroll / already-enrolled / conflict / would-revoke / already-revoked / not-found.

## 18. Atomicity (HPSE-REQ-031..032)

Reuses `repository_identity.py::_write_atomic`'s exact idiom (`mkstemp` same directory, `fsync`, `os.replace`, symlink rejection before/after) — the identical idiom `hatp_deployment_binding_admin.py` already reuses. Read-back verification before reporting success, mirroring `_read_back_and_verify` exactly. No new idiom invented anywhere in this contract.

## 19. Locking / Concurrency (HPSE-REQ-033)

**A genuinely load-bearing correctness issue was found and resolved, not assumed away**: `principals`/`signers` and `deployment_bindings` all live in the *same* `registry.json` document. If the Principal/Signer writer used a separate, independently-named lock file from `hatp_deployment_binding_admin.py`'s existing `.deployment-binding-transition.lock`, two concurrent writer processes (one enrolling a signer, one creating a binding) could race on the same underlying file — a split-brain write, exactly the failure mode `hatp_deployment_binding_admin.py`'s own module docstring already goes out of its way to prevent for its own writes. HPSE-REQ-033 resolves this: both writers acquire the *identical* fixed lock-file path — a shared, whole-registry-document transition lock, not two section-scoped locks — requiring no change to the existing `hatp_deployment_binding_admin.py` module, only a shared naming convention in the new one.

## 20. Error Vocabulary (HPSE-REQ-034)

A closed, distinct hierarchy rooted at `HATPPrincipalSignerAdminError`: principal/signer not found, duplicate principal/signer, signer/principal mismatch, unsupported provider profile, revoked principal/signer, malformed registry (reusing `HATPTrustStoreMalformedError`), read-back mismatch. No bare `ValueError` for any of these — mirroring `hatp_deployment_binding_admin.py`'s own typed-exception discipline exactly, not the generic-exception style the governing prompt explicitly warns against.

## 21. Fail-Closed Behavior (HPSE-REQ-035..037)

Absent `registry.json` → EMPTY (zero enrolled, not an error — matches the current live Dell state exactly, per 149O.20L.7O.2C's own re-confirmed observation). Malformed `registry.json` → INVALID, fail closed, never partially accepted. Missing/revoked principal, or duplicate `principal_id`/`signer_key_id` → fail closed with the specific typed error (never silently coerced to a different outcome).

## 22. Audit Discipline (HPSE-REQ-038..039)

Ordering: validate → mutate atomically under the shared lock → read back and verify → emit audit → return — identical to `hatp_deployment_binding_admin.py`'s own already-established ordering. **The governing prompt explicitly asked whether this phase can avoid reproducing the known audit-after-durable-write defect "if architecture permits" — it was considered, and the honest, derived conclusion is that it does not, without disproportionate new machinery**: the alternative ordering (commit audit before state) was evaluated and rejected because it does not close the underlying problem, it only relocates it to the opposite failure mode (an audit record asserting an enrollment that never durably wrote). Genuinely closing this would require a real two-phase-commit mechanism across two independently-atomic storage systems — new, untested machinery this architecture-only phase declines to invent. HPSE-REQ-039 therefore accepts the identical disclosed limitation `hatp_deployment_binding_admin.py` already carries, names a future reconciliation-scan tool as the only available mitigation short of real 2PC, and does not pretend to have solved what it has not.

## 23. Enrollment Authority (HPSE-REQ-040..041)

Three roles kept explicitly distinct even when one physical person occupies all three under HATP-REQ-028's frozen two-principal topology: human decision authority (elects/authorizes), admin execution principal (runs the writer), enrolled human principal (the `principal_id` subject). Self-enrollment by the admin is not exempt from the same fresh-election requirement as enrolling anyone else (HPSE-REQ-041, extending HATP-REQ-040's existing agent-self-enrollment prohibition to this specific admin-self-enrollment case, which HATP-REQ-040 does not itself literally cover).

## 24. CHGR / Election Requirements (HPSE-REQ-042..043)

All four mutating operations require fresh, separate election evidence, mirroring HBDC-REQ-064 exactly; the reference is audit metadata only, never cryptographically verified by the writer, mirroring HBDC-REQ-065 exactly. Enrollment is treated as authority-bearing — it changes a trusted registry — exactly as the governing prompt's own §24 instruction anticipated ("likely, unless primary contracts prove otherwise"); nothing in HATP-001/HBDC-001 proves otherwise, so the full election discipline applies without exception.

## 25. Physical Credential Requirement (HPSE-REQ-044)

**Not weakened.** HATP-REQ-021 already forbids a software-key substitution absent an explicit future contract version/profile naming one satisfying every `HATP_HARDWARE_PROVIDER_V1` property; this contract records — rather than dissolves — the current absence of any FIDO2/PIV device on the target Dell host (149O.20L.7O.2C §7/§16, not re-verified live this session since no new Dell session was opened; this phase relies on that immediately-preceding, same-day, independently-verified finding rather than re-running the identical read-only inspection) as a named future provisioning prerequisite, exactly as the governing prompt's §25 instructs.

## 26. Credential Provisioning Boundary (HPSE-REQ-045..046)

Credential provisioning (physical device usable on-host) is separated from credential enrollment (this contract's writer) is separated from `DeploymentBinding` creation (HBDC-001 §16.1's existing producer). Sequence (HPSE-REQ-046): provisioning → principal enrollment → signer enrollment → independent verification → `DeploymentBinding` proposition → election + CHGR (a *separate* election from the enrollment elections) → binding creation → independent real-host verification. No step is collapsed or reordered from what the source material supports.

## 27. Human Principal First-Use Model

No `principal_id` value is assigned by this phase. The selection *procedure* for a later election/provisioning phase: the Human/Admin operator freely chooses a `principal_id` at enrollment-ceremony time, subject only to non-empty-string shape, mechanically-enforced uniqueness, and HPSE-REQ-002's OS-identity-independence rule — no mechanical derivation formula is specified or needed, since HATP-REQ-037 already frames this as an admin *assignment*, not a computed value.

## 28. Signer-Key Identifier Derivation

Resolved in full at §6/HPSE-REQ-010..012 above: derived once, live, from the provider's own `credential_identity()` at enrollment time; durably recorded, not re-derivable on demand thereafter (per FIDO2's own documented behavior); encoded as lowercase hex, reusing the existing `public_key_hex` convention. No real key was generated, imported, or derived in the production of this phase's report.

## 29. `provider_profile` Derivation

Resolved at §9/§14/§22 above (HPSE-REQ-048): captured from the enrolling provider's own `capabilities().provider_profile` at signer-enrollment time; a future `DeploymentBinding` producer amendment derives it from the referenced signer's registry entry rather than accepting independent, potentially-mismatched caller input.

## 30. `authority_scope` Validation Ownership

HBDC-001 exclusively (§11 above) — HPSE-001 has no authority over a field it does not govern. A future producer amendment (HBDC-REQ-074) is the single validation point; HBDC-REQ-042's conformance check remains deliberately unamended (§32 below explains why).

## 31. `DeploymentBinding` Producer Amendments (Named, Not Built) — HPSE-REQ-047

A future HBDC-001 amendment SHALL require `create_deployment_binding`/`rotate_deployment_binding` to: (1) confirm `principal_id` exists and is `active`; (2) confirm `signer_key_id` exists and is `active`; (3) confirm the signer's own `principal_id` equals the supplied `principal_id`; (4) derive `provider_profile` from the signer's registry entry (§29); (5) validate `authority_scope` against HBDC-001 §16.2's closed vocabulary (a distinct amendment, HBDC-REQ-074). None of this is implemented by this phase — HPSE-REQ-047 names it as required future contract text.

## 32. HBDC Implications — Reasoned, Not Assumed

**Is a `DeploymentBinding` with fake principal/signer/scope currently capable of satisfying HBDC-REQ-042? Yes, today, unchanged by this phase.** `_check_deployment_identity`/`deployment_binding_matches` validate only `repository_id`/`canonical_deployment_root`/`status` (149O.20L.7O.2C §14, independently re-confirmed this session by re-reading the same functions). This phase's own considered conclusion, per the governing prompt's explicit "be conservative" instruction: **this is intentional and should remain so** — HBDC-REQ-042's own stated job (§16) is repository/root matching, the copy/clone/theft defense; it was never HBDC-REQ-042's job to validate principal/signer/scope *content*, and folding that in would duplicate, not add to, the assurance the future producer-side amendment (§31/HBDC-REQ-074) already provides at write time. **This conclusion carries an explicitly disclosed conditional**: it is only correct once §31's producer amendment is actually implemented; until then, a residual risk window exists in which today's unamended producer could still write an internally-inconsistent `DeploymentBinding` that would pass HBDC-REQ-042 undetected. HBDC-REQ-076 records this exact reasoning and its conditional in the contract text itself, not only in this report.

## 33. HMIC Implications

Not amended by this phase. The future implementation module (`hatp_principal_signer_admin.py`) and companion script are named (§26/HPSE-001 §26) as expected future members of HMIC-001's frozen `_FROZEN_SRC_PCAE_RELATIVE_FILES`/`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`, mirroring the exact v1.4 precedent that bound `hatp_deployment_binding_admin.py`; this new contract file itself is named as an expected future sixth bound-contract entry, mirroring HBDC-001's own v1.2 (149O.20D.1/149O.20F) binding precedent. **Does HMIC need registry-content binding, not just producer-byte binding, for principal/signer records specifically? Considered and rejected for v1.0**: HMIC's existing, disclosed design philosophy (149O.20L.7O.2C §14) is producer byte-integrity, not live-value re-validation at certification time; §32's own reasoning (validate at the write boundary, not the read/certify boundary) applies identically here. The residual risk this leaves — an out-of-band raw-filesystem edit to `registry.json` bypassing the writer entirely — is a speculative future-hardening concern with no current evidence requiring it, not a v1.0 HPSE-001 requirement.

## 34. Revocation Semantics (HPSE-REQ-049..050)

Revoking a `PrincipalRecord`/`SignerRecord` does **not** cascade to an already-created `DeploymentBinding` that copied the (now-stale) `principal_id`/`signer_key_id` at creation time — `DeploymentBinding` stores field copies, not live references, and no cascade/join logic exists anywhere in the current code (confirmed by absence, this session). This is the concrete, traced instance of §32's disclosed residual-risk window, named as HBDC-001's own future decision to make (extending HBDC-REQ-042), not HPSE-001's. **A second, independently-traced asymmetry**: `_resolve_signer` (proof *production*) checks only `SignerRecord.status`, never the referenced principal's status; `human_approval_trusted_provenance.py`'s verification path *does* check `PrincipalRecord.status` separately. This is confirmed intentional, not a defect — production succeeding against a revoked principal's still-active signer simply produces a proof that fails at the verification boundary, the actually security-relevant checkpoint (HATP-REQ-016-018's model).

## 35. Time Semantics (HPSE-REQ-052)

Identical strict grammar to HBDC-REQ-067 (`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$`), no new grammar invented, applied to `SignerRecord.revoked_at` today and to `PrincipalRecord.revoked_at` once §5's schema widening lands.

## 36. Provider/Runtime Separation (HPSE-REQ-051)

Freshly re-derived, not merely re-asserted from 149O.20L.7O.2C §22: `provider_profile` denotes the signing-hardware security-property class only (HATP-REQ-019(a)-(e)); nothing traced this session in `hatp_providers.py`, `hatp_fido2_provider.py`, `hatp_piv_provider.py`, `hatp_signing_ceremony.py`, or `hatp_bootstrap.py` ties it to agent-runtime identity. The enrollment writer itself is reachable only via a standalone, non-agent-invocable script (HPSE-REQ-028/029/051), never through any runtime-adapter code path — Claude, Codex, DeepSeek Harness, or any future adapter remain equally and entirely irrelevant to this trust layer.

## 37. Disposable Examples (Non-Authoritative)

Clearly-fake illustrative records, never written anywhere, never touching real state:

```
NON-AUTHORITATIVE EXAMPLE — DISPOSABLE, ILLUSTRATIVE ONLY:

PrincipalRecord(
  principal_id="DISPOSABLE-EXAMPLE-PRINCIPAL-NOT-REAL",
  status="active",
)

SignerRecord(
  signer_key_id="deadbeef00112233445566778899aabbccddeeff",  # lowercase hex, illustrative
  principal_id="DISPOSABLE-EXAMPLE-PRINCIPAL-NOT-REAL",
  provider_profile="HATP_HARDWARE_PROVIDER_V1",
  status="active",
  revoked_at=None,
)

DeploymentBinding(
  repository_id="0107866f-af7c-40b4-8317-74e71acb05ca",  # real repository_id, illustrative context only
  canonical_deployment_root="/opt/pcae/runtime/src",
  principal_id="DISPOSABLE-EXAMPLE-PRINCIPAL-NOT-REAL",
  signer_key_id="deadbeef00112233445566778899aabbccddeeff",
  provider_profile="HATP_HARDWARE_PROVIDER_V1",
  authority_scope="CLASS_B_DEPLOYMENT",
  valid_from="2026-08-18T00:00:00.000Z",
  status="active",
  revoked_at=None,
)
```

No file was written; no producer function was invoked against any real or disposable store this phase (unlike 149O.20L.7O.2C's own §17, this phase performs no code execution at all — it is contract-text-only).

## 38. Contract Artifact Choice

Two artifacts, matching 149O.20L.7O.2C's own §20 "two, not four, patches" conclusion and the governing prompt's own "prefer separation of concerns" instruction:

1. **New companion contract**: `docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md` (HPSE-001 v1.0) — formalizes HATP-REQ-036/037 into concrete requirements, mirroring HSCE-001's own "additive, not amending" relationship to HATP-001.
2. **Narrow HBDC-001 amendment**: v1.1 → v1.2, new §16.2 (HBDC-REQ-071..076, CBD-11) — `authority_scope` vocabulary, since that field belongs to HBDC-001's own `DeploymentBinding` schema, not to the Principal/Signer registry.

Neither is a HATP-001 section amendment: HATP-001 remains the conceptual-procedure source (HATP-REQ-036/037), unamended, exactly mirroring how HSCE-001 formalizes HATP-001's signing-ceremony prose without amending HATP-001 itself.

## 39. Normative Requirement Numbering

HPSE-001: `HPSE-REQ-001` through `HPSE-REQ-052`, sequential, no gaps, no duplicates (mechanically verified this session: 52 distinct integers, range 1-52, zero missing). A distinct namespace from `HATP-REQ-*`/`HBDC-REQ-*`/`HMIC-REQ-*`/`HSCE-REQ-*`, mirroring HSCE-001's own separate-namespace precedent. HBDC-001's amendment continues its own existing sequence: `HBDC-REQ-071` through `HBDC-REQ-076` (mechanically verified: all six present exactly once), plus `CBD-11`. No existing requirement ID in either contract was renumbered, superseded, or reused.

## 40. Implementation Boundary (Named, Not Created)

Future production surfaces, mirroring `hatp_deployment_binding_admin.py`/`scripts/hatp_deployment_binding_admin.py`'s exact naming and layout precedent: `src/pcae/core/hatp_principal_signer_admin.py` (the writer module, sibling to `hatp_bootstrap.py`, never imported by `cli.py`/`commands/agent.py`/`core/agent.py`) and `scripts/hatp_principal_signer_admin.py` (the standalone admin-tool entrypoint, outside `src/pcae/`, not packaged, not console-script-installed). Neither file is created by this phase.

## 41. HMIC Source-Scope Consequence

Resolved at §33 above: yes, expected — both the future module and script, plus this phase's new contract file, are named as future HMIC-001 frozen-set members, mirroring the exact v1.4/v1.2 precedents already established for `hatp_deployment_binding_admin.py` and `HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` respectively. HMIC-001 itself is not amended by this phase.

## 42. Verification Architecture

This contract SHALL undergo its own independent verification (mirroring HBDC-001 v1.1's own 149O.20L.7G → 149O.20L.7H precedent, and HBDC-001 v1.0's own 149O.20B → 149O.20C precedent) before any implementation phase builds against it. Recommended: 149O.20L.7O.2D.1 (§47 below).

## 43. First-Use Sequence After Implementation

Derived, matching the governing prompt's own smallest-correct-sequence instruction, and consistent with — but independently re-derived from, not copied from — 149O.20L.7O's own general chain shape: contract architecture (this phase) → independent contract verification (149O.20L.7O.2D.1) → enrollment-writer implementation → independent implementation verification → hardware-credential provisioning (a real-host prerequisite, not a code phase) → principal/signer enrollment ceremony → independent enrollment-state verification → `DeploymentBinding` producer amendment (§31) implementation + its own independent verification → `DeploymentBinding` proposition → election + CHGR → binding creation → independent real-host verification.

## 44. `authority_scope` Disposition

Frozen in the same overall phase as the Principal/Signer contract but as a *separate contract artifact* (HBDC-001 §16.2, not HPSE-001) — resolved explicitly at §11/§38 above: it is small and narrow enough to resolve without coupling it to signer enrollment, but it belongs to a different contract's schema, so "same phase, different artifact" — not "same document" — is the correct granularity. No free-form acceptance remains specified as acceptable in future production text: HBDC-REQ-071 closes it to a one-member closed vocabulary.

## 45. Current Live State Preservation

Unchanged, not re-touched this session (§2): `RepositoryIdentity` `0107866f-af7c-40b4-8317-74e71acb05ca`; `DeploymentBinding` ABSENT; Protected Root EMPTY; HBDC NON_COMPLIANT, sole residual `HBDC-REQ-042`. No Dell command of any kind — read or write — was issued this phase; this is a pure contract-text/documentation phase over already-verified source and already-verified (same-day, immediately-prior-phase) Dell facts.

## 46. Final Verdict

**HATP PRINCIPAL/SIGNER ENROLLMENT CONTRACT ARCHITECTURE READY FOR INDEPENDENT VERIFICATION.**

Both new/amended contract artifacts (HPSE-001 v1.0, HBDC-001 v1.2 §16.2) are internally self-consistent, requirement-numbering-complete (§39), reuse every existing atomicity/locking/audit/error idiom this codebase already establishes rather than inventing parallel ones, and explicitly name — as normative requirement text, not merely prose — every piece of required future work this architecture phase does not itself perform: the `PrincipalRecord.revoked_at` schema widening (HPSE-REQ-008), the `DeploymentBinding` producer cross-validation amendment (HPSE-REQ-047/048, HBDC-REQ-074), the HMIC frozen-set binding (§33/§41), and the revocation-cascading decision left to a future HBDC-001 amendment (HPSE-REQ-049). None of these open items blocks this phase's own completeness as an *architecture* document — each is a fully specified pointer to a distinct, later, independently-verified phase, not an unresolved ambiguity in this phase's own text. Readiness is not forced: had any of the four target fields (`principal_id`/`signer_key_id`/`provider_profile`/`authority_scope`) lacked a derivable, closed resolution from primary source, this verdict would instead have been "REQUIRES ADDITIONAL DESIGN" — that did not occur.

## 47. Recommended Next Phase

**149O.20L.7O.2D.1 — HATP Principal/Signer Enrollment Contract Independent Verification.** That phase must independently attack: principal semantics (HPSE-REQ-001..008, including the disclosed `PrincipalRecord.revoked_at` gap), signer semantics (HPSE-REQ-009..017), provider profile (HPSE-REQ-018..020), authority_scope vocabulary (HBDC-REQ-071..076), registry schema (HPSE-REQ-021..025), the enrollment writer's API/preview/atomicity/locking design (HPSE-REQ-026..033), error vocabulary (HPSE-REQ-034), fail-closed behavior (HPSE-REQ-035..037), audit ordering (HPSE-REQ-038..039), enrollment authority separation (HPSE-REQ-040..041), election/CHGR requirements (HPSE-REQ-042..043), the hardware-credential prerequisite (HPSE-REQ-044..046), the named-but-unbuilt `DeploymentBinding` producer amendments (HPSE-REQ-047..048), the disclosed revocation-cascading gap (HPSE-REQ-049..050), runtime-provider separation (HPSE-REQ-051), timestamp grammar (HPSE-REQ-052), and both contracts' HMIC/HBDC-REQ-042 consequences (§32-§33). No implementation. Only after clean independent verification should implementation planning/building begin.

## 48. Strategic Breakpoint (Unchanged)

The approved breakpoint stands exactly as recorded by 149O.20L.7O/7N/7O.2C: after `DeploymentBinding` first-use is executed and independently verified, and HBDC reaches its intended clean state, pause before Boundary C; then begin (1) DeepSeek Harness vs PCAE Comparative Architecture Study, (2) PCAE Runtime Adapter + Plugin Architecture. This phase does not begin either study — it remains further from Boundary C than 7O.2C left it, having produced two new not-yet-independently-verified contract artifacts that must clear their own IV cycle before the enrollment-writer implementation phase (itself a further prerequisite) can even begin.

## 49. Proof — No Dell Mutation / No Provisioning / No DeploymentBinding / No Election / No CHGR / No Certification

- **No Dell mutation**: zero commands of any kind were issued against `hac-dell` this phase — not even a read. §2/§45 reuse 149O.20L.7O.2C's own same-day, independently-verified facts rather than re-querying them.
- **No signer/principal provisioning or enrollment**: `enroll_principal`/`enroll_signer`/`revoke_principal`/`revoke_signer` do not exist as code; nothing resembling them was executed. `registry.json` remains absent on Dell (unverified freshly this session, per §2, but unchanged by anything this phase did, since nothing this phase did could have altered it).
- **No `DeploymentBinding` created**: `create_deployment_binding`/`rotate_deployment_binding`/`revoke_deployment_binding`/any preview variant were never invoked this phase — this phase performed zero Python execution of any kind, contract-text and documentation only.
- **No election initiated**: no decision-session, no proposition text presented for approval, no real `election_reference` created or referenced as authorizing anything (the disposable examples in §37 use an explicitly labeled placeholder timestamp/IDs, never presented as real).
- **No CHGR published**: no `chgr-*` record created, read for mutation, or referenced as authorizing anything.
- **No certification performed**: `verify_hatp_proof`, `hatp_mandatory_certification.py`'s certification entry points, and every HMIC certification path were never invoked.

## 50. Tests

`tests/test_phase_149o_20l_7o_2d_hatp_principal_signer_enrollment_contract_architecture.py` — self-consistency assertions: both contract documents exist and are internally requirement-numbering-complete (no gaps/duplicates in `HPSE-REQ-*`/the new `HBDC-REQ-07[1-6]` range); the new HBDC-001 header correctly states v1.2; `PrincipalRecord`/`SignerRecord` source-fact claims (schema fields, the `revoked_at` asymmetry) re-verified directly against current `hatp_bootstrap.py` source; `HATP_HARDWARE_PROVIDER_V1`/`_PRODUCTION_HARDWARE_PROVIDER_PROFILES` claims re-verified against current `hatp_providers.py` source; no production `.py` file under `src/pcae/` or `scripts/` was modified by this phase (mechanically checked against the phase-entry commit's tree).

## 51. Governance Results

- `pcae status coherence`: pass
- `pcae health`: pass
- `pcae check`: pass
- `python -m pytest -n auto`: fast_green tier green (see final commit's recorded counts)
- Pre-existing `tests/test_hatp_deployment_binding_admin.py`, `tests/test_phase_149o_20l_7o_2c_deploymentbinding_first_use_field_resolution_architecture.py`: unchanged, all passing, re-confirmed this session with zero modification.

## 52. Commits, Push Status, `origin/main..HEAD`

See `.pcae/phase-completion-metadata.json`/`.pcae/phase-completion-report.md` for the exact commit hash, push status, and `origin/main..HEAD` diff recorded at phase completion.
