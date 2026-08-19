# Phase 149O.20L.7O.2F.1 — HATP Trust-Enrollment Implementation Capability Independent Verification

Phase type: **INDEPENDENT VERIFICATION ONLY.** No production source (`src/pcae/**`, `scripts/**`) modified. No HPSE-001/HHCE-001 contract text modified. No repair of the Blocking findings recorded below was performed in this phase. No principal, signer, or hardware credential enrolled, provisioned, or registered against real hardware. No Dell host mutated. No HMIC amendment.

## 1. Entering State / Phase-Entry Commit

Phase-entry commit: `8e1d3227` (`Phase 149O.20L.7O.2F: close task, transition to idle`). Latest completed phase: 149O.20L.7O.2F (HATP Trust-Enrollment Implementation Capability), completed, pushed, commit `0459bf76` (task-close `8e1d3227`). Verified against HPSE-001 v1.1 and HHCE-001 v1.1 as frozen entering this phase.

## 2. Verification Methodology

Verification was performed in an isolated git worktree (`.claude/worktrees/agent-a1254e16c5a2b9cda`) so the test suite could be run freely without touching canonical repo state. Every claim was independently re-derived from primary source — `hatp_signing_ceremony.py`, `hatp_fido2_provider.py`, `hatp_hardware_credential_admin.py`, `hatp_hardware_credentials.py`, `hatp_principal_signer_admin.py`, `hatp_bootstrap.py`, `hatp_deployment_binding_admin.py`, HPSE-001 v1.1, HHCE-001 v1.1, and the already-frozen HSCE-001 (`HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`) — not accepted from Phase 149O.20L.7O.2F's own characterization of its work. No canonical repo state was mutated; no push was performed from the isolated worktree.

## 3. The Two Load-Bearing Questions

### 3.1 `credential_identity()` vs `enroll_credential()` — Answer B, not A

The question posed entering this phase: is `credential_identity()` a distinct discovery operation no required first-use path depends on (Answer A), or does a required production path still need it (Answer B)?

**Answer: B.**

- `hatp_signing_ceremony.py::_resolve_signer` (lines 528–556) is called from `sign_rollback_evidence`, whose sole zero-override caller is `production_sign_rollback_evidence` — the real, only production signing orchestrator behind `pcae hatp sign rollback`. Line 542 calls `provider.credential_identity()` as the **exclusive** mechanism for resolving `signer_key_id`. This is confirmed against the already-frozen HSCE-001 contract: `HSCE-REQ-018` states this field is "resolved from the hardware provider's own credential exchange," caller may not supply it; `HSCE-REQ-024` confirms no `--signer` flag exists to bypass this.
- `Fido2HardwareProvider.credential_identity()` (`hatp_fido2_provider.py:307–313`) remains, byte-for-byte, an unconditional `raise HATPProviderUnavailableError(...)` — unchanged by Phase 149O.20L.7O.2F, confirmed identical to the state independently verified in 149O.20L.7O.2D.1, 149O.20L.7O.2D.3, and 149O.20L.7O.2E.1.
- Phase 149O.20L.7O.2F instead added `enroll_credential()` (`hatp_fido2_provider.py:332–391`), a one-time CTAP2 `makeCredential` minting ceremony consumed only by Surface B's `register_credential`. No code path connects `enroll_credential()`'s output back to `credential_identity()`, and no code path makes `credential_identity()` capable of re-deriving that identity at a later signing attempt.
- `hatp_principal_signer_admin.py::enroll_signer` (line 563) never calls `provider.credential_identity()` — it takes `evidence.signer_key_id` as caller-supplied administrative input, obtained out-of-band from `enroll_credential()` + `register_credential()`. This is contract-permitted under HPSE-REQ-059.

**Root cause of the gap:** HPSE-REQ-059/060/072(a) are scoped to `enroll_signer`'s own implementation-readiness (the registry-writer path, Surfaces B/C) — they do not require `credential_identity()` to work, because `enroll_signer` never calls it. But HSCE-001 — an independent, already-frozen, already-implemented contract governing the real `pcae hatp sign rollback` command — does require it, and Phase 149O.20L.7O.2F did not touch HSCE-001 or `_resolve_signer`. The two contracts' requirements were never reconciled. HPSE/HHCE's "implementation-ready" gate is satisfied by 149O.20L.7O.2F's work; that gate does not cover whether the resulting enrolled signer is actually usable — and it is not.

**Compounding structural detail:** `enroll_credential()`'s `ctap2.make_credential(...)` call (`hatp_fido2_provider.py:361–367`) passes no `options` map, so per the CTAP2 specification the `rk` (resident-key) bit defaults to `false` — the credential minted is non-resident. `credential_identity()`'s own error text (line 309) describes the operation it stands in for as requiring "a live CTAP2 device with a discoverable/resident credential." Even a hypothetical future implementation of `credential_identity()` built around resident-credential enumeration could never discover a credential Surface A itself mints, because Surface A produces the wrong credential shape for that discovery mechanism. This is a second, independent instance of the same underlying gap, not previously disclosed by Phase 149O.20L.7O.2F.

