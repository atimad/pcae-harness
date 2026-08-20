# Phase 149O.20L.7O.2L.4 — HATP Hardware-Credential Admin Recovery Authority Repair Independent Verification

Independent verification of the narrow repair implemented by Phase 149O.20L.7O.2L.3. **VERIFICATION ONLY. No real hardware, no hac-dell, no real protected-state write, no HMIC/contract change, no Principal/Signer/DeploymentBinding creation, no HATP activation.**

## 1. Finding State Entering This Phase

Prior independent verdict (149O.20L.7O.2L.2, commit `ab12406e`): **NOT VERIFIED** — Blocking finding **HARDWARE-ENROLLMENT RECOVERY AUTHORITY DEFECT**. Repaired by 149O.20L.7O.2L.3 (commit `b010cdff`), entering this phase as **REPAIRED — INDEPENDENT VERIFICATION PENDING**, not self-closed.

## 2. Fixed Historical Checkpoints

- **True phase-entry commit**: `f72113a0` ("Phase 149O.20L.7O.2L.3: task lifecycle sync (close task, open idle placeholder)"). Working tree clean, `origin/main..HEAD` = 0 at entry.
- **(A) Vulnerable checkpoint (post-2L.1 / pre-2L.3)**: `2396055f` ("Phase 149O.20L.7O.2L.2: task lifecycle sync (close task, open idle placeholder)") — confirmed by `git diff 2396055f b010cdff --stat`, identical to `git show b010cdff --stat`'s own file list, i.e. `2396055f` is exactly the tree state immediately before 2L.3's repair commit.
- **(B) Repaired checkpoint**: current HEAD `f72113a0` (identical source to `b010cdff` for all files this verification concerns).
- Isolated `git worktree add` checkpoints were created at both commits, used for direct source inspection and fast_green A/B comparison, then removed (`git worktree remove --force`) after use — no stash-only reliance.

## 3. Primary-Source Re-Derivation (Independent)

Read directly this phase, not trusted from 2L.3's summary: `docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md` (HHCE-001 v1.1, full text); `docs/PHASE_149O_20L_7O_2L_POST_HMIC_ACTIVATION_TRUST_ENROLLMENT_DAG_RE_DERIVATION_AND_ADMINISTRATIVE_ENTRY_POINT_ARCHITECTURE.md`; current `scripts/hatp_hardware_credential_admin.py` (full file, 310 lines); `src/pcae/core/hatp_hardware_credential_admin.py` (full file, 649 lines); `src/pcae/core/hatp_fido2_provider.py` (`EnrolledFido2Credential`, `enroll_credential`, `credential_identity`); `src/pcae/core/hatp_hardware_credentials.py`.

Independently determined:
- **HHCE-REQ-015** names exactly `register_credential`/`revoke_credential` (+ preview variants) — no third operation. No recover/import/restore/register-from-fields exists anywhere normatively in HHCE-001.
- **HHCE-REQ-016**: `register_credential` is idempotent via `_candidate_equal` (compares `provider_profile`/`protocol_name`/`algorithm`/`public_key`) — an identical-evidence retry is always safe (no-op if landed, genuine write if not).
- **HHCE-REQ-017**: differing evidence for an existing `signer_key_id`, or an existing revoked record, fails closed (`CredentialConflictError`) — never overwrites, never reactivates.
- The real security boundary (HHCE-REQ-019/020) is **OS filesystem write permission plus the standalone script's own public CLI surface**, never an in-process provenance check inside the core writer — confirmed directly: `register_credential()` itself has no code that inspects *how* its `evidence` argument was constructed. This means the historical defect necessarily lived entirely in the vulnerable script's CLI (its `recover` subcommand), not in the core module — independently reproduced in §8 below.
- No normative requirement anywhere in HHCE-001 authorizes an external recovery/import/manual-registration operation. The architecture-freeze document's own §6 states the retry model (physical ceremony → provider evidence → bounded in-process retry) is sufficient, requiring "no additional recovery state machine."

## 4. Contract Surface Confirmation

Independently confirmed: HHCE-001 names exactly two mutating operations, `register_credential`/`revoke_credential`. No requirement text supports recover/import/restore/register-from-fields/manual registration. The repaired public script exposes none of these — confirmed mechanically in §5-§7.

## 5. Current Public CLI Reconstruction

Direct argparse inspection (`scripts/hatp_hardware_credential_admin.py::_build_parser`):

- Subcommands: exactly `{enroll, revoke}` (`sub.choices` == this set, asserted).
- `enroll` arguments: `--repository-root`, `--enrollment-reference` (required), `--presence-timeout-s`, `--assume-yes`, `--preview`. No `--signer-key-id`/`--public-key-hex`/`--provider-profile`/`--protocol-name`/`--algorithm` flag exists on `enroll`.
- `revoke` arguments: `--repository-root`, `--signer-key-id` (required — identifies an *existing* record for revocation, never creates new identity material), `--enrollment-reference` (required), `--assume-yes`, `--preview`.
- No hidden dispatch path: `main()`'s branch is exactly `if args.ceremony == "enroll": ... else: return _cmd_revoke(args)` — no third branch, no undocumented option.

