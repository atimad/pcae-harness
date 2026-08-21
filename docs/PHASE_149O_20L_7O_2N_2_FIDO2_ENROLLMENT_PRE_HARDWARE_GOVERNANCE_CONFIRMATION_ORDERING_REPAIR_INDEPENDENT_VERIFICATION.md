# Phase 149O.20L.7O.2N.2 — FIDO2 Enrollment Pre-Hardware Governance Confirmation Ordering Repair Independent Verification

**Verdict: A — INDEPENDENTLY VERIFIED — B-149O.20L.7O.2N-1 CLOSED — REPAIRED HARDWARE ADMIN ENTRYPOINT READY FOR HMIC/DEPLOYMENT PROGRESSION.**

Verification-only phase. No production implementation modified. No real
FIDO2/PIV hardware touched. No Dell connection. No `fido2` package
installed. No `HardwareCredentialRecord`/`Principal`/`Signer`/
`DeploymentBinding` created. No HMIC membership/certification/deployment
change. No Protected Root mutation.

## 1. Phase entry commit

`e422c643be346da826fb8f1b71a56b1412390f0a` (working tree clean at entry).

## 2. Fixed vulnerable checkpoint

Independently re-derived, not trusted from 2N.1's own report:
`9e5981067fc5ba16638a5fe066d66ebcb4e68489^` resolves to `cbcbcc0c`,
matching 2N.1's claim (`git rev-parse` and `git log` cross-checked).

## 3. Vulnerable event sequence (source-level)

`git show cbcbcc0c:scripts/hatp_hardware_credential_admin.py` shows
`_cmd_enroll` calling `_run_enrollment_ceremony(...)` as its **first**
statement, unconditionally, before `args.preview` is even checked and
before `_prompt_confirm`/`--assume-yes` is evaluated. Confirmed
mechanically by `tests/test_phase_149o_20l_7o_2n_2_fido2_ordering_
independent_verification.py::test_vulnerable_checkpoint_ran_ceremony_
before_confirmation`, which parses the vulnerable-checkpoint source
directly from git history and asserts the token offset of
`_run_enrollment_ceremony` precedes `_prompt_confirm`/`confirmed =`.

## 4. Repaired event sequence (current HEAD)

`_cmd_enroll` now: builds `_describe_prospective_enrollment(...)`
(non-secret) → returns early if `--preview` → checks confirmation
(`args.assume_yes or _prompt_confirm(description)`) → raises
`ConfirmationDeclinedError` with zero further calls if declined → only
then calls `_run_enrollment_ceremony` → derives evidence → calls
`_register_with_in_process_retry`. Independently instrumented with a
fresh synthetic provider/confirm/register seam (this phase's own test
module, not 2N.1's fixtures):
`test_successful_enroll_confirms_before_provider_before_writer` records
the literal event list `['confirmation_checked', 'provider_ceremony',
'register_credential']` — confirmation strictly precedes the hardware
ceremony, which strictly precedes the registry write.

## 5. Primary contract ordering (HHCE-001 v1.1)

HHCE-001 v1.1 §2 explicitly places "human decision workflows, election,
or CHGR mechanics" out of its own scope, deferring to HBDC-REQ-064's
model — it does not itself state a hardware-ordering rule in so many
words. The operative precedent is architectural, established by the one
existing writer precedent HHCE-001 §"Architecture basis" names directly:
`scripts/hatp_deployment_binding_admin.py`'s `preview → confirm → write`
sequencing (verified directly: every subcommand there computes a preview,
optionally prints-and-returns for `--preview`, else calls
`_prompt_confirm`/`--assume-yes` before ever calling its write function).
The hardware case cannot reuse that pattern verbatim, because a truthful
`HardwareCredentialPreview` requires provider-derived evidence that does
not exist before a real ceremony runs — which was precisely the
vulnerable checkpoint's design (`preview_register_credential` was
computed from a ceremony that had already run). The repair's resolution —
a prospective, non-committing description in place of the full preview,
with the real ceremony strictly gated behind confirmation — is the
narrowest change that preserves the "no committing effect before
confirmation" invariant this precedent embodies. **Classification: the
contract does not explicitly mandate this ordering in named requirement
text; the ordering requirement is established by direct architectural
precedent (`hatp_deployment_binding_admin.py`) that HHCE-001 itself names
as its own basis, not by ambiguity requiring a contract amendment.**

## 6. Prospective description fields

