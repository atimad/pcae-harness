# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R — Production Protected-Presentation Registration Continuation Against Existing Generation-1 Deployment State

## CPIPC successor confirmation

Predecessor: `...1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R` (Privileged
Read-Only Generation-1 Protected-Root / PPA-Absence Verification and F-5
Execution-Hold Clearance Adjudication, completed, pushed `4fa2ddb1`).
Verified via `pcae.core.phase_id.parse/same_series/same_branch/compare`:
same series (149) and branch (O); `compare(pred, cand) == "less"`; this
phase's subphase tuple equals the predecessor's plus exactly one
trailing `(1,'R')` segment — a direct CPIPC successor. Confirmed unused
in prior history. No discrepancy; no alternate ID derived.

**G0 = `4fa2ddb1fe1ef6b4b7588bbaa49131d11120efb5`**, working tree and
index both clean, `origin/main..HEAD` = 0 at phase entry.

## Scope actually authorized and performed

Exactly the previously-blocked canonical PPA `install` configuration
transaction against the existing generation-1 protected root, anchor,
installation, agent-exclusion, and helper bytes verified by the
predecessor phase. No reprovisioning, no helper reinstall, no generation
reset, no human-approval ceremony, no YubiKey/FIDO2 interaction, no
production principal, no Gate 5 certification, no runtime enablement.

## Method and two non-blocking environmental obstacles

Minimum-necessary local administrator privilege was obtained via `sudo`
in the operator's own local terminal; the password was entered directly
by the human and never seen, echoed, requested, or logged by this
session. Full transcript and classification:
`.pcae/evidence/PHASE_1R_1R_1R_PRIVILEGED_COMMAND_AUDIT.json`.

Two obstacles were hit and root-caused before the transaction succeeded
— neither is a product defect and neither required any `src/pcae`
change:

1. **Attempt 1** failed closed with `acl_inspection_unavailable` because
   the operator's interactive shell `PATH` has several
   uid-501(configured-agent)-writable directories preceding `/usr/bin`
   and `/bin`; `_resolve_trusted_executable_for_subject` correctly
   refused to trust `ls` resolved through a contaminated PATH — the
   guard working as designed. Root-caused read-only, without sudo, by
   directly calling the resolver with the real PATH vs. a sanitized one.
2. **Attempt 2**, retried with a sanitized
   `PATH=/usr/bin:/bin:/usr/sbin:/sbin`, failed with
   `ModuleNotFoundError: No module named 'pcae'` because that sanitized
   PATH resolves `python3` to Apple's system interpreter, which does not
   see this repo's editable-install `sys.path` entry.
3. **Attempt 3** (successful): sanitized `PATH` for the internal
   `ls`/`getfacl` trust check, combined with an explicit full path to the
   Homebrew interpreter that has the editable install
   (`/opt/homebrew/bin/python3`) for module resolution. Neither change
   widens authority or touches product source.

A subsequent read-back diagnostic script raised one additional,
carefully root-caused false-positive exception
(`production HPAC root is not protected from the configured agent
principal`) — traced to the diagnostic script's own use of a freshly
constructed, unbound `HPACStoreAuthority.production()` (which falls back
to the *live process* identity, i.e. root under sudo, when no PAWA
writer factory has bound the configured-agent identity — and root
trivially "owns" the root it provisioned). Raw, direct `stat` of the root
and every ancestor directory (recorded below) independently confirms
the real topology is correctly protected from the actual configured
agent (uid 501). No source change was made or proposed for this; it is
documented as a diagnostic-script pitfall, not adjudicated as a product
defect.

## Independent pre-mutation revalidation

- Helper SHA-256 independently recomputed from `src/pcae/protected_presentation_helper.py`
  (unchanged since commit `a85abff6`, confirmed stable through G0):
  `933c66464516080b91fa2b5e7e2b50ea176a5887058bc63a51ddb083c9ea6182` — matches.
- Verifier-configuration digest independently recomputed via
  `canonical_json_bytes`/`canonical_digest` on
  `{"schema":"v1","verifier_kind":"pcae-protected-local-presentation/1.0"}`:
  `951182f5e737068d286313903504e34cb3dc57b47a2a19f9031ac068c7992c85` — matches.
- Complete registration write set derived from
  `protected_presentation_installation.py`/`hpac_protected_presentation_admin.py`
  source: `descriptor.json`, `installations/<generation>/installation.json`,
  `current-generation.json` under
  `presentation-mechanisms/v2/pcae-protected-local-presentation/` — all
  create-only, metadata only.
- Pre-registration host state reconfirmed: protected root present/trusted
  (root:admin, 0700), generation 1, PAWA installation id
  `hpawi-bfc91d001ac940b8bda0ed06566180eb`, configured agent
  atilamadai/501, agent-exclusion ACTIVE, helper present and matching, PPA
  installation/current-generation/partial-transaction all ABSENT.

