# Phase 149O.20L.7O.2N.9 — HSCE Remote WebAuthn Assertion Ceremony and Evidence-Capture Companion Contract Freeze

**Status:** COMPLETE — CONTRACT/ARCHITECTURE FREEZE ONLY. NO IMPLEMENTATION. NO WEBAUTHN SERVER. NO CLIENT. NO CREDENTIAL CREATED. NO HMIC CHANGE. NO REDEPLOYMENT.

## 1. Phase entry

- True phase-entry commit (local HEAD == origin/main at phase start): `7740f524` (149O.20L.7O.2N.8's exact-match `pcae_push_check` trust-field-value finalization-gate repair commit — the phase this one directly follows).
- Latest completed phase: 149O.20L.7O.2N.8 — HRWP-001 Remote WebAuthn Provider Contract Independent Verification (INDEPENDENTLY VERIFIED WITH ONE NON-BLOCKING FINDING, no blocking defect).
- `git status --short` clean at phase start; `pcae session bootstrap --agent-id claude-local --sync-lock` confirmed agent lock healthy, push clean/nothing-to-push, recommended next phase matching this phase's own subject exactly.

## 2. Entering verified state (carried forward, not re-derived)

- HRWP-001 v1.0: INDEPENDENTLY VERIFIED (Phase 149O.20L.7O.2N.8), one Non-Blocking finding (protocol_name/HRWP-REQ-019, §44 below carries it forward).
- Hybrid local-CTAP + remote-WebAuthn provider architecture: VERIFIED.
- Remote WebAuthn registration: CONTRACTUALLY SUPPORTED (HRWP-001 §8).
- Remote WebAuthn assertion/signing: CONTRACTUALLY SUPPORTED at the provider cryptographic-profile boundary (HRWP-001 §26-§27).
- HSCE-001: v1.3, UNCHANGED. HHCE-001/HPSE-001/HBDC-001: unchanged. HMIC: v1.7/38, real Dell certification VALID.
- Current real Trust-Enrollment: `HardwareCredentialRecord`/`Principal`/`Signer`/`DeploymentBinding` all ABSENT. HATP: NOT READY / NOT ACTIVE. Runtime: Observed / observe / unavailable.

## 3. Primary-contract re-derivation performed this phase

Read fresh, in full, this phase (not from either predecessor phase's own summary): `docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md` (HSCE-001 v1.3, all 84 requirements, §1-§48 including the three in-place repairs) and `docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md` (HRWP-001 v1.0, all 68 requirements). Read fresh: `src/pcae/core/hatp_signing_ceremony.py` in full (the exact current production synchronous orchestrator — `resolve_signing_context`, `_resolve_deployment_binding_signer`, `sign_rollback_evidence`, `production_sign_rollback_evidence`).

## 4. New companion contract

**HRAC-001 v1.0** — "HATP Remote Assertion Ceremony Contract" — `docs/contracts/HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md`, 76 requirements (`HRAC-REQ-001`–`HRAC-REQ-076`), FROZEN, not yet independently verified, not implemented. Named to state its subject precisely: the asynchronous request/response/correlation/evidence-capture *orchestration* for a remote-WebAuthn *assertion* ceremony — distinct from HRWP-001 (provider/cryptographic contract) and HSCE-001 (existing synchronous CLI ceremony/evidence-store contract). Scope: remote *assertion* (signing) ceremonies only; remote *registration* (enrollment) remains HRWP-001 §8's own, unreopened scope.

## 5. Relationship to HSCE-001 and HRWP-001

Strictly additive, mirroring HSCE-001's own "additive to HATP-001/RAE-001" and HPSE-001's own "additive to HATP-001/HBDC-001" precedent. Depends on HRWP-001 v1.0 (unamended) and HSCE-001 v1.3 (unamended); through HSCE-001's own chain, also HPSE-001 v1.1 and HBDC-001 v1.2 (both unamended). No contract in this dependency chain requires amendment for HRAC-001 to exist or for a future phase to implement it (contract §46, HRAC-REQ-068 — see §17 below).

## 6. Current-vs-remote signing orchestration analysis

`hatp_signing_ceremony.py::sign_rollback_evidence` (re-read in full this phase): resolve context A (no touch) → resolve `DeploymentBinding`-based signer identity (HSCE-REQ-080) → render blind-touch preview, synchronous same-process human confirmation (`input()`) → construct proof, call `provider.request_signature()` synchronously, blocking in-process → resolve context B + signer resolution B for TOCTOU recheck → build/publish envelope. All six steps execute in one CLI invocation; no network round trip, no persisted intermediate state. The remote path's only structural difference: steps (3)-(4) move to a separate client device at an unknown future time, reachable only over a network round trip (contract §5, HRAC-REQ-008/009). Steps (1), (2), (5)-(6) are required to run again, unchanged in kind, at verification time.

## 7. State machine

Frozen closed set: `PENDING`, `RESPONSE_RECEIVED`, `VERIFIED`, `COMPLETED`, `EXPIRED`, `FAILED`, `CANCELLED` (7 states, deliberately narrower than the 9-state menu offered — no separate `CREATED`/`AUTHORIZED` state, since a request becomes fetchable atomically with already-authorized creation; no separate `CONSUMED` state, since reaching `COMPLETED` under this contract's one-time-consumption model IS the consumption event). Transitions: `PENDING`→`RESPONSE_RECEIVED`/`EXPIRED`/`CANCELLED`; `RESPONSE_RECEIVED`→`VERIFIED`/`FAILED`; `VERIFIED`→`COMPLETED`/`FAILED` (persistence failure only). `COMPLETED`/`EXPIRED`/`FAILED`/`CANCELLED` are terminal, no re-entry. Contract §7, HRAC-REQ-010-014.

## 8. Request identity

`request_id`: fresh, cryptographically random 256-bit value (64 lowercase hex), never content-derived — deliberately distinct from HSCE-001's `evidence_id = digest_hatp_proof_payload(proof)` content-addressing convention, because a pending request (pre-signature) has no signed content to address, and unguessable identity (not content-addressing) is the correct security property for a pending attempt. Bound fields: `request_id`, `repository_id`, `canonical_deployment_root`, `operation_type`, `operation_reference`, `principal_id`, `signer_key_id`, `provider_profile`, binding/decision id+digest, `expected_rp_id`, `allowed_credential_ids`, `domain`, `nonce`, `created_at`/`expires_at`, `governance_authorization_reference` — all resolved from the identical HSCE-001 canonical live-state sources, never client-suppliable. Contract §8, HRAC-REQ-015-018.

## 9. Challenge derivation, encoding, domain separation

Challenge context: canonical structure of exactly the fields above, serialized with HSCE-REQ-053's identical canonicalization discipline (UTF-8, sorted keys, no NaN, duplicate-key rejection) — reused, not reinvented. Challenge value = SHA-256 digest of those canonical bytes, base64url-encoded (WebAuthn's own wire convention) — a digest, not the full canonical bytes, since the server reconstructs and re-hashes independently at verification time. Domain-separation string frozen as **`PCAE/HATP/HRAC/SIGN/V1`**, included as a field inside the canonical structure, never concatenated ad hoc. Contract §11-§13, HRAC-REQ-022-026.

## 10. Session model, delivery, client contract

Session token/URL is a locator only, never authority (restates HRWP-REQ-045). Delivery: short-lived HTTPS URL, presentation-agnostic (QR/deep-link/manual entry; Telegram or any outbound channel MAY deliver it, never becomes an inbound authority channel). Client may fetch only: challenge, `expected_rp_id`, `allowCredentials`, timeout, fixed `userVerification: "preferred"` policy, display text, `request_id` — never server-internal digests/identifiers beyond what WebAuthn itself needs. Client response schema: `request_id`, `credential_id`, `authenticatorData`, `clientDataJSON`, `signature`, optional `userHandle` — no other field carries authority. Contract §14-§18, HRAC-REQ-027-032.

## 11. Verification handoff

The orchestration layer never performs its own cryptographic/origin/RP-ID check — it calls HRWP-001's authoritative server-side verifier (HRWP-REQ-033/034) exactly once per response, with the server-reconstructed expected challenge and re-resolved `allowCredentials`, and treats the outcome as dispositive. A TOCTOU re-resolution (mirroring HSCE-REQ-083 exactly, re-run at verification time instead of only pre/post one synchronous touch) runs alongside it; any mismatch discards the assertion, no evidence persisted. Contract §19, HRAC-REQ-033-034.

## 12. Replay protection, one-time consumption, concurrency

One-time consumption reuses HSCE-REQ-052's identical atomic hard-link exclusive-publish technique, applied to a path keyed by `request_id` rather than `evidence_id` — the first successful `os.link` call is the sole "consumed" event; every other concurrent writer loses and is rejected (`request_already_consumed`), generalizing to any number of concurrent responses (Mac + iPhone both answering the same ceremony, or more). Unlike HSCE-001's evidence store, there is no idempotent-byte-identical-rewrite case here: a second WebAuthn assertion is never byte-identical to the first (each `getAssertion` re-signs fresh bytes), so a second response is always rejected outright, never treated as a safe duplicate. Late responses (after `expires_at`) are rejected before any verification call, `error_type = expired_challenge`, never reviving the request. No "latest pending request" correlation exists anywhere — every response binds an exact `request_id`. Contract §20-§23, HRAC-REQ-035-040.

## 13. Cancellation

Supported, narrowly: a `PENDING`-only operation, requiring the same governance-authorization tier as request creation, mirroring existing HHCE-001/HPSE-001 revocation precedent applied to a pending ceremony. A cancelled request can never later complete. Contract §24, HRAC-REQ-041-042.

## 14. Server restart / durability

Explicit v1.0 choice: outstanding non-terminal requests (`PENDING`/`RESPONSE_RECEIVED`) do NOT survive a server/process restart — a restart invalidates every non-terminal request, with the identical externally-observable effect as `expired_challenge`. A `COMPLETED` request's evidence, once published, is unaffected by restart (HSCE-REQ-052's own crash-after-publish durability, reused verbatim). No half-durable ambiguity. Contract §26, HRAC-REQ-045-046.

## 15. Request-store authority classification

Narrowly authority-bearing only for consumption-state and creation-time snapshot; never a substitute for cryptographic trust (mirrors HSCE-REQ-060/061's "existence is never approval," restated for request records). Locking reuses the same atomic-exclusive-create discipline already required for consumption-marking; no new locking primitive. Contract §27, HRAC-REQ-047-048.

## 16. Signing result and evidence capture

The verified result mapped back to HSCE: the identical `HumanApprovalProvenanceProof` shape and `canonicalize_hatp_proof_payload`/`build_hatp_signed_evidence_envelope`/`HATPEvidenceStore.publish` call already used synchronously, invoked from the async verification-handoff step instead of a synchronous CLI call — no new envelope format, no HSCE-001 schema widening. An additive **remote evidence record**, distinct from and never a modification of `HATPSignedEvidenceEnvelope`'s closed four-field schema, captures request-layer audit metadata a purely local ceremony never needed: `request_id`, `evidence_id`, signer/credential identity, challenge/request digest, RP-ID/origin actually matched, UP/UV results, verification outcome and `error_type`, timestamps, `governance_authorization_reference` — no private key material, no unnecessary browser fingerprint/IP/device identity. Raw `clientDataJSON`/`authenticatorData`/`signature` are retained only as HRWP-001's own already-defined `provider_assertion` encoding — no redundant second raw copy. `signCount`, if reported, MAY be captured as diagnostic metadata only, promising no clone-detection beyond what authenticator semantics support. Contract §28-§33, HRAC-REQ-049-056.

## 17. HSCE-001 compatibility / versioning / vocabulary audit

Reused unchanged: proof shape, envelope schema, evidence-ID formula, evidence-store root/layout/exclusive-publish mechanism, evidence lookup semantics, the closed-error-vocabulary *style*, storage trust classification, blind-touch-defense UX precedent (reused as UX pattern only), and the TOCTOU cross-record recheck discipline (HSCE-REQ-069/070/080-083). New, additive only: the request/session state machine, `request_id` as a distinct non-content-addressed identity class, the challenge-context canonicalization/digest scheme, the remote evidence record, and this contract's own closed request-layer error vocabulary. **HSCE-001 does NOT require a version bump** (HRAC-REQ-068): every reused concept is reused unchanged; every new concept is additive alongside, never inside or in conflict with, HSCE-001's existing closed surface. For every new vocabulary item (`operation_type`, `error_type`, state-machine values), this contract requires a closed enum/frozenset from first implementation, explicitly avoiding a repeat of HRWP-REQ-019's open-string mistake. Contract §42/§46-§47, HRAC-REQ-063-064/068-069.

## 18. `protocol_name` Non-Blocking finding — disposition

Carried forward, not repaired here (no production source touched by this phase): `_PROTOCOL_VALUES = frozenset({"FIDO2", "PIV"})` would reject `"WEBAUTHN"`, contradicting HRWP-REQ-019's "no schema widening" claim (independently confirmed by Phase 149O.20L.7O.2N.8). This contract's own signer-resolution reuse (HSCE-REQ-080, unamended) reads `provider_profile`, never `protocol_name` — **HRAC-001 does not depend on that finding being resolved to be internally coherent.** It MUST be resolved before a real WebAuthn-enrolled `HardwareCredentialRecord` can exist at all (a prerequisite for HRWP-001's own registration scope, not this contract's), which in turn is a hard prerequisite before any real remote *assertion* under this contract can occur (§19/§21 below, DAG entry 2). The finding is not allowed to disappear — restated explicitly as a named prerequisite. Contract §44, HRAC-REQ-066.

## 19. Trusted-kernel / adapter boundary, future HMIC impact

Trusted: request/challenge construction, the pending-request state manager, response correlation, the verification-handoff call plus TOCTOU re-resolution, the exclusive-publish consumption mechanism, the remote-evidence-record/envelope builder. Thin/adapter: HTTP transport, the ceremony-delivery page's HTML/JS, QR/deep-link presentation. Every trusted-kernel component named above will become new HMIC-001-scope-bearing source requiring independent verification before activation, once implemented — no HMIC-001 amendment occurs in this contract, and final member count is not pre-derived. Contract §48-§49, HRAC-REQ-070-071.

## 20. Required future security tests / synthetic-interoperability gate

Frozen minimum attack matrix: challenge replay, expired response, wrong credential, wrong signer, wrong repository, wrong operation, wrong origin, wrong RP-ID, bad signature, missing UP, missing UV, two genuinely concurrent valid responses, cross-session/cross-request substitution, server-restart behavior, a cancelled request receiving a late response, malformed response. No first implementation test may require real hardware or a real browser session — a synthetic WebAuthn fixture MUST pass full interoperability (every state transition, every failure category, the full attack matrix) before any real ceremony is attempted; frozen as a hard gate. Contract §50-§51, HRAC-REQ-072-073.

## 21. Implementation prerequisite DAG

(1) independent verification of HRAC-001; (2) the §18 `protocol_name`/HRWP-REQ-019 narrow text repair (hard prerequisite for real enrollment, not for this contract's own coherence); (3) RP-ID/origin/HTTPS infrastructure selection (HRWP-001's own still-open item); (4) server-side request/challenge/state-machine/verifier-handoff implementation; (5) minimal browser WebAuthn client; (6) synthetic interoperability tests (§20 gate); (7) independent verification of (4)-(6); (8) HMIC-001 source-scope expansion; (9) deployment + recertification; (10) first real remote WebAuthn *enrollment* (HRWP-001's own scope, its own phase, a hard prerequisite for step 11); (11) first real remote WebAuthn *assertion* ceremony under HRAC-001, its own phase, not combined with step 10. Steps 2 and 3 have no ordering dependency on each other; both precede step 4 producing a working implementation, though step 4's code MAY be written/unit-tested against synthetic fixtures ahead of either resolving. Contract §52, HRAC-REQ-074.

## 22. Proof of no implementation, no hardware effect, runtime unchanged

No `makeCredential`/`getAssertion` invoked against real or simulated hardware this phase. No PIN requested. No configuration of the currently-attached Security Key C NFC changed. No `HardwareCredentialRecord`/`Principal`/`Signer`/`DeploymentBinding` created. No request-store code, HTTP route, WebAuthn JavaScript, or provider implementation written. No `src/pcae/**` or `scripts/**` file modified this phase — `git diff --stat` for this phase's implementation commit touches only `docs/`, `tests/`, and governance/task-lifecycle files. No HMIC-001 record, certification, or Permission Broker policy changed. `pcae runtime inspect` unchanged from prior phase's baseline (Observed / execution_unavailable).

## 23. Testing

New disposable file `tests/test_phase_149o_20l_7o_2n_9_hrac_001_contract_freeze.py`: asserts the contract document exists, freezes contract identity (`HRAC-001 v1.0`, FROZEN, no-implementation declaration), verifies `HRAC-REQ-###` numbering is sequential 001-076 with no gaps/duplicates, asserts presence of every required orchestration section (state machine, request identity, signer selection, challenge construction, domain separation, client contract, verification handoff, one-time consumption, cancellation, closed error vocabulary, durability, evidence capture, HSCE-001 compatibility mapping, the `protocol_name` finding's carried-forward disposition, trusted-kernel boundary, HMIC impact, synthetic-interoperability gate, and the No-Go section); confirms the frozen closed state set and the frozen domain-separation string; confirms `request_id`'s random-not-content-addressed design is explicit in the text; confirms HRWP-001/HSCE-001 remain unamended (their own identity/version/count strings unchanged); and confirms `hatp_signing_ceremony.py`'s key production entry points and "no CLI implemented" framing are unchanged in source, evidencing no production regression. No test touches real hardware, a protected root, or performs any registry write.

## 24. Regression

No production source (`src/pcae/`, `scripts/`) changed this phase — only new `docs/` and `tests/` files plus governance/lifecycle artifacts. This phase's own new tests pass standalone; no broader Fast Green regression surface is introduced.

## 25. Governance

`pcae health`, `pcae check`, `pcae status coherence`, `pcae doctor task-memory`, `pcae push check`, `pcae runtime inspect` all run per the governing prompt's §55 — results recorded in `.pcae/phase-completion-metadata.json`'s `governance_results`.

## 26. Findings

None Blocking. The `protocol_name`/HRWP-REQ-019 finding (§18) is carried forward explicitly, not concealed, as a named implementation-DAG prerequisite — not a defect in anything this phase touched, since this phase implemented nothing and this contract's own coherence does not depend on that finding's resolution.

## 27. Commits

See `.pcae/phase-completion-metadata.json` `phase_commits` for the exact hash list (this phase's implementation commit plus lifecycle/status/metadata-sync commits).

## 28. Pushed / `origin/main..HEAD`

Not yet pushed as of this report's writing — staged pending push per this repository's governed two-step finalization procedure (`pcae phase complete --stage-pending-report`, then human-confirmed `pcae push`). `origin/main..HEAD` will be 0 after push; not yet re-verified at report-writing time.

## 29. Expected verdict

**REMOTE WEBAUTHN ASSERTION CEREMONY COMPANION CONTRACT FROZEN — ASYNC REQUEST / RESPONSE / EVIDENCE ORCHESTRATION DEFINED.**
HRWP-001 CRYPTOGRAPHIC PROFILE: PRESERVED, UNAMENDED.
HSCE-001 CORE SEMANTICS: PRESERVED, UNAMENDED.
REMOTE SIGNING: CONTRACTUALLY ORCHESTRATABLE.
NO IMPLEMENTATION. NO REAL HARDWARE EFFECT.

## 30. Next phase

Independent verification of HRAC-001 before any implementation. Do not begin RP-ID/TLS infrastructure selection or provider implementation until that verification passes. If the independent verifier uncovers an HSCE-001/HRWP-001 incompatibility, the recommended remedy is a narrow contract repair to whichever contract is at fault, mirroring this repository's existing repair-then-reverify precedent — never a silent reinterpretation of frozen text. Stop after completing 149O.20L.7O.2N.9.
