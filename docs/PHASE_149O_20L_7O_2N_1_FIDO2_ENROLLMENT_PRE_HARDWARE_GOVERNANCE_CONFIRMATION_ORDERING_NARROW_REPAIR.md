# Phase 149O.20L.7O.2N.1 — FIDO2 Enrollment Pre-Hardware Governance Confirmation Ordering Narrow Repair

Narrow implementation-repair phase. **NO REAL HARDWARE TOUCHED. NO `fido2` PACKAGE INSTALLED. NO DELL CONNECTION. NO HMIC/CONTRACT/PRINCIPAL/SIGNER CHANGE.**

## 1. Phase Entry State

- True phase-entry commit: `cbcbcc0c` ("Phase 149O.20L.7O.2N: task lifecycle sync (close task, open idle placeholder)"). `origin/main..HEAD` = 0 at entry; working tree clean at entry.
- Latest completed phase entering 2N.1: 149O.20L.7O.2N — Post-HMIC-v1.7 Trust-Enrollment Real-Effect Node Selection and FIDO2 Enrollment Authorization. Verdict B/D (no usable FIDO2 authenticator, `fido2` package absent). No authorization envelope frozen.

## 2. Blocking Finding Repaired (Exact)

**B-149O.20L.7O.2N-1 — FIDO2 Enrollment Governance Confirmation / Hardware-Effect Ordering Defect.** 2N independently established from current production source that `scripts/hatp_hardware_credential_admin.py::_cmd_enroll` ran the real FIDO2 `makeCredential` ceremony (`_run_enrollment_ceremony` → `Fido2HardwareProvider.enroll_credential()`) **before** the governance confirmation gate (`_prompt_confirm`/`--assume-yes`) was even constructed or checked. A declined confirmation could not prevent a real hardware effect that had already happened.

## 3. Primary-Source Re-Derivation (Not Trusted From 2N's Prose)

Re-read directly this phase: `docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md` (HHCE-001 v1.1), `docs/PHASE_149O_20L_7O_2L_POST_HMIC_ACTIVATION_TRUST_ENROLLMENT_DAG_RE_DERIVATION_AND_ADMINISTRATIVE_ENTRY_POINT_ARCHITECTURE.md` (architecture freeze), `docs/PHASE_149O_20L_7O_2L_4_...md` (independent verification evidence), `scripts/hatp_hardware_credential_admin.py` (pre-repair, full file), `src/pcae/core/hatp_hardware_credential_admin.py`, `src/pcae/core/hatp_fido2_provider.py`, `scripts/hatp_principal_signer_admin.py` (precedent for `--assume-yes` semantics).

Mechanically reproduced the defect with a synthetic provider seam and instrumented `_run_enrollment_ceremony`/`_prompt_confirm` calls against the fixed pre-repair checkpoint (`cbcbcc0c`), declining confirmation:

```
EVENT ORDER: ['PROVIDER_ENROLLMENT_CALLED', 'CONFIRMATION_CHECKED']
exit code: 1
```

Confirmed the vulnerable ordering exactly as 2N described — the ceremony ran unconditionally, and only afterward did `_cmd_enroll` construct the preview/confirmation description and check `_prompt_confirm`. This reproduction is preserved as `tests/test_phase_149o_20l_7o_2n_1_...py::test_pre_repair_checkpoint_reproduces_provider_before_confirmation`, which loads the script's source directly from the frozen `cbcbcc0c` git blob (not the current working tree) so the historical defect stays independently re-demonstrable after this repair lands.

## 4. Exact Authority Requirement Determined

The pre-hardware confirmation may bind only information that exists before any ceremony runs: `repository_root`, `enrollment_reference`, the fixed provider-profile constant (`HATP_HARDWARE_PROVIDER_V1`, a plain string imported from `hatp_providers.py` — no `fido2`/hardware import required to read it), the operation name (`ENROLL HARDWARE CREDENTIAL`), and the ceremony's own presence-timeout policy. It cannot bind `signer_key_id`/`public_key`, since neither exists until `makeCredential` succeeds — no prospective credential identity is fabricated anywhere in the repaired prompt.

Two-stage human evidence: **not required**. HHCE-001 v1.1 and the 2L architecture-freeze document specify only a single pre-effect authorization (`enrollment_reference`, HHCE-REQ-049, audit metadata for a fresh separate human election) plus the runtime confirmation this phase repairs. Post-ceremony output (`_report_result`) remains audit evidence only, never a second permission gate — no primary source requires more.

