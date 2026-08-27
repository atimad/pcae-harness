# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.2 — Human-Principal Authentication,
# Protected Approval Presentation, and Proof-Lifecycle Implementation Planning

**Phase type:** Implementation planning only. No `src/pcae/` change, no
`tests/` change, no PB implementation, no Runtime Enforcement, no Shell
Gate, no runtime adapter, no dry-runtime consumer, no hardware/FIDO2
interaction, no network access, and no relaxation of POL-005. Runtime
remains `Observed` / `observe` / `unavailable`. Public release remains
v0.4.3 at commit `63580893`, unchanged.

**Predecessor:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.1 — Independent
Verification of Trusted Approval Presentation Evidence and HPAC
Proof-Lifecycle Canonicalization Repair. That phase independently
reconstructed and confirmed the frozen contract baseline below from
primary contract text; this phase treats that freeze as ground truth
and finds no inconsistency against the source read for this document
(see §5 note).

---

## 1. Objective

Design — without implementing — the minimum staged path that turns the
now-frozen six-contract human-principal-authentication authority model into
real production components: `HumanPrincipalRegistry`, a protected
approval-presentation mechanism, a trusted presentation-evidence store, a
FIDO2 HPAC authenticator, an authentication-proof store, a hash-chained
proof-lifecycle store, a Gate-9 authority-consumption store, and the four
outstanding production repairs (B1, B7, N1, N2). The design is expressed as
eight non-collapsible layers (§52) so that each can be independently
implemented and independently verified before the next begins.

## 2. Baseline

