# HPAC-001 v2.0 — Human Principal Authentication Contract

## Contract identity and status

**Contract:** HPAC-001
**Version:** 2.0
**Status:** FROZEN
**Frozen by:** Phase 149O.20L.7O.3W.1R.2B.1R.1 — Cross-Contract Runtime
Invocation Human-Principal Authentication Freeze Repair
**Supersedes:** HPAC-001 v1.0. V1 proof, registry, enrollment, assurance, and
presentation semantics are not authority-compatible with v2 and SHALL NOT be
silently upgraded.
**Depends on:** RIHAC-001 v2.0 (`RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md`,
this contract's consumer for runtime-invocation approval), RIASC-001 v3.0
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
credential authentication       != user presence
user presence                   != user verification
user verification               != informed approval intent
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
  (§8-§9); authentication-proof production and structure (§16-§17); trusted
  approval-presentation evidence (§16); proof verification behavior (§18);
  revocation (§21); mechanism status (§13); trust/assurance level (§20); and
  failure behavior (§25).
- **HPAC-REQ-003.** HPAC-001 SHALL NOT own, define, or gate: Permission
  Broker permission, runtime-target selection, execution capability, Runtime
  Enforcement, or dispatch. Those remain exclusively RIHAC-001/RIASC-001/
  PBRD-001/RDGO-001/RPAC-001 territory. This contract produces evidence
  consumed by RIHAC-001's validator (RIHAC-001 v2.0 §16
  step 4); it does not itself decide whether a `RuntimeInvocationApproval`
  is created, validated, or consumed.
