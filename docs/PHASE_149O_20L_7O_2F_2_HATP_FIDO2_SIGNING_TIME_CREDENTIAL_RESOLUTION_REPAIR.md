# Phase 149O.20L.7O.2F.2 — FIDO2 Signing-Time Credential Resolution Repair

## 1. Entering State / Phase-Entry Commit

Phase-entry commit: `55d7ca8b` (Phase 149O.20L.7O.2F.1: close task,
transition to idle). Entering verdict: Phase 149O.20L.7O.2F.1
(Independent Verification) found the Trust-Enrollment implementation
capability (149O.20L.7O.2F, Surfaces A-E) **BLOCKED** with two Blocking
findings:

- **BF-1.** Production signing (`hatp_signing_ceremony.py::
  sign_rollback_evidence` → `_resolve_signer`) depended unconditionally
  on `provider.credential_identity()`; `Fido2HardwareProvider.
  credential_identity()` unconditionally raises `HATPProviderUnavailableError`.
  No enrolled FIDO2 signer could ever reach production signing.
- **BF-2.** `Fido2HardwareProvider.enroll_credential()`'s CTAP2
  `make_credential` call requests no `rk`/resident-key option, producing
  a non-resident credential — a structural mismatch against
  `credential_identity()`'s own resident-credential assumption.

Surfaces B, C, D, E were independently verified clean by 149O.20L.7O.2F.1
and are not reopened here except for regression re-confirmation.

## 2. Primary-Source Reconstruction

Read directly (not from prior-phase prose) before any change:
`docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`
(HSCE-001 v1.1), `docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md`
(HPSE-001 v1.1), `docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md`
(HHCE-001 v1.1), `src/pcae/core/hatp_signing_ceremony.py`,
`src/pcae/core/hatp_fido2_provider.py`, `src/pcae/core/hatp_hardware_credentials.py`,
`src/pcae/core/hatp_hardware_credential_admin.py`,
`src/pcae/core/hatp_principal_signer_admin.py`, `src/pcae/core/hatp_bootstrap.py`,
`src/pcae/core/human_approval_trusted_provenance.py`, and the actual
`pcae hatp sign rollback` command path
(`src/pcae/commands/hatp.py::run_hatp_sign_rollback` →
`production_sign_rollback_evidence` → `sign_rollback_evidence`).

## 3. BF-1 Re-derivation

Confirmed exact production path: `run_hatp_sign_rollback`
(`src/pcae/commands/hatp.py`) calls
`production_sign_rollback_evidence(root, site=site, job_id=..., per_id=...)`
with zero overrides, which calls `sign_rollback_evidence` with every
default in place. Prior to this repair, `sign_rollback_evidence` called
`_resolve_signer(trust_store, provider)`, whose entire body was:

```python
signer_key_id = provider.credential_identity()
```

unconditional — no branch, no fallback. `Fido2HardwareProvider.
credential_identity()` (`hatp_fido2_provider.py:307-313`) is:

```python
def credential_identity(self) -> str:
    raise HATPProviderUnavailableError(...)
```

also unconditional, independent of device presence. BF-1 confirmed
exactly as 149O.20L.7O.2F.1 found it, re-derived from current source, not
from prior-phase prose.

## 4. BF-2 Re-derivation

`Fido2HardwareProvider.enroll_credential()`'s CTAP2 call site
(`hatp_fido2_provider.py`, `enroll_credential`):

```python
attestation = ctap2.make_credential(
    client_data_hash=client_data_hash,
    rp=_HATP_RP,
    user=user,
    key_params=key_params,
)
```

No `options` argument at all — CTAP2 `authenticatorMakeCredential`
defaults `rk` (resident key) to `false` when the `options` map, or its
`rk` member, is absent. The credential this ceremony mints is therefore
non-resident (non-discoverable) by construction. `credential_identity()`'s
own (pre-repair) docstring explicitly required "a live CTAP2 device with
a discoverable/resident credential" — confirmed independently as a
structural mismatch, not merely a documentation gap. BF-2 confirmed
independently of BF-1.

## 5. Architecture Decision