Confirmed from `git log`, `PROJECT_STATUS.md`, and the contract documents
themselves (all read directly for this phase, not taken on trust from a
predecessor's summary):

- Working tree clean at commit `81209d74` ("Transition phase
  149O.20L.7O.3W.1R.2B.1R.1.1R.1 to idle").
- `PROJECT_STATUS.md`'s "Current Phase" section records
  149O.20L.7O.3W.1R.2B.1R.1.1R.1 as VERIFICATION-ONLY — COMPLETE; VERIFIED,
  and names exactly this phase (149O.20L.7O.3W.1R.2B.1R.1.1R.2) as the
  recommended next phase, not begun, human decision required.
- Runtime state: `Observed` / `observe` / `unavailable`, stated identically
  in HPAC-001, RIHAC-001, and RDGO-001's own headers.
- Latest public release: v0.4.3 at commit `63580893` (from prior-cycle
  memory; not re-verified by re-reading release artifacts in this
  research-only phase, and not touched by it).
- None of the following exist anywhere in `src/pcae` (confirmed by
  `grep -rl` across the tree): `HumanPrincipalRegistry`,
  `TrustedApprovalPresentationEvidence`, `HumanAuthenticationProof`,
  `RuntimeInvocationAuthorityConsumption`.
- The private research repo `~/repos/pcae-deepseek-research` was not
  opened, referenced, or touched.

## 3. Verified contract set

Independently re-read in full (not from summary) for this phase:

| Contract | Version | File |
|---|---|---|
| RIHAC-001 | 2.0 | `docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` |
| RIASC-001 | 3.0 | `docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md` |
| HPAC-001 | 2.0 | `docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` |
| PBRD-001 | 2.0 | `docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` |
| RDGO-001 | 3.0 | `docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md` |
| RPAC-001 | 1.0 (unchanged) | `docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md` |

This phase's own reading corroborates the predecessor's independent
verification: all originally-BLOCKING findings (7/7) and MUST-FIX (2/2) are
closed in contract text, B-3 and B-4 are closed by HPAC-001 §§38-42, the N2
contract gap is closed by RIASC-001 v3.0 §7's `provenance` redefinition, and
RDGO-001 v3.0 retains the eleven-gate order (§1 table) with gates 3/4
transposed relative to v1.0 only, unchanged again in v3.0. **No
inconsistency was found** between the prior freeze's claims and the primary
contract text read for this phase.

## 4. Production gap

None of the following production components exist: `HumanPrincipalRegistry`
(HPAC-001 §5), the protected `TrustedApprovalPresentationMechanism` and its
evidence store (§39), a `HumanAuthenticator` implementation of any kind
(§10, including a deterministic/test one), the canonical
`HumanAuthenticationProof` store and hash-chained lifecycle (§§17, 40), the
Gate-9 `RuntimeInvocationAuthorityConsumption` store (§41), or the B1/B7/N1
production-code repairs. `RuntimeInvocationApproval` creation
(`runtime_authority.create_runtime_invocation_approval`), the RIASC-001 v3.0
`provenance` object with its four new fields, and `validate_approval`'s v2
provenance elaboration (RIHAC-001 §16 step 4) are likewise unimplemented
against the current contract version — the existing `runtime_authority.py`
implements only the pre-v2 shape (its `ApprovalProvenance` dataclass, read
in this phase, predates `principal_id`/`credential_id`/
`authentication_mechanism_id`/`authentication_proof_ref`). This is the
entire distance this multi-phase plan must close.

## 5. Requirement-code mapping

Every new normative requirement across the six contracts is classified in
Matrix A (§ below) into one of: **Reuse** (existing production code already
satisfies or can be adapted), **New-Model** (new dataclass/schema), **New-
Store** (new canonical create-only store), **New-Validator** (new
verification sequence), **New-Test** (adversarial/regression coverage), or
**Deferred-Hardware** (requires real FIDO2/UI, explicitly out of scope
until Phases 3/4, §52). No requirement is left unmapped; Matrix A is
organized by contract section rather than by individual `-REQ-` number for
readability, but every section's requirements are covered by the row's
disposition.

### Matrix A — Requirement implementation

| Contract requirement (by section) | Production component | Reuse/new | Planned phase |
|---|---|---|---|
| HPAC §4 principal identity (REQ-007-011) | `HumanPrincipalRecord` model | New-Model | 1 |
| HPAC §5 registry shape/atomicity (REQ-012-017) | `HumanPrincipalRegistryStore` | New-Store (reuses `_write_atomic` pattern, §35) | 1 |
| HPAC §6 HATP separation (REQ-018-020) | Separate document/path/namespace; enforced by store construction, not shared code | New-Store constraint | 1 |
| HPAC §7 registry scope/trust root (REQ-021-024) | Deployment-scoped root resolver, external-admin bootstrap ceremony | New-Component (model+store now; ceremony deferred, §8) | 1 (model), N/A (ceremony not yet authorized) |
| HPAC §8-9 enrollment/credential multiplicity (REQ-025-031) | `HumanPrincipalRegistryStore` writer API (`enroll_principal`/`revoke_principal`/`enroll_credential`/`revoke_credential` + preview variants) | New-Store | 1 (data model + preview-only API), 5 (protected-admin-gated real mutation) |
| HPAC §10-11 `HumanAuthenticator` abstraction/non-collapse (REQ-032-035) | `HumanAuthenticator` protocol | New-Interface | 3 |
| HPAC §13-14 mechanism status/FIDO2 descriptor (REQ-037-046) | Static/dynamic descriptor dataclasses; deterministic authenticator implements the same interface | New-Model (1/3), Deferred-Hardware (real FIDO2, 6) | 1/3/6 |
| HPAC §15 domain separation (REQ-047-048) | Challenge-construction component enforces `pcae.hpac.runtime-invocation-approval.v2` domain tag | New-Component | 3 |
| HPAC §16 challenge/nonce/replay (REQ-049-051) | Challenge model + consumed-challenge ledger | New-Model/Store | 1/3 |
| HPAC §17 proof structure (REQ-052-053) | `HumanAuthenticationProof` model + `HumanAuthenticationProofStore` | New-Model/Store | 1 |
| HPAC §18 verification sequence (REQ-054-055) | HPAC verifier (mechanism-neutral) | New-Validator | 3 |
| HPAC §19 trusted construction (REQ-056-058) | `AuthenticatedHumanPrincipal` (ephemeral, non-serializable) trusted-construction type | New-Model | 3 |
| HPAC §20 assurance model (REQ-059-060) | Assurance-level enum + gate on `PRINCIPAL_VERIFIED_INTENT` | New-Model | 1/3 |
| HPAC §21 revocation (REQ-061-065) | Registry revocation API + Gate-5/Gate-9 re-resolution | New-Store API / New-Validator | 1 (API), 5 (wiring) |
| HPAC §22-26 fallback/audit/replay/failure (REQ-066-076) | Fail-closed verifier behavior, audit-record emission | New-Validator/New-Store field | 3 |
| HPAC §27-29 delegation/config-authority/multi-principal (REQ-077-081) | Enforced structurally (no delegation API, no repo-config path in root resolver) | Reuse of non-existence + New-Component guard | 1/7 |
| HPAC §30-31 offline/HATP cross-check (REQ-082-084) | No network call in verifier; explicit domain-separation test | New-Test | 3/6 |
| HPAC §32 reuse map | `hatp_providers.py`/`hatp_fido2_provider.py`/`hatp_bootstrap.py` patterns | Reuse (pattern only, §35) | 6 |
| HPAC §33-35 hardware-unavailable/same-user-agent/delegated-isolation (REQ-085-087) | Verifier fails closed on `unavailable`; adversarial same-user-agent test suite | New-Validator/New-Test | 3/6/8 |
| HPAC §38 canonical approval subject (REQ-088-089) | `CanonicalRuntimeApprovalSubject` model | New-Model | 1 |
| HPAC §39 presentation mechanism/evidence (REQ-090-093) | `ProtectedApprovalPresentationMechanism` abstraction + `TrustedApprovalPresentationEvidence` model/store | New-Interface (2), New-Model/Store (1) | 1 (model/store), 2 (deterministic mechanism), 7 (real mechanism) |
| HPAC §40 proof lifecycle (REQ-094-097) | `HPACLifecycleStore` (hash-chained event sequence) | New-Store | 1 |
| HPAC §41-42 Gate-9 consumption (REQ-098-102) | `RuntimeInvocationAuthorityConsumptionStore` | New-Store | 1 (model/store), 5 (real gate-9 wiring) |
| HPAC §43 closure ownership (REQ-103-105) | Cross-contract ownership boundaries — enforced by keeping stores/validators in separate modules | New-Component boundary | 1-5 |
| RIASC §7 provenance fields (`principal_id`, `authentication_mechanism_id`, `credential_id`, `authentication_proof_ref`) | `ApprovalProvenance` dataclass extension in `runtime_authority.py` | Repair (N2) | 5 |
| RIHAC §3/§16 step 4 provenance verification | `validate_approval`'s v2 elaboration | Repair (N2) + New-Validator | 5 |
| RIHAC §17 Gate-9 consumption point | `RuntimeInvocationAuthorityConsumptionStore` write | New-Store integration | 5 |
| PBRD §4 item 14 `human_authority_binding` | `project_human_authority_binding` (already exists, pre-v2 shape) | Repair (narrow — accept typed RIHAC v2 projection instead of ad hoc binding) | 5 |
| RDGO gate 3/5/9 sequencing | No gate-count/order change; slot new components into existing gates | Reuse of gate contract, New-Component wiring | 5 |
| B1 forgeable seal | `runtime_authority.ValidatedAuthorityProjection` / `runtime_dispatch_permission` seals | Repair | 5 |
| B7 copied identity seal | `runtime_dispatch_permission.RuntimeDispatchIdentity` | Repair | 5 |
| N1 unbound store provenance | `runtime_invocation_approval_store.RuntimeInvocationApprovalStore.load` / `runtime_authority.validate_approval` | Repair | 5 |
| N2 caller-supplied approver | `runtime_authority.create_runtime_invocation_approval` (line ~858-860 per 3W.1R.2B's own citation) | Repair | 5 |

## 6. Component inventory

Evaluated against the smallest-coherent-design principle (governing
instruction: prefer merging over multiplying files/classes).

- **`HumanPrincipalRegistry` / `HumanPrincipalRegistryStore`**: kept as
  two names but **one module** (mirrors `hatp_bootstrap.py`'s own
  `PrincipalRecord`+`HATPTrustStore` co-location in one file). The registry
  is the logical schema; the store is its atomic-write/read-back
  implementation — splitting them into separate files would only add
  import indirection with no independent reuse benefit.
- **`HumanAuthenticator` interface**: a single `Protocol` (mirrors
  `hatp_providers.HATPHardwareSigner`'s existing `Protocol` shape) — no
  separate ABC hierarchy.
- **`FIDO2HumanAuthenticator`**: a distinct module from the interface
  (real hardware I/O deserves isolation so the interface module has zero
  hardware imports), deferred to Phase 6.
- **`ProtectedApprovalPresentationMechanism`**: interface lives with
  `HumanAuthenticator` in concept but is a *separate* Protocol — HPAC-001
  §11 (HPAC-REQ-034/035) explicitly requires authenticator and
  presentation to remain non-collapsed components, so these must not
  share a file/class despite superficial similarity (both are "human
  interaction" abstractions). Keep two Protocols in two modules.
- **`TrustedApprovalPresentationEvidence` / `TrustedApprovalPresentationStore`**:
  one module, same store-file-pairing rationale as the registry.
- **`HumanAuthenticationProof` / `HumanAuthenticationProofStore`**: one
  module.
- **`HPACLifecycleStore`**: separate module from the proof store — the
  lifecycle is a distinct hash-chained record family with its own
  fork/gap detection logic (HPAC-REQ-094), not a field on the proof.
- **`RuntimeInvocationAuthorityConsumptionRecord` /
  `RuntimeInvocationAuthorityConsumptionStore`**: one module, reusing the
  registry/evidence/proof pairing convention.
- **Approval authority validator changes**: extend `runtime_authority.py`
  in place (it already owns `validate_approval`) rather than creating a
  parallel validator module — HPAC-001 §11 forbids folding
  `HumanAuthenticator` *into* the validator, not calling the HPAC verifier
  *from* it.
- **PB projection changes / dispatch identity re-resolution**: narrow
  in-place repairs to `runtime_dispatch_permission.py`, not new files
  (§30, §35).

Net new modules for Phase 1 (the first slice, §37): a schemas/models
module, four store modules (registry, presentation evidence, proof+
lifecycle as two closely related stores, consumption), and one deterministic
fixtures module — roughly six to seven files, not the eleven-plus a naive
one-class-one-file reading of the prompt's inventory would produce.

## 7. Principal registry

- **Scope**: deployment/user-scoped (HPAC-REQ-021), never per-repository.
  Repository code, `.pcae/` config, environment variables, or task state
  MUST NOT select, override, or influence the registry path
  (HPAC-REQ-079/080) — this is a hard architectural constraint on the
  resolver, not a policy default.
- **Path**: `<HPAC_PROTECTED_ROOT>/principals/registry.json` (or
  equivalent single canonical file under the protected root), resolved by
  a dedicated function analogous to `hatp_bootstrap.resolve_canonical_deployment_root`
  but rooted in its own namespace-distinct location per HPAC-REQ-018 (never
  `registry.json` itself, which is HATP's).
- **Ownership**: root and every ancestor owned/writable only by an
  OS-level protected administration principal (HPAC-REQ-022) — this
  mirrors HATP's own `_default_production_trust_root`/ownership-check
  pattern, reused conceptually, not by calling into HATP's own resolver.
- **Read/write API**: read-only resolution + preview available to any
  caller; mutation (`enroll_principal`, `revoke_principal`,
  `enroll_credential`, `revoke_credential`) available only through the
  protected-admin path (§8).
- **Immutable identity fields**: `principal_id` (opaque, HPAC-REQ-007),
  `credential_id` (HPAC-REQ-030) — neither is ever reassigned.
- **Active/revoked status**: closed two-value vocabulary
  `{"active","revoked"}`, monotonic (HPAC-REQ-061/062).
- **Credential mapping**: one principal to zero-or-more credentials
  (HPAC-REQ-030), each credential naming exactly one principal.
- **Versioning**: registry document itself carries a schema version field
  (mirrors every other v2 schema's `*_schema_version` const pattern);
  unknown versions fail closed (HPAC-REQ-017).
- **Corruption behavior**: any malformed document, duplicate ID, symlink,
  or unknown field is rejected outright — no partial/best-effort parse
  (HPAC-REQ-017, mirrors `hatp_bootstrap._parse_registry_document`'s
  existing reject-on-any-anomaly discipline, reused as a pattern).

**Repository code MUST NOT control registry selection** — this is
restated here as a hard design constraint carried into the file plan
(§34): the resolver function takes no repository-derived input at all,
only host/user-scoped environment (analogous to how `hatp_bootstrap`
resolves independent of cwd).

## 8. Bootstrap/enrollment

Two separable concerns, deliberately kept apart:

1. **Data model + store (testable deterministically now, Phase 1)**: the
   `PrincipalRecord`/`CredentialRecord` schema, the atomic
   create/read/list/revoke store operations, and their preview variants
   (HPAC-REQ-026). All of this can be built and unit-tested today with a
   fake/deterministic protected root — no hardware, no human, no real
   enrollment ceremony required.
2. **Trusted enrollment ceremony (NOT planned for implementation in this
   phase or the next several phases)**: the external deployment-owner
   anchor, the non-defaultable protected-admin ceremony, FIDO2
   registration-response verification, and the resulting first-write to
   the real protected root (HPAC-REQ-023/028/029). This requires a real
   human, real hardware, and a real protected-admin execution context —
   none of which this phase, or Phases 1-2, may touch. It is scheduled no
   earlier than Phase 5/6 (§52), and even then only as its own separately
   authorized sub-phase, following the precedent this repository already
   set for HATP's own admin-entrypoint ceremonies (HHCE-001/HPSE-001,
   `hatp_bootstrap.py`, `hatp_deployment_binding_admin.py`).

## 9. Authenticator abstraction

```python
class HumanAuthenticator(Protocol):
    def describe(self) -> MechanismDescriptor: ...
    def status(self) -> MechanismStatus: ...
    def prepare_challenge(self, subject_digest: str, presentation_digest: str) -> Challenge: ...
    def verify_response(self, challenge: Challenge, response: bytes, credential: CredentialRecord) -> ProofMaterial: ...
    def resolve_principal(self, verified_proof: ProofMaterial) -> tuple[str, str]: ...
```

No authority-validation logic, no PB logic, and no registry-mutation logic
belongs inside an implementation of this interface (HPAC-REQ-032/034/035).
`verify_response` returns unverified-but-parsed proof material only; the
HPAC verifier (§18, a separate component) is what turns that into a trusted
`AuthenticatedHumanPrincipal`. This mirrors `hatp_providers.HATPHardwareSigner`'s
existing shape (sign/verify primitives with no authority opinion) as a
pattern, not a live dependency (HPAC-REQ-019).

## 10. FIDO2 boundary

**Reusable at the library-primitive level only** (HPAC-REQ-019):
`hatp_fido2_provider.Fido2HardwareProvider` (credential-identity/assertion
parse-and-verify shape, `_parse_fido2_evidence`, `_serialize_evidence`,
`_payload_digest`) and `hatp_providers.HardwareProviderCapabilities`/
`discover_hardware_providers`/`create_production_hardware_provider` (static
capability descriptor shape and provider-discovery pattern). These are
low-level CTAP2 parsing/verification primitives with no notion of "PCAE
runtime-invocation approval" baked in — they are candidates for a future
`FIDO2HumanAuthenticator` to call as a library dependency.

**Explicitly NOT reusable — separate trust domains (HPAC-REQ-018/047/048/084)**:
HATP's `registry.json`, its `principal_id`/`SignerRecord` namespace, its
`hatp_bootstrap.HATPTrustStore`, its challenge/domain-separation constants,
and its authority semantics (Class-B admin-signing authority) MUST NOT be
reused, imported, or referenced by the new HPAC-001 verifier or registry. A
future implementation SHALL NOT allow an HPAC-001 verification to accept a
HATP signing-ceremony assertion or vice versa (HPAC-REQ-084) — the same
physical FIDO2 device MAY be cross-enrolled under both registries but each
enrollment gets its own distinct `credential_id` in its own store
(HPAC-REQ-048).

## 11. Deterministic authenticator

A `DeterministicTestHumanAuthenticator` implements `HumanAuthenticator`
entirely in-process (no hardware I/O), parameterized to produce every
adversarial combination the verifier must reject:

- UP true/false, UV true/false, independently settable;
- credential/principal match or deliberate mismatch;
- challenge match or deliberate stale/foreign challenge;
- replay (same proof presented twice);
- revoked-credential/revoked-principal state at verification time.

**Architectural incapability for real dispatch**: the type itself is
tagged, e.g. a class-level `SIMULATION_ONLY: Final[bool] = True` constant
and a `mechanism_id` that can never equal `hpac.fido2.uv_presence.v2` (it
uses its own namespaced test `mechanism_id`, e.g.
`hpac.deterministic.test-only.v1`). Any future real-dispatch gate (Gate 5/9,
§21/§22) is planned to reject any `mechanism_id` outside a real-mechanism
allowlist by construction — this excludes the deterministic authenticator
from the real dispatch path structurally, not merely by convention, mirroring
`hatp_providers.TestHATPProofVerifierProvider`'s existing test-only pattern
(reused as a pattern, §35) which HATP itself keeps clearly separate from
`create_production_hardware_provider`.

## 12. Presentation abstraction

```python
class ProtectedApprovalPresentationMechanism(Protocol):
    def descriptor(self) -> PresentationMechanismDescriptor: ...
    def present(self, canonical_subject: CanonicalRuntimeApprovalSubject) -> TrustedApprovalPresentationEvidence: ...
```

The caller (agent, adapter, CLI) can request a presentation but cannot
mint `TrustedApprovalPresentationEvidence` directly: `present()` is the
only path to a valid evidence object, and only a mechanism satisfying
HPAC-REQ-090's protected-installation requirement is eligible to implement
it in a way the verifier will accept (§15/§16, HPAC-REQ-092's mechanism
attestation check). An evidence-shaped object built by ordinary code is
schema-valid but fails `mechanism_attestation` verification and is
rejected — the boundary is enforced by verification, not merely by API
shape, since Python cannot prevent direct dataclass construction at the
language level.

## 13. Deterministic presentation mechanism

A `DeterministicTestPresentationMechanism` is simulation/test-only
(mirrors §11's tagging discipline) but exercises the full B-3 conjunction
adversarially: it can be parameterized to produce a presentation whose
`human_visible_representation_digest` deliberately does not match
`canonical_subject.approval_preview_digest` (display/subject mismatch), an
`election.occurred_at` before `presented_at` (ordering violation), a
`mechanism_attestation` that fails to verify against its own descriptor
(forged attestation), or no `election` at all (blind touch equivalent).
Each of these must be independently rejectable by the verifier built in
Phase 3, giving Phase 1's deterministic fixtures direct reuse as adversarial
inputs to Phase 2's verifier tests.

## 14. Real presentation mechanisms

Planning only — no implementation. Ranked by feasibility for macOS (dev)
and Linux (deploy):

1. **Dedicated local PCAE UI** (small native or Tauri-style window PCAE
   itself controls) — highest control over `agent_substitution_resistant`
   and rendering fidelity; requires new UI toolkit dependency (§42);
   feasible on both platforms but highest implementation cost.
2. **Protected OS-native dialog** (macOS: a signed helper using
   `NSAlert`/Touch ID prompt style; Linux: a `polkit`-style privileged
   dialog) — good agent-substitution resistance if the dialog process runs
   under a different, protected principal; platform-specific adapters
   required (violates the "no OS-specific adapter" preference HPAC-001 §30
   states only for the *authenticator*, not the presentation channel, so
   this remains viable here).
3. **Separate trusted terminal/TTY path** (e.g., a physically distinct
   console session or a protected pty the ordinary agent process cannot
   write to) — lower implementation cost, weaker guarantee that an
   agent cannot observe/spoof the display without kernel-level session
   isolation.
4. **Authenticator display/out-of-band** (a FIDO2 device with its own
   trusted display, if one is enrolled) — strongest agent-substitution
   resistance but hardware-dependent and not universally available;
   treated as a future optional upgrade, not the baseline plan.

Recommendation for eventual Phase 7 (not decided now, flagged for human
input, §55): option 1 or 2, since both plausibly satisfy
`agent_substitution_resistant` without requiring every enrolled FIDO2
device to have its own display.

### Matrix C — Mechanisms

| Mechanism | Real/simulation | UP | UV | Trusted presentation | Real-runtime eligible? |
|---|---|---|---|---|---|
| `hpac.deterministic.test-only.v1` (§11 authenticator) | Simulation | Parameterizable | Parameterizable | N/A (authenticator, not presentation) | No — structurally excluded by `mechanism_id` allowlist and import boundary |
| `DeterministicTestPresentationMechanism` (§13) | Simulation | N/A (presentation, not authenticator) | N/A | Deterministic, fixture-rendered | No — same exclusion discipline as above |
| `hpac.fido2.uv_presence.v2` (§14/HPAC-REQ-039, real FIDO2) | Real | Required (`true`) | Required (`true`) | N/A (authenticator; paired with a real presentation mechanism at Gate 3) | Yes, once Phase 3 verified and paired with a real presentation mechanism |
| Dedicated local PCAE UI (§14 option 1) | Real | N/A (presentation) | N/A | Protected, agent-substitution-resistant (design goal) | Yes, once Phase 4 verified |
| Protected OS-native dialog (§14 option 2) | Real | N/A | N/A | Protected if isolated-principal process | Yes, once Phase 4 verified |
| Separate trusted terminal/TTY (§14 option 3) | Real | N/A | N/A | Weaker guarantee absent kernel-level isolation | Conditionally — only if isolation is independently verified |
| Authenticator display/out-of-band (§14 option 4) | Real | N/A | N/A | Strongest, hardware-dependent | Conditionally — only for enrolled devices with a trusted display |

## 15. Presentation evidence model/store

HPAC-001 §39.2's exact fields (HPAC-REQ-091) map directly to a
`TrustedApprovalPresentationEvidence` dataclass: `presentation_schema_version`,
`presentation_id` (`hpe-<32-hex>`), `presentation_digest`, `approval_id`,
`canonical_subject`, `approval_subject_digest`, `mechanism_ref`,
`human_visible_facts` (its own closed sub-object, HPAC-REQ-091's second
table), `human_visible_representation_digest`, `presented_at`, `election`,
`mechanism_attestation`, `mechanism_attestation_digest`. All fields are
immutable once written (HPAC-REQ-093, create-only). The store:

- **Path**: `<HPAC_PROTECTED_ROOT>/presentations/v2/<presentation_id>/presentation.json`.
- **Write discipline**: create-only, atomic, read-back verified (reuse
  `repository_identity._write_atomic`'s pattern).
- **Lookup**: only by the closed `(presentation_id, presentation_digest)`
  pair — no caller-supplied path (HPAC-REQ-093).
- **Corruption/duplicate/replay**: symlink, traversal, duplicate ID,
  non-canonical bytes, digest mismatch, or wrong ownership/ACL all fail
  closed at resolution time; a duplicate create attempt at the same ID is
  rejected by the create-only guarantee, not silently overwritten.

**Mechanism installation authority (§16)**: only the protected
administrator (HPAC-REQ-080) may install/revoke a
`TrustedApprovalPresentationMechanism` descriptor
(`<HPAC_PROTECTED_ROOT>/presentation-mechanisms/v2/<mechanism_id>/descriptor.json`,
HPAC-REQ-090). Trust in a piece of evidence therefore derives from two
independent facts holding together: (a) the mechanism that produced it was
itself installed by protected-admin authority, and (b) the evidence's own
`mechanism_attestation` verifies against that installed descriptor's
`verifier_configuration_digest`. Neither repo config nor any
repository-controlled state can substitute for either fact
(HPAC-REQ-079).

## 16. Mechanism installation authority

Covered above (§15); restated as its own explicit non-goal: a repository
`.pcae/` file, environment variable, or task/agent input can never install,
select, or weaken a presentation-mechanism descriptor. This is enforced at
the resolver level (the descriptor path is under `HPAC_PROTECTED_ROOT`,
which is itself resolved independent of repository/cwd/environment per
HPAC-REQ-080), not by a runtime permission check that a compromised agent
could bypass.

### Matrix B — Stores

| Store | Scope | Trust root | Writer | Reader | Atomicity |
|---|---|---|---|---|---|
| `HumanPrincipalRegistry` (`PrincipalRecord`/`CredentialRecord`) | Deployment/user-scoped, outside every repository (HPAC-REQ-021) | Protected admin-owned root, ancestor ACL-checked (HPAC-REQ-022) | Protected-admin-gated writer only (`enroll_principal`/`revoke_principal`/`enroll_credential`/`revoke_credential`) | Any resolver that needs `active` status lookup (verifier, §21/§22) | Create-only/append-only, read-back verified, sorted serialization (HPAC-REQ-015/016) |
| `TrustedApprovalPresentationEvidence` store | Deployment-scoped, one record per presentation | Protected mechanism-installation authority (HPAC-REQ-080) + mechanism attestation | Only the installed `ProtectedApprovalPresentationMechanism`'s internal factory (§12) | Verifier (Gate 5/9), audit tooling | Create-only, atomic, read-back verified (HPAC-REQ-093) |
| `HumanAuthenticationProof` store | Deployment-scoped, one record per `proof_id` | Trusted challenge/verification coordinator only | Verifier, after sequence-2 `PROOF_VERIFIED` succeeds (HPAC-REQ-096) | Gate 5/9, audit tooling | Create-only, atomic, read-back verified (HPAC-REQ-053) |
| `HPACLifecycleStore` (hash-chained events) | Deployment-scoped, per `proof_id` subtree | Trusted coordinator (sequence 0) + Gate 5 (sequence 3) only | Narrow transition API only (§20) — no direct event construction | Gate 5/9, verifier, audit tooling | Append-only, hash-chained, gap/fork/duplicate-sequence rejected (HPAC-REQ-094/095) |
| `RuntimeInvocationAuthorityConsumption` store (Gate-9) | Deployment-scoped, one record per `proof_id` | Gate 9's protected serialization boundary only | Gate 9's atomic compare-and-create, nothing else | Gate 10/11, audit tooling | Single atomic create-only commit, durability-proven before Gate 10 (HPAC-REQ-100) |

## 17. Proof model/store

Four distinct representations are kept separate, matching HPAC-001's own
layering:

1. **Raw authenticator response** — mechanism-specific bytes
   (`assertion`), never persisted standalone; transient input to
   verification.
2. **Untrusted parsed proof** — the lifecycle's `ASSERTION_RECEIVED` state
   (HPAC-REQ-095/096): challenge-digest-matched but not yet fully
   verified; not a `HumanAuthenticationProof`.
3. **Canonical proof record** — `HumanAuthenticationProof`
   (HPAC-PROOF/2.0, HPAC-REQ-052), created only after full sequence-2
   verification succeeds; stored at
   `<HPAC_PROTECTED_ROOT>/proofs/v2/<proof_id>/proof.json`, create-only,
   atomic, canonical-lookup-only (HPAC-REQ-053).
4. **Verified principal result** — `AuthenticatedHumanPrincipal`, ephemeral
   and non-serializable (HPAC-REQ-056/058); never itself stored, always
   re-derived by re-running §18's sequence against current state.

## 18. Hash-chain lifecycle

Recovered exactly from HPAC-001 §40 (not reinvented): `HumanAuthenticationProofLifecycleEvent`
files at `<HPAC_PROTECTED_ROOT>/proofs/v2/<proof_id>/lifecycle/<seq-4-digits>.json`,
beginning at `0000.json`, each event's `previous_event_digest` chaining to
the prior event (null only at sequence 0). States in strict order:
`CHALLENGE_CREATED` (0) → `ASSERTION_RECEIVED` (1) → `PROOF_VERIFIED` (2) →
`PROOF_VERIFIED_AND_BOUND` (3), or a terminal `EXPIRED`/`REVOKED`/`REJECTED`
event at any point. `HPACLifecycleStore` rejects gaps, duplicate sequences,
forks (a drifted repeat of the sequence-0 `binding` object), and broken hash
links (HPAC-REQ-094).

## 19. Genesis authority

Sequence 0 (`CHALLENGE_CREATED`) is **not** authoritative merely because its
hash-chain math is internally consistent — "hash matches" is explicitly
rejected as a genesis criterion by the predecessor phase's own verified
finding (HPAC-REQ-092's "digest agreement without successful attestation
verification is non-authority" principle, generalized to the lifecycle).
The trusted creator of sequence 0 is the **trusted challenge coordinator**
(HPAC-REQ-096: "`proof_id` is allocated by the trusted challenge
coordinator before sequence 0"), which itself only acts after a presentation
has already been resolved and attested (HPAC-REQ-097's Gate-3/Gate-5
sequencing, RDGO-001 §4's Gate-3 description). Concretely, the planned
genesis-gating condition is: sequence 0 may be created only by the same
protected coordinator process that already holds a resolved, attested
`TrustedApprovalPresentationEvidence` record for the exact `approval_id`
being challenged — a caller without that antecedent evidence cannot invoke
the code path that creates sequence 0 at all, closing the "caller mints
their own genesis" gap by construction rather than by a checkable field.

## 20. Lifecycle API

One narrow transition API, not a generic "create any event" method:

```python
class HPACLifecycleStore:
    def open_challenge(self, presentation_ref, binding) -> LifecycleEvent: ...       # seq 0, gated per §19
    def record_assertion(self, proof_id, assertion_digest) -> LifecycleEvent: ...    # seq 1
    def record_verified(self, proof_id, proof_digest, registry_state_digest, verifier_version) -> LifecycleEvent: ...  # seq 2
    def bind_gate5(self, proof_id, approval_digest) -> LifecycleEvent: ...           # seq 3, idempotent same-binding
    def terminate(self, proof_id, reason_code, state) -> LifecycleEvent: ...         # EXPIRED/REVOKED/REJECTED
```

Callers request a transition; only the store itself computes
`event_digest`, chains `previous_event_digest`, and enforces the exact
entry/exit conditions in HPAC-REQ-095's table. No caller can construct a
`LifecycleEvent` directly and have it accepted (mirrors §19's construction
gating).

## 21. Gate 5

Gate 5 (RDGO-001 §6, HPAC-001 §40.2) is a **read-and-revalidate** gate; it
consumes nothing. Exact production calls it must make: canonical
presentation resolution (`TrustedApprovalPresentationStore.resolve`),
canonical proof resolution (`HumanAuthenticationProofStore.resolve`),
principal-registry lookup (`HumanPrincipalRegistryStore.resolve_principal`/
`resolve_credential`), credential status check (same store), UP/UV flags
(from the resolved proof), challenge-binding check
(`HPACLifecycleStore`'s sequence-0 `binding` object), freshness check
(challenge/proof/presentation expiry against trusted clock), replay-state
check (existing sequence-3 event, if any, for same-binding idempotency),
approval-subject binding (`approval_subject_digest` equality across
presentation/proof/challenge), and attempt binding (RDGO-001's `attempt_id`,
bound at Gate 2, checked for consistency here). Success calls
`HPACLifecycleStore.bind_gate5`, which atomically creates sequence 3; no
store write consumes anything.

## 22. Gate 9

Exact atomic operation: **one** create-only write of
`RuntimeInvocationAuthorityConsumption` at
`<HPAC_PROTECTED_ROOT>/proofs/v2/<proof_id>/consumption.json`
(HPAC-REQ-098), containing the eight closed binding objects verbatim from
HPAC-001 §41 (`request_identity`, `repository_task_binding`,
`target_binding`, `prompt_binding`, `authority_binding`, `pb_binding`,
`runtime_enforcement_binding`, `dispatch_binding`). This single record
simultaneously constitutes: the durable `dispatch_attempted` marker, and
the consumption of the approval, presentation, challenge, and proof
(HPAC-REQ-071). There is exactly one authoritative store
(`RuntimeInvocationAuthorityConsumptionStore`) — no second "approval
consumed" flag anywhere else.

## 23. Crash safety

Per HPAC-REQ-100/RDGO-001 §10, the store recognizes exactly two
recoverable outcomes plus one unrecoverable one:

| State | Meaning | Behavior |
|---|---|---|
| No record | Not consumed | Full revalidation required before any new create attempt; no Gate-10 effect permitted |
| Valid complete record | Consumed | Replay rejected; no re-entry to Gate 9/10 with this authority |
| Partial/corrupt record | Durability-uncertain | Fail closed; no dispatch; manual recovery required — never interpreted as either consumed or unconsumed |
| Duplicate/conflicting record | Integrity violation | Fail closed; treated the same as corrupt |

All four fail closed; none defaults to permissive behavior.

## 24. Concurrency

Two concurrent Gate-9 attempts for the same `proof_id` are serialized to
exactly one winner via the same "protected evidence-store
transaction/serialization boundary" HPAC-REQ-099 requires: a
compare-and-create on the filesystem (open with `O_CREAT|O_EXCL` on a
same-filesystem temp-then-atomic-rename sequence, mirroring
`repository_identity._write_atomic`'s existing pattern) is inherently a
single-winner primitive — the loser's `O_EXCL` open fails, and the loser
must re-read the just-created record and treat it as "already consumed,"
never retry the create. No in-process lock is sufficient alone (multiple
OS processes might attempt Gate 9), so the store's exclusivity guarantee
must be filesystem-level, not just a Python `threading.Lock`.

## 25. Revocation

Revocation freshness is rechecked **immediately before** the Gate-9
compare-and-create, inside the same protected serialization boundary
(HPAC-REQ-099): principal status, credential status, presentation
descriptor/expiry, and proof/lifecycle state are all re-resolved against
current registry state at that exact moment, not cached from Gate 5. This
closes the TOCTOU window HPAC-REQ-063/064 describes (revocation between
Gate 5 and Gate 9 must fail closed) — the recheck happens inside, not
before, the boundary that decides whether the consumption record is
created.

## 26. B1

**Original finding**: `runtime_authority.ValidatedAuthorityProjection`
and `runtime_dispatch_permission`'s PB-request sealing both use a bare
module-level `object()` singleton (`_VALIDATED_AUTHORITY_SEAL`,
`_RUNTIME_DISPATCH_IDENTITY_SEAL`) checked only by identity
(`is _VALIDATED_AUTHORITY_SEAL`). `dataclasses.replace()` preserves the
`compare=False` seal field verbatim while every other field — including
`approval_id`, `record_digest`, `subject_scope_binding_digest` — can be
overwritten arbitrarily, producing a forged-but-"sealed" projection that
still reads as trusted.

**Repair**: replace the identity-only seal with an HMAC-keyed digest
computed over the projection's actual content (not a constant), using a
key held only by the trusted validator/builder process. A forged
`dataclasses.replace()` copy now fails because its content changed but its
HMAC did not follow. This was already scoped as a strengthening, not a new
normative semantic, by 149O.20L.7O.3W.1R.2 §9 ("RIHAC/PBRD require
'validator-issued evidence'... not a specific mechanism") — the repair
requires no contract change.

## 27. B7

**Original finding**: `runtime_dispatch_permission._identity_registration_digest`
is a plain, unkeyed, public-algorithm hash over
`(invocation_id, attempt_id, idempotency_key)`. It is never compared
against the durable `RuntimeDispatchIdentityTracker` files on disk at
builder time, so an attacker who calls `dataclasses.replace()` on a
`RuntimeDispatchIdentity` and re-invokes the same pure hash function
produces a self-consistent digest for any forged triple —
`build_runtime_dispatch_permission_broker_request` never re-reads
`.pcae/runtime-dispatch-identities/v1/**` to confirm actual registration.

**Repair**: `build_runtime_dispatch_permission_broker_request` must
re-read the exact canonical construction identity registry (not the
identity object it was handed) immediately before building the PB
request, and reject if the triple is not durably registered there. This
uses an already-existing mechanism (the on-disk
`RuntimeDispatchIdentityTracker`) applied at the point it was previously
skipped — no new store is required for B7 specifically.

## 28. N1

**Original finding**: `RuntimeInvocationApprovalStore.load` returns a bare
`RuntimeInvocationApproval` dataclass with no field or wrapper
distinguishing "read through the confined, create-only store" from
"constructed in-process by any caller." `validate_approval`'s own
docstring says the store-resolution step is "another caller's
responsibility," so a recomputed, schema-valid object can be handed
directly to `validate_approval` and pass, without ever having existed
canonically.

**Repair**: require canonical approval-store resolution as the only path
into `validate_approval` — the store's `load()` (and the internal creation
path) emits a store-sealed handle (same HMAC pattern as B1's repair, §26),
and `validate_approval` refuses any input that is not such a handle. Direct
in-memory approval construction must never become trusted authority,
whatever its field values.

## 29. N2

**Original finding**: `create_runtime_invocation_approval` accepts a
caller-supplied `approver_id`/`identity_evidence_kind` pair with no
independent verification that a real human confirmation or authentication
event ever occurred (`runtime_authority.py:858-860` per the freeze phase's
own citation).

**Repair**: RIASC-001 v3.0 §7 already retires both fields contractually,
replacing them with `principal_id` + `authentication_mechanism_id` +
`credential_id` + `authentication_proof_ref`. The production repair is to
extend `ApprovalProvenance` with these four fields and make
`create_runtime_invocation_approval` refuse to construct an approval unless
it is handed a fresh, successful HPAC-018-verification result (an
`AuthenticatedHumanPrincipal`, §19) — never a caller-supplied string of any
kind. This repair depends on Phases 1-4 existing first (there is nothing to
verify against until the registry/proof/presentation stores and verifier
exist), so it is sequenced into Phase 5, not sooner.

### Matrix D — Finding repair

| Finding | Production root cause | Planned repair | Verification phase |
|---|---|---|---|
| B1 | `_VALIDATED_AUTHORITY_SEAL`/`_RUNTIME_DISPATCH_IDENTITY_SEAL` are bare `object()` singletons checked only by identity; `dataclasses.replace()` preserves the `compare=False` seal while overwriting every trust-bearing field | HMAC-keyed digest over actual content, recomputed and compared at verification time, using a key held only by the trusted validator/builder | 2.1 |
| B7 | `_identity_registration_digest` is an unkeyed public-algorithm hash never compared against the durable on-disk `RuntimeDispatchIdentityTracker` registry at builder time | `build_runtime_dispatch_permission_broker_request` re-reads the durable registry for the presented triple and rejects if not actually registered | 2.1 |
| N1 | `RuntimeInvocationApprovalStore.load` returns a bare dataclass with nothing distinguishing store-resolved from in-process-constructed | Store emits an HMAC-sealed handle (same pattern as B1); `validate_approval` refuses any input that is not such a handle | 2.1 |
| N2 | `create_runtime_invocation_approval` accepts caller-supplied `approver_id`/`identity_evidence_kind` strings with no independent verification | `ApprovalProvenance` extended with `principal_id`/`credential_id`/`authentication_mechanism_id`/`authentication_proof_ref`; construction refuses anything but a fresh, successful HPAC-verified `AuthenticatedHumanPrincipal` | 2.1 (contract-shape) / 5 (full closure, since N2's repair value depends on B1/N1 already holding) |

## 30. PB integration

Smallest viable change: `project_human_authority_binding` /
`build_runtime_dispatch_permission_broker_request` (both in
`runtime_dispatch_permission.py`) must accept the typed RIHAC-001 v2.0
authority projection (`authority_projection_id`, `authority_projection_digest`,
`proof_validation_digest`, `registry_state_digest`, etc. — PBRD-001 §4 item
14's exact closed object) as their sole authority input, and must stop
accepting whatever ad hoc binding shape they currently accept for the field.
PB itself is not touched beyond this: it still "SHALL NOT authenticate
humans, parse FIDO2 assertions, read HPAC registries, receive raw proof
material" (PBRD-001 §7) — this is a type-narrowing repair at the
request-construction boundary, not new PB logic.

## 31. POL-004

`MissingHumanApprovalRule` behavior must remain unchanged for the
non-`runtime_dispatch` action types it already governs. For
`runtime_dispatch` specifically, PBRD-001 §8 already specifies: a valid
`RuntimeInvocationApproval` (post-Gate-5) makes `approval_present=true`
and POL-004's rule is not triggered; its absence may still produce
`HUMAN_REVIEW`. No planned phase changes this composition — Phase 5's
PB-integration change (§30) only narrows *what* counts as valid approval
evidence, not whether POL-004 applies.

## 32. POL-005

POL-005 (real-runtime hard deny) is preserved unmodified through every
phase in §52. Phase 1 (models/stores/deterministic fixtures) cannot enable
real dispatch because no dispatch code path consumes these stores yet.
Phase 2 (verifier + B1/B7/N1/N2 repair) only makes existing validation
*more* correct, never adds a new real-dispatch path. Phase 3 (real FIDO2)
only makes the authenticator interface have a second, real implementation
— it is not wired into RDGO-001's gates until authorized separately. Phase
4 (real presentation UI) is symmetric. No phase in this plan proposes
touching POL-005's own policy text or the runtime-availability flags
(`Observed`/`observe`/`unavailable`); that remains a distinct, separately
governed decision this phase does not make or recommend making.

## 33. RDGO

RDGO-001 v3.0's eleven-gate order (§1 table, reproduced faithfully here) is
unchanged by this plan: Prompt preparation (1) → target selection (2) →
human authority creation (3) → static preflight (4) → approval validation
(5) → Permission Broker (6) → Runtime Enforcement (7) → containment/live
preflight (8) → durable pre-dispatch record (9) → adapter dispatch (10) →
result capture (11). New components slot into existing gates: Phase 1's
stores are read/written inside Gates 3 (presentation+challenge+proof
creation), 5 (revalidation+binding), and 9 (consumption) exactly as those
gates are already specified; no gate is added, removed, reordered, or
reassigned to a different owner.

## 34. File plan

| File | New/Modified/Unchanged | Responsibility |
|---|---|---|
| `src/pcae/core/human_principal_registry.py` | New | `PrincipalRecord`/`CredentialRecord` models + `HumanPrincipalRegistryStore` (Phase 1) |
| `src/pcae/core/human_authenticator.py` | New | `HumanAuthenticator` Protocol, `MechanismDescriptor`/`MechanismStatus` models (Phase 1 interface, no implementation) |
| `src/pcae/core/human_authenticator_deterministic.py` | New | `DeterministicTestHumanAuthenticator` (Phase 1/2) |
| `src/pcae/core/human_authenticator_fido2.py` | New | `FIDO2HumanAuthenticator` (Phase 6, deferred) |
| `src/pcae/core/approval_presentation.py` | New | `ProtectedApprovalPresentationMechanism` Protocol, `CanonicalRuntimeApprovalSubject`, `TrustedApprovalPresentationEvidence` model + store (Phase 1) |
| `src/pcae/core/approval_presentation_deterministic.py` | New | `DeterministicTestPresentationMechanism` (Phase 1/2) |
| `src/pcae/core/approval_presentation_real.py` | New | real mechanism (Phase 7, deferred) |
| `src/pcae/core/human_authentication_proof.py` | New | `HumanAuthenticationProof` model + `HumanAuthenticationProofStore` (Phase 1) |
| `src/pcae/core/hpac_lifecycle.py` | New | `HumanAuthenticationProofLifecycleEvent` model + `HPACLifecycleStore` (Phase 1) |
| `src/pcae/core/runtime_invocation_authority_consumption.py` | New | `RuntimeInvocationAuthorityConsumption` model + store (Phase 1) |
| `src/pcae/core/hpac_verifier.py` | New | Gate-18 verification sequence, mechanism-neutral (Phase 3) |
| `src/pcae/core/runtime_authority.py` | Modified | `ApprovalProvenance` v2 fields; `create_runtime_invocation_approval` refuses caller-supplied provenance (N2); `validate_approval` requires store-sealed input (N1); `ValidatedAuthorityProjection` HMAC-keyed seal (B1) (Phase 5) |
| `src/pcae/core/runtime_dispatch_permission.py` | Modified | Re-read durable identity registry before request construction (B7); accept typed RIHAC v2 projection only (PB integration) (Phase 5) |
| `src/pcae/core/runtime_invocation_approval_store.py` | Modified | Emit store-sealed handle from `load()`/create path (N1) (Phase 5) |
| `src/pcae/core/hatp_bootstrap.py`, `hatp_fido2_provider.py`, `hatp_providers.py` | Unchanged | Pattern/library reuse only; no live dependency introduced |
| `src/pcae/core/permission_broker_foundation.py` | Unchanged | Existing PB evaluation logic untouched |

## 35. Reuse audit

Actual reusable existing helpers, identified by reading the source in this
phase:

- `repository_identity._write_atomic` (`src/pcae/core/repository_identity.py:153`) — atomic write-then-rename primitive, reused for every new store's create-only writes.
- `repository_identity.compute_repo_fingerprint` (existing, cited in RIHAC-001 §7) — repository identity, reused unchanged.
- `runtime_authority._canonical_json` / `_normalize_recursive` / `_digest` / `compute_canonical_digest` (`src/pcae/core/runtime_authority.py:65-99`) — exact NFC/sorted-key/SHA-256 canonicalization already implementing HPAC-REQ-089's rule; reused directly rather than reimplemented.
- `runtime_authority.new_approval_id` / `is_valid_approval_id` — ID-generation/validation pattern, reused (with a new prefix/regex) for `principal_id`, `proof_id`, `presentation_id`, etc.
- `hatp_bootstrap._reject_symlink`, `_require_nonempty_str`, `_require_timestamp`, `_require_revoked_at_consistency`, `_parse_registry_document`'s reject-on-anomaly discipline — pattern reuse for the new registry's parser (not a call into HATP's own parser).
- `hatp_providers.HardwareProviderCapabilities` / `discover_hardware_providers` / `create_production_hardware_provider` — static-descriptor and provider-discovery pattern for the future `FIDO2HumanAuthenticator` (Phase 6).
- `hatp_fido2_provider.Fido2HardwareProvider`, `_parse_fido2_evidence`, `_serialize_evidence`, `_payload_digest` — low-level CTAP2 parse/verify primitives, candidate library-level reuse for Phase 6 only (HPAC-REQ-019).
- `hatp_providers.TestHATPProofVerifierProvider` — existing precedent for a clearly-tagged simulation-only provider, reused as the pattern for §11's deterministic authenticator.
- `runtime_dispatch_permission.RuntimeDispatchIdentityTracker` — existing durable on-disk registry, reused (re-read, not replaced) for B7's repair.
- No existing canonical JSON/digest helper is a separate shared module today (`_canonical_json` lives inside `runtime_authority.py`); the new stores either import it from there or duplicate the same four functions locally — **recommendation**: import from `runtime_authority` to avoid duplication, since it is already the canonicalization authority for this contract family.

## 36. Dependency graph

```
schemas/models (HumanPrincipalRecord, CanonicalRuntimeApprovalSubject,
                TrustedApprovalPresentationEvidence, HumanAuthenticationProof,
                LifecycleEvent, AuthorityConsumption)
        |
        v
stores (RegistryStore, PresentationStore, ProofStore, LifecycleStore,
        ConsumptionStore)  -- each create-only/atomic, independently testable
        |
        v
deterministic mechanisms (DeterministicTestHumanAuthenticator,
                           DeterministicTestPresentationMechanism)
        |
        v
HPAC verifier (mechanism-neutral §18 sequence; exercised first against
               deterministic mechanisms only)
        |
        v
authority integration (RIHAC/RIASC v2 provenance fields, B1/B7/N1/N2 repair,
                        PB projection narrowing)
        |
        v
FIDO2 (real HumanAuthenticator implementation; verifier now exercised
       against real hardware too, no verifier-code change expected)
        |
        v
protected UI (real presentation mechanism; same relationship to the
              verifier as FIDO2's)
```

Each arrow is a phase boundary (§52); nothing downstream is required to
build or unit-test anything upstream.

## 37. First implementation slice

**Recommended smallest executable slice (Phase 1)**: `HumanPrincipalRegistry`
model/store + `TrustedApprovalPresentationEvidence` model/store +
`HumanAuthenticationProof` + `HPACLifecycleStore` model/store +
deterministic non-real `HumanAuthenticator`/`ProtectedApprovalPresentationMechanism`
implementations. **No PB integration, no `runtime_authority.py` change, no
RIHAC/RIASC production change** in this slice.

**Justification**: every one of these six pieces is independently unit-
testable today with no hardware, no human, and no dependency on anything
that does not yet exist — they are pure data-model/store correctness
(atomicity, canonicalization, corruption handling, hash-chain integrity).
Deferring the verifier (Phase 3) and the B1/B7/N1/N2 repairs (Phase 5) out
of this slice means Phase 1's independent verification (Phase 1.1) can
focus entirely on store correctness without also having to reason about
authority semantics — a materially smaller, more independently-checkable
unit of work, consistent with this repository's demonstrated preference
for narrow, independently verifiable phases (see the entire 149O.20L.7O.3W
lineage).

## 38. Adversarial tests

| Test | What it proves |
|---|---|
| Forged principal record | A hand-constructed `PrincipalRecord` never accepted by the store's read path as if it were canonically enrolled |
| Repo-controlled registry | Registry path resolution ignores repository/cwd/env/task overrides entirely |
| Fake presentation evidence | An evidence-shaped object without a valid `mechanism_attestation` fails verification even with correct-looking digests |
| Presentation/challenge mismatch | A presentation for approval A cannot bind a challenge for approval B |
| Blind touch | UP+UV true with no resolved presentation evidence never satisfies `PRINCIPAL_VERIFIED_INTENT` |
| Raw proof object | A hand-constructed `HumanAuthenticationProof` (never produced by sequence-2 verification) is rejected by the lifecycle store |
| Parallel hash chain | Two divergent sequence-1 events for the same `proof_id` are detected as a fork and rejected |
| Forked chain | A drifted repeat of the sequence-0 `binding` object is rejected as a fork |
| Stale proof | A proof past its challenge's `expires_at` fails Gate 5 revalidation |
| Revoked credential | Revocation between Gate 5 and Gate 9 is caught by Gate 9's immediate-before-create recheck |
| Duplicate Gate 9 | Two processes racing to create `consumption.json` for the same `proof_id` produce exactly one winner |
| Partial Gate-9 record | A truncated/corrupt `consumption.json` is treated as durability-uncertain, never as consumed or unconsumed |
| Cross-attempt replay | A proof bound to `attempt_id` A is rejected when presented for `attempt_id` B under the same `invocation_id` |

## 39. Hardware test levels

- **Level A — pure deterministic, no hardware**: all of §38's tests, run
  entirely against `DeterministicTestHumanAuthenticator`/
  `DeterministicTestPresentationMechanism`. Runs in ordinary CI, always
  available.
- **Level B — software/mock FIDO2 protocol fixture**: a CTAP2-shaped mock
  transport (no physical device) exercising `FIDO2HumanAuthenticator`'s
  parsing/verification code paths without real hardware I/O — validates
  the Phase 6 code against protocol-correct byte shapes.
- **Level C — real physical FIDO2 hardware**: an actual security key,
  requiring a human physically present. Not executed by this phase or any
  phase before Phase 3.1's independent hardware-backed verification
  (§52); described here only as the eventual target, not scheduled work.

## 40. UI test strategy

- Deterministic protected mechanism (Level A-equivalent): fully automated,
  no human, exercises the presentation-evidence schema and attestation
  logic.
- OS/UI adapter contract tests: once a real mechanism candidate (§14) is
  chosen, contract tests verify it correctly implements
  `ProtectedApprovalPresentationMechanism` (digest agreement, election
  ordering) without requiring a live human for every test run (e.g.,
  scripted UI-automation driving a real dialog).
- Human interaction tests (later, Phase 4.1/5): a real person actually
  performing the approval act, needed only for final independent
  verification, not for ordinary regression runs.

## 41. Platform strategy

macOS is the development platform; Linux is the deployment target. The
recommended design keeps the core (models, stores, verifier, HPAC
lifecycle logic) entirely OS-neutral — this is already true of HPAC-001's
primary mechanism, which is explicitly "offline capable... no OS-specific
adapter... FIDO2 CTAP2 hardware keys are portable across macOS and Linux"
(HPAC-REQ-082/083). Only the presentation mechanism (§14) is expected to
need a replaceable per-OS adapter; the authenticator interface (§9) does
not, since the primary real mechanism (FIDO2) is already OS-neutral.

## 42. Dependencies

Candidates, **not added now**: a Python FIDO2/CTAP2 library (e.g.
`python-fido2` or equivalent) for Phase 6 if `hatp_fido2_provider.py`'s
existing implementation does not already cover the needed CTAP2 surface —
requires reading that module in full during Phase 6 planning, not assumed
here. For Phase 7's real presentation UI, a UI toolkit dependency (native
or a lightweight cross-platform framework) if option 1 (§14) is chosen; no
new dependency if option 2 or 3 is chosen (both can use OS-native/existing
tooling). No dependency is added by Phases 1-2 (pure Python stdlib
suffices for models/stores/deterministic fixtures).

## 43. Credential security

`CredentialRecord` stores only `public_key` and `assurance_capabilities`
(HPAC-REQ-013) — no private key, PIN, biometric secret material, or
repository path is ever persisted, matching the contract's explicit
prohibition. This is a reference-only model by construction: the schema
itself has no field capable of holding a secret, so there is no runtime
check that could be bypassed — the impossibility is structural.

## 44. Artifact migration

Per HPAC-001 §38 and RIHAC-001's own versioning sections: there is
explicitly no valid pre-correction artifact to migrate, because no
conforming v2.0 presentation/lifecycle record could have existed before
this contract completion. Any old RIHAC v1.x/RIASC v1.x/v2.x approval
artifact remains historical evidence only and is never silently upgraded
or accepted by a v2/v3 validator — this plan introduces no migration path
and no compatibility shim; old artifacts simply fail validation under the
new schema versions, by design.

## 45. Inspect surfaces

**Decision**: future human-authentication status should surface through a
**separate authority/authentication inspect surface**, not folded into the
existing `pcae runtime inspect` command. **Justification**: `runtime
inspect` today reports runtime-target/adapter/dry-execution state; human
principal/credential/proof-lifecycle status is a categorically different
authority-domain concern (HPAC-001 §0's semantic walls explicitly separate
"human principal" from "runtime identity"). Mixing the two into one
command's output risks exactly the kind of conflation this contract family
has repeatedly had to correct (e.g., N2's approver-identity conflation).
This is a planning decision only — no command is modified or added by this
phase.

## 46. Internal APIs

Plan internal (non-CLI) APIs first: `HumanPrincipalRegistryStore`,
`TrustedApprovalPresentationStore`, `HumanAuthenticationProofStore`,
`HPACLifecycleStore`, and `RuntimeInvocationAuthorityConsumptionStore` are
all planned as importable Python APIs with no CLI surface in Phase 1. A
public enrollment or approval CLI is not part of the first foundation
slice — it is unnecessary until a real ceremony (Phase 5/6+) needs a human
entry point, and adding one earlier would create an attack surface with no
corresponding trust boundary to defend it yet.

## 47. Approval UX

A later command/UI is anticipated conceptually — e.g. something in the
shape of `pcae authority approve-runtime <invocation-id>` or a
repository-conventional equivalent — but no CLI name is frozen by this
phase. The actual UX depends on which real presentation mechanism (§14) is
eventually chosen, which is explicitly not decided here.

## 48. Enrollment UX

Planned as a categorically higher-authority, separate flow from ordinary
approval (§8) — never reachable from an ordinary `pcae` invocation, an
agent tool call, or same-UID execution (HPAC-REQ-024). Its eventual
command surface (if any) would live under protected-admin tooling
analogous to `hatp_deployment_binding_admin.py`'s existing admin-entrypoint
pattern, not under ordinary user-facing CLI commands.

## 49. Delegated-agent capability debt

Explicitly carried separately per HPAC-REQ-087: this contract's
authentication guarantee does not rely on, and is not weakened by, any
future delegated-subagent capability-bounding mechanism
(149O.20L.7O.3W.1R.2C's own named incident/debt). This plan does not
attempt to solve delegated-agent capability bounding through HPAC — "not
delegated" is never treated as proof of humanity anywhere in this design;
only a verified §18 proof is.

## 50. Older findings

The 3S.2.1 malformed-adapter-result finding (`docs/PHASE_149O_20L_7O_3S_2_1_...md`)
concerns Gate 11 (result capture): a forced malformed `collect()` return at
the `simulate_invocation` layer confirmed that a malformed adapter result
must never be persisted as a successful result document
(`test_malformed_adapter_result_never_persists_a_result_document`).
RDGO-001 §12 itself notes "This contract does not repair the existing
3S.2.1 malformed-result finding; that repair is blocking before the first
non-mock adapter becomes reachable." **This plan does not repair 3S.2.1.**
It becomes newly *reachable* (not yet urgent) once Phase 6/real-FIDO2
groundwork approaches an actual non-mock adapter path, since 3S.2.1 sits at
Gate 11 — after Gate 9's human-authority consumption this plan designs —
and must be closed before any real adapter dispatch, independent of and
in addition to everything in this plan.

## 51. Regression attribution

Conceptual plan only: this repository uses a `fast_green` test-selection
sentinel (referenced throughout `PROJECT_STATUS.md`/`tasks/DONE.md`) as its
fast regression gate for phase completion, and prior-cycle memory records
that its derived-correctness check is a literal-text scanner sensitive to
exact "N failed" phrasing and to `--deselect` argv-list handling. This
plan's regression strategy for future implementation phases: attribute
every new-phase test file to a fixed commit SHA at creation time (so a
`git diff <entry-commit>..HEAD -- <test-file>` self-check can prove no
scope creep), avoid inventing new custom process-group/parallelization
tooling beyond what `fast_green` already provides, and keep each phase's
new tests in their own new file(s) rather than editing shared/pre-existing
test files where avoidable — minimizing collision with the "N failed"
text-scanning gate. This section is planning-only; no test infrastructure
is touched by this phase.

## 52. Phase sequence

- **Phase 1**: canonical models/stores (§6, §34) + deterministic
  protected-presentation/proof fixtures (§11, §13). No verifier, no B1/B7/
  N1/N2 repair, no PB change.
- **Phase 1.1**: independent verification of Phase 1 (store atomicity,
  corruption handling, hash-chain integrity, deterministic-fixture
  adversarial coverage per §38's Level-A tests).
- **Phase 2**: HPAC verifier (§21/§18 sequence) + authority canonical
  revalidation logic, exercised only against Phase 1's deterministic
  fixtures + B1/B7/N1/N2 production source repair (§26-§29) + PB
  projection narrowing (§30).
- **Phase 2.1**: independent verification of Phase 2 (verifier correctness
  against every §38 adversarial case; confirm B1/B7/N1/N2 closure with
  fresh reproduction tests mirroring the original finding-reproduction
  discipline this repository already uses).
- **Phase 3**: real FIDO2 mechanism (`FIDO2HumanAuthenticator`, §10/§39).
- **Phase 3.1**: independent hardware-backed verification (Level B/C per
  §39), requiring actual physical hardware and a human tester.
- **Phase 4**: real protected approval presentation mechanism (§14).
- **Phase 4.1**: independent verification of Phase 4 (real presentation
  mechanism contract tests, §40).
- **Phase 5**: integrated human approval ceremony verification — the
  first end-to-end exercise of Gates 3/5/9 with real FIDO2 + real
  presentation together (not before both Phase 3 and Phase 4 are
  independently verified).
- **Phase 6**: only then reconsider Runtime Enforcement planning — this
  plan does not schedule Runtime Enforcement work before Phase 5's
  end-to-end verification exists, since Runtime Enforcement (RDGO-001
  Gate 7) sits strictly after Gate 5/9's human-authority machinery in the
  gate order.

No deviation from this sequence is proposed; §37's Phase-1 recommendation
is fully consistent with it (Phase 1 here matches §37's "first
implementation slice" exactly, and the B1/B7/N1/N2 repair is placed in
Phase 2 rather than Phase 1 for the same reason §37 gives).

### Matrix E — Implementation phases

| Phase | Scope | Effects allowed | Acceptance | Next verification |
|---|---|---|---|---|
| 1 | Canonical models/stores (registry, presentation evidence, proof, lifecycle, consumption) + deterministic authenticator/presentation fixtures | New files only; no `runtime_authority.py`/`runtime_dispatch_permission.py`/PB change | All Level-A adversarial tests (§38) pass; stores independently atomic/corruption-safe | 1.1 |
| 1.1 | Independent verification of Phase 1 | Test files only | Fresh, independently-authored suite reproduces Phase 1's claims | — |
| 2 | HPAC verifier + B1/B7/N1/N2 production repair + PB projection narrowing | Modifies `runtime_authority.py`, `runtime_dispatch_permission.py`, `runtime_invocation_approval_store.py`; adds verifier module | B1/B7/N1/N2 each independently reproduced-then-closed; no new BLOCKING; existing regression suite green | 2.1 |
| 2.1 | Independent verification of Phase 2 | Test files only | Independent verification confirms closure and no new blocking | — |
| 3 | Real FIDO2 mechanism (`FIDO2HumanAuthenticator`) | New authenticator module only; no dispatch-path change; hardware read-only | Level B/C tests (§39) pass in isolation from dispatch | 3.1 |
| 3.1 | Independent hardware-backed verification of Phase 3 | Verification only, real hardware | Independent hardware-backed verification succeeds | — |
| 4 | Real protected approval presentation mechanism | New presentation-mechanism module only; no dispatch-path change | UI adapter contract tests (§40 tier 2) pass | 4.1 |
| 4.1 | Independent verification of Phase 4 | Verification only | Independent verification succeeds | — |
| 5 | Integrated human approval ceremony verification (Gates 3/5/9, real FIDO2 + real presentation together) | Wiring/integration only; POL-005 still denies | End-to-end ceremony proven; POL-005 confirmed still denying | Self-verifying (integrated) |
| 6 | Runtime Enforcement planning reconsidered | Out of this document's scope | A new planning phase, not this one | N/A |

## 53. Stop boundaries

| Phase | Allowed files | Prohibited effects | Hardware/network | Acceptance | Verification phase |
|---|---|---|---|---|---|
| 1 | New files listed §34 (models/stores/deterministic fixtures only) | No `runtime_authority.py`/`runtime_dispatch_permission.py`/PB change; no real mechanism | None | All §38 Level-A tests pass; stores independently atomic/corruption-safe | 1.1 |
| 1.1 | Test files only (independent, fresh) | No production change | None | Fresh, independently-authored suite passes against Phase 1 code | (self-terminating) |
| 2 | `hpac_verifier.py` (new) + `runtime_authority.py`, `runtime_dispatch_permission.py`, `runtime_invocation_approval_store.py` (B1/B7/N1/N2 repair only) | No real FIDO2/UI; no PB policy text change beyond typed-projection narrowing | None | Verifier passes all §38 cases against deterministic fixtures; B1/B7/N1/N2 fresh reproduction tests fail-then-pass | 2.1 |
| 2.1 | Test files only | No production change | None | Independent re-derivation of closure from contract text, per this repository's existing verification discipline | (self-terminating) |
| 3 | `human_authenticator_fido2.py` (new) | No presentation-mechanism change; no gate wiring beyond authenticator interface | Real FIDO2 hardware required for Level C | Level A/B pass without hardware; Level C requires human + device | 3.1 |
| 3.1 | Test files only | No production change | Real hardware, one human tester | Same-user-agent resistance (HPAC-REQ-086) affirmatively demonstrated | (self-terminating) |
| 4 | `approval_presentation_real.py` (new) + chosen platform adapter | No authenticator change | Real display; may require OS-level dialog APIs, no network | Contract tests pass; `agent_substitution_resistant` demonstrated | 4.1 |
| 4.1 | Test files only | No production change | Real UI, human tester | Independent confirmation of §14's chosen mechanism's guarantees | (self-terminating) |
| 5 | Gate wiring across `runtime_authority.py`/RDGO gate implementations (not yet existing as executable gates; scope TBD at Phase 5 planning) | No Runtime Enforcement activation; POL-005 unchanged | Real FIDO2 + real UI together | End-to-end Gate 3/5/9 exercise with real human, real hardware | Phase 5's own independent verification (not yet named) |
| 6 | N/A — planning phase only | No implementation | None | Runtime Enforcement planning phase, itself producing another planning document | Its own future verification |

## 54. Final recommendation

Proceed with **Phase 1 exactly as scoped in §37/§52**: canonical
models/stores for `HumanPrincipalRegistry`, `TrustedApprovalPresentationEvidence`,
`HumanAuthenticationProof`, and the HPAC hash-chained lifecycle, plus
deterministic non-real `HumanAuthenticator`/`ProtectedApprovalPresentationMechanism`
implementations — with no PB integration, no `runtime_authority.py`
production change, and no B1/B7/N1/N2 repair in this first slice. This is
the smallest unit of work that is both independently meaningful (it makes
every downstream layer testable) and independently verifiable (Phase 1.1
can assess it in isolation, without also having to reason about authority
semantics that do not yet exist). Real FIDO2 (Phase 3) and real protected
UI (Phase 4) remain deferred until their respective prerequisite phases are
independently verified; B1/B7/N1/N2 production repair is sequenced into
Phase 2, immediately after the verifier exists to test against, since a
repair without a verifier to validate it against would itself be
unverifiable.

## 55. Human decision required

A human MUST authorize Phase 1 (§37/§52/§53) before any code is written.
This phase produces no code and takes no such authorization itself. In
particular, the human should confirm: (a) the Phase 1 scope boundary in
§53 is acceptable as the first implementation phase; (b) the
component-inventory consolidation in §6 (fewer files than a
naive one-class-one-file reading would produce) is an acceptable design
simplification; and (c) the inspect-surface decision in §45 (separate
surface, not folded into `runtime inspect`) is acceptable, since it affects
future CLI surface area even though no command changes in this phase.

---

```
IMPLEMENTATION PLANNING: COMPLETE
VERIFIED CONTRACT BASELINE: RIHAC 2.0, RIASC 3.0, HPAC 2.0, PBRD 2.0, RDGO 3.0, RPAC 1.0
FIRST IMPLEMENTATION SLICE: HumanPrincipalRegistry model/store + TrustedApprovalPresentationEvidence model/store + HumanAuthenticationProof + HPACLifecycleStore model/store + deterministic non-real HumanAuthenticator/ProtectedApprovalPresentationMechanism implementations (no PB integration, no runtime_authority.py change)
REAL FIDO2: DEFERRED
REAL PROTECTED UI: DEFERRED
DETERMINISTIC TRUST FIXTURES: PLANNED FIRST
B1/B7/N1/N2: PRODUCTION REPAIR SEQUENCED
POL-005: PRESERVED
RUNTIME: Observed / observe / unavailable
NEXT: Phase 1 — canonical human-principal/presentation/proof-lifecycle models and stores plus deterministic authenticator/presentation fixtures (human authorization required before code is written)
HUMAN DECISION: REQUIRED
```
