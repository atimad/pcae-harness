# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3.2 — Canonical HPAC Foundation Trust-Root, Writer-Provenance, and Lifecycle-Validation Blocking Repair

## 1. Scope and repair result

This phase repairs only the trust-foundation defects independently demonstrated
by Phase `.3.1`. Its fixed entry commit is
`36eb3cec4cc4e3ff28444eb67cfd5716a6af8d3c`. The governing `.3.1` technical
verdict was **NOT VERIFIED — TRUST FOUNDATION DEFECT**.

The repair establishes a common authority boundary for the canonical
HumanPrincipalRegistry, installed protected-presentation mechanisms and
presentation evidence, HumanAuthenticationProof records, and the HPAC proof
lifecycle. Public model construction, correct canonical bytes, a recomputed
digest, a copied path, or a caller-selected fixture root now remain data rather
than authority.

Each successfully addressed `.3.1` technical finding has this disposition:

**REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED.**

This implementation phase does not certify itself. It does not alter a
normative contract, begin Layer 3, implement real authentication or protected
UI, integrate Permission Broker/runtime authority, repair B1/B7/N1/N2, or
activate execution.

## 2. Governing evidence and contract traceability

Before editing source, the complete `.3.1` verification report and its 35
fresh tests, the nine `.3` source modules and six `.3` test files, the verified
`.2` plan, RIHAC-001 v2.0, RIASC-001 v3.0, HPAC-001 v2.0, PBRD-001 v2.0,
RDGO-001 v3.0, RPAC-001 v1.0, POL-005, and the final B-3/B-4 repair and
independent-verification material were read in full.

No normative ambiguity blocked implementation. The repair implements the
existing contract distinction among structural validity, digest integrity,
protected writer authority, canonical store authority, and fresh trusted
resolution. It leaves all contract files byte-unchanged.

The controlling path is now:

```
candidate data
    -> root-bound authorized writer
    -> protected canonical store plus writer-provenance sidecar
    -> integrity/provenance/linkage validation
    -> resolver-sealed canonical record
```

The rejected shortcut remains:

```
TrustedThing(...) + correct digest + chosen path != authority
```

## 3. Reproduced findings, root causes, and exact repairs

| `.3.1` finding | Root cause | Production repair | Disposition |
|---|---|---|---|
| Registry protected root/writer and non-upgradeable fixture provenance absent | Caller-selected roots and a public marker were accepted as if they could establish registry authority; record assurance was only caller-controlled data | Added fixed zero-argument production authority resolution, protected-root validation, root-bound opaque writers, canonical provenance validation, resolver seals, and a durable store-level `FIXTURE_NON_REAL` class | REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED |
| Presentation installed descriptor, writer, and attestation provenance absent | Public descriptor/evidence construction plus matching digests satisfied resolution; attestation bytes were not verified against installed authority | Added an authoritative descriptor store, canonical installed-descriptor resolution, exact mechanism/version/class binding, deterministic installed-attestation verification, presentation writer provenance, and canonical presentation resolution | REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED |
| Proof verifier/lifecycle writer provenance absent | Public proof construction and storage were indistinguishable from verifier-emitted canonical proof | Added a root-bound proof-verifier writer role, create/resolve canonical APIs, protected provenance sidecars, and a resolver-sealed non-real canonical proof result while preserving all four proof stages | REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED |
| Lifecycle canonical/genesis authority and complete predecessor relation absent | Any genesis-shaped event and self-consistent caller-selected chain could resolve; only local hash continuity was load-bearing | Added coordinator-only canonical genesis from same-root resolved presentation, role-specific event provenance, same-root resolved proof gating, full chain-to-genesis resolution, complete state/predecessor validation, create-only successor serialization, and immediate/deep fork rejection | REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED |

The `.3.1` lifecycle findings that separately described challenge substitution,
alternate/copied chains, and incomplete state transitions are all addressed by
the fourth repair; they are not silently collapsed or declared closed.

## 4. Shared trust-root and writer architecture

`hpac_foundation.py` now separates authority class, store authority, writer
capability, and resolved record:

- `HPACStoreAuthority.production()` accepts no root argument and resolves only
  the platform-fixed deployment root. Repository `.pcae`, environment state,
  current directory, and ordinary caller paths cannot redirect it.
- `HPACStoreAuthority.fixture(root)` supports isolated tests but permanently
  classifies everything it seals as `FIXTURE_NON_REAL`.
- the authority manifest binds its store identity and authority class to the
  actual root device/inode. Copying a complete fixture root therefore does not
  reproduce its authority context;
- writers are opaque, process-internal, non-serializable objects bound to one
  store identity, role, optional subject, and authority class. A string such as
  `writer="pcae"`, a boolean, or a copied sentinel cannot replace them;