Both Model A (authenticator rediscovery) and Model B (durable-registry
signer resolution) were evaluated against HSCE-001 compatibility, CTAP2
support, multiple-credential/multiple-signer behavior, deterministic
identity, testability, recovery, and the blind-touch-defense requirement.
Full analysis: `docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`
§46 ("Model evaluated and rejected: Model A" / "Model selected: Model B").

**Selected: Model B — durable-registry signer resolution.**
`HATPTrustStore`'s existing `DeploymentBinding` (HATP-REQ-057-063,
frozen, unamended) already binds exactly one
`(principal_id, signer_key_id, provider_profile)` tuple to exactly one
`(repository_id, canonical_deployment_root)` pair — the durable,
non-hardware-derived signer-identity source Model B needs, already
present and already unique-by-construction (one `DeploymentBinding` per
`repository_id` in the registry's own dict-keyed storage). Model A was
rejected primarily because it requires a live hardware touch merely to
discover *who* is signing, in direct tension with HSCE-REQ-071's
blind-touch defense (the full preview, including `principal_id`/
`signer_key_id`, must be shown *before* any hardware touch) — Model B's
resolution is fully pre-touch by construction.

## 6. Contract Amendment

HSCE-001 amended in place, **v1.1 → v1.2**
(`docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`, new
§46/§47). Changed: HSCE-REQ-018's table row for `principal_id`/
`signer_key_id`, HSCE-REQ-024, one HSCE-REQ-047 table cell's wording,
HSCE-REQ-078's count. Added: HSCE-REQ-080 (six-step signer-resolution
order), HSCE-REQ-081 (multiple-signer determinism via
`DeploymentBinding` uniqueness), HSCE-REQ-082 (authority distinction:
registry resolves identity, hardware proves possession — never
substituted for each other), HSCE-REQ-083 (TOCTOU recheck extended to
signer identity), HSCE-REQ-084 (`credential_identity()`'s explicit
non-required-method disposition). No requirement renumbered or removed.
No other HATP contract touched — HATP-001, RAE-001, HPSE-001, HHCE-001
all remain byte-unchanged.

## 7. Exact Signing-Resolution Flow (Post-Repair)

`sign_rollback_evidence` → `_resolve_deployment_binding_signer(root,
trust_store, repository_id=context_a.repository_id,
provider_profile=HATP_HARDWARE_PROVIDER_V1,
hardware_credential_store_factory=...)`:

1. `resolve_canonical_deployment_root(Path(root.path))`.
2. `trust_store.resolve_deployment_authorization(repository_id=...,
   canonical_deployment_root=...)` → `DeploymentBinding` or
   `no_authorized_signer`.
3. `binding.provider_profile` must equal the resolved production
   provider profile (`HATP_HARDWARE_PROVIDER_V1`).
4. `trust_store.lookup_signer(binding.signer_key_id)` must be `active`.
5. `trust_store.lookup_principal(binding.principal_id)` must be `active`.
6. `hardware_credential_store.lookup_credential(binding.signer_key_id)`
   must be `active` with a matching `provider_profile`.

Every step above completes before any hardware touch. The hardware
provider's `request_signature(payload, signer_key_id=..., provider_profile=...)`
(unchanged) is still called exactly once, still requires a fresh
per-operation physical touch, and its output is still independently
verified at consumption time against the durable `HardwareCredentialRecord`'s
public key (HATP-001 §21-22, unchanged) — the registry never substitutes
for hardware possession proof (HSCE-REQ-082).

A new TOCTOU extension (HSCE-REQ-083) re-runs steps 1-6 a second time,
immediately before publication, and discards the signed candidate
(`evidence_serialization_failure`) if the resolved `(principal_id,
signer_key_id)` pair differs from the pre-touch snapshot — closing a race
this repair's own model change would otherwise introduce (a
`DeploymentBinding` rotation landing mid-ceremony).

## 8. Multiple-Signer Behavior

Fully determined by `DeploymentBinding`'s own existing structural
uniqueness (unamended): at most one `DeploymentBinding` per
`repository_id`, enforced at the writer layer
(`create_deployment_binding` → `DuplicateConflictingBindingError` on a
second attempt for the same repository). There is no "pick one of
several" step in the repaired resolver — no `--signer` flag was added,
none was needed. Confirmed directly by
`test_attack_multiple_active_signers_each_repository_resolves_only_its_own`
(two fully-enrolled signers, two repositories, each repository resolves
only its own).

