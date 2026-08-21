# Phase 149O.20L.7O.2N.6 Completion Report

**Verdict:** DELL DIRECT FIDO2 PATH ZERO DEVICE — MAC-ATTACHED SECURITY
KEY C NFC INSPECTED READ-ONLY AND IDENTIFIED — EXISTING REGISTRY
ALREADY SUPPORTS MULTI-CREDENTIAL/MULTI-SIGNER PER PRINCIPAL — HYBRID
LOCAL + REMOTE-WEBAUTHN ARCHITECTURE RECOMMENDED (ANALYSIS ONLY) — NO
REAL FIDO2 CREDENTIAL CREATED.
See docs/PHASE_149O_20L_7O_2N_6_HAC_DELL_FIDO2_PHYSICAL_AUTHENTICATOR_
INSPECTION_AND_MULTI_AUTHENTICATOR_REMOTE_WEBAUTHN_ARCHITECTURE.md for
the full phase report.

Originally scoped as a Dell-local physical-authenticator availability/
selection phase; revised mid-phase by the human, since the intended
FIDO2 authenticator is attached to the Mac, not hac-dell, and the human
does not want it moved there. The revised directive superseded the
Dell-local-attachment assumption without reopening or repeating the
Dell-side work already completed.

Preserved the already-obtained hac-dell zero-device result
(`lsusb`/`CtapHidDevice.list_devices()`/`discover_fido2()` all report
zero eligible authenticators; no hardware mutation, no `makeCredential`,
no `HardwareCredentialRecord`). Re-verified hac-dell host identity,
deployed revision (`cdb77b75fc8bbca04340c7f25c405db3b07d32f7`,
unchanged and clean), HMIC v1.7/38 re-derivation (validator `VALID`,
matching 149O.20L.7O.2N.5's own activation), venv freshness
(`fido2==1.2.0`, `cryptography==44.0.3`), and Protected Root/
Trust-Enrollment absence (`HardwareCredentialRecord`/`Principal`/
`Signer`/`DeploymentBinding` all confirmed absent).

Read-only inspected the Mac-attached authenticator: `ioreg -p IOUSB -l`
(direct attach to the Mac's native USB-C controller, no intervening
hub — `idVendor=0x1050`/Yubico, `idProduct=0x0402`/"YubiKey FIDO",
`bcdDevice=0x0574`) and `python-fido2`'s non-mutating
`authenticatorGetInfo` (`versions=['U2F_V2','FIDO_2_0','FIDO_2_1_PRE',
'FIDO_2_1']`, `transports=['nfc','usb']`,
`aaguid=b7d3f68e88a6471e9ecf2df26d041ede`, `options.rk=True`,
`options.clientPin=True`, `algorithms` include ES256). No
`makeCredential`, `getAssertion`, PIN entry, or touch was requested.

Cross-referenced the AAGUID against a community-maintained,
independently fetched Yubico AAGUID table (external primary-source
research, distinguished throughout the full report from repository
evidence) → **Security Key C NFC by Yubico**, firmware 5.7.4, FIDO2
Level 2 certified — a FIDO-only product line (no OTP/PIV/OpenPGP/OATH),
confirmed compatible with PCAE's current `ES256`-only enrollment
allowlist. Externally researched and tabulated YubiKey 5C (USB-C, no
NFC, full application suite) and YubiKey 5C NFC (USB-C+NFC, full
application suite) for comparison against the current device.

Read `src/pcae/core/hatp_hardware_credentials.py` and
`src/pcae/core/hatp_bootstrap.py` fresh and confirmed — with 9 new
disposable tests exercising the real parsers, no production source
change — that the on-disk registry already supports an arbitrary
number of simultaneously active `HardwareCredentialRecord`s and
multiple `SignerRecord`s sharing one `principal_id` ("one Principal,
many Signers" is pre-existing, not a gap); `DeploymentBinding` remains
the single explicit-selection point (exactly one active binding per
`repository_id`), confirmed via a duplicate-rejection test against the
real parser. The one singleton assumption found is at the physical
hardware layer, not the registry layer: `enroll_credential()`/
`request_signature()` both select `devices[0]` — re-confirmed fresh
from source, unchanged from prior findings.

Investigated a remote-WebAuthn architecture (analysis only, nothing
implemented): enrollment evidence (credential ID, COSE public key,
algorithm) maps onto the existing `HardwareCredentialRecord` schema
without a schema change, but remote *signing* cannot reuse the fixed
internal `_HATP_RP_ID="hatp.pcae.local"`/`_HATP_ORIGIN` constants
unmodified — a real HTTPS origin and resolvable RP ID are required for
a browser-mediated WebAuthn ceremony, since browsers enforce origin/
RP-ID binding that a private internal string cannot satisfy. This is
flagged as the key open design question for any future implementation
phase, not something this phase resolved or built.

**Recommended architecture:** hybrid — the existing local/raw
`Fido2HardwareProvider` retained unmodified for Dell-local use, plus a
new, structurally separate remote-WebAuthn provider implementation
sharing the same `HardwareCredentialRecord`/`Principal`/`SignerRecord`/
`DeploymentBinding` governance model this phase confirmed already
supports the required multiplicity. Dell/PCAE remains authoritative for
every governance-sensitive fact; the client supplies only cryptographic
ceremony output. No schema change required to represent the
multiplicity investigated; a new `provider_profile` value and
provider-specific evidence format would be additive for enrollment.

Focused tests: this phase's own 9 new disposable tests (registry/
signer/binding multiplicity via the real parsers, `discover_fido2()`
non-mutating across zero/one/multiple/failure device counts,
enumeration-order preservation), all passing in isolation. No
production source changed this phase, so no regression surface was
introduced.

**No `makeCredential` was invoked anywhere in this phase, on either
host.** No credential created. No Dell protected-state mutation. No
redeployment, no venv mutation, no HATP activation, no contract/HMIC/
certification change. The user was not asked to move the key to
hac-dell.

Next phase: if the hybrid remote-WebAuthn direction is the one the
human wants pursued, the narrowest next step is a remote-WebAuthn
contract/architecture freeze phase (RP-ID/origin decision, new
`provider_profile` value, evidence schema, challenge-binding contract
fields) — still no implementation, no hardware, no `makeCredential`. If
instead a device is later attached directly to hac-dell, the original
Dell-local availability/selection phase shape remains valid and
unblocked whenever that happens.
