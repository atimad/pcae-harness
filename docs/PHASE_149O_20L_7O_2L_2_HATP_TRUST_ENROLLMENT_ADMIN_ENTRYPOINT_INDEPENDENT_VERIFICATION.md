# Phase 149O.20L.7O.2L.2 — HATP Trust-Enrollment Standalone Protected Admin Entry-Point Independent Verification

Verification-only phase. **NO TRUST-ENROLLMENT REAL EFFECT PERFORMED. NO REPAIR PERFORMED.**

## 1. Phase Entry State

- True phase-entry commit for 2L.1 (the "pre-2L.1" fixed checkpoint): `d4c699e5` ("Phase 149O.20L.7O.2L: finalize task transition to idle").
- Latest completed phase entering 2L.2: 149O.20L.7O.2L.1 — HATP Trust-Enrollment Standalone Protected Admin Entry-Point Implementation.
- `origin/main..HEAD` = 0 at entry; working tree clean at entry.

## 2. Fixed Historical Checkpoint

An isolated `git worktree` was created at `d4c699e5`. Confirmed directly (not trusted from 2L.1's own report):
- `scripts/hatp_hardware_credential_admin.py` and `scripts/hatp_principal_signer_admin.py` are **absent** at this commit.
- All six named core writer modules (`hatp_hardware_credential_admin.py`, `hatp_principal_signer_admin.py`, `hatp_fido2_provider.py`, `hatp_hardware_credentials.py`, `hatp_bootstrap.py`, `hatp_deployment_binding_admin.py`) already **exist**.
- `diff -q` of all six core writers between the fixed checkpoint and current HEAD: **byte-identical, zero output** — 2L.1 modified no core writer.

## 3. Independent CLI Grammar Reconstruction

Directly read (not reconstructed from 2L.1's report):
- `scripts/hatp_hardware_credential_admin.py`: subcommands exactly `enroll`, `recover`, `revoke`. `enroll` has no `--signer-key-id`/`--public-key-hex`/`--algorithm`/`--provider-profile` flags. `recover` requires all five identity fields as plain CLI strings, human-typed. No `--store-root`/`--output`/root-override flag on any subcommand.
- `scripts/hatp_principal_signer_admin.py`: subcommands exactly `enroll-principal`, `revoke-principal`, `enroll-signer`, `revoke-signer`. `_protected_root`/`_hardware_store_root` are never exposed as CLI flags (hardcoded `None` in `main()`, resolved to production roots only inside the core writer).

## 4. Thin-Wrapper Proof

AST inspection of both scripts: no `json.dump(s)`/`json.load(s)`/`fcntl.flock` calls anywhere in either script. `hatp_hardware_credential_admin.py`'s only `pcae.core.*` imports are `hatp_hardware_credential_admin`, `hatp_hardware_credentials`, `hatp_providers`, and (lazily, inside `_run_enrollment_ceremony`) `hatp_fido2_provider` — exactly the intended provider seam, imported lazily to preserve the existing "fido2 extras optional" discipline. Confirmed: no parsing/validation/identity-derivation/locking/persistence/duplicate-resolution/revocation logic is reimplemented in either script — every mutating call is a single pass-through into the unmodified core writer.

## 5. Exact Core Call Graph

- `enroll` → `Fido2HardwareProvider.enroll_credential()` → (evidence built) → `register_credential()`.
- `recover` → (evidence built directly from CLI args) → `register_credential()`.
- `revoke` → `revoke_credential()`.
- `enroll-principal`/`revoke-principal`/`enroll-signer`/`revoke-signer` → `enroll_principal`/`revoke_principal`/`enroll_signer`/`revoke_signer` (one call each, no alternate writer path).

## 6. Live Instrumentation Results

- **Confirmation boundary**: declined confirmation (`input()` → `"no"`) on `enroll` and `recover` produces exit code 1, zero calls into `register_credential`, and no `hardware-credentials.json` written — instrumented directly, not merely output-checked.
- **Recovery never touches hardware**: `_cmd_recover` contains no reference to `_run_enrollment_ceremony`/`enroll_credential` (AST-checked); live-instrumented `recover` run makes zero calls to the ceremony seam.
- **Two-lock continuity (`enroll_signer`)**: live-traced lock acquire/release order against disposable `tmp_path` roots: `hw_acquire → bind_acquire → bind_release → hw_release` — confirms `hardware_credential_transition_lock` (outer) and `_deployment_binding_transition_lock` (inner) are held continuously, nested correctly, across the whole critical section, exactly as HPSE-REQ-057/HHCE-REQ-037 require.
- **No DeploymentBinding/HMIC/HATP side effects**: grep + live disposable-state runs confirm neither script references `create_deployment_binding`, `certify(`, or `activate_hatp_mandatory`; no `deployment-bindings.json` file is created by any hardware-script operation.
- **Secret safety**: no `--pin`/`--private-key`/`--secret`/`--password`/`--bearer-token` flag exists on either script; only public credential-identity fields are ever printed as "RECOVERY EVIDENCE".
- **Path containment**: neither script exposes a store-root/output/protected-root override flag; `--repository-root` is a neutral locator only, resolved to the fixed production root by the unmodified core writer.

## 7. Recovery Provenance Analysis — BLOCKING FINDING

Independently re-derived from primary source, not trusted from 2L.1:

- **HHCE-001 v1.1 never mentions "recover"** anywhere in its text. HHCE-REQ-015 names exactly two mutating writer operations, `register_credential`/`revoke_credential` (plus preview variants) — no third "recovery" operation is contract-defined.
- **Phase 149O.20L.7O.2L's own architecture-freeze document** (`docs/PHASE_149O_20L_7O_2L_...md`, §18, "Selected Next Implementation Phase Scope") explicitly authorizes, for the hardware script: `` `scripts/hatp_hardware_credential_admin.py` (register/revoke, mirroring `hatp_deployment_binding_admin.py`'s CLI shape...; never caller-supplied credential ID/public key). `` — a single, unqualified sentence naming only two operations, with an explicit "never caller-supplied credential ID/public key" clause.
- That same document's §6 states the *intended* recovery mechanism precisely: a `makeCredential` success followed by a `register_credential()` failure is recovered by retrying `register_credential()` "with the identical evidence" **already held by the caller** (the same in-process script/operator from the same failed attempt) — "the two-transition split by itself provides the recovery path... so no additional recovery state machine is required — HHCE-001 already covers this by construction, not by a new mechanism this phase needs to invent."
- 2L.1 did not implement that in-process retry. It instead added a **separate, third CLI subcommand** (`recover`) that accepts fully human-typed `--signer-key-id`/`--provider-profile`/`--protocol-name`/`--algorithm`/`--public-key-hex` values and passes them straight into `register_credential()` with **zero binding** to any actual completed hardware ceremony.
- A fresh, independently-authored test (`TestRecoverScopeAndProvenance::test_recover_accepts_fully_fabricated_evidence_with_no_prior_ceremony`) demonstrates this concretely: fully fabricated `signer_key_id`/`public_key_hex` values that were never produced by any `enroll_credential()` call are accepted by `recover --assume-yes` and persisted as an authoritative, active `HardwareCredentialRecord`, exit code 0.
- This is not merely a theoretical gap: it directly contradicts `enroll`'s own module-docstring invariant ("`signer_key_id`/`public_key`/`algorithm` are never caller-supplied here") for the one subcommand (`recover`) that is the described exception — an exception the governing architecture document never authorized.

**Disposition**: The security boundary this whole admin-script architecture relies on (OS filesystem write permission on the Protected Root, per HHCE-REQ-020/HPSE-REQ-029, mirroring HBDC-REQ-066) is real and unchanged — this is not a claim that the OS-level boundary is broken. But `recover`'s specific CLI shape is (a) not named or required by HHCE-001, and (b) affirmatively **contradicted** by 2L's own architecture-freeze document, which both limited the hardware script's authorized surface to register/revoke and explicitly described the intended recovery mechanism as requiring no new external-input surface at all. Introducing a second, independent way to mint an authoritative `HardwareCredentialRecord` from arbitrary human-typed values — never required, never authorized, and inconsistent with the one document that scoped this implementation phase — is classified **Blocking** per this phase's own adjudication instructions (§18/§43 of the governing prompt): "If the script accepts arbitrary unsigned/unbound recovery material and persists it as authoritative `HardwareCredentialRecord` without contract authority, classify Blocking" and "[public-surface scope expansion] may be Blocking even if implementation is technically sound."

## 8. Public-Surface Scope Classification

- `enroll` (hardware): **CLEAN** — explicitly authorized by 2L's architecture doc.
- `revoke` (hardware): **CLEAN** — explicitly authorized by 2L's architecture doc (paired with `register`/`enroll`).
- `recover` (hardware): **BLOCKING** — not named by HHCE-001, not named by 2L's architecture doc, and directly inconsistent with that document's own described recovery mechanism (in-process retry, no new CLI surface).
- `enroll-principal`/`revoke-principal`/`enroll-signer`/`revoke-signer` (principal/signer): **CLEAN** — all four are explicitly, individually named by 2L's architecture doc §18.

## 9. Independent HMIC-REQ-052 Analysis and Transitive Closure

Both scripts' `pcae.core.*` imports were independently enumerated (AST-walked, not trusted from 2L.1): both remain entirely within the current HMIC v1.6 frozen 36-file set (no import of any module outside it). Independently answering HMIC-REQ-052's own test for each script: modifying either script while every currently-bound byte stays unchanged **could** alter an authority-bearing Trust-Enrollment result (e.g. a modified `recover` could import arbitrary evidence with even less friction, or a modified `enroll` could skip confirmation) — **YES** for both, confirming the exact future HMIC delta is these two script files (36 → 38), pending resolution of the Blocking finding above. No hidden dependency (e.g. no repeat of the historical `paths.py` under-count) was found in either script's import closure.

## 10. Active Dell Certification Consequence

Unchanged and unaddressed by this phase: the current active certification (bound to the 36-file v1.6 `implementation_scope_digest`) remains valid for its own currently-deployed identity, which does not include either new script. The new scripts must not be used against Dell before an HMIC v1.7 scope evolution, independent verification of that evolution, redeployment, and a new CertificationRecord/activation — none of which are authorized or performed here, and which in any case cannot proceed responsibly while the Blocking finding above stands unrepaired.

## 11. Regression / Fast Green

- A fresh, independently-authored verification suite (`tests/test_phase_149o_20l_7o_2l_2_hatp_trust_enrollment_admin_entrypoint_independent_verification.py`, 20 tests, does not import or extend any 2L.1 test file) was written and run: **20 passed, 0 failed.**
- Fast Green (`-m fast_green -n auto`) was run twice: once against the current tree (this phase's own new test file included), once against an isolated `git worktree` fixed at the pre-2L.1 commit (`d4c699e5`). Raw results: fixed baseline **334 failed, 8240 passed, 7 skipped, 12 errors**; current **333 failed, 8320 passed, 8 skipped, 12 errors**. Node-ID diff: exactly one test appears as failed only in the current run (`tests/test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`); re-run in isolation, it **passes** — a `pytest-xdist` ordering flake, not attributable to 2L.1 or 2L.2. **Zero attributable regressions.** The remaining 333/334 failures are pre-existing, historical-baseline-drift debt (stale phase-entry-commit self-checks from dozens of earlier phases, e.g. `test_phase_149o_17_*`, `test_phase_149o_18*_*`, `test_phase_149o_20e_*`) unrelated to Trust-Enrollment and out of this phase's scope to repair.

## 12. Verdict

**C — NOT VERIFIED: HARDWARE-ENROLLMENT RECOVERY AUTHORITY DEFECT** (with a contributing F-type public-surface scope-expansion classification for the same `recover` subcommand).

All other verified surfaces (`enroll`, `revoke`, all four principal/signer operations, two-lock continuity, confirmation boundary, path containment, secret safety, no out-of-scope side effects, transitive closure) are **CLEAN**. The sole Blocking finding is `recover`'s unauthorized, unauthenticated arbitrary-credential-import surface on the hardware script. Per this phase's own governing instructions, this defect is **preserved, not repaired**, in 2L.2.

## 13. Recommended Next Phase

**149O.20L.7O.2L.3 — narrowest repair**: resolve the `recover` scope/provenance defect by one of: (a) removing the `recover` subcommand entirely and instead documenting the in-process-retry recovery path 2L's own architecture already specified (no new CLI surface); or (b) if a human-entry recovery path is genuinely still desired, obtaining an explicit architecture/contract amendment that names it and defines a provenance-binding requirement (e.g. binding recovery evidence to the specific failed `enroll` attempt via a token/digest), then re-implementing to that amended authority. Do not proceed to HMIC v1.7 source-scope evolution until this is repaired and independently re-verified.

## 14. No Real Effect / No Mutation Proof

No physical FIDO2/PIV hardware was touched. No `HardwareCredentialRecord`/`Principal`/`Signer`/`DeploymentBinding` was created on any production/protected path — every writer/provider call in this phase's own test suite uses disposable `tmp_path` state and a monkeypatched provider seam. No Dell (hac-dell) host was connected to or mutated. No HMIC certification action was performed. No HATP activation occurred. Runtime state unchanged throughout (`Observed`/`observe`/`unavailable`, confirmed via `pcae runtime inspect` before and after). This phase wrote only: this doc, its companion test file, `CHANGELOG.md`, `PROJECT_STATUS.md`, `.pcae/phase-completion-metadata.json`, `.pcae/phase-completion-report.md`, and task-lifecycle files.
