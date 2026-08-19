# Phase 149O.20L.7O.2H — HMIC-001 v1.4-to-v1.5 Contract Evolution and Production Alignment: Trust-Enrollment / Signing Closure Limb (d)

**Phase-entry commit:** `e65b4ce0` (Phase 149O.20L.7O.2G.1: close governed task, transition to idle)

**Status:** Contract evolution **and** production alignment, combined in this phase, per the 149O.20L.7K precedent. No certification, no HATP activation, no FIDO2 provisioning, no real Principal/Signer enrollment, no real `DeploymentBinding`, no `hac-dell` mutation, no readiness-semantics change, no CBV-S10 closure, no runtime-capability change.

## Verdict

**HMIC-001 v1.5 TRUST-ENROLLMENT / SIGNING AUTHORITY-SCOPE ALIGNMENT IMPLEMENTED — INDEPENDENT VERIFICATION PENDING**

Frozen content/source identity: **35 members** (26 `src/pcae/`-relative + 9 repository-root-relative).
Contract-version identity: **7 members**.
Closure limb (d): **implemented**.
`B-149O.20L.7O.2G-1`: **ALIGNED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED**.
HMIC certification: **NOT PERFORMED**. HATP activation: **NOT PERFORMED**.
Runtime: **Observed / observe / unavailable**.

## 1. Entering State

- 149O.20L.7O.2G.1 (HMIC Trust-Enrollment/Signing Target-Set Reconciliation) confirmed complete at phase-entry commit `e65b4ce0`.
- Repository clean, zero commits ahead of `origin/main`, no active governed phase, HMIC-001 still v1.4, production still 30 frozen files / 5 `contract_versions` members. Runtime unchanged (Observed/observe/unavailable).
- `pcae health`/`pcae check`/`pcae status coherence` all passed at entry.

## 2. Primary Evidence Read Before Editing

Read in full before any edit: `docs/PHASE_149O_20L_7O_2G_HATP_TRUST_ENROLLMENT_AND_SIGNING_HMIC_TRANSITIVE_AUTHORITY_SCOPE_ANALYSIS.md`, `docs/PHASE_149O_20L_7O_2G_1_HMIC_TRUST_ENROLLMENT_SIGNING_TARGET_SET_RECONCILIATION.md`, HMIC-001 v1.4 (`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`), and `src/pcae/core/hatp_mandatory_certification.py`. Independently re-verified against live current bytes: the three new source files' `import pcae.*` statements (byte-identical to 2G.1's own §9 result), HPSE-001/HHCE-001's live `**Contract:**`/`**Version:**` headers (both `1.1`), and `production_sign_rollback_evidence`'s existence as `hatp_signing_ceremony.py`'s sole exported production entry point. No discrepancy from 2G.1's derivation was found — the reconciled 35/7 target was implemented exactly as derived, using the exact membership lists 2G.1's own report enumerates (its §11.1/§11.2/§12.1), not merely the counts in the governing prompt.

## 3. Reconciled Target Implemented

Following `B-149O.20L.7O.2G-1`'s reconciliation exactly:

- `_FROZEN_SRC_PCAE_RELATIVE_FILES`: 23 → 26 (added `core/hatp_signing_ceremony.py`, `core/hatp_hardware_credential_admin.py`, `core/hatp_principal_signer_admin.py`).
- `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`: 7 → 9 (added `docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md` and `docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md`, positioned after `HBDC-001` and before the two `scripts/` entries).
- `_FROZEN_AUTHORITY_BEARING_FILES`: 30 → 35, `assert len(...) == 35`.
- `_CONTRACT_IDENTITY_FILES`: 5 → 7 (added `HPSE-001`, `HHCE-001`).