## 9. Provider API Changes

**None.** `Fido2HardwareProvider.request_signature()` already accepted
an explicit `signer_key_id` parameter and used it as CTAP2
`get_assertion`'s `allow_list` credential id — it never depended on
resident-credential discovery. No new provider method was needed; the
entire repair is confined to `_resolve_deployment_binding_signer`'s
*source* of `signer_key_id` (a registry read, replacing a hardware
call).

## 10. FIDO2 Enrollment Compatibility

`enroll_credential()` is unchanged. BF-2 is closed structurally, not by
repairing residency: the production signing path never performs
resident-credential discovery under Model B, so `enroll_credential()`'s
non-resident output is not a defect relative to HSCE-001 v1.2's actual
resolution mechanism. `credential_identity()` remains an unconditional
raise, explicitly disposed of by HSCE-REQ-084 as a structural
`HATPHardwareSigner`-adjacent method no current production code path
(enrollment or signing) calls for FIDO2 — not a dead required method
left without disposition.

## 11. Production-Path End-to-End Test

`tests/test_phase_149o_20l_7o_2f_2_hatp_fido2_signing_time_credential_resolution_repair.py::
test_full_production_signing_path_with_synthetic_fido2_credential`:
synthetic FIDO2 enrollment (real `enroll_credential()`, monkeypatched
CTAP2 transport only) → `register_credential` (Surface B) →
`enroll_principal`/`enroll_signer` (Surface C) →
`create_deployment_binding` (Surface E) → the real, injectable
`ceremony.sign_rollback_evidence` orchestrator (not a direct
`_resolve_deployment_binding_signer` call) with a synthetic hardware
touch → published `HATPSignedEvidenceEnvelope`. Asserts the provider's
`credential_identity()` was never called and the provider received
exactly the enrolled credential's own `signer_key_id`.

## 12. BF-1 Repair Result

**REPAIRED — INDEPENDENT VERIFICATION PENDING.**
`test_bf1_repro_credential_identity_still_unconditionally_raises`
reproduces the original symptom against the real provider class.
`test_bf1_repaired_enrolled_signer_reaches_signing_resolution` and the
full end-to-end test above demonstrate the same enrolled signer now
reaches signing-time resolution successfully, via the real production
orchestrator, without any call to `credential_identity()`.

## 13. BF-2 Repair Result

**REPAIRED (MOOT) — INDEPENDENT VERIFICATION PENDING.**
`test_bf2_repro_enroll_credential_requests_no_resident_key` reproduces
the original finding (still no `rk`/`options`). `test_bf2_moot_non_resident_credential_remains_fully_valid_for_signing`
and the end-to-end test demonstrate the non-resident credential
`enroll_credential()` produces remains fully valid for the entire
production signing path. No ambiguous halfway state: FIDO2's
`credential_identity()` is cleanly and permanently out of the production
path (HSCE-REQ-084).

## 14. B-E Regression Result

`tests/test_hatp_trust_enrollment_capability.py` (Surfaces A-E focused/
adversarial), `tests/test_hatp_deployment_binding_admin.py` (Surface E),
`tests/test_hatp_bootstrap_foundation.py`: all green, unmodified by this
phase. HHCE idempotency/revocation, the continuous two-lock section,
`PrincipalRecord.revoked_at`, and `DeploymentBinding` cross-validation
were not altered.

## 15. Security Attacks

Covered in `tests/test_hatp_signing_ceremony.py` and
`tests/test_phase_149o_20l_7o_2f_2_...py`: multiple active signers
(cross-repository isolation), wrong credential (never bound to this
repository), wrong principal (revoked-principal fail-closed), revoked
signer, revoked credential, provider mismatch (both at the
`DeploymentBinding` level and the `HardwareCredentialRecord` level),
missing credential, stale registry state (TOCTOU signer-identity
rotation, HSCE-REQ-083), duplicate credential (writer-layer conflict,
unweakened), authenticator returns unexpected credential (`verify()`'s
existing `credential_id` mismatch check, unweakened), signing device
unavailable / cancelled FIDO2 operation / malformed public key /
replayed request (all pre-existing, unweakened, re-confirmed passing).
All fail closed.

