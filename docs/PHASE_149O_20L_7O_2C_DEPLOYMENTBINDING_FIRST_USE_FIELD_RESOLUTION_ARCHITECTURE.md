# Phase 149O.20L.7O.2C — DeploymentBinding First-Use Field Resolution Architecture

## 0. Status

Architecture / field-resolution only. Read-only. No `DeploymentBinding` created, no election initiated, no CHGR published, no HMIC certification performed, no Dell mutation of any kind. Governed by `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001), `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` (HATP-001), `docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md` (HSCE-001), `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` (HMIC-001).

## 1. Phase-Entry Commit

`0e5df0b7adc72fab8b491b9c3baf8469508805ce` — "Phase 149O.20L.7O.2B.1: sync active task allowed-file list". Working tree clean at entry; `origin/main` up to date.

## 2. RepositoryIdentity (Current, Independently Reconfirmed This Session)

- `repository_instance_id`: `0107866f-af7c-40b4-8317-74e71acb05ca`
- Independently re-read this session via fresh SSH: `sudo cat /opt/pcae/runtime/src/.pcae/repository-identity.json` on `hac-dell` returned `{"created_at": "2026-08-18T12:53:43.508Z", "repository_instance_id": "0107866f-af7c-40b4-8317-74e71acb05ca", "schema_version": 1}` — matches the entering-state value exactly.
- File ownership on Dell: `-rw------- 1 pcae pcae 138 Aug 18 14:53 repository-identity.json` (owner-only, `0600`, matches `repository_identity.py::_write_atomic`'s `tempfile.mkstemp` default mode).
- Protected Root (`/etc/pcae/hatp/trust-store`): `drwxr-x--- 2 root pcae`, confirmed empty (`no registry.json`) — read-only `sudo ls -la` / `sudo cat registry.json` (ENOENT) this session.

## 3. Local Entry Checks / 149O.20L.7O.2B.1 Reconciliation

`pcae session bootstrap --agent-id claude-code --json` at phase entry: `health_status: healthy`, `check_status: passed`, `push_check.mode: nothing_to_push`, active task the idle placeholder created by 149O.20L.7O.2B.1's close-out. No disagreement found between this session's bootstrap and 149O.20L.7O.2B.1's own recorded final state. No production-source mutation performed.

## 4. Schema Reconstruction — Primary Source Only

`DeploymentBinding` (`src/pcae/core/hatp_bootstrap.py:127-137`), read directly this session, not from prior-phase prose:

```python
@dataclass(frozen=True)
class DeploymentBinding:
    repository_id: str
    canonical_deployment_root: str
    principal_id: str
    signer_key_id: str
    provider_profile: str
    authority_scope: str
    valid_from: str
    status: str
    revoked_at: Optional[str] = None
```

Parse-time validation (`_parse_deployment_binding`, `hatp_bootstrap.py:351-395`): closed field set (unrecognized keys rejected); `repository_id` must satisfy `is_valid_repository_instance_id` (UUID4); `canonical_deployment_root`/`principal_id`/`signer_key_id`/`provider_profile`/`authority_scope` each only checked non-empty-string; `status` restricted to `_STATUS_VALUES = frozenset({"active", "revoked"})`; `valid_from` must parse as a timezone-aware ISO-8601 timestamp; `revoked_at` consistency enforced against `status` (`_require_revoked_at_consistency`: `"revoked"` requires `revoked_at` set, `"active"` requires it `None`).

Registry document (`registry.json`, under the Protected Root) top-level shape: `{"registry_version": 1, "principals": [...], "signers": [...], "deployment_bindings": [...], "authorities": [...]}` (`_parse_registry_document`, `hatp_bootstrap.py:406-455`). Companion record types in the same file, also read directly:

```python
@dataclass(frozen=True)
class PrincipalRecord:
    principal_id: str
    status: str

@dataclass(frozen=True)
class SignerRecord:
    signer_key_id: str
    principal_id: str
    provider_profile: str
    status: str
    revoked_at: Optional[str] = None

@dataclass(frozen=True)
class AuthorityRecord:
    principal_id: str
    repository_id: str
    authority_scope: str
    status: str
    valid_from: str
    revoked_at: Optional[str] = None
