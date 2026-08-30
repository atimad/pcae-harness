# HPAC-001 v2.1 — Human Principal Authentication Contract

## Contract identity and status

**Contract:** HPAC-001
**Version:** 2.1
**Status:** FROZEN
**Frozen by:** Phase 149O.20L.7O.3W.1R.2B.1R.1 — Cross-Contract Runtime
Invocation Human-Principal Authentication Freeze Repair
**Correctively completed by:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R —
Trusted Approval Presentation Evidence and HPAC Proof-Lifecycle
Canonicalization Blocking Repair. This completion retains v2.0 for the
reason frozen in §38: it defines previously absent companion records without
changing the challenge or proof wire schemas and without making any v2.0
artifact newly authority-valid by migration.
**Normalized to v2.1 by:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 —
Runtime-Dispatch Contract Normalization Implementation. **v2.1 is a MINOR
addition of optional verification evidence** (§37): §41's
`RuntimeInvocationAuthorityConsumption` evolves to schema
`HPAC-AUTHORITY-CONSUMPTION/2.1` with one additional closed binding object,
`authority_generation_binding` (the new `HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0`),
durably committing the monotonic authority-generation snapshot gate 9
verified unchanged immediately before the create-only linearization
(finding V-15-1; RDGO-001 v3.1 §10). It grants **no** authority — it is
historical/verification evidence that a future gate 10 re-reads and
compares against current canonical state. The challenge, proof, principal,
credential, presentation, lifecycle-event, and pre-existing consumption
binding schemas are byte-unchanged; a `/2.0` consumption record is
readable historical/test data (gate-10-ineligible). See HPAC-REQ-098,
HPAC-REQ-098a, HPAC-REQ-099, and §37.
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
  approval-presentation evidence (§38-§39); proof verification behavior
  (§18); canonical proof lifecycle and authority consumption (§40-§42);
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
- **TrustedApprovalPresentationEvidence.** The canonical, protected-store
  artifact defined by §39. It records and attests that a
  human-usable representation of PCAE-canonical repository, task, target,
  operation/effect, prompt/instruction, invocation, expiry, and one-shot facts
  was displayed and explicitly elected. Its component runs in the protected
  presentation context configured by HPAC-REQ-080; ordinary agent-controlled
  stdout/stdin and repository-authored labels cannot produce it. An
  evidence-shaped caller object is not this trusted artifact.
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
  digest (§38), exact trusted-presentation-evidence digest (§39), fresh cryptographically random
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
  `approval_subject_digest` is the digest of the exact
  `CanonicalRuntimeApprovalSubject` in §38; `trusted_presentation_digest` is
  the digest of the exact `TrustedApprovalPresentationEvidence` in §39.
  UTF-8 compact JSON with recursively sorted
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
  proof store exactly as §40 specifies. Successful verification binds the
  nonce/proof to exactly one approval without consuming it. Consumption
  occurs only through §41's single gate-9 authority-consumption record.
- **HPAC-REQ-051.** No predictable, sequential, timestamp-only, or reusable
  challenge value is permitted.

## 17. Authentication proof — normalized structure

Resolves governing-prompt item 18.

