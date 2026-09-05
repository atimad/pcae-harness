# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R — Privileged Read-Only Generation-1 Protected-Root / PPA-Absence Verification and F-5 Execution-Hold Clearance Adjudication

## CPIPC successor confirmation

Predecessor: `...1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R` (Batch-013 causal
isolation, completed, pushed `423df35a`). Verified via
`pcae.core.phase_id.parse/same_series/same_branch/compare`: same series
(149) and branch (O); `compare(pred, cand) == "less"`; candidate's
subphase tuple equals the predecessor's plus exactly one trailing
`(1,'R')` segment — a direct CPIPC successor. No discrepancy; no
alternate ID derived.

**H0 = `423df35af49c2c52ce4939f4d1af03b7f92d974a`**, working tree and
index both clean, `origin/main..HEAD` = 0 at phase entry.

## Predecessor readiness model reconstructed

The predecessor's own doc (`..._BATCH013_CAUSAL_ISOLATION.md`) states: of
12 governed clearance criteria (its own item 33), 11 satisfied, blocked
only on **criterion 11** ("no current generation-1 invariant violation")
because its diagnostic process hit `PermissionError` reading
`_PROTECTED_ROOT/.authority/*` — specifically the two host-dependent
tests `test_host_protected_root_generation_and_helper_digest_unchanged`
and `test_ppa_current_generation_and_installation_absent_on_host` in
`tests/test_..._1r_1_independent_verification_configured_agent_identity_threading_repair.py`.
This phase re-derives the complete current canonical readiness model
(below) rather than assuming a bare 12-count is still exhaustive, per the
phase charter's instruction not to silently equate the two models; the
reconstructed set below happens to also total 12 and is judged
sufficient.

## Method

Minimum-necessary local administrator privilege was obtained via
macOS's native Authorization Services dialog
(`osascript -e "do shell script ... with administrator privileges"`),
never through this session's terminal or chat — this environment's Bash
tool and the CLI's own terminal both lack a controlling TTY for `sudo`
to read a password from directly, so the native GUI dialog was the only
available legitimate mechanism. Every privileged command was classified
READ-ONLY before execution; the full transcript and classification is
recorded in `.pcae/evidence/PHASE_1R_1R_PRIVILEGED_COMMAND_AUDIT.json`.
**5 privileged commands executed; 0 mutated PCAE protected state.**

One methodological finding: the first topology-recognition attempt
failed with `acl_inspection_unavailable` because this development
shell's ambient `PATH` has uid-501(configured-agent)-writable
directories preceding the real `/bin` — the repaired
`_resolve_trusted_executable_for_subject` correctly refused to trust
`ls`/`getfacl` resolved through a contaminated PATH. This is the
guard working as designed, not a regression; re-running under a clean
system-only PATH (`/usr/bin:/bin:/usr/sbin:/sbin`) succeeded.

## Reconstructed readiness criteria table

| # | Criterion | Canonical source | Current evidence | Verdict |
|---|---|---|---|---|
| 1 | Protected root exists, is a real directory, not a symlink | HPAC-PAWA architecture | `stat`: Directory, not symlink | PASS |
| 2 | Protected root owner/group/mode == root:admin/0700 | frozen PAWA expectation | `stat`: root:admin, 0700 | PASS |
| 3 | Ancestor chain (`/`, `/Library`, `/Library/Application Support`, `.../PCAE`, `.../HPAC`) not configured-agent-writable | HPAC-PAWA-REQ-017/020 | all 0755/root-owned, no group/other write bit; non-privileged `stat` | PASS |
| 4 | Canonical §33 topology-recognition sequence succeeds for the configured agent (uid 501), not ambient root | `hpac_protected_admin_writer._run_recognition_sequence` | direct call as root, clean PATH: `RECOGNITION: SUCCESS` | PASS |
| 5 | PAWA anchor_id == `hpaw-f9661f...819a` | `deployment-owner.json` | read: exact match | PASS |
| 6 | PAWA installation_id == `hpawi-bfc91d...0eb` | `current-generation.json` / `deployment-owner.json` | read: exact match (both, and they agree with each other) | PASS |
| 7 | Generation == 1 | `current-generation.json` | read: `current_generation/generation` = 1 in both `current-generation.json` and `agent-exclusion.json` | PASS |
| 8 | Configured symbolic_account == `atilamadai`, provisioned_uid == 501, live OS mapping agrees | `agent-exclusion.json` + `id`/`dscl` | read + independent `id atilamadai` / `dscl` lookup: all agree | PASS |
| 9 | Agent-exclusion binding valid (digests cross-consistent, state ACTIVE) | `agent-exclusion.json` + `current-generation.json` + `deployment-owner.json` | `current-generation.json.agent_exclusion_digest` == `agent-exclusion.json.record_digest`; `current-generation.json.descriptor_digest` == `deployment-owner.json.descriptor_digest`; state ACTIVE | PASS |
| 10 | Generation-1 helper integrity: installed bytes == immutable Git blob (commit `2e416e9b`, blob `d80abf74`) | Git + installed file | independently reproduced from `git cat-file`: 16295 bytes, SHA-256 `933c664...9ea6182`; installed file: same size, same SHA-256, `cmp` byte-for-byte IDENTICAL; regular file, root:admin, 0644, canonical content-addressed path | PASS |
| 11 | Complete PPA registration write-set absent (clean pre-registration state) | derived from `protected_presentation_installation.py`/`approval_presentation.py` source | entire `presentation-mechanisms/v2/pcae-protected-local-presentation/` subtree absent; no `descriptor.json`/`installation.json`/anchor; no `.authority/writer.lock` (no writer_transaction of any kind has ever run); no unexpected `*presentation*`/`*install*` artifacts beyond the one known helper | PASS |
| 12 | RHAMP contamination trigger remains test-harness-only / absent from production and from this phase's own privileged path | grep + this phase's method | `grep -rn 'del sys.modules\|importlib.reload' src/pcae/ scripts/` → 0 occurrences; this phase's own privileged commands used no such trigger | PASS |

