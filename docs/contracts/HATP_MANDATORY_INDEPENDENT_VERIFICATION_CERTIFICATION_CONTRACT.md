# HATP Mandatory Independent-Verification Certification Contract

**Contract ID:** HMIC-001
**Version:** 1.7
**Status:** FROZEN — TRUST-ENROLLMENT STANDALONE ADMIN ENTRY-POINT SOURCE-SCOPE EVOLVED (149O.20L.7O.2M) — PENDING INDEPENDENT VERIFICATION (not VERIFIED at v1.7)
**Frozen by:** Phase 149O.19.2
**Repaired by:** Phase 149O.19.3R (finding B-149O.19.3-1; see §49) — v1.0, independently re-verified VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS at 149O.19.3R.1
**Amended by:** Phase 149O.19.5E.1 (v1.0 → v1.1: HMIC-REQ-050/052 widened to bind the now-implemented HMIC validator/admin source; W-1 resolved at the contract level; see §50)
**Amended by:** Phase 149O.20D (v1.1 → v1.2: HMIC-REQ-067 widened to bind HBDC-001 v1.0 into `contract_versions`, closing HBDC-001's own HBDC-REQ-048 prerequisite; contract evolution only, no production change; see §51)
**Repaired by:** Phase 149O.20D.1 (finding B-149O.20D-1: HBDC-001's v1.2 binding was version-header-only, leaving same-version content-only byte drift certification-invisible; repaired in place, same version, by additionally binding HBDC-001's document bytes into `implementation_scope_digest` — HMIC-REQ-050/052/053 widened to twenty-five files; HMIC-REQ-145 revised from a disclosed residual limitation to a closed one; no production change; see §52)
**Amended by:** Phase 149O.20K (v1.2 → v1.3: HMIC-REQ-052 widened with a new limb (c) binding the Class-B deployment-conformance verifier island's own authority-sensitive source; HMIC-REQ-050 widened to twenty-eight files (`core/hatp_class_b_topology_verifier.py`, `core/hatp_environment_lock_verifier.py`, `core/hatp_class_b_conformance.py`); addresses CBV-S1; contract evolution only, not yet operative in production, no readiness integration, no Class-B provisioning; see §53)
**Repaired by:** Phase 149O.20L.1A (finding B-149O.20L.1-1: the `Depends on` header line below still described `HMRC-001` as `v1.0, byte-unchanged` after Phase 149O.20L.1 amended HMRC-001 to v1.1 — a stale non-normative descriptive-header defect only; `derive_contract_versions` and this contract's own §20 live-header-comparison mechanism were independently confirmed already correct and unaffected; repaired in place, same version, updating only this document's own descriptive header line — no requirement text, no production source, changed; see §54)
**Amended by:** Phase 149O.20L.7K (v1.3 → v1.4: HMIC-REQ-052 limb (c) widened with a third anchor binding the DeploymentBinding producer/rotation/revocation functions in `core/hatp_deployment_binding_admin.py` and their sole intended Protected Admin ceremony caller `scripts/hatp_deployment_binding_admin.py` — this write path is not reachable from `verify_class_b_deployment_conformance`'s own call graph, but its output is exactly the `DeploymentBinding` data the already-frozen `hatp_bootstrap.py`/`repository_identity.py` read path consumes to compute HBDC-REQ-042's contribution to that same verdict, mirroring limb (b)'s own dual-anchor precedent (§50); HMIC-REQ-050 widened to thirty files; production `_FROZEN_SRC_PCAE_RELATIVE_FILES`/`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` aligned in the same phase, unlike 149O.20K's split contract/alignment sequencing; closes the 7J §31 HMIC frozen-source-membership finding at the contract-and-production layer, independent verification pending; see §55)
**Repaired by:** Phase 149O.20L.7L.1 (findings F-7L-1/F-7L-2, surfaced by 149O.20L.7L's withheld independent verification: this document falsely stated in HMIC-REQ-052 limb (c)'s closing paragraph, §55.4's citation, §55.15's verdict, and attack row 39 clause (a) that no readiness/certification/activation code path calls `verify_class_b_deployment_conformance` or consults its result, when Phase 149O.20L.3 had already wired it into `hatp_mandatory_cutover.py` as the eighth activation-readiness term, ancestral to 149O.20L.7K's own phase entry; and the `Depends on` header below still named `HBDC-001 v1.0` after `HBDC-001` had been v1.1 since Phase 149O.20L.7G; both repaired in place, same version, no requirement text widened or narrowed, no production source changed; see §56)
**Repaired by:** Phase 149O.20L.7L.3 (finding F-7L-5, rows 33/34/36/37: 149O.20L.7L.1 deferred these rows' "Not yet operative"/stale file-and-member-count language as outside its own narrow evidence chain; 149O.20L.7L.2's independent verification found the deferral does not hold — each row's live production-state claim is directly, trivially false, and row 34's additional hard-coded-ceiling/zero-readiness-caller clauses are independently falsified by the Wave F integration (Phase 149O.19.5F), predating even 149O.20L.7K; repaired in place, same version, restating each row's "not yet operative" framing as "operative, not yet consequential" against the live thirty-file/five-member production identity, while preserving each row's original rejection mechanism and the still-true "no stored certification exists on this host" conclusion — see §57. Also finding F-7L-7: the test-only AST-level `_pcae_imports` guard helper recorded only `ast.ImportFrom.module`, not its `.names`, missing `from package import submodule` forms (single- and multi-line); extended to enumerate `ast.Import` and `ast.ImportFrom` targets precisely, including aliases and multi-name/multiline forms, with a conservative package-vs-symbol adjudication and adversarial/negative-control test coverage — test/evidence code only, no production source changed; see §57.8)
**Repaired by:** Phase 149O.20L.7L.5 (findings surfaced by 149O.20L.7L.4's independent verification: (1) the whole-document scan's own §57.9 misclassified this document's top-of-document §0 intro paragraph as historical when it in fact restated the same stale "hard-coded `False` ceiling ... is unchanged" claim rows 33/34/36/37 already corrected — repaired in place, same version, see §58.1; (2) `_pcae_import_targets`'s AST guard helper detected absolute imports only, silently missing every relative-import form (`from . import x`, `from .x import y`, `from ..pkg import x`) of the protected `DeploymentBinding` producer module — widened to resolve relative-import levels against a canonical file-path-to-module-name derivation, see §58.2; (3) `test_admin_script_is_the_only_non_test_caller_of_the_producer_entry_points` still called the unrepaired `_pcae_imports` helper — migrated to the repaired `_pcae_import_targets`, see §58.3; test/evidence and contract-text only, no production source changed; see §58)
**Amended by:** Phase 149O.20L.7O.2H (v1.4 → v1.5: HMIC-REQ-052 widened with a new closure limb (d) binding the Trust-Enrollment/signing authority surface — `core/hatp_signing_ceremony.py`'s production signing ceremony, `core/hatp_hardware_credential_admin.py`'s hardware-credential administrative writer, and `core/hatp_principal_signer_admin.py`'s principal/signer administrative writer; HMIC-REQ-050 widened from thirty to thirty-five files (three new `src/pcae/`-relative source entries, two new repository-root-relative contract-content entries); HMIC-REQ-053/067/069 widened so `contract_versions` (HMIC-REQ-067) grows from five to seven members, content- and version-binding `HPSE-001` v1.1 and `HHCE-001` v1.1 per HMIC-REQ-053's existing uniform-coverage rule; production `_FROZEN_SRC_PCAE_RELATIVE_FILES`/`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`/`_CONTRACT_IDENTITY_FILES` aligned in the same phase, per the 149O.20L.7K precedent; uses the exact target set reconciled by 149O.20L.7O.2G.1 (`B-149O.20L.7O.2G-1`); independent verification pending; see §59)
**Amended and repaired by:** Phase 149O.20L.7O.2H.2 (v1.5 → v1.6: HMIC-REQ-050 widened thirty-five → thirty-six by binding unchanged `core/paths.py`; HMIC-REQ-052(d)'s closure analysis corrected after independent verification demonstrated that reached `HarnessPath.join`/`.path` behavior selects authority-bearing AG3/AG5 signing inputs; HMIC-REQ-076 corrected from stale four-contract prose to the current exact seven-contract live-header ceremony; production identity aligned in the same phase; contract identity remains exactly seven; independent verification pending; see §60)
**Amended by:** Phase 149O.20L.7O.2M (v1.6 → v1.7: HMIC-REQ-050 widened thirty-six → thirty-eight by binding the two newly-implemented, independently-verified standalone Trust-Enrollment administrative entry points `scripts/hatp_hardware_credential_admin.py` and `scripts/hatp_principal_signer_admin.py` — the sole intended Protected Admin ceremony callers of the already-bound core writer modules `core/hatp_hardware_credential_admin.py`/`core/hatp_principal_signer_admin.py`, mirroring the identical `scripts/`-caller-anchor precedent HMIC-REQ-052(d) already applies (§59) and limb (b)/(c)'s own dual-anchor construction (§50/§55); a fresh transitive-closure re-walk of both scripts' own import graphs found no not-yet-bound dependency (every reachable module, direct and lazy-imported, is already inside `_FROZEN_SRC_PCAE_RELATIVE_FILES`); contract identity remains exactly seven, only the `HMIC-001` version value itself changes (`HMIC-001` is not, and does not become, a member of `contract_versions` — its own document bytes are also not, and do not become, a member of the frozen file set, avoiding the self-reference `contract_versions`'s uniform-coverage rule would otherwise create); production `_FROZEN_SRC_PCAE_RELATIVE_FILES`/`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` aligned in the same phase, per the 149O.20L.7K/149O.20L.7O.2H precedent; independent verification pending; see §61)
**Depends on (current, HMIC-unamended):** HMRC-001 v1.1, HATP-001 v1.0, HSCE-001 v1.1, RAE-001 v1.0, HBDC-001 v1.1, HPSE-001 v1.1, HHCE-001 v1.1
**Selected architecture source:** `docs/PHASE_149O_19_1_HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_ARCHITECTURE.md`

This is a **contract-freeze document**. It normatively freezes the shape
of a future implementation. It implements nothing. No `src/pcae/**`
file, and no other contract file, was modified to produce this
document. No certification artifact, active-certification pointer, or
revocation record exists as a result of this phase. *(Status corrected
149O.20L.7L.5, finding F-7L-5 whole-document scan; see §57.9/§58.)* The
hard-coded `mandatory_consumption_implementation_independently_verified
= False` ceiling this paragraph originally described no longer exists
at `hatp_mandatory_cutover.py:842-853`: Phase 149O.19.5F (Wave F)
replaced it with a fresh, uncached call to
`validate_active_hatp_mandatory_independent_verification_certification`,
whose result is mapped to this readiness term only via exact
`CertificationStatus.VALID` identity (`certification_status_satisfies_
readiness`), with every other status and any exception mapping to
`False` (fail-closed, no OR-path, no caller-supplied override). This
mechanical change does not, by itself, satisfy the term: no stored HMIC
certification exists anywhere on this host (§61), so the validator's
fresh call still resolves to `MISSING` and this readiness term still
evaluates `False` today — the same functional outcome as the old
hard-coded ceiling, reached by a different, now-dynamic mechanism. This
paragraph does not assert HMIC certification, HATP activation readiness,
Boundary C completion, first use, or `DeploymentBinding` existence — see
§0/§60 for those statuses, all still unmet.

---

## 0. Contract Identity and Status

HMIC-001 is a new, standalone contract. It does not amend HMRC-001,
HATP-001, HSCE-001, or RAE-001. It **consumes** those contracts'
existing, frozen, unmodified guarantees and defines the one remaining
seam HMRC-001 itself named but did not resolve: what protected evidence
may satisfy `mandatory_consumption_implementation_independently_verified`
inside `assess_hatp_mandatory_activation_readiness`'s six-item
conjunction, without collapsing that fact into anything the Agent OS
principal can write, influence, or self-certify.

Naming rationale (restated from the architecture phase): "HATP Mandatory
Independent-Verification Certification Contract" (**HMIC-001**) was
selected over reusing `HMRC-001` because certification is a distinct
trust domain from mandatory rollback *consumption* — HMRC-001 governs
how signed HATP evidence gates a real AG3/AG5 effect; HMIC-001 governs
how a *separate* protected certification statement gates one specific
input fact inside HMRC-001's own activation-readiness conjunction.
Reusing HMRC-001's numbering for a different trust domain would blur,
not clarify, contract ownership (§38).

---

## 1. Normative Language

SHALL / SHALL NOT / MUST / MUST NOT express mandatory requirements. MAY
expresses a genuinely open implementation choice. Every requirement
carries a stable ID: `HMIC-REQ-###`.

---

## 2. Purpose

Freeze a normative contract governing the protected, independently
verifiable certification that may eventually satisfy:

```
mandatory_consumption_implementation_independently_verified
```

inside HMRC-001's `assess_hatp_mandatory_activation_readiness` readiness
conjunction (`hatp_mandatory_cutover.py:842-853`), such that only a
valid protected certification for the **exact repository**, the
**exact deployment**, the **exact independently-verified
implementation**, and the **exact relevant contract set** can satisfy
that one input fact — and no repo-controlled status file, phase report,
test result, git commit string, environment value, or caller boolean
may substitute.

**HMIC-REQ-001.** This contract SHALL govern only the creation,
storage, validation, revocation, and supersession of the protected
independent-verification certification described above, and its
consumption as exactly one input fact inside HMRC-001's readiness
conjunction. It SHALL NOT govern any other readiness term, any other
operation class, or general software-release/deployment signing.

---

## 3. Scope and Relationship to Other Contracts

**HMIC-REQ-002.** This contract does NOT own, and SHALL NOT redefine:
the `LEGACY_COMPATIBLE` / `PREPARED` / `HATP_MANDATORY` Cutover State
Model, its transition graph, or any other term of the activation-
readiness conjunction (HMRC-001, unamended); proof cryptography,
verification algorithm, freshness, revocation, or binding semantics
(HATP-001); the signing ceremony or evidence-store schema (HSCE-001);
RAE Decision/Binding semantics (RAE-001); Permission Broker policy
meanings, POL-005, or decision vocabulary (PBPA-001/PBPC-001, neither of
which this contract amends); or repository-wide mutation coverage
classification (RWMPC-001).

**HMIC-REQ-003.** This contract references those frozen authorities by
exact existing function/class/contract name. It SHALL NOT introduce a
duplicate, parallel implementation of any identity, storage, or
verification primitive any of them already define.

**HMIC-REQ-004.** HMIC-001 supplies exactly one input fact —
`mandatory_consumption_implementation_independently_verified` — to
HMRC-001's six-item readiness conjunction. It does NOT own, evaluate, or
substitute for any of the other five terms (Class-B deployment valid,
HATP substrate operational, HSCE signing available, production
dependency provenance valid, Protected Activation Authority mechanism
available).

**HMIC-REQ-005.** This contract does not establish general software
release, build, or deployment signing. Its scope is narrowly the
HMRC-001 mandatory-consumption independent-verification certification
named above. A future, separate contract may generalize certification;
this one SHALL NOT be read as already having done so.

**HMIC-REQ-006.** `activate_hatp_mandatory` itself, the Cutover Record,
`POL-005`, and `COMP-002` are unaffected by this contract and remain
governed exclusively by HMRC-001 and the Permission Broker contracts.

---

## 4. Terminology

**HMIC-REQ-007.** The following terms are frozen for this contract and
any future implementation/verification phase that cites it:

| Term | Meaning |
|---|---|
| **Certification** | A `CertificationRecord` (§12) that has been validated `VALID` by §33's algorithm. Never a phase report, a test result, a status file entry, or a commit. |
| **Certification Record** | One immutable (except `status`/`revoked_at`) entry in `certifications.json` (§11-12). |
| **Active-Certification Pointer** | The single, explicit entry in `certification-bindings.json` (§13) naming which `CertificationRecord`, if any, is currently active for one `(repository_instance_id, canonical_deployment_root)` key. |
| **Protected Root** | `HATPTrustStore.production().root` — the same fixed, non-agent-writable, platform-level directory HATP-001/HMRC-001 already use. No second root exists (§9). |
| **Protected Admin Authority** | `PCAE_BOOTSTRAP_ADMIN_PRINCIPAL` — the same Class-B protected administrative/bootstrap principal 149O.1B.1 established, identical to HMRC-001's "Protected Activation Authority" (HMRC-REQ-041). |
| **Implementation Identity** | The pair `(implementation_commit, implementation_scope_digest)` (§17-19) identifying exactly what was independently verified. |
| **Frozen Authority-Bearing File Set** | The exact, enumerated file list of §18, whose byte contents feed `implementation_scope_digest`. |
| **Certify** | The creation ceremony (§25) producing a new immutable `CertificationRecord`. Distinct from, and never automatically causing, **Activate**. |
| **Activate** (this contract's sense) | The distinct, explicit admin write making a `CertificationRecord` the active pointer (§28). Not to be confused with `activate_hatp_mandatory` (HMRC-001), an unrelated, separate ceremony. |
| **Validation Status** | One value of the closed vocabulary in §34. |
| **Readiness Fact** | The boolean `mandatory_consumption_implementation_independently_verified`, `True` iff Validation Status is exactly `VALID` (§34). |

**HMIC-REQ-008.** "Certified" or "certification" SHALL NOT be used
informally in any future implementation to mean any of: a phase report
existing, a test suite passing, a git commit existing, or
`PROJECT_STATUS.md`/`tasks/TODO.md`/`CHANGELOG.md` stating completion.
These are all repository-local, agent-writable, and non-authoritative
(§24).

---

## 5. Semantic Walls (Normative)

**HMIC-REQ-009.** The following distinctions are frozen and extend
HMRC-001 §5 (HMRC-REQ-007). They SHALL NOT be collapsed by any future
implementation, log message, status field, or user-facing text:

```
phase completed                              ≠  certification
tests passed                                 ≠  certification
git commit exists                            ≠  certification
repository status (PROJECT_STATUS.md, etc.)  ≠  certification
implementation identity matches              ≠  certification (unless the
                                                 protected certification
                                                 itself validates VALID)
certification valid                          ≠  activation
certification valid                          ≠  PB ALLOW
certification valid                          ≠  HATP approval
certification valid                          ≠  runtime capability
certification valid                          ≠  execution
certification valid                          ≠  HATP production READY
activation                                   ≠  rollback permission
```

**HMIC-REQ-010.** No future implementation SHALL introduce a
`VALID_WITH_WARNING`-class status, or any other partial-credit outcome,
that still satisfies the readiness fact. The readiness fact is binary:
exactly `VALID` maps to `True`; every other status maps to `False`
(§34-35, HMIC-REQ-010 restated at HMIC-REQ-086).

---

## 6. Threat Model

**HMIC-REQ-011 (Threat-A, this contract's governing threat — unchanged
from HMRC-001 §28/HATP-001).** The agent/attacker principal CAN: edit
the repository; author, edit, or delete any repository-local file
(`PROJECT_STATUS.md`, `tasks/TODO.md`, `CHANGELOG.md`, phase reports,
test files, `.pcae/**`); author and run tests; commit and push; call any
public Python function directly, bypassing the CLI; invoke `pcae`
commands, including any read-only certification-inspection command this
contract permits (§26).

**HMIC-REQ-012.** The agent/attacker principal CANNOT: write to the
Protected Root (`HATPTrustStore.production().root`); create, activate,
supersede, or revoke a `CertificationRecord` or Active-Certification
Pointer; forge a hardware-backed signature or trusted-signer enrollment
(HATP-001, unmodified); substitute the production HATP provider or
trust store (F-2 closure, unmodified); or supply any certification-
validity-bearing boolean, digest, or identity string to any production
function (§24, §40).

**HMIC-REQ-013 (Class-B Protected Administrator).** The trusted
bootstrap/admin principal with real OS write access to the Protected
Root, per the existing Class-B model (149O.1B.1). This contract grants
this principal no *new* power; it reuses exactly the write-access
property HMRC-001's own Protected Activation Authority already
requires (HMIC-REQ-016).

**HMIC-REQ-014 (Root/platform compromise — explicitly out of scope).**
Root or full-host compromise (Threat-B) is explicitly out of scope,
exactly as HMRC-001/HATP-001 already scope it. This contract claims no
protection against an attacker with root/platform-level access, and
does not overclaim otherwise.

**HMIC-REQ-015 (No overclaim on transitive dependencies).** This
contract's implementation-identity binding (§17-21) is strictly
stronger than a bare commit SHA but does not achieve whole-program
formal identity; it names its residual limitation explicitly (§21)
rather than silently overclaiming completeness.

---

## 7. Authority Principal and Write Authority

**HMIC-REQ-016.** The sole authority permitted to create, activate,
supersede, or revoke a certification is the Protected Admin Authority
(§4, HMIC-REQ-013) — the same principal HMRC-REQ-041 already names as
"Protected Activation Authority" for `PREPARED → HATP_MANDATORY`
activation. Certification and activation share one authority principal
because both require the identical real-world property: real OS write
access to the Protected Root that the Agent OS principal structurally
lacks.

**HMIC-REQ-017.** The following are explicitly rejected as certification
authority, with no exception: the agent OS principal; any process or
CLI invocation running as the agent principal; an ordinary CLI user
sharing the agent's OS account (149O.1B.1 §6's same-user finding);
phase-lifecycle code; a test suite; a git hook; a `PROJECT_STATUS.md` or
`CHANGELOG.md` generator; an environment variable; a CLI boolean flag; a
username string; Git author identity; or repository ownership.

**HMIC-REQ-018.** The Agent OS principal has no effective filesystem
write permission to the production certification store. No in-process
"authority check" substitutes for this OS-level property (§26).

**HMIC-REQ-019 (Read Authority).** The agent/runtime principal MAY read
`certifications.json` and `certification-bindings.json` as part of
readiness evaluation — the same posture HATP-001 §11 already grants for
trust-store public material. Read access SHALL NOT imply, grant, or be
mistaken for write authority.

**HMIC-REQ-020 (No Application-Level Fake Admin).** No future
implementation SHALL permit any of the following to establish Protected
Admin Authority: a username string; an environment variable; a CLI
boolean; repository ownership; or Git author identity. Real OS file
permissions on the Protected Root are the only enforcement boundary.

---

## 8. Protected Storage Root

**HMIC-REQ-021.** The Protected Root is exactly `HATPTrustStore.
production().root` — the same fixed, platform-level, non-`Path.home()`-
derived, non-agent-writable directory `hatp_bootstrap.py::_default_
production_trust_root` already resolves. No new, second, or
independently-selected protected root is introduced.

**HMIC-REQ-022.** Certification files SHALL live under this existing
root, in their own file(s) (§11), never merged into `registry.json`
(deployment-binding/signer state) and never merged into
`cutover-record.json` (HMRC-001's own Cutover Record) — preserving
independent auditability and independent corruptibility-without-
affecting-integrity for each concern, per HMRC-REQ-043's own precedent.

**HMIC-REQ-023.** No environment variable, CLI flag, or configuration
file SHALL allow a production entrypoint to resolve any root other than
`HATPTrustStore.production().root` (§26, §40).

---

## 9. Storage Topology — Certification Model, Files, Multi-Repository Keying

**HMIC-REQ-024 (Certification Model, Selected).** The certification
model is a **protected registry entry**: append-only, keyed
`CertificationRecord` entries in one file, plus a separate explicit
active-pointer file — structurally parallel to `registry.json`'s
existing `DeploymentBinding`/`SignerRecord` shape (each entry immutable
except a `status`/`revoked_at` pair). This is not a monotonic latch (a
certification may be created, revoked, and recreated multiple times
before activation ever happens once — a different concern from
`HATP_MANDATORY`'s own one-way monotonicity, HMRC-REQ-039/040) and not a
single flat immutable artifact (which cannot support supersession or
repository/deployment keying without inventing ad hoc naming).

**HMIC-REQ-025 (Exactly Two Files, Frozen Names).** Exactly two files,
both directly under the Protected Root:

```
certifications.json               (append-only CertificationRecord entries, §12)
certification-bindings.json       (explicit active-certification pointer entries, §13)
```

No other certification-related file SHALL be introduced under v1.0. No
directory-per-repository or directory-per-deployment layout is used;
both files are single, shared files whose *entries* are keyed (§26).

**HMIC-REQ-026 (Repository/Deployment-Keyed Storage — Multi-Repository
Safety).** Both files key every entry by `(repository_instance_id,
canonical_deployment_root)` (§16), exactly mirroring how `registry.
json`'s own `deployment_bindings` dict is already keyed by
`repository_id`. Certification state for one repository or deployment
SHALL NOT affect, be visible to, or be selectable for any other
repository or deployment. No shared single-slot authority crossover
exists.

**HMIC-REQ-027.** This is a deliberate improvement over the Cutover
Record's own acknowledged flat single-slot topology (HMRC-001 §17,
carried forward): a second repository sharing the Protected Root
observes its own, correctly-scoped certification state, never another
repository's.

---

## 10. Portability

**HMIC-REQ-028 (Local-Only, No Import/Export).** Certification is
local-only. No production API imports, exports, or otherwise transports
a `CertificationRecord` or Active-Certification Pointer between hosts,
repositories, or deployments. Copying the underlying files to another
protected root does not certify that root's repository/deployment
(§16's binding checks reject it; §42 attack #8/#30).

**HMIC-REQ-029 (No Signature Added, v1.0).** No cryptographic signature
is added to `CertificationRecord` or the Active-Certification Pointer.
The Protected-Root OS-permission boundary is this repository's entire
trust boundary for identically-shaped artifacts (the Cutover Record
itself is unsigned); adding a signature only here, without also signing
the Cutover Record, would be asymmetric hardening of one artifact in a
system whose actual boundary is elsewhere. If a future phase makes
certification portable, that decision SHALL re-open this choice
explicitly — portability is exactly when a signature stops being
unnecessary and starts being required.

**HMIC-REQ-030 (No Hardware Touch Required, v1.0).** Certification
validation SHALL NOT require a FIDO2/hardware human-presence touch.
Certification is not rollback approval (HATP-001's evidence-signing
ceremony); it is a distinct administrative attestation gated by the
Protected Root's OS-permission boundary alone.

---

## 11. `CertificationRecord` Schema (v1, Closed)

**HMIC-REQ-031.** `certifications.json` contains a JSON object whose
schema version and entry list are both closed: unknown top-level fields
SHALL be rejected; duplicate JSON keys SHALL be rejected if the parser
can detect them; a boolean `version` SHALL be rejected (HMIC-REQ-032) —
mirroring `hatp_mandatory_cutover.py`'s and `hatp_bootstrap.py`'s
existing strict-parser discipline exactly.

**HMIC-REQ-032.** Exactly these fields per `CertificationRecord` entry,
no more, no fewer:

```
certification_id             opaque identifier; a SHA-256 hex digest
                              derived from the record's own
                              authority-sensitive fields at creation
                              time (§14) — never caller-supplied
repository_instance_id        CRI Model A Layer 1 repository identity
                              (repository_identity.py, unmodified)
canonical_deployment_root     CRI Layer 2 deployment binding
                              (hatp_bootstrap.py::resolve_canonical_
                              deployment_root, unmodified)
implementation_commit         git commit SHA of HEAD at certify time —
                              an identity component, not authority alone
                              (§17)
implementation_scope_digest   canonical SHA-256 digest over the frozen
                              authority-bearing file set (§18-19) — the
                              highest-priority implementation-identity
                              field
contract_versions             {"HMRC-001": "1.0", "HATP-001": "1.0",
                              "HSCE-001": "1.1", "RAE-001": "1.0",
                              "HBDC-001": "1.0", "HPSE-001": "1.0",
                              "HHCE-001": "1.0"} (illustrative versions;
                              see §20 for the current, exact seven-entry
                              key set) — the minimal sufficient contract
                              set (§20)
verification_record_digest    digest of the canonical phase-report
                              artifact this certification attests to —
                              evidentiary metadata only, never authority
                              (§23)
certified_at                  strict `YYYY-MM-DDTHH:MM:SS[.ffffff]Z`
                              timestamp, reusing `hatp_mandatory_
                              cutover.py::_TIMESTAMP_PATTERN` exactly
certified_by                  protected-authority reference string,
                              caller-supplied, no default, no process/
                              session/environment derivation — mirrors
                              `CutoverRecord.activated_by` exactly
status                        "active" | "revoked" (exactly these two
                              string values; mirrors `SignerRecord`/
                              `AuthorityRecord`'s existing vocabulary)
revoked_at                    present if and only if status == "revoked"
```

**HMIC-REQ-033.** `version` SHALL be validated as a strict positive
integer. A JSON boolean (`true`/`false`) SHALL be rejected as an
invalid `version`, identically to HMRC-REQ-046's own rule; `"1"`, `1.0`,
and `True` SHALL NOT equal `1` for this field.

**HMIC-REQ-034.** `status`/`revoked_at` SHALL be validated together,
never independently, mirroring `hatp_bootstrap.py::_require_revoked_at_
consistency` exactly: `revoked_at` present with `status == "active"` is
invalid; `status == "revoked"` with `revoked_at` absent is invalid.

**HMIC-REQ-035.** Once created, every field of a `CertificationRecord`
other than `status`/`revoked_at` is immutable. No future implementation
SHALL mutate `implementation_commit`, `implementation_scope_digest`,
`contract_versions`, or any other identity field of an existing record
in place. Recertification always creates a *new* record (§29).

---

## 12. `CertificationBinding` (Active-Certification Pointer) Schema (v1, Closed)

**HMIC-REQ-036.** `certification-bindings.json` contains a JSON object
with the same closed-schema discipline as §11 (unknown/duplicate/
malformed rejected). Exactly these fields per entry, keyed by
`(repository_instance_id, canonical_deployment_root)`:

```
repository_instance_id
canonical_deployment_root
active_certification_id       explicit pointer into certifications.json's
                              certification_id field, or the key is
                              simply absent (no active certification for
                              this repository/deployment) — never
                              computed by scanning, sorting, or globbing
```

**HMIC-REQ-037.** `active_certification_id` SHALL contain the exact
`certification_id` string. It SHALL NOT contain a file path, a partial
identifier, or any value requiring further resolution beyond an exact
lookup in `certifications.json`.

---

## 13. Certification ID Derivation

**HMIC-REQ-038.** `certification_id` is a SHA-256 hex digest (lowercase,
64 characters) computed over the canonical serialization (§15) of the
record's own authority-sensitive fields — `repository_instance_id`,
`canonical_deployment_root`, `implementation_commit`,
`implementation_scope_digest`, `contract_versions`, `verification_
record_digest`, `certified_at`, `certified_by` — excluding
`certification_id` itself (computed before it is assigned) and
excluding `status`/`revoked_at` (mutable fields never participate in
the identity digest).

**HMIC-REQ-039.** `certification_id` SHALL NOT be caller-supplied as a
free-form string under any circumstance. It is always tool-derived
(§25).

**HMIC-REQ-040 (Self-Consistency Check).** Validation (§33 step 11)
SHALL re-derive `certification_id` from the record's own stored fields
and reject the record as `MALFORMED` if it does not match the stored
`certification_id` — detecting in-place tampering of the file.

---

## 14. Canonical Serialization

**HMIC-REQ-041.** Every write to `certifications.json` or
`certification-bindings.json` SHALL use exactly `json.dumps(document,
indent=2, sort_keys=True) + "\n"`, UTF-8 encoded, `\n` line endings —
identical to the serialization convention `repository_identity.py`/
`hatp_mandatory_cutover.py` already use for their own protected
records.

**HMIC-REQ-042.** All digest inputs derived from this serialization
(certification-ID derivation, §13) use this exact canonical form — no
alternate whitespace, key-ordering, or separator convention is
permitted anywhere in a future implementation.

---

## 15. Repository and Deployment Binding

**HMIC-REQ-043.** `repository_instance_id` SHALL be derived exactly as
`repository_identity.py`'s existing CRI Model A Layer 1 identity — never
a new identity system, and never path-only identity.

**HMIC-REQ-044.** `canonical_deployment_root` SHALL be derived exactly
as `hatp_bootstrap.py::resolve_canonical_deployment_root`/
`DeploymentBinding` already define it — the same Layer 2 binding that
already defends against a copied `repository_instance_id` being reused
at the wrong physical deployment (HATP-REQ-057-063).

**HMIC-REQ-045.** Both identifiers SHALL be derived read-only by the
admin tool at certify time (§25) and re-derived read-only by the
validator at validation time (§33) — never accepted as caller input on
either path (§20, §40).

---

## 16. Implementation Identity — Git Commit Component

**HMIC-REQ-046.** `implementation_commit` is the git commit SHA of HEAD
in the repository being certified, obtained via `git rev-parse HEAD` (or
equivalent), at certify time.

**HMIC-REQ-047.** A commit SHA alone is explicitly insufficient as
authority. It is an identity component only; `implementation_scope_
digest` (§17-19) is the load-bearing implementation-identity term.

**HMIC-REQ-048 (Commit-Changed, Bytes-Same).** If a later validation
observes a different `HEAD` commit SHA than the certified value, even if
the frozen file set's bytes are unchanged, validation SHALL fail
(`IMPLEMENTATION_MISMATCH`, §34) — both `implementation_commit` and
`implementation_scope_digest` are required identity terms; a mismatch in
either is a mismatch of the whole.

**HMIC-REQ-049 (Bytes-Changed, Commit-Same).** If any frozen file's
on-disk bytes differ from the certified `implementation_scope_digest`
while `HEAD` is unchanged (a dirty working tree touching a frozen file),
validation SHALL fail (`IMPLEMENTATION_MISMATCH`) identically.

---

## 17. Implementation Identity — Frozen Authority-Bearing File Set

**HMIC-REQ-050 (Exact Enumeration, No Prose Substitute).** The frozen
authority-bearing file set for `implementation_scope_digest` is exactly
these thirty-eight files, no more, no fewer, no caller-suppliable
alternate or "legacy" scope selector of any kind — established at v1.1
(§50), carried forward byte-unchanged through v1.2 (§51), widened by
one entry at the same v1.2 version by the 149O.20D.1 content-identity
binding repair (§52; finding B-149O.20D-1), widened by three further
entries at v1.3 by the 149O.20K Class-B verifier source-scope closure
(§53), widened by two further entries at v1.4 by the 149O.20L.7K
DeploymentBinding producer source-scope closure (§55), widened by
five further entries at v1.5 by the 149O.20L.7O.2H Trust-Enrollment/
signing closure-limb (d) amendment (§59), widened by one further
`src/pcae/`-relative entry at v1.6 by the 149O.20L.7O.2H.2 symbol-level
source-closure repair (§60), and widened by two further
repository-root-relative entries at v1.7 by the 149O.20L.7O.2M
standalone Trust-Enrollment admin entry-point source-scope evolution
(§61). Paths under `src/pcae/` are
given relative to that directory; every other path is given relative to
the repository root (this includes, but is not limited to, contract
documents under `docs/contracts/` and standalone scripts under
`scripts/`):

```
core/hatp_mandatory_cutover.py
core/hatp_ag_authority.py
core/hatp_rollback_consumption.py
core/hatp_bootstrap.py
core/human_approval_trusted_provenance.py
core/repository_identity.py
core/rollback_approval_evidence.py
core/hatp_evidence_store.py
core/hatp_signed_evidence.py
core/agent.py
commands/agent.py
cli.py
core/permission_broker.py
core/permission_broker_foundation.py
core/hatp_providers.py
core/hatp_fido2_provider.py
core/hatp_piv_provider.py
core/hatp_hardware_credentials.py
core/hatp_mandatory_certification.py
core/hatp_class_b_topology_verifier.py
core/hatp_environment_lock_verifier.py
core/hatp_class_b_conformance.py
core/hatp_deployment_binding_admin.py
core/hatp_signing_ceremony.py
core/hatp_hardware_credential_admin.py
core/hatp_principal_signer_admin.py
core/paths.py

docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md      (HMRC-001)
docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md        (HATP-001)
docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md     (HSCE-001)
docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md               (RAE-001)
docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md                  (HBDC-001)
docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md         (HPSE-001)
docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md      (HHCE-001)
scripts/hatp_certification_admin.py
scripts/hatp_deployment_binding_admin.py
scripts/hatp_hardware_credential_admin.py
scripts/hatp_principal_signer_admin.py
```

The thirty-first through thirty-third entries,
`core/hatp_signing_ceremony.py`, `core/hatp_hardware_credential_
admin.py`, and `core/hatp_principal_signer_admin.py`, and the thirty-
fourth and thirty-fifth entries, `docs/contracts/HATP_PRINCIPAL_SIGNER_
ENROLLMENT_CONTRACT.md` (HPSE-001) and `docs/contracts/HATP_HARDWARE_
CREDENTIAL_ENROLLMENT_CONTRACT.md` (HHCE-001), were added by Phase
149O.20L.7O.2H under newly-added closure limb (d) (§59): the first three
implement the Trust-Enrollment/signing authority surface — the
production signing ceremony and the hardware-credential/principal-
signer administrative writers — reachable from, or a non-reachable
producer anchor of, limb (d)'s named entry points; the two contract
documents are HPSE-001's and HHCE-001's own governing-contract bytes,
bound under HMIC-REQ-053's separate, distinct content-binding rule (not
limb (d)'s call-graph closure rule — see HMIC-REQ-052's own text) the
moment both contracts join `contract_versions` (HMIC-REQ-067, §59.10).

The v1.6 source addition, `core/paths.py`, is the twenty-seventh
`src/pcae/`-relative entry in the literal presentation above. Phase
149O.20L.7O.2H.1 demonstrated that the reached `HarnessPath.join` and
`.path` behavior selects the live AG3/AG5 records from which
`original_commit_sha`/`ecp_id` become signing-context authority inputs.
Changing only that file can redirect those inputs while every v1.5
frozen byte remains unchanged; §60 records the reproduction and repair.

The twenty-ninth and thirtieth entries, `core/hatp_deployment_binding_
admin.py` and `scripts/hatp_deployment_binding_admin.py`, were added by
Phase 149O.20L.7K under limb (c)'s newly-added third anchor (§55): these
two files are, respectively, the sole producer of `DeploymentBinding`
create/rotate/revoke authority and its sole intended Protected Admin
ceremony caller — neither is reachable from `verify_class_b_deployment_
conformance`'s own call graph (they are a separate write path), but
their output is exactly the `DeploymentBinding` registry state the
already-frozen `hatp_bootstrap.py`/`repository_identity.py` read path
consumes to compute HBDC-REQ-042's contribution to that same
`COMPLIANT`/`NON_COMPLIANT`/`INDETERMINATE` verdict, directly mirroring
why `scripts/hatp_certification_admin.py` was bound at v1.1 (§50) as a
second, non-call-graph anchor under limb (b).

The twenty-fifth entry, `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`
(HBDC-001), was added by Phase 149O.20D.1 to repair finding
B-149O.20D-1 (§52): Phase 149O.20D (§51) had bound `HBDC-001` into
`contract_versions` (HMIC-REQ-067) but deliberately left its document
bytes outside `implementation_scope_digest`, leaving a same-version,
content-only edit to `HBDC-001` certification-invisible — unlike the
other four bound contracts, which HMIC-REQ-053 already binds by both
mechanisms. This entry closes that gap using the identical mechanism
already applied to `HMRC-001`/`HATP-001`/`HSCE-001`/`RAE-001`, not a new
one.

The four entries `core/hatp_providers.py`, `core/hatp_fido2_provider.py`,
`core/hatp_piv_provider.py`, `core/hatp_hardware_credentials.py` were
added by Phase 149O.19.3R to repair finding B-149O.19.3-1 (§49): the
original eighteen-file v1.0 enumeration under-bound four
authority-sensitive production dependencies of files already in the
frozen set. The next two entries, `core/hatp_mandatory_certification.py`
and `scripts/hatp_certification_admin.py`, were added by Phase
149O.19.5E.1 to resolve Stop Condition W-1 (§50): Waves A–E
(149O.19.5A–5E) implemented this contract's own certification-parsing,
implementation-identity-derivation, protected-storage, active-binding,
revocation, and Validation Status determination logic in
`core/hatp_mandatory_certification.py`, and its sole intended Protected
Admin ceremony caller in `scripts/hatp_certification_admin.py` — neither
file existed when the original v1.0/repaired-v1.0 enumeration was
written, and both are now themselves capable of altering
certification-relevant outcomes (§17 HMIC-REQ-052(b)). The final three
entries, `core/hatp_class_b_topology_verifier.py`,
`core/hatp_environment_lock_verifier.py`, and
`core/hatp_class_b_conformance.py`, were added by Phase 149O.20K under
newly-added closure limb (c) (§53; addresses CBV-S1): these three files
implement the Class-B deployment-conformance verifier island (149O.20H–
149O.20J) whose `COMPLIANT`/`NON_COMPLIANT`/`INDETERMINATE` verdict
HMIC-REQ-067's own v1.2 text already names as the fact HMIC-REQ-063's
Option-C accepted-residual branch depends on, but whose source bytes
were, before v1.3, outside `implementation_scope_digest` entirely —
capable of silently altering that verdict without changing any
HMIC-bound digest. §49 records the v1.0 repair history; §50 records the
v1.1 amendment history; §51 records the v1.2 amendment history
(contract_versions widened to five members, twenty-four-file enumeration
left unchanged); §52 records the 149O.20D.1 repair history that added
the twenty-fifth entry; §53 records the 149O.20K amendment history that
added the twenty-sixth through twenty-eighth entries; §55 records the
149O.20L.7K amendment history that added the twenty-ninth and thirtieth
entries; §59 records the 149O.20L.7O.2H amendment history that added the
thirty-first through thirty-fifth entries; §60 records the v1.6
`core/paths.py` addition; §61 records the v1.7 addition of the
thirty-seventh and thirty-eighth entries, `scripts/hatp_hardware_
credential_admin.py` and `scripts/hatp_principal_signer_admin.py`;
this section states only the current, thirty-eight-file enumeration.
`core/hatp_mandatory_certification.py` is listed in the `src/pcae/`-
relative bucket (it lives at `src/pcae/core/hatp_mandatory_certification.py`);
`scripts/hatp_certification_admin.py` is listed in the repository-root-
relative bucket (it lives outside `src/pcae/` entirely, at the
repository-root-relative path shown) — see HMIC-REQ-055 for the
canonicalization rule this split feeds, and §50 for why a standalone
`scripts/` path is safely representable under the existing grammar. The
three 149O.20K entries are all `src/pcae/`-relative, at
`src/pcae/core/hatp_class_b_topology_verifier.py`,
`src/pcae/core/hatp_environment_lock_verifier.py`, and
`src/pcae/core/hatp_class_b_conformance.py`. The two 149O.20L.7K entries
follow the identical `core/hatp_mandatory_certification.py`/`scripts/
hatp_certification_admin.py` split precedent: `core/hatp_deployment_
binding_admin.py` is `src/pcae/`-relative (it lives at `src/pcae/core/
hatp_deployment_binding_admin.py`); `scripts/hatp_deployment_binding_
admin.py` is repository-root-relative (it lives outside `src/pcae/`
entirely, at the repository-root-relative path shown). The three
149O.20L.7O.2H source entries are all `src/pcae/`-relative, at
`src/pcae/core/hatp_signing_ceremony.py`, `src/pcae/core/hatp_hardware_
credential_admin.py`, and `src/pcae/core/hatp_principal_signer_admin.py`;
the two 149O.20L.7O.2H contract-content entries are repository-root-
relative, at `docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_
CONTRACT.md` and `docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_
CONTRACT.md`, following the identical placement convention already
applied to `HMRC-001`/`HATP-001`/`HSCE-001`/`RAE-001`/`HBDC-001`'s own
contract-document entries — contract bytes are never `src/pcae/`-
relative, regardless of which limb or requirement binds them. The two
149O.20L.7O.2M entries, `scripts/hatp_hardware_credential_admin.py` and
`scripts/hatp_principal_signer_admin.py`, are both repository-root-
relative, following the identical `scripts/hatp_certification_admin.py`/
`scripts/hatp_deployment_binding_admin.py` placement precedent (they
live outside `src/pcae/` entirely, at the repository-root-relative
paths shown) — see §61 for the worked closure analysis.

**HMIC-REQ-051 (Ownership — Embedded, Not an External Manifest).** This
enumeration is embedded directly in this frozen contract (HMIC-REQ-050),
not delegated to an external, separately-versioned manifest file. No
agent-editable list can redefine the certified scope: changing this
enumeration requires amending this contract itself (§44), which is not
an agent-writable action under this repository's own contract-freeze
discipline (contract files are themselves part of the frozen set they
describe, HMIC-REQ-050's seven `docs/contracts/` entries, as of the
149O.20L.7O.2H amendment — formerly five since the 149O.20D.1 repair,
formerly four before it, §52/§59).

**HMIC-REQ-052 (Transitive-Dependency Coverage — Closure Rule).** The
frozen set SHALL contain every PCAE-owned (`src/pcae/**` or `scripts/`)
production source file whose modification is capable of altering
either:

(a) the certification-relevant HMRC-001 mandatory-consumption-chain
enforcement or HATP-001 verification-authority semantics that this
certification attests were correctly implemented — specifically, any
file reachable from `assess_hatp_mandatory_activation_readiness`'s own
call graph (or from any function it calls, transitively) that can
change: provider registry/selection; hardware or cryptographic
assertion verification; trust-store or protected-credential-store
resolution; HATP verification status derivation; RAE/HATP approval
derivation; Permission Broker request construction; or AG3/AG5
mandatory-effect gating; or

(b) *(added v1.1, §50)* this certification's own implementation
semantics — certification/binding parsing and canonical serialization,
certification-ID or implementation-identity derivation, protected
certification-state storage/persistence, active-certification binding,
revocation, or Validation Status / VALID-non-VALID determination —
specifically, any file reachable from
`validate_active_hatp_mandatory_independent_verification_certification`'s
own call graph, or from the Protected Admin ceremony functions
`certify`/`activate`/`revoke` in `scripts/hatp_certification_admin.py`,
transitively; or

(c) *(added v1.3, §53; widened v1.4, §55)* the Class-B deployment-
conformance verdict that a future, separately-governed HMIC-REQ-063
Option-C mechanism would rely on — specifically, any file reachable
from `verify_class_b_deployment_conformance`'s own call graph (its
topology and environment-lock sub-verifiers included, transitively)
that can change the `COMPLIANT` / `NON_COMPLIANT` / `INDETERMINATE`
result `hatp_class_b_conformance.py` computes, **or**, *(added v1.4,
§55)* the `DeploymentBinding` producer/rotation/revocation functions
(`create_deployment_binding`/`rotate_deployment_binding`/`revoke_
deployment_binding`) in `core/hatp_deployment_binding_admin.py`, or
their sole intended Protected Admin ceremony caller in `scripts/
hatp_deployment_binding_admin.py`, transitively — mirroring limb (b)'s
own dual-anchor construction (§50): this third anchor is not reachable
from `verify_class_b_deployment_conformance`'s own call graph (it is a
separate write path never imported by the verifier), but its write
output is exactly the `DeploymentBinding` registry state HBDC-REQ-042's
already-bound check (`_check_deployment_identity`, reached via `hatp_
bootstrap.py`/`repository_identity.py`, both already HMIC-REQ-050
members) reads to help compute that same verdict — a byte edit to the
producer or its admin-ceremony caller (e.g. weakening `AuthorityEvidence`
validation, or silently reactivating a revoked entry) can change what
`DeploymentBinding` the already-frozen read path accepts as matching,
and therefore the verdict, without changing any pre-v1.4 HMIC-bound
digest. *(Corrected 149O.20L.7L.1, finding F-7L-1; see §56.)* Unlike
this third anchor, limb (c)'s first anchor is **not** anticipatory as of
v1.4: `verify_class_b_deployment_conformance` already has a real,
mandatory production consumer — Phase 149O.20L.3 wired it into
`hatp_mandatory_cutover.py`'s `_assess_hatp_mandatory_activation_
readiness_at_root` as the eighth activation-readiness term
(`class_b_deployment_conformance_satisfies_readiness`), re-evaluated
again, lock-held, immediately before any real `HATP_MANDATORY`
activation write; that wiring landed after 149O.20K (v1.3, §53) — so
§53's own "zero production consumers" language was accurate when
149O.20K wrote it and is left unmodified as a legitimate historical
snapshot (§56.1) — but the wiring predates 149O.20L.7K (v1.4, §55)
itself: by the time 149O.20L.7K wrote the same "zero production
consumers" language, it was no longer true, and §55's language is
repaired at §56.1. The producer's own
third-anchor rationale is unaffected by this correction and remains
exactly as originally stated: the `DeploymentBinding` producer/admin
write path (`create_deployment_binding`/`rotate_deployment_binding`/
`revoke_deployment_binding` and their Protected Admin ceremony caller)
is genuinely **not** reachable from `verify_class_b_deployment_
conformance`'s own call graph — it is a separate write path never
imported by, and never importing, the verifier — which is precisely why
this third anchor exists as a distinct, non-reachability binding rather
than being redundant with the first anchor. That separate write path
remains anticipatory: no real `DeploymentBinding` has ever been created
(§55 reconfirms zero live invocations) — the third anchor binds the
producer's authority-sensitive source now, before it has a real
invocation, precisely so that the eventual first `DeploymentBinding`
write inherits an already-closed source scope rather than an open one.
The verifier itself needed no such anticipatory framing even at v1.3/
v1.4's own telling — it was already live-consumed throughout.

(d) *(added v1.5, §59; source closure corrected v1.6, §60; standalone admin entry-point anchor widened v1.7, §61)* the Trust-Enrollment/signing authority surface —
specifically, any file reachable from `production_sign_rollback_
evidence`'s own call graph (`core/hatp_signing_ceremony.py`'s production
signing-ceremony entry point) that can change hardware-credential
registry state, principal/signer identity binding, provider-profile
validation at registration time, or signing-time signer/credential
resolution, **or**, mirroring limb (c)'s own dual-anchor construction
(§55), the Trust-Enrollment writer entry points — the registration/
revocation mutating operations in `core/hatp_hardware_credential_
admin.py` and `core/hatp_principal_signer_admin.py` — which are not
themselves reachable from `production_sign_rollback_evidence`'s own call
graph (they are a separate write path), but whose write output
(`HardwareCredentialRecord`/`PrincipalRecord`/`SignerRecord` state) is
exactly what the signing ceremony's consumer-side lookups read at
signing time. This includes `core/paths.py`: the signing path reaches
`HarnessPath.join` through `build_rollback_review` for AG3 and reaches
`HarnessPath.path` through `lookup_promotion_execution_record` for AG5;
those symbols select the live operation record whose `original_commit_
sha`/`ecp_id` is incorporated into the signing context. As of v1.7
(§61), this limb further extends to the standalone Trust-Enrollment
administrative CLI entry points `scripts/hatp_hardware_credential_
admin.py` and `scripts/hatp_principal_signer_admin.py` — the sole
intended Protected Admin ceremony callers of the two already-bound core
writer modules named above, mirroring this same limb's own existing
dual-anchor pattern one layer further out: neither script is reachable
from `production_sign_rollback_evidence`'s own call graph either (they
are the operator-facing callers of the write path, not the write path
itself), but each script owns the real operation-selection,
confirmation-boundary, and dispatch logic that decides *which*
`register_credential`/`revoke_credential`/`enroll_principal`/
`revoke_principal`/`enroll_signer`/`revoke_signer` call the
already-bound writer executes — an attacker who altered only a script
(e.g. skipping its confirmation gate, or dispatching `revoke` where
`enroll` was requested) could change the protected registry's real
content while every pre-v1.7 frozen byte remained unchanged. This limb
governs *source* closure only; it does not
itself bind `HPSE-001`'s or `HHCE-001`'s contract bytes — that separate
binding is HMIC-REQ-053's concern (§59.16), reached independently via
`contract_versions`' widening (§59, HMIC-REQ-067), not via this limb's
call-graph logic. This limb's own worked transitive-completeness
analysis is recorded at §59.3-§59.6; §60 corrects its `pcae.core.paths`
misclassification and rechecks the still-excluded audit-only leaves
`pcae.core.provenance`, `pcae.core.git_status`, and `pcae.core.tasks`;
§61 records the v1.7 worked closure analysis of both standalone admin
scripts' own import graphs, finding no not-yet-bound dependency.

A file SHALL NOT be added merely because it is imported by a frozen
file if no reachable code path from that file can change one of the
outcomes above under any limb (§49's transitive-completeness table
records this contract's own worked application of limb (a); §50
records the worked application of limb (b), including files
deliberately left unbound with rationale; §53 records the worked
application of limb (c)'s first anchor; §55 records the worked
application of limb (c)'s third anchor; §59 records the worked
application of limb (d), corrected by §60's symbol-level reanalysis).

This enumeration is derived as the union of: (a) the architecture-
selected core set (`docs/PHASE_149O_19_1_..._ARCHITECTURE.md` §9 — the
HMRC-001 dependency closure plus the four contract files themselves),
(b) 149O.19.2's own named minimum transitive-dependency evaluation set
(`hatp_mandatory_cutover.py`, `hatp_rollback_consumption.py`,
`hatp_ag_authority.py`, `human_approval_trusted_provenance.py`,
`rollback_approval_evidence.py`, `hatp_evidence_store.py`,
`hatp_signed_evidence.py`, `agent.py`, `commands/agent.py`, `cli.py`,
`permission_broker.py`, `permission_broker_foundation.py`, and
repository-identity/Class-B trust-root code), (c) Phase 149O.19.3R's
own independent re-walk of the provider-layer authority path (§49),
which added `hatp_providers.py`, `hatp_fido2_provider.py`,
`hatp_piv_provider.py`, and `hatp_hardware_credentials.py`, (d)
Phase 149O.19.5E.1's own application of newly-added limb (b) above to
the by-then-implemented HMIC certification/validation implementation
itself, which added `core/hatp_mandatory_certification.py` and
`scripts/hatp_certification_admin.py` (§50), (e) Phase 149O.20K's
own fresh AST/import dependency walk of the Class-B verifier island
under newly-added limb (c) above, which added
`core/hatp_class_b_topology_verifier.py`,
`core/hatp_environment_lock_verifier.py`, and
`core/hatp_class_b_conformance.py` (§53), and (f) Phase 149O.20L.7K's
own fresh AST/import dependency walk of the newly-implemented
`DeploymentBinding` producer under limb (c)'s newly-widened third
anchor above, which added `core/hatp_deployment_binding_admin.py` and
`scripts/hatp_deployment_binding_admin.py` (§55), and (g) Phase
149O.20L.7O.2H's own fresh AST/import dependency walk of the
Trust-Enrollment/signing authority surface under newly-added limb (d)
above, which added `core/hatp_signing_ceremony.py`, `core/hatp_
hardware_credential_admin.py`, and `core/hatp_principal_signer_
admin.py` (§59), (h) Phase 149O.20L.7O.2H.2's symbol-level re-walk
of that same limb (d), which added `core/paths.py` (§60), and (i)
Phase 149O.20L.7O.2M's own fresh re-derivation of limb (d)'s standalone
admin-entry-point anchor, which added `scripts/hatp_hardware_
credential_admin.py` and `scripts/hatp_principal_signer_admin.py`
(§61). The reached
authority sources are now fully covered under this closure rule; §49
records the complete
limb-(a) transitive-completeness analysis, including the specific,
non-authority-sensitive dependencies that rule deliberately excludes
(the Permission-Broker policy-decision-support
modules `gate_dry_run`/`scope_preflight`/`shell_gate` and their own
`gate_dry_run_context`/`artifact_index`/`decision_log`/
`governance_timeline`/`memory_snapshot`/`project_state`/`risk_register`
dependents; and `rollback_approval_evidence.py`'s own RAE-001
creation-ceremony publication/interactive-workflow imports, which are
not reachable from the readiness-evaluation call graph); §50 records
the complete limb-(b) transitive-completeness analysis for the two
newly-bound files; §53 records the complete limb-(c)
transitive-completeness analysis for the three newly-bound Class-B
verifier files, including the same `pcae.core.paths` exclusion
reapplied under limb (c) and the two already-bound files
(`hatp_bootstrap.py`, `repository_identity.py`) the island also
imports; §55 records the complete limb-(c)-third-anchor
transitive-completeness analysis for the two newly-bound
DeploymentBinding producer files, including the `pcae.core.paths` and
`pcae.core.provenance` exclusions and the two already-bound files
(`hatp_bootstrap.py`, `repository_identity.py`) the producer also
imports; §59 records the complete limb-(d) transitive-completeness
analysis for the three newly-bound Trust-Enrollment/signing authority
files and its original four leaf exclusions; §60 supersedes only the
`pcae.core.paths` classification, binds it, and independently retains
the audit-only `pcae.core.provenance`/`pcae.core.git_status`/
`pcae.core.tasks` exclusions; §61 records the complete v1.7 closure
analysis for the two newly-bound standalone Trust-Enrollment admin
scripts, finding their entire import graph (direct and lazy-imported)
already resolves within the pre-v1.7 frozen set.

**HMIC-REQ-053 (Contract Bytes Participate Directly, Explicit
Separation from `contract_versions`).** The seven contract files'
byte contents — as of the 149O.20D.1 repair (§52), this included
`HBDC-001`, previously the sole `contract_versions` member excepted from
this rule (§51, HMIC-REQ-145 pre-repair); as of the 149O.20L.7O.2H
amendment (§59), this additionally includes `HPSE-001` and `HHCE-001`,
bound uniformly the moment both join `contract_versions` (HMIC-REQ-067),
never as a deferred, disclosed exception the way `HBDC-001`'s v1.2
addition originally was — participate in `implementation_scope_digest`
directly (HMIC-REQ-050), as a distinct, additional binding from the
`contract_versions` field's own version-header check (§22, §33 step
10). These two mechanisms are deliberately redundant, not
interchangeable: an edit to a bound contract's *prose* (without a
version-header bump) is caught by the digest binding even though
`contract_versions`' version-string comparison alone would not detect
it. No future implementation SHALL treat either mechanism as sufficient
without the other. As of the 149O.20L.7O.2H amendment, every
`contract_versions` member (HMIC-REQ-067, seven entries) receives both
bindings uniformly — no `contract_versions` member is exempted from the
digest binding.

---

## 18. Implementation Identity — Digest Algorithm and Canonical Manifest

**HMIC-REQ-054 (File Digest Algorithm).** SHA-256, applied to the raw
bytes of each frozen file's on-disk content at digest-computation time
(never `git show HEAD:<path>` — HMIC-REQ-049 requires working-tree
bytes, not a clean-commit blob).

**HMIC-REQ-055 (Path Canonicalization).** Every frozen path (HMIC-REQ-
050) is repository-relative, POSIX-separator (`/`), case-sensitive
exactly as stored on disk, containing no `..` segment and no absolute
component. No path normalization beyond exact string match against
HMIC-REQ-050's literal enumeration is permitted.

**HMIC-REQ-056 (File Order).** Files are processed in the exact
lexicographic order of their canonical path strings (HMIC-REQ-055) —
never filesystem enumeration order, never manifest-declaration order if
those ever differ (they do not for v1.0, since the manifest is HMIC-
REQ-050's own literal list).

**HMIC-REQ-057 (Per-File Record Domain — Avoiding Concatenation
Ambiguity).** For each frozen path, the per-file record is exactly:

```
<canonical_path> + "\0" + <sha256_hex_of_file_bytes> + "\n"
```

UTF-8 encoded. The null byte (`\0`) between path and digest, and the
newline (`\n`) terminating each record, make every record
self-delimiting and immune to the concatenation ambiguity that a bare
"sort and concatenate raw file bytes" scheme would introduce (two
different file-content splits could otherwise hash identically).

**HMIC-REQ-058 (`implementation_scope_digest` Derivation).**
`implementation_scope_digest` is the SHA-256 hex digest of the
concatenation, in HMIC-REQ-056's order, of every HMIC-REQ-057 record for
every path in HMIC-REQ-050. This two-level construction (hash each
file's bytes first, then hash the ordered, delimited list of
path+digest records) is frozen exactly; no future implementation SHALL
substitute a single-level "hash all file bytes concatenated" scheme.

**HMIC-REQ-059 (Missing Frozen File).** If any HMIC-REQ-050 path does
not exist on disk at digest-computation (creation) or digest-
recomputation (validation) time, the operation SHALL fail:
certification creation SHALL fail (§25); certification validation
SHALL yield `IMPLEMENTATION_MISMATCH` (§34).

**HMIC-REQ-060 (Extra, Non-Frozen Files).** A file present in the
repository but not named in HMIC-REQ-050 SHALL NOT affect
`implementation_scope_digest` in either direction — its presence,
absence, or content change is invisible to this digest. This is a
deliberate, named limitation (§21), not a claim that no unlisted file
could ever matter.

**HMIC-REQ-061 (Symlinked Frozen File — Reject).** If any HMIC-REQ-050
path resolves to a symlink (the path itself, or any parent directory
component up to the repository root, is a symlink), digest computation
SHALL treat this as a failure for that file — mirroring the
`_reject_symlink` discipline `hatp_mandatory_cutover.py`/`repository_
identity.py`/`hatp_bootstrap.py` already apply to every protected path
they own. No attacker-controlled external symlink target is ever
resolved and hashed.

**HMIC-REQ-062 (Non-Regular Frozen File — Reject).** If any HMIC-REQ-050
path resolves to a directory, FIFO, device, socket, or any non-regular
file, digest computation SHALL treat this identically to HMIC-REQ-061 —
a failure for that file, propagating to `IMPLEMENTATION_MISMATCH` at
validation (or creation failure at certify time, §25).

---

## 19. Implementation Identity — Residual Limitations (Named, Not Hidden)

**HMIC-REQ-063 (Import-Shadowing / Executed-Code Binding — Out of
Scope, v1.0).** `implementation_scope_digest` binds the *on-disk byte
content* of the frozen file set. It does NOT verify that the Python
interpreter actually executing PCAE resolves its imports of those
modules to those exact on-disk files (module shadowing, `sitecustomize`,
`PYTHONPATH` injection, or an editable-install redirect could in
principle cause a different file's code to execute despite an identical
on-disk frozen-file digest). v1.0 of this contract does NOT implement an
executed-code/runtime-module-resolution check. This is a named,
explicit limitation — not a silent gap — carried forward unresolved from
`docs/PHASE_149O_19_1_..._ARCHITECTURE.md` §9's own honest disclosure
(item 139 there). A future implementation MAY add such a check (e.g.
verifying loaded module `__file__` paths resolve inside the certified
repository root); this contract neither requires nor forbids that
future addition, but v1.0 certification validity SHALL NOT be
represented, in any user-facing text, as having verified it.

**HMIC-REQ-064 (Editable-Install / Source-Checkout Topology Only,
v1.0).** v1.0 certification is scoped exclusively to a canonical
source-checkout or editable-install deployment topology — the only
topology PCAE runs from today. Installed-wheel or other non-editable
distribution modes are explicitly unsupported by v1.0; no future
implementation SHALL silently treat a wheel-installed deployment as
certifiable under this version without an explicit, separate future
contract revision naming that mode.

**HMIC-REQ-065 (Transitive-Dependency Boundary).** `implementation_
scope_digest` does not bind: the Python interpreter version; native or
third-party package versions; or any file not named in HMIC-REQ-050
that those files might transitively import. These are separate,
future deployment/environment-readiness concerns, explicitly out of
this contract's scope — named here so no future implementation
accidentally assumes this contract already covers them.

**HMIC-REQ-066 (No Overclaim Restated).** This contract's implementation
identity is strictly stronger than a bare commit SHA and is consistent
with, not weaker than, this repository's existing trust model elsewhere
(the Cutover Record itself relies on the identical Protected-Root
OS-permission boundary without a stronger executed-code binding).
Requiring more of certification than the repository already requires of
`activate_hatp_mandatory` itself would be inconsistent, not more secure.

---

## 20. Contract Binding Set

**HMIC-REQ-067 (Revised, v1.5 — HPSE-001/HHCE-001 added).** The minimal
sufficient `contract_versions` set is exactly: `HMRC-001` (defines the
consumption chain this certification ultimately gates), `HATP-001`
(proof verification/trust-store semantics the consumption chain depends
on), `HSCE-001` (evidence envelope schema the consumption chain loads),
`RAE-001` (approval-derivation semantics the consumption chain calls),
`HBDC-001` (*as of v1.2*, deployment-topology/environment-lock
semantics that determine whether the Class-B environment a Model-A
certification's `implementation_scope_digest` is computed inside may
legitimately be treated as sufficient for HMIC-REQ-063's Option-C
accepted-residual branch — §51), and, *as of v1.5*, `HPSE-001`
(Principal/Signer enrollment identity, cross-registry consistency, lock
ordering, and revocation semantics the Trust-Enrollment/signing closure
limb (d) source directly implements — §59) and `HHCE-001` (Hardware
Credential enrollment identity, public-key representation,
provider-profile validation, and registration/revocation semantics the
same closure-limb (d) source directly implements — §59). Seven entries,
no more, no fewer, as of v1.5, unchanged at v1.6 (§60), and unchanged at
v1.7 (§61) — v1.7 widens HMIC-REQ-050's *source* scope only (the two
standalone Trust-Enrollment admin scripts), not `contract_versions`.

**HMIC-REQ-068.** `RWMPC-001`, `PBPA-001`, and `PBPC-001` remain
explicitly excluded from `contract_versions`, unchanged by v1.2-v1.7.
`RWMPC-001` only classifies AG3/AG5 as `EXECUTION_CLASS_ROLLBACK`;
changing it does not change what mandatory-consumption *implementation*
looked like at verification time. `PBPA-001`/`PBPC-001` govern
Permission Broker policy, a separate, downstream concern from the
consumption chain's own implementation correctness (HMRC-REQ-002-004) —
a `POL-005` policy change does not retroactively invalidate the
verification that the consumption chain itself was implemented
correctly. `HBDC-001` (v1.2, HMIC-REQ-067) receives the opposite
disposition deliberately: unlike `RWMPC-001`/`PBPA-001`/`PBPC-001`,
HBDC-001 governs a fact this certification's own Option-C reliance
directly depends on (§51), not a downstream policy concern — it is
included, not excluded. (Note: PB *module bytes* —
`permission_broker.py`/`permission_broker_foundation.py` — are still
bound into `implementation_scope_digest` per HMIC-REQ-050/052; only the
separate `contract_versions` policy-version binding excludes PBPA-001/
PBPC-001. §17's HMIC-REQ-053 note applies: these are two distinct
bindings, not one.)

**HMIC-REQ-069 (Contract Drift).** Validation (§33 step 10) SHALL
compare each `contract_versions` entry — seven entries as of v1.5,
unchanged at v1.6, and unchanged at v1.7 — against
the named contract's own current, live version header. Any mismatch —
including a contract having been revised to a new version since
certification, or a required contract key absent from a stored record
(HMIC-REQ-031's closed-schema discipline) — SHALL yield
`CONTRACT_MISMATCH` or `MALFORMED` as HMIC-REQ-031/069 respectively
require (§34). No compatibility-mapping table exists; any version
difference, or any missing required key, is a mismatch. This is
version-header comparison only. As of the 149O.20D.1 repair, `HBDC-001`
additionally receives the HMIC-REQ-053 content-digest binding, closing
the same-version content-drift residual limitation this section
previously left for `HBDC-001` specifically — see HMIC-REQ-145
(repaired) and §52. As of the 149O.20L.7O.2H amendment, `HPSE-001` and
`HHCE-001` join `contract_versions` already content-digest-bound from
the moment of admission — never as a deferred, disclosed exception — see
§59.

**HMIC-REQ-070.** If a future contract-freeze phase judges the HMIC-
REQ-068 exclusion wrong, it MAY widen `contract_versions` further in a
new contract version. This contract does not overbind irrelevant files
by default.

**HMIC-REQ-145 (Repaired 149O.20D.1 — HBDC-001 Content-Identity Binding;
formerly "HBDC-001 Binding Residual Limitation, Named Not Hidden," added
v1.2).** `HBDC-001`'s `contract_versions` binding (HMIC-REQ-067) was, as
originally added at v1.2 (149O.20D, §51), a version-header comparison
only — identical in mechanism to `HMRC-001`/`HATP-001`/`HSCE-001`/
`RAE-001`'s own `contract_versions` binding, but *unlike* those four,
`HBDC-001`'s document bytes did **not** additionally participate in
`implementation_scope_digest`. This left a disclosed gap, recorded as
finding **B-149O.20D-1**: a revision of `HBDC-001` to a new version
string was caught (HMIC-REQ-069, `CONTRACT_MISMATCH`), but a `HBDC-001`
content edit made *without* a version bump (same-version byte drift) was
**not** caught by the `contract_versions` mechanism alone, because that
mechanism, by design, compares version headers, not content digests.

**Repair (this section, as of 149O.20D.1, §52).** `HBDC-001`'s document,
`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`, is now the
twenty-fifth entry in HMIC-REQ-050's frozen file enumeration and
therefore participates in `implementation_scope_digest` exactly as
`HMRC-001`/`HATP-001`/`HSCE-001`/`RAE-001`'s documents already do
(HMIC-REQ-053, now stated uniformly for all five `contract_versions`
members). Consequence: `HBDC-001` now receives the *identical* dual
binding as the other four bound contracts —
`contract_versions`' version-header comparison (HMIC-REQ-067/069) **and**
`implementation_scope_digest`'s content-digest inclusion (HMIC-REQ-050/
053-058). A same-version, content-only `HBDC-001` byte edit now changes
`implementation_scope_digest`, which HMIC-REQ-058's two-level SHA-256
construction makes overwhelmingly unlikely to coincide with the
pre-edit digest; a mismatch at §31 step 9 yields `IMPLEMENTATION_
MISMATCH`, invalidating any certification bound to the pre-edit bytes.
A version-bumped `HBDC-001` revision remains additionally, redundantly
caught by `contract_versions`' own version-header comparison
(HMIC-REQ-069, `CONTRACT_MISMATCH`) — both mechanisms now apply to
`HBDC-001`, exactly as HMIC-REQ-053 already requires of the other four
bound contracts ("no future implementation SHALL treat either mechanism
as sufficient without the other").

**Status: CLOSED.** B-149O.20D-1 is repaired at the contract level.
This closure does not depend on repository actors honestly bumping
`HBDC-001`'s version string — content bytes, not merely a declared
version, now determine certification-visible identity, mirroring the
protection the other four bound contracts already had from the moment
they joined `contract_versions`. *(Status corrected 149O.20L.7L.3,
finding F-7L-5; see §57.9.)* This closure's own mechanical-enforcement
status is **now mechanically enforced in production**: `core/hatp_
mandatory_certification.py`'s own `_FROZEN_AUTHORITY_BEARING_FILES`
constant has been realigned past the pre-repair twenty-four-file set
named here — production now implements the current live thirty-file
set, mechanically enforced since Phase 149O.20L.7K (§55) — superseding
this paragraph's original "not yet mechanically enforced" framing and
its cross-reference to attacks #33/#34/#36's now-corrected caveats
(§41, §57.3-§57.5). This repair does not, and does not claim to, solve
HMIC-REQ-063's own executed-code/import-shadowing residual limitation,
which remains separately named, unchanged, and unsolved by this
section.

---

## 21. Verification Record Reference (Evidentiary Only)

**HMIC-REQ-071.** `verification_record_digest` (§11) is a digest of the
canonical phase-report artifact (e.g. the 149O.19-class independent-
verification phase report) this certification attests to. It is
audit/traceability metadata only.

**HMIC-REQ-072.** `verification_record_digest`, and any phase/report
identifier stored alongside it, SHALL NEVER themselves be sufficient,
partially sufficient, or a fallback path to a `VALID` validation
outcome. Validation (§33) never inspects the referenced report's
content — it is recorded for human audit, never re-parsed as an
authority input.

**HMIC-REQ-073.** A phase ID, standing alone, MAY be stored as
descriptive metadata. It is never, by itself, a validity condition.

---

## 22. Non-Authoritative Repo-Local Signals (Closed Prohibition List)

**HMIC-REQ-074.** None of the following SHALL ever be consulted,
directly or indirectly, by the validation algorithm (§33) as a
sufficient or contributing condition for a `VALID` outcome:
`PROJECT_STATUS.md`; `tasks/TODO.md`; `CHANGELOG.md`; any phase-report
document under `docs/`; `.pcae/phase-completion-metadata.json`;
`.pcae/phase-completion-report.md`; `tasks/DONE.md`; test results of any
kind; a git commit message string (as opposed to the commit SHA
identity term, HMIC-REQ-046, which is an identity component only, not
authority); any environment variable; any CLI-supplied boolean flag.

**HMIC-REQ-075.** No future implementation SHALL replace the current
hard-coded `False` readiness-ceiling constant with a hard-coded `True`
constant as a stand-in for certification. Future readiness for this
term SHALL derive exclusively from a fresh, dynamic call to the
certification validator (§35).

---

## 23. Creation Ceremony

**HMIC-REQ-076.** Certification creation proceeds exactly:

```
1. A 149O.19-class independent-verification phase completes
   (agent-authored, evidentiary only — never itself authority, §22).
2. Protected Admin Authority reviews the canonical phase report
   out of band (human judgment; not this contract's concern).
3. Protected Admin Authority invokes a separate, non-agent-writable
   admin tool (§26) — never the ordinary `pcae` CLI surface an agent
   process can reach.
4. The tool itself — never the human, never the agent — computes:
   repository_instance_id (read-only, §15), canonical_deployment_root
   (read-only, §15), implementation_commit (read-only, §16),
   implementation_scope_digest (read-only, §18), contract_versions
   (read-only, by reading each of the exact seven bound contracts'
   own live version headers, §20), certified_at (read-only, wall-clock
   at invocation).
5. The tool presents this computed tuple to the human for confirmation
   (a target, not a blank form) together with the verification
   record's digest (§21).
6. On confirmation, the tool derives certification_id (§13) and
   atomically appends a new, immutable CertificationRecord to
   certifications.json (§27) under the certification-transition lock
   (§32).
7. Making the new record active (§28) is a distinct, explicit step —
   the tool does not do this automatically unless the human separately
   confirms "activate this as current."
```

**HMIC-REQ-077 (Minimized Human-Entered Authority-Sensitive Input).**
The human never types a repository ID, digest, commit SHA, or a
"verified=True" boolean. The only human-entered fields are confirmation
of a tool-derived target and `certified_by` (the human's own identity
string). Every authority-sensitive field is tool-re-derived, never
accepted as free-form operator input.

**HMIC-REQ-078 (Certifier Input, Minimized).** Beyond confirmation and
`certified_by`, the only additional input the human MAY provide is an
explicit verification-record locator/reference (§21) if the tool cannot
derive it automatically. No user-entered implementation digest, commit
SHA, or repository/deployment identifier is ever accepted as authority.

---

## 24. Writer Surface and Agent Write Prohibition

**HMIC-REQ-079.** The certification writer (create/activate/revoke) is
a separate admin/deployment tool, not a subcommand of the ordinary
`pcae` CLI binary an agent process routinely invokes for everything
else. Putting certification-writing code in the same process image the
agent principal executes would put the real enforcement boundary at an
in-process check — exactly the "application-level authority-check
mechanism" this repository's own `hatp_mandatory_cutover.py` module
docstring already concludes does not, and should not, exist here. The
real enforcement boundary is OS file permissions on the Protected Root.

**HMIC-REQ-080 (Root Resolution, No Override).** The admin tool
resolves the Protected Root exactly as production code does
(`HATPTrustStore.production().root`). It does NOT accept a `--root`
override in its ordinary invocation mode, preserving the "no
caller-selectable trust root" property `HATPTrustStore.production()`
already guarantees. A test-only seam (§35) accepting an explicit root
exists structurally outside this production entrypoint, mirroring
`HATPTrustStore.__init__`'s own `_test_only_root` pattern exactly.

**HMIC-REQ-081 (Ordinary `pcae` CLI Prohibition).** The ordinary `pcae`
CLI MUST NOT expose any certification write or revoke operation under
agent authority — no `pcae certify`, `pcae revoke-certification`, or
equivalent subcommand on the agent-reachable binary. Read-only
certification inspection (e.g. "show current certification status for
this deployment") MAY be exposed later on the ordinary CLI, provided it
never implies "certification valid → rollback permitted" (§37).

**HMIC-REQ-082 (No Agent-Reachable Write API).** No production,
agent-reachable API exposes `create_certification()`,
`activate_certification()`, `revoke_certification()`,
`mark_independently_verified()`, `set_certified(True)`, or any
equivalently-named write capability. The only write path is the
separate admin tool (HMIC-REQ-079), itself gated by OS permissions, not
by an in-process check.

---

## 25. Storage Write Safety and Atomicity

**HMIC-REQ-083.** Every write (create, activate, revoke) to either
certification file SHALL use the same `mkstemp` + `fsync` +
`os.replace` atomic-write idiom every other protected-record writer in
this codebase already uses (`repository_identity.py::_write_atomic`,
`hatp_mandatory_cutover.py::_atomic_write_json`). No partially-written
document is ever observable by a concurrent reader.

**HMIC-REQ-084 (Create-Once for Immutable Records).** Appending a new
`CertificationRecord` to `certifications.json` SHALL be a create-once
publication: the write SHALL fail, not silently overwrite, if a record
with the same `certification_id` already exists with different
authority-sensitive field values (§32's concurrency rule governs the
identical-content case).

---

## 26. Active-Certification Binding — No Implicit Latest

**HMIC-REQ-085.** `certification-bindings.json` (§13) is the *only* way
a validator learns which certification, if any, is active for a given
`(repository_instance_id, canonical_deployment_root)` key. A validator
SHALL NEVER list `certifications.json`, sort by `certified_at`, and
select the newest, most-recent, first-found, or any other implicitly-
discovered entry. This is the same "implicit latest" anti-pattern
HSCE-001 already prohibits for evidence-ID selection (HSCE-REQ-014-class
rule) and HMRC-REQ-014 already prohibits for evidence lookup, extended
here identically.

**HMIC-REQ-086.** Creating a new `CertificationRecord` does NOT
automatically make it active. Activating it requires a second, explicit
admin write to `certification-bindings.json` (§23 step 7) — mirroring
HMRC-001 §15's own deliberate decoupling of `PREPARED` (readiness) from
`HATP_MANDATORY` (activation).

---

## 27. Supersession and Recertification

**HMIC-REQ-087.** Recertification creates a *new* `CertificationRecord`
(new `certification_id`, new `implementation_commit`/`implementation_
scope_digest` reflecting the changed implementation). The old record is
never mutated to reflect the new implementation — it remains unchanged
as historical evidence of what was certified and when.

**HMIC-REQ-088.** Making a new certification active requires a
*separate*, explicit admin write to `certification-bindings.json`
(HMIC-REQ-086). No automatic "latest certification becomes active"
behavior exists.

**HMIC-REQ-089.** Old-implementation replay (a stale `implementation_
scope_digest`, HMIC-REQ-049) and old-contract replay (a stale
`contract_versions` entry, HMIC-REQ-069) are both rejected purely by
§33's comparison-against-current-state validation steps — no special-
cased "is this superseded" flag exists or is needed.

**HMIC-REQ-090.** Even with multiple `CertificationRecord` entries
present for the same repository/deployment key, only the one named by
the Active-Certification Pointer's `active_certification_id` (§26) is
ever consulted by validation.

---

## 28. Revocation

**HMIC-REQ-091 (Mechanism — Field Mutation, Not Deletion).** Revocation
is performed by the same admin tool (§24) writing `status: "revoked"`
and `revoked_at: <timestamp>` onto the existing `CertificationRecord`
(HMIC-REQ-034's consistency rule applies). This is a field mutation on
an otherwise-immutable record, never a deletion — the record remains
present, auditable, and readable as historical evidence.

**HMIC-REQ-092 (Explicit ID Only).** Revocation SHALL name the exact
`certification_id` to revoke. No "revoke latest," "revoke active," or
any other implicit-selection revocation form SHALL exist.

**HMIC-REQ-093 (Protected-Admin-Only).** Revocation requires the same
Protected-Root write access creation requires (§7). No repo-local
revocation path exists.

**HMIC-REQ-094 (Revocation Effect on Readiness).** If the revoked
`certification_id` is the currently active-pointed certification,
validation SHALL yield `REVOKED` (§34), mapping the readiness fact to
`False`. If the revoked record is not the active one, revocation has no
readiness effect (§27's historical-record principle).

---

## 29. Post-Activation Certification Loss

**HMIC-REQ-095 (Never Downgrades Mode — Critical, HMRC-001-Consistent).**
If, after a deployment reaches `HATP_MANDATORY` (HMRC-001), its
certification later becomes invalid — revoked, corrupted, or the
implementation has drifted — this contract's validator SHALL NOT, and
structurally cannot, cause `HATP_MANDATORY → PREPARED` or
`HATP_MANDATORY → LEGACY_COMPATIBLE`. The Cutover Record's own
transition graph (HMRC-REQ-038/039) has no reverse edge; nothing in this
contract adds one.

**HMIC-REQ-096.** Post-activation, a revoked or otherwise invalid
certification MAY feed a separate, future operational-readiness/
diagnostic signal ("this deployment is `HATP_MANDATORY` but its
certification is currently invalid"). This contract does NOT implement
that diagnostic signal; it only guarantees this contract's own design
does not require or invite a mode downgrade to express revocation.

---

## 30. Concurrency and Locking

**HMIC-REQ-097 (Dedicated Lock).** Every write (create, activate,
revoke) to either certification file SHALL acquire an exclusive
`fcntl.flock` lock on a dedicated `.certification-transition.lock` file
under the Protected Root — mirroring `_write_cutover_transition`'s own
locking discipline, but a distinct lock file from the Cutover Record's
own `.cutover-transition.lock`, since the two concerns are independently
auditable (§9) and SHALL NOT serialize on each other unnecessarily.

**HMIC-REQ-098 (Creation Race — Deterministic).** Two concurrent
creation attempts for logically identical content serialize through the
lock; the second writer's precondition check (does this
`certification_id` already exist) observes the first writer's already-
committed state. No silent overwrite; the second writer either
no-ops (identical content) or fails (conflicting content, HMIC-REQ-084).

**HMIC-REQ-099 (Supersession Race — Deterministic).** Two certifications
racing to become active serialize through the same lock; whichever write
completes second is the one that determines the final active pointer,
observed deterministically, with no ambiguous or half-applied
intermediate state ever persisted (HMIC-REQ-083's atomicity applies to
each individual write; the lock orders the sequence of writes).

**HMIC-REQ-100 (Revocation Race — Fail-Safe Ordering).** A revoke
racing a concurrent recertify/activate serializes through the identical
lock; whichever completes second observes the other's already-written
state as its starting point. "Revoke old cert while a new cert is
simultaneously being activated" cannot produce an ambiguous or
half-applied result.

**HMIC-REQ-101 (Lock Ordering with Cutover Transition Lock).**
Certification validation, when invoked from inside HMRC-001's
activation-lock-held recheck (§36), performs a read-only certification-
file read; it SHALL NOT itself acquire the `.certification-
transition.lock` for a read-only validation pass, avoiding a lock-
ordering/deadlock hazard between the two independent lock files. Only
certification *writes* (create/activate/revoke) acquire `.
certification-transition.lock`, and no certification write is ever
performed from inside an `activate_hatp_mandatory` call — the two
ceremonies (§37) never nest their write locks.

**HMIC-REQ-102 (No Agent-Controlled Lock Path).** The lock file's path
is fixed under the Protected Root, exactly as `HATPTrustStore.
production().root` resolves it. No caller-suppliable lock-file path
exists.

---

## 31. Validation Algorithm

**HMIC-REQ-103.** The certification validation algorithm, executed
fresh on every invocation (§35), is exactly:

```
 1. resolve Protected Root              (HATPTrustStore.production().root)
 2. resolve repository_instance_id      (repository_identity.py, read-only)
 3. resolve canonical_deployment_root   (hatp_bootstrap.py, read-only)
 4. load certification-bindings.json    -> active_certification_id, or MISSING
 5. load certifications.json            -> CertificationRecord for that id,
                                            or MISSING
 6. strict-parse both documents          (closed schema, duplicate-key
                                            rejection, strict version/
                                            timestamp grammar)
                                            -> MALFORMED on any deviation
 7. validate repository_instance_id +
    canonical_deployment_root match      -> WRONG_REPOSITORY /
                                            WRONG_DEPLOYMENT
 8. validate status == "active"          -> REVOKED
 9. recompute implementation_commit +
    implementation_scope_digest fresh
    from the current working tree,
    compare against the record          -> IMPLEMENTATION_MISMATCH
10. validate contract_versions against
    the seven bound contracts' own
    current version headers             -> CONTRACT_MISMATCH
11. validate certification_id itself
    re-derives from the record's own
    fields (self-consistency)           -> MALFORMED
12. only if every step above passes     -> VALID
```

**HMIC-REQ-104.** Steps SHALL be evaluated in exactly this order. The
first failing step determines the returned Validation Status; no
implementation SHALL evaluate later steps once an earlier step fails, and
no implementation SHALL return a status not defined by the failing step.

**HMIC-REQ-105 (Root/File Access Failure).** If the Protected Root
itself is absent or unreadable (step 1), or a file access error occurs
at step 4/5 (e.g. a permissions error distinct from ordinary absence),
the result is `MISSING` if the cause is absence, or `ACCESS_ERROR`
(§34) if the cause is a genuine I/O error distinct from absence — both
map to the readiness fact `False`. No auto-provisioning of the
Protected Root or its files SHALL occur as a side effect of validation.

---

## 32. Validation Status Vocabulary and Readiness Mapping

**HMIC-REQ-106 (Closed Vocabulary).** The exact, closed Validation
Status vocabulary, matching §31's steps one-to-one, is:

```
MISSING | MALFORMED | WRONG_REPOSITORY | WRONG_DEPLOYMENT |
IMPLEMENTATION_MISMATCH | CONTRACT_MISMATCH | REVOKED | ACCESS_ERROR |
VALID
```

No future implementation SHALL introduce an additional status value
without amending this contract. An unrecognized/future status value
encountered by a consumer SHALL be treated as failure (mapped to
`False`), never as success-by-default.

**HMIC-REQ-107 (Readiness Mapping — Exactly One Success Status).**
`mandatory_consumption_implementation_independently_verified = True` if
and only if Validation Status is exactly `VALID`. Every other status in
HMIC-REQ-106's vocabulary maps to `False`. No `VALID_WITH_WARNING` or
other partial-credit status exists (HMIC-REQ-010, restated).

**HMIC-REQ-108 (No Partial Certification).** The Validation Status is
binary at the readiness boundary: `VALID` or not-`VALID`. Non-blocking
diagnostic detail (e.g. "certification is valid but will expire
soon" — no expiry mechanism exists in v1.0, this is illustrative only)
MAY be surfaced separately for human inspection, but SHALL NEVER
substitute for, or be conflated with, the binary Validation Status
itself.

---

## 33. Validation API and Freshness

**HMIC-REQ-109 (Conceptual Production API).** A future implementation's
production validation entrypoint is conceptually
`validate_active_hatp_mandatory_independent_verification_certification
(repository_root: Path) -> <typed validation result with Validation
Status>`. `repository_root` (or an equivalent repository locator) MAY be
caller-supplied as a neutral locator; `repository_instance_id` is still
independently derived from it and cross-checked (§31 step 7) — the
caller never supplies `repository_instance_id` itself.

**HMIC-REQ-110 (No Caller-Suppliable Authority Input).** The validator
SHALL NOT accept, from any production caller: `implementation_digest=`,
a pre-computed `implementation_commit=`, a pre-computed `contract_
versions=`, or any other authority-bearing value as a parameter. Every
authority-sensitive value is derived fresh, internally, by the
validator itself (HMIC-REQ-045, restated).

**HMIC-REQ-111 (Production Root Resolution — Closed).** The production
validation entrypoint resolves `HATPTrustStore.production().root`
internally. It does NOT accept a caller-suppliable root override.

**HMIC-REQ-112 (Test Seam).** A future implementation's validator and
writer each MAY expose an internal, non-production-reachable function
accepting an explicit `protected_root: Path`, used only by tests
constructing isolated fixture roots — mirroring `HATPTrustStore.
__init__`'s own `_test_only_root` pattern and `_assess_hatp_mandatory_
activation_readiness_at_root`'s explicit `protected_root` parameter
exactly. Production entrypoints never accept this parameter.

**HMIC-REQ-113 (No Validity Cache).** Every readiness assessment and
every activation attempt re-runs §31 in full. No process-long, in-
memory, or any-other cache of Validation Status or the readiness fact
is permitted — identical discipline to HMRC-REQ-052's "no cached
Consumption Mode" rule, extended here.

---

## 34. Activation-Readiness Integration and Locked Recheck

**HMIC-REQ-114.** A future implementation replaces the current literal
`False` constant at `hatp_mandatory_cutover.py:842-853` with a call to
the validation entrypoint (§33), mapped per HMIC-REQ-107. The literal
`False` constant SHALL be removed only when the certification validator
described by this contract exists and is wired to this exact call site
— no intermediate hard-coded `True` constant, and no other stand-in,
SHALL ever be substituted (HMIC-REQ-075, restated).

**HMIC-REQ-115 (Locked Recheck Inside Activation).** `activate_hatp_
mandatory` SHALL run the full readiness conjunction — including this
term — under the existing `_write_cutover_transition` transition lock,
via its existing `readiness_check` hook (`hatp_mandatory_
cutover.py:669-681`), exactly mirroring how every other readiness term
is already rechecked fresh immediately before the Cutover Record write.
No new lock, no new hook signature, no new race window is introduced.

**HMIC-REQ-116 (Earlier Assessment Non-Authoritative).** An earlier,
advisory call to `assess_hatp_mandatory_activation_readiness()` that
returns `ready=True` does not mint a token, capability, or any other
carry-forward authority. A subsequent `activate_hatp_mandatory()` call
recomputes this term (and every other term) fresh, under the lock.

**HMIC-REQ-117 (Consequences of Freshness — Frozen).** If certification
is revoked, or the working tree is modified in a way that changes
`implementation_scope_digest`, between an earlier advisory readiness
call and a later locked activation attempt, the fresh recheck observes
the new state and refuses. If the certification-bindings.json pointer
changes between the two calls, the fresh recheck sees the current
explicit pointer, not a stale one.

---

## 35. Certification/Activation Independence (Explicit Non-Causation)

**HMIC-REQ-118.** `CERTIFY` (§23) and `ACTIVATE` (HMRC-001's
`activate_hatp_mandatory`, unchanged by this contract) are, and MUST
remain, separate ceremonies performed by the same principal (§7) but
never combined into one action.

**HMIC-REQ-119.** A Protected Admin Authority MAY certify an
implementation and explicitly choose not to activate `HATP_MANDATORY`
(e.g. certifying well ahead of an intended cutover window).

**HMIC-REQ-120 (Certification Does Not Activate).** A `VALID`
certification satisfies this contract's one readiness term. It does
NOT, by itself, cause `PREPARED → HATP_MANDATORY`; every other HMRC-
REQ-054 term must also independently hold, and activation remains the
separate, explicit `activate_hatp_mandatory` call.

**HMIC-REQ-121 (Activation Does Not Create Certification).** No code
path invoked by `activate_hatp_mandatory`, or by any activation-adjacent
production function, SHALL create, activate, or revoke a
`CertificationRecord` or Active-Certification Pointer as a side effect.

**HMIC-REQ-122 (Certification Does Not Evaluate PB).** No certification
creation, validation, activation-pointer write, or revocation
operation SHALL construct or evaluate a Permission Broker request.

**HMIC-REQ-123 (Certification Does Not Set Approval).** No certification
operation SHALL write, derive, or influence `rollback_approval_state`,
HATP rollback approval, or any RAE-001 Decision/Binding artifact.

**HMIC-REQ-124 (Certification Does Not Create Capability).** No
certification operation SHALL create, grant, or influence any runtime
execution capability, `COMP-002`, or `COMP-008`.

**HMIC-REQ-125 (`POL-005`/`COMP-002` Unaffected).** This contract does
not amend, trigger, or interact with `POL-005` or `COMP-002`. A valid
certification does not change whether a real AG3/AG5 effect request
resolves `ALLOW`/`DENY`/`HUMAN_REVIEW` under current PB policy — that
remains entirely HMRC-001/PBPA-001/PBPC-001's domain (HMRC-REQ-055's
own cross-contract statement, restated here for HMIC-001's own
avoidance of doubt).

**HMIC-REQ-126 (Bootstrap Circularity Forbidden).** No future
implementation SHALL require an already-activated `HATP_MANDATORY`
deployment as a precondition to create the certification needed to
reach `HATP_MANDATORY` in the first place. Certification authority
exists independently of, and prior to, any `HATP_MANDATORY` activation
— it is never derived from an already-activated state.

**HMIC-REQ-127 (No AG3/AG5 Execution Dependency).** The certification
ceremony (§23) does not require, invoke, or depend on any real or
simulated AG3/AG5 rollback execution. Certification concerns
independent verification of the *implementation*, not a live rollback
demonstration.

---

## 36. Path Safety and Certification-ID Validation

**HMIC-REQ-128 (Symlink Rejection — Root, Parent, Certification Files,
Pointer File).** The Protected Root itself, every parent directory
component, `certifications.json`, and `certification-bindings.json`
SHALL each be rejected if any is a symlink, per the existing Class-B
safe-path discipline (HMIC-REQ-061, applied identically to the
certification/pointer files themselves, not merely to frozen
implementation files).

**HMIC-REQ-129 (No Path Traversal via `certification_id`).**
`certification_id` (a SHA-256 hex digest, HMIC-REQ-038) SHALL never be
used to construct a filesystem path directly. Because both certification
files are single shared files (§9), no per-certification filesystem
path is ever derived from `certification_id` in v1.0 — this
structurally eliminates path-traversal risk from this field, rather
than merely validating it defensively. If a future version ever derives
a path component from `certification_id`, that version SHALL enforce:
no `/`, no `\`, no `..`, and no filesystem-normalization of
attacker-influenced input, mirroring HSCE-REQ-056's evidence-ID
discipline exactly.

---

## 37. Audit Metadata and Reporting Semantics

**HMIC-REQ-130.** `certified_at` and `certified_by` are informational/
audit metadata. Neither independently establishes validity; both are
inputs to the `certification_id` digest (HMIC-REQ-038) for tamper-
detection purposes only, not standalone authority signals.

**HMIC-REQ-131 (`certified_by` Is Not Cryptographic Proof).**
`certified_by` is a caller-supplied identity string with no default. If
stored, it is audit metadata, not proof of identity — no username
string, by itself, is proof of Protected Admin Authority (HMIC-REQ-020,
restated). Real authority derives solely from the Protected-Root
OS-permission boundary.

**HMIC-REQ-132 (Inspection Output Wording).** Any future read-only
inspection/reporting surface (HMIC-REQ-081) that displays certification
status SHALL NOT phrase its output such that "certification valid"
reads as "rollback permitted," "activation occurred," or "execution
capability exists" (§5). Inspection output is descriptive of
certification state only.

**HMIC-REQ-133 (No Secret Material).** A `CertificationRecord` SHALL
contain no private key material, PINs, or credential secrets. It
contains only identity/digest/timestamp/reference fields (§11).

---

## 38. Cross-Contract Relationship and Non-Redefinition

**HMIC-REQ-134.** HMIC-001 owns the independent-verification
certification described in §2. HMRC-001 continues to own mandatory
rollback consumption/cutover activation, unmodified. HATP-001 continues
to own proof provenance, unmodified. RAE-001 continues to own rollback
approval evidence, unmodified. PBPA-001/PBPC-001 continue to own
Permission Broker policy, unmodified. No contract's ownership is
redefined by this contract.

**HMIC-REQ-135 (Readiness-Fact Ownership).** HMIC-001's validator
supplies exactly one input fact —
`mandatory_consumption_implementation_independently_verified` — to
HMRC-001's six-item readiness conjunction. It does not own, and SHALL
NOT be wired to influence, any of the other five terms.

**HMIC-REQ-136 (No Activation-Contract Redefinition).** HMIC-001 does
not change the `LEGACY_COMPATIBLE` / `PREPARED` / `HATP_MANDATORY`
transition semantics, the Cutover Record schema, or any HMRC-001
requirement.

**HMIC-REQ-137 (No PB-Contract Redefinition).** HMIC-001 makes no
change to PBPA-001 or PBPC-001, their decision vocabulary, or their
policy rules.

**HMIC-REQ-138 (No General-Deployment-Certification Overreach).** This
contract's scope is narrowly the HMRC-001 mandatory-consumption
independent-verification certification (§2, §5). It does not
accidentally establish a universal PCAE software-release/deployment
signing mechanism; a future, separate, explicitly-scoped contract would
be required for that.

---

## 39. Requirement Inventory — Category Index

| Category | Requirements |
|---|---|
| Purpose / scope / relationship | HMIC-REQ-001 – 006 |
| Terminology / semantic walls | HMIC-REQ-007 – 010 |
| Threat model | HMIC-REQ-011 – 015 |
| Authority principal / write / read authority | HMIC-REQ-016 – 020 |
| Protected root | HMIC-REQ-021 – 023 |
| Storage topology / multi-repo keying | HMIC-REQ-024 – 027 |
| Portability / signature / hardware touch | HMIC-REQ-028 – 030 |
| `CertificationRecord` schema | HMIC-REQ-031 – 035 |
| `CertificationBinding` schema | HMIC-REQ-036 – 037 |
| Certification-ID derivation | HMIC-REQ-038 – 040 |
| Canonical serialization | HMIC-REQ-041 – 042 |
| Repository / deployment binding | HMIC-REQ-043 – 045 |
| Implementation identity — commit | HMIC-REQ-046 – 049 |
| Implementation identity — frozen file set | HMIC-REQ-050 – 053 |
| Implementation identity — digest/canonicalization | HMIC-REQ-054 – 062 |
| Implementation identity — residual limitations | HMIC-REQ-063 – 066 |
| Contract binding set | HMIC-REQ-067 – 070, HMIC-REQ-145 (added v1.2) |
| Verification-record reference | HMIC-REQ-071 – 073 |
| Non-authoritative repo-local signals | HMIC-REQ-074 – 075 |
| Creation ceremony | HMIC-REQ-076 – 078 |
| Writer surface / agent-write prohibition | HMIC-REQ-079 – 082 |
| Storage write safety | HMIC-REQ-083 – 084 |
| Active-certification binding / no implicit latest | HMIC-REQ-085 – 086 |
| Supersession | HMIC-REQ-087 – 090 |
| Revocation | HMIC-REQ-091 – 094 |
| Post-activation certification loss | HMIC-REQ-095 – 096 |
| Concurrency / locking | HMIC-REQ-097 – 102 |
| Validation algorithm | HMIC-REQ-103 – 105 |
| Validation vocabulary / readiness mapping | HMIC-REQ-106 – 108 |
| Validation API / freshness | HMIC-REQ-109 – 113 |
| Activation-readiness integration | HMIC-REQ-114 – 117 |
| Certification/activation independence | HMIC-REQ-118 – 127 |
| Path safety / certification-ID validation | HMIC-REQ-128 – 129 |
| Audit metadata / reporting semantics | HMIC-REQ-130 – 133 |
| Cross-contract relationship | HMIC-REQ-134 – 138 |
| Versioning | HMIC-REQ-139 – 140 |
| Implementation readiness | HMIC-REQ-141 |
| B-149O-1..4 closure criteria | HMIC-REQ-142 |

---

## 40. Security Invariants (CIVC-1 .. CIVC-12)

- **CIVC-1.** Repository-local metadata — `PROJECT_STATUS.md`,
  `tasks/TODO.md`, `CHANGELOG.md`, any phase report, any test result, any
  commit message string — is non-authoritative for certification
  validity (§22).
- **CIVC-2.** Only the Protected Admin Authority may create, activate,
  or revoke a certification; no agent-reachable production API exists
  to do any of the three (§7, §24).
- **CIVC-3.** A certification is valid only for the exact
  `repository_instance_id` + `canonical_deployment_root` pair it names
  (§15, §31 step 7).
- **CIVC-4.** A certification is valid only for the exact implementation
  — `implementation_commit` and `implementation_scope_digest` both — it
  names; any drift in either invalidates it (§16-19, §31 step 9). As of
  v1.1, "the implementation" bound by `implementation_scope_digest`
  includes this contract's own certification-parsing, identity-
  derivation, storage, active-binding, revocation, and validation-outcome
  implementation (`core/hatp_mandatory_certification.py`) and its sole
  intended Protected Admin ceremony caller
  (`scripts/hatp_certification_admin.py`), once production identity
  derivation is aligned to the v1.1 frozen set (§17 HMIC-REQ-050, §50) —
  drift in either therefore invalidates a certification exactly as drift
  in any other frozen file does, with no special-cased exemption for the
  code that itself decides `VALID`/non-`VALID` or writes protected
  certification state.
- **CIVC-5.** A certification is valid only while its `contract_
  versions` match the current, live version headers of the bound
  contracts (§20, §31 step 10) — four contracts (`HMRC-001`, `HATP-001`,
  `HSCE-001`, `RAE-001`) under v1.0/v1.1, five (adding `HBDC-001`) under
  v1.2 (HMIC-REQ-067, §51), seven (adding `HPSE-001`/`HHCE-001`) under
  v1.5 (HMIC-REQ-067, §59). A required `contract_versions` key absent
  from a stored record fails closed as `MALFORMED` under HMIC-REQ-031's
  pre-existing closed-schema discipline — no new mechanism was needed to
  reject a stored record produced under an earlier, narrower
  scope. **As of the 149O.20D.1 repair (§52, HMIC-REQ-053/145), and
  again as of the 149O.20L.7O.2H amendment (§59), all seven
  `contract_versions` members' document bytes additionally participate
  in `implementation_scope_digest` uniformly** — a same-version,
  content-only edit to any of the seven bound contracts, including
  `HBDC-001`/`HPSE-001`/`HHCE-001`, is caught by CIVC-4's digest-drift
  invariant, not merely by this invariant's version-header comparison;
  the two invariants are deliberately redundant for all seven, not only
  the original four.
- **CIVC-6.** Exactly one certification per repository/deployment key is
  ever authoritative — the one named by the Active-Certification
  Pointer's explicit `active_certification_id`; no implicit-latest
  selection exists anywhere (§26).
- **CIVC-7.** Every readiness/activation evaluation revalidates fresh;
  no cached Validation Status or readiness fact persists across calls
  (§33, §34).
- **CIVC-8.** Any non-`VALID` Validation Status fails closed to
  readiness `False`, with no partial-credit outcome (§32).
- **CIVC-9.** A `VALID` certification is necessary but never sufficient
  for activation, PB `ALLOW`, runtime capability, or execution, and
  never automatically causes any of them (§5, §35).
- **CIVC-10.** No source constant, environment variable, or caller-
  supplied boolean may substitute for a validated certification (§22,
  §33).
- **CIVC-11.** Revocation after `HATP_MANDATORY` activation never
  downgrades Consumption Mode (§29).
- **CIVC-12.** The Agent OS principal cannot self-certify: certification
  authority is structurally independent of, and never derived from, any
  agent-authored artifact, agent-writable state, or agent-reachable API
  (§7, §22, §24).

---

## 41. Full Mandatory Attack Matrix (43 Scenarios)

| # | Attack | Expected Result (frozen) |
|---|---|---|
| 1 | Fake `PROJECT_STATUS.md` completion entry | No effect — repository status is non-authoritative, CIVC-1/HMIC-REQ-074 |
| 2 | Fake/forged phase-report document | No effect — phase reports are non-authoritative, CIVC-1/HMIC-REQ-074 |
| 3 | Fake or fabricated passing test-suite output | No effect — test results are non-authoritative, CIVC-1/HMIC-REQ-074 |
| 4 | Source edit replacing the hard-coded `False` ceiling with `True` | Forbidden by this contract (HMIC-REQ-075); this contract does not implement the ceiling, but no future implementation may treat this as certification |
| 5 | Environment variable asserting "verified" | Structurally impossible — no such input exists, HMIC-REQ-020/074 |
| 6 | CLI boolean flag asserting "verified" | Structurally impossible — no such input exists, HMIC-REQ-020/081 |
| 7 | Repo-local fabricated certification-shaped JSON placed under `.pcae/` | No effect — certification only lives under the Protected Root, never `.pcae/`, HMIC-REQ-022 |
| 8 | Wrong-repository certification (copied from repo A's protected root into repo B's) | Rejected — `WRONG_REPOSITORY`, §31 step 7 |
| 9 | Wrong-deployment certification (same repository, different `canonical_deployment_root`) | Rejected — `WRONG_DEPLOYMENT`, §31 step 7 |
| 10 | Old-implementation replay (valid certification for implementation X presented for modified implementation Y) | Rejected — `IMPLEMENTATION_MISMATCH`, §31 step 9, highest-priority property |
| 11 | Dirty frozen file (working-tree edit to a HMIC-REQ-050 file after certification) — including a hardware-provider implementation file such as `hatp_fido2_provider.py`/`hatp_piv_provider.py`/`hatp_providers.py`/`hatp_hardware_credentials.py` (e.g. an edit making `Fido2HardwareProvider.verify()` unconditionally return `signature_valid=True`); repaired by Phase 149O.19.3R (B-149O.19.3-1) to bring these four files inside the frozen set — see §49; **or, as of v1.1, an edit to the certification/validation implementation itself, `core/hatp_mandatory_certification.py`, that would make `_validate_at_root` unconditionally return `VALID`, or an edit to the Protected Admin ceremony script, `scripts/hatp_certification_admin.py`, that would make `certify`/`activate`/`revoke` write a self-consistent but misleading record — bound by Phase 149O.19.5E.1 (W-1) to bring these two files inside the frozen set, once production identity derivation is realigned to the v1.1 set — see §50** | Rejected — `IMPLEMENTATION_MISMATCH`, HMIC-REQ-049 |
| 12 | Commit changed, frozen-file bytes unchanged | Rejected — `IMPLEMENTATION_MISMATCH`, HMIC-REQ-048 (both identity terms required) |
| 13 | Commit unchanged, frozen-file bytes changed (dirty tree) | Rejected — `IMPLEMENTATION_MISMATCH`, HMIC-REQ-049 |
| 14 | Contract-version replay (a bound contract revised; stale certification re-applied) | Rejected — `CONTRACT_MISMATCH`, §31 step 10, HMIC-REQ-069 |
| 15 | Missing certification (no record for the active pointer's ID) | `MISSING` → readiness `False`, §31 step 4-5 |
| 16 | Corrupt certification record (malformed JSON, unknown field) | `MALFORMED` → readiness `False`, §31 step 6 |
| 17 | Duplicate JSON keys in the certification/pointer file | `MALFORMED` → readiness `False`, §31 step 6 |
| 18 | Unknown/future schema version | Fails closed — `MALFORMED`/unsupported version, §31 step 6, HMIC-REQ-031 |
| 19 | Symlinked certification file, pointer file, or Protected Root/parent | Rejected — HMIC-REQ-128 |
| 20 | Missing Active-Certification Pointer entirely | `MISSING` → readiness `False`, §31 step 4 |
| 21 | Corrupt Active-Certification Pointer file | `MALFORMED` → readiness `False`, §31 step 6 |
| 22 | Implicit-latest attempt (validator sorts `certifications.json` by `certified_at` and selects newest) | Structurally impossible — production validator only ever consults the explicit pointer, HMIC-REQ-085 |
| 23 | Revoked active certification | `REVOKED` → readiness `False`, §31 step 8 |
| 24 | Certification deleted after an earlier successful advisory readiness check, retried before activation | Fresh recheck observes `MISSING`, fails — HMIC-REQ-113/117 |
| 25 | Certification superseded (pointer repointed to a different record) between an earlier check and a later activation attempt | Fresh recheck observes the current explicit pointer deterministically — HMIC-REQ-117 |
| 26 | Concurrent revoke and activate/create race | Deterministic via `.certification-transition.lock` ordering, never half-applied — HMIC-REQ-097-100 |
| 27 | Agent attempts to call a certification writer/writer API directly | No such production-reachable API exists — HMIC-REQ-082 |
| 28 | Attacker-controlled alternate root injection (attempt to point validation at a non-production root) | Production validator always resolves `HATPTrustStore.production().root` internally, never a caller override — HMIC-REQ-111 |
| 29 | Imported module resolves outside the certified repository/source root (import-shadowing / `sitecustomize` / `PYTHONPATH` injection) | Named residual limitation, not solved by `implementation_scope_digest` alone in v1.0 — explicitly out of scope, not silently claimed solved — HMIC-REQ-063 |
| 30 | Certification files copied between two different Protected Roots/deployments | Rejected via repository/deployment binding, identical to #8/#9 — reinforced as a portability rejection, HMIC-REQ-028 |
| 31 | Stale readiness token reuse (an earlier advisory `ready=True` result presented at a later activation attempt without a fresh recheck) | Rejected — activation always recomputes under the transition lock; no token is ever minted, carried, or accepted, HMIC-REQ-116 |
| 32 | Certification creation automatically activates itself, or activation automatically creates a certification | Structurally impossible — `CERTIFY` and `ACTIVATE` are separate ceremonies with no code path coupling them, HMIC-REQ-118-121 |
| 33 *(added v1.1, §50)* | v1.0-scope replay: a hypothetical certification whose `implementation_scope_digest` was computed over the pre-v1.1 twenty-two-file set is presented for validation today | Rejected — `IMPLEMENTATION_MISMATCH`: a twenty-two-file digest cannot equal the live thirty-file digest under HMIC-REQ-054/058's two-level construction over a different input file list; no compatibility/grandfathering mode exists (HMIC-REQ-050's "no more, no fewer" enumeration has no version-conditional branch). *(Status corrected 149O.20L.7L.3, finding F-7L-5; see §57.3.)* **Operative, not yet consequential**: production identity derivation has since been realigned past the v1.1 twenty-four-file set this row originally named, mechanically enforced at the full live thirty-file set since Phase 149O.20L.7K — this row's original "production still computes the twenty-two-file digest" caveat is superseded and no longer accurate. The digest-comparison mechanism now runs on every fresh validation (§57.2), but no stored certification exists anywhere on this host for any file count to be compared against (§61), so no live readiness decision currently turns on this particular rejection; see attack #34 |
| 34 *(added v1.1, §50)* | File-set downgrade: a caller (or unaligned production code) computes `implementation_scope_digest` over fewer files than this contract's current enumeration | Not a certification bypass: this contract defines exactly one canonical enumeration at a time (HMIC-REQ-050/051), with no caller-suppliable `version=1.0`/`legacy_scope`/`file_count=22` override of any kind (HMIC-REQ-051 — the enumeration is embedded in this contract, not an agent-editable external manifest). *(Status corrected 149O.20L.7L.3, finding F-7L-5; see §57.4.)* This row's original premise no longer holds: production `_FROZEN_AUTHORITY_BEARING_FILES` has been realigned to this contract's own current thirty-file enumeration since Phase 149O.20L.7K — there is no live "still-unaligned production" file-set today. The row's two supporting claims were independently found false and are corrected: (1) the hard-coded `mandatory_consumption_implementation_independently_verified = False` ceiling this row cited no longer exists — Phase 149O.19.5F (Wave F) replaced it with a dynamic call to the certification validator, as this contract's own §51 (149O.20D) already recorded; and (2) that validator is not uncalled — it has exactly one production readiness/cutover caller, `hatp_mandatory_cutover.py`'s `_assess_hatp_mandatory_activation_readiness_at_root` (wired at 149O.19.5F, re-invoked lock-held immediately before activation), not "zero readiness/cutover callers." Despite both corrections, the row's bottom-line conclusion is unchanged for an independent reason: no stored certification exists anywhere on this host (§61), so the validator's fresh call always resolves to `MISSING` regardless of file count or ceiling wording — no functional readiness decision currently turns on which file count a caller computes over |
| 35 *(added v1.2, §51; revised 149O.20D.1, §52)* | HBDC semantic-drift-after-certification: a hypothetical certification is created while `HBDC-001` reads v1.0 with byte content A; `HBDC-001` is later revised to a new version, or replaced/removed, while the certification remains the active pointer | Rejected — `CONTRACT_MISMATCH` (revised-version case, via HMIC-REQ-069's five-member `contract_versions` comparison) or the general HMIC-REQ-059/062-class missing/unsafe-file failure (removed/replaced/unsafe case, via `implementation_scope_digest`, as of the 149O.20D.1 repair). Same-version content-only drift is **no longer** a disclosed exception — see attack #37 |
| 36 *(added v1.2, §51)* | Legacy four-contract certification replay: a hypothetical certification whose `contract_versions` was derived under pre-v1.2 (four-member: `HMRC-001`/`HATP-001`/`HSCE-001`/`RAE-001`) semantics is presented for validation today | Rejected — `MALFORMED`: the stored record's `contract_versions` mapping lacks the now-required `HBDC-001` key, which HMIC-REQ-031's pre-existing closed-schema discipline (missing required key) already rejects; no new mechanism, no caller-suppliable `legacy_contract_set=True`/`bound_contract_count=4`/`ignore_hbdc=True` override exists or is introduced (HMIC-REQ-067 restated, no exception clause). *(Status corrected 149O.20L.7L.3, finding F-7L-5; see §57.5.)* **Operative, not yet consequential**: production `_CONTRACT_IDENTITY_FILES` has been realigned to the current five-member `contract_versions` set since Phase 149O.20L.7K — this row's original "production still computes the four-member set" caveat is superseded and no longer accurate. The comparison mechanism now runs on every fresh validation (§57.2), but no stored certification exists anywhere on this host for either member count to be compared against (§61), so no live readiness decision currently turns on this particular rejection; mirrors attack #33's corrected caveat |
| 37 *(added 149O.20D.1, §52; finding B-149O.20D-1)* | HBDC-001 same-version content drift: `HBDC-001` still declares Contract ID `HBDC-001`, Version `v1.1`, but its normative document bytes are edited (e.g. an environment-lock requirement quietly loosened, an attack-matrix row weakened) without any version-header bump, while a certification created against the pre-edit bytes remains the active pointer | Rejected — `IMPLEMENTATION_MISMATCH`, via `implementation_scope_digest` (HMIC-REQ-050's twenty-fifth entry, `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`, HMIC-REQ-053/058, §31 step 9), the identical mechanism attack #11/#13 already describe for the other twenty-four frozen files, now extended to `HBDC-001`'s own document bytes; this is what closes B-149O.20D-1 (§52), superseding the same-version exception attack #35 previously disclosed. *(Status corrected 149O.20L.7L.3, finding F-7L-5; see §57.6.)* **Operative, not yet consequential**: production identity derivation has since been realigned to the full live thirty-file set (which includes `HBDC-001`'s own bytes) since Phase 149O.20L.7K — this row's original "production still computes the twenty-four-file digest" caveat is superseded and no longer accurate. The digest-comparison mechanism now runs on every fresh validation (§57.2), but no stored certification exists anywhere on this host for either file count to be compared against (§61), so no live readiness decision currently turns on this particular rejection |
| 38 *(added v1.3, §53)* | Class-B verifier byte modification while HMIC identity is unchanged: `hatp_class_b_topology_verifier.py`, `hatp_environment_lock_verifier.py`, or `hatp_class_b_conformance.py` is edited (e.g. an ACL right silently reclassified from dangerous to safe, an ancestor-chain check short-circuited, an aggregator branch flipped) such that `verify_class_b_deployment_conformance()` returns a materially different verdict, while a certification created before the edit remains the active pointer | Rejected — `IMPLEMENTATION_MISMATCH`, via `implementation_scope_digest` (HMIC-REQ-050's twenty-sixth through twenty-eighth entries, HMIC-REQ-052(c)/053-058, §31 step 9), the identical mechanism attacks #11/#13/#37 already describe for the other twenty-five frozen files, now extended under newly-added closure limb (c) to the three Class-B verifier files. *(Status corrected 149O.20L.7L.1, finding F-7L-1; see §56.1.)* **Operative and consequential in this repository's current state**: production identity derivation has since been realigned to HMIC-REQ-050's full thirty-file set (mechanically enforced since Phase 149O.20L.7K, superseding the twenty-eight-file threshold this caveat originally named), and `verify_class_b_deployment_conformance`'s result already has a real production consumer — `hatp_mandatory_cutover.py`'s mandatory activation-readiness assessment, wired by Phase 149O.20L.3 (predating even 149O.20L.7K's own phase entry) — not the HMIC-REQ-063 Option-C mechanism this caveat originally anticipated, which remains unbuilt and is a separate, still-hypothetical consumption path. This rejection is therefore both mechanically enforced and functionally load-bearing: an edit to any of the three Class-B verifier files, without a corresponding HMIC re-certification, would be rejected by a live readiness decision, not merely a contractually-mandated-but-inert one |
| 39 *(added v1.4, §55)* | `DeploymentBinding` producer/admin-script byte modification while HMIC identity is unchanged: `core/hatp_deployment_binding_admin.py` or `scripts/hatp_deployment_binding_admin.py` is edited (e.g. `create_deployment_binding`'s create-against-revoked fail-closed check is silently dropped, or `AuthorityEvidence` validation is weakened to accept an empty `principal_id`) such that an unauthorized or malformed `DeploymentBinding` can be durably written, which the already-frozen `hatp_bootstrap.py`/`repository_identity.py` read path then loads and `_check_deployment_identity` (`hatp_class_b_conformance.py`, itself frozen since v1.3) matches as `COMPLIANT`, while a certification created before the edit remains the active pointer | Rejected — `IMPLEMENTATION_MISMATCH`, via `implementation_scope_digest` (HMIC-REQ-050's twenty-ninth and thirtieth entries, HMIC-REQ-052(c)'s third anchor/053-058, §31 step 9), the identical mechanism attacks #11/#13/#37/#38 already describe for the other twenty-eight frozen files, now extended under limb (c)'s v1.4 widening to the DeploymentBinding producer and its admin-ceremony caller. **Not yet operative, and not yet consequential**: this phase (149O.20L.7K) realigns production identity derivation to the thirty-file set in the same phase as the contract amendment (unlike attacks #33/#34/#36/#37/#38's split contract-then-alignment sequencing), so the digest mechanism itself is mechanically enforced as of this phase — but the attack remains **not functionally load-bearing**, because (a) *(corrected 149O.20L.7L.1, finding F-7L-1; see §56.1)* the `DeploymentBinding` producer/admin-ceremony pair is bound to `implementation_scope_digest` under limb (c)'s third, non-reachability anchor precisely because it is a separate authority-bearing write path not transitively captured by `verify_class_b_deployment_conformance`'s own call graph (§55.1/§55.4) — not, as this clause previously and incorrectly stated, because the verifier itself has no production consumer: `verify_class_b_deployment_conformance` already has a real one, `hatp_mandatory_cutover.py`'s mandatory activation-readiness assessment, wired by Phase 149O.20L.3; this row's own conclusion never actually rested on the verifier's consumer status and is unaffected by the correction, resting instead on legs (b)/(c) below, (b) no real `DeploymentBinding` has ever been created on any host (§55 reconfirms zero live invocations, disposable-path-only testing) — so there is no live `DeploymentBinding` state yet for a compromised producer to have corrupted, even though the read path that would consume it is itself live — and (c) no HMIC certification exists to be invalidated by this or any other attack row in this matrix |
| 40 *(added v1.5, §59)* | Trust-Enrollment/signing authority-surface byte modification while HMIC identity is unchanged: `core/hatp_signing_ceremony.py`, `core/hatp_hardware_credential_admin.py`, or `core/hatp_principal_signer_admin.py` is edited (e.g. the signing ceremony's signer/provider consistency check is silently dropped, or a hardware-credential/principal writer's revocation check is weakened) such that an unauthorized signing operation succeeds or a compromised credential/principal/signer record is durably written, while a certification created before the edit remains the active pointer | Rejected — `IMPLEMENTATION_MISMATCH`, via `implementation_scope_digest` (HMIC-REQ-050's thirty-first through thirty-third entries, HMIC-REQ-052(d)/053-058, §31 step 9), the identical mechanism attacks #11/#13/#37/#38/#39 already describe for the other thirty frozen files, now extended under newly-added closure limb (d) to the Trust-Enrollment/signing authority surface. Mechanically enforced as of this phase: production identity derivation is realigned to the thirty-five-file set in the same phase as the contract amendment, per the 149O.20L.7K precedent (§59.16-§59.17). Not functionally load-bearing today, for the identical reason attack #39 remains not load-bearing: no HMIC certification exists on any host (§61) to be invalidated by this or any other attack row in this matrix |
| 41 *(added v1.5, §59)* | HPSE-001 same-version content drift: `HPSE-001` still declares Contract ID `HPSE-001`, Version `v1.1`, but its normative document bytes are edited (e.g. a lock-ordering requirement quietly loosened, a cross-registry consistency invariant weakened) without any version-header bump, while a certification created against the pre-edit bytes remains the active pointer | Rejected — `IMPLEMENTATION_MISMATCH`, via `implementation_scope_digest` (HMIC-REQ-050's thirty-fourth entry, `docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md`, HMIC-REQ-053/058, §31 step 9), the identical mechanism attack #37 already describes for `HBDC-001`, now extended to `HPSE-001`'s own document bytes from the moment of its admission to `contract_versions` — never as a deferred, disclosed exception the way `HBDC-001`'s v1.2 addition originally was (§59.16) |
| 42 *(added v1.5, §59)* | HHCE-001 same-version content drift: `HHCE-001` still declares Contract ID `HHCE-001`, Version `v1.1`, but its normative document bytes are edited (e.g. a provider-profile validation rule quietly loosened, a revocation-check semantic weakened) without any version-header bump, while a certification created against the pre-edit bytes remains the active pointer | Rejected — `IMPLEMENTATION_MISMATCH`, via `implementation_scope_digest` (HMIC-REQ-050's thirty-fifth entry, `docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md`, HMIC-REQ-053/058, §31 step 9), the identical mechanism attack #37/#41 already describe for `HBDC-001`/`HPSE-001`, now extended to `HHCE-001`'s own document bytes from the moment of its admission to `contract_versions` (§59.16) |
| 43 *(added v1.6, §60)* | `core/paths.py` is modified so reached `HarnessPath.join`/`.path` redirects the AG3 remote-job or AG5 promotion-execution record lookup to attacker-selected state while every v1.5 frozen member remains byte-identical | Rejected — `IMPLEMENTATION_MISMATCH`, because v1.6 adds `core/paths.py` to HMIC-REQ-050 and production's frozen identity; its raw bytes now participate in `implementation_scope_digest` under HMIC-REQ-054-058 before contract-version comparison (§31 step 9). No compatibility/grandfathering path accepts the old thirty-five-member digest (§60) |

---

## 42. Contract Versioning

**HMIC-REQ-139.** This contract is frozen as `HMIC-001 v1.0`.

**HMIC-REQ-140.** An unknown future `HMIC-001` version number
encountered by any consumer SHALL fail closed (treated as unsupported),
never silently treated as compatible.

---

## 43. Implementation Readiness

**HMIC-REQ-141.** This contract is implementation-ready — meaning a
future implementation phase may begin design work — only because:
authority principal and write/read authority are frozen (§7); the
Protected Root and storage topology are frozen (§8-9); the certification
and active-pointer schemas are frozen, closed (§11-13); certification-ID
derivation and canonical serialization are frozen (§13-14); repository/
deployment binding is frozen (§15); implementation identity — commit
component, frozen file set, digest algorithm, canonicalization, and
named residual limitations — is frozen (§16-19); the contract binding
set is frozen (§20); the creation ceremony, writer surface, and agent-
write prohibition are frozen (§23-24); storage write safety is frozen
(§25); active-pointer/no-implicit-latest, supersession, and revocation
are frozen (§26-28); post-activation behavior is frozen (§29);
concurrency/locking is frozen (§30); the validation algorithm, status
vocabulary, readiness mapping, and freshness discipline are frozen
(§31-33); activation-readiness integration and the locked recheck are
frozen (§34); certification/activation independence is frozen (§35);
path safety is frozen (§36); and the 43-scenario attack matrix (§41) and
12 security invariants (§40) are frozen. No authority-sensitive TBD
remains in this document.

---

## 44. B-149O-1..4 Closure Criteria (Frozen, Not Met by This Phase)

**HMIC-REQ-142.** This contract's freeze does not itself move B-149O-
1..4 closer to closure. B-149O-1..4 remain **INDEPENDENTLY CONFIRMED
CLOSED AT SYSTEM IMPLEMENTATION/ENFORCEMENT BOUNDARY — DEPLOYMENT/
OPERATIONAL ACTIVATION DEFERRED**, unchanged by this phase, until a
future implementation phase both implements this contract and is
independently verified against it, and HMRC-001's own B-149O-1..4
closure criteria (HMRC-REQ-083) are separately satisfied.

---

## 45. Contract Self-Consistency Statement

**HMIC-REQ-143.** This document has been searched for the terms
`certified`, `certification`, `verified`, `activate`, `PROJECT_STATUS`,
`phase report`, `test`, `commit`, `environment`, `latest`, `newest`, and
`glob`. No contradictory authority statement was found: every use of
"verified"/"certified" outside this contract's own certification model
(§4, §11-12) is confined to non-authoritative evidentiary meaning (§21-
22); no clause grants validity on the strength of `PROJECT_STATUS.md`,
a phase report, a test result, a commit message, or an environment
variable (§22); no clause permits implicit certification selection by
sorting, "latest," "newest," or globbing (§26, HMIC-REQ-085); no clause
authorizes a caller-supplied validity/authority override (§33,
HMIC-REQ-110).

**HMIC-REQ-144 (No Self-Certification Path).** No clause in this
document establishes, or could be read as establishing, a path by which
the Agent OS principal derives its own certification authority from any
agent-authored, agent-writable, or agent-influenced artifact (CIVC-12,
restated).

---

## 46. Expected Contract Verdict

```
HMIC-001 v1.0: FROZEN — READY FOR INDEPENDENT CONTRACT VERIFICATION
```

This is explicitly **not** a claim of VERIFIED. Independent contract
verification is the next phase's job (§47).

---

## 47. Next Phase

**149O.19.3 — HATP Mandatory Independent-Verification Certification
Contract Independent Verification.** Verification MUST independently
attack: implementation identity (commit + frozen-file-set digest,
§16-19); editable-source/import-shadowing binding and its named
residual limitation (§19); transitive file-set completeness against
HMRC-001's own dependency closure (§17, HMIC-REQ-052); contract binding
and drift detection (§20); Protected Root/storage topology, including
the certification/pointer schema closure (§8-13); the Active-
Certification Pointer's no-implicit-latest discipline (§26); revocation
and supersession semantics (§27-28); concurrency/locking, including
lock-ordering with the Cutover Transition Lock (§30, HMIC-REQ-101);
self-certification impossibility (§7, §24, CIVC-12); multi-repository/
cross-deployment replay (§9, §41 attacks #8, #9, #30); and activation-
readiness consumption, including the locked recheck (§34). No
implementation SHALL begin before 149O.19.3 completes.

---

## 48. Explicit Confirmations (Restated for the Phase Report)

No production source (`src/pcae/**`) was modified to produce this
contract. HMRC-001 v1.0, HATP-001 v1.0, HSCE-001 v1.1, and RAE-001 v1.0
all remain byte-unchanged. PBPA-001 v1.0, PBPC-001 v1.2, and RWMPC-001
v1.0 remain byte-unchanged. The current hard-coded `False` readiness
ceiling remained unchanged. No certification artifact, Active-
Certification Pointer, or revocation record was created. No Cutover
Record or activation marker was created or modified. No real
`HATP_MANDATORY` activation occurred. No Class-B provisioning occurred.
No Permission Broker behavior changed. `POL-005` remained unchanged. No
`COMP-002` capability was implemented. `PROJECT_STATUS.md`, phase
reports, test results, and a bare Git commit SHA were not made
certification authority. No self-certification path was created or
proposed as production-reachable. B-149O-1..4 remain independently
closed at the system implementation/enforcement boundary with
deployment/operational activation deferred. HATP production remains
**NOT READY**. Runtime remains **Observed / observe / unavailable**.

---

## 49. Contract Repair History — Phase 149O.19.3R (Finding B-149O.19.3-1)

**Status of this section:** descriptive/historical record of the repair;
it introduces no new `HMIC-REQ-###` identifier and amends no other
section's normative force beyond what §17 (HMIC-REQ-050/052) and §41
attack #11 already state in their repaired form above.

**Finding.** Phase 149O.19.3's independent verification (`docs/
PHASE_149O_19_3_..._INDEPENDENT_VERIFICATION.md` §7.5) found the
original v1.0 eighteen-file `HMIC-REQ-050` enumeration under-bound a
security-relevant transitive production dependency: three frozen files
(`hatp_ag_authority.py`, `hatp_rollback_consumption.py`,
`human_approval_trusted_provenance.py`) import `pcae.core.
hatp_providers`, which is not itself named in HMIC-REQ-050, and which
dynamically resolves the concrete hardware-verification implementations
`hatp_fido2_provider.py`/`hatp_piv_provider.py` — also unnamed. An edit
to `Fido2HardwareProvider.verify()` unconditionally returning
`signature_valid=True` changes zero bytes of any frozen file, leaving
`implementation_scope_digest` — and therefore certification validity —
unaffected. This finding is recorded permanently as **B-149O.19.3-1**.
Verdict at the end of 149O.19.3: **NOT VERIFIED — BLOCKING HMIC-001
CONTRACT FINDING**.

**Pre-repair reproduction (independently re-confirmed by this repair
phase before editing this contract).** With the pre-repair eighteen-file
enumeration: `hatp_providers.py`, `hatp_fido2_provider.py`, and
`hatp_piv_provider.py` were each absent from `_FROZEN_DOTTED_MODULES`;
`hatp_ag_authority.py`/`hatp_rollback_consumption.py`/
`human_approval_trusted_provenance.py` each directly `import pcae.core.
hatp_providers`; `hatp_providers.create_production_hardware_provider`
dynamically imports `Fido2HardwareProvider`
(`hatp_fido2_provider.py:243`, class `Fido2HardwareProvider`) and, with
explicit `allow_piv_fallback=True`, `PivHardwareProvider`
(`hatp_piv_provider.py`); `Fido2HardwareProvider.verify()`
(`hatp_fido2_provider.py:341-397`) performs the real FIDO2 cryptographic
signature/attestation check producing the raw
`HATPProviderVerificationOutcome` facts `human_approval_trusted_
provenance.verify_hatp_proof` (frozen) consumes to reach a HATP
verification status; none of this is visible to a digest computed only
over the pre-repair eighteen paths.

**Extended authority-dependency re-walk (this phase, going beyond
149O.19.3's own three named files).** This repair phase independently
re-walked the `pcae.*` import closure of the frozen set plus the three
named candidates via Python `ast` (not the contract's own prose;
methodology matches 149O.19.3's own strict-subset approach, excluding
`cli.py`/`commands/agent.py`/`core/agent.py`'s own dozens of unrelated
command-dispatch imports, already reviewed and accepted at 149O.19.2/
149O.19.3). This re-walk found a **fourth** omitted authority-sensitive
file 149O.19.3 did not name: `hatp_fido2_provider.py` imports
`pcae.core.hatp_hardware_credentials` (`HATPHardwareCredentialStore`,
`HATPHardwareCredentialStoreError`) — a protected, read-only registry
mapping an enrolled hardware `signer_key_id` to the public-key material
`Fido2HardwareProvider.verify()` checks a hardware signature against, at
its own fixed, non-agent-writable, platform-level root
(`/Library/Application Support/PCAE/HATP/hardware-credentials` on
macOS, `/etc/pcae/hatp/hardware-credentials` on Linux) — structurally
the same class of protected trust-store `HATPTrustStore` (Wave 2,
already frozen via `hatp_bootstrap.py`) is, for a different credential
namespace. Modifying this file's parsing/lookup logic (e.g., making
`lookup_credential` return an attacker-chosen public key, or return a
stale/no-op success for any `signer_key_id`) is exactly as invisible to
the pre-repair digest as modifying `hatp_fido2_provider.py` itself, and
was not covered by 149O.19.3's own three-file recommendation. This
repair adds it as the fourth new frozen path.

**Transitive-Completeness Table.**

| Source file | Reached from | Security-sensitive behavior | Pre-repair frozen? | Classification | Repair action | Rationale |
|---|---|---|---|---|---|---|
| `core/hatp_providers.py` | `hatp_ag_authority.py`, `hatp_rollback_consumption.py`, `human_approval_trusted_provenance.py` (all frozen) | Production hardware-provider registry/selection (`create_production_hardware_provider`, `discover_hardware_providers`) | No | A — authority-sensitive | Added to HMIC-REQ-050 | Controls which concrete provider implementation is selected for real verification |
| `core/hatp_fido2_provider.py` | `hatp_providers.py` (dynamic import) | Real FIDO2 cryptographic signature/attestation verification (`Fido2HardwareProvider.verify()`) | No | A — authority-sensitive | Added to HMIC-REQ-050 | Produces the raw `signature_valid`/`human_presence_proven` facts HATP verification status is built from |
| `core/hatp_piv_provider.py` | `hatp_providers.py` (dynamic import, explicit fallback) | PIV verification interface; currently `NOT_CONFORMANT`/fail-closed by design, not hardware-backed today | No | A — authority-sensitive | Added to HMIC-REQ-050 | Deferred/non-conformant today is not a reason to exclude (a future phase could complete it without changing HMIC identity otherwise, item 39); it already implements the same `HATPProofVerifierProvider` interface real callers can reach |
| `core/hatp_hardware_credentials.py` | `hatp_fido2_provider.py` | Protected hardware-credential registry supplying the public-key material `verify()` checks a signature against | No | A — authority-sensitive | Added to HMIC-REQ-050 | Structurally the same class of protected trust-store as `HATPTrustStore` (already frozen); a fourth omission 149O.19.3 did not name |
| `pcae.core.paths` | `hatp_mandatory_cutover.py`, `hatp_evidence_store.py`, `hatp_rollback_consumption.py`, `hatp_ag_authority.py` (all frozen) | Generic repo-root/`HarnessPath` path-join helper | No | B — non-authority utility | Not added | No HATP/consumption-authority logic; a path-join helper cannot change a verification/approval outcome |
| `pcae.core.gate_dry_run` / `scope_preflight` / `shell_gate` | `permission_broker.py` (frozen) | Permission Broker policy-decision-support | No | C — already-excluded PB-policy concern | Not added | HMIC-REQ-068 already excludes PBPA-001/PBPC-001 policy from `contract_versions` as downstream of consumption-chain correctness; these modules implement that same excluded concern |
| `pcae.core.gate_dry_run_context`, `artifact_index`, `decision_log`, `governance_timeline`, `memory_snapshot`, `project_state`, `risk_register` | `gate_dry_run.py` (transitively) | Project-status/governance-timeline reporting aggregation; no signature, approval, or verification logic present (independently confirmed by source inspection: none reference `signature`, `verify_hatp`, `approval_present`, `RollbackApproval`, or `HATPProof`) | No | C — downstream of already-excluded PB-policy concern | Not added | Same rationale as the gate_dry_run/scope_preflight/shell_gate trio, extended one hop further; purely reporting/aggregation utilities |
| `pcae.governance.publication.{chgr_envelope,coordinator,storage}`, `pcae.interactive_workflow.{models.session,publication_handoff.models,session.identity}` | `rollback_approval_evidence.py` (frozen), module-level import | RAE-001's own decision-creation ceremony (`create_rollback_approval_decision`, `PublicationCoordinator.execute`) | No | C — RAE-001 creation-ceremony concern, not reachable from readiness evaluation | Not added; open question from 149O.19.3 §7.6 resolved | `resolve_rollback_approval_evidence`/`resolve_rollback_approval_evidence_with_hatp` — the only entry points the frozen consumption chain (`hatp_ag_authority.py`, `hatp_rollback_consumption.py`) calls — never call `create_rollback_approval_decision` or `PublicationCoordinator.execute` (independently confirmed: those symbols do not appear anywhere in the frozen consumption-chain files). `PublicationRecordStore` is touched only for its `.root` default-path property in the read path; no authority check lives there. This publication/interactive-workflow import group is RAE-001's own human-driven creation-ceremony surface, already governed unmodified by RAE-001, and is not on the certified consumption-chain's own call graph |
| `fido2` (third-party, `fido2>=1.1,<2` per `pyproject.toml`) | `hatp_fido2_provider.py` | Real FIDO2 protocol implementation | No | Environment/deployment boundary (HMIC-REQ-065) | Not added | Third-party package versions are explicitly out of `implementation_scope_digest`'s scope per HMIC-REQ-065; this contract binds PCAE-owned source only |

**Additional required files found beyond 149O.19.3's own three-file
recommendation?** **YES** — one (`core/hatp_hardware_credentials.py`),
found by this phase's own extended re-walk.

**Third-party/stdlib boundary.** Reaffirmed unchanged: `fido2` (real
FIDO2 protocol library) is a pinned third-party dependency
(`pyproject.toml`), explicitly out of `implementation_scope_digest`'s
PCAE-owned-source scope per HMIC-REQ-065; no PIV smart-card library
(`pyscard`/`python-pkcs11`) is installed or imported at all today. No
Python standard-library module is added to the frozen set.

**Future HMIC validator self-reference / circularity disposition.**
HMIC-001 v1.0's frozen file set describes the pre-existing HMRC-001
mandatory-consumption implementation being certified (§2, §17) — it
does not, and structurally cannot yet, name the future HMIC-001
validator/admin-writer module's own source files, because that
implementation does not exist yet (no `certifications.json`, no
validator, no admin tool exists anywhere in this repository today,
independently reconfirmed by this repair phase's own repetition of
149O.19.3's self-certification-impossibility search). This is not a
silent gap: HMIC-REQ-076-082 already require the future validator/writer
to live outside the agent-reachable `pcae` CLI surface, gated by real OS
permissions on the Protected Root, not by an in-process check — the
same non-circular posture `activate_hatp_mandatory` itself already has
relative to the Cutover Record it writes. When a future implementation
phase adds the validator's own source files, that phase's own
architecture/freeze work SHALL explicitly decide whether those files
join a future HMIC-001 version's own frozen set (self-binding a
validator to the identity it computes is not automatically circular —
`hatp_mandatory_cutover.py` already binds itself into HMRC-001's own
implicit trust boundary the same way — but this decision is explicitly
deferred to that future phase, not silently assumed here, exactly as
149O.19.1 §9 (item 139) and HMIC-REQ-063 already defer the related
import-shadowing/executed-code-binding question).

**Contract version decision.** HMIC-001 remains **v1.0** rather than
incrementing to v1.1. Rationale: v1.0 was never independently verified
as `VALID`/passing (149O.19.3's verdict was `NOT VERIFIED — BLOCKING`)
and no implementation of v1.0 has ever been built or certified against
it — there is no shipped v1.0 artifact, deployed certification, or
external consumer whose compatibility a version bump would need to
signal breakage to. Repairing a contract before its first successful
independent verification is a repair of the same unreleased version,
not a breaking change to a released one, consistent with this
repository's own precedent of repairing not-yet-verified contract text
in place (e.g. 149O.1F-class same-phase repairs) rather than
version-bumping definitionally-unstable, pre-verification contract
drafts.

**Digest algorithm / canonicalization / Git-identity / contract-binding
change disposition.** None of HMIC-REQ-054 (file digest algorithm),
HMIC-REQ-055 (path canonicalization), HMIC-REQ-056 (file order),
HMIC-REQ-057 (per-file record domain), HMIC-REQ-058 (digest
derivation), HMIC-REQ-046-049 (git-identity component), or §20's
contract-binding-set mechanics (HMIC-REQ-067-070) were changed by this
repair — 149O.19.3 independently verified the algorithm itself sound
(§7.1-7.3 there); only the input file *list* changed (HMIC-REQ-050/052).

**Requirement / invariant / attack-matrix counts after repair.**
Requirement IDs remain exactly `HMIC-REQ-001`–`HMIC-REQ-144` (144
total, no renumbering, no new ID minted — HMIC-REQ-050/052 were revised
in place). CIVC invariants remain exactly CIVC-1–CIVC-12 (unchanged).
The attack matrix remains exactly 32 rows (attack #11 was strengthened
in place to name the provider-layer files explicitly, per §41 above; no
row was added or removed).

**Finding status.** **B-149O.19.3-1: REPAIRED AT CONTRACT LEVEL —
PENDING INDEPENDENT RE-VERIFICATION.** This repair phase does not, and
cannot, close B-149O.19.3-1 itself (§51 of the governing phase
instruction); only an independent re-verification phase may do so.

**HMIC-001 repair verdict.** **HMIC-001: REPAIRED / FROZEN — READY FOR
INDEPENDENT RE-VERIFICATION.** Not `VERIFIED`.

**Recommended next phase.** **149O.19.3R.1 — HMIC Frozen Implementation
Identity Contract Repair Independent Re-Verification** (or
repository-conventional equivalent), which must independently:
reconstruct the pre-repair defect and this repair's diff; re-walk the
authority-sensitive provider dependency closure itself rather than
trusting this table; confirm the repaired twenty-two-file set's
completeness; independently test `implementation_scope_digest`
sensitivity to each of the four newly-added files; re-evaluate the
implementation-identity and frozen-file-set verdicts; re-evaluate the
32-scenario attack matrix as affected by file-set identity; and close
or retain B-149O.19.3-1. No `149O.19.4`-class implementation phase
SHALL begin before that re-verification completes with a passing
verdict.

**No production or upstream-contract change (restated).** No
`src/pcae/**` file was modified by this repair. HMRC-001 v1.0,
HATP-001 v1.0, HSCE-001 v1.1, RAE-001 v1.0, PBPA-001 v1.0, PBPC-001
v1.2, and RWMPC-001 v1.0 all remain byte-unchanged. The hard-coded
`mandatory_consumption_implementation_independently_verified = False`
ceiling (`hatp_mandatory_cutover.py:842-853`) is unchanged. No
certification artifact, Active-Certification Pointer, or revocation
record was created. No Cutover Record or activation marker was created
or modified. No real `HATP_MANDATORY` activation occurred. No Class-B
provisioning occurred. No Permission Broker behavior changed. `POL-005`
remained unchanged. No `COMP-002` capability was implemented. B-149O-
1..4 remain independently closed at the system implementation/
enforcement boundary with deployment/operational activation deferred.
HATP production remains **NOT READY**. Runtime remains **Observed /
observe / unavailable**.

---

## 50. Contract Amendment History — Phase 149O.19.5E.1 (v1.1)

**Status of this section:** descriptive/historical record of the
amendment; it introduces no new `HMIC-REQ-###` identifier and amends no
other section's normative force beyond what §17 (HMIC-REQ-050/052), §40
(CIVC-4), and §41 (attacks #11, #33, #34) already state in their
amended form above.

**Context — Stop Condition W-1.** Phase 149O.19.4's implementation plan
(§10.3, §13) established Stop Condition **W-1**: Wave F (replacement of
the hard-coded `mandatory_consumption_implementation_independently_
verified = False` ceiling with a real readiness check) SHALL NOT begin
until a HMIC-001 v1.1 contract amendment binds the implemented HMIC
validator/admin source into the frozen file set, and that amendment is
independently verified. Waves A–E (149O.19.5A–5E) then implemented
`core/hatp_mandatory_certification.py` (certification/binding parsing
and canonical serialization — Wave A; implementation/contract identity
derivation — Wave B; protected certification-state storage — Wave C;
the active-certification validation engine — Wave D) and
`scripts/hatp_certification_admin.py` (the Protected Admin
create/activate/revoke ceremony script — Wave E), each wave doc
explicitly restating W-1 as "not crossed" and explicitly not modifying
this contract. Phase 149O.19.5E's own §13 "W-1 Source Inventory" closed
out that inventory at exactly these two files and named this phase,
149O.19.5E.1, as the mandatory next step. This section is that step.

**Independent reconstruction of the v1.0 twenty-two-file set (this
phase, before amending anything).** This phase mechanically re-extracted
HMIC-REQ-050's pre-amendment enumeration directly from this contract
file and cross-checked it against the production source constants
`_FROZEN_SRC_PCAE_RELATIVE_FILES`/`_FROZEN_REPOSITORY_ROOT_RELATIVE_
FILES` in `core/hatp_mandatory_certification.py` (its own module-level
`assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 22`) and against
`docs/PHASE_149O_19_5B_...md`'s own restatement: eighteen `src/pcae/`-
relative files, four repository-root-relative contract files, twenty-
two total, byte-identical across all three sources. No discrepancy was
found.

**Independent reconstruction of the actual Wave A–E production diff
(this phase, not trusting phase-summary prose).** This phase confirmed,
by reading every 5A/5B/5C/5D/5E phase doc's own "production files
changed" / "No-Go Confirmations" section and by direct inspection of
both files' current content, that Waves A–E touched exactly two
production files outside the pre-existing twenty-two-file set:
`core/hatp_mandatory_certification.py` (created by Wave A; extended,
never modified outside the file itself, by Waves B/C/D; explicitly not
touched by Wave E) and `scripts/hatp_certification_admin.py` (created
by Wave E; the file Wave A created is explicitly confirmed unmodified
by Wave E's own §3). `core/hatp_mandatory_cutover.py` — the file a
future Wave F will eventually modify — remains byte-unchanged through
every wave. No third production file, inside or outside `src/pcae/**`,
was added or modified by any of Waves A–E.

**Authority-sensitive source inventory and disposition.**

| Source file | Classification | Disposition |
|---|---|---|
| `core/hatp_mandatory_certification.py` | AUTHORITY-SENSITIVE — MUST BE BOUND. Contains certification/binding parsing and canonical serialization (Wave A); implementation-identity, contract-identity, and certification-ID derivation (Wave B); protected certification-state storage/persistence, atomic writes, and the create-once/revocation writers (Wave C); and the sole production Validation Status / VALID-non-VALID determination algorithm, `_validate_at_root` / `validate_active_hatp_mandatory_independent_verification_certification` (Wave D). An edit to any of these — e.g. making `_validate_at_root`'s final comparison step unconditionally return `CertificationStatus.VALID` — changes zero bytes of any pre-v1.1 frozen file, leaving the pre-v1.1 `implementation_scope_digest` (and therefore, once this validator has any production caller, certification validity) unaffected. This is structurally the same class of gap B-149O.19.3-1 named for the provider layer (§49), now applying to the validator itself, exactly as `docs/PHASE_149O_19_5D_...md` §10 anticipated. | Added to HMIC-REQ-050 (limb (b), HMIC-REQ-052) |
| `scripts/hatp_certification_admin.py` | AUTHORITY-SENSITIVE — BIND INTO V1.1, defense-in-depth. This script is the sole intended caller of `core/hatp_mandatory_certification.py`'s internal (non-`__all__`) writer functions (`_append_certification_record`, `_write_active_binding`, `_write_revocation`) and controls the exact content, activation target, and revocation of protected certification state. Per the Writer-vs-Validator analysis below, a compromised writer cannot force the validator to accept an arbitrary implementation identity — the validator independently re-derives `implementation_commit`/`implementation_scope_digest`/`contract_versions`/`certification_id` from live repository state and never trusts a stored value at face value (HMIC-REQ-038-040, §31 step 11). But a compromised or edited writer can still create a self-consistent-yet-misleading protected record (e.g. one whose `certified_by` field misattributes review it never received, since `certified_by` is audit metadata only — HMIC-REQ-130/131 — but a systematically broken writer could in principle be edited to skip a verification-record hash check or otherwise misrepresent what a human Protected Admin actually reviewed before typing `y`), select which candidate record an `activate` ceremony binds as current, and invoke `revoke`. This is a defense-in-depth concern, not a soundness break in the validator's own binary VALID/non-VALID determination — but W-1 (§13 of `PHASE_149O_19_5E_...md`) names it exhaustively, and this contract elects to bind it for the same reason `hatp_mandatory_cutover.py` (item 1 of the original eighteen-file set) was always bound: the contract's own precedent is that code controlling a certification/readiness-relevant outcome belongs inside the scope that certification protects, not only code a validator directly executes. | Added to HMIC-REQ-050 (limb (b), HMIC-REQ-052) |

**Writer vs. validator — explicit, non-overclaimed distinction.** A
malicious or buggy writer (`scripts/hatp_certification_admin.py`)
cannot make the validator (`core/hatp_mandatory_certification.py`)
accept a certification for an implementation identity the validator's
own fresh, independent re-derivation does not match — `derive_
implementation_commit`, `derive_implementation_scope_digest`, `derive_
contract_versions`, and `derive_repository_instance_id` are all called
by the validator itself against live repository state, never read from
the stored record as authoritative (§31 steps 2-3, 9-10). At worst, a
compromised writer produces a record that *fails to validate* — a
denial, safe by construction, exactly `docs/PHASE_149O_19_4_...md` §10.4's
original analysis of the writer. What a compromised writer *can* do —
and why this contract still elects to bind it rather than rely solely
on that safety property — is control the *content* and *timing* of
what gets certified in the first place: which repository state a human
Protected Admin is asked to confirm, whether a revocation is honored,
and which of several candidate records becomes the active pointer. The
validator's soundness (never accepting a false `VALID`) and the
writer's integrity (accurately recording what a human actually
reviewed and decided) are two distinct properties; this contract binds
both files but does not claim they carry identical security roles.

**Additional dependency walk (this phase, not stopping at the two
top-level files).** This phase re-walked the PCAE-owned import closure
of both new files via direct inspection of their `import` statements.
`core/hatp_mandatory_certification.py` imports `pcae.core.hatp_
bootstrap` (`HATPTrustStore`, `HATPTrustStoreError`, `resolve_
canonical_deployment_root` — already frozen, entry 4), `pcae.core.
paths` (`HarnessPath` — already excluded as a B-classification
non-authority utility by §49's own transitive-completeness table; that
adjudication is inherited unchanged, not redone), and `pcae.core.
repository_identity` (already frozen, entry 6). `scripts/hatp_
certification_admin.py` imports `pcae.core.hatp_bootstrap`, `pcae.core.
paths`, `pcae.core.repository_identity` (all three dispositioned
identically to the above), and `pcae.core.hatp_mandatory_certification`
itself (the file already being added in this same amendment). Neither
file imports `hatp_mandatory_cutover.py`, `permission_broker.py`,
`permission_broker_foundation.py`, `rollback_approval_evidence.py`,
`hatp_ag_authority.py`, or `hatp_rollback_consumption.py` — both
modules' own docstrings assert this dependency-minimality, independently
confirmed here by direct source reading, not merely by citing the
docstring. **No additional PCAE-owned production file beyond the two
named above is required by HMIC-REQ-052(b)'s closure rule.** No other
newly-introduced HMIC implementation module exists: all Wave A–D logic
lives in the single `core/hatp_mandatory_certification.py` module; Wave
E introduced no second script.

**`scripts/` path-grammar confirmation and repair.** HMIC-REQ-050's
pre-v1.1 framing sentence read "Paths under `src/pcae/` are given
relative to that directory; contract paths are given relative to the
repository root" — a phrasing that, read literally, named only two
categories (`src/pcae/`-relative, and "contract paths"), leaving a
repository-root-relative *non-contract* path such as
`scripts/hatp_certification_admin.py` structurally unaddressed by the
prose even though HMIC-REQ-055's own canonicalization rule ("every
frozen path... is repository-relative, POSIX-separator, case-sensitive
exactly as stored on disk...") was already fully generic and never
restricted to `src/pcae/**`. This phase repairs HMIC-REQ-050's framing
sentence in place (§17 above) to "every other path is given relative to
the repository root," removing the implicit contract-files-only
reading; HMIC-REQ-055 itself required no change, since its
canonicalization rule was already path-shape-agnostic. This is a
normative clarification of existing intent, not a new binding rule: the
four `docs/contracts/...` entries have always been repository-root-
relative, non-`src/pcae/`-prefixed paths, so the grammar already had to
support that shape; this repair only makes explicit that the same
repository-root-relative bucket is not limited to contract documents.
No symlink loophole is introduced or exists: HMIC-REQ-061/062 (reject
symlinked or non-regular frozen files) apply identically to
`scripts/hatp_certification_admin.py` as to every other frozen path,
with no `scripts/`-specific exception.

**Self-reference resolution (freezing §49's deferred question).** §49's
"Future HMIC validator self-reference/circularity disposition" explicitly
deferred this exact question to "a future implementation phase [that]
adds the validator's own source files." That phase has now occurred
(Waves A–E), and this contract now freezes the answer §49 anticipated:
self-binding a validator to the implementation identity it computes is
**not** circular, for the same reason `core/hatp_mandatory_cutover.py`
(entry 1 of the original set) has always been bound despite being the
file that *enforces* HMRC-001's readiness gate. The reasoning: (1) a
certification stores an *expected* implementation identity
(`implementation_commit` + `implementation_scope_digest`) at the moment
a human Protected Admin reviews and certifies it; (2) at validation
time, the *current* implementation identity is freshly re-derived from
the live repository's own bytes — `derive_implementation_commit` and
`derive_implementation_scope_digest` read the working tree and `git
rev-parse HEAD` anew on every call, never a cached or stored value; (3)
`core/hatp_mandatory_certification.py`'s own source bytes are among the
files that re-derivation hashes, once bound into HMIC-REQ-050 (this
amendment); (4) therefore, editing the validator's own source *changes
the current implementation identity being freshly computed*, which no
longer matches the *expected* identity a certification names — an old
certification simply fails to validate (`IMPLEMENTATION_MISMATCH`),
exactly as editing any other frozen file does. There is no fixed-point
or self-verifying-its-own-correctness problem: the validator never
asks "am I currently valid," it asks "does the live repository's
current implementation identity match what this specific stored
certification names," and its own bytes are one input to the left-hand
side of that comparison, computed completely independently of anything
the right-hand side (the stored certification) claims.

**Admin-script self-binding — identical, non-circular reasoning.** The
same structure applies to `scripts/hatp_certification_admin.py`: at
`certify` time, the script computes `implementation_scope_digest` over
the frozen set *including its own on-disk bytes at that moment*, then
constructs a certification naming that digest. This is not circular
because the two computations happen in strict sequence over disjoint
data: the **implementation digest** is computed over the frozen
*source* files (including the admin script's own source, once bound);
the **certification ID** (`derive_certification_id`) is computed
*afterward*, over the *certification payload itself* (the eight
authority-sensitive fields, including the already-computed
implementation digest as one of its inputs) — never over the generated
certification artifact's own bytes a second time. No later step feeds
the certification artifact's own hash back into the implementation
digest; the dependency graph between "hash of source" and "hash of
certification payload" is strictly one-directional.

**No certification-artifact self-hash (explicit exclusion, confirmed
unchanged).** `implementation_scope_digest`'s frozen file set (HMIC-
REQ-050) contains only PCAE-owned production *source* files and the
four bound *contract* documents — never `certifications.json`,
`certification-bindings.json`, or any other generated protected-storage
artifact. This was true before this amendment and remains true after
it: the two files added by this phase are source implementation files
(one Python module, one Python script), not generated output. True
circularity — a digest that is partly a function of its own prior
output — does not exist anywhere in this scheme, before or after v1.1.

**Runtime/executed-source binding (HMIC-REQ-063) — explicitly
preserved, not silently extended.** This amendment binds *on-disk
source-byte* identity for two additional files; it does not add, imply,
or require any check that the Python interpreter actually executing
`core/hatp_mandatory_certification.py` resolves its import to that exact
on-disk file (module shadowing, `sitecustomize`, `PYTHONPATH`
injection, or an editable-install redirect remain unaddressed, exactly
as HMIC-REQ-063 already names for the pre-v1.1 frozen set). Source-byte
identity binding (what this amendment does) and executed-source
provenance binding (what HMIC-REQ-063 defers) remain two distinct,
independently-tracked concerns; this phase changes only the former, for
two additional files, and leaves the latter's residual-limitation
status completely unchanged. HMIC-REQ-063's own text is byte-unchanged
by this amendment.

**Version-evolution decision.** HMIC-001 moves from **v1.0** to
**v1.1**, reversing §49's earlier decision to keep v1.0 unbumped through
the B-149O.19.3-1 repair. §49's rationale for not bumping ("v1.0 was
never independently verified... no implementation of v1.0 has ever been
built or certified against it") no longer holds: v1.0 *was*
subsequently independently re-verified (149O.19.3R.1: VERIFIED WITH
NON-BLOCKING FINDINGS — CONFORMS), and a real implementation of v1.0's
certification/validation/admin surface now exists (Waves A–E) — there
is a live, meaningfully-shaped v1.0 semantic surface whose frozen-scope
meaning this amendment materially changes (twenty-two files → twenty-
four). Continuing to call the widened scope "v1.0" would let "a v1.0
certification" silently mean two different things (a twenty-two-file
identity claim before this phase, a twenty-four-file identity claim
after) depending on when the reader encountered the term — exactly the
ambiguity HMIC-REQ-140 (unknown-version fail-closed) exists to prevent
consumers from being exposed to. The version bump makes the scope
change an explicit, named, unambiguous fact rather than a silent
redefinition of "v1.0."

**v1.0 certification replay semantics — no grandfathering.** No v1.0-
scoped certification (had one ever been created — none has; §61 below)
would silently satisfy v1.1 validation. There is no compatibility mode,
no caller-suppliable `legacy_scope`/`version=1.0`/`file_count=22`
override, and no alternate scope selector of any kind (HMIC-REQ-050's
"no more, no fewer" enumeration is unconditional). See attack matrix
rows #33-34 (§41) for the precise mechanism and its honest "not yet
operative until production alignment" caveat.

**Certification-artifact schema version vs. contract semantic
version.** `CERTIFICATIONS_DOCUMENT_SCHEMA_VERSION` and
`CERTIFICATION_BINDINGS_DOCUMENT_SCHEMA_VERSION` (the artifact-level
JSON schema versions defined in `core/hatp_mandatory_certification.py`)
are **not** changed by this amendment and remain **1**. Nothing about
this amendment alters `CertificationRecord`'s field set, `Certification
Binding`'s field set, or either document's on-disk JSON shape — only
the *frozen file list* HMIC-REQ-050 enumerates changed. The contract's
own semantic version (HMIC-001 v1.0 → v1.1) and the certification
artifact's own schema version are, and remain, two independent axes;
this phase moves only the former.

**Digest algorithm / canonicalization / Git-identity / contract-binding
change disposition.** None of HMIC-REQ-054 (file digest algorithm),
HMIC-REQ-056 (file order — still strict lexicographic sort of canonical
path strings; the two new entries' presentation position in HMIC-REQ-
050's prose list has no bearing on their digest-processing order),
HMIC-REQ-057 (per-file record domain), HMIC-REQ-058 (digest
derivation), HMIC-REQ-059-062 (missing/extra/symlinked/non-regular
frozen file handling), HMIC-REQ-046-049 (git-identity component), or
§20's contract-binding-set mechanics (HMIC-REQ-067-070, the four bound
contracts' own `contract_versions` check) were changed by this
amendment — only the input file *list* (HMIC-REQ-050) and the closure
rule that derives it (HMIC-REQ-052) changed. The eight-contract bound
set (HMIC-001, HMRC-001, HATP-001, HSCE-001, RAE-001, RWMPC-001,
PBPA-001, PBPC-001) is unchanged; among these, **only HMIC-001's own
bytes changed** — HMRC-001 v1.0, HATP-001 v1.0, HSCE-001 v1.1, RAE-001
v1.0, RWMPC-001 v1.0, PBPA-001 v1.0, and PBPC-001 v1.2 all remain
byte-unchanged, independently confirmed by this phase (`git diff
--name-only <phase-entry-commit>..HEAD -- docs/contracts/` names only
this file). Note explicitly: HMIC-001's own version/bytes are **not** a
member of any `CertificationRecord`'s `contract_versions` mapping
(HMIC-REQ-067 lists exactly HMRC-001/HATP-001/HSCE-001/RAE-001 as the
minimal sufficient `contract_versions` set) — this amendment does not
change that. The mechanism by which this contract's own version change
becomes enforced against a stored certification is exclusively through
`implementation_scope_digest` (HMIC-001's own contract-file bytes are
not among the twenty-four frozen files either, so it is not digest-bound
directly — HMIC-001 is the contract *defining* the digest, not a file
the digest hashes), operating once production identity derivation is
realigned to hash the twenty-four-file v1.1 set naming the two new
source files (a future phase). This is the same "not yet operative
until production alignment" caveat as attack #33; it is stated once
more here for the digest-mechanism section specifically so the two
independent framings (attack-matrix and digest-algorithm) do not appear
to contradict each other.

**Requirement / invariant / attack-matrix counts after amendment.**
Requirement IDs remain exactly `HMIC-REQ-001`–`HMIC-REQ-144` (144
total, no renumbering, no new ID minted — HMIC-REQ-050/052 were revised
in place, following the same in-place-revision precedent §49 already
established). CIVC invariants remain exactly CIVC-1–CIVC-12 (unchanged
— CIVC-4 was strengthened in place to state explicitly that it now
covers the certification/validation implementation itself, per §40
above; no invariant was added or removed). The attack matrix grows from
32 to **34** rows: attack #11 was strengthened in place (per §41 above)
to name the two new frozen files explicitly, and two genuinely new rows
were added — #33 (v1.0-scope replay under a v1.1 environment) and #34
(file-set-downgrade / production-still-22-during-transition) — because
neither pre-existing row addressed a *contract-version-scope* change as
distinct from a *file-bytes-drift* change (attack #14's "contract-
version replay" concerns only the four externally-bound HMRC/HATP/HSCE/
RAE contracts' own `contract_versions` field, not HMIC-001's own
frozen-scope enumeration, which is not part of any certification's
`contract_versions` mapping).

**W-1 status after this amendment.** **REPAIRED AT CONTRACT LEVEL —
INDEPENDENT VERIFICATION PENDING — PRODUCTION TWENTY-FOUR-FILE
ALIGNMENT PENDING.** Not CLOSED. Three separate, still-open facts
remain, exactly as the governing phase instruction requires be kept
distinct: (A) this contract now enumerates twenty-four frozen files,
including the validator and admin-script source (§17 above); (B) an
independent verification phase must confirm that enumeration is correct
— complete, minimal, and structurally sound — before it may be relied
upon (§51 below); (C) `core/hatp_mandatory_certification.py`'s own
production identity-derivation code (`_FROZEN_SRC_PCAE_RELATIVE_FILES`
etc.) still implements the pre-amendment twenty-two-file enumeration
and was **not** modified by this phase (§56 below) — a dedicated,
bounded future implementation-alignment phase must update it to the
verified twenty-four-file set, and that alignment must itself be
independently verified, before Wave F may be considered.

**Production-contract divergence after this phase (expected, disclosed,
fail-closed).** As of this amendment: HMIC-001 v1.1's contract text
names a twenty-four-file frozen subject; `core/hatp_mandatory_
certification.py`'s own `_FROZEN_AUTHORITY_BEARING_FILES` constant (and
its module-level `assert len(...) == 22`) still implements the
twenty-two-file v1.0 subject, unchanged by this phase. Production is
therefore temporarily **not conformant** to HMIC-001 v1.1's
implementation-scope enumeration, by intentional sequencing (§29 of the
governing phase instruction; this is the same sequencing §27 of that
instruction requires be stated plainly, not hidden or euphemized). This
divergence has **zero** functional effect on any real readiness
decision: the hard-coded `mandatory_consumption_implementation_
independently_verified = False` ceiling in `hatp_mandatory_cutover.py`
is unchanged (§58/82 below), zero production callers of the validator
exist (§60/83 below), and no real certification state exists anywhere
on this host to be validated against either file count (§61 below).
Fail-closed holds throughout regardless of which of the two file counts
production happens to compute over.

**Finding status.** **W-1 (149O.19.4 §13 / 149O.19.5E §13): REPAIRED AT
CONTRACT LEVEL — PENDING INDEPENDENT VERIFICATION.** This amendment
phase does not, and cannot, close W-1 itself; only an independent
verification phase, followed by a bounded production-alignment phase
and that phase's own independent verification, may do so (§51 below).

**HMIC-001 v1.1 amendment verdict.** **HMIC-001 v1.1: FROZEN —
VALIDATOR/ADMIN IMPLEMENTATION IDENTITY CONTRACT EVOLUTION COMPLETE —
PENDING INDEPENDENT VERIFICATION.** Not `VERIFIED`. Not `READY FOR WAVE
F` — this amendment alone does not, and is not intended to, authorize
Wave F (§28 of the governing phase instruction).

**Recommended next phase.** **149O.19.5E.2 — HMIC v1.1 Validator/Admin
Implementation Identity Contract Independent Verification** (or
repository-conventional equivalent), which must independently:
reconstruct the pre-amendment twenty-two-file set and this amendment's
diff; reconstruct the actual Wave A–E implementation itself (not trust
this section's prose); independently re-determine whether exactly these
two additions are sufficient and complete under HMIC-REQ-052's
broadened closure rule; verify the twenty-four-file set's transitive
closure and the `scripts/` path-grammar repair; verify the self-
reference and admin-self-binding resolutions for soundness (not merely
that this section asserts them); verify v1.0-scope-replay rejection
semantics and their "not yet operative" caveat are both correct and
honestly stated; verify no production source or hard-coded `False`
ceiling was touched; and confirm production remains intentionally,
fail-closed-ly stale at twenty-two files pending a future bounded
implementation-alignment phase. If that verification passes, the next
phase after it is **not** Wave F — it is a bounded implementation-
alignment phase (recommended name: `149O.19.5E.3` or
repository-conventional equivalent) that updates `core/hatp_mandatory_
certification.py`'s own frozen-file constants from twenty-two to the
verified twenty-four-file set, followed by that alignment's own
independent verification. Only after both of those complete may Wave F
(149O.19.5F or repository-conventional equivalent) be considered — not
recommended directly by this phase or by the verification phase that
follows it.

**No production or upstream-contract change (restated).** No
`src/pcae/**` or `scripts/**` file was modified by this amendment. Only
`HMIC-001` changed among the eight bound contracts; HMRC-001 v1.0,
HATP-001 v1.0, HSCE-001 v1.1, RAE-001 v1.0, RWMPC-001 v1.0, PBPA-001
v1.0, and PBPC-001 v1.2 all remain byte-unchanged. The exact twenty-two-
file HMIC-REQ-050 v1.0 production implementation (`_FROZEN_AUTHORITY_
BEARING_FILES` etc. in `core/hatp_mandatory_certification.py`) was
**not** updated to twenty-four files by this phase — that is an
intentional, disclosed, future-phase obligation, not an oversight. The
hard-coded `mandatory_consumption_implementation_independently_
verified = False` ceiling (`hatp_mandatory_cutover.py:842-853`) is
unchanged. `hatp_mandatory_cutover.py` was not modified and gained no
new import or call. No certification artifact, Active-Certification
Pointer, or revocation record was created anywhere on this host. No
Cutover Record or activation marker was created or modified. No real
`HATP_MANDATORY` activation occurred. No Class-B provisioning occurred.
No Permission Broker behavior changed. `POL-005` remained unchanged. No
`COMP-002` capability was implemented. B-149O.19.3-1 remains
independently closed, unchanged by this phase. B-149O-1..4 remain
independently closed at the system implementation/enforcement boundary
with deployment/operational activation deferred, unchanged by this
phase. HATP production remains **NOT READY**. Runtime remains
**Observed / observe / unavailable**.

---

## 51. Contract Amendment History — Phase 149O.20D (v1.2)

**Status of this section:** descriptive/historical record of the
amendment; it introduces exactly one new `HMIC-REQ-###` identifier
(HMIC-REQ-145, §20) and amends no other section's normative force
beyond what §20 (HMIC-REQ-067/068/069/145), §40 (CIVC-5), and §41
(attacks #35, #36) already state in their amended form above.

**Context — HBDC-REQ-048.** Phase 149O.20B froze `docs/contracts/
HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001 v1.0), electing "Option
A" (§17 there): HBDC-001 governs deployment-topology claims but is not,
as of v1.0, one of HMIC-001's bound contracts. HBDC-REQ-048 states this
explicitly as a forward obligation: *"Before any deployment may be
represented as satisfying HMIC-REQ-063's Option-C accepted-residual
branch on the strength of this contract in a mechanically-gated way,
HBDC-001 SHALL be added to HMIC-001's bound-contract set — at minimum,
its version tracked in `contract_versions` — via a future HMIC-001
amendment (target: HMIC-001 v1.2)."* Phase 149O.20C then independently
re-verified HBDC-001 (VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS)
and independently re-derived that Option A is correct, empirically
confirming HBDC-001's bytes participate in neither `contract_versions`
nor `implementation_scope_digest` today, and recommending exactly this
phase, 149O.20D, as the required next step. This phase performs the
HBDC-REQ-048 amendment 149O.20C recommended and no more.

**Independent reconstruction of the v1.1 baseline (this phase, before
amending anything).** This phase mechanically re-extracted, directly
from the live contract text (not from any phase-report summary): HMIC-
001 v1.1, `HMIC-REQ-001`–`HMIC-REQ-144` (144 requirements, no gaps, no
duplicates), `CIVC-1`–`CIVC-12` (12 invariants), a 34-row attack matrix
(§41), a twenty-four-file `HMIC-REQ-050` frozen implementation-source
enumeration, and a four-member `contract_versions` set (HMIC-REQ-067:
`HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`). This phase cross-checked
the twenty-four-file enumeration and the four-member `contract_versions`
set directly against live production source
(`core/hatp_mandatory_certification.py`'s `_FROZEN_AUTHORITY_BEARING_
FILES` — asserted `== 24` at module scope — and
`_CONTRACT_IDENTITY_FILES`, which literally enumerates the same four
contracts). No discrepancy was found: production's frozen-file count is
already aligned to twenty-four (the `149O.19.5E.3`-class alignment phase
HMIC-001 v1.1 anticipated has already occurred, prior to this phase),
independently confirmed, not assumed from `PROJECT_STATUS.md`.

**Independent reconstruction of HBDC-001's status (this phase).**
Directly re-read `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` in
full: HBDC-001 v1.0, 55 requirements (`HBDC-REQ-001`–`HBDC-REQ-055`), 8
invariants (`CBD-1`–`CBD-8`), a 21-row attack matrix, `Status: FROZEN —
PENDING INDEPENDENT VERIFICATION` at freeze time, subsequently confirmed
`INDEPENDENTLY VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS` at
149O.20C. Directly re-read `core/hatp_mandatory_certification.py`:
`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` appears in neither
`_FROZEN_AUTHORITY_BEARING_FILES` (the twenty-four-file
`implementation_scope_digest` set) nor `_CONTRACT_IDENTITY_FILES` (the
four-member `contract_versions` set). This phase independently confirms
149O.20C's own empirical finding; it does not merely accept it.

**Terminology precision restated (149O.20C §12, preserved exactly, not
re-litigated).** The governing phase instruction's "current HMIC
bound-contract set: 8 → target 9" framing describes the repository's
**total frozen-contract corpus** — `HATP-001`, `HMRC-001`, `HMIC-001`,
`HSCE-001`, `RAE-001`, `RWMPC-001`, `PBPA-001`, `PBPC-001` (eight,
becoming nine with `HBDC-001` added) — a distinct notion from HMIC-001's
own `contract_versions` binding field (HMIC-REQ-067), which contains
four entries pre-amendment and **five**, not nine, post-amendment. This
phase reports both counts explicitly and does not conflate them, exactly
as 149O.20C's own disclosure (§12 there) requires of any phase that
follows it: **total frozen-contract corpus: 8 → 9. HMIC-001
`contract_versions` membership: 4 → 5.**

**Option-A rationale, re-derived (not merely restated).** HBDC-001
determines whether a Model-A deployment's environment-lock state (§13
there) is sufficient to invoke HMIC-REQ-063's Option-C accepted-residual
branch instead of its BLOCKING branch. If HBDC-001's own normative text
could be edited — its environment-lock requirements loosened, an
attack-matrix row weakened, its Model-A scope silently broadened — without
that edit changing anything HMIC-001's certification identity tracks,
an existing `VALID` certification could continue to read as "Option-C
conditions independently verified sufficient" while the deployment rules
a human reviewer actually approved had since been quietly weakened. This
is the identical class of risk `contract_versions` already exists to
close for `HMRC-001`/`HATP-001`/`HSCE-001`/`RAE-001` (HMIC-REQ-069): a
downstream trust-gating contract's own drift must be certification-
visible. HBDC-001 is not a downstream *policy* concern like
`RWMPC-001`/`PBPA-001`/`PBPC-001` (HMIC-REQ-068) — it is a prerequisite-
topology contract a Model-A certification's Option-C reliance directly
depends on, structurally identical in role to the four already-bound
contracts. This rationale is frozen normatively at HMIC-REQ-067's
revised text (§20 above).

**Decision — HBDC-001 joins `contract_versions`, not
`implementation_scope_digest`.** HBDC-REQ-048's own text sets the
required floor: *"at minimum, its version tracked in
`contract_versions`."* This phase implements exactly that floor and no
more: HMIC-REQ-067 is revised in place to name `HBDC-001` as a fifth
`contract_versions` member (§20). This phase deliberately does **not**
add `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` to HMIC-REQ-050's
twenty-four-file `implementation_scope_digest` enumeration. Three
independent reasons converge: (1) HBDC-REQ-048's own text names
`contract_versions` membership as the required minimum, not digest
membership; (2) HBDC-001 §17's own "Rejected alternatives" analysis
explicitly rejected introducing a second, parallel protected-binding
mechanism for HBDC-001, in favor of reusing the existing
`contract_versions` field "for exactly this purpose" — extending that
same reasoning, widening `contract_versions` (an existing, already-
proven mechanism) is preferable to also silently growing a differently-
purposed enumeration (`implementation_scope_digest` binds *PCAE-owned
source and contract-document* implementation identity, HMIC-REQ-052(a)/
(b) — not deployment-topology-contract identity per se, even though the
other four bound contracts happen to receive both bindings, per their
own closure-rule history in §49/§50); (3) the governing phase
instruction's own repeated default expectation is that the twenty-four-
file enumeration remains unchanged unless direct analysis proves
otherwise (item 20/25/76/77 there), and no such proof was found — HBDC-
REQ-048's literal minimum is fully satisfiable without it. This decision
necessarily leaves a residual limitation, disclosed at HMIC-REQ-145
(§20) and restated below, rather than silently claiming a completeness
this amendment does not achieve.

**Residual limitation, honestly disclosed (HMIC-REQ-145, restated
here).** `HMRC-001`/`HATP-001`/`HSCE-001`/`RAE-001` each receive *two*
independent bindings — `contract_versions`' version-header comparison
*and* `implementation_scope_digest`'s content-digest inclusion
(HMIC-REQ-053: "these two mechanisms are deliberately redundant, not
interchangeable... No future implementation SHALL treat either mechanism
as sufficient without the other"). `HBDC-001` under v1.2 receives only
the first. Consequence: a version-bumped `HBDC-001` revision is
certification-visible (`CONTRACT_MISMATCH`) the moment production
identity derivation is realigned to the five-member set; a same-version,
content-only `HBDC-001` edit is **not** certification-visible under
v1.2. This is named explicitly, not hidden, using the identical
disclosure discipline HMIC-REQ-063 already established for the
executed-code/import-shadowing limitation — this phase does not claim
completeness it has not achieved, and a future contract revision MAY
close this specific gap by additionally digest-binding HBDC-001's
document bytes (HMIC-REQ-145 names this explicitly as an available,
not-yet-taken, future option).

**Option C / HMIC-REQ-063 — explicitly preserved, not solved.** Binding
HBDC-001 into `contract_versions` makes HBDC-001's own *stated*
environment-lock requirements drift-visible to certification identity
(subject to HMIC-REQ-145's residual limitation). It does **not**
implement, and does not claim to implement, any cryptographic executed-
source or runtime-module-resolution attestation. HMIC-REQ-063's own text
is byte-unchanged by this amendment. A certification binds (a) the
consumption-chain implementation's source-byte identity
(`implementation_scope_digest`), (b) the four consumption-chain
contracts' semantic identity, and, as of v1.2, (c) HBDC-001's own stated
deployment-topology semantics — this combination produces *certified
source/contract identity plus verified deployment-environment
configuration claims*, not cryptographic executed-process attestation.
Option C (HMIC-REQ-063's conditional accepted-residual branch, gated on
HBDC-001 Model-A environment-lock conformance) remains exactly as
conditional as 149O.20A/149O.20C established it; this amendment does not
convert it into an unconditional acceptance, and Model A remains the
sole HBDC-001-authorized deployment model (HBDC-REQ-022..024, unchanged
by this phase).

**24-file implementation-source scope preserved (verified, not
assumed).** HMIC-REQ-050's twenty-four-file enumeration is byte-identical
before and after this phase (this phase's own diff touches no line of
§17). `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` was not added
to it (§ decision above). Source count before this phase: 24. Source
count after this phase: 24. Unchanged.

**Requirement / invariant / attack-matrix counts after amendment.**
Requirement IDs are now `HMIC-REQ-001`–`HMIC-REQ-145` (145 total):
HMIC-REQ-067/068/069 were revised in place (widened `contract_versions`
enumeration, unchanged exclusion list, widened drift-comparison
description), following the identical in-place-revision precedent §49
and §50 already established for HMIC-REQ-050/052; exactly one genuinely
new identifier was minted and appended after the prior final ID,
HMIC-REQ-145 (§20), naming the residual limitation no prior requirement
already stated. CIVC invariants remain exactly `CIVC-1`–`CIVC-12` (12
total, unchanged in count) — `CIVC-5` was strengthened in place to state
the five-member v1.2 `contract_versions` set explicitly; no invariant was
added or removed. The attack matrix grows from 34 to **36** rows: two
genuinely new rows were added — #35 (HBDC semantic-drift-after-
certification) and #36 (legacy four-member `contract_versions` replay) —
because neither pre-existing row addressed a *fifth-contract-membership*
drift or replay concern; no pre-existing row was altered in substance
(attack #14's "contract-version replay" continues to describe the four
pre-existing bound contracts generically and already covers `HBDC-001`
by the same mechanism once HMIC-REQ-067 is read as five-member; #35/#36
were still added for the HBDC-specific framing the governing phase
instruction itself required — semantic-drift and legacy-scope-replay
named explicitly, not merely inferable from #14's generic statement).

**Certification-artifact schema — unchanged, confirmed.**
`CERTIFICATIONS_DOCUMENT_SCHEMA_VERSION` and
`CERTIFICATION_BINDINGS_DOCUMENT_SCHEMA_VERSION` are not touched by this
amendment and remain **1**. `CertificationRecord`'s field set,
`CertificationBinding`'s field set, and both documents' on-disk JSON
shape are unchanged — only `contract_versions`' own *entry count*
(within its existing `Mapping[str, str]` shape) grows from four to five,
exactly as the schema already accommodates for any string-keyed
dictionary. `CertificationStatus`/Validation Status vocabulary
(HMIC-REQ-106) is unchanged — `CONTRACT_MISMATCH` and `MALFORMED`
already exist and already suffice for every v1.2 rejection scenario
(§41 attacks #35, #36); no new status value was introduced. The
validation algorithm's structural shape (§31, HMIC-REQ-103) is
unchanged — step 10 now compares five entries instead of four; no new
step was added.

**Certification ID algorithm — unchanged, confirmed.** `certification_
id`'s derivation (HMIC-REQ-038) is unchanged. Certification-ID *values*
computed after production alignment will differ from certification-ID
values computed before it, because the `contract_versions` field —
already one of `certification_id`'s digest inputs (HMIC-REQ-038) —
gains a fifth entry; this is an expected consequence of a wider payload,
not an algorithm change.

**Ninth-contract ordering.** `contract_versions` is a `Mapping[str,
str]`, not an ordered sequence with positional meaning; HMIC-REQ-041's
canonical-serialization rule (`json.dumps(..., sort_keys=True)`) already
determines deterministic on-disk key order independent of Python
dict-literal insertion order or any other non-deterministic source.
`HBDC-001` sorts lexicographically after `HATP-001`/`HMRC-001`/
`HSCE-001` and before `RAE-001` under `sort_keys=True` — this is a
mechanical consequence of the existing, unchanged serialization rule,
not a new ordering decision this amendment makes.

**Production-contract divergence after this phase (expected, disclosed,
fail-closed — the required "contract-first temporary divergence").** As
of this amendment: HMIC-001 v1.2's contract text names a five-member
`contract_versions` set (HMIC-REQ-067). `core/hatp_mandatory_
certification.py`'s own `_CONTRACT_IDENTITY_FILES` constant still
implements the four-member v1.1 set, unchanged by this phase. Production
is therefore temporarily **not conformant** to HMIC-001 v1.2's
`contract_versions` enumeration, by intentional sequencing, stated
plainly: real Class-B is not provisioned; no real HMIC certification
exists anywhere on this host; HATP production remains **NOT READY**; no
real `HATP_MANDATORY` activation has occurred or is authorized by this
phase. **Correction to §50's own "zero production callers" framing,
independently re-verified by this phase against live source, not
assumed from §50's prose:** Phase 149O.19.5F (Wave F, prior to and
independent of 149O.20A–D, gated by Stop Condition W-1, confirmed closed
at 149O.19.5E.4) has since wired a real production caller —
`hatp_mandatory_cutover.py`'s `_assess_hatp_mandatory_activation_
readiness_at_root` now calls
`validate_active_hatp_mandatory_independent_verification_certification`
fresh on every readiness assessment, mapping its result via
`certification_status_satisfies_readiness`, with every non-`VALID`
status and every exception failing closed to `False`; the literal
hard-coded `False` ceiling §49/§50 both describe no longer exists in
this file. This divergence nonetheless has **zero** functional effect on
any real readiness decision: no `certifications.json` or
`certification-bindings.json` file exists anywhere on this host (this
phase independently re-confirmed their absence by direct filesystem
inspection), so every fresh validation call returns `MISSING`
(§31 step 4) — mapping the readiness fact to `False` — identically
regardless of whether `contract_versions` is read as a four-member or
five-member requirement. Fail-closed holds throughout regardless of
which `contract_versions` cardinality production happens to compute
over, because there is no stored certification record on this host for
either cardinality to be compared against.

**HBDC-BINDING-GATE status.** Using this repository's own gate-naming
convention (mirroring `B-149O.19.3-1`, `W-1`): **HBDC-BINDING-GATE:
CONTRACT-LEVEL EVOLUTION COMPLETE — INDEPENDENT CONTRACT VERIFICATION
PENDING — PRODUCTION FIVE-MEMBER `contract_versions` ALIGNMENT PENDING.**
Not CLOSED. Three separate, still-open facts remain distinct, exactly as
W-1 (§50) modeled: (A) this contract now names a five-member
`contract_versions` set including `HBDC-001` (§20 above); (B) an
independent verification phase must confirm that amendment is correct —
sound, minimal, honestly disclosed — before it may be relied upon (next
phase, below); (C) `core/hatp_mandatory_certification.py`'s own
`_CONTRACT_IDENTITY_FILES` constant still implements the pre-amendment
four-member enumeration and was **not** modified by this phase — a
dedicated, bounded future implementation-alignment phase must update it
to the verified five-member set, and that alignment must itself be
independently verified, before Class-B provisioning planning may be
considered.

**W-1 / B-149O.19.3-1 status — unaffected, not reopened.** `W-1`
(§50) concerned binding the HMIC validator/admin-writer *source files*
(`core/hatp_mandatory_certification.py`, `scripts/hatp_certification_
admin.py`) into the twenty-four-file `implementation_scope_digest`
enumeration — a source-implementation-scope question. This phase's
twenty-four-file enumeration is byte-identical to pre-phase (§ above);
`W-1` remains exactly as §50 left it: **repaired at the contract level,
independent verification of that repair still pending from 149O.19.5E.2
onward** — this phase does not reopen, narrow, or widen `W-1`'s own
scope. `B-149O.19.3-1` (§49, the provider-layer four-file finding)
remains independently closed, untouched by this phase. Both use a
distinct identifier space from this phase's own new
**HBDC-BINDING-GATE** identifier (above), per the governing phase
instruction's own explicit caution not to misuse `W-1`'s name for a
different prerequisite.

**Contract-evolution verdict.** **HMIC-001 v1.2: FROZEN — HBDC BOUND-
CONTRACT IDENTITY EVOLUTION COMPLETE — PENDING INDEPENDENT
VERIFICATION.** Not `VERIFIED`. **HBDC binding gate: CONTRACT-LEVEL
EVOLUTION COMPLETE — INDEPENDENT CONTRACT VERIFICATION PENDING —
PRODUCTION FIVE-MEMBER ALIGNMENT PENDING.** **Class-B: CONTRACT
VERIFIED — NOT PROVISIONED** (149O.20C's own verdict, unchanged by this
phase). **HATP production: NOT READY.**

**Recommended next phase.** **149O.20E — HMIC v1.2 HBDC Bound-Contract
Identity Independent Verification** (or repository-conventional
equivalent), which must independently: reconstruct the pre-amendment
four-member `contract_versions` baseline and this amendment's diff;
independently re-derive that `HBDC-001` is the correct, sufficient fifth
member (not merely accept this section's rationale); independently
verify the total-frozen-contract-corpus-vs-`contract_versions`-
membership terminology distinction is correctly, non-conflatingly
restated (8→9 corpus, 4→5 `contract_versions`); independently verify
`HBDC-001` byte drift (version-bumped case) would change certification
contract identity once production is realigned, and independently verify
and honestly restate the same-version byte-drift residual limitation
(HMIC-REQ-145) rather than silently accepting or silently overclaiming
it; independently verify legacy four-member `contract_versions` replay
rejection semantics and their "not yet operative" caveat; independently
verify the twenty-four-file `implementation_scope_digest` source scope
remains exactly 24, byte-identical; independently verify HMIC-REQ-063/
Option-C semantics are preserved, not weakened or solved; independently
verify production remains intentionally, fail-closed-ly stale at the
four-member set pending a future bounded alignment phase; and confirm no
real provisioning/certification/activation occurred. If 149O.20E passes,
the next phase after it is **not** Class-B provisioning — it is a
bounded implementation-alignment phase (recommended name: `149O.20F` or
repository-conventional equivalent) that updates `core/hatp_mandatory_
certification.py`'s own `_CONTRACT_IDENTITY_FILES` constant from four to
the verified five-member set, followed by that alignment's own
independent verification. Only after both of those complete may Class-B
provisioning planning be considered — not recommended directly by this
phase or by the verification phase that follows it.

**No production or upstream-contract change (restated).** No
`src/pcae/**` or `scripts/**` file was modified by this amendment. Only
`HMIC-001` changed among the now-nine-contract total frozen corpus;
`HMRC-001` v1.0, `HATP-001` v1.0, `HSCE-001` v1.1, `RAE-001` v1.0,
`RWMPC-001` v1.0, `PBPA-001` v1.0, `PBPC-001` v1.2, and `HBDC-001` v1.0
all remain byte-unchanged. `HBDC-001` itself was not modified by this
phase — only HMIC-001 changed among the eight pre-existing bound
contracts plus HBDC-001 (nine total post-amendment). The existing
four-member `HMIC-REQ-067` v1.1 production implementation
(`_CONTRACT_IDENTITY_FILES` in `core/hatp_mandatory_certification.py`)
was **not** updated to five members by this phase — that is an
intentional, disclosed, future-phase obligation, not an oversight. The
twenty-four-file `HMIC-REQ-050` implementation-source enumeration was
not touched and was not updated to twenty-five. `hatp_mandatory_
cutover.py` was not modified by this phase and gained no new import or
call from this phase (its Wave-F wiring — a real, fresh call to
`validate_active_hatp_mandatory_independent_verification_certification`
on every readiness assessment — predates this phase, from Phase
149O.19.5F, and is independently re-confirmed unchanged here, not newly
introduced). No certification artifact, Active-Certification Pointer, or
revocation record was created anywhere on this host. No Cutover Record
or activation marker was created or modified. No real `HATP_MANDATORY`
activation occurred. No Class-B provisioning occurred. No Permission
Broker behavior changed. `POL-005` remained unchanged. No `COMP-002`
capability was implemented. `W-1` and `B-149O.19.3-1` remain
independently closed/repaired exactly as §49/§50 left them, unchanged by
this phase. B-149O-1..4 remain independently closed at the system
implementation/enforcement boundary with deployment/operational
activation deferred, unchanged by this phase. HATP production remains
**NOT READY**. Runtime remains **Observed / observe / unavailable**.

---

## 52. Contract Repair History — Phase 149O.20D.1 (Finding B-149O.20D-1)

**Status of this section:** descriptive/historical record of the
repair; it introduces no new `HMIC-REQ-###` identifier and amends no
other section's normative force beyond what §17 (HMIC-REQ-050/052/053),
§20 (HMIC-REQ-069/145), §40 (CIVC-5), and §41 (attacks #35, #37) already
state in their repaired form above.

**Finding.** Phase 149O.20D (§51) bound `HBDC-001` into `contract_
versions` (HMIC-REQ-067, v1.2) but deliberately left its document bytes
outside `implementation_scope_digest`, disclosing the consequence at
HMIC-REQ-145: a same-version, content-only edit to `HBDC-001` — the
same declared Contract ID `HBDC-001`, the same declared Version `v1.0`,
different normative bytes — would leave `implementation_scope_digest`,
and therefore certification identity, unchanged. Because HBDC-001's own
Option-A disposition (149O.20B §17, independently re-verified 149O.20C)
exists precisely so that a repository-controlled actor's changes to
Class-B deployment-trust semantics cannot remain invisible to an
existing certification, a mechanism that protects only the *declared*
version and not the *actual* content bytes does not fully deliver that
purpose: version-bump discipline is a repository-actor convention, not
a security boundary. This finding is recorded permanently as
**B-149O.20D-1**.

**Pre-repair defect, independently reproduced (before editing this
contract).** This phase independently confirmed, directly against live
contract text and production source, all four premises the governing
phase instruction required proven before treating this as a real
defect:

(A) **HBDC-001 is a normative `contract_versions` member.** HMIC-REQ-067
(v1.2, pre-repair text) names `HBDC-001` as the fifth `contract_
versions` entry, confirmed by direct re-reading of §20.

(B) **The pre-repair binding is declared-identity-only, not
content-sensitive.** HMIC-REQ-069 compares `contract_versions` entries
against "the named contract's own current, live version header" —
version-string comparison, not a content digest; HMIC-REQ-145
(pre-repair text) stated this explicitly for `HBDC-001` specifically.

(C) **HBDC-001 is absent from the 24-file `implementation_scope_digest`
enumeration.** HMIC-REQ-050's pre-repair text (twenty-four entries) did
not include `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`;
independently cross-checked against live production
(`core/hatp_mandatory_certification.py`'s `_FROZEN_AUTHORITY_BEARING_
FILES`, asserted `== 24`, does not name that path either — confirmed by
direct `grep` of the module, not assumed from contract prose).

(D) **A version-preserving `HBDC-001` byte mutation is invisible to the
pre-repair contract-identity representation.** Modeled directly: given a
hypothetical certification `C` created while `HBDC-001` reads Contract
ID `HBDC-001`, Version `v1.0`, byte content `A`, and a subsequent edit to
`HBDC-001`'s normative prose producing byte content `B` while its
declared Contract ID and Version string are left unchanged —
`contract_versions`' stored value for `HBDC-001` (`"v1.0"`) is
unaffected (HMIC-REQ-069 compares version strings only, premise B), and
`implementation_scope_digest` is unaffected because `HBDC-001`'s bytes
are not among the files that digest hashes (premise C). Neither of
`certification_id`'s two authority-bearing digest inputs changes, so
`C` would continue to validate as `VALID` against the mutated `HBDC-001`
bytes under the pre-repair contract. All four premises independently
confirmed true; the finding is real, not reassessed away (per the
governing phase instruction's own "if any premise is false, reassess"
caution).

**Reconstruction of the existing four dual-bound contracts' own
content-binding mechanism (this phase, before selecting a repair).**
This phase independently re-walked HMIC-REQ-050/053 rather than
accepting §51's own prior characterization. For each of `HMRC-001`,
`HATP-001`, `HSCE-001`, `RAE-001`: (1) contract ID/path — each is one of
the four `docs/contracts/*.md` entries directly enumerated in
HMIC-REQ-050's twenty-four-file (pre-repair) list; (2) version-identity
binding — via `contract_versions` (HMIC-REQ-067/069), version-header
string comparison, identical in mechanism to `HBDC-001`'s own pre-repair
binding; (3) content-byte visibility — via direct inclusion of the
contract document's own path in HMIC-REQ-050, whose bytes SHA-256
digest into `implementation_scope_digest` under HMIC-REQ-054/056-058's
frozen two-level construction, exactly as any production source file
in the same enumeration does; (4) mechanism source — HMIC-REQ-053 states
this explicitly: "the four contract files' byte contents participate in
`implementation_scope_digest` directly... as a distinct, additional
binding from the `contract_versions` field's own version-header check...
These two mechanisms are deliberately redundant, not interchangeable."
This confirms, by direct textual re-derivation rather than inference,
that the existing four contracts' content-sensitivity comes from
**digest-set membership**, not from any separate mechanism —
`implementation_scope_digest` is content-sensitive by construction
(SHA-256 over raw bytes); `contract_versions` is not (string comparison
over a declared header). `HBDC-001` lacked only the first of these two
bindings.

**Repair design options evaluated.**

- **Option A (extend normative contract identity to
  `contract_id`/`contract_version`/`contract_content_digest` for all
  bound contracts).** Would add a new, dedicated per-contract digest
  field to `contract_versions`' existing `Mapping[str, str]` shape (or a
  parallel structure), requiring a schema-level change to
  `CertificationRecord` (§11) and a corresponding validation-algorithm
  step (§31) distinct from the existing `implementation_scope_digest`
  check. Rejected: this would introduce a new digest-bearing artifact
  field where the existing `implementation_scope_digest` mechanism
  already provides content-sensitivity for the other four bound
  contracts without any schema change; inventing a second content-digest
  mechanism duplicates, rather than reuses, working machinery, and would
  require this repair phase to design and freeze new canonical-
  serialization and validation-algorithm text for a field the four
  precedent contracts have never needed.

- **Option B (bind `HBDC-001`'s document bytes into the existing
  `implementation_scope_digest`/HMIC-REQ-050 enumeration — selected,
  below).**

- **Option C (a separate, dedicated `bound_contract_content_digest`
  component, protecting only the five `contract_versions` members,
  independent of `implementation_scope_digest`).** Would cleanly
  separate "production/source implementation identity" from "normative
  contract identity" (§25 of the governing phase instruction), avoiding
  Option B's consequence of growing the twenty-four-file enumeration.
  Rejected, for three reasons: (1) it requires the same new schema field
  and validation-algorithm step Option A requires — `CertificationRecord`
  has no existing digest-bearing field scoped to `contract_versions`
  members only, so this is not a "no schema change" option either; (2)
  HBDC-001's own frozen text (HBDC-001 §17, "Rejected alternatives,"
  Option C there) already rejected "a separate protected deployment
  manifest binds HBDC-001's version/digest, independent of HMIC-001" as
  "an unnecessary second protected-binding mechanism when HMIC-001's
  existing `contract_versions` field already exists for exactly this
  purpose" — while that rejected alternative concerned a manifest
  external to HMIC-001 entirely (not a field inside `CertificationRecord`
  itself), the underlying reasoning — prefer reusing an existing,
  already-proven mechanism over inventing a parallel one — applies with
  equal force to a new digest field scoped only to bound contracts; (3)
  it would leave the four pre-existing bound contracts covered by *two
  different* content-binding mechanisms depending on when this contract
  reads them (`implementation_scope_digest` for their historical
  inclusion, the new field for uniformity with `HBDC-001`), or would
  require migrating all five onto the new mechanism and retiring their
  existing HMIC-REQ-053 digest-set membership — a materially larger,
  riskier change than this bounded repair phase's scope permits (the
  governing phase instruction prohibits implementing production code or
  a new validator in this phase in any case).

- **Option D (repository-conventional equivalent not covered above).**
  None found: the repository's own precedent for "make a specific file's
  content certification-visible" is, in every prior instance (the
  original eighteen-file set, the four-file B-149O.19.3-1 provider-layer
  repair at §49, the two-file W-1 addition at §50), enumeration in
  HMIC-REQ-050. No alternative repository-conventional mechanism exists.

**Selected repair: Option B.** `docs/contracts/
HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (`HBDC-001`) is added as the
twenty-fifth entry to HMIC-REQ-050's frozen file enumeration (§17),
identically to how the other four bound contracts' documents already
participate. **Rationale:** (1) reuses an existing, already-verified
mechanism (HMIC-REQ-054-058's digest algorithm, already covering
twenty-four files, is unchanged in every particular except processing
one additional path — HMIC-REQ-056's lexicographic-order rule already
determines where the new entry sorts, no new algorithm text is needed);
(2) requires **no** `CertificationRecord`/`CertificationBinding` schema
change (§29 of the governing phase instruction is directly satisfied:
"If existing contract identity structure already supports digests: no
schema bump may be necessary" — it does, via `implementation_scope_
digest`); (3) is the *identical* mechanism HMIC-REQ-145's own pre-repair
text already named as the available closing option ("A future contract
revision MAY close this gap by additionally binding `HBDC-001`'s
document bytes into `implementation_scope_digest`, mirroring HMIC-REQ-
053's existing redundant-binding precedent for the other four bound
contracts") — this repair takes exactly that pre-identified path, not a
novel one; (4) does not conflict with HBDC-001's own "Rejected
alternatives" text (§17 there), which rejected a *parallel, HMIC-001-
external* manifest, not extension of HMIC-001's own existing digest set
that the other four bound contracts already use; (5) does not modify
`HBDC-001` itself — the contract-change allowlist (only `HMIC-001` may
change) is satisfied, because HBDC-001's inclusion in
`implementation_scope_digest` is achieved by naming its path in
`HMIC-001`'s own HMIC-REQ-050 enumeration, not by editing HBDC-001's own
document.

**Content bytes now matter, regardless of declared version (item 11 of
the governing phase instruction, satisfied).** Same `HBDC-001` Contract
ID, same declared Version `v1.0`, different normative bytes now produces
a different `implementation_scope_digest`, and therefore a different
`certification_id` (HMIC-REQ-038's existing digest-input list is
unchanged in structure — `implementation_scope_digest` was already one
of its inputs; its *value* now additionally depends on `HBDC-001`'s
bytes). An existing certification bound to the pre-mutation digest fails
`implementation_scope_digest` comparison at §31 step 9, yielding
`IMPLEMENTATION_MISMATCH` — the highest-priority rejection property
(attack #10) — deterministically, not merely as a matter of convention.

**Version identity still matters, separately (item 12, satisfied).**
`contract_versions`' version-header comparison (HMIC-REQ-069) is
unchanged and continues to apply to `HBDC-001` independently of the
digest binding — a version-bumped `HBDC-001` revision remains caught by
`CONTRACT_MISMATCH` even if its content-digest happened, hypothetically,
to coincide (SHA-256 collision), and conversely a content-only edit is
now caught by the digest even though the version string is unchanged.
Both mechanisms apply; HMIC-REQ-053 already forbids treating either as
sufficient without the other, and this repair extends that requirement
to `HBDC-001`, not merely restates it for the original four.

**Attack scenarios, explicitly defined (items 13-20).**

- *Same version / different content* (item 13): existing certification
  becomes non-`VALID` — `IMPLEMENTATION_MISMATCH` via digest mismatch
  (attack #37, §41). No compatibility escape: HMIC-REQ-050's "no more,
  no fewer" enumeration and HMIC-REQ-058's frozen two-level construction
  admit no caller-suppliable exception.
- *Different version / same content* (item 14): mismatch —
  `CONTRACT_MISMATCH` via `contract_versions` (attack #35, §41, revised).
- *Contract ID change* (item 15): mismatch — a `contract_versions` key
  rename is a missing-required-key `MALFORMED` case under HMIC-REQ-031's
  closed-schema discipline (mirrors attack #36's reasoning for the whole
  five-member set).
- *HBDC-001 missing* (item 16): fail closed — HMIC-REQ-059
  (`IMPLEMENTATION_MISMATCH` for a missing HMIC-REQ-050 path) now applies
  to `HBDC-001`'s document exactly as it already applies to the other
  twenty-four frozen files.
- *HBDC-001 unreadable* (item 17): fail closed — the same HMIC-REQ-059
  class of failure; no partial-credit read path exists.
- *HBDC-001 symlink/unsafe input* (item 18): HMIC-REQ-061/062 already
  reject any HMIC-REQ-050 path (or parent) that resolves to a symlink,
  directory, or other non-regular file — this now covers `HBDC-001`'s
  document identically to every other frozen path; no gap identified
  requiring separate recording.
- *Old HMIC v1.1 replay* (item 19): still rejected — unaffected by this
  repair; a v1.1-computed twenty-two/twenty-four-file digest cannot equal
  a v1.2/149O.20D.1 twenty-five-file digest (mirrors attack #33's
  reasoning, extended by one file-count step).
- *Current pre-repair v1.2 replay* (item 20): a hypothetical certification
  whose `implementation_scope_digest` was computed over the pre-repair
  twenty-four-file set (i.e., without `HBDC-001`'s bytes) does not
  satisfy the repaired twenty-five-file digest — `IMPLEMENTATION_
  MISMATCH`, by the identical two-level-construction argument attack #33
  already makes for file-count changes. No compatibility/grandfathering
  path exists or is introduced. Because no real certification exists
  anywhere on this host (independently re-confirmed, §51), this scenario
  remains hypothetical, not a live compatibility break.

**Contract version decision: HMIC-001 remains v1.2.** Not incremented to
v1.2.1 or v1.3. Rationale, following the identical precedent §49 already
established for repairing HMIC-001 v1.0 in place after Phase 149O.19.3's
`NOT VERIFIED — BLOCKING` verdict: v1.2 has never been independently
verified (149O.20E, the next recommended phase after 149O.20D, has not
yet run) and no implementation of v1.2 has ever been built or certified
against it — there is no shipped v1.2 artifact, deployed certification,
or external consumer whose compatibility a version bump would need to
signal breakage to. Repairing a contract before its first successful
independent verification is a repair of the same unreleased version, not
a breaking change to a released one, exactly as §49 reasoned for v1.0
and this repository's broader precedent of repairing not-yet-verified
contract text in place.

HMIC-REQ-145's repair disposition: revised in place from a disclosed
residual limitation to a closed one (§20 above) — not deleted, not
renumbered; its ID and its role in the Requirement Inventory Category
Index (§39, "Contract binding set" category) are unchanged.

**HBDC-REQ-048 cross-check.** HBDC-REQ-048's own text sets a floor: "at
minimum, its version tracked in `contract_versions`." This repair
satisfies that floor (unchanged, still true) and additionally exceeds
it by closing the same-version content-drift gap HBDC-001's own
Option-A rationale (149O.20D §51, re-derived) requires be closed before
HBDC-001's deployment-trust semantics can be relied upon as
certification-identity-visible in the fullest sense. HBDC-REQ-048 does
not require this additional binding, but does not forbid it either
("at minimum" leaves headroom this repair uses); the repair does not
reinterpret HBDC-REQ-048 downward — it exceeds its stated floor.

**Option-A purpose, reaffirmed after repair.** HBDC-001 binding exists
so that repository-side changes to deployment-trust semantics cannot
remain invisible to an existing, protected HMIC certification. This
remains true, and is now true for content-only edits as well as
version-bumped ones — closing exactly the gap that previously left it
only partially true.

**Source/contract identity separation — preserved, not conflated.**
`implementation_scope_digest` continues to bind two categorically
different kinds of files under one mechanism, exactly as it already did
for the original nineteen `src/pcae/`-relative production-source files
plus the four (now five) `docs/contracts/*.md` normative-contract
documents plus the one `scripts/` admin-ceremony script: production
implementation identity and normative-contract identity are digest-bound
by the *same* algorithm (HMIC-REQ-054-058) but remain textually and
conceptually distinct within HMIC-REQ-050's own enumeration (the
`src/pcae/`-relative bucket versus the repository-root-relative bucket,
HMIC-REQ-055). This repair does not blur that distinction; it extends an
existing, already-mixed enumeration by one more `docs/contracts/*.md`
entry, the identical category the other four contract documents already
occupy.

**24-file source scope — explicitly, justifiably changed to 25 (item 26
of the governing phase instruction, "strong preference: preserve 24
unless selected repair necessarily changes it" — addressed, not
defaulted around).** HMIC-REQ-050's enumeration grows from twenty-four
to twenty-five entries. This is not a default-avoided change: 149O.20D
(§51) explicitly declined to make this change, for reasons stated there
(HBDC-REQ-048's literal floor, HBDC-001's own external-manifest
rejection, and the governing instruction's own default-preservation
expectation, absent proof otherwise). This repair phase supplies exactly
the proof 149O.20D's own decision anticipated might later require it:
finding B-149O.20D-1, independently reproduced above, demonstrates the
twenty-four-file scope leaves a security-relevant defect uncorrected.
The twenty-fifth entry is the *only* change to HMIC-REQ-050; no other
file is added, removed, or reordered.

**HBDC contract-count / total-corpus terminology — unaffected,
restated.** `contract_versions` membership (HMIC-REQ-067) remains
**five** — this repair does not touch `contract_versions`' own entry
count, only `implementation_scope_digest`'s file count. Total frozen
contract corpus remains **nine** (`HATP-001`, `HMRC-001`, `HMIC-001`,
`HSCE-001`, `RAE-001`, `RWMPC-001`, `PBPA-001`, `PBPC-001`, `HBDC-001`) —
unaffected by this repair, which touches only `HMIC-001`'s own text.
This section preserves 149O.20C/149O.20D's own terminology-
disambiguation discipline (§51 above) rather than re-litigating it.

**Artifact schema — unchanged, confirmed.**
`CERTIFICATIONS_DOCUMENT_SCHEMA_VERSION` and `CERTIFICATION_BINDINGS_
DOCUMENT_SCHEMA_VERSION` remain **1**, untouched by this repair.
`CertificationRecord`'s field set (§11) and `CertificationBinding`'s
field set (§12) are unchanged — `implementation_scope_digest` is a
single SHA-256 hex string field both before and after this repair; only
the *set of files* HMIC-REQ-058 hashes to produce that one string value
grows by one entry. No new field was added or considered necessary,
directly because Option B (not A or C) was selected. `CertificationStatus`
/ Validation Status vocabulary (HMIC-REQ-106) is unchanged —
`IMPLEMENTATION_MISMATCH` already exists and already suffices for the
newly-closed same-version-drift rejection (attack #37); no new status
value was introduced. The validation algorithm's structural shape (§31,
HMIC-REQ-103) is unchanged — step 9 now recomputes a digest over
twenty-five files instead of twenty-four; no new step was added.

**Canonical serialization — no ambiguity introduced.** HMIC-REQ-055
(path canonicalization), HMIC-REQ-056 (lexicographic file order), and
HMIC-REQ-057 (self-delimiting per-file record domain,
`<path>\0<sha256_hex>\n`) already fully specify how any HMIC-REQ-050
entry — including the twenty-fifth — is canonicalized and hashed; no
optional field, no omittable entry, and no map-order ambiguity exists
for `implementation_scope_digest`, which remains a single ordered,
delimited concatenation with no caller-suppliable variant.

**Certification ID — algorithm unchanged, values will differ, as
expected.** `certification_id`'s derivation (HMIC-REQ-038) is unchanged
by this repair. Certification-ID values computed after production
alignment to the twenty-five-file set will differ from values computed
before it, because `implementation_scope_digest` — already one of
`certification_id`'s digest inputs — now depends on one additional
file's bytes; this is an expected consequence of a wider digest input,
not an algorithm change, identical in kind to §51's own analysis of
`contract_versions`' fifth entry.

**Validator consequence (contractual, not implemented here).** A future
validator recomputes `implementation_scope_digest` fresh, over the live,
current twenty-five-file set, at validation time (HMIC-REQ-054, "never
`git show HEAD:<path>`... working-tree bytes"), and compares the result
to the certified value — mismatch on any drift, including `HBDC-001`'s.
This mirrors HMIC-REQ-058's existing frozen algorithm exactly; no new
validator behavior is specified or required beyond processing one
additional enumerated path.

**No caller-supplied HBDC digest (item 33, reaffirmed).** Exactly as
HMIC-REQ-054/058 already forbid for every other frozen file, no future
validator or admin surface may accept a caller-supplied
`implementation_scope_digest` value, `HBDC-001` digest, or any per-file
override — the digest is always internally, freshly re-derived from
live working-tree bytes at computation time. This repair introduces no
exception to that existing, contract-wide rule.

**Admin ceremony consequence (item 34, contractual, not implemented
here).** A future `certify` ceremony (`scripts/hatp_certification_
admin.py`) derives `HBDC-001`'s content contribution to
`implementation_scope_digest` fresh from live bytes at ceremony time,
identically to every other HMIC-REQ-050 entry — no authority argument,
no caller-supplied digest or version string for `HBDC-001` specifically,
mirrors the existing rule this repair does not change.

**Requirement / invariant / attack-matrix counts after repair.**
Requirement IDs remain exactly `HMIC-REQ-001`–`HMIC-REQ-145` (145 total,
no renumbering, no new ID minted) — HMIC-REQ-050/052/053/069/145 were
revised in place, following the identical in-place-revision precedent
§49/§50/§51 already established. CIVC invariants remain exactly
`CIVC-1`–`CIVC-12` (12 total, unchanged in count) — `CIVC-5` was
strengthened in place to state the uniform five-member dual-binding
consequence; no invariant was added or removed. The attack matrix grows
from 36 to **37** rows: one genuinely new row was added — #37 (HBDC
same-version content-drift, now rejected) — because no pre-existing row
addressed the *now-closed* content-drift case with its own expected
result; attack #35 was revised in place (its same-version-exception
clause now points to #37 instead of restating the closed gap); attack
#36 is unaffected (a `contract_versions`-only concern, orthogonal to
`implementation_scope_digest` membership).

**Certification-artifact schema and other cross-cutting confirmations —
identical structure to §51's own "unchanged, confirmed" findings,
independently re-verified here, not merely copied:** schema versions
unchanged (above); `HMIC-REQ-063`/Option-C text byte-unchanged by this
repair (`grep` of §35/HBDC-001 §14 confirms zero diff); `HBDC-001`
itself byte-unchanged (`git status --porcelain docs/contracts/
HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` empty throughout); the other three
frozen corpus members this phase does not touch (`RWMPC-001`,
`PBPA-001`, `PBPC-001`) byte-unchanged; no `src/pcae/**` or `scripts/**`
file modified.

**Existing four contracts' protections — preserved, not weakened
(item 37 of the governing phase instruction).** `HMRC-001`, `HATP-001`,
`HSCE-001`, `RAE-001` retain the identical dual binding they already
had — their positions within HMIC-REQ-050's enumeration, their digest
inputs, and HMIC-REQ-053's redundancy rule are all byte-identical before
and after this repair; only `HBDC-001`'s document was added, at the end
of the `docs/contracts/` sub-list, immediately before
`scripts/hatp_certification_admin.py`. No existing file's position,
inclusion, or exclusion changed.

**Bound-contract completeness — HBDC remains mandatory, no legacy path
(item 38).** `contract_versions`' five-member requirement (HMIC-REQ-067)
is unchanged by this repair; no four-member legacy path is introduced or
revived. `implementation_scope_digest`'s new twenty-five-file
requirement (HMIC-REQ-050) is, identically, "no more, no fewer" — no
twenty-four-file legacy path is introduced or revived either.

HMIC-REQ-063 remains unaffected, not solved (item 39): this repair
concerns normative-contract semantic drift for a `contract_versions`
member's *document*, not executed-source provenance or import-shadowing.
HMIC-REQ-063's own text is byte-unchanged; it remains a named, disclosed,
unsolved residual limitation, exactly as it was before this repair and
exactly as §51 already confirmed for the 149O.20D amendment.

**Option C / Model-A environment-lock condition — unchanged (item 40).**
This repair does not touch HBDC-001 §13's environment-lock condition or
HMIC-REQ-063's Option-C conditional-acceptance branch; both remain
exactly as conditional as 149O.20A/149O.20C/149O.20D (§51) established.
No unconditional acceptance is introduced.

**Class-B implementation-coverage findings — retained, not repaired
here (item 41).** The ACL/effective-group verifier gap, full
ancestor-chain verifier gap, hard-link verifier gap, and the remaining
149O.20C non-blocking implementation findings are unaffected by this
contract-only repair phase and remain open for a future implementation
phase; this phase does not attempt to close them.

**W-1 — unaffected, not reopened or conflated (item 42).** `W-1` (§50)
concerns binding the HMIC validator/admin-writer *source files*
(`core/hatp_mandatory_certification.py`, `scripts/hatp_certification_
admin.py`) into `implementation_scope_digest` — a source-implementation-
scope question, already resolved at the contract level, independent
verification still pending from 149O.19.5E.2 onward. This repair's own
new enumeration entry is a *contract-document* addition, not a
source-implementation addition; it does not touch, narrow, or widen
`W-1`'s own scope, and this repair does not conflate the two the way the
governing phase instruction explicitly cautions against (item 42 there).

**HBDC-BINDING-GATE status.** Using this repository's own gate-naming
convention: **HBDC-BINDING-GATE: CONTRACT CONTENT-BINDING REPAIR
COMPLETE — INDEPENDENT VERIFICATION PENDING — PRODUCTION ALIGNMENT
PENDING.** Not CLOSED. Updated from 149O.20D's own three-part status
(§51: "CONTRACT-LEVEL EVOLUTION COMPLETE — INDEPENDENT CONTRACT
VERIFICATION PENDING — PRODUCTION FIVE-MEMBER `contract_versions`
ALIGNMENT PENDING") to reflect that the content-identity binding gap
149O.20D left open is now itself repaired at the contract level, while
both of 149O.20D's own open facts remain open, joined by a third: (A)
this contract now binds `HBDC-001`'s content bytes into
`implementation_scope_digest`, closing B-149O.20D-1 at the contract
level (this section); (B) an independent verification phase must confirm
this repair is correct — sound, minimal, honestly disclosed, and that
it does not weaken the existing four contracts' protections — before it
may be relied upon (next phase, below); (C) `core/hatp_mandatory_
certification.py`'s own `_FROZEN_AUTHORITY_BEARING_FILES` constant still
implements the pre-repair twenty-four-file enumeration, and its
`_CONTRACT_IDENTITY_FILES` constant still implements the pre-149O.20D
four-member `contract_versions` set — both were **not** modified by this
phase; a dedicated, bounded future implementation-alignment phase must
update both to the verified twenty-five-file/five-member sets, and that
alignment must itself be independently verified, before Class-B
provisioning planning may be considered.

**W-1 / B-149O.19.3-1 status — unaffected, not reopened.** Both remain
exactly as §49/§50/§51 left them, untouched by this phase, using a
distinct identifier space from this phase's own **B-149O.20D-1** and
**HBDC-BINDING-GATE** identifiers.

**Contract-repair verdict.** **HMIC-001 v1.2: FROZEN — HBDC BOUND-
CONTRACT IDENTITY EVOLUTION COMPLETE, CONTENT-IDENTITY BINDING REPAIRED
— PENDING INDEPENDENT VERIFICATION.** Not `VERIFIED`. **B-149O.20D-1:
REPAIRED AT CONTRACT LEVEL — INDEPENDENT VERIFICATION PENDING — NOT
CLOSED** (only an independent re-verification phase may close it, per
this repository's own B-149O.19.3-1/§49 precedent). **HBDC binding
gate: CONTRACT CONTENT-BINDING REPAIR COMPLETE — INDEPENDENT
VERIFICATION PENDING — PRODUCTION ALIGNMENT PENDING.** **Class-B:
CONTRACT VERIFIED — NOT PROVISIONED** (149O.20C's own verdict, unchanged
by this phase). **HATP production: NOT READY.**

**Recommended next phase.** **149O.20E — HMIC v1.2 HBDC Bound-Contract
Identity Independent Verification** (or repository-conventional
equivalent, unchanged in name from 149O.20D's own recommendation, §51),
whose scope must now additionally include independent verification of
this repair: independently re-confirm B-149O.20D-1's pre-repair defect
from the 149O.20D contract snapshot (not erased, preserved in git
history); independently re-derive that Option B (digest-set extension)
is the correct, sufficient, minimal repair, not merely accept this
section's own analysis; independently test that a same-version
`HBDC-001` content mutation changes `implementation_scope_digest` and
would invalidate a certification bound to the pre-mutation value;
independently verify version-drift and Contract-ID-drift detection
remain intact; independently verify the other four bound contracts'
protections are unweakened; independently verify the twenty-five-file
`implementation_scope_digest` enumeration and five-member
`contract_versions` set; independently verify HMIC-REQ-063/Option-C
remain preserved, not solved; independently verify production remains
intentionally, fail-closed-ly stale at the pre-repair twenty-four-file/
four-member sets; and confirm no real provisioning/certification/
activation occurred. If 149O.20E passes (now covering both the 149O.20D
amendment and this repair), the next phase after it remains the bounded
implementation-alignment phase 149O.20D already recommended (§51,
suggested name `149O.20F`), updating both `_FROZEN_AUTHORITY_BEARING_
FILES` and `_CONTRACT_IDENTITY_FILES` to their verified twenty-five-file/
five-member sets, followed by that alignment's own independent
verification. Only after both complete may Class-B provisioning planning
be considered — not recommended directly by this phase.

**No production or upstream-contract change (restated).** No
`src/pcae/**` or `scripts/**` file was modified by this repair. Only
`HMIC-001` changed among the now-nine-contract total frozen corpus;
`HBDC-001` v1.0 itself remained byte-unchanged throughout this repair —
its inclusion in `implementation_scope_digest` is achieved entirely by
naming its existing path inside `HMIC-001`'s own HMIC-REQ-050
enumeration, requiring zero edits to HBDC-001's own document. `HMRC-001`
v1.0, `HATP-001` v1.0, `HSCE-001` v1.1, `RAE-001` v1.0, `RWMPC-001`
v1.0, `PBPA-001` v1.0, and `PBPC-001` v1.2 all remain byte-unchanged.
The existing four-member `contract_versions` production implementation
(`_CONTRACT_IDENTITY_FILES`) and the existing twenty-four-file
`implementation_scope_digest` production implementation
(`_FROZEN_AUTHORITY_BEARING_FILES`) were **not** updated by this phase
— that remains an intentional, disclosed, future-phase obligation
(149O.20F), not an oversight, now covering one additional dimension
(digest file count) beyond what 149O.20D's own disclosed divergence
(`contract_versions` member count) already named. `hatp_mandatory_
cutover.py` was not modified by this phase and gained no new import or
call. No certification artifact, Active-Certification Pointer, or
revocation record was created anywhere on this host. No Cutover Record
or activation marker was created or modified. No real `HATP_MANDATORY`
activation occurred. No Class-B provisioning occurred. No Permission
Broker behavior changed. `POL-005` remained unchanged. No `COMP-002`
capability was implemented. `W-1` and `B-149O.19.3-1` remain
independently closed/repaired exactly as §49/§50 left them, unchanged by
this phase. B-149O-1..4 remain independently closed at the system
implementation/enforcement boundary with deployment/operational
activation deferred, unchanged by this phase. HATP production remains
**NOT READY**. Runtime remains **Observed / observe / unavailable**.

---

## 53. Contract Amendment History — Phase 149O.20K (v1.3)

**Context.** By 149O.20J.8, the Class-B deployment-conformance verifier
island — `hatp_class_b_topology_verifier.py` (149O.20H/20I/20J.1-20J.8),
`hatp_environment_lock_verifier.py` (149O.20I), and
`hatp_class_b_conformance.py` (149O.20I) — was independently verified to
implement HBDC-001's Model-A topology and environment-lock checks
correctly, read-only, with zero production consumers, entirely outside
HMIC-001's frozen twenty-five-file identity. This left CBV-S1 open: the
verifier's own authority-sensitive source was not itself HMIC-bound, so
an edit to any of its three files could silently change the
`COMPLIANT`/`NON_COMPLIANT`/`INDETERMINATE` verdict a future certification
mechanism (HMIC-REQ-063's Option-C branch, named at v1.2 §51) would rely
on, without changing any digest HMIC-001 already computes. This section
records 149O.20K's independent derivation of the exact closure this gap
requires — contract evolution only, no production change.

**§53.1 Independent reconstruction of HMIC-REQ-052 (as it stood at
v1.2).** Before analyzing the verifier graph, 149O.20K re-read
HMIC-REQ-052 from this document directly (not from any prior phase's
summary). At v1.2, the closure rule bound a PCAE-owned file only if it
was reachable, transitively, from either (a)
`assess_hatp_mandatory_activation_readiness`'s own call graph, or (b)
`validate_active_hatp_mandatory_independent_verification_certification`'s
call graph or the Protected Admin ceremony functions in
`scripts/hatp_certification_admin.py`. Neither limb reaches the Class-B
verifier island: `verify_class_b_deployment_conformance` and its two
sub-verifiers are called from neither of those two call graphs anywhere
in production (confirmed by direct source search, §53.4). Under the
v1.2 text alone, the three verifier files are therefore *not* bound by
HMIC-REQ-052 — not an oversight in the v1.2 text (it correctly closed
what was reachable from the readiness/certification call graphs that
existed at v1.2), but a genuine scope gap relative to a verifier island
that exists and is authority-sensitive but has no consumer yet. This is
exactly why a new limb is required rather than a re-application of
limbs (a)/(b): those limbs are reachability-based, and the Class-B
island is, by design (§53.3), currently reachable from neither.

**§53.2 Independent reconstruction of the current 25/5 identity.** Read
directly from `src/pcae/core/hatp_mandatory_certification.py`:
`_FROZEN_SRC_PCAE_RELATIVE_FILES` (19 entries) +
`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` (6 entries, the five bound
contract documents plus `scripts/hatp_certification_admin.py`) =
`_FROZEN_AUTHORITY_BEARING_FILES`, asserted `len(...) == 25` in the
module itself (a live runtime self-check, not merely a comment).
Compared entry-for-entry against this document's own pre-amendment
HMIC-REQ-050 text: identical, in the same order, confirming production
and contract were already in alignment at 25/5 before this phase (as
149O.20F/149O.20G established and 149O.20J.8's own reconfirmation
restated). `_CONTRACT_IDENTITY_FILES` independently read: exactly five
`(contract_id, path)` pairs — `HMRC-001`, `HATP-001`, `HSCE-001`,
`RAE-001`, `HBDC-001` — matching HMIC-REQ-067. Both sets recorded here
as the pre-amendment baseline this phase widens from.

**§53.3 Fresh static dependency graph — the three verifier modules.** An
`ast`-based import walk (`ast.parse` + `ast.walk` for `Import`/
`ImportFrom` nodes) was run independently against the current on-disk
bytes of all three modules, not against any prior phase's dependency
list. Results:

- `hatp_class_b_topology_verifier.py`: `from pcae.core import
  hatp_bootstrap`; everything else is standard library (`ast`,
  `inspect`, `os`, `re`, `stat`, `subprocess`, `sys`, `dataclasses`,
  `enum`, `pathlib`, `typing`, `grp`, `pwd`). No dynamic
  (`importlib.import_module`/`__import__`) PCAE-owned import found by
  text search of the module.
- `hatp_environment_lock_verifier.py`: `from
  pcae.core.hatp_class_b_topology_verifier import (ClassBCheckResult,
  ClassBDeploymentVerificationResult, _ancestor_chain_safe,
  _build_result, _current_agent_identity, _effective_write_access,
  _resolve_trusted_executable_with_effective_access, _safe_check)` —
  i.e. it imports symbols from the sibling verifier module, not a
  fourth PCAE module; everything else is standard library
  (`importlib.metadata`, `importlib.util`, `os`, `site`, `sys`,
  `pathlib`, `typing`, `shutil.which`).
- `hatp_class_b_conformance.py`: `from pcae.core import hatp_bootstrap`,
  `from pcae.core import repository_identity`, `from
  pcae.core.hatp_class_b_topology_verifier import (...)`, `from
  pcae.core.hatp_environment_lock_verifier import
  verify_environment_lock_conformance, _current_agent_identity`, `from
  pcae.core.paths import HarnessPath`; everything else is standard
  library (`importlib.metadata`, `pathlib`, `typing`, `json`).

No fourth PCAE-owned module is reached by any import statement across
all three files. `hatp_bootstrap` and `repository_identity` are already
HMIC-REQ-050 members (§53.2's baseline). `pcae.core.paths` is not — see
§53.5.

**§53.4 Semantic dependency check and zero-consumer confirmation.** Text
search of all of `src/` for `hatp_class_b_topology_verifier`,
`hatp_environment_lock_verifier`, `hatp_class_b_conformance`,
`verify_class_b_deployment_conformance`,
`verify_class_b_topology_conformance`, and
`verify_environment_lock_conformance`, excluding the three files
themselves, returned zero matches: no production module — not
`hatp_mandatory_cutover.py`, not `hatp_mandatory_certification.py`, not
`scripts/hatp_certification_admin.py`, not any readiness/certification/
activation/Permission-Broker code — imports or calls into the verifier
island. `hatp_mandatory_cutover.py` and `human_approval_trusted_
provenance.py` were separately confirmed to reference only the
string/concept "Class-B" (e.g. `class_b_protected_storage_available`,
`class_b_bootstrap_environment_safe`) for pre-existing, unrelated
readiness terms (CBV-S10's own gap) — neither imports or calls any of
the three verifier modules' symbols. No hidden or parallel Class-B
decision logic exists elsewhere in production capable of computing a
materially equivalent topology/environment-lock/conformance result
outside the three declared modules. This reconfirms the precondition
CBV-S1's current safety already depends on (verifier unbound, consumers
zero) and confirms this phase introduces no new consumer.

**§53.5 Dependency classification.** Every dependency reached by §53.3's
walk is classified:

- **Category A (PCAE-owned, authority-sensitive — bind).** The three
  root modules themselves. Each can independently alter the final
  `COMPLIANT`/`NON_COMPLIANT`/`INDETERMINATE` verdict:
  `hatp_class_b_topology_verifier.py` computes agent identity, mode/
  group/ACL write-access resolution (Linux and macOS ACL parsing),
  Trusted-Git and Protected-Root ancestor-chain resolution, symlink/
  hard-link safety, and the eleven topology sub-checks whose aggregate
  feeds `verify_class_b_topology_conformance`;
  `hatp_environment_lock_verifier.py` re-exports and extends that
  module's identity/ACL primitives to compute interpreter-writability,
  venv-lock, `PYTHONPATH`/user-site/`.pth`/meta-path/module-origin/
  editable-install/launcher/shell-environment-injection/third-party-
  boundary checks; `hatp_class_b_conformance.py` is the aggregator
  (§53.6) that combines both sub-verifiers' results plus its own two
  additional checks (`_check_model_a_deployment`,
  `_check_deployment_identity`) into the single exported verdict. A
  byte edit to any of the three — e.g. reclassifying a dangerous ACL
  right as safe, short-circuiting an ancestor-chain walk, or flipping
  an aggregator branch — changes that verdict without changing any
  pre-v1.3 HMIC-bound digest. This is precisely HMIC-REQ-052(a)'s
  authority-sensitivity test, applied under new limb (c) rather than
  limb (a) because the island is not (yet) reachable from
  `assess_hatp_mandatory_activation_readiness`.
- **Category B (PCAE-owned, non-authority-sensitive — exclude).**
  `pcae.core.paths` (`HarnessPath`), imported once by
  `hatp_class_b_conformance.py` and used only as a lightweight
  filesystem-path value type (`root.path`, `HarnessPath.cwd()`) — it
  carries no ACL, identity, or verdict-affecting logic of its own. This
  is the identical exclusion HMIC-REQ-052's own text already names for
  limb (a) (§49) and limb (b) (§50); this phase reapplies the same
  precedent under limb (c) rather than inventing a new exception.
  `hatp_bootstrap.py` and `repository_identity.py` are PCAE-owned and
  genuinely authority-sensitive, but require no new binding decision:
  both are already HMIC-REQ-050 members via limb (a) (§49's own
  transitive-completeness table), so limb (c) contributes nothing new
  for them — they remain bound, for the reason already on record, not a
  new one.
- **Category C (standard library — do not bind, disclose residual
  trust).** `ast`, `inspect`, `os`, `re`, `stat`, `subprocess`, `sys`,
  `dataclasses`, `enum`, `pathlib`, `typing`, `grp`, `pwd`,
  `importlib.metadata`, `importlib.util`, `site`, `shutil`. Not
  HMIC-bindable, per HMIC-REQ-065 (already frozen, unchanged): the
  Python interpreter and its standard library are named there as an
  explicit, out-of-scope transitive-dependency boundary. Residual trust
  in the interpreter/stdlib's own correctness is unchanged by this
  phase and remains disclosed, not silently assumed away.
- **Category D (external/system tools — relate to HBDC, do not
  overclaim as HMIC-solvable).** `git` (resolved via
  `_resolve_trusted_executable`/`_resolve_trusted_executable_with_
  effective_access`), the `ls`-based macOS ACL text format the topology
  verifier parses (`subprocess.run` calls at lines 193/354 of
  `hatp_class_b_topology_verifier.py`), the `pcae` launcher resolved via
  `shutil.which` in the environment-lock verifier, the Python
  interpreter binary itself, and the underlying filesystem/kernel ACL
  subsystem. None of these can be brought into HMIC-REQ-050's scope by
  naming a PCAE source file — HMIC source-set membership binds bytes
  PCAE owns, not external binaries or kernel behavior. These remain
  HBDC-001's own environment-lock/deployment-model assumptions (already
  the subject of HMIC-REQ-067's v1.2 `contract_versions` binding, §51)
  and HMIC-REQ-063's already-named residual limitation (import-shadowing/
  executed-code binding is out of scope for `implementation_scope_
  digest`, which binds on-disk bytes only). This phase does not
  overclaim HMIC as runtime cryptographic provenance, and does not treat
  the environment lock as anything stronger than deployment conformance.
- **Category E (contract/document inputs).** Neither
  `hatp_class_b_topology_verifier.py` nor `hatp_environment_lock_
  verifier.py` nor `hatp_class_b_conformance.py` reads any
  `docs/contracts/**` document's bytes at runtime (confirmed: no
  `open(`/`read_text(` call against a `docs/contracts` path in any of
  the three files; the sole `Path(__file__).read_text(...)` call, in
  `_own_source_ast`, reads the topology verifier's own source for its
  self-scanning admin-inference/forbidden-attribute checks, not a
  contract document). `HBDC-001`'s normative text informed these
  modules' human-authored implementation but is not a runtime
  dependency of them. `HBDC-001` is already bound into both
  `implementation_scope_digest` (HMIC-REQ-050's twenty-fifth entry,
  §52) and `contract_versions` (HMIC-REQ-067, §51) — this phase does not
  duplicate that binding.

**§53.6 Aggregator and sub-verifier semantics (worked, not assumed).**
`hatp_class_b_conformance.py::verify_class_b_deployment_conformance`
calls `verify_class_b_topology_conformance()`,
`verify_environment_lock_conformance()`, `_check_model_a_deployment`,
and `_check_deployment_identity`, then folds all four results through
the shared `_aggregate_status`/`_build_result` primitives (imported from
the topology module, not reimplemented) to produce the single exported
`ClassBDeploymentVerificationResult`. Every one of the four inputs can
independently drive the aggregate away from `COMPLIANT` — there is no
leaf-only assumption here: the aggregator's own two additional checks
(`_check_model_a_deployment`, using `repository_identity`/
`hatp_bootstrap` to confirm live agent identity and Protected-Root
trust-store resolution; `_check_deployment_identity`, using
`hatp_bootstrap.resolve_canonical_deployment_root`/`repository_identity.
read_repository_identity`/`hatp_bootstrap.deployment_binding_matches`)
are themselves authority-sensitive and are covered by
`hatp_class_b_conformance.py`'s own Category-A membership (§53.5), not
by a separate binding.
`hatp_environment_lock_verifier.py::verify_environment_lock_conformance`
was independently traced for every PCAE-owned dependency capable of
affecting executable-source identity, `.pth` evaluation, environment
paths, editable-install checks, or fail-closed state: all such logic is
local to the module itself or imported from the topology verifier
(§53.3) — no third PCAE module is reached.
`hatp_class_b_topology_verifier.py::verify_class_b_topology_conformance`
was independently traced for every PCAE-owned dependency capable of
affecting agent identity, mode/group/ACL rights, Trusted-Git resolution,
Protected-Root topology, ancestor-chain semantics, symlink handling, or
error handling: all thirty-nine of its top-level `def`s are local to the
module (confirmed by direct `grep -n "^def "` inventory); the module is
genuinely self-contained apart from its one `hatp_bootstrap` import
(already bound).

**§53.7 A literal duplicate, not an import (self-binding/cycle check).**
`hatp_environment_lock_verifier.py` defines
`_AUTHORITY_MODULE_RELATIVE_PATHS`, a nineteen-entry tuple of plain path
strings, reproduced by hand from HMIC-REQ-050's `src/pcae/`-relative
bucket, used only by `_check_module_origin_containment` (HBDC-REQ-034).
Its own comment states this explicitly: it is *not* imported from
`hatp_mandatory_certification.py::_FROZEN_SRC_PCAE_RELATIVE_FILES`
"since that would make this diagnostic-only module a runtime dependent
of an already-HMIC-bound file for no authority reason." Independently
confirmed by import-graph inspection: neither
`hatp_mandatory_certification.py` nor `scripts/hatp_certification_
admin.py` imports any of the three Class-B verifier modules, and none of
the three verifier modules imports either of those two files (only the
string literal `"core/hatp_mandatory_certification.py"` appears inside
`_AUTHORITY_MODULE_RELATIVE_PATHS`, a data value, not a Python `import`
statement — confirmed by AST walk finding zero `Import`/`ImportFrom`
nodes naming `hatp_mandatory_certification` or
`hatp_certification_admin` in any of the three files, §53.3). No HMIC
validator/admin self-reference, no digest-construction cycle, no
Class-B-verifier→HMIC-verifier→Class-B-verifier recursion, no contract-
identity cycle, and no certification-dependency cycle is introduced by
binding the three verifier files. W-1 (§50) is not reopened: this
finding does not disturb the assumptions under which W-1 was closed
(that closure concerned `hatp_mandatory_certification.py`/
`hatp_certification_admin.py` binding themselves into their own digest,
a distinct file pair from this phase's three, with no import
relationship between the two pairs in either direction). The static
import graph (§53.3) and the semantic authority-dependency graph
(§53.5-53.6) agree: no dependency reached by the semantic walk exceeds
what the static import graph already shows, and no cycle exists in
either.

**§53.8 Regression: B-149O.19.3-1 and B-149O.20D-1.** Independently
re-confirmed, by the same direct read used in §53.2, that
`hatp_providers.py`, `hatp_fido2_provider.py`, `hatp_piv_provider.py`,
and `hatp_hardware_credentials.py` (B-149O.19.3-1's four repair entries)
remain present, unremoved, and unmodified by this phase in
`_FROZEN_SRC_PCAE_RELATIVE_FILES`; and that
`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (B-149O.20D-1's
repair entry) remains present, unremoved, and unmodified by this phase
in `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`, still receiving both the
`contract_versions` version-header binding (HMIC-REQ-067/069) and the
`implementation_scope_digest` content binding (HMIC-REQ-050/053). This
phase edits only this contract document (`HMIC-001` itself); it does not
touch `src/pcae/core/hatp_mandatory_certification.py`, so neither
provider-source closure nor HBDC content-identity binding is weakened,
narrowed, or bypassed by this amendment.

**§53.9 Over-binding check.** The criterion applied throughout §53.5 was
authority-sensitive dependency, not "everything transitively imported."
`pcae.core.paths` was inspected and excluded (Category B) precisely to
avoid over-binding a genuinely inert utility type. No PCAE-owned file
beyond the three root modules was found reachable at all (§53.3), so
there was no broader candidate set to prune from — the three-file result
is not a default ceiling, it is the complete outcome of the walk.

**§53.10 Threat analysis — incomplete binding.** If
`hatp_class_b_topology_verifier.py` were omitted from the widened set,
an ACL/mode/ancestor-chain edit there could change
`verify_class_b_topology_conformance`'s result, which
`hatp_class_b_conformance.py` (itself bound) folds into the aggregate —
but `hatp_class_b_conformance.py`'s own digest-bound bytes would be
unchanged (it calls the topology module, it does not embed its bytes),
so the aggregate verdict could change while every *bound* file's digest
stayed identical: closure would be violated. The identical argument
applies to omitting `hatp_environment_lock_verifier.py` (reached via the
aggregator's second call) or `hatp_class_b_conformance.py` itself
(omitting the aggregator would leave the two sub-verifiers bound but the
combination logic — including its own two additional checks, §53.6 —
unbound, so an aggregator-level edit, e.g. flipping how `INDETERMINATE`
is decided, would be invisible). No transitive PCAE-owned helper was
found omitted (§53.3-53.4 found none beyond the three roots and the
already-bound/already-excluded set), so this threat class is fully
closed for the current source tree by binding exactly these three
files.

**§53.11 Threat analysis — over-binding.** Binding `pcae.core.paths`
(rejected, §53.5/§53.9) would have added digest volatility and
recertification churn for a file with no authority-relevant content —
any future editable-install refactor touching that module's non-
authority code would force recertification for no security benefit.
Binding `git`, `ls`, or the interpreter itself (impossible in any case,
Category D/C) would misrepresent HMIC as covering environment/kernel
assumptions it structurally cannot cover, contradicting HMIC-REQ-065/066's
own no-overclaim discipline. The three files actually bound are the
minimal set the semantic walk identified as capable of altering the
verdict; no additional file was added merely because it was nearby in
the module graph.

**§53.12 CBV-S1 status — restated, not closed.** This amendment widens
the *contract's* closure rule and enumeration. It does not implement,
consume, or wire the Class-B verifier's result into any readiness,
certification, or activation code path (§53.4 reconfirms zero
consumers); it does not update
`_FROZEN_AUTHORITY_BEARING_FILES`/`_CONTRACT_IDENTITY_FILES` in
`hatp_mandatory_certification.py` (still 25/5 after this phase); and it
creates no certification, binding, or revocation record. **CBV-S1: OPEN
— HMIC SOURCE-SCOPE CONTRACT EVOLVED — PRODUCTION SOURCE-SET ALIGNMENT
AND INDEPENDENT VERIFICATION PENDING — NOT CLOSED.** Only a future
production-alignment phase (updating the live constants to the verified
twenty-eight-file set, mirroring 149O.20F's own precedent for the
twenty-five-file alignment) followed by that alignment's own independent
verification (mirroring 149O.20G) can move CBV-S1 further; even then,
CBV-S1 remains open until a further, separately-governed phase actually
wires `verify_class_b_deployment_conformance`'s result into
`assess_hatp_mandatory_activation_readiness` or an equivalent
certification input (HMIC-REQ-063 Option-C), which this phase explicitly
does not attempt, authorize, or imply.

**§53.13 Contract-version determination.** This amendment widens
HMIC-REQ-050's enumeration (25 → 28 entries) and adds a new limb (c) to
HMIC-REQ-052's closure rule — normative-scope changes of the same shape
as the v1.0 → v1.1 amendment (§50, which widened HMIC-REQ-050/052 by
adding limb (b) and two files), not the shape of a within-version repair
like 149O.20D.1's same-version HBDC-001 gap closure (§52, which repaired
a disclosed limitation without changing what limb applied). No existing
requirement's meaning is narrowed, no existing consumer's expectation
(HMIC-REQ-069's version-drift detection, HMIC-REQ-059/061/062's
missing/symlink/non-regular-file handling, HMIC-REQ-054-058's digest
algorithm) is broken — every prior mechanism continues to apply
unmodified to a longer file list. Following this repository's own
established minor-bump convention for scope-widening amendments (v1.0 →
v1.1 at §50, v1.1 → v1.2 at §51), this amendment is `HMIC-001 v1.2 →
v1.3`, an in-place minor version bump, not v2.0 (no existing field,
schema, or algorithm is redefined or removed) and not a same-version
repair (unlike §52, this is a scope addition, not a defect fix in an
existing binding).

**§53.14 Verdict.** HMIC-001 v1.3: contract-evolved, not yet
independently verified. Closure limb (c) added to HMIC-REQ-052;
HMIC-REQ-050 widened to twenty-eight files; `contract_versions`
(HMIC-REQ-067) unchanged at five members — no new contract document is
introduced by this phase, and `HBDC-001` remains the sole v1.2 addition
there. `HBDC-001` itself (`docs/contracts/HATP_CLASS_B_DEPLOYMENT_
CONTRACT.md`) is unchanged by this phase — the strong expectation of
§17/§51 (no HBDC amendment for HMIC trust-binding work) holds; this is
HMIC-side binding of a verifier that already implements HBDC-001, not a
rewrite of HBDC-001 to ease that binding. Zero production consumers of
the Class-B verifier island remain (§53.4). Production
`_FROZEN_AUTHORITY_BEARING_FILES`/`_CONTRACT_IDENTITY_FILES` remain
25/5, unaligned to this contract's new 28/5 target, intentionally and
disclosed-ly (§53.12), mirroring the identical contract-ahead-of-
production sequencing already established at v1.1 (§50, attacks #33/#34)
and v1.2/149O.20D.1 (§52, attacks #36/#37). `W-1`, `B-149O.19.3-1`, and
`B-149O.20D-1` remain independently closed/repaired exactly as
§49/§50/§52 left them (§53.8). CBV-S1 remains **OPEN — HMIC SOURCE-SCOPE
CONTRACT EVOLVED — PRODUCTION ALIGNMENT + INDEPENDENT VERIFICATION
PENDING — NOT CLOSED**. CBV-S10 (readiness contract/integration gap) is
untouched by this phase. Class-B: **CONTRACT VERIFIED — VERIFIER REPAIR
LINE INDEPENDENTLY VERIFIED — HMIC SOURCE-SCOPE CONTRACT EVOLVED —
PRODUCTION ALIGNMENT PENDING — NOT PROVISIONED**. HATP production
remains **NOT READY**. Runtime remains **Observed / observe /
unavailable**.

**Recommended next phase.** **149O.20K.1 — HMIC Class-B Verifier
Source-Scope Contract Independent Verification**, which must
independently reconstruct, without trusting this section's narrative:
HMIC-REQ-052 (pre- and post-amendment text); the current 25/5 production
identity; the Class-B verifier dependency graph (static and semantic);
the authority-sensitive/excluded classification (§53.5); the target
twenty-eight-file set; the v1.2 → v1.3 version-bump rationale; the
cycle/self-binding analysis (§53.7); the W-1/B-149O.19.3-1/B-149O.20D-1
regression (§53.8); and HBDC-001 identity preservation. 149O.20K.1 does
not authorize production alignment or readiness integration; only after
it passes may a future, separately-governed production-alignment phase
(updating `_FROZEN_AUTHORITY_BEARING_FILES` to the verified
twenty-eight-file set) and its own independent verification proceed —
in that order, not out of it.

---

## 54. Contract Repair History — Phase 149O.20L.1A (Finding B-149O.20L.1-1)

**Status of this section:** descriptive/historical record of the
repair; it introduces no new `HMIC-REQ-###` identifier, narrows no
existing requirement, and amends no other section's normative force.
The only change this phase made outside this section is the header
block (Status line, new `Repaired by` line, and the `Depends on` line)
at the top of this document.

**Finding.** Phase 149O.20L.1 amended `HMRC-001` from v1.0 to v1.1
(repairing HMRC-REQ-054's six-vs-seven drift and adding
HMRC-REQ-086-100). That phase did not touch `HMIC-001` (explicitly out
of its scope, disclosed in its own report). Immediately following that
amendment, this document's own header "Depends on" line (formerly
labeled "unamended, byte-unchanged," formerly naming HMRC-001's version
as 1.0) became a false statement: `HMRC-001` had in fact been amended (by a
different phase) and was no longer byte-unchanged since this document's
v1.3 freeze. This descriptive-header staleness is recorded as
**B-149O.20L.1-1**.

**§54.1 Pre-repair state, independently reproduced.** Read directly,
not assumed from the governing phase brief: `docs/contracts/
HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`'s own Version header
field read the value one-point-one, and its own Status header field
read `FROZEN — FULL-HBDC CLASS-B READINESS CONTRACT EVOLVED (149O.20L.1)
— PENDING INDEPENDENT CONTRACT VERIFICATION (not VERIFIED at v1.1)`.
This document's (pre-repair) header line 12 read `HMRC-001 v1.0,
HATP-001 v1.0, HSCE-001 v1.1, RAE-001 v1.0, HBDC-001 v1.0`. The
divergence — `1.0` claimed, `1.1` live — was confirmed directly against
both files' live bytes before any edit was made this phase.

**§54.2 Pre-149O.20L.1 baseline, independently reconstructed.** At the
true 149O.20L.1 phase-entry commit (`f14e524e`), `HMRC-001`'s live
header read `**Version:** 1.0`, matching this document's then-current
`Depends on` line exactly — the two were consistent at that commit.
This confirms the divergence is a direct, sole consequence of
149O.20L.1's HMRC-001 amendment landing after this document's v1.3
freeze (149O.20K), not a pre-existing defect and not evidence that
149O.20K, 149O.20K.1, 149O.20K.2, or 149O.20K.3 were ever inconsistent
when completed.

**§54.3 Normative-mechanism check (Outcome B confirmed).** HMIC-REQ-067
(§20) itself names `HMRC-001` as a `contract_versions` family member by
Contract ID only — it contains no version-number literal for `HMRC-001`
anywhere in its normative text. HMIC-REQ-069 (§20) independently
requires `contract_versions` validation to compare "each ... entry ...
against the named contract's own current, live version header" — i.e.
the contract's own normative mechanism is designed to track the live
document dynamically, never to freeze a version number in prose.
Production's `derive_contract_versions` (`core/hatp_mandatory_
certification.py`) was directly exercised against the live repository
this phase, before any edit: it returned `{"HMRC-001": "1.1", ...}` —
correctly reflecting the live v1.1 document, with no stale literal
anywhere in its implementation (`_CONTRACT_IDENTITY_FILES` stores
`(contract_id, path)` pairs, never `(contract_id, version)` pairs; the
version string is read fresh from each file's header on every call).
**Conclusion: Outcome B.** Neither HMIC-REQ-067's normative text nor
production's `derive_contract_versions` mechanism was ever stale;
`certification_id`/`contract_versions` computed today already correctly
reports `HMRC-001` as `1.1`. The sole defect was this document's own
descriptive `Depends on` header line — a summary field structurally
parallel to the `Version:`/`Status:` header fields above it, not a
normative requirement body, and not the same field as the illustrative,
deliberately non-synchronized four-member `contract_versions` example
under §14 (which has already been left un-updated in place across the
v1.2 and v1.3 amendments, an established prior disposition this phase
does not disturb).

**§54.4 Repair.** Updated only this document's header block (see the
top of this document): the `Status:` line now names this repair; a new
`Repaired by: Phase 149O.20L.1A` line was added; the `Depends on` line
was corrected to `HMRC-001 v1.1` (all other four members unchanged) and
its label reworded from `(unamended, byte-unchanged)` to `(current,
HMIC-unamended)` to remove the now-inaccurate byte-unchanged claim while
preserving the true claim that HMIC-001 itself did not amend any of the
five dependency contracts. `**Version:** 1.3` is unchanged — this is a
same-version repair, mirroring §52's (149O.20D.1) precedent: a
defect discovered post-freeze, corrected in place, with no widening or
narrowing of any `HMIC-REQ-###` requirement's meaning.

**§54.5 Scope discipline confirmed.** No `HMIC-REQ-###` text was added,
removed, or reworded. `HMIC-REQ-067`'s five-member `contract_versions`
family list is unchanged (`HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`,
`HBDC-001` — still five, same order). No `HMRC-001` byte was touched by
this phase (`HMRC-001` remains v1.1, exactly as 149O.20L.1 left it). No
Class-B verifier module was touched. `HMIC-001`'s own twenty-eight-file
source-scope target (§53) and production's current twenty-five-file/
five-contract identity are both unchanged by this repair — this phase
touched only this document's own header prose, nothing in §17
(HMIC-REQ-050/052/053) or §20 (HMIC-REQ-067/068/069/145). `verify_
class_b_deployment_conformance` remains uncalled by any readiness or
certification path; `hatp_mandatory_cutover.py` remains the unwired
seven-term production readiness vector. No certification, activation,
or Class-B provisioning occurred.

**§54.6 Verdict.** **B-149O.20L.1-1: REPAIRED — INDEPENDENT
VERIFICATION PENDING — NOT CLOSED.** `HMIC-001` remains v1.3. This
document's `Depends on` header now accurately states `HMRC-001 v1.1`,
matching both the live `HMRC-001` document and production's live
`derive_contract_versions` output. `CBV-S1` is unaffected and remains
exactly as §53.14 left it: **OPEN — HMIC SOURCE-SCOPE CONTRACT EVOLVED —
PRODUCTION ALIGNMENT + INDEPENDENT VERIFICATION PENDING — NOT CLOSED**.
`CBV-S10` is unaffected and remains **OPEN — READINESS CONTRACT
EVOLVED — HMIC CONTRACT-IDENTITY REALIGNMENT IN PROGRESS/COMPLETE —
INDEPENDENT READINESS CONTRACT VERIFICATION + PRODUCTION INTEGRATION
PENDING**. Class-B remains **NOT PROVISIONED**. HATP production remains
**NOT READY**. Runtime remains **Observed / observe / unavailable**.

**Recommended next phase.** **149O.20L.1B — HMRC-001 v1.1 HMIC
Contract-Identity Alignment Independent Verification**, which must
independently reconstruct, without trusting this section's narrative:
the pre-149O.20L.1 consistency (§54.2); the exact post-149O.20L.1
mismatch (§54.1); the Outcome-B determination that HMIC-REQ-067/069 and
`derive_contract_versions` were never themselves stale (§54.3); the
exact repair delta (§54.4); five-member `contract_versions` family
preservation; `HMRC-001` byte-identity at v1.1; the twenty-eight-file
source-scope and twenty-five/five production-identity regressions
(§53); zero readiness-path consumer of the Class-B verifier island; and
that production readiness remains the unwired seven-term vector. Only
after a clean 149O.20L.1B should the project return to **149O.20L.2 —
Full-HBDC Readiness Contract / Schema Independent Verification** — this
repair does not substitute for, and must not be used to skip, 149O.20L.2.

---

## 55. Contract Amendment History — Phase 149O.20L.7K (v1.4)

**Status of this section:** descriptive/historical record of the
149O.20L.7K contract-and-production amendment, appended without
modifying the original v1.0 freeze narrative (§0-48), §49-52's v1.0/
v1.1/v1.2 history, §53's v1.3 amendment, or §54's repair record.

**Context.** By 149O.20L.7J, the `DeploymentBinding` producer —
`core/hatp_deployment_binding_admin.py` (149O.20L.7I) and its sole
intended Protected Admin ceremony caller `scripts/hatp_deployment_
binding_admin.py` (149O.20L.7I) — was independently verified to
implement HBDC-001 v1.1's create/rotate/revoke ceremony correctly
(HBDC-REQ-056..070), with zero real invocations, entirely outside
HMIC-001's frozen twenty-eight-file identity (7J §31, its own named,
non-blocking-for-HBDC finding). This left that gap open: an edit to
either file could silently change what `DeploymentBinding` the
already-frozen `hatp_bootstrap.py`/`repository_identity.py` read path
accepts as authoritative, and therefore the Class-B deployment-
conformance verdict `hatp_class_b_conformance.py::_check_deployment_
identity` (HBDC-REQ-042) folds into its aggregate, without changing any
digest HMIC-001 already computes. This section records 149O.20L.7K's
independent derivation of the exact closure this gap requires —
contract amendment **and** production alignment in the same phase
(deliberately not split across a contract-then-alignment sequence the
way §53/149O.20K.2/149O.20K.3 were, since this phase's own governing
scope directs a single combined amendment).

**§55.1 Independent reconstruction of HMIC-REQ-052 (as it stood at
v1.3).** Before analyzing the producer, 149O.20L.7K re-read HMIC-REQ-052
from this document directly (not from 7J's summary). At v1.3, the
closure rule bound a PCAE-owned file only if reachable, transitively,
from: (a) `assess_hatp_mandatory_activation_readiness`'s own call graph;
(b) `validate_active_hatp_mandatory_independent_verification_
certification`'s call graph, or the Protected Admin ceremony functions
`certify`/`activate`/`revoke` in `scripts/hatp_certification_admin.py`;
or (c) `verify_class_b_deployment_conformance`'s own call graph. A
direct text search of `hatp_class_b_conformance.py` (the sole entry
point limb (c) names) confirms it imports `hatp_bootstrap`,
`repository_identity`, the topology/environment-lock verifier modules,
and `pcae.core.paths` only — it does **not** import `core/hatp_
deployment_binding_admin.py`, `scripts/hatp_deployment_binding_
admin.py`, or any symbol from either. None of limbs (a), (b), or (c) as
their v1.3 "specifically, any file reachable from ... call graph" text
literally reads reaches the producer or its admin script: the producer
is a separate write path, never imported by, and never importing, any
v1.3-bound entry point. Under the v1.3 text alone, the two files are
therefore *not* bound by HMIC-REQ-052 — not an oversight in the v1.3
text (it correctly closed what was reachable from the three named call
graphs that existed at v1.3), but a genuine scope gap of a different
shape than §53's: the Class-B verifier island lacked a call-graph
anchor entirely (§53.1); the DeploymentBinding producer has a call-graph
anchor that exists but does not reach it, because the producer
influences the verdict through the *data* it writes, not through being
called by the verifier. This is exactly why limb (c) required a second,
non-reachability anchor (mirroring limb (b)'s own dual-anchor
construction at v1.1, §50) rather than a fourth limb: the concern is the
same verdict limb (c) already names, reached by a different mechanism.

**§55.2 Independent reconstruction of the current 28/5 identity.** Read
directly from `src/pcae/core/hatp_mandatory_certification.py`, as it
stood immediately before this phase's own production edit:
`_FROZEN_SRC_PCAE_RELATIVE_FILES` (22 entries) + `_FROZEN_REPOSITORY_
ROOT_RELATIVE_FILES` (6 entries, the five bound contract documents plus
`scripts/hatp_certification_admin.py`) = `_FROZEN_AUTHORITY_BEARING_
FILES`, `assert`-pinned at exactly 28 in the module itself. Compared
entry-for-entry against this document's own pre-amendment HMIC-REQ-050
text: identical, in the same order, confirming production and contract
were already in alignment at 28/5 (149O.20K.2/149O.20K.3's own
established result) before this phase. `_CONTRACT_IDENTITY_FILES`
independently read: exactly five `(contract_id, path)` pairs —
`HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`, `HBDC-001` — matching
HMIC-REQ-067, unchanged target for this phase (§55.10). Both sets
recorded here as the pre-amendment baseline this phase widens from.

**§55.3 Fresh static dependency graph — the two producer files.** An
`ast`-based import walk (`ast.parse` + `ast.walk` for `Import`/
`ImportFrom` nodes) was run independently against the current on-disk
bytes of both files, not against 7J's or 7I's prior dependency
narrative. Results:

- `core/hatp_deployment_binding_admin.py`: `from pcae.core.hatp_
  bootstrap import (DeploymentBinding, HATPTrustStore,
  HATPTrustStoreError, HATPTrustStoreMalformedError,
  HATPTrustStoreSymlinkError, REGISTRY_SCHEMA_VERSION, _parse_registry_
  document, resolve_canonical_deployment_root)`, `from pcae.core.paths
  import HarnessPath`, `from pcae.core.provenance import append_
  provenance_event`, `from pcae.core.repository_identity import
  (RepositoryIdentityError, read_repository_identity)`; everything else
  is standard library (`fcntl`, `json`, `os`, `re`, `tempfile`,
  `contextlib`, `dataclasses`, `datetime`, `enum`, `pathlib`, `typing`).
  No dynamic (`importlib.import_module`/`__import__`) PCAE-owned import
  found by text search of the module.
- `scripts/hatp_deployment_binding_admin.py`: `from pcae.core.hatp_
  bootstrap import HATPTrustStoreError`, `from pcae.core.hatp_
  deployment_binding_admin import (AuthorityEvidence, ..., create_
  deployment_binding, preview_create_deployment_binding, preview_revoke_
  deployment_binding, preview_rotate_deployment_binding, revoke_
  deployment_binding, rotate_deployment_binding)` (the sixteen public
  names the script's `main` dispatches to), `from pcae.core.repository_
  identity import RepositoryIdentityError`; everything else is standard
  library (`argparse`, `sys`, `pathlib`, `typing`).

No third PCAE-owned module is reached by either file's import
statements beyond the pair being classified, `hatp_bootstrap`, `pcae.
core.paths`, `pcae.core.provenance`, and `repository_identity`.
`hatp_bootstrap` and `repository_identity` are already HMIC-REQ-050
members (§55.2's baseline). `pcae.core.paths` is not — see §55.5, same
disposition as §49/§53. `pcae.core.provenance` is not — see §55.5, a
disposition not previously worked in this contract's history.

**§55.4 Semantic dependency check and zero-consumer/zero-invocation
confirmation.** Text search of all of `src/` for `hatp_deployment_
binding_admin` (module name) and `create_deployment_binding`/`rotate_
deployment_binding`/`revoke_deployment_binding` (the three producer
entry points), excluding the two files themselves and their own test
modules, returned zero matches: no production module — not `hatp_
bootstrap.py`, not `hatp_class_b_conformance.py`, not `hatp_mandatory_
certification.py`, not `scripts/hatp_certification_admin.py`, not any
readiness/certification/activation/Permission-Broker code — imports or
calls into the producer. `hatp_class_b_conformance.py::_check_
deployment_identity` reads `DeploymentBinding` state via `HATPTrustStore.
load_repository_enrollment`/`hatp_bootstrap.deployment_binding_matches`
(both already-frozen `hatp_bootstrap.py` read primitives) — it does not
call the producer, confirming §55.1's "data dependency, not call-graph
dependency" characterization directly at the source. Separately
reconfirmed (mirroring 7J's own §31/§33): no real `DeploymentBinding`
has ever been created on any host by this producer — every prior test
of it, and every test added by this phase (§55.13), targets disposable
paths only.

*(Scope note added 149O.20L.7L.1, finding F-7L-1; see §56.1.)* This
section's "zero-consumer" finding is, and was always, scoped to the
`DeploymentBinding` **producer** (`create_deployment_binding`/`rotate_
deployment_binding`/`revoke_deployment_binding` and their admin-ceremony
caller) — it does not establish, and was never evidence for, any claim
about `verify_class_b_deployment_conformance` itself. §55.15 previously
cited this section alongside §53.4 as joint support for a broader "zero
production consumers of `verify_class_b_deployment_conformance`" verdict
sentence; that citation was inaccurate and is repaired at §55.15 and
§56.1 — `verify_class_b_deployment_conformance` already had a real
production readiness/activation consumer (`hatp_mandatory_cutover.py`,
wired by Phase 149O.20L.3) at the time this section was written. The
producer-level finding above is unaffected and remains correct.

**§55.5 Dependency classification.** Every dependency reached by
§55.3's walk is classified:

- **Category A (PCAE-owned, authority-sensitive — bind).** The two root
  files themselves. `core/hatp_deployment_binding_admin.py`'s
  `create_deployment_binding`/`rotate_deployment_binding`/`revoke_
  deployment_binding` each independently decide whether a
  `DeploymentBinding` write is `ALREADY_SATISFIED`, a fresh mutation, or
  a fail-closed rejection (`DuplicateConflictingBindingError`/
  `DeploymentBindingNotFoundError`/`DeploymentBindingRevokedError`), and
  what authority-bearing field values (`principal_id`, `signer_key_id`,
  `provider_profile`, `authority_scope`, `canonical_deployment_root`)
  the resulting record carries — a byte edit here (e.g. dropping the
  create-against-revoked fail-closed check, or widening the idempotency
  comparison to ignore `principal_id`) changes what `DeploymentBinding`
  state becomes durably active without changing any pre-v1.4 HMIC-bound
  digest. `scripts/hatp_deployment_binding_admin.py` is the sole
  production-intended caller of those three functions and constructs
  the `AuthorityEvidence` passed to them from raw CLI argument strings —
  a byte edit here (e.g. removing the `_prompt_confirm` gate, or
  silently defaulting a missing `--authority-scope`) changes what
  authority evidence reaches the producer without changing any pre-v1.4
  HMIC-bound digest either. This is precisely HMIC-REQ-052(c)'s
  authority-sensitivity test, applied under limb (c)'s new third anchor
  rather than its first (call-graph) anchor, because the producer pair
  is not reachable from `verify_class_b_deployment_conformance` (§55.1/
  §55.4).
- **Category B (PCAE-owned, non-authority-sensitive — exclude).**
  `pcae.core.paths` (`HarnessPath`) — the identical exclusion this
  contract's text already names for limb (a) (§49), limb (b) (§50), and
  limb (c)'s first anchor (§53); this phase reapplies the same
  precedent under limb (c)'s third anchor, not a new exception.
  `pcae.core.provenance` (`append_provenance_event`) — independently
  inspected: it appends an audit record to `.pcae/provenance-history.
  json` and is called strictly *after* the producer's own trust-store
  mutation and read-back verification already succeed (the producer's
  own documented ordering: validate → lock → mutate → read-back verify
  → audit → return); it cannot alter what `DeploymentBinding` value is
  written or what `_check_deployment_identity` subsequently matches — a
  fault in it can only cause an already-decided, already-durable
  mutation to lack an audit record (7J §17's own named, carried-forward,
  non-blocking finding), not change the mutation's content. This is a
  new exclusion for this contract's own precedent table (no prior
  amendment phase encountered `pcae.core.provenance` in a walk), applied
  using the identical authority-sensitivity criterion, not a new
  criterion. `hatp_bootstrap.py` and `repository_identity.py` are
  PCAE-owned and genuinely authority-sensitive, but require no new
  binding decision: both are already HMIC-REQ-050 members via limb (a)
  (§49's transitive-completeness table), so limb (c)'s third anchor
  contributes nothing new for them — they remain bound, for the reason
  already on record, not a new one.
- **Category C (standard library — do not bind, disclose residual
  trust).** `fcntl`, `json`, `os`, `re`, `tempfile`, `contextlib`,
  `dataclasses`, `datetime`, `enum`, `pathlib`, `typing`, `argparse`,
  `sys`. Not HMIC-bindable, per HMIC-REQ-065 (already frozen, unchanged):
  the Python interpreter and its standard library are named there as an
  explicit, out-of-scope transitive-dependency boundary. Residual trust
  in the interpreter/stdlib's own correctness is unchanged by this phase
  and remains disclosed, not silently assumed away.
- **Category D (external/system — not applicable).** Unlike §53.5's
  Category D (git, `ls`, ACL subsystem), the producer pair invokes no
  external binary or subprocess (confirmed: no `subprocess`/`os.system`/
  `os.exec*` call in either file) — its only I/O beyond the standard
  `open`/`os.replace` file primitives already covered by `hatp_
  bootstrap.py`'s own atomic-write idiom (reused, not reimplemented,
  per the producer's own docstring) is the interactive `input()` prompt
  in the admin script's `_prompt_confirm`, itself Category-A-bound as
  part of the script's own authority-sensitive bytes (§55.5 Category A).
- **Category E (contract/document inputs).** Neither file reads any
  `docs/contracts/**` document's bytes at runtime (confirmed: no
  `open(`/`read_text(` call against a `docs/contracts` path in either
  file). `HBDC-001`'s normative text informed both files' human-authored
  implementation but is not a runtime dependency of them. `HBDC-001` is
  already bound into both `implementation_scope_digest` (HMIC-REQ-050's
  twenty-fifth entry, §52) and `contract_versions` (HMIC-REQ-067, §51) —
  this phase does not duplicate, alter, or extend that binding (§55.11).

**§55.6 Worked verdict-influence chain (not assumed).** The full
authority path from admin invocation to Class-B verdict, traced
end-to-end: `scripts/hatp_deployment_binding_admin.py::main` parses CLI
arguments, builds `AuthorityEvidence`, and (after operator confirmation)
calls `core/hatp_deployment_binding_admin.py::create_deployment_binding`
(or `rotate_`/`revoke_`), which validates, locks, mutates `registry.json`
under `HATPTrustStore.production().root` atomically, reads back, audits,
and returns — all via already-frozen `hatp_bootstrap.py` primitives for
the trust-store shape and atomic-write idiom, and already-frozen
`repository_identity.py` for the subject repository's identity. Later,
`hatp_class_b_conformance.py::_check_deployment_identity` (itself
Category-A-bound to `hatp_class_b_conformance.py`'s own membership since
v1.3, §53) calls `HATPTrustStore.load_repository_enrollment` and `hatp_
bootstrap.deployment_binding_matches` — both already-frozen `hatp_
bootstrap.py` read primitives — against the exact `registry.json` the
producer wrote, folding the boolean match result into `verify_class_b_
deployment_conformance`'s aggregate verdict. Every step of this chain
is either already HMIC-bound (`hatp_bootstrap.py`, `repository_
identity.py`, `hatp_class_b_conformance.py`) or newly bound by this
phase (the producer pair) — no unbound step remains (§55.9 restates this
as the full transitive-coverage matrix).

**§55.7 A parallel construction, not a duplicate (self-binding/cycle
check).** Independently confirmed by import-graph inspection: neither
`hatp_mandatory_certification.py` nor `scripts/hatp_certification_
admin.py` imports `hatp_deployment_binding_admin.py` (core or script) in
either direction, and neither of the two new files imports `hatp_
mandatory_certification.py` or `scripts/hatp_certification_admin.py` —
zero references, by AST walk, of either symbol pair in the other pair's
files. No HMIC validator/admin self-reference, no digest-construction
cycle, no producer→HMIC-verifier→producer recursion, and no
certification-dependency cycle is introduced by binding the two
producer files. W-1 (§50) is not reopened: it concerned `hatp_mandatory_
certification.py`/`hatp_certification_admin.py` binding themselves into
their own digest, a distinct file pair from this phase's two, with no
import relationship between the two pairs. CBV-S1/§53's Class-B verifier
binding is likewise undisturbed: `hatp_class_b_topology_verifier.py`/
`hatp_environment_lock_verifier.py`/`hatp_class_b_conformance.py` import
no symbol from either newly-bound producer file (confirmed by the same
AST walk, §53.3's own result unchanged by this phase), and the producer
pair imports no symbol from any of the three verifier files.

**§55.8 Regression: B-149O.19.3-1, B-149O.20D-1, CBV-S1's three files.**
Independently re-confirmed, by the same direct read used in §55.2, that
`hatp_providers.py`, `hatp_fido2_provider.py`, `hatp_piv_provider.py`,
and `hatp_hardware_credentials.py` (B-149O.19.3-1's four repair entries)
remain present, unremoved, and unmodified by this phase; that `docs/
contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (B-149O.20D-1's repair
entry) remains present, unremoved, and unmodified; and that `hatp_class_
b_topology_verifier.py`, `hatp_environment_lock_verifier.py`, and `hatp_
class_b_conformance.py` (§53's three v1.3 entries) remain present,
unremoved, and unmodified by this phase in `_FROZEN_SRC_PCAE_RELATIVE_
FILES`/`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`. `HBDC-001` continues
receiving both the `contract_versions` version-header binding
(HMIC-REQ-067/069) and the `implementation_scope_digest` content binding
(HMIC-REQ-050/053), unchanged.

**§55.9 Full transitive authority-bearing coverage matrix (HBDC-001
first-use authority path).**

| Component | HMIC-frozen? | Anchor | Evidence |
|---|---|---|---|
| `scripts/hatp_deployment_binding_admin.py` | Yes, as of v1.4 | limb (c), third anchor | §55.5 Category A, §55.6 |
| `core/hatp_deployment_binding_admin.py` | Yes, as of v1.4 | limb (c), third anchor | §55.5 Category A, §55.6 |
| `DeploymentBinding` schema (`hatp_bootstrap.py`) | Yes, since v1.1 | limb (a) | §49, §55.2 baseline |
| `HATPTrustStore` read/write primitives (`hatp_bootstrap.py`) | Yes, since v1.1 | limb (a) | §49, §55.2 baseline |
| `RepositoryIdentity` reader/validator (`repository_identity.py`) | Yes, since v1.1 | limb (a) | §49, §55.2 baseline |
| Canonical serialization/atomic-write idiom (`hatp_bootstrap.py`) | Yes, since v1.1 | limb (a) | §49, §55.2 baseline |
| HBDC matcher (`hatp_bootstrap.deployment_binding_matches`) | Yes, since v1.1 | limb (a) | §49, §55.2 baseline |
| Class-B aggregator (`hatp_class_b_conformance.py`) | Yes, since v1.3 | limb (c), first anchor | §53.5, §55.6 |
| Audit sink (`pcae.core.provenance`) | No — intentionally excluded | n/a | §55.5 Category B |
| Path value type (`pcae.core.paths`) | No — intentionally excluded | n/a | §55.5 Category B, §49/§53 precedent |

Every executable component in the create-to-verdict chain is either
frozen directly (this phase's two entries), already frozen as a
dependency (five `hatp_bootstrap.py`/`repository_identity.py`/`hatp_
class_b_conformance.py` rows), or intentionally outside scope with
documented rationale (two rows) — no unaccounted component remains.

**§55.10 Non-widening of `contract_versions`.** This phase adds zero
members to `contract_versions` (HMIC-REQ-067): the DeploymentBinding
producer is PCAE-owned *source*, not a separate normative *contract* —
its own governing contract, `HBDC-001`, is already a `contract_versions`
member (since v1.2, §51) and already digest-bound (since 149O.20D.1,
§52), both unchanged by this phase. `contract_versions` remains exactly
five entries: `HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`, `HBDC-001`.

**§55.11 HBDC-001 unchanged proof.** `docs/contracts/HATP_CLASS_B_
DEPLOYMENT_CONTRACT.md` was read in full before and after this phase's
edits to this document (`HMIC-001` itself, a distinct file) and to `hatp_
mandatory_certification.py`; byte-identical in both comparisons (`git
diff` against the phase-entry commit shows zero lines changed in that
path). This phase edits only `HMIC-001` (this document) and `hatp_
mandatory_certification.py`'s frozen-set constants/count — it does not
touch `HBDC-001`, the DeploymentBinding producer's implementation
(`core/hatp_deployment_binding_admin.py`), or the admin script
(`scripts/hatp_deployment_binding_admin.py`) themselves; all three
remain byte-identical to their 149O.20L.7J-verified state (confirmed by
SHA-256 comparison, §55.13).

**§55.12 Over-binding / under-binding threat analysis.** *Under-binding*:
if `scripts/hatp_deployment_binding_admin.py` were omitted while `core/
hatp_deployment_binding_admin.py` were bound, an edit to the script
alone (e.g. skipping the confirmation prompt, or hand-constructing
`AuthorityEvidence` with an empty `principal_id` that the core module's
own `_validate_authority_evidence` might not by itself catch, since the
script currently supplies argparse `required=True` as an outer gate) —
the same closure-violation shape §53.10 already demonstrated for the
Class-B verifier's three files, now demonstrated for this pair. If
`core/hatp_deployment_binding_admin.py` were omitted while only the
script were bound, the script's own bytes would be digest-covered but
the actual create/rotate/revoke decision logic (idempotency comparison,
fail-closed branches) would be unbound — the more consequential half of
the pair, left open. Binding both closes this threat class fully for
the current source tree (§55.3-§55.4 found no further transitive
PCAE-owned dependency). *Over-binding*: `pcae.core.paths` and `pcae.
core.provenance` were both inspected and excluded (§55.5) rather than
bound by proximity; binding either would add digest volatility (e.g.
recertification churn from an unrelated audit-log formatting change)
for files with no verdict-influencing content, contradicting the
minimality this contract's own precedent (§53.9/§53.11) already
establishes. No PCAE-owned file beyond the two producer-pair roots was
found reachable at all (§55.3-55.4), so there was no broader candidate
set to prune from.

**§55.13 Producer/admin-script implementation-unchanged proof.**
SHA-256 of `core/hatp_deployment_binding_admin.py` and `scripts/hatp_
deployment_binding_admin.py`, computed immediately before this phase's
first edit and again immediately before this phase's finalization
commit, are identical for both files — this phase's own production
edit is confined to `hatp_mandatory_certification.py`'s frozen-set
constants and this contract document; the producer and its admin
script are not touched. `hatp_bootstrap.py` and `repository_identity.py`
SHA-256 are likewise unchanged across the same window (consumer
unchanged, §55.6/§55.11). Digest sensitivity was independently tested
in a disposable worktree: a single-byte perturbation to `core/hatp_
deployment_binding_admin.py` changes `derive_implementation_scope_
digest`'s output once the file is a frozen member; the identical
perturbation against the pre-amendment (28-file) constant set does not
change the digest, confirming the omission was real before this phase
and is closed after it. The same test was independently repeated for
`scripts/hatp_deployment_binding_admin.py`. A control perturbation
against a disposable, clearly non-authority-bearing file (a scratch
file outside every frozen bucket) changes neither the pre- nor
post-amendment digest, confirming no accidental scope broadening.
Removing a required newly-frozen member from a disposable copy of the
frozen set and recomputing the digest fails closed (`HMICIdentity
DerivationError`/equivalent HMIC-REQ-059 missing-file behavior), not a
silent skip. No duplicate logical path exists in the widened
thirty-entry set (confirmed: `len(set(_frozen_canonical_paths())) ==
len(_FROZEN_AUTHORITY_BEARING_FILES)) == 30`). All thirty canonical
paths resolve to existing, non-symlinked, regular files on this
repository's current worktree.

**§55.14 Contract-version determination.** This amendment widens
HMIC-REQ-050's enumeration (28 → 30 entries) and widens HMIC-REQ-052
limb (c) with a third anchor — a normative-scope change of the same
shape as the v1.2 → v1.3 amendment (§53, which added a new limb and
three files) and the v1.0 → v1.1 amendment (§50, which added limb (b)
and two files, including the direct file-pair precedent this phase
mirrors), not the shape of a within-version repair like 149O.20D.1's
same-version HBDC-001 gap closure (§52) or 149O.20L.1A's same-version
descriptive-header repair (§54), neither of which changed which limb
applied or how many files were bound. No existing requirement's meaning
is narrowed; no existing consumer's expectation (HMIC-REQ-069's
version-drift detection, HMIC-REQ-059/061/062's missing/symlink/
non-regular-file handling, HMIC-REQ-054-058's digest algorithm) is
broken — every prior mechanism continues to apply unmodified to a
longer file list. Following this repository's own established
minor-bump convention for scope-widening amendments (v1.0 → v1.1 at
§50, v1.1 → v1.2 at §51, v1.2 → v1.3 at §53), this amendment is
`HMIC-001 v1.3 → v1.4`, an in-place minor version bump, not v2.0 (no
existing field, schema, or algorithm is redefined or removed) and not a
same-version repair (unlike §52/§54, this is a scope addition, not a
defect fix in an existing binding).

**§55.15 Verdict.** HMIC-001 v1.4: contract-evolved **and**
production-aligned in the same phase. Closure limb (c) widened with a
third anchor; HMIC-REQ-050 widened to thirty files; `contract_versions`
(HMIC-REQ-067) unchanged at five members (§55.10) — no new contract
document is introduced by this phase, and `HBDC-001` remains the sole
v1.2 addition there, unchanged (§55.11). *(Corrected 149O.20L.7L.1,
finding F-7L-1; see §56.1 — this sentence, as originally written, was
never accurate: `verify_class_b_deployment_conformance` already had a
real production readiness/activation consumer, `hatp_mandatory_
cutover.py`, wired by Phase 149O.20L.3, ancestral to this phase's own
149O.20L.7K entry; §53.4/§55.4 never established the contrary as of
this phase's own entry — §53.4's zero-consumer finding was accurate
when 149O.20K (v1.3) wrote it, since it predates Phase 149O.20L.3's
later wiring, and §53.4 is left unmodified as a legitimate historical
snapshot (§56.1); by the time this phase (149O.20L.7K, v1.4) cited it
alongside §55.4 to support the present-tense "remain" wording above,
Phase 149O.20L.3 had already landed, making the citation stale at the
moment it was written here, not merely afterward. §55.4 itself (per its
own scope note) only ever scoped its zero-consumer finding to the
`DeploymentBinding` producer, never to the verifier.)* Zero real `DeploymentBinding` invocations exist on any
host (§55.4) — that finding is unaffected and remains correct. Production
`_FROZEN_AUTHORITY_BEARING_FILES`/`_CONTRACT_IDENTITY_FILES` are
realigned to 30/5 by this same phase (§55.13, §55.16), unlike the
deliberate contract-ahead-of-production sequencing at v1.1 (§50), v1.2
(§51-52), and v1.3 (§53) — this phase's own governing scope directs
combined amendment-and-alignment, and 149O.20L.7L (§55.17) is the
independent-verification phase that checks this combination was done
correctly, not a separate alignment phase. `W-1`, `B-149O.19.3-1`,
`B-149O.20D-1`, and CBV-S1's three-file binding remain independently
closed/repaired/bound exactly as §49/§50/§52/§53 left them (§55.8). The
7J §31 HMIC frozen-source-membership finding: **REPAIRED AT THE
CONTRACT-AND-PRODUCTION LAYER — INDEPENDENT VERIFICATION PENDING — NOT
CLOSED** (only 149O.20L.7L may close it). The 7J §17 audit-failure-
after-mutation exception-type finding, the `hatp_bootstrap.py::_parse_
iso_timestamp` permissive-parser finding (7I/7J), and HMIC-REQ-103's
revocation-does-not-invalidate-existing-validation finding (7G/7H/7J)
are all carried forward unchanged — this phase does not touch, repair,
or claim to have repaired any of them. No `DeploymentBinding` was
created. No `RepositoryIdentity` was created. No first-use election was
initiated. No Boundary C or Boundary A work occurred. Dell was not
accessed. HATP production remains **NOT READY**. Runtime remains
**Observed / observe / unavailable**.

**§55.16 Production alignment (this phase, not deferred).** Unlike
§53.12's explicit non-alignment, this phase updates `hatp_mandatory_
certification.py`'s `_FROZEN_SRC_PCAE_RELATIVE_FILES` (append `core/
hatp_deployment_binding_admin.py`) and `_FROZEN_REPOSITORY_ROOT_
RELATIVE_FILES` (append `scripts/hatp_deployment_binding_admin.py`),
widening the module's own `assert len(_FROZEN_AUTHORITY_BEARING_FILES)
== 28` to `== 30`, in this same phase — per this phase's own governing
scope (item 16), which directs combined amendment. `hatp_mandatory_
certification.py` is itself already a frozen member (since v1.1, §50);
this phase's edit to it therefore changes `implementation_scope_digest`
twice over — once because its own bytes changed, and once because the
file set it enumerates grew — both expected and independently confirmed
(§55.13).

**Recommended next phase.** **149O.20L.7L — HMIC Frozen Source-Scope
Amendment for the DeploymentBinding Producer Independent Verification**,
which must independently reconstruct, without trusting this section's
narrative: HMIC-REQ-052 (pre- and post-amendment text, §55.1); the
current 28/5 production identity immediately before this phase (§55.2);
the producer-pair dependency graph (static and semantic, §55.3-§55.4);
the authority-sensitive/excluded classification (§55.5); the full
verdict-influence chain (§55.6); the cycle/self-binding analysis
(§55.7); the B-149O.19.3-1/B-149O.20D-1/CBV-S1 regression (§55.8); the
full transitive coverage matrix (§55.9); `contract_versions`
non-widening (§55.10); HBDC-001 identity preservation (§55.11); the
over-/under-binding threat analysis (§55.12); the producer/admin-script
byte-identity and digest-sensitivity proofs (§55.13); the v1.3 → v1.4
version-bump rationale (§55.14); and the combined production alignment
(§55.16). 149O.20L.7L does not authorize `DeploymentBinding` creation,
`RepositoryIdentity` creation, first-use election, Dell redeployment, or
any certification/activation work — only after it passes may a future,
separately-governed first-use-preparation phase proceed, in that order,
not out of it.

---

## 56. Contract Repair History — Phase 149O.20L.7L.1 (Findings F-7L-1, F-7L-2)

**Status of this section:** descriptive/historical record of the
149O.20L.7L.1 same-version repair; it introduces no new `HMIC-REQ-###`
identifier, narrows or widens no existing requirement's normative
meaning, and does not touch `HMIC-REQ-050`'s thirty-file enumeration or
any production source. The only changes this phase made outside this
section are: the header block (Status line, new `Repaired by` line, and
the `Depends on` line) at the top of this document; the closing
paragraph of HMIC-REQ-052 limb (c) (§17); a scope-clarifying note
appended to §55.4; the verdict sentence of §55.15; and attack matrix
rows 38 and 39 (§41).

**Context.** 149O.20L.7L's own independent verification of 149O.20L.7K
(v1.4) withheld a VERIFIED verdict: while the frozen source-scope
widening (28 → 30 files, the `DeploymentBinding` producer pair) was
independently confirmed technically correct, 149O.20L.7L found that
HMIC-001 v1.4 itself asserted, in multiple places, that no readiness,
certification, or activation code path consumes
`verify_class_b_deployment_conformance` — a statement contradicted by
this repository's own primary production source,
`src/pcae/core/hatp_mandatory_cutover.py`, which imports the function
and calls it as the eighth activation-readiness term. This section
records 149O.20L.7L.1's independent reconstruction of that contradiction
and its narrow, same-version, contract-text-only repair.

**§56.1 Finding F-7L-1 (Blocking) — independent reconstruction.** Read
directly from `src/pcae/core/hatp_mandatory_cutover.py`, not from any
prior phase's narrative: line 74 reads `from pcae.core.hatp_class_b_
conformance import verify_class_b_deployment_conformance`; line 952,
inside `_assess_hatp_mandatory_activation_readiness_at_root` (the
function `assess_hatp_mandatory_activation_readiness`, the sole
production activation-readiness entrypoint, calls at line 993), reads
`class_b_result = verify_class_b_deployment_conformance(...)`, with the
result appended to the function's `checks` list under the name
`class_b_deployment_conformance_satisfies_readiness` — the eighth and
final entry among the eight `HATPMandatoryActivationReadinessCheck`
instances the function assembles (`class_b_protected_storage_available`,
`repository_deployment_identity_valid`, `hatp_substrate_operational`,
`hsce_signing_implementation_available`,
`mandatory_consumption_implementation_independently_verified`,
`production_dependency_provenance_valid`,
`protected_activation_authority_mechanism_available`, and finally
`class_b_deployment_conformance_satisfies_readiness`), exactly matching
the module's own comment at lines 938-949 ("HMRC-REQ-086-100 ... the
eighth, additive readiness term"). The same internal function is also
re-invoked, lock-held, immediately before any real `HATP_MANDATORY`
activation write, via `_activate_hatp_mandatory_at_root`'s
`readiness_check` callback (lines 1049-1051) — so the verifier is
consumed both by the advisory readiness assessment and by the
lock-held pre-activation re-check, not merely referenced in passing. No
other `src/pcae/**` module calls `assess_hatp_mandatory_activation_
readiness` or `_assess_hatp_mandatory_activation_readiness_at_root`
(confirmed by repository-wide grep); the verifier has exactly one
production consumer, and it is a real readiness/activation consumer, not
a certification consumer — `hatp_mandatory_certification.py`'s own
validator (`validate_active_hatp_mandatory_independent_verification_
certification`) neither calls nor is called by
`verify_class_b_deployment_conformance`. Git history independently
confirms this wiring was introduced by Phase 149O.20L.3 (`git log`
identifies commit `e2ccb7a3`, "Phase 149O.20L.3: Full-HBDC Production
Readiness Integration") and re-confirmed unmodified by 149O.20L.4; both
commits are ancestral to 149O.20K's (v1.3) own phase entry and,
a fortiori, to 149O.20L.7K's (v1.4) phase entry — `git log --oneline
main` places the 149O.20L.3 commit range strictly before the 149O.20K
commit range, which is itself strictly before the 149O.20L.7K commit
range. Consequently: HMIC-001 v1.3's own §53.4 "zero production
consumers" finding (149O.20K) was accurate when written, since it
predates the 149O.20L.3 wiring, and is left unmodified as a legitimate
historical snapshot, per this repository's own historical-truth-
preservation discipline. HMIC-001 v1.4's §55.4/§55.15/HMIC-REQ-052 limb
(c) closing paragraph and attack rows 38/39 (149O.20L.7K), by contrast,
were written strictly *after* the 149O.20L.3 wiring landed — their
"zero production consumers"/"no readiness ... code path calls" language
was never accurate at the moment it was written, not merely stale
afterward. This is the repaired defect.

**§56.2 Distinguishing consumption categories.** Independently verified
from the source, not asserted by analogy: `verify_class_b_deployment_
conformance` — **readiness**: yes, direct call at cutover.py:952,
inside the sole production readiness-assessment function. **Activation**:
yes, indirect via readiness — the same readiness function is re-invoked,
lock-held, immediately before any real `HATP_MANDATORY` write
(cutover.py:1049-1051); there is no separate, distinct activation-time
call to the verifier. **Certification**: no — `hatp_mandatory_
certification.py`'s validator does not call, and is not called by,
`verify_class_b_deployment_conformance`; the two are independent
readiness terms evaluated by different functions (`hmic_verified` at
cutover.py:887 vs. `class_b_satisfied` at cutover.py:955). **Other
production paths**: none found — repository-wide grep for the symbol
name outside `hatp_class_b_conformance.py` (its definition site) and
`hatp_mandatory_cutover.py` (its sole consumer) returns no further
production matches. This repair therefore states "readiness/activation
consumer, not a certification consumer" precisely, rather than replacing
one false universal claim ("no consumer at all") with a different false
universal claim ("consumed everywhere").

**§56.3 Repair — HMIC-REQ-052 limb (c) closing paragraph (§17).** The
closing paragraph previously stated that, as of v1.4, "no readiness,
certification, or activation code path calls `verify_class_b_
deployment_conformance` or consults its result." Repaired to state that
limb (c)'s **first anchor is not anticipatory** — the verifier already
has the real readiness/activation consumer reconstructed at §56.1 —
while explicitly preserving limb (c)'s **third-anchor rationale
unweakened**: the `DeploymentBinding` producer/admin-ceremony write path
remains genuinely unreachable from the verifier's own call graph (a
distinct fact, independently true regardless of the verifier's consumer
status, per §55.1/§55.4's own static/semantic dependency walk, untouched
by this repair), and remains anticipatory in its own right because no
real `DeploymentBinding` has ever been created. The repair distinguishes
these as the two different facts item 9 of this phase's own governing
scope names: "the producer is not reachable through the verifier's own
transitive dependency graph" (still true, unweakened) is not the same
fact as "the verifier itself is unconsumed" (was false, now corrected).

**§56.4 Repair — §55.4 scope note.** §55.4's own text was, read
narrowly, always scoped to the `DeploymentBinding` **producer**'s
zero-consumer/zero-invocation status (confirmed at §56.1's grep) — it
never itself asserted a claim about the verifier. The defect was
§55.15's citation of §55.4 as joint support for a broader verifier-level
claim it never established. A scope-clarifying note was appended to
§55.4 stating this explicitly and cross-referencing the correction at
§55.15/§56.1, without altering §55.4's own (accurate, unaffected)
producer-level finding.

**§56.5 Repair — §55.15 Verdict.** The sentence "Zero production
consumers of `verify_class_b_deployment_conformance` remain
(§53.4/§55.4)" is repaired with an inline correction explaining why it
was never accurate (§56.1's chronology) and why §53.4/§55.4 do not, and
never did, jointly support it. The adjacent, independent claim "zero
real `DeploymentBinding` invocations exist on any host (§55.4)" is
preserved unmodified — it remains true and unaffected by this repair.

**§56.6 Repair — attack row 38 (§41).** Row 38's "Not yet operative, and
not yet consequential" framing rested on two premises: production
identity derivation not yet realigned past twenty-eight files, and no
readiness/certification path consuming the verifier. Both premises are
now false: production has since been realigned to the full thirty-file
set (mechanically enforced since 149O.20L.7K), and the verifier has a
real readiness/activation consumer (§56.1). The row's outcome cell is
repaired to state the attack is now **operative and consequential**:
`IMPLEMENTATION_MISMATCH` rejection via `implementation_scope_digest`
would actually reject a Class-B-verifier byte edit under an unchanged
HMIC identity, because a live readiness decision now depends on the
verifier's verdict. The rejection *mechanism* (`HMIC-REQ-050`'s
twenty-sixth through twenty-eighth entries, `HMIC-REQ-052(c)`) is
unchanged; only the operative/consequential status is corrected.

**§56.7 Repair — attack row 39 clause (a) (§41).** Clause (a) previously
grounded row 39's "not functionally load-bearing" conclusion in the same
false "zero readiness/certification consumers" claim repaired at §56.3.
Repaired to ground clause (a) instead in the true, independently-verified
fact that already carried the actual normative weight: the
`DeploymentBinding` producer/admin-ceremony pair is bound under limb
(c)'s third, non-reachability anchor precisely *because* it is a
separate authority-bearing write path not transitively captured by the
verifier's own call graph — a fact wholly independent of the verifier's
consumer status. The row's overall "not functionally load-bearing"
conclusion is preserved, resting on legs (b) (no real `DeploymentBinding`
has ever been created) and (c) (no HMIC certification exists), neither
of which this repair touches; the verifier's now-corrected consumer
status is noted but does not change the conclusion, since a compromised
producer still has no live `DeploymentBinding` state to have corrupted.

**§56.8 Finding F-7L-2 (Non-blocking) — repair.** This document's own
"Depends on" header line read `HBDC-001 v1.0`. `HBDC-001`'s own Version
header field independently reads `1.1` (confirmed directly against the
live file, not assumed); `HBDC-001` has been v1.1 since Phase
149O.20L.7G. `derive_contract_versions` (`core/hatp_mandatory_
certification.py`) was independently exercised against the live
repository and returns `{"HBDC-001": "1.1", ...}` — the live-header
derivation mechanism was never stale, exactly the same Outcome-B shape
§54.3 (149O.20L.1A) established for the identical class of defect
against `HMRC-001`. Repaired: the `Depends on` header now reads
`HBDC-001 v1.1`; all other four members unchanged. This is a
same-version, descriptive-header-only repair, mirroring §54's own
precedent exactly.

**§56.9 Finding F-7L-5 — adjudication of attack rows 33/34/36/37.**
Rows 33, 34, 36, and 37 each carry a "Not yet operative" caveat tied to
a **different** production identity derivation subsystem than the one
this phase's own evidence base covers: row 34's caveat additionally
names "zero readiness/cutover callers of the validator" for `hatp_
mandatory_certification.py`'s validator — a Wave F integration
(`docs/PHASE_149O_19_5F_HMIC_ACTIVATION_READINESS_INTEGRATION.md`)
distinct from, and reconstructed independently of, the Class-B verifier/
DeploymentBinding-producer chain this phase's F-7L-1 evidence
establishes. Confirming whether, and exactly when, each of these four
rows' file-count/contract-count realignment thresholds was superseded
requires independently re-deriving multiple earlier, separately-governed
alignment phases (the v1.1→v1.2→v1.3→v1.4 file-count history and the
Wave F readiness-integration history) outside this phase's own narrow
evidence chain. Per this phase's own governing scope (item 25:
"If repair requires wider architecture interpretation: defer"), rows
33/34/36/37 are **DEFERRED, non-blocking** — left byte-unmodified. Row
38 was **REPAIRED NARROWLY** (§56.6): unlike 33/34/36/37, its stale
"zero production consumers" clause is a direct restatement of the exact
F-7L-1 claim this phase already independently reconstructed in full at
§56.1, and leaving it unrepaired while repairing row 39's twin clause in
the same table would leave a contradictory duplicate stale claim,
violating this phase's own duplicate-wording-search discipline (item
13).

**§56.10 Finding F-7L-7 — adjudication of the 7I/7J guard-test
exemptions.** Two textual guard tests —
`tests/test_phase_149o_20l_7i_deploymentbinding_producer_implementation.py
::TestNotAgentReachable::test_no_src_pcae_module_imports_the_producer_
except_itself` and `tests/test_phase_149o_20l_7j_deploymentbinding_
producer_implementation_independent_verification.py::test_producer_
module_not_imported_anywhere_in_src_pcae_except_itself` — previously
exempted `hatp_mandatory_certification.py` from their substring scan at
whole-file granularity (`if path.name == "hatp_mandatory_certification.
py": continue`), because that file legitimately references the producer
module name as literal path-string data in its frozen-file enumeration,
not as an import. 149O.20L.7L already added a strictly stronger,
unconditional AST-level guard with no per-file exemption (`test_no_
module_under_src_pcae_imports_the_producer_at_ast_level`) and a
companion test confirming `hatp_mandatory_certification.py` references
the producer only as frozen path-string data (`test_certification_
module_references_the_producer_only_as_frozen_path_data`) — both
preserved byte-unmodified by this phase. This finding's own narrow scope
is the two *older*, textual guards specifically: each is tightened from
skipping `hatp_mandatory_certification.py` outright to scanning it and
failing only if any matching line's first token is `import` or `from`
(an exact-occurrence exemption: the file's three known non-import
literal-string occurrences, at lines 952/983/1008, continue to pass; a
future real import statement referencing the producer would now be
caught by these two tests independently of the AST guard, not only by
it). Zero-imports, zero-agent-reachability, and the frozen-path-only
disposition are all unweakened; the AST guard is untouched. See the
focused test diffs for the exact tightened assertions.

**§56.11 Scope discipline confirmed.** No `HMIC-REQ-###` text was added,
removed, or reworded. `HMIC-REQ-050`'s thirty-file enumeration and exact
member list are unchanged (byte-identical before/after, confirmed
§56.12). `HMIC-REQ-052`'s three limbs and their scope are unchanged; only
limb (c)'s own prose describing the first anchor's consumer status was
corrected — the closure rule's *membership test* ("any file reachable
from `verify_class_b_deployment_conformance`'s own call graph...") is
untouched. No `src/pcae/**` file was modified by this phase.
`hatp_mandatory_cutover.py`, `hatp_class_b_conformance.py`, `hatp_
deployment_binding_admin.py`, `scripts/hatp_deployment_binding_admin.py`,
and `hatp_mandatory_certification.py` are all byte-identical
before/after (§56.12). `HMIC-001` remains v1.4 — this is a same-version
repair, mirroring §52's (149O.20D.1) and §54's (149O.20L.1A) precedent
exactly: a defect discovered post-freeze, corrected in place, with no
requirement widened or narrowed. No certification, activation,
`DeploymentBinding` creation, `RepositoryIdentity` creation, first-use
election, or Dell access occurred.

**§56.12 Byte-identity and digest proofs.** SHA-256/git-blob-hash of
`src/pcae/core/hatp_deployment_binding_admin.py`, `scripts/hatp_
deployment_binding_admin.py`, `docs/contracts/HATP_CLASS_B_DEPLOYMENT_
CONTRACT.md` (`HBDC-001`), and `src/pcae/core/hatp_mandatory_cutover.py`,
computed immediately before this phase's first edit and again
immediately before its finalization commit, are identical for all four.
`implementation_scope_digest`, independently recomputed against the live
repository both before and after this phase's edits, is unchanged (HMIC
is not itself a member of its own frozen thirty-file set — a contract-
document-only edit does not enter this digest). `derive_contract_
versions`, recomputed after the repair, returns `HBDC-001: "1.1"`,
matching the repaired header exactly.

**§56.13 Verdict.** **F-7L-1: REPAIRED — INDEPENDENT VERIFICATION
PENDING — NOT CLOSED.** **F-7L-2: REPAIRED — INDEPENDENT VERIFICATION
PENDING — NOT CLOSED.** **F-7L-5 (rows 33/34/36/37): DEFERRED,
NON-BLOCKING — UNMODIFIED.** **F-7L-5 (row 38): REPAIRED — INDEPENDENT
VERIFICATION PENDING.** **F-7L-7: REPAIRED — INDEPENDENT VERIFICATION
PENDING** (test-only; no production source touched). The 7J §31 HMIC
frozen-source-membership finding remains **REPAIRED AT THE
CONTRACT-AND-PRODUCTION LAYER — INDEPENDENT VERIFICATION PENDING — NOT
CLOSED**, exactly as §55.15 left it; this phase's own text repair does
not itself close it — only 149O.20L.7L.2 may. `HMIC-001` remains v1.4.
`HMIC-REQ-050`'s thirty-file enumeration is unchanged. No production
source was modified. `HBDC-001` remains v1.1, unamended. No
`DeploymentBinding` was created. No `RepositoryIdentity` was created. No
first-use election was initiated. No Boundary C or Boundary A work
occurred. Dell was not accessed. HATP production remains **NOT READY**.
Runtime remains **Observed / observe / unavailable**.

**Recommended next phase.** **149O.20L.7L.2 — HMIC-001 v1.4
Consumer-Status and Dependency-Header Repair Independent Verification**,
which must independently reconstruct, without trusting this section's
narrative: every F-7L-1 correction (§56.1-§56.3, §56.6-§56.7); the
`HBDC-001` dependency-header correction (§56.8); the same-version repair
legitimacy (§56.11, mirroring §52/§54); that `HMIC-REQ-050`/`HMIC-REQ-052`
carry no semantic weakening (§56.11); the unchanged thirty-member source
scope and unchanged `implementation_scope_digest` (§56.12); that no
production behavior changed (§56.11-§56.12); and the F-7L-5/F-7L-7
adjudications (§56.9-§56.10). Only after a clean 149O.20L.7L.2 may the
7J §31 finding be closed, and only after that may a separate,
separately-governed phase decide the first-use sequencing architecture
(redeploy-first vs. SHA-bound election vs. two-CHGR). No binding,
election, certification, redeployment, or Dell mutation is authorized by
149O.20L.7L.1 or by 149O.20L.7L.2.

---

## 57. Contract Repair History — Phase 149O.20L.7L.3 (Findings F-7L-5, F-7L-7)

**Status of this section:** descriptive/historical record of the
149O.20L.7L.3 same-version, contract-text-and-test-only repair. It
introduces no new `HMIC-REQ-###` identifier, narrows or widens no
existing requirement's normative meaning, and does not touch
`HMIC-REQ-050`'s thirty-file enumeration, `HMIC-REQ-052`'s three limbs,
or any production source. The only changes this phase made outside this
section are: the header block (Status line, new `Repaired by` line) at
the top of this document; attack-matrix rows 33, 34, 36, and 37 (§41);
and the `HMIC-REQ-145` closure paragraph's own stale file-count
restatement (§19).

**Context.** 149O.20L.7L.1 (§56.9) deferred rows 33/34/36/37 as
non-blocking, reasoning that adjudicating their "Not yet operative"
caveats required independently re-deriving multiple earlier,
separately-governed file-count/contract-count alignment phases outside
its own narrow F-7L-1/F-7L-2 evidence chain. 149O.20L.7L.2's independent
verification found that deferral does not hold: each row's live
production-state claim is directly, trivially false against current
production constants — no wide archaeology required, only a direct read
of `core/hatp_mandatory_certification.py`'s own live constants. This
section records 149O.20L.7L.3's independent reconstruction of that
finding and its narrow, same-version, contract-text-only repair.

**§57.1 Finding F-7L-5 — independent reconstruction.** Read directly
from `core/hatp_mandatory_certification.py` and `core/hatp_mandatory_
cutover.py`, not from either prior phase's narrative: `_FROZEN_
AUTHORITY_BEARING_FILES` (`_FROZEN_SRC_PCAE_RELATIVE_FILES` +
`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`) has exactly thirty entries,
guarded by its own module-level `assert`; `derive_contract_versions`,
executed live, returns exactly five keys (`HMRC-001`, `HATP-001`,
`HSCE-001`, `RAE-001`, `HBDC-001`); no literal `mandatory_consumption_
implementation_independently_verified = False` (or `=False`) assignment
exists anywhere in `hatp_mandatory_cutover.py` — the term is computed
live via `hmic_verified = certification_status_satisfies_readiness(
hmic_validation.status)`, itself fed by a fresh call to `validate_
active_hatp_mandatory_independent_verification_certification`; and that
validator function has exactly one production caller outside its own
definition site (`hatp_mandatory_cutover.py`'s `_assess_hatp_mandatory_
activation_readiness_at_root`), confirmed by repository-wide grep. Git
history independently confirms this wiring (`validate_active_hatp_
mandatory_independent_verification_certification(` at cutover.py) was
introduced by commit `478f8b2c`, "Phase 149O.19.5F: HMIC Activation-
Readiness Integration" (Wave F) — strictly ancestral to 149O.20L.7K's
own phase entry in `git log --oneline main`, exactly as this contract's
own §51 (149O.20D) already recorded in an unrelated correction to §50's
own once-accurate "zero production callers" framing. Consequently: rows
33/34/36/37's "Not yet operative"/"production still computes the old
N-file/M-member set" language, and row 34's additional hard-coded-
ceiling/zero-caller clauses, were accurate when originally written
(v1.1/v1.2/149O.20D.1) but have been superseded by intervening,
separately-governed alignment phases (culminating in 149O.20L.7K's
same-phase contract-and-production realignment to the thirty-file/
five-member set) and were never revisited — the same class of
"contract-first, production-catches-up-later" sequencing this contract
uses throughout, left stale after production caught up.

**§57.2 The one fact all four rows share.** Independently confirmed: no
`certifications.json`, `certification-bindings.json`, or `active-
certification.json` file exists anywhere in this repository (filesystem
search). Every fresh call to the validator therefore resolves to
`MISSING` regardless of which file count or member count a caller
computes over — this is the still-true, unaffected reason each row's
underlying rejection scenario remains **not yet consequential** even
though the digest/version-comparison *mechanism* itself now runs, live,
on every readiness assessment (§57.1). This is the one premise 149O.20L.
7L.1's §50/§51 archival history already established and this repair
does not disturb.

**§57.3 Repair — row 33 (§41).** The row's "Not yet operative: ...
production still computes the twenty-two-file digest" caveat is
repaired to "Operative, not yet consequential", crediting the thirty-
file realignment (§57.1) and preserving §57.2's still-true "no stored
certification exists" conclusion. The row's rejection mechanism
(`IMPLEMENTATION_MISMATCH` via `implementation_scope_digest`) is
unchanged.

**§57.4 Repair — row 34 (§41).** Two independently false supporting
claims are corrected: the hard-coded `False` ceiling (superseded by
Wave F, §57.1) and "zero readiness/cutover callers of the validator"
(the validator has exactly one, §57.1). The row's bottom-line
conclusion — "no functional readiness decision currently turns on
[file count]" — is preserved unweakened, now resting on §57.2's
independent, unaffected ground (no stored certification exists) rather
than on the two false premises the original text cited.

**§57.5 Repair — row 36 (§41).** Mirrors §57.3 for the five-member
`contract_versions` set: "Not yet operative: ... production still
computes the four-member set" is repaired to "Operative, not yet
consequential", crediting the five-member realignment (§57.1).

**§57.6 Repair — row 37 (§41).** Mirrors §57.3 for the thirty-file
digest (which now includes `HBDC-001`'s own bytes). The row's own
illustrative attack description ("`HBDC-001` still declares ... Version
`v1.0`") is additionally corrected to `v1.1` — `HBDC-001`'s live Version
header has read `1.1` since Phase 149O.20L.7G, and this row's
description had not been updated to match, a small, same-class
descriptive-only correction bundled with the row's own caveat repair
rather than left as a second stale detail in an already-open row.

**§57.7 Rows 38/39 — unchanged, confirmed.** Row 38 and row 39, already
independently repaired by 149O.20L.7L.1 (findings F-7L-1, §56.6-§56.7),
are confirmed byte-unmodified by this phase — neither carries a
149O.20L.7L.3 status-correction citation, and both retain their existing
149O.20L.7L.1 citations exactly. Diffing row 38's and row 39's text
against the pre-149O.20L.7L.3 phase-entry commit's contract file confirms
zero byte difference for either row.

**§57.8 Finding F-7L-7 — repair.** `_pcae_imports` (`tests/test_phase_
149o_20l_7l_hmic_frozen_source_scope_amendment_independent_verification.
py`) recorded, for `ast.ImportFrom`, only `node.module` — never `node.
names` — so `from pcae.core import hatp_deployment_binding_admin`
(single- or multi-line, aliased or not) surfaced only `"pcae.core"`,
never the producer's own dotted path. Independently reproduced against
literal `ast.parse()` snippets before any edit (`tests/test_phase_149o_
20l_7l_3_attack_matrix_and_ast_guard_narrow_repair.py`,
`TestOldHelperBlindSpotIndependentlyReproduced`). Repaired by adding a
new, separate helper, `_pcae_import_targets`, alongside the
byte-unchanged `_pcae_imports` — a distinct function, not an in-place
rewrite, because `_pcae_imports` also backs an unrelated,
already-passing transitive-closure completeness check (`test_producer_
pair_reaches_no_unbound_pcae_module`) whose correctness depends on
receiving only real module dotted names; naively concatenating `module.
name` for every `ImportFrom` alias there would fabricate non-module
strings (e.g. a genuine symbol import like `HATPTrustStoreError` turned
into a fake `...hatp_bootstrap.HATPTrustStoreError` "module") and
regress that check. `_pcae_import_targets` additionally records `f"{
node.module}.{alias.name}"` for each non-wildcard `ImportFrom` alias —
the conservative "package.name equals the protected producer path"
reading item 24 of this phase's own governing instruction requires,
since Python's own `from package import name` grammar cannot be
statically disambiguated between a submodule import and a symbol import
without executing the import (not attempted here). The two guard tests
that previously called `_pcae_imports` for producer-reachability
purposes now call `_pcae_import_targets` instead: `test_no_module_under_
src_pcae_imports_the_producer_at_ast_level` (the primary, unconditional
AST guard) and `test_certification_module_references_the_producer_only_
as_frozen_path_data` (the companion negative-direction check for `core/
hatp_mandatory_certification.py` specifically, which carried the
identical `node.module`-only gap in its own inline logic). A bare `from
<module> import *` cannot be proven to exclude the producer by static
AST alone; the repaired helper never treats this as silently safe —
`node.module` is still recorded as a hit, and additionally surfaced in a
second, dedicated "wildcard" set the guard tests treat as suspicious.
Full coverage (Import, ImportFrom, aliases, single- and multi-line,
multiple names, module-vs-symbol adjudication, wildcard, and negative
controls for path-string/comment/tuple-literal occurrences) is verified
in `tests/test_phase_149o_20l_7l_3_attack_matrix_and_ast_guard_narrow_
repair.py`. The 149O.20L.7L.2 test module's own `TestF7L5DeferredRows
CurrentlyFalse` and `TestASTGuardBlindSpot` classes are updated in place,
per that module's own original instruction to update rather than delete
these guards once the gap they document closes.

**§57.9 Whole-document stale-current-claim scan.** Beyond rows
33/34/36/37, this phase searched the full document for the same defect
class (old file/member counts, "not yet operative", "hard-coded
ceiling", "zero callers" language) outside archival "Contract
Repair/Amendment History — Phase 149O.XX" sections (each already marked
"descriptive/historical record of..." at its own start, and correctly
left untouched as accurate snapshots of that historical phase's own
state — e.g. §48-56's repeated "hard-coded `False` ceiling ...
unchanged" restatements are true of the phase each restates, not stale
claims about today). One additional live, non-archival hit was found and
repaired: `HMIC-REQ-145`'s own "Status: CLOSED" closure paragraph (§19)
stated, in the present tense, that its `implementation_scope_digest`
protection was "not yet mechanically enforced in production" because
`_FROZEN_AUTHORITY_BEARING_FILES` "still implements the pre-repair
twenty-four-file set" — the identical stale-count defect class as rows
33/34/36/37, now corrected to state the closure is mechanically
enforced in production, since Phase 149O.20L.7K realigned that constant
to the current thirty-file set. No other live, non-archival hit was
found; the top-of-document intro paragraph (§0, "the current hard-coded
... ceiling ... is unchanged") and `HMIC-REQ-114`/`HMIC-REQ-075`/attack
row 4 were independently read and classified HISTORICAL AND TRUE IN
CONTEXT or NORMATIVE-REQUIREMENT-TEXT (a live `SHALL`, not a stale
factual claim) respectively, per this phase's own item 12 ("STOP" rule
for any repair that would touch normative `SHALL`/`MUST` text) and item
45 (do not rewrite historical facts elsewhere merely to normalize
terminology) — left unmodified, deferred, not silently ignored.

**§57.10 Same-version discipline confirmed.** No `HMIC-REQ-###` text was
added, removed, or reworded. `HMIC-REQ-050`'s thirty-file enumeration and
exact member list are unchanged (byte-identical before/after,
confirmed §57.11). `HMIC-REQ-052`'s three limbs and their scope are
unchanged. `HMIC-REQ-145`'s own normative first two paragraphs (the
finding statement and the repair mechanism) are unchanged; only its
closure paragraph's mechanical-enforcement-status prose was corrected.
No `src/pcae/**` file was modified by this phase. `HMIC-001` remains
v1.4 — this is a same-version repair, mirroring §52's (149O.20D.1),
§54's (149O.20L.1A), and §56's (149O.20L.7L.1) precedent exactly: a
defect discovered post-freeze, corrected in place, with no requirement
widened or narrowed. No certification, activation, `DeploymentBinding`
creation, `RepositoryIdentity` creation, first-use election, or Dell
access occurred.

**§57.11 Byte-identity and digest proofs.** `src/pcae/core/hatp_
mandatory_cutover.py`, `src/pcae/core/hatp_mandatory_certification.py`,
`src/pcae/core/hatp_class_b_topology_verifier.py`, `src/pcae/core/hatp_
environment_lock_verifier.py`, `src/pcae/core/hatp_class_b_conformance.
py`, `src/pcae/core/hatp_deployment_binding_admin.py`, and `scripts/
hatp_deployment_binding_admin.py` are confirmed byte-identical against
this phase's own entry commit (`git diff --name-only origin/main...HEAD
-- src/pcae/` returns empty, checked in CI-equivalent test form). `HMIC-
REQ-050`'s thirty-file enumeration, entry-for-entry, is confirmed
unchanged. `implementation_scope_digest`, recomputed live against the
real repository both before and after this phase's edits, is unchanged
(`65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8`) —
this document is not itself a member of its own frozen thirty-file set,
so a contract-document-only edit does not enter this digest.
`derive_contract_versions`, recomputed after the repair, still returns
the unchanged five-member set.

**§57.12 Verdict.** **F-7L-5 (rows 33/34/36/37): REPAIRED — INDEPENDENT
VERIFICATION PENDING — NOT CLOSED.** **F-7L-5 (row 38): unaffected,
remains REPAIRED — INDEPENDENT VERIFICATION PENDING** (149O.20L.7L.1).
**F-7L-7: REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED**
(test-only; no production source touched). The 7J §31 HMIC
frozen-source-membership finding remains **REPAIRED AT THE
CONTRACT-AND-PRODUCTION LAYER — INDEPENDENT VERIFICATION PENDING — NOT
CLOSED**, exactly as §56.13 left it; this phase's own text repair does
not itself close it — only a clean 149O.20L.7L.4 may. `HMIC-001` remains
v1.4. `HMIC-REQ-050`'s thirty-file enumeration is unchanged. No
production source was modified. No `DeploymentBinding` was created. No
`RepositoryIdentity` was created. No first-use election was initiated.
No Boundary C or Boundary A work occurred. Dell was not accessed. HATP
production remains **NOT READY**. Runtime remains **Observed / observe
/ unavailable**.

**Recommended next phase.** **149O.20L.7L.4 — Attack-Matrix and
AST-Guard Narrow Repair Independent Verification**, which must
independently verify, without trusting this section's narrative: every
corrected row (§57.3-§57.6); the whole-document stale-current-claim
scan's completeness, including the `HMIC-REQ-145` correction (§57.9);
the AST guard's `ImportFrom` coverage, multiline coverage, alias
handling, module-vs-symbol adjudication, and wildcard adjudication
(§57.8); that no path-string/comment/tuple-literal occurrence produces a
false positive (§57.8); the unchanged thirty-member source scope and
unchanged `implementation_scope_digest` (§57.11); and that no production
behavior changed (§57.10-§57.11). Only after a clean 149O.20L.7L.4 may
the 7J §31 finding be closed, and only after that may a separate,
separately-governed phase decide the first-use sequencing architecture
(redeploy-first vs. SHA-bound election vs. two-CHGR). No binding,
election, certification, redeployment, or Dell mutation is authorized by
149O.20L.7L.3 or by 149O.20L.7L.4.

---

## 58. Contract Repair History — Phase 149O.20L.7L.5 (Findings from 149O.20L.7L.4's Independent Verification)

**Status of this section:** descriptive/historical record of the repair;
it introduces no new `HMIC-REQ-###` identifier, widens no requirement,
and narrows no requirement. `HMIC-001` remains v1.4.

**§58.1 Repair — top-of-document §0 preamble.** 149O.20L.7L.4
independently found that 149O.20L.7L.3's own §57.9 whole-document scan
misclassified the §0 intro paragraph's "The current hard-coded
`mandatory_consumption_implementation_independently_verified = False`
ceiling ... is unchanged" sentence as historical, when it in fact
restated — in the present tense, outside any archival "Phase 149O.XX"
history section — the identical stale defect class rows 33/34/36/37
already corrected: the literal hard-coded `False` ceiling this sentence
described no longer exists at `hatp_mandatory_cutover.py:842-853`,
superseded by Phase 149O.19.5F (Wave F)'s dynamic call to
`validate_active_hatp_mandatory_independent_verification_certification`.
Repaired in place, same version: the sentence now names the current
mechanism (a fresh, uncached, fail-closed validator call, mapped via
exact `CertificationStatus.VALID` identity) and states, without
overstating, that the functional outcome is unchanged — this readiness
term still evaluates `False` today, because no stored HMIC certification
exists anywhere on this host (§61) — explicitly disclaiming any
inference of HMIC certification, HATP activation readiness, Boundary C
completion, first use, or `DeploymentBinding` existence. No other live,
non-archival stale-current-claim hit was found by this phase's own
independent whole-document re-scan (§48's "Explicit Confirmations"
section and §49-57's phase-history sections remain correctly classified
HISTORICAL AND TRUE IN CONTEXT, each restating its own named phase's
snapshot in the past tense; `HMIC-REQ-114`/`HMIC-REQ-075`/attack row 4
remain correctly classified NORMATIVE-REQUIREMENT-TEXT, unaffected).

**§58.2 Repair — AST guard relative-import blind spot.**
`_pcae_import_targets` (`tests/test_phase_149o_20l_7l_hmic_frozen_
source_scope_amendment_independent_verification.py`) filtered every
detected import target to a `pcae.`-prefixed name, but a relative
`ast.ImportFrom` node's `.module` is never `pcae.`-prefixed by itself
(e.g. `"errors"`, or `None` for `from . import x`) — every relative
import of the `DeploymentBinding` producer was silently invisible to
both critical producer-reachability guards. Relative imports are a live
convention elsewhere in this codebase (`schema_runtime/**`, 29
instances), not a theoretical gap. Repaired: a new canonical
file-path-to-dotted-module-name derivation (`_module_name_for_path`)
and a Python-relative-import-algorithm-faithful base resolver
(`_resolve_relative_import_base`) resolve every relative `ImportFrom`
node (`node.level >= 1`) to its absolute dotted target before the
existing absolute-import logic runs unchanged on the resolved name.
Covers level-1 (`from . import x`, `from .x import y`) and multilevel
(`from ..pkg import x`) forms, aliasing, single- and multi-line/
parenthesized forms, and multiple imported names per statement,
identically to the existing absolute-import coverage. A relative import
that climbs above the `pcae` package root, or that occurs in a file with
no derivable module context, fails closed into the wildcard/suspicious
set as a synthetic `<unresolved-relative ...>` entry — never silently
treated as "no import found" (mirrors the existing wildcard-import
fail-closed precedent, §57.8). Test/evidence code only; no production
source changed.

**§58.3 Repair — second critical guard still on the blind helper.**
`test_admin_script_is_the_only_non_test_caller_of_the_producer_entry_
points`, a second, broader critical producer-reachability guard co-located
in the same test module, still called the un-widened `_pcae_imports`
after 149O.20L.7L.3 introduced `_pcae_import_targets` and migrated only
`test_no_module_under_src_pcae_imports_the_producer_at_ast_level` to it.
Migrated in place to `_pcae_import_targets`, mirroring that earlier
migration's own precedent exactly — an actual switch of which helper
inspects the import targets, not a re-scoped expected-caller list. This
guard now also surfaces any wildcard/unresolved-relative hit as an
unexpected-importer finding, identical in kind to the other guard.

**§58.4 Helper inventory at close.** `_pcae_imports` (the original,
`.names`-blind, absolute-only helper) is retained, unmodified: it still
backs `test_producer_pair_reaches_no_unbound_pcae_module`, an unrelated
completeness check over the producer pair's own outbound dependencies
(§57's own docstring rationale for keeping the two helpers distinct,
unaffected by this repair) — not a producer-reachability guard, and
therefore not a defect this phase's scope covers (item 34: no
unnecessary test refactor). No other test module's own local
`_pcae_imports`-style reproduction (`test_phase_149o_19_3_hmic_contract_
independent_verification.py`, `test_phase_149o_19_3r_hmic_frozen_file_
set_contract_repair.py`) references the `DeploymentBinding` producer at
all — both predate its existence and check an unrelated, already-closed
v1.0 frozen file set; left untouched. The 149O.20L.7L.3/149O.20L.7L.4
test modules' own historical reproductions of the pre-repair helper
(`_old_pcae_imports`, and 7L.4's own read of `_GUARD_MODULE._pcae_
imports`) are deliberately preserved, unmodified, as regression evidence
of the gap's own history — not live guards.

**§58.5 Same-version discipline confirmed.** No `HMIC-REQ-###` text was
added, removed, or reworded. `HMIC-REQ-050`'s thirty-file enumeration
and exact member list are unchanged (byte-identical before/after).
`HMIC-REQ-052`'s three limbs and their scope are unchanged. Attack rows
33/34/36/37/38/39 and `HMIC-REQ-145`'s closure paragraph are unchanged
(byte-identical before/after, confirmed by test). No `src/pcae/**` file
was modified by this phase. `HMIC-001` remains v1.4 — a same-version
repair, mirroring §52/§54/§56/§57's precedent exactly: a defect
discovered post-freeze/post-verification, corrected in place, with no
requirement widened or narrowed.

**§58.6 Byte-identity and digest proofs.** `implementation_scope_digest`,
recomputed live against the real repository both before and after this
phase's edits, is unchanged
(`65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8`) —
neither this document nor the test module edited by this phase is a
member of the frozen thirty-file set, so a contract-document-only or
test-only edit does not enter this digest. `git diff --name-only
<pre-7L.5>...HEAD -- src/pcae/` is empty. `derive_contract_versions`
still returns the unchanged five-member set.

**§58.7 Verdict.** **F-7L-5 (whole-document scan, §0 preamble):
REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED.** **F-7L-5
(rows 33/34/36/37/38, HMIC-REQ-145): unaffected, remain REPAIRED —
INDEPENDENT VERIFICATION PENDING**, unchanged from §57.12/§56.13.
**F-7L-7 (relative-import gap and second-guard migration): REPAIRED —
INDEPENDENT VERIFICATION PENDING — NOT CLOSED.** The 7J §31
frozen-source-membership finding remains **REPAIRED AT THE
CONTRACT-AND-PRODUCTION LAYER — INDEPENDENT VERIFICATION PENDING — NOT
CLOSED**; this phase's own text-and-test repair does not itself close
it — only a clean 149O.20L.7L.6 may. `HMIC-001` remains v1.4.
`HMIC-REQ-050`'s thirty-file enumeration is unchanged. No production
source was modified. No `DeploymentBinding` was created. No
`RepositoryIdentity` was created. No first-use election was initiated.
No Boundary C or Boundary A work occurred. Dell was not accessed. HATP
production remains **NOT READY**. Runtime remains **Observed / observe
/ unavailable**.

**Recommended next phase.** **149O.20L.7L.6 — Contract-Preamble and
Relative-Import Guard Repair Independent Verification**, which must
independently verify, without trusting this section's narrative: the §0
preamble correction's accuracy and non-overstatement (§58.1); the
whole-document stale-current-claim scan's completeness; relative-import
resolution at level 1 and multiple levels, module-context derivation,
alias/multiline/multi-name handling, wildcard adjudication, and
escape-root adjudication (§58.2); that absolute-import detection has no
regression; negative controls; that both critical producer-reachability
guards use the repaired resolver (§58.2/§58.3); that no dynamic
producer-reachability path exists; the unchanged thirty-member source
scope and unchanged `implementation_scope_digest` (§58.5-§58.6); and
that no production behavior changed. Only after a clean 149O.20L.7L.6
may the 7J §31 finding close, and only after that may a separately-
governed phase decide the first-use sequencing architecture. No binding,
election, certification, redeployment, or Dell mutation is authorized by
149O.20L.7L.5 or by 149O.20L.7L.6.

---

## 59. Contract Amendment History — Phase 149O.20L.7O.2H (v1.5)

**Status of this section:** descriptive/historical record of the
149O.20L.7O.2H contract-and-production amendment, appended without
modifying the original v1.0 freeze narrative (§0-48), §49-52's v1.0/
v1.1/v1.2 history, §53's v1.3 amendment, §54's repair record, §55's v1.4
amendment, or §56-58's repair records.

**Context.** By 149O.20L.7O.2G.1, an inconsistency in 149O.20L.7O.2G's
own arithmetic (§9.1 counted only the three new Python source additions,
33 total, while §9.2/§10 of the same report already concluded HPSE-001
and HHCE-001 required both content and version binding, an obligation
that adds two more entries) was reconciled: the exact future target is
**35** frozen authority-bearing files (26 `src/pcae/`-relative + 9
repository-root-relative) and **7** `contract_versions` members, not 33.
This section records 149O.20L.7O.2H's independent re-verification of
that reconciled target against the live current source and contract
tree, and its combined contract amendment **and** production alignment
in the same phase, mirroring the 149O.20L.7K precedent (§55) rather than
149O.20K's split contract-then-alignment sequencing (§53/§53.12).

**§59.1 Independent reconstruction of HMIC-REQ-052 (as it stood at
v1.4).** Before drafting limb (d), this phase re-read HMIC-REQ-052 from
this document directly (not from 2G/2G.1's summary). At v1.4, the
closure rule bound a PCAE-owned file only if reachable, transitively,
from: (a) `assess_hatp_mandatory_activation_readiness`'s own call graph;
(b) `validate_active_hatp_mandatory_independent_verification_
certification`'s call graph, or the Protected Admin ceremony functions
`certify`/`activate`/`revoke`; or (c) `verify_class_b_deployment_
conformance`'s own call graph, or the `DeploymentBinding` producer/
admin-ceremony pair as a non-reachability anchor. A direct text search
confirms none of limbs (a)/(b)/(c) as their v1.4 text reads reaches
`core/hatp_signing_ceremony.py`, `core/hatp_hardware_credential_
admin.py`, or `core/hatp_principal_signer_admin.py`: `hatp_mandatory_
cutover.py` (limb (a)'s anchor module) only checks `hatp_signing_
ceremony`'s importability, never calling into its functions, and none of
limbs (a)/(b)/(c)'s named entry points import any of the three files.
This is a genuine scope gap, structurally identical in shape to limb
(c)'s original gap (§53.1) — a new authority-sensitive production
surface with no existing call-graph anchor — requiring a new limb, not a
file-list realignment under existing text.

**§59.2 Independent reconstruction of the current 30/5 identity.** Read
directly from `src/pcae/core/hatp_mandatory_certification.py`, as it
stood immediately before this phase's own production edit (phase-entry
commit `e65b4ce0`): `_FROZEN_SRC_PCAE_RELATIVE_FILES` (23 entries) +
`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` (7 entries, the five bound
contract documents plus the two Protected Admin ceremony scripts) =
`_FROZEN_AUTHORITY_BEARING_FILES`, `assert`-pinned at exactly 30 in the
module itself. Compared entry-for-entry against this document's own
pre-amendment HMIC-REQ-050 text: identical, in the same order,
confirming production and contract were already in alignment at 30/5
before this phase. `_CONTRACT_IDENTITY_FILES` independently read:
exactly five `(contract_id, path)` pairs — `HMRC-001`, `HATP-001`,
`HSCE-001`, `RAE-001`, `HBDC-001` — matching HMIC-REQ-067, the
pre-amendment baseline this phase widens from.

**§59.3 Fresh static dependency graph — the three Trust-Enrollment/
signing files.** An `ast`-based import walk (direct `grep -n "^from
pcae\|^import pcae"` against the live current bytes, re-verified against
2G/2G.1's own AST-walk claims byte-for-byte) was run independently.
Results:

- `core/hatp_signing_ceremony.py`: `pcae.core.agent`, `pcae.core.hatp_
  bootstrap`, `pcae.core.hatp_evidence_store`, `pcae.core.hatp_hardware_
  credentials`, `pcae.core.hatp_providers`, `pcae.core.hatp_signed_
  evidence`, `pcae.core.human_approval_trusted_provenance`, `pcae.core.
  paths`, `pcae.core.repository_identity`, `pcae.core.rollback_approval_
  evidence`.
- `core/hatp_hardware_credential_admin.py`: `pcae.core.hatp_hardware_
  credentials`, `pcae.core.paths`, `pcae.core.provenance`.
- `core/hatp_principal_signer_admin.py`: `pcae.core.hatp_bootstrap`,
  `pcae.core.hatp_deployment_binding_admin`, `pcae.core.hatp_hardware_
  credential_admin`, `pcae.core.hatp_hardware_credentials`, `pcae.core.
  hatp_providers`, `pcae.core.paths`, `pcae.core.provenance`.

Every import target other than `pcae.core.paths` and `pcae.core.
provenance` is already a bound HMIC member (`agent.py`, `hatp_
bootstrap.py`, `hatp_evidence_store.py`, `hatp_hardware_credentials.py`,
`hatp_providers.py`, `hatp_signed_evidence.py`, `human_approval_trusted_
provenance.py`, `repository_identity.py`, `rollback_approval_evidence.
py`, `hatp_deployment_binding_admin.py`, and, among the three new files
themselves, `hatp_hardware_credential_admin.py`). No candidate imports
`commands/hatp.py`, and `commands/hatp.py` imports none of the three
candidates' authority-computation entry points either — CLI dispatch
only, correctly excluded, exactly as 2G's own analysis found.

**§59.4 Semantic dependency check and anchor confirmation.**
`production_sign_rollback_evidence` (line 889 of `hatp_signing_
ceremony.py`) is confirmed, by direct read, as the module's sole
production signing-ceremony entry point (exported in `__all__`,
consuming `resolve_signing_context` and the module's provider/evidence
plumbing). `register_credential`/`revoke_credential` (`hatp_hardware_
credential_admin.py`) and `enroll_principal`/`revoke_principal`/
`enroll_signer`/`revoke_signer` (`hatp_principal_signer_admin.py`) are
confirmed as the two writers' registration/revocation mutating
operations. Text search of `src/` for `hatp_hardware_credential_admin`/
`hatp_principal_signer_admin` (module names), excluding the files
themselves and their own test modules, finds only `hatp_principal_
signer_admin.py`'s own import of `hatp_hardware_credential_admin` (§59.3
— an internal cross-reference within the new triad, not a call from any
existing limb (a)/(b)/(c) anchor) and CLI dispatch in `commands/hatp.py`
— confirming, as limb (d)'s text states, that the two writers are not
reachable from `production_sign_rollback_evidence`'s own call graph and
require the dual-anchor construction mirroring limb (c)'s own precedent
(§55.1).

**§59.5 Dependency classification.**

- **Category A (PCAE-owned, authority-sensitive — bind).** The three
  root files themselves. `hatp_signing_ceremony.py`'s `production_sign_
  rollback_evidence` decides whether a rollback-approval-evidence
  signing operation proceeds, resolving signer/provider/credential state
  and constructing the signed evidence envelope — a byte edit here (e.g.
  loosening signer/provider consistency, or skipping a hardware
  assertion check) changes what signing outcome is durably recorded
  without changing any pre-v1.5 HMIC-bound digest. `hatp_hardware_
  credential_admin.py`'s `register_credential`/`revoke_credential` and
  `hatp_principal_signer_admin.py`'s `enroll_principal`/`revoke_
  principal`/`enroll_signer`/`revoke_signer` each independently decide
  whether a registration/enrollment/revocation write proceeds and what
  authority-bearing field values the resulting record carries — the
  identical authority-sensitivity test HMIC-REQ-052(c)'s third anchor
  already applies to the `DeploymentBinding` producer (§55.5 Category A),
  applied here under limb (d)'s own dual-anchor construction.
- **Category B (PCAE-owned, non-authority-sensitive — exclude).**
  `pcae.core.paths` (`HarnessPath`) — the identical exclusion already
  named for limbs (a)/(b)/(c) (§49/§50/§53/§55). `pcae.core.provenance`
  (`append_provenance_event`) — the identical exclusion §55.5 already
  established for the `DeploymentBinding` producer: it appends an
  audit-log record strictly after the writer's own mutation and
  read-back verification already succeed, and cannot alter what record
  is written. `pcae.core.git_status` and `pcae.core.tasks` — reached
  only transitively, via `provenance.py`'s own narrow call, for a single
  audit-event field each (current-branch name; latest-active-task
  glob-and-parse); neither gates, rejects, alters, or influences a
  Trust-Enrollment/signing authority decision, and the call-graph unit
  of analysis is the specific symbol called, not whole-module import,
  matching this contract's own established methodology (§49, §55.5).
- **Category C (standard library — do not bind, disclose residual
  trust).** Unchanged from every prior amendment's disposition —
  HMIC-REQ-065 already names the Python interpreter/standard library as
  an explicit, out-of-scope transitive-dependency boundary.
- **Category D (external/system — not applicable).** Neither of the
  three files invokes an external binary or subprocess.
- **Category E (contract/document inputs).** None of the three files
  reads any `docs/contracts/**` document's bytes at runtime. `HPSE-001`/
  `HHCE-001`'s normative text informed the writers' human-authored
  implementation but is not a runtime dependency of them — their
  document bytes are bound separately, under HMIC-REQ-053, not as a
  limb (d) call-graph dependency (§59.16).

**§59.6 Worked verdict-influence chain.** `scripts/hatp_certification_
admin.py`'s ceremony functions and `hatp_mandatory_cutover.py`'s
readiness assessment are unaffected by this phase's own three new files
directly; the relevant chain limb (d) closes is: an operator or
automated caller invokes `hatp_signing_ceremony.py::production_sign_
rollback_evidence`, which resolves the signer/credential/principal state
that `hatp_hardware_credential_admin.py`/`hatp_principal_signer_
admin.py`'s writers durably produced via already-frozen `hatp_bootstrap.
py`/`hatp_hardware_credentials.py` read/write primitives — every step of
this chain is either already HMIC-bound or newly bound by this phase; no
unbound step remains (§59.9 restates this as the full transitive
coverage matrix).

**§59.7 Self-binding / cycle check.** Independently confirmed by
import-graph inspection (§59.3): none of the three new files imports
`hatp_mandatory_certification.py` or `scripts/hatp_certification_
admin.py`, and neither of those two imports any of the three new files.
No HMIC validator/admin self-reference, no digest-construction cycle is
introduced. Class-B/`DeploymentBinding` binding (§53/§55) is likewise
undisturbed: `hatp_principal_signer_admin.py` imports `hatp_deployment_
binding_admin.py` (§59.3) — a read-only dependency on an already-frozen
module, not a new binding decision, since `hatp_deployment_binding_
admin.py` has been HMIC-bound since v1.4 (§55).

**§59.8 Regression: B-149O.19.3-1, B-149O.20D-1, CBV-S1/CBV-third-anchor
unchanged.** Independently re-confirmed that the four B-149O.19.3-1
provider files, `HBDC-001`, the three Class-B verifier files, and the
`DeploymentBinding` producer pair all remain present, unremoved, and
unmodified by this phase's own edits to `_FROZEN_SRC_PCAE_RELATIVE_
FILES`/`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`. `HBDC-001` continues
receiving both its `contract_versions` and `implementation_scope_digest`
bindings, unchanged.

**§59.9 Full transitive authority-bearing coverage matrix (Trust-
Enrollment/signing authority path).**

| Component | HMIC-frozen? | Anchor | Evidence |
|---|---|---|---|
| `core/hatp_signing_ceremony.py` | Yes, as of v1.5 | limb (d), first anchor | §59.5 Category A, §59.4 |
| `core/hatp_hardware_credential_admin.py` | Yes, as of v1.5 | limb (d), second (non-reachability) anchor | §59.5 Category A, §59.4 |
| `core/hatp_principal_signer_admin.py` | Yes, as of v1.5 | limb (d), second (non-reachability) anchor | §59.5 Category A, §59.4 |
| `docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md` (HPSE-001) | Yes, as of v1.5 | HMIC-REQ-053 content binding (not limb (d)) | §59.16 |
| `docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md` (HHCE-001) | Yes, as of v1.5 | HMIC-REQ-053 content binding (not limb (d)) | §59.16 |
| `hatp_bootstrap.py`, `hatp_evidence_store.py`, `hatp_hardware_credentials.py`, `hatp_providers.py`, `hatp_signed_evidence.py`, `human_approval_trusted_provenance.py`, `repository_identity.py`, `rollback_approval_evidence.py`, `agent.py`, `hatp_deployment_binding_admin.py` | Yes, since v1.1/v1.4 | limb (a)/(b)/(c) | §49/§50/§55, §59.3 baseline |
| Audit sink (`pcae.core.provenance`) | No — intentionally excluded | n/a | §59.5 Category B |
| Path value type (`pcae.core.paths`) | No — intentionally excluded | n/a | §59.5 Category B |
| Branch-name reader (`pcae.core.git_status`) | No — intentionally excluded | n/a | §59.5 Category B |
| Active-task reader (`pcae.core.tasks`) | No — intentionally excluded | n/a | §59.5 Category B |

Every executable component in the sign/register/enroll-to-verdict chain
is either frozen directly (this phase's three source entries), already
frozen as a dependency, or intentionally outside scope with documented
rationale — no unaccounted component remains.

**§59.10 Contract-version widening.** Unlike §55.10 (the v1.4 amendment,
which added zero `contract_versions` members), this phase widens
`contract_versions` from five to seven, adding `HPSE-001` and
`HHCE-001` — the governing contracts for the two new writer files. This
is not a source-file realignment but a genuine new-contract admission,
required by HMIC-REQ-053's own existing, current text ("no
`contract_versions` member is exempted from the digest binding," §4 of
149O.20L.7O.2G.1's own reconciliation): the moment HPSE-001/HHCE-001
join `contract_versions`, their document bytes are mechanically required
to also join `implementation_scope_digest` — this is a consequence of
HMIC-REQ-053's existing text, not a new discretionary choice made by
this phase.

**§59.11 HPSE-001/HHCE-001 unchanged proof.** Both contract documents
were read in full before and after this phase's edits to this document
(`HMIC-001` itself, a distinct file) and to `hatp_mandatory_
certification.py`; byte-identical in both comparisons (`git diff`
against the phase-entry commit shows zero lines changed in either
path). This phase binds HPSE-001 v1.1/HHCE-001 v1.1's existing bytes; it
does not edit them, and does not edit the three Trust-Enrollment/signing
source files either — all five newly-bound entries are the objects being
bound, not objects modified to be bound (confirmed by SHA-256
comparison, §59.13).

**§59.12 Over-binding / under-binding threat analysis.** *Under-binding*:
if `hatp_hardware_credential_admin.py`/`hatp_principal_signer_admin.py`
were omitted while only `hatp_signing_ceremony.py` were bound, an edit
to either writer (e.g. weakening `_validate_enrollment_evidence`) could
durably corrupt hardware-credential/principal/signer state that the
signing ceremony's own bound bytes would then faithfully, but
incorrectly, consume — the same closure-violation shape §55.12 already
demonstrated for the `DeploymentBinding` producer pair, now demonstrated
for this triad. If the contract documents were version-bound but not
content-bound (the same shape as `HBDC-001`'s original v1.2 gap,
B-149O.20D-1, §52), a same-version content-only edit to either contract
would go certification-invisible — exactly the reconciliation this
section closes by binding both mechanisms from admission (§59.10).
*Over-binding*: `pcae.core.paths`, `pcae.core.provenance`, `pcae.core.
git_status`, and `pcae.core.tasks` were all inspected and excluded
(§59.5) rather than bound by proximity, preserving this contract's own
minimality precedent (§53.9/§53.11/§55.12). No PCAE-owned file beyond
the three Trust-Enrollment/signing roots was found reachable at all
(§59.3-§59.4), so there was no broader candidate set to prune from.

**§59.13 Implementation-unchanged proof.** SHA-256 of all three new
source files and both new contract documents, computed immediately
before this phase's first edit and again immediately before this
phase's finalization commit, are identical for all five — this phase's
own production edit is confined to `hatp_mandatory_certification.py`'s
frozen-set constants and this contract document; none of the five newly
bound files is touched. Digest sensitivity was independently tested in a
disposable worktree/copy: a single-byte perturbation to each of the five
newly-frozen files changes `derive_implementation_scope_digest`'s output
once the file is a frozen member; the identical perturbation against the
pre-amendment (30-file) constant set does not change the digest for the
three new source files, and against the pre-amendment (5-member)
`_CONTRACT_IDENTITY_FILES`/30-file frozen set does not change the digest
for the two new contract documents — confirming the omission was real
before this phase and is closed after it. A control perturbation against
a disposable, clearly non-authority-bearing file changes neither the
pre- nor post-amendment digest. No duplicate logical path exists in the
widened thirty-five-entry set. All thirty-five canonical paths resolve
to existing, non-symlinked, regular files on this repository's current
worktree.

**§59.14 Contract-version determination.** This amendment widens
HMIC-REQ-050's enumeration (30 → 35 entries), widens HMIC-REQ-052 with a
new limb (d), and widens `contract_versions` (HMIC-REQ-067, 5 → 7
entries) — a normative-scope change of the same shape as the v1.0 → v1.1
amendment (§50, which added limb (b) and two files) and the v1.2 → v1.3
amendment (§53, which added a new limb and three files), not the shape
of a within-version repair. No existing requirement's meaning is
narrowed; no existing consumer's expectation is broken — every prior
mechanism continues to apply unmodified to a longer file list and a
larger contract-version set. Following this repository's own
established minor-bump convention for scope-widening amendments, this
amendment is `HMIC-001 v1.4 → v1.5`, an in-place minor version bump, not
v2.0 (no existing field, schema, or algorithm is redefined or removed)
and not a same-version repair.

**§59.15 Verdict.** HMIC-001 v1.5: contract-evolved **and**
production-aligned in the same phase, per the 149O.20L.7K precedent
(§55.16/§55.14's own conditions — the added members are already fully
built and stable, `hatp_mandatory_certification.py` computes its digest
fresh at read time with no caching hazard, and no certification exists
on this host to invalidate mid-flight — all independently reconfirmed
for this phase by §59.11/§59.13). Closure limb (d) added with a dual
(reachability + non-reachability) anchor construction, mirroring limb
(c)'s own precedent (§55.1); HMIC-REQ-050 widened to thirty-five files
(26 `src/pcae/`-relative + 9 repository-root-relative); `contract_
versions` (HMIC-REQ-067) widened to seven members (§59.10),
content-and-version-binding `HPSE-001`/`HHCE-001` from admission, never
as a deferred exception. Production `_FROZEN_AUTHORITY_BEARING_FILES`/
`_CONTRACT_IDENTITY_FILES` are realigned to 35/7 by this same phase
(§59.13, §59.16). `B-149O.20L.7O.2G-1` (HMIC Target-Set / Contract-
Content Binding Reconciliation Gap): **ALIGNED — 35-MEMBER CONTENT/
SOURCE IDENTITY IMPLEMENTED — 7-MEMBER CONTRACT IDENTITY IMPLEMENTED —
INDEPENDENT VERIFICATION PENDING — NOT CLOSED** (only a future
independent-verification phase may close it). `W-1`, `B-149O.19.3-1`,
`B-149O.20D-1`, CBV-S1, and the `DeploymentBinding` producer's third
anchor remain independently closed/repaired/bound exactly as prior
sections left them (§59.8). BF-1, BF-2, `B-149O.20L.7O.2F.3-1`, and
`B-149O.20L.7O.2F.3-2` are unaffected — this phase's finding concerns
HMIC identity-binding scope only, orthogonal to implementation
correctness, and were independently reconfirmed unchanged by
149O.20L.7O.2G.1 immediately prior to this phase's own entry. No
`DeploymentBinding` was created. No real hardware was provisioned. No
real Principal was enrolled. No real Signer was enrolled. No HMIC
certification was created or activated. No HATP activation was
performed. CBV-S10 remains **OPEN**, untouched. Runtime remains
**Observed / observe / unavailable**.

**§59.16 HPSE-001/HHCE-001 content binding — separate from limb (d).**
Consistent with §16's general rule (contract documents are never a
closure-limb source), limb (d)'s text (§17) explicitly does not name
`HPSE-001`/`HHCE-001`'s own contract bytes as call-graph dependencies of
`production_sign_rollback_evidence` or the two writer entry points. Both
documents' bytes are instead bound via HMIC-REQ-053's separate,
distinct rule, uniformly applied the moment both contracts join
`contract_versions` (§59.10) — the same two-mechanism separation this
contract's own architecture has maintained since v1.0 (§16), and the
same reconciliation 149O.20L.7O.2G.1 already derived independently
before this phase began (its own §16).

**§59.17 Production alignment (this phase, not deferred).** This phase
updates `hatp_mandatory_certification.py`'s `_FROZEN_SRC_PCAE_RELATIVE_
FILES` (append `core/hatp_signing_ceremony.py`, `core/hatp_hardware_
credential_admin.py`, `core/hatp_principal_signer_admin.py`),
`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` (append `docs/contracts/
HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md`, `docs/contracts/
HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md`, in the presentation
order established by HMIC-REQ-050 — after `HBDC-001` and before the two
`scripts/` entries), and `_CONTRACT_IDENTITY_FILES` (append `HPSE-001`,
`HHCE-001`), widening the module's own `assert len(_FROZEN_AUTHORITY_
BEARING_FILES) == 30` to `== 35`, in this same phase, per the
149O.20L.7K precedent (§55.16/§55.14). `hatp_mandatory_certification.py`
is itself already a frozen member (since v1.1, §50); this phase's edit
to it therefore changes `implementation_scope_digest` twice over — once
because its own bytes changed, and once because the file set it
enumerates grew — both expected and independently confirmed (§59.13).
This phase also inspected `_CONTRACT_VERSIONS_REQUIRED_KEYS` (a
separate, Wave-A-owned `CertificationRecord` closed-schema constant used
only by `_require_contract_versions`, distinct from Wave B's own
`_CONTRACT_IDENTITY_FILES`/`derive_contract_versions`), per this phase's
own governing scope's instruction to reconcile the contract-version
parser/required-key set. That inspection found `_CONTRACT_VERSIONS_
REQUIRED_KEYS` was, and remains, a historically four-member literal
(`HMRC-001`/`HATP-001`/`HSCE-001`/`RAE-001`) that had never itself been
widened to include `HBDC-001` when `_CONTRACT_IDENTITY_FILES` gained it
at v1.2 — a pre-existing drift 149O.20L.7O.2G's own analysis first
disclosed and 149O.20L.7O.2G.1 independently reconfirmed present,
unchanged, and explicitly out of that phase's own scope ("non-blocking,
unrelated, unrepaired ... a pre-existing drift 2G already correctly
flagged as out of this scope"). This phase widens `_CONTRACT_VERSIONS_
REQUIRED_KEYS` strictly additively, by this phase's own two new members
only (`HPSE-001`, `HHCE-001`, four → six), leaving the pre-existing,
already-disclosed `HBDC-001` gap untouched, exactly as 149O.20L.7O.2G.1
left it — closing that unrelated, pre-existing drift is not within this
phase's own additive, limb-(d)-scoped charter (item 41 of this phase's
own governing scope: "Do not opportunistically rewrite HMIC[-adjacent
production code beyond stated scope]"; the closure-limb (d)/contract-
content-binding widening this phase performs is a distinct concern from
an unrelated Wave-A schema constant's own pre-existing bug) and is
deferred to a future, separately-governed repair phase, which this
section's own recommended-next-phase note (below) does not itself
authorize to begin. `derive_contract_versions` (Wave B) is unaffected by
this distinction and continues to return the full, correct seven-member
mapping (§59.10); only the separate Wave A closed-schema *acceptance*
set for a stored `CertificationRecord` is widened by two, not
reconciled to include `HBDC-001` (§59.19).

**§59.18 Digest-sensitivity, contract-version-sensitivity, and
certification-compatibility tests (mechanical evidence).** A dedicated
disposable-worktree/fixture-based test module independently proves, for
each of the five newly-bound files: (1) a same-version content-only byte
perturbation changes `implementation_scope_digest`; (2) removing a
required newly-frozen member and recomputing fails closed
(`HMICIdentityDerivationError`/`FrozenFileDerivationError`); (3) for the
two contract documents, a live version-header change is independently
detected by `derive_contract_versions` (`ContractIdentityDerivationError`
on ID/header mismatch, a changed version string on legitimate revision);
(4) a same-version content-only edit to either contract changes
`implementation_scope_digest` while `derive_contract_versions` reports
the version unchanged — the identical HBDC-001 same-version-drift
protection (§4/§5 of 149O.20L.7O.2G.1, generalized from the HBDC-001
precedent, §52) now demonstrated for HPSE-001/HHCE-001; (5) a
synthetic, disposable `CertificationRecord` constructed with only the
pre-v1.5 five-member (or four-member) `contract_versions` set fails the
widened seven-member `_require_contract_versions`/`_CONTRACT_
VERSIONS_REQUIRED_KEYS` schema check, and a record with an unknown
eighth contract key likewise fails closed; (6) repeated `implementation_
scope_digest` derivation on an unchanged tree is deterministic across
calls.

**§59.19 Certification Record Closed Schema — six-member consequence,
distinct from Wave B's seven-member derivation.** `_CONTRACT_VERSIONS_
REQUIRED_KEYS` (§59.17) is widened by this phase's own two new members
only, to exactly six (`HMRC-001`/`HATP-001`/`HSCE-001`/`RAE-001`/
`HPSE-001`/`HHCE-001`) — the pre-existing `HBDC-001` gap is left
untouched, unchanged from 149O.20L.7O.2G.1's own reconfirmation. The
canonical `CertificationRecord` schema (HMIC-REQ-031/032) therefore
remains deterministic and closed at exactly six required keys as parsed
by `_require_contract_versions`: a valid new record must supply all six;
a record containing only a strict subset is rejected as `MALFORMED`
(missing required key); a record containing a seventh, unrecognized key
— including, still, `HBDC-001` itself, exactly as before this phase —
is rejected as `MALFORMED` (unknown key) — no optional/partial-validity
compatibility behavior is introduced, consistent with HMIC-REQ-031's
pre-existing closed-schema discipline and this contract's own
"no compatibility-mapping table exists" rule (HMIC-REQ-069). This is a
narrower, deliberately incomplete mirror of Wave B's own `derive_
contract_versions`, which correctly returns the full seven-member
mapping (§59.10) — the two mechanisms' divergence over `HBDC-001` is the
same pre-existing, disclosed drift named at §59.17, carried forward
unrepaired by this phase, not a new inconsistency this phase
introduces.

**Recommended next phase.** **149O.20L.7O.2H.1 — HMIC-001 v1.5
Trust-Enrollment/Signing Authority-Scope Alignment Independent
Verification**, which must independently reconstruct, without trusting
this section's narrative: HMIC-REQ-052 (pre- and post-amendment text,
§59.1); the current 30/5 production identity immediately before this
phase (§59.2); the Trust-Enrollment/signing triad's dependency graph
(static and semantic, §59.3-§59.4); the authority-sensitive/excluded
classification (§59.5); the full verdict-influence chain (§59.6); the
cycle/self-binding analysis (§59.7); the prior-finding regression
(§59.8); the full transitive coverage matrix (§59.9); `contract_
versions` widening (§59.10); HPSE-001/HHCE-001 byte-identity
preservation (§59.11); the over-/under-binding threat analysis (§59.12);
the digest-sensitivity/certification-compatibility proofs (§59.13,
§59.18); the v1.4 → v1.5 version-bump rationale (§59.14); the combined
production alignment, including the `_CONTRACT_VERSIONS_REQUIRED_KEYS`
reconciliation (§59.17); and the closed-schema consequence (§59.19).
149O.20L.7O.2H.1 does not authorize HMIC certification, HATP activation,
FIDO2 hardware provisioning, real Principal/Signer enrollment, real
`DeploymentBinding` creation, `hac-dell` mutation, Permission Broker/
runtime-capability change, PIV implementation, or CBV-S10 wiring — only
after it passes may a future, separately-governed phase decide the next
step in that sequence, not out of it.

## 60. Contract Amendment and Consistency Repair History — Phase 149O.20L.7O.2H.2 (v1.6)

**§60.1 Entering findings.** Phase 149O.20L.7O.2H.1 independently
demonstrated two Blocking defects in v1.5: `core/paths.py` was reached
by limb (d) authority paths but absent from HMIC-REQ-050, and current
HMIC-REQ-076 still described a four-contract creation ceremony despite
HMIC-REQ-067/069 and the repaired `CertificationRecord` schema requiring
exactly seven. This section records only the narrow repairs; it does not
independently verify them or authorize certification.

**§60.2 Symbol-level source closure.** The AG3 chain is
`production_sign_rollback_evidence` → `sign_rollback_evidence` →
`resolve_signing_context` → `_resolve_ag3_operation` →
`build_rollback_review` → `HarnessPath.join` → the live
`.pcae/remote/jobs/<job_id>.json` record → `original_commit_sha`. The
AG5 sibling is `resolve_signing_context` → `_resolve_ag5_operation` →
`lookup_promotion_execution_record` → `HarnessPath.path` → the live
promotion-execution record → `ecp_id`. Those record fields enter the
canonical signing context before confirmation and hardware touch.
Changing only `paths.py` can redirect either lookup without changing a
v1.5 frozen byte. `core/paths.py` is therefore authority-bearing under
HMIC-REQ-052(d), not a neutral value type, and joins HMIC-REQ-050
unchanged.

**§60.3 Prior-exclusion root cause and remaining leaves.** §59.5
substituted a whole-module “generic utility” label and prior exclusion
precedent for symbol-level behavioral closure. An imported dependency
is not absorbed by the caller's own byte binding: if its reached symbol
can select a signing input, its own bytes must be bound. The narrow
recheck does not overturn the other three leaves. `provenance.py` is
called by the two enrollment writers only after the authority mutation
and durable readback, to append audit evidence; its reached
`git_status.read_git_branch` and `tasks.find_latest_active_task` calls
populate audit metadata only. None gates, selects, or changes a
credential, Principal, Signer, signing context, provider, publication,
or protected registry record. They remain non-authority under limb (d).

**§60.4 Exact identity consequence.** The repair is additive:
`_FROZEN_SRC_PCAE_RELATIVE_FILES` grows 26 → 27;
`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` remains 9; total frozen
source/content identity grows 35 → 36 with no removal. All three v1.5
Trust-Enrollment/signing sources, both v1.5 contract-content additions,
all Class-B members, and both DeploymentBinding members remain bound.
`_CONTRACT_IDENTITY_FILES` and `_CONTRACT_VERSIONS_REQUIRED_KEYS`
remain the identical exact seven-ID set; no eighth contract is added.

**§60.5 Version determination.** Adding a new authority-bearing digest
input changes the normative certified implementation identity and
widens HMIC-REQ-050/052. That is the same minor scope-evolution shape as
v1.1/v1.3/v1.5, not an editorial same-version repair. The accompanying
HMIC-REQ-076 change restores consistency with already-current seven-key
semantics and does not change the schema or algorithm. The combined
amendment is therefore v1.5 → v1.6, not v2.0.

**§60.6 Seven-contract ceremony consistency.** HMIC-REQ-076 now
requires the tool to read each of the exact seven bound contracts' own
live version headers, matching HMIC-REQ-067/069,
`derive_contract_versions`, and the closed `CertificationRecord`
representation. It neither admits an eighth identity nor permits a
four/five/six-member legacy record. The pre-v1.6 35-member digest is
rejected first as `IMPLEMENTATION_MISMATCH` at §31 step 9 before the
unchanged seven-member comparison at step 10.

**§60.7 Finding disposition.** `B-149O.20L.7O.2H.1-1` is **REPAIRED —
PATHS SOURCE-SCOPE CLOSURE IMPLEMENTED — INDEPENDENT VERIFICATION
PENDING — NOT CLOSED**. `B-149O.20L.7O.2H.1-2` is **REPAIRED — CURRENT
SEVEN-CONTRACT CEREMONY SEMANTICS RESTORED — INDEPENDENT VERIFICATION
PENDING — NOT CLOSED**. `B-149O.20L.7O.2G-1` is **REALIGNED —
TRANSITIVE SOURCE CLOSURE REPAIRED — CONTRACT/PRODUCTION IDENTITY
UPDATED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED**.
`B-149O.20L.7O.2H-1` remains independently closed at the seven-member
CertificationRecord/contract-identity representation boundary.

**Recommended next phase.** **149O.20L.7O.2H.3 — HMIC-001 v1.6 Paths
Source-Scope Closure and Seven-Contract Ceremony Consistency Repair
Independent Verification.** No certification, provisioning, real
enrollment, real `DeploymentBinding`, readiness integration, HATP
activation, CBV-S10, PIV, or Stream-B work is authorized by this
amendment.

---

## 61. Contract Amendment History — Phase 149O.20L.7O.2M (v1.7)

**§61.1 Entering state.** Phase 149O.20L.7O.2L.4 independently verified
the repair of the HARDWARE-ENROLLMENT RECOVERY AUTHORITY DEFECT
Blocking finding and independently re-derived that the two standalone
Trust-Enrollment administrative CLI entry points,
`scripts/hatp_hardware_credential_admin.py` and
`scripts/hatp_principal_signer_admin.py`, are authority-bearing under
HMIC-REQ-052 and not yet HMIC-bound. Verdict: VERIFIED WITH
NON-BLOCKING FINDINGS. This section records this phase's own,
independent primary-source re-derivation of that conclusion and the
resulting v1.6 → v1.7 amendment; it does not itself constitute
independent verification of the amendment (§61.9).

**§61.2 HMIC-REQ-052 authority-sensitivity test, re-derived.** For each
script, independently: if only that script changed while every v1.6
frozen member remained byte-identical, could an authoritative
Trust-Enrollment result differ? `scripts/hatp_hardware_credential_
admin.py` owns operation selection (`enroll`/`revoke`), the
confirmation boundary, provider-enrollment invocation, registration
retry orchestration, and revoke dispatch — a rewrite that skipped
confirmation, silently retried past a rejection, or dispatched the
wrong operation would change the real `HardwareCredentialRecord`
registry content with zero v1.6 frozen byte changed. Answer: YES.
`scripts/hatp_principal_signer_admin.py` owns operation selection
(`enroll-principal`/`revoke-principal`/`enroll-signer`/`revoke-signer`),
the confirmation boundary, and exact core-writer invocation dispatch —
the identical reasoning applies to `PrincipalRecord`/`SignerRecord`
content. Answer: YES. Both scripts are therefore authority-bearing
under HMIC-REQ-052(d)'s existing dual-anchor construction (§59, §832 of
this document), one layer further out than the core writer modules
already bound at v1.5.

**§61.3 Complete transitive closure, re-derived independently.** A
fresh, symbol-level AST/import walk of both scripts (not merely
restated from the entering-state phase's own prose) finds:
`scripts/hatp_hardware_credential_admin.py` imports
`pcae.core.hatp_hardware_credential_admin` (already bound,
`_FROZEN_SRC_PCAE_RELATIVE_FILES`), `pcae.core.hatp_hardware_
credentials` (already bound), `pcae.core.hatp_providers` (already
bound), and lazily imports `pcae.core.hatp_fido2_provider` (already
bound, mirroring that module's own documented lazy-import discipline).
`scripts/hatp_principal_signer_admin.py` imports `pcae.core.hatp_
bootstrap` (already bound), `pcae.core.hatp_hardware_credentials`
(already bound), and `pcae.core.hatp_principal_signer_admin` (already
bound). No helper, path, authority, parsing, provider, confirmation/
election, serialization, or lock module reachable from either script
resolves outside the pre-v1.7 frozen set — unlike the `core/paths.py`
omission §60 repaired, no unfrozen transitive dependency is reached
here. The exact delta is therefore +2, both entries the scripts
themselves, no third file.

**§61.4 Exact identity consequence.** The amendment is additive only:
`_FROZEN_SRC_PCAE_RELATIVE_FILES` remains 27; `_FROZEN_REPOSITORY_ROOT_
RELATIVE_FILES` grows 9 → 11 (the two new entries appended after
`scripts/hatp_deployment_binding_admin.py`, following the existing
`scripts/`-anchor placement precedent, HMIC-REQ-055); total frozen
source/content identity grows 36 → 38 with no removal and no reordering
of any existing member. `_CONTRACT_IDENTITY_FILES` and `_CONTRACT_
VERSIONS_REQUIRED_KEYS` remain the identical exact seven-ID set — this
amendment widens HMIC-REQ-050 *source* scope only, not `contract_
versions`; no eighth contract is added, and `HMIC-001` itself joins
neither `contract_versions` nor its own frozen file set (avoiding the
self-reference §12 of the governing prompt for this phase warns
against; HMIC-001's own document bytes are bound into no digest it
itself computes).

**§61.5 Version determination.** Adding two new authority-bearing
digest inputs changes the normative certified implementation identity
and widens HMIC-REQ-050/052(d) — the same minor scope-evolution shape
as v1.1/v1.3/v1.4/v1.5/v1.6, not an editorial same-version repair and
not a schema/algorithm change warranting a major bump. The amendment is
therefore v1.6 → v1.7, not v2.0, per the established repository
contract-versioning precedent (§60.5 records the identical v1.5 → v1.6
determination).

**§61.6 Self-consistency.** After the accompanying production
alignment (same phase): HMIC contract-enumerated count (38, §HMIC-REQ-
050 above) == production `_FROZEN_AUTHORITY_BEARING_FILES` count (38)
== this section's independently re-derived source-membership count
(38); and contract identity count (7) == `CertificationRecord
contract_versions` key count (7). Exact-member comparison, not
count-only: both new entries are `scripts/hatp_hardware_credential_
admin.py` and `scripts/hatp_principal_signer_admin.py`, no other member
differs from the v1.6 enumeration.

**§61.7 Current-certification consequence.** The existing real Dell
`CertificationRecord` remains immutable historical truth for its
deployed v1.6/36-member source identity — this amendment does not
revoke it. Once a future, separately-governed redeployment carries the
new v1.7/38-member source identity, that old certification does not,
and structurally cannot, certify the new deployment identity: a v1.6
`CertificationRecord` evaluated against v1.7 source fails the
`implementation_scope_digest` comparison at §31 step 9 as
`IMPLEMENTATION_MISMATCH`, before the unchanged seven-member
`contract_versions` comparison at step 10 is ever reached — the
identical mechanism §60.6 already describes for the v1.5 → v1.6
transition, now applied one version further. No compatibility or
grandfathering path exists for the old digest.

**§61.8 Mac/Dell divergence, intentional.** After this amendment, the
Mac development source is HMIC-001 v1.7 / 38-member identity; the real
Dell deployment remains on its prior HMIC-001 v1.6 / 36-member
certified generation, internally consistent for what it actually runs.
That divergence is intentional and expected until a later, separately
governed redeployment carries the new Trust-Enrollment admin surface to
the Dell — this amendment performs no such redeployment, no real
Trust-Enrollment effect, no certification effect, and no Protected Root
mutation.

**§61.9 Finding disposition.** No Blocking finding is opened: the
transitive closure is not broader than expected (§61.3), the contract/
source counts do not diverge (§61.6), both new scripts affect
`implementation_scope_digest` (independently demonstrated by this
phase's own byte-mutation regression tests), the old v1.6 certification
does not remain `VALID` against the new v1.7 source (§61.7), and no
authority dependency remains outside the widened frozen scope. This
amendment is therefore **HMIC v1.7 TRUST-ENROLLMENT ADMIN ENTRY-POINT
SOURCE SCOPE EVOLVED — 38-MEMBER AUTHORITY IDENTITY IMPLEMENTED — EXACT
+2 DELTA ESTABLISHED — INDEPENDENT VERIFICATION PENDING — NOT VERIFIED
AT v1.7**. Independent verification, not this phase's own self-
assessment, must still confirm the 38-member closure, the exact
two-script delta, contract/source consistency, digest participation,
absence of an omitted transitive dependency, and that the old
certification does not cover the new source, before HMIC v1.7 may be
treated as trusted.

**Recommended next phase.** **149O.20L.7O.2M.1 — HMIC v1.7
Trust-Enrollment Admin Entry-Point Source-Scope Evolution Independent
Verification.** No redeployment, no fresh `CertificationRecord`, no
activation, and no real FIDO2/PIV hardware enrollment is authorized
before that independent verification passes.

---
