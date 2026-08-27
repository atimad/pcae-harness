# HPAC-001 v1.0 — Human Principal Authentication Contract

## Contract identity and status

**Contract:** HPAC-001
**Version:** 1.0
**Status:** FROZEN
**Frozen by:** Phase 149O.20L.7O.3W.1R.2B — Runtime Invocation
Human-Principal Authentication Contract Freeze
**Depends on:** RIHAC-001 v1.1 (`RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md`,
this contract's consumer for runtime-invocation approval), RIASC-001 v2.0
(`RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md`, the schema whose
`provenance` object references this contract's artifacts by ID), HPSE-001
v1.1 and HHCE-001 (pattern precedent only — reused as a *design pattern*,
not as a live dependency; see §6 for the exact reuse-vs-separation
decision), HATP-001 v1.0 (terminology precedent for "principal" and
"presence-gated" — not amended, not depended upon for well-formedness).
**Architecture basis:**
`docs/PHASE_149O_20L_7O_3W_1R_2A_RUNTIME_INVOCATION_HUMAN_PRINCIPAL_AUTHENTICATION_AUTHORITY_PROVENANCE_ARCHITECTURE.md`
(149O.20L.7O.3W.1R.2A §29-§66, the architecture this contract formalizes),
`docs/PHASE_149O_20L_7O_3W_1R_2B_RUNTIME_INVOCATION_HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT_FREEZE.md`
(this freeze's own report — full rationale for every decision below).

This is a contract-freeze document. It formalizes the human-principal
authentication architecture 149O.20L.7O.3W.1R.2A designed into concrete,
testable requirements. It is not an implementation: it creates no real
registry, enrolls no real principal, verifies no real proof, touches no
hardware, and does not modify `src/pcae/core/runtime_authority.py`,
`hatp_bootstrap.py`, `hatp_fido2_provider.py`, or any other production
module.

Runtime remains `Observed` / `observe` / `unavailable`.

---

## 0. Normative language

`SHALL`, `SHALL NOT`, `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY`
are normative, per RFC 2119 conventions used throughout this repository's
other bound contracts. Every normative sentence carries a unique
requirement ID, `HPAC-REQ-###`, sequential from 001, no gaps, no
duplicates. This contract's own numbering namespace is independent of
`RIHAC-REQ-*`/`RIASC-REQ-*`/`HPSE-REQ-*`/`HHCE-REQ-*`/`HATP-REQ-*`,
mirroring HPSE-001's own precedent of a separate namespace for a companion
contract. An ambiguity at any authority boundary SHALL fail closed.

```text
authenticated human principal != confirmation
confirmation                  != approval
approval                      != PB permission
PB permission                 != runtime capability
runtime capability            != execution
human principal                != agent identity
human principal                != producer identity
human principal                != runtime identity
human principal                != OS username
human principal                != Git identity
human principal                != session agent identity
```

- **HPAC-REQ-001.** Every semantic wall above is normative contract text,
  not commentary. A future implementation that collapses any pairing named
  above into a single mechanism or a single check is non-conformant.

## 1. Purpose and scope

- **HPAC-REQ-002.** HPAC-001 governs, and owns exclusively: human principal
  identity (§4); the `HumanPrincipalRegistry` (§5); the `HumanAuthenticator`
  mechanism abstraction (§10-§15); principal and credential enrollment
  (§8-§9); authentication-proof production and structure (§16-§17); proof
  verification behavior (§18); revocation (§21); mechanism status (§13);
  trust/assurance level (§20); and failure behavior (§25).
- **HPAC-REQ-003.** HPAC-001 SHALL NOT own, define, or gate: Permission
  Broker permission, runtime-target selection, execution capability, Runtime
  Enforcement, or dispatch. Those remain exclusively RIHAC-001/RIASC-001/
  PBRD-001/RDGO-001/RPAC-001 territory (§39-§41 below). This contract
  produces evidence consumed by RIHAC-001's validator (RIHAC-001 v1.1 §16
  step 4); it does not itself decide whether a `RuntimeInvocationApproval`
  is created, validated, or consumed.
- **HPAC-REQ-004.** This contract resolves finding **N2**
  (149O.20L.7O.3W.1R.1 §14, restated 149O.20L.7O.3W.1R.2 §4,
  re-derived verbatim in the required phase document's §3): the fact that
  `create_runtime_invocation_approval` accepted a caller-supplied
  `approver_id`/`identity_evidence_kind` pair with no independent
  verification. This contract makes that verification structurally
  required and independently checkable; it does not itself perform the
  verification (that remains RIHAC-001 v1.1 §16 step 4's job, consuming
  this contract's artifacts).

## 2. Terminology

- **Human principal.** A human identified by a stable `principal_id` (§4) —
  categorically distinct from any OS account, Git identity, PCAE
  agent/session identity, or producer identity (§4's own exclusion list).
- **Authentication mechanism.** A concrete method (e.g. hardware-backed
  FIDO2) by which a principal proves presence/identity for one specific
  challenge. Described statically by a mechanism descriptor (§14) and
  dynamically by mechanism status (§13).
- **Credential.** The specific enrolled key/device material bound to one
  principal under one mechanism (§9). One principal MAY own more than one
  credential (§9).
- **Challenge.** A fresh, single-use, subject-bound value the authenticator
  must incorporate into its proof (§16).
- **Authentication proof.** The normalized, verifiable artifact a
  `HumanAuthenticator` produces in response to one challenge (§17).
- **Assurance level.** A closed vocabulary describing how strong a
  mechanism's presence/identity guarantee is (§20).
- **Verifier.** The trusted component that checks a proof against a
  registry, credential, and challenge/subject binding (§18); conceptually
  the same actor as RIHAC-001's `ApprovalAuthorityValidator`
  (149O.20L.7O.3W.1R.2A §44), not a new independent trust root.

## 3. Non-authority rule

- **HPAC-REQ-005.** Schema conformance, digest agreement, storage presence,
  registry-record existence, or identifier shape alone SHALL NOT
  independently create authenticated-human authority. Authority exists only
  through this contract's full verification chain (§18) succeeding, and
  even then only as evidence consumed by RIHAC-001's own authority
  determination (RIHAC-001 v1.1 §12) — HPAC-001 verification is necessary,
  never solely sufficient, for a `RuntimeInvocationApproval` to be trusted.
- **HPAC-REQ-006.** No field named `approved`, `authorized`, `permission`,
  `trusted`, `human_verified`, or an equivalent authority shortcut is
  permitted anywhere in this contract's artifacts. `additionalProperties:
  false` applies recursively to every object this contract defines.

---

## 4. Human principal identity

- **HPAC-REQ-007.** `principal_id` SHALL be a stable, non-display, opaque
  identifier. It SHALL NOT equal, be derived from, or be required to equal
  any OS-level username, UID, GECOS field, process identity,
  `$USER`/`getpass.getuser()`/`os.getlogin()` value, Git `user.name`/
  `user.email`, PCAE `--agent-id` value, session identifier, or artifact
  `producer_component` constant. This restates, as this contract's own
  binding rule rather than borrowed text, HPSE-REQ-001/002's identical
  discipline for HATP's own `principal_id` — the same rule, independently
  adopted here because it is correct, not merely because HPSE-001 says so.
- **HPAC-REQ-008.** `principal_id` grammar: non-empty string, max 256
  characters, no leading/trailing whitespace — identical grammar to
  RIASC-001's existing `nonempty_id` pattern (RIASC-001 §10 `$defs`), for
  consistency across the contract family. No new grammar is invented.
- **HPAC-REQ-009.** `principal_id` is globally unique within
  `HumanPrincipalRegistry` (§5) and, once assigned, SHALL NOT be
  reassigned, reused after revocation, or changed across credential
  rotation (§21/§22).
- **HPAC-REQ-010.** `display_name`, `email`, and any other human-facing
  presentation metadata are explicitly NOT part of `principal_id` and, per
  §23 (privacy), SHALL NOT be persisted in this contract's registry at all
  — not merely kept separate from `principal_id`, but omitted entirely.
  UI/audit readability needs, if any, are a future, separately governed
  concern outside this contract's registry schema.
- **HPAC-REQ-011.** Immutability: a `principal_id` denotes the same human
  principal for the entire lifetime of every record that references it.
  Revocation (§21) ends a principal's ability to authenticate; it does not
  reassign or retire the identifier for reuse by a different human.

## 5. `HumanPrincipalRegistry`

- **HPAC-REQ-012.** A canonical `HumanPrincipalRegistry` is required. This
  affirms 149O.20L.7O.3W.1R.2A §29's own recommendation and closes the
  governing prompt's item 7 requirement to decide, not defer, this
  question.
- **HPAC-REQ-013.** The registry SHALL contain exactly two record kinds:
  `PrincipalRecord` (`principal_id`, `status`) and `CredentialRecord`
  (`credential_id`, `principal_id`, `mechanism_id`, `public_key_ref`,
  `status`, `enrolled_at`, `revoked_at`). No third record kind exists in
  v1. This mirrors HPSE-001's `PrincipalRecord`/`SignerRecord` two-record
  shape (schema pattern reuse, HPSE-REQ-007/013) without reusing HPSE-001's
  actual document or namespace (§6 below).
- **HPAC-REQ-014.** `status` for both record kinds is the closed two-value
  vocabulary `{"active", "revoked"}` — identical convention to HPSE-001
  (HPSE-REQ-005), reused because it is the correct minimal vocabulary, not
  merely for consistency's own sake.
- **HPAC-REQ-015.** Every registry write SHALL be atomic (create-only or
  append-only for revocation), read-back verified, and SHALL preserve every
  other record byte-for-byte unchanged except the one record being enrolled
  or revoked — identical discipline to HPSE-REQ-023/031/032, reused as a
  correct, already-proven idiom.
- **HPAC-REQ-016.** List entries SHALL be sorted by their key field
  (`principal_id` for `PrincipalRecord`, `credential_id` for
  `CredentialRecord`) on every write, for deterministic byte-identical
  serialization — identical discipline to HPSE-REQ-024.
- **HPAC-REQ-017.** Unknown fields and malformed documents SHALL be
  rejected; the registry has no free-form extension container in v1.

## 6. HATP reuse vs. separation (mandatory determination)

This section resolves the governing prompt's mandatory item 13 explicitly,
comparing all three named options.

- **Option A (direct reuse of HATP's `registry.json`
  `principals`/`signers` sections):** Rejected. `registry.json` is governed
  exclusively by HPSE-001 (HPSE-001 §2), scoped to Class-B Protected-Root
  admin-signing authority (HBDC-REQ-066) — a materially different authority
  domain from per-invocation runtime approval (RPAC-REQ-049 explicitly
  forbids reinterpreting HATP artifacts as "generic invocation
  permission"). Writing HPAC-001 records into that same document would
  either require an HPSE-001 scope amendment (out of this phase's
  authorization) or silently blur `HATP authority == runtime invocation
  approval authority`, which the governing prompt's item 13 explicitly
  forbids.
- **Option C (entirely separate, no shared pattern or primitives):**
  Rejected as unnecessarily wasteful. HPSE-001/HHCE-001 already define a
  correct, independently-verified registry-write discipline (atomic write,
  read-back verification, sorted serialization, closed schema, typed error
  hierarchy) and HATP's FIDO2 provider interface (`hatp_fido2_provider.py`,
  `hatp_providers.py`) already defines a correct low-level CTAP2
  credential-identity/verification primitive shape. Reinventing either from
  nothing would be premature complexity the governing prompt's item 45
  explicitly warns against.
- **Option B — SELECTED: reuse the low-level pattern and, where a future
  implementation chooses, the low-level FIDO2 provider primitives, while
  maintaining a completely separate registry document, namespace, and
  credential/challenge domain from HATP's own.**
- **HPAC-REQ-018.** `HumanPrincipalRegistry` SHALL be a document
  physically and logically separate from HATP's `registry.json`, stored at
  a distinct canonical path (§7). HPAC-001 registry records SHALL NOT be
  merged into, read from, or written to `registry.json`, and vice versa.
- **HPAC-REQ-019.** A future implementation MAY reuse HATP's low-level
  FIDO2/PIV provider primitives (`hatp_providers.py`'s
  `HardwareProviderCapabilities`/credential-identity/verify shape) as a
  *library dependency* for HPAC-001's own `HumanAuthenticator`
  implementation. Doing so SHALL NOT cause HPAC-001's registry, principal
  identity space, or challenge domain to become HATP's registry, principal
  identity space, or challenge domain — the code MAY be shared; the trust
  domains SHALL NOT be.
- **HPAC-REQ-020.** `HumanPrincipalRegistry`'s `principal_id` space is
  independent of HATP's `principal_id` space. The same physical human MAY
  hold a `principal_id` in both registries; they are not required, and are
  not permitted by this contract, to be the same string or to be
  cross-referenced by either registry's schema.

## 7. Registry scope, path, and trust root

Resolves governing-prompt items 66/68/69 explicitly.

- **HPAC-REQ-021.** `HumanPrincipalRegistry` is a **deployment/user-scoped**
  artifact, not a per-repository artifact. Rationale: a human principal is
  a real-world identity a human enrolls once and expects to reuse across
  every repository they operate PCAE in (governing-prompt item 66's own
  framing: "human identity is user/deployment-level, while approval is
  repo/task-bound"). `RuntimeInvocationApproval`'s existing five-member
  subject (RIHAC-001 §5) already supplies the repo/task-bound half of that
  distinction; this contract supplies only the user-level half.
- **HPAC-REQ-022.** The canonical registry path SHALL be outside any single
  repository's own working tree or `.pcae/` governance store — analogous to
  HATP's own Protected-Root-outside-ordinary-repository-control pattern
  (HBDC-001), but a **separate** Protected-Root instance from HATP's own
  (HPAC-REQ-018). This directly closes the malicious-repository threat
  (§10 below, HPAC-REQ-069): no code path reachable from within a
  repository's own agent-writable tree can resolve to this path by
  construction, because the path is never inside the repository at all.
- **HPAC-REQ-023.** Bootstrap trust root: the first `PrincipalRecord` and
  its first `CredentialRecord` are established by a **local admin/human
  bootstrap ceremony**, run by the human who physically controls the
  deployment machine at that moment — the identical pattern HATP already
  uses (HBDC-REQ-066's "Admin execution principal", restated at
  149O.20L.7O.3W.1R.2A §31) and the same trust-anchor-bootstrapping pattern
  WebAuthn itself uses for first-credential registration. This is
  necessarily circular-trust-free: no prior PCAE-internal principal exists
  to check the first enrollment against, so trust is anchored in physical/
  local-machine control at that one moment, not in any PCAE mechanism.
  This requirement resolves the governing prompt's item 9 (bootstrap trust
  root) explicitly rather than leaving it implicit.
- **HPAC-REQ-024.** The bootstrap/enrollment writer SHALL be a standalone,
  non-agent-invocable admin tool — never a subcommand of the ordinary
  agent-reachable `pcae` CLI, mirroring HPSE-REQ-028/029's identical
  discipline, adopted here as a correct pattern, not a dependency.

## 8. Enrollment

- **HPAC-REQ-025.** Enrollment establishes who may ever authenticate; it
  does not itself authenticate or approve anything — identical discipline
  to HPSE-001's own framing (HPSE-001 §3's "Enrollment... establishes who
  may approve; it does not itself approve anything"), restated here as
  this contract's own binding rule.
- **HPAC-REQ-026.** The writer SHALL expose exactly: `enroll_principal`,
  `revoke_principal`, `enroll_credential`, `revoke_credential` — plus a
  read-only preview variant for each, mirroring HPSE-REQ-026/030's
  discipline (never-writes preview, would-enroll/already-enrolled/
  conflict/would-revoke/already-revoked/not-found classification).
- **HPAC-REQ-027.** `enroll_credential` SHALL require an existing, `active`
  `PrincipalRecord` for the supplied `principal_id`. Enrolling a credential
  against a missing or revoked principal fails closed.
- **HPAC-REQ-028.** Every enrollment/revocation operation SHALL require
  explicit evidence of a fresh, separate human election authorizing that
  specific operation — mirroring HPSE-REQ-042's identical discipline. An
  unverified boolean or free-form "approved" string is never sufficient.
  The election-evidence reference is recorded as audit metadata only,
  never cryptographically verified by this writer (mirrors HPSE-REQ-043).
- **HPAC-REQ-029.** No entity SHALL enroll or expand its own authentication
  authority without the same fresh-election evidence required to enroll any
  other principal — mirrors HPSE-REQ-041's identical self-enrollment
  prohibition, including for the admin's own enrollment.

## 9. Credential ownership and multiplicity

- **HPAC-REQ-030.** Cardinality is exactly one principal → zero or more
  credentials; each `CredentialRecord` names exactly one `principal_id`.
  This contract explicitly permits multiple credentials per principal in
  v1 (governing-prompt item 35's "prefer simple but recoverable design" —
  a single-credential-only rule would make ordinary hardware-key loss
  unrecoverable without a bootstrap-ceremony repeat).
- **HPAC-REQ-031.** Credential rotation (replacing a principal's credential
  with a new physical device) SHALL be modeled as two separate writer
  operations — `enroll_credential` for the new credential followed by
  `revoke_credential` for the old one — never a single in-place field
  overwrite, mirroring HPSE-REQ-016's identical rationale (`credential_id`
  is itself the credential's stable identity; in-place reassignment would
  silently reassign what a still-referenced record's primary key denotes).

## 10. `HumanAuthenticator` mechanism abstraction

- **HPAC-REQ-032.** `HumanAuthenticator` is a minimal interface, not a
  general plugin registry (resolving governing-prompt items 30/45
  explicitly: build one narrow interface, not a plugin system, unless a
  second concrete implementation is required at launch — it is not, per
  §14/§15). Its responsibilities:
  1. **describe** — return this mechanism's static descriptor (§14);
  2. **status** — return this mechanism's current dynamic status (§13);
  3. **prepare_challenge** — bind a fresh, single-use challenge to an exact
     approval subject/preview digest (§16);
  4. **verify_response** — verify a produced proof against a challenge and
     a resolved credential (§18, invoked by the verifier, not by the
     authenticator itself); and
  5. **resolve_principal** — given a verified proof, return the
     `principal_id`/`credential_id` pair it was produced under.
- **HPAC-REQ-033.** No implementation is created by this contract. This
  section freezes the interface's semantic responsibilities only, per the
  governing prompt's own instruction (item 30: "No implementation").

## 11. Component responsibilities (non-collapse)

- **HPAC-REQ-034.** `HumanAuthenticator` (produces proofs) SHALL NOT be
  folded into `create_runtime_invocation_approval` (which remains a pure,
  already-validated-input constructor per RIHAC-001) and SHALL NOT be
  folded into the RIHAC-001 validator (which verifies proofs, not
  produces them) — restating 149O.20L.7O.3W.1R.2A §44's own component
  boundary as binding contract text.
- **HPAC-REQ-035.** PB SHALL NOT become a human-authentication verifier.
  PB continues to receive only a validated-authority reference plus a
  validation-evidence projection digest (PBRD-001 §7); it never receives
  raw `HumanAuthenticationProof` material, mechanism internals, or registry
  content.

## 12. Authentication proof — overview

- **HPAC-REQ-036.** An authentication proof is meaningless outside the
  exact challenge/subject it was produced for (§16/§17). A proof valid for
  invocation A SHALL fail for invocation B; a proof for a previous
  challenge SHALL fail for a new challenge (§24).

## 13. Mechanism status (dynamic)

- **HPAC-REQ-037.** Mechanism status is distinct from mechanism
  registration and SHALL NOT be conflated with it (governing-prompt item
  32's explicit instruction). Closed vocabulary:
  `configured` (credential/verifier wiring present),
  `credential_available` (a live credential responds),
  `verifier_available` (the verification backend is reachable),
  `healthy` (all of the above, ready to authenticate now),
  `unavailable` (any prerequisite missing — fails closed, §25),
  `revoked` (the associated credential or principal has been revoked).
- **HPAC-REQ-038.** `healthy` status alone never constitutes authority; it
  only means an authentication *attempt* may proceed. Only a verified proof
  (§18) constitutes evidence.

## 14. Primary v1 mechanism descriptor — hardware-backed FIDO2

Resolves governing-prompt items 12/33/54/55 (mechanism design, assurance
model, minimum required assurance).

- **HPAC-REQ-039.** `mechanism_id`: `hpac.fido2.presence_gated.v1`.
- **HPAC-REQ-040.** Static descriptor fields: `mechanism_id`; `assurance_level`
  (§20); `offline_capable` (`true`, §17 below); `presence_support` (`true`
  — UP, user-presence gesture, required); `verification_support`
  (`configurable` — UV, user-verification/biometric-or-PIN, MAY be required
  by a future deployment policy but is not itself the property that
  resists §16's same-user-agent threat, see HPAC-REQ-042); `platform_compat`
  (`macos, linux` — CTAP2 hardware keys are OS-neutral, resolving
  governing-prompt items 46/57 without a platform-specific adapter).
- **HPAC-REQ-041.** Enrollment ceremony: reuses HPSE-REQ-059's already-frozen
  target semantics (a canonical, protocol-appropriate credential-minting
  ceremony producing a stable, durable credential-identity byte string) as
  a *pattern*, applied to this contract's own separate registry (§6) — not
  a live call into HATP's own enrollment writer.
- **HPAC-REQ-042 (UP/UV determination — resolves item 33 explicitly).**
  User Presence (UP) — a physical touch gesture — is the property that
  actually closes the mandatory same-user-agent threat (§16 below): it is
  the one signal a co-resident autonomous process structurally cannot
  produce without physical device access, regardless of whether it can
  silently trigger the device's electrical "wake" state. UP alone is
  therefore the v1 minimum required flag. User Verification (UV — PIN or
  biometric binding the gesture to a specific enrolled human, not merely
  "someone touched it") strengthens identity binding but is not required
  to resist the *same-user-agent* threat specifically, because that threat
  is about presence of *a* human, not about distinguishing *which* human
  among several who might share physical access to the device — a
  narrower, deployment-specific question this v1 mechanism does not need
  to answer for the single-principal default (§9 of the required phase
  document / 149O.20L.7O.3W.1R.2A §50). **v1 minimum: UP required; UV
  optional, deployment-configurable, not load-bearing for the mandatory
  threat this contract exists to resist.**
- **HPAC-REQ-043.** Challenge generation: uses `HumanAuthenticator.
  prepare_challenge` (§10), which SHALL derive the challenge from the exact
  RIHAC-001 approval-preview digest plus a fresh cryptographically random
  nonce (§16) — never a static or predictable value.
- **HPAC-REQ-044.** Signed assertion: the FIDO2 CTAP2 assertion (or
  equivalent future-protocol signature) SHALL be verified against the
  enrolled credential's public verification material resolved from
  `CredentialRecord` (§5), following the identical provider-identity-
  exchange discipline HATP's own `_resolve_signer`/`verify()` path already
  uses at the *pattern* level (HPAC-REQ-019), applied against HPAC-001's
  own separate registry.
- **HPAC-REQ-045.** Replay protection: the challenge/nonce SHALL be
  single-use; a durable, checked-at-verification-time record of consumed
  challenges SHALL prevent reuse (§16/§24).
- **HPAC-REQ-046.** Hardware touch semantics: a physical touch on the
  authenticator device grants no authority by itself. The touch's
  resulting assertion is authority-relevant only when it is bound, by
  signature, to the exact challenge/subject this specific approval
  presented — a touch on an unrelated operation (e.g. a concurrent HATP
  signing ceremony) SHALL fail verification here, per §15's mandatory
  domain separation.

## 15. Domain separation (mandatory — resolves items 14/15)

- **HPAC-REQ-047.** A challenge namespace tag, `hpac.runtime_invocation_approval.v1`,
  SHALL be included in every challenge this contract's `prepare_challenge`
  constructs. A signed assertion produced for this contract's challenge
  domain SHALL NOT verify successfully as an HATP signing-ceremony
  assertion, a publication approval, a Class-B action, or any other
  human-confirmation domain, and vice versa — even if the same physical
  hardware credential is cross-enrolled under both HATP's registry and this
  contract's registry (§6).
- **HPAC-REQ-048.** Cross-domain credential reuse (governing-prompt item
  14): a human MAY enroll the identical physical FIDO2 device under both
  HATP's registry and `HumanPrincipalRegistry`. This is permitted — the
  key material itself is not this contract's authority boundary, the
  challenge domain is (§14's separation). Each enrollment SHALL receive its
  own distinct `credential_id`/`signer_key_id` in its own registry (never
  a shared cross-registry identifier), preserving independent audit
  attribution: a proof verified under this contract's domain SHALL always
  be traceable to exactly this contract's own `CredentialRecord`, never
  ambiguously to a HATP `SignerRecord` sharing the same physical device.

## 16. Challenge subject, nonce, and replay

Resolves governing-prompt items 16/17.

- **HPAC-REQ-049.** The challenge SHALL bind, at minimum: `principal_id`
  (once resolved during proof production), the RIHAC-001 approval-preview
  digest (which itself already encodes `invocation_id`, `runtime_target_id`,
  `prompt_hash`, `repository_identity`, `task_id`, and `approval_scope` per
  RIHAC-001 §10/§11), a fresh nonce, and the `hpac.runtime_invocation_approval.v1`
  domain tag (§15).
- **HPAC-REQ-050.** Nonce origin: cryptographically strong random bytes,
  generated by the trusted challenge-construction component (never the
  authenticator, adapter, or caller). Uniqueness: SHALL NOT repeat across
  any two challenges ever issued for the same or different principals.
  Lifetime: a challenge SHALL expire if unconsumed within a short,
  separately-governed bound (not frozen numerically here — a future
  implementation phase sets it, consistent with RIHAC-001's own precedent
  of not freezing an arbitrary duration for `expires_at`, RIHAC-001 §14).
  Storage: the nonce SHALL be durably recorded as consumed at the moment
  verification succeeds (§18), atomically with the proof-consumption record
  (§24), never before.
- **HPAC-REQ-051.** No predictable, sequential, timestamp-only, or reusable
  challenge value is permitted.

## 17. Authentication proof — normalized structure

Resolves governing-prompt item 18.

- **HPAC-REQ-052.** A `HumanAuthenticationProof` SHALL contain exactly:
  `proof_id`; `mechanism_id`; `principal_id`; `credential_id`;
  `challenge_digest` (SHA-256 of the exact challenge bytes, not the raw
  challenge, mirroring RIASC-001's own digest-not-raw-content discipline);
  `assertion` (the mechanism-specific signature/response bytes, opaque to
  this schema, base64url-encoded); `authenticated_at` (UTC RFC 3339,
  identical grammar to RIHAC-001 §14's timestamp discipline);
  `verifier_version`. No secret, PIN, private key, or raw biometric
  template is ever included (§23).
- **HPAC-REQ-053.** `additionalProperties: false` applies. No free-form
  extension field exists in v1.

## 18. Proof verification — exact sequence

Resolves governing-prompt item 19, consumed by RIHAC-001 v1.1 §16 step 4.

- **HPAC-REQ-054.** Verification SHALL execute in this fail-closed order:
  1. resolve `principal_id` in `HumanPrincipalRegistry`; reject if missing
     or not `active`;
  2. resolve `credential_id` under that principal; reject if missing, not
     bound to this `principal_id`, or not `active`;
  3. resolve `mechanism_id`; reject if unknown or below the minimum
     required assurance level (§20);
  4. recompute `challenge_digest` from the exact challenge state and
     compare; reject on mismatch;
  5. verify subject binding: the challenge's bound approval-preview digest
     equals the exact `RuntimeInvocationApproval` subject/scope/expiry
     under validation; reject on mismatch;
  6. verify `assertion` against the resolved credential's public
     verification material; reject on signature/assertion failure;
  7. verify presence/verification flags meet the mechanism's minimum
     requirement (§14: UP required, UV per deployment policy); reject if
     unmet;
  8. verify freshness: `authenticated_at` is recent relative to a trusted
     clock and the challenge has not expired (§16); reject if stale;
  9. verify the challenge/nonce has not been previously consumed (replay
     check, §24); reject on replay; and
  10. emit an immutable, trusted `AuthenticatedHumanPrincipal` result
      binding `principal_id`, `credential_id`, `mechanism_id`, and the
      verified challenge/subject digest (§19).
- **HPAC-REQ-055.** No later step runs as a shortcut when an earlier step
  fails. Verification evidence is not itself PB permission, Runtime
  Enforcement approval, or a `RuntimeInvocationApproval` — it is the
  evidence RIHAC-001 v1.1 §16 step 4 consumes to decide whether one may be
  trusted.

## 19. Authenticated-principal result — trusted construction

Resolves governing-prompt items 20/21/22.

- **HPAC-REQ-056.** `AuthenticatedHumanPrincipal` is a trusted-construction
  type: it SHALL be producible only as the return value of a successful
  §18 verification sequence, never by direct construction from caller-
  supplied strings or dicts. This is the identical structural discipline
  RIHAC-001's own family already applies elsewhere (B1's forgeable-seal
  finding, 149O.20L.7O.3W.1R.2 §9, names exactly this class of mistake to
  avoid) — HPAC-001 does not repeat it here.
- **HPAC-REQ-057.** A caller (adapter, runtime, CLI argument, or approval
  producer) SHALL NOT construct, serialize-and-replay, or otherwise
  manufacture an `AuthenticatedHumanPrincipal` value without a fresh,
  successful §18 verification producing it.
- **HPAC-REQ-058.** Serialization boundary: an `AuthenticatedHumanPrincipal`
  or a `HumanAuthenticationProof` MAY be persisted (e.g. as the canonical
  proof-store artifact referenced by RIASC-001's `authentication_proof_ref`,
  §20 of RIASC-001), but deserializing stored proof material SHALL NOT by
  itself yield trusted `AuthenticatedHumanPrincipal` state — every
  consumption SHALL re-run §18's verification sequence against current
  registry state (principal/credential status may have changed since the
  proof was stored) rather than trusting a cached verification result.

## 20. Assurance level model

Resolves governing-prompt items 54/55.

- **HPAC-REQ-059.** Closed vocabulary, minimal by design (governing-prompt
  item 54's own "maybe a boolean capability set is sufficient" steer,
  resolved here as a small enum rather than a boolean, because a third,
  future presence-gated-but-not-hardware-backed mechanism — §22 — needs a
  middle value): `ASSERTED` (an unverified claim — never sufficient,
  this is v1.0's retired `identity_evidence_kind` shape, named here only
  to be excluded); `PRESENCE_GATED` (a mechanism requiring a physical or
  OS-mediated presence gesture a co-resident process cannot silently
  trigger, but not backed by dedicated cryptographic hardware — e.g. a
  correctly OS-presence-gated software key, §22 Option A-fallback);
  `HARDWARE_BACKED_PRESENCE_GATED` (a dedicated cryptographic authenticator
  requiring a physical touch gesture — the primary v1 mechanism, §14).
- **HPAC-REQ-060.** Minimum required assurance for real local-CLI v1
  dispatch: `PRESENCE_GATED` or stronger. `ASSERTED` SHALL NEVER qualify —
  this is the structural closure of N2: no mechanism whose evidence is a
  bare claim, however shaped, may ever satisfy RIHAC-001 v1.1 §12 condition
  7.

## 21. Revocation and recovery

Resolves governing-prompt items 37/38.

- **HPAC-REQ-061.** Principal revocation: monotonic — the first-recorded
  revocation is authoritative; a later revocation of an already-revoked
  principal is an idempotent no-op, mirroring HPSE-REQ-006's identical
  discipline.
- **HPAC-REQ-062.** Credential revocation: identical monotonic discipline,
  scoped to one `CredentialRecord`.
- **HPAC-REQ-063.** Effect on unconsumed approvals: revoking a principal or
  credential does not retroactively invalidate a `RuntimeInvocationApproval`
  already validated (RIHAC-001 v1.1 §14's identical disposition) — this is
  the same open question RIHAC-001 v1.1 §14 names, resolved identically in
  both contracts rather than left to silently diverge.
- **HPAC-REQ-064.** Effect on outstanding challenges: revoking a principal
  or credential SHALL invalidate every outstanding, unconsumed challenge
  issued to that principal — a revoked principal/credential SHALL NOT be
  able to complete an in-flight authentication after revocation, even if
  the challenge itself has not expired.
- **HPAC-REQ-065.** Credential loss/compromise recovery: revoke the
  compromised `credential_id`; enroll a replacement `CredentialRecord`
  under the same `principal_id` (identity persists across credential
  rotation, HPAC-REQ-009/HPAC-REQ-031). Recovery from total principal loss
  (e.g. sole enrolled principal unreachable) requires a repeat of the
  bootstrap ceremony (§7) — this contract does not invent a
  principal-recovery shortcut, since one would reopen the exact
  same-user-agent threat this contract exists to close.

## 22. Alternative and fallback mechanisms

Resolves governing-prompt items 52/53.

- **HPAC-REQ-066.** No automatic mechanism fallback exists in v1. If the
  primary mechanism (§14) is `unavailable` (§13), authentication SHALL
  fail closed — SHALL NOT silently substitute a weaker mechanism.
- **HPAC-REQ-067.** A gated software-key mechanism (`hpac.software_key.
  presence_gated.v1`, assurance `PRESENCE_GATED`, §20) MAY be configured as
  an explicit, deployment-selected alternative for environments lacking
  hardware-key access, provided it is gated behind an OS-level presence
  check (converging toward OS-authentication, 149O.20L.7O.3W.1R.2A §25/§26)
  — a bare on-disk software key with no additional gate SHALL NOT be
  registered as a conformant mechanism under this contract, because it
  does not resist §16's mandatory same-user-agent threat (RIHAC-001 v1.1
  §3).
- **HPAC-REQ-068.** Future alternative mechanisms (OS-authenticated
  presence, an external approval service, another hardware authenticator
  family) MAY be added as additional `HumanAuthenticator` implementations,
  provided each meets its declared assurance level honestly (§20) and the
  minimum-required-assurance gate (HPAC-REQ-060) is never lowered to
  accommodate a weaker mechanism.

## 23. Audit and privacy

Resolves governing-prompt items 58/59.

- **HPAC-REQ-069.** Every writer operation (enrollment, revocation) and
  every proof verification (success or failure) SHALL emit exactly one
  audit record recording: `principal_id`; mechanism/`credential_id`
  reference (not raw key material); challenge/nonce identifier (not the
  raw challenge, per HPAC-REQ-052's digest-not-raw discipline);
  verification result; timestamp; and verifier version. No PIN, private
  key, raw biometric template, or secret device state is ever recorded —
  identical discipline to HPSE-REQ-014/HHCE's existing rule, independently
  adopted here as the correct rule.
- **HPAC-REQ-070.** No unnecessary personal data is stored: `principal_id`
  (opaque), credential public material, and mechanism/status metadata are
  sufficient; no email, legal name, or biometric template is ever
  persisted in this contract's registry or audit trail (HPAC-REQ-010).

## 24. Replay and consumption

- **HPAC-REQ-071.** A durable, checked-under-lock record of consumed
  challenge/nonce values SHALL exist; §18 step 9 SHALL reject any proof
  whose challenge/nonce is already so recorded. Consumption is recorded
  atomically with successful verification (§18 step 10) — never before
  (which would burn a challenge on a failed attempt) and never after a
  window in which the same proof could be double-submitted.
- **HPAC-REQ-072.** A proof produced for invocation A's subject/preview
  digest SHALL fail verification (§18 step 5) if presented for invocation
  B's subject/preview digest, even under an otherwise-valid, unconsumed
  challenge — subject binding is checked independently of challenge/nonce
  consumption.

## 25. Failure behavior

- **HPAC-REQ-073.** Every failure path in §18 fails closed: no partial
  trust, no default-permissive outcome, no inference of authority from an
  earlier passing step when a later step fails.
- **HPAC-REQ-074.** Required authenticator unavailable (§13 `unavailable`)
  → no authenticated proof can be produced → RIHAC-001 v1.1 §12 condition 7
  cannot be satisfied → no `RuntimeInvocationApproval` can be trusted → no
  real dispatch. There is no fallback to a caller assertion under any
  unavailability condition (HPAC-REQ-066).

## 26. Session caching

Resolves governing-prompt item 63.

- **HPAC-REQ-075.** A successful enrollment (§8) establishes a durable
  *enrollment* state (who is enrolled) but SHALL NOT be treated as a
  cached *authentication* for any future approval. Each real invocation
  requires its own fresh challenge and its own fresh proof
  (HPAC-REQ-050/HPAC-REQ-071) — "authenticated once" in the enrollment
  sense never means "many one-shot approval acts are auto-authorized
  thereafter," matching the mandatory semantic wall (§0) `authenticated
  human principal != confirmation`.
- **HPAC-REQ-076.** No session-caching layer for authentication exists in
  v1. If a future implementation ever introduces one (e.g. a device-pairing
  state that reduces friction across a burst of approvals), it requires a
  separate governed contract amendment defining TTL, lock/logout boundary,
  invalidation-on-terminal-closure, invalidation-on-sleep, and
  invalidation-on-account-switch — not introduced by this contract.

## 27. Delegation and automated approval

- **HPAC-REQ-077.** No delegation exists in v1: a human principal MAY NOT
  delegate authentication authority to another human, an agent, or a
  policy. A delegated/forked agent (149O.20L.7O.3W.1R.2C's own incident,
  cited as a threat-model example, not a counter-example, by
  149O.20L.7O.3W.1R.2A §17) is never treated as, and can never become, an
  `AuthenticatedHumanPrincipal` under this contract.
- **HPAC-REQ-078.** No automated or policy-based auto-authentication exists
  in v1. Every authentication requires a live, fresh proof-production act
  (§16/§17) — silence, timeout, inactivity, or a default response SHALL
  NOT produce a valid proof.

## 28. Configuration authority and malicious-repository protection

Resolves governing-prompt items 69/70 explicitly.

- **HPAC-REQ-079.** A repository under agent control SHALL NOT be able to:
  enroll its own principal or credential (enrollment requires the
  out-of-repository admin writer, HPAC-REQ-024, and fresh election
  evidence, HPAC-REQ-028); alter `HumanPrincipalRegistry` (the registry
  path is outside repository control, HPAC-REQ-022); downgrade the
  required assurance level (HPAC-REQ-060 is contract-fixed, not
  repository-configurable); or silently select a weaker authentication
  mechanism (HPAC-REQ-066 forbids automatic fallback; mechanism selection
  is deployment-configured outside repository control).
- **HPAC-REQ-080.** Only the deployment/user-level admin, never repository
  configuration, MAY configure: the required authenticator mechanism, the
  registry location, and the enrolled-credential set. Repository
  configuration SHALL NOT be capable of lowering security below this
  contract's fixed minimums (HPAC-REQ-060/HPAC-REQ-066).

## 29. Multiple principals

- **HPAC-REQ-081.** v1 does not require support for more than one enrolled
  human principal (149O.20L.7O.3W.1R.2A §50's own recommendation, affirmed
  here as binding contract text). The registry schema (§5) does not
  preclude enrolling more than one principal later; no role/RBAC model is
  introduced in v1.

## 30. Offline capability and portability

- **HPAC-REQ-082.** The primary v1 mechanism (§14) SHALL function fully
  offline: no network call is required to produce or verify a proof.
  Registry lookups and challenge/proof verification are local-only
  operations.
- **HPAC-REQ-083.** No OS-specific adapter is required for the primary v1
  mechanism: FIDO2 CTAP2 hardware keys are portable across the development
  (macOS) and deployment (Linux) targets without a platform-specific
  presence API, resolving the dev/deploy portability question the
  governing prompt's items 46/57 raise, without building the dual-adapter
  surface an OS-authentication-primary mechanism would require.

## 31. HATP compatibility cross-check

Resolves governing-prompt item 49.

- **HPAC-REQ-084.** No conflict exists between this contract and HATP's
  existing credential-registry, principal-binding, provider-class, touch,
  challenge-replay, or signature-verification conventions: this contract
  reuses their *pattern* (§6) under an entirely separate registry,
  namespace, and challenge domain (§15), never their live state. A future
  implementation SHALL NOT allow an HPAC-001 verification to accept a HATP
  signing-ceremony assertion, or vice versa, by structural similarity
  alone (mirrors RIASC-001 §13's identical "no schema from another family
  accepted by structural similarity" discipline).

## 32. Existing FIDO2 implementation reuse map

Resolves governing-prompt item 50. No code is written by this contract;
this section names reusable production components conceptually only.

| Component | Existing location | Reuse role for HPAC-001 |
|---|---|---|
| Provider capability descriptor shape | `hatp_providers.py::HardwareProviderCapabilities` | Pattern reuse for §14's static descriptor |
| Provider allowlist discipline | `hatp_providers.py::_PRODUCTION_HARDWARE_PROVIDER_PROFILES` | Pattern reuse for a future closed `mechanism_id` allowlist |
| Credential-identity/verify shape | `hatp_fido2_provider.py::Fido2HardwareProvider` | Library-level primitive reuse only (HPAC-REQ-019); not a live HATP dependency |
| Atomic registry write idiom | `repository_identity.py::_write_atomic`, reused by `hatp_bootstrap.py`/`hatp_deployment_binding_admin.py` | Pattern reuse for §5's registry writes |
| Principal/signer schema shape | `hatp_bootstrap.PrincipalRecord`/`SignerRecord` | Pattern reuse for §5's `PrincipalRecord`/`CredentialRecord` (separate document, HPAC-REQ-018) |

## 33. Hardware-unavailable behavior

- **HPAC-REQ-085.** If the required FIDO2 authenticator is unavailable
  (§13 `unavailable`), no authenticated proof can be produced. This
  propagates, unmodified, through RIHAC-001 v1.1 and RDGO-001 gate 3/5: no
  real dispatch occurs. There is no fallback to a caller assertion under
  any unavailability condition — restated from HPAC-REQ-074 for emphasis
  at this contract's own hardware-specific boundary.

## 34. Same-user-agent resistance — verification obligation

Resolves governing-prompt item 60.

- **HPAC-REQ-086.** A future implementation and its independent
  verification SHALL affirmatively demonstrate that an autonomous agent
  process running under the same OS account as the enrolled human cannot,
  by any code path reachable from that process alone, produce a
  `HumanAuthenticationProof` that passes §18 verification, without the
  human physically performing the presence gesture (§14 UP requirement) at
  the moment of proof production. This is a normative future verification
  requirement, not evidence produced by this contract-only phase.

## 35. Delegated-agent isolation (explicit non-reliance)

- **HPAC-REQ-087.** This contract's authentication guarantee SHALL NOT rely
  on, assume, or be weakened by any future delegated-subagent
  capability-bounding mechanism (149O.20L.7O.3W.1R.2C's own named debt,
  restated at 149O.20L.7O.3W.1R.2A §70). "Not delegated" is never treated
  as proof of humanity anywhere in this contract; only a verified §18 proof
  is.

---

## 36. Non-goals and implementation boundary

This freeze does not add an executable schema package under
`src/pcae/schema_resources/**`, an enrollment CLI, a registry writer, a
`HumanAuthenticator` implementation, a PB field, Runtime Enforcement
integration, Shell Gate, adapter, process launch, credential access,
network capability, or execution availability. It does not modify
`src/pcae/core/runtime_authority.py`, `hatp_bootstrap.py`,
`hatp_fido2_provider.py`, `hatp_piv_provider.py`, RIHAC-001's or RIASC-001's
own text beyond the amendments this phase makes there, PBRD-001, RDGO-001,
RPAC-001, CHGR, Interactive Workflow, HATP-001, HPSE-001, HHCE-001, HMIC,
Class-B, CLTR, the dry adapter consumer, or POL-005.

## 37. Versioning

HPAC-001 uses contract `MAJOR.MINOR`, identical discipline to every other
contract in this family. Additive clarification or optional evidence may
increment MINOR only when it does not widen existing authority. A subject-
member removal, presence-gating relaxation, required-field removal,
semantic redefinition, minimum-assurance-level lowering, or trust weakening
is incompatible and requires a new MAJOR plus explicit migration and
independent verification. Unknown versions fail closed. No future version
may retrospectively widen an already-issued proof or an already-enrolled
principal's granted assurance.

## 38. Freeze verdict

**HPAC-001 v1.0: FROZEN.**
**`HumanAuthenticator` implementation: NOT BUILT / NOT AUTHORIZED.**
**`HumanPrincipalRegistry`: NOT CREATED.**
**Hardware: NOT TOUCHED.**
**Real execution: UNAVAILABLE.**