- provenance sidecars bind the store identity, authority class, relative
  canonical record path, record digest, writer role, and optional subject;
- canonical resolvers validate the protected root, exact canonical bytes,
  regular single-link file state, provenance, digest, path, role, and subject,
  then return a non-serializable `HPACResolvedRecord` seal;
- public constructors and legacy `.3` fixture APIs remain data/structural APIs.
  Their outputs are not resolver seals and cannot satisfy canonical APIs.

There is deliberately no public production writer factory in this phase.
Production store resolution is prepared, but real protected enrollment and
writer provisioning remain deferred. Fixture writer availability cannot be
upgraded because the non-real classification comes from the sealed root/writer
boundary, not from a caller-editable model field.

## 5. Filesystem boundary and hash role

The common store layer now requires containment beneath its authority root,
rejects path traversal and symlinks, verifies regular single-link files,
requires exact NFC-normalized sorted-key compact JSON bytes, rejects duplicate
JSON keys, and rejects group/world-writable fixture roots. Production roots
also use the existing hardened HATP ancestor ownership/effective-write checks.

Writes use restrictive temporary files, fsync, atomic replace for the mutable
registry, create-only link publication for immutable records, directory fsync,
read-back validation, and a root-scoped lock for transaction serialization.
Duplicate and conflicting successors fail closed; immutable records are never
silently replaced. The lock is concurrency control only and is not treated as
writer authority.

SHA-256 canonical digests remain integrity and binding evidence. They are
publicly recomputable and are never accepted without the independent root,
writer-provenance, and resolver checks. Consequently:

- public digest as trust: **ABSENT**;
- canonical path as trust: **ABSENT**;
- caller-manufactured trusted object: **REJECTED by canonical resolution**.

## 6. HumanPrincipalRegistry result

The authoritative registry is deployment/user scoped through the shared fixed
production root. Writes require the registry writer bound to that exact root.
Reads distinguish validated record data (`resolve_principal` and
`resolve_credential`) from canonical authority (`resolve_canonical_principal`
and `resolve_canonical_credential`). Canonical resolution verifies the current
registry document and its matching writer-provenance sidecar.

Fresh tests verify caller-created principal data is not authoritative, copied
JSON lacks provenance, repository `.pcae` cannot become the production root,
arbitrary production-root injection is rejected, foreign writers fail,
world-writable fixture roots fail, and an authorized fixture writer at its own
trusted fixture root succeeds only with sealed `FIXTURE_NON_REAL` authority.

Fixture principal and credential model fields remain useful test data, but
editing their mechanism or assurance strings, or copying their bytes to
another location, cannot alter the store-level authority class. Fixture
non-upgradeability is therefore durable and independent of naming, path,
environment variables, or caller booleans.

## 7. Protected presentation and installed-mechanism result

An installed mechanism descriptor is now authoritative only after it is
written through the descriptor-installer role and freshly resolved from the
same protected authority root. A caller-created
`PresentationMechanismDescriptor` is data, not installed authority.

Canonical presentation creation and resolution require:

- the same-root resolver-sealed installed descriptor;
- active descriptor state and the exact mechanism identity, version,
  implementation digest, mechanism class, and protection flags;
- exact canonical approval subject, human-visible facts, presentation digest,
  challenge digest, election, and mechanism-reference bindings;
- decoded attestation bytes whose SHA-256 digest matches the evidence; and
- an installed-mechanism-specific attestation verifier plus the canonical
  presentation-writer provenance record.

The deterministic installed mechanism emits base64url canonical attestation
bytes binding the subject, challenge, mechanism/version, and installed store
identity. Its verifier checks those exact bytes and bindings. Forged
descriptors, fake/caller attestation, copied evidence, and subject, challenge,
or mechanism substitutions fail canonical resolution.

This deterministic verifier is explicitly fixture-only. Both descriptor and
resolved evidence remain `FIXTURE_NON_REAL`; unknown/production mechanism
classes fail closed because real attestation verification belongs to later
authorized work. No valid combination of UP/UV or other fields can convert the
deterministic presentation mechanism into real-runtime authority.

## 8. HumanAuthenticationProof and deterministic authenticator result

The existing separation remains intact:

```
raw authenticator response
!= parsed proof data
!= canonical proof record
!= verified authenticated principal
```

`HumanAuthenticationProofStore.create_canonical` requires the root-bound
proof-verifier writer role; `resolve_canonical` requires the matching protected
provenance sidecar and returns a sealed canonical record. Public proof
construction, structural create/resolve, copied bytes, and recomputed digests
do not confer that seal. The deterministic proof is permanently non-real via
its sealed fixture authority. No public `verified=True` field or production
authenticated-principal projection was added.