- **HPAC-REQ-052.** `HumanAuthenticationProof` has schema identity
  `HPAC-PROOF/2.0` and exactly these closed fields: `proof_schema_version`,
  `proof_id` (`hap-<32-hex>`), `proof_digest`, `mechanism_id`, `principal_id`,
  `credential_id`, `challenge_digest`, `approval_subject_digest`,
  `trusted_presentation_ref` (exact `presentation_id`/`presentation_digest`
  pair resolving only under §39), `assertion` (base64url mechanism bytes), `up` (const true), `uv`
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
  lifecycle state. The adjacent protected lifecycle consists only of the
  canonical event records and derived consumption state frozen in §40-§41;
  a state name, mutable flag, or caller-supplied lifecycle object is
  insufficient. Proof and lifecycle-event writes are atomic, create-only,
  and read-back verified.

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
     `trusted_presentation_ref` resolves by §39's canonical path and exact
     schema to evidence whose mechanism descriptor and attestation verify
     that the identical canonical facts were displayed through a channel the
     requesting agent could not substitute; reject caller-created lookalikes, ordinary
     agent-controlled stdout/stdin, missing explicit election, blind touch,
     or any display/challenge mismatch;
  6. verify `assertion` against the resolved credential's public
     verification material; reject on signature/assertion failure;
  7. verify both UP and UV flags are true for real-runtime authority; reject
     UP-only, UV-only, or policy/config downgrade;
  8. verify freshness: `authenticated_at` is recent relative to a trusted
     clock and the challenge has not expired (§16); reject if stale;
  9. resolve §40's complete hash-chained lifecycle and §41's canonical
     consumption path; verify state is either fresh or already
     `PROOF_VERIFIED_AND_BOUND` to this exact same approval, presentation,
     challenge, subject, attempt, proof, and approval bytes; reject
     cross-binding, expired/revoked state, or consumed replay; and
  10. atomically create §40's `PROOF_VERIFIED_AND_BOUND` event for this
      approval, or accept an already-present byte-identical same-binding event
      idempotently, and emit an ephemeral immutable
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
  consumption SHALL re-run §18's verification sequence, including canonical
  §39-§41 resolution, against current
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
  and gate 9 SHALL re-resolve current protected registry, presentation,
  proof, and lifecycle state inside §41's protected compare-and-create
  boundary; stale cached principal state never qualifies. Only an
  approval/proof already atomically consumed by §41's record remains historical
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
  consume. Gate 9 atomically creates the single canonical
  `RuntimeInvocationAuthorityConsumption` record defined by §41; its
  existence simultaneously constitutes the durable `dispatch_attempted`
  marker and consumption of the canonical approval, presentation evidence,
  and bound HPAC proof. Revalidation at gate 9 repeats canonical
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
  redirect, replace, delete, or write the registry/proof/presentation/
  consumption stores or their mechanism descriptors;
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

**v2.1 (Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4) — MINOR.** v2.1 adds one
closed binding object (`authority_generation_binding`, schema
`HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0`) to the §41
`HPAC-AUTHORITY-CONSUMPTION` record, bumping it to `/2.1`. It **widens no
authority**: the object is verification evidence a future gate 10 re-reads
and compares against current canonical state — it carries no capability
field, grants nothing on possession, and does not make any previously
invalid consumption newly valid. No field is removed or re-typed; no
existing binding object changes; the challenge/proof/principal/credential/
presentation/lifecycle schemas are byte-unchanged. A `/2.0` record without
the new object remains readable historical/test data and is
gate-10-ineligible. This meets the MINOR bar.

## 38. Corrective version treatment and canonical approval subject

- **HPAC-REQ-088.** This phase is a corrective completion of the
  independently rejected HPAC-001 v2.0 candidate, not a successor authority
  model. It adds the first canonical definitions of companion presentation,
  lifecycle, and consumption records already required by HPAC-REQ-043,
  HPAC-REQ-053, HPAC-REQ-054, and HPAC-REQ-071. It does not change
  `HPAC-CHALLENGE/2.0`, `HPAC-PROOF/2.0`, the challenge domain, the proof
  field set, the UP+UV floor, or any previously valid authority meaning.
  Because no v2.0 presentation/lifecycle record could conform to a schema
  that did not exist, there is no valid old artifact to migrate or silently
  upgrade. Retaining contract version 2.0 is therefore a correction of the
  same unverified freeze, not backward-compatible acceptance of incomplete
  evidence. Any implementation of the pre-correction prose is non-conformant.

- **HPAC-REQ-089.** `CanonicalRuntimeApprovalSubject` has schema identity
  `HPAC-APPROVAL-SUBJECT/2.0` and exactly these closed fields:
  `subject_schema_version` (const `HPAC-APPROVAL-SUBJECT/2.0`), `subject`
  (the exact closed five-field RIASC-001 v3.0 `subject` object),
  `approval_scope` (the exact closed RIASC-001 v3.0 `approval_scope`
  object), `approval_preview_digest` (64 lowercase hex), `expires_at`
  (RIASC-001 timestamp grammar), and `attempt_limit` (const `1`). Its
  canonical bytes are UTF-8 compact JSON with NFC strings and recursively
  ASCII-sorted object keys; arrays retain order. `approval_subject_digest`
  is SHA-256 of those exact bytes. No caller-selected label, filesystem path,
  display-only text, or mechanism evidence is part of this subject.

