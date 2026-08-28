# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.4 — Mechanism-Neutral HPAC Verifier
# and Principal-Registry Consumption Boundary Implementation Planning

**Phase type:** Planning/reconciliation only. No `src/pcae/` production
change, no verifier implementation, no trust-path modification, no
B1/B7/N1/N2 repair, no PB change, no Runtime Enforcement, no Shell Gate,
no FIDO2/hardware, no network, no relaxation of POL-005. Runtime remains
`Observed` / `observe` / `unavailable`.

**Predecessor:** Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3.2.2.1 — independent
verification that closed Finding P (protected-presentation attestation
schema) and Finding C (canonical-store containment). The Layer-1/2
foundation (canonical models/stores, deterministic mechanisms, HPAC
lifecycle, inert Gate-9 primitive) is treated here as independently
verified implementation fact, not re-derived.

---

## 1. Purpose

The original implementation-planning artifact,
`149O.20L.7O.3W.1R.2B.1R.1.1R.2` (hereafter **".1R.2"**), scoped and
justified the now-complete foundation work, and sketched the phases after
it. Its own §1 states the design is "expressed as eight non-collapsible
layers," but its concrete phase sequence (§52, "Matrix E") never lists
eight layers — it lists ten numbered sub-phases (1, 1.1, 2, 2.1, 3, 3.1, 4,
4.1, 5, 6), and its "Phase 2" bundles the mechanism-neutral HPAC verifier
together with the B1/B7/N1/N2 production-authority repair.

Now that the foundation is independently verified, the next work must be
deliberately re-planned rather than inferred by silently treating ".1R.2
Phase 2" as the next governed phase. This document:

1. Reconstructs what ".1R.2 §1's eight layers" actually correspond to in
   §52's concrete sequence.
2. Determines whether the verifier can be implemented and independently
   verified before B1/B7/N1/N2 repair, as its own governed phase.
3. Produces a precise implementation plan for that standalone verifier +
   registry-consumption boundary — inputs, outputs, ownership, anti-transfer
   model, failure model, threat matrix, test plan — sufficient for a future
   implementation phase to execute without re-deriving contract text.
4. Freezes exact next-phase IDs/titles for the immediate next steps.

No verifier code is written in this phase. No production trust-path file
is touched.

## 2. Verified foundation state (treated as ground truth, not reopened)

Confirmed present in `src/pcae/core/` and independently verified through
`.1R.1` → `.1R.3.2.2.1`:

| Module | Purpose | Key types |
|---|---|---|
| `hpac_foundation.py` | Shared trust-root/provenance foundation. Every HPAC store below is built on this — **the existing canonical persistence pattern; §30 reuses it, does not reinvent it.** | `HPACStoreAuthority` (`.fixture(root)` / `.production()`, `authority_class ∈ {FIXTURE_NON_REAL, PRODUCTION}`, `is_real_runtime_eligible`); `HPACWriterCapability` (opaque, constructor-sealed via `_WRITER_CONSTRUCTOR_SEAL`); `HPACResolvedRecord[T]` (record + non-serialized provenance: `authority_class`, `store_id`, `record_digest`, `record_path`, `writer_role`, `writer_subject`; constructor-sealed); `ProtectedAdminCapability` (legacy fixture-only marker, cannot authorize production); plus `write_atomic_create_only`/`write_atomic_replace`/`read_canonical_json_document`/`canonical_digest`/`resolve_hpac_protected_root()` helpers |
| `human_principal_registry.py` | Canonical trust root; authorized writer provenance | `PrincipalRecord`, `CredentialRecord`, `HumanPrincipalRegistryStore` (`resolve_principal`, `resolve_canonical_principal → HPACResolvedRecord[PrincipalRecord]`, `resolve_credential`, `resolve_canonical_credential`, `enroll_principal`, `revoke_principal`, `enroll_credential`, `revoke_credential`, plus preview variants) |
| `approval_presentation.py` | Authoritative installed-mechanism provenance; HPAC-REQ-092 8-field attestation (independently verified exact-match, `.1R.3.2.2.1`) | `CanonicalRuntimeApprovalSubject`, `PresentationMechanismDescriptor`/`Store`, `TrustedApprovalPresentationEvidence`, `ProtectedApprovalPresentationMechanism` (Protocol), `TrustedApprovalPresentationStore` |
| `approval_presentation_deterministic.py` | Deterministic NON-REAL presentation mechanism | `DeterministicTestPresentationMechanism` |
| `human_authentication_proof.py` | Canonical proof writer provenance; caller-created proof cannot become authority | `HumanAuthenticationProof`, `HumanAuthenticationProofStore` (`create`, `create_canonical`, `resolve`, `resolve_canonical`) |
| `human_authenticator.py` / `human_authenticator_deterministic.py` | Mechanism-neutral authenticator abstraction; deterministic NON-REAL implementation | `HumanAuthenticator` (Protocol), `MechanismDescriptor`, `MechanismStatus`, `Challenge`, `ProofMaterial`, `AssuranceLevel`; `DeterministicTestHumanAuthenticator` (fixed non-real `MECHANISM_ID`) |
| `hpac_lifecycle.py` | Hash-chained lifecycle: genesis, predecessor validation, fork/gap/duplicate rejection, canonical-store containment (independently verified `.1R.3.2.2.1`) | `LifecycleEvent`, `HPACLifecycleStore`, `HPACLifecycleForkError`/`GapError`/`StateError`, per-role `fixture_*_writer` capability factories |
| `runtime_invocation_authority_consumption.py` | The **Gate-9 primitive**: plan-authorized, canonical-store confined, inert, not production-wired | `RuntimeInvocationAuthorityConsumption`, `new_inert_consumption_record(...)`, `RuntimeInvocationAuthorityConsumptionStore` (`create`, `resolve`) |

