# Phase 149O.20L.7O.2N.13 Completion Report

**Verdict:** IMPLEMENTED — INDEPENDENT VERIFICATION PENDING.
NBF-149O.20L.7O.2N.12-2: REPAIRED — INDEPENDENT VERIFICATION PENDING.
NBF-149O.20L.7O.2N.12-1: DISPOSED — OUTCOME A (NOT A PRESENT DEFECT /
FUTURE IMPLEMENTATION OBLIGATION). REMOTE PROVIDER_PROFILE: KNOWN
CONTRACT IDENTITY BUT NOT YET PRODUCTION-AVAILABLE. PROVIDER FACTORY:
NOT FALSELY ADVERTISING AN UNIMPLEMENTED REMOTE PROVIDER. LOCAL FIDO2:
UNCHANGED. HMIC MEMBERSHIP: UNCHANGED. DELL: UNCHANGED / STILL CERTIFIED
FOR ITS CURRENT DEPLOYED SOURCE. NO REMOTE WEBAUTHN PROVIDER IMPLEMENTED.

Narrow implementation/prerequisite-resolution phase, following Phase
149O.20L.7O.2N.12's independent verification. Resolves the two
prerequisites that phase named.

**1. NBF-149O.20L.7O.2N.12-2 (REPAIRED).** `hatp_hardware_credentials.py::_PROTOCOL_VALUES`
additively widened from `frozenset({"FIDO2", "PIV"})` to
`frozenset({"FIDO2", "PIV", "WEBAUTHN"})`. `hatp_hardware_credential_admin.py`'s
previously-duplicated, mirrored `("FIDO2", "PIV")` closed-vocabulary
check in `_validate_enrollment_evidence` now imports and consumes that
same canonical `_PROTOCOL_VALUES` object — verified `is`-identical, not
merely equal — via an already-valid, pre-existing dependency boundary
(this module already imports other underscore-private symbols from
`hatp_hardware_credentials.py`; the docstring documents this as
established codebase convention). This *eliminates* the divergence
NBF-149O.20L.7O.2N.12-2 identified rather than widening two mirrored
literals in parallel (§7 Option B, chosen over Option A).

**2. NBF-149O.20L.7O.2N.12-1 (DISPOSED — OUTCOME A).**
`create_production_hardware_provider()` (`hatp_providers.py`) was read
fresh, start to finish, this phase. It is a closed-allowlist *gate*
(`if provider_profile not in _PRODUCTION_HARDWARE_PROVIDER_PROFILES:
raise ...`) followed by an *unconditional* FIDO2-then-PIV-fallback
attempt — there is no branch that dispatches by profile value to a
distinct provider class. Adding `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN`
to the allowlist today would therefore not "enable" a remote provider —
it would silently route any remote-profile caller into the *local*
`Fido2HardwareProvider`, which is exactly the remote-to-local fallback
HRWP-001 (client trust model, §19) and this phase's own governing prompt
(§16) prohibit. `hatp_providers.py` was therefore left unmodified, and
the remote profile continues to fail closed
(`HATPProviderUnavailableError`), mechanically confirmed — never falling
through to local FIDO2. `HRWP-REQ-006` already explicitly defers this
exact dispatch-mechanism decision to a future implementation phase and
does not itself resolve it; this disposition is consistent with, not
contradicted by, that deferral.

**No production change outside the intended scope:** `git diff --stat
5ec43cb4..HEAD -- src/pcae/ scripts/` shows exactly
`hatp_hardware_credentials.py` and `hatp_hardware_credential_admin.py`
changed (13 insertions, 4 deletions total). No contract file
(HRWP-001/HRAC-001/HSCE-001/HHCE-001) changed this phase.