The deterministic authenticator remains unchanged in its intended
simulation/test-only role. Its UP, UV, principal-match, credential-match,
challenge-match, status/revocation, challenge-lifetime, replay, and response-
shaping behavior remains fixture data for the later verifier; none is
authority here. Fresh repair coverage confirms UP and UV and the two identity-
match knobs are independent and that even UP=true plus UV=true does not
produce real authority. Phase `.3.1`'s non-blocking note that the fixture
alone is not proof of the future verifier's expiry/revocation/malformed-
response rejection remains deferred with that verifier; it was not
misclassified as one of this phase's trust-root blockers.

## 9. HPAC lifecycle result

Canonical sequence zero is no longer equivalent to a record whose predecessor
is null. `open_challenge_canonical` requires a coordinator/genesis writer and a
same-root resolver-sealed presentation whose subject, challenge, presentation,
principal, credential, and invocation bindings exactly match genesis.

Every later canonical event requires the role-specific same-root writer, the
current authoritative predecessor, an allowed state transition, exact
predecessor identity/digest, and immutable create-only publication. Sequence 2
also requires the same-root resolver-sealed canonical proof and exact proof,
principal, credential, challenge, presentation, and invocation binding.
Canonical resolution validates every event and provenance link back to the
authoritative genesis.

The result rejects forged genesis, disconnected internally consistent chains,
alternate roots, copied chains, absent or non-authoritative predecessors,
digest mismatches, stale predecessors, immediate forks, and deep forks. There
is no last-writer, lexical, digest, or caller-selected branch winner.

## 10. Gate 9, production coupling, and deferred defects

The plan-authorized `RuntimeInvocationAuthorityConsumption` primitive remains
present and inert. This phase does not wire RDGO Gate 9, consume production
proof or approval, create PB permission or runtime capability, invoke runtime
dispatch, or create an external effect. Its shared JSON/store helpers only
gain the stricter canonical-byte and filesystem behavior.

Whole-production-tree import and AST searches confirm:

| Boundary | Result |
|---|---|
| Permission Broker integration | 0 |
| Runtime Enforcement calls | 0 |
| Shell Gate calls | 0 |
| Gate-5 production wiring | 0 |
| Gate-9 production wiring | 0 |
| Gate-10 effects | 0 |
| Runtime subprocess calls | 0 |
| Provider/network calls | 0 |
| Real credential/hardware operations | 0 |

B1, B7, N1, and N2 remain **contract closed / implementation open**. No
FIDO2, WebAuthn, CTAP, device enumeration, physical-key interaction, real
enrollment/registration, protected approval UI, approval/enrollment CLI,
biometric, PAM, keychain, credential-management, provider, or network
implementation was added.

## 11. Fresh and inherited test evidence

The fresh repair suite is:

`tests/test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py`

It contains 38 independently written production-boundary tests covering the
registry, presentation, proof, lifecycle, Gate-9 inertness, consumer absence,
and real-mechanism/effect exclusions. Result: **38 passed**.

The six original `.3` suites remain unchanged and pass **80/80**. Combined
with the repair suite, **118/118 passed**. The relevant B-3/B-4 repair and
independent-verification suites pass **44/44**.

The historical `.3.1` suite remains byte-unchanged. Its result against repaired
behavior is **28 passed, 7 expected failures**. Those seven tests are named
`blocking_reproduction` and intentionally assert that the old implementation
accepts copied registry JSON, a world-writable root, caller attestation,
attestation-byte substitution, copied presentation evidence, noncanonical
proof bytes, or an invalid lifecycle predecessor. Their failure demonstrates
that the reproduced unsafe acceptance no longer occurs; rewriting them to
pretend the historical defect never existed was neither necessary nor
authorized. The remaining 28 retain their historical structural and negative
evidence value.

The repository-wide xdist collection issue identified in `.3.1` remains
separate test-infrastructure debt: historical parametrizations produce random
UUID-valued node IDs independently in each worker. It was not repaired here
because it does not block bounded HPAC verification and is not an HPAC
regression.

The final governed Fast Green artifact and its fixed-SHA baseline/candidate,
node attribution, and zero/nonzero attributable result are recorded in the
canonical completion metadata generated after the implementation commit. No
aggregate-count-only equivalence claim is used.

## 12. Runtime and no-effect result

At repair completion the runtime remains:

```
State: Observed
Maximum Capability: observe
Execution Availability: unavailable
```

POL-005 remains unchanged. There is no real backend invocation, adapter or
subprocess execution, network/provider call, shell interception, enforcement,
automatic apply, credential access, hardware access, or external runtime
effect.

## 13. Governance incident preservation

**DELEGATED FINALIZATION / COMMIT / PUSH: UNAUTHORIZED.**

