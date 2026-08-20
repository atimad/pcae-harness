# Phase 149O.20L.7O.2M.1 Completion Report

**Verdict:** A — INDEPENDENTLY VERIFIED — HMIC v1.7/38-MEMBER SOURCE
IDENTITY VERIFIED — EXACT +2 DELTA VERIFIED — GOVERNED REDEPLOYMENT MAY
PROCEED. Zero Blocking findings. Superseded stale draft below
regenerated on successful `pcae phase complete`; see docs/
PHASE_149O_20L_7O_2M_1_HMIC_V1_7_TRUST_ENROLLMENT_ADMIN_ENTRY_POINT_
SOURCE_SCOPE_EVOLUTION_INDEPENDENT_VERIFICATION.md for the full phase
report.

Prior (149O.20L.7O.2M) verdict, retained below for reference only:

Independently re-verified 149O.20L.7O.2L.3's repair of the sole
Blocking finding identified by 149O.20L.7O.2L.2 (HARDWARE-ENROLLMENT
RECOVERY AUTHORITY DEFECT). Used isolated `git worktree` checkpoints at
the vulnerable commit `2396055f` (post-2L.1/pre-2L.3) and the repaired
commit (current tree), not stash-only. Independently re-read HHCE-001
v1.1 and the 149O.20L.7O.2L architecture-freeze document directly, not
trusted from 2L.3's own summary.

Reproduced the historical fabricated-evidence exploit against the
frozen vulnerable source blob (`git show 2396055f:...`): the vulnerable
`_cmd_recover` constructs `CredentialEnrollmentEvidence` directly from
caller argparse fields with zero hardware ceremony, and persists it as
an authoritative `HardwareCredentialRecord` (independently
reconfirmed, executed against a disposable store root). Applied the
identical attack to the repaired CLI (central closure test): argparse
rejects `recover` before any provider/writer call; `register_credential`
(monkeypatched to raise if reached) was never called; zero record
created.

Independently instrumented and confirmed: provider-only enrollment
identity provenance (no caller override after the ceremony returns);
exactly one hardware ceremony per `enroll` invocation even under a
flaky registry write; retry-object identity (all attempts pass the
identical evidence object, `is`-compared); the retry helper's
reachability is gated strictly behind a successful ceremony call, with
no argparse path that can construct its evidence argument
independently.

Freshly classified `_register_with_in_process_retry`'s exact
`_HANDLED_ERRORS` catch scope across nine failure categories:
transient/uncertain failure and already-landed idempotent replay are
correctly retried/resolved; deterministic conflict, malformed on-disk
state, and permission/path failure are all retried unnecessarily but
every path still fails closed with no overwrite/reactivation/false
success (classified **Non-Blocking**, `NB-2L.4-1`); unexpected
programming exceptions (`AttributeError`/`TypeError`) are correctly
**not** caught or retried, propagating immediately (classified
**Clean**). Exhausted retries are finite (3, no infinite loop), fail
closed, and print a diagnostic naming no credential material.

Confirmed confirmation zero-touch for both `enroll` and `revoke`
(writer call count = 0 on decline); `revoke` non-regression (valid
revoke, idempotent monotonic replay, missing-ID fails closed, no other
record mutated); `scripts/hatp_principal_signer_admin.py` and its core
module byte-identical since both 2L.3's phase entry and the vulnerable
checkpoint; all six named core writer/provider modules and both bound
contracts (HHCE-001, HPSE-001) byte-identical since the vulnerable
checkpoint; the retry helper's AST call set is exactly
`{register_credential, print, range, len, type}` — a thin
orchestration wrapper, not a reimplemented transaction engine.

Freshly (not quoted from 2L.3) applied HMIC-REQ-052 to both repaired
scripts: both independently answer YES. `_FROZEN_AUTHORITY_BEARING_FILES`
independently confirmed exactly 36 (live-object-asserted); neither
script is a current member; the future delta is independently
re-derived (set-union computed) as exactly 36 → 38, unchanged from
2L.3's own claim.

All six required original-finding-closure elements independently
established (no public `recover`; no equivalent import path; fabricated
evidence cannot reach registration via public CLI; identity derives
only from provider output; retry is not an externally-supplied-identity
channel; no new provenance bypass). **HARDWARE-ENROLLMENT RECOVERY
AUTHORITY DEFECT: INDEPENDENTLY CONFIRMED CLOSED AT THE
TRUST-ENROLLMENT STANDALONE ADMIN ENTRY-POINT BOUNDARY** — this does
not claim broader HATP readiness closure, and does not claim the Dell
(hac-dell) certification either validates or is invalidated by these
Mac-side-only repaired scripts (hac-dell continues running its own
prior deployed source generation, unaffected by this development).

45 new, independently-authored tests (does not import any 2L.3 test
module), all pass:
`tests/test_phase_149o_20l_7o_2l_4_hatp_hardware_credential_admin_recovery_authority_repair_independent_verification.py`.
Combined focused suite across `hatp_hardware_credential_admin_script.py`
+ `hatp_principal_signer_admin_script.py` + all five 2L/2L.1/2L.2/2L.3/2L.4
phase test files: 179/179 pass.

`git worktree`-isolated A/B fast_green comparison (vulnerable `2396055f`
vs. current repaired tree, `python -m pytest -m fast_green -n auto -q`):
vulnerable 334 failed/8471 passed/4 skipped/9 errors; repaired 333
failed/8498 passed/4 skipped/9 errors. Full FAILED/ERROR node-ID diff
found exactly one candidate-only node and two vulnerable-only nodes,
each individually investigated and confirmed non-attributable
(`-n auto` parallel-execution flakiness re-confirmed passing in
isolation; one is a detached-HEAD-checkpoint `origin/main` comparison
artifact, not a code regression). **Zero attributable regressions.**
Fast Green raw result reported honestly above, not converted to "0
failed" shorthand.

No physical FIDO2/PIV hardware was touched in any test this phase
wrote; hac-dell was not connected to; no real protected writer path was
exercised (every writer call targets a disposable `tmp_path` root); no
HMIC source scope was changed; no HATP readiness/activation state was
changed.

Full findings:
`docs/PHASE_149O_20L_7O_2L_4_HATP_HARDWARE_CREDENTIAL_ADMIN_RECOVERY_AUTHORITY_REPAIR_INDEPENDENT_VERIFICATION.md`.

Recommended next phase: the narrow **HMIC v1.7 source-scope evolution
phase**, binding exactly `scripts/hatp_hardware_credential_admin.py`
and `scripts/hatp_principal_signer_admin.py` (36 → 38); not authorized
here. `NB-2L.4-1` (retry-quality, Non-Blocking) may optionally be
repaired narrowly in a follow-on phase; it does not block HMIC
progression.