`hpac_verifier.py` **does not exist**. No production consumption path
converts these authoritative canonical records into a verified
authenticated-principal result. `runtime_authority.py` and
`runtime_dispatch_permission.py` are untouched by any of the foundation
work (still pre-verifier `ApprovalProvenance` shape).

## 3. Current production gap

**B1 — contract closed / implementation open.** `_VALIDATED_AUTHORITY_SEAL`/
`_RUNTIME_DISPATCH_IDENTITY_SEAL` are bare `object()` identity-only seals,
forgeable via `dataclasses.replace()`. Repair: HMAC-keyed content digest.

**B7 — contract closed / implementation open.**
`_identity_registration_digest` is an unkeyed hash never checked against
the durable `RuntimeDispatchIdentityTracker`. Repair: re-read the registry
at builder time.

**N1 — contract closed / implementation open.**
`RuntimeInvocationApprovalStore.load` returns a bare, unmarked dataclass.
Repair: HMAC-sealed handle; `validate_approval` refuses non-handle input.

**N2 — contract closed / implementation open.**
`create_runtime_invocation_approval` accepts a caller-supplied
`approver_id` string. Repair: require a fresh `AuthenticatedHumanPrincipal`
produced by HPAC verification, never a caller-supplied string. **N2's
repair is the one production repair that structurally depends on the
verifier existing** — this is load-bearing for §8's central decision below.

None of B1/B7/N1/N2 is touched in this phase.

## 4. Planning-conflict reconstruction

### 4.1 What ".1R.2 §1" claims: "eight non-collapsible layers"

No section of `.1R.2` enumerates eight layers by name; §1 asserts the
count and cross-references §52, but §52 is a ten-item *phase* sequence,
not an eight-item *layer* list. Reconstructing the only decomposition
consistent with both the "eight" claim and §52's actual content requires
splitting §52's Phase 1 into three responsibilities and Phase 2 into two:

| # | Layer (reconstructed) | Corresponds to `.1R.2 §52` |
|---|---|---|
| L1 | Canonical models and stores (registry, presentation-evidence, proof, lifecycle, consumption) | Phase 1 (models/stores half) |
| L2 | Deterministic protected-presentation mechanism | Phase 1 (deterministic presentation half) |
| L3 | Mechanism-neutral HPAC verifier + principal registry consumption | Phase 2 (verifier half) |
| L4 | Deterministic/mock authentication proof path | Phase 1 (deterministic authenticator half) |
| L5 | B1/B7/N1/N2 production authority repair | Phase 2 (repair half) |
| L6 | Real FIDO2 mechanism | Phase 3 |
| L7 | Real protected human approval UI | Phase 4 |
| L8 | Independent end-to-end verification | Phase 5 |

(Phase 6, Runtime Enforcement planning, is explicitly out of scope of both
models and is not one of the eight layers.)

### 4.2 What `.1R.2 §52`/Matrix E actually schedules

```
Phase 1   — canonical models/stores + deterministic fixtures   [L1+L2+L4]
Phase 1.1 — independent verification of Phase 1
Phase 2   — HPAC verifier + B1/B7/N1/N2 repair + PB narrowing  [L3+L5, BUNDLED]
Phase 2.1 — independent verification of Phase 2
Phase 3   — real FIDO2                                         [L6]
Phase 3.1 — independent hardware-backed verification
Phase 4   — real protected presentation UI                     [L7]
Phase 4.1 — independent verification
Phase 5   — integrated e2e ceremony (Gates 3/5/9)               [L8]
Phase 6   — Runtime Enforcement planning (out of scope)
```

Phase 1 already correctly keeps L1/L2/L4 together as one phase (this
matches "eight layers" reasoning too: they are the deterministic,
non-authority-bearing foundation, safely built and verified together, and
this repository already executed them together and separately verified
the result five times over — `.1R.3`, `.1R.3.1`, `.1R.3.2`, `.1R.3.2.1`,
`.1R.3.2.2`, `.1R.3.2.2.1`). The only unresolved bundling is Phase 2 = L3 +
L5.

### 4.3 `.1R.2`'s own stated rationale for that bundling (§54)

> "B1/B7/N1/N2 production repair is sequenced into Phase 2, immediately
> after the verifier exists to test against, since a repair without a
> verifier to validate it against would itself be unverifiable."

This is a **sequencing** argument (repair must come after the verifier
exists), not a **packaging** argument (repair must be in the same governed
phase as the verifier). Sequencing "verifier, then repair" is fully
satisfied by two consecutive governed phases; it does not require them to
be one phase.

## 5. Reconciliation decision