`_describe_prospective_enrollment(repository_root, enrollment_reference,
presence_timeout_s)` emits exactly: `repository_root`,
`enrollment_reference`, `provider_profile` (`HATP_HARDWARE_PROVIDER_V1`,
a fixed constant), the literal operation name, a fixed policy string, and
`presence_timeout_s`. All six are knowable before any ceremony runs.
Verified by `test_prospective_description_contains_no_fabricated_
identity`: the string never contains `credential_id`, `signer_key_id`,
or `public_key`.

## 7. No pre-hardware identity fabrication

Confirmed by the same test above and by direct source read: no code path
prints or confirms a prospective `signer_key_id`/`public_key` before a
real ceremony produces one.

## 8. Declined confirmation — zero provider effect

`test_declined_confirmation_zero_provider_zero_writer_calls`: with
confirmation declined, `events == ['confirmation_checked']` only — zero
`provider_ceremony`, zero `register_credential` calls, exit code 1.

## 9. Declined confirmation — hardware-touch semantics

`_run_enrollment_ceremony` lazily imports `Fido2HardwareProvider` and
calls `provider.enroll_credential(...)` — nothing constructs the provider
object at all until after confirmation passes, since the import itself is
inside the function body executed only at that call site. Pre-confirmation,
zero provider construction of any kind occurs (not merely zero mutation).

## 10. Success event order

See §4: `confirmation_checked → provider_ceremony → register_credential`,
independently instrumented, matches the required conceptual order
exactly (no provider ceremony precedes confirmation).

## 11. Exactly one hardware ceremony under retry

`test_persistence_retry_reuses_identical_evidence_one_ceremony_only`:
forces `register_credential` to fail transiently twice then succeed;
`events.count('provider_ceremony') == 1` while
`attempts['n'] == 3` — the retry loop (`_register_with_in_process_retry`,
byte-identical to pre-2N.1) never re-invokes the ceremony.

## 12. Retry evidence identity

Same test: the final persisted record's `signer_key_id` equals the
single ceremony's `credential_id_hex` — the identical
`CredentialEnrollmentEvidence` object is reused across all three write
attempts; no caller reconstruction, no second provider call.

## 13. NB-2L.4-1 non-interference

`git diff cbcbcc0c HEAD -- scripts/hatp_hardware_credential_admin.py`
shows `_HANDLED_ERRORS` and `_register_with_in_process_retry`'s body are
byte-identical before and after 2N.1's repair — the retry-quality
Non-Blocking finding (broad `_HANDLED_ERRORS` catching some deterministic
failures unnecessarily) is untouched, not repaired, not regressed.
Independently reconfirmed behaviorally by §11/§12's retry test, which
exercises this exact code path.

## 14. Preview public surface — hardware-free

`test_preview_never_touches_provider_or_writer`: with `--preview`,
`events == []` (zero provider ceremony, zero confirmation prompt call —
`_prompt_confirm` is monkeypatched to raise if called at all, and does
not fire), exit code 0.

## 15. Preview description truthfulness

Same test asserts the printed preview text contains `"has NOT run yet"`
and none of `signer_key_id`, `public_key`, or the synthetic credential
ID/pubkey values — it describes only the prospective operation, never a
fabricated result.

## 16. Preview ≠ authorization

`--preview` returns immediately after printing, before the confirmation
check is ever reached (§4/§14) — it cannot itself establish `confirmed =
True` for any subsequent invocation; each CLI invocation is a fresh
process with no persisted preview-to-authorization binding of any kind.

## 17. `--assume-yes` independent authority analysis

Read directly: `--assume-yes` sets `args.assume_yes`; `_cmd_enroll`
evaluates `confirmed = args.assume_yes or _prompt_confirm(description)` —
it is a pure substitute for the interactive prompt, evaluated at the
identical ordering position an interactive `yes` response would occupy.
It does not read, check, or require any separate authorization token,
election record, or CHGR reference beyond the required
`--enrollment-reference` string (recorded as audit metadata only, HHCE-
REQ-049, never cryptographically verified — confirmed unchanged from
pre-2N.1). This exactly mirrors `hatp_deployment_binding_admin.py`'s own
`--assume-yes` semantics (identical `args.assume_yes or _prompt_confirm(...)`
pattern) and the script's own module docstring (§27-30 of this file):
the real security boundary is OS filesystem write permission on the
protected store root (HHCE-REQ-020), never an in-process authority check.
**Possession of that OS-level write permission plus `--assume-yes` is,
by this codebase's established architecture, sufficient to reach the
hardware ceremony — this is the intentional Protected Admin model, not a
gap introduced by 2N.1.**