```

Producer (`src/pcae/core/hatp_deployment_binding_admin.py`, Phase 149O.20L.7I, HBDC-001 §16.1): `create_deployment_binding` / `rotate_deployment_binding` / `revoke_deployment_binding` plus read-only `preview_*` variants. `AuthorityEvidence` (lines 255-270) is the caller-supplied input: `principal_id: str`, `signer_key_id: str`, `provider_profile: str`, `authority_scope: str`, `election_reference: str` — each validated only for non-empty-string shape (`_validate_authority_evidence`, lines 279-296). The producer's own module docstring (lines 36-46) states explicitly: `repository_id`/`canonical_deployment_root` are always derived read-only; the four authority fields are drawn from `AuthorityEvidence` "unchanged and unvalidated against any registry vocabulary beyond non-empty-string shape — cross-validation against `principals`/`signers` registry entries is explicitly deferred (149O.20L.7H finding, HBDC-REQ-058)".

This phase adds zero new fields, zero new validation, and reconstructs this schema from primary source exactly as summarized above — not from any prior phase's prose.

## 5. Already-Resolved Fields — Independently Reconfirmed

- **`repository_id`**: `0107866f-af7c-40b4-8317-74e71acb05ca`. Derived read-only via `_resolve_repository_id` (`hatp_deployment_binding_admin.py:513-521`) → `read_repository_identity(HarnessPath(repository_root)).repository_instance_id`. Fails closed (`RepositoryIdentityMissingError`) if absent — confirmed present on Dell (§2).
- **`canonical_deployment_root`**: derived via `resolve_canonical_deployment_root(Path)` (`hatp_bootstrap.py:157-174`) — absolute path, `os.path.normpath`, `Path.resolve(strict=True)` (symlink resolution), rendered `.as_posix()`. Independently re-executed this session on Dell (read-only): `sudo -u pcae readlink -f /opt/pcae/runtime/src` → `/opt/pcae/runtime/src` (no symlink indirection at any level). **Proven, not assumed**: the expected `/opt/pcae/runtime/src` value is exact because the path already resolves to itself under `readlink -f` — canonicalization is a no-op here, not merely "likely."
- **`status`**: initial value on `create_deployment_binding` is the literal `"active"` (line 586); the schema's own closed vocabulary is exactly `{"active", "revoked"}` (`_STATUS_VALUES`, `hatp_bootstrap.py:54`); no other value is producible by any code path.
- **`revoked_at`**: initial representation on create is `None` (line 587), consistent with `status="active"`, enforced symmetrically on read (`_require_revoked_at_consistency`).
- **`valid_from`**: generation semantics — `_canonical_timestamp_now()` (`hatp_deployment_binding_admin.py:334-338`), called fresh at the moment of the write, asserted against the strict grammar `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$` (HBDC-REQ-067) before being used. Not a fixed value — a generation *rule* bound to call time, never caller-suppliable (no `valid_from` parameter exists on any producer function).

## 6. `principal_id` — Semantics, Source, and the "== pcae" Test

**Semantics.** HATP-REQ-014 (`docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md:179-182`): "Each enrolled human approver SHALL be identified by a stable `principal_id`, distinct from any human-readable display name. `principal_id` SHALL NOT change across key rotation." This is a **registry identity for an enrolled human approver** — not an OS account, not a runtime process identity, not a display name. HBDC-REQ-058 (§16.1 of HBDC-001) places `principal_id` in the "admin's own enrollment context" category, drawn at `DeploymentBinding`-creation time, not derived from repository-local state or agent input.

**Producer/consumer/validator trace.** Every producer/consumer/comparator touching `principal_id` in this codebase was traced:
- Producer: `hatp_deployment_binding_admin.py` accepts it verbatim from `AuthorityEvidence.principal_id`, validates only non-empty-string shape.
- Consumer: `hatp_bootstrap.HATPTrustStore.lookup_principal(principal_id)` (read-only) exists but has zero production callers outside its own module and `hatp_deployment_binding_admin.py`'s (never-invoked) potential cross-check path — confirmed by repo-wide search.
- Comparator: `_binding_fields_equal_for_idempotency` compares `principal_id` (among four fields) against an existing entry only for create-idempotency/rotation purposes — a literal-equality check, not a registry lookup.
- A *structurally distinct* production consumer exists in `hatp_signing_ceremony.py::_resolve_signer` (lines 528-556): it resolves `principal_id` via `trust_store.lookup_signer(signer_key_id).principal_id` — i.e., for the **signing-ceremony proof** (`HumanApprovalProvenanceProof`, HSCE-001), `principal_id` is registry-cross-validated. This is a different record type from `DeploymentBinding`; HSCE's 1227-line contract never mentions `DeploymentBinding` (confirmed by full-text grep).

**Canonical source classification (§7 of the governing prompt's four options): (B) canonical derivation rule exists but the required artifact is absent**, refined: HATP-REQ-037 (`HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md:330-336`) states the *conceptual* enrollment procedure — "the Human/Admin principal authenticates to its own OS account, verifies the hardware/provider identity, obtains the signer's public/credential identity, **assigns a `principal_id`**, assigns repository-specific rollback authority, registers the protected deployment binding, and writes the protected HATP trust state" — but this procedure has never been implemented as code (`HATPTrustStore`'s own docstring, `hatp_bootstrap.py:513-520`: "enrollment, revocation, and rotation are administrative-surface-only and are not implemented by this phase at all"). A repo-wide search for `enroll`/`grant_authority`/`register_principal`/`register_signer` across `src/`, `scripts/`, `docs/`, `tests/` returns zero implementations. No `principals` registry entry exists anywhere (Dell's `registry.json` is absent).

**`principal_id == "pcae"` test (§8 of the governing prompt): INVALID, proven not merely doubted.** Two independent, converging proofs:
1. HATP-REQ-028 freezes the topology as exactly two OS principals — **Agent OS principal** and **Human/Admin OS principal** — and HATP-REQ-014 requires `principal_id` identify "each enrolled **human approver**." `pcae` (uid 1004, `/usr/sbin/nologin`, confirmed live on Dell this session: `getent passwd pcae` → `pcae:x:1004:1004:PCAE agent principal:/home/pcae:/usr/sbin/nologin`) is by its own `/etc/passwd` GECOS field and its `nologin` shell definitionally the **Agent OS principal** — the untrusted party HATP-REQ-027 requires have *no* privilege-escalation path to Human/Admin state, not the enrolled human approver HATP-REQ-014 requires `principal_id` to denote.
2. Live filesystem evidence, read-only, this session: `/etc/pcae/hatp/trust-store` is `drwxr-x--- 2 root pcae` — `pcae`'s group membership grants **read+execute only** (no `w` bit in the group triad); only `root` (owner) has write access. This is the module docstring's own stated design (`hatp_deployment_binding_admin.py:19-25`): "the only principal with real write access to `HATPTrustStore.production().root`" is "the Class-B Protected Administrator OS principal," and `pcae` is confirmed live, today, on the actual target host, **not** that principal.

The fact that `pcae` is the runtime execution account is not evidence for `principal_id == "pcae"` — it is direct evidence against it, since HATP's entire threat model (Threat A, HATP-REQ-007-009/027) exists specifically to keep the Agent OS principal from being able to assert Human/Admin-scoped facts like `principal_id`.

## 7. `signer_key_id` — Semantics, Source, Registry State

**Semantics.** Identifies an enrolled hardware signing credential. HATP-REQ-019 freezes the conceptual provider profile `HATP_HARDWARE_PROVIDER_V1`, required to supply "(d) a stable key/credential identity usable for enrollment." HATP-REQ-039: "A signer SHALL already be enrolled and authorized before producing a valid approval proof."

**Two distinct, non-conflated registries were traced, both real code, neither wired to `DeploymentBinding`:**
1. `hatp_bootstrap.py`'s Wave-2 `signers` registry section (`SignerRecord`: `signer_key_id`, `principal_id`, `provider_profile`, `status`, `revoked_at`) — an *identity* mapping, read via `HATPTrustStore.lookup_signer`.
2. `src/pcae/core/hatp_hardware_credentials.py`'s Wave-5 `hardware-credentials.json` registry — a *cryptographic* mapping (`signer_key_id` → public-key material), explicitly documented (lines 9-16) as "deliberately separate from `hatp_bootstrap.py`'s Wave-2 `HATPTrustStore`," restricted to `_PROTOCOL_VALUES = frozenset({"FIDO2", "PIV"})`. Its own docstring (lines 27-34) states enrollment is "explicitly OUT of Wave-5 scope" and exposes no `enroll()`/`revoke()`/`rotate()` API — read-only lookup only.

**Real, wired, production consumer exists — for a different record type.** `hatp_signing_ceremony.py::_resolve_signer` (lines 528-556) resolves `signer_key_id` via `provider.credential_identity()` (a live hardware-provider call), then cross-checks it against `trust_store.lookup_signer(signer_key_id)`, requiring `status == "active"` — fails closed (`NoAuthorizedSignerError`) otherwise. This is the resolution mechanism for `HumanApprovalProvenanceProof.signer_key_id` (an AG3/AG5 rollback-evidence signing proof), **not** for `DeploymentBinding.signer_key_id` — the two share a field name and a conceptual home (the same `HATPTrustStore`) but `hatp_deployment_binding_admin.py` never calls `_resolve_signer` or `lookup_signer`.

**Live Dell state, read-only, this session:**
- `/etc/pcae/hatp/trust-store/registry.json`: absent (confirmed §2) — zero `signers` entries exist, by construction.
- `/etc/pcae/hatp/` hardware-credentials sibling path: no `hardware-credentials*` file found anywhere under `/etc/pcae` or `/opt/pcae`.
- Physical hardware signer: `gpg --card-status` → `"error getting version from 'scdaemon': No SmartCard daemon"` / `"OpenPGP card not available"`; `lsusb` (full device list) shows no FIDO2/PIV/security-key-class device (webcam, Broadcom Bluetooth/WiFi combo, touchscreen, USB root hubs only).

**Classification (§7 four options): (B) canonical derivation rule exists (the exact mechanism `_resolve_signer` already implements) but the required artifact is absent** — no enrolled `SignerRecord`, no hardware-credentials entry, no physical FIDO2/PIV device present on the target host, and no enrollment writer exists to create any of the three even if a device were present.

## 8. GitHub Deploy-Key Non-Equivalence — Proven

Explicitly inspected, read-only, this session: `/root/.ssh/pcae_harness_deploy_ed25519` / `.pub` (public key comment: `pcae-harness-deploy-readonly@hac-dell`), referenced by `/root/.ssh/config`'s `Host github.com` stanza (`IdentityFile /root/.ssh/pcae_harness_deploy_ed25519`, `IdentitiesOnly yes`), and confirmed as the live transport credential for `git@github.com:atimad/pcae-harness.git` (`sudo -u pcae git -c safe.directory=... remote -v`). This is:
- Owned by `root`, not `pcae` — `pcae` itself has **no** `~/.ssh` directory at all (`ls: cannot access '/home/pcae/.ssh': No such file or directory`, confirmed live).
- An Ed25519 SSH keypair used exclusively for Git object transport (fetch/clone over SSH), never for HATP-style application-level payload signing.
- Never referenced, imported, or read by `hatp_bootstrap.py`, `hatp_deployment_binding_admin.py`, `hatp_providers.py`, `hatp_hardware_credentials.py`, or `hatp_signing_ceremony.py` (confirmed by grep — the module names never appear near any SSH/deploy-key code, and vice versa).
- Categorically the wrong *kind* of credential for `signer_key_id`: HATP-REQ-019/020 require a **hardware-backed**, non-exportable key with fresh-human-presence enforcement per signing operation (FIDO2/PIV class); an on-disk SSH private key file is explicitly the opposite of that (HATP-REQ-021: "A local software signing key... SHALL NOT silently substitute for a required hardware signer").

**Result: none, exactly as expected.** The deploy key is reused for nothing beyond its stated purpose (read-only Git transport for source redeployment, already independently verified in the 149O.20L.7N chain).

## 9. `provider_profile` — Semantics, Source, Registry/Current-Host State

**Semantics.** HATP-REQ-019 (`HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md:210-220`): freezes "a conceptual provider profile, `HATP_HARDWARE_PROVIDER_V1`, defined by required security properties, not by vendor or protocol branding" — properties (a) non-exportable hardware key, (b) fresh human-presence enforcement, (c) operation-specific-payload signing, (d) stable enrollable credential identity, (e) verification against independently trusted material.

**Canonical vocabulary — exists in code, not wired to `DeploymentBinding`.** `src/pcae/core/hatp_providers.py:183`: `HATP_HARDWARE_PROVIDER_V1 = "HATP_HARDWARE_PROVIDER_V1"`; line 186-187: `_PRODUCTION_HARDWARE_PROVIDER_PROFILES = (HATP_HARDWARE_PROVIDER_V1,)` — a **closed, single-member allowlist** consulted by `create_production_hardware_provider` (raises `HATPProviderUnavailableError` on any other value). This constant is the `provider_profile` value used, unconditionally, by every real production consumer traced this session: `hatp_signing_ceremony.py` (signing-ceremony preview/proof), `hatp_ag_authority.py`, `hatp_rollback_consumption.py`, `hatp_fido2_provider.py`, `hatp_piv_provider.py`, `human_approval_trusted_provenance.py`.

`hatp_deployment_binding_admin.py` never imports `hatp_providers.py` or `_PRODUCTION_HARDWARE_PROVIDER_PROFILES` — `DeploymentBinding.provider_profile` is accepted as an opaque, unvalidated non-empty string from `AuthorityEvidence` (HBDC-REQ-058). Every existing test fixture (`tests/test_hatp_deployment_binding_admin.py:65`) nonetheless uses the literal string `"HATP_HARDWARE_PROVIDER_V1"` — a convention, not an enforced constraint.

**Provider registry/current-host state:** no provider configuration file or registry distinct from the fixed source constant was found anywhere in the codebase or on Dell — `HATP_HARDWARE_PROVIDER_V1` is a code-level constant, not a per-deployment configuration value, so there is nothing host-specific to "already be configured" for it. What *is* absent on Dell is a physical device satisfying the profile (§7) — the profile name itself is not host-provisioned, the hardware backing it is.

**Classification: strong (C-leaning-toward-A) candidate.** Unlike `principal_id`/`signer_key_id`, `provider_profile` already has a real, closed, single-valued production vocabulary (`HATP_HARDWARE_PROVIDER_V1` — the only value `_PRODUCTION_HARDWARE_PROVIDER_PROFILES` will ever accept as of this contract version). The only gap is that `hatp_deployment_binding_admin.py` does not import or enforce it (149O.20L.7H's own named non-blocking finding). This is the one field of the four where "the narrowest valid value" is already unambiguous from primary source, contingent only on the wiring gap being closed (or the admin simply supplying the correct literal, which every test already does).

## 10. `authority_scope` — Semantics and Vocabulary

**Semantics.** Neither HBDC-001 nor HATP-001 defines `authority_scope`'s internal structure — `hatp_bootstrap.py`'s parser (`_require_nonempty_str`) treats it as an opaque string everywhere it appears (`AuthorityRecord.authority_scope`, `DeploymentBinding.authority_scope`). The closest structural precedent is `AuthorityRecord` (registry `authorities` section: `principal_id`, `repository_id`, `authority_scope`, `status`, `valid_from`, `revoked_at`) — its only real production consumer is the rollback-authority resolution path (`resolve_ag3/ag5_gated_rollback_authority`, per HATP-REQ-043: "A repository-scoped `principal → rollback authority` mapping SHALL come exclusively from the protected bootstrap state"). That establishes `authority_scope` denotes **action-scoped authority** (e.g., "may authorize a rollback"), not a path scope, not a raw capability set, and not a HATP verification-boundary scope — but this is AG3/AG5's own established usage, not a value HBDC-001 itself defines for `DeploymentBinding`.

**Vocabulary — none exists.** Repo-wide search for any enum, allowlist, or contract-defined set of `authority_scope` values found none. `tests/test_hatp_deployment_binding_admin.py:319`'s `test_authority_fields_never_widened_or_transformed` is an affirmative test proving the producer accepts and byte-for-byte preserves `authority_scope="totally-unrecognized-scope-string"` — a deliberate demonstration that no cross-validation occurs, not an accidental absence. The only value used across all existing fixtures is `"rollback"` (`tests/test_hatp_deployment_binding_admin.py:66`, `tests/test_hatp_bootstrap_foundation.py`) — a convention inherited from the AG3/AG5 use case, not a canonical or contract-derived value for a Class-B deployment binding specifically.

**Minimum-safe value (§15 of the governing prompt): cannot be derived.** No canonical constrained vocabulary exists from which to select a narrowest value; selecting one here (even "deployment" or "class_b_deployment") would be inventing a value this document is instructed not to invent. **Classified as unresolved architecture** exactly per the governing prompt's own fallback instruction.

## 11. Cross-Field Constraints

Traced directly in validation/matching code, not inferred from comments:

- **`principal_id` ↔ `signer_key_id`**: enforced only inside `_resolve_signer` (`hatp_signing_ceremony.py`) for the *signing-ceremony* proof — `SignerRecord.principal_id` binds a signer to its enrolling principal in the registry schema. `hatp_deployment_binding_admin.py` performs no such cross-check; the two fields are independent unvalidated strings at the `DeploymentBinding` producer.
- **`provider_profile` ↔ `authority_scope`**: no code anywhere couples these two fields.
- **`signer_key_id` ↔ `provider_profile`**: `SignerRecord` stores both together (identity + the provider profile that signer enrolled under) — a real schema-level pairing in the *registry*, but again never consulted by the `DeploymentBinding` producer.
- **`repository_id` ↔ `canonical_deployment_root`**: the one cross-field constraint that IS load-bearing and live — `deployment_binding_matches` (`hatp_bootstrap.py:177-196`) requires both to agree (plus `status == "active"`) before HBDC-REQ-042 is satisfied; this is the "copy/clone/theft defense" the whole Class-B model rests on.
- **Idempotency comparison** (`_COMPARED_AUTHORITY_FIELDS`, `hatp_deployment_binding_admin.py:171-177`): `canonical_deployment_root`, `principal_id`, `signer_key_id`, `provider_profile`, `authority_scope` are compared as a group for create-idempotency purposes (exact match on all five ⇒ `ALREADY_SATISFIED`; any difference ⇒ fail-closed `DuplicateConflictingBindingError`) — this is a producer-internal consistency rule, not a semantic cross-validation of what the fields *should* contain.

## 12. `AuthorityEvidence` Relationship

`AuthorityEvidence` (`hatp_deployment_binding_admin.py:255-270`) is the producer's sole input: `principal_id`, `signer_key_id`, `provider_profile`, `authority_scope`, `election_reference` — all five required non-empty strings (`_validate_authority_evidence`). It does **not** wrap or reference an `AuthorityRecord` (the registry concept) at all; they are unrelated types despite the similar name. `election_reference` (HBDC-REQ-064/065, verbatim above, §13) is recorded as **audit metadata only** — `_audit()` embeds it in the provenance-event `summary` string (e.g., `deployment_binding_create_noop`/`deployment_binding_created`) — never cryptographically verified, never cross-checked against a real CHGR record by this module. It resolves none of the four unresolved fields; it is an orthogonal authorization-evidence field layered on top of them.

## 13. HBDC-REQ-056..070 — Verbatim (§16.1 of HBDC-001)

- **HBDC-REQ-056.** "The `DeploymentBinding` creation/rotation/revocation writer SHALL be a separate, non-agent-writable admin tool — never a subcommand of the ordinary agent-reachable `pcae` CLI."
- **HBDC-REQ-057.** "The writer SHALL derive `repository_id` and `canonical_deployment_root` read-only, from the target repository's existing `RepositoryIdentity` and `resolve_canonical_deployment_root()` respectively — never as free-form caller input."
- **HBDC-REQ-058.** "`principal_id`, `signer_key_id`, `provider_profile`, `authority_scope` SHALL be drawn from the admin's own enrollment context, not from repository-local state or agent-supplied input."
- **HBDC-REQ-059.** Fail-closed on conflicting existing entry; idempotent no-op on identical.
- **HBDC-REQ-060.** Rotation/revocation are distinct explicit operations from creation.
- **HBDC-REQ-061.** Revocation is field mutation (never deletion); rotation is in-place overwrite; no trust-store history.
- **HBDC-REQ-062.** Every writer operation SHALL produce an audit record via existing infrastructure.
- **HBDC-REQ-063.** Writer SHALL reuse `repository_identity.py::_write_atomic`'s exact atomic-write idiom.
- **HBDC-REQ-064.** Writer SHALL require explicit fresh, separate human-election evidence before writing.
- **HBDC-REQ-065.** Election-evidence reference recorded as audit metadata only, not cryptographically verified by the writer.
- **HBDC-REQ-066.** Writer invocable only by the admin OS principal, never agent-reachable.
- **HBDC-REQ-067.** Future writer output SHALL use the strict timestamp grammar.
- **HBDC-REQ-068.** RepositoryIdentity (Layer 1) creation is not gated by this section's election requirement.
- **HBDC-REQ-069.** This contract text alone does not satisfy any governing CHGR election condition.
- **HBDC-REQ-070.** This section's bytes participate in `implementation_scope_digest` automatically.

## 14. HMIC Downstream Consumption

Traced across the 5103-line HMIC-001 contract (grep for `principal_id`/`signer_key_id`/`provider_profile`/`authority_scope`/`DeploymentBinding`) and `hatp_class_b_conformance.py`. Two independent findings converge:

1. **`_check_deployment_identity`** (`hatp_class_b_conformance.py:96-132`), the function that actually computes HBDC-REQ-042's live pass/fail, calls only `hatp_bootstrap.deployment_binding_matches(binding, repository_id=..., canonical_deployment_root=...)` — a comparison over `repository_id`, `canonical_deployment_root`, and `status == "active"` **only**. `principal_id`/`signer_key_id`/`provider_profile`/`authority_scope` play **no role whatsoever** in whether HBDC-REQ-042 passes.
2. HMIC-001's v1.4 amendment (Phase 149O.20L.7K, `HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md:13`) widened `implementation_scope_digest` (HMIC-REQ-052 limb (c)) to bind the `DeploymentBinding` producer's **source-code bytes** (`core/hatp_deployment_binding_admin.py`, `scripts/hatp_deployment_binding_admin.py`) — i.e., HMIC's concern is that the producer code has not been tampered with (attack-matrix row 39: a hypothetical silently-weakened `AuthorityEvidence` validator accepting an empty `principal_id`), detected via digest mismatch, not via HMIC re-validating live field *values* against any registry at certification time.

**Conclusion: HMIC imposes no stronger value-level constraint than HBDC on these four fields.** Its only added discipline is byte-integrity monitoring of the producer module pair. A `DeploymentBinding` with opaque-but-non-empty `principal_id`/`signer_key_id`/`provider_profile`/`authority_scope` values that satisfies HBDC-REQ-042 today would satisfy any HMIC certification computed after it, exactly as-is — there is no risk of "passes HBDC but is unusable for later HMIC" from field-value looseness alone (though it would remain a live *governance* risk if the values are meaningless, independent of HMIC's mechanical scope).

## 15. Election-Derived / Environment-Derived Classification

No contract or module in this repository uses a formal five-way taxonomy (`ENVIRONMENT-DERIVED`/`CANONICAL-REGISTRY-DERIVED`/`HUMAN-ELECTION-DERIVED`/`PRODUCER-GENERATED`/`FIXED-CONTRACT-VALUE`) verbatim — confirmed by repo-wide search. Applying it as an analytical frame to this phase's own findings (not sourced as contract text, but derived from it):

| Field | Classification | Basis |
|---|---|---|
| `repository_id` | CANONICAL-REGISTRY-DERIVED | Read-only from existing `RepositoryIdentity` artifact (HBDC-REQ-057) |
| `canonical_deployment_root` | ENVIRONMENT-DERIVED | Pure function of live filesystem state (`resolve_canonical_deployment_root`) |
| `principal_id` | HUMAN-ELECTION-DERIVED (admin-assigned, unimplemented) | HATP-REQ-037 conceptual procedure; HBDC-REQ-058 "admin's own enrollment context" |
| `signer_key_id` | CANONICAL-REGISTRY-DERIVED (mechanism exists, artifact/enrollment absent) | `_resolve_signer` precedent; no enrolled `SignerRecord`/hardware credential exists |
| `provider_profile` | FIXED-CONTRACT-VALUE (candidate, unwired) | `HATP_HARDWARE_PROVIDER_V1`, sole member of `_PRODUCTION_HARDWARE_PROVIDER_PROFILES` |
| `authority_scope` | UNRESOLVED / no vocabulary | No canonical source of any kind found |
| `valid_from` | PRODUCER-GENERATED | `_canonical_timestamp_now()` at call time |
| `status` | FIXED-CONTRACT-VALUE | `"active"` on create, closed two-value enum |
| `revoked_at` | PRODUCER-GENERATED / FIXED-CONTRACT-VALUE | `None` on create |

## 16. Live Dell Read-Only Evidence (This Session)

All commands executed read-only over a fresh SSH session to `hac-dell`; no write, no `sudo` mutation, no file created or modified:

- `sudo ls -la /etc/pcae/hatp/trust-store` → empty directory, `drwxr-x--- root:pcae`.
- `sudo cat /etc/pcae/hatp/trust-store/registry.json` → `No such file or directory`.
- `sudo cat /opt/pcae/runtime/src/.pcae/repository-identity.json` → matches §2 exactly.
- `getent passwd pcae` / `id pcae` → `uid=1004(pcae) gid=1004(pcae)`, shell `/usr/sbin/nologin`.
- `sudo ls -la /home/pcae/.ssh` → `No such file or directory` (no SSH material for `pcae`).
- `sudo -u pcae git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src remote -v` → `origin git@github.com:atimad/pcae-harness.git`.
- `sudo find / -xdev -iname 'id_ed25519*' -o -iname 'id_rsa*'` → only `/home/atila/.ssh/id_ed25519*` (the human operator's personal key, unrelated).
- `sudo ls -la /root/.ssh` → `pcae_harness_deploy_ed25519` (+`.pub`), `config`, `known_hosts`, `authorized_keys` (empty).
- `sudo cat /root/.ssh/config` → `Host github.com` → `IdentityFile /root/.ssh/pcae_harness_deploy_ed25519`.
- `sudo cat /root/.ssh/pcae_harness_deploy_ed25519.pub` → comment `pcae-harness-deploy-readonly@hac-dell`.
- `gpg --card-status` → `No SmartCard daemon` / `OpenPGP card not available`.
- `lsusb` → webcam, Broadcom combo (WiFi/BT), Intel Bluetooth, Elan touchscreen, USB root hubs only — no FIDO2/PIV/security-key-class device.
- `sudo find /etc/pcae /opt/pcae -iname 'hardware-credentials*'` → no results.
- `sudo -u pcae readlink -f /opt/pcae/runtime/src` → `/opt/pcae/runtime/src` (confirms §5's canonicalization claim).

## 17. Disposable Producer Preview (Non-Authoritative Simulation)

Executed locally, this session, entirely in a `tempfile.TemporaryDirectory()` sandbox (disposable repository directory, disposable protected-root directory) — never touching `HATPTrustStore.production()`'s real path or any Dell state. Used the **real** `repository_id` (`0107866f-af7c-40b4-8317-74e71acb05ca`) as instructed, written into a disposable local `.pcae/repository-identity.json`, with placeholder `AuthorityEvidence` values explicitly labeled `DISPOSABLE-NON-AUTHORITATIVE-SIMULATION`:

```
NON-AUTHORITATIVE SIMULATION RESULT (disposable local state only):
kind: DeploymentBindingPreviewKind.WOULD_CREATE
repository_id: 0107866f-af7c-40b4-8317-74e71acb05ca
canonical_deployment_root: <disposable tmp path>
candidate_binding: DeploymentBinding(repository_id='0107866f-af7c-40b4-8317-74e71acb05ca',
  canonical_deployment_root='<disposable tmp path>',
  principal_id='DISPOSABLE-NON-AUTHORITATIVE-SIMULATION',
  signer_key_id='DISPOSABLE-NON-AUTHORITATIVE-SIMULATION',
  provider_profile='HATP_HARDWARE_PROVIDER_V1',
  authority_scope='DISPOSABLE-NON-AUTHORITATIVE-SIMULATION',
  valid_from='2026-08-18T14:04:21.527Z', status='active', revoked_at=None)