```
OLD PLAN (.1R.2 §52, Phase 2 = L3+L5 bundled)
        ↓
VERIFIED IMPLEMENTATION EXPERIENCE
  — L1/L2/L4 (old Phase 1) were built and independently verified as one
    coherent, non-authority-bearing unit, then required THREE further
    repair/re-verify rounds at fine granularity (.3.1→.3.2→.3.2.1→.3.2.2→
    .3.2.2.1) before Findings P and C closed. This repository's own
    demonstrated practice is fine-grained, single-responsibility governed
    phases with a dedicated independent-verification phase after each,
    not larger bundled phases.
  — N2's repair explicitly requires a fresh `AuthenticatedHumanPrincipal`
    from the verifier (§3 above) — i.e. repair is a *consumer* of the
    verifier's output, and the verifier's own contract (HPAC-REQ-056)
    requires every consumer to re-run full verification, not reuse a
    cached result. A repair phase that also builds the verifier it
    consumes cannot itself be independently verified without first
    independently verifying the verifier it depends on — the same
    "downstream depends on independently verified upstream" discipline
    already used for L1/L2/L4 → L3.
        ↓
REVISED IMPLEMENTATION SEQUENCE
  L3 (verifier) becomes its own governed implementation phase with its own
  independent-verification phase, BEFORE L5 (B1/B7/N1/N2 repair) begins.
  L5 then consumes the independently-verified verifier rather than being
  built and verified in the same phase as the thing it depends on.
```

`.1R.2` remains historical evidence and is not overwritten. This document
supersedes only its Phase-2 packaging decision, not its Phase 1/3/4/5/6
scoping, its contract analysis, or its component inventory.

## 6. Central planning decision — is the verifier separable from L5?

**Yes.** Re-derived from contracts and production dependencies, not
assumed:

- The verifier (HPAC-001 §18/HPAC-REQ-054) consumes only the already
  independently-verified L1/L2/L4 canonical stores (§2 table above). It
  needs no B1/B7/N1/N2 repair to exist, and no PB/runtime-authority change,
  to be built and tested.
- Its output, `AuthenticatedHumanPrincipal` (HPAC-REQ-056), is contractually
  ephemeral and non-serializable (HPAC-REQ-058) — it cannot leak into
  production authority merely by existing; nothing consumes it until L5
  explicitly wires N2 to call it.
- `runtime_authority.py`/`runtime_dispatch_permission.py`/
  `runtime_invocation_approval_store.py` (the B1/B7/N1/N2 files) are not
  touched by building the verifier — L5 modifies those files, L3 does not.
- PB (PBRD-001 §7) is untouched — PB never receives raw proof material,
  never calls the verifier directly, and remains bound only to the RIHAC
  v2 projection reference produced downstream of Gate 5, which is later
  than both L3 and L5.
- RuntimeInvocationApproval repair (N2) is a **consumer** of the verifier,
  confirmed above — not a co-requisite for building it.

Separation holds under all five criteria in the governing prompt: the
verifier can consume trusted canonical HPAC state, produce a
mechanism-neutral non-authorizing result, remain unconsumed by production
runtime authority, remain independent of PB, and remain independent of
RuntimeInvocationApproval repair. No carve-out is forced for cleanliness —
it falls out of the contract's own trust boundaries.

## 7. Verifier responsibilities

The verifier's algorithm is **already normatively specified** in
HPAC-001 §18 (HPAC-REQ-054) — this phase does not invent it, it plans the
implementation of the existing specification:

1. Resolve the canonical `RuntimeInvocationApproval`/challenge and the
   `HumanAuthenticationProof` it references.
2. Resolve registry/credential status for the claimed principal
   (`human_principal_registry.py`) and validate subject/scope binding.
3. Resolve `trusted_presentation_ref` and confirm its mechanism
   descriptor/attestation prove the exact canonical facts were displayed
   through a non-substitutable channel (reject lookalikes, blind touch,
   display/challenge mismatch — B-3).
4. Verify the assertion against the resolved credential's public key.
5. Verify UP **and** UV both true for real-runtime authority; reject
   UP-only/UV-only/downgrade attempts.
6. Verify freshness against a trusted clock (non-expired).
7. Resolve the full HPAC lifecycle and Gate-9 consumption path; accept
   only fresh-or-already-`PROOF_VERIFIED_AND_BOUND`-to-this-exact-binding
   state; reject cross-binding, expired, revoked, or replayed proofs.
8. Atomically create the `PROOF_VERIFIED_AND_BOUND` lifecycle event
   (idempotent on a byte-identical same-binding repeat) and emit the
   ephemeral `AuthenticatedHumanPrincipal` (HPAC-REQ-055/056).

No step is a shortcut. All eight are the verifier's responsibility; none
is deferred to a later production authority adapter.

## 8. Verifier non-responsibilities (explicit exclusions)

The verifier does **not**:

- Return PB `ALLOW`, evaluate POL policies, or authenticate for PB
  (PBRD-001 §7 — PB validates only the typed RIHAC v2 projection
  reference/digest, never raw proof material).
- Implement Gate 5's read-and-revalidate ephemeral-projection construction
  (RDGO-001 §6) — the verifier provides the reusable core logic Gate 5
  will call, but does not itself produce the Gate-5 authority projection
  object.