This exact object resolves the former prose-only phrase “repository, task,
target, operation/effect/scope, prompt, invocation, expiry, and one-shot”:
repository/task/target/prompt/invocation are the five `subject` members;
operation/effect/scope is `approval_scope`; expiry and one-shot are the final
two fields. Any field or byte mismatch creates a different subject.

## 39. Canonical trusted approval-presentation evidence

### 39.1 Trusted presentation mechanism descriptor

- **HPAC-REQ-090.** A presentation mechanism qualifies only through one
  protected, administrator-installed `TrustedApprovalPresentationMechanism`
  descriptor at
  `<HPAC_PROTECTED_ROOT>/presentation-mechanisms/v2/<mechanism_id>/descriptor.json`.
  The descriptor has schema identity `HPAC-PRESENTATION-MECHANISM/2.0` and
  exactly these closed fields: `descriptor_schema_version` (const),
  `mechanism_id` (non-empty ID), `descriptor_version` (non-empty ID),
  `descriptor_digest` (self-excluding SHA-256), `verifier_kind` (non-empty
  closed implementation identifier), `verifier_configuration_digest`
  (SHA-256 of protected verifier configuration), `renderer_profile`
  (non-empty versioned deterministic-renderer identifier), `protected_output` (const
  `true`), `agent_substitution_resistant` (const `true`),
  `canonical_subject_rendering` (const `true`), `explicit_election_support`
  (const `true`), and `status` (enum `active`, `revoked`). Descriptor bytes
  use HPAC-REQ-089 canonicalization. Only HPAC-REQ-080's protected
  administrator may create or revoke descriptors. Repository, task, agent,
  cwd, environment, stdin, or caller state cannot install, select, redirect,
  or weaken one. Ordinary terminal stdout/stdin cannot truthfully satisfy
  `agent_substitution_resistant` and is ineligible.

### 39.2 Evidence schema

- **HPAC-REQ-091.** `TrustedApprovalPresentationEvidence` has schema
  identity `HPAC-PRESENTATION-EVIDENCE/2.0`, ID grammar
  `hpe-<32-lowercase-hex>`, and exactly these closed top-level fields:

| Field | Exact type / meaning |
|---|---|
| `presentation_schema_version` | const `HPAC-PRESENTATION-EVIDENCE/2.0` |
| `presentation_id` | `^hpe-[0-9a-f]{32}$`, allocated by the protected presentation component |
| `presentation_digest` | SHA-256 over canonical evidence bytes excluding only this field |
| `approval_id` | reserved trusted-coordinator `^ria-[0-9a-f]{32}$` identity |
| `canonical_subject` | exact HPAC-REQ-089 object |
| `approval_subject_digest` | SHA-256 of `canonical_subject` bytes |
| `mechanism_ref` | closed `mechanism_id` / `descriptor_version` / `descriptor_digest` triple |
| `human_visible_facts` | exact closed object in the table below |
| `human_visible_representation_digest` | SHA-256 of the exact normalized bytes the protected mechanism displayed |
| `presented_at` | trusted-clock UTC RFC 3339 timestamp |
| `election` | closed `event_id`, `action`, `occurred_at` object; `event_id` matches `^hpevt-[0-9a-f]{32}$`, `action` is const `approve`, and `occurred_at >= presented_at` |
| `mechanism_attestation` | non-empty base64url mechanism evidence bytes |
| `mechanism_attestation_digest` | SHA-256 of decoded mechanism evidence bytes |

`human_visible_facts` contains exactly:

