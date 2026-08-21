# Phase 149O.20L.7O.2N.7 — Remote WebAuthn Provider Contract and Ceremony Architecture Freeze

**Status:** COMPLETE — CONTRACT/ARCHITECTURE FREEZE ONLY. NO IMPLEMENTATION. NO WEBAUTHN SERVER. NO CLIENT. NO CREDENTIAL CREATED. NO HMIC CHANGE. NO REDEPLOYMENT.

## 1. Phase entry

- True phase-entry commit (local HEAD == origin/main at phase start): `651f7df2` (149O.20L.7O.2N.6's report-finalization-gate repair commit — the phase this one directly follows).
- Latest completed phase: 149O.20L.7O.2N.6 — hac-dell FIDO2 Physical Authenticator Inspection and Multi-Authenticator / Remote-WebAuthn Architecture.
- `git status --short` clean at phase start; `pcae session bootstrap --agent-id claude-local --sync-lock` confirmed agent lock healthy, active task the post-2N.6 idle placeholder, push clean/nothing-to-push.

## 2. Entering Security Key C NFC evidence (carried forward, not re-derived)

Phase 149O.20L.7O.2N.6 established, and this phase treats as given (no hardware re-inspection performed — read-only architecture work only):

- Current human-side physical authenticator: **Security Key C NFC by Yubico**, firmware 5.7.4, FIDO2 Level 2 certified, AAGUID `b7d3f68e-88a6-471e-9ecf-2df26d041ede`.
- Transports self-reported: `['nfc', 'usb']`.
- Attached directly to the Mac's native USB-C controller, no intervening hub.
- Zero FIDO2 devices attached to hac-dell directly.
- Trust-Enrollment records (`HardwareCredentialRecord`, `Principal`, `Signer`, `DeploymentBinding`): all absent.
- HMIC v1.7/38 active certification: VALID.

## 3. Current multi-credential capability (re-derived from source, this phase)

Read fresh: `src/pcae/core/hatp_hardware_credentials.py`, `src/pcae/core/hatp_bootstrap.py`, `src/pcae/core/hatp_providers.py`, `src/pcae/core/hatp_fido2_provider.py`.

- `HardwareCredentialRecord` registry already parses a JSON array into `Dict[str, HardwareCredentialRecord]` keyed by `signer_key_id` — arbitrary simultaneous active credentials already supported, no schema change.
- `SignerRecord` is keyed by `signer_key_id` only; `principal_id` is not a uniqueness key — one `Principal`, many `SignerRecord`s is already valid.
- `DeploymentBinding` is keyed by `repository_id`, exactly one active binding per repository — confirmed unchanged, still the single governance-authoritative selector.

These confirm Phase 149O.20L.7O.2N.6 §14's findings; no new test of production parsers was required this phase since no schema is being changed, only a design document is being frozen (contract/evidence tests for the *new* provider's shape are added instead — §17 below).

## 4. Chosen hybrid provider model

Confirmed **Architecture D** (hybrid) from Phase 149O.20L.7O.2N.6 §19: the existing `Fido2HardwareProvider` (local/raw CTAP) is retained unmodified; a new, conceptually distinct `RemoteWebAuthnProvider` implementation — structurally satisfying the same `HATPProofVerifierProvider`/`HATPHardwareSigner` `Protocol`s already defined in `hatp_providers.py` — is the additive second provider. Nothing is renamed. Nothing is implemented this phase. Full normative text: `docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md` (HRWP-001 v1.0).

## 5. Exact `provider_profile` vocabulary