- Implement or call Gate 9's consumption write (RDGO-001 §10) — it must
  not consume `dispatch_attempted`, must not treat itself as the one-shot
  authority boundary.
- Repair B1, B7, N1, or N2, or touch `runtime_authority.py`,
  `runtime_dispatch_permission.py`, or `runtime_invocation_approval_store.py`.
- Implement real FIDO2 or a real presentation UI — it consumes the
  existing `HumanAuthenticator`/`ProtectedApprovalPresentationMechanism`
  Protocols, which the deterministic implementations already satisfy.
- Persist a cacheable/reusable "verified" flag — HPAC-REQ-058 requires
  every consumer to re-run full verification against current registry
  state; the verifier must not offer a shortcut that violates this.

## 9. Input contracts

The verifier consumes, by canonical resolution (never caller-supplied
objects):

| Input | Source | Resolution method |
|---|---|---|
| Canonical approval/challenge | RIASC-001 v3.0 record | `RuntimeInvocationApprovalStore` (existing) |
| Human authentication proof | `human_authentication_proof.py` | `HumanAuthenticationProofStore.resolve_canonical` |
| Principal/credential | `human_principal_registry.py` | `HumanPrincipalRegistryStore.resolve_canonical_principal` / `resolve_canonical_credential` — **never** a caller-provided `PrincipalRecord` |
| Presentation evidence | `approval_presentation.py` | `TrustedApprovalPresentationStore.resolve_canonical` |
| Mechanism descriptor/installation | `PresentationMechanismDescriptorStore` | existing store |
| Lifecycle chain | `hpac_lifecycle.py` | `HPACLifecycleStore` (existing narrow transition API) |

Every input resolves through an `HPACResolvedRecord`-carrying store, so
`authority_class`/`writer_role`/`writer_subject`/`record_digest` provenance
is available to the verifier for every fact it relies on — it must not
accept any of these as bare caller-constructed dataclasses.

## 10. Output contract

`AuthenticatedHumanPrincipal` is the **existing, frozen contract type**
for the verifier's result (HPAC-REQ-056/057/058) — this plan does not
invent a new type name. Its defining properties, already normative:

- Trusted-construction only: producible solely as HPAC-001 §18's return
  value, never caller-constructed.
- **Ephemeral and non-serializable** — only the underlying proof/lifecycle
  evidence persists; the result object itself is not written to disk, not
  JSON-encodable, cannot be logged as a durable artifact.
- Every consumption must re-run full §18 verification against current
  registry state — a stored/cached verification result is not by itself
  sufficient trust for a later consumer.

This directly answers §12–13 of the governing prompt: persistence,
anti-transfer, and "copied result" resistance are already closed by
contract, by construction — a value that cannot be serialized cannot be
copied out of the verifier's call stack in the first place. The
implementation plan's job is to make the Python type actually enforce
this (no `__reduce__`/pickling, no `to_dict`, no JSON store), not to add
new binding fields beyond what HPAC-REQ-056 already requires.

## 11. Trust/provenance model

Every field the verifier reasons about is fetched via canonical resolvers
returning `HPACResolvedRecord`-wrapped values (§9), so provenance is
carried automatically. The verifier itself introduces no new writer
capability except the lifecycle-role writer it already needs
(`fixture_verifier_writer`/production equivalent from `hpac_lifecycle.py`,
already present) to append the `PROOF_VERIFIED_AND_BOUND` event.

## 12. Anti-transfer model

Because `AuthenticatedHumanPrincipal` cannot be serialized (§10), the two
threat scenarios in the governing prompt are handled as follows:

- **Attacker copies a valid verified-principal result** — impossible to
  persist or transmit a genuine instance outside the verifying call's
  stack; nothing downstream can accept a "copy" because nothing downstream
  is designed to accept the type as an argument from outside the verifier
  call itself (only L5's future N2 repair constructs a caller path, and
  that path calls the verifier directly, not a stored value).
- **Attacker constructs an identical-looking verified result** — blocked
  by trusted-construction (only the verifier's own `__init__`/factory can
  produce one; no public constructor), matching the pattern already used
  by `HPACWriterCapability`/`HPACResolvedRecord` (`_WRITER_CONSTRUCTOR_SEAL`
  or equivalent sealed-construction guard).

No additional binding fields (invocation identity, challenge, presentation
evidence, proof identity, principal, mechanism, lifecycle state, freshness)
need to be invented — HPAC-REQ-054's eight-step algorithm already re-checks
every one of these on every call, and re-verification-per-consumption
means a "stolen" result can never substitute for a real check.

## 13. Assurance classification / deterministic NON-REAL handling

The deterministic mechanism (`DeterministicTestHumanAuthenticator`,
`DeterministicTestPresentationMechanism`) may satisfy UP=true, UV=true, and
pass every verifier step, and must still be represented in the output as
**NON-REAL**, never as "real authenticated human principal." This
distinction is encoded, not documented, via:

- `AssuranceLevel`/mechanism identity already carried on
  `MechanismDescriptor` (fixed non-real `MECHANISM_ID` on the deterministic
  implementation, §2 table).
