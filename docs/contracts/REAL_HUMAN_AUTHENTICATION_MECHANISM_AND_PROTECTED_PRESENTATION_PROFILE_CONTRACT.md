# RHAMP-001 v1.0 — Real Human Authentication Mechanism & Protected Presentation Profile Contract

## Contract identity and status

**Contract:** RHAMP-001
**Version:** 1.0
**Status:** FROZEN
**Frozen by:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.29 — N-16-5 Real Human
Authentication Mechanism & Protected Presentation Profile Contract Freeze.
**Planning baseline:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.28 — N-16-5 Real
FIDO2/WebAuthn/CTAP and Protected Human-Approval UI Architecture and Contract
Planning (`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_28_N_16_5_REAL_FIDO2_WEBAUTHN_CTAP_AND_PROTECTED_HUMAN_APPROVAL_UI_ARCHITECTURE_AND_CONTRACT_PLANNING.md`).
**Independent verification:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.31 (of the
`.1R.30` mechanism implementation) and Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.33
(of the `.1R.32` protected-presentation implementation and N-16-5 closure,
including the mandatory real-CTAP2-hardware manual verification).
**Scope:** the concrete profile of the real
`hpac.fido2.uv_presence.v2` human-authentication mechanism and the real
protected approval-presentation mechanism for the first real runtime-invocation
approval — the residual decisions HPAC-001 v2.1 left to "a future
implementation phase" or left silent: the real `mechanism_id` allowlist, the
`verifier_kind` allowlist plus the process-isolated presentation-helper
integrity obligations, the native-CTAP2 relying-party / client-data model, the
attestation policy, the discoverable-credential / attachment / transport
profile, the challenge / proof / presentation TTL bounds, the signature-counter
policy plus a new protected per-credential counter-state artifact, a new
protected per-credential FIDO2-credential sidecar artifact, the first-credential
bootstrap authority, the closed `terminal_reason_code` vocabulary, and the
local-interactive deployment-topology prerequisite.
**Production surface (future — not created by this contract):**
`src/pcae/core/hpac_verifier.py` (`_ELIGIBLE_MECHANISM_IDS`,
`_verify_assertion_material`, `_check_up_uv`, `_authority_class_of`),
`src/pcae/core/human_authenticator.py` /
a new `human_authenticator_fido2.py`,
`src/pcae/core/approval_presentation.py` (`verifier_kind` acceptance),
a new protected presentation-helper module and its administrator-installed
descriptor, `src/pcae/core/human_principal_registry.py` (production writer
path exercised, schema byte-unchanged), and the new protected artifacts under
`HPAC_PROTECTED_ROOT`.
**Related contracts:** HPAC-001 v2.1 (`HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md`
— the parent; RHAMP-001 profiles its extension points and changes none of its
text), RIHAC-001 v2.0 (`RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` — §12
condition 7 consumer, unchanged), RIASC-001 v3.0
(`RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md` — wire shape unchanged),
HPSE-001 v1.1 / HHCE-001 (pattern precedent only, per HPAC-001 §6),
REPRC-001 v1.0 (`RUNTIME_ENFORCEMENT_POSITIVE_RESULT_CONTRACT.md` — the
companion-contract precedent this contract follows exactly),
RDGO-001 v3.1 (`RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md` — Gate 5 / Gate 9
timing, unchanged), PBRD-001 v3.0 (no HPAC coupling; unchanged),
RPAC-001 v1.0 (`RUNTIME_PROVIDER_ADAPTER_CONTRACT.md` — N-16-6 territory;
provider-neutral; unchanged), the HATP family
(`HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md`,
`HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md`,
`HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md` — a **separate trust domain**;
RHAMP-001 reuses `hatp_fido2_provider.py` **code** as a library, never HATP
**state**, per HPAC-REQ-019).

RHAMP-001 is a **companion** contract — the REPRC-001 v1.0 / PBNDE-001 shape.
It introduces **no** HPAC-001 challenge/proof/presentation/lifecycle/consumption
schema change, **no** HPAC-001 version bump, **no** RIHAC-001 / RIASC-001 /
RDGO-001 / PBRD-001 / RPAC-001 change, **no** RDGO-001 state-machine change, no
gate reorder, no first-effect-boundary move, no merge of the
authentication / presence / verification / informed-intent / approval /
PB-permission / Runtime-Enforcement / runtime-capability / execution concerns,
no freshness weakening, and no effect-scope widening. HPAC-001 stays v2.1;
`HPAC-AUTHORITY-CONSUMPTION` stays `/2.1`. The only version movement in the
entire N-16-5 track is **RHAMP-001 v1.0 (initial freeze)**.

This is a contract-freeze document. It creates no real registry, enrolls no
real principal, verifies no real proof, touches no hardware, implements no
`HumanAuthenticator`, implements no presentation helper, produces no
`AuthenticatedHumanPrincipal` of class `PRODUCTION`, and enables
`require_real_assurance` on no production path. Runtime remains
`not_implemented` / `Observed` / `observe` / `unavailable`. The first external
effect remains **ABSENT**.

---

## 0. Normative language

