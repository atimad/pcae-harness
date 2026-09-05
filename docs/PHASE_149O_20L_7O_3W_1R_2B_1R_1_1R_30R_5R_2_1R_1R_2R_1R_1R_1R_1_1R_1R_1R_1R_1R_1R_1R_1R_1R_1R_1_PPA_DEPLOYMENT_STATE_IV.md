# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1 — Independent Verification of Production Protected-Presentation Generation-1 Deployment State

## CPIPC successor confirmation

Predecessor: `...1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R` (Production
Protected-Presentation Registration Continuation Against Existing
Generation-1 Deployment State, completed, pushed `8db9178e`). Verified via
`pcae.core.phase_id.parse/same_series/same_branch/compare`: same series
(149) and branch (O); `compare(pred, cand) == "less"`; this phase's
subphase tuple equals the predecessor's plus exactly one trailing
`(1, "")` segment — a direct CPIPC successor. No discrepancy; the phase ID
given in the operator directive is used exactly as given.

**V0 = `8db9178e61c44f36bba4c7e879e79fc75fdf99fc`** (identical to the
predecessor's finalized endpoint `G_FINAL` — no intervening commits).
`G0` (predecessor phase-open) = `4fa2ddb1fe1ef6b4b7588bbaa49131d11120efb5`.
`G_CHANGE` (predecessor registration commit) = `f78a13ff`.

## Purpose and scope actually performed

This is a strictly verification-only phase. It independently re-derives
and checks the ACTUAL production deployment state the predecessor
registration transaction created — not a re-run of predecessor
self-verification, not a trust of predecessor exit codes or prose. No
registration was re-run, no reprovisioning, no helper reinstall, no
generation reset, no repair of protected host state, no production/test
source change, no human-approval ceremony, no YubiKey/FIDO2 interaction,
no presentation evidence, no PRODUCTION principal, no Gate 5
certification, no runtime enablement.

## Method: privileged read-only inspection

All reads inside the root-owned, mode-0700
`/Library/Application Support/PCAE/HPAC/protected-root` tree were
performed by the human operator directly in their own trusted terminal
via `sudo` (`stat`, `ls`, `cat`, `find`, `shasum`, `lsof`, `plutil
-extract`, and `sudo -u atilamadai test -w` as a non-destructive
permission probe) — never through this agent's own shell, which has no
interactive TTY for a password prompt and correctly refused with "a
terminal is required to read the password" when tried. The password was
never seen, echoed, requested, logged, or persisted by any agent process.
Full results are recorded in
`.pcae/evidence/PHASE_1R_1R_1R_1_DEPLOYMENT_STATE_IV.json` and
independently re-checked (recomputed digests, cross-record consistency,
git-history tracing, a fresh forged-object construction against the real
Gate 5 boundary) in
`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1_ppa_deployment_state_iv.py`
(36 tests, 36 passed).

No mutating command was issued at any point: `writer.lock` is 0 bytes and
held by no process; the full `find` listing of
`presentation-mechanisms/` and `presentation-helper/` shows exactly the
same 3 mechanism files + 1 content-addressed helper file the predecessor
phase's own registration evidence recorded, nothing more, nothing fewer.

## Findings, by category

**Protected root / PAWA.** `/Library/Application Support/PCAE/HPAC/protected-root`
is `root:admin`, mode `0700`, device `16777230` / inode `555016224` —
matches the PAWA anchor's own `protected_root_identity` exactly. PAWA
anchor: `anchor_id=hpaw-f9661f401f204d828a4aec951855819a`,
`installation_id=hpawi-bfc91d001ac940b8bda0ed06566180eb`, `generation=1`,
`state=ACTIVE`, `supersedes=null` — matches expected exactly, no
unexplained rotation. Configured agent: `atilamadai` / uid `501`, bound in
`.authority/agent-exclusion.json` to the same PAWA installation ID and
generation, `state=ACTIVE`.

**Generation-1 helper.** Immutable source (`src/pcae/protected_presentation_helper.py`
at the frozen commit) independently re-hashed: 16295 bytes,
SHA-256 `933c66464516080b91fa2b5e7e2b50ea176a5887058bc63a51ddb083c9ea6182`.
Installed helper at the canonical content-addressed path: regular file,
not a symlink, 1 hard link, mode `0644` (not group/other-writable), same
byte length, same SHA-256 — byte-for-byte identity confirmed, and
identical to the pre-registration evidence recorded by the predecessor
phase (unchanged by registration).

**PPA installation descriptor / current-generation.** `descriptor.json`
binds `mechanism_id=pcae-protected-local-presentation`,
`verifier_kind=pcae-protected-local-presentation/1.0`,
`verifier_configuration_digest=951182f5e737068d286313903504e34cb3dc57b47a2a19f9031ac068c7992c85`
— independently recomputed from
`{"schema":"v1","verifier_kind":"pcae-protected-local-presentation/1.0"}`
via the repository's own `canonical_digest`, matches exactly.
`installations/1/installation.json` and `current-generation.json` both
have their `installation_digest` / `anchor_digest` independently
recomputed via the self-excluding canonical-digest scheme and both match
the recorded values; the two records cross-agree on
`installation_digest`/`descriptor_digest`; `current_generation=1` with no
conflicting generation directory found anywhere under the mechanism
path. All three durable files carry `status=active`; no revocation
marker of any kind exists in this schema, and no stale/orphaned pointer
is present.

**Write-set confinement.** The full `find` of
`presentation-mechanisms/v2/pcae-protected-local-presentation/` returns
exactly `descriptor.json`, `current-generation.json`, and
`installations/1/installation.json` — no other generation directory, no
other mechanism version. The full `find` of `presentation-helper/`
returns exactly one content-addressed directory containing exactly one
helper file. This independently confirms (not merely repeats) the
predecessor's claimed 3-file write set.

**Capability provenance / terminal consumption.** `HPACWriterCapability`
is process-local, single-use, and non-serializable by construction
(`hpac_protected_admin_writer.py`); no persisted capability token exists
anywhere in the verified write set. Live replay was correctly not
attempted (would require a second production mutation, out of scope).
Verified structurally, not by a live replay attempt.

**Substitution / unprivileged-mutation resistance.** `_reject_symlink_chain`
walks every path component up to `protected_root` and is wired directly
into `verify_helper_bytes` (HPAC-PPA-REQ-012) — confirmed at the source
level; no symlinked component exists anywhere in the live tree per the
`find`/`stat` results. `sudo -u atilamadai test -w` against both
`current-generation.json` and the protected root itself both report "not
writable" — the configured agent cannot modify protected trust state.

**Role separation.** Installer (`hpac_protected_presentation_admin.py`,
sole PAWA `configure_presentation_mechanism` consumer), launcher
(`protected_presentation.py`, sole `posix_spawn` mediator), evidence
writer (`mint_protected_presentation_evidence_writer`, seal-guarded), and
human approver (`protected_presentation_helper.py`) remain four distinct
modules; the registration transaction's write set contains no artifact
that grants launcher or evidence-writer authority to install.

**Forged-object negative verification (HPAC-REQ-056).** A fresh,
independently constructed `object.__new__(AuthenticatedHumanPrincipal)`
with every slot populated including `assurance_class=PRODUCTION` is
`isinstance`-true and reports `is_real_runtime_eligible=True` — the
documented construction-boundary gap is real and reproduced (pre-existing,
tracked, not repaired here; it is unrelated to PPA registration or host
state). However, the actual Gate 5 consumption boundary
(`is_verifier_authenticated_principal`, an identity-keyed process-local
registry populated only by `verify_human_authentication`'s own return
path) independently and correctly rejects the forged object —
`runtime_dispatch_gate5.py:236-241` calls this exact function first and
returns `("authenticated_principal_not_verifier_issued",)` before any
approval/lifecycle logic runs; `runtime_authority.py` uses the same
boundary at two further call sites. Gate 9 never touches the raw
principal, only registry-provenanced results. **The forged object cannot
traverse the real production authority boundary — not a blocker for F-5
or N-16-5.**

**Predecessor five-failure re-adjudication.** A fresh, independent
targeted-suite run (`--tb=no -rf` across the same 11 suites) reproduces
exactly the same 5 failures, 468 passed:

1. `test_31_current_phase_changes_no_production_or_contract` — HISTORICAL
   / POINT-IN-TIME GUARD. Fixed historical anchor; HEAD has legitimately
   advanced.
2. `test_30_repair_suite_contains_a_stale_live_head_assertion_finding_f3`
   — HISTORICAL / POINT-IN-TIME GUARD. Content-scan guard against a
   repair suite's source text as it existed at an earlier phase; the
   suite has since been legitimately edited by intervening phases.
3. `test_05_production_diff_is_exactly_the_two_authorized_files` —
   HISTORICAL / POINT-IN-TIME GUARD. Independently traced: the diff
   against fixed anchor `0250e5f7` now additionally includes
   `hatp_class_b_topology_verifier.py`, `notifications.py`,
   `phase_reports.py`; `git log 0250e5f7..HEAD` for exactly those three
   files resolves to commits `8407dd24` ("configured-agent-identity
   threading repair") and `8bfce890` ("durable Telegram notification
   acceptance receipts") — two distinct, already-completed, unrelated
   phases. Not PPA registration, not host-state change.
4. `test_object_dunder_new_bypasses_trusted_construction_seal` — CURRENT
   PRODUCT DEFECT (see forged-object section above). Non-blocking:
   independently confirmed the real Gate 5 boundary rejects it.
5. `test_forged_via_object_new_would_report_real_runtime_eligible` —
   CURRENT PRODUCT DEFECT, same gap, same non-blocking confirmation.

None of the five is host-state-dependent (none reads the protected root
or any PPA/PAWA state); classification was **not** made by source-diff
absence alone — items 1-3 are independently traced to specific unrelated
commits via `git log`, and items 4-5 are independently re-exercised
against the real Gate 5 code path, not merely re-run as existing unit
tests. **No hidden F-5/N-16-5 blocker found.**

**Ordinary-development independence.** `pcae health`, `pcae check`,
`pcae status coherence`, `pcae doctor task-memory`, and
`pcae runtime inspect` all remain usable without any hardware or
ceremony. Runtime: `not_implemented` / `Observed` / `observe` /
`unavailable`, 0 plugins, 0 capabilities. First governed runtime external
effect: **ABSENT / UNREACHABLE**.

**Host mutation audit.** `AUTHORIZED MUTATING HOST COMMANDS: 0`.
`UNAUTHORIZED MUTATING HOST COMMANDS: 0`. Every privileged command issued
this phase was one of `stat`/`ls`/`cat`/`find`/`shasum`/`lsof`/`plutil
-extract`/`sudo -u <agent> test -w` (a permission probe, not a write).

## Required final verdicts (§57)

```
PRIVILEGED DEPLOYMENT-STATE INSPECTION:            COMPLETE
AUTHORIZED MUTATING HOST COMMANDS:                 0
PROTECTED-ROOT TOPOLOGY:                           VERIFIED
PAWA GENERATION-1 STATE:                           VERIFIED
GENERATION-1 HELPER PROVENANCE:                    VERIFIED
GENERATION-1 HELPER BYTE IDENTITY:                 VERIFIED
PPA INSTALLATION DESCRIPTOR:                       VERIFIED
PPA CURRENT-GENERATION STATE:                      VERIFIED
PPA CURRENTNESS:                                   VERIFIED
PPA REVOCATION STATE:                              VERIFIED
DESCRIPTOR / HELPER / CONFIG / PROFILE BINDINGS:   VERIFIED
PAWA DEPLOYMENT CAPABILITY PROVENANCE:             VERIFIED
PAWA DEPLOYMENT CAPABILITY TERMINAL CONSUMPTION:   VERIFIED
PPA TRANSACTION STATE:                             COMPLETE
SUBSTITUTION RESISTANCE:                           VERIFIED
UNPRIVILEGED MUTATION RESISTANCE:                  VERIFIED
ROLE SEPARATION:                                   VERIFIED
PREDECESSOR FIVE-FAILURE ATTRIBUTION:              COMPLETE
PRODUCTION PROTECTED-PRESENTATION GENERATION-1
  DEPLOYMENT STATE:                                INDEPENDENTLY VERIFIED
F-5:                DEPLOYMENT VERIFIED — FINAL REAL ASSURANCE CERTIFICATION PENDING
N-16-5:             NOT CLOSED
```

## What remains (not begun this phase)

`hpac_verifier`'s documented `AuthenticatedHumanPrincipal` raw-construction
gap (HPAC-REQ-056, `object.__new__` bypass) remains open product debt —
non-blocking for F-5/N-16-5 because the real Gate 5/`runtime_authority`
consumption boundary independently rejects it, but not repaired in this
verification-only phase.

Next CPIPC-valid successor (conceptual title, not begun): **Final
Real-Human / Genuine-YubiKey Protected-Presentation N-16-5 Certification
and Closure Adjudication** — the real current installed helper, a real
human explicit APPROVE, a real protected-presentation evidence write, a
genuine YubiKey assertion through the certified FIDO2 profile, genuine
UP/UV, `verify_human_authentication(require_real_assurance=True)`, a
PRODUCTION `AuthenticatedHumanPrincipal`, and Gate 5 consumption — with
the standard negative cases (wrong challenge, replay, revoked credential,
missing presentation, PB DENY, policy DENY) all denying. No human or
hardware ceremony was performed in this phase.