- **HPAC-REQ-004.** This contract resolves finding **N2**
  (149O.20L.7O.3W.1R.1 §14, restated 149O.20L.7O.3W.1R.2 §4,
  re-derived verbatim in the required phase document's §3): the fact that
  `create_runtime_invocation_approval` accepted a caller-supplied
  `approver_id`/`identity_evidence_kind` pair with no independent
  verification. This contract makes that verification structurally
  required and independently checkable; it does not itself perform the
  verification (that remains RIHAC-001 v2.0 §16 step 4's job, consuming
  this contract's artifacts).

## 2. Terminology

- **Human principal.** An opaque PCAE identity represented by a stable
  `principal_id` (§4), categorically distinct from OS, Git, agent/session,
  producer, biological, civil, or legal identity. An **authenticated human
  principal** means only that an active credential enrolled to that ID met
  the required proof profile against current protected registry state.
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
- **TrustedApprovalPresentation.** Protected-channel evidence that a
  human-usable representation of PCAE-canonical repository, task, target,
  operation/effect, prompt/instruction, invocation, expiry, and one-shot facts
  was displayed and explicitly elected. Its component runs in the protected
  presentation context configured by HPAC-REQ-080; ordinary agent-controlled
  stdout/stdin and repository-authored labels cannot produce it.
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
  determination (RIHAC-001 v2.0 §12) — HPAC-001 verification is necessary,
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
- **HPAC-REQ-013.** The registry SHALL contain exactly two closed record
  kinds: `PrincipalRecord` (`principal_id`, `status`, `enrollment_provenance_ref`,
  `enrolled_at`, `revoked_at`) and `CredentialRecord` (`credential_id`,
  `principal_id`, `mechanism_id`, `public_key`, `assurance_capabilities`,
  `status`, `enrollment_provenance_ref`, `enrolled_at`, `revoked_at`). No
  private key, PIN, biometric secret, repository path, or display metadata is
  permitted. No third record kind exists in v2. This mirrors HPSE-001's
  `PrincipalRecord`/`SignerRecord` two-record
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
  rejected; the registry has no free-form extension container in v2.

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
- **HPAC-REQ-022.** Registry, proof-store, mechanism policy, assurance floor,
  and presentation-channel configuration SHALL resolve from one deployment-
  scoped protected root outside every repository. The root and every ancestor
  SHALL be owned and writable only by an OS/equivalent protected administration
  principal unavailable to ordinary same-user agent execution. Resolution
  SHALL reject symlinks, traversal, owner/ACL mismatch, replace/delete access,
  and repository, environment, cwd, task, or caller overrides. Location alone
  is never the trust basis.
- **HPAC-REQ-023.** First-principal bootstrap is anchored by an externally
  established deployment-owner administration principal, not by a prior PCAE
  principal and not by ordinary same-UID machine access. That protected
  principal SHALL launch a non-defaultable ceremony, display the exact
  registry identity and credential being enrolled through a protected
  presentation channel, require authenticator UP and UV, verify the FIDO2
  registration response, and atomically create the first records and durable
  provenance/audit entry. This explicit external OS/equivalent trust anchor
  terminates bootstrap without circular PCAE self-authorization.
- **HPAC-REQ-024.** Bootstrap/enrollment mutation SHALL be available only in
  the protected administration context and never as an ordinary `pcae` CLI,
  repository hook, task action, agent tool, stdin confirmation, environment
  toggle, or unattended workflow. A same-UID agent invocation SHALL be denied
  before credential registration or registry mutation.

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
- **HPAC-REQ-028.** Every enrollment, replacement, recovery, or revocation
  SHALL require protected-admin authorization plus a fresh, UV-required,
  non-defaultable human act over a protected presentation of the exact
  operation. The writer SHALL cryptographically verify the ceremony evidence
  before mutation and persist its canonical ID/digest as provenance. A
  reference-only record, boolean, free-form approval, or ordinary CLI input
  is insufficient.
- **HPAC-REQ-029.** No entity may enroll or expand its own authentication
  authority. The protected writer enforces this independently of caller
  claims, repository state, and target principal. Recovery after loss uses
  the external deployment-owner anchor in HPAC-REQ-023; it never lowers the
  ceremony or permits same-user-agent self-enrollment.

## 9. Credential ownership and multiplicity

- **HPAC-REQ-030.** Cardinality is exactly one principal → zero or more
  credentials; each `CredentialRecord` names exactly one `principal_id`.
  This contract explicitly permits multiple credentials per principal in
  v2 (governing-prompt item 35's "prefer simple but recoverable design" —
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

## 14. Primary v2 mechanism descriptor — hardware-backed FIDO2

Resolves governing-prompt items 12/33/54/55 (mechanism design, assurance
model, minimum required assurance).

- **HPAC-REQ-039.** `mechanism_id`: `hpac.fido2.uv_presence.v2`.
- **HPAC-REQ-040.** Static descriptor fields: `mechanism_id`; `assurance_level`
  (§20); `offline_capable` (`true`, §17 below); `presence_support` (`true`
  — UP, user-presence gesture, required); `verification_support`
  (`required` — UV, user-verification/biometric-or-PIN, is mandatory for the
  first real-runtime profile); `platform_compat`
  (`macos, linux` — CTAP2 hardware keys are OS-neutral, resolving
  governing-prompt items 46/57 without a platform-specific adapter).
- **HPAC-REQ-041.** Enrollment ceremony: reuses HPSE-REQ-059's already-frozen
  target semantics (a canonical, protocol-appropriate credential-minting
  ceremony producing a stable, durable credential-identity byte string) as
  a *pattern*, applied to this contract's own separate registry (§6) — not
  a live call into HATP's own enrollment writer.
- **HPAC-REQ-042 (UP/UV determination).** UP proves an active presence event
  at the enrolled authenticator; it does not identify which person acted or
  prove approval intent. UV proves authenticator-local user verification; it
  does not prove approval intent. For the first real-runtime profile both UP
  and UV are mandatory and form an immutable contract minimum. Deployment
  policy may require stronger assurance but neither repository nor protected
  administrator may lower this floor. UP-only proofs may be recorded as
  credential-presence evidence but SHALL NOT authorize real runtime and SHALL
  NOT yield `AuthenticatedHumanPrincipal`.
- **HPAC-REQ-043.** Challenge generation uses `HumanAuthenticator.
  prepare_challenge` (§10) over the exact versioned canonical approval-subject
  digest, exact trusted-presentation digest, fresh cryptographically random
  nonce, principal/credential binding, proof-schema version, and v2 domain
  separator (§16). The protected presentation channel SHALL display the same
  canonical facts before the non-defaultable approval act.
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

- **HPAC-REQ-047.** A challenge namespace tag,
  `pcae.hpac.runtime-invocation-approval.v2`,
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

- **HPAC-REQ-049.** Canonical challenge bytes SHALL encode exactly a closed
  object containing `domain_separator` const
  `pcae.hpac.runtime-invocation-approval.v2`, `challenge_version` const
  `HPAC-CHALLENGE/2.0`, `proof_schema_version` const `HPAC-PROOF/2.0`,
  `principal_id`, `credential_id`, `approval_subject_digest`,
  `trusted_presentation_digest`, `nonce`, `issued_at`, and `expires_at`.
  The subject digest covers repository identity, task ID, runtime target,
  operation/effect and scope, prompt/instruction identity, invocation ID,
  expiry, and one-shot status. UTF-8 compact JSON with recursively sorted
  keys and NFC strings is hashed with SHA-256. Any display, subject, domain,
  principal, credential, or version mismatch invalidates the proof.
- **HPAC-REQ-050.** Nonce origin: cryptographically strong random bytes,
  generated by the trusted challenge-construction component (never the
  authenticator, adapter, or caller). Uniqueness: SHALL NOT repeat across
  any two challenges ever issued for the same or different principals.
  Lifetime: a challenge SHALL expire if unconsumed within a short,
  separately-governed bound (not frozen numerically here — a future
  implementation phase sets it, consistent with RIHAC-001's own precedent
  of not freezing an arbitrary duration for `expires_at`, RIHAC-001 §14).
  Storage: the trusted coordinator records lifecycle state in the protected
  proof store. Successful verification binds the nonce/proof to exactly one
  approval without consuming it. Consumption occurs only atomically with the
  gate-9 approval consumption marker (§24).
- **HPAC-REQ-051.** No predictable, sequential, timestamp-only, or reusable
  challenge value is permitted.

## 17. Authentication proof — normalized structure

Resolves governing-prompt item 18.

- **HPAC-REQ-052.** `HumanAuthenticationProof` has schema identity
  `HPAC-PROOF/2.0` and exactly these closed fields: `proof_schema_version`,
  `proof_id` (`hap-<32-hex>`), `proof_digest`, `mechanism_id`, `principal_id`,
  `credential_id`, `challenge_digest`, `approval_subject_digest`,
  `trusted_presentation_ref` (exact `presentation_id`/`presentation_digest`
  pair), `assertion` (base64url mechanism bytes), `up` (const true), `uv`
  (const true), `authenticated_at`, and `verifier_version`. `proof_digest`
  is SHA-256 over canonical UTF-8 compact JSON excluding only itself, with
  recursively sorted keys and NFC strings. Unknown/missing fields fail
  closed. No secret, PIN, private key, raw challenge, or biometric template
  is included.
- **HPAC-REQ-053.** Canonical proof storage is the protected deployment path
  `<HPAC_PROTECTED_ROOT>/proofs/v2/<proof_id>/proof.json`; callers supply only
  the exact closed reference `(proof_id, proof_digest)`, never a path.
  Resolution rejects traversal, symlinks, duplicate IDs, non-canonical bytes,
  digest mismatch, wrong owner/ACL, repository/config override, and missing
  lifecycle state. The adjacent protected lifecycle record has exactly
  `CHALLENGE_CREATED`, `ASSERTION_RECEIVED`, `PROOF_VERIFIED_AND_BOUND`,
  `PROOF_CONSUMED_WITH_APPROVAL`, or terminal `EXPIRED`, `REVOKED`,
  `REJECTED`. Proof and lifecycle writes are atomic, create/append-only, and
  read-back verified.

## 18. Proof verification — exact sequence

Resolves governing-prompt item 19, consumed by RIHAC-001 v2.0 §16 step 4.

- **HPAC-REQ-054.** Verification SHALL execute in this fail-closed order:
  1. resolve `principal_id` in `HumanPrincipalRegistry`; reject if missing
     or not `active`;
  2. resolve `credential_id` under that principal; reject if missing, not
     bound to this `principal_id`, or not `active`;
  3. resolve `mechanism_id`; reject if unknown or below the minimum
     required assurance level (§20);
  4. recompute `challenge_digest` from the exact challenge state and
     compare; reject on mismatch;
  5. verify subject and informed-intent binding: the challenge's canonical
     subject digest equals the approval subject/scope/expiry, and the
     `trusted_presentation_ref` resolves in the protected presentation store
     to evidence that the identical canonical facts were displayed through a
     channel the requesting agent could not substitute; reject ordinary
     agent-controlled stdout/stdin, missing explicit election, blind touch,
     or any display/challenge mismatch;
  6. verify `assertion` against the resolved credential's public
     verification material; reject on signature/assertion failure;
  7. verify both UP and UV flags are true for real-runtime authority; reject
     UP-only, UV-only, or policy/config downgrade;
  8. verify freshness: `authenticated_at` is recent relative to a trusted
     clock and the challenge has not expired (§16); reject if stale;
  9. verify protected lifecycle state is either fresh or already
     `PROOF_VERIFIED_AND_BOUND` to this exact same approval and bytes; reject
     cross-binding, expired/revoked state, or consumed replay; and
  10. atomically transition fresh proof state to `PROOF_VERIFIED_AND_BOUND`
      for this approval and emit an ephemeral immutable
      `AuthenticatedHumanPrincipal` binding IDs, assurance, subject, and
      presentation digest (§19). Same-binding revalidation is idempotent and
      does not consume the nonce/proof.
- **HPAC-REQ-055.** No later step runs as a shortcut when an earlier step
  fails. Verification evidence is not itself PB permission, Runtime
  Enforcement approval, or a `RuntimeInvocationApproval` — it is the
  evidence RIHAC-001 v2.0 §16 step 4 consumes to decide whether one may be
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
- **HPAC-REQ-058.** Serialization boundary: `AuthenticatedHumanPrincipal` is
  ephemeral and non-serializable; only the canonical proof/lifecycle evidence
  may persist. Deserializing stored proof material SHALL NOT by itself yield
  trusted `AuthenticatedHumanPrincipal` state — every
  consumption SHALL re-run §18's verification sequence against current
  registry state (principal/credential status may have changed since the
  proof was stored) rather than trusting a cached verification result.

## 20. Assurance level model

Resolves governing-prompt items 54/55.

- **HPAC-REQ-059.** Closed assurance vocabulary is `ASSERTED`,
  `CREDENTIAL_PRESENCE` (valid enrolled credential plus UP), and
  `PRINCIPAL_VERIFIED_INTENT` (valid enrolled credential plus UP plus UV plus
  protected subject-bound presentation/election). Each property is verified
  independently; none silently implies another.
- **HPAC-REQ-060.** The immutable minimum for first real local-CLI dispatch
  is `PRINCIPAL_VERIFIED_INTENT`. `ASSERTED` and `CREDENTIAL_PRESENCE` never
  qualify. Required mechanism unavailable means approval unavailable; there
  is no downgrade. This closes N2 at the contract layer because caller IDs,
  references, booleans, or plausible proof-shaped bytes cannot satisfy the
  protected-root, cryptographic, current-state, and presentation conjunction.

## 21. Revocation and recovery

Resolves governing-prompt items 37/38.

- **HPAC-REQ-061.** Principal revocation: monotonic — the first-recorded
  revocation is authoritative; a later revocation of an already-revoked
  principal is an idempotent no-op, mirroring HPSE-REQ-006's identical
  discipline.
- **HPAC-REQ-062.** Credential revocation: identical monotonic discipline,
  scoped to one `CredentialRecord`.
- **HPAC-REQ-063.** Principal or credential revocation immediately marks all
  its unused challenges, verified/bound proofs, unmaterialized approvals,
  unconsumed approvals, and derived PB authority projections invalid. Gate 5
  and every pre-gate-9 revalidation SHALL re-resolve current protected
  registry state; stale cached principal state never qualifies. Only an
  approval/proof already atomically consumed at gate 9 remains historical
  evidence, never reusable authority.
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

- **HPAC-REQ-066.** No automatic mechanism fallback exists in v2. If the
  primary mechanism (§14) is `unavailable` (§13), authentication SHALL
  fail closed — SHALL NOT silently substitute a weaker mechanism.
- **HPAC-REQ-067.** No software-key or UP-only alternative qualifies for the
  first real-runtime profile. A future alternative requires a new governed
  HPAC version and must independently provide protected-root enrollment,
  UP-equivalent presence, UV-equivalent principal verification, protected
  subject presentation, and exact challenge binding. A bare on-disk key,
  OS username, normal same-UID UI, or ordinary CLI confirmation never
  qualifies.
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

- **HPAC-REQ-071.** Protected lifecycle state SHALL reject any proof consumed
  with another approval or dispatch. Gate-5 verification binds but does not
  consume. Gate 9 atomically writes the durable `dispatch_attempted` marker,
  consumes the canonical approval, and transitions the bound HPAC proof to
  `PROOF_CONSUMED_WITH_APPROVAL`. Revalidation before gate 9 repeats canonical
  byte/digest/signature/domain/presentation/current-registry checks against
  the same binding without a second consumption attempt.
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
  → no authenticated proof can be produced → RIHAC-001 v2.0 §12 condition 7
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
  v2. If a future implementation ever introduces one (e.g. a device-pairing
  state that reduces friction across a burst of approvals), it requires a
  separate governed contract amendment defining TTL, lock/logout boundary,
  invalidation-on-terminal-closure, invalidation-on-sleep, and
  invalidation-on-account-switch — not introduced by this contract.

## 27. Delegation and automated approval

- **HPAC-REQ-077.** No delegation exists in v2: a human principal MAY NOT
  delegate authentication authority to another human, an agent, or a
  policy. A delegated/forked agent (149O.20L.7O.3W.1R.2C's own incident,
  cited as a threat-model example, not a counter-example, by
  149O.20L.7O.3W.1R.2A §17) is never treated as, and can never become, an
  `AuthenticatedHumanPrincipal` under this contract.
- **HPAC-REQ-078.** No automated or policy-based auto-authentication exists
  in v2. Every authentication requires a live, fresh proof-production act
  (§16/§17) — silence, timeout, inactivity, or a default response SHALL
  NOT produce a valid proof.

## 28. Configuration authority and malicious-repository protection

Resolves governing-prompt items 69/70 explicitly.

- **HPAC-REQ-079.** Repository/task/agent-controlled state SHALL NOT select,
  redirect, replace, delete, or write the registry/proof/presentation stores;
  enroll or map principals/credentials; set mechanism allowlists; lower UP,
  UV, assurance, freshness, or presentation requirements; or supply trusted
  human-visible labels. Any influence or protected-root validation failure
  invalidates the ceremony and yields no authority.
- **HPAC-REQ-080.** Only the external protected deployment administration
  principal may configure registry/proof paths, credential mapping, enabled
  mechanisms, assurance/UV floor, and presentation channel. Immutable v2
  minima cannot be lowered even by that administrator. Configuration is
  resolved independently of repository, cwd, environment, task, caller, and
  ordinary same-UID process state.

## 29. Multiple principals

- **HPAC-REQ-081.** v2 does not require support for more than one enrolled
  human principal (149O.20L.7O.3W.1R.2A §50's own recommendation, affirmed
  here as binding contract text). The registry schema (§5) does not
  preclude enrolling more than one principal later; no role/RBAC model is
  introduced in v2.

## 30. Offline capability and portability

- **HPAC-REQ-082.** The primary v2 mechanism (§14) SHALL function fully
  offline: no network call is required to produce or verify a proof.
  Registry lookups and challenge/proof verification are local-only
  operations.
- **HPAC-REQ-083.** No OS-specific adapter is required for the primary v2
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
  propagates, unmodified, through RIHAC-001 v2.0 and RDGO-001 gate 3/5: no
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
  human performing required UP, UV, and explicit election after a protected
  presentation of the exact canonical subject. Verification SHALL prove
  `WHAT HUMAN WAS SHOWN == WHAT HUMAN AUTHENTICATED == WHAT PCAE AUTHORIZES`
  at the canonical semantic level. This is a normative future verification
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
  own text beyond the amendments this phase makes there, RPAC-001, CHGR,
  Interactive Workflow, HATP-001, HPSE-001, HHCE-001, HMIC,
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

**HPAC-001 v2.0: FROZEN; supersedes v1.0 with no authority migration.**
**`HumanAuthenticator` implementation: NOT BUILT / NOT AUTHORIZED.**
**`HumanPrincipalRegistry`: NOT CREATED.**
**Hardware: NOT TOUCHED.**
**Real execution: UNAVAILABLE.**