**READINESS CRITERIA: 12 / 12 PASS.**

## Required final verdicts

- PRIVILEGED READ-ONLY HOST INSPECTION: **COMPLETE**
- MUTATING PCAE HOST COMMANDS: **0**
- GENERATION-1 PROTECTED-ROOT STATE: **VERIFIED**
- PROTECTED-ROOT TOPOLOGY TRUST: **VERIFIED**
- PAWA ANCHOR STATE: **VERIFIED**
- PAWA INSTALLATION STATE: **VERIFIED**
- PAWA GENERATION: **1**
- CONFIGURED AGENT BINDING: **VERIFIED**
- AGENT-EXCLUSION BINDING: **VERIFIED**
- GENERATION-1 HELPER INTEGRITY: **VERIFIED**
- PPA INSTALLATION: **ABSENT VERIFIED**
- PPA CURRENT GENERATION: **ABSENT VERIFIED**
- PPA PARTIAL TRANSACTION: **ABSENT VERIFIED**
- PPA PRE-REGISTRATION STATE: **CLEAN**
- READINESS CRITERIA: **12 / 12 PASS**
- CURRENT F-5 READINESS: **SUPPORTED BY CURRENT VERIFIED HOST STATE**
- F-5 EXECUTION HOLD: **CLEARED**
- N-16-5: **NOT CLOSED**

Configured-Agent-Identity Threading Repair: **INDEPENDENTLY VERIFIED**
(reconfirmed against real host state this phase — the strongest
available confirmation; no ambient-root defect reappeared).

## No production / existing-test / contract / dependency / host change

- `git diff --name-only H0 HEAD -- src/pcae scripts pyproject.toml docs/contracts` → empty.
- `git diff --name-status H0 HEAD -- tests/` → additions-only (this
  phase's own new file).
- No `provision`/`install`/`rotate`/`revoke`/`configure` operation was
  invoked; `production_writer`/`apply_configuration`/`writer_transaction`
  were never called (only the read-only `_run_recognition_sequence`
  primitive, directly).
- Runtime unchanged: `not_implemented` / `Observed` / `observe` /
  `unavailable`; 0 plugins, 0 capabilities; first governed runtime
  external effect ABSENT/UNREACHABLE.

## Clearance is not registration authority

F-5 EXECUTION HOLD is CLEARED. This does **not** authorize PPA
registration in this phase or any other action beyond deriving the
successor below. No registration was attempted.

## Derived successor (not begun)

**Production Protected-Presentation Registration Continuation Against
Existing Generation-1 Deployment State** — the exact CPIPC-valid
successor of this phase. It must retry only the previously blocked
canonical PPA `install` configuration transaction against the
*existing* generation-1 protected root/anchor/installation/agent-
exclusion/helper bytes verified above (no reprovision, no generation
reset/rotation, no anchor delete/recreate, no helper reinstall). Carry
forward, subject to fresh primary-source revalidation:

- helper SHA-256: `933c66464516080b91fa2b5e7e2b50ea176a5887058bc63a51ddb083c9ea6182`
- helper version: `pcae-protected-local-presentation-helper/1.0`
- verifier configuration semantic object: `{"schema":"v1","verifier_kind":"pcae-protected-local-presentation/1.0"}`
- expected verifier-config digest: `951182f5e737068d286313903504e34cb3dc57b47a2a19f9031ac068c7992c85`
- renderer profile: `pcae-protected-local-presentation-renderer/1.0`
- descriptor version: `pcae-protected-local-presentation-descriptor/1.0`

After that registration, F-5 remains DEPLOYED/IV PENDING, not VERIFIED,
until an Independent Verification of Production Protected-Presentation
Deployment State, then final real protected-human + genuine YubiKey
certification, only after which N-16-5 closure may be adjudicated.
N-16-6 and N-16-7 remain untouched. This phase does not begin the
successor.

## Evidence

- `.pcae/evidence/PHASE_1R_1R_HOST_VERIFICATION.json` — full structured
  host-verification artifact.
- `.pcae/evidence/PHASE_1R_1R_PRIVILEGED_COMMAND_AUDIT.json` — every
  privileged command, its classification, exit code, and mutation
  result.
- `tests/test_..._1r_1r_1r_1r_1r_1r_1r_1r_1r_privileged_ro_gen1_ppa_absence_f5_hold.py`
  — 14 fresh tests, all passing: CPIPC successor validity, immutable
  Git helper provenance, RHAMP-trigger absence, no-diff-since-H0, non-
  privileged ancestor/root topology corroboration, and the recorded
  privileged findings frozen as regression-guarding literals.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` preserved. No
delegated worker was used for any privileged inspection or lifecycle
step in this phase.
