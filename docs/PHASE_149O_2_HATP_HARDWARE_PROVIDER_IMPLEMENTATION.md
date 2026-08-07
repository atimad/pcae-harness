# Phase 149O.2 — HATP Hardware Provider + Human-Presence Implementation (Wave 5)

## 1. Initial State

- Latest completed phase: **149O.1J** (HATP Verification Engine Independent
  Verification), commit `89bebdc0`, pushed, `origin/main..HEAD = 0`.
- Wave-4 verdict: **VERIFIED WITH NON-BLOCKING FINDINGS** — HATP Wave 4
  Verification Engine CONFORMS; readiness READY FOR WAVE 5 IMPLEMENTATION.
- HATP production: **NOT READY**. Runtime: **Observed / observe /
  unavailable**.
- `pcae health`/`pcae check`/`pcae status coherence`: healthy / passed /
  coherent. `pcae doctor task-memory`: pre-existing `tasks/DONE.md` sync
  warnings, unrelated to HATP. `pcae push check`: clean, nothing to push.
  `pcae runtime inspect`: Observed/observe/unavailable, as expected.
  `pcae phase-report show --latest` / `pcae phase-report reconcile
  --phase-id 149O.1J`: confirmed 149O.1J's canonical report consistent,
  reconciliation a no-op (mutation: none, inspection only).

## 2. Wave-5 Requirement Reconstruction

Directly re-read `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`
(HATP-001 v1.0, 117 requirements) and
`docs/PHASE_149O_1D_HUMAN_APPROVAL_TRUSTED_PROVENANCE_IMPLEMENTATION_PLAN.md`
directly, not only from 149O.1I/149O.1J's own summaries.

Wave 5 owns, per the plan's own Wave 5 section: *"`hatp_providers.py`
gains a real provider adapter (FIDO2 primary, PIV fallback per §23); a
human-side approval CLI surface (namespace TBD, §29-32)."* Requirements
implemented at the concrete-implementation level: **HATP-REQ-016..025**
(human presence, device attestation, `HATP_HARDWARE_PROVIDER_V1`
profile) and **HATP-REQ-076** (provider/signature semantics sufficiency).

| HATP-REQ | Meaning | Wave-5 owner | Implementation |
|---|---|---|---|
| 016-018 | Fresh human presence, 1:1 with proof, no session caching | Yes | `AuthenticatorData.FLAG.UP`, re-checked every `getAssertion` call; `human_presence_proven` never cached |
| 019 | `HATP_HARDWARE_PROVIDER_V1` profile properties (a)-(e) | Yes | See §4 below |
| 020 | FIDO2/PIV not interchangeable; must demonstrate signing capability | Yes | Spike documented in `hatp_fido2_provider.py` module docstring; result: FIDO2 succeeds |
| 021 | No silent software-key downgrade | Yes | No production code path constructs a software signer; enforced by `create_production_hardware_provider`'s closed factory |
| 022 | Test provider must not be production-selectable | Yes (re-confirmed) | `TestHATPProofVerifierProvider` unreferenced by any Wave-5 module (AST/grep-tested) |
| 023-025 | Device attestation semantics, trust root not self-selected | Partial | FIDO2 attestation **not implemented** this phase (documented non-blocking limitation, `attestation_valid=None`) |
| 076 | Provider/signature semantics sufficiency, no algorithm overclaim | Yes | ES256 only; no caller-selectable algorithm |