## 5. Narrow Repair Target

`scripts/hatp_hardware_credential_admin.py` only. No change to `src/pcae/core/hatp_hardware_credential_admin.py` (core writer), `src/pcae/core/hatp_fido2_provider.py` (provider), `docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md`, or `scripts/hatp_principal_signer_admin.py`/`src/pcae/core/hatp_principal_signer_admin.py`. The script architecture could safely express the required ordering without any core change — confirmed by `tests/test_phase_149o_20l_7o_2n_1_...py::test_all_other_hmic_bound_files_byte_identical_across_2n_1` (parametrized over all 9 other HMIC-bound production/contract files, git-blob-diffed against the pre-repair checkpoint).

## 6. Exact Code Change

`scripts/hatp_hardware_credential_admin.py`:

- Added `_describe_prospective_enrollment(*, repository_root, enrollment_reference, presence_timeout_s)`: builds the pre-hardware operation description from only the non-secret parameters listed in §4. Used for **both** the interactive confirmation prompt and `--preview`.
- `_cmd_enroll` reordered: build the prospective description → if `--preview`, print it and return (never touches hardware) → check `confirmed = args.assume_yes or _prompt_confirm(description)` → if not confirmed, raise `ConfirmationDeclinedError` (message updated: no longer claims "the physical makeCredential ceremony already happened", since it now provably has not) → **only then** call `_run_enrollment_ceremony` → build evidence → `_register_with_in_process_retry`.
- `--preview` redefined: it previously ran the real ceremony *unconditionally*, with **zero** confirmation of any kind — the same root defect in a more severe form (an absent gate, not a too-late one). It now renders the identical pre-hardware description and never calls `_run_enrollment_ceremony` at all. Help text and module docstring updated to match.
- `preview_register_credential` import retained (no longer called by this script's own logic) solely because three pre-existing, out-of-scope test files (`tests/test_phase_149o_20l_7o_2l_3_...py`, `tests/test_phase_149o_20l_7o_2l_4_...py`) monkeypatch `module.preview_register_credential` as part of their own fixture setup; removing the import would `AttributeError` those unrelated, frozen suites. Not a functional no-op left by oversight — deliberately kept for backward test-surface compatibility.
- Nothing else changed: `_cmd_revoke`, `_register_with_in_process_retry`, `_run_enrollment_ceremony`, `_evidence_from_enrolled_credential`, `_report_result`, `_describe_preview`, `_prompt_confirm`, all revoke-path argparse wiring — byte-identical to the pre-repair checkpoint (confirmed by `test_revoke_subcommand_source_unchanged_by_this_repair`, exact-substring extraction + equality).

No reimplementation of CTAP, credential parsing, record validation, identity derivation, JSON persistence, locking, or idempotency/revocation semantics — the thin-wrapper shape (argument parsing → authority/confirmation → provider orchestration → existing core writer → deterministic output) is preserved exactly.

## 7. Exact Post-Repair Event Ordering

Instrumented against **current** source (`tests/test_phase_149o_20l_7o_2n_1_...py::test_post_repair_confirmation_checked_before_provider_enrollment`):

```
EVENT ORDER: ['CONFIRMATION_CHECKED', 'PROVIDER_ENROLLMENT_CALLED']
```

confirmation strictly precedes the provider call — the exact inversion of §3's pre-repair order.

## 8. Declined-Confirmation Zero-Effect Proof

`test_post_repair_declined_confirmation_zero_provider_zero_writer` and `tests/test_hatp_hardware_credential_admin_script.py::test_declined_confirmation_zero_provider_and_writer_calls`: with confirmation declined, `_run_enrollment_ceremony` is never called (event list = `['CONFIRMATION_CHECKED']` only), `register_credential` is never called (0 write attempts recorded), exit code 1, and `HATPHardwareCredentialStore(...).lookup_credential(...)` returns `None`. `--preview` mode independently proven never to call the provider seam either (`test_preview_mode_never_touches_hardware_or_writes` / `test_preview_mode_never_calls_provider`, both asserting on a ceremony stub that raises `AssertionError` if invoked at all).

## 9. Successful Synthetic Enrollment Sequence

`test_successful_enrollment_full_sequence`:

```
EVENT ORDER: ['CONFIRMATION_CHECKED', 'PROVIDER_ENROLLMENT', 'REGISTER_CREDENTIAL']
```

Matches §13 of the governing prompt exactly: authority/election prerequisite → governance confirmation accepted → provider enrollment invoked exactly once → provider-derived evidence → `register_credential` → result.

## 10. One-Hardware-Ceremony Invariant (Preserved)

`test_persistence_retry_never_calls_provider_a_second_time` (flaky first write, succeeds on retry): `_run_enrollment_ceremony` called exactly once; `register_credential` called twice against the identical (`is`-identical) evidence object. Matches the 2L.3/2L.4-verified behavior; not repaired or altered by this phase, only reconfirmed post-reorder.

## 11. Provider Failure After Confirmation (No Authority Problem)

`tests/test_hatp_hardware_credential_admin_script.py::test_provider_init_failure_after_confirmation_leaves_no_record`: confirmation succeeds (`--assume-yes`), then `_run_enrollment_ceremony` raises `HATPProviderDeviceError` before producing any evidence. Result: exit code 1, `HATPProviderDeviceError` in stderr, no `HardwareCredentialRecord` created. Confirmation succeeding does not imply hardware succeeded.

## 12. User-Presence / Timeout Failure After Confirmation

`tests/test_hatp_hardware_credential_admin_script.py::test_user_presence_timeout_after_confirmation_fails_closed`: confirmation accepted via prompt, ceremony then raises a simulated presence-timeout `HATPProviderDeviceError`. Result: exit code 1, no record created — operation fails closed. A governance authorization does not imply credential creation succeeded.

## 13. Persistence-Retry Non-Regression / No Public Recover-Import Surface

`_register_with_in_process_retry` itself is byte-unchanged (only its caller's position in `_cmd_enroll` moved). §10's test plus the pre-existing `tests/test_hatp_hardware_credential_admin_script.py::test_enroll_persistence_transient_failure_then_retry_succeeds`/`test_enroll_persists_via_idempotent_retry_when_first_write_actually_landed`/`test_enroll_exhausts_retries_and_fails_closed_with_no_import_path` all still pass unmodified. No `recover`/import/restore subcommand exists (`test_recover_subcommand_no_longer_exists`, unchanged, still passes).

## 14. No Caller-Supplied Credential Identity Introduced

`test_no_caller_supplied_credential_identity_flag_exists`: `enroll`'s argparse actions contain none of `{credential_id, public_key, public_key_hex, signer_key_id}`. `_describe_prospective_enrollment` takes no identity parameter of any kind — confirmed by direct inspection of its signature and by the fact it is called before any evidence object exists.

## 15. `--assume-yes` / Protected Admin Authority Analysis

`--assume-yes` still means exactly what it meant before this repair and what `scripts/hatp_principal_signer_admin.py`'s own `--assume-yes` means (identical `args.assume_yes or _prompt_confirm(description)` pattern, confirmed by direct source comparison): it substitutes for the interactive terminal prompt only. It does **not** substitute for the real security boundary (HHCE-REQ-020: OS filesystem write permission on the hardware-credential-store root — the same principal running `--assume-yes` must already hold that permission or every write fails closed regardless of the flag). `test_assume_yes_still_checked_before_provider_enrollment_call` confirms the flag still gates hardware access at the identical pre-ceremony position as the interactive path (an assertion-raising `_prompt_confirm` stub proves the prompt function itself is never called, while `_run_enrollment_ceremony` still only fires once, after that decision). No new Blocking finding opened: this mirrors this codebase's existing, already-accepted precedent (`hatp_deployment_binding_admin.py`, `hatp_principal_signer_admin.py`) rather than inventing a new authority model, and the repair strictly narrows — never widens — what `--assume-yes` was already capable of bypassing.

## 16. FIDO2 Dependency Declaration Analysis (Analysis Only, No Install)

`fido2>=1.1,<2` (with `cryptography>=42,<45`) **is already correctly declared** in `pyproject.toml` under `[project.optional-dependencies] hatp-hardware` — not undeclared, not a packaging defect. This matches the script's own module docstring claim ("optional `pcae-harness[hatp-hardware]` extra"). The gap 2N found (package absent from hac-dell's *deployed* venv) is a deployment/provisioning-step gap, not a packaging-declaration gap — nothing in `pyproject.toml` needs to change. Confirmed by direct read of `pyproject.toml` lines 22-39; no install performed anywhere, including locally.

## 17. HMIC Digest Consequence

`scripts/hatp_hardware_credential_admin.py` is one of HMIC v1.7's 38 frozen `implementation_scope_digest` members (`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`, added at v1.7 by Phase 149O.20L.7O.2M). Changing its bytes therefore changes its own per-file SHA-256 contribution to `derive_implementation_scope_digest` (HMIC-REQ-057/058's two-level construction: hash each file's bytes, then hash the ordered, delimited record list — any single per-file digest change propagates to the overall digest). Confirmed directly:

```
pre-repair per-file sha256:  (from cbcbcc0c blob)
post-repair per-file sha256: (from working tree)
-- differ (test_repaired_script_per_file_digest_changes_from_pre_repair_checkpoint)
```

and, concretely, against the real production digest function on this Mac development checkout: `tests/test_phase_149o_20l_7o_2m_2_...py::TestLocalHMICReconstruction::test_local_digest_matches_recorded_digest` now fails — `derive_implementation_scope_digest` on the current working tree (`abfbffca...`) no longer equals the certified/recorded digest (`3b076a63...`). **This is the expected, disclosed consequence of this repair, not a regression to fix.** Fixing it (re-certifying) is explicitly out of scope (§24/NO-GO: "Do not edit HMIC in 2N.1").

## 18. HMIC Contract-Version Consequence (Determined, Not Implemented)

Per §25 of the governing prompt: expected **no** HMIC-001 contract-version bump. The 38-member frozen *membership* is unchanged (this script was already a bound member since v1.7/2M); only an already-bound member's *bytes* changed. HMIC-001's version history (v1.5→v1.6→v1.7 in this repo's own precedent) bumps on membership/scope/semantic changes to the frozen-file *set* or the contract's own normative text (e.g. 2M's v1.6→v1.7 added two new members to the set), never on an already-admitted member's content drifting — that is precisely what `implementation_scope_digest`/re-certification exists to detect and re-bind without touching the contract. Not implemented in this phase (forbidden by NO-GO).

## 19. Current Dell Certification Interpretation

hac-dell's deployed source and its active v1.7/38 `CertificationRecord` (`de110d41...`, confirmed VALID by 2N's own fresh SSH inspection) are **entirely unaffected** by this phase — this phase made zero changes to any file under `/opt/pcae/runtime/src` (no Dell connection, §22/§23). Dell's certification remains internally valid for the deployed identity it actually certifies. It does **not** cover this repaired script's new bytes — that parity gap is inherent and expected (§24) until a future governed redeployment + fresh `CertificationRecord` binds the repaired Mac development source, per the future deployment sequence in §26 of the governing prompt (not frozen or authorized here).

## 20. Focused Tests

- `tests/test_phase_149o_20l_7o_2n_1_fido2_enrollment_pre_hardware_governance_confirmation_ordering_narrow_repair.py` — 19 new tests: pre-repair checkpoint reproduction; post-repair ordering (success + declined); preview hardware-free proof; 9-file byte-identity parametrize + explicit script-divergence + per-file digest-divergence proof; full successful sequence; one-ceremony/retry non-regression; no-caller-identity; revoke-source-unchanged.
- `tests/test_hatp_hardware_credential_admin_script.py` — updated (removed dead `preview_register_credential` fixture patch; `--preview` test rewritten for hardware-free semantics; added declined/assume-yes/provider-failure/user-presence ordering tests) — 33/33 passing.
- `tests/test_phase_149o_20l_7o_2n_post_hmic_trust_enrollment_dag_and_fido2_authorization.py` — the one test that structurally asserted the *pre-repair* (defective) ordering as expected (`test_confirmation_prompt_gates_only_registry_write_not_hardware_touch`) rewritten to assert the repaired ordering, renamed `test_confirmation_prompt_gates_registry_write_and_hardware_touch`.
- `tests/test_phase_149o_20l_7o_2m_1_hmic_v1_7_independent_verification.py` — `scripts/hatp_hardware_credential_admin.py` removed from the byte-identity-across-2M parametrize list (with an explanatory comment), since this phase's own repair intentionally changes it; the other 7 files in that list remain checked unchanged.
- `tests/test_phase_149o_20l_7o_2l_3_...py`, `tests/test_phase_149o_20l_7o_2l_4_...py` — unmodified; all pass except one pre-existing, unrelated failure (`test_recover_rejected_by_argparse_returncode_nonzero`) confirmed to fail identically on the unmodified pre-repair checkpoint (`ModuleNotFoundError: No module named 'pcae'` in a `sys.executable` subprocess that doesn't inherit this repo's venv — an environment artifact, not a code defect, and not attributable to this phase).

## 21. Fast Green — Raw vs. Attributable

Raw `python -m pytest -m fast_green -n auto` on the **unmodified pre-repair checkpoint** (`cbcbcc0c`, clean working tree, `git stash`-verified): **671 failed / 8272 passed / 4 skipped / 9 errors**. This diverges sharply from 2N's own recorded baseline five commits earlier (335 failed / 8592 passed / 9 errors) — a pre-existing environmental discrepancy in this sandbox unrelated to any change in this phase (reproduced identically on the untouched checkpoint) and out of this narrow repair's scope to diagnose.

Raw on **this phase's working tree**: 682-683 failed / 8283 passed / 4 skipped / 9 errors (a handful of node-count jitter observed between runs, unrelated to this phase's own new/changed tests, which are stable).

Diffing the two failure-node sets (`comm -13` on sorted `FAILED ...` lines) before committing isolated 11 attributable new failures: 10 were historical phases' own `test_no_scripts_files_dirty_in_working_tree` / `test_git_status_touches_no_src_pcae_...`-style self-checks (assert live `git status --porcelain` is empty, unconditionally, regardless of which phase is running) that fail only while this repair sits uncommitted in the working tree, plus the 1 disclosed HMIC digest-mismatch consequence (§17).

Re-run after this phase's implementation commit landed (working tree clean under `scripts/`/`src/pcae`): all 10 dirty-tree self-checks cleared as predicted. Exactly **2** attributable failures remain:

- **1** is the disclosed, expected HMIC digest-mismatch consequence documented in §17 (`test_local_digest_matches_recorded_digest`).
- **1** is `tests/test_phase_149o_20l_7n_1_...py::TestCandidateCurrentness::test_head_equals_origin_main`, which fails only because this phase's own commit is not yet pushed to `origin/main` at the moment of this test run — an ordinary, expected, self-resolving artifact of the governed commit-then-push lifecycle, not a code regression.

Zero unexplained attributable regressions. This phase's own 19 new tests plus its 3 modified test files' full suites are independently green (§20).

## 22. Proof: No Real Hardware, No Dell Connection, Runtime Unchanged

Every test in this phase uses `EnrolledFido2Credential`/monkeypatched `_run_enrollment_ceremony` stubs against `tmp_path`-rooted stores — never `HATPHardwareCredentialStore.production()`. No test imports or exercises `fido2.hid`/`Ctap2`/any real transport. No `lsusb`, no `ssh`, no `hac-dell` hostname appears anywhere in this phase's diff. `pcae runtime inspect` unchanged (`Observed`/`execution_unavailable`). No `pip install`/`uv pip install`/`pyproject.toml` edit performed.

## 23. Finding Status

**B-149O.20L.7O.2N-1 — REPAIRED — INDEPENDENT VERIFICATION PENDING.** Not self-closed.

## 24. Governance

- `pcae health`: healthy.
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings — pre-existing historical `tasks/DONE.md` sync debt (dozens of pre-2N `tasks/done/` entries not listed), unrelated to this phase.
- `pcae push check`: `not_ready` pending this phase's own bookkeeping commit (working tree dirty with report/status/task files at the time of the mid-phase check); resolves once this phase's remaining files are committed.
- `pcae runtime inspect`: `Observed` / `execution_unavailable` — unchanged.
- Telegram notification sent via `pcae notify status`.

## 25. Commits / Push

Phase-owned commits (this phase only):

1. `9e598106` — implementation: `scripts/hatp_hardware_credential_admin.py` + 4 test files (repair, ordering tests, dependent-suite updates).
2. (bookkeeping commit — report/status/task lifecycle files; hash recorded in `.pcae/phase-completion-metadata.json`)

Pushed: yes (recorded at finalization). `origin/main..HEAD`: 0 after push.

## 26. Recommended Next Phase

**149O.20L.7O.2N.2 — FIDO2 Enrollment Pre-Hardware Governance Confirmation Ordering Repair Independent Verification.** Do not provision the Dell `fido2` dependency or attach/use real hardware as a governed PCAE enrollment prerequisite until that verification closes B-149O.20L.7O.2N-1.