## 6. Recover Removal Proof

- `_cmd_recover` does not exist in the current script (mechanical string search — zero occurrences outside historical docstring prose explaining *why* the finding was repaired).
- `argparse` `--help` output never mentions `recover` (subprocess-invoked, asserted).
- `python scripts/hatp_hardware_credential_admin.py recover ...` fails at argument parsing with a nonzero return code and `"invalid choice"` in stderr/stdout — rejection occurs **before** any provider call, writer call, or protected-state mutation is possible (argparse itself raises `SystemExit(2)` inside `parse_args`, prior to any `main()` dispatch logic executing).
- `sub.choices` (the live parser object, not string search) confirms `"recover"` is absent as a registered subparser name.

## 7. Generic Import-Surface Search

Searched the entire script (not just the literal word "recover") for: `import`, `restore`, `register`, `manual`, `evidence`, `credential-id`, `public-key`, `signer-key-id`, `from-json`, `from-file`, `stdin`. Findings:
- `--from-json`, `--from-file`, `--restore`, `--import` — absent as CLI flags.
- `sys.stdin` — absent.
- `--public-key-hex`, `--provider-profile`, `--protocol-name`, `--algorithm` — absent as CLI flags anywhere in the script (present only as documentation-string tokens describing the removed `recover` surface's history, and as `CredentialEnrollmentEvidence` dataclass field names in the imported core module, never as script-level argparse arguments).
- `--signer-key-id` exists **only** under `revoke`, confirmed attached to no other subparser (`enroll_dests` does not contain `signer_key_id`).
- The single `CredentialEnrollmentEvidence(...)` construction site in the script is inside `_evidence_from_enrolled_credential`, whose only parameters are `enrolled` (provider output) and `enrollment_reference` — no `args.signer_key_id`/`args.public_key_hex` in the 400 characters preceding that construction call.
- **No CLI combination can create a `HardwareCredentialRecord` from caller-controlled identity.** Confirmed.

## 8. Fabricated-Evidence Exploit — Historical (Vulnerable Checkpoint)

Independently reproduced the 2L.2 exploit against the frozen vulnerable source (`git show 2396055f:scripts/hatp_hardware_credential_admin.py`), not merely re-read: `_cmd_recover` builds `CredentialEnrollmentEvidence` **directly from `args.signer_key_id`/`args.provider_profile`/`args.protocol_name`/`args.algorithm`/`args.public_key_hex`** — zero call to `enroll_credential`/`_run_enrollment_ceremony` anywhere in its body — then passes that evidence straight to `register_credential`.

Concretely executed (disposable `tmp_path` store root, no real production path, no real hardware):

```
fabricated = CredentialEnrollmentEvidence(
    signer_key_id="deadbeef...ff", provider_profile="totally-fabricated-profile-no-hardware-ever-touched",
    protocol_name="FIDO2", algorithm="ES256", public_key_hex="aabbccdd",
    enrollment_reference="FABRICATED-NO-CEREMONY",
)
register_credential(repository_root=..., evidence=fabricated, _store_root=disposable_root)
→ HardwareCredentialOutcome.REGISTERED
```

`hardware-credentials.json` at the disposable root then contained the fully fabricated record as an `active`, authoritative entry. **The historical Blocking finding is independently reconfirmed to have really existed.** The exploit succeeds because the core writer, by contract design (HHCE-REQ-019/020), performs no in-process provenance check — the entire security boundary was supposed to be the script's own CLI surface, and the vulnerable script's `recover` subcommand handed that boundary to the caller.

## 9. Fabricated-Evidence Exploit — Repaired (Central Closure Test)

Applied the conceptually identical attack to the current script via subprocess invocation of `recover` with the identical fabricated field values used in §8, plus `register_credential` monkeypatched to raise `AssertionError` if reached at all:

- Return code: nonzero (argparse rejection — `"invalid choice: 'recover'"`).
- `register_credential` call count: **0** (the monkeypatch's `AssertionError` never fired — it was never called).
- No `hardware-credentials.json` written anywhere.
- **Zero record created.** The caller has no public CLI mechanism to submit fabricated credential identity for registration.

## 10. Enroll Identity Provenance

Instrumented `_cmd_enroll`/`_evidence_from_enrolled_credential` directly. Confirmed:
- `_evidence_from_enrolled_credential(enrolled, *, enrollment_reference)` — its only two parameters, verified via `inspect.signature`. `enrolled` originates exclusively from `_run_enrollment_ceremony()`'s return value, which itself calls `Fido2HardwareProvider().enroll_credential(...)` and returns its result unmodified.
- Every field of the constructed `CredentialEnrollmentEvidence` (`signer_key_id`, `algorithm`, `public_key_hex`, `provider_profile`) is read directly from the `enrolled` object's own attributes — traced with a fake enrolled-credential object carrying distinguishable sentinel values per field; all four sentinels propagated unchanged into the evidence object.
- No caller override occurs after the provider returns: `_cmd_enroll`'s only path from ceremony result to evidence is this one function call, with no intervening mutation.

## 11. Exactly One Hardware Ceremony

Using an independently-authored synthetic provider stub (`_FakeEnrolledCredential`) monkeypatched over `_run_enrollment_ceremony`, with a flaky `register_credential` that fails transiently twice then succeeds: **`_run_enrollment_ceremony` call count = exactly 1** across the whole `_cmd_enroll` invocation, while `register_credential` was called 3 times (2 failures + 1 success). No second `makeCredential`, no device re-enumeration, occurs under retry — confirmed for both the declined-confirmation path (ceremony runs once regardless, per the script's own documented design — physical ceremony already happened before confirmation is asked) and the successful-enroll path.

## 12. Retry Object/Value Identity

Instrumented `register_credential` to record every `evidence` object passed to it across 3 flaky attempts. All three references are the **identical Python object** (`is` comparison, not just field equality) — the retry loop never regenerates or mutates evidence between attempts; it is the exact same `CredentialEnrollmentEvidence` instance the one ceremony call produced.

## 13. Retry Authority Boundary

`_register_with_in_process_retry` is called from exactly one place in the module (`_cmd_enroll`), textually **after** `_run_enrollment_ceremony` in that function's source (index comparison confirmed: `_run_enrollment_ceremony` appears before `_register_with_in_process_retry` in `_cmd_enroll`'s source). No other function in the module calls the retry helper (enumerated every module-level function via `inspect`, searched each source for the call — none found). No argparse dest maps directly onto a `CredentialEnrollmentEvidence` field other than `enrollment_reference` (set intersection of `enroll` subparser dests and the dataclass's field names is `{enrollment_reference}` at most). **The retry helper cannot be invoked with arbitrary user-derived evidence; argparse/input parsing cannot construct its evidence argument.** No remaining defect identified here.

## 14. Retry Exception Classification (Load-Bearing)

`_HANDLED_ERRORS = (HATPHardwareCredentialAdminError, HATPHardwareCredentialStoreError, HATPHardwareProviderError, OSError)` — confirmed by direct tuple-equality assertion against the live module object, not narration.

Classified by direct injection of each condition into a mocked `register_credential`:

| Condition | Caught/retried? | Attempts | Disposition |
|---|---|---|---|
| (A) Transient/uncertain failure (`HardwareCredentialStoreUnavailableError` on attempts 1-2, success on 3) | Yes | up to 3 | Correct — legitimate retry target |
| (B) Already-landed/idempotent replay | Yes (via real `register_credential`, not simulated) | 1 (resolves `ALREADY_REGISTERED`) | Correct |
| (C) Deterministic record conflict (`CredentialConflictError`, every attempt) | Yes | 3 (full budget), then re-raises | **Redundant but harmless** — see §15/§38 |
| (D) Malformed existing state (`HATPHardwareCredentialStoreMalformedError`) | Yes | 3 (full budget), then re-raises | **Redundant, never heals** — see §16 |
| (E) Validation failure (`CredentialEvidenceMalformedError`) | Yes (subclass of `HATPHardwareCredentialAdminError`) | up to 3 | Same class as (C); this failure occurs before any I/O, so retries are inert |
| (F) Revoked-state rejection | Folds into (C) — `CredentialConflictError` also covers "existing revoked record" | 3 | Same disposition as (C) |
| (G) Permission/path failure (`PermissionError`, an `OSError` subclass) | Yes | 3 (full budget), then re-raises | **Fails closed, no fallback path** — see §17 |
| (H) Programming errors (`TypeError`/`AttributeError`) | **No** — not a member of `_HANDLED_ERRORS`, not a subclass of any member | 1 (propagates immediately, uncaught) | **Correct — appropriately narrow exclusion** — see §18 |
| (I) Arbitrary `Exception` | **No** — bare `Exception`/`KeyError`/`ValueError`/`RuntimeError` confirmed NOT subclasses of `_HANDLED_ERRORS` via `issubclass` | 1 | Correct |

A bounded retry is justified only where repeating identical evidence can legitimately resolve uncertainty/transience (A) or safely resolve to a no-op (B). The catch scope also retries (C)/(D)/(E)/(F)/(G) — none of which can be healed by an identical retry — but in every one of those cases the operation still **fails closed** on exhaustion (the last error is re-raised, never swallowed, never converted to a false success). The three-attempt bound is finite and does not itself constitute a security defect; it is a **retry-quality inefficiency**, adjudicated separately in §38.

## 15. Deterministic Failure Retry

Injected a permanent `CredentialConflictError` (the real record-conflict exception, HHCE-REQ-017's own error type) into `register_credential`. Measured call count: **exactly `_MAX_REGISTER_ATTEMPTS` (3)**, then the helper re-raises `CredentialConflictError` uncaught — `_cmd_enroll` propagates it to `main()`'s except-clause, prints `ERROR: CredentialConflictError: ...`, returns exit code 1.

**Disposition: NON-BLOCKING.** The retries are unnecessary (a genuine field-differing conflict cannot resolve itself by replay) but produce zero authority or safety effect: no overwrite, no reactivation, no false success, identical final fail-closed outcome to a single-attempt implementation, costing only 2 wasted in-process calls (no additional hardware interaction, no additional filesystem writes — `register_credential`'s conflict path raises before any write). Contracts do not prohibit redundant identical retries; they prohibit overwriting/reactivating a conflicting record, which does not occur.

## 16. Malformed State Retry

Injected a permanent `HATPHardwareCredentialStoreMalformedError` (the reader's own malformed-registry exception). Measured call count: **exactly 3**, then re-raised. A malformed authoritative store cannot heal through replay — confirmed the wrapper does not attempt any repair, relaxation, or alternate read path; it simply calls `register_credential` again, which re-parses the same malformed document and fails identically each time.

**Disposition: NON-BLOCKING.** Redundant (3 identical failing parse attempts instead of 1) but no repair, no relaxation of HHCE-REQ-024/025's closed-schema fail-closed discipline, no security effect.

## 17. Permission/Path Failure Retry

Injected a permanent `PermissionError` (a genuine `OSError` subclass, matching `_HANDLED_ERRORS`'s last tuple member). Measured call count: **exactly 3**, then re-raised. Source-inspected `_register_with_in_process_retry`'s body: no `chmod`, no `chown`, no "fallback"/"elsewhere" alternate-path string or logic exists anywhere in the helper. **Repeated failure remains fail closed** — no alternate write location, no privilege escalation, no silent success.

**Disposition: NON-BLOCKING.** Same redundant-but-harmless pattern as §15/§16.

## 18. Unexpected Programming Exception

Injected `AttributeError` (and separately `TypeError`) — errors distinct from every legitimate persistence/idempotency/domain-error type — into a mocked `register_credential`. **Call count: exactly 1. The exception propagates immediately, uncaught by the retry loop, on the very first attempt.** Confirmed `_HANDLED_ERRORS`'s tuple membership by direct `issubclass` checks: `Exception`, `KeyError`, `ValueError`, `AttributeError`, `RuntimeError`, `TypeError` are all confirmed **not** subclasses of any `_HANDLED_ERRORS` member.

**Disposition: CLEAN.** The catch scope is appropriately narrow here — it does not mask programmer or invariant failures. This does not reopen the original authority defect and represents good defensive design.

## 19. Never-Landed Write

Simulated: `register_credential` raises `CredentialReadbackMismatchError` (HHCE-REQ-027's own "first attempt never landed" signal) on attempt 1, succeeds on attempt 2. Result: **one provider ceremony** (unrelated to this simulation, confirmed separately in §11), **same evidence object** across both attempts (§12), **exactly one final authoritative record** (the successful attempt's own result), **correct CLI result** (`outcome=registered`), **no caller involvement in identity** (evidence unchanged from the ceremony's output throughout).

## 20. Already-Landed/Ack-Uncertain Write

Using the **real, unmocked core `register_credential`** against a disposable `tmp_path` store root (not simulated): registered a credential once (`outcome=registered`), then called `register_credential` again with the byte-identical `CredentialEnrollmentEvidence` object. Second call result: `outcome=already_registered` — `_candidate_equal`'s existing idempotency correctly recognizes the identical state. The persisted `hardware-credentials.json` contains **exactly one** record for that `signer_key_id` (no duplicate, no overwrite) after both calls. This is the exact underlying mechanism the in-process retry relies on for the "already-landed" branch of HHCE-REQ-016.

## 21. Exhausted Retries

Forced every one of the 3 permitted attempts to fail (`CredentialReadbackMismatchError`, deterministic). Verified: **finite attempts** (exactly 3, `_MAX_REGISTER_ATTEMPTS` — confirmed `< 10`, no infinite loop), **no device re-touch** (the retry helper never calls `_run_enrollment_ceremony`/`enroll_credential`, confirmed in §13), **final result is a raised exception, not a false success** (the last error is re-raised, `main()` returns exit code 1), **diagnostic text contains no replayable credential identity** — captured stderr does not contain `"recovery evidence"` (case-insensitive), `--public-key-hex`, or `--signer-key-id` — and contains no fabricated "paste these values" recovery instructions. It does contain the phrase `"governed reconciliation"`.

## 22. No External Recovery Evidence

Captured stderr on exhaustion (§21, §23): confirmed **zero occurrence** of `"RECOVERY EVIDENCE"` or any case-insensitive variant, and zero occurrence of any CLI flag name (`--public-key-hex`, `--signer-key-id`) that a human could copy into a re-invocation. The repaired script's diagnostic is purely descriptive prose naming no credential material — it does **not** recreate an implicit manual recovery/import protocol.

## 23. Failure Diagnostic

Exact diagnostic text emitted on exhaustion:

```
REGISTRY PERSISTENCE DIAGNOSTIC: the physical hardware credential was created
(signer_key_id=<hex>), but registry persistence did not complete after 3
in-process attempts using the identical provider-generated evidence (last
error: <ExceptionType>: <message>). This operation requires governed
reconciliation/retry; no manual credential import path exists.
```

This matches the expected safe shape: states that hardware-side creation may have succeeded while persistence failed, directs the operator to a separately governed reconciliation, and explicitly disclaims any manual-import path — it never instructs "paste these credential values into..." Note: `signer_key_id` (the hex identity) is printed — this is the credential's own public, non-secret identifier (not `public_key_hex`, not a private key, not a PIN), needed for an operator to know *which* credential is affected when initiating governed reconciliation; it does not by itself enable reconstructing a valid registration (that still requires the actual `public_key_hex`/`algorithm`/`provider_profile`, none of which are printed). This is a disclosed, narrow, non-blocking design choice, not a defect.

## 24. Confirmation Zero-Touch

- `enroll`, confirmation declined (`input()` returns `"no"`): provider ceremony **does** run (the physical ceremony already happened by the time confirmation is asked — this is the script's own documented, disclosed design, not a defect: declining cannot undo a completed hardware ceremony). **Writer call count: 0** — `_register_with_in_process_retry` is never invoked.
- `revoke`, confirmation declined: **writer call count: 0** — `revoke_credential` is never invoked.
- Both measured via direct call-count instrumentation (not output-text inspection).

## 25. Revoke Regression

Independently exercised the real core `revoke_credential` against a disposable store root: **valid revoke** (active → revoked, `outcome=revoked`); **idempotent replay** (`outcome=already_revoked`, `revoked_at` unchanged from the first revocation — monotonic per HHCE-REQ-011); **missing ID** fails closed with `CredentialNotFoundError`; **no deletion, no other record mutated** — registered two credentials, revoked one, confirmed the second remains `status=active` and both records still present (`len(credentials) == 2`) after the revoke. Declined confirmation on `revoke` produces zero writer calls (§24). `_cmd_revoke`/`revoke_parser` are unchanged from 2L.2's own independently-verified clean state.

## 26. Principal/Signer Non-Regression

`git diff --name-only b010cdff HEAD -- scripts/hatp_principal_signer_admin.py src/pcae/core/hatp_principal_signer_admin.py` — **empty** (byte-identical since 2L.3's own phase entry, confirmed both against the 2L.3 entry commit and independently against the pre-2L.2 vulnerable checkpoint `2396055f`). Confirmed the script's public surface string tokens `enroll-principal`/`revoke-principal`/`enroll-signer`/`revoke-signer` are all present. Full re-verification of the entire Principal/Signer subsystem was not performed (byte-identity evidence gives no reason to suspect drift); the focused existing test suite `tests/test_hatp_principal_signer_admin_script.py` was re-run for regression and passes.

## 27. Core Writer Immutability

`git diff --name-only 2396055f HEAD -- src/pcae/core/hatp_hardware_credential_admin.py src/pcae/core/hatp_fido2_provider.py src/pcae/core/hatp_hardware_credentials.py src/pcae/core/hatp_piv_provider.py src/pcae/core/hatp_providers.py src/pcae/core/hatp_principal_signer_admin.py` — **empty**. All six core writer/provider modules are byte-identical from the vulnerable checkpoint through the repaired checkpoint. 2L.3 made no semantic modification to any of them.

## 28. Contract Immutability

`git diff --name-only 2396055f HEAD -- docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md` — **empty**. HHCE-001 remains v1.1 (`**Version:** 1.1` string-confirmed present in the live file). No contract laundering occurred; 2L.3 is a pure implementation repair.

## 29. Thin-Wrapper Recheck

AST-parsed `_register_with_in_process_retry`'s body: the complete set of function calls made is `{register_credential, print, range, len, type}` — an explicit allowlist comparison confirms no call outside this set. No record comparison, no schema validation, no JSON persistence (`json.load`/`json.dump` absent from the entire script, confirmed by string search), no locking (`fcntl` absent from the entire script), no canonicalization, no duplicate-detection logic exists in the helper or anywhere else in the script. Those responsibilities remain entirely in `src/pcae/core/hatp_hardware_credential_admin.py` (unchanged, §27). The helper remains orchestration-only: call `register_credential`, catch the declared tuple, retry with the identical evidence, render/re-raise the result.

## 30. Authority Call Graph

Repaired exact hardware-enroll call graph, confirmed by direct instrumentation:

```
CLI `enroll` invocation
  → _run_enrollment_ceremony()              [exactly 1 call, §11]
      → Fido2HardwareProvider().enroll_credential()
  → _evidence_from_enrolled_credential(enrolled, enrollment_reference)  [only provider-derived fields, §10]
  → preview_register_credential(evidence)   [read-only]
  → confirmation gate (assume_yes or _prompt_confirm)  [zero-touch on decline, §24]
  → _register_with_in_process_retry(evidence)
      → register_credential(evidence)  ×1..3 [identical evidence object every call, §12]
  → _report_result(result)
```

No branch exists from CLI identity fields (`args.signer_key_id`/`args.public_key_hex`/etc.) directly into a `CredentialEnrollmentEvidence` constructor for normal production creation — the single construction site (§7) takes only provider output.

## 31. Path Containment

Re-ran negative checks against the current script: no `--trust-store`, `--output-path`, `--store-root`, or `--registry-path` override flag exists anywhere in the script (mechanical string search). No symlink/path bypass is introduced by the retry helper — it performs no filesystem I/O of its own (§29's AST call-set contains no path/file primitive). Repository-root semantics remain exactly `HATPHardwareCredentialStore.production().root`-derived, resolved entirely inside the unchanged core module (§27).

## 32. Secret Handling

Inspected all changed exception/error paths (the new retry helper and its diagnostic print, §21-§23): no PIN, private key, or authenticator-internal material is ever printed — the only identity-adjacent value emitted on exhaustion is `signer_key_id` (a public, non-secret hex identifier), and the exception's own string representation (`last_error`), which for every domain exception type in `_HANDLED_ERRORS` carries no secret material (confirmed by reading each exception class's docstring/constructor in `src/pcae/core/hatp_hardware_credential_admin.py` — none embeds key/PIN/token fields). No argparse argument named `pin`/`private_key`/`secret` exists on any subcommand (dest-set search). Removal of the vulnerable script's `_print_recovery_evidence` (which printed the full `public_key_hex` for manual re-entry) genuinely reduced credential-data exposure — the repaired script's exhaustion diagnostic prints `signer_key_id` only, never `public_key_hex`.

## 33. Historical Evidence Preservation

`tests/test_phase_149o_20l_7o_2l_2_hatp_trust_enrollment_admin_entrypoint_independent_verification.py` still exists and still contains the word "recover" in its narrative/docstrings, preserving the historical finding's description. The vulnerable implementation remains permanently, byte-exactly inspectable at commit `2396055f` (confirmed reachable via `git cat-file -e 2396055f`) and at `ab12406e` (2L.2's own verification commit, also confirmed reachable). 2L.3 did not rewrite history into "recover never existed" — the historical commits, the historical test file's narrative, and this phase's own §8 direct re-execution of the vulnerable code all independently confirm the finding's original truth remains reconstructable.

## 34. Independent HMIC-REQ-052 Application

Freshly applied HMIC-REQ-052's authority-sensitivity test to both repaired scripts (`scripts/hatp_hardware_credential_admin.py`, `scripts/hatp_principal_signer_admin.py`), independently, not trusting 2L.3's answer: **if only this script changed while every other current v1.6 frozen member remained byte-identical, could authoritative Trust-Enrollment output change?** For both scripts: **YES** — each is the sole caller deciding which `register_credential`/`revoke_credential` (respectively `enroll_signer`/`revoke_signer`/etc.) call happens, with what evidence, after what confirmation gate; a hostile or buggy change to either script could alter which `HardwareCredentialRecord`/`SignerRecord` mutation actually occurs even with the core writer modules held fixed. This is derived directly from re-reading each script's control flow this phase (§5-§13, §26), not asserted from 2L.3's own text.

## 35. Transitive Source Closure

Freshly enumerated: `hatp_mandatory_certification.py::_FROZEN_AUTHORITY_BEARING_FILES` currently contains **exactly 36** entries (`len(...) == 36`, live-object-asserted, v1.6). Confirmed neither `scripts/hatp_hardware_credential_admin.py` nor `scripts/hatp_principal_signer_admin.py` is a current member (`not in` check against the live tuple). The retry implementation introduces **no new imported helper/module** — `_register_with_in_process_retry` calls only names already present in the script's existing import set (`register_credential` from the already-bound-eligible core module; no new third-party or internal dependency). **Future delta remains exactly: + `scripts/hatp_hardware_credential_admin.py`, + `scripts/hatp_principal_signer_admin.py`, 36 → 38** — independently re-derived (`set(current) | {two new scripts}` has length 38), matching 2L.3's own claim exactly, not merely trusted from it.

## 36. Current Dell Certification Consequence

No connection to Dell was made or attempted this phase. Reasoning from the known deployment boundary: hac-dell continues running the prior deployed source generation; its active HMIC certification remains a claim about *that* deployed identity, unaffected by any Mac-development-only source change. Mac development now contains the repaired admin scripts (`recover` removed, retry helper added) outside the currently-frozen HMIC v1.6 scope (§35 — neither script is a frozen member). **This phase does not claim the Dell certification validates the repaired scripts, and does not claim the Dell certification is invalidated by this Mac-side development.** Both claims would be unsupported; the correct position is that Dell's certification and Mac's repaired-but-unbound scripts are currently independent facts about different source generations.

## 37. Original Finding Closure Test

All six required elements independently established:

1. **Public `recover` command absent** — §5, §6.
2. **No equivalent manual import path** — §7.
3. **Fabricated credential evidence cannot reach authoritative registration via public CLI** — §9 (central closure test, zero writer calls, zero record created).
4. **Normal enrollment identity derives only from actual provider output** — §10.
5. **Retry cannot be invoked as an externally supplied identity channel** — §13.
6. **No new provenance bypass replaces `recover`** — §7, §31 (no alternate override flag, no new construction site).

**All six pass. The original HARDWARE-ENROLLMENT RECOVERY AUTHORITY DEFECT finding is independently CLOSED**, not merely narrated as closed.

## 38. Retry-Quality Finding (Adjudicated Separately)

The retry loop's exception classification (§14) catches and retries several conditions that cannot be healed by identical replay: deterministic conflicts (§15), malformed on-disk state (§16), and permission/path failures (§17). In every one of these cases the loop still terminates finitely (3 attempts, never infinite), never overwrites, never reactivates, never produces a false success, and never masks the eventual failure (the last error always propagates). This wastes at most 2 redundant in-process calls per affected failure mode — no additional hardware interaction, no additional filesystem mutation beyond what a single attempt would also risk, no security-relevant semantic change.

**Retry-quality verdict: NON-BLOCKING** — `NB-2L.4-1: the bounded retry catches and redundantly retries several deterministic/non-transient failure classes (CREDENTIAL_CONFLICT, malformed-state, permission/path failure) that cannot be resolved by identical-evidence replay; this is inefficient but not unsafe, since every affected path still fails closed with an unmodified final outcome.` This is a separate, non-blocking issue from the original recover-authority defect, which is independently closed regardless of this finding (§37).

## 39. Independent Test Suite

`tests/test_phase_149o_20l_7o_2l_4_hatp_hardware_credential_admin_recovery_authority_repair_independent_verification.py` — freshly authored this phase, does not import or reuse any 2L.3 test module. **45 passed, 0 failed.** Covers: vulnerable-checkpoint exploit reproduction (§8); repaired-exploit rejection (§9); CLI grammar (§5); no recover alias (§6); no manual identity fields (§7); normal provider-derived evidence (§10); one hardware ceremony (§11); same-evidence retries (§12); retry exception classification for all nine catch-scope categories (§14, §18); deterministic conflict behavior (§15); malformed-state behavior (§16); never-landed write (§19); already-landed/uncertain result (§20); exhausted retry (§21); no recovery-evidence output (§22); confirmation zero-touch (§24); revoke (§25); Principal/Signer non-regression (§26); core/contract immutability (§27, §28); HMIC-REQ-052 (§34); transitive closure (§35).

## 40. Fixed/Current A/B Regression

Isolated `git worktree add` checkpoints at `2396055f` (vulnerable) and `f72113a0`/current HEAD (repaired) — not stash-only. Full `python -m pytest -m fast_green -n auto -q` run on each. Exact FAILED/ERROR node-ID sets diffed (`comm -23`/`comm -13`):

- **Candidate-only** (present in repaired, absent in vulnerable): `tests/test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli` (1 node).
- **Vulnerable-only** (present in vulnerable, absent in repaired): `tests/test_phase_149o_20l_7n_1_dell_redeployment_proposition_independent_verification.py::TestCandidateCurrentness::test_head_equals_origin_main`, `tests/test_shell_gate.py::TestAuditPersistence::test_verify_detects_tampered_record` (2 nodes).

Investigated every node individually:
- `test_head_equals_origin_main` asserts `git rev-parse HEAD == git rev-parse origin/main` — necessarily fails in any detached-HEAD worktree checkout at a historical commit; this is a checkpoint-comparison artifact, not a code regression (the repaired tree, run from the real `main` branch tip, passes it).
- `test_audit_verify_cli` and `test_verify_detects_tampered_record` are both members of the same `TestAuditPersistence` class; re-run in isolation (`pytest tests/test_shell_gate.py::TestAuditPersistence -v`, no `-n auto`), **all 7 tests in that class pass**, confirming both are `-n auto`-parallel-execution flakes unrelated to any file this phase or 2L.3 touched (`test_shell_gate.py` shares no import with `hatp_hardware_credential_admin`).

**Zero attributable regressions.**

## 41. Fast Green — Raw Result

`python -m pytest -m fast_green -n auto -q` against the current (repaired) tree: **333 failed, 8498 passed, 4 skipped, 105 warnings, 9 errors** (191.24s). Against the vulnerable checkpoint worktree: 334 failed, 8471 passed, 4 skipped, 105 warnings, 9 errors (203.36s). Both runs carry the same large pre-existing historical-baseline debt documented across many prior phases in this repository (contract/source byte-identity assertions in old phase test files that drift as the repository legitimately evolves past their own phase-entry snapshots — not attributable to this phase). The one-node net difference (333 vs 334 raw failed) is fully explained by §40's node-level diff (one candidate-only xdist flake, one vulnerable-only flake, one vulnerable-only checkpoint-drift artifact — net effect on the raw count is incidental to which specific parallel worker picked up which flaky test that run, not a real behavioral difference). Raw numbers are reported here honestly and are not converted to "0 failed" shorthand; **attributable regressions are separately and explicitly zero (§40)**.

## 42. No Real Effect

No connection to hac-dell was made or attempted. No FIDO2/PIV device enumeration was performed (every provider/ceremony interaction in this phase's own tests is a synthetic monkeypatched or fake object, never `CtapHidDevice.list_devices()` or any real CTAP2 call). No real protected writer path was exercised — every `register_credential`/`revoke_credential` call in this phase's tests passes an explicit disposable `tmp_path`-derived `_store_root=`, never `HATPHardwareCredentialStore.production().root`. All state used by this phase's own tests lives under pytest `tmp_path` roots, deleted automatically after each test.

## 43. Finding Disposition

**HARDWARE-ENROLLMENT RECOVERY AUTHORITY DEFECT → INDEPENDENTLY CONFIRMED CLOSED AT THE TRUST-ENROLLMENT STANDALONE ADMIN ENTRY-POINT BOUNDARY** (`scripts/hatp_hardware_credential_admin.py`'s public CLI surface, exactly). This closure is scoped precisely to that boundary — it does not claim broader HATP readiness closure, does not claim HMIC recertification, does not claim Dell-side validation of the repaired scripts (§36), and does not claim the separate retry-quality issue (§38, Non-Blocking) is resolved (it is a distinct, non-blocking issue, not part of this finding).

## 44. Overall Implementation Verdict

2L.2's overall verdict was NOT VERIFIED solely because of the recover defect (no other Blocking finding was raised against hardware enroll/revoke, Principal/Signer's four operations, or the repaired-recovery behavior). This phase closes that sole defect (§37) and identifies exactly one new issue, itself Non-Blocking (§38, retry-quality). Combined coverage this phase: hardware `enroll`/`revoke` (§5-§25, §29-§32), Principal/Signer's four operations at the non-regression level (§26), repaired recovery behavior at the standalone admin-entrypoint implementation boundary (§8-§23, §37).

**Overall verdict: VERIFIED WITH NON-BLOCKING FINDINGS** — original defect closed, one new Non-Blocking retry-quality finding (NB-2L.4-1) recorded, no new Blocking finding.

## 45. HMIC Progression Gate

Because the implementation is independently verified with no Blocking finding, the project may proceed to the narrow HMIC source-scope evolution phase. Expected candidate future target, independently re-derived (§35), not merely quoted from 2L.3: **HMIC v1.7, source-bearing-file count 36 → 38**, binding exactly `scripts/hatp_hardware_credential_admin.py` and `scripts/hatp_principal_signer_admin.py`. No HMIC edit was performed in this phase.

## 46. Verdict

**B: VERIFIED WITH NON-BLOCKING FINDINGS — ORIGINAL DEFECT CLOSED — HMIC SCOPE EVOLUTION MAY PROCEED.**

(Not A, because NB-2L.4-1, the retry-quality finding, remains outstanding, even though it does not block progression.)

## 47. Governance

Governed PCAE lifecycle only — no raw git commit/push, no `--no-verify`, no force push, no hook/lifecycle bypass. `pcae health` healthy; `pcae check` passed; `pcae status coherence` coherent; `pcae doctor task-memory` — see `.pcae/phase-completion-report.md` for literal output; `pcae push check` clean; `pcae runtime inspect` — runtime unchanged throughout (no runtime activation performed); Telegram notification sent via `pcae notify status` after `source ~/.config/pcae/telegram.env`. Phase-owned commit(s): identified exactly in `.pcae/phase-completion-metadata.json::phase_commits`.

## 48. No-Go Confirmations (Negative Findings, This Phase)

See `.pcae/phase-completion-metadata.json::no_go_confirmation` for the full literal list (11+ items).

## 49. Recommended Next Phase

**149O.20L.7O.2L.5 (or equivalent next-numbered phase) — HMIC v1.7 Narrow Source-Scope Evolution**, binding exactly the two verified admin scripts (`scripts/hatp_hardware_credential_admin.py`, `scripts/hatp_principal_signer_admin.py`), widening `_FROZEN_AUTHORITY_BEARING_FILES` 36 → 38 per §35/§45. Do not redeploy or touch real hardware in that phase. The retry-quality Non-Blocking finding (NB-2L.4-1, §38) may optionally be repaired narrowly in a follow-on phase (tightening `_HANDLED_ERRORS`'s catch scope to exclude conditions that cannot be healed by identical-evidence replay) but does not block HMIC progression.
