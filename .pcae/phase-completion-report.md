# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3.2 Complete — Canonical HPAC Foundation Trust-Root, Writer-Provenance, and Lifecycle-Validation Blocking Repair

Status: completed.

Phase entry: `36eb3cec4cc4e3ff28444eb67cfd5716a6af8d3c`.

Canonical implementation report:
`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_3_2_CANONICAL_HPAC_FOUNDATION_TRUST_ROOT_WRITER_PROVENANCE_LIFECYCLE_VALIDATION_BLOCKING_REPAIR.md`.

## Governing verdict and result

Phase `.3.1` concluded **NOT VERIFIED — TRUST FOUNDATION DEFECT**. This phase
repaired only its demonstrated HumanPrincipalRegistry, protected-presentation,
HumanAuthenticationProof, and HPAC-lifecycle trust-root defects. The result is:

**IMPLEMENTATION REPAIR COMPLETE — INDEPENDENT VERIFICATION REQUIRED.**

For every successfully addressed technical defect, the disposition remains:

**REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED.**

## Root causes and production repairs

- HumanPrincipalRegistry previously allowed caller-selected roots and
  caller-controlled record fields to stand in for authority. It now uses a
  zero-argument fixed production root, root-bound opaque writers, canonical
  provenance sidecars and sealed resolution. Fixture authority is sealed as
  `FIXTURE_NON_REAL` at the store/writer boundary and cannot be promoted by
  copying or field mutation.
- Protected presentation previously accepted public descriptor/evidence
  construction and matching digests without authoritative installation or
  attestation provenance. It now requires a same-root installed-descriptor
  resolver seal, exact mechanism/version/class/subject/challenge binding,
  installed-mechanism attestation verification, presentation-writer provenance,
  and canonical resolution. Deterministic presentation remains non-real.
- HumanAuthenticationProof previously did not distinguish public canonical-
  looking proof data from proof-verifier output. Canonical persistence now
  requires the root-bound proof-verifier writer and matching provenance; the
  resolver returns a non-serializable canonical seal. Raw response, parsed
  proof, canonical proof, and verified principal remain distinct. No
  `verified=True` authority shortcut was added.
- HPAC lifecycle previously treated self-consistent hashes as sufficient for
  genesis and predecessor authority. Canonical genesis now requires the
  coordinator writer and a same-root resolved presentation; every successor
  requires the authorized role writer, authoritative current predecessor,
  allowed transition, full chain-to-genesis validation, and exact evidence
  bindings. Create-only successor publication rejects immediate and deep
  forks, stale predecessors, alternate/disconnected chains, and copied roots.

Public constructors remain data constructors only. Correct object shape,
canonical bytes, a recomputed SHA-256 digest, or a chosen canonical-looking
path does not establish authority. Filesystem validation adds containment,
symlink/path-traversal rejection, regular single-link file requirements,
exact canonical JSON, protected-root checks, atomic/durable writes, and
conflict rejection; filesystem safety and writer authority remain separate.

## Files changed and boundaries

Production repair files:

- `src/pcae/core/hpac_foundation.py`
- `src/pcae/core/human_principal_registry.py`
- `src/pcae/core/approval_presentation.py`
- `src/pcae/core/approval_presentation_deterministic.py`
- `src/pcae/core/human_authentication_proof.py`
- `src/pcae/core/hpac_lifecycle.py`

The phase also adds
`tests/test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py`, the canonical
implementation document, fixed-SHA attribution evidence, and ordinary governed
project/task/completion artifacts. Contracts, POL-005, PB/runtime/Shell Gate,
packaging, and release files are unchanged. `human_authenticator.py`,
`human_authenticator_deterministic.py`, and
`runtime_invocation_authority_consumption.py` are byte-identical to entry.

The deterministic authenticator remains simulation/test-only with independent
UP, UV, principal-match, credential-match, challenge-match, revocation,
expiry, replay, and malformed-response controls. UP=true plus UV=true never
establishes real human authentication.

Gate 9 remains plan-authorized and inert. Production boundary search found:

- PB integration: 0
- Runtime Enforcement calls: 0
- Shell Gate calls: 0
- Gate-5 wiring: 0
- Gate-9 production wiring: 0
- Gate-10 effects: 0
- runtime subprocess calls: 0
- provider/network calls: 0
- real credential/hardware operations: 0

B1, B7, N1, and N2 remain **contract closed / implementation open**. Real
FIDO2, WebAuthn, CTAP, enrollment, protected UI, approval/enrollment CLI,
biometrics, PAM, keychain, provider, and network work remain absent.

## Test and regression evidence

- `.3.2` fresh repair suite: **38 passed, 0 failed**.
- Original `.3` suites: **80 passed, 0 failed**.
- Combined current HPAC behavior: **118 passed, 0 failed**.
- Relevant B-3/B-4 contract/storage regressions: **44 passed, 0 failed**.
- Unchanged historical `.3.1` suite: **28 passed, 7 expected failures**.
  The seven old `blocking_reproduction` assertions fail because the repaired
  code now rejects the unsafe acceptance they intentionally encoded; no
  `.3.1` historical test was rewritten.