| Field | Canonical source / display rule |
|---|---|
| `repository_identity` | exact subject digest value; human-visible |
| `repository_display` | protected resolver's human-usable repository label plus recognizable fingerprint; raw digest alone forbidden |
| `task_id` | exact subject value; human-visible |
| `task_display` | protected resolver's human-usable active-task label plus `task_id` |
| `runtime_target_id` | exact subject value; human-visible |
| `runtime_target_display` | protected descriptor's human-usable target label plus exact ID |
| `operation_effect_scope_display` | protected rendering of the complete canonical `approval_scope`, including requested capability, local transport, effect class, filesystem/process references, no-network fact, and one-dispatch limit |
| `prompt_hash` | exact subject value |
| `prompt_instruction_display` | protected rendering of prompt/instruction identity plus a recognizable fingerprint; opaque digest alone forbidden |
| `invocation_id` | exact subject value; human-visible |
| `invocation_display` | human-usable invocation label plus recognizable fingerprint |
| `expires_at` | exact canonical subject expiry; human-visible |
| `one_shot_notice` | const `true`, rendered as a human-usable one-attempt notice |

- **HPAC-REQ-092.** Evidence canonicalization is HPAC-REQ-089's rule.
  Before `presentation_digest` is computed, only `presentation_digest` is
  omitted; no attestation or other field is omitted. The registered
  mechanism verifies `mechanism_attestation` over exactly one closed object
  containing `attestation_version` (const
  `HPAC-PRESENTATION-ATTESTATION/2.0`), `presentation_id`, `approval_id`,
  `approval_subject_digest`, `human_visible_representation_digest`,
  `descriptor_digest`, the complete closed `election` object, and
  `presented_at`; no other or omitted field is permitted. That object's
  bytes use HPAC-REQ-089 canonicalization and protected verification
  configuration selected by the resolved descriptor. Digest agreement
  without successful attestation verification is non-authority. The
  descriptor's `renderer_profile` deterministically renders only the closed
  `human_visible_facts` into the actual protected display. Display bytes are
  UTF-8 with NFC strings and LF line endings; no hidden, caller-supplied, or
  non-attested authority text is permitted. The protected component hashes
  those exact displayed bytes as `human_visible_representation_digest`; a
  resolver rerenders the same facts under the exact descriptor version and
  requires byte/digest equality. The `canonical_subject`'s
  `approval_preview_digest` SHALL equal this exact
  `human_visible_representation_digest`; inequality fails closed. Thus the
  attested digest identifies what was
  actually shown, not merely an abstract data object. The
  requesting caller may request a ceremony but only the protected mechanism
  may allocate the ID, render canonical facts, observe explicit election,
  produce the attestation, and persist the evidence.

### 39.3 Store, resolution, correlation, and state

- **HPAC-REQ-093.** Canonical evidence storage is exactly
  `<HPAC_PROTECTED_ROOT>/presentations/v2/<presentation_id>/presentation.json`.
  The file is immutable, create-only, atomically written, read-back verified,
  and resolved only by the closed `(presentation_id, presentation_digest)`
  pair. Resolution revalidates protected root/ancestor ownership and ACL,
  canonical bytes/digest, the active descriptor and protected verifier
  configuration, mechanism attestation, canonical-subject equality, human-
  visible-fact equality, election ordering, and current expiry. Symlink,
  traversal, duplicate ID, caller path, repository override, corruption,
  descriptor revocation, missing attestation, or mismatch fails closed.
  A valid evidence record is intrinsically `PRESENTED`; its later
  `BOUND_TO_CHALLENGE` and `USED` states are derived only from the canonical
  proof lifecycle and consumption records in §40-§41. `EXPIRED` or
  `INVALIDATED` is derived from trusted time, descriptor status, protected
  configuration, or linked trust-state invalidation. No mutable status flag
  is trusted. A presentation for invocation A cannot bind invocation B
  because approval ID, exact canonical subject, and digest are present in
  both the attestation and the later challenge/lifecycle chain.

Valid FIDO2 signature, UP, and UV without a successfully resolved
HPAC-REQ-091 evidence artifact is a blind touch and SHALL NOT satisfy
`PRINCIPAL_VERIFIED_INTENT`.

## 40. Canonical proof lifecycle

### 40.1 Record form and path