Explicitly **not** implemented this phase (Wave 6/7 territory, confirmed
by direct reading of the plan's Wave 6/7 sections):

- RAE integration (`rollback_approval_evidence.py` conditioning
  `approval_present` on `HATPVerificationResult`) — Wave 6.
- Class-B deployment provisioning, hardware-in-the-loop attack #6/#20
  closure — Wave 7.
- Credential **enrollment** (writing to any protected registry) — the
  plan explicitly defers this to a future Human/Admin-only
  administrative surface, "Wave 2/7 territory."

**Scope decision, disclosed:** the plan's Wave-5 file list also mentions
"a human-side approval CLI surface (namespace TBD, §29-32)." The plan
itself defers this interaction-design work to "Wave 5/7's actual CLI
implementation" without freezing a namespace or shape, and none of the
phase prompt's 117 required tests (items 96-117) exercise a CLI surface.
This phase deliberately narrows scope to the provider layer itself
(signing interface, verification interface, discovery, factory,
protected credential registry) and defers the CLI surface to a future
phase — a disclosed scope-narrowing decision, not a silent omission.

## 3. `HATP_HARDWARE_PROVIDER_V1` — Reconstructed From Contract Text

HATP-REQ-019: *"defined by required security properties, not by vendor
or protocol branding."* A compliant provider supports: (a) a protected,
non-exportable private key; (b) fresh human-presence enforcement per
signing operation; (c) signing/assertion over an operation-specific
payload suitable for HATP's canonical payload; (d) a stable
key/credential identity usable for enrollment; (e) verification using
independently trusted public/provider material that does not originate
from the proof itself.

No concrete algorithm, wire format, or provider identifier string beyond
`HATP_HARDWARE_PROVIDER_V1` itself is frozen by the contract — this
phase's FIDO2 and PIV adapters both legitimately claim that same profile
string; the Wave-2 trust store's per-signer `provider_profile` field
remains the authoritative binding, not a protocol tag.

## 4. FIDO2 Primary / PIV Fallback — Spike Result

`docs/PHASE_149O_1D...`'s §23 stop condition: *"if the FIDO2 spike
cannot bind HATP's exact canonical payload as the signed challenge,
switch to the PIV fallback strategy before continuing."*

**Spike result: FIDO2 succeeds.** Confirmed directly against the
installed `fido2` 1.2.0 library's own source (not assumed):

- `fido2.ctap2.base.AssertionResponse.verify()` computes
  `public_key.verify(self.auth_data + client_param, self.signature)`
  where `client_param` is `sha256(clientDataJSON)` — the real WebAuthn
  signed-data structure is `authenticatorData || SHA-256(clientDataJSON)`.
- `fido2.webauthn.CollectedClientData.create(type, challenge, origin,
  ...)` accepts an arbitrary caller-supplied byte string as `challenge`,
  embedded into `clientDataJSON`.

This module (`hatp_fido2_provider.py`) binds
`sha256(canonicalize_hatp_proof_payload(proof))` as that `challenge`.
Any change to the canonical payload changes the digest, changes
`clientDataJSON`, changes its SHA-256 hash, and invalidates the
signature over `authenticatorData || client_param` — a genuine,
byte-exact binding, independently exercised by this phase's test suite
(`test_provider_evidence_binds_full_canonical_bytes_not_a_truncation`,
`test_wrong_payload_fails`, `test_presence_from_operation_a_cannot_satisfy_operation_b`).

Because the FIDO2 spike succeeded, PIV was **not required** to reach
full conformance this phase (149O.1D §23's conditional wording: "PIV as
the documented fallback if that spike fails"). `hatp_piv_provider.py`
therefore implements PIV's structural interface only — every method
unconditionally reports/raises unavailability, honestly, per items
56-57/137 ("PIV fallback may be structurally unavailable rather than
silently accepted... do not weaken HATP to make fallback pass"). No
`pyscard`/`python-pkcs11` dependency was added; none exists in this
environment.

## 5. Root-1 (Non-Exportable Key, Fresh Presence) Mapping

- **Non-exportable key:** CTAP2 authenticators never expose the private
  key over any documented command. `hatp_fido2_provider.py` has no code
  path that requests, receives, or constructs a private key on the
  verification side; `request_signature()` never accepts one as a
  parameter — signing happens entirely inside the physical device via
  `Ctap2.get_assertion`.
- **Fresh human presence:** mapped to `AuthenticatorData.FLAG.UP` ("User
  Present"), read via `AuthenticatorData.is_user_present()`. Per item 51
  ("do not confuse UP with UV unless HATP-001 requires one or both"):
  HATP-001's text says "human-presence," not "user verification"/
  biometric, so this module requires UP only, not UV. CTAP2
  authenticators re-evaluate UP on every `getAssertion` call — there is
  no "unlock once, sign many" caching at this layer (HATP-REQ-017); no
  code in this module caches or reuses a prior presence result.

## 6. Provider Capability Matrix (Item 58)

| Capability | FIDO2 | PIV |
|---|---|---|
| Non-exportable key | Yes (CTAP2 hardware guarantee) | No (not implemented) |
| Fresh touch per operation | Yes (UP flag, re-checked per call) | No (not implemented) |
| Credential identity | Yes (raw credential-id bytes, hex-encoded `signer_key_id`) | No (not implemented) |
| Signature verification | Yes (real ECDSA/COSE via `cryptography`+`fido2.cose`) | No (not implemented) |
| Device attestation | **No** (not implemented this phase — documented limitation) | No (not implemented) |
| Provider profile | Yes (`HATP_HARDWARE_PROVIDER_V1`) | Yes (interface only) |
| HATP-conformant | **CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS** (missing attestation) | **NOT_CONFORMANT** (structurally deferred this phase) |

## 7. Exact Signed-Byte Source

`request_signature(payload, ...)` receives `payload` from the caller as
the exact `canonicalize_hatp_proof_payload(proof)` bytes (Wave 3's
existing function, reused verbatim — never reconstructed). This module
computes `challenge = sha256(payload)` itself and never accepts a
caller-supplied pre-digested value. On the verification side,
`verify(canonical_payload=..., ...)` receives the same exact bytes from
`verify_hatp_proof` (Wave 4, unmodified) and independently recomputes
`sha256(canonical_payload)` to compare against the challenge embedded in
the assertion's `clientDataJSON`. No second canonicalizer exists
anywhere in this module.

## 8. Credential Identity / Non-Exportability

`signer_key_id` for a FIDO2 credential is the raw WebAuthn credential ID,
hex-encoded. `credential_identity()` reports `HATPProviderUnavailableError`
in this environment (no device with a discoverable/resident credential
present) — a stable identity for a non-resident credential can only be
established at enrollment time (explicitly Wave 2/7 territory, not
re-derivable from the device alone, and this phase does not implement
enrollment). Non-exportability is a CTAP2 protocol guarantee (verified
against the installed library's documented command surface, not merely
"PCAE exposes no export function" — see item 11's exact caution, honored
here: this module never claims non-exportability based on the absence of
its own export API).

## 9. Human-Presence Mechanism

See §5 above. `human_presence_proven` in every `HATPProviderVerificationOutcome`
this module returns is set from `AuthenticatorData.is_user_present()`,
computed fresh per `verify()` call from the assertion's own signed
`authenticatorData` bytes — never a caller-supplied boolean (item 17: no
`human_present=True`/`user_presence=True` parameter exists anywhere in
this module's public interface, confirmed by
`test_no_production_code_path_accepts_a_private_key_parameter`-style AST
scanning for suspicious names, and by direct interface-signature
inspection).

## 10. Attestation Semantics

**Not implemented this phase.** `verify()` always returns
`attestation_valid=None`, meaning (per the existing, Wave-4-defined
contract on `HATPProviderVerificationOutcome.attestation_valid`) "this
provider profile does not perform/require device attestation" — Wave 4
treats `None` as non-blocking. This is why `capabilities().hatp_conformant`
reports `CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS`, not `CONFORMANT`.
Root 2A (device/provider genuineness) therefore remains substantively
unimplemented; a future phase would add vendor attestation-object
validation (AAGUID / attestation-statement verification against a
vendor-provided trust anchor, itself never sourced from the proof, the
caller, an environment variable, a CLI flag, or unprotected repository
state — item 22-24).

## 11. Provider Discovery

`discover_hardware_providers()` (in `hatp_providers.py`) reports
availability facts only — library presence and a raw enumeration count —
never trust, never a readiness claim. On this development machine:
FIDO2 library **is** installed (`fido2` 1.2.0), **zero** FIDO2 devices
detected (`CtapHidDevice.list_devices()` returns empty); PIV has no
library installed and reports unavailable unconditionally. These are
genuine, honestly-observed environment facts, not fabricated (item 89).

## 12. Dependency Strategy

New optional extra `pcae-harness[hatp-hardware]` in `pyproject.toml`:
`fido2>=1.1,<2` (pulls in `cryptography<45` transitively, so
`cryptography>=42,<45` is pinned to stay compatible rather than
independently constrained). Neither dependency is in the base
`dependencies` list — ordinary PCAE installs are unaffected. Verified
compatible with `requires-python = ">=3.9"` (installed and exercised
under this repository's own `.venv`, Python 3.9.6). No hard import of
either library exists in `hatp_providers.py`, `hatp_hardware_credentials.py`,
or any other core module — only `hatp_fido2_provider.py` imports them,
and it is imported lazily, only from inside
`discover_hardware_providers()`/`create_production_hardware_provider()`.
Missing-dependency behavior: `discover_hardware_providers()` catches
`ImportError` and reports `library_installed=False`; it never crashes
PCAE's ordinary import/use (items 63-65, independently confirmed by
`test_discover_hardware_providers_reports_honest_facts` and by
`hatp_providers.py`/`hatp_hardware_credentials.py` importing cleanly with
neither optional package installed, verified at the start of this
phase's implementation work before either was installed).

## 13. Failure Behavior

`request_signature()` maps: no device found →
`HATPProviderUnavailableError`; `CtapError` with
`ACTION_TIMEOUT`/`KEEPALIVE_CANCEL`/`USER_ACTION_TIMEOUT` →
`HATPProviderCancelledError`; any other `CtapError` or transport
exception → `HATPProviderDeviceError`. `verify()` never raises for a
structurally invalid/unrecognized assertion (malformed JSON, unknown
schema version, unknown field, wrong credential, unknown credential,
revoked credential, wrong profile, bad signature) — it returns
`signature_valid=False` instead, exactly matching
`HATPProofVerifierProvider.verify`'s existing (Wave-4-frozen) contract.
A genuine registry failure (malformed/symlinked/unreadable credential
store) propagates as an exception, which Wave 4's existing broad
`except Exception` maps to `INVALID_SIGNATURE` — fail-closed, never a
silent pass.

## 14. Evidence Serialization

Strict, closed, versioned JSON schema (`_EVIDENCE_SCHEMA_VERSION = 1`,
fields `version`/`credential_id_hex`/`authenticator_data_hex`/
`client_data_json_hex`/`signature_hex`, hex-encoded binary fields).
Unknown fields, missing fields, unknown version, duplicate JSON object
keys, and non-UTF-8/non-JSON garbage all fail closed to
`signature_valid=False` (never raise) — independently tested
(`test_evidence_rejects_unknown_field`,
`test_evidence_rejects_missing_field`,
`test_evidence_rejects_unknown_version`,
`test_evidence_rejects_duplicate_json_keys`,
`test_evidence_rejects_non_json_garbage`,
`test_verify_never_raises_for_malformed_assertion`).

## 15. Protected Hardware-Credential Registry

New module `hatp_hardware_credentials.py`: a provider-owned, read-only,
protected registry mapping `signer_key_id` → enrolled public-key
material (`HardwareCredentialRecord`), needed because Wave-2's
`SignerRecord` carries identity-binding facts only, no raw crypto key
material, and Wave 2 is out of scope to modify (item 131). This module
deliberately does **not** import `hatp_bootstrap.py` (independently
verified by `test_hatp_hardware_credentials_does_not_import_hatp_bootstrap`),
mirroring `hatp_bootstrap.py`'s own documented dependency-direction
discipline. It duplicates (never imports) the same fixed-platform-path,
symlink-rejection, and duplicate-JSON-key-rejection discipline
`hatp_bootstrap.py` established for the Wave-2 trust store. No
`enroll()`/`grant()`/`revoke()`/`rotate()` production API exists — only
`lookup_credential()`, read-only, exactly mirroring `HATPTrustStore`.

## 16. Test-Provider / Software-Key Containment

`TestHATPProofVerifierProvider` is referenced by name only inside its
own defining module (`hatp_providers.py`) — confirmed both by this
phase's own tests and by the pre-existing Wave-4/149O.1J tests, which
continue to pass unmodified (a docstring reference this phase
accidentally introduced into `hatp_fido2_provider.py` was found and
removed during this phase's own regression pass — see §21). No AST-
detectable name resembling `private_key`/`priv_key`/`pem_key`/
`software_key` exists anywhere in the four Wave-5 modules
(`test_no_production_code_path_accepts_a_private_key_parameter`).
`request_signature()`'s only path to producing evidence is a real
`Ctap2.get_assertion()` call — no `generate_private_key`/in-process
`.sign()` call exists in that method
(`test_fido2_provider_signing_path_has_no_software_fallback`).
`create_production_hardware_provider` never imports or returns
`TestHATPProofVerifierProvider` (source-inspected with docstrings/
comments stripped, not merely grepped).

## 17. Real-Device Test Status

**REAL HARDWARE NOT EXERCISED.** This development machine has zero
attached FIDO2 or PIV devices (`system_profiler SPUSBDataType` grep for
`yubikey|fido|security key` returns nothing; `discover_hardware_providers()`
independently confirms `device_detected=False` for both protocols). One
test (`test_real_device_sign_and_verify_round_trip`, marked
`@pytest.mark.hatp_hardware_required`) exists as a structural placeholder
for a real device and is `skipif`-skipped, never fabricated as passing.
Every other test in the new suite exercises real WebAuthn/CTAP2 data
structures (`fido2.webauthn.AuthenticatorData`/`CollectedClientData`)
and real ECDSA cryptography (`cryptography.hazmat.primitives.asymmetric.ec`,
`fido2.cose.ES256`) signed with a test-only, never-enrolled, in-memory
key — genuine cryptographic verification logic, not a fabricated
mock-always-succeeds stub. This methodology surfaced and fixed a real
bug during development: an initial `is_user_present` implementation
accessed a bound method without calling it (always truthy); the
deterministic real-crypto round-trip test caught this immediately,
which a hand-wavy mock would not have.

## 18. Substrate Readiness / Operational Hard Ceiling

`inspect_hatp_verification_substrate_readiness` (Wave 4,
`human_approval_trusted_provenance.py`) was **not modified** this phase.
`provider_profile_available`/`provider_attestation_trusted` remain
permanently hardcoded `False` in that function; `operational` remains
`False` even with the FIDO2 library installed and a real credential
enrolled in a test registry — independently confirmed by
`test_fido2_library_installed_does_not_flip_substrate_operational`. This
is a deliberate, disclosed choice: 149O.1D's plan states *"Waves 1-6
cannot activate production trust; only Wave 7 independent verification +
Class-B deployment provisioning can make HATP_TRUSTED_OPERATIONAL
achievable."* Provider availability is reported as a fact via the new,
separate `discover_hardware_providers()` (Wave-5-owned), not by touching
Wave 4's ceiling function.

## 19. Regression Results

All commands actually re-run this phase (not assumed):

| Suite | Result |
|---|---|
| `test_hatp_verification_engine.py` (Wave-4 own suite) | 59 passed (exact match to 149O.1I/149O.1J's claim) |
| `test_repository_identity.py` + `test_hatp_bootstrap_foundation.py` (Wave 1/2) | 40 passed |
| `tests/ -k "hatp or 149o_1 or 149o_2"` | 1376 passed, 3 skipped, 91 failed (identical failure set to unmodified `main` under the same selection, confirmed via `git stash`; all pre-existing, environment/timezone-dependent, unrelated to this phase) |
| New Wave-5 suite (`test_phase_149o_2_...py`) | 62 passed, 1 skipped (real-hardware placeholder) |
| Report-trust (`test_phase_reports.py` + 2 more) | 186 passed, 1 failed (pre-existing, confirmed identical on unmodified `main` — a stateful test interacting with live `.pcae/` state) |
| Permission Broker (`-k permission_broker`, `-n auto`) | 978 passed, 1 failed (pre-existing false positive from `hatp_bootstrap.py`'s own docstring prose, unrelated — same finding 149O.1I/149O.1J recorded) |
| RAE canonical-provenance suite | 1 passed, 16 failed — differs from 149O.1J's recorded "4 failed/13 passed"; **confirmed identical (16 failed/1 passed) on unmodified `main` via `git stash`**, so unrelated to this phase; the discrepancy from 149O.1J's number is environment-dependent and not investigated further per item 124 ("do not repair") — B-149O-1..4 remain OPEN, unaffected |
| Fast Green (`-m fast_green -n auto`) | **4652 passed, 1 skipped, 0 failed** (baseline 4590 + this phase's 62 new tests, 61 counted + 1 skip) |
| `test_agent.py` (single-process, per 149O.1J's documented xdist-stall workaround) | 4236 passed, 0 failed (exact match to 149O.1J's claim); independently re-confirmed no Wave-5 symbol is referenced by `agent.py`/`commands/agent.py` |

Two pre-existing diff-scope guard tests
(`test_phase_149o_1e_hatp_repository_identity_trust_store_foundation.py::test_only_expected_production_files_changed`,
`test_phase_149o_1g_hatp_proof_models_canonical_serialization.py::test_only_expected_production_files_changed`)
were widened to account for this phase's three new files
(`hatp_fido2_provider.py`, `hatp_piv_provider.py`,
`hatp_hardware_credentials.py`), mirroring this project's own documented
allowed-file-widening precedent for 149O.1G's and 149O.1I's entries.

## 20. Findings

- **NON-BLOCKING**: FIDO2 device attestation (Root 2A) is not
  implemented this phase. `capabilities().device_attestation == False`,
  `hatp_conformant == CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS`,
  `attestation_valid` always `None`. Wave 4 treats `None` as
  non-blocking by existing (unmodified) contract. Recommended follow-up:
  a future phase implementing vendor attestation-object validation.
- **NON-BLOCKING**: PIV fallback is structurally deferred
  (`NOT_CONFORMANT`, this phase) — the FIDO2 spike succeeded, so PIV was
  not required; no PKCS#11/smart-card dependency exists in this
  environment. Documented, not silently accepted (item 56/57/137).
- **NON-BLOCKING**: `credential_identity()` always raises
  `HATPProviderUnavailableError` in this environment (no discoverable
  credential on any attached device, and none attached at all) —
  expected given zero hardware and no enrollment surface this phase.
- **DEFERRED**: the plan's "human-side approval CLI surface" was
  disclosed and deliberately deferred (§2 above), not silently dropped.
- 149O.1J's retained diagnostic-precision finding (unenrolled-repository
  replay resolving to `UNAUTHORIZED_SIGNER` instead of `WRONG_REPOSITORY`)
  was **not repaired** this phase, per explicit instruction — Wave 5
  exposed no new security-relevant ambiguity around it.

## 21. Development-Time Corrections (Disclosed, Not Hidden)

Two mistakes were found and fixed during this phase's own implementation
work, before any commit:

1. `AuthenticatorData.is_user_present` is a **method**, not a property;
   an early draft of `verify()` accessed it without calling it, which is
   always truthy for a bound method object — silently defeating the
   presence check. Caught immediately by a real-cryptography round-trip
   test asserting `human_presence_proven is False` for a UP-unset
   assertion; fixed before any other test was written against it.
2. `hatp_fido2_provider.py`'s original docstring mentioned
   `TestHATPProofVerifierProvider` by name, which broke a pre-existing
   149O.1J test (`test_test_provider_not_referenced_outside_its_own_module`)
   asserting that name appears nowhere outside `hatp_providers.py`.
   Reworded to describe the same fact (`Protocol` structural typing)
   without naming the class.

## 22. Wave-5 Implementation Verdict

**HATP WAVE 5 HARDWARE PROVIDER IMPLEMENTED — READY FOR INDEPENDENT
VERIFICATION.**

No Blocking finding (per the phase prompt's own Blocking-condition list,
item 136) was produced: no software-exportable key accepted as
production evidence; no caller-supplied presence boolean; no presence
replay across payloads (independently tested); no proof self-selecting
its own trusted key/provider/root; test provider unreachable from the
production factory; hardware provider signs/verifies only the exact
Wave-3 canonical payload's digest; wrong/unknown credential rejected;
provider availability does not flip `operational`; no `approval_present`
derivation; no RAE/PB/agent wiring; canonicalization unchanged; no
Class-B deployment assumed; hardware absence does not crash ordinary
PCAE import/use; the new optional dependency does not affect non-HATP
installs.

## 23. HATP Production Readiness

**HATP PRODUCTION: NOT READY.** Wave 5 does not authorize production
activation. `HATP_TRUSTED_OPERATIONAL` remains unreachable — Wave 4's
hard ceiling (`inspect_hatp_verification_substrate_readiness`) was not
modified and its `assert operational is False` remains intact. Runtime
remains Observed / observe / unavailable.

## 24. Recommended Next Phase

**149O.3 — HATP Hardware Provider Independent Verification.** Should
independently attack: the hardware-backed-key property claim,
fresh-touch-per-operation enforcement, provider-profile binding,
credential binding, the (currently absent) attestation path, payload
byte-exactness, replay across every named dimension, test-provider
isolation, optional-dependency behavior, and the operational-readiness
hard ceiling — exactly the same rigor 149O.1J applied to Wave 4.
