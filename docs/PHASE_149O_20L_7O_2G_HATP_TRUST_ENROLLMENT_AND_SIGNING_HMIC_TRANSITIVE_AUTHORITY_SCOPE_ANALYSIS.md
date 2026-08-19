# Phase 149O.20L.7O.2G — HATP Trust-Enrollment and Signing HMIC Transitive Authority-Scope Analysis

**Phase entry commit:** `021175c9b3136243dff068130165c34f7e14bc0c` (Phase 149O.20L.7O.2F.5: close governed task, transition to idle)

**Status:** Analysis only. No HMIC modification, no provisioning, no real trust state. No production source or contract file was edited by this phase (only `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DONE.md`, this document, and its test/task/report artifacts).

## Verdict

**HATP TRUST-ENROLLMENT / SIGNING HMIC TRANSITIVE AUTHORITY SCOPE INDEPENDENTLY DERIVED — ALIGNMENT PREREQUISITE DEFINED**

Not "HMIC ALIGNED." Not "HATP READY." Not "TRUST ENROLLMENT AUTHORIZED." Not "PROVISIONING READY." No HMIC change occurred in this phase.

---

## 1. Methodology

This phase read HMIC-001's current primary contract text directly (`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`, 5103 lines, Contract ID `HMIC-001`, **Version 1.4**) and the current production implementation of that contract (`src/pcae/core/hatp_mandatory_certification.py`, 2130 lines) directly from current `main` (`021175c9`). No prior phase's summary, count, or file list was assumed as a starting point. Every membership claim below was independently re-derived from one of:

- the contract's own literal HMIC-REQ-050 enumeration and HMIC-REQ-052 closure-rule text (read directly, in full, in this phase);
- the production `_FROZEN_SRC_PCAE_RELATIVE_FILES` / `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` / `_CONTRACT_IDENTITY_FILES` constants in `hatp_mandatory_certification.py` (read directly, in full, in this phase);
- a fresh Python `ast`-module import-graph walk of every candidate module, executed in this phase, not reused from any prior phase's trace;
- direct `grep`/`git log` inspection of candidate files and their call sites.

No file-count assumption (25, 28, 30, "old + N") was used as a starting hypothesis anywhere in this derivation; the target set below is a set-membership result, and its size is incidental.

## 2. HMIC-REQ-052 — Direct Re-Read

HMIC-REQ-052 ("Transitive-Dependency Coverage — Closure Rule," contract §17, text at or near line 682) currently defines **three** closure limbs, each anchored to a specific production entry point's own call graph:

- **Limb (a):** every file reachable from `assess_hatp_mandatory_activation_readiness`'s call graph that can change provider registry/selection; hardware/cryptographic assertion verification; trust-store/protected-credential-store resolution; HATP verification status derivation; RAE/HATP approval derivation; Permission Broker request construction; or AG3/AG5 mandatory-effect gating.
- **Limb (b)** *(added v1.1)*: every file reachable from `validate_active_hatp_mandatory_independent_verification_certification`'s call graph, or from the Protected Admin ceremony functions `certify`/`activate`/`revoke` in `scripts/hatp_certification_admin.py` — HMIC's own self-binding limb.
- **Limb (c)** *(added v1.3, widened v1.4)*: every file reachable from `verify_class_b_deployment_conformance`'s call graph, **or** the `DeploymentBinding` producer/rotation/revocation functions in `core/hatp_deployment_binding_admin.py` and their admin-ceremony caller `scripts/hatp_deployment_binding_admin.py` (a non-reachability anchor, mirroring limb (b)'s dual-anchor construction).

**Finding (structural, not a defect):** HMIC-REQ-052 currently has **no limb anchored on `production_sign_rollback_evidence`** (the Trust-Enrollment/signing entry point in `hatp_signing_ceremony.py`) and **no limb anchored on the Trust-Enrollment writer functions** (`hatp_hardware_credential_admin.py`, `hatp_principal_signer_admin.py`). This is not an oversight discovered by this phase to be silently repaired — HMIC-REQ-052's own amendment history (§49–§55) shows each limb was deliberately added by a dedicated contract-evolution phase when a new production authority surface was built (v1.1 added limb (b) for the certification module itself; v1.3/v1.4 added and widened limb (c) for Class-B/DeploymentBinding). Trust-Enrollment/signing (`hatp_signing_ceremony.py`, `hatp_hardware_credential_admin.py`, `hatp_principal_signer_admin.py`, built across Phases 149O.20L.7O.2D–2F) has not yet had its own corresponding closure-rule limb added. **This is precisely why the recommended next step (§10) is an additive HMIC contract-evolution phase, not merely a file/version realignment under the existing rule text** — under the current HMIC-REQ-052 wording, these three files are not actually required to be bound; they are outside all three limbs' call-graph reach.

