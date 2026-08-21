# Phase 149O.20L.7O.2N.7 Completion Report

**Verdict:** REMOTE WEBAUTHN PROVIDER CONTRACT FROZEN — HYBRID
LOCAL-CTAP + REMOTE-WEBAUTHN ARCHITECTURE SELECTED — MULTI-AUTHENTICATOR
MODEL SUPPORTED BY EXISTING REGISTRY / ADDITIVE POLICY ONLY —
RP-ID/ORIGIN MODEL RESOLVED (as an explicit infrastructure requirement,
no literal hostname selected) — REMOTE REGISTRATION ARCHITECTURALLY
SUPPORTED — REMOTE SIGNING SUPPORTED VIA NEW PROVIDER-SPECIFIC ASSERTION
PROFILE — NO REAL CREDENTIAL CREATED.
See docs/PHASE_149O_20L_7O_2N_7_REMOTE_WEBAUTHN_PROVIDER_CONTRACT_AND_
CEREMONY_ARCHITECTURE_FREEZE.md for the full phase report and
docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md (HRWP-001 v1.0)
for the frozen normative contract text.

Follows Phase 149O.20L.7O.2N.6's recommendation (Architecture D, hybrid)
to freeze the remote-WebAuthn provider contract and ceremony
architecture before any implementation. This phase performed a
contract/architecture freeze only: no WebAuthn server, no browser/mobile
client, no credential creation, no HMIC change, no redeployment.

Read fresh, this phase: `src/pcae/core/hatp_fido2_provider.py`,
`src/pcae/core/hatp_providers.py`, `src/pcae/core/hatp_hardware_
credentials.py`, `src/pcae/core/hatp_bootstrap.py`, `src/pcae/core/
hatp_signing_ceremony.py`, and the four existing frozen HATP contracts
(HHCE-001 v1.1, HPSE-001 v1.1, HSCE-001 v1.3, HBDC-001 v1.2) to ground
every architectural decision directly in current code rather than
extending the prior phase's own necessarily-cautious framing without
re-verification.

**Central technical finding, re-derived from source rather than
assumed:** the existing local `Fido2HardwareProvider.request_signature()`/
`.verify()` already construct and verify a signature over
`authenticatorData || SHA-256(clientDataJSON)` — the exact same
cryptographic construction a browser's WebAuthn `getAssertion` ceremony
produces, not an arbitrary raw-bytes signature scheme. The one genuine
divergence between the local and a future remote provider is
**origin/RP-ID enforcement**: the local provider hand-constructs
`clientDataJSON` with a fixed, non-resolvable, non-HTTPS internal
origin/RP-ID pair (`pcae-hatp://hatp.pcae.local` / `hatp.pcae.local`)
that a real browser will never let a page assert, since browsers
enforce the page's actual origin and validate `rp.id` against it. This
materially narrows the semantic gap the prior phase correctly flagged
as unresolved (§15/§24 of that phase's report) — **remote WebAuthn
signing is concluded SUPPORTED via a new, provider-specific assertion
profile that reuses the existing verification algorithm and
challenge-binding technique unmodified**, differing only in
`provider_profile` routing, RP-ID/origin constants, and evidence
wire-encoding — not requiring an incompatible cryptographic scheme.

Froze **HRWP-001 v1.0**
(`docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md`, 68
sequential requirements, `HRWP-REQ-001`–`HRWP-REQ-068`, no gaps, no
duplicates), covering: a new, distinct `provider_profile` value
(`HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN`) required because
`Fido2HardwareProvider.verify()` already fail-closes on profile
mismatch and cannot parse WebAuthn-sourced evidence bytes;
registration/assertion evidence field mappings onto the existing
`HardwareCredentialRecord` schema (HHCE-001, unwidened — `signer_key_id`,
`public_key`, `algorithm`, `provider_profile` all populatable without a
schema change; `protocol_name` gains a third value, `"WEBAUTHN"`,
requiring no enum widening since the field is a plain string); the
`SignerRecord`/`DeploymentBinding` impact (HPSE-001/HBDC-001, both
unamended — confirmed still exactly one `DeploymentBinding` per
`repository_id`, protocol-agnostic); explicit, named-but-unresolved
RP-ID/HTTPS/TLS infrastructure requirements for the next phase (no
literal hostname, certificate authority, or network topology selected);
challenge/session field set, one-time-use replay protection, and
single-use session-binding requirements; the credential-selection
policy (EXPLICIT_SIGNER, matching PCAE's existing `DeploymentBinding`
single-selector model); the client-trust boundary (Model B preserved:
hac-dell remains authoritative for every governance-sensitive fact, the
Mac/iPhone client supplies only cryptographic ceremony output); and a
named, explicitly-deferred HSCE-001-companion-contract gap for how a
remote, asynchronous, browser-round-trip ceremony's evidence is
captured into the existing evidence store with the same atomicity/
no-clobber discipline HSCE-001 v1.3 already requires for the local
path — this gap is disclosed as future work, not concealed or silently
assumed resolved.

USB-over-IP is classified EXPERIMENTAL/NOT PRIMARY (Mac-only, does not
address the human's stated iPhone/NFC requirement). The existing local
raw FIDO2 path is retained unmodified — hybrid means additive, not a
deprecation.

Testing: a new disposable file,
`tests/test_phase_149o_20l_7o_2n_7_remote_webauthn_provider_contract_
architecture_freeze.py` (17 tests, all passing in isolation) —
structural completeness of the frozen contract document (required
sections, distinct provider_profile, RP-ID safety constraints, the
raw-CTAP/WebAuthn semantic-gap discussion, requirement-numbering
integrity, No-Go coverage) plus non-regression assertions confirming
this documentation-only phase left `hatp_fido2_provider.py`'s RP-ID/
origin constants, `hatp_providers.HATP_HARDWARE_PROVIDER_V1`, and
`HardwareCredentialRecord`'s field set byte-unchanged. No production
source (`src/pcae/`, `scripts/`) was changed this phase, so no broader
regression surface exists to attribute.

**No `makeCredential`/`getAssertion` was invoked against real hardware
this phase, on either host.** No credential created. No configuration
of the currently-attached Security Key C NFC changed. No
`HardwareCredentialRecord`/`Principal`/`Signer`/`DeploymentBinding`
created. No Dell protected-state mutation. No redeployment, no venv
mutation, no HATP activation, no contract amendment to HATP-001/
HHCE-001/HPSE-001/HSCE-001/HBDC-001 (HRWP-001 is additive, new), no
HMIC-001 change, no Permission Broker/runtime change.

Next phase: independent verification of HRWP-001 before any
implementation. Do not start a WebAuthn server, RP-ID/DNS/TLS
provisioning, or any implementation work until that independent
verification is complete.
