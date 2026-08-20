# Phase 149O.20L.7O.2L.1 — HATP Trust-Enrollment Standalone Protected Admin Entry-Point Implementation

## Status

**CODE IMPLEMENTATION ONLY — NO REAL TRUST-ENROLLMENT EFFECT PERFORMED.**

## Summary

Implements exactly the two standalone Protected Admin entry-point
scripts that Phase 149O.20L.7O.2L's architecture re-derivation named as
the sole missing artifact between the already-implemented, already-HMIC
-bound Trust-Enrollment core writers and a real hardware-credential/
principal/signer enrollment:

- `scripts/hatp_hardware_credential_admin.py`
- `scripts/hatp_principal_signer_admin.py`

Both scripts are thin, fail-closed wrappers: administrative input
parsing → protected confirmation boundary → call the existing core
writer → render a deterministic result. Neither reimplements record
parsing, validation, identity derivation, locking, persistence, duplicate
detection, revocation semantics, or `DeploymentBinding` validation — all
of that remains owned by `pcae.core.hatp_hardware_credential_admin` and
`pcae.core.hatp_principal_signer_admin`, unmodified by this phase.

## Architecture Preserved From 149O.20L.7O.2L

Two standalone scripts, not a combined script, not a `pcae` CLI
subcommand, not ad hoc snippets — mirroring `scripts/
hatp_certification_admin.py`/`scripts/hatp_deployment_binding_admin.py`
exactly. This phase did not redesign that interface; no library API
defect was found that would have required it.

## Hardware Credential Admin — `scripts/hatp_hardware_credential_admin.py`

Three subcommands:

- **`enroll`** — runs a live FIDO2 CTAP2 `makeCredential` ceremony
  (`Fido2HardwareProvider.enroll_credential()`, Surface A) to mint a
  fresh credential, then registers it (`register_credential()`, Surface
  B). `signer_key_id`/`public_key`/`algorithm` are always the live
  ceremony's own output — never caller-supplied (HHCE-REQ-012, governing
  prompt §10). Confirmation happens after the ceremony (identity is not
  knowable before it) and before the registry write. `--preview` runs
  the ceremony and computes the target without writing the registry.
- **`recover`** — the named exception to "no caller-supplied identity."
  If a prior `enroll` ceremony succeeded on the physical device but the
  subsequent registry write failed, errored, or its outcome was
  uncertain, `enroll` prints the ceremony's own non-secret identity
  fields as **RECOVERY EVIDENCE** to stderr before propagating the
  error. An operator re-runs `recover` with those exact values to retry
  *only* the registry write, never re-touching the physical device
  (which would mint a second, distinct credential). This is safe by
  construction: `register_credential()`'s own `_candidate_equal`
  idempotency (HHCE-REQ-016) makes a retry with identical evidence a
  no-op if the original write actually landed, and a genuine write if
  it did not; a retry with *different* evidence for the same
  `signer_key_id` fails closed as a conflict (HHCE-REQ-017) — this
  script performs no evidence reconciliation of its own.
- **`revoke`** — `revoke_credential()`. No hardware interaction.

No `--credential-id`/`--public-key` flag exists on `enroll` (only
`recover` accepts explicit identity fields, per governing prompt §10).
No PIN, private key, or other secret device material is ever accepted
as a CLI argument or printed (HHCE-REQ-004).

### Exact core APIs consumed

`register_credential`, `revoke_credential`, `preview_register_credential`,
`preview_revoke_credential`, `CredentialEnrollmentEvidence` (all from
`pcae.core.hatp_hardware_credential_admin`); `Fido2HardwareProvider.
enroll_credential()` (lazily imported from `pcae.core.hatp_fido2_provider`,
mirroring that module's own optional-dependency discipline — `enroll`/
`--help` on `recover`/`revoke` do not require the `fido2` package to be
importable at module load time for those subcommands, only `enroll`
actually invokes the lazy import).

## Principal/Signer Admin — `scripts/hatp_principal_signer_admin.py`

Four subcommands, one core operation each: `enroll-principal`,
`revoke-principal`, `enroll-signer`, `revoke-signer` — mirroring the core
module's own four-operation writer API (HPSE-REQ-026) exactly. This
phase did not invent a single combined "enroll principal+signer"
ceremony: HPSE-001's own architecture keeps them as two independent
operations, and `enroll_signer` merely *requires* an existing active
`PrincipalRecord` rather than needing to run in the same process as the
principal's own enrollment.

