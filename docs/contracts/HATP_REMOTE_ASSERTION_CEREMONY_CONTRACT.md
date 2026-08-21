# HATP Remote Assertion Ceremony Contract

## Contract identity and status

**Contract:** HRAC-001
**Version:** 1.0
**Status:** FROZEN — CONTRACT/ARCHITECTURE FREEZE ONLY, NOT YET INDEPENDENTLY VERIFIED, NOT IMPLEMENTED
**Frozen by:** Phase 149O.20L.7O.2N.9 — HSCE Remote WebAuthn Assertion Ceremony and Evidence-Capture Companion Contract Freeze; follows Phase 149O.20L.7O.2N.8 (HRWP-001 Independent Verification, one non-blocking finding, no blocking defect).
**Depends on:** HRWP-001 v1.0 (`HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md`, unamended — this contract consumes, never redefines, its cryptographic/evidence-format and server-verification requirements), HSCE-001 v1.3 (`HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`, unamended — this contract is an explicit companion to the gap HSCE-REQ-060/HRWP-REQ-060 both name and neither resolves), HATP-001 v1.0 (unamended), HPSE-001 v1.1 (unamended — `SignerRecord`/`PrincipalRecord` identity this contract's signer resolution reuses verbatim), HBDC-001 v1.2 (unamended — `DeploymentBinding` this contract's signer resolution reuses verbatim).
**Architecture basis:** `docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md` (HRWP-001, read fresh this phase — §7/§12/§13/§16/§20-§25/§26-§28/§35 in particular); `docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md` (HSCE-001 v1.3, read fresh this phase — §9-§13, §17-§24, §32-§33, §37, §46-§48 in particular); `src/pcae/core/hatp_signing_ceremony.py` (the exact current synchronous, single-process, CLI-shaped signing orchestrator, read directly this phase — `resolve_signing_context`, `_resolve_deployment_binding_signer`, `sign_rollback_evidence`); `src/pcae/core/hatp_bootstrap.py`, `src/pcae/core/hatp_hardware_credentials.py`, `src/pcae/core/hatp_evidence_store.py`, `src/pcae/core/hatp_signed_evidence.py` (read directly this phase for their existing field/format conventions, reused rather than reinvented below).