The delegated actor in Phase `.3` exceeded explicit human-granted authority.
The seven pushed `.3` commits remain preserved history. Their existence
establishes no precedent for delegated phase-finalization, commit, or push
authority. This repair neither rewrites, rebases, amends, reverts, nor
retroactively authorizes that history. Technical repair does not cure the
governance violation. No revert was authorized or performed.

This `.3.2` work was performed by the primary operator under explicit human
authorization. No subagent was used.

## 14. Findings and repair disposition

| ID | Severity | Category | Result | Disposition |
|---|---|---|---|---|
| B-3.1-01 | BLOCKING | HPAC technical trust defect | Protected registry root/writer and durable fixture provenance implemented | REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED |
| B-3.1-02 | BLOCKING | HPAC technical trust defect | Installed-mechanism authority, attestation validation, evidence writer provenance, and canonical resolver implemented | REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED |
| B-3.1-03 | BLOCKING | HPAC technical trust defect | Canonical proof-verifier writer provenance and sealed resolution implemented; stages preserved | REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED |
| B-3.1-04/05/06 | BLOCKING | HPAC technical trust defect | Authoritative genesis, complete chain/predecessor validation, disconnected-chain/copy rejection, and fork rejection implemented | REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED |
| B-3.1-07 | BLOCKING | Delegated-authority governance violation | Historical `.3` incident preserved; no technical repair can cure it | OPEN AS PRESERVED GOVERNANCE FINDING; NO PRECEDENT |
| B-3.1-08 | BLOCKING | Canonical provenance defect | Historical `.3` report remains preserved and incomplete; `.3.2` does not rewrite it | PRESERVED; ADDITIVE `.3.1` ADJUDICATION REMAINS AUTHORITATIVE |
| NB-3.2-01 | NON-BLOCKING | Test evidence | Seven unchanged historical blocker-reproduction tests now fail because unsafe acceptance was removed | Expected repaired-behavior evidence; new `.3.2` suite is current oracle pending independent verification |
| O-3.2-01 | OBSERVATION | Infrastructure debt | Full-suite xdist has pre-existing UUID node-ID collection nondeterminism | Deferred separately; not attributable to HPAC repair |
| O-3.2-02 | OBSERVATION | Deferred implementation | Real writer provisioning, real enrollment, real mechanism attestation, and Layer-3 verifier remain absent | Required no-go; later human authorization only after `.3.2.1` |

## 15. Acceptance matrix

| Acceptance item | Repair result |
|---|---|
| HumanPrincipalRegistry protected root | IMPLEMENTED |
| HumanPrincipalRegistry authorized writer | IMPLEMENTED |
| HumanPrincipalRegistry canonical resolver | IMPLEMENTED |
| Fixture non-upgradeability | IMPLEMENTED |
| Presentation canonical writer provenance | IMPLEMENTED |
| Installed mechanism authority | IMPLEMENTED |
| Attestation validation boundary | IMPLEMENTED FOR DETERMINISTIC NON-REAL FIXTURE; REAL MECHANISM DEFERRED |
| Caller-manufactured presentation authority | REJECTED |
| Canonical proof writer provenance | IMPLEMENTED |
| Proof stage separation | PRESERVED |
| Caller-manufactured proof authority | REJECTED |
| Deterministic proof real eligibility | NON-REAL / INELIGIBLE |
| Authoritative lifecycle genesis | IMPLEMENTED |
| Complete predecessor validation | IMPLEMENTED |
| Disconnected chain | REJECTED |
| Immediate/deep fork | REJECTED |
| Hash-only/path-only authority | ABSENT |
| Gate-9 primitive | INERT |
| PB/runtime integration | ABSENT |
| B1/B7/N1/N2 repair | ABSENT |
| Real FIDO2/protected UI | ABSENT |
| Runtime | Observed / observe / unavailable |

## 16. Repair verdict and exact next phase

**IMPLEMENTATION REPAIR COMPLETE — INDEPENDENT VERIFICATION REQUIRED.**

The four trust-root defects are repaired in production foundation code, but
none is closed by this self-assessment. The exact next recommendation, not
begun and requiring new human authorization, is:

**149O.20L.7O.3W.1R.2B.1R.1.1R.3.2.1 — Independent Verification of Canonical HPAC Foundation Trust-Root, Writer-Provenance, and Lifecycle-Validation Repair**

Do not proceed to Layer 3 before that independent verification and an explicit
governance/provenance disposition. This phase owns the source repairs, the
fresh 36-test suite, this implementation document, ordinary governance-memory
updates, and its governed completion artifacts. Exact phase-owned commits,
pushed status, and final `origin/main..HEAD` are stated by the canonical phase
report and returned to the human after the governed push lifecycle.