## 18. `--assume-yes` bypass test

`test_assume_yes_skips_prompt_but_still_confirms_before_provider`:
monkeypatches `_prompt_confirm` to raise `AssertionError` if called at
all (proving it is genuinely skipped, not merely accepted), and confirms
`events == ['provider_ceremony', 'register_credential']` — the ceremony
still only runs because `--assume-yes` supplies `confirmed = True`, in
the same position confirmation always occupies. No contract (HHCE-001,
the governing prompt, or architectural precedent) requires an external
election check inside this script beyond OS-permission-boundary
authority (§5) — so this is **not** a bypass of any requirement the
primary contracts actually define. No new Blocking finding opened.

## 19. Confirmation binding content

The prospective description (§6) binds exactly the dimensions HHCE-001's
architecture basis supports for a pre-hardware description:
`repository_root`, `enrollment_reference`, `provider_profile`, operation
name, and policy/timeout. It does not bind `credential_id`/`public_key`
because neither is knowable pre-ceremony (§6/§7) — no narrower field the
contract actually defines was omitted.

## 20. Provider initialization before confirmation

None occurs. `_run_enrollment_ceremony`'s `Fido2HardwareProvider` import
and construction both live inside the function body, called only after
`confirmed` is established (§9). Zero provider object construction,
device enumeration, or HID access before confirmation.

## 21. Safe device discovery boundary (documentation only, not performed)

No enumeration code path exists in this script pre-confirmation today
(§20). A future real-device discovery step, if added, would need its own
explicit read-only classification — this phase performs no such
enumeration, synthetic or real, and makes no source change enabling one.

## 22. Provider failure after confirmation

`test_provider_failure_after_confirmation_no_record_no_false_success`:
confirmation accepted, ceremony raises `HATPProviderDeviceError` —
result: exit code 1, `events == ['confirmation_checked',
'provider_ceremony']`, and `lookup_credential` on the real (test-scoped)
store returns `None`. No false success, no partial record.

## 23. User-presence timeout

`test_user_presence_timeout_after_confirmation_clean_failure`: identical
shape to §22 with a presence-timeout-flavored provider error — exit code
1, exactly one ceremony attempt (`events.count('provider_ceremony') ==
1`, no automatic hardware retry), no record created.

## 24. Hardware success / persistence failure

Covered by §11/§12's retry test: hardware ceremony succeeds exactly
once; the registry write is what retries (bounded, in-process,
identical evidence), never the ceremony.

## 25. No caller-supplied credential identity

`test_enroll_parser_has_no_identity_override_flags`: the `enroll`
subparser's argument `dest` set contains none of `credential_id`,
`public_key`, `public_key_hex`, `signer_key_id`.

## 26. No recover/import regression

`test_no_recover_import_restore_subcommand_or_flag`: the top-level
subparser choices are exactly `{enroll, revoke}`; neither subparser
defines any of `recover`, `restore`, `import_`, `from_file`, `from_json`,
`stdin_evidence` as an argument dest.

## 27. Revoke non-regression

`test_revoke_never_calls_provider_ceremony` (not-found case, zero
ceremony calls) and `test_revoke_declined_confirmation_no_write`
(declined revoke leaves the existing record `active`, unmutated) both
pass against this phase's own fresh instrumentation.

## 28. Principal/Signer immutability

`git diff cbcbcc0c HEAD --stat -- scripts/hatp_principal_signer_admin.py`
produces no output — byte-identical.

## 29. Core writer/provider immutability

`git diff cbcbcc0c HEAD --stat` for `src/pcae/core/
hatp_hardware_credential_admin.py`, `hatp_fido2_provider.py`,
`hatp_providers.py`, `hatp_piv_provider.py`, and
`hatp_hardware_credentials.py` produces no output for all five —
byte-identical.

## 30. Contract immutability

`git diff cbcbcc0c HEAD --stat -- docs/contracts/
HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md` produces no output.
HPSE-001 was not touched by 2N.1 either (not present in the 12-file
commit-range diff at all).

## 31. Thin-wrapper recheck

The changed script's new logic is exactly: prospective description
construction, confirmation gating, provider orchestration (unchanged
call), writer invocation (unchanged call), output mapping (unchanged).
No record schema, JSON persistence, locking, duplicate-detection, or
revocation logic was added — all delegated to the untouched core module
(§29).

## 32. Current HMIC digest consequence