`SHALL`, `SHALL NOT`, `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY` are
normative (RFC 2119, as used throughout this repository's bound contracts).
Every normative sentence carries a unique requirement ID `RHAMP-REQ-###`,
sequential from 001, no gaps, no duplicates. RHAMP-REQ-* is an independent
numbering namespace (HPSE-001 precedent). Unknown, missing, conflicting,
malformed, or unverifiable facts **fail closed**: no proof is minted, no
`AuthenticatedHumanPrincipal` is emitted, no approval authority is created, and
a terminal `terminal_reason_code` (§21) is recorded where a lifecycle event can
be persisted. The absence of a denial is never approval. An ambiguity at any
authority boundary fails closed.

---

## 1. Position under HPAC-001 v2.1 — companion, not amendment

- **RHAMP-REQ-001.** RHAMP-001 profiles HPAC-001 v2.1's existing extension
  points **only**. It SHALL NOT redefine, relax, widen, or reinterpret any
  HPAC-001 requirement, wall, schema, digest rule, assurance level, or trust
  boundary. Where RHAMP-001 and HPAC-001 appear to conflict, HPAC-001 governs
  and the implementing phase STOPS (BLOCKED).
- **RHAMP-REQ-002.** The HPAC-001 extension points RHAMP-001 fills are exactly:
  (a) HPAC-REQ-039's `mechanism_id` — the real allowlist (§4);
  (b) HPAC-REQ-090's `verifier_kind` closed-but-unenumerated identifier — the
  real allowlist plus helper integrity obligations (§5, §28–§30);
  (c) HPAC-REQ-047's RP/challenge-namespace tag realized as a concrete `rp_id`
  and client-data context (§6–§8);
  (d) HPAC-REQ-039/040 silence on attestation — the attestation policy (§19);
  (e) HPAC-REQ-032's minimal interface — the discoverable-credential /
  attachment / transport profile (§9, §51);
  (f) HPAC-REQ-050's explicitly-deferred `expires_at` bound and HPAC-REQ-054
  step 8's "recent relative to a trusted clock" — the TTL numbers (§23–§25);
  (g) HPAC-001's silence on the FIDO2 signature counter — the counter policy
  and a new protected artifact (§20–§22);
  (h) HPAC-REQ-095's non-empty-ID `terminal_reason_code` — the closed
  vocabulary (§21);
  (i) HPAC-REQ-021/022/082/083's local-only model — the local-interactive
  deployment-topology prerequisite (§53–§56).
- **RHAMP-REQ-003.** Every existing normative contract is byte-unchanged by the
  N-16-5 track through `.1R.29`. The implementing phase's finalization SHALL
  independently prove `git diff --name-only <entry> HEAD -- docs/contracts`
  names exactly the RHAMP-001 file and `git diff <entry> HEAD -- src/pcae` is
  empty for `.1R.29`.
- **RHAMP-REQ-004.** RHAMP-001 v1.0 makes NON_REAL authentication and NON_REAL
  presentation objects **no more upgradeable** than HPAC-001 v2.1 already makes
  them; §41 restates the structural non-upgradeability as this contract's own
  binding rule.

## 2. `rhamp_schema_version`

- **RHAMP-REQ-005.** Every artifact this contract newly defines — the
  per-credential FIDO2-credential sidecar (§17) and the per-credential
  counter-state record (§21) — SHALL carry a `rhamp_schema_version` field whose
  value under this contract is exactly the literal string `RHAMP-001/1.0`.
- **RHAMP-REQ-006.** `rhamp_schema_version` is a closed-field-set marker, not an
  authority input. A consumer that does not recognise the schema version SHALL
  treat the artifact as untrusted and fail closed. A future RHAMP-001 MINOR or
  MAJOR SHALL change this literal.
- **RHAMP-REQ-007.** Canonicalization for every RHAMP-001 artifact is
  HPAC-REQ-089's rule verbatim: UTF-8 compact JSON, recursively ASCII-sorted
  object keys, NFC strings, arrays retain order, SHA-256 over the exact bytes,
  the self-digest field excluded from its own input.

## 3. Native CTAP2 / FIDO2 / WebAuthn terminology freeze (mandatory gate)

- **RHAMP-REQ-008.** RHAMP-001 v1.0 defines a **native CTAP2** mechanism. The
  three terms are frozen distinct and SHALL NOT be conflated in the
  implementation, its tests, its audit records, or its human-visible strings:
  - **FIDO2** — the umbrella specification family (CTAP + WebAuthn). The
    mechanism *conforms to* FIDO2.
  - **CTAP2** — the client-to-authenticator transport/command protocol
    (`authenticatorMakeCredential`, `authenticatorGetAssertion`) over USB-HID
    and NFC. This is **the protocol RHAMP-001 uses**, driven directly via
    `fido2.ctap2` over `fido2.hid.CtapHidDevice`.
  - **WebAuthn** — the W3C browser-side JavaScript client API
    (`navigator.credentials.create` / `.get`). RHAMP-001 v1.0 **does not use
    WebAuthn**: there is no browser, no web page, no DOM, and no WebAuthn
    client.
- **RHAMP-REQ-009.** RHAMP-001 v1.0 adopts the WebAuthn/CTAP2 **wire shapes**
  (`authenticatorData`, `clientDataHash`, COSE public keys, the assertion
  signature form `sign(authenticatorData ‖ SHA-256(clientDataHash-input))`)
  because the pinned `fido2` library implements them and they give byte-exact
  challenge binding — exactly as `hatp_fido2_provider.py` already does. Adopting
  the wire shapes SHALL NOT be described or documented as "running a WebAuthn
  ceremony".
- **RHAMP-REQ-010.** The implementation SHALL NOT claim, in code comments,
  audit output, or human-visible text, that a browser, a web origin, TLS, a
  secure context, or a WebAuthn client enforces any property. §8 governs the
  precise security claims that MAY be made.

## 4. Real `mechanism_id` allowlist

- **RHAMP-REQ-011.** The closed set of real-authority-eligible `mechanism_id`
  values under RHAMP-001 v1.0 is exactly:

  ```
  hpac.fido2.uv_presence.v2
  ```

  — one entry, no wildcard, no `fido2.*` prefix match, no `fnmatch`, no
  "contains-at-least". `_ELIGIBLE_MECHANISM_IDS` in `hpac_verifier.py` SHALL be
  widened by **exactly** `{"hpac.fido2.uv_presence.v2"}` in the `.1R.30`
  implementation phase, with an explicit `.1R.30` / RHAMP-001 §4 citation, and
  SHALL remain a `frozenset` literal.
- **RHAMP-REQ-012.** `mechanism_id` is **verifier-owned**. It is resolved from
  the trusted `CredentialRecord.mechanism_id` of the credential the assertion
  was produced under (HPAC-REQ-054 step 2/3), never from a caller-supplied,
  proof-declared, or adapter-declared field. A proof whose declared
  `mechanism_id` is `hpac.fido2.uv_presence.v2` but whose resolved
  `CredentialRecord` names a different mechanism SHALL be rejected
  (`mechanism_unknown`).
- **RHAMP-REQ-013.** The deterministic test mechanism id
  `hpac.deterministic.test-only.v1` SHALL remain permanently outside the real
  allowlist. RHAMP-001 v1.0 adds no test mechanism to any real allowlist and
  defines no path by which a `hpac.deterministic.*`-prefixed id becomes real.

## 5. `verifier_kind` allowlist

- **RHAMP-REQ-014.** The closed set of real-authority-eligible
  `verifier_kind` values for the protected approval-presentation mechanism
  (HPAC-REQ-090) under RHAMP-001 v1.0 is exactly:

  ```
  pcae-protected-local-presentation/1.0
  ```

  — one entry, exact string equality, no wildcard, no prefix match. The
  deterministic NON_REAL kind `deterministic-test-fixture` SHALL remain
  accepted **only** for `FIXTURE_NON_REAL` resolution and SHALL NEVER yield a
  `PRODUCTION` `HPACAuthorityClass`.
- **RHAMP-REQ-015.** A `verifier_kind` string is **not** presentation
  assurance. `pcae-protected-local-presentation/1.0` confers real presentation
  assurance only in conjunction with all of: a protected, administrator-installed
  `TrustedApprovalPresentationMechanism` descriptor of `status == active`
  carrying that kind and a `PRODUCTION`-class `verifier_configuration_digest`
  (HPAC-REQ-090); a verified `mechanism_attestation` over the closed
  `HPAC-PRESENTATION-ATTESTATION/2.0` object (HPAC-REQ-092); a helper whose
  integrity is established per §30; and byte/digest re-render equality
  (HPAC-REQ-092, §32). A caller-provided descriptor, a repository-provided
  descriptor, or an agent-launched process SHALL NEVER mint or attest this kind.
- **RHAMP-REQ-016.** Only HPAC-REQ-080's protected administrator may create or
  revoke the descriptor for `pcae-protected-local-presentation/1.0`. Repository,
  task, agent, cwd, environment, stdin, or caller state SHALL NOT install,
  select, redirect, or weaken it.

## 6. Relying-party identifier semantics

- **RHAMP-REQ-017.** The CTAP2 relying-party identifier is frozen:

  ```
  rp_id = "hpac.pcae.local"
  ```

  It is a **compiled-in PCAE constant**, distinct from HATP's
  `hatp.pcae.local` (HPAC-REQ-047/084 domain separation). It is supplied to
  `authenticatorMakeCredential` and `authenticatorGetAssertion` as the `rp.id` /
  `rpId`.
- **RHAMP-REQ-018.** `authenticatorData.rpIdHash` returned by the authenticator
  SHALL equal `SHA-256(UTF-8("hpac.pcae.local"))`. Assertion verification
  (§37) SHALL recompute this hash from the constant and reject any mismatch
  (`rp_id_hash_mismatch`).
- **RHAMP-REQ-019.** `rp_id` SHALL NOT be derived from, or varied by,
  repository, working directory, environment, agent identity, hostname,
  deployment target, task, or any caller input (HPAC-REQ-079/080). Because it
  is a constant string and not a hostname, it does not vary between the macOS
  development host and the Linux deployment host — there is no per-host RP
  registration and no cross-trust-domain problem.
- **RHAMP-REQ-020.** `rp_id` is **not a web origin** and carries **no browser
  origin claim**. It is an internal namespacing constant that scopes
  RHAMP-001 credentials exactly as a WebAuthn `rpId` scopes ordinary WebAuthn
  credentials — a domain-separation label, not a network identity. A future
  profile that introduces a browser or a web origin requires a new governed
  HPAC-001 version (HPAC-REQ-067), not a RHAMP-001 MINOR.
- **RHAMP-REQ-021.** Every `CredentialRecord` enrolled under RHAMP-001 v1.0 is
  permanently bound to `rp_id == "hpac.pcae.local"`. A future contract
  evolution that changes `rp_id` SHALL define an explicit credential-migration
  or re-enrollment path; silent rebinding is prohibited.

## 7. PCAE native-CTAP2 client-data model

- **RHAMP-REQ-022.** RHAMP-001 v1.0 does **not** use a WebAuthn browser
  `clientDataJSON` produced by a user agent, and it does **not** treat any
  string as a browser security origin. Instead it defines a **PCAE-owned
  canonical native-CTAP2 client-data context**, produced by the trusted
  challenge-construction component (never by the authenticator, the adapter,
  the requesting agent, or any caller).
- **RHAMP-REQ-023.** The canonical client-data context is a closed object,
  schema identity `RHAMP-CLIENT-CONTEXT/1.0`, with exactly these fields:

  | Field | Meaning |
  |---|---|
  | `client_context_schema` | const `RHAMP-CLIENT-CONTEXT/1.0` |
  | `ceremony_kind` | const `runtime-invocation-approval` (enrollment uses `credential-enrollment`) |
  | `context_identifier` | const `pcae-hpac://hpac.pcae.local/runtime-invocation-approval.v2` — a PCAE-internal **domain-separation constant**, classified explicitly as **not** a browser security origin (§8) |
  | `domain_separator` | const `pcae.hpac.runtime-invocation-approval.v2` (HPAC-REQ-047) |
  | `challenge_digest` | the exact `Challenge.challenge_digest` (HPAC-REQ-049) |
  | `approval_subject_digest` | the exact `CanonicalRuntimeApprovalSubject` digest (HPAC-REQ-089) |
  | `trusted_presentation_digest` | the exact `TrustedApprovalPresentationEvidence` digest (HPAC-REQ-091) |
  | `principal_id` | the resolved `principal_id` |
  | `credential_id` | the resolved opaque `hpc-<hex>` `credential_id` |
  | `invocation_id` | the governed invocation id |
  | `attempt_id` | the governed attempt id |
  | `nonce` | the CSPRNG challenge nonce (HPAC-REQ-050) |
  | `issued_at` | trusted-clock RFC 3339 UTC |
  | `expires_at` | `issued_at + challenge TTL` (§23) |
  | `mechanism_id` | const `hpac.fido2.uv_presence.v2` |

- **RHAMP-REQ-024.** `client_data_bytes` is the HPAC-REQ-089 canonical
  serialization of that object; `client_data_hash = SHA-256(client_data_bytes)`.
  The CTAP2 `getAssertion` / `makeCredential` call SHALL pass this
  `client_data_hash` as its `clientDataHash` input. The signed assertion
  therefore binds `authenticatorData ‖ client_data_hash`, which transitively
  binds every field above.
- **RHAMP-REQ-025.** Assertion verification (§37) SHALL reconstruct the exact
  canonical client-data object from trusted state, recompute `client_data_hash`,
  and reject any mismatch against the value the assertion signed
  (`client_data_hash_mismatch`). It SHALL also reject if `ceremony_kind` or
  `context_identifier` is not the frozen constant for the operation
  (`client_data_context_mismatch`).
- **RHAMP-REQ-026.** No field of the canonical client-data object is
  caller-selectable. The requesting agent MAY request that a ceremony begin; it
  SHALL NOT supply, influence, or observe the nonce, the digests, or the
  timestamps.

## 8. No false origin-enforcement / phishing-resistance claim

- **RHAMP-REQ-027.** RHAMP-001 v1.0 SHALL state, in the mechanism module and in
  audit documentation, exactly this security posture and no stronger:

  > The native CTAP2 `rpIdHash` binding (§6) plus the PCAE-controlled canonical
  > `client_data_hash` (§7) cryptographically bind the assertion to PCAE's
  > exact ceremony context — this exact challenge, this exact presentation,
  > this exact subject, this exact principal and credential. The initial
  > native profile does **not** rely on, and does **not** claim, browser or
  > WebAuthn web-origin enforcement, TLS, or secure-context guarantees,
  > because no browser or WebAuthn client is in the loop.

- **RHAMP-REQ-028.** `context_identifier`
  (`pcae-hpac://hpac.pcae.local/runtime-invocation-approval.v2`) is classified
  as a **PCAE-internal context / domain-separation constant**. It SHALL NOT be
  documented, logged, or reasoned about as a browser security origin, and no
  code SHALL treat it as one (e.g. no same-origin comparison semantics, no
  navigation checks).
- **RHAMP-REQ-029.** The anti-substitution property RHAMP-001 v1.0 does provide
  is: the protected presentation helper (§28–§30) is the sole party that
  renders the canonical facts, observes the election, and drives the CTAP2
  call, and the requesting agent cannot launch, replace, observe, or feed it
  (HPAC-REQ-090 `agent_substitution_resistant`). This is a **local process /
  helper-integrity** property, not a network-origin property.

## 9. Authenticator profile

- **RHAMP-REQ-030.** The supported authenticator profile for RHAMP-001 v1.0 is
  exactly: a **roaming / cross-platform** FIDO2 authenticator; spoken to over
  **CTAP2**; holding a **non-discoverable** credential; authenticated via an
  **`allowList`-bound** `getAssertion` (the CLI resolves `principal_id →
  credential_id → raw credential id` from trusted state and passes
  `allow_list=[{type: "public-key", id: <raw credential id>}]`); over
  **USB-HID** or **NFC**; with **UP required** and **UV required** (§10).
- **RHAMP-REQ-031.** Explicitly **unsupported** under RHAMP-001 v1.0 (a future
  contract evolution is required to add any of them, and each requires its own
  threat analysis): BLE transport; hybrid / caBLE / cross-device flows; synced
  / multi-device passkeys; browser platform authenticators; the OS platform
  authenticator (Secure Enclave / TPM / Windows Hello) as the RHAMP mechanism;
  discoverable / resident credentials; and any usernameless / principal-discovery
  flow. A platform authenticator MAY be added later as an *additional*
  `HumanAuthenticator` under HPAC-REQ-068 without lowering the UP/UV floor — but
  not under a RHAMP-001 MINOR.
- **RHAMP-REQ-032.** An assertion or credential that does not match this profile
  (e.g. a discoverable-credential assertion, a platform-authenticator assertion,
  a BLE transport) SHALL be rejected. The mechanism SHALL request
  non-discoverable credentials at enrollment (`rk = discouraged`/absent) and
  SHALL NOT fall back to a resident-credential or usernameless flow on failure.

## 10. UP / UV policy

- **RHAMP-REQ-033.** `UP = REQUIRED` and `UV = REQUIRED`, both mandatory, an
  immutable contract minimum (HPAC-REQ-042/060). Neither the repository nor the
  protected administrator may lower this floor.
- **RHAMP-REQ-034.** Assertion verification SHALL check both
  `authenticatorData.FLAG.UP` and `authenticatorData.FLAG.UV` are set. A
  missing UP flag → reject (`user_presence_missing`). A missing UV flag →
  reject (`user_verification_missing`). A UP-only assertion SHALL NOT be
  recorded as anything more than credential-presence evidence and SHALL NOT
  yield an `AuthenticatedHumanPrincipal` (HPAC-REQ-042). **This is stronger
  than `hatp_fido2_provider.py`, which checks UP only** (finding N-16-5-3):
  RHAMP-001's mechanism SHALL add the UV check in HPAC-001's own verifier path.
- **RHAMP-REQ-035.** UV is satisfied **inside the authenticator** (PIN or
  biometric). PCAE never sees, requests, or stores the PIN or biometric — only
  the `FLAG.UV` bit (§18). An authenticator that cannot perform UV → the
  mechanism status is `unavailable`, authentication fails closed, and there is
  **no downgrade and no fallback mechanism** (HPAC-REQ-066).
- **RHAMP-REQ-036.** UV is **not** approval intent. `FLAG.UV` proves the
  authenticator locally verified the user; the explicit election (§34) is the
  separate observed fact that proves the human chose to approve *this*
  operation. Neither implies the other.

## 11. Authentication is not approval

- **RHAMP-REQ-037.** A successful CTAP2 assertion is **not** approval; an
  `AuthenticatedHumanPrincipal` is **not** approval authority; a hardware touch
  is **not** approval (HPAC-REQ-001 walls, restated as RHAMP-001's own binding
  rule). Approval additionally requires the protected presentation of the exact
  canonical facts and the human's explicit, observed election (§12, §34), and
  the downstream RIHAC-001 §16 / Gate 5 / Gate 9 chain.
- **RHAMP-REQ-038.** `hpac_verifier` resolves the presentation evidence
  (HPAC-REQ-054 step 5) and the assertion signature (step 6) as **independent**
  steps that both must pass. A valid assertion over an unrelated challenge, or a
  valid assertion with no resolved `HPAC-REQ-091` evidence (a blind touch),
  SHALL NOT satisfy `PRINCIPAL_VERIFIED_INTENT` (`election_missing`).

## 12. Ceremony model and order

- **RHAMP-REQ-039.** RHAMP-001 v1.0 freezes the **single-assertion,
  step-up-at-approval-time** ceremony (planning §19 model B/D): one fresh CTAP2
  assertion whose canonical client-data (§7) contains the exact presentation
  digest and subject digest, bound to exactly one approval. There is **no
  authenticated login session** and **no session cache** (HPAC-REQ-075/076).
- **RHAMP-REQ-040.** The frozen stage order for a runtime-invocation approval
  is exactly:

  1. the trusted coordinator reserves `approval_id` (`ria-<hex>`) and resolves
     `principal_id → credential_id → raw credential id` from trusted state;
  2. the protected presentation helper renders the closed `human_visible_facts`
     (HPAC-REQ-091) deterministically via `renderer_profile` and hashes the
     exact displayed bytes → `human_visible_representation_digest`;
     `canonical_subject.approval_preview_digest` SHALL equal it;
  3. the human performs the explicit election (`action = approve`) on the
     protected surface → the `election` object;
  4. **only after** an `approve` election, the helper constructs the
     `Challenge` (HPAC-REQ-049) and the canonical client-data (§7) and drives
     the CTAP2 `getAssertion` over `client_data_hash`, `allow_list`, and
     `rp_id = "hpac.pcae.local"`; the human touches the key and satisfies UV;
  5. `hpac_verifier.verify_human_authentication` runs the unchanged
     HPAC-REQ-054 steps 1–10 with the real signature branch (§37);
  6. on success, the trusted proof writer mints the canonical `proof.json` and
     lifecycle events; RIHAC-001 §16 / Gate 5 / Gate 9 consume downstream.

- **RHAMP-REQ-041.** On a **reject** election (§34), the ceremony SHALL NOT
  drive a CTAP2 assertion, SHALL NOT mint an approval proof, and SHALL record a
  terminal `approval_rejected_by_human` outcome. (An audit-only lifecycle event
  MAY be persisted; no authority is created.)
- **RHAMP-REQ-042.** The `election.occurred_at >= presented_at` ordering check
  (HPAC-REQ-091) plus the challenge `expires_at` (§23) plus the one-shot
  lifecycle are the frozen defences against a presentation/action race. An
  `election` earlier than `presented_at`, or after `expires_at`, → reject
  (`election_ordering_invalid`).

## 13. Credential registration profile

- **RHAMP-REQ-043.** The frozen registration flow is:

  ```
  protected-admin ceremony launch (HPAC-REQ-024 — never an ordinary pcae CLI,
      hook, task action, agent tool, stdin confirmation, env toggle, or
      unattended workflow; a same-UID agent invocation is denied before any
      registry mutation)
    → protected presentation of the exact registry identity + credential being
      enrolled (HPAC-REQ-023/028)
    → explicit protected-admin election over that presentation
    → CTAP2 authenticatorMakeCredential (rp.id = "hpac.pcae.local", ES256,
      UP + UV, non-discoverable, no attestation preference / "none")
    → PCAE verifies the makeCredential response, extracts
      (raw_credential_id: bytes, COSE public key)
    → HumanPrincipalRegistryStore.enroll_credential(
        protected_admin_capability,
        credential_id = fresh opaque "hpc-<hex>"  (NOT the raw CTAP2 id),
        principal_id = <existing active PrincipalRecord>,
        mechanism_id = "hpac.fido2.uv_presence.v2",
        public_key = hex(cbor(COSE_Key)),
        assurance_capabilities = ("UP", "UV", "usb"|"nfc"),
        ... )   [atomic, read-back verified, writer-provenance recorded]
    → create the per-credential FIDO2-credential sidecar (§17) and the
      per-credential counter-state record (§21), both atomic + read-back
      verified
    → durable enrollment provenance / audit entry (HPAC-REQ-028/069, §61)
    → credential eligible for future authentication
  ```

- **RHAMP-REQ-044.** `enroll_credential` SHALL require an existing, `active`
  `PrincipalRecord` for the supplied `principal_id` (HPAC-REQ-027); enrolling
  against a missing or revoked principal fails closed
  (`enrollment_principal_ineligible`).
- **RHAMP-REQ-045.** Enrolling a `credential_id`, or a raw CTAP2 credential id,
  that already exists in the registry (under any principal) → reject
  (`enrollment_duplicate_credential`). "First registrant wins" is prohibited.
- **RHAMP-REQ-046.** Credential rotation is two operations —
  `enroll_credential` then `revoke_credential` — never an in-place overwrite
  (HPAC-REQ-031).

## 14. First-credential bootstrap authority

- **RHAMP-REQ-047.** The authority that may enroll the **first** credential for
  a human principal is frozen as HPAC-REQ-023's **externally established
  deployment-owner protected administration principal** — an OS/equivalent
  protected administration principal that owns the deployment-scoped protected
  root outside every repository and is **unavailable to ordinary same-user
  agent execution** (HPAC-REQ-022). This is the trust anchor; it terminates
  bootstrap without circular PCAE self-authorization.
- **RHAMP-REQ-048.** The first-credential bootstrap ceremony SHALL be a
  protected local administrative ceremony that requires all of: local
  interactive mode (§53); an already-canonical `PrincipalRecord` selected by
  the protected admin; explicit protected-administrative confirmation; a
  protected presentation of the exact principal + credential being enrolled;
  authenticator UP + UV; verification of the `makeCredential` response; and an
  atomic create of the first `CredentialRecord` + sidecar + counter-state +
  durable provenance entry.
- **RHAMP-REQ-049.** The bootstrap authority SHALL NOT be, in whole or in part:
  an arbitrary `pcae` CLI caller; an arbitrary OS username; the first process
  or user to run enrollment; an agent identity; a repository-supplied identity;
  a Git identity; a session id; an environment variable; or a stdin
  confirmation. A ceremony that cannot establish the HPAC-REQ-023 anchor →
  reject (`bootstrap_authority_unproven`); the implementing phase STOPS
  (BLOCKED) if the existing governance model provides no such anchor.
- **RHAMP-REQ-050.** Recovery from total principal loss = **repeat the
  bootstrap ceremony** (HPAC-REQ-065). There is no principal-recovery shortcut
  and **no fallback to a NON_REAL mechanism** (§60).

## 15. Bootstrap / enrollment evidence

- **RHAMP-REQ-051.** The durable evidence that principal `P` was intentionally
  enrolled with credential `C` SHALL record exactly: the bootstrap/enrollment
  operation id; `principal_id`; `credential_id` (opaque); raw-credential-id
  digest (not the raw bytes in the audit record); `mechanism_id`; the
  enrollment `challenge`/nonce identifier (not the raw challenge —
  HPAC-REQ-069); the registrar / protected-administrative authority provenance
  reference; the trusted-clock timestamp; the registry-generation transition
  (`credential_generation` before/after); and the enrollment result digest.
- **RHAMP-REQ-052.** This enrollment evidence is **audit evidence, not reusable
  authority**. It authenticates no future approval; every approval requires a
  fresh §12 ceremony.

## 16. Multi-credential policy

- **RHAMP-REQ-053.** One principal MAY have multiple `active` credentials
  (HPAC-REQ-030). Each `credential_id` and each raw CTAP2 credential id is
  unique across the registry; a credential id SHALL NOT map to more than one
  principal (`credential_principal_mismatch` on any attempt to use one under a
  different principal).
- **RHAMP-REQ-054.** Backup / replacement credentials are ordinary additional
  `enroll_credential` operations. Authentication resolves the `allowList` from
  **all `active` credentials of the principal**; the authenticator selects
  which of its enrolled credentials to assert. A revoked credential is excluded
  from the `allowList`.

## 17. Credential record schema and FIDO2-credential sidecar

- **RHAMP-REQ-055.** `CredentialRecord` (HPAC-REQ-013) is **byte-unchanged** by
  RHAMP-001. The RHAMP-001 profile of its existing fields:

  | `CredentialRecord` field | RHAMP-001 v1.0 value |
  |---|---|
  | `credential_id` | fresh opaque `hpc-<hex>` (never the raw CTAP2 id) |
  | `principal_id` | the owning principal |
  | `mechanism_id` | const `hpac.fido2.uv_presence.v2` |
  | `public_key` | `hex(cbor(COSE_Key))` — exactly the bytes `CoseKey.parse(cbor.decode(...))` consumes |
  | `assurance_capabilities` | a tuple containing exactly `"UP"`, `"UV"`, and one transport marker `"usb"` or `"nfc"` |
  | `status` / `revoked_at` | `{active, revoked}` monotonic (HPAC-REQ-062) |
  | `enrollment_provenance_ref` | the §15 enrollment-evidence reference |
  | `enrolled_at` | trusted-clock timestamp |

- **RHAMP-REQ-056.** The raw CTAP2 credential id, the bound `rp_id`, the
  transport set, and an optional advisory AAGUID are stored in a **new
  protected per-credential sidecar artifact**, not in the registry (which is
  create/append-only for revocation only, HPAC-REQ-015). Canonical path:

  ```
  <HPAC_PROTECTED_ROOT>/credentials/<credential_id>/fido2-credential.json
  ```

  Closed schema, identity `RHAMP-FIDO2-CREDENTIAL/1.0`, fields exactly:
  `rhamp_schema_version` (const `RHAMP-001/1.0`), `artifact_schema_version`
  (const `RHAMP-FIDO2-CREDENTIAL/1.0`), `record_digest` (self-excluding
  SHA-256), `credential_id`, `principal_id`, `rp_id` (const `hpac.pcae.local`),
  `raw_credential_id` (base64url of the CTAP2 credential id bytes),
  `cose_public_key` (hex of `cbor(COSE_Key)` — the same bytes as
  `CredentialRecord.public_key`, duplicated here so the sidecar is
  self-contained for `allowList` construction and re-verification),
  `transports` (ordered subset of `["usb", "nfc"]`), `aaguid` (advisory; hex or
  `null`; §19), `mechanism_id` (const `hpac.fido2.uv_presence.v2`),
  `created_at`, `writer_provenance_ref`, and `status` (mirrors the
  `CredentialRecord.status`, resolved read-only from the registry — the
  registry is authoritative for status).
- **RHAMP-REQ-057.** The sidecar is immutable, create-only, atomically written,
  read-back verified, and resolved only by `(credential_id, record_digest)`.
  Resolution rejects symlinks, traversal, owner/ACL mismatch, non-canonical
  bytes, digest mismatch, a `credential_id` absent from the registry, or a
  `principal_id`/`mechanism_id` that disagrees with the registry
  (`protected_root_invalid`). It stores **no private key, PIN, or biometric
  material** (§18).
- **RHAMP-REQ-058.** `allowList` construction and assertion verification read
  the sidecar for `raw_credential_id` and `cose_public_key`; both SHALL be
  cross-checked against the registry `CredentialRecord` (`public_key` equality)
  before use.

## 18. Private-key / biometric / PIN boundary

- **RHAMP-REQ-059.** PCAE SHALL store **no** credential private key. The
  authenticator's non-exportable private key never leaves the device; CTAP2
  never exposes it. This is structural: no field for a private key exists on
  `CredentialRecord` or any RHAMP-001 artifact.
- **RHAMP-REQ-060.** PCAE SHALL NOT request, receive, store, or log any
  biometric template or authenticator PIN. Only the derived `FLAG.UV` bit is
  observed. No RHAMP-001 artifact has a field for a PIN or biometric.

## 19. Attestation policy

- **RHAMP-REQ-061.** For RHAMP-001 v1.0: attestation is **not required for
  authority**; a `none` / `self` / `packed` statement is accepted **without
  validation**; `makeCredential` is requested with no attestation preference or
  `attestation = "none"`. This mirrors `hatp_fido2_provider.py`'s
  `attestation_valid = None` non-blocking posture.
- **RHAMP-REQ-062.** **Enterprise attestation is prohibited** (it would leak a
  device serial — a privacy regression for no threat-model gain).
- **RHAMP-REQ-063.** The FIDO Metadata Service (MDS) is **not used**. There is
  **no** AAGUID allowlist and **no** authenticator model / device-uniqueness
  claim. If an AAGUID is retained in the sidecar (§17) it is **advisory / audit
  metadata only** and SHALL NOT gate authority.
- **RHAMP-REQ-064.** A future profile MAY add attestation under HPAC-REQ-068
  without lowering the UP/UV floor — but not under a RHAMP-001 MINOR (§68).

## 20. Signature-counter policy

- **RHAMP-REQ-065.** RHAMP-001 v1.0 SHALL NOT assert "the signature counter
  must always monotonically increment". CTAP2 authenticators legitimately
  report `signCount == 0` permanently (modern / passkey authenticators) or
  omit meaningful counter semantics.
- **RHAMP-REQ-066.** The frozen accept/block rules, evaluated against the last
  accepted meaningful value in the §21 counter-state record:

  | Authenticator report | Rule |
  |---|---|
  | `signCount` absent, or `== 0` | **accept**; record `0`; treat as "non-counter authenticator" |
  | `signCount > last_accepted_meaningful` (both meaningful, i.e. non-zero) | **accept**; update `last_accepted_meaningful` |
  | `signCount == last_accepted_meaningful`, both non-zero | **reject** — `signature_counter_regression` (a non-incrementing meaningful counter is treated as a regression signal for this profile); record and surface for protected-admin review |
  | `signCount < last_accepted_meaningful`, new value non-zero | **reject** — `signature_counter_regression`; record and surface for protected-admin review |
  | `last_accepted_meaningful == 0` (non-counter authenticator) and a later report is non-zero | **accept**; adopt the non-zero value as the new `last_accepted_meaningful` (a one-time transition) |

- **RHAMP-REQ-067.** A counter anomaly is a **security signal, not proof of
  cloning**. A `signature_counter_regression` SHALL fail the current
  authentication closed, emit an audit record, and mark the credential for
  protected-admin review. It SHALL NOT auto-revoke the credential — revocation
  is a protected-admin decision.

## 21. Counter-state artifact

- **RHAMP-REQ-068.** A **new protected per-credential counter-state artifact**
  is frozen. Canonical path:

  ```
  <HPAC_PROTECTED_ROOT>/credentials/<credential_id>/counter-state.json
  ```

  Closed schema, identity `RHAMP-COUNTER-STATE/1.0`, fields exactly:
  `rhamp_schema_version` (const `RHAMP-001/1.0`), `artifact_schema_version`
  (const `RHAMP-COUNTER-STATE/1.0`), `record_digest` (self-excluding SHA-256),
  `credential_id`, `last_accepted_meaningful` (non-negative integer;
  `0` means "no meaningful counter observed"), `last_observed_raw`
  (non-negative integer — the most recent value the authenticator reported,
  accepted or not), `generation` (non-negative integer, incremented on every
  accepted update), `updated_at` (trusted-clock timestamp),
  `writer_provenance_ref`, and `review_flag` (bool — set `true` when a
  regression was observed; cleared only by a protected-admin operation).
- **RHAMP-REQ-069.** The counter-state artifact is created at enrollment (§13)
  with `last_accepted_meaningful = 0`, `last_observed_raw = 0`, `generation =
  0`, `review_flag = false`. It is updated by **atomic replace** (create a new
  canonical file, `fsync`, atomic rename, read-back verify). Corruption, a
  digest mismatch, an owner/ACL failure, or an absent record for an `active`
  credential → **fail closed** (`protected_root_invalid`) — a missing or
  corrupt counter-state record SHALL NOT be silently treated as "counter 0".
- **RHAMP-REQ-070.** The counter-state artifact is **not** a `CredentialRecord`
  schema change and is **not** an authority-generation input: it uses no wall
  clock in any generation marker, it is read at verify time and updated after
  the proof mints (§22), and `credential_generation` (HPAC-REQ-098a) does
  **not** fold it. It is anti-clone / audit evidence only.

## 22. Counter-state update linearization

- **RHAMP-REQ-071.** The frozen ordering for a successful authentication is:

  1. `hpac_verifier` runs HPAC-REQ-054 steps 1–9, **including** the §20 counter
     check read against the current counter-state record (a regression here
     rejects **before** any proof is minted);
  2. step 10 atomically creates the `PROOF_VERIFIED_AND_BOUND` lifecycle event
     and emits the ephemeral `AuthenticatedHumanPrincipal`;
  3. **immediately after** step 10 succeeds, and before the
     `AuthenticatedHumanPrincipal` is returned to any consumer, the trusted
     verifier atomically updates the counter-state record
     (`last_accepted_meaningful`, `last_observed_raw`, `generation`,
     `updated_at`).

- **RHAMP-REQ-072.** If the process crashes **after** step 10 but **before**
  the counter-state update, the outstanding proof remains bound to exactly one
  approval and is single-use (HPAC-REQ-071); the same assertion cannot be
  replayed for a second approval (the challenge/nonce is one-use, §27), so the
  un-updated counter does not create replay authority. On the next
  authentication with the same credential, the counter check runs against the
  stale `last_accepted_meaningful`; an honest authenticator's `signCount` will
  be `>=` the stale value (accept) — a genuine clone would still regress below
  the last value the authenticator itself issued. The residual window is
  bounded and does not admit a replay of the crashed ceremony's own assertion.
- **RHAMP-REQ-073.** If the implementation's protected store cannot provide
  atomic replace with read-back verification for the counter-state artifact,
  the implementing phase records it as an implementation prerequisite and
  STOPS (BLOCKED) rather than shipping a non-atomic counter update.

## 23. Challenge TTL

- **RHAMP-REQ-074.** The maximum lifetime of a registration challenge, an
  authentication challenge, and an approval challenge is **≤ 120 seconds**
  (`RHAMP_CHALLENGE_MAX_TTL_SECONDS = 120`). A deployment MAY configure a
  stricter bound; neither the repository nor the protected administrator may
  configure a looser one.
- **RHAMP-REQ-075.** The challenge object carries `issued_at` and `expires_at =
  issued_at + TTL`, both from the **trusted invocation coordinator's clock**
  (never a caller-supplied time). A challenge whose `expires_at` is at or
  before the current trusted time at any verification point → reject
  (`challenge_expired`). Challenge expiry is **not** revocation and **not**
  authority-generation currentness — those are separate and additionally
  required (§43–§44).

## 24. Proof age

- **RHAMP-REQ-076.** `max_proof_age_seconds` is **≤ 300 seconds**
  (`RHAMP_MAX_PROOF_AGE_SECONDS = 300`). A real proof whose `authenticated_at`
  is older than 300 seconds relative to the trusted clock at a consumption
  point → **ineligible even if cryptographically valid**
  (`proof_age_exceeded`). Authority-generation currentness (§44) remains
  separately required.

## 25. Presentation / approval expiry

- **RHAMP-REQ-077.** The presentation's `expires_at`
  (`human_visible_facts.expires_at`, the canonical-subject expiry) SHALL equal
  the RIASC-001 approval `expires_at` for the same `approval_id`. A stale
  displayed presentation cannot approve a refreshed or different challenge: the
  `approval_preview_digest == human_visible_representation_digest` equality
  (HPAC-REQ-092) plus the shared `approval_id` and `approval_subject_digest`
  bind the exact presentation to the exact approval.
- **RHAMP-REQ-078.** A presentation whose `expires_at` has passed at election
  time or at verification time → reject (`challenge_expired` if the bound
  challenge has also expired; otherwise `presentation_unresolved` for a
  presentation the resolver marks `EXPIRED`).

## 26. Challenge entropy

- **RHAMP-REQ-079.** Production challenge nonces SHALL be
  cryptographically-secure random bytes (≥ 256 bits) generated by the trusted
  challenge-construction component (HPAC-REQ-050), never by the authenticator,
  the adapter, or any caller. No predictable, sequential, timestamp-only, or
  reusable challenge value is permitted (HPAC-REQ-051). NON_REAL test fixtures
  MAY remain deterministic, and SHALL remain structurally NON_REAL (§41).

## 27. Replay semantics

- **RHAMP-REQ-080.** Frozen single-use rules:
  - a registration challenge is one-use;
  - an authentication / approval challenge and its nonce are one-use — a
    durable, checked-at-verification-time record of consumed
    challenges/nonces prevents reuse (HPAC-REQ-045); a replayed nonce →
    reject (`challenge_replayed`);
  - an approval proof is bound to exactly one authority lifecycle and is
    consumed exactly once, atomically, by Gate 9's single `consumption.json`
    (HPAC-REQ-071/098); a post-consumption replay → reject
    (`consumption_replay`);
  - Gate 9 consumption remains the final single-use authority consumption and
    is unchanged by RHAMP-001.
- **RHAMP-REQ-081.** Replay at any layer fails closed. A retry requires a fresh
  invocation / attempt / presentation / challenge / proof / approval.

## 28. Presentation helper trust model

- **RHAMP-REQ-082.** Process isolation alone is **insufficient**. A real
  `pcae-protected-local-presentation/1.0` presentation requires **all** of:
  - a **PCAE-owned, fixed helper implementation** (not agent-authored, not
    repository-provided) with a declared implementation identity and version;
  - an administrator-installed `TrustedApprovalPresentationMechanism`
    descriptor (HPAC-REQ-090) of `status == active` binding that
    `verifier_kind`, a fixed `renderer_profile`, and a `PRODUCTION`-class
    `verifier_configuration_digest`;
  - helper **integrity evidence** established per §30 before the helper is
    trusted to render or attest;
  - the canonical presentation payload delivered to the helper **only** over a
    PCAE-owned channel the requesting agent cannot write to (§57);
  - the helper's inability to substitute, mutate, reorder, or suppress any of
    the closed `human_visible_facts` (§31–§32);
  - the requesting agent's inability to launch, replace, observe, screen-scrape,
    or feed the helper (HPAC-REQ-090 `agent_substitution_resistant`).
- **RHAMP-REQ-083.** A caller SHALL NOT nominate an arbitrary executable, path,
  interpreter, or helper. The helper is resolved **only** from the
  administrator-installed protected descriptor / installation record.

## 29. Presentation helper process model

- **RHAMP-REQ-084.** The helper is a **local process only**: no agent-owned
  helper, no repository-provided executable, no arbitrary shell, no remote
  presentation endpoint, no network listener, no bound socket, no port.
- **RHAMP-REQ-085.** The helper is short-lived: it starts for **one** approval
  challenge, and terminates on success, reject, cancel, timeout, or error.
  Where practical it serves exactly one approval challenge per process
  lifecycle. It holds no persistent daemon state.
- **RHAMP-REQ-086.** The helper renders on a surface the requesting agent
  cannot substitute or scrape — a controlled local pane or a dedicated file
  descriptor not shared with the agent process. Ordinary terminal stdout/stdin
  of the agent process is **structurally ineligible** (HPAC-REQ-090).

## 30. Helper integrity evidence

- **RHAMP-REQ-087.** RHAMP-001 v1.0 freezes the **intended** helper-integrity
  trust evidence as, in order of preference and subject to the implementing
  phase's confirmation against the then-current PCAE architecture:
  1. a **pinned executable digest** recorded in a protected installation
     record under `HPAC_PROTECTED_ROOT`, verified immediately before launch;
  2. plus the administrator-installed **descriptor digest**
     (`descriptor_digest`, HPAC-REQ-090) and its
     `verifier_configuration_digest`;
  3. plus, where the then-current architecture provides it, a
     supply-chain-admitted package identity or a signed descriptor.
  Integrity SHALL NOT depend on the helper's path or filename alone.
- **RHAMP-REQ-088.** If, at implementation time, none of (1)–(3) can be
  established as **provably canonical / integrity-bound** without a broader
  architecture change, the implementing phase STOPS (BLOCKED) and reports the
  exact gap — it SHALL NOT ship a helper trusted only by location.
- **RHAMP-REQ-089.** Helper-integrity failure at launch or at attestation time
  → reject (`helper_integrity_unverified`); no presentation evidence is
  resolved and no approval proof is minted.
- **RHAMP-REQ-090.** The protected-UI helper's admission is **separate** from
  the N-16-6 runtime effect-adapter supply-chain admission (§65). A helper
  installation record SHALL NOT be reinterpreted as adapter admission, and vice
  versa. Human credential identity SHALL NOT influence adapter admission.

## 31. Canonical presentation payload

- **RHAMP-REQ-091.** The canonical presentation payload is **exactly**
  HPAC-REQ-091's closed `human_visible_facts` (13 fields): `repository_identity`
  + `repository_display`; `task_id` + `task_display`; `runtime_target_id` +
  `runtime_target_display`; `operation_effect_scope_display` (the **complete**
  canonical `approval_scope` — requested capability, local transport, effect
  class, filesystem/process references, the no-network fact, the one-dispatch
  limit); `prompt_hash` + `prompt_instruction_display`; `invocation_id` +
  `invocation_display`; `expires_at`; `one_shot_notice` (const `true`).
  RHAMP-001 adds **no field** to this set and removes none.
- **RHAMP-REQ-092.** The helper SHALL render **all 13** fields. No
  security-critical field may be omitted from the display or from the digest.
  `operation_effect_scope_display` SHALL render the complete `approval_scope`
  with no default-collapsed / truncated / "click to expand" treatment of any
  mandatory field. No caller-supplied label, hidden field, or non-attested
  authority text is permitted (HPAC-REQ-092).

## 32. Display / digest equivalence

- **RHAMP-REQ-093.** The frozen relationship:

  ```
  closed human_visible_facts  --renderer_profile (deterministic)-->  displayed bytes
  displayed bytes             --SHA-256-->                            human_visible_representation_digest
  ```

  Display bytes are UTF-8, NFC strings, LF line endings. The
  `renderer_profile` is a versioned deterministic identifier; the same facts
  under the same `renderer_profile` version SHALL always produce byte-identical
  output. A resolver re-renders the same facts under the exact descriptor
  version and requires byte/digest equality (HPAC-REQ-092); inequality →
  reject (`presentation_digest_mismatch`).
- **RHAMP-REQ-094.** Security-critical fields SHALL NOT differ in meaning
  between the digested payload and the displayed bytes: the digest covers
  exactly the bytes displayed. `canonical_subject.approval_preview_digest`
  SHALL equal `human_visible_representation_digest` (HPAC-REQ-092); inequality
  → reject (`subject_digest_mismatch` or `presentation_digest_mismatch` per the
  failing comparison).

## 33. Untrusted-content escaping

- **RHAMP-REQ-095.** Every repository-, task-, path-, prompt-, and
  scope-derived string in `human_visible_facts` is **untrusted presentation
  data**. Before rendering, the helper SHALL: escape or strip C0/C1 control
  characters; neutralize ANSI / terminal escape sequences; escape native-UI
  markup (HTML/RTF/etc.) for the rendering surface in use; prevent
  line-truncation and right-to-left-override ambiguity; and clearly delimit
  untrusted strings from trusted labels.
- **RHAMP-REQ-096.** No repository-controlled text SHALL be able to alter,
  spoof, or suppress a trusted label, the Approve/Reject controls, the PCAE
  identity banner, the expiry notice, or the one-shot notice. An injected
  escape sequence or markup fragment SHALL be neutralized and SHALL NOT change
  `human_visible_representation_digest` relative to the neutralized rendering
  (the digest is over the neutralized displayed bytes).

## 34. Approve / Reject action

- **RHAMP-REQ-097.** The helper SHALL present an **explicit Approve** control
  and an **explicit Reject** control. There is **no implicit approval**, **no
  timeout-as-approval**, and **no authenticator-touch-alone-as-approval**.
- **RHAMP-REQ-098.** The authenticator touch occurs **only after** a distinct,
  explicit Approve action (§12 step 4) and the ceremony binds that choice: the
  `election` object records `action = approve` with `event_id` (`hpevt-<hex>`)
  and `occurred_at`, and the subsequent CTAP2 client-data (§7) carries the
  presentation digest of the exact payload the human approved.
- **RHAMP-REQ-099.** A Reject election records `action`-not-`approve` handling
  as `approval_rejected_by_human` (§41 category `approval_declined`), drives no
  CTAP2 assertion, and mints no proof.

## 35. No accidental approval

- **RHAMP-REQ-100.** Frozen UX safeguards for the helper:
  - **no default affirmative control** — Approve SHALL NOT be the focused /
    default action such that a single accidental keypress approves;
  - **no ambiguous Enter shortcut** that submits Approve;
  - a **clear PCAE identity** indicator on the surface;
  - **clear consequential / irreversible wording** where the effect class
    warrants it (rendered from `operation_effect_scope_display`);
  - an **expired presentation is visibly invalid** and its Approve control is
    disabled;
  - an explicit **approval-confirmation state** is shown after a completed
    approval.

## 36. Client-data / approval binding

- **RHAMP-REQ-101.** The canonical client-data object (§7) SHALL bind exactly:
  `ceremony_kind = runtime-invocation-approval`; the domain-separation
  `context_identifier` and `domain_separator`; the challenge `nonce`; the
  `principal_id` and `credential_id`; the `trusted_presentation_digest`; the
  `approval_subject_digest`; the `invocation_id` and `attempt_id`; `issued_at`
  and `expires_at`; and `mechanism_id` / profile version. Redundant raw
  payload where a canonical digest already suffices SHALL be avoided — the
  digests are the binding.

## 37. Assertion verification requirements

- **RHAMP-REQ-102.** The `.1R.30` real signature branch in
  `hpac_verifier._verify_assertion_material` SHALL, using the pinned library's
  primitives and **no custom cryptography**, verify **all** of:
  1. credential lookup — resolve `credential_id` and the sidecar; principal
     ownership (`credential.principal_id == resolved principal_id`, else
     `credential_principal_mismatch`);
  2. `authenticatorData.rpIdHash == SHA-256("hpac.pcae.local")` (§6), else
     `rp_id_hash_mismatch`;
  3. the assertion signature over `authenticatorData ‖ client_data_hash` using
     `CoseKey.parse(cbor.decode(credential.public_key))` (§17), else
     `signature_invalid`;
  4. `client_data_hash` equals the hash recomputed from the reconstructed
     canonical client-data object (§7/§25), else `client_data_hash_mismatch`;
     `ceremony_kind` / `context_identifier` are the frozen constants, else
     `client_data_context_mismatch`;
  5. `FLAG.UP` set (else `user_presence_missing`) **and** `FLAG.UV` set (else
     `user_verification_missing`);
  6. the §20 signature-counter policy against the §21 counter-state record
     (else `signature_counter_regression`);
  7. `credential.status == active` (else `credential_not_active`);
     `principal.status == active` (else `principal_not_active`);
  8. the challenge is active and unconsumed (else `challenge_replayed` /
     `challenge_expired`); `challenge_digest` recomputes and matches (else
     `challenge_digest_mismatch`);
  9. `mechanism_id` resolves and is at or above `PRINCIPAL_VERIFIED_INTENT`
     (else `mechanism_unknown` / `mechanism_below_assurance`);
  10. the HPAC-REQ-054 step 5 presentation resolution and step 9 lifecycle /
      consumption checks pass (else `presentation_unresolved` /
      `presentation_digest_mismatch` / `presentation_attestation_invalid` /
      `election_missing` / `election_ordering_invalid` / `lifecycle_fork` /
      `lifecycle_cross_binding` / `consumption_replay`);
  11. proof age ≤ 300 s (§24, else `proof_age_exceeded`); authority-generation
      currentness (§44, else `authority_generation_stale`).
- **RHAMP-REQ-103.** No later check runs as a shortcut when an earlier check
  fails (HPAC-REQ-055). The real branch SHALL be reachable **only** when
  `_authority_class_of(...)` is `PRODUCTION` for every resolved record and the
  resolved `mechanism_id` is in the §4 real allowlist; a `FIXTURE_NON_REAL`
  credential SHALL never reach real signature verification (finding N-16-5-2).

## 38. HATP FIDO2 provider reuse boundary

- **RHAMP-REQ-104.** The implementing phase MAY reuse `hatp_fido2_provider.py`
  primitives as a **shared library only** (HPAC-REQ-019/§32), never as a live
  HATP trust dependency and never against HATP registry state. Classification:

  | `hatp_fido2_provider` capability | RHAMP-001 reuse |
  |---|---|
  | CTAP2 device enumeration (`CtapHidDevice.list_devices`) | **reusable** as a transport primitive |
  | `authenticatorMakeCredential` / `authenticatorGetAssertion` invocation over `fido2.ctap2` | **reusable** as protocol primitives |
  | `CoseKey` parse + `verify` | **reusable** as the signature primitive |
  | `CollectedClientData` construction | **reusable** as a wire-shape helper only — RHAMP-001 supplies its own canonical `client_data_hash` (§7), not a WebAuthn `clientDataJSON`; the HATP `_HATP_RP_ID` / `_HATP_ORIGIN` constants are **not** reused |
  | `allow_list` construction | **reusable** as a pattern |
  | cancellation / timeout handling | **reusable** as a pattern |
  | UP-only presence check (`is_user_present()` with no UV check) | **NOT reusable as-is** — RHAMP-001 SHALL add its own `FLAG.UV` enforcement (§10, finding N-16-5-3) |
  | `_HATP_RP_ID` / `_HATP_ORIGIN` / HATP registry / HATP `SignerRecord` semantics | **NOT reusable** — separate trust domain (HPAC-REQ-084) |

- **RHAMP-REQ-105.** Future implementation SHOULD extract the genuinely shared
  CTAP2 transport / COSE-verify primitives into a shared library module only if
  the extraction is needed; blind code copying is not frozen and is
  discouraged.

## 39. FIDO2 dependency policy

- **RHAMP-REQ-106.** The accepted dependencies are the **already-declared**
  `fido2>=1.1,<2` and `cryptography>=42,<45` (currently the `hatp-hardware`
  extra in `pyproject.toml`). RHAMP-001 adds **no new dependency**.
- **RHAMP-REQ-107.** If the `.1R.30` implementation promotes `fido2` /
  `cryptography` from the `hatp-hardware` extra to a base dependency, that is a
  pinned, provenance-reviewed, non-vendored change carrying its own guard note;
  the version pins SHALL NOT be loosened. No custom signature-algorithm
  implementation and no opaque binary vendoring is permitted;
  `CoseKey.verify` is the library's.
- **RHAMP-REQ-108.** No dependency installation, upgrade, or lockfile change
  occurs in the `.1R.29` contract-freeze phase.

## 40. Real verifier / mechanism-registry evolution

- **RHAMP-REQ-109.** The only mechanism-registry change RHAMP-001 v1.0
  authorizes is: `hpac_verifier._ELIGIBLE_MECHANISM_IDS` gains **exactly**
  `{"hpac.fido2.uv_presence.v2"}`, as a `frozenset` literal, with a `.1R.30`
  citation. No wildcard, no `fido2.*`, no generic prefix. Test mechanisms stay
  isolated by their `hpac.deterministic.*` prefix. Duplicate registration is
  impossible (a `frozenset`). The registry identity is the compiled module
  constant.
- **RHAMP-REQ-110.** `approval_presentation.py`'s `verifier_kind` acceptance
  gains **exactly** `pcae-protected-local-presentation/1.0` as a second
  accepted kind (`.1R.32`), gated on a `PRODUCTION`-class descriptor;
  `deterministic-test-fixture` remains accepted for `FIXTURE_NON_REAL` only.

## 41. NON_REAL non-upgradeability

- **RHAMP-REQ-111.** A NON_REAL authentication proof or NON_REAL presentation
  evidence object SHALL NEVER be relabeled, converted, wrapped, or "upgraded"
  into REAL authority under RHAMP-001 v1.0. Restated as binding rule:

  ```
  NON_REAL object  +  REAL-looking mechanism_id  +  copied REAL-looking fields
      !=  REAL authority
  ```

- **RHAMP-REQ-112.** REAL eligibility requires **all** of, structurally: a
  trusted REAL mechanism implementation (§4); the verifier-owned registry
  identity (`_ELIGIBLE_MECHANISM_IDS`, §40); a canonical REAL `CredentialRecord`
  + sidecar resolved from the `PRODUCTION` protected root; successful
  cryptographic verification (§37); real protected-presentation assurance
  (§5, §28–§32); and lifecycle / currentness (§43–§44). Enforced by the
  existing structural walls — `SIMULATION_ONLY: Final[bool]`, the
  `_ELIGIBLE_MECHANISM_IDS` frozenset, `HPACAuthorityClass` propagation,
  `_authority_class_of`, `is_verifier_authenticated_principal`'s identity
  registry, and `AuthenticatedHumanPrincipal.__reduce__` raising — none of
  which RHAMP-001 weakens.
- **RHAMP-REQ-113.** A deterministic authenticator output with `mechanism_id`
  forged to `hpac.fido2.uv_presence.v2` SHALL still be rejected: the resolved
  `CredentialRecord.mechanism_id` for a fixture-root credential will not match a
  real credential, and `_authority_class_of` returns `FIXTURE_NON_REAL` for a
  fixture-root credential (`mechanism_unknown` or a class rejection).

## 42. Principal / credential ownership

- **RHAMP-REQ-114.** The canonical `CredentialRecord` for a `credential_id`
  determines its `principal_id`. A caller SHALL NOT assert `principal_id = X`
  and thereby override registry ownership; verification resolves the principal
  from the credential, not from caller input (`credential_principal_mismatch`
  on any disagreement).
- **RHAMP-REQ-115.** A raw CTAP2 credential id or an opaque `credential_id`
  present under one principal SHALL NOT be enrolled or resolved under another
  (`enrollment_duplicate_credential` at enrollment;
  `credential_principal_mismatch` at verification).

## 43. Revocation / deactivation

- **RHAMP-REQ-116.** A `revoked` credential SHALL NOT authenticate
  (`credential_not_active`). A `revoked` or disabled principal SHALL NOT
  authenticate (`principal_not_active`) and SHALL invalidate its outstanding
  challenges, verified/bound proofs, unmaterialized and unconsumed approvals,
  and derived PB authority projections (HPAC-REQ-063/064) — an in-flight
  authentication cannot complete after revocation even within the challenge
  TTL.
- **RHAMP-REQ-117.** Only an approval/proof **already atomically consumed** by
  Gate 9's `consumption.json` remains historical audit evidence — never
  reusable authority.

## 44. Credential generation / currentness

- **RHAMP-REQ-118.** RHAMP-001 v1.0 **reuses the existing** authority-generation
  mechanism (HPAC-REQ-098a): credential lifecycle participates through the
  existing `credential_generation` marker (a whole-record canonical digest of
  the current `CredentialRecord`, which moves on `revoke_credential`,
  replacement, or any mechanism/key/binding change). **No parallel freshness
  system is introduced.**
- **RHAMP-REQ-119.** A revoked or replaced credential moves
  `credential_generation`; a future Gate 10 re-reads current generation state
  and compares against the durable `authority_generation_binding` snapshot
  (RDGO-001 v3.1 §10/§11). An outstanding unconsumed proof whose
  `credential_generation` has moved is stale (`authority_generation_stale`).
- **RHAMP-REQ-120.** If the existing authority-generation contract cannot
  accommodate credential-lifecycle currentness without a version evolution, the
  implementing phase STOPS (BLOCKED) and adjudicates — it SHALL NOT add a new
  freshness artifact. (Analysis at freeze time: `credential_generation` already
  folds the whole `CredentialRecord`, so no evolution is anticipated.)

## 45. Real authentication proof

- **RHAMP-REQ-121.** RHAMP-001 v1.0 introduces **no new authentication-proof
  artifact**. The existing mechanism-neutral `HumanAuthenticationProof`
  (`HPAC-PROOF/2.0`, HPAC-REQ-052) already carries `mechanism_id`, `assertion`
  (base64url), `up` (const true), `uv` (const true), `challenge_digest`,
  `approval_subject_digest`, and `trusted_presentation_ref`. RHAMP-001's real
  branch populates these with real CTAP2 values; the schema is byte-unchanged.
- **RHAMP-REQ-122.** The REAL-only commitments the proof carries are: a real
  `mechanism_id` from the §4 allowlist; an `assertion` that verifies under
  §37; `up == true` and `uv == true` as verified `FLAG` bits; and a
  `trusted_presentation_ref` resolving to `pcae-protected-local-presentation/1.0`
  evidence. No redundant authority artifact is created.

## 46. Real approval proof

- **RHAMP-REQ-123.** The frozen approval-proof semantics:

  ```
  cryptographically verified CTAP2 authentication (UP + UV, §37)
    +  resolved protected presentation digest (§5, §32)
    +  explicit observed approve election (§34)
    +  exact challenge / subject / client-data binding (§7, §23, §27)
    +  lifecycle + generation currentness (§43, §44)
    ->  a trusted real approval proof of HPACAuthorityClass.PRODUCTION,
        assurance PRINCIPAL_VERIFIED_INTENT, for exactly one governed
        runtime-invocation approval
  ```

- **RHAMP-REQ-124.** Still: `approval proof != PB permission != Runtime
  Enforcement approval != runtime capability != execution`. The real approval
  proof is the evidence RIHAC-001 v2.0 §16 consumes; every downstream gate
  independently re-validates it (HPAC-REQ-055, RDGO-001 v3.1).

## 47. Proof writer

- **RHAMP-REQ-125.** Only the trusted verifier / proof writer under the
  protected root (`is_verifier_authenticated_principal` identity boundary,
  `HPACStoreAuthority.verify_record`) may mint the canonical `proof.json`, the
  hash-chained lifecycle events, the §17 sidecar, the §21 counter-state record,
  and (via Gate 9) `consumption.json`. All writes are atomic, create-only (or
  atomic-replace for the counter-state record, §21), and read-back verified.
- **RHAMP-REQ-126.** A structurally valid file is **not** trusted authority. An
  arbitrary JSON file, a copied lifecycle file, a caller-constructed object, or
  a plausible reference is non-authority until the complete protected chain
  resolves and verifies (HPAC-REQ-096). RHAMP-001 reuses the existing proof
  writer where compatible and adds no second constructor of an authority
  artifact.

## 48. Raw-artifact retention and privacy

- **RHAMP-REQ-127.** Data-minimization decisions, frozen:

  | Item | Retained? |
  |---|---|
  | opaque `credential_id`, `principal_id` | yes (registry) |
  | COSE public key | yes (registry `public_key`; duplicated in the sidecar) |
  | raw CTAP2 credential id | yes — sidecar only; needed for `allowList` |
  | bound `rp_id`, transports | yes — sidecar; advisory |
  | AAGUID | optional advisory metadata only; MAY be `null`; never authority-gating |
  | verified UP / UV facts | yes — as audit booleans in the lifecycle/audit record |
  | `client_data_hash`, `challenge_digest`, `presentation_digest` | yes — digests, in the proof / lifecycle |
  | raw `authenticatorData`, raw signature, raw client-data bytes | **only** the base64url `assertion` blob the existing `HPAC-PROOF/2.0` schema already carries; no *additional* raw-blob field is created |
  | authenticator PIN, biometric template, private key | **never** (§18) |
  | device serial / model fingerprint | **never** (§19) |

- **RHAMP-REQ-128.** Every writer operation and every proof verification
  (success or failure) emits exactly one audit record with the HPAC-REQ-069
  field set plus the RHAMP-001 `terminal_reason_code` where terminal. No PIN,
  private key, raw biometric, or raw device state is recorded.

## 49. `terminal_reason_code` vocabulary

- **RHAMP-REQ-129.** The closed `terminal_reason_code` vocabulary for the real
  mechanism and the protected presentation is exactly the **41** values in the
  §49.1 table. Every terminal failure of enrollment, bootstrap, authentication,
  presentation, election, or consumption SHALL map **deterministically to
  exactly one** of them. Free-form authority-decision reason strings are
  prohibited. `terminal_reason_code` is `null` for non-terminal lifecycle
  states (HPAC-REQ-095).
- **RHAMP-REQ-130.** **Discrepancy disclosure.** The `.1R.28` planning
  artifact's §12 item 10 and its summary state a "25-code" vocabulary, while
  its §18 enumerated block actually lists **27** tokens and omits
  enrollment/bootstrap, helper-integrity, explicit-human-rejection,
  cancellation, and timeout codes. RHAMP-001 v1.0 **re-derives** the closed set
  from every rejection point across the real ceremony (enrollment writer,
  bootstrap anchor, `hpac_verifier` HPAC-REQ-054 steps 1–10, the §7 client-data
  checks, the §20 counter policy, the presentation resolver / attestation,
  helper integrity, the election observer, ceremony cancel/timeout/supersession,
  the lifecycle chain, Gate-9 consumption, and protected-root I/O) and arrives
  at **41** codes. The "25" and "27" figures are superseded by this contract.

### 49.1 Closed `terminal_reason_code` table

| # | `terminal_reason_code` | Stage | Trigger | Human-visible category | Retryable? | Audit significance | Authority result |
|---:|---|---|---|---|---|---|---|
| 1 | `bootstrap_authority_unproven` | bootstrap | HPAC-REQ-023 external anchor not established | `enrollment_error` | after admin remediation | high — trust-anchor gap | none |
| 2 | `enrollment_not_protected_admin` | enrollment | mutation attempted outside the protected-admin context (HPAC-REQ-024) | `enrollment_error` | no (as attempted) | high — same-UID-agent attempt | none |
| 3 | `enrollment_ceremony_evidence_invalid` | enrollment | UV-required human act / makeCredential evidence fails verification | `enrollment_error` | yes (retry ceremony) | medium | none |
| 4 | `enrollment_duplicate_credential` | enrollment | `credential_id` or raw credential id already registered | `enrollment_error` | no | low | none |
| 5 | `enrollment_principal_ineligible` | enrollment | target `PrincipalRecord` missing or not `active` | `enrollment_error` | after principal fix | low | none |
| 6 | `principal_not_found` | verify step 1 | `principal_id` absent from registry | `not_authenticated` | no | medium | none |
| 7 | `principal_not_active` | verify step 1 / anytime | principal `revoked` or disabled (incl. mid-flight) | `not_authenticated` | no | high | none |
| 8 | `credential_not_found` | verify step 2 | `credential_id` absent | `not_authenticated` | no | medium | none |
| 9 | `credential_not_active` | verify step 2 / anytime | credential `revoked` (incl. mid-flight) | `not_authenticated` | no | high | none |
| 10 | `credential_principal_mismatch` | verify step 2 | credential not bound to the resolved principal | `not_authenticated` | no | high — ownership violation | none |
| 11 | `mechanism_unknown` | verify step 3 | resolved `mechanism_id` not in the real allowlist | `not_authenticated` | no | medium | none |
| 12 | `mechanism_below_assurance` | verify step 3 | mechanism below `PRINCIPAL_VERIFIED_INTENT` | `not_authenticated` | no | medium | none |
| 13 | `rp_id_hash_mismatch` | verify step (RP) | `authenticatorData.rpIdHash != SHA-256("hpac.pcae.local")` | `not_authenticated` | no | high — wrong RP / cross-domain | none |
| 14 | `client_data_context_mismatch` | verify step (client-data) | `ceremony_kind` / `context_identifier` not the frozen constant | `not_authenticated` | no | high | none |
| 15 | `client_data_hash_mismatch` | verify step (client-data) | signed `client_data_hash` != recomputed canonical hash | `not_authenticated` | no | high — binding failure | none |
| 16 | `challenge_digest_mismatch` | verify step 4 | recomputed `challenge_digest` != signed value | `not_authenticated` | no | high | none |
| 17 | `challenge_expired` | verify step 8 / election | challenge (or bound presentation) past `expires_at` | `not_authenticated` | yes (fresh ceremony) | low | none |
| 18 | `challenge_replayed` | verify step 8 | nonce/challenge already consumed | `not_authenticated` | no | high — replay | none |
| 19 | `subject_digest_mismatch` | verify step 5 | canonical subject digest != approval subject/scope/expiry | `presentation_integrity_error` | no | high | none |
| 20 | `presentation_unresolved` | verify step 5 | `trusted_presentation_ref` fails canonical resolution / `EXPIRED` / `INVALIDATED` | `presentation_integrity_error` | yes (fresh ceremony) | medium | none |
| 21 | `presentation_digest_mismatch` | verify step 5 / §32 | re-rendered bytes != `human_visible_representation_digest`, or `approval_preview_digest` inequality | `presentation_integrity_error` | no | high — display/digest divergence | none |
| 22 | `presentation_attestation_invalid` | verify step 5 | `mechanism_attestation` over `HPAC-PRESENTATION-ATTESTATION/2.0` fails | `presentation_integrity_error` | no | high | none |
| 23 | `helper_integrity_unverified` | presentation | helper pinned-digest / descriptor / installation-record integrity check fails (§30) | `presentation_integrity_error` | after admin remediation | high — helper trust gap | none |
| 24 | `helper_response_untrusted` | presentation | helper response schema / provenance / digest binding invalid (§58) | `presentation_integrity_error` | yes (fresh ceremony) | medium | none |
| 25 | `election_missing` | verify step 5 | valid assertion but no resolved explicit election (blind touch) | `presentation_integrity_error` | yes (fresh ceremony) | high — blind touch | none |
| 26 | `election_ordering_invalid` | verify step 5 | `election.occurred_at` before `presented_at` or after `expires_at` | `presentation_integrity_error` | yes | medium | none |
| 27 | `approval_rejected_by_human` | election | human chose Reject | `approval_declined` | yes (new invocation) | low — expected outcome | none |
| 28 | `ceremony_cancelled` | ceremony | helper closed / authenticator cancelled by the human | `approval_declined` | yes | low | none |
| 29 | `ceremony_timed_out` | ceremony | authenticator or challenge timeout with no election/assertion | `approval_declined` | yes | low | none |
| 30 | `ceremony_superseded` | ceremony | a newer challenge/helper lifecycle for the same invocation invalidated this one (restart/concurrency/stale helper) | `approval_declined` | yes | medium | none |
| 31 | `signature_invalid` | verify step 6 | COSE signature verification fails | `not_authenticated` | no | high | none |
| 32 | `user_presence_missing` | verify step 7 | `FLAG.UP` not set | `not_authenticated` | yes (touch) | medium | none |
| 33 | `user_verification_missing` | verify step 7 | `FLAG.UV` not set (UP-only assertion) | `not_authenticated` | yes (UV) | high — floor violation | none |
| 34 | `signature_counter_regression` | verify step (counter) | §20 non-zero counter regression / non-increment | `not_authenticated` | no | high — possible clone | none; credential flagged for admin review |
| 35 | `proof_age_exceeded` | consumption | proof older than 300 s (§24) | `authority_stale` | yes (fresh ceremony) | low | none |
| 36 | `authority_generation_stale` | verify step 9 / Gate 5 / Gate 10 | `credential_generation` / other generation marker moved (§44) | `authority_stale` | yes (fresh ceremony) | medium | none |
| 37 | `lifecycle_fork` | verify step 9 | proof lifecycle chain fork / gap / duplicate sequence | `presentation_integrity_error` | no | high | none |
| 38 | `lifecycle_cross_binding` | verify step 9 | lifecycle event bound to a different approval/proof/challenge/subject/attempt | `presentation_integrity_error` | no | high | none |
| 39 | `consumption_replay` | Gate 9 | `consumption.json` already present for this proof | `authority_stale` | no | high — replay | none |
| 40 | `protected_root_invalid` | any protected I/O | protected root / sidecar / counter-state ownership, ACL, symlink, traversal, canonical-bytes, or digest failure | `internal_error` | after admin remediation | high — protected-store integrity | none |
| 41 | `internal_verification_error` | any | an unexpected fail-closed error in the verification path | `internal_error` | maybe | high — investigate | none |

## 50. Terminal-reason semantics

- **RHAMP-REQ-131.** Four terminal outcomes yield **no approval authority** but
  carry distinct audit semantics and SHALL NOT be conflated:
  - **`not_authenticated`** — a cryptographic / credential / presence /
    verification failure;
  - **`presentation_integrity_error`** — the displayed / attested / elected
    facts did not bind to the assertion;
  - **`approval_declined`** — the human explicitly rejected, cancelled, or let
    the ceremony time out (an expected, non-alarming outcome);
  - **`authority_stale`** — the evidence was valid but is no longer current;
  - **`internal_error`** — a fail-closed infrastructure error.
  A human rejection (`approval_rejected_by_human`) is never reported as an
  authentication failure, and an authentication failure is never reported as a
  human rejection.

## 51. Transport policy

- **RHAMP-REQ-132.** Supported transports under RHAMP-001 v1.0: **USB-HID** and
  **NFC**, over the same CTAP2 path.
- **RHAMP-REQ-133.** Not supported under RHAMP-001 v1.0 (future contract
  evolution required for each): **BLE**, **hybrid / caBLE / cross-device**,
  **remote phone / passkey transports**, and **platform authenticators**. A
  transport marker in a `CredentialRecord.assurance_capabilities` /
  sidecar `transports` outside `{usb, nfc}` → the credential is ineligible.

## 52. Device-identity / attestation claims

- **RHAMP-REQ-134.** RHAMP-001 v1.0 SHALL state: **credential validity does not
  imply a unique physical device identity.** There is no MDS trust, no
  authenticator-model trust claim, and no AAGUID-based security classification.
  A future policy that adds any device claim requires a new governed contract
  version.

## 53. Local interactive control-plane requirement

- **RHAMP-REQ-135.** RHAMP-001 v1.0 REAL approval eligibility **requires a
  local interactive control-plane host** capable of, locally and in an
  interactive session: launching the trusted presentation helper; accessing the
  supported roaming CTAP2 authenticator (USB-HID / NFC); collecting the
  explicit human election; and executing the CTAP2 ceremony. A headless-only
  host is **ineligible** for RHAMP-001 v1.0 REAL approval.
- **RHAMP-REQ-136.** This prerequisite is derivable from HPAC-REQ-021/022/082/083
  (deployment/user-scoped, local-only, offline, OS-neutral roaming key) and is
  **not** a BLOCKED condition — it is a recorded deployment prerequisite.

## 54. Dell / Mac deployment topology consequence

- **RHAMP-REQ-137.** Consequence, stated plainly: if the deployment host (e.g.
  a headless Dell Ubuntu box) has no interactive session and no attached CTAP2
  key, **RHAMP-001 v1.0 REAL approval cannot run on that host directly.** The
  human physically carries the USB CTAP2 key to whichever **local interactive
  control-plane host** owns the authority for a given invocation and performs
  the ceremony there. Because `rp_id` is a constant string (§6), it is
  identical on the macOS development host and the Linux deployment host — there
  is no per-host RP registration and no cross-trust-domain problem.
- **RHAMP-REQ-138.** RHAMP-001 v1.0 SHALL NOT add a remote Mac→Dell (or any
  controller→deployment) approval transport. The deployment host and the
  authority-UI host SHALL NOT be silently equated. The initial supported
  real-authority execution topology is whichever **local interactive
  control-plane host** satisfies §53.

## 55. Remote approval deferred

- **RHAMP-REQ-139.** Explicitly **out of scope for RHAMP-001 v1.0** and
  deferred to a separate, separately-authorized architecture: remote approval;
  controller-to-deployment challenge transport; any networked approval relay;
  any headless approval service. That future work MAY reuse the patterns in
  `HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md` /
  `HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md` (which exist precisely because
  remote assertion is a distinct capability HATP governs separately), but it is
  **not** smuggled into N-16-5.
- **RHAMP-REQ-140.** **No network authority transport is authorized by this
  contract.**

## 56. No browser / no WebAuthn profile

- **RHAMP-REQ-141.** RHAMP-001 v1.0 does **not** define, require, or permit: a
  browser WebAuthn ceremony; a web origin; a TLS requirement; a secure-context
  requirement; a localhost / loopback HTTP service; an ephemeral web port; a
  CSRF / cookie / session model; or a web UI. The stale `.1R.28` "web option"
  ambiguity is resolved: there is no web path in RHAMP-001 v1.0.
- **RHAMP-REQ-142.** Any future profile that introduces a browser or loopback
  path requires a **new governed HPAC-001 version** (HPAC-REQ-067) with a full
  CSRF / origin / secure-context / session freeze — explicitly **not** a
  RHAMP-001 MINOR.

## 57. Presentation-helper IPC

- **RHAMP-REQ-143.** The local helper invocation is conceptually frozen as: an
  authenticated / provenance-bound local invocation of the
  administrator-installed helper; the canonical presentation payload transmitted
  **without shell interpretation** (no argv string concatenation of untrusted
  facts, no shell); a one-shot request/response; the helper's response bound to
  the challenge id, the presentation digest, and the decision; and any
  unexpected or unbound helper response rejected (`helper_response_untrusted`).
  RHAMP-001 v1.0 freezes the requirements, not the transport implementation.

## 58. Helper response

- **RHAMP-REQ-144.** The helper response is conceptually a closed object with:
  a schema/version; the `challenge_id` / `approval_id`; the
  `presentation_digest`; the `decision` (`APPROVE` / `REJECT`); the
  `renderer_profile` / `verifier_kind`; a helper integrity / provenance
  binding; a trusted-clock timestamp; and a self-excluding response digest.
- **RHAMP-REQ-145.** Response structure alone is **not** trust. The response is
  trusted only when its helper-integrity binding verifies (§30), its
  `presentation_digest` matches the payload PCAE sent, and its `challenge_id` /
  `approval_id` match the active ceremony. A mismatch →
  `helper_response_untrusted`.

## 59. Cancel / timeout / concurrency / restart

- **RHAMP-REQ-146.** Helper close/cancel, authenticator cancel, authenticator
  timeout, and challenge timeout each yield **no approval proof and no
  authority**, with the distinct terminal codes `ceremony_cancelled`
  (close/cancel), `ceremony_timed_out` (timeout), or `challenge_expired`
  (challenge past TTL).
- **RHAMP-REQ-147.** **Concurrency:** exactly one active protected-approval
  ceremony per `(invocation_id, attempt_id)`. Multiple concurrent *unrelated*
  approvals are permitted only if each has a unique challenge, a unique helper
  lifecycle, a unique presentation digest, and an independent credential
  assertion. A stale helper response or window for challenge A SHALL NOT
  satisfy challenge B (`ceremony_superseded`).
- **RHAMP-REQ-148.** **Process restart:** a pending ceremony's trust is lost on
  restart — the pending challenge is invalidated and a new challenge is
  required (`ceremony_superseded`). There is no stale-helper-window
  continuation and no durable pending-ceremony store. The durable truth that
  survives restart is the canonical proof / lifecycle / consumption records,
  each of which is re-verified from scratch (HPAC-REQ-058).

## 60. Recovery

- **RHAMP-REQ-149.** Credential recovery within RHAMP-001 v1.0 scope: lost or
  compromised credential → `revoke_credential` + `enroll_credential` of a
  replacement under the same `principal_id` (HPAC-REQ-065). Loss of **all**
  credentials for the sole enrolled principal → **REAL approval is unavailable
  until a protected administrative re-bootstrap** (§14). There is **no silent
  bypass and no fallback to a NON_REAL mechanism** under any recovery
  condition. A full automated recovery mechanism beyond re-bootstrap is
  **deferred**.

## 61. Protected admin enrollment / audit

- **RHAMP-REQ-150.** The future enrollment command/tool SHALL require: local
  interactive mode (§53); canonical `PrincipalRecord` selection by the
  protected admin; explicit protected-administrative confirmation; a protected
  presentation of the exact operation; authenticator presence + UV; and **no
  agent-delegated enrollment authority** (HPAC-REQ-024/029). The trusted
  bootstrap authority is HPAC-REQ-022/023's external deployment-owner protected
  administration principal (§14).
- **RHAMP-REQ-151.** Durable audit evidence SHALL be recorded for enrollment,
  revocation, replacement, and recovery/bootstrap (the §15 field set). These
  records **do not themselves authenticate** any future approval.

## 62. Mandatory real-hardware verification

- **RHAMP-REQ-152.** Before N-16-5 closes (in `.1R.33`), **at least one** real
  CTAP2 hardware verification against a genuine attached security key SHALL be
  performed, producing, at minimum, this evidence:
  - a supported roaming USB CTAP2 security key was used;
  - a real `makeCredential` enrollment succeeded and produced a canonical
    `CredentialRecord` + sidecar + counter-state record;
  - a real `getAssertion` produced an assertion that passed the full §37
    verifier sequence with `FLAG.UP` and `FLAG.UV` observed;
  - a presentation-bound approval succeeded end-to-end (real helper render →
    explicit Approve election → assertion → proof → Gate 5) and yielded a
    `PRODUCTION` `AuthenticatedHumanPrincipal` for exactly one approval;
  - a **wrong-challenge** assertion was rejected (`challenge_digest_mismatch` /
    `client_data_hash_mismatch`);
  - a **missing / failed UV** attempt was rejected where testable
    (`user_verification_missing`);
  - a **replayed** challenge/proof was rejected (`challenge_replayed` /
    `consumption_replay`);
  - a **revoked credential** was rejected (`credential_not_active`).
- **RHAMP-REQ-153.** No hardware is accessed in the `.1R.29` contract-freeze
  phase or in any phase before `.1R.33`'s controlled hardware session.

## 63. Automated test-fixture policy

- **RHAMP-REQ-154.** The automated verification suite SHALL NOT require real
  hardware for every run. It uses: a deterministic virtual / synthetic
  authenticator test fixture that is **explicitly TEST / NON_PRODUCTION**
  (monkeypatched `CtapHidDevice.list_devices` / `Ctap2` + an in-memory
  test-only ES256 key — the `hatp_fido2_provider.py` pattern); real
  WebAuthn/CTAP2 protocol test vectors for `authenticatorData` / client-data
  parsing; cryptographic negative cases; a mocked CTAP transport boundary; and
  the ≥ 55-case negative matrix frozen in `.1R.28` §36.
- **RHAMP-REQ-155.** **No synthetic / virtual / deterministic fixture object
  SHALL ever become REAL authority in a production registry.** The automated
  fixture is structurally NON_REAL (§41). N-16-5 closure requires **both** the
  automated suite green **and** the mandatory real-hardware evidence (§62) —
  they are not substitutes for each other.

## 64. Implementation / IV decomposition

- **RHAMP-REQ-156.** The frozen successor sequence (phase IDs **recommended,
  NOT reserved**; each is its own explicitly human-authorized phase with its
  own independent-verification pair):

  | Phase | Scope |
  |---|---|
  | `.1R.30` | **Real FIDO2 credential registry + authentication mechanism implementation.** Production `HumanPrincipalRegistryStore` writer path; the §17 sidecar and §21 counter-state store; the protected-admin enrollment + first-credential bootstrap ceremony tool (§13, §14); `FIDO2HumanAuthenticator` for `hpac.fido2.uv_presence.v2`; real CTAP2 assertion verification in `hpac_verifier` (§37) incl. the `FLAG.UV` check; `_ELIGIBLE_MECHANISM_IDS += {hpac.fido2.uv_presence.v2}`; `terminal_reason_code` wiring; reuse `hatp_fido2_provider` CTAP2 primitives as a shared library (§38). **No protected approval UI. No real approval-authority production path yet.** |
  | `.1R.31` | **Independent verification of `.1R.30`** — broad fixed-SHA A/B; the `.1R.28` §31 IV requirements. |
  | `.1R.32` | **Protected human-approval presentation + real approval-proof integration.** The process-isolated presentation helper; the deterministic `renderer_profile`; helper integrity / provenance (§30); explicit Approve/Reject (§34); presentation-digest binding; real `mechanism_attestation`; `verifier_kind = pcae-protected-local-presentation/1.0`; wire `require_real_assurance = True` through Gate 5 / Gate 9; a `PRODUCTION` `AuthenticatedHumanPrincipal` becomes obtainable for exactly one bound approval. **Still no N-16-6 / N-16-7.** |
  | `.1R.33` | **Independent verification of `.1R.32` + mandatory real-CTAP2-hardware verification (§62) + N-16-5 closure.** |

- **RHAMP-REQ-157.** The N-16 ordering is preserved: N-16-5 → N-16-6 → N-16-7,
  with **N-16-7 strictly last**. **No Slice C** until N-16-3..7 all close.
  RHAMP-001 does not begin, reference, or unblock N-16-6 or N-16-7.

## 65. N-16-6 / N-16-7 separation

- **RHAMP-REQ-158.** RHAMP-001 SHALL NOT govern runtime effect-adapter
  admission. The protected-presentation-helper trust model (§28–§30) is
  **separate** from the N-16-6 runtime effect-adapter supply-chain admission.
  Human credential identity SHALL NOT influence adapter admission, and adapter
  admission SHALL NOT influence human authentication.
- **RHAMP-REQ-159.** Real human approval does **not** enable runtime
  capability. After N-16-5 closes, the runtime remains
  `Observed` / `observe` / `unavailable` until the separately-authorized N-16-7
  transition. Even real approval + a future PB admission + a Gate 7 ALLOW
  leaves the runtime `unavailable`.
- **RHAMP-REQ-160.** **Production positive path after N-16-5 alone = NONE.**
  Gate 6 still blocks (no admissible adapter — N-16-6); Gate 7 still DENYs in
  production (N-16-4 seam only); runtime `unavailable` (N-16-7); no
  `adapter.dispatch(` call site exists. The first external effect remains
  **UNREACHABLE**.

## 66. N-23-1 / N-23-2

- **RHAMP-REQ-161.** N-23-1 (INFO) and N-23-2 (INFO / DEFERRED NORMALIZATION
  DEBT) are carried unchanged. RHAMP-001 does **not** normalize PBRD / PBNDE
  semantics.

## 67. Guard-impact expectations

- **RHAMP-REQ-162.** The `.1R.29` contract-freeze phase changes no `src/pcae`
  and no `tests/**` and trips no guard. The predicted guard impact for
  `.1R.30` / `.1R.32` (a **prediction**, reconciled phase-aware in those
  phases, `.1R.26` method):
  - `_ELIGIBLE_MECHANISM_IDS` guards — widen by exactly
    `{hpac.fido2.uv_presence.v2}`; subset/`==` orientation; no wildcard;
  - `verifier_kind == "deterministic-test-fixture"` guards — add
    `pcae-protected-local-presentation/1.0` as a second accepted kind;
  - `require_real_assurance` "can only reject" guards — evolve to "rejects
    unless a `PRODUCTION` descriptor + `PRODUCTION` registry records resolve";
  - `HPACAuthorityClass.PRODUCTION` unreachability guards — evolve to
    "reachable only via the full real ceremony";
  - Gate 5 / Gate 9 "no production `AuthenticatedHumanPrincipal`" guards —
    evolve to "real assurance requires the full HPAC-REQ-054 chain + a
    `PRODUCTION` descriptor";
  - "no real FIDO2 / hardware / network" no-go assertions across `.1R.3`..`.1R.20`
    IV suites — phase-aware reconciliation, each widened by exactly the new
    module set with an explicit citation; **no `def test_` renamed or
    removed**; broad fixed-SHA A/B in a worktree;
  - runtime-posture (`Observed`/`unavailable`) and `first external effect
    ABSENT` guards — **unchanged**.
- **RHAMP-REQ-163.** Historical NON_REAL phases (`.1R.3`..`.1R.20`) are **not**
  rewritten as if real FIDO2 existed then; `.1R.30` / `.1R.32` add companion
  current-canonical assertions and reconcile point-in-time scope fences
  phase-aware.

## 68. Contract-production equivalence obligation

- **RHAMP-REQ-164.** Every normative requirement of RHAMP-001 SHALL be mapped,
  by the `.1R.30` / `.1R.32` implementing phases and re-derived by `.1R.31` /
  `.1R.33` independent verification, to exact production-source and test
  evidence — the `mechanism_id` allowlist (§4), the `verifier_kind` allowlist
  and helper integrity (§5, §28–§30), the RP / client-data model (§6–§8), the
  credential / sidecar / counter-state schemas (§17, §21), the ceremony order
  (§12), the bootstrap authority (§14), the assertion-verification sequence
  (§37), UP/UV enforcement (§10), NON_REAL non-upgradeability (§41), the
  `terminal_reason_code` table (§49), the TTL bounds (§23–§25), currentness
  (§44), and the local-interactive topology (§53). **No prose-only security
  guarantee.**

## 69. Normative matrices (index)

- **RHAMP-REQ-165.** RHAMP-001 v1.0 freezes, as normative matrices, at least:
  (1) mechanism profile — §9; (2) CTAP2 / RP / client-data semantics — §6–§8;
  (3) credential schema + sidecar — §17; (4) registration / bootstrap lifecycle
  — §13–§15; (5) counter-state lifecycle — §20–§22; (6) authentication ceremony
  — §12; (7) protected presentation profile — §28–§33; (8) helper integrity
  model — §30; (9) approval challenge / client-data binding — §7, §36; (10)
  approval proof semantics — §45–§47; (11) UP/UV policy — §10; (12) revocation
  / currentness — §43–§44; (13) terminal reason vocabulary — §49; (14)
  transport / platform profile — §51; (15) local-interactive deployment
  topology — §53–§55; (16) explicit unsupported / deferred profile — §31, §55,
  §56; (17) NON_REAL non-upgradeability — §41; (18) audit / privacy retention —
  §48; (19) automated / hardware verification requirements — §62–§63; (20)
  implementation / IV decomposition — §64.

## 70. Versioning

- **RHAMP-REQ-166.** RHAMP-001 uses contract `MAJOR.MINOR`. **v1.0 is the
  initial freeze.** Unknown versions fail closed.
- **RHAMP-REQ-167.** A change that does any of the following requires a new
  **MAJOR** plus explicit human authorization and independent verification:
  introducing a browser / WebAuthn web-origin ceremony; introducing remote or
  headless approval or any network authority transport; permitting discoverable
  / resident credentials or a usernameless flow; relaxing the UP or UV
  requirement; changing the approval-intent election ceremony or its ordering;
  changing the first-credential bootstrap authority model; making attestation
  or a device-identity claim authoritative; adding a transport outside
  `{USB-HID, NFC}`; or making a NON_REAL object upgradeable.
- **RHAMP-REQ-168.** A **MINOR** may: re-state verified behaviour; add an
  additional supported authenticator model within the frozen transport /
  discoverability / UP+UV profile; tighten (never loosen) a TTL bound; add a
  `terminal_reason_code` for a newly-identified terminal path **without**
  removing or re-meaning an existing one; or clarify a test-fixture rule —
  provided no meaning above changes. A change to `rhamp_schema_version` (§2) is
  at least MINOR.
- **RHAMP-REQ-169.** No future RHAMP-001 version may retrospectively widen an
  already-issued proof's or an already-enrolled credential's granted assurance.

## 71. Invariants

| ID | Statement |
|---|---|
| RHAMP-INV-001 | The real `mechanism_id` allowlist is exactly `{hpac.fido2.uv_presence.v2}` and the real `verifier_kind` allowlist is exactly `{pcae-protected-local-presentation/1.0}` — verifier-owned, exact-match, no wildcard (§4, §5, §40). |
| RHAMP-INV-002 | A successful CTAP2 assertion, an `AuthenticatedHumanPrincipal`, and a hardware touch are each **not** approval; approval additionally requires the resolved protected presentation and the explicit observed `approve` election, verified as independent steps (§11, §12, §34, §38). |
| RHAMP-INV-003 | Both `FLAG.UP` and `FLAG.UV` are mandatory; a UP-only assertion never yields an `AuthenticatedHumanPrincipal`; the floor cannot be lowered by repository or protected administrator (§10, §37). |
| RHAMP-INV-004 | The `rp_id` (`hpac.pcae.local`) and the canonical client-data context (`pcae-hpac://…`) are compiled-in PCAE constants, not caller-selectable and not browser origins; the assertion binds `authenticatorData ‖ SHA-256(canonical client-data bytes)` (§6, §7, §8). |
| RHAMP-INV-005 | The first-credential bootstrap authority is HPAC-REQ-023's external deployment-owner protected administration principal — never an arbitrary CLI caller, OS username, first registrant, agent, or repository identity; an unprovable anchor fails closed / BLOCKS (§14). |
| RHAMP-INV-006 | PCAE stores no private key, PIN, or biometric material — structurally (no such field on any RHAMP-001 artifact); the sidecar and counter-state artifacts hold only public / audit data (§17, §18, §21). |
| RHAMP-INV-007 | Attestation is not authoritative: `none`/`self` accepted unvalidated, enterprise attestation prohibited, no MDS, no AAGUID security classification, no device-uniqueness claim (§19, §52). |
| RHAMP-INV-008 | The signature-counter policy fails closed on a non-zero regression / non-increment, records it, and flags the credential for admin review — never auto-revoking, never treating a `0`/absent counter as a regression (§20, §21). |
| RHAMP-INV-009 | Challenge TTL ≤ 120 s; `max_proof_age_seconds` ≤ 300 s; presentation `expires_at` == the RIASC approval `expires_at`; each may be tightened, never loosened (§23–§25). |
| RHAMP-INV-010 | Every terminal failure maps deterministically to exactly one of the 41 closed `terminal_reason_code` values; human rejection, authentication failure, presentation-integrity failure, staleness, and internal error are distinct audit categories (§49, §50). |
| RHAMP-INV-011 | The protected presentation helper is PCAE-owned, integrity-bound (pinned digest + descriptor, not path), process-isolated, short-lived, local-only, non-networked, and un-substitutable / un-observable by the requesting agent; caller-nominated helpers are prohibited (§28–§30). |
| RHAMP-INV-012 | The digest covers exactly the neutralized displayed bytes; `approval_preview_digest == human_visible_representation_digest`; all 13 `human_visible_facts` are rendered with no truncation of a mandatory field; untrusted repository text cannot alter a trusted label or control (§31–§33). |
| RHAMP-INV-013 | A NON_REAL proof / presentation object is never upgradeable into REAL authority — structurally, via `SIMULATION_ONLY`, the `_ELIGIBLE_MECHANISM_IDS` frozenset, `HPACAuthorityClass` propagation, `_authority_class_of`, the identity registry, and `__reduce__` raising (§41). |
| RHAMP-INV-014 | RHAMP-001 v1.0 REAL approval requires a local interactive control-plane host with an attached USB/NFC CTAP2 key; headless / remote / networked approval is out of scope, deferred, and authorized by no part of this contract (§53–§55). |
| RHAMP-INV-015 | RHAMP-001 v1.0 defines no browser, web origin, TLS, loopback service, port, CSRF/cookie/session model, or web UI (§56). |
| RHAMP-INV-016 | The only normative delta of the entire N-16-5 track through `.1R.29` is RHAMP-001 v1.0; HPAC-001 stays v2.1 and every other contract is byte-unchanged; no `src/pcae` change; runtime `Observed`/`observe`/`unavailable`; first external effect ABSENT (§1). |
| RHAMP-INV-017 | Real human approval does not enable runtime capability or admit any adapter; N-16-6 and N-16-7 remain independent, unbegun, and (N-16-7) strictly last; the production positive path after N-16-5 alone is NONE (§64, §65). |
| RHAMP-INV-018 | N-16-5 closure requires **both** the ≥ 55-case automated negative suite green **and** ≥ 1 real-CTAP2-hardware verification (§62, §63); neither substitutes for the other. |

## 72. Freeze verdict

**RHAMP-001 v1.0: FROZEN.**

The real human-authentication mechanism is native CTAP2
(`hpac.fido2.uv_presence.v2`), roaming hardware key, USB-HID / NFC,
non-discoverable, `allowList`-bound, UP + UV mandatory, no attestation trust,
no browser, no WebAuthn client, no web origin, fixed internal `rp_id`
`hpac.pcae.local`, fixed PCAE canonical client-data context. The protected
approval presentation is a PCAE-owned, integrity-bound, process-isolated,
short-lived local helper (`verifier_kind = pcae-protected-local-presentation/1.0`)
that renders exactly the 13 closed `human_visible_facts`, observes an explicit
Approve/Reject election, and drives the single step-up assertion whose
canonical client-data binds the presentation digest. First-credential bootstrap
is anchored by HPAC-REQ-023's external deployment-owner protected administration
principal. A new protected per-credential FIDO2-credential sidecar and a new
protected per-credential counter-state record are frozen; `CredentialRecord` and
every HPAC-001 schema are byte-unchanged. Challenge TTL ≤ 120 s, proof age
≤ 300 s, presentation expiry == approval expiry. The closed `terminal_reason_code`
vocabulary is 41 values (re-derived; the `.1R.28` "25"/"27" figures superseded).
NON_REAL objects remain structurally non-upgradeable. RHAMP-001 v1.0 REAL
approval requires a local interactive control-plane host; headless / remote
approval is deferred and authorized by no part of this contract. The
implementation is decomposed into `.1R.30` (mechanism + registry + bootstrap)
→ `.1R.31` (IV) → `.1R.32` (protected presentation + real-assurance wiring) →
`.1R.33` (IV + mandatory real-hardware verification + N-16-5 closure). No
production source, no HPAC-001 bump, no MAJOR/MINOR to any existing contract, no
FIDO2/CTAP implementation, no hardware access, no protected-UI implementation,
no N-16-6/N-16-7 work, no Slice C, no first external effect, no execution
enablement is performed by the `.1R.29` freeze. Runtime remains
`Observed` / `observe` / `unavailable`. The first external effect remains
**ABSENT**.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.