**Disclosure gap:** Phase 149O.20L.7O.2F's own report (§4, §19) frames leaving `credential_identity()` untouched as deliberate and architecturally correct, and discloses PIV, audit-after-write, and `CROSS_REGISTRY_MISMATCH` as known limitations — but never discloses that the consequence is that the entire Trust-Enrollment capability cannot produce a usable signer. This phase does not inherit that characterization.

### 3.2 Independent Regression Attribution

Method: two isolated environments compared against the same two commits — phase-entry `d11b8cd0` (checked out via `git worktree add`, not `git stash`) and current HEAD `0459bf76`/`8e1d3227`. Environment 1: this worktree's default Python (no `fido2` package, matching Phase 149O.20L.7O.2F's likely own dev environment per its O-1/O-2 disclosures). Environment 2: a dedicated venv with `pip install -e ".[hatp-hardware]"` (real `fido2` + `cryptography` installed), so the Surface A/B/C test suites could actually execute rather than module-skip. Both ran `python3 -m pytest -k hatp -q --continue-on-collection-errors` against each commit.

- Environment 1 (no `fido2`): baseline `d11b8cd0` = 86 failed/3099 passed/5 skipped/3 errors. Head `0459bf76` = 97 failed/3087 passed/6 skipped/3 errors. 11 net-new failing node IDs, 0 resolved.
- Environment 2 (`fido2` installed): baseline `d11b8cd0` = 94 failed/3416 passed/5 skipped/2 errors. Head `0459bf76` = 105 failed/3450 passed/5 skipped/2 errors. Identical 11 net-new failing node IDs, 0 resolved.

The 11 net-new node IDs (identical in both environments):

```
tests/test_phase_149o_20l_7i_deploymentbinding_producer_implementation.py::TestNoSchemaDrift::test_hatp_bootstrap_byte_unchanged_since_phase_entry
tests/test_phase_149o_20l_7j_deploymentbinding_producer_implementation_independent_verification.py::test_hatp_bootstrap_and_repository_identity_byte_identical_since_7h
tests/test_phase_149o_20l_7l_hmic_frozen_source_scope_amendment_independent_verification.py::test_behavioural_surfaces_are_byte_identical_across_the_amendment[scripts/hatp_deployment_binding_admin.py]
tests/test_phase_149o_20l_7l_hmic_frozen_source_scope_amendment_independent_verification.py::test_behavioural_surfaces_are_byte_identical_across_the_amendment[src/pcae/core/hatp_bootstrap.py]
tests/test_phase_149o_20l_7l_hmic_frozen_source_scope_amendment_independent_verification.py::test_behavioural_surfaces_are_byte_identical_across_the_amendment[src/pcae/core/hatp_deployment_binding_admin.py]
tests/test_phase_149o_20l_7o_2d_1_hatp_principal_signer_enrollment_contract_independent_verification.py::TestNoProductionSourceModified::test_no_src_or_scripts_files_changed_since_phase_entry_commit
tests/test_phase_149o_20l_7o_2d_1_hatp_principal_signer_enrollment_contract_independent_verification.py::TestPrincipalRevokedAtGapReconfirmed::test_parse_principal_allowed_fields_excludes_revoked_at
tests/test_phase_149o_20l_7o_2d_2_hatp_principal_signer_enrollment_contract_repair.py::TestNoProductionSourceModified::test_no_src_or_scripts_files_changed_since_phase_entry_commit
tests/test_phase_149o_20l_7o_2d_hatp_principal_signer_enrollment_contract_architecture.py::TestNoProductionSourceModified::test_hatp_bootstrap_dataclasses_unchanged_shape
tests/test_phase_149o_20l_7o_2d_hatp_principal_signer_enrollment_contract_architecture.py::TestNoProductionSourceModified::test_no_new_production_module_created
tests/test_phase_149o_20l_7o_2d_hatp_principal_signer_enrollment_contract_architecture.py::TestSourceFactsStillTrue::test_parse_principal_allowed_fields_excludes_revoked_at
```

Two spot-checked directly, not merely inferred from name: `test_no_new_production_module_created` fails because `hatp_principal_signer_admin.py` now legitimately exists; `test_hatp_bootstrap_byte_unchanged_since_phase_entry` fails because `hatp_bootstrap.py` was legitimately widened for Surface D. Every one of the 11 is a stale "byte-identical since an earlier, now-superseded phase" or "no new production module" self-check from a prior phase's own verification suite, tripped precisely because Phase 149O.20L.7O.2F legitimately touched exactly the files its own phase doc claims it touched. **No unexplained new failure, no trust-boundary regression, in either environment.**