No fourth candidate source file was added; `paths.py`, `provenance.py`, `git_status.py`, `tasks.py` remain correctly excluded on established precedent (§10 of 2G.1, independently re-verified by this phase's own `test_limb_d_closure_every_import_bound_or_excluded_leaf`).

## 4. HMIC-001 Contract Amendment (v1.4 → v1.5)

Requirements amended in place (no requirement text removed or weakened):

- **HMIC-REQ-050**: enumeration widened thirty → thirty-five; narrative updated to record this phase's five new entries and their placement.
- **HMIC-REQ-052**: new closure limb (d) added — dual-anchor construction (reachability via `production_sign_rollback_evidence`; non-reachability via the hardware-credential/principal-signer administrative writers), mirroring limb (c)'s own precedent.
- **HMIC-REQ-053**: "five contract files" → "seven contract files"; HPSE-001/HHCE-001 named as receiving uniform dual binding from admission, never as a deferred exception.
- **HMIC-REQ-067**: "Revised, v1.2" → "Revised, v1.5"; five → seven `contract_versions` members, HPSE-001/HHCE-001 added with their rationale.
- **HMIC-REQ-069**: "five entries as of v1.2" → "seven entries as of v1.5".
- **CIVC-5**: updated to record the v1.5 seven-member state and HPSE-001/HHCE-001's dual binding.
- **Attack matrix**: widened 39 → 42 scenarios (row 40: limb (d) source byte-modification; rows 41/42: HPSE-001/HHCE-001 same-version content-drift, mirroring row 37's HBDC-001 precedent).
- New **§59** (Contract Amendment History — Phase 149O.20L.7O.2H, v1.5): full worked closure-limb analysis, transitive-completeness matrix, digest-sensitivity proofs, version-bump rationale, and the `_CONTRACT_VERSIONS_REQUIRED_KEYS` scope decision (§7 below), mirroring §55's (149O.20L.7K) structure.

Header block updated: version 1.4 → 1.5, new "Amended by" line, `Depends on` line extended to include `HPSE-001 v1.1, HHCE-001 v1.1`.

## 5. Production Alignment (Same Phase)

`src/pcae/core/hatp_mandatory_certification.py` updated in the same phase as the contract amendment (per the 149O.20L.7K precedent, not the split contract-then-alignment sequencing 149O.20K used): `_FROZEN_SRC_PCAE_RELATIVE_FILES`, `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`, `_FROZEN_AUTHORITY_BEARING_FILES`'s count assertion, `_CONTRACT_IDENTITY_FILES`, module docstring, and the two error classes' docstrings (`FrozenFileDerivationError`, `ContractIdentityDerivationError`) — all updated to reflect 35/7. No other production behavior changed.

## 6. Self-Binding Verification

`hatp_mandatory_certification.py` is itself frozen member #19 (since v1.1). Widening its own tuples changes its own bytes and therefore its own digest contribution — the identical pattern already safely used at v1.3/v1.4 (149O.20K/149O.20L.7K). `derive_implementation_scope_digest` always reads bytes fresh at computation time; no stale-cache hazard. Confirmed deterministic across repeated calls (`test_deterministic_repeated_digest`).

## 7. `_CONTRACT_VERSIONS_REQUIRED_KEYS` — Scoped, Not Fully Reconciled

The governing prompt asked this phase to "reconcile the contract-version parser/required keys." Direct inspection found `_CONTRACT_VERSIONS_REQUIRED_KEYS` (a separate, Wave-A-owned `CertificationRecord` closed-schema constant used only by `_require_contract_versions`) was, and had been since well before this phase, a **four**-member literal (`HMRC-001`/`HATP-001`/`HSCE-001`/`RAE-001`) that had never itself been widened to include `HBDC-001` when `_CONTRACT_IDENTITY_FILES` gained it at v1.2 — a pre-existing, disclosed drift 149O.20L.7O.2G first surfaced and 149O.20L.7O.2G.1 independently reconfirmed present, unchanged, and explicitly **out of that phase's own scope** ("non-blocking, unrelated, unrepaired … a pre-existing drift 2G already correctly flagged as out of this scope").

This phase widens `_CONTRACT_VERSIONS_REQUIRED_KEYS` **strictly additively, by this phase's own two new members only** (HPSE-001, HHCE-001 — four → six), leaving the pre-existing HBDC-001 gap untouched, exactly as 2G.1 left it. Closing that unrelated, pre-existing drift is not within this phase's own additive, limb-(d)-scoped charter and is deferred to a future, separately-governed repair phase. `derive_contract_versions` (Wave B) is unaffected and continues to return the full, correct seven-member mapping; only the separate Wave A closed-schema *acceptance* set for a stored `CertificationRecord` is six, not seven, members — a narrower, deliberately incomplete mirror, not a new inconsistency this phase introduces.

(An initial edit in this phase's working history did fully reconcile this constant by deriving it from `_CONTRACT_IDENTITY_FILES` — closing the HBDC-001 gap too. That was reverted after review: it silently expanded this phase's own scope beyond its additive charter and broke ~180 test fixtures across the repository that build synthetic `CertificationRecord`s against the historical four/five-member set. The final, committed state is the scoped six-member widening described above.)

## 8. Digest Sensitivity, Certification Compatibility, Closed Schema

Mechanically proven in a disposable in-memory scratch tree (`tests/test_phase_149o_20l_7o_2h_hmic_trust_enrollment_signing_closure_limb_d.py`):

- Each of the five newly-bound files (three source, two contract documents) is individually digest-sensitive; the pre-amendment 30-file scope was blind to the two contract-document perturbations (proven indirectly — HPSE-001/HHCE-001 were not members before this phase).
- HPSE-001/HHCE-001's versions are dynamically derived (not hardcoded), and same-version content-only drift changes `implementation_scope_digest` while `derive_contract_versions` reports the version unchanged — the identical HBDC-001 same-version-drift protection, now demonstrated for both new contracts.
- A synthetic `CertificationRecord` built against the pre-2H four-member `_CONTRACT_VERSIONS_REQUIRED_KEYS` set fails the current six-member schema as missing required entries; a record with an unrecognized seventh key fails closed as unrecognized. No optional/partial-validity compatibility behavior was introduced.
- `implementation_scope_digest` derivation is deterministic across repeated calls.

## 9. Regression

**Focused new suite:** `tests/test_phase_149o_20l_7o_2h_hmic_trust_enrollment_signing_closure_limb_d.py` — 36/36 passed, covering all 28 items of the phase's required-test list (exact membership counts, no-duplicate/no-missing paths, contract↔production equality, closed-schema behavior, digest/version sensitivity, limb (d) closure, Class-B/DeploymentBinding retention, old-record rejection, unknown-key rejection, determinism, self-binding, no-certification/runtime-unchanged proofs, HMIC-REQ-053 uniform coverage, HPSE/HHCE header parsing, and a zero-commits-since-entry check on the four signing/hardware authority files BF-1/BF-2/2F.3-1/2F.3-2 depend on).

**Existing HMIC/HATP/Trust-Enrollment/signing regression:** A repository-wide `hmic or hatp_mandatory_certification` selection was compared, node-for-node, against a `git stash`-derived pre-phase baseline (195 pre-existing failures, all confirmed unrelated to this phase's own scope). This phase's own widening initially introduced 215 additional node failures — overwhelmingly (a) old phases' own "current live state is exactly N" test suites whose literal counts (30, five, "v1.4", "twenty-eight", etc.) predate this additive widening, and (b) isolated-fixture tests whose synthetic `_CONTRACT_IDENTITY_FILES` monkeypatch didn't also monkeypatch the (previously coincidentally-matching) `_CONTRACT_VERSIONS_REQUIRED_KEYS`. All were repaired using the established, already-precedented pattern this repository uses for additive HMIC amendments (e.g. 149O.20L.7K's own predecessor-test updates): exact-count assertions widened to `>=`/subset checks with a docstring recording the prior exact value and the amendment that widened it; docstring-only diffs (in `derive_contract_versions`, `ContractIdentityDerivationError`, `FrozenFileDerivationError`) excluded from byte-identity comparisons; isolated fixtures given the matching `_CONTRACT_VERSIONS_REQUIRED_KEYS` monkeypatch. After repair, **12 node failures remain**, all of the "working tree / HEAD state" class (`git status --porcelain` emptiness checks and HEAD-vs-working-tree digest/enumeration comparisons) that trivially resolve once this phase's own changes are committed — not functional regressions. A parallel spot-check against the broader `signing_ceremony or hardware_credential_admin or principal_signer_admin or fido2` and `class_b or deployment_binding` selections found the same pattern: zero functional regressions, only the same working-tree-dirty class, confirming `hatp_signing_ceremony.py`, `hatp_fido2_provider.py`, `hatp_hardware_credential_admin.py`, and `hatp_principal_signer_admin.py` were not touched by this phase (BF-1/BF-2/`B-149O.20L.7O.2F.3-1`/`B-149O.20L.7O.2F.3-2` unaffected).

## 10. Class-B / CBV / Finding Disposition

- `hatp_class_b_topology_verifier.py`, `hatp_environment_lock_verifier.py`, `hatp_class_b_conformance.py`, `hatp_deployment_binding_admin.py` (core + script) remain bound, unmodified.
- CBV-S1 unaffected. **CBV-S10 remains OPEN**, untouched.
- **`B-149O.20L.7O.2G-1`**: ALIGNED — 35-member content/source identity implemented, 7-member contract identity implemented — INDEPENDENT VERIFICATION PENDING — NOT CLOSED (this phase does not close its own finding).
- BF-1, BF-2, `B-149O.20L.7O.2F.3-1`, `B-149O.20L.7O.2F.3-2`: unaffected, remain independently closed at their implementation boundaries.

## 11. No-Go Confirmed

No HMIC certification created or activated. No HATP activation. No FIDO2 hardware provisioned. No real Principal or Signer enrolled. No real `DeploymentBinding` created. No `hac-dell`/Protected Root mutation. No Permission Broker/runtime-capability change. No PIV implementation. CBV-S10 not wired. Stream B not touched.

## 12. Fast Green

Isolated disposable `git worktree` at this phase's own entry commit (`e65b4ce0`) compared against current source, `python -m pytest -m fast_green -n auto` both times. See the phase-completion report's `validation_results`/`test_results` for the exact recorded node counts and diff.

## 13. Recommended Next Phase

**149O.20L.7O.2H.1 — HMIC-001 v1.5 Trust-Enrollment/Signing Authority-Scope Alignment Independent Verification.** Must independently reconstruct: the v1.4 historical identity; the 35/7 target derivation; limb (d); contract/content dual binding; production equality; digest sensitivity; old-certification invalidation; transitive closure; and this phase's own `_CONTRACT_VERSIONS_REQUIRED_KEYS` scope decision (§7). Does not begin certification, provisioning, readiness work, or activation. Stop after 149O.20L.7O.2H itself.