- `HPACStoreAuthority.authority_class` (`FIXTURE_NON_REAL` vs `PRODUCTION`)
  already propagated through every `HPACResolvedRecord` the verifier reads.
- The verifier must copy the resolved mechanism's assurance
  class/`authority_class` onto the `AuthenticatedHumanPrincipal` it
  constructs (a field HPAC-REQ-056 already anticipates), so "deterministic
  verification success" and "real human authentication" are structurally
  distinguishable in every consumer without re-deriving it from mechanism
  ID string matching.

## 14. Principal registry consumption

`principal_id → HumanPrincipalRegistryStore.resolve_canonical_principal →
AuthoritativeCurrentPrincipal` (via `HPACResolvedRecord[PrincipalRecord]`).
The verifier must not accept an arbitrary `PrincipalRecord` from a caller.
Fail-closed for: missing principal, duplicate/conflicting principal,
revoked principal, fixture-only principal presented where real assurance
is required, and assurance-ineligible principal (§16/§27 below).

## 15. Proof, presentation, and lifecycle consumption

Proof: `HumanAuthenticationProofStore.resolve_canonical`, never a caller
object; canonicality/currentness enforced at resolution. Presentation:
`TrustedApprovalPresentationStore.resolve_canonical`, mechanism-installation
resolved via `PresentationMechanismDescriptorStore`. Lifecycle: the
verifier reads the full hash-chained history via `HPACLifecycleStore`'s
existing narrow API and appends exactly one `PROOF_VERIFIED_AND_BOUND`
event through its lifecycle-role writer capability — it does not implement
its own chain logic; `HPACLifecycleForkError`/`GapError`/`StateError` are
reused, not reimplemented.

## 16. Credential relationship

Re-derived from HPAC-001/RIHAC-001 directly (not imported from HATP/FIDO2):
credential identity, principal↔credential relationship, current status,
and revocation are all already modeled in `human_principal_registry.py`'s
`CredentialRecord` and `revoke_credential`/`revoke_principal` methods.
Mechanism compatibility is a property the verifier checks (credential's
declared mechanism vs. the resolved `MechanismDescriptor`), not a
HATP/FIDO2-specific concept baked into the verifier core.

## 17. UP / UV semantics

UP and UV remain mandatory and are checked as two independent booleans
(§7 step 5 above). The verifier must not fold them into a single "assurance
passed" flag — HPAC-REQ-054 requires rejecting UP-only/UV-only/downgrade
explicitly, which requires the two booleans to remain individually visible
in the verifier's internal decision trail (useful for diagnostics/tests,
§28) even though the external result type communicates NON-REAL/real
assurance via mechanism classification (§13), not via exposing UP/UV
directly to callers.

## 18. Replay and lifecycle validation ownership

The verifier **validates and consumes** the lifecycle transition to
`PROOF_VERIFIED_AND_BOUND` (§7 step 7–8) — this is explicitly allowed by
HPAC-001 §18/RDGO-001 §6: Gate 5 "atomically creates lifecycle sequence 3
`PROOF_VERIFIED_AND_BOUND` (idempotent same-binding repeat allowed)" and
the verifier is the reusable core Gate 5 will call to do exactly this. It
is **not** Gate 9: Gate 9 (RDGO-001 §10) is the separate, later, one-shot
`consumption.json` write that atomically consumes the approval binding
itself (`dispatch_attempted`). The verifier must never write to the
consumption store; only its lifecycle-role writer for the
`PROOF_VERIFIED_AND_BOUND` event.

## 19. Gate 5 relationship

The verifier implements the reusable validation core of the future Gate 5
(RDGO-001 §6): resolve canonical approval/proof/lifecycle/registry/
presentation/mechanism-attestation, re-run RIHAC-001 v2.0 validation,
produce the ephemeral validated result. Gate 5 itself (not built in this
phase) will additionally construct RDGO-001 §6's specific ephemeral
validated-authority projection object (approval/subject/authority-
projection digests, freshness/consumption-state verdicts, etc.) — a
Gate-5-specific wrapper around a fresh verifier call, not a second
independent implementation of §18's steps. No state may be cached across
the Gate-5→Gate-9 interval; each of Gate 5's own future invocations must
call the verifier fresh, per HPAC-REQ-058.

## 20. Gate 9 relationship

Out of scope for implementation. The verifier plan treats
`runtime_invocation_authority_consumption.py`'s inert primitive purely as
future downstream infrastructure: the verifier's `AuthenticatedHumanPrincipal`
and the lifecycle event it writes will eventually be inputs to a future
Gate-9 consumption write, but this phase and the verifier-implementation
phase that follows it do not call, wire, or extend that store.

## 21. Gate 10

Completely out of scope. No verifier phase approaches execution;
Gate 10 (first external effect) is untouched by name or reference beyond
this statement.

## 22. B1/B7/N1/N2 production repair separation

A dedicated later phase (§26 below) performs B1/B7/N1/N2 repair,
consuming the independently-verified verifier from this planning's
immediate next phase. Rationale for separation is §5/§6 above. That later
phase is the first to modify `runtime_authority.py`,
`runtime_dispatch_permission.py`, and `runtime_invocation_approval_store.py`.

## 23. PB separation