- **HPAC-REQ-094.** The proof lifecycle is a hash-chained sequence of
  immutable `HumanAuthenticationProofLifecycleEvent` files, not a mutable
  state flag. Event schema identity is `HPAC-PROOF-LIFECYCLE-EVENT/2.0`.
  Canonical path is
  `<HPAC_PROTECTED_ROOT>/proofs/v2/<proof_id>/lifecycle/<sequence-four-digits>.json`,
  beginning at `0000.json`. Each event is atomically create-only and
  read-back verified. The resolver rejects gaps, duplicate sequences,
  forks, unknown files/states, non-canonical bytes, broken hash links,
  ownership/ACL/path failure, or any binding-field drift.

- **HPAC-REQ-095.** Every lifecycle event has exactly these closed fields:
  `lifecycle_schema_version` (const
  `HPAC-PROOF-LIFECYCLE-EVENT/2.0`), `event_id`
  (`^hpl-[0-9a-f]{32}$`), `event_digest` (self-excluding SHA-256),
  `sequence` (non-negative integer), `previous_event_digest` (null only at
  sequence 0, otherwise the prior event digest), `proof_id`, `state`,
  `occurred_at`, `binding`, `assertion_digest`, `proof_digest`,
  `approval_digest`, `registry_state_digest`, `verifier_version`, and
  `terminal_reason_code`. `binding` is a closed object containing exactly
  `approval_id`, `invocation_id`, `attempt_id`, `principal_id`,
  `credential_id`, `mechanism_id`, `approval_subject_digest`,
  `trusted_presentation_ref` (ID/digest pair), and `challenge_digest`.
  `state` is exactly one of `CHALLENGE_CREATED`, `ASSERTION_RECEIVED`,
  `PROOF_VERIFIED`, `PROOF_VERIFIED_AND_BOUND`, `EXPIRED`, `REVOKED`, or
  `REJECTED`. `assertion_digest`, `proof_digest`, `approval_digest`, and
  `registry_state_digest` are either null or 64 lowercase hex exactly as the
  state table requires; `verifier_version` and `terminal_reason_code` are
  either null or non-empty IDs under the same state rules. All other
  IDs/digests use their owning contract grammars. Event bytes use
  HPAC-REQ-089 canonicalization. Every event repeats the sequence-0 `binding`
  byte-for-byte; a drifted repeat is a fork and fails closed.

The non-terminal sequence is exact:

| Sequence/state | Entry condition | Required non-null evidence | Exit condition | Reusable? |
|---:|---|---|---|---|
| `0 CHALLENGE_CREATED` | presentation resolved/attested; trusted coordinator allocates `proof_id` and creates exact challenge | none of assertion/proof/approval/registry/verifier fields | one assertion received or terminal state | challenge once only |
| `1 ASSERTION_RECEIVED` | assertion challenge digest matches sequence 0 | `assertion_digest` | preliminary full proof verification or terminal state | no |
| `2 PROOF_VERIFIED` | signature, subject, presentation, UP, UV, freshness, domain, registry, and assertion verify for approval creation | `assertion_digest`, `proof_digest`, `registry_state_digest`, `verifier_version`; `approval_digest` null | immutable RIASC approval created, then gate 5 | no |
| `3 PROOF_VERIFIED_AND_BOUND` | gate 5 revalidates canonical proof and approval and binds exact same bytes | all evidence fields non-null | gate 9 consumption or terminal state | same-binding revalidation only; no authority transfer |

`terminal_reason_code` is null for non-terminal states. A terminal
`EXPIRED`, `REVOKED`, or `REJECTED` event is the next sequence and requires
all evidence available at that point plus a non-empty closed reason code;
no later lifecycle event is permitted. Independently current trusted time or
registry/descriptor state yields terminal invalidity even before an event can
be persisted; failure to record the observation never preserves authority.

