# Phase 149O.20L.7O.2L.3 — HATP Hardware-Credential Admin Recovery Authority Narrow Repair

Narrow-repair phase. **NO TRUST-ENROLLMENT REAL EFFECT PERFORMED. NO HMIC AMENDMENT. NO HHCE/HPSE CONTRACT CHANGE.**

## 1. Phase Entry State

- True phase-entry commit: `2396055f` ("Phase 149O.20L.7O.2L.2: task lifecycle sync (close task, open idle placeholder)"). `origin/main..HEAD` = 0 at entry; working tree clean at entry.
- Latest completed phase entering 2L.3: 149O.20L.7O.2L.2 — HATP Trust-Enrollment Standalone Protected Admin Entry-Point Independent Verification. Verdict: **NOT VERIFIED** — one Blocking finding: **HARDWARE-ENROLLMENT RECOVERY AUTHORITY DEFECT**.

## 2. Blocking Finding Repaired (Exact)

Independently verified by 2L.2 (`docs/PHASE_149O_20L_7O_2L_2_...md` §7, commit `ab12406e`): `scripts/hatp_hardware_credential_admin.py` exposed a public `recover` subcommand that:

- was not authorized by HHCE-001 v1.1 (HHCE-REQ-015 names exactly `register_credential`/`revoke_credential`, no third "recovery" operation);
- was not authorized by the Phase 149O.20L.7O.2L architecture-freeze document, which named only register/revoke for this script and explicitly described the intended recovery mechanism as an in-process retry requiring "no additional recovery state machine... not by a new mechanism this phase needs to invent" (§6 of that document);
- accepted fully human-typed `--signer-key-id`/`--provider-profile`/`--protocol-name`/`--algorithm`/`--public-key-hex` values with zero binding to any actual completed hardware ceremony;
- persisted that fabricated evidence as an authoritative, active `HardwareCredentialRecord` (demonstrated concretely by 2L.2's own exploit test, exit code 0, fabricated `signer_key_id`/`public_key_hex` found in the written registry).

## 3. Repair Decision

**Removed the public `recover` subcommand entirely.** Did not amend HHCE-001. Did not invent a recovery token/provenance protocol. Did not redesign Trust-Enrollment.

Considered and rejected: extending HHCE-001/the architecture to formally authorize an external human-entry recovery path. Rejected because no primary evidence demonstrates such a path is required — the architecture-freeze document's own §6 already states the contract-supported model (physical ceremony → provider-generated evidence → `register_credential`, with in-process retry of that same evidence) is sufficient, and 2L.2's own finding is precisely that 2L.1 built an unauthorized path *instead of* the already-specified in-process retry, not that the specified retry was insufficient.

## 4. Primary-Source Re-Read (Independent, Not Trusted from 2L.2's Summary)

Re-read directly this phase: `docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md` (HHCE-001 v1.1, full text, §11 "Hardware Credential Writer API"), `docs/PHASE_149O_20L_7O_2L_POST_HMIC_ACTIVATION_TRUST_ENROLLMENT_DAG_RE_DERIVATION_AND_ADMINISTRATIVE_ENTRY_POINT_ARCHITECTURE.md` (§4-§6, "Failure-After-Hardware-Creation Design"), `scripts/hatp_hardware_credential_admin.py` (full file, pre-repair), `src/pcae/core/hatp_hardware_credential_admin.py` (full file), `src/pcae/core/hatp_fido2_provider.py` (`enroll_credential()`, `EnrolledFido2Credential`).

Confirmed independently:
- HHCE-REQ-015 names exactly `register_credential`/`revoke_credential` (+ preview variants) — no recovery/import operation.
- HHCE-REQ-016: `register_credential` is idempotent on identical evidence (`_candidate_equal` compares `provider_profile`/`protocol_name`/`algorithm`/`public_key_hex`) — a retry with the same evidence object is always safe: no-op if it already landed, a genuine write if it did not.
- HHCE-REQ-017: differing evidence for the same `signer_key_id`, or an existing revoked record, fails closed as `CredentialConflictError` — never overwrites, never reactivates.
- `core/hatp_hardware_credential_admin.py` was **not modified** to support this repair — the existing idempotency semantics already provide everything an in-process retry needs. No core writer change was required or made.

## 5. Exact Source Change

`scripts/hatp_hardware_credential_admin.py`:

- Removed: `recover` argparse subcommand and all five of its CLI arguments (`--signer-key-id`, `--provider-profile`, `--protocol-name`, `--algorithm`, `--public-key-hex`, plus the shared `--repository-root`/`--enrollment-reference`/`--assume-yes`/`--preview`); the `_cmd_recover` dispatch function; the `recover` branch in `main()`; `_print_recovery_evidence` (the helper that printed full credential identity material for manual re-entry into `recover`).
- Added: `_register_with_in_process_retry(*, repository_root, evidence)` — a bounded (3-attempt) retry loop around the existing `register_credential()`, called from `_cmd_enroll` in place of the former single call. Reuses the identical `CredentialEnrollmentEvidence` object the one ceremony call already produced; never calls `_run_enrollment_ceremony`/`enroll_credential` a second time; never accepts caller-supplied identity. On exhausting all retries, prints a diagnostic (`REGISTRY PERSISTENCE DIAGNOSTIC: ...this operation requires governed reconciliation/retry; no manual credential import path exists.`) that names no credential material, then re-raises the last error.
- Not removed/not modified: `enroll`'s hardware-ceremony call, confirmation gate, and preview path; `revoke`/`_cmd_revoke`; the module's imports; `_prompt_confirm`/`_describe_preview`/`_report_result`.

`src/pcae/core/hatp_hardware_credential_admin.py`, `src/pcae/core/hatp_principal_signer_admin.py`, `src/pcae/core/hatp_fido2_provider.py`, `src/pcae/core/hatp_hardware_credentials.py`, `src/pcae/core/hatp_bootstrap.py`, `src/pcae/core/hatp_deployment_binding_admin.py`, `scripts/hatp_principal_signer_admin.py`, `docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md`: **byte-unchanged since phase entry** (git-diff-asserted, `tests/test_phase_149o_20l_7o_2l_3_...py::TestNoCoreWriterOrContractChanges`, `::TestPrincipalSignerScriptUnchanged`).

## 6. Public CLI Before/After

Before: `enroll`, `recover`, `revoke`. After: `enroll`, `revoke`. `--help` no longer mentions `recover` anywhere (out-of-process subprocess check). Any `recover ...` invocation now fails at argparse parsing (`SystemExit` code 2) before any provider/writer call is reached.

## 7. Fabricated-Evidence Rejection Proof

`tests/test_phase_149o_20l_7o_2l_3_...py::TestNoCallerSuppliedIdentityImportSurface::test_fabricated_evidence_cannot_be_submitted_through_any_public_cli_path` and `TestRecoverSubcommandRemoved` prove: no sequence of CLI arguments under any subcommand can submit a caller-fabricated `signer_key_id`/`public_key_hex` for record creation; `enroll` never declares identity flags at all (argparse rejects them); no import/restore/register-from-fields/manual-credential flag or subcommand exists anywhere on the script's public surface (mechanical argparse-choices + source-text search). 2L.2's own historical exploit test (`tests/test_phase_149o_20l_7o_2l_2_...py::TestRecoverScopeAndProvenance::test_recover_accepts_fully_fabricated_evidence_with_no_prior_ceremony`) is updated in place (not deleted) to assert the identical attempt now fails at argparse parsing (`SystemExit` code 2) with zero registry write, while its docstring preserves the original finding's narrative; the vulnerable code remains permanently inspectable in git history at commit `ab12406e`.

## 8. `enroll` FIDO2 Call-Count Proof

`tests/test_phase_149o_20l_7o_2l_3_...py::TestEnrollSingleCeremonyInvariant::test_enroll_calls_ceremony_exactly_once_even_when_write_is_retried`: with a flaky `register_credential` (fails once, then succeeds), the ceremony seam (`_run_enrollment_ceremony`) is invoked exactly once and `register_credential` is invoked exactly twice, both times with the identical evidence object (`is` comparison, not merely `==`).

## 9. Hardware-Success / Persistence-Failure Behavior (Full Matrix)

`TestHardwareSuccessPersistenceFailureMatrix`:
- **Never-landed write**: fails twice, lands on the third in-process attempt — record ends up active, no orphaned state.
- **Already-landed write, ack/audit failure**: the write actually succeeds on attempt 1 but the caller sees an exception (simulating a post-write audit failure); retry resolves via `register_credential`'s own idempotency (`ALREADY_REGISTERED`, no duplicate) — code 0, single active record.
- **Conflicting state**: a genuine differing-evidence conflict (`CredentialConflictError`) fails identically on every attempt and fails closed after exhausting retries — the pre-existing record is never overwritten.
- **Exhausted retries with a persistent failure**: fails closed (exit code 1), diagnostic printed naming no credential material (`RECOVERY EVIDENCE` string absent, public-key hex absent from output), directing the operator to governed reconciliation.

## 10. Revoke Regression

`TestRevokeUnchanged`: `revoke` still revokes an existing active record (exit code 0, `outcome=revoked`), and a declined confirmation still makes zero writer calls (record remains active). `scripts/hatp_hardware_credential_admin.py`'s `_cmd_revoke`/`revoke_parser` wiring is unmodified by this repair — only the `recover_parser` block and the `enroll` write path changed.

## 11. Principal/Signer Script Unchanged

`scripts/hatp_principal_signer_admin.py` is git-diff-asserted byte-identical since phase entry; its public surface remains exactly `enroll-principal`/`revoke-principal`/`enroll-signer`/`revoke-signer` (unchanged from 2L.2's own independently-verified six clean properties).

## 12. Thin-Wrapper Proof

No `json.dump(s)`/`json.load(s)`/`fcntl.flock` call anywhere in the repaired script (AST-checked). `_register_with_in_process_retry`'s own body contains no registry validation/persistence/canonicalization/lock logic — its only calls are `register_credential`, `print`, `range`, `len`, `type` (AST-enumerated and asserted against an explicit allowlist) — a thin call-and-catch loop, not a reimplemented transaction engine. The script's `pcae.core.*` imports are unchanged: `hatp_hardware_credential_admin`, `hatp_hardware_credentials`, `hatp_providers`, and (lazily) `hatp_fido2_provider`.

## 13. No Core Writer / Contract Changes

`git diff --name-only 2396055f..HEAD -- src/pcae/core/hatp_hardware_credential_admin.py src/pcae/core/hatp_principal_signer_admin.py src/pcae/core/hatp_fido2_provider.py src/pcae/core/hatp_hardware_credentials.py src/pcae/core/hatp_bootstrap.py src/pcae/core/hatp_deployment_binding_admin.py` — empty. `git diff --name-only 2396055f..HEAD -- docs/contracts` — empty. HHCE-001 remains v1.1, `**Version:** 1.1` string-asserted present.

## 14. Historical Exploit Evidence Preserved

2L.2's own test file docstring and `TestRecoverScopeAndProvenance` class are edited in place, not deleted, per the governing prompt's §20 instruction: the historical finding's full narrative (mechanism, why shape-valid recovery evidence was insufficient authorization, the repair) is preserved in prose; the executable assertion is converted to prove the CURRENT tree rejects the identical exploit attempt. The vulnerable implementation itself is preserved verbatim in git history at commit `ab12406e` (`git show ab12406e:scripts/hatp_hardware_credential_admin.py`).

## 15. Fresh HMIC-REQ-052 Analysis (Post-Repair)

Both scripts still answer **YES** to HMIC-REQ-052's authority-sensitivity test — removing `recover` does not make `scripts/hatp_hardware_credential_admin.py` non-authority-bearing: it remains the sole caller deciding which `register_credential`/`revoke_credential` call happens, with what evidence, after what confirmation. `_FROZEN_AUTHORITY_BEARING_FILES` remains exactly 36 (unmodified by this phase — no HMIC action performed). Neither script is yet a member of `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`. Exact future HMIC-REQ-050 delta remains **36 + 2 = 38**, unchanged from 2L/2L.1/2L.2's own derivation (`tests/test_phase_149o_20l_7o_2l_3_...py::TestFreshHmicReq052AnalysisAfterRepair`).

## 16. Focused Tests

- `tests/test_phase_149o_20l_7o_2l_3_hatp_hardware_credential_admin_recovery_authority_narrow_repair.py` — **27 passed, 0 failed** (new, independently authored this phase).
- `tests/test_hatp_hardware_credential_admin_script.py` — **28 passed, 0 failed** (updated: `recover`-specific tests converted to absence/retry tests; `RECOVERY EVIDENCE` assertions removed).
- `tests/test_phase_149o_20l_7o_2l_1_hatp_trust_enrollment_admin_entrypoint_implementation.py` — **28 passed, 0 failed** (updated: `recover`-presence assertions converted to `recover`-absence assertions).
- `tests/test_phase_149o_20l_7o_2l_2_hatp_trust_enrollment_admin_entrypoint_independent_verification.py` — **20 passed, 0 failed** (updated in place per §14 above).
- `tests/test_hatp_principal_signer_admin_script.py` — unchanged, re-run for regression: passes.
- Combined focused run (`hatp_hardware_credential_admin_script.py` + `hatp_principal_signer_admin_script.py` + all four 2L/2L.1/2L.2/2L.3 phase test files): **134 passed, 0 failed**.

## 17. Fast Green — Raw Outcome and Attributable Regressions

Ran twice for comparison: candidate working tree (uncommitted) vs. a `git stash`-isolated pre-repair baseline, both under `python -m pytest -m fast_green -n auto -q`.

- Baseline (pre-repair, stashed): 333 failed, 8472 passed, 4 skipped, 9 errors.
- Candidate (this phase's uncommitted changes): 345 failed, 8486 passed, 4 skipped, 9 errors.
- Diff of FAILED/ERROR test-node sets: **12 tests appear in the candidate list but not the baseline list; zero tests appear in the baseline list but not the candidate list.**

All 12 are non-attributable:
- **8 are dirty-working-tree checks** (`test_no_scripts_files_dirty_in_working_tree`, `test_no_src_pcae_or_scripts_files_dirty`, `test_git_status_touches_no_src_pcae_or_existing_contract_file`, `test_git_status_touches_no_src_pcae_scripts_or_contract_file`, `test_no_authority_relevant_source_mutated_by_this_phase` ×2, `test_this_phase_touches_no_production_source_or_contract_files`) — each asserts `git status --short -- scripts/ ...` is empty; they fail only because `scripts/hatp_hardware_credential_admin.py` was uncommitted at comparison time. Verified by direct inspection of each assertion's source. These resolve once this phase's changes are committed (the working tree becomes clean relative to HEAD again).
- **2 are confirmed flaky under `-n auto` parallel execution**, not related to this phase's files: `tests/test_backend_cli.py::TestBackendReviewReject::test_reject_updates_latest` and `tests/test_phase_149o_20l_7o_2k_3_hatp_hmic_certificationrecord_real_host_creation_source_parity_revalidated.py::TestCreateOnlyWriterBehavior::test_activate_on_unknown_id_fails_closed` — both re-run individually and pass; neither touches `scripts/hatp_hardware_credential_admin.py`, `hatp_hardware_credential_admin` (core), or any file this phase changed.

**Zero attributable regressions.**

## 18. Finding Status

**HARDWARE-ENROLLMENT RECOVERY AUTHORITY DEFECT: REPAIRED — INDEPENDENT VERIFICATION PENDING.** Not self-closed. Closure requires Phase 149O.20L.7O.2L.4's independent re-verification.

## 19. No-Hardware / No-Dell / Runtime-Unchanged Proof

Every FIDO2 interaction in every test this phase touches is a synthetic monkeypatched seam (`_run_enrollment_ceremony`/`_fake_ceremony_factory`) — no USB enumeration, no authenticator touch, no real CTAP2 `makeCredential`. No connection to `hac-dell` was made. No `HardwareCredentialRecord`/`Principal`/`Signer`/`DeploymentBinding` was created against any production/protected path — every writer call in this phase's tests targets a disposable `tmp_path` root via `_store_root=`. No HMIC source scope was changed (`_FROZEN_AUTHORITY_BEARING_FILES` unmodified). No HATP readiness/activation state was touched.

## 20. Commits, Push, Recommended Next Phase

See `.pcae/phase-completion-report.md` for literal governance-command output and the exact commit hash / `origin/main..HEAD` count captured at finalization.

**Recommended next phase**: **149O.20L.7O.2L.4 — independent verification of the recovery-authority repair.** Must independently confirm: no public `recover`/import route exists; fabricated credential evidence cannot be persisted through any CLI path; provider-derived enrollment (`enroll`'s single-ceremony, evidence-from-provider-only behavior) remains intact; the in-process retry's safe failure/idempotent/conflict semantics hold under independently-authored instrumentation; no authority regression elsewhere (principal/signer script, revoke). Do not proceed to HMIC v1.7 source-scope evolution until 2L.4 closes this Blocking finding.
