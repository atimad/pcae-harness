# HATP Remote WebAuthn Provider Contract

## Contract identity and status

**Contract:** HRWP-001
**Version:** 1.1
**Status:** FROZEN — CONTRACT REPAIRED (§45, closes NBF-149O.20L.7O.2N.8-1) — NOT YET INDEPENDENTLY VERIFIED, NOT IMPLEMENTED
**Frozen by:** Phase 149O.20L.7O.2N.7 — Remote WebAuthn Provider Contract and Ceremony Architecture Freeze; follows Phase 149O.20L.7O.2N.6 (hac-dell FIDO2 Physical Authenticator Inspection and Multi-Authenticator / Remote-WebAuthn Architecture), whose §15-§21 this contract formalizes into normative requirement text. Repaired in place by Phase 149O.20L.7O.2N.11 (§45, closes NBF-149O.20L.7O.2N.8-1 identified by Phase 149O.20L.7O.2N.8's independent verification and reconfirmed by Phase 149O.20L.7O.2N.10; `HRWP-REQ-019` revised in place, same requirement identity, no renumbering, mirroring HHCE-001 v1.1's own §30 precedent for a text-only, in-place requirement revision).
**Depends on:** HATP-001 v1.0 (`HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`, unamended), HHCE-001 v1.1 (`HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md`, unamended — this contract's registration evidence targets HHCE-001's existing `HardwareCredentialRecord` schema without widening it), HPSE-001 v1.1 (`HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md`, unamended), HSCE-001 v1.3 (`HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`, unamended — this contract names, but does not resolve, the additional signing-evidence-format work HSCE-001 would need for remote assertions to be consumed by `pcae hatp sign rollback`), HBDC-001 v1.2 (`HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`, unamended).
**Architecture basis:** `docs/PHASE_149O_20L_7O_2N_6_HAC_DELL_FIDO2_PHYSICAL_AUTHENTICATOR_INSPECTION_AND_MULTI_AUTHENTICATOR_REMOTE_WEBAUTHN_ARCHITECTURE.md` (prior phase's architecture analysis, read fresh); `src/pcae/core/hatp_fido2_provider.py` (the exact current local/raw FIDO2 provider — signing/verification algorithm, RP-ID/origin constants, evidence schema — read directly this phase); `src/pcae/core/hatp_providers.py` (provider-neutral interfaces — `HATPProofVerifierProvider`, `HATPHardwareSigner`, `HardwareProviderCapabilities`, `HATP_HARDWARE_PROVIDER_V1` — read directly this phase); `src/pcae/core/hatp_hardware_credentials.py` (`HardwareCredentialRecord` schema, read directly this phase); `src/pcae/core/hatp_bootstrap.py` (`SignerRecord`, `DeploymentBinding` schemas, read directly this phase).

This is a contract-freeze document. It authorizes no implementation, no WebAuthn server, no browser/mobile client, no credential creation, no HMIC change, and no redeployment. It defines the normative interface, evidence formats, and ceremony ordering a future implementation phase must build to, mirroring the freeze-then-implement precedent already established by HHCE-001/HPSE-001/HSCE-001 in this repository.

---

## 0. Normative language

"SHALL", "SHALL NOT", "MUST", "MUST NOT", "MAY", and "SHOULD" are interpreted per RFC 2119, matching this repository's other bound contracts. Every normative sentence carries a unique requirement ID, `HRWP-REQ-###`, sequential from 001, no gaps, no duplicates. This contract's numbering namespace is independent of `HATP-REQ-*`/`HHCE-REQ-*`/`HPSE-REQ-*`/`HSCE-REQ-*`/`HBDC-REQ-*`/`HMIC-REQ-*`.

## 1. Purpose

**HRWP-REQ-001.** This contract exists to freeze the architecture and evidence contract for **remote WebAuthn as a second `HardwarePossessionProvider`-family implementation**, additive to the existing local/raw `Fido2HardwareProvider` (`hatp_fido2_provider.py`), so that a human's security key attached to a Mac or iPhone — not to hac-dell — can participate in PCAE governance ceremonies while hac-dell remains the sole authority for governance identity, exactly as Phase 149O.20L.7O.2N.6 §15/§19 recommended (Architecture D: hybrid).

**HRWP-REQ-002.** This contract does not implement a WebAuthn server, a browser or mobile client, credential creation, or any protected-state write. It defines interface shape, field mappings, and ceremony ordering only.

## 2. Core strategic invariant (carried forward, not reopened)

**HRWP-REQ-003.** "Registry resolves governance identity; hardware proves possession and signs" (HATP-001's Model B) SHALL hold for remote WebAuthn exactly as it holds for local/raw FIDO2 today. hac-dell remains authoritative for `RepositoryIdentity`, `Principal`, `SignerRecord`, `HardwareCredentialRecord`, `DeploymentBinding`, the allowed-credential set, challenge issuance, challenge/response verification, revocation, and audit. A Mac or iPhone client SHALL supply only cryptographic WebAuthn ceremony output — never governance identity, never an authorization decision.

## 3. Provider model

**HRWP-REQ-004.** The existing provider-neutral interfaces in `hatp_providers.py` — `HATPProofVerifierProvider.verify()` and `HATPHardwareSigner.capabilities()/credential_identity()/request_signature()` — are sufficient as the common interface shape for a second provider implementation. No change to either `Protocol` is required: a future `RemoteWebAuthnProvider` class implements the same `verify()` signature (`canonical_payload`, `signer_key_id`, `provider_profile`, `assertion` → `HATPProviderVerificationOutcome`) that `Fido2HardwareProvider.verify()` implements today, structurally, with no explicit inheritance, exactly as the existing class already does.

**HRWP-REQ-005.** The conceptual provider family is:

```
HardwarePossessionProvider  (existing informal grouping, Protocol-based, unrenamed)
    ├── LocalCtapFido2Provider   == today's Fido2HardwareProvider (hatp_fido2_provider.py, unmodified)
    └── RemoteWebAuthnProvider  == new, this contract's subject (not implemented this phase)
```

No class is renamed. No existing class is modified by this contract.

**HRWP-REQ-006.** `create_production_hardware_provider()` (`hatp_providers.py`) is NOT amended by this contract. A future implementation phase MUST decide, as its own scoped question, whether remote-WebAuthn provider selection is added to that factory's existing `provider_profile`-string dispatch or reached by a distinct call path — this contract does not resolve that dispatch question, since it depends on implementation-phase decisions (e.g. whether the caller is a CLI command or an HTTP server process) outside this freeze's scope.

## 4. `provider_profile` vocabulary

**HRWP-REQ-007.** Remote WebAuthn SHALL use a distinct `provider_profile` value from `HATP_HARDWARE_PROVIDER_V1` (the value `hatp_providers.py` defines and both `Fido2HardwareProvider` and the not-yet-implemented `PivHardwareProvider` currently share). Rationale, from source: `Fido2HardwareProvider.verify()` fail-closes when `record.provider_profile != provider_profile` (`hatp_fido2_provider.py`, verification side) — `provider_profile` is the field that lets a verifier route a stored `HardwareCredentialRecord` to the correct provider implementation and evidence parser. A remote-WebAuthn-sourced record MUST be routable to a WebAuthn-specific verifier, not accidentally accepted by `Fido2HardwareProvider.verify()`'s CTAP2-evidence parser (which would raise or fail-closed on WebAuthn's different evidence encoding — see §11).

**HRWP-REQ-008.** The frozen value is **`HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN`**. This follows `HATP_HARDWARE_PROVIDER_V1`'s own documented naming discipline ("defined by required security properties, not by vendor or protocol branding," `hatp_providers.py`) by remaining a `HATP_HARDWARE_PROVIDER_V1`-family suffix rather than an unrelated new root string — the underlying security properties this contract's provider targets (non-exportable key, fresh human presence, credential identity, signature verification) are the same four `HATP_HARDWARE_PROVIDER_V1` already names; only the ceremony/evidence *transport* differs, which HRWP-REQ-007 requires be distinguishable. `provider_profile` identifies ceremony semantics (local raw CTAP vs. browser-mediated WebAuthn), never physical transport (USB-C vs. NFC) — §6 below.

**HRWP-REQ-009.** A future implementation phase MAY revise this exact string (e.g. versioning it `_V1`/`_V2` independently of the base profile) if implementation reveals a need; this contract fixes the naming *pattern* and its rationale, not an unchangeable literal, consistent with how `HHCE-001`/`HSCE-001` have each been revised in place by later phases without renumbering.

## 5. Transport is not governance identity

**HRWP-REQ-010.** USB-C, NFC, and browser-WebAuthn are transport/session characteristics only. `HardwareCredentialRecord.signer_key_id` (== the WebAuthn credential ID, hex-encoded, §10) SHALL remain the same value for the same physical authenticator regardless of which compatible transport carried a given ceremony. This is standard WebAuthn/CTAP2 behavior: the authenticator, not the transport, produces the credential and signs the assertion; `client_data.origin`/`rp_id` — not the physical transport — are what a verifier checks. No new field is required to represent "same key, different transport."

## 6. Multiple-credential model (re-derived from primary source, not re-designed)

**HRWP-REQ-011.** `HardwareCredentialRecord`'s registry (`hatp_hardware_credentials.py`, `_parse_credential_registry_document()`) already parses a JSON array into `Dict[str, HardwareCredentialRecord]` keyed by `signer_key_id`, supporting an arbitrary number of simultaneously active credentials with no schema change. This contract requires no widening of that schema for remote-WebAuthn-sourced records (§10 states the exact field mapping).

**HRWP-REQ-012.** `SignerRecord` (`hatp_bootstrap.py`: `signer_key_id`, `principal_id`, `provider_profile`, `status`, `revoked_at`) is keyed by `signer_key_id` only — `principal_id` is not a uniqueness key, so one `Principal` legitimately owns multiple `SignerRecord`s today. This contract requires no schema change to represent a human's Mac-attached and Dell-attached (or multiple Mac-attached) authenticators as distinct `SignerRecord`s under one `Principal`.

**HRWP-REQ-013.** `DeploymentBinding` (`hatp_bootstrap.py`) is keyed by `repository_id` with exactly one active binding per repository — confirmed unchanged by this contract (§13). A live signing ceremony still resolves to exactly one `(principal_id, signer_key_id)` pair via the existing `DeploymentBinding`, regardless of how many `SignerRecord`s exist.

## 7. Credential selection policy

**HRWP-REQ-014.** PCAE's server side SHALL populate WebAuthn's `allowCredentials` list (registration ceremony's counterpart at assertion time) from its own registry's active, non-revoked `HardwareCredentialRecord`s for the resolved `signer_key_id`(s) only — never accept an arbitrary credential ID the client asserts, and never construct `allowCredentials` from client-supplied input. This is the **EXPLICIT_SIGNER** policy (one of the three candidates surveyed: `ANY_ACTIVE`, `EXPLICIT_SIGNER`, `PREFERRED_WITH_FALLBACK`) — the only one PCAE's existing `DeploymentBinding`-as-single-selector model (§6) naturally supports without new design. Threshold/multi-key authentication is explicitly out of scope for this contract (no current PCAE contract supports it).

## 8. Enrollment ceremony (registration flow, frozen shape)

**HRWP-REQ-015.** The frozen registration flow is:

```
1. PCAE server validates governance authorization for a new-credential-enrollment
   operation (per §9's ordering requirement) BEFORE step 2.
2. PCAE server creates a short-lived, single-use WebAuthn registration
   challenge/options object bound to the fields in §11.
3. PCAE server delivers the ceremony to a trusted client session (§14).
4. Mac or iPhone invokes navigator.credentials.create() (or the native
   platform equivalent) with those options.
5. The physical security key performs the makeCredential ceremony locally
   on the client device — the private key never leaves the device, and no
   ceremony byte crosses the network except the final WebAuthn response.
6. The client returns the WebAuthn registration response (attestationObject,
   clientDataJSON, credential.id) to the PCAE server.
7. PCAE server independently verifies the response per §16.
8. PCAE server derives HardwareCredentialRecord fields per §10 and persists
   via HHCE-001's existing protected writer, unmodified.
```

No step in this flow is implemented by this contract; the sequence is normative for whichever phase implements it.

## 9. Pre-hardware governance ordering

**HRWP-REQ-016.** The invariant repaired for the local path by Phase 149O.20L.7O.2N.1/149O.20L.7O.2N.2 (governance authorization strictly before any hardware credential ceremony) SHALL apply identically to remote enrollment: the PCAE server MUST NOT issue a registration challenge (§8 step 2) until the governed operation is already authorized. The client receives only an already-authorized, short-lived ceremony request — it never itself carries or grants authorization.

## 10. WebAuthn registration evidence mapping

**HRWP-REQ-017.** A WebAuthn registration response's `credential.id` (WebAuthn credential ID, base64url on the wire) maps to `HardwareCredentialRecord.signer_key_id` (hex-encoded), identically in kind to how `Fido2HardwareProvider.enroll_credential()`'s `credential_data.credential_id` maps to `EnrolledFido2Credential.credential_id_hex` today (`hatp_fido2_provider.py`) — both are the raw CTAP2 `makeCredential` credential-ID bytes; WebAuthn's browser layer only changes the wire encoding (base64url vs. this module's raw hex), not the underlying identity value.

**HRWP-REQ-018.** The registration response's COSE public key (extractable from `attestationObject.attStmt`/`authData.attestedCredentialData.credentialPublicKey`, CBOR-encoded) maps to `HardwareCredentialRecord.public_key`, identically in format to the existing FIDO2 provider's `cbor.encode(cose_key)` output — both are CBOR-encoded COSE_Key bytes, the exact format `CoseKey.parse(cbor.decode(record.public_key))` already consumes on the verification side (`hatp_fido2_provider.py`). **No `HardwareCredentialRecord`/HHCE-001 schema field changes are required for registration evidence** — every field HHCE-001 v1.1 already defines (`signer_key_id`, `provider_profile`, `protocol_name`, `algorithm`, `public_key`, `status`, `revoked_at`) is populatable from a WebAuthn registration response.

**HRWP-REQ-019 (revised, v1.1 — corrects an inaccurate v1.0 closed-vocabulary claim; full rationale at §45).** `HardwareCredentialRecord.provider_profile` SHALL be `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN` (§4) for a remote-WebAuthn-enrolled record. `protocol_name` SHALL be `"WEBAUTHN"` — a new value alongside the existing `"FIDO2" | "PIV"`. This requires **no `HardwareCredentialRecord` structural schema widening**: no new field, no change to any other field's type or meaning (§10/HRWP-REQ-018/056, unchanged by this revision). It DOES, separately, require an **additive closed-vocabulary widening**: `hatp_hardware_credentials.py::_parse_credential` enforces `protocol_name` against a closed `_PROTOCOL_VALUES = frozenset({"FIDO2", "PIV"})` allowlist in code today — this is a closed enum in code, not the open/unvalidated plain string field v1.0's text here incorrectly assumed. A real `HardwareCredentialRecord` with `protocol_name="WEBAUTHN"` is therefore rejected as malformed (`HATPHardwareCredentialStoreMalformedError`) by current production until `_PROTOCOL_VALUES` is additively widened to include `"WEBAUTHN"` — a narrow, one-line, mechanically obvious future code change (§12) confined to that frozenset, requiring no other production or schema change and no HMIC-001 change on its own. This closed-vocabulary discipline is itself a security property (fail-closed rejection of unrecognized `protocol_name` values, §13) and SHALL NOT be relaxed to an open string merely to avoid this future edit. Schema shape (unchanged) and closed vocabulary (must additively expand before real enrollment) are two distinct claims; this requirement's text SHALL NOT blur them.

**HRWP-REQ-020.** `algorithm` maps from the negotiated COSE algorithm identifier exactly as the local path already does (`type(cose_key).__name__`, e.g. `"ES256"`) — no new derivation logic, same COSE algorithm space.

**HRWP-REQ-021.** RP identity (`rp.id` used at registration) is not itself a `HardwareCredentialRecord` field (mirroring HHCE-REQ-006's precedent of excluding audit/context metadata from the record) — it is enforced structurally by verification (§16), not stored per-credential, since §13 fixes one RP ID for the whole remote-WebAuthn provider, not a per-credential value.

**HRWP-REQ-022.** Attestation data, if produced by the authenticator, MAY be retained as audit-event metadata (mirroring HHCE-REQ-006's disposition for `enrolled_at`/`enrollment_reference`) but is NOT a `HardwareCredentialRecord` field — consistent with §12's attestation-policy determination.

**HRWP-REQ-023.** Transports (`response.getTransports()`, e.g. `["usb", "nfc"]`) MAY be retained as audit-event metadata for operational/diagnostic purposes only. They SHALL NOT be treated as part of credential identity (§5/§6) and SHALL NOT be persisted as a `HardwareCredentialRecord` field.

## 11. Attestation policy

**HRWP-REQ-024.** Neither of PCAE's two current provider profiles requires or evaluates authenticator (manufacturer/device) attestation today: `Fido2HardwareProvider.capabilities()` reports `device_attestation=False`, and `verify()` always returns `attestation_valid=None` ("this provider profile does not evaluate attestation," a documented, non-blocking limitation per `HardwareProviderConformance.CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS`). Per HRWP-REQ-002/§12 of the governing prompt ("if current HHCE does not require attestation, do not add it casually"), `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN` SHALL likewise NOT require device attestation as a gating condition for registration in v1.0 of this contract. **This is a deliberate parity choice with the existing local provider, not an oversight** — remote enrollment is not held to a stricter attestation bar than local enrollment already is.

**HRWP-REQ-025.** Credential possession / public-key establishment (what `makeCredential` always produces) is distinguished from manufacturer/device attestation (an optional, separately-evaluated `attestationObject` trust chain) — this contract requires only the former, exactly as the local path does today.

## 12. RP ID — load-bearing, resolved as an open infrastructure requirement

**HRWP-REQ-026.** The existing local/raw path's `_HATP_RP_ID = "hatp.pcae.local"` / `_HATP_ORIGIN = "pcae-hatp://hatp.pcae.local"` (`hatp_fido2_provider.py`) are non-resolvable, non-HTTPS internal constants, deliberately chosen because raw CTAP2 "is not a web origin" (module docstring). A real browser WebAuthn implementation enforces the actual page origin as `clientDataJSON.origin` and validates `rp.id` against that origin's effective domain per the WebAuthn specification — it will not allow a page to mint an assertion claiming the existing internal origin string. **These constants are therefore NOT reusable, unmodified, for a browser-mediated remote-WebAuthn RP ID/origin.** This is the single largest architectural difference between the two providers, and this contract does not conceal it (per the governing prompt's explicit instruction not to).

**HRWP-REQ-027.** `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN` SHALL use its own, distinct, real-domain-form RP ID — a stable hostname PCAE (or a governed companion service in front of hac-dell) is reachable at over HTTPS. This contract does NOT select a literal hostname value: no PCAE-controlled domain, LAN name, or reverse-proxy hostname has been provisioned or decided as of this freeze (§54 No-Go: "do not provision any of these yet"). **This is an explicit open requirement for the implementation phase**, not a silent gap: the implementation phase MUST fix a concrete RP ID string as part of its own scoped work, satisfying: (a) a stable, non-`localhost`, non-raw-IP, non-per-session value (HRWP-REQ-028); (b) resolvable via DNS or an equivalent mechanism reachable from both a Mac browser and an iPhone browser (§16 of the governing prompt); (c) matching the origin the client actually loads the ceremony page from.

**HRWP-REQ-028.** The RP ID SHALL NOT be: `localhost` or any `localhost`-equivalent, a raw IP address, or a value that varies per session/ceremony. WebAuthn credentials are permanently scoped to the RP ID present at registration time; a per-session or per-ceremony RP ID would make every credential registered under it uninvokable under any other RP ID, silently fragmenting the credential the human believes they registered once.

## 13. Origin model

**HRWP-REQ-029.** Allowed WebAuthn origins SHALL be exactly `https://<the RP-ID-matching stable host>` (or the small number of origin variants, e.g. with/without a non-default port, the implementation phase's concrete deployment actually serves) — never `http://`, never a wildcard, never an origin derived from caller-supplied input. Mac and iPhone ceremonies for the *same* credential MUST resolve to the *same* RP ID and an allowed origin under it, so that one registered credential is invocable from both platforms (§16 of the governing prompt's "Mac + iPhone common origin" requirement) — this is satisfied automatically once HRWP-REQ-027's single stable RP ID is fixed, since WebAuthn origin/RP-ID matching is browser-platform-neutral by specification, not something PCAE must special-case per client platform.

**HRWP-REQ-030.** Origin validation SHALL be performed server-side by PCAE against `clientDataJSON.origin`, in addition to (not instead of) the browser's own origin enforcement — mirroring the existing local provider's own explicit `parsed.client_data.origin != _HATP_ORIGIN` check (`hatp_fido2_provider.py`, `verify()`), applied to the new fixed origin value instead.

## 14. HTTPS / certificate requirement — named, not provisioned

**HRWP-REQ-031.** A real remote-WebAuthn client requires TLS: WebAuthn's specification requires a secure context (`https:`) for `navigator.credentials.create()`/`.get()` in all mainstream browsers, with no PCAE-side exception possible. This contract does not select a certificate authority (public CA vs. private/internal CA), reverse-proxy topology, DNS provider, or LAN/VPN-only vs. public reachability model — each is named here as an **explicit infrastructure requirement the implementation phase must resolve**, per §15 of the governing prompt ("do not provision any of these yet; say exactly what infrastructure a later phase must provide"):

- A DNS name resolvable by both the Mac and the iPhone's actual network path (which may differ from each other and from hac-dell's LAN).
- A TLS certificate valid for that DNS name, from either a publicly-trusted CA (simplest client compatibility, if the name is a real public domain) or a private CA the Mac/iPhone are provisioned to trust (more infrastructure, avoids exposing a public DNS name for a personal deployment).
- A TLS-terminating endpoint reachable from both client platforms — directly on hac-dell, or via a reverse proxy in front of it — network topology (LAN-only, VPN-gated, or public) is an operational decision this contract does not make.

## 15. Mac + iPhone common origin

**HRWP-REQ-032.** One stable HTTPS PCAE-controlled origin (HRWP-REQ-027/HRWP-REQ-029) SHALL serve both a Mac browser and an iPhone browser ceremony, with hac-dell remaining the sole authoritative backend for challenge issuance and verification regardless of which client platform connects. This is architecturally satisfied by construction once one RP ID / origin pair is fixed (§12/§13) — no per-platform branching is required in the server-side contract this document defines; any client-side platform differences (§17-§20) are presentation/UX concerns, not governance-identity concerns (§2).

## 16. Server verification requirements (registration and assertion)

**HRWP-REQ-033.** PCAE server-side verification of a WebAuthn response (registration or assertion) SHALL check, at minimum: (a) the challenge matches the exact one PCAE issued and has not already been consumed (§22); (b) `clientDataJSON.origin` matches the fixed allowed origin (§13); (c) `clientDataJSON.type` matches the expected ceremony type (`webauthn.create` or `webauthn.get`); (d) `authData.rpIdHash` matches SHA-256 of the fixed RP ID (§12), mirroring the existing local provider's own `parsed.authenticator_data.rp_id_hash != _RP_ID_HASH` check; (e) for assertions, the credential ID is a member of the server-constructed `allowCredentials` set (§7); (f) the signature verifies against the stored public key; (g) the user-presence flag is set (§17); (h) user-verification, if required by policy (§17), is set; (i) for registration, attestation is evaluated only if HRWP-REQ-024's non-requirement is later revised; (j) the challenge/session has not expired (§21/§22).

**HRWP-REQ-034.** Every check in HRWP-REQ-033 SHALL fail closed (reject the ceremony) on any single failure, exactly as `Fido2HardwareProvider.verify()`'s existing discipline already fails closed per-check rather than accumulating partial trust — this contract requires the same discipline for the new provider, not a weaker one.

## 17. User verification policy

**HRWP-REQ-035.** This contract fixes: `userVerification: "preferred"` for both registration and assertion ceremonies, and `userPresence` (implicit in every WebAuthn ceremony) as always required. Rationale: HATP-001's text requires "human-presence," not biometric/PIN user-verification specifically — identical to the local provider's own documented choice (`hatp_fido2_provider.py`: "UP, not UV — HATP-001's text says 'human-presence', not 'user verification'/biometric"). `"preferred"` (rather than `"required"`) avoids silently rejecting a ceremony on a client/authenticator combination that cannot perform UV, while still using it when available, and avoids inferring a PIN requirement from platform defaults (per the governing prompt's explicit caution). This is an explicit, frozen setting, not a default left to a future implementer's discretion.

## 18. Authenticator selection

**HRWP-REQ-036.** For assertion (signing) ceremonies, the server SHALL populate `allowCredentials` with exactly the resolved, expected credential ID(s) per §7 — never an empty/omitted list that would let the client's platform choose arbitrarily among all registered discoverable credentials.

**HRWP-REQ-037.** For registration ceremonies, physical authenticator choice occurs entirely client-side (the human decides which key to touch); the governance confirmation obtained per §9 authorizes creation of **one** credential under this provider profile and policy, not any specific future credential ID — identical in kind to how the existing local `enroll_credential()` ceremony's governance confirmation precedes, and is independent of, whichever physical device happens to be `devices[0]` at ceremony time.

## 19. Client trust model

**HRWP-REQ-038.** The Mac/iPhone client is not trusted to assert credential identity, `Principal`, `Signer`, an authorization result, or a challenge value. It MAY only: receive server-issued ceremony options, invoke the platform's own WebAuthn API with them unmodified, and return the platform-produced result verbatim. hac-dell validates everything (§16); mere possession of a working ceremony URL (§25/§26 of the governing prompt) is never itself authorization.

## 20. Session / challenge structure

**HRWP-REQ-039.** A PCAE-issued remote-WebAuthn challenge context SHALL bind, at minimum: `repository_id` (RepositoryIdentity), `canonical_deployment_root`, `operation_type` (e.g. `enrollment` | `assertion`), `provider_profile` (§4), `phase_or_session_identifier`, a fresh random `nonce`, `issued_at`, `expires_at`, the `expected_rp_id` (§12), the `allowed_credential_ids` where applicable (§7/§18), and the resolved `principal_id`/`signer_key_id` where applicable (assertion ceremonies only — not yet resolvable for a first-ever enrollment). This context is PCAE-owned server-side state, not derived from or trusted from opaque browser session state alone.

## 21. Challenge replay protection

**HRWP-REQ-040.** Every issued challenge SHALL be one-time-use, server-side-consumed on first valid use (accept-and-invalidate, not merely accept), and SHALL carry a short, fixed expiry (an exact duration is an implementation-phase parameter, not fixed by this contract, but SHALL be short — minutes, not hours, consistent with HSCE-001's own precedent of short-lived signing ceremonies). A verification attempt SHALL be rejected if: the challenge has already been consumed, the challenge has expired, the challenge does not match the one issued for this exact `repository_id`/`operation_type`/`provider_profile` (§20), the credential used is not in `allowed_credential_ids` (§18), or the response's origin does not match (§13).

## 22. Session binding

**HRWP-REQ-041.** The browser/mobile session invoking a given ceremony SHALL be bound to the server-issued challenge via a single-use, unguessable, server-generated identifier embedded in the ceremony delivery mechanism (§25) — e.g. a single-use URL path component or signed request identifier — rather than a long-lived bearer cookie or token that would itself become a standing authority artifact. This contract does not select the exact mechanism (single-use URL vs. signed request ID vs. another equally narrow option) as a fixed literal; it fixes the requirement that whichever mechanism is chosen be single-use and scoped to exactly one challenge, never a reusable or long-lived credential in its own right.

## 23. CSRF / cross-session protection

**HRWP-REQ-042.** The WebAuthn response returned to PCAE SHALL be verified to resolve to the exact server-generated governed request it was issued for (§20/§22) — cross-tab, cross-device, and cross-session substitution SHALL be rejected by the same single-use challenge-binding mechanism (§21/§22), not by a separate CSRF-token layer bolted on afterward. No requirement in this contract introduces a second, independent session-identity concept beyond the challenge/session binding already required.

## 24. Remote ceremony delivery

**HRWP-REQ-043.** The ceremony is delivered to the human as a short-lived HTTPS URL, openable on Mac or iPhone, which the human's browser loads to begin the WebAuthn ceremony. QR code, deep link, or manual URL entry are all acceptable convenience presentations of the same underlying single-use URL (§22) — this contract does not mandate one over another.

**HRWP-REQ-044.** Telegram (or any other outbound notification channel already used elsewhere in this repository) MAY be used to *deliver* the ceremony link, exactly as an outbound notification, and SHALL NOT become an inbound authority channel — receiving/opening the message is never itself proof of anything beyond "a link was opened" (§25/§26 below restate this as a standing rule, not a Telegram-specific one).

## 25. Authorization ≠ ceremony-link possession

**HRWP-REQ-045.** Possessing or opening the ceremony URL SHALL NOT itself constitute PCAE governance authority. The server MUST already hold the correct governed authorization state (§9) before issuing the challenge the URL carries; the URL exists only to start the cryptographic possession ceremony a human has already been authorized to perform.

## 26. Assertion / signing — the raw-CTAP-vs-WebAuthn semantic analysis

**HRWP-REQ-046.** Both the existing local/raw `Fido2HardwareProvider.request_signature()`/`.verify()` and a browser-mediated remote WebAuthn assertion produce the **same underlying cryptographic construction**: a signature over `authenticatorData || SHA-256(clientDataJSON)`, where `clientDataJSON` embeds a caller-supplied `challenge` field. This is confirmed directly from `hatp_fido2_provider.py`'s own module docstring and `verify()` implementation (`cose_key.verify(bytes(parsed.authenticator_data) + parsed.client_data.hash, parsed.signature)`) — the local provider already speaks the WebAuthn/CTAP2 assertion wire format, not an arbitrary raw-bytes signature scheme. **This materially narrows the semantic gap the governing prompt's §27/§28 flagged as the hardest open question**: the divergence between the two providers is not "PCAE requires a raw signature over arbitrary envelope bytes that WebAuthn cannot provide" — PCAE's existing HATP FIDO2 signing already *is* a WebAuthn-shaped `getAssertion` ceremony. The genuine divergence, confirmed by source (Phase 149O.20L.7O.2N.6 §15 and independently re-confirmed reading the same code this phase), is narrower and specific: **origin/RP-ID enforcement**. The local provider hand-constructs `clientDataJSON` with a fixed, non-browser-enforced origin/RP-ID pair (§12); a real browser enforces the page's actual origin and validates `rp.id` against it, and will not let a page mint `clientDataJSON.origin = "pcae-hatp://hatp.pcae.local"`.

**HRWP-REQ-047.** Because the cryptographic construction is identical and only the origin/RP-ID pair differs, a WebAuthn-specific signing proof model IS achievable without inventing an incompatible evidence scheme: PCAE computes the exact same canonical-payload digest (`sha256(canonical_payload)`) it uses today, binds that digest into the browser WebAuthn ceremony's `challenge` field exactly as the local provider already does, and verifies the resulting assertion the same way `Fido2HardwareProvider.verify()` already does — swapping only the expected `origin`/`rp_id_hash` constants for the remote provider's own fixed values (§12/§13), and swapping the evidence wire encoding (§27) for whatever a browser's `PublicKeyCredential` response actually returns.

**HRWP-REQ-048.** **Conclusion (governing prompt §31): remote WebAuthn signing is SUPPORTED VIA A NEW, PROVIDER-SPECIFIC ASSERTION PROFILE that reuses the existing signature-verification algorithm and challenge-binding technique unmodified, differing only in (a) `provider_profile`/`protocol_name` routing (§4/§10), (b) the RP-ID/origin constants (§12/§13), and (c) the evidence serialization format (§27) — NOT via an incompatible cryptographic scheme requiring new HSCE-001 verification semantics.** This is a more favorable finding than Phase 149O.20L.7O.2N.6's own necessarily-cautious "requires additional contract work" framing left open — that phase correctly declined to assume equivalence without formalizing it; this contract performs that formalization and finds the two providers' underlying cryptography already compatible in kind. What genuinely remains additional, non-trivial work for the implementation phase (named explicitly, not concealed) is: (i) HSCE-001 itself does not yet define how `pcae hatp sign rollback`'s CLI-driven, synchronous, single-process ceremony model extends to an asynchronous, network-mediated, browser-round-trip ceremony — that orchestration-layer question is out of this contract's scope and SHALL be resolved by whichever phase amends or companions HSCE-001 for remote ceremonies; (ii) the RP-ID/HTTPS infrastructure named in §14 must exist before any real remote assertion can be produced or verified.

## 27. WebAuthn assertion evidence mapping

**HRWP-REQ-049.** A remote-WebAuthn assertion response's `authenticatorData`, `clientDataJSON`, and `signature` fields map directly onto the existing FIDO2 evidence schema's `authenticator_data_hex`, `client_data_json_hex`, and `signature_hex` fields (`hatp_fido2_provider.py`, `_serialize_evidence()`) — same field *kinds*, produced by a browser's WebAuthn API instead of this module's own `Ctap2.get_assertion()` call. `credential_id_hex` maps identically (§10/HRWP-REQ-017).

**HRWP-REQ-050.** `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN`'s evidence format SHALL be a distinct, strictly-versioned, closed-field JSON schema — structurally identical in discipline to `_EVIDENCE_SCHEMA_VERSION`/`_EVIDENCE_FIELDS` (`hatp_fido2_provider.py`: reject unknown fields, reject missing fields, reject unsupported version, reject duplicate JSON keys) — carrying the same four cryptographic fields (§HRWP-REQ-049) plus nothing else. It is a distinct schema instance from the local provider's (not a shared/overloaded one), consistent with §4's provider-profile-based routing requirement, even though its field *names* and *kinds* may be identical.

**HRWP-REQ-051.** A future implementation SHALL NOT reuse `hatp_fido2_provider.py`'s exact evidence-parsing functions unmodified against browser-sourced bytes without first confirming the browser's `PublicKeyCredential.response.authenticatorData`/`.clientDataJSON`/`.signature` byte encodings match what `AuthenticatorData`/`CollectedClientData` (the `fido2` library's own classes, already used for parsing) expect — this contract asserts field-kind compatibility (HRWP-REQ-049), not byte-identical wire compatibility, which is an implementation-phase verification task.

## 28. Multiple WebAuthn credentials / allow-list

**HRWP-REQ-052.** Restates §7/§18: `allowCredentials` is always populated from PCAE's own registry, scoped by the resolved `DeploymentBinding` (§6), never from client-asserted input.

## 29. Backup key / revocation model

**HRWP-REQ-053.** A second physical key becomes usable via a separate `HardwareCredentialRecord` enrollment (§8) and a separate `SignerRecord` enrollment (HPSE-001's existing `enroll_signer`, unmodified), under the same `Principal` — never by cloning, manual import, or treating two distinct physical keys as cryptographically equal. This mirrors Phase 149O.20L.7O.2N.6 §14's "no cloning assumption" finding for the local path exactly.

**HRWP-REQ-054.** Revoking a `HardwareCredentialRecord` (HHCE-001's existing revocation surface, unmodified) SHALL remove that credential from future `allowCredentials` construction (§7) and from future signing selection, for both local and remote providers identically — revocation is provider-profile-agnostic, since it operates on the shared registry, not on provider-internal state. Other active credentials remain usable per existing policy; revocation SHALL NOT cascade to other records or automatically rebind `DeploymentBinding` (HHCE-REQ-043's existing discipline, unchanged).

## 30. Lost-all-keys limitation (explicitly preserved, not solved here)

**HRWP-REQ-055.** If all hardware credentials for a `Principal` are lost or revoked, this contract creates no unauthenticated recovery shortcut. Recovery requires a separately governed identity/authority process, out of scope for this contract and for remote WebAuthn specifically — identical in kind to the existing local-path limitation, not weakened or strengthened by adding a remote provider.

## 31. `HardwareCredentialRecord` impact

**HRWP-REQ-056.** No `HardwareCredentialRecord`/HHCE-001 schema field changes are required (§10/HRWP-REQ-018). The existing schema already represents remote-WebAuthn-enrolled credentials once `provider_profile`/`protocol_name` carry the new values this contract defines (§4/HRWP-REQ-019).

## 32. `SignerRecord` impact

**HRWP-REQ-057.** No `SignerRecord`/HPSE-001 schema field changes are required. `SignerRecord.provider_profile` SHALL carry `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN` for a remote-WebAuthn-sourced signer, exactly as it already carries `HATP_HARDWARE_PROVIDER_V1` for the local path — no new field, no browser/client identity stored as signer identity (Model B, §2, preserved).

## 33. `DeploymentBinding` impact

**HRWP-REQ-058.** No `DeploymentBinding`/HBDC-001 schema change is required. Phase 149O.20L.7O.2N.6 confirmed, and this contract re-confirms from the same source read (`hatp_bootstrap.py`), exactly one active `DeploymentBinding` per `repository_id` — this continues to reference one selected `(principal_id, signer_key_id)` pair regardless of whether that signer's credential was enrolled locally or remotely; the binding record itself carries no protocol/transport information and needs none.

## 34. Multi-credential policy (restated as the frozen decision)

**HRWP-REQ-059.** One `Principal` MAY have multiple active `SignerRecord`s/credentials (local and/or remote-WebAuthn). Each governed signing operation SHALL resolve to exactly one `signer_key_id` via the existing `DeploymentBinding` selection mechanism (§6/HRWP-REQ-013), or, for a future ceremony type that explicitly supports an allow-list rather than a single binding, an explicitly server-constructed allow-list (§7) — never "any available key" chosen by the client.

## 35. HSCE-001 relationship (named gap, not resolved here)

**HRWP-REQ-060.** HSCE-001 v1.3 governs `pcae hatp sign rollback`'s CLI surface and evidence-store format for the existing, synchronous, single-process signing ceremony. This contract does NOT amend HSCE-001. A future phase companion to (or revising) HSCE-001 MUST define: how a remote, asynchronous, browser-round-trip ceremony's evidence is captured into `.pcae/hatp-evidence/` (or an equivalent store) with the same atomicity/no-clobber discipline HSCE-001 v1.3 already requires for the local path; and whether `pcae hatp sign rollback` gains a remote-ceremony mode or a distinct CLI/API surface exists instead. This contract fixes only the cryptographic/evidence-format compatibility question (§26/§27) that a future HSCE-001-adjacent contract will depend on.

## 36. Future HMIC-001 consequence (named, not amended)

**HRWP-REQ-061.** No HMIC-001 amendment occurs in this contract (§52 No-Go). A future implementation of the components this contract names — a remote-WebAuthn server verifier module, a challenge/session manager, a `RemoteWebAuthnProvider` adapter, a registration-evidence mapper, an assertion verifier, and possibly a ceremony-delivery HTTP endpoint — will each become new authority-bearing source requiring HMIC-001 source-scope inclusion and independent verification before activation, exactly as `hatp_fido2_provider.py` itself already required (its own module docstring). This is flagged here for the eventual implementation sequence, not undertaken now.

## 37. Trusted-kernel vs. adapter boundary

**HRWP-REQ-062.** Inside PCAE's trusted governance kernel (subject to HMIC-001 scope, §36): challenge construction and binding (§20), authority/governance-ordering enforcement (§9), the credential allow-list (§7/§28), server-side response verification (§16/§26/§27), and registry writes (HHCE-001/HPSE-001, unmodified). Replaceable/thin, outside the trusted kernel: the HTTP transport layer, the browser-facing ceremony page's presentation, and mobile-app presentation layers, if any — these carry no independent trust; they only relay bytes the trusted kernel produces and validates.

## 38. USB-over-IP disposition

**HRWP-REQ-063.** USB-over-IP (Mac → hac-dell, evaluated by Phase 149O.20L.7O.2N.6 §18) is classified **EXPERIMENTAL, NOT THE PRIMARY ARCHITECTURE** by this contract. It reuses the existing raw-CTAP `Fido2HardwareProvider` code path unmodified, avoiding the RP-ID/HTTPS work this contract requires, but is Mac-only (no comparable iPhone path), introduces a network-transport dependency with its own reconnect/exclusivity failure modes, and does not address the human's stated iPhone/NFC requirement. It MAY remain a documented fallback option for Mac-only use cases; it SHALL NOT be treated as satisfying this contract's Mac+iPhone scope (§1).

## 39. Direct-hac-dell raw FIDO2 disposition

**HRWP-REQ-064.** The existing local/raw `Fido2HardwareProvider` path SHALL be retained unmodified. A directly-attached hac-dell authenticator remains a supported, first-class path — hybrid means additive, not a deprecation of the local path (governing prompt §46). Nothing in this contract requires, schedules, or implies removing or modifying `hatp_fido2_provider.py`.

## 40. Known limitations

**HRWP-REQ-065.** This contract records, without resolving, the following known limitations for the implementation phase's awareness: iOS security-key WebAuthn support is exposed only through the platform's WebAuthn/native APIs, never arbitrary raw CTAP forwarding; a plain YubiKey 5C has no NFC (USB-C only); NFC-capable authenticators require tap-proximity and a bounded session window whose exact current-iOS-version behavior is unverified by this contract or its predecessor phase; browser WebAuthn implementations may differ in supported transport/UV combinations; the remote ceremony requires live network reachability from the client to the fixed RP-ID/origin (§12/§13) — no offline remote ceremony is possible; WebAuthn assertions/attestations are RP/origin-bound by specification, never portable across RP IDs; **WebAuthn enrollment support does not, by itself, imply the exact same evidence bytes are automatically consumable by HSCE-001's existing evidence store without the companion work named in §35**; the physical authenticator remains required locally to the human at ceremony time in every case — no scenario in this contract eliminates that requirement.

## 41. Device/platform compatibility matrix (carried forward from Phase 149O.20L.7O.2N.6 §12/§17, evidence-based, not re-derived)

| Device | Mac USB-C (local raw or remote-WebAuthn client) | iPhone USB-C (remote-WebAuthn client only) | iPhone NFC (remote-WebAuthn client only) | hac-dell direct (local raw) |
|---|---|---|---|---|
| Security Key C NFC by Yubico (currently attached, Mac) | Yes | UNKNOWN (platform-version-dependent, unverified) | UNKNOWN (platform-version-dependent, unverified) | Yes, if physically attached there (currently: zero devices attached) |
| YubiKey 5C (no NFC) | Yes | UNKNOWN | Not applicable (no NFC hardware) | Yes, if attached |
| YubiKey 5C NFC | Yes | UNKNOWN | UNKNOWN (platform-version-dependent, unverified) | Yes, if attached |

This matrix is unchanged from Phase 149O.20L.7O.2N.6's own findings; this contract adds no new hardware verification, per its architecture-freeze-only scope.

## 42. Implementation sequence (non-binding ordering, for the next phase's planning only)

**HRWP-REQ-066.** A safe implementation sequence, subject to the next phase's own dependency analysis (this contract does not bind it): (1) independent verification of this contract; (2) HSCE-001-companion contract for remote-ceremony evidence capture (§35); (3) server-side challenge issuance + verification implementation (hac-dell-side only, still no client); (4) minimal browser WebAuthn ceremony client; (5) synthetic interoperability tests (no real hardware); (6) independent verification of steps 3-5; (7) HMIC-001 source-scope expansion (§36); (8) deployment + recertification; (9) first real remote WebAuthn registration (a narrowly-scoped phase on its own, mirroring the existing local-path precedent of not combining enrollment with Principal/Signer creation); (10) Principal/Signer enrollment against the new credential; (11) signing/assertion verification track, gated on step 2's resolution.

## 43. What this contract does NOT do

**HRWP-REQ-067.** This contract creates no real WebAuthn credential, invokes no `makeCredential`/`getAssertion` against real hardware, alters no state of the currently-attached Security Key C NFC, implements no server or client code, creates no HTTPS endpoint, modifies no DNS/TLS configuration, modifies no HMIC-001 record, performs no redeployment, creates no protected record, activates no HATP production state, and changes no Permission Broker/runtime policy. It is architecture and contract text only.

## 45. v1.1 Repair (Phase 149O.20L.7O.2N.11, Closes NBF-149O.20L.7O.2N.8-1)

Phase 149O.20L.7O.2N.8's independent verification found NBF-149O.20L.7O.2N.8-1 (Non-Blocking): HRWP-REQ-019's v1.0 text asserted `protocol_name="WEBAUTHN"` "requir[es] no schema widening," relying on HHCE-REQ-002's descriptive comment that `protocol_name` is "a plain string field, not a closed enum in code." That reliance was inaccurate: `hatp_hardware_credentials.py::_parse_credential` (read directly this phase, unchanged since 149O.20L.7O.2N.8/2N.10 re-derived it) enforces `protocol_name in _PROTOCOL_VALUES` where `_PROTOCOL_VALUES = frozenset({"FIDO2", "PIV"})` — a closed allowlist in code, not an open string. A real `HardwareCredentialRecord` with `protocol_name="WEBAUTHN"` would be rejected today (`HATPHardwareCredentialStoreMalformedError`, raised at `hatp_hardware_credentials.py:225`) until that frozenset is additively widened. Phase 149O.20L.7O.2N.10's independent verification of HRAC-001 independently reconfirmed this finding (that contract's §44/HRAC-REQ-066) and confirmed it does not block HRAC-001's own internal coherence, since HRAC-001's signer-resolution path never reads `protocol_name`.

This repair does **not** change the schema-shape claim, which was always accurate and independently confirmed twice: no new field is required on `HardwareCredentialRecord`, `SignerRecord`, or `DeploymentBinding` for remote WebAuthn (§10/§31-§33, HRWP-REQ-018/056-058, all unchanged). It corrects only the **closed-vocabulary** claim: `HRWP-REQ-019`'s text now states explicitly that production's `_PROTOCOL_VALUES` is closed in code and that accepting a real `protocol_name="WEBAUTHN"` record requires an additive widening of that frozenset — a narrow, one-line, mechanically obvious future code change, not a structural schema change and not a security-property weakening (unknown values remain rejected fail-closed both before and after that future widening). This is the same "narrative-vs-code discrepancy, repaired in place without blocking" discipline HHCE-001 v1.1 §30 already precedented for this same module family.

**Version consequence.** A normative requirement's text changed (`HRWP-REQ-019`), so per this repository's established convention (HHCE-001 v1.0→v1.1, HPSE-001 v1.0→v1.1) this is the smallest justified version change: HRWP-001 is bumped 1.0 → 1.1. No other requirement's text changes. No requirement is added, removed, or renumbered; the requirement count remains 68 (§46).

**Downstream contract impact, independently checked this phase:**

- **HRAC-001:** No amendment, no version bump. HRAC-001 v1.0's §44/HRAC-REQ-066 already names this exact finding accurately as "carried forward, not resolved" and already states HRAC-001's own signer-resolution reuse (§9) never reads `protocol_name` — this repair does not change HRAC-001's dependency-graph claims about HRWP-001, since HRAC-001 never asserted "no vocabulary widening required" in the first place, only HRWP-REQ-019 did.
- **HSCE-001:** No amendment, no version bump. HSCE-001 is unamended by HRWP-001 v1.0 and remains unamended by this repair; nothing in HSCE-001's own text made the corrected claim.
- **HHCE-001:** No amendment, no version bump. `HHCE-REQ-002`'s own text ("a plain string field, not a closed enum in code") is a comment about `HardwareCredentialRecord`'s Python dataclass type annotation (`protocol_name: str`), which is accurate on its own terms — the dataclass field itself is untyped beyond `str`. The closed-enum enforcement HRWP-REQ-019 needed to account for lives in the *parser* (`_parse_credential`'s `if protocol_name not in _PROTOCOL_VALUES` check), a distinct claim from the dataclass field's own type. HHCE-001 never claimed the parser has no closed-vocabulary check — HRWP-REQ-019 v1.0 over-read HHCE-REQ-002's narrower claim. No HHCE-001 text is inaccurate; no amendment is required.

**Implementation prerequisite frozen by this repair (not performed this phase):** add exactly one value, `"WEBAUTHN"`, to `_PROTOCOL_VALUES` in `hatp_hardware_credentials.py`, plus focused tests confirming the widened set accepts `"WEBAUTHN"` and continues to reject any other unknown value. No other production change is implied by this repair.

**Finding status:** REPAIRED — INDEPENDENT VERIFICATION PENDING. Not marked independently closed by this phase (§19 of the governing prompt).

## 44. Requirement count

**HRWP-REQ-068.** This contract defines 68 normative requirements, `HRWP-REQ-001` through `HRWP-REQ-068`, sequential, no gaps, no duplicates. This count is unchanged by the v1.1 repair (§45): `HRWP-REQ-019` was revised in place, not added, removed, or renumbered.