Fast Green was re-derived by exact fixed-SHA raw node IDs in isolated
worktrees: entry `36eb3cec4cc4e3ff28444eb67cfd5716a6af8d3c` versus pushed
repair candidate `bbd1b9a2c34031bf0b1001d26593895bccf28237`. There were 351
common nonpassing nodes, zero candidate-only nonpassing nodes, and one
baseline-only origin-currentness node. Therefore **UNEXPLAINED ATTRIBUTABLE
FUNCTIONAL REGRESSIONS = 0**. Evidence is preserved at
`.pcae/fast-green-attribution/4f02d9f968fc0ff205d7e3f63e6bf29162a289e58f966dd33fbe5731ad7bfcc3.json`.

The canonical helper's initial self-baseline result was rejected: its
commit-subject-only resolver collapsed both sides to `bbd1b9a2` because the
first governed repair commit subjects omitted the long phase token. This is
reported as separate infrastructure debt, as is the pre-existing full-suite
xdist UUID node-ID collection nondeterminism.

## Runtime and governance

Runtime remains:

- State: Observed
- Maximum Capability: observe
- Execution Availability: unavailable

No external runtime effect, real backend/adapter/subprocess execution,
provider/network call, credential operation, hardware operation, release,
deployment, Dell, research, or Layer-3 work occurred.

**DELEGATED FINALIZATION / COMMIT / PUSH: UNAUTHORIZED.** The delegated actor
in `.3` exceeded explicit human-granted authority. All seven `.3` commits and
the independently adjudicated incomplete historical `.3` report remain
preserved. Their existence establishes no delegated authority precedent. This
repair does not rewrite, amend, rebase, revert, or retroactively authorize the
incident, and technical repair does not cure it. No subagent was used in
`.3.2`.

## Findings

| ID | Severity/category | Result | Disposition |
|---|---|---|---|
| B-3.1-01 | BLOCKING / HPAC trust | Registry root, writer, resolver, and fixture provenance repaired | REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED |
| B-3.1-02 | BLOCKING / HPAC trust | Installed mechanism, attestation, presentation writer, and resolver repaired | REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED |
| B-3.1-03 | BLOCKING / HPAC trust | Proof-writer provenance and canonical seal repaired; stages preserved | REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED |
| B-3.1-04/05/06 | BLOCKING / HPAC trust | Genesis, full predecessor chain, disconnected-chain and fork rejection repaired | REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED |
| B-3.1-07 | BLOCKING / governance | Unauthorized `.3` delegated lifecycle incident preserved | OPEN; NO PRECEDENT |
| B-3.1-08 | BLOCKING / provenance | Incomplete historical `.3` report preserved; additive `.3.1` adjudication remains authoritative | PRESERVED |
| NB-3.2-01 | NON-BLOCKING / tests | Seven historical unsafe-acceptance assertions now fail | Expected repaired-behavior evidence |
| O-3.2-01 | OBSERVATION / infrastructure | Historical xdist UUID node-ID nondeterminism | Deferred; not HPAC regression |
| O-3.2-02 | OBSERVATION / scope | Real writers, enrollment, attestation and Layer 3 remain absent | Required deferral |
| O-3.2-03 | OBSERVATION / infrastructure | Canonical Fast Green subject resolver self-baselined | Rejected; exact fixed-SHA evidence used |

## Acceptance result and commits

The registry, protected-presentation evidence, proof store, and lifecycle trust
roots/writers/resolvers are implemented; fixture and deterministic mechanisms
remain non-real; genesis and complete predecessor/fork validation are
implemented; digest/path/caller shape are not authority; Gate 9 is inert;
PB/runtime integration and real mechanisms are absent; attributable regressions
are zero.

Phase-owned implementation/evidence commits through canonical-report staging:

- `7089854e254e618fae9b67f75f2a255ff59bd663`
- `ad816df5dc50061e62f3dde4e43f22d3826c5a26`
- `bbd1b9a2c34031bf0b1001d26593895bccf28237`
- `0e564ce48b6fd4e1c7dfc0b50337d1507baafecc`
- `7ccfa76c74e182e4925adb03ddd87716ba87c32b`

Later mechanically generated report/task closure commits are additive because
a commit cannot truthfully list its own hash. The final pushed status,
`origin/main..HEAD`, and complete actual `.3.2` commit sequence are returned to
the human after governed closure.

## Recommended next phase

**149O.20L.7O.3W.1R.2B.1R.1.1R.3.2.1 — Independent Verification of Canonical HPAC Foundation Trust-Root, Writer-Provenance, and Lifecycle-Validation Repair**

New human authorization is required. `.3.2.1` was not begun. Do not proceed to
Layer 3.