## 16. Fast Green

`.venv/bin/python -m pytest -m fast_green` — see governance metadata for
the exact node count executed as part of this phase's `pcae phase
complete` gate; the newly-added/modified files
(`hatp_signing_ceremony.py`, `hatp_fido2_provider.py`,
`test_hatp_signing_ceremony.py`, `test_phase_149o_12c_hsce_attack_matrix.py`,
`test_phase_149o_13_hatp_signing_ceremony_evidence_store_independent_verification.py`,
`test_phase_149o_20l_7o_2f_2_...py`) are fully covered.

## 17. Regression Attribution Methodology

Full `-k hatp` suite run twice: once against phase-entry commit
`55d7ca8b` (`git stash push -u`), once against this phase's working
tree, using the repository's real `.venv` interpreter (Python 3.9,
`fido2`/`cryptography` extras installed) rather than the ambient
homebrew interpreter (which lacks the optional `hatp-hardware` extra and
cannot even collect the FIDO2-dependent test modules). Baseline: 195
failed / 3360 passed. This phase: 220 failed / 3345 passed (Surface
count differs because this phase's own new test file adds passing
nodes and several pre-existing failures are Surface-adjacent). Exact set
diff (`comm -13`/`comm -23` on sorted `FAILED`/`ERROR` lines): 25 net-new
failures, zero net-fixed. All 25 net-new failures independently
inspected: every one is a "byte-identical since phase entry" / "no
production source changed since phase X" / "`_resolve_signer` still
exists" pinned-baseline self-check in a *historical* phase's own test
file, tripped because this phase legitimately and disclosedly modifies
`hatp_signing_ceremony.py`, `hatp_fido2_provider.py`, and the HSCE-001
contract file for the first time since those historical phases' own
entry commits — the same "repin-debt, not flaky" class of self-check
failure this repository's own accumulated project memory already
documents for prior contract-touching phases. Zero net-new *functional*
regressions in HATP business logic were found. The one additional
initially-suspicious failure
(`test_pcae_cli_health_and_check_work_with_no_device_attached`) was
independently confirmed to be `pcae health`'s own governed-task-scope
gate reacting to this phase's own not-yet-committed working tree, not a
code defect.

## 18. HMIC Source-Scope Impact

This repair modifies `hatp_signing_ceremony.py` (production source) and
the HSCE-001 contract file. `hatp_fido2_provider.py` was touched only for
documentation/comment clarification (no behavioral line changed —
`enroll_credential`/`request_signature`/`verify`/`credential_identity`
bodies are byte-identical). HMIC (`HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`)
is **not amended by this phase** (no authorization was given, per the
governing prompt). **Exact required future source-scope effect:** any
future HMIC frozen-source-set enumeration that includes
`hatp_signing_ceremony.py` and/or `docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`
in its pinned baseline will need its own pinned baseline advanced past
this phase's commit before it can pass again — this is the same
"repin-debt" class this phase's own regression-attribution analysis
(§17) already found and disclosed, not a new category of debt. No HMIC
text is touched, and no certification/activation claim is made or
implied by this phase.

## 19. No Real Hardware / No Dell Mutation / Runtime Unchanged

No real FIDO2 hardware was provisioned. No real credential was
registered. No real principal or signer was enrolled. No real
`DeploymentBinding` was created. `hac-dell` was not touched. No election
was initiated. No CHGR was published. HMIC was not certified. HATP was
not activated. Runtime capability is unchanged: State: Observed, Maximum
Capability: observe, Execution Availability: unavailable — identical
before and after this phase.

## 20. Final Verdict

**FIDO2 SIGNING-TIME CREDENTIAL RESOLUTION REPAIRED — INDEPENDENT
VERIFICATION PENDING.** BF-1 and BF-2 are each marked REPAIRED —
INDEPENDENT VERIFICATION PENDING, not self-closed.

## 21. Next Phase

Recommended: **149O.20L.7O.2F.3 — FIDO2 Signing-Time Credential
Resolution Repair Independent Verification**, narrowly scoped per
HSCE-001 §47. Not authorized by this phase; not begun.