Permission Broker remains fully downstream. The verifier must not return
PB `ALLOW`, evaluate POL policies, authenticate for PB, or create runtime
capability. Future flow remains: verified authenticated-principal
authority → Gate 5's typed RIHAC authority projection → PB. These three
steps are not merged in the verifier's design.

## 24. Runtime authority separation

No planned changes to `runtime_authority.py` or
`runtime_dispatch_permission.py` in the verifier-implementation phase. The
verifier is planned as new, isolated modules (`hpac_verifier.py` + tests)
only.

## 25. Real FIDO2 / protected UI remain later (L6/L7)

Not planned into the verifier phase. The verifier's mechanism-neutral
interface (Protocol-based `HumanAuthenticator`/
`ProtectedApprovalPresentationMechanism` consumption, §2) is designed so
`FIDO2HumanAuthenticator` (L6) and a real presentation mechanism (L7) can
satisfy the same interfaces later without changing the verifier core. The
deterministic mechanisms continue to support verifier testing in the
interim.

## 26. Failure model

Fail-closed, no best-effort fallback, for every case enumerated in the
governing prompt (§27): missing principal; revoked principal;
fixture-only principal where real assurance is required; missing proof;
invalid proof; wrong mechanism; wrong installation; attestation invalid;
challenge mismatch; invocation mismatch; UP false; UV false; expired
proof; revoked credential; replayed proof; invalid lifecycle state;
noncanonical record; unsupported mechanism; internal verification error.
Each maps to a specific HPAC-REQ-054 step (§7) rejecting before any later
step runs — the verifier is a short-circuiting pipeline, not an
accumulate-then-decide evaluator.

## 27. Error taxonomy

No new overlapping taxonomy is needed. Reuse the existing typed exceptions
already present in the foundation: `HPACAuthorityError`,
`HPACCorruptionError`, `HPACDuplicateError`, `HPACMalformedError`,
`HPACSymlinkError`, store-specific `*TrustError`/`*ConflictError`/
`*NotFoundError` subclasses, `HPACLifecycleForkError`/`GapError`/
`StateError`, and HPAC-001 §40's `terminal_reason_code`
(`EXPIRED`/`REVOKED`/`REJECTED`). The verifier-implementation phase should
define a typed, deterministic outcome (success →
`AuthenticatedHumanPrincipal`; failure → one of the existing exception
types, or a new narrow verifier-specific exception subclassing
`HPACAuthorityError` only if none of the existing ones fits a given §26
case) suitable for tests, future Gate 5, future authority repair, and
diagnostics.

## 28. No caller-forgeable boolean authority

Designs such as bare `is_authenticated = true` / `verified = true` /
`trusted = true` booleans are explicitly prohibited as sufficient
downstream authority. `AuthenticatedHumanPrincipal`'s trusted-construction
and non-serializability (§10, §12) are exactly what makes a bare boolean
insufficient — a boolean can be forged by any caller; a value that only
the verifier's own call can produce, and that cannot be persisted or
copied out, cannot.

## 29. Persistence decision