Additional independent confirmation, not merely accepted from 149O.20L.7O.2F's own claim: with `fido2`/`cryptography` installed, `tests/test_hatp_trust_enrollment_capability.py` + `tests/test_hatp_deployment_binding_admin.py` were run directly — 100/100 passed (46 + 54).

## 4. Surfaces A–E Findings

- **Surface A (FIDO2 enrollment ceremony, `enroll_credential()`):** Well-built in isolation — real CTAP2 `makeCredential`, fail-closed algorithm allowlist (`_SUPPORTED_ENROLLMENT_ALGORITHMS`), correct error mapping, cannot extract a private key (structurally impossible via CTAP2 `makeCredential`). **Blocking at the system level, not as an isolated unit** — see §3.1 and §5 (BF-1, BF-2).
- **Surface B (HHCE-001 writer, `hatp_hardware_credential_admin.py`):** Independently re-derived — idempotent registration, fail-closed conflict handling, monotonic revocation, atomic write + read-back, symlink rejection reused from the existing idiom. `revoked_at` widening on `HardwareCredentialRecord` (`hatp_hardware_credentials.py:112–113,163–173`) correctly reuses `_require_revoked_at_consistency` discipline. **No Blocking finding.**
- **Surface C (Principal/Signer writer, `hatp_principal_signer_admin.py`):** `enroll_signer` (lines 563–698) independently re-read — confirmed continuous two-lock critical section: outer `hardware_credential_transition_lock(...)` nests inner `_deployment_binding_transition_lock(...)`, with the HPSE-REQ-056 precondition check, principal validation, write, read-back, and post-write cross-registry re-verification all textually inside both, no release/reacquire. This structurally closes NBF-1 (from 149O.20L.7O.2D.3) as claimed. **No Blocking finding on this surface in isolation.**
- **Surface D (`PrincipalRecord.revoked_at`):** Confirmed at `hatp_bootstrap.py:103–131,288–306` — `allowed` set widened to include `revoked_at`, `_require_revoked_at_consistency` applied, matches the phase's claim exactly. **No Blocking finding.**
- **Surface E (`DeploymentBinding` producer):** Confirmed `AuthorityEvidence.provider_profile` removed (`hatp_deployment_binding_admin.py:393–410`), `provider_profile` now derived from the resolved `SignerRecord` (line 384), cross-checked against the registered `HardwareCredentialRecord` (lines 378–381). Legitimate breaking change given `DeploymentBinding: ABSENT`. **No Blocking finding.**
- **Runtime neutrality / public-first:** `grep -rIni "claude|codex|deepseek|openai|anthropic"` over both new modules returns zero matches — independently reconfirmed, not merely accepted.

## 5. Findings

**BLOCKING:**

- **BF-1 (production signing unconditionally depends on `provider.credential_identity()`, which FIDO2 leaves unavailable).** `hatp_signing_ceremony.py::_resolve_signer`, the sole identity-resolution path for `production_sign_rollback_evidence` (the real `pcae hatp sign rollback` command, governed by the already-frozen HSCE-001 contract), calls `provider.credential_identity()` unconditionally at line 542. `Fido2HardwareProvider.credential_identity()` remains an unconditional `raise HATPProviderUnavailableError(...)` after this phase (`hatp_fido2_provider.py:307–313`, unchanged). No FIDO2 signer enrolled through this phase's new Surfaces A–E capability can ever be used to sign real evidence in production — the capability is enrollment-only and cannot reach its own purpose. See §3.1.
- **BF-2 (`enroll_credential()` produces a non-resident credential incompatible with the existing discoverable/resident credential-identity model).** `enroll_credential()`'s `ctap2.make_credential(...)` call (`hatp_fido2_provider.py:361–367`) passes no `options` map, so the CTAP2 `rk` bit defaults to `false` — the minted credential is non-resident. `credential_identity()`'s own error text describes the operation it stands in for as requiring "a live CTAP2 device with a discoverable/resident credential." A future `credential_identity()` built on resident-credential discovery/enumeration could not find a credential Surface A itself mints — the credential shape Surface A produces is structurally incompatible with the discovery model `credential_identity()`'s own text commits to. This is independent of BF-1: fixing `credential_identity()` alone, without addressing the resident/non-resident mismatch, would not close the gap. See §3.1.

**NON-BLOCKING:** None recorded this phase beyond the already-carried-forward NBF-149O.20L.7O.2E.1-1 (public_key field-format text), not independently re-verified in the frozen contract text this session (low-priority, editorial, already dispositioned Non-Blocking by 149O.20L.7O.2E.1).

**OBSERVATIONS:**