Corroborating evidence: `hatp_mandatory_cutover.py` (the file whose call graph *is* limb (a)'s anchor) only checks `hatp_signing_ceremony`'s *importability* (`importlib.import_module("pcae.core.hatp_signing_ceremony")`, lines ~854–858) as one of several component-presence checks — it does not call into `production_sign_rollback_evidence` or any Trust-Enrollment writer function. No decision made by `assess_hatp_mandatory_activation_readiness`, `validate_active_hatp_mandatory_independent_verification_certification`, or `verify_class_b_deployment_conformance` depends on the three candidate files' logic.

**Digest construction (HMIC-REQ-058):** two-level SHA-256 — hash each frozen file's raw working-tree bytes first, then hash the ordered (HMIC-REQ-056: lexicographic, not presentation-order), NUL/newline-delimited concatenation of `<canonical_path>\0<file_sha256>\n` records. **Canonicalization (HMIC-REQ-055):** repository-relative, POSIX separators, `src/pcae/`-relative for the first N entries and repository-root-relative for the rest, no symlink component, no `..`. **Ownership (HMIC-REQ-051):** the enumeration is embedded literally in the frozen contract itself, never an external manifest — amending it requires amending HMIC-001, which itself requires the contract file (already a bound member) to change. **Contract-version set (HMIC-REQ-067, v1.2):** exactly five members currently, each derived dynamically at validation time by regex-reading the live contract file's own `**Contract ID:**`/`**Contract:**` and `**Version:**` header lines (never a hardcoded version string) — this means a contract's version is picked up automatically the moment its file's header changes; it is the *set of which contract IDs participate* that is frozen, not any specific version value.

## 3. Current HMIC Baseline (Independently Re-Derived From Current Source)

### 3.1 Current implementation/content source set — 30 entries

Re-derived directly from `_FROZEN_SRC_PCAE_RELATIVE_FILES` (23 entries) + `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` (7 entries) in `hatp_mandatory_certification.py`, confirmed by the module's own `assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 30` runtime invariant:

| # | Path | Bound since |
|---|---|---|
| 1 | `src/pcae/core/hatp_mandatory_cutover.py` | v1.0 |
| 2 | `src/pcae/core/hatp_ag_authority.py` | v1.0 |
| 3 | `src/pcae/core/hatp_rollback_consumption.py` | v1.0 |
| 4 | `src/pcae/core/hatp_bootstrap.py` | v1.0 |
| 5 | `src/pcae/core/human_approval_trusted_provenance.py` | v1.0 |
| 6 | `src/pcae/core/repository_identity.py` | v1.0 |
| 7 | `src/pcae/core/rollback_approval_evidence.py` | v1.0 |
| 8 | `src/pcae/core/hatp_evidence_store.py` | v1.0 |
| 9 | `src/pcae/core/hatp_signed_evidence.py` | v1.0 |
| 10 | `src/pcae/core/agent.py` | v1.0 |
| 11 | `src/pcae/commands/agent.py` | v1.0 |
| 12 | `src/pcae/cli.py` | v1.0 |
| 13 | `src/pcae/core/permission_broker.py` | v1.0 |
| 14 | `src/pcae/core/permission_broker_foundation.py` | v1.0 |
| 15 | `src/pcae/core/hatp_providers.py` | v1.0(repair, 149O.19.3R) |
| 16 | `src/pcae/core/hatp_fido2_provider.py` | v1.0(repair, 149O.19.3R) |
| 17 | `src/pcae/core/hatp_piv_provider.py` | v1.0(repair, 149O.19.3R) |
| 18 | `src/pcae/core/hatp_hardware_credentials.py` | v1.0(repair, 149O.19.3R) |
| 19 | `src/pcae/core/hatp_mandatory_certification.py` | v1.1 (self-binding, limb b) |
| 20 | `src/pcae/core/hatp_class_b_topology_verifier.py` | v1.3 (limb c) |
| 21 | `src/pcae/core/hatp_environment_lock_verifier.py` | v1.3 (limb c) |
| 22 | `src/pcae/core/hatp_class_b_conformance.py` | v1.3 (limb c) |
| 23 | `src/pcae/core/hatp_deployment_binding_admin.py` | v1.4 (limb c, 3rd anchor) |
| 24 | `docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md` (HMRC-001) | v1.0 |
| 25 | `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` (HATP-001) | v1.0 |
| 26 | `docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md` (HSCE-001) | v1.0 |
| 27 | `docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md` (RAE-001) | v1.0 |
| 28 | `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001) | v1.2 (149O.20D.1) |
| 29 | `scripts/hatp_certification_admin.py` | v1.1 (self-binding, limb b) |
| 30 | `scripts/hatp_deployment_binding_admin.py` | v1.4 (limb c, 3rd anchor) |

### 3.2 Current contract-version set — 5 members

Re-derived from `_CONTRACT_IDENTITY_FILES` (the production constant `derive_contract_versions` actually iterates): `HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`, `HBDC-001`. Each is dynamically re-read from its bound file's live header at validation time — **HSCE-001's currently-live version (v1.3) is therefore already correctly represented in HMIC identity without any code change**, and its content bytes are already digest-bound (entry 26 above). §20 of the phase brief asked this explicitly: **HSCE-001 v1.3 is fully and correctly represented in current HMIC identity, both content and version — no gap exists here.**

**Non-Blocking observation (new, surfaced by this phase — not a 2F.5 carryover):** a second, older constant, `_CONTRACT_VERSIONS_REQUIRED_KEYS` (line 227, a 4-member frozenset: `HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`), is used only by `_require_contract_versions` (Wave A parsing/schema-validation of a *persisted* `CertificationRecord` document) and has not been widened to include `HBDC-001` since v1.2. This is a Wave A/Wave B drift: the schema validator's required-key set (4) and the production derivation set (5) disagree. It does not affect `derive_contract_versions` (which uses `_CONTRACT_IDENTITY_FILES`, already 5) and no certification currently exists on this host for the drift to be exercised against (per 2F.5's own confirmed "no stored certification exists anywhere on this host" state). **Not repaired in this phase** (analysis only); flagged for whichever phase next touches Wave A parsing.

## 4. Production Authority Entry Points Traced

- `pcae hatp sign rollback` (`src/pcae/commands/hatp.py`, 251 lines) → `production_sign_rollback_evidence` (`hatp_signing_ceremony.py`). Direct inspection of `commands/hatp.py::run_hatp_sign_rollback` confirms it is pure CLI plumbing: argument validation, `RollbackSite` enum mapping, a single call into the production entry point with zero overrides, and closed `error_type`/exit-code mapping — no independent authority computation. Classified **NON-AUTHORITY — EXCLUDED (CLI dispatch only)**, consistent with the existing "CLI formatting only" exclusion category already used elsewhere in this contract's own exclusion analysis (e.g. `commands/hatp.py` is not, and does not need to become, a frozen member).
- Hardware credential registration → `hatp_hardware_credential_admin.py` (no CLI wrapper found; invoked directly by test/administrative callers in this repo's current state — consistent with 2F/2E's "synthetic/local fixtures only, no real hardware" scope).
- Principal/Signer enrollment → `hatp_principal_signer_admin.py`.
- DeploymentBinding creation → `hatp_deployment_binding_admin.py` (already bound, #23/#30).
- HATP bootstrap/trust-store production → `hatp_bootstrap.py` (already bound, #4).

## 5. Fresh AST Import-Graph Analysis

A direct Python `ast` walk (executed in this phase, not reused) of the three not-yet-bound candidate files' PCAE-owned (`pcae.*`) imports:

```
hatp_signing_ceremony.py:
  pcae.core.agent, pcae.core.hatp_bootstrap, pcae.core.hatp_evidence_store,
  pcae.core.hatp_hardware_credentials, pcae.core.hatp_providers,
  pcae.core.hatp_signed_evidence, pcae.core.human_approval_trusted_provenance,
  pcae.core.paths, pcae.core.repository_identity, pcae.core.rollback_approval_evidence

hatp_hardware_credential_admin.py:
  pcae.core.hatp_hardware_credentials, pcae.core.paths, pcae.core.provenance,
  pcae.core.hatp_bootstrap

hatp_principal_signer_admin.py:
  pcae.core.hatp_bootstrap, pcae.core.hatp_deployment_binding_admin,
  pcae.core.hatp_hardware_credential_admin, pcae.core.hatp_hardware_credentials,
  pcae.core.hatp_providers, pcae.core.paths, pcae.core.provenance
```

Recursing one level further into the two new non-authority-looking leaves (`paths.py`, `provenance.py`):

```
paths.py:       (no pcae imports — leaf)
provenance.py:  pcae.core.agent, pcae.core.git_status, pcae.core.paths, pcae.core.tasks
```

**Every other PCAE-owned import above is already a bound member** (`agent.py` #10, `hatp_bootstrap.py` #4, `hatp_evidence_store.py` #8, `hatp_hardware_credentials.py` #18, `hatp_providers.py` #15, `hatp_signed_evidence.py` #9, `human_approval_trusted_provenance.py` #5, `repository_identity.py` #6, `rollback_approval_evidence.py` #7, `hatp_deployment_binding_admin.py` #23). The transitive closure over the three candidates therefore terminates at exactly two new leaf-level utility modules (`paths.py`, `provenance.py`) plus their own further leaves (`git_status.py`, `tasks.py`) — all four classified and excluded below (§6).

## 6. Direct vs. Transitive vs. Excluded Classification

| Module | Classification | Rationale |
|---|---|---|
| `hatp_signing_ceremony.py` | **DIRECT AUTHORITY SOURCE** | Implements the entire Model-B signing-time authority chain independently verified in 2F.5: repository/root resolution, DeploymentBinding resolution, Principal/Signer lookup, hardware-credential lookup, provider-profile checks, immutable `HATPSignerResolution`, hardware signature request, post-touch fresh re-resolution, signed-evidence publication. Changing this file's bytes while every currently-bound file stays byte-identical changes signing-authority outcomes — direct application of the HMIC-REQ-052 closure test. |
| `hatp_hardware_credential_admin.py` | **DIRECT AUTHORITY SOURCE** | Sole production writer of `HardwareCredentialRecord`s (active/revoked hardware-credential registry state) that `hatp_signing_ceremony.py`'s consumer-side lookup (already-bound `hatp_hardware_credentials.py`) reads. A byte edit here (e.g. weakening a revocation check) can durably corrupt registry state that the already-bound consumer would then load as if legitimate — the identical "producer write path, not reachable from the verifier/consumer's own call graph" shape HMIC-REQ-052 limb (c)'s third anchor already uses for `hatp_deployment_binding_admin.py`. |
| `hatp_principal_signer_admin.py` | **DIRECT AUTHORITY SOURCE** | Sole production writer of `PrincipalRecord`/`SignerRecord` state (including the continuous two-lock cross-registry critical section whose correctness B-149O.20L.7O.2F.3-1/-2 concerned) that both `hatp_bootstrap.py`'s read path and `hatp_signing_ceremony.py`'s consumer lookup depend on. Same producer/consumer asymmetry as above. |
| `paths.py` | **NON-AUTHORITY — EXCLUDED** | 16-line frozen dataclass wrapper (`HarnessPath`) with zero branching logic — `cwd()` and a `Path` join, nothing else. Already imported by the *currently-bound* `hatp_mandatory_certification.py` itself and by nearly the entire codebase (89 importers found via `grep`), yet was never separately added to the frozen set at any prior HMIC amendment — established repository precedent already treats pure structural/type-wrapper leaves with no decision logic as outside HMIC-REQ-052's closure, and this phase applies that identical precedent rather than inventing a new one. |
| `provenance.py` | **NON-AUTHORITY — EXCLUDED (audit/telemetry only)** | Append-only provenance-event writer (`ProvenanceEvent`/`append_provenance_event`); read via `grep`, its functions only serialize an event record to `.pcae/provenance-history.json` — they never gate, reject, or alter an authority decision. Already imported by the *currently-bound* `hatp_deployment_binding_admin.py` (#23/#30) and was not separately added — same established-precedent argument as `paths.py`. Changed-semantics test: editing `append_provenance_event` to silently no-op changes zero signing/enrollment/DeploymentBinding outcomes, only audit-trail completeness. |
| `git_status.py`, `tasks.py` | **NON-AUTHORITY — EXCLUDED** | Reached only via `provenance.py`'s own (excluded) import; `git_status.py` reads the current branch name for an audit-event field, `tasks.py::find_latest_active_task` reads the active task file for the same audit-event field. Neither participates in any accept/reject/resolve/sign/verify/publish decision. |
| `commands/hatp.py` | **NON-AUTHORITY — EXCLUDED (CLI dispatch only)** | See §4 — pure argument/exit-code plumbing, single zero-override call into the (soon-to-be-bound) production entry point. |

**Methodological refinement discovered while building §17's test suite:** a naive whole-*module* recursive import walk through the four excluded leaves does not terminate cleanly — `tasks.py` alone (reached via `provenance.py`) also backs this repository's entire `pcae task`/`pcae health`/`pcae session` CLI surface and transitively imports dozens of unrelated modules (`health.py`, `session.py`, `status.py`, `orchestration.py`, `phase_reports.py`, and further). Blindly following every module-level import edge would drag essentially the whole codebase into the candidate set — exactly the "blindly include every imported utility" trap §9 of the phase brief warns against. The correct unit of analysis is the *specific symbol* each new candidate actually calls, not everything its containing module happens to import for unrelated purposes: `provenance.py`'s `append_provenance_event` calls `tasks.py::find_latest_active_task`, whose own body (independently read, §17's test suite asserts this mechanically) does nothing but glob `tasks/active/*.md` and parse the latest file — it never calls into `health`/`session`/`status`/any of `tasks.py`'s other unrelated fan-out. That broader fan-out is real but is never reached by the code path the new candidates exercise, so it is excluded on call-graph grounds, not merely module-import grounds.

**Forbidden-shortcut check (§29):** no step above assumed a target count. The three DIRECT additions were reached by literally reading HMIC-REQ-052's three limb definitions, confirming by direct grep/import-trace that none of the three candidate files is reachable from any of the three anchors, then applying the identical semantic test (§17's own "could changing this file alter authority-relevant outcome" standard) file-by-file. The four EXCLUDED leaves were reached by finishing the transitive walk, not by assumption, and each exclusion cites the specific established precedent (already-imported-by-a-bound-file, never-separately-bound) rather than a generic "it's a utility" hand-wave.

## 7. Trust-Enrollment Writers — Detailed Findings (§13)

- **`hatp_hardware_credential_admin.py`:** transitive authority inputs are `hatp_hardware_credentials.py` (registry schema/parser, already bound), `hatp_bootstrap.py` (`HATPTrustStore`, already bound), plus the excluded audit/utility leaves above. No new transitive PCAE-owned authority dependency.
- **`hatp_principal_signer_admin.py`:** in addition to the above, transitively depends on `hatp_deployment_binding_admin.py` (already bound — its own `_atomic_write_registry`/`_deployment_binding_transition_lock`/`_load_raw_registry_document`/`_resolve_protected_root`/`_require_trust_store_available` helpers are reused directly, not reimplemented) and on `hatp_hardware_credential_admin.py`'s own `hardware_credential_transition_lock` (the continuous two-lock critical section B-149O.20L.7O.2F.3-1/-2 concerned). This confirms the two-lock section's correctness depends on **both** admin modules being bound together — they cannot be split into separate HMIC evolutions without leaving one half of the critical section's authority surface unbound.
- **`hatp_deployment_binding_admin.py`:** already bound (#23/#30); its cross-validation dependencies (`hatp_bootstrap.py`, `hatp_hardware_credentials.py`, `repository_identity.py`) are all already-bound members. No new dependency surfaces from re-tracing it in this phase.

**Determination:** yes — all three writer modules' semantics must be HMIC-bound before real enrollment can be relied upon under HMIC-REQ-052's own stated purpose (attesting that the complete authority-bearing implementation, not merely its read/consumer half, matches a certified byte identity). Producer validation is part of the authority model even though 2F.3–2F.5 already proved consumers independently fail closed on inconsistent historical state — that consumer-side fail-closed behavior is a different, already-verified layer (§8 below), not a substitute for producer-side HMIC binding.

## 8. BF-1/BF-2 and B-...2F.3-1/-2 Status (Unchanged, Not Reopened)

Per §40 of the phase brief, and independently reconfirmed by this phase (no production source touched since 2F.5; `git log` shows zero commits to `hatp_signing_ceremony.py`, `hatp_fido2_provider.py`, `hatp_hardware_credential_admin.py`, or `hatp_principal_signer_admin.py` since `021175c9`):

- **BF-1:** INDEPENDENTLY CONFIRMED CLOSED AT HATP TRUST-ENROLLMENT / SIGNING IMPLEMENTATION BOUNDARY.
- **BF-2:** INDEPENDENTLY CONFIRMED CLOSED AT HATP TRUST-ENROLLMENT / SIGNING IMPLEMENTATION BOUNDARY.
- **B-149O.20L.7O.2F.3-1:** INDEPENDENTLY CONFIRMED CLOSED AT HATP SIGNING CONSUMER IMPLEMENTATION BOUNDARY.
- **B-149O.20L.7O.2F.3-2:** INDEPENDENTLY CONFIRMED CLOSED AT HATP SIGNING CONSUMER IMPLEMENTATION BOUNDARY.

These four findings concern **implementation correctness** (does the code fail closed on inconsistent state?), which is orthogonal to and unaffected by **HMIC identity binding** (does a byte-identity certification cover that code?). This phase's finding that the implementation is not yet HMIC-bound does not reopen any of the four — it defines a *prerequisite for relying on a future certification*, not a defect in current behavior.

## 9. Exact Target Set

### 9.1 Required implementation/content source set — 33 entries (30 current + 3 added)

Added paths (exact set difference, `src/pcae/`-relative bucket):
```
core/hatp_signing_ceremony.py
core/hatp_hardware_credential_admin.py
core/hatp_principal_signer_admin.py
```
Removed paths: **none.** No evidence justifies retiring any of the current 30 entries — all three candidate additions were confirmed to have zero authority-superseding relationship to any existing member.

### 9.2 Required contract-version set — 7 entries (5 current + 2 added)

Added contract/version pairs:
```
HPSE-001  v1.1  docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md
HHCE-001  v1.1  docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md
```
Both files currently exist, carry `**Contract:**`-labeled headers matching the same regex grammar `derive_contract_versions` already parses for the other five, and are **not currently in `_CONTRACT_IDENTITY_FILES`** — confirmed by direct read of that constant (§3.2) and by `grep` confirming neither file appears in `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` either. **Both content and version are currently unbound for these two contracts** — the same "content vs. version" distinction §19 of the phase brief asks about applies identically to HPSE-001/HHCE-001 as it did to HBDC-001 pre-149O.20D.1: version-only binding without content binding would leave same-version semantic drift (a quietly loosened HPSE-001/HHCE-001 requirement with no version bump) undetected, exactly the gap the HBDC-001 precedent (§52 of the contract) already demonstrated and closed for that contract. Recommendation: bind both content (add to the repository-root-relative frozen-file list) and version (add to `_CONTRACT_IDENTITY_FILES`), mirroring the HBDC-001 precedent exactly — no new binding mechanism required.

## 10. Contract-by-Contract Treatment (§18/§19)

| Contract | Current version | Content bound? | Version bound? | Required action |
|---|---|---|---|---|
| HMIC-001 (self) | v1.4 | Yes (self, entry via own bytes as member #19 = `hatp_mandatory_certification.py`, and the contract file itself is one of the 5 `docs/contracts/` frozen files) | N/A (not in `contract_versions` — self-referential) | None |
| HMRC-001 | (dynamic) | Yes (#24) | Yes | None |
| HATP-001 | (dynamic) | Yes (#25) | Yes | None |
| HSCE-001 | **v1.3** | Yes (#26) | Yes (dynamic re-read) | **None — already fully current** (§3.2) |
| RAE-001 | (dynamic) | Yes (#27) | Yes | None |
| HBDC-001 | v1.2 | Yes (#28, since 149O.20D.1) | Yes (since 149O.20D/F) | None |
| **HPSE-001** | v1.1 | **No** | **No** | **Add both** (§9.2) |
| **HHCE-001** | v1.1 | **No** | **No** | **Add both** (§9.2) |

## 11. Source/Contract Coverage Matrix

| Authority capability | Production source(s) | Transitive deps | Governing contract(s) | Current HMIC bound? | Required action |
|---|---|---|---|---|---|
| FIDO2 enrollment | `hatp_fido2_provider.py` | `hatp_hardware_credentials.py`, `hatp_providers.py` | HHCE-001, HPSE-001 | Source: Yes (#16). Contracts: **No** | Bind HPSE-001/HHCE-001 content+version |
| HardwareCredential registration | `hatp_hardware_credential_admin.py` | `hatp_hardware_credentials.py`, `hatp_bootstrap.py` | HHCE-001 | **No** | Add source; bind HHCE-001 |
| Principal enrollment | `hatp_principal_signer_admin.py` | `hatp_bootstrap.py`, `hatp_deployment_binding_admin.py`, `hatp_hardware_credential_admin.py` | HPSE-001 | **No** | Add source; bind HPSE-001 |
| Signer enrollment | `hatp_principal_signer_admin.py` | (same as above) | HPSE-001 | **No** | Add source; bind HPSE-001 |
| DeploymentBinding creation | `hatp_deployment_binding_admin.py` | `hatp_bootstrap.py`, `hatp_hardware_credentials.py`, `repository_identity.py` | HBDC-001 | Yes (#23/#30) | None |
| Durable signer resolution | `hatp_signing_ceremony.py` | `hatp_bootstrap.py`, `hatp_hardware_credentials.py`, `hatp_providers.py` | HSCE-001 | **No** (source) | Add source |
| Pre-touch consistency | `hatp_signing_ceremony.py` | (same) | HSCE-001 | **No** | Add source |
| Hardware signing | `hatp_signing_ceremony.py`, `hatp_fido2_provider.py`, `hatp_providers.py` | — | HSCE-001, HPSE-001, HHCE-001 | Partial (2/3 sources bound) | Add `hatp_signing_ceremony.py`; bind HPSE-001/HHCE-001 |
| Signature verification | `hatp_signing_ceremony.py`, `hatp_fido2_provider.py` | — | HSCE-001 | Partial | Add `hatp_signing_ceremony.py` |
| Post-touch state revalidation | `hatp_signing_ceremony.py` | `hatp_bootstrap.py`, `hatp_hardware_credentials.py` | HSCE-001 | **No** | Add source |
| Signed evidence publication | `hatp_signing_ceremony.py`, `hatp_evidence_store.py`, `hatp_signed_evidence.py` | — | HSCE-001 | Partial (2/3 sources bound) | Add `hatp_signing_ceremony.py` |
| Class-B verifier | `hatp_class_b_topology_verifier.py`, `hatp_environment_lock_verifier.py`, `hatp_class_b_conformance.py` | — | HBDC-001 | Yes (#20-22) | None (unchanged, §12) |

## 12. Class-B Verifier Interaction (§21) and CBV-S1/CBV-S10 (§22/§23)

Freshly checked (`git log` on all three files: last commit `73ea8b23`, unrelated to and predating this phase and 2F entirely): **no change to Class-B verifier status.** All three remain HMIC-bound (#20-22) exactly as of v1.3.

**CBV-S1** ("no positive Class-B conformance result may become production-authoritative while source deriving that result is outside HMIC identity"): unaffected by this phase's findings — the Class-B verifier files themselves were already bound at v1.3/v1.4 and remain so; this phase's gap is in the *separate* Trust-Enrollment/signing surface, not the Class-B surface. **Not marked closed or reopened by this phase; no HMIC change occurred.**

**CBV-S10** (readiness integration): remains **OPEN**, exactly as instructed (§23). No readiness Boolean invented, no wiring performed.

**Unified-vs-separate recommendation (§21):** Trust-Enrollment/signing's missing limb and Class-B's existing limb (c) are structurally independent — Class-B's own closure (limb c) is already complete and correct; Trust-Enrollment needs a *new*, separate limb, not a widening of limb (c). They should **remain separately staged** (Option B-shaped for this specific pairing): Class-B's HMIC-REQ-052 limb (c) already closed CBV-S1's source-binding prerequisite for the Class-B surface specifically; a future Trust-Enrollment limb (a new limb (d), by the numbering convention this contract already uses) would close the analogous prerequisite for the signing surface. Bundling them into one contract-evolution phase would not be incorrect, but is not required by any shared dependency — the three new Trust-Enrollment files import none of the three Class-B verifier files or vice versa (confirmed by the AST walk in §5, which found no such edge in either direction).

## 13. HMIC Administrative/Self-Binding Check (§24, W-1)

`hatp_mandatory_certification.py` (#19) and `scripts/hatp_certification_admin.py` (#29) remain bound exactly as of the v1.1 W-1 closure; this phase found no new production source responsible for manifest/digest/contract-version-list construction, validation, or certification administration outside these two already-bound files. **W-1 not reopened** — no direct evidence contradicts its historical closure. The Wave A/Wave B `_CONTRACT_VERSIONS_REQUIRED_KEYS` drift noted in §3.2 is a genuinely new observation from this phase, but it concerns a stale *validation* key-set inside the already-bound `hatp_mandatory_certification.py`, not an unbound file — it does not reopen W-1 (which concerned production sources being *outside* HMIC identity, not internal staleness within an already-bound file).

## 14. 2F.5 Non-Blocking Finding Dispositions (§32)

- **ABA transient state:** unchanged — accepted residual limitation, not repaired, no new contradicting evidence found.
- **Architecture Status presentation:** unchanged — presentation-only, not repaired.
- **HMIC consequence scope note:** **resolved by this phase.** 2F.5 explicitly deferred the full HMIC-REQ-052 transitive-dependency re-derivation; §2–§11 above are that derivation.
- **Mixed-read atomicity observation:** re-considered for HMIC-inclusion relevance — the trust-registry read pattern it concerns lives inside already-bound `hatp_bootstrap.py`/already-newly-added `hatp_hardware_credential_admin.py`/`hatp_principal_signer_admin.py`; once those two admin files are bound (per this phase's recommendation), the locking semantics it describes fall inside HMIC identity's future scope. Not repaired in this phase.
- **Fixed-only unexplained historical test difference:** recorded, unrelated to HMIC scope; not investigated further here (out of this phase's scope per §32's own instruction).

## 15. Next-Phase Options and Selected Recommendation (§30)

- **Option A** (one additive HMIC evolution covering the full newly-required closure): covers both the 3 new source files and both new contracts in a single amendment.
- **Option B** (separate Class-B and Trust-Enrollment evolutions): moot for *this* gap — Class-B's own closure is already complete (§12); there is nothing pending on the Class-B side to stage separately from Trust-Enrollment.
- **Option C** (prerequisite contract clarification needed before alignment): not supported by evidence — HMIC-REQ-052's existing limb (b)/(c) dual-anchor pattern (self-binding writer anchors not reachable from a verifier's own call graph) is directly reusable for the new limb; no ambiguity blocks drafting it.
- **Option D** (no HMIC change needed): contradicted directly by §2/§5's findings.

**Selected: Option A.** A single additive HMIC-001 contract-evolution phase should add one new closure limb (d) to HMIC-REQ-052, anchored on `production_sign_rollback_evidence`'s own call graph (mirroring limb (a)'s construction) plus a non-reachability anchor on the two Trust-Enrollment writer modules' functions (mirroring limb (c)'s third-anchor precedent for `hatp_deployment_binding_admin.py`), widen HMIC-REQ-050's enumeration from 30 to 33 entries, and widen the `contract_versions` set from 5 to 7 members (adding HPSE-001, HHCE-001, both content- and version-bound, mirroring the HBDC-001 precedent). This single amendment closes the entire gap identified in §9–§11 with no remaining split-staging rationale, consistent with every prior HMIC amendment in this repository's history (each added exactly the limb needed for the newly-built authority surface it was written for).

## 16. Real-Host / No-Go / Runtime Proof

- **No HMIC modification:** confirmed — `git diff` for this phase touches only `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DONE.md`, this document, its task/report artifacts, and its own analysis test file; zero bytes of `hatp_mandatory_certification.py` or `HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` changed.
- **No certification, activation, or repin:** no `pcae hatp` certification/activation command was invoked.
- **No real provisioning:** no FIDO2 hardware touched; no real Principal/Signer/DeploymentBinding created; confirmed by `git status` showing zero production-file diffs and by direct inspection (no new fixture/registry files under `.pcae/hatp-*` created by this phase).
- **No Dell mutation:** this phase performed local, read-only repository analysis only; no SSH/network action to `hac-dell` was taken.
- **Runtime unchanged:** `pcae runtime inspect` re-run at phase entry (§ Initial Inspection below) shows `Runtime state: Observed`, `Execution capability: unavailable`, identical to the 2F.5 bootstrap snapshot.

## 16.1 Fast Green — Exact Fixed-vs-Current Node-ID Diff

An isolated disposable `git worktree` was checked out at the phase-entry commit (`021175c9`, pre-2G) and `python -m pytest -m "fast_green" -n auto -ra -q` was run there, then again on current source (post-2G, doc/test-only changes), using the identical governed interpreter and marker selection both times:

- **Fixed (pre-2G, `021175c9`):** 304 failed / 8160 passed / 4 skipped / 9 errors — matches 2F.5's own cited fixed-entry baseline exactly.
- **Current (post-2G):** 305 failed / 8159 passed / 4 skipped / 9 errors.
- **Exact FAILED-node-ID diff:** one current-only node, `tests/test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`; zero fixed-only nodes (nothing newly resolved, nothing new stayed broken from before).
- **ERROR-node-ID set diff:** zero (identical 9-member error set both trees).

**Disposition of the one current-only failure:** re-run in isolation (no concurrent `-n auto` worker contention from the simultaneous fixed-worktree comparison run), it **passed** in 13.38s against its own 15-second subprocess timeout (a `pcae shell-gate audit verify` CLI subprocess invocation). This is system-load-induced timing flakiness from running two full parallel `-n auto` fast_green invocations concurrently on this host during the fixed-vs-current comparison, not a defect introduced by this phase — `tests/test_shell_gate.py` is untouched by 2G (this phase edited only `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DONE.md`, this document, its own test file, and task/report artifacts), and the test's own production target (`pcae shell-gate audit verify`) has no relationship to HATP/HMIC/Trust-Enrollment. **Zero durable regressions; 0 failed** attributable to this phase's changes.

## 17. Tests

`tests/test_phase_149o_20l_7o_2g_hmic_transitive_authority_scope_analysis.py` mechanically re-validates: the current 30/5 baseline extraction against live `hatp_mandatory_certification.py` constants; the three candidate files exist and are importable; a fresh AST-based import-graph walk of the three candidates produces the exact PCAE-owned-import set documented in §5; the proposed 33-entry/7-member target sets are deterministic, sorted, duplicate-free, and every path exists on disk; the HPSE-001/HHCE-001 header-regex match succeeds against their live files. No production module is imported or exercised for a *decision* (no signing, no enrollment) — only static analysis and constant/file-existence checks.

## 18. Next Phase

**149O.20L.7O.2H — HMIC-001 v1.4→v1.5 Contract Evolution: Trust-Enrollment/Signing Closure Limb (d)** — an additive HMIC contract-evolution phase implementing the Option A recommendation in §15: add closure limb (d) to HMIC-REQ-052; widen HMIC-REQ-050 to the 33-entry set in §9.1; widen the `contract_versions` set to the 7-member set in §9.2 (content- and version-bind HPSE-001/HHCE-001, mirroring the HBDC-001 precedent); update the production `_FROZEN_SRC_PCAE_RELATIVE_FILES`/`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`/`_CONTRACT_IDENTITY_FILES` constants in the same phase as the contract amendment (per the 149O.20L.7K precedent, not the split 149O.20K sequencing). Followed by an independent verification phase and, later, a production alignment verification phase — not started, not authorized, per §42's instruction to stop after 2G.