The load-bearing continuous two-lock critical section this contract
requires (HPSE-REQ-057, HHCE-REQ-037: the hardware-credential-store
lock held OUTER and `.deployment-binding-transition.lock` held INNER,
continuously, across `enroll_signer`'s own precondition-check-through-
write sequence) is entirely internal to one single call to
`hatp_principal_signer_admin.enroll_signer()`. The script never
decomposes that call across multiple shell invocations, never acquires
either lock itself, and never releases/reacquires anything — it simply
invokes the one Python function that already holds both locks for its
own entire duration. Verified structurally in this phase's test suite
(`test_enroll_signer_called_exactly_once_as_a_single_function_call`).

`enroll-signer` never accepts a public-key/cryptographic-material flag:
`--signer-key-id`/`--provider-profile` name an *already-registered*
`HardwareCredentialRecord` (via the hardware-credential script's
`enroll`, run first) — the core writer re-validates that registration
live, under the lock, rather than trusting the caller's claim
(HPSE-REQ-056).

### Exact core APIs consumed

`enroll_principal`, `revoke_principal`, `enroll_signer`, `revoke_signer`,
`preview_enroll_principal`, `preview_revoke_principal`,
`preview_enroll_signer`, `preview_revoke_signer`,
`PrincipalEnrollmentEvidence`, `SignerEnrollmentEvidence` (all from
`pcae.core.hatp_principal_signer_admin`, unmodified).

## Protected Admin Authority Behavior

Real security boundary: **OS filesystem write permission** on the
hardware-credential-store root / `HATPTrustStore.production().root`,
never an in-process authority check — identical discipline to
`scripts/hatp_deployment_binding_admin.py` (HBDC-REQ-066,
HHCE-REQ-020, HPSE-REQ-029). Neither script establishes or substitutes
for that permission. `sudo` access is never treated as PCAE
authorization; there is no in-process election/authority-type check to
invent or misuse, mirroring existing precedent scripts exactly.

## Confirmation Behavior

Both scripts follow the existing `scripts/hatp_deployment_binding_admin.py`
confirmation model precisely: a preview description is always computed
and printed before any write; `--assume-yes` skips the interactive
`input()` prompt; declining (anything other than exactly `yes`) raises
`ConfirmationDeclinedError`, exits 1, and performs no write.
`--preview` computes and prints the target and returns 0 without ever
reaching the confirmation step. No unaudited `--force` flag exists.

Governance confirmation and FIDO2 user presence are deliberately never
conflated: nothing in either script interprets a successful ceremony
touch as governance approval, or vice versa — `enroll`'s confirmation
prompt is a distinct step from the CTAP2 device's own user-presence
check inside `enroll_credential()`.

## Idempotency / Conflict / Malformed-State Handling

All reused unchanged from the core writers (governing prompt §25/§26):
identical `signer_key_id`/`principal_id`/`(principal_id, signer_key_id)`
replay is idempotent; differing-field replay fails closed as a conflict;
revoked-entry re-registration/re-enrollment fails closed, never
reactivates; a malformed `hardware-credentials.json`/`registry.json`
fails every operation closed. Verified in this phase's own focused
suites (`tests/test_hatp_hardware_credential_admin_script.py`,
`tests/test_hatp_principal_signer_admin_script.py`) — the scripts add
no wrapper-specific duplicate-detection logic of their own (AST-checked:
neither script contains `json.load`/`json.dump`/`fcntl`/`mkstemp`/
`os.replace`).

## Secret Handling