**Ephemeral only**, per HPAC-REQ-058 — no new persistence is added beyond
what already exists (the lifecycle event, §18/§19). No separate canonical
store, writer, provenance record, digest, or retention policy is needed
for the verifier's *result*; the durable evidence of a successful
verification is entirely the `PROOF_VERIFIED_AND_BOUND` lifecycle event
already covered by `hpac_lifecycle.py`'s existing store/writer/digest/
provenance model (§2, §5's foundation reuse). If a future phase later
finds a need to persist verification outcomes as a distinct canonical
record, that is out of scope here and would need its own contract
justification — this phase does not add it speculatively.

## 30. Threat matrix

| # | Attack | Rejection behavior |
|---|---|---|
| 1 | Forged principal object | Rejected — verifier only accepts `principal_id`, resolves via canonical registry (§14), never a caller `PrincipalRecord` |
| 2 | Copied principal record | Rejected — registry resolution re-checks current status/revocation on every call |
| 3 | Fixture-to-real upgrade | Rejected — `authority_class` provenance is non-serialized/non-caller-settable (`HPACResolvedRecord`, §2); mechanism assurance classification (§13) is copied from the resolved mechanism, never caller-declared |
| 4 | Forged proof object | Rejected — proof resolved via `HumanAuthenticationProofStore.resolve_canonical`, never accepted as a caller object |
| 5 | Copied proof | Rejected — lifecycle/freshness/replay checks (§7 steps 7-8) re-run against current chain state on every call |
| 6 | Forged presentation | Rejected — presentation resolved via canonical store; attestation schema independently verified exact-match (`.1R.3.2.2.1`) |
| 7 | Copied attestation | Rejected — attestation bound to installed-mechanism provenance + presentation record digest, re-resolved each call |
| 8 | Mechanism substitution | Rejected — mechanism descriptor resolved from installation authority (§16 above), not caller-declared |
| 9 | Installation substitution | Rejected — installation authority resolution is canonical, not caller-suppliable |
| 10 | Challenge substitution | Rejected — challenge bound to the resolved approval/invocation subject (§7 step 1-2), mismatch rejected |
| 11 | Invocation substitution | Rejected — invocation-subject equality checked as part of §7 step 2/3 binding |
| 12 | UP false | Rejected — §7 step 5, UP mandatory |
| 13 | UV false | Rejected — §7 step 5, UV mandatory |
| 14 | Revoked principal | Rejected — registry resolution surfaces revocation (§14) |
| 15 | Revoked credential | Rejected — credential resolution surfaces revocation (§16) |
| 16 | Expired proof | Rejected — freshness check (§7 step 6) |
| 17 | Replayed proof | Rejected — lifecycle/consumption-state check (§7 step 7); idempotent only on byte-identical same-binding repeat, not a distinct replay |
| 18 | Stale lifecycle | Rejected — lifecycle chain re-resolved fresh, not cached, each call |
| 19 | Disconnected lifecycle | Rejected — `HPACLifecycleForkError`/`GapError` (existing, independently verified `.1R.3.2.2.1`) |
| 20 | Copied verifier result | Impossible to persist/transmit — `AuthenticatedHumanPrincipal` is non-serializable (§10, §12) |
| 21 | Caller-constructed verifier result | Rejected — trusted-construction only, no public constructor (§12) |
| 22 | Verifier result reused for another invocation | Structurally impossible — result is ephemeral, scoped to the verifying call; every consumer must re-verify (HPAC-REQ-058) rather than accept a passed-in result |
| 23 | Deterministic mechanism relabeled real | Rejected — assurance classification copied from resolved mechanism's `authority_class`/`MECHANISM_ID`, not caller-settable (§13) |
| 24 | Canonical-looking record outside trusted store | Rejected — `resolve_hpac_protected_root()` fixed paths, canonical-store containment independently verified with a 10-vector matrix (`.1R.3.2.2.1`) |
| 25 | Internal verifier exception/failure | Fail-closed — any unexpected exception must not fall through to a success path; the verifier-implementation phase must test this explicitly (§31) |

## 31. Test plan for the next implementation phase

- Focused verifier unit tests, one per §7 step, each independently
  controlling UP/UV/mechanism/lifecycle inputs.
- All 25 threat-matrix (§30) cases as explicit adversarial tests.
- Caller-forged-result and copied-result tests (attempt construction from
  outside the verifier module; attempt to serialize/pickle/hash-compare
  the result type; expect failure).
- Invocation-bound-result tests (result from invocation A must not
  validate/apply to invocation B).
- Assurance-class tests (deterministic path always yields NON-REAL,
  regardless of UP/UV values).
- Principal/proof/presentation/lifecycle canonical-resolution tests
  (reject any caller-supplied bare object in place of a resolved one).
- Full foundation regression suite (existing HPAC family, currently 80
  passing per `.1R.3.2.2.1`) re-run to confirm zero regressions.
- PB/runtime-authority zero-consumer tests: assert no reference to the new
  verifier module exists from `runtime_authority.py`,
  `runtime_dispatch_permission.py`, or PB modules after this phase.
- Fixed-SHA regression attribution, per this repository's existing
  discipline (§33 below), not aggregate pass/fail counts alone.

## 32. Regression infrastructure debt (carried, not mixed into verifier scope)

- Fast Green baseline resolver's commit-subject inference remains known
  debt, unrelated to verifier architecture.
- xdist random-UUID node-ID collection instability remains known debt.
- Historical state-sensitive tests remain known debt.

The verifier-implementation phase should use explicit immutable SHAs for
its own before/after regression comparison (as `.1R.3.2.2.1` did:
baseline `9cbdc45b` vs candidate `6cd753c6`), not rely on these unresolved
infrastructure issues.

## 33. Repository phase-naming convention (re-derived, not assumed)

Observed directly from `ls docs/ | grep 149O_20L_7O_3W_1R` (chronological):
a new top-level phase is `.<N>`; its independent verification is
`.<N>.1`; if verification finds a blocking issue, repair is `.<N>.2`,
verification of the repair is `.<N>.2.1`, and if a further round is
needed, `.<N>.2.2` then `.<N>.2.2.1` — exactly the pattern this repository
already used for `...1R.3` → `.3.1` → `.3.2` → `.3.2.1` → `.3.2.2` →
`.3.2.2.1`. Repair/re-verify sub-numbers are **not** pre-allocated
speculatively; they are appended only if and when an independent
verification actually finds a blocking issue.

This document is phase `...1R.4`, itself a new top-level phase (following
`.1R.2`'s planning → `.1R.3`'s implementation pattern, i.e. `.1R.4` is a
second planning phase, not a numbered continuation of `.1R.3`'s
implementation/verification chain). Therefore **the next new top-level
phase after this one is `...1R.5`**, and its independent verification is
`...1R.5.1` — not `.1R.4.1`/`.1R.4.2`, which would incorrectly imply
`.1R.4` itself needed repair.

## 34. Revised implementation sequence

| Step | Phase ID | Title | Scope | Layer(s) |
|---|---|---|---|---|
| A | `...1R.5` | Mechanism-Neutral HPAC Verifier and Principal-Registry Consumption Boundary Implementation | New `hpac_verifier.py` + tests only; no `runtime_authority.py`/`runtime_dispatch_permission.py`/PB change | L3 |
| B | `...1R.5.1` | Independent Verification of Mechanism-Neutral HPAC Verifier Implementation | Test files only; full §30 threat-matrix reproduction, fresh-authored suite | — |
| C | `...1R.6` | B1/B7/N1/N2 Production Authority Repair | Modifies `runtime_authority.py`, `runtime_dispatch_permission.py`, `runtime_invocation_approval_store.py`; consumes the independently-verified verifier for N2 | L5 |
| D | `...1R.6.1` | Independent Verification of B1/B7/N1/N2 Production Authority Repair | Test files only; fresh reproduction-then-closure of each finding | — |
| E | `...1R.7` | Real FIDO2 Mechanism Implementation (`FIDO2HumanAuthenticator`) | New authenticator module only; hardware read-only; no dispatch-path change | L6 |
| F | `...1R.7.1` | Independent Hardware-Backed Verification of Real FIDO2 Mechanism | Real hardware, human tester required | — |
| G | `...1R.8` | Real Protected Approval Presentation Mechanism Implementation | New presentation-mechanism module only; no dispatch-path change | L7 |
| H | `...1R.8.1` | Independent Verification of Real Protected Approval Presentation Mechanism | Verification only | — |
| I | `...1R.9` | Integrated Human-Approval Ceremony End-to-End Verification (Gates 3/5/9, real FIDO2 + real presentation) | Wiring/integration only; POL-005 still denies real dispatch | L8 |
| — | (future) | Runtime Enforcement planning reconsidered | Out of this document's scope — a new planning phase, not scheduled here | — |

This mirrors `.1R.2`'s own step count and ordering exactly (L6/L7/L8 and
their verifications are unchanged from `.1R.2 §52` Phases 3/3.1/4/4.1/5),
splitting only what `.1R.2` bundled (old Phase 2 → steps C, now
correctly sequenced after A/B rather than containing them). No
unnecessary fragmentation is introduced: A/B and C/D each keep
implementation and its independent verification as the minimal
two-phase unit, consistent with every completed phase pair to date.