```

**NON-AUTHORITATIVE.** This confirms only that `preview_create_deployment_binding` mechanically accepts the real `repository_id` and produces a `WOULD_CREATE` classification against an empty disposable store — it proves nothing about what the real field values should be, and no artifact from this run was written anywhere outside the temporary directory (deleted automatically on context-manager exit).

## 18. Complete Field-Resolution Table

| Field | Value / generation rule | Authority source | Evidence | Resolved? | Reason |
|---|---|---|---|---|---|
| `repository_id` | `0107866f-af7c-40b4-8317-74e71acb05ca` | `read_repository_identity` (HBDC-REQ-057) | §2, §5, §16 | **Yes** | Live artifact re-confirmed on Dell this session |
| `canonical_deployment_root` | `/opt/pcae/runtime/src` | `resolve_canonical_deployment_root` (HBDC-REQ-057) | §5, §16 (`readlink -f`) | **Yes** | Canonicalization proven a no-op for this path |
| `principal_id` | — (no value) | HATP-REQ-014/037, HBDC-REQ-058 ("admin's own enrollment context") | §6 | **No** | No enrollment writer exists; no registry entry exists; `"pcae"` proven invalid |
| `signer_key_id` | — (no value) | HATP-REQ-039, `_resolve_signer` precedent, HBDC-REQ-058 | §7, §8, §16 | **No** | No enrolled `SignerRecord`, no hardware-credentials entry, no physical device on host |
| `provider_profile` | `HATP_HARDWARE_PROVIDER_V1` (candidate, unwired) | `hatp_providers.py::_PRODUCTION_HARDWARE_PROVIDER_PROFILES` | §9 | **Partial** | Sole valid production value exists; not enforced/wired by the `DeploymentBinding` producer |
| `authority_scope` | — (no value) | None found | §10 | **No** | Contract-silent; no vocabulary anywhere; test suite affirmatively proves free-form acceptance |
| `valid_from` | `_canonical_timestamp_now()` at call time | HBDC-REQ-067 | §5 | **Yes** | Generation rule, not a fixed value |
| `status` | `"active"` on create | `_STATUS_VALUES` | §5 | **Yes** | Closed two-value enum, fixed on create |
| `revoked_at` | `None` on create | `_require_revoked_at_consistency` | §5 | **Yes** | Fixed on create, mutated only by revoke |

## 19. Blocking Dependency Graph

```
principal_id  ──┐
signer_key_id ──┼──►  ONE missing artifact: Principal/Signer enrollment admin
provider_profile─┘     surface (HATP-REQ-036/037's conceptual, never-implemented
                       procedure) — populates `principals` + `signers` sections
                       of registry.json, ideally paired with an enrolled
                       FIDO2/PIV hardware credential (Wave-5 hardware-credentials
                       store) for the Human/Admin OS principal on the target host.

