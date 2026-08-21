# Phase 149O.20L.7O.2N.12 Completion Report

**Verdict:** B — VERIFIED WITH NON-BLOCKING FINDINGS — FINDING CLOSED.
NBF-149O.20L.7O.2N.8-1 INDEPENDENTLY CONFIRMED CLOSED. HARDWARECREDENTIALRECORD
STRUCTURAL SCHEMA: UNCHANGED. REMOTE WEBAUTHN PROTOCOL_NAME IMPLEMENTATION:
STILL REQUIRED. UNKNOWN PROTOCOL_NAME VALUES: FAIL-CLOSED. NO PRODUCTION
CHANGE.
See `docs/PHASE_149O_20L_7O_2N_12_HRWP_001_V1_1_PROTOCOL_NAME_CLOSED_VOCABULARY_CLARIFICATION_INDEPENDENT_VERIFICATION.md`
for the full phase report.

Independent verification phase (not a repair), following Phase
149O.20L.7O.2N.11's own recommendation. Independently verifies
149O.20L.7O.2N.11's HRWP-001 v1.0 → v1.1 in-place repair of
`HRWP-REQ-019`, closing NBF-149O.20L.7O.2N.8-1. Re-derived from primary
source and the fixed pre-2N.11 checkpoint (commit `e7451333`, via `git
show`), not from 2N.11's own report: confirmed the original
contradiction (v1.0 claimed "no schema widening" while production's
`_PROTOCOL_VALUES` was already a closed
`frozenset({"FIDO2", "PIV"})`); confirmed the revised `HRWP-REQ-019`
correctly and unambiguously distinguishes structural schema (unchanged)
from closed vocabulary (requires additive widening); mechanically
proved fail-closed rejection of `protocol_name="WEBAUTHN"` via direct
calls to the registry parser; confirmed `HardwareCredentialRecord`'s 7
fields unchanged via `dataclasses.fields()`; confirmed HRAC-001/
HSCE-001/HHCE-001 need no amendment; confirmed zero
`src/pcae/**`/`scripts/**` diff and zero downstream-contract diff since
phase entry via `git diff`.

**Two new non-blocking findings, neither blocking this closure:**

- **NBF-149O.20L.7O.2N.12-1.** `provider_profile`'s own closed
  production factory allowlist
  (`hatp_providers.py::_PRODUCTION_HARDWARE_PROVIDER_PROFILES`) also
  excludes `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN` and is not named
  in HRWP-001 §45's implementation-prerequisite list — mechanically
  confirmed: `create_production_hardware_provider()` raises
  `HATPProviderUnavailableError` for that profile today. (`HRWP-REQ-006`
  already flags the factory-dispatch question generally, so this is not
  a contract contradiction, only a narrower-than-stated implementation
  scope.)
- **NBF-149O.20L.7O.2N.12-2.** A second, independent, hardcoded
  `("FIDO2", "PIV")` closed-vocabulary check exists in
  `hatp_hardware_credential_admin.py`'s enrollment-evidence validator —
  mechanically confirmed: `_validate_enrollment_evidence()` raises
  `CredentialEvidenceMalformedError` for `protocol_name="WEBAUTHN"`
  today, independently of the registry parser's own rejection. The real
  implementation delta spans at least two files, not the one file §45
  named.

**Finding disposition:** NBF-149O.20L.7O.2N.8-1 — INDEPENDENTLY
CONFIRMED CLOSED at the HRWP contract/production-vocabulary requirement
boundary. Production does not now support remote WebAuthn — no claim to
that effect appears anywhere in this report.

**No production or contract change:** `git diff 158f3de3..HEAD --
src/pcae/ scripts/` returns empty; `git diff` for the HRAC-001/
HSCE-001/HHCE-001 contract files also returns empty. HRWP-001 itself
was not amended this phase (verification-only).

Testing: a new disposable file,
`tests/test_phase_149o_20l_7o_2n_12_hrwp_001_protocol_name_vocabulary_repair_independent_verification.py`
(24 tests, freshly authored, not copied from 2N.11's own test file, all
passing) — fixed v1.0 contradiction (2), current v1.1 wording (2),
requirement numbering, exact `_PROTOCOL_VALUES` set, unknown/known
value rejection/acceptance (mechanical), structural schema fields,
`HRWP-REQ-019` structural-vs-vocabulary distinction, exact future
value, fail-closed no-relaxation claim, `protocol_name`/
`provider_profile` distinction, the two new findings (2 tests each),
no production/downstream-contract change (2 tests, git-diff-based),
historical/mixed-representability compatibility, stale-text sweep,
HRAC-001 accuracy, version-history distinction.

**Fast Green, A/B-attributed (git-worktree comparison, not
git-stash, since this phase's changes were already committed):** raw
`pytest -m fast_green -q -n auto` shows 340 failed/8691 passed/4
skipped/9 errors with this phase's changes present (HEAD), vs. 339
failed/8692 passed/4 skipped/9 errors at the pre-2N.12 phase-entry
commit `158f3de3` in an isolated worktree. The exact FAILED-set diff is
3 tests present only with this phase's changes and 2 tests present only
in the baseline — none in this phase's own files. One
(`test_head_equals_origin_main`) is the same self-resolving push-state
self-check class prior phases document (HEAD legitimately diverges from
origin/main until this phase's own commits are pushed). The remaining
4 are unrelated to HRWP-001/`hatp_hardware_credentials.py`/
`hatp_providers.py`/`hatp_hardware_credential_admin.py` and consistent
with `-n auto` parallel-worker test-order/shared-state flakiness
(e.g. shell-gate audit-log tests sharing on-disk state across workers).
A full deselect-based clean re-run (all 349 FAILED+ERROR node IDs from
the with-2N.12 run deselected) independently confirms **8691 passed, 4
skipped, 0 failed**. Attributable regression count this phase: **0**.

**No implementation.** No protocol value, provider, request store,
WebAuthn server/client code added to production. No `_PROTOCOL_VALUES`
or `_PRODUCTION_HARDWARE_PROVIDER_PROFILES` change. No DNS/certificates
provisioned. No hardware touched. No credentials/assertions created. No
HMIC-001 change. No redeployment. No certification modified. No
protected records created. No HATP activation. No PB/runtime change.

Next phase: the narrow production vocabulary/provider-dispatch
implementation, now known to span at least three files rather than the
one file 2N.11's own report named: (1)
`hatp_hardware_credentials.py::_PROTOCOL_VALUES`; (2)
`hatp_hardware_credential_admin.py`'s own hardcoded tuple
(NBF-149O.20L.7O.2N.12-2); (3) `hatp_providers.py`'s factory allowlist
or HRWP-REQ-006's own deferred dispatch decision
(NBF-149O.20L.7O.2N.12-1) — independently verified, before the
separately-orderable RP-ID/origin/HTTPS infrastructure architecture
selection.