- **HPAC-REQ-096.** `proof_id` is allocated by the trusted challenge
  coordinator before sequence 0. An unverified response is transient
  mechanism input and may produce only `ASSERTION_RECEIVED`; it is not a
  `HumanAuthenticationProof`. The canonical `proof.json` is created only
  after the sequence-2 verification succeeds, and its `assertion` bytes must
  hash to `assertion_digest`. A raw assertion, proof-shaped caller object,
  copied lifecycle file, state string, or plausible reference is
  non-authority until the complete protected chain resolves and verifies.

### 40.2 Gate-5 binding

- **HPAC-REQ-097.** Gate 5 reruns HPAC-REQ-054 against current registry,
  descriptor/configuration, presentation, challenge, proof, approval,
  freshness, revocation, and consumption state. Success atomically creates
  sequence 3 with the exact final `approval_digest`. If a byte-identical
  sequence-3 event already exists, same-binding revalidation is idempotent
  after all current checks rerun; no event is rewritten and no authority is
  consumed. **Cross-reference (RDGO-001 v3.1 §4 — V-2):** in the verified
  runtime-dispatch flow the sequence-3 event is created by the **first**
  HPAC-REQ-054 run — the verifier's assurance-independent step 10 at gate 3
  (approval creation) time — so gate 5's rerun takes the idempotent-accept
  path and its coordinator performs a read-only re-confirmation. HPAC-REQ-054
  step 10's "atomically create … or accept an already-present byte-identical
  same-binding event idempotently" wording already covers both; RDGO-001
  v3.1 narration is aligned to this. A different approval digest, proof digest, presentation,
  challenge, subject, invocation, attempt, principal, credential, or
  mechanism is cross-binding and fails closed. Gate 5 emits only an
  ephemeral `AuthenticatedHumanPrincipal` and RIHAC projection; persisted
  event shape alone does not recreate either trusted result.

## 41. Gate-9 atomic authority consumption

- **HPAC-REQ-098.** The one canonical consumption artifact is
  `RuntimeInvocationAuthorityConsumption`, schema identity
  `HPAC-AUTHORITY-CONSUMPTION/2.1` (v2.1; `/2.0` records without
  `authority_generation_binding` remain readable historical/test data and
  are gate-10-ineligible — RDGO-001 v3.1 §10 — but gate 9 writes only
  `/2.1`), stored exactly at
  `<HPAC_PROTECTED_ROOT>/proofs/v2/<proof_id>/consumption.json`. It has
  exactly these closed top-level fields: `consumption_schema_version`
  (const), `record_digest` (self-excluding SHA-256), `request_identity`,
  `repository_task_binding`, `target_binding`, `prompt_binding`,
  `authority_binding`, `authority_generation_binding`, `pb_binding`,
  `runtime_enforcement_binding`, and `dispatch_binding`.

The nine closed binding objects contain exactly (v2.1 — `authority_generation_binding`
added; the eight `/2.0` objects and the closed 12-field `authority_binding`
are byte-unchanged):

| Object | Exact fields |
|---|---|
| `request_identity` | `invocation_id`, `attempt_id`, `idempotency_key` |
| `repository_task_binding` | `repository_identity`, `head_commit`, `task_id`, `task_contract_digest`, `phase_id`, `session_id` (string or null only when not session-scoped) |
| `target_binding` | `runtime_target_id`, `adapter_id`, `descriptor_version`, `descriptor_digest`, `target_config_digest`, `executable_identity_digest` |
| `prompt_binding` | `prompt_hash`, `prompt_hash_profile` const `pcae.prompt-semantic.v1` |
| `authority_binding` | `approval_id`, `approval_digest`, `authority_projection_id`, `authority_projection_digest`, `authority_contract_version` const `RIHAC-001/2.0`, `proof_id`, `proof_digest`, `proof_validation_digest`, `registry_state_digest`, `approval_subject_digest`, `trusted_presentation_ref`, `challenge_digest` |
| `authority_generation_binding` (v2.1) | `snapshot_schema_version` const `HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0`, `principal_generation`, `credential_generation`, `approval_generation`, `lifecycle_generation`, `consumption_generation` — see HPAC-REQ-098a |
| `pb_binding` | `request_digest`, `decision_digest`, `decision`, `policy_version`, `causing_policy_ids`, `matched_no_go_ids` |
| `runtime_enforcement_binding` | `decision_id`, `decision_digest`, `verdict`, `expires_at`, `evaluated_input_digest` |
| `dispatch_binding` | `containment_evidence_ref` (closed ID/digest pair), `state` const `dispatch_attempted`, `consumed_at` |