authority_scope ──► SEPARATE, smaller gap: no canonical vocabulary/policy
                     exists at all (not even conceptually, unlike the three
                     fields above) — requires its own narrow contract
                     decision (e.g. an HBDC-001 amendment defining the
                     permitted scope literal(s) for a Class-B deployment
                     binding), independent of the enrollment-surface gap.
```

Ordering: the enrollment-surface architecture (mirroring the exact
`docs/PHASE_149O_20L_7G_...` → `...7H_...` (independent verification) →
`...7I_...` (implementation) sequence this repository already used for
the `DeploymentBinding` producer itself, applied instead to
Principal/Signer/Authority enrollment) must precede `principal_id`/
`signer_key_id`/`provider_profile` resolution. `authority_scope`'s
vocabulary decision has no such dependency and could be resolved in
parallel or in the same architecture phase, but is analytically
distinct.

## 20. One Missing Concept Resolving Multiple Fields (§30)

**Yes — investigated and confirmed, not assumed.** `principal_id`, `signer_key_id`, and `provider_profile` are not three independent gaps: they are three outputs of exactly one missing artifact — a **Principal/Signer enrollment admin surface** — for the following converging reasons, each independently traced above:
- All three already share one registry home (`hatp_bootstrap.py`'s `principals`/`signers` sections) and one real, working resolution mechanism (`hatp_signing_ceremony.py::_resolve_signer` + `HATPTrustStore.lookup_signer`), just applied to a different record type today.
- HATP-REQ-037's conceptual enrollment procedure produces exactly these three facts (`principal_id` assignment, "verifies the hardware/provider identity" → `signer_key_id`/`provider_profile`) plus repository authority, in one described ceremony.
- `SignerRecord` itself stores `principal_id` + `provider_profile` alongside `signer_key_id` as one coherent record — enrolling a signer necessarily enrolls its principal-binding and provider-profile together.

`authority_scope` does **not** fold into this same artifact — it has no vocabulary anywhere, conceptual or implemented, unlike the other three. The smallest coherent architecture is therefore **two**, not four, patches: (1) a Principal/Signer enrollment admin surface (resolves three fields), (2) a narrow `authority_scope` vocabulary decision for Class-B deployment bindings specifically (resolves the fourth) — not four separate ad-hoc phases, but not a single one either, since the two gaps are evidentially independent.

## 21. `DeploymentBinding` Proposition Readiness Gate

**Classification: (C) CONTRACT/ARCHITECTURE GAP — NEW DESIGN REQUIRED.**

Not (B) "resolvable after an existing configuration/provisioning step" — no enrollment tool, command, or procedure exists anywhere in this repository to *run*; HATP-REQ-036/037 describe the procedure only in prose, never implemented. Not (D) "producer/schema gap" — the `DeploymentBinding` schema itself (§4) is complete, closed, and already independently verified (149O.20L.7H/7J); the gap is one layer upstream, in the principal/signer enrollment surface HBDC-REQ-058 assumes exists but which HATP-001 has only ever conceptually specified.

## 22. Future-Adapter / Runtime-Neutrality Check (§25)

The one candidate fixed value found, `provider_profile = "HATP_HARDWARE_PROVIDER_V1"`, is defined exclusively by hardware-signer security properties (HATP-REQ-019(a)-(e): non-exportable key, human-presence enforcement, payload signing, enrollable identity, independent verification material) — it denotes the physical signing device class (FIDO2/PIV), categorically unrelated to which PCAE agent runtime (Claude, Codex, or any future adapter) is executing. No field interpretation proposed or found in this phase hard-codes the current agent runtime; `principal_id` denotes a human approver, `signer_key_id` a hardware credential, `authority_scope` an unresolved action-scope concept — none of the four fields has any structural relationship to agent-runtime identity. This phase's own findings introduce no new runtime-neutrality risk and confirm none exists in the fields as currently defined.

## 23. Audit Durability / `architecture-history.json` (§35-36)

Carried unchanged from 149O.20L.7J's finding (re-confirmed present in current source this session, `hatp_deployment_binding_admin.py`'s own module docstring, lines 84-105): a durable trust-store mutation can outlive a failed audit-emission call; this is a named, disclosed, non-repaired limitation, not addressed by this phase (out of scope: architecture-only). This phase's own field-resolution architecture makes no assumption that `AuthorityEvidence.election_reference` is mutable during any retry path — `election_reference` is treated throughout this document exactly as HBDC-REQ-065 defines it: an immutable, evidentiary, non-cryptographically-verified audit-metadata string. `.pcae/architecture-history.json` (git-ignored runtime artifact) is not touched, read, or reasoned about as a source of DeploymentBinding field semantics anywhere in this document — carried separately, not mixed in, per the governing prompt.

## 24. Live HBDC / Runtime State — Unchanged, Proven

- **HBDC**: `verify_class_b_deployment_conformance()` was not invoked live this session (no code executed against the real Dell trust store or real repository state beyond the read-only inspections in §16, all of which are pure reads with zero side effects). No write occurred at any point (§2, §16 confirm the Protected Root remains empty; `registry.json` still does not exist). Sole residual, by construction unchanged: `HBDC-REQ-042`, reason `no_active_deployment_binding_matches_repository_and_root`.
- **Runtime**: Observed / observe / unavailable — unchanged; nothing in this phase touches `hatp_mandatory_cutover.py` or any runtime-activation code path.
- **HMIC digest** (`65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8`): unaffected — this phase adds only a new, non-frozen doc file and a new, non-frozen test file; neither is a member of HMIC-001's `_FROZEN_SRC_PCAE_RELATIVE_FILES`/`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` sets (confirmed: those are closed, named 30-member lists of pre-existing tracked files; new files cannot retroactively join a closed enumeration without their own separate contract amendment, which this phase does not perform).

## 25. Proof — No DeploymentBinding / No Election / No CHGR / No Certification / No Dell Mutation

- **No `DeploymentBinding` created**: `create_deployment_binding`/`rotate_deployment_binding`/`revoke_deployment_binding` were never called against `HATPTrustStore.production()` or any real path; the only invocation of producer code this phase performed was `preview_create_deployment_binding` (read-only by construction — "never writes," `hatp_deployment_binding_admin.py:828-833`) against a disposable `tempfile.TemporaryDirectory()` sandbox (§17), auto-deleted on exit. `/etc/pcae/hatp/trust-store/registry.json` remains absent on Dell (§2, §16).
- **No election initiated**: no decision-session, no proposition text presented for approval, no `AuthorityEvidence.election_reference` referencing anything but the disposable simulation's placeholder string.
- **No CHGR published**: no `chgr-*` record created, read for mutation, or referenced as authorizing anything in this phase; the two governing CHGRs cited by 149O.20L.7O §18 remain the only relevant records, unchanged.
- **No certification performed**: `verify_hatp_proof`, `hatp_mandatory_certification.py`, and every HMIC certification entry point were never invoked.
- **No Dell mutation**: every Dell-directed command this session was a read (`ls`, `cat`, `find`, `readlink`, `git remote -v`, `getent`, `id`, `gpg --card-status`, `lsusb`); `sudo` was used only for read access to root-owned paths, never for a write, `chmod`, `touch`, or file-creation command. `git status` on Dell's checkout was not altered by anything this phase did (not re-checked live this session, since no command that could plausibly dirty the tree was ever issued).

## 26. Final Verdict

**DEPLOYMENTBINDING FIELD CONTRACT GAP — ARCHITECTURE REQUIRED.**

Two of nine fields (`principal_id`, `authority_scope`) have zero canonical source of any kind; one (`signer_key_id`) has a real, working, but unwired-and-unenrolled derivation mechanism; one (`provider_profile`) has a real, closed, single-valued vocabulary that is simply not consulted by the producer. Three of the four (`principal_id`/`signer_key_id`/`provider_profile`) converge on one missing artifact — a Principal/Signer enrollment admin surface, conceptually specified by HATP-REQ-036/037 but never implemented anywhere in this repository. `authority_scope` is a second, independent, smaller gap with no conceptual precedent at all. Neither gap is closed by any existing configuration step an operator could simply run today (Category B is explicitly rejected, §21) — both require new architecture/contract work before a real `DeploymentBinding` proposition can be drafted with genuine, non-invented field values.

## 27. Recommended Next Phase

**149O.20L.7O.2D — HATP Principal/Signer Enrollment Contract Architecture** (narrowest next step): design, on the same rigor level as HBDC-001 §16.1's own `DeploymentBinding`-producer amendment (149O.20L.7G's own precedent), a companion contract amendment (either a new HATP-001 section formalizing HATP-REQ-036/037 into concrete, numbered, testable requirements, or a new sibling contract mirroring HBDC-001's structure) specifying: the exact enrollment writer's schema/error vocabulary/atomicity/audit discipline for the `principals`/`signers` registry sections, the relationship to the Wave-5 hardware-credentials store, and — as a second, explicitly separate work item within the same or an immediately following phase — a narrow `authority_scope` vocabulary decision for Class-B deployment bindings specifically. This must not implement anything (mirrors 149O.20L.7G's own architecture-only discipline), must not create real protected state, and must itself undergo independent verification (mirroring 7G→7H) before any implementation phase (mirroring 7H→7I) builds against it. Only after that full chain resolves `principal_id`/`signer_key_id`/`provider_profile`/`authority_scope` with genuine, non-invented values can a dedicated `DeploymentBinding` proposition-preparation phase (the original 7O.4/7O.5-equivalent chain: proposition → independent verification → election + CHGR → execution → independent real-host verification) proceed. The Boundary-C breakpoint (per 149O.20L.7O/7N's own recorded strategic pause) remains unchanged and unapproached by this phase.

## 28. Tests

`tests/test_phase_149o_20l_7o_2c_deploymentbinding_first_use_field_resolution_architecture.py` — self-consistency and source-fact assertions (doc records the exact live values claimed above; schema/vocabulary claims re-verified directly against `hatp_bootstrap.py`/`hatp_deployment_binding_admin.py`/`hatp_providers.py`/`hatp_hardware_credentials.py`/`hatp_signing_ceremony.py` source; HBDC-REQ-042 matching logic confirmed field-value-independent; no production source modified).

## 29. Governance Results

- `pcae status coherence`: pass
- `pcae health`: pass
- `pcae check`: pass
- `python -m pytest -n auto`: fast_green tier green (see final commit's recorded counts)
- Pre-existing `tests/test_hatp_deployment_binding_admin.py` (55 tests): unchanged, all passing, re-confirmed this session with zero modification.

## 30. Commits, Push Status, `origin/main..HEAD`

See `.pcae/phase-completion-metadata.json`/`.pcae/phase-completion-report.md` for the exact commit hash, push status, and `origin/main..HEAD` diff recorded at phase completion.

## 31. Strategic Breakpoint (Unchanged)

The approved breakpoint stands exactly as recorded by 149O.20L.7O/7N: after `DeploymentBinding` first-use is executed and independently verified, and HBDC reaches its intended clean state, pause before Boundary C; then begin (1) DeepSeek Harness vs PCAE Comparative Architecture Study, (2) PCAE Runtime Adapter + Plugin Architecture. This phase does not begin either study — it remains, if anything, further from Boundary C than 7O.2B.1 left it, since it has newly identified an additional architecture prerequisite (§27) that was not previously named as a distinct blocking phase.