Neither script accepts `--pin`/`--password`/`--private-key`/
`--bearer-token` (grepped absent from both scripts' argparse surface and
confirmed by test). Public-key material and credential IDs are printed
only where HHCE-001 defines them as public record fields
(`HardwareCredentialRecord`'s own `public_key_hex`/`signer_key_id`).
No exception text dumps a hardware-library object.

## Proof of No Real Effect

- No `DeploymentBinding` created: neither script imports or calls
  `create_deployment_binding`; `create_deployment_binding(` does not
  appear in either script's source.
- No HMIC certification action: neither script imports
  `hatp_mandatory_certification`; neither performs a certify/activate/
  revoke action.
- No hardware touched by this phase's own test suite: every FIDO2
  interaction in `tests/test_hatp_hardware_credential_admin_script.py`
  monkeypatches the script's own `_run_enrollment_ceremony` seam to a
  synthetic `EnrolledFido2Credential` — no `fido2.hid.CtapHidDevice`
  enumeration or `Ctap2` call occurs in any test.
- No real `HardwareCredentialRecord`/`Principal`/`Signer`/
  `DeploymentBinding` created on any production/protected path: every
  test uses a disposable `tmp_path` store root, injected by
  monkeypatching the script modules' own call targets — never
  `HATPHardwareCredentialStore.production()`/`HATPTrustStore.
  production()`.
- Dell (`hac-dell`) untouched: no deployment, no SSH, no remote
  invocation anywhere in this phase.

## Fresh HMIC-REQ-052 Analysis

Performed independently against current production
`hatp_mandatory_certification.py` (not merely restated from Phase
149O.20L.7O.2L's own prose — see
`tests/test_phase_149o_20l_7o_2l_1_hatp_trust_enrollment_admin_entrypoint_implementation.py::TestFreshHmicReq052Analysis`).

**Question (governing prompt §30):** if an attacker/developer modified
only one of these two new scripts while every current HMIC v1.6 frozen
member remained byte-identical, could the protected Trust-Enrollment
result change?

**Answer: YES**, for both scripts. Each is the sole, real, standalone
administrative ceremony (HHCE-REQ-020/HPSE-REQ-029) that decides *which*
`register_credential`/`revoke_credential`/`enroll_principal`/
`enroll_signer`/`revoke_principal`/`revoke_signer` call happens, with
what evidence, after what confirmation. An attacker who rewrote
`_cmd_enroll` to skip the confirmation prompt, or `recover` to accept
mismatched evidence silently, would change the protected registry's
real content without touching any currently-frozen file — both core
writer modules (`core/hatp_hardware_credential_admin.py`, `core/
hatp_principal_signer_admin.py`) are already HMIC-bound (v1.5, limb
(d)), but the scripts that are their sole intended callers are not.
This mirrors exactly the precedent already established for the other
two Protected Admin scripts, both already bound
(`scripts/hatp_certification_admin.py` at v1.1/limb (a),
`scripts/hatp_deployment_binding_admin.py` at v1.4/limb (c)) — these two
new scripts are structurally identical in kind, not merely by analogy.

## Exact Future HMIC Source-Scope Delta

`_FROZEN_AUTHORITY_BEARING_FILES` is currently exactly 36
(`_FROZEN_SRC_PCAE_RELATIVE_FILES` = 27, `_FROZEN_REPOSITORY_ROOT_
RELATIVE_FILES` = 9). Both new scripts' own import graphs were
AST-walked (not merely read) this phase:

- `scripts/hatp_hardware_credential_admin.py` imports only
  `pcae.core.hatp_hardware_credential_admin`, `pcae.core.
  hatp_hardware_credentials`, `pcae.core.hatp_providers`, and (lazily,
  inside `_run_enrollment_ceremony`) `pcae.core.hatp_fido2_provider` —
  **all four already inside `_FROZEN_SRC_PCAE_RELATIVE_FILES`**.
- `scripts/hatp_principal_signer_admin.py` imports only `pcae.core.
  hatp_bootstrap`, `pcae.core.hatp_hardware_credentials`, and
  `pcae.core.hatp_principal_signer_admin` — **all three already inside
  `_FROZEN_SRC_PCAE_RELATIVE_FILES`**.

No new, not-yet-bound transitive dependency is introduced by either
script — unlike the `paths.py` precedent Phase 149O.20L.7O.2H.2 had to
correct after an initially-missed call-graph edge, this phase's AST
analysis found the two scripts' entire reachable import surface already
inside the frozen set. **The exact expected future HMIC-REQ-050 delta is
therefore +2, both entries belonging in
`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`** (repository-root-relative,
mirroring the other two Protected Admin scripts' own existing binding
precedent, never `_FROZEN_SRC_PCAE_RELATIVE_FILES` — these scripts live
outside `src/pcae/` by design, HHCE-REQ-019/HPSE-REQ-028):

```
scripts/hatp_hardware_credential_admin.py
scripts/hatp_principal_signer_admin.py
```

Expected future `_FROZEN_AUTHORITY_BEARING_FILES` count: **38** (36 + 2).
No HMIC-001 amendment is performed in this phase — this is analysis
only, confirming 149O.20L.7O.2L's own expectation with fresh,
independent, primary-source verification.

## Impact on Current Active Certification

The currently active certification (`certification_id=
2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7`,
bound at v1.6/36-member identity) **remains a truthful, immutable,
historical record** of the source identity it was computed against —
this phase does not revoke or alter it. However, now that these two
new authority-bearing scripts exist in the Mac development repository's
source tree, the current certification **must no longer be treated as
certifying the (future, not-yet-bound) 38-member architecture** once a
future HMIC contract/source-scope evolution actually widens
`_FROZEN_AUTHORITY_BEARING_FILES` to include them. Until that future
phase lands, the two scripts are simply new, uncertified, non-agent-
reachable files — real use against production Trust-Enrollment state
requires: (1) a future HMIC-001 source-scope evolution binding both
scripts; (2) independent verification of that evolution; (3) redeployment
to `hac-dell`; (4) a new `CertificationRecord` + activation for that
newly-deployed identity; only then (5) real FIDO2 hardware enrollment.
This phase does not perform, and does not authorize, any of those five
steps.

## Focused Tests

- `tests/test_hatp_hardware_credential_admin_script.py` — 29 tests:
  `--help`, argument validation, declined confirmation, `--preview`,
  synthetic-FIDO2 success, hardware-success-then-persistence-failure
  recovery evidence, safe `recover` retry (both "original write landed"
  and "original write never landed" cases), conflicting retry, no
  duplicate record, malformed store, revoke success/idempotent/not-found/
  preview, no secret output, no unrelated protected write, no
  `--output-file`/store-root override.
- `tests/test_hatp_principal_signer_admin_script.py` — 31 tests:
  `--help`, argument validation, declined confirmation, missing
  hardware-credential precondition, missing/revoked principal, provider-
  profile mismatch, successful enroll-principal/enroll-signer/revoke-
  principal/revoke-signer, idempotent replay, conflicting existing
  principal/signer, revoked hardware credential, malformed store, no
  secret output, no `DeploymentBinding` created, no HMIC import, no
  `--output-file`/root override.
- `tests/test_phase_149o_20l_7o_2l_1_hatp_trust_enrollment_admin_entrypoint_implementation.py`
  — 28 tests: contract-text-unchanged, core-writer-unchanged, AST-verified
  import-surface closure, no-reimplemented-locking/persistence,
  continuous-two-lock-preserved (single call-site, AST-verified), no
  caller-supplied credential identity on `enroll`, fresh HMIC-REQ-052
  analysis (36 unchanged, delta = +2 = 38), no secret CLI flags.

Total: 88 new focused tests, all pass.

## Affected Regressions

`tests/test_hatp_trust_enrollment_capability.py` (100 tests, Surfaces
A-E of the core writers), `tests/test_hatp_deployment_binding_admin.py`,
`tests/test_phase_149o_20l_7o_2l_post_hmic_activation_trust_enrollment_dag.py`
(one assertion updated — the prior phase's own "scripts absent" snapshot
is superseded by this phase's own implementation, all other assertions
in that file remain true and unchanged) — all pass.

## No-Go Confirmations

- No physical FIDO2/PIV hardware was touched.
- No `HardwareCredentialRecord` was created on any production/protected
  path.
- No `Principal` was created on any production/protected path.
- No `Signer` was created on any production/protected path.
- No `DeploymentBinding` was created.
- No HMIC source scope was changed.
- No HMIC certification was performed, activated, or revoked.
- No Dell (`hac-dell`) host was redeployed or otherwise mutated.
- No HATP readiness state was changed.
- No HATP activation occurred.
- No `docs/contracts/**` file was modified.

## Recommended Next Phase

**149O.20L.7O.2L.2 — independent implementation verification** of this
phase's two new scripts against primary source (the frozen HHCE-001
v1.1/HPSE-001 v1.1 contract text, the unmodified core writer modules,
and the scripts' own actual public surface — not against this document's
own prose). If it passes: a future HMIC source-scope evolution phase to
bind both scripts (36 → 38), followed by independent verification of
that evolution, redeployment, a new `CertificationRecord`/activation for
the newly-deployed identity, and only then real FIDO2 hardware
enrollment. None of those real-effect steps are pre-authorized here.