Arrays retain order and all other strings/digests use their owning contract
grammar. Canonicalization is HPAC-REQ-089's rule. The artifact is the single
authoritative fact that the named approval, presentation, challenge, proof,
and attempt were consumed together; no separate mutable `consumed` fields
or cross-file sequence of consumption writes exists.

- **HPAC-REQ-098a (v2.1 — V-15-1 durable authority-generation snapshot).**
  `authority_generation_binding` is a closed object, schema identity
  `HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0`, with exactly these fields:
  `snapshot_schema_version` (const), and the five markers
  `principal_generation`, `credential_generation`, `approval_generation`,
  `lifecycle_generation`, `consumption_generation` — each a non-empty
  bounded (≤256 char) stripped string that is a digest or fixed marker over
  **durable canonical state only**:

  | Marker | Committed value |
  |---|---|
  | `principal_generation` | whole-record canonical digest of the current principal registry record (moves on `revoke_principal`, disablement, eligibility change, record replacement) |
  | `credential_generation` | whole-record canonical digest of the current credential registry record (moves on `revoke_credential`, replacement, mechanism/key/binding change) |
  | `approval_generation` | canonical digest folding the current resolved immutable RIASC-001 v3.0 approval `record_digest` + `approval_id` + a forward hook for a future RIHAC-001 v2.0 §14 append-only, digest-bound early-revocation artifact (`null` until that separate governed amendment). Absent/unreadable approval → the resolver fails closed. Approval revocation is otherwise transitive via `principal_generation` / `credential_generation` / `lifecycle_generation` / wall-clock expiry |
  | `lifecycle_generation` | digest over every `(sequence, state, event_digest)` triple of the full hash-chained proof lifecycle chain (moves on any successor, a terminal `EXPIRED`/`REVOKED`/`REJECTED` event, any transition, or a fork → fail closed) |
  | `consumption_generation` | consumption-record state observed at the linearization point — `"absent"` on the create path (a present or durability-uncertain record short-circuits before the create) |

  The committed object is the exact snapshot `S1` that gate 9 captured
  after the HPAC-REQ-099 in-boundary revalidation battery and verified
  unchanged at the final zero-effectful-I/O re-read `S2` immediately before
  the create; it is **never** rebuilt from post-`S2` state. No field uses a
  wall clock, mtime, nonce, or process identity, so every marker is
  reconstructible from durable state after a restart. This object is
  **verification evidence, not execution authority**: it carries no
  capability field and no identity claim beyond digests; possession or
  reconstruction grants nothing; a future gate 10 MUST re-read current
  canonical generation state and compare it against this durable snapshot
  (RDGO-001 v3.1 §10/§11).

- **HPAC-REQ-099.** Immediately before create, gate 9 reruns
  current principal/credential/descriptor status, presentation attestation
  and expiry, challenge/proof/lifecycle chain, approval freshness/expiry,
  exact gate-5 binding, PB/Runtime Enforcement freshness, and absence of a
  consumption record. It then captures the HPAC-REQ-098a authority-generation
  snapshot `S1` and re-reads it as `S2` with **zero intervening effectful
  I/O** immediately before the create; any `S2 != S1` fails closed with no
  `consumption.json`. It compare-and-creates `consumption.json` against the
  exact current registry/configuration state digest and sequence-3 event.
  The per-`proof_id` create-only atomic primitive (HPAC-REQ-100) **is** the
  serialization boundary and the sole transaction mechanism — there is no
  separate held lock or transaction object (RDGO-001 v3.1 §10; `.1R.9`
  §18). The revalidation battery plus the zero-I/O `S1`/`S2` re-check make
  the validity check and the atomic consumption serialized with respect to
  each other to the practical limit; a residual instruction-level
  micro-window between the `S2 == S1` decision and the create is the
  acknowledged limit and produces no external effect (gate 10 absent; its
  mandatory re-read re-closes it). Revocation, expiry, invalidation, or
  drift after gate 5 but before the atomic create fails closed. Gate-5
  validation is never a substitute for this gate-9 revalidation.