**Testing:** a new disposable file,
`tests/test_phase_149o_20l_7o_2n_13_hrwp_protocol_vocabulary_and_provider_dispatch_prerequisite.py`
(28 tests, all passing) — exact widened vocabulary, no aliases;
registry-parser WEBAUTHN acceptance / arbitrary-unknown rejection /
legacy FIDO2-PIV regression; admin-validator centralization and
shared-object identity; absence of a third duplicated validator anywhere
in `src/pcae` (full-tree grep); unchanged structural schema (both
`HardwareCredentialRecord` and `CredentialEnrollmentEvidence`);
mixed-protocol-record coexistence (FIDO2+PIV+WEBAUTHN, no collision);
multi-`SignerRecord`-per-`Principal` regression; unchanged factory
allowlist; fail-closed rejection (not fallback) of the remote profile;
factory source re-derivation proving no per-profile dispatch branch
exists; local-FIDO2-construction regression-freedom; truthful
`discover_hardware_providers()` (never advertises WEBAUTHN); HRWP-001
text unamended by this phase; HMIC membership (both files already
bound, count still 38) and digest derivability.

**Pre-existing test debt repaired as a side effect:** 8 tests across 6
downstream phase test modules (2N.1, 2N.8, 2N.11, 2N.12, 2M.1, 2H.1)
pinned this phase's two files as byte/commit-unchanged relative to
*their own* historical phase-entry checkpoints — an assertion this
phase's legitimate, intended change necessarily broke. All 8 were
updated to assert the historical fact via a fixed `git show`/checkpoint
read instead of a live-HEAD comparison, mirroring the identical pattern
`test_phase_149o_20l_7o_2n_1_...py` already established for
`scripts/hatp_hardware_credential_admin.py`'s own prior legitimate
change. All 8 re-verified passing after the update.

**Fast Green, A/B-attributed (git-stash isolation, both runs at
identical `-n auto` parallelism, working tree clean post-commit for the
with-changes run):** baseline (stashed, pre-phase-entry commit
`5ec43cb4`): 339 failed / 8692 passed / 4 skipped / 9 errors in 135.52s.
With this phase's changes: 341 failed / 8686 passed / 4 skipped / 9
errors in 136.32s. The exact FAILED-set diff (`comm -13`) is exactly 2
new node IDs, both expected and correctly disposed:

- `test_phase_149o_20l_7n_1_...::test_head_equals_origin_main` — the
  same self-resolving push-state self-check class prior phases document;
  resolves once this phase's commits are pushed.
- `test_phase_149o_20l_7o_2n_3_...::test_local_digest_matches_recorded_digest` —
  expected: this phase changed bytes of two already-HMIC-bound files, so
  the local development `implementation_scope_digest` now legitimately
  differs from hac-dell's still-valid, unredeployed certified digest,
  exactly as this phase's own governing prompt anticipates (§24-§26: do
  not redeploy or recertify hac-dell this phase).

A third apparent new failure
(`test_backend_cli.py::TestHardeningReviewCLI::test_review_create_no_raw_content_in_text`)
was independently confirmed to be `-n auto` parallel-worker order/state
flakiness, not attributable: it passes in isolation. A full
deselect-based clean re-run (all 341 FAILED node IDs from the
with-2N.13 run deselected) independently confirms **8686 passed, 4
skipped, 0 failed**; the 9 errors were confirmed byte-identical/
pre-existing between the baseline and with-changes runs. Attributable
regression count this phase: **0**.

**No implementation.** No `RemoteWebAuthnProvider` class, challenge/
session store, HTTP route, browser/mobile client code. No
`makeCredential`/`getAssertion` invoked against real or simulated
hardware. No `HardwareCredentialRecord`/`Principal`/`Signer`/
`DeploymentBinding` created. No DNS/TLS/RP-ID provisioned. No HMIC-001
amendment (membership count unchanged at 38). No hac-dell redeployment
or recertification. No HATP activation. No Permission Broker/runtime
change. `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN` was **not** added to
`_PRODUCTION_HARDWARE_PROVIDER_PROFILES` — an explicit disposition, not
an oversight.

Next phase: independent verification of this narrow production
prerequisite repair (protocol_name vocabulary widening +
duplicated-validator centralization, and the NBF-149O.20L.7O.2N.12-1
provider-dispatch disposition), mirroring the 2N.11-to-2N.12
verification precedent. Only after that verification lands should the
project move to the separately-orderable RP-ID/origin/HTTPS
infrastructure architecture selection (HRWP-REQ-027/HRWP-REQ-031) — not
remote-WebAuthn server/provider implementation, which remains gated on
that infrastructure decision and on HSCE-001's own named-but-unresolved
remote-ceremony evidence-capture companion work (HRWP-REQ-060).
