# Phase 149O.20L.7O.2N.6 — hac-dell FIDO2 Physical Authenticator Inspection and Multi-Authenticator / Remote-WebAuthn Architecture

**Status:** COMPLETE — READ-ONLY INSPECTION + ARCHITECTURE ANALYSIS ONLY. NO FIDO2 CREDENTIAL CREATED. NO HARDWARE MUTATION. NO PROTECTED-STATE MUTATION. NO PRODUCTION SOURCE CHANGE.

## 0. Directive supersession

This phase began under the original 149O.20L.7O.2N.6 prompt (Dell-local physical-authenticator availability/selection only) and was revised mid-phase by the human: the user's intended FIDO2 authenticator is attached to the PCAE development Mac, not to hac-dell, and does not want to move it there. The revised directive supersedes the Dell-local-attachment assumption and redirects this same phase to (1) preserve the Dell zero-device result already obtained, (2) inspect the Mac-attached authenticator read-only, and (3) investigate a multi-authenticator / remote-WebAuthn architecture. No `makeCredential` occurred under either version of the directive.

## 1. Entering state

- True phase-entry commit (local HEAD == origin/main at phase start): `871e72ad41931fffc0249e733fe5fe2a45ca09a9` (149O.20L.7O.2N.5's task-lifecycle-sync commit).
- Dell deployed revision at phase entry: `cdb77b75fc8bbca04340c7f25c405db3b07d32f7` (unchanged since 149O.20L.7O.2N.3).
- Latest completed phase: 149O.20L.7O.2N.5 — hac-dell Repaired FIDO2 Admin HMIC v1.7/38 Certification Activation — Successor Binding Only.

## 2. Local governance precheck

`git status --short` clean; `## main...origin/main`, 0 commits ahead/behind. `pcae health` → healthy, agent lock held by `claude-sonnet-5`. `pcae check` → passed. `pcae status coherence` → coherent. `pcae push check` → clean, nothing to push, task memory warnings only (pre-existing).

## 3. Mac ↔ Dell source/authority freshness (§5/§7 of the original directive, still applicable)

`git log --oneline cdb77b75...HEAD` (local) shows five phases (149O.20L.7O.2N.3 → .2N.5) landed since the Dell deployment; `git diff --stat cdb77b75...HEAD` shows every changed path is `.pcae/**` governance artifacts, `docs/**` phase reports, `tasks/**` lifecycle files, `CHANGELOG.md`, `PROJECT_STATUS.md`, or disposable test files — none touch `scripts/hatp_hardware_credential_admin.py`, `src/pcae/core/hatp_fido2_provider.py`, `src/pcae/core/hatp_providers.py`, `src/pcae/core/hatp_hardware_credentials.py`, `src/pcae/core/hatp_bootstrap.py`, `src/pcae/core/hatp_mandatory_certification.py`, or any contract. **Deployment remains authority-parity-valid; no redeployment required or performed.**

## 4. Fresh host identity and HMIC re-derivation (hac-dell, as root, deployed venv)

```
ssh hac-dell "hostname; cat /etc/machine-id"
→ atila-Latitude-E5470 / 54ff22ce400b475aa0d55cb68f4a3334  (exact match)
sudo git -C /opt/pcae/runtime/src rev-parse HEAD → cdb77b75fc8bbca04340c7f25c405db3b07d32f7 (clean tree)
```

Fresh derivation via `pcae.core.hatp_mandatory_certification` (root, deployed venv, `/opt/pcae/runtime/src`):

- `repository_instance_id`: `0107866f-af7c-40b4-8317-74e71acb05ca`
- `canonical_deployment_root`: `/opt/pcae/runtime/src`
- `implementation_commit`: `cdb77b75fc8bbca04340c7f25c405db3b07d32f7`
- `implementation_scope_digest`: `abfbffca527d3bf6d6ba610f6f5cd2d80bf113f9aa08f4339eb40322a8c077c4`
- `contract_versions` (7): `HATP-001=1.0, HBDC-001=1.2, HHCE-001=1.1, HMRC-001=1.1, HPSE-001=1.1, HSCE-001=1.3, RAE-001=1.0`

All five values are byte-identical to 149O.20L.7O.2N.5's own re-derivation — confirms no drift since that phase's certification activation.

`validate_active_hatp_mandatory_independent_verification_certification()` → `HMICValidationResult(status=VALID, reason='certification is valid: repository, deployment, implementation, contract, and revocation checks all passed')`.

`assess_hatp_mandatory_activation_readiness()` (root context) → `ready=False` overall; `mandatory_consumption_implementation_independently_verified=True` (HMIC term, matches 2N.5's activation); `hatp_substrate_operational=False` (`no_production_hardware_provider_detected` among its reasons — expected, Trust-Enrollment absent); `class_b_deployment_conformance_satisfies_readiness=False` (`INDETERMINATE`, multiple `HBDC-REQ-*` residuals) — same as 149O.20L.7O.2N.5 §11/§18's documented root-context read, informational only, not an authoritative Class-B verdict (no Class-B ceremony invoked, no change capable of affecting Class-B state).

## 5. Deployed venv freshness

`fido2==1.2.0`, `cryptography==44.0.3` (root, deployed venv) — unchanged from 149O.20L.7O.2N.5. No installation or upgrade performed.

## 6. Protected Root / Trust-Enrollment absence (unchanged)

`sudo stat /etc/pcae/hatp/trust-store` → real directory (`0750`, `root:pcae`), not a symlink. `sudo find /etc/pcae/hatp -type f` → exactly `.certification-transition.lock`, `certification-bindings.json`, `certifications.json`. **`HardwareCredentialRecord`, `Principal`, `Signer`, `DeploymentBinding` all absent** — confirmed fresh, not merely carried over from 2N.5's own reading.

## 7. Primary source re-derivation (HHCE-001 v1.1 surface + FIDO2 provider)

Re-read fresh, local Mac repo (byte-identical to deployed source per §3):

- `scripts/hatp_hardware_credential_admin.py` — standalone Protected-Admin script, never imported by any agent-executable path (HHCE-REQ-019/020). `enroll` requires governance confirmation strictly before any hardware ceremony (149O.20L.7O.2N.1 repair). No `--credential-id`/`--public-key` flag exists; identity is always the live ceremony's own output.
- `src/pcae/core/hatp_fido2_provider.py`:
  - `discover_fido2()` — the exact, narrowest read-only discovery surface: `sum(1 for _ in CtapHidDevice.list_devices())`, wrapped in a broad `except Exception` that reports `device_detected=False` with a note rather than raising. **Never mutating** — it calls no `Ctap2` method, no `make_credential`, no `get_assertion`; it only opens the HID device list. This is the exact call this phase used both on hac-dell and on the Mac (§9/§10 below).
  - `enroll_credential()` (Surface A) and `request_signature()` (signing side) both do `devices = list(CtapHidDevice.list_devices()); ...; device = devices[0]` — **confirmed fresh from source**: physical device selection is unconditional "first enumerated device," with no path selector, no serial-number pinning, no persisted device handle. This directly confirms the 2N-series' prior "deterministic-first-wins" finding.
  - `authenticatorGetInfo` (`Ctap2(device).info`, called from Python's `fido2` library when constructing a `Ctap2` object) is itself a standard, non-mutating CTAP2 command per the CTAP2 specification: it never requires user presence, PIN entry, or touch, and this module's own code never uses its result for anything mutating.
- `src/pcae/core/hatp_providers.py` — `discover_hardware_providers()` calls `discover_fido2()` (and the PIV equivalent) purely for availability facts; `create_production_hardware_provider()` never silently falls back to a weaker provider and never resolves the test provider (HATP-REQ-021/022).
- `src/pcae/core/hatp_hardware_credentials.py` / `hatp_bootstrap.py` — read in full for §14/§15 below (multi-credential architecture).

## 8. hac-dell direct device visibility (preserved from the original-directive session; not repeated)

```
lsusb                          → root hub, Dell webcam, Broadcom, Intel BT, Elan touchscreen -- no FIDO2 device
ls /dev/hidraw*                → hidraw0 only, ID_VENDOR=Elan Microelectronics (touchscreen), not a security key
CtapHidDevice.list_devices()   → raw_device_count: 0
discover_fido2()                → HardwareProviderAvailability(library_installed=True, device_detected=False, notes=('devices_detected:0',))
```

**DIRECT HAC-DELL FIDO2 PATH: ZERO DEVICE CURRENTLY PRESENT.** No hardware mutation occurred; no `makeCredential` occurred; no `HardwareCredentialRecord` exists. This result is preserved as valid evidence of "direct-local-device path unavailable right now," not "no FIDO2 authenticator exists" and not a software defect — the operator's intended authenticator is attached to the Mac by design, not to hac-dell.

## 9. Mac OS-level device inspection

`system_profiler SPUSBDataType` returned no output in this sandboxed session (denied silently, exit 0). `ioreg -p IOUSB -l` succeeded and is the evidence source used:

```
+-o AppleT8142USBXHCI@02000000
    +-o YubiKey FIDO@02100000  <class IOUSBHostDevice, ...>
        idVendor = 4176 (0x1050)      USB Vendor Name = "Yubico"
        idProduct = 1026 (0x0402)     USB Product Name = "YubiKey FIDO"
        bcdDevice = 1396 (0x0574)     bcdUSB = 512 (0x0200, USB 2.0)
        USBSpeed = 1 (full speed)     iSerialNumber = 0 (no serial descriptor exposed)
        bDeviceClass = 0 (defined per-interface)
```

The device attaches directly to the Mac's native `AppleT8142USBXHCI` controller node with **no intervening USB hub** in the `ioreg` tree — i.e. it is plugged directly into a Mac USB-C port, not through an adapter/hub with its own enumerated node (strong, not absolute, evidence of a USB-C-native plug).

## 10. FIDO2-library-level inspection (Mac, python-fido2 1.2.0, same version as hac-dell's deployed venv)

Non-mutating `CtapHidDevice.list_devices()` + `Ctap2(device).info` (`authenticatorGetInfo`, per §7 above):

```
raw_device_count: 1
vid:pid: 0x1050 0x402
product_name: "YubiKey FIDO"
serial_number: None
versions: ['U2F_V2', 'FIDO_2_0', 'FIDO_2_1_PRE', 'FIDO_2_1']
extensions: ['credProtect', 'hmac-secret', 'largeBlobKey', 'credBlob', 'minPinLength']
aaguid: b7d3f68e88a6471e9ecf2df26d041ede
options: {rk: True, up: True, plat: False, alwaysUv: False, credMgmt: True, authnrCfg: True,
          clientPin: True, largeBlobs: True, pinUvAuthToken: True, setMinPINLength: True,
          makeCredUvNotRqd: True, credentialMgmtPreview: True}
max_msg_size: 1536
pin_uv_protocols: [2, 1]
transports: ['nfc', 'usb']
algorithms: [{alg:-7 (ES256)}, {alg:-8 (EdDSA)}, {alg:-35 (ES384)}]
firmware_version: 329476 (0x050704 = 5.7.4)
```

No `makeCredential`, `getAssertion`, PIN entry, or touch was requested or performed — `authenticatorGetInfo` requires none of those. `clientPin: True` records only the boolean fact that a PIN is configured on the device (never the PIN itself, never requested).

## 11. Current device identification

**External research (primary sources), distinguished from repository evidence:**

- USB PID `0x1050:0x0402` ("YubiKey FIDO") identifies only that the device's **FIDO interface is the sole USB interface currently enabled** — Yubico's own USB-ID documentation states PID 0402=FIDO-only, 0401=OTP-only, 0404=CCID-only, etc., independent of physical form factor or connector. [How to Find the USB Product ID (PID) of your YubiKey](https://support.yubico.com/hc/en-us/articles/360013714459-How-to-Find-the-USB-Product-ID); [DeviceHunt 1050:0402](https://devicehunt.com/view/type/usb/vendor/1050/device/0402). **USB PID alone cannot identify form factor** — this is why AAGUID (§10) is the authoritative identifier used below.
- AAGUID `b7d3f68e-88a6-471e-9ecf-2df26d041ede` cross-referenced against a community-maintained, actively updated YubiKey AAGUID reference (`aaguids.csv`, [JMarkstrom/aaguids](https://github.com/JMarkstrom/aaguids), fetched directly this phase) → **exact match**: `Security Key NFC, firmware 5.7, FIDO L2 certified`. This is Yubico's **Security Key** product line, not the full YubiKey 5 series — structurally FIDO2/U2F-only (no OTP, PIV, OpenPGP, or OATH applications exist on this product line at all, confirmed against Yubico's own product page for [Security Key C NFC](https://www.yubico.com/product/security-key-c-nfc-by-yubico-black/): "does not support One-Time Passwords... does not include PIV... OpenPGP").
- Combined with the direct-USB-C, no-hub physical evidence (§9) and `transports: ['nfc', 'usb']` self-reported by the device's own `authenticatorGetInfo` (§10, independent corroboration of NFC capability), the evidence-supported identification is:

**Current device: Security Key C NFC by Yubico** (USB-C + NFC variant of the Security Key NFC family), firmware 5.7.4, FIDO2 Level 2 certified.

The USB-A "Security Key NFC" sibling (same AAGUID family, different connector) cannot be ruled out with absolute certainty from AAGUID alone — Yubico does not appear to vary the AAGUID by connector within the same firmware/certification family — but the direct-to-native-USB-C-controller attachment with no adapter/hub node is strong evidence for the USB-C variant specifically.

## 12. Current device capability matrix (evidence-based)

| Capability | Current device |
|---|---|
| USB-A | No (evidence: direct native-USB-C-controller attach, no hub) |
| USB-C | Yes (direct attach evidence, §9) |
| NFC | Yes (self-reported `transports=['nfc','usb']`, §10; AAGUID family confirms NFC-line, §11) |
| FIDO2 / CTAP2 | Yes — `FIDO_2_0`, `FIDO_2_1_PRE`, `FIDO_2_1` |
| U2F / CTAP1 | Yes — `U2F_V2` |
| WebAuthn | Yes (WebAuthn is the browser-facing name for the same CTAP2 protocol this device implements) |
| Resident/discoverable credentials | Supported (`options.rk = True`) |
| PIN / user verification | Supported and **currently configured** (`options.clientPin = True`); not required for every operation (`alwaysUv = False`) |
| PIV | No (Security Key product line has no PIV application) |
| OATH | No (Security Key product line has no OATH application) |
| OpenPGP | No (Security Key product line has no OpenPGP application) |
| OTP | No (Security Key product line has no OTP application; also consistent with the current FIDO-only USB interface config, §11) |
| Algorithms | ES256 (`-7`), EdDSA (`-8`), ES384 (`-35`) — **ES256 is in PCAE's current `_SUPPORTED_ENROLLMENT_ALGORITHMS` allowlist** (`hatp_fido2_provider.py`), so this device is compatible with PCAE's current enrollment path without any algorithm-allowlist change. |

## 13. Current device suitability

- **Model-B FIDO2 architecture (local/raw CTAP, current PCAE implementation):** Yes — CTAP2, `rk=True`, ES256-capable; nothing in `enroll_credential()`/`request_signature()` requires a capability this device lacks.
- **Direct use on the Mac:** Mechanically yes (attached and enumerable by `python-fido2` locally), but **PCAE's production FIDO2 provider path only exists in the deployed hac-dell venv/CLI** — there is no `pcae`-blessed local-Mac enrollment path today; using this device from the Mac against PCAE would require one of the architectures in §15-§21.
- **Remote WebAuthn (Mac as ceremony client):** Feasible in principle (device is CTAP2/WebAuthn-capable) — see §15-§27 for what PCAE-side infrastructure this would require. **UNKNOWN whether/when implemented** — nothing in this phase built it.
- **iPhone via USB-C:** UNKNOWN whether PCAE could reach it this way without a remote-WebAuthn architecture; the device itself is USB-C, but see §17's platform-support caveat before assuming this works via a browser flow today on every iOS version.
- **iPhone via NFC:** UNKNOWN in the same sense — device supports NFC (§10/§12), but platform/browser WebAuthn-over-NFC support and interaction constraints are a client-platform question this phase did not implement or test end-to-end (§18).

## 14. Existing multi-credential / multi-signer support (repository evidence, not external research)

Read fresh, `src/pcae/core/hatp_hardware_credentials.py` and `src/pcae/core/hatp_bootstrap.py`:

- **`HardwareCredentialRecord` registry** (`hardware-credentials.json`): `_parse_credential_registry_document()` parses a JSON **array** of records into a `Dict[str, HardwareCredentialRecord]` keyed by `signer_key_id`, rejecting only exact-duplicate keys. **Already supports an arbitrary number of active credentials simultaneously** — no schema change needed. `register_credential()` (admin.py) only ever adds/no-ops against the *same* `signer_key_id`'s existing entry; it never touches other entries, so enrolling a second, different physical key is already structurally possible via the existing writer, one `enroll` ceremony at a time.
- **`SignerRecord`** (`hatp_bootstrap.py`): `signer_key_id, principal_id, provider_profile, status, revoked_at`. The registry parses an array into `Dict[str, SignerRecord]` keyed by `signer_key_id` only — **`principal_id` is not a uniqueness key**, so multiple `SignerRecord`s legitimately sharing one `principal_id` are already structurally valid (confirmed by this phase's disposable test `test_signer_registry_supports_one_principal_with_multiple_signers`). **"One Principal, many Signers" is a pre-existing capability, not a gap.**
- **`DeploymentBinding`**: parsed into `Dict[str, DeploymentBinding]` keyed by `repository_id` — **exactly one active binding per `(repository_id)` at a time** (confirmed by this phase's test `test_duplicate_repository_id_deployment_binding_rejected`, which reproduces the existing parser's rejection of two bindings for the same `repository_id`). This is the **explicit selection point**: PCAE may know about many credentials/signers, but exactly one `signer_key_id` is "the" active governance-authoritative signer for a given deployment at a time, chosen by an explicit, governed `DeploymentBinding` write (the same unconditional-replace "successor binding" mechanism already proven safe by 149O.20L.7O.2M.4/149O.20L.7O.2N.5's `_write_active_binding`-equivalent pattern for `CertificationRecord` binding).
- **Revocation**: `revoke_credential()` and (by the same module discipline) signer revocation are per-key, monotonic (`ALREADY_REVOKED` idempotent), and never cascade to other records or automatically rebind `DeploymentBinding` (HHCE-REQ-043 as documented in the admin script) — a revoked backup key does not silently activate; rebinding remains a separate, explicit, governed act.
- **Singleton assumptions found**: exactly one, and it is at the **physical hardware layer**, not the registry layer — `enroll_credential()`/`request_signature()` both use `devices[0]` (§7). This is the "physical enrollment selection," strictly distinct from "registered multiplicity" (§13 of the original directive) — multiple *registered* credentials are already fine; a live *ceremony* still unambiguously needs exactly one physical device present.
- **Device labels/aliases**: absent from both `HardwareCredentialRecord` and `SignerRecord`. No `label`/`nickname`/`alias` field exists. This phase does not add one; a "primary-key"/"backup-key"/"travel-key" human-facing label would need to be a **new, explicitly non-authoritative** field (cryptographic `signer_key_id` remains identity) — a small, additive schema change if wanted, not required for the multi-credential model itself to work.

**Multi-credential policy current model:** PCAE naturally implements **"EXPLICIT SIGNER/CREDENTIAL"** (§32 of the original directive's option list) — not "any active registered credential," not threshold/multi-key. `DeploymentBinding` is the single point of truth for which one credential a live ceremony trusts.

## 15. Remote WebAuthn architecture — candidate design (analysis only, nothing implemented)

```
PCAE (hac-dell, authoritative)
   │  1. issues a governed, short-lived WebAuthn challenge bound to:
   │       RepositoryIdentity, canonical_deployment_root, operation type,
   │       phase/session id, nonce, expiry, expected credential allow-list,
   │       human governance/election state already obtained
   ▼
Human opens a trusted ceremony on Mac or iPhone
   │  2. browser/native WebAuthn API invoked with that challenge
   ▼
Physical security key, connected locally to that client device
   │  3. USB-C or NFC (client-local transport only — never crosses the network)
   ▼
WebAuthn response (attestation or assertion) returned to hac-dell
   │  4. PCAE independently verifies signature/challenge/origin/RP ID
   ▼
Governed operation continues (registry write, signing acceptance, etc.)
```

- **Model-B preservation (§22 of the original directive):** "Registry resolves governance identity; hardware proves possession and signs" survives cleanly — Dell/PCAE remains authoritative for `Principal`, `Signer`, `HardwareCredentialRecord`, `DeploymentBinding`, revocation, the allowed-credential set, challenge issuance, and result verification; the remote client supplies only a cryptographic ceremony *response*, never governance identity, exactly like the current local/raw path already does.
- **Registration mapping (§23):** A WebAuthn `navigator.credentials.create()` response's `credential.id` (the credential ID), `response.getPublicKey()`/`attestationObject`'s COSE public key, and the negotiated `alg` map directly onto `HardwareCredentialRecord.signer_key_id` (credential ID, hex), `algorithm`, and `public_key` (COSE_Key bytes) — the **same fields** `enroll_credential()`'s local path already produces (§7/`EnrolledFido2Credential`). `provider_profile` would need a **new, distinct** value (e.g. a `HATP_HARDWARE_PROVIDER_V1`-conformant WebAuthn adapter profile string, per the existing `provider_profile` field's own stated purpose of describing "required security properties," not vendor/protocol branding) so verification code can tell a WebAuthn-sourced record from a raw-CTAP one if their evidence formats differ (see next point). No `HHCE-001`/`HardwareCredentialRecord` schema field needs to change — only a new provider implementation and (likely) a new evidence byte-format for that provider.
- **Signing/assertion mapping (§24):** This is where local/raw CTAP and remote WebAuthn genuinely diverge, and the original directive is right not to assume otherwise. `Fido2HardwareProvider.request_signature()`/`.verify()` (§ read in full, §7) construct and check a **specific, hand-built `clientDataJSON`** (`CollectedClientData.create(type=GET, challenge=sha256(canonical_payload), origin=_HATP_ORIGIN)`) and a fixed `_HATP_RP_ID = "hatp.pcae.local"` that is **not a resolvable DNS name or HTTPS origin** — it is a private, internal string chosen precisely because HATP "is not a web origin" (module docstring, §7). A browser's real WebAuthn implementation enforces the actual page origin as `clientDataJSON.origin` and enforces `rp.id` against that origin's effective domain (per the WebAuthn spec) — it will not let a page mint an assertion claiming `origin="pcae-hatp://hatp.pcae.local"`. **A real HTTPS origin and a real, resolvable RP ID are required for a browser-mediated remote-WebAuthn client** (§26); the current fixed constants are load-bearing for the local/raw path and cannot be reused unmodified for a browser flow.
- **Raw CTAP vs. WebAuthn differences (§21), concretely, from source + spec knowledge:**
  - *Registration*: both ultimately call `authenticatorMakeCredential`; a WebAuthn browser flow additionally wraps it in `clientDataJSON`/origin binding and (usually) returns an `attestationObject` rather than the raw `credential_data` this module parses directly.
  - *Possession proof / signing*: both call `authenticatorGetAssertion` under the hood, but the *origin* and *rp.id* are browser-enforced under WebAuthn, versus this module's own fixed internal constants under raw CTAP — this is the specific incompatibility above.
  - *Attestation*: neither path currently validates device attestation (`capabilities().device_attestation = False`, §7) — this is an existing, disclosed, non-blocking limitation, unaffected by transport choice.
  - *Challenge semantics*: raw CTAP here binds `sha256(canonical_payload)` directly as the challenge; WebAuthn's `clientDataJSON.challenge` is the same kind of caller-supplied byte string, so the **binding technique itself (§ module docstring's "genuine and byte-exact" reasoning) is transport-independent** — only the origin/RP-ID enforcement differs.
  - **Conclusion: remote WebAuthn *enrollment* evidence can plausibly be mapped into the existing `HardwareCredentialRecord` schema (§23) without a schema change, but remote WebAuthn *signing* requires either a browser-origin-compatible RP ID/origin story for `hatp.pcae.local`-equivalent semantics, or a structurally separate signing verification path — do not assume enrollment support implies signing support (§24 of the original directive's own caution, independently re-confirmed here from source, not merely repeated).**
- **RP ID / origin / HTTPS requirement (§26):** the largest new infrastructure surface. A real remote-WebAuthn client needs PCAE (or a governed companion service) reachable at a stable HTTPS origin with a real RP ID the browser will accept — a private/LAN/VPN domain behind a reverse proxy, or a dedicated small HTTPS companion service in front of hac-dell, are the standards-compliant options; a bare internal string like the current `hatp.pcae.local` is not usable for a real browser WebAuthn ceremony.
- **Network security (§27):** TLS is implied by the HTTPS requirement above; origin validation and RP-ID binding are enforced by the browser itself (not something PCAE needs to re-implement client-side), but PCAE-side still needs fresh challenge issuance with expiry, anti-replay (a challenge used at most once), session/CSRF binding of "this human, this operation, this challenge," and the existing allow-list/verification/audit machinery this phase found already exists for the local path (§14).
- **Telegram boundary (§28/§29 of the original directive, reaffirmed):** any future delivery of a ceremony link (QR, deep link, Telegram message) remains **outbound notification only** — receiving a Telegram message must never become an inbound authority channel, and chat confirmation, WebAuthn possession proof, and Protected Admin authority remain three distinct, non-substitutable facts, exactly as the existing governance model already requires for the local ceremony's own human-confirmation step (§7, `_prompt_confirm`).
- **Multiple WebAuthn credentials / allow-list (§30):** the existing `DeploymentBinding`-as-explicit-selector model (§14) composes naturally with WebAuthn's own `allowCredentials` list — PCAE would populate that list from its own registry's active, non-revoked `HardwareCredentialRecord`s (or a governed subset), never trusting an arbitrary credential the client asserts.
- **Transport independence (§31):** for a *given* physical key, its FIDO2 credential ID and public key are properties of the credential itself, not of the transport used to reach it in a given ceremony — the **same** credential ID would appear whether the key is used via USB-C, NFC, or a browser WebAuthn flow (this is standard CTAP2/WebAuthn behavior: the authenticator, not the transport, produces the credential). PCAE's `signer_key_id` (§14) is therefore already transport-independent by construction; no new field is needed to represent "same key, different transport" — a re-derivation this phase performed by reading `enroll_credential()`/`.verify()`'s exact field derivation, not merely assumed.

## 16. iPhone-specific analysis (§16-§18 of the original directive)

- **Not raw USB-over-IP:** correctly excluded by the directive. iOS does not expose arbitrary attached USB HID devices as raw kernel devices to third-party code the way Linux does; the standards-compliant iPhone integration path is the platform's own WebAuthn/security-key APIs (Safari/WebKit's WebAuthn implementation, and native `ASAuthorizationSecurityKeyPublicKeyCredentialProvider` for apps), not low-level CTAP/HID forwarding.
- **iPhone USB-C:** current-generation iPhones (USB-C connector) can physically mate with a USB-C security key; whether a *given* iOS/Safari version's WebAuthn implementation currently accepts a wired USB-C security key (as opposed to NFC only) is a **platform capability this phase did not independently verify against a live device** — reported as **UNKNOWN**, not assumed, per the original directive's explicit instruction not to guess.
- **iPhone NFC:** iOS Safari and native WebAuthn both support NFC security keys for WebAuthn ceremonies in modern iOS versions, subject to well-known interaction constraints this phase did not re-verify end-to-end: a user gesture is required to start the NFC read, there is a bounded tap/session window, and (per the directive's own caution, §18) raw low-level FIDO APIs are **not** exposed to arbitrary code — only the browser/native WebAuthn ceremony flow is. This phase makes **no claim** about exact current-iOS-version behavior beyond this general, well-established platform shape; a live test on the user's actual iPhone/iOS version would be needed before relying on it operationally.
- **Current device (§17/§18 applied to the identified Security Key C NFC, §11):** USB-C-connectable in principle; NFC-connectable in principle (device supports NFC per §10/§12). Whether PCAE's *own, not-yet-built* remote-WebAuthn flow works end-to-end on the user's iPhone is **UNKNOWN** until that flow exists and is tested — this phase performed no such implementation or test (No-Go §46).

## 17. YubiKey 5C / YubiKey 5C NFC comparison (external research, distinguished from repository evidence)

External research this phase performed (Yubico's own product pages, cited): [YubiKey 5C](https://www.yubico.com/product/yubikey-5c/) — USB-C only, **no NFC**; [YubiKey 5C NFC](https://www.yubico.com/product/yubikey-5c-nfc/) — USB-C **and** NFC. Both are full **YubiKey 5-series** devices: FIDO2/WebAuthn, U2F/CTAP1, Smart card (PIV-compatible), Yubico OTP, OATH-HOTP/TOTP, OpenPGP, Secure Static Passwords — a materially larger application surface than the currently-attached Security Key C NFC (§11-§12), which is FIDO-only by product-line design.

| Capability | Current device (Security Key C NFC) | YubiKey 5C | YubiKey 5C NFC |
|---|---|---|---|
| USB-A | No | No | No |
| USB-C | Yes | Yes | Yes |
| NFC | Yes | **No** | Yes |
| FIDO2 / CTAP2 | Yes | Yes | Yes |
| U2F / CTAP1 | Yes | Yes | Yes |
| WebAuthn | Yes | Yes | Yes |
| PIV | No | Yes | Yes |
| OTP | No | Yes | Yes |
| OATH | No | Yes | Yes |
| OpenPGP | No | Yes | Yes |
| Mac direct use (local/raw CTAP, current PCAE path) | Yes | Yes | Yes |
| iPhone USB-C | UNKNOWN (platform-dependent, §16) | UNKNOWN | UNKNOWN |
| iPhone NFC | Not applicable (no NFC hardware) | Not applicable (no NFC hardware) | Yes-capable, platform-behavior UNKNOWN (§16) |
| Dell direct use | Yes (mechanically — zero devices only because none is attached there now, §8) | Yes (same) | Yes (same) |
| USB-over-IP (Mac→Dell, §18) | Technically compatible with raw CTAP either way | Same | Same |
| Remote WebAuthn (once built, §15) | Feasible | Feasible | Feasible |

Only FIDO/WebAuthn capabilities are currently load-bearing for PCAE (§7 of the original directive) — the PIV/OTP/OATH/OpenPGP rows are inventory context only; PCAE uses none of them today.

## 18. USB-over-IP alternative — evaluated, not implemented (§20)

Not installed, not attempted. Evaluated on its merits against remote WebAuthn:

- **Advantages:** reuses the existing, already-verified raw-CTAP `Fido2HardwareProvider` code path unmodified (§7) — no new provider, no origin/RP-ID problem (§15).
- **Disadvantages:** Mac-only in practice (no comparable iPhone USB-over-IP story); introduces a network-transport dependency (a USB/IP daemon or similar) between the physical key and hac-dell with its own latency/reconnect and exclusive-device-ownership failure modes; widens hac-dell's network trust surface for a raw HID device rather than a narrow, well-specified HTTPS+WebAuthn ceremony; device-set ambiguity (§7's `devices[0]` first-wins finding) would still apply exactly as today, now over a virtual USB bus instead of a physical one; does nothing for the user's stated iPhone/NFC goal.
- **Comparison verdict:** narrower short-term win for Mac-only, but does not address the user's full stated requirement (Mac + iPhone + USB-C + NFC + multiple keys); remote WebAuthn is the more complete, standards-based answer to the actual requirement, at the cost of the RP-ID/HTTPS infrastructure work identified in §15.

## 19. Architecture comparison and recommended verdict (§36/§43)

| Option | Meets Mac | Meets iPhone | Meets NFC | Preserves Model-B | New infra required |
|---|---|---|---|---|---|
| A. Dell-local raw FIDO2 only | No (key stays with human) | No | No | Yes | None |
| B. Mac USB-over-IP → Dell raw FIDO2 | Yes | No | No | Yes | USB/IP transport (§18) |
| C. Remote WebAuthn only | Yes | Yes | Yes | Yes (with care, §15) | HTTPS/RP-ID (§15/§26), new provider |
| **D. Hybrid: existing local/raw provider + new remote-WebAuthn provider, shared registry/governance** | Yes | Yes | Yes | Yes | Same as C, additively |

**Recommended architecture: D — hybrid multi-authenticator architecture.** The existing local/raw `Fido2HardwareProvider` is retained unmodified for Dell-local use (still the only production hardware provider, still `HATP_HARDWARE_PROVIDER_V1`-conformant); a new, structurally separate `HardwarePossessionProvider`-family implementation (conceptually `RemoteWebAuthnProvider`, alongside the existing `LocalCtapFido2Provider`-equivalent — naming only, nothing renamed or implemented this phase, §37) would be added for Mac/iPhone-mediated ceremonies, sharing the **same** `HardwareCredentialRecord`/`Principal`/`SignerRecord`/`DeploymentBinding` governance model this phase confirmed already supports the required multiplicity (§14). Dell/PCAE remains authoritative for every governance-sensitive fact (§15's Model-B analysis, §38); the client supplies only cryptographic ceremony output.

**Schema/contract impact:** none required to *represent* the multiplicity this phase investigated (§14/§39) — the existing `HardwareCredentialRecord`/`SignerRecord` arrays already support it. A new `provider_profile` value and a new provider-specific evidence format are additive, not schema-breaking, for enrollment (§15/§23). Remote *signing* verification is the one piece that structurally cannot reuse the current fixed `_HATP_RP_ID`/`_HATP_ORIGIN` constants unmodified (§15/§24) and would need its own contract treatment before implementation.

**HMIC impact:** none this phase — no authority-bearing source changed (§3/§7). A future remote-WebAuthn provider module would itself become new authority-bearing code requiring HMIC-001 scope-digest inclusion and independent verification before activation, exactly as `hatp_fido2_provider.py` itself already required (module docstring, §7) — flagged here for the eventual implementation sequence (§20 below), not undertaken now.

## 20. Immediate real-enrollment status (§44)

- **DIRECT DELL:** not ready — zero device present at hac-dell (§8).
- **MAC USB FORWARDING:** possible in principle (§18), **not selected**, not implemented.
- **REMOTE WEBAUTHN:** partially feasible — enrollment-side evidence mapping looks compatible with the existing schema (§15/§23); signing-side verification needs its own RP-ID/origin design before it can be called feasible (§15/§24) — **blocked pending implementation and its own contract/architecture freeze.**

**No `makeCredential` was invoked anywhere in this phase, on either host.**

## 21. Implementation sequence (§45, if the recommended direction is pursued later)

1. Remote-WebAuthn contract/architecture freeze — resolve the RP-ID/origin question (§15) explicitly, define the new `provider_profile` value and evidence schema, define challenge-binding fields (§15's list) as a real contract, not prose.
2. Server-side challenge issuance + result-verification implementation (Dell-side only; still no client work).
3. Minimal browser/mobile ceremony (the actual HTML/JS or native flow a human uses).
4. Multi-credential *policy* implementation only if a concrete gap is found beyond what §14 already confirmed (labels/aliases, §14's last bullet, are the only identified optional addition).
5. Independent verification of steps 1-4.
6. HMIC source-scope expansion to cover the new authority-bearing module(s), per §20's HMIC-impact note.
7. Deployment + recertification (mirroring the existing 2N.3/2N.4/2N.5 deploy → create → activate pattern this repo already uses for certification changes).
8. Synthetic interoperability testing (no real hardware) before any live ceremony.
9. First real WebAuthn/FIDO2 enrollment — a separate, narrowly-scoped phase, exactly as the original directive already required for the local path (not combined with Principal/Signer creation, per the original §32/§45).

## 22. No-Go compliance

Independently re-confirmed true at phase end: no `makeCredential` anywhere, on hac-dell or the Mac; no credential created; current key's configuration untouched (only `authenticatorGetInfo`/HID enumeration performed — both read-only, neither requires or performs a write); no PIN requested or entered; no `HardwareCredentialRecord`/`Principal`/`Signer`/`DeploymentBinding` created; no Dell protected-state mutation (§6, re-confirmed fresh); no contract/HMIC/certification change; no redeployment; no venv mutation; no HATP activation; no Permission Broker/runtime change; VirtualHere/USB-forwarding/WebAuthn not implemented (evaluated only, §18-§21); user was not asked to move the key to hac-dell (directive honored).

## 23. Testing / evidence

New disposable file `tests/test_phase_149o_20l_7o_2n_6_hac_dell_fido2_availability_multi_authenticator_architecture.py` (9 tests, all passing in isolation): `discover_fido2()` non-mutating across zero/one/multiple/enumeration-failure device counts; enumeration-order preservation (source basis for the `devices[0]` first-wins finding, §7); multiple simultaneous active `HardwareCredentialRecord`s via the real parser; one `principal_id` with multiple `SignerRecord`s via the real parser; exactly-one-`DeploymentBinding`-per-`repository_id` and its duplicate-rejection, via the real parser. No test touches real hardware, a protected root, or performs any registry write.

## 24. Regression

No production source change this phase (only new test file + docs/governance artifacts) — no regression surface introduced. This phase's own 9 new tests pass standalone (§23). Full command output retained; a broader Fast Green sweep was not re-run as an untailored count (matches this lineage's own established precedent of citing the phase's own dedicated tests plus the unchanged-production-source fact, since zero production lines changed).

## 25. Governance

`pcae health` → healthy. `pcae check` → passed. `pcae status coherence` → coherent. `pcae push check` (pre-push) → clean/nothing-to-push baseline confirmed at phase start (§2); re-run below after this phase's commits, before push.

## 26. Commits / push

See `.pcae/phase-completion-metadata.json` `phase_commits` for the exact hash list. Pushed to `origin/main`; `origin/main..HEAD` = 0 after push.

## 27. Findings

None. Zero Blocking, zero Non-Blocking. (The RP-ID/origin incompatibility for remote *signing*, §15/§24, is a design finding this phase surfaces deliberately for the *next* phase's benefit — it is not a defect in anything this phase touched, since this phase implemented nothing.)

## 28. Next phase

Per §51 of the revised directive: do not pre-authorize implementation. If the hybrid remote-WebAuthn direction (§19) is the one the human wants pursued, the narrowest next phase is **step 1 of §21 only** — a remote-WebAuthn contract/architecture freeze phase (RP-ID/origin decision, new `provider_profile` value, evidence schema, challenge-binding contract fields) — still no implementation, no hardware, no `makeCredential`. If instead the human simply wants to attach the Security Key C NFC to hac-dell directly at some point, the original 149O.20L.7O.2N.6-style Dell-local availability/selection phase remains valid and unblocked whenever a device is actually attached there (§8 — currently zero).