Independently recomputed via `derive_implementation_scope_digest
(HarnessPath.cwd())` (the real production function, not a re-
implementation): `abfbffca527d3bf6d6ba610f6f5cd2d80bf113f9aa08f4339eb
40322a8c077c4` — differs from the deployed/certified
`3b076a639b9f1b0c55facfd1a721d59d92a377d4bb63dce920843264e873a68e`, as
expected (an already-bound frozen member's bytes changed).
`_frozen_canonical_paths()` still returns exactly 38 paths, and
`scripts/hatp_hardware_credential_admin.py` remains one of them — no
membership change.

## 33. HMIC contract version consequence

No `HMIC-001` requirement text changed by this or the prior phase — the
frozen 38-member set and its normative definition are unchanged; only an
already-bound member's implementation bytes changed. Per precedent
(HHCE-001 v1.0→v1.1's own §30 rule: a version bump is required only when
requirement *text* changes), no `HMIC-001` version bump is required —
this is a new `implementation_scope_digest` value requiring fresh
certification at redeployment time, not a contract amendment.

## 34. `fido2` dependency declaration

`pyproject.toml` (unchanged by this or 2N.1): `hatp-hardware = ["fido2>=1.1,<2",
"cryptography>=42,<45"]` — **packaging declared**, confirmed. Separately,
`fido2` is importable in this Mac development environment right now
(local dev venv has the optional extra installed) — this is **not**
evidence about the deployed hac-dell venv, which per Phase
149O.20L.7O.2N's own fresh read-only inspection remains without the
package. **Packaging declared ≠ deployed venv provisioned** — both facts
independently reconfirmed, not installed or changed by this phase.

## 35. Original finding closure criteria — all nine independently proven

1. Vulnerable checkpoint calls hardware ceremony before confirmation — §3.
2. Repaired source confirms before provider enrollment — §4.
3. Declined confirmation ⇒ zero makeCredential/hardware mutation — §8/§9.
4. Preview ⇒ zero hardware mutation — §14.
5. Successful path preserves exactly one hardware ceremony — §11.
6. Provider-derived identity intact (never caller-supplied) — §12/§25.
7. Persistence retry never re-touches hardware — §11.
8. No alternate recover/import path exists — §26.
9. No authority bypass replaced the old ordering defect — §17/§18 (the
   OS-permission + `--assume-yes` model is the pre-existing, intentional
   architecture, not a new bypass introduced by this repair).

**All nine independently proven. B-149O.20L.7O.2N-1 CLOSED at the FIDO2
enrollment pre-hardware governance authorization boundary** (no claim
that FIDO2 enrollment is operational or that hardware is available —
this is a software-ordering closure only).

## 36. Possible secondary finding

None opened. §17/§18's `--assume-yes` analysis found the existing
OS-permission-boundary authority model, not a new bypass of any
requirement the primary contracts actually define.

## 37. Fixed-history evidence

The vulnerable-checkpoint reproduction test (§3) reads directly from the
frozen `cbcbcc0c` git blob via `git show`, never the working tree — the
historical defect remains permanently mechanically reconstructable and
this suite does not rewrite history into "confirmation always happened
first."

## 38. Independent test suite

`tests/test_phase_149o_20l_7o_2n_2_fido2_ordering_independent_
verification.py` — 13 fresh tests, authored independently of 2N.1's own
`tests/test_hatp_hardware_credential_admin_script.py` additions (no
shared fixtures or assertions). Covers: fixed vulnerable ordering,
repaired ordering, declined-confirmation zero provider/writer, preview
zero hardware + truthful description, `--assume-yes` semantics, one-
ceremony retry with identical evidence, provider failure after
confirmation, user-presence timeout, no caller identity flags, no
recover/import path, revoke non-regression (not-found + declined), and
the historical checkpoint re-derivation. All 13 pass:
`python -m pytest tests/test_phase_149o_20l_7o_2n_2_fido2_ordering_
independent_verification.py -q` → `13 passed`.

## 39. A/B worktree regression

Isolated `git worktree add ... cbcbcc0c --detach` for the vulnerable
checkpoint, compared against current HEAD via two full raw `-m
fast_green -n auto -q --tb=no -rf` runs (no `stash` used as baseline).
Vulnerable checkpoint: 333 failed / 8610 passed / 4 skipped / 9 errors.
Current HEAD: 334 failed / 8645 passed / 4 skipped / 9 errors. Node-ID
set diff (`comm -23`/`comm -13` on sorted FAILED+ERROR lists):

- **Current-HEAD-only failures (2):**
  `test_phase_149o_20l_7o_2m_2_..._2m_2_..._2m_2::TestLocalHMICReconstruction::
  test_local_digest_matches_recorded_digest` — the exact, expected §32
  digest-mismatch consequence, not a regression bug.
  `test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli` —
  reproduced as a `subprocess.TimeoutExpired` under `-n auto` parallel
  load; reran standalone and it passed (`1 passed in 13.62s`) — flaky,
  environmental, unrelated to this repair (shell-gate audit, not
  hardware-credential admin).
- **Vulnerable-checkpoint-only failure (1, "fixed" at HEAD):**
  `test_phase_149o_20l_7n_1_..._proposition_independent_verification.py::
  TestCandidateCurrentness::test_head_equals_origin_main` — a candidate-
  vs-origin/main currentness check that trivially differs by which
  commit the worktree happens to be checked out at; not attributable to
  this repair.

**Attributable regressions: zero.**

## 40. Fast Green (raw)

Current HEAD, full run: **334 failed, 8645 passed, 4 skipped, 9 errors**
(105 warnings). This large raw failed-count is a pre-existing,
environment-level baseline divergence independently reproduced
identically on the untouched vulnerable checkpoint (333 failed) —
consistent with 2N.1's own report of the same phenomenon. Not
normalized away; see §39 for the isolated attributable delta (2 new
nodes, both explained, zero unexplained).

## 41. No real effect

No Dell connection, no real FIDO2 enumeration, no physical authenticator,
no production protected store touched anywhere in this phase. All
provider/writer/registry state in every new test uses `tmp_path`-scoped
synthetic stores and monkeypatched seams.

## 42. Finding disposition

**B-149O.20L.7O.2N-1 → INDEPENDENTLY CONFIRMED CLOSED at the FIDO2
enrollment pre-hardware governance authorization boundary.** FIDO2
enrollment is **not** operational and real hardware is **not** available
as a consequence of this closure — this is a narrower, software-ordering
closure only (§35).

## 43. Overall verdict

**A: INDEPENDENTLY VERIFIED — B-149O.20L.7O.2N-1 CLOSED — REPAIRED
HARDWARE ADMIN ENTRYPOINT READY FOR HMIC/DEPLOYMENT PROGRESSION.**

## 44-46. Post-verification sequencing / package provisioning / hardware presence

Strong expected direction, narrowest sane sequence: (1) this
independently verified repair → (2) governed redeployment of the
repaired, already-HMIC-bound script/source to hac-dell → (3) fresh HMIC
`CertificationRecord` covering the new `implementation_scope_digest` →
(4) fresh activation / validator `VALID` → (5) provision the declared
`hatp-hardware` optional extra (`fido2`, `cryptography`) into the
deployed venv → (6) physically attach exactly one eligible authenticator
→ (7) read-only availability recheck → (8) authorize real FIDO2
enrollment → (9) real one-credential enrollment. On whether package
provisioning belongs inside step (2)'s same governed deployment-
environment transition or as a separate infrastructure step: `fido2` is
already declared under a normal optional extra (§34, standard packaging
mechanism, not bespoke infrastructure), so installing it is ordinary
environment realization of an already-frozen dependency declaration —
the narrowest sane sequence folds it into the same governed redeployment
transition that installs the repaired script, rather than treating it as
a distinct infrastructure phase. Physical authenticator attachment
remains separate and later (step 6), not a prerequisite for source-level
verification or redeployment — this phase requires no physical device
and used none.

## 47. Governance

`pcae health`: healthy (task scoped to this phase). `pcae check`:
passed. Full governed task/phase lifecycle used throughout — no raw git
commit/push, no `--no-verify`, no force push, no hook bypass.

## 48. Commits / push / origin

See `.pcae/phase-completion-metadata.json` `phase_commits` for the exact
phase-owned commit hashes; `pushed_status` and `origin_main_head` synced
there per this repository's standard finalization sequence.

## 49. Recommended next phase

**149O.20L.7O.2N.3 (or equivalent next-numbered phase) — Governed
redeployment of the repaired, already-HMIC-bound
`scripts/hatp_hardware_credential_admin.py` to hac-dell, including
provisioning the already-declared `hatp-hardware` optional extra into
the deployed venv as part of the same transition, followed by a fresh
HMIC `CertificationRecord`/activation covering the new
`implementation_scope_digest`.** Do not create a `CertificationRecord`
in that redeployment phase itself if certification is more naturally a
distinct follow-on step — determine at that phase's own start. Do not
touch real FIDO2 hardware yet; no new Blocking finding was opened this
phase, so no alternate narrow-repair phase is recommended instead.