## Registration transaction and read-back

`scripts/hpac_protected_presentation_admin.py install` executed exactly
once successfully:

```
install ok: mechanism=pcae-protected-local-presentation installation_id=hppi-648bee5e950b4f5e971a6c65c8cc53cf generation=1 descriptor_digest=c4e9a04d8d4af865372d78db280b8a2ba40f7ad29414b365acf87b775b13fc6e
```

Post-registration read-back (recorded in
`.pcae/evidence/PHASE_1R_1R_1R_PPA_REGISTRATION.json`, independently
re-verified by `tests/test_..._ppa_registration.py`):

- Write set confined to exactly the three authorized files; no
  unexpected durable artifact.
- `installation_digest` and `anchor_digest` both independently recompute
  (self-excluding canonical digest) to the stored values.
- `descriptor_digest` agrees across `descriptor.json`,
  `installation.json`, and `current-generation.json`; `installation_digest`
  agrees between `installation.json` and `current-generation.json`
  (currentness binding correct).
- Installed helper re-hashed after registration: unchanged, still
  `933c6646...9ea6182`, still byte-identical to the immutable
  generation-1 source.
- Protected root and its full ancestor chain re-`stat`'d directly:
  `uid=0`, modes `0700`/`0755` throughout; the configured agent (uid 501)
  has zero write access anywhere in the chain — topology trust holds.
- PAWA anchor unchanged: generation still 1, installation id
  `hpawi-bfc91d...`, agent-exclusion still ACTIVE.
- PAWA deployment capability consumed inside the single bounded
  multi-write (`HPACWriterCapability` is process-local, single-use,
  non-serializable by construction); adversarial replay against the
  now-live installation was deliberately not attempted (would require a
  second production mutation) and is deferred to the successor
  deployment-state IV.

## Bounded regression band

Targeted suites (RHAMP/PPA/Gate5/hpac_verifier): **468 passed, 5
failed**. `git diff --name-only -- src/pcae scripts pyproject.toml`
between G0 and HEAD is **empty** (zero product source changes this
phase), so every failure is necessarily pre-existing and unattributable
to this phase:

- `test_31_current_phase_changes_no_production_or_contract` and
  `test_05_production_diff_is_exactly_the_two_authorized_files` — both
  point-in-time `git diff` guards anchored to an earlier, now-stale fixed
  SHA; HEAD has legitimately moved since (other, unrelated completed
  phases).
- `test_30_repair_suite_contains_a_stale_live_head_assertion_finding_f3` —
  a point-in-time content-scan guard against historical file content.
- `test_object_dunder_new_bypasses_trusted_construction_seal` and
  `test_forged_via_object_new_would_report_real_runtime_eligible` — a
  pre-existing, documented forgery-detection gap unrelated to PPA
  registration.

## Required final verdicts

- GENERATION-1 START STATE: **REVALIDATED**
- PPA REGISTRATION TRANSACTION: **COMPLETE**
- AUTHORIZED REGISTRATION MUTATION: **PERFORMED**
- UNAUTHORIZED MUTATING HOST COMMANDS: **0**
- PPA INSTALLATION DESCRIPTOR: **PRESENT VERIFIED**
- PPA CURRENT GENERATION: **PRESENT VERIFIED**
- PPA TRANSACTION STATE: **COMPLETE**
- PAWA DEPLOYMENT CAPABILITY: **CONSUMED**
- GENERATION-1 HELPER AFTER REGISTRATION: **UNCHANGED VERIFIED**
- PROTECTED-ROOT / PAWA GENERATION: **PRESERVED**
- PROTECTED-ROOT TOPOLOGY TRUST: **VERIFIED**
- F-5 PROTECTED-PRESENTATION REGISTRATION: **COMPLETE — DEPLOYMENT-STATE IV PENDING**
- F-5: **DEPLOYED / IV PENDING**
- N-16-5: **NOT CLOSED**

## Recommended successor (not begun)

**Independent Verification of Production Protected-Presentation
Generation-1 Deployment State** — must independently re-verify (fresh,
not reusing this phase's own evidence as its sole source): protected
root/ancestors, anchor/install/generation, helper exact bytes/provenance,
helper path/ownership/modes, PPA installation and current-generation
descriptors, currentness, revocation, descriptor/helper binding,
verifier-config binding, PAWA capability provenance/consumption, absence
of any generic deployment authority, substitution resistance,
unprivileged-mutation resistance, installer != launcher != evidence
writer != human approver, ordinary development remaining unaffected, and
runtime remaining unavailable. Only after that IV may a separately
authorized final certification phase perform the real human/YubiKey
ceremony. N-16-6 and N-16-7 remain open, untouched, strictly last.