- **O-1.** `tests/test_hatp_trust_enrollment_capability.py` is entirely module-skipped in a default `pip install -e .` environment without the `hatp-hardware` extra (module-level `pytest.importorskip("fido2")`; `hatp_fido2_provider.py:73` hard-imports `fido2` unconditionally). Independently repaired for verification purposes by building a dedicated venv with `pip install -e ".[hatp-hardware]"` (§3.2). Packaging/CI-environment note, not a contract defect — mirrors 149O.20L.7O.2E.1's own O-2.

## 6. No Repair Performed

Per this phase's scope, no repair of BF-1 or BF-2 was attempted. `hatp_signing_ceremony.py`, `hatp_fido2_provider.py`, and every other production source file were read but not modified in this phase's isolated worktree or in the canonical repository. No push was made from the isolated worktree.

## 7. Final Verdict

```
PHASE 149O.20L.7O.2F (HATP TRUST-ENROLLMENT IMPLEMENTATION CAPABILITY):
BLOCKED

— SURFACES B, C, D, E: INDEPENDENTLY VERIFIED CLEAN, NO BLOCKING FINDING
— SURFACE A (enroll_credential()): CORRECT IN ISOLATION, BLOCKING AT SYSTEM LEVEL
— BF-1: PRODUCTION SIGNING STILL UNCONDITIONALLY DEPENDS ON provider.credential_identity(),
  WHICH FIDO2 LEAVES UNAVAILABLE — NO ENROLLED SIGNER CAN EVER SIGN
— BF-2: enroll_credential() MINTS A NON-RESIDENT CREDENTIAL, INCOMPATIBLE WITH THE
  EXISTING DISCOVERABLE/RESIDENT credential_identity() MODEL
— REGRESSION DELTA INDEPENDENTLY RE-DERIVED (NOT INHERITED FROM 2F'S 304-NODE SET):
  11 NET-NEW FAILURES, 0 RESOLVED, ALL CONFIRMED AS EXPECTED BYTE-IDENTITY/SCHEMA-WIDENING
  SELF-CHECKS, IN TWO INDEPENDENT ENVIRONMENTS — NO UNDISCLOSED TRUST-BOUNDARY REGRESSION
— LANE 1 (46+54 TESTS) INDEPENDENTLY RE-RUN AND CONFIRMED 100/100 PASSED WITH REAL fido2 INSTALLED
— NO REPAIR PERFORMED THIS PHASE
— NO PRODUCTION SOURCE MODIFIED, NO CONTRACT TEXT MODIFIED
```

## 8. Next Phase

**149O.20L.7O.2F.2 — FIDO2 Signing-Time Credential Resolution Repair.** Must begin with an explicit contract-level decision between:

(a) **Authenticator rediscovery** — implement a real `credential_identity()` compatible with the non-resident credentials `enroll_credential()` already mints (e.g., `_resolve_signer` supplying the trust store's enrolled `signer_key_id`s as an `allow_list` to CTAP2 `get_assertion`/discovery, rather than requiring bare resident-credential enumeration), or

(b) **Durable-registry signer resolution** — amend HSCE-001's signing-time identity-resolution mechanism itself to consume the durable `HardwareCredentialRecord`/`SignerRecord` registries this phase's own Surfaces B/C already populate, rather than requiring a live `credential_identity()` round-trip at sign time.

This decision must be made and disclosed explicitly, with its consequences for both BF-1 and BF-2 traced through before any repair implementation begins. Until 149O.20L.7O.2F.2 resolves this, no positive authority should be attributed to the Trust-Enrollment capability as "complete" — it remains enrollment-only.

## 9. No-Go Boundary Compliance (Restated Positively, Literal)

No production source file under `src/pcae/**` was modified this phase. No file under `scripts/**` was modified this phase. HPSE-001 was not modified this phase. HHCE-001 was not modified this phase. HSCE-001 was not modified this phase. BF-1 was not repaired this phase. BF-2 was not repaired this phase. No hardware was provisioned this phase. No credential was registered this phase against real hardware. No principal was enrolled this phase. No signer was enrolled this phase. No Dell host was mutated this phase. No election was initiated this phase. No CHGR was published this phase. No certification was performed this phase. HATP was not activated this phase.

## 10. Governance Results

- `pcae check`: passed.
- `pcae health`: healthy, agent lock held by `claude-local`, session continuity verified.
- No raw `git commit`. No raw `git push`. No `--no-verify`. No force push. No governance bypass of any kind.
- Regression evidence: see §3.2 — independently re-derived across two environments against the actual phase-entry commit, not inherited from Phase 149O.20L.7O.2F's own deselection set.
- Verification performed in isolated git worktree `.claude/worktrees/agent-a1254e16c5a2b9cda`; canonical repository confirmed unmodified throughout (`git status --short` clean before and after, aside from this phase's own documentation/task/status files).