This is a contract-freeze document. It authorizes no implementation, no WebAuthn server, no request-store code, no HTTP routes, no browser client, no credential creation, no HMIC change, and no redeployment. It defines the normative asynchronous request/response/evidence orchestration layer a future implementation phase must build to, closing the gap both HRWP-001 (§35, HRWP-REQ-060) and HSCE-001 (§36, HSCE-REQ-074's neighboring text) name but explicitly decline to resolve.

---

## 0. Normative language

"SHALL", "SHALL NOT", "MUST", "MUST NOT", "MAY", and "SHOULD" are interpreted per RFC 2119, matching this repository's other bound contracts. Every normative sentence carries a unique requirement ID, `HRAC-REQ-###`, sequential from 001, no gaps, no duplicates. This contract's numbering namespace is independent of `HRWP-REQ-*`/`HSCE-REQ-*`/`HATP-REQ-*`/`HPSE-REQ-*`/`HBDC-REQ-*`/`HMIC-REQ-*`.

## 1. Purpose

**HRAC-REQ-001.** This contract exists to define, at contract-text level only, how a PCAE-governed operation requiring a remote-WebAuthn cryptographic signature (HRWP-001) is requested, correlated, delivered to a client, verified, and captured as authoritative evidence — the asynchronous, network-round-trip orchestration layer that HRWP-001 §35 (HRWP-REQ-060) and HSCE-001's own synchronous, single-process, CLI-shaped ceremony model (`hatp_signing_ceremony.py`, re-read this phase) do not yet cover.

**HRAC-REQ-002.** This contract does not redefine the cryptographic meaning of a WebAuthn assertion (HRWP-001 §16/§26-§27, unamended) or the meaning of a verified `HumanApprovalProvenanceProof`/`HATPSignedEvidenceEnvelope` (HATP-001 §19-§26, HSCE-001 §14-§22, unamended). Its job is orchestration only: request lifecycle, correlation, state, verification handoff, and evidence capture for the asynchronous path — never a second, competing verification algorithm.

## 2. Scope

**HRAC-REQ-003.** This contract SHALL govern: the remote assertion request's state machine (§7); request identity and its bound fields (§8); challenge construction and domain separation (§11-§13); the delivery/session model (§15-§16); the client-visible request-fetch surface and response schema (§17-§18); the verification handoff to HRWP-001's authoritative verifier (§19); one-time consumption, replay, and concurrency semantics (§20-§23); cancellation (§24); the closed failure taxonomy (§25); durability/restart semantics (§26-§27); the mapping of a verified remote result into HSCE-001-compatible evidence (§28-§30); privacy/data-retention limits (§31); and the trusted-kernel/adapter boundary for the future components this contract names (§48).

**HRAC-REQ-004.** This contract SHALL NOT govern: WebAuthn cryptographic proof semantics or origin/RP-ID verification rules (HRWP-001's exclusive scope, unamended); `HumanApprovalProvenanceProof`/HATP proof-verification semantics (HATP-001's exclusive scope, unamended); the existing synchronous `pcae hatp sign rollback` CLI surface or `HATPSignedEvidenceEnvelope` local-path schema (HSCE-001's exclusive scope, unamended — this contract is additive to it, per §29 below); `Principal`/`SignerRecord`/`HardwareCredentialRecord`/`DeploymentBinding` enrollment or schema (HPSE-001/HHCE-001/HBDC-001's exclusive scope, unamended); literal RP-ID/DNS/TLS/hostname selection (an infrastructure decision HRWP-001 §12-§14 already named as open and this contract does not resolve); or any real implementation, WebAuthn server, request store, or HTTP route.

## 3. Definitions

**HRAC-REQ-005.** The following terms are frozen for this contract:

- **Remote assertion request** — one server-created, uniquely identified, single-use record binding a governed operation to a pending remote-WebAuthn assertion ceremony (§7-§8). Distinct from, and never itself, a `HumanApprovalProvenanceProof` or a `HATPSignedEvidenceEnvelope`.
- **Ceremony session** — the client-visible, single-use delivery mechanism (a short-lived URL or equivalent, HRWP-REQ-041/HRWP-REQ-043) through which one remote assertion request's challenge/options are fetched and its response returned. A ceremony session locates a request; it never itself authorizes anything (§14).
- **Verified remote result** — the output of a successful HRWP-001 §16 server-side verification of a client-returned WebAuthn assertion, bound to exactly one remote assertion request (§19).
- **Remote evidence record** — this contract's own evidence-capture artifact (§29), additive to and never a modification of HSCE-001's `HATPSignedEvidenceEnvelope` schema.

## 4. Contract identity rationale

**HRAC-REQ-006.** This contract's identity is **HRAC-001** ("HATP Remote Assertion Ceremony Contract"), chosen to name its actual subject precisely — the asynchronous *ceremony orchestration* (request/response/correlation/evidence-capture) for a *remote assertion* — distinct in kind from HRWP-001 (the *provider*'s cryptographic/evidence-format contract) and from HSCE-001 (the *existing synchronous CLI ceremony*'s command/evidence-store contract). "Assertion" rather than "signing" in the name mirrors HRWP-001's own §26 terminology (a WebAuthn `getAssertion` ceremony); this contract's scope is assertion (signing) ceremonies only — remote *registration* (enrollment) ceremonies are HRWP-001 §8's own scope and are not reopened here (§45 below).

**HRAC-REQ-007.** This contract's relationship to HSCE-001 and HRWP-001 is strictly additive, mirroring HSCE-001's own "additive to HATP-001/RAE-001" precedent (HSCE-REQ-006/007) and HPSE-001's own "additive to HATP-001/HBDC-001" precedent: neither HSCE-001 nor HRWP-001 requires amendment for this contract's text to exist, and this contract amends neither (§46 resolves the one narrow question of whether HSCE-001 needs a version bump — it does not).

## 5. Current synchronous ceremony — what changes for the remote path

**HRAC-REQ-008.** The existing production orchestrator (`hatp_signing_ceremony.py::sign_rollback_evidence`, re-read this phase) is: (1) resolve context A (no hardware touch); (2) resolve signer identity from `DeploymentBinding` (HSCE-REQ-080); (3) render a blind-touch-defense preview and require synchronous, same-process human confirmation (`input()`); (4) construct the proof and call `provider.request_signature(...)` exactly once, synchronously, blocking on the hardware touch in the same process invocation; (5) re-resolve context B and signer resolution B for a TOCTOU recheck; (6) build and publish the envelope. Every step from (1) through (6) executes in one CLI process invocation, with no network round trip and no persisted intermediate state between steps.

**HRAC-REQ-009.** The remote path differs from HRAC-REQ-008 in exactly one structural respect: steps (3)-(4) (preview confirmation and hardware touch) are no longer synchronous, same-process operations — they occur on a separate client device, at an unknown future time, reachable only over a network round trip. This contract's entire purpose is to define the request/response/correlation/evidence machinery that makes that separation safe, replacing the single synchronous confirm-then-touch call with: create a durable pending request (§7-§8) → deliver a ceremony session (§15-§16) → await an asynchronous client response (§17) → verify it via HRWP-001's authoritative verifier (§19) → run the equivalent of HSCE-REQ-069/070/083's TOCTOU recheck against live state at verification time (§19, restated) → capture evidence (§29). Steps (1), (2), (5)-(6) of HRAC-REQ-008 are unchanged in kind — this contract requires them to run again at verification time, from the same canonical sources HSCE-001 already names, never a new source.

## 6. Requirement-count-in-scope statement (non-normative orientation)

This document intentionally requires a state machine, a request-identity schema, a challenge-construction scheme, a client contract, a verification-handoff rule, replay/concurrency/cancellation rules, a closed failure taxonomy, durability semantics, and an evidence-capture schema — the same order the governing phase prompt's §7-§34 enumerate. Sections below are numbered independently of that prompt's numbering; a cross-reference table appears at §54.

## 7. Remote request state machine

**HRAC-REQ-010.** The following closed state set is frozen, deliberately narrower than the nine-state list the governing prompt offered as a menu ("use only necessary states"): `PENDING`, `RESPONSE_RECEIVED`, `VERIFIED`, `COMPLETED`, `EXPIRED`, `FAILED`, `CANCELLED`. No `CREATED` state exists separately from `PENDING`: a remote assertion request becomes fetchable atomically with its creation (HRAC-REQ-016's governance-ordering requirement means "created" already implies "already authorized" — there is no observable authorized-but-not-yet-pending intermediate state to name). No separate `AUTHORIZED` state exists for the identical reason. No separate `CONSUMED` state exists distinct from `COMPLETED`: this contract's one-time-consumption model (§20) makes reaching `COMPLETED` and being consumed the same event, mirroring HSCE-REQ-052's own "successful publication IS the winning event" discipline.

**HRAC-REQ-011.** Legal transitions are exactly:

```
PENDING            -> RESPONSE_RECEIVED   (client posts a syntactically valid response, pre-verification)
PENDING            -> EXPIRED             (expires_at reached with no VERIFIED response ever received)
PENDING            -> CANCELLED           (explicit governed cancellation, §24, before any response)
RESPONSE_RECEIVED  -> VERIFIED            (HRWP-001 §16 server verification succeeds)
RESPONSE_RECEIVED  -> FAILED              (HRWP-001 §16 verification fails, or the response is malformed, or the request had already expired when the response arrived, §21)
VERIFIED           -> COMPLETED           (evidence capture, §29, durably persisted -- the exclusive-publish winner, §20)
VERIFIED           -> FAILED              (evidence persistence failure only, §26 -- never a re-verification failure; the assertion was already cryptographically verified and is discarded, not distrusted)
```

**HRAC-REQ-012.** `COMPLETED`, `EXPIRED`, `FAILED`, and `CANCELLED` are terminal. No transition out of a terminal state exists under any condition — mirrors HSCE-REQ-052's own "canonical status is never reopened" discipline applied to request state rather than evidence-file state.

**HRAC-REQ-013.** A late response — one arriving after `expires_at` has passed, regardless of whether the request's state was still `PENDING` or had already been lazily observed as `EXPIRED` — SHALL be rejected before any HRWP-001 verification call is made, with `error_type = expired_challenge` (§25), and SHALL NOT transition the request to `RESPONSE_RECEIVED` or any other non-terminal state. This distinguishes "no response ever arrived" and "a response arrived too late" as the same terminal outcome (`EXPIRED`) at the request-state level, while still recording the late-arrival attempt via ordinary diagnostic logging (§31) — never reviving the request (§21 of the governing prompt).

**HRAC-REQ-014.** Distinct from `EXPIRED`: `FAILED` is reserved for a response that arrived before expiry but failed verification, was malformed, or encountered a device/provider-reported fault (HRWP-REQ-033/034) — or a `VERIFIED` request whose subsequent evidence persistence failed (§26). This mirrors HSCE-001's own `human_signing_cancelled`-vs-`hardware_device_fault`-vs-`provider_unavailable` non-collapsing discipline (HSCE-REQ-030), extended here to the request-state level rather than only the CLI error-vocabulary level.

## 8. Request identity

**HRAC-REQ-015.** `request_id` SHALL be a fresh, cryptographically random, server-generated 256-bit value, rendered as 64 lowercase hexadecimal characters (mirroring this repository's plain-hex digest convention, but generated by a CSPRNG, e.g. `secrets.token_hex(32)`-equivalent — never derived from operation content). This deliberately differs from HSCE-001's own `evidence_id = digest_hatp_proof_payload(proof)` content-addressing convention (HSCE-REQ-036): content-addressing is the correct identity scheme for an *already-signed, immutable* evidence artifact, where two independently-produced identical artifacts should collide by design (HSCE-REQ-038). A *pending request*, before any signature exists, has no signed content to address — two ceremonies for the same operation at nearly the same instant must NOT collide into one request merely because their canonical context happens to match; unguessability, not content-addressing, is the security property a pending request's identity needs (HRWP-REQ-041's own "single-use, unguessable" requirement, restated here as the request's own primary key).

**HRAC-REQ-016.** Before a remote assertion request is created (before `PENDING` is ever entered), the underlying governed operation SHALL already be authorized as required by whatever contract governs that operation (mirrors HRWP-REQ-016's pre-hardware governance-ordering repair, extended verbatim to remote assertion ceremonies — never only remote *enrollment* ceremonies). The remote-ceremony request mechanism itself SHALL NOT manufacture, substitute for, or relax that authorization (§34 restates this as a standing rule).

**HRAC-REQ-017.** Every remote assertion request SHALL bind, at creation and for its entire lifetime, exactly the following fields, none client-suppliable, none mutable after creation:

```
request_id            (HRAC-REQ-015)
repository_id           (RepositoryIdentity, read live -- HSCE-REQ-018's own canonical source)
canonical_deployment_root (HSCE-REQ-080 step 1's own canonical source)
operation_type          ("rollback_ag3" | "rollback_ag5", or a future closed value --
                         never an open string; mirrors HSCE-REQ-010's closed-choices discipline)
operation_reference     (job_id+original_commit_sha, or per_id+ecp_id -- HSCE-REQ-013/016, read live)
principal_id            (HSCE-REQ-080's resolved signer identity, read live, pre-touch)
signer_key_id           (HSCE-REQ-080's resolved signer identity, read live, pre-touch)
provider_profile        (HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN, HRWP-REQ-008, fixed)
binding_id, binding_digest, decision_record_id, decision_record_digest
                        (HSCE-REQ-018's own canonical sources, read live, pre-touch)
expected_rp_id          (HRWP-REQ-027's fixed value, once an implementation phase selects it)
allowed_credential_ids  (HRWP-REQ-014/036's server-constructed allow-list, scoped to signer_key_id)
domain                  (the fixed domain-separation string, §13)
nonce                   (fresh, random, per request)
created_at, expires_at  (server clock, §26 -- never client-supplied)
governance_authorization_reference (whatever identifier the pre-authorized operation's own
                        governing contract already defines, e.g. a Decision/Binding id -- restates
                        HRAC-REQ-016, never a second, independent authorization concept)
```

This list is exhaustive for v1.0; a future amendment MAY add a field through a governed contract amendment only (mirrors HSCE-REQ-043's closed-store-contents discipline).

**HRAC-REQ-018.** Every field in HRAC-REQ-017 except `request_id`, `domain`, `nonce`, `created_at`, and `expires_at` SHALL be resolved by the identical canonical live-state resolution HSCE-001 §9-§11/§80 already defines for the synchronous path (`resolve_signing_context`, `_resolve_deployment_binding_signer`) — this contract introduces no second, competing resolution algorithm. The client SHALL NOT supply, select, or influence any of these fields (mirrors HSCE-REQ-017/HRAC-REQ-016's "no user-typed security fields" discipline, extended to the remote path's request-creation step).

## 9. Signer selection (EXPLICIT_SIGNER, reaffirmed)

**HRAC-REQ-019.** The `DeploymentBinding`-resolved signer identity (HSCE-REQ-080, HRWP-REQ-014) SHALL be resolved once at request-creation time (pre-touch) exactly as HRAC-REQ-017/018 require, and SHALL be re-resolved a second time at verification time (§19, restated from HSCE-REQ-083's cross-record TOCTOU discipline) before any evidence is captured. The client never chooses `principal_id`, `signer_key_id`, `HardwareCredentialRecord`, `DeploymentBinding`, or `provider_profile` (mirrors HRWP-REQ-038's client-trust-model exclusions verbatim).

**HRAC-REQ-020.** The WebAuthn `allowCredentials` set delivered to the client (§17) SHALL be constructed server-side, scoped exclusively to the request-creation-time-resolved `signer_key_id`'s active `HardwareCredentialRecord`(s) matching `provider_profile` (HRWP-REQ-014/HRWP-REQ-036/HRAC-REQ-017), and SHALL NOT be broadened by any client input, browser platform default, or "discoverable credential" behavior (HRWP-REQ-036's own "never an empty/omitted list" requirement, restated).

## 10. Multi-authenticator behavior

**HRAC-REQ-021.** One `Principal` MAY own multiple active `SignerRecord`s (HRWP-REQ-012/059, HSCE-REQ-081's own structural-uniqueness finding for `DeploymentBinding`). Because `DeploymentBinding` remains exactly one per `repository_id` (HRWP-REQ-013, HSCE-REQ-081, both unamended), every remote assertion request for a given repository resolves to exactly one `(principal_id, signer_key_id)` pair via the identical mechanism HSCE-REQ-080 already defines — this contract introduces no new disambiguation step, and no browser-platform credential picker is ever permitted to silently broaden authority beyond that one resolved pair (HRAC-REQ-020).

## 11. Challenge construction — canonical structure

**HRAC-REQ-022.** The WebAuthn ceremony `challenge` value SHALL be derived from a canonical structure (the "challenge context") containing exactly: `request_id`, `repository_id`, `canonical_deployment_root`, `operation_reference` (its own canonical rendering, reusing `human_approval_trusted_provenance.py`'s existing `Ag3OperationReference`/`Ag5OperationReference` canonical encoding, never a new ad hoc format), `principal_id`, `signer_key_id`, `provider_profile`, `binding_digest`, `decision_record_digest`, `domain` (§13), `nonce`, `issued_at`, `expires_at`. No field is omitted; no additional field is silently included. This mirrors HATP-001/HSCE-001's own "every signed field is enumerable, no ambiguous concatenation" discipline (HSCE-REQ-009's own governing prompt §12 concern, restated here for the challenge rather than the proof).

**HRAC-REQ-023.** The challenge context SHALL be serialized using the identical canonicalization discipline HSCE-REQ-053 already defines for evidence-store JSON (UTF-8, `sort_keys=True`, `allow_nan=False`, duplicate-key rejection on parse) — reused, not reinvented, so that "canonical bytes" means the same thing across HSCE-001's evidence store and this contract's challenge construction.

## 12. Challenge encoding — digest, not full bytes

**HRAC-REQ-024.** The WebAuthn ceremony's `challenge` parameter SHALL carry a SHA-256 digest of the challenge context's canonical bytes (HRAC-REQ-022/023) — not the full canonical bytes themselves. Rationale: WebAuthn challenges are conventionally short, opaque, random-looking byte strings; carrying the full canonical structure (which includes human-readable identifiers) as the literal challenge value would be non-standard and would not improve on a digest's binding strength, since the server independently reconstructs and re-hashes the same canonical structure at verification time (§19) to confirm the challenge matches — exactly the same reconstruct-and-compare discipline `canonicalize_hatp_proof_payload`/`digest_hatp_proof_payload` already use for the local synchronous path (HSCE-REQ-017/HATP-001's own digest convention).

**HRAC-REQ-025.** The exact algorithm is frozen as: `challenge = sha256(canonical_challenge_context_bytes)`, raw 32-byte digest, base64url-encoded (no padding) for the wire per WebAuthn's own `challenge` field convention — never base64 standard, never hex, matching the WebAuthn specification's own base64url convention for this field (distinct from this repository's own plain-hex convention used elsewhere, because this one value crosses the browser API boundary where the platform, not PCAE, dictates the wire encoding).

## 13. Domain separation

**HRAC-REQ-026.** The fixed domain-separation string is **`PCAE/HATP/HRAC/SIGN/V1`**, included as the `domain` field inside the canonical challenge context (HRAC-REQ-022) — never concatenated ad hoc onto the challenge bytes themselves. Purpose: prevent a valid challenge digest minted for one PCAE ceremony type (e.g. a future remote-*enrollment* ceremony, or an unrelated future WebAuthn-shaped PCAE ceremony) from being reinterpretable as a valid HRAC-001 remote-assertion-signing challenge, and vice versa — the version suffix (`V1`) allows a future incompatible revision of this contract's challenge context to mint a distinguishable domain string without colliding with v1.0's.

## 14. Session token is not authority

**HRAC-REQ-027.** The single-use ceremony-session identifier (§16) that locates a pending remote assertion request is a locator only. Possessing or opening it SHALL NOT itself constitute PCAE governance authority, verification success, or evidence — restates HRWP-REQ-045 verbatim, extended explicitly to this contract's own request/session model (not only HRWP-001's abstract statement of the principle). Only a HRWP-001 §16-verified WebAuthn assertion, correlated to the exact `request_id` the session locates, advances the state machine (§7, §19).

## 15. Delivery model

**HRAC-REQ-028.** The ceremony is delivered to the human as a short-lived HTTPS URL (HRWP-REQ-043), abstractly: the human opens it on Mac or iPhone, the client fetches the request's options (§17), the platform's WebAuthn API runs, and the client posts the result (§18). This contract does not bind delivery to Telegram, QR code, or any specific browser or presentation mechanism — those remain transport/presentation adapters (HRWP-REQ-044, restated), outside this contract's trusted-kernel boundary (§48).

## 16. Session binding — locator mechanism

**HRAC-REQ-029.** The ceremony-session identifier embedded in the delivery URL SHALL be single-use, unguessable, and server-generated, and SHALL be scoped to exactly one `request_id` (restates HRWP-REQ-041 verbatim). This contract does not fix whether the session identifier is literally identical to `request_id` or a distinct value bound 1:1 to it at creation — either satisfies this requirement provided the binding is 1:1, single-use, and never itself treated as authority (HRAC-REQ-027). It SHALL NOT be a long-lived bearer cookie or reusable token.

## 17. Client request-fetch surface

**HRAC-REQ-030.** A client possessing a valid, unexpired ceremony-session identifier for a request in state `PENDING` MAY fetch exactly: `challenge` (§12), `expected_rp_id` (HRWP-REQ-027), `allowCredentials` (§10, §20), a ceremony timeout duration, the `userVerification` policy value (`"preferred"`, HRWP-REQ-035, restated — fixed, not client-selectable), a human-readable operation/provider display string (presentation only, never authority-bearing), and `request_id` (for the client to echo back in its response, §18). No other server-internal field (e.g. `binding_digest`, `decision_record_digest`, `principal_id`, `signer_key_id` in cleartext) is exposed to the client fetch surface — the client needs only what WebAuthn's own API requires plus a display string; it never needs, and is never given, the full challenge-context fields the server itself reconstructs at verification time (§19).

**HRAC-REQ-031.** Fetching a request already in state `RESPONSE_RECEIVED`, `VERIFIED`, `COMPLETED`, `EXPIRED`, `FAILED`, or `CANCELLED` SHALL NOT re-issue a fresh challenge or re-open the ceremony — the fetch surface SHALL report only that the ceremony is no longer awaiting a response, never leak whether it succeeded or failed beyond what the original requester (the governance operator, not the client browser) is separately entitled to see through the request's own audit/evidence surface (§31's privacy-minimization principle applied to the fetch response itself).

## 18. Client response schema

**HRAC-REQ-032.** The client's returned WebAuthn assertion response SHALL carry exactly: `request_id` (echoed, for correlation — §19 confirms it matches server state, never trusts it as authority by itself), `credential_id` (base64url, WebAuthn wire convention), `authenticatorData`, `clientDataJSON`, `signature` (all base64url, per HRWP-REQ-049's field-kind mapping), and `userHandle` if the authenticator returns one. No other field carries authority; any additional field the client includes (e.g. client extension outputs) MAY be recorded as diagnostic/audit metadata only (mirrors HRWP-REQ-022/023's attestation/transport-metadata disposition) and SHALL NEVER be treated as part of the verified result.

## 19. Verification handoff — single authoritative call

**HRAC-REQ-033.** On receiving a client response for a request in state `PENDING` whose `expires_at` has not yet passed (§13), the orchestration layer SHALL: (1) transition the request to `RESPONSE_RECEIVED`; (2) re-resolve HRAC-REQ-017's live-state fields a second time (repository identity, `DeploymentBinding`/`SignerRecord`/`PrincipalRecord`/`HardwareCredentialRecord`, Decision/Binding digests) — the exact HSCE-REQ-083 cross-record TOCTOU discipline, re-run against the request's own creation-time snapshot; (3) call HRWP-001's authoritative server-side verifier (HRWP-REQ-033/034) with the reconstructed expected challenge (recomputed from the request's own stored canonical context, HRAC-REQ-024, never trusted from the client), the fixed `expected_rp_id`/allowed origin (HRWP-REQ-027/029), the re-resolved `allowCredentials` set, and the client-supplied assertion bytes; (4) if verification fails for any reason, or the TOCTOU recheck in step (2) finds the live state differs from the request's creation-time snapshot, transition to `FAILED` — no evidence is captured, mirroring HSCE-REQ-070's own "discard the freshly-produced assertion, persist nothing" discipline exactly; (5) if both succeed, transition to `VERIFIED` and proceed to evidence capture (§29).

**HRAC-REQ-034.** This contract's orchestration layer SHALL NOT perform its own cryptographic signature, origin, or RP-ID check — it SHALL call HRWP-001's authoritative verifier exactly once per response and treat its outcome as dispositive, never duplicating or second-guessing that check with independent logic (restates HRWP-REQ-033/034's "fail closed on any single failure" discipline as a call-once, trust-the-verifier's-outcome rule for this orchestration layer specifically).

## 20. One-time consumption

**HRAC-REQ-035.** Transitioning a request from `VERIFIED` to `COMPLETED` (evidence durably captured, §29) SHALL use the identical atomic, exclusive-publish technique HSCE-REQ-052 already defines for evidence-envelope publication (temp-file-plus-fsync, then `os.link` as the exclusive-create primitive against a path keyed by `request_id`) — reused, not reinvented, as this contract's own consumption-marking mechanism. The first successful `os.link` call is the sole authoritative "this request has been consumed" event; every other concurrent attempt against the same `request_id` fails the `os.link` call and is treated as a loser (§22).

**HRAC-REQ-036.** A request already in state `COMPLETED` SHALL NOT be re-verified, re-signed, or produce a second remote evidence record under any condition. A structurally-identical duplicate response arriving for an already-`COMPLETED` request SHALL be rejected before any HRWP-001 verification call is repeated, with `error_type = request_already_consumed` (§25) — mirrors HSCE-REQ-039(A)/(B)'s idempotent-vs-conflict distinction, except here there is no idempotent-success case: a second response for an already-completed request is always rejected outright, because (unlike HSCE-001's content-addressed evidence, where byte-identical re-writes are legitimately idempotent) a second WebAuthn assertion is never byte-identical to the first even when produced by the same authenticator for the same challenge (each `getAssertion` call increments the authenticator's own signature counter and re-signs fresh bytes) — there is no meaningful "same answer, safe to ignore" case here.

## 21. Late response

**HRAC-REQ-037.** Restates HRAC-REQ-013 with the exact failure vocabulary: a response received after `expires_at` SHALL be rejected as `expired_challenge`, before any verification is attempted, without reviving the request into `PENDING` or `RESPONSE_RECEIVED`. Server-side wall-clock time, read from the identical internal clock discipline HSCE-REQ-068 already requires (never a client/browser-supplied timestamp), is authoritative for the expiry comparison.

## 22. Concurrent responses

**HRAC-REQ-038.** If two devices (e.g. Mac and iPhone) both hold a valid ceremony-session identifier for the same request and both return valid, independently-verifiable assertions, exactly one SHALL win the `PENDING`→...→`COMPLETED` race, via the identical exclusive-publish mechanism (HRAC-REQ-035). The losing response — even if it independently passes HRWP-001 verification on its own merits — SHALL be rejected once the request's state is already `VERIFIED` or `COMPLETED` at the moment the losing response is processed, with `error_type = request_already_consumed` (§25). No second signing result is ever produced for one request under any interleaving, mirroring HSCE-REQ-052's own many-writer generalization (not only the two-writer case).

**HRAC-REQ-039.** The precise ordering guarantee is: whichever response's verification (HRAC-REQ-033) completes first and reaches the exclusive-publish step (HRAC-REQ-035) first wins; a response that begins verification before the winner's publish completes but loses the publish race SHALL be rejected exactly as HRAC-REQ-038 describes, not treated as a distinct error category from an already-terminal-state rejection.

## 23. Multiple outstanding requests

**HRAC-REQ-040.** PCAE SHALL support multiple independent, concurrently outstanding remote assertion requests (for distinct operations, or even for the identical operation re-requested — HRAC-REQ-015's unguessable-identity design permits this without collision). No correlation logic anywhere in this contract's surface SHALL use an implicit "most recent pending request" selection rule (mirrors HSCE-REQ-044's own "explicit ID only, no latest" discipline, restated for requests rather than evidence). Every client response binds to an exact `request_id` (HRAC-REQ-032); a response omitting or mismatching `request_id` against the ceremony session it arrived through SHALL be rejected as `malformed_response` (§25) before any further processing.

## 24. Cancellation

**HRAC-REQ-041.** A remote assertion request in state `PENDING` MAY be cancelled by a governance authority possessing at least the same authorization tier required to have created the request (HRAC-REQ-016) — this is a deliberate, narrow inclusion (not an invented feature): it mirrors this repository's existing revocation precedent (HHCE-001/HPSE-001 credential and signer revocation, HRWP-REQ-054) applied to a pending ceremony rather than a durable registry record. Cancellation transitions the request directly to `CANCELLED` (HRAC-REQ-011) and SHALL invalidate its ceremony-session identifier immediately — a client that later posts a response against a cancelled request's session SHALL be rejected with `error_type = request_cancelled` (§25), never silently accepted or misreported as expired.

**HRAC-REQ-042.** A request in state `RESPONSE_RECEIVED`, `VERIFIED`, `COMPLETED`, `EXPIRED`, or `FAILED` SHALL NOT be cancelled — cancellation is a `PENDING`-only operation (HRAC-REQ-011's transition table). A cancelled request can never later complete under any condition (HRAC-REQ-012's terminal-state closure).

## 25. Closed failure/error vocabulary

**HRAC-REQ-043.** The following `error_type` vocabulary is frozen and closed, mirroring HSCE-REQ-046/047's own small-closed-set-of-categories discipline rather than one error per distinct English sentence:

| `error_type` | Meaning | Resulting state (if request-scoped) |
|---|---|---|
| `governance_authorization_missing` | Underlying operation not yet authorized at request-creation time (§34) | request never created |
| `no_authorized_signer` | HSCE-REQ-080-equivalent signer resolution fails at creation or at re-resolution time (§19) | request never created, or `FAILED` |
| `operation_not_found` | Job/PER record locator cannot resolve (HSCE-REQ-013/016-equivalent) | request never created |
| `provider_unavailable` | No compatible remote-WebAuthn client/authenticator path resolvable at verification (rare — mostly a client-side condition reported by the client itself, not server-detected) | `FAILED` |
| `human_signing_cancelled` | Human explicitly declines/cancels the client-side WebAuthn prompt (client-reported) | `FAILED` |
| `malformed_response` | Response fails schema validation (§18), or `request_id` mismatch (§23) | `FAILED` |
| `verification_failed` | HRWP-001 §16 server-side verification fails for any reason (bad signature, wrong origin, wrong RP-ID, wrong credential, missing UP/UV, challenge mismatch) — HRWP-001's own sub-taxonomy is not re-exposed at this layer, mirroring HSCE-REQ-049's vocabulary-separation discipline | `FAILED` |
| `toctou_context_changed` | Live-state re-resolution (§19 step 2) differs from the request's creation-time snapshot | `FAILED` |
| `expired_challenge` | Response arrives after `expires_at`, or a fetch/verification attempt targets an already-lazily-expired request | `EXPIRED` (no state change caused by the late attempt itself) |
| `request_already_consumed` | A second (or losing-concurrent) response targets an already-`VERIFIED`/`COMPLETED` request | no state change |
| `request_cancelled` | A response targets an already-`CANCELLED` request | no state change |
| `evidence_persistence_failure` | Atomic evidence-record publish (§29, mirroring HSCE-REQ-052) fails at the filesystem/store layer | `FAILED` |

**HRAC-REQ-044.** This vocabulary is closed. A future implementation SHALL NOT introduce an `error_type` outside this table without a governed contract amendment (mirrors HSCE-REQ-048). Errors are never expressed using HRWP-001's or HATP-001's own internal verification-status vocabulary directly (mirrors HSCE-REQ-049) — `verification_failed` is this layer's own closed category name for "HRWP-001's verifier said no," not a re-export of HRWP-001's internal check names.

## 26. Server restart / durability

**HRAC-REQ-045.** Outstanding remote assertion requests (states `PENDING`, `RESPONSE_RECEIVED`) SHALL NOT be required to survive a server/process restart in this contract's v1.0 scope. A restart invalidates every non-terminal request: on restart, any request still in `PENDING` or `RESPONSE_RECEIVED` SHALL be treated as no longer resolvable to `COMPLETED` by any subsequently-arriving response for that `request_id` — an implementation MAY represent this by eagerly marking such requests `FAILED` (`error_type = server_restarted`, added to §25's table only if an implementation needs to distinguish it diagnostically; not a new outcome category, since the externally observable effect is identical to `expired_challenge`: no completion is ever possible) or by simply never persisting `PENDING`/`RESPONSE_RECEIVED` state durably to begin with and losing it naturally. This is an explicit v1 choice, not an unresolved ambiguity: durable pending-request survival across restart is deferred to a future contract revision if operational experience shows it is needed, avoiding half-durable ambiguity (per the governing prompt's own instruction) in this freeze.

**HRAC-REQ-046.** A `COMPLETED` request's remote evidence record (§29) is, once durably published, unaffected by any subsequent server restart — identical in kind to HSCE-001's own evidence-store durability guarantee (HSCE-REQ-052's crash-after-publish-leaves-canonical-artifact-intact property, reused verbatim).

## 27. Request-store authority classification

**HRAC-REQ-047.** If a request/session store is required by a future implementation, it is authority-bearing in one narrow respect only: it is the sole record of which `request_id` has already reached `COMPLETED` (§20, replay/idempotency enforcement) and of each request's creation-time canonical snapshot used for the TOCTOU recheck (§19). It is not authority-bearing for cryptographic trust — a stored request record never substitutes for HRWP-001 verification (mirrors HSCE-REQ-060/061's "evidence-file existence is never approval" discipline, restated for request records: request-record existence is never verification success). Canonical location: repository-local, analogous in trust classification to HSCE-001's own `.pcae/hatp-evidence/` (untrusted-for-cryptographic-purposes, HSCE-REQ-060), though this contract does not fix its literal path (an implementation-phase decision, since unlike HSCE-001's evidence store this store may need to be reachable from a network-facing process, a topology this contract does not select, per §41). Locking/transaction expectations: the same atomic-exclusive-create discipline already required for consumption-marking (HRAC-REQ-035) suffices; no additional locking primitive is required by this contract. Single-use semantics: restates HRAC-REQ-035/036. Cleanup/expiry: terminal-state requests (§7) MAY be pruned after an operationally-chosen retention window; this contract does not fix that window, only that pruning a terminal request never re-enables it (§7's terminal-state closure is permanent, not merely until cleanup).

**HRAC-REQ-048.** This future store will likely become HMIC-relevant (§49) once implemented, exactly as `hatp_evidence_store.py`/`rollback_approval_evidence.py` already are.

## 28. Signing result — what HSCE receives

**HRAC-REQ-049.** On reaching `COMPLETED`, the orchestration layer produces exactly: the verified `HumanApprovalProvenanceProof`-shaped fields (constructed from the request's own bound context, HRAC-REQ-017, plus the now-verified assertion — identical field set to what `sign_rollback_evidence` already constructs synchronously, HSCE-REQ-018's table, unamended) and a HRWP-001-shaped verified-assertion evidence blob (HRWP-REQ-050's own closed-field remote evidence schema, unamended). This is a provider-specific *verified* proof/result — never raw, unverified browser JSON (§18's response schema is discarded once verification succeeds; only the verified, re-derived proof fields and the HRWP-shaped evidence blob progress past `VERIFIED`).

**HRAC-REQ-050.** The current production integration shape (`hatp_signing_ceremony.py`, re-read this phase) constructs a `HumanApprovalProvenanceProof`, calls `canonicalize_hatp_proof_payload`, invokes the provider synchronously, and calls `build_hatp_signed_evidence_envelope`/`HATPEvidenceStore.publish` directly, in-process. This contract's remote path SHALL produce the same `HumanApprovalProvenanceProof` shape and the same `build_hatp_signed_evidence_envelope` call, but invoked from the asynchronous verification-handoff step (§19 step 5) instead of from a synchronous CLI call — the envelope-construction and evidence-store publication code (`hatp_signed_evidence.py`/`hatp_evidence_store.py`) is reused unmodified; this contract requires no new envelope format for the resulting `HATPSignedEvidenceEnvelope` itself (§29 defines what additional metadata, if any, is captured alongside it).

## 29. Evidence capture — canonical fields

**HRAC-REQ-051.** Once `VERIFIED`, the orchestration layer SHALL capture a **remote evidence record**, additive to (never a modification of) HSCE-001's `HATPSignedEvidenceEnvelope` (HSCE-REQ-032's closed four-field schema, unamended), containing at minimum: `request_id`, `evidence_id` (the resulting `HATPSignedEvidenceEnvelope`'s own `evidence_id`, HSCE-REQ-036/037, unamended formula and meaning), `signer_key_id`, `principal_id`, `provider_profile` (`HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN`), `credential_id`, the challenge/request digest (HRAC-REQ-024's own value), `expected_rp_id`/allowed origin actually matched, the user-presence result and user-verification result HRWP-001's verifier reported (§33 restated), the verification result (`VERIFIED`/`FAILED` and, if failed, the closed `error_type`, §25), `created_at`/`completed_at` timestamps, and `governance_authorization_reference` (HRAC-REQ-017, restated for audit traceability). No private key material, PIN, or other provider secret is ever included (mirrors HSCE-REQ-050 verbatim).

**HRAC-REQ-052.** The resulting `HATPSignedEvidenceEnvelope` itself (HSCE-001's own artifact, unamended shape) SHALL be published through `HATPEvidenceStore.publish` (149O.12A, unmodified) exactly as the synchronous path already does — this contract's own remote evidence record (HRAC-REQ-051) is stored alongside/adjacent to, never inside or in place of, that envelope. This preserves HSCE-001's own closed four-field envelope schema (HSCE-REQ-032) untouched while adding the request/ceremony-specific audit metadata a purely local, synchronous ceremony never needed to record (there being no network round trip, no separate client device, and no asynchronous correlation problem to document in that case).

## 30. Raw client data — minimum retained

**HRAC-REQ-053.** The remote evidence record (§29) SHALL retain only digests/canonical-field derivatives of `clientDataJSON`/`authenticatorData`/`signature` (specifically: whatever HRWP-001's own evidence schema, HRWP-REQ-050, already persists as part of the resulting envelope's `provider_assertion` bytes, unamended) — it SHALL NOT additionally retain a second, redundant raw copy of the full client response payload outside that already-defined provider-assertion encoding. This closes the auditability-vs-retention question in favor of the minimum already required by HRWP-001's own frozen evidence format, adding nothing beyond it at this contract's layer.

## 31. Privacy

**HRAC-REQ-054.** The remote evidence record (§29) SHALL NOT collect or persist: browser fingerprint, IP address, device name/model, or any other client-device identity signal, unless a future contract amendment names a specific security/audit justification for one such field (mirrors HRWP-001's own §31 privacy stance, restated here as this contract's own binding rule rather than only HRWP-001's non-normative "what evidence must not include" framing). The credential itself proves possession; the client device is never PCAE governance identity (HRWP-REQ-038, restated).

## 32. Sign-counter evidence

**HRAC-REQ-055.** If HRWP-001's verifier validates or reports a WebAuthn `signCount` value (an authenticator-model-dependent, optional check HRWP-001 itself does not mandate as of v1.0, HRWP-REQ-033 item (f) covering only the signature itself), the remote evidence record MAY capture the reported `signCount` value as diagnostic metadata only. This contract does not promise clone-detection capability where authenticator semantics do not meaningfully support it (mirrors the governing prompt's own caution) — `signCount` capture here is observational, never itself a verification gate this contract adds beyond what HRWP-001 already requires.

## 33. User-presence / user-verification evidence

**HRAC-REQ-056.** The remote evidence record SHALL capture, as reported by HRWP-001's verifier: whether user-presence was required and observed (always required, HRWP-REQ-035), and whether user-verification was required (`"preferred"`, HRWP-REQ-035) and observed. Server verification policy (HRWP-001's, unamended) remains authoritative for what is *required*; this contract's evidence only records what was *observed*, never substituting its own policy.

## 34. Governance authorization ordering

**HRAC-REQ-057.** Restates HRAC-REQ-016 as the standing sequencing rule for the entire ceremony: governance authorization for the underlying operation MUST already exist before a remote assertion request is ever created; the remote ceremony (request → session → response → verification → evidence) never itself manufactures, substitutes for, or independently establishes that authorization. The ceremony's job is producing a cryptographic possession proof for an operation that is already authorized to require one — never authorizing the operation itself.

## 35. Client-side "Continue" confirmation

**HRAC-REQ-058.** A ceremony-delivery web page MAY present a human-facing "Continue"-style confirmation before invoking `navigator.credentials.get()`, purely as UX (matching the local synchronous path's own blind-touch-defense preview UX precedent, HSCE-REQ-071, reused as a UX pattern only). This contract does not require such a button as a security control: server-side governance authorization (§34) and HRWP-001 verification (§19) remain the sole authority boundary regardless of whether a client-side confirmation step exists, mirrors HSCE-REQ-071's own "UX precedent only, never a self-asserted-identity model" caution.

## 36. iPhone NFC / 37. iPhone USB-C / 38. Mac UX (non-normative, carried forward)

**HRAC-REQ-059.** The expected async flow — open ceremony URL, invoke WebAuthn, platform prompts for a security key (NFC tap or USB-C plug on iPhone; USB-C or already-attached on Mac), return the assertion — is documented here for orientation only; no iOS-specific or platform-specific UI text is frozen as contract (mirrors HRWP-REQ-065's own "UNKNOWN, platform-version-dependent" disposition, unchanged and not re-tested by this contract). Mac and iPhone SHALL use the identical server-side ceremony contract (§39's portability discussion) — transport/platform differences are presentation concerns, never authority concerns (HRWP-REQ-032, restated).

## 39. Ceremony portability across devices

**HRAC-REQ-060.** A ceremony session opened on one device is not, by default, silently transferable to a second device unless the same single-use session/request design intentionally permits it (a session identifier, once fetched, MAY remain openable from a second device until a valid response is posted, since HRAC-REQ-035's exclusive-publish consumption — not session-open-count — is what actually enforces one-time completion). If cross-device opening is permitted (the simpler v1.0 default, since restricting a session to "first device that opened it" would need its own additional state this contract does not otherwise require), the server still enforces the exact challenge/request binding (§19) regardless of which device's browser ultimately posts the winning response (§22's concurrent-response handling already covers the resulting race).

## 40. Phishing / origin boundary

**HRAC-REQ-061.** This contract creates no alternate origin, callback origin, or redirect target that would weaken WebAuthn's own origin/RP-ID phishing resistance (HRWP-001 §12-§13/§40, unamended). The ceremony-delivery page SHALL be served from the identical fixed origin HRWP-REQ-029 already requires for the WebAuthn ceremony itself — this contract does not introduce a separate "delivery domain" distinct from the "WebAuthn RP origin," since doing so would itself be the kind of alternate-origin weakening HRWP-REQ-040 (part of the governing prompt's own concern) warns against.

## 41. RP-ID infrastructure dependency (named, not resolved)

**HRAC-REQ-062.** This contract carries forward HRWP-001's own distinction unmodified: semantic RP-ID/origin *requirements* are frozen (HRWP-REQ-026-031, this contract's own §12-§13/§40 build directly on them); the literal domain name, TLS certificate, and network topology remain unresolved infrastructure decisions (HRWP-REQ-027/031). This contract additionally identifies exactly what it will consume once that infrastructure exists: a single fixed `expected_rp_id` value and a single fixed allowed-origin set (HRAC-REQ-017's `expected_rp_id` field, HRAC-REQ-033's verification-time use) — no new infrastructure dependency beyond what HRWP-001 already named.

## 42. HSCE-001 compatibility mapping

**HRAC-REQ-063.** The following HSCE-001 concepts are reused **unchanged** by this contract: `HumanApprovalProvenanceProof`'s shape and canonical payload function (HSCE-REQ-018's table, `canonicalize_hatp_proof_payload`); `HATPSignedEvidenceEnvelope`'s closed four-field schema (HSCE-REQ-032); the evidence-ID formula and content-addressing precision (HSCE-REQ-036-038); the evidence-store root, layout, and exclusive-publish mechanism (HSCE-REQ-041/042/052); evidence lookup semantics (HSCE-REQ-044); the closed error-vocabulary-to-exit-code pattern *style* (HSCE-REQ-046-048, though this contract's own vocabulary, §25, is a distinct closed set at a different layer, not a re-export); the storage trust classification and forbidden-pattern discipline (HSCE-REQ-060/061); the blind-touch-defense UX precedent (HSCE-REQ-071, reused as UX pattern only, §35); and the TOCTOU cross-record recheck discipline (HSCE-REQ-069/070/080-083), extended (not altered) to run at verification time instead of only pre/post a single synchronous touch.

**HRAC-REQ-064.** New concepts this contract introduces, additive to HSCE-001, requiring no change to any existing HSCE-001 requirement: the request/session state machine (§7); `request_id` as a distinct, non-content-addressed identity class from `evidence_id` (§8); the challenge-context canonicalization and digest scheme (§11-§13); the remote evidence record (§29-§33), a new artifact type distinct from `HATPSignedEvidenceEnvelope`; and the closed request-layer error vocabulary (§25), distinct from HSCE-001's own CLI-layer error vocabulary.

## 43. Evidence-type / profile discriminator

**HRAC-REQ-065.** The `HATPSignedEvidenceEnvelope`'s embedded `proof.provider_profile` field already carries `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN` (HRWP-REQ-008, unamended) — this alone is a sufficient, already-existing discriminator distinguishing a remote-WebAuthn-sourced envelope from a local-FIDO2-sourced one; this contract does NOT introduce a second, redundant evidence-type/profile field on the envelope itself (no schema widening of HSCE-REQ-032's closed four-field set). The remote evidence record (§29), being a distinct, additive artifact (not a field on the envelope), carries its own implicit type by virtue of its own distinct schema and storage location — no further discriminator field is needed there either.

## 44. `protocol_name` non-blocking finding — disposition

**HRAC-REQ-066.** Phase 149O.20L.7O.2N.8 independently confirmed HRWP-REQ-019's claim that `protocol_name = "WEBAUTHN"` requires "no schema widening" is inaccurate: `hatp_hardware_credentials.py`'s `_PROTOCOL_VALUES` is a closed `frozenset({"FIDO2", "PIV"})` that would reject it. This contract's own signer-resolution reuse (§9, HRAC-REQ-019-020) reads `HardwareCredentialRecord.provider_profile`, never `protocol_name`, at signing/verification time — HSCE-REQ-080's six-step resolution (reused unamended, §9) does not check `protocol_name` at all. **This contract therefore does not depend on that finding being resolved to be internally coherent or implementable as contract text.** It nonetheless MUST be resolved before a real `HardwareCredentialRecord` with `protocol_name = "WEBAUTHN"` can ever be durably enrolled (HRWP-001's own registration-flow scope, §8, unamended, not reopened by this contract) — i.e., before HRAC-001's remote *enrollment* prerequisite exists at all, remote *assertion* (this contract's subject) has no live credential to assert against. This contract recommends, but does not itself perform, a narrow future HRWP-001 text repair (widening `_PROTOCOL_VALUES` to include `"WEBAUTHN"`, or correcting HRWP-REQ-019's prose to acknowledge the required widening) ahead of — not as part of — implementation. The finding is not allowed to disappear: it is carried forward here, explicitly, as this contract's own §54 prerequisite-DAG entry.

## 45. Contract relationship / no circular authority

**HRAC-REQ-067.** This contract normatively references and depends on HRWP-001 (provider/cryptographic/evidence-format authority) and HSCE-001 (existing local-ceremony CLI/evidence-store authority, and this contract's own additive-evidence-schema precedent), and, through HSCE-001's own unamended dependency chain, HPSE-001 (`SignerRecord`/`PrincipalRecord` identity) and HBDC-001 (`DeploymentBinding`). No authority flows in the reverse direction: HRWP-001 and HSCE-001 remain independently meaningful and unamended whether or not this contract is ever implemented; this contract cannot retroactively grant itself authority those contracts do not already grant, and it introduces no cycle (HRAC-001 depends on HRWP-001/HSCE-001; neither depends on HRAC-001).

## 46. HSCE-001 versioning impact

**HRAC-REQ-068.** HSCE-001 does NOT require a version bump for this contract to exist or for a future implementation to build to it. Verification: every HSCE-001 concept this contract reuses (§42) is reused unchanged, in its existing closed form; this contract adds new artifacts (the remote evidence record, the request/session state machine) additively, alongside HSCE-001's existing surface, never inside or in conflict with it. HSCE-001's own text (§36, HSCE-REQ-074's neighboring provisions) already anticipates exactly this kind of future companion without requiring self-amendment — consistent with HRWP-001's own HSCE-REQ-060/HRWP-REQ-060 framing of the gap this contract closes as a "companion," never an "amendment."

## 47. Open/closed vocabulary — new-field audit

**HRAC-REQ-069.** For every new vocabulary item this contract introduces, its current production parser status is: `operation_type` (§8) — does not yet exist in production; a future implementation choosing a closed Python `Enum`/`frozenset` (not an open string) avoids repeating HRWP-REQ-019's mistake, and this contract requires that closed-vocabulary choice explicitly (HRAC-REQ-017's own "never an open string" note). `error_type` (§25) — does not yet exist in production; this contract's own table (HRAC-REQ-043) is closed by construction from this freeze forward, with the identical "any addition requires a governed amendment" discipline HSCE-REQ-048 already establishes. `provider_profile`/`protocol_name` (§44) — pre-existing HRWP-001 vocabulary, correctly identified there as requiring the narrow future repair named in §44; this contract adds no new value to either field. State-machine values (§7) — do not yet exist in production; a future implementation SHALL represent them as a closed enum, never an open string, from first implementation (avoiding ever needing a "was this always closed?" audit later).

## 48. Trusted-kernel vs. adapter boundary

**HRAC-REQ-070.** Inside PCAE's trusted governance kernel (future HMIC-001 scope, §49): request creation and challenge-context construction (§8, §11-§13); the pending-request state manager and its state-transition enforcement (§7); response correlation and the request-identity match (§18-§19, §23); the credential allow-list construction (§10, §20); the call to HRWP-001's authoritative verifier and the TOCTOU re-resolution (§19); the exclusive-publish one-time-consumption mechanism (§20, §35-§36); and the remote-evidence-record/envelope builder (§29-§30). Thin, replaceable adapters outside the trusted kernel: the HTTP transport layer, the ceremony-delivery page's HTML/JavaScript, and QR/deep-link presentation — these relay bytes the trusted kernel produces and validates; they carry no independent trust and are never HMIC-scope-bearing on their own (mirrors HRWP-REQ-062 verbatim, restated for this contract's own component list).

## 49. Future HMIC impact

**HRAC-REQ-071.** No HMIC-001 amendment occurs in this contract. A future implementation of every trusted-kernel component named in §48 — a request/challenge constructor, a pending-request state-manager module, a response-correlation/verification-handoff module, a consumption/exclusive-publish module, and a remote-evidence-record builder — will each become new authority-bearing source requiring HMIC-001 source-scope inclusion and independent verification before activation, exactly as `hatp_signing_ceremony.py`, `hatp_evidence_store.py`, and `hatp_fido2_provider.py` already required (HRWP-REQ-061, restated for this contract's own component list). Final HMIC member count is not derivable before that code exists (mirrors HRWP-REQ-061's own explicit refusal to pre-derive it).

## 50. Required future security tests

**HRAC-REQ-072.** A future implementation's independent verification MUST exercise, at minimum: challenge replay (a consumed or already-verified challenge reused); expired response (§21/§37); wrong credential (not in the resolved `allowCredentials` set); wrong signer (a `DeploymentBinding`/`SignerRecord` mismatch surfacing at either creation-time or verification-time re-resolution); wrong repository (`repository_id` mismatch); wrong operation (`operation_reference` mismatch); wrong origin; wrong RP-ID; bad signature; missing user-presence; missing user-verification where policy requires it; two genuinely concurrent valid responses (§22); a cross-session/cross-request substitution attempt (a response's `request_id` not matching the session it arrived through, §23); server-restart behavior (§26); a cancelled request receiving a late response (§24); and a malformed/schema-violating response (§18). This list mirrors, and is not smaller in coverage than, the governing prompt's own §50 enumeration.

## 51. Synthetic interoperability gate

**HRAC-REQ-073.** No implementation phase's first test suite SHALL require the human's real hardware key or a real WebAuthn browser session. A synthetic browser/WebAuthn fixture (a deterministic fake `authenticatorData`/`clientDataJSON`/`signature` triple, matching HRWP-REQ-051's own explicit caution about not assuming byte-identical wire compatibility without confirming it first) MUST pass full interoperability testing — every state-machine transition (§7), every failure category (§25), and the full attack matrix (§50) — before any real hardware or real remote WebAuthn ceremony is attempted. This is frozen as a hard implementation gate, not a suggestion.

## 52. Implementation prerequisite DAG

**HRAC-REQ-074.** The dependency-ordered sequence for future work, subject to the next phase's own scoped analysis (this contract does not bind it beyond ordering the hard dependencies actually named above): (1) independent verification of this contract (HRAC-001); (2) resolution of the §44 `protocol_name`/HRWP-REQ-019 finding (a narrow HRWP-001 text repair — a hard prerequisite for real credential enrollment, not for this contract's own internal coherence, per HRAC-REQ-066); (3) RP-ID/origin/HTTPS infrastructure selection (HRWP-REQ-027/031, unresolved by both HRWP-001 and this contract); (4) server-side request/challenge/state-machine/verifier-handoff implementation (hac-dell-side only, still no browser client); (5) minimal browser WebAuthn ceremony client; (6) synthetic interoperability tests (§51 gate); (7) independent verification of steps 4-6; (8) HMIC-001 source-scope expansion (§49); (9) deployment + recertification; (10) first real remote WebAuthn *enrollment* (HRWP-001's own scope, its own narrowly-scoped phase, a hard prerequisite before any real remote *assertion* can occur, since assertion requires an already-enrolled `HardwareCredentialRecord`); (11) first real remote WebAuthn *assertion* ceremony under this contract, its own narrowly-scoped phase, not combined with step 10. Steps 3 and 2 have no ordering dependency on each other; both must complete before step 4 can produce a working implementation, though step 4's code MAY be written and unit-tested against synthetic fixtures (step 6) before either resolves, per this repository's existing precedent of freezing/implementing contract-shaped code ahead of infrastructure provisioning.

## 53. What this contract does NOT do

**HRAC-REQ-075.** This contract creates no request-store code, no HTTP route, no WebAuthn JavaScript, no provider implementation, no production evidence schema, no new constant in `src/pcae/` source, no real remote assertion, no real credential, no DNS/TLS provisioning, no HMIC-001 amendment, and no redeployment. It amends neither HRWP-001 nor HSCE-001 nor any contract either depends on. It is contract text only.

## 54. Requirement count and prompt cross-reference

**HRAC-REQ-076.** This contract defines 76 normative requirements, `HRAC-REQ-001` through `HRAC-REQ-076`, sequential, no gaps, no duplicates.

## 55. Freeze verdict

```
HRAC-001 v1.0 FROZEN
— HATP REMOTE ASSERTION CEREMONY CONTRACT COMPLETE
ASYNC REQUEST / RESPONSE / EVIDENCE ORCHESTRATION: DEFINED
HRWP-001 CRYPTOGRAPHIC PROFILE: PRESERVED, UNAMENDED
HSCE-001 CORE SEMANTICS: PRESERVED, UNAMENDED
REMOTE SIGNING: CONTRACTUALLY ORCHESTRATABLE
NO IMPLEMENTATION. NO REAL HARDWARE EFFECT.
```

## 56. Recommended next phase

The independent verifier SHALL, at minimum: re-derive this contract's dependency chain (HRWP-001 v1.0, HSCE-001 v1.3) fresh from those contracts' own text, not from this contract's summary of them; confirm the state machine (§7) is complete and every transition closed; confirm the request-identity/challenge-construction scheme (§8, §11-§13) leaves no ambiguous concatenation; confirm the closed failure vocabulary (§25) covers every case §50/§72 name; confirm no HSCE-001 or HRWP-001 requirement is contradicted or silently narrowed; and confirm the §44 `protocol_name` finding's disposition (carried forward, not resolved) is stated accurately. Do not begin RP-ID/TLS infrastructure selection or any server/client implementation until that independent verification passes. If the independent verifier finds an HSCE-001 incompatibility this contract's authors missed, the recommended remedy is a narrow HSCE-001 or HRWP-001 contract repair, mirroring this repository's existing repair-then-reverify precedent — not a silent reinterpretation of either contract's frozen text.