Frozen value: **`HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN`** (HRWP-REQ-008). Chosen as a `HATP_HARDWARE_PROVIDER_V1`-family suffix (matching that profile's own "security properties, not protocol branding" naming discipline) rather than an unrelated new root string, since the underlying required security properties (non-exportable key, fresh human presence, credential identity, signature verification) are unchanged — only ceremony/evidence transport differs. A distinct value from the local provider's `HATP_HARDWARE_PROVIDER_V1` is required because `Fido2HardwareProvider.verify()` already fail-closes on `provider_profile` mismatch, and a WebAuthn-sourced record's evidence bytes are not parseable by that same verifier's CTAP2-specific parser.

## 6. Registration flow (frozen)

`docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md` §8 (HRWP-REQ-015): server validates governance authorization → issues short-lived, single-use registration challenge → delivers to trusted client → client invokes platform WebAuthn `create()` → physical key performs `makeCredential` locally → client returns response → server independently verifies → derives `HardwareCredentialRecord` fields → persists via HHCE-001's existing, unmodified protected writer. Pre-hardware governance ordering (§9, HRWP-REQ-016) is preserved identically to the local path's own already-repaired invariant (Phase 149O.20L.7O.2N.1/.2N.2).

## 7. Registration evidence schema (mapping)

No `HardwareCredentialRecord`/HHCE-001 schema field change is required. `credential.id` → `signer_key_id` (hex); COSE public key (CBOR) → `public_key` (identical byte format the existing FIDO2 verifier already consumes); `provider_profile` → `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN`; `protocol_name` → new value `"WEBAUTHN"` (a plain string field, no enum widening needed); `algorithm` → same COSE-algorithm-name derivation already used. RP identity, attestation data, and transports are NOT persisted per-credential fields — audit-metadata-only at most, mirroring HHCE-REQ-006's existing exclusion precedent. Full detail: contract §10.

## 8. Assertion/signing flow and evidence schema

Both providers ultimately produce and verify a signature over `authenticatorData || SHA-256(clientDataJSON)`, with a caller-bound `challenge` embedded in `clientDataJSON` — confirmed directly from `hatp_fido2_provider.py`'s own docstring and `verify()` implementation. A remote-WebAuthn-specific evidence schema (contract §27, HRWP-REQ-050) carries the same four cryptographic fields (`credential_id_hex`, `authenticator_data_hex`, `client_data_json_hex`, `signature_hex`) as the existing local-provider schema, under the same closed-field/versioned/no-duplicate-keys discipline, as a **distinct schema instance** (routed via `provider_profile`, §5) rather than a shared/overloaded one.

## 9. Raw CTAP vs. WebAuthn semantic gap — the honest finding

This is the phase's central technical finding, and it differs materially from what a naive reading of the governing prompt's §27/§28 framing ("PCAE may require a raw signature over arbitrary envelope bytes that WebAuthn cannot provide") might suggest before checking source:

**The existing local `Fido2HardwareProvider` already speaks the WebAuthn/CTAP2 `getAssertion` wire format, not an arbitrary raw-bytes signature scheme.** `request_signature()`/`verify()` construct and check a real `CollectedClientData` object and verify `authenticatorData || SHA-256(clientDataJSON)` — exactly what a browser's `navigator.credentials.get()` produces and what any standard WebAuthn relying-party verifier checks. The one genuine divergence is **origin/RP-ID enforcement**: the local provider hand-constructs `clientDataJSON` with a fixed, non-resolvable, non-HTTPS origin/RP-ID pair (`pcae-hatp://hatp.pcae.local` / `hatp.pcae.local`) that a real browser will never let a page assert, because browsers enforce the page's actual origin and `rp.id` against it.

**Conclusion: remote WebAuthn signing is SUPPORTED VIA A NEW, PROVIDER-SPECIFIC ASSERTION PROFILE that reuses the existing signature-verification algorithm and challenge-binding technique unmodified** (same digest-as-challenge binding, same `authenticatorData || SHA-256(clientDataJSON)` verification), differing only in (a) `provider_profile`/`protocol_name` routing, (b) RP-ID/origin constants, and (c) evidence wire-encoding — **not** an incompatible cryptographic scheme requiring new verification semantics. This is a more favorable, more specific finding than 149O.20L.7O.2N.6's necessarily-cautious "requires additional contract work" — that phase correctly declined to assume equivalence without formalizing it; this phase performed that formalization from source and confirmed compatibility in kind.

What genuinely remains open (named, not concealed): HSCE-001 v1.3 governs a synchronous, single-process, CLI-driven signing ceremony; it does not yet define how an asynchronous, network-mediated, browser-round-trip ceremony's evidence is captured with the same atomicity/no-clobber discipline. That orchestration-layer question is explicitly deferred to a future HSCE-001-companion contract (HRWP-REQ-060), not resolved here — remote *enrollment* is architecturally cleaner than remote *signing integration with the existing evidence store*, even though the underlying cryptography for both is now confirmed compatible.

## 10. Model-B compatibility

Preserved identically: hac-dell remains authoritative for `RepositoryIdentity`, `Principal`, `SignerRecord`, `HardwareCredentialRecord`, `DeploymentBinding`, the allowed-credential set, challenge issuance/verification, and revocation; the Mac/iPhone client supplies only cryptographic ceremony output, never governance identity (contract §2, §19, §25).

## 11. RP ID

Resolved as a **named, unresolved infrastructure requirement**, not a literal value: the existing `hatp.pcae.local`/`pcae-hatp://` constants are confirmed unusable, unmodified, for a browser flow (§9 above). The implementation phase MUST fix a concrete, stable, non-`localhost`, non-raw-IP, non-per-session RP ID reachable via DNS from both Mac and iPhone client networks (contract §12, HRWP-REQ-026/027/028). No literal hostname is selected by this phase — none has been provisioned.

## 12. Allowed origins

`https://<the fixed RP-ID-matching host>` only — no `http://`, no wildcard, no caller-derived origin (contract §13, HRWP-REQ-029/030).

## 13. HTTPS/TLS requirement

Named as required infrastructure, not provisioned: a DNS name reachable from both client networks, a TLS certificate (public-CA or private-CA, an operational decision this phase does not make), and a TLS-terminating endpoint reachable from both platforms (directly on hac-dell or via reverse proxy) — contract §14, HRWP-REQ-031. Nothing was provisioned, configured, or deployed this phase.

## 14. Session/challenge fields

Frozen minimum set (contract §20, HRWP-REQ-039): `repository_id`, `canonical_deployment_root`, `operation_type`, `provider_profile`, `phase_or_session_identifier`, `nonce`, `issued_at`, `expires_at`, `expected_rp_id`, `allowed_credential_ids` (where applicable), `principal_id`/`signer_key_id` (assertion ceremonies only).

## 15. Replay protection

One-time-use, server-consumed on first valid use, short fixed expiry; rejection on reuse, expiry, wrong repository/operation/provider-profile, wrong credential, or wrong origin (contract §21, HRWP-REQ-040).

## 16. CSRF/session binding

Single-use, unguessable, server-generated identifier bound to exactly one challenge (URL path component or signed request ID — mechanism not fixed to a literal choice); no long-lived bearer artifact; cross-tab/cross-device/cross-session substitution rejected by the same single-use binding, not a bolted-on separate CSRF layer (contract §22-§23, HRWP-REQ-041/042).

## 17. Mobile ceremony delivery model

Short-lived HTTPS URL, opened via QR code, deep link, or manual entry (presentation choice, not fixed); any outbound-notification channel (including Telegram) MAY deliver the link but never becomes an inbound authority channel — link possession is never itself authorization (contract §24-§25, HRWP-REQ-043/044/045).

## 18. Mac compatibility

Yes, both for the existing local/raw path (device already Mac-attached) and as a remote-WebAuthn client once built.

## 19. iPhone USB-C compatibility

UNKNOWN — platform/browser-version-dependent, not independently verified by this phase or its predecessor (carried forward from 149O.20L.7O.2N.6 §16, re-stated, not re-tested).

## 20. iPhone NFC compatibility

UNKNOWN in the same sense — device supports NFC; iOS/Safari WebAuthn-over-NFC platform behavior for the current iOS version was not tested end-to-end by this phase (carried forward, re-stated).

## 21. YubiKey 5C compatibility

USB-C only, no NFC; compatible with the remote-WebAuthn architecture on any USB-C-capable client; iPhone-specific behavior UNKNOWN in the same sense as §19-20.

## 22. YubiKey 5C NFC compatibility

USB-C and NFC; same disposition as §19-21.

## 23. Security Key C NFC compatibility (currently attached device)

USB-C and NFC capable; usable conceptually via Mac USB-C, iPhone USB-C (UNKNOWN platform behavior), and iPhone NFC (UNKNOWN platform behavior) once the remote-WebAuthn provider is implemented. No credential created this phase.

## 24. Multiple-credential policy

One `Principal` MAY have multiple active `SignerRecord`s/credentials (local and/or remote). Each governed signing operation resolves to exactly one `signer_key_id` via the existing `DeploymentBinding` selector, or an explicitly server-constructed allow-list for ceremony types that support one — never client-chosen (contract §7/§34, HRWP-REQ-014/059).

## 25. `allowCredentials` policy

Populated exclusively from PCAE's own registry, scoped by the resolved binding — never from client-asserted input (contract §7/§28, HRWP-REQ-014/052).

## 26. Backup/revocation model

A second key = a separate `HardwareCredentialRecord` + separate `SignerRecord`, same `Principal` — no cloning, no manual import. Revocation removes a credential from future `allowCredentials`/selection, never cascades, never auto-rebinds `DeploymentBinding` (contract §29, HRWP-REQ-053/054).

## 27. Lost-all-keys limitation

Explicitly preserved, not solved: recovery requires a separately governed identity/authority process, out of this contract's and this phase's scope (contract §30, HRWP-REQ-055).

## 28. `HardwareCredentialRecord` impact

None required beyond populating existing fields with new values (`provider_profile`, `protocol_name`) — contract §31.

## 29. `SignerRecord` impact

None required — same schema, new `provider_profile` value, no client identity stored as signer identity — contract §32.

## 30. `DeploymentBinding` impact

None required — confirmed still exactly one binding per `repository_id`, protocol-agnostic — contract §33.

## 31. Existing contract changes required

**None to HATP-001, HHCE-001, HPSE-001, HBDC-001** — all three are consumed unamended. **HSCE-001 is named, not amended**, with an explicit deferred companion-contract requirement for remote-ceremony evidence-capture orchestration (§9 above, contract §35, HRWP-REQ-060).

## 32. New companion contract

**HRWP-001 v1.0** — `docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md`, 68 requirements (`HRWP-REQ-001`–`HRWP-REQ-068`), FROZEN, not yet independently verified, not implemented.

## 33. Future HMIC impact

Named, not amended: a future `RemoteWebAuthnProvider` module, challenge/session manager, registration-evidence mapper, assertion verifier, and possibly a ceremony-delivery HTTP endpoint will each become new authority-bearing source requiring HMIC-001 scope inclusion and independent verification before activation (contract §36, HRWP-REQ-061). No HMIC-001 record touched this phase.

## 34. Trusted-kernel vs. adapter boundary

Trusted: challenge construction/binding, authority-ordering enforcement, credential allow-list, server-side response verification, registry writes. Replaceable/thin: HTTP transport, browser ceremony page, mobile presentation layer (contract §37, HRWP-REQ-062).

## 35. USB-over-IP disposition

**EXPERIMENTAL, NOT PRIMARY ARCHITECTURE.** Reuses the existing raw-CTAP path unmodified but is Mac-only, adds a network-transport dependency, and does not satisfy the iPhone/NFC requirement (contract §38, HRWP-REQ-063).

## 36. Direct-hac-dell raw FIDO2 disposition

Retained unmodified as a first-class, additive path — not deprecated by adding remote WebAuthn (contract §39, HRWP-REQ-064).

## 37. Known limitations

Recorded in full at contract §40 (HRWP-REQ-065): iOS exposes only platform WebAuthn APIs (no raw CTAP forwarding); plain YubiKey 5C has no NFC; NFC requires tap-proximity within a bounded session window (current-iOS-version behavior unverified); browser behavior may vary; remote ceremony requires live network reachability to the fixed RP-ID/origin; WebAuthn is strictly RP/origin-bound; WebAuthn enrollment support does not automatically imply the exact same evidence bytes are consumable by HSCE-001's existing evidence store without the companion work named in §9/§31; the physical authenticator remains required locally to the human in every case.

## 38. Implementation sequence

Contract §42 (HRWP-REQ-066), non-binding: (1) independent verification of HRWP-001; (2) HSCE-001-companion contract for remote-ceremony evidence capture; (3) server-side challenge issuance + verification implementation; (4) minimal browser WebAuthn client; (5) synthetic interoperability tests; (6) independent verification of 3-5; (7) HMIC-001 source-scope expansion; (8) deployment + recertification; (9) first real remote WebAuthn registration (its own narrowly-scoped phase); (10) Principal/Signer enrollment; (11) signing/assertion verification track.

## 39. No real hardware effect proof

No `makeCredential`/`getAssertion` invoked against real hardware this phase. No PIN requested. No configuration of the currently-attached Security Key C NFC changed. No `HardwareCredentialRecord`/`Principal`/`Signer`/`DeploymentBinding` created. This phase performed source reads and documentation writes only — `git diff --stat` for this phase's implementation commit (§41) touches only `docs/`, `tests/`, and governance/task-lifecycle files; no path under `src/pcae/` or `scripts/` is modified.

## 40. Runtime unchanged

No HMIC record, no certification, no Permission Broker policy, no deployed hac-dell state changed. `pcae runtime inspect` unchanged from prior phase's baseline (Observed / execution_unavailable).

## 41. Commits

See `.pcae/phase-completion-metadata.json` `phase_commits` for the exact hash list (this phase's implementation commit plus lifecycle/status/metadata-sync commits).

## 42. Pushed / `origin/main..HEAD`

**Not yet pushed as of this report's writing** — staged pending push per this repository's governed two-step finalization procedure (`pcae phase complete --stage-pending-report`, then human-confirmed `pcae push`). `origin/main..HEAD` will be 0 after push; not yet re-verified at report-writing time.

## 43. Testing

New disposable file `tests/test_phase_149o_20l_7o_2n_7_remote_webauthn_provider_contract_architecture_freeze.py`: structural/evidence tests asserting (a) the contract document exists, freezes a distinct `provider_profile` string different from `HATP_HARDWARE_PROVIDER_V1`, and contains every section this phase's governing prompt required (RP ID, origin, HTTPS, challenge fields, replay protection, multi-credential policy, Model-B boundary language, raw-CTAP/WebAuthn semantic-gap discussion); (b) the existing local FIDO2 provider's real evidence-verification algorithm (`authenticatorData || SHA-256(clientDataJSON)`) is unchanged by this phase, confirming no production regression; (c) `HATP_HARDWARE_PROVIDER_V1` (the existing profile constant) is untouched in `hatp_providers.py`. No test touches real hardware, a protected root, or performs any registry write — this phase implements no production behavior.

## 44. Regression

No production source (`src/pcae/`, `scripts/`) changed this phase — only new `docs/` and `tests/` files plus governance/lifecycle artifacts. This phase's own new tests pass standalone; no broader Fast Green regression surface is introduced.

## 45. Governance

`pcae health`, `pcae check`, `pcae status coherence`, `pcae doctor task-memory`, `pcae push check`, `pcae runtime inspect` all run per §54 of the governing prompt — results recorded in `.pcae/phase-completion-metadata.json`'s `governance_results`.

## 46. Findings

None Blocking. The RP-ID/HTTPS infrastructure gap (§11/§13) and the HSCE-001-companion evidence-capture gap (§9/§31) are design findings this phase surfaces deliberately for the next phase's benefit, not defects in anything this phase touched — this phase implemented nothing.

## 47. Expected verdict

**REMOTE WEBAUTHN PROVIDER CONTRACT FROZEN — HYBRID LOCAL-CTAP + REMOTE-WEBAUTHN ARCHITECTURE SELECTED.**
MULTI-AUTHENTICATOR MODEL: SUPPORTED BY EXISTING REGISTRY / ADDITIVE POLICY ONLY.
RP-ID / ORIGIN MODEL: RESOLVED (as an explicit infrastructure requirement for the next phase; no literal hostname selected).
REMOTE REGISTRATION: ARCHITECTURALLY SUPPORTED.
REMOTE SIGNING: **SUPPORTED VIA NEW PROVIDER-SPECIFIC ASSERTION PROFILE** (reusing the existing verification algorithm; HSCE-001 evidence-capture orchestration named as separate future work, not a cryptographic incompatibility).
NO REAL CREDENTIAL CREATED.

## 48. Next phase

Per contract §42 and the governing prompt §57: independent verification of HRWP-001 before any implementation. Do not start a WebAuthn server, RP-ID/DNS/TLS provisioning, or any implementation work until that independent verification is complete. Stop after completing 149O.20L.7O.2N.7.