- **HPAC-REQ-100.** The create is an atomic, create-only, same-filesystem
  durable commit: write canonical bytes to a protected temporary sibling,
  fsync-equivalent the file, atomically install only if the final path is
  absent, fsync-equivalent the parent, and read-back verify before gate 10.
  Contract semantics admit only two recoverable outcomes: final artifact
  absent (not consumed; no gate-10 effect permitted) or one complete valid
  final artifact present (consumed; replay rejected). Temporary/partial,
  corrupt, duplicate, conflicting, or durability-uncertain state is not
  interpreted as reusable authority and yields no dispatch. An existing
  byte-identical record means the attempt is already consumed, not an
  idempotent license to enter gate 10 again.

## 42. Crash, retry, replay, and store relationships

- **HPAC-REQ-101.** If the process stops after gate 5 and before gate 9,
  sequence 3 remains bound but unconsumed; resume may rerun gate 5 only for
  the exact same binding and only while every live check still passes. A
  gate-9 interruption resolves under HPAC-REQ-100: absent means no effect and
  permits only full revalidation before another create attempt; valid present
  means consumed and prohibits dispatch/retry with that authority; ambiguous
  or corrupt means fail closed and manual recovery, never replay. After a
  successful gate 9, every retry requires a fresh invocation, attempt,
  presentation, challenge, proof, and approval under RIHAC/RDGO one-shot
  rules.

- **HPAC-REQ-102.** Presentation mechanisms, presentation evidence, proof
  JSON, lifecycle events, and consumption records are distinct record
  families within one deployment-scoped `HPAC_PROTECTED_ROOT`. Their exact
  paths and cross-digests form one immutable chain; no repository-local copy,
  caller-provided path, HATP registry/evidence, structural lookalike, or raw
  digest can substitute. The approval remains in RIHAC's repository
  governance store, but its immutable ID/digest is consumed solely by the
  protected §41 record. Any repository-side dispatch record is a mirror or
  reference to that commit and cannot independently establish consumption or
  authority.

## 43. Closure and cross-contract ownership

- **HPAC-REQ-103.** B-3 is closed only by the full conjunction of active
  protected descriptor, canonical subject, protected evidence path/schema,
  verified mechanism attestation, human-usable facts, explicit election,
  challenge digest binding, and later lifecycle revalidation. Missing any
  conjunct makes blind touch insufficient and produces no authority.

- **HPAC-REQ-104.** B-4 is closed only by the complete proof JSON plus
  hash-chained lifecycle events, exact approval/presentation/challenge/
  subject/attempt binding, gate-5 sequence-3 semantics, and the single
  crash-safe gate-9 consumption record. No object field or reference alone
  carries trust.

- **HPAC-REQ-105.** HPAC owns presentation/mechanism/proof/lifecycle/
  consumption artifact schemas and protected resolution; RIHAC owns
  approval validity and projection; RIASC owns only immutable approval wire
  shape; PBRD consumes only RIHAC projection; RDGO owns when gates 5 and 9
  execute these operations. RPAC remains provider-neutral and unchanged.
  Caller-created principal, presentation, lifecycle, proof, approval, or
  projection objects without this complete canonical ceremony have zero
  authority, closing N2 at the contract layer.

## 44. Freeze verdict

**HPAC-001 v2.1: NORMALIZED AND FROZEN; supersedes v1.0 with no
authority migration. B-3 and B-4 canonical evidence gaps are closed. v2.1
adds the §41 `authority_generation_binding` verification-evidence object
(`HPAC-AUTHORITY-CONSUMPTION/2.1`) — MINOR, no authority widening.**
**`HumanAuthenticator` implementation: NOT BUILT / NOT AUTHORIZED.**
**`HumanPrincipalRegistry`: NOT CREATED.**
**Hardware: NOT TOUCHED.**
**Real execution: UNAVAILABLE.**