## 35. Exact next-phase freeze

**Immediate next implementation phase (recommended, not started by this
document):**

- **Phase ID:** `149O.20L.7O.3W.1R.2B.1R.1.1R.5`
- **Title:** Mechanism-Neutral HPAC Verifier and Principal-Registry
  Consumption Boundary Implementation
- **Scope:** exactly §7–§30 of this document (responsibilities,
  input/output contracts, anti-transfer model, threat matrix) as its
  implementation and test brief. New `hpac_verifier.py` and its tests
  only. No `runtime_authority.py`/`runtime_dispatch_permission.py`/PB
  change.

**Its independent-verification phase:**

- **Phase ID:** `149O.20L.7O.3W.1R.2B.1R.1.1R.5.1`
- **Title:** Independent Verification of Mechanism-Neutral HPAC Verifier
  and Principal-Registry Consumption Boundary Implementation
- **Scope:** fresh, independently-authored reproduction of the full §30
  threat matrix and §31 test plan against Phase `...1R.5`'s code; no
  production change.

The later sequence (`...1R.6` through `...1R.9`, §34 table) is frozen at
the ID/title/scope level above but is **not** authorized for start by
this document — each remains subject to its own predecessor's independent
verification passing first, per §53 of `.1R.2` and this repository's
consistent practice.

## 36. Recommended immediate next-phase scope (restated, no-go bounded)

Phase `...1R.5` should contain **only**: the mechanism-neutral HPAC
verifier; canonical principal-registry consumption; trusted proof/
presentation/lifecycle resolution needed by the verifier; the typed,
non-authorizing `AuthenticatedHumanPrincipal` result; the deterministic
NON-REAL verifier path; and tests. It must **not** contain B1/B7/N1/N2
repair, PB integration, runtime-authority production repair, real FIDO2,
real UI, Gate-9 consumption, or Gate-10 effect — per §6's separability
analysis, no primary-source finding requires departing from this.

## 37. Authority walls (preserved)

```
verified authenticated principal  !=  approval
approval                          !=  PB permission
PB permission                     !=  runtime capability
runtime capability                !=  execution
deterministic verification success !=  real human authentication
```

## 38. Runtime boundary (preserved)

State: `Observed`. Maximum capability: `observe`. Execution availability:
`unavailable`. No execution-enablement work is planned by this document
or any phase in §34's sequence up to and including `...1R.9` — POL-005
remains unchanged throughout, and §34's own acceptance criteria for
step I explicitly require confirming POL-005 still denies real dispatch
after end-to-end wiring.

## 39. No-go for this planning phase (confirmed observed)

Not done in this phase: verifier code; principal/proof/presentation/
lifecycle implementation changes; PB changes; runtime-authority/dispatch
changes; contract changes; FIDO2 implementation; UI implementation;
provider/network calls; hardware access; deployment; release work; the
private research repository; article work. Documentation and governance
artifacts only.

## 40. Independent-verification boundaries

Per §33/§34/§35: every implementation step (A, C, E, G, I) has a dedicated
independent-verification phase (B, D, F, H, and step I is itself
end-to-end self-verifying per `.1R.2 §52` Phase 5's own acceptance
criterion) before the next implementation step may begin. No
implementation step may start before its predecessor's independent
verification is complete, matching this repository's demonstrated
`.1R.3`→`.1R.3.2.2.1` discipline.
