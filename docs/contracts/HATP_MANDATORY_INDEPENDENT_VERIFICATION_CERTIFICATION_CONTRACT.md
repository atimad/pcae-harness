# HATP Mandatory Independent-Verification Certification Contract

**Contract ID:** HMIC-001
**Version:** 1.2
**Status:** FROZEN — HBDC BOUND-CONTRACT IDENTITY EVOLUTION COMPLETE, CONTENT-IDENTITY BINDING REPAIRED (149O.20D.1) — PENDING INDEPENDENT VERIFICATION (not VERIFIED at v1.2)
**Frozen by:** Phase 149O.19.2
**Repaired by:** Phase 149O.19.3R (finding B-149O.19.3-1; see §49) — v1.0, independently re-verified VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS at 149O.19.3R.1
**Amended by:** Phase 149O.19.5E.1 (v1.0 → v1.1: HMIC-REQ-050/052 widened to bind the now-implemented HMIC validator/admin source; W-1 resolved at the contract level; see §50)
**Amended by:** Phase 149O.20D (v1.1 → v1.2: HMIC-REQ-067 widened to bind HBDC-001 v1.0 into `contract_versions`, closing HBDC-001's own HBDC-REQ-048 prerequisite; contract evolution only, no production change; see §51)
**Repaired by:** Phase 149O.20D.1 (finding B-149O.20D-1: HBDC-001's v1.2 binding was version-header-only, leaving same-version content-only byte drift certification-invisible; repaired in place, same version, by additionally binding HBDC-001's document bytes into `implementation_scope_digest` — HMIC-REQ-050/052/053 widened to twenty-five files; HMIC-REQ-145 revised from a disclosed residual limitation to a closed one; no production change; see §52)
**Depends on (unamended, byte-unchanged):** HMRC-001 v1.0, HATP-001 v1.0, HSCE-001 v1.1, RAE-001 v1.0, HBDC-001 v1.0
**Selected architecture source:** `docs/PHASE_149O_19_1_HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_ARCHITECTURE.md`

This is a **contract-freeze document**. It normatively freezes the shape
of a future implementation. It implements nothing. No `src/pcae/**`
file, and no other contract file, was modified to produce this
document. No certification artifact, active-certification pointer, or
revocation record exists as a result of this phase. The current
hard-coded `mandatory_consumption_implementation_independently_verified
= False` ceiling (`hatp_mandatory_cutover.py:842-853`) is unchanged.

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
                              "HSCE-001": "1.1", "RAE-001": "1.0"} —
                              the minimal sufficient contract set (§22)
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
these twenty-five files, no more, no fewer, no caller-suppliable
alternate or "legacy" scope selector of any kind — established at v1.1
(§50), carried forward byte-unchanged through v1.2 (§51), and widened by
one entry at the same v1.2 version by the 149O.20D.1 content-identity
binding repair (§52; finding B-149O.20D-1). Paths under `src/pcae/` are
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

docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md      (HMRC-001)
docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md        (HATP-001)
docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md     (HSCE-001)
docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md               (RAE-001)
docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md                  (HBDC-001)
scripts/hatp_certification_admin.py
```

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
frozen set. The final two entries, `core/hatp_mandatory_certification.py`
and `scripts/hatp_certification_admin.py`, were added by Phase
149O.19.5E.1 to resolve Stop Condition W-1 (§50): Waves A–E
(149O.19.5A–5E) implemented this contract's own certification-parsing,
implementation-identity-derivation, protected-storage, active-binding,
revocation, and Validation Status determination logic in
`core/hatp_mandatory_certification.py`, and its sole intended Protected
Admin ceremony caller in `scripts/hatp_certification_admin.py` — neither
file existed when the original v1.0/repaired-v1.0 enumeration was
written, and both are now themselves capable of altering
certification-relevant outcomes (§17 HMIC-REQ-052(b)). §49 records the
v1.0 repair history; §50 records the v1.1 amendment history; §51 records
the v1.2 amendment history (contract_versions widened to five members,
twenty-four-file enumeration left unchanged); §52 records the
149O.20D.1 repair history that added the twenty-fifth entry, this
section states only the current, twenty-five-file enumeration.
`core/hatp_mandatory_certification.py` is listed in the `src/pcae/`-
relative bucket (it lives at `src/pcae/core/hatp_mandatory_certification.py`);
`scripts/hatp_certification_admin.py` is listed in the repository-root-
relative bucket (it lives outside `src/pcae/` entirely, at the
repository-root-relative path shown) — see HMIC-REQ-055 for the
canonicalization rule this split feeds, and §50 for why a standalone
`scripts/` path is safely representable under the existing grammar.

**HMIC-REQ-051 (Ownership — Embedded, Not an External Manifest).** This
enumeration is embedded directly in this frozen contract (HMIC-REQ-050),
not delegated to an external, separately-versioned manifest file. No
agent-editable list can redefine the certified scope: changing this
enumeration requires amending this contract itself (§44), which is not
an agent-writable action under this repository's own contract-freeze
discipline (contract files are themselves part of the frozen set they
describe, HMIC-REQ-050's five `docs/contracts/` entries, as of the
149O.20D.1 repair — formerly four, §52).

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
transitively.

A file SHALL NOT be added merely because it is imported by a frozen
file if no reachable code path from that file can change one of the
outcomes above under either limb (§49's transitive-completeness table
records this contract's own worked application of limb (a); §50
records the worked application of limb (b), including files
deliberately left unbound with rationale).

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
`hatp_piv_provider.py`, and `hatp_hardware_credentials.py`, and (d)
Phase 149O.19.5E.1's own application of newly-added limb (b) above to
the by-then-implemented HMIC certification/validation implementation
itself, which added `core/hatp_mandatory_certification.py` and
`scripts/hatp_certification_admin.py` (§50). All four sources are now
fully covered under this closure rule; §49 records the complete
limb-(a) transitive-completeness analysis, including the specific,
non-authority-sensitive dependencies that rule deliberately excludes
(`pcae.core.paths`; the Permission-Broker policy-decision-support
modules `gate_dry_run`/`scope_preflight`/`shell_gate` and their own
`gate_dry_run_context`/`artifact_index`/`decision_log`/
`governance_timeline`/`memory_snapshot`/`project_state`/`risk_register`
dependents; and `rollback_approval_evidence.py`'s own RAE-001
creation-ceremony publication/interactive-workflow imports, which are
not reachable from the readiness-evaluation call graph); §50 records
the complete limb-(b) transitive-completeness analysis for the two
newly-bound files.

**HMIC-REQ-053 (Contract Bytes Participate Directly, Explicit
Separation from `contract_versions`).** The five contract files'
byte contents — as of the 149O.20D.1 repair (§52), this now includes
`HBDC-001`, previously the sole `contract_versions` member excepted from
this rule (§51, HMIC-REQ-145 pre-repair) — participate in
`implementation_scope_digest` directly (HMIC-REQ-050), as a distinct,
additional binding from the `contract_versions` field's own
version-header check (§22, §33 step 10). These two mechanisms are
deliberately redundant, not interchangeable: an edit to a bound
contract's *prose* (without a version-header bump) is caught by the
digest binding even though `contract_versions`' version-string
comparison alone would not detect it. No future implementation SHALL
treat either mechanism as sufficient without the other. As of the
149O.20D.1 repair, every `contract_versions` member (HMIC-REQ-067, five
entries) receives both bindings uniformly — no `contract_versions`
member is exempted from the digest binding.

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

**HMIC-REQ-067 (Revised, v1.2 — HBDC-001 added).** The minimal
sufficient `contract_versions` set is exactly: `HMRC-001` (defines the
consumption chain this certification ultimately gates), `HATP-001`
(proof verification/trust-store semantics the consumption chain depends
on), `HSCE-001` (evidence envelope schema the consumption chain loads),
`RAE-001` (approval-derivation semantics the consumption chain calls),
and, *as of v1.2*, `HBDC-001` (deployment-topology/environment-lock
semantics that determine whether the Class-B environment a Model-A
certification's `implementation_scope_digest` is computed inside may
legitimately be treated as sufficient for HMIC-REQ-063's Option-C
accepted-residual branch — §51). Five entries, no more, no fewer, under
v1.2.

**HMIC-REQ-068.** `RWMPC-001`, `PBPA-001`, and `PBPC-001` remain
explicitly excluded from `contract_versions`, unchanged by v1.2.
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
compare each `contract_versions` entry — five entries as of v1.2 — against
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
(repaired) and §52.

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
they joined `contract_versions`. This closure is, like every
`implementation_scope_digest`-mediated protection in this contract,
**not yet mechanically enforced in production**: `core/hatp_mandatory_
certification.py`'s own `_FROZEN_AUTHORITY_BEARING_FILES` constant still
implements the pre-repair twenty-four-file set (§52) — see HMIC-REQ-069's
own "not yet operative" framing (attacks #33/#34/#36, §41) for the
identical class of disclosed, intentional contract-first/production-
stale sequencing this repair follows. This repair does not, and does not
claim to, solve HMIC-REQ-063's own executed-code/import-shadowing
residual limitation, which remains separately named, unchanged, and
unsolved by this section.

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
   (read-only, by reading the four frozen contracts' own version
   headers, §20), certified_at (read-only, wall-clock at invocation).
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
    the four frozen contracts' own
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
  v1.2 (HMIC-REQ-067, §51). A required `contract_versions` key absent
  from a stored record fails closed as `MALFORMED` under HMIC-REQ-031's
  pre-existing closed-schema discipline — no new mechanism was needed to
  reject a stored record produced under the pre-v1.2, four-member
  scope. **As of the 149O.20D.1 repair (§52, HMIC-REQ-053/145), all five
  `contract_versions` members' document bytes additionally participate
  in `implementation_scope_digest` uniformly** — a same-version,
  content-only edit to any of the five bound contracts, including
  `HBDC-001`, is caught by CIVC-4's digest-drift invariant, not merely
  by this invariant's version-header comparison; the two invariants are
  deliberately redundant for all five, not only the original four.
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

## 41. Full Mandatory Attack Matrix (37 Scenarios)

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
| 33 *(added v1.1, §50)* | v1.0-scope replay: a hypothetical certification whose `implementation_scope_digest` was computed over the pre-v1.1 twenty-two-file set is presented for validation in a v1.1 environment (production identity derivation realigned to the twenty-four-file set, a future phase — §50) | Rejected — `IMPLEMENTATION_MISMATCH`: a twenty-two-file digest cannot equal a twenty-four-file digest under HMIC-REQ-054/058's two-level construction over a different input file list; no compatibility/grandfathering mode exists (HMIC-REQ-050's "no more, no fewer" enumeration has no version-conditional branch). **Not yet operative**: until production identity derivation is realigned to the v1.1 file set (a distinct future phase — §50), production still computes the twenty-two-file digest, so this rejection is contractually mandated but not yet mechanically enforced; see attack #34 |
| 34 *(added v1.1, §50)* | File-set downgrade during the v1.1-contract/v1.0-production transition window: a caller (or the still-unaligned production code itself) computes `implementation_scope_digest` over only the old twenty-two files after this contract has moved to the twenty-four-file v1.1 enumeration | Not a certification bypass: this contract defines exactly one canonical enumeration at a time (HMIC-REQ-050/051), with no caller-suppliable `version=1.0`/`legacy_scope`/`file_count=22` override of any kind (HMIC-REQ-051 — the enumeration is embedded in this contract, not an agent-editable external manifest). The temporary divergence between this contract's twenty-four-file v1.1 enumeration and production's still-twenty-two-file identity derivation is a disclosed, intentional sequencing consequence of this phase (§50), not a silent gap: it is fail-closed throughout because the hard-coded `mandatory_consumption_implementation_independently_verified = False` ceiling remains unchanged and zero readiness/cutover callers of the validator exist — no functional readiness decision depends on which file count production currently computes over |
| 35 *(added v1.2, §51; revised 149O.20D.1, §52)* | HBDC semantic-drift-after-certification: a hypothetical certification is created while `HBDC-001` reads v1.0 with byte content A; `HBDC-001` is later revised to a new version, or replaced/removed, while the certification remains the active pointer | Rejected — `CONTRACT_MISMATCH` (revised-version case, via HMIC-REQ-069's five-member `contract_versions` comparison) or the general HMIC-REQ-059/062-class missing/unsafe-file failure (removed/replaced/unsafe case, via `implementation_scope_digest`, as of the 149O.20D.1 repair). Same-version content-only drift is **no longer** a disclosed exception — see attack #37 |
| 36 *(added v1.2, §51)* | Legacy four-contract certification replay: a hypothetical certification whose `contract_versions` was derived under pre-v1.2 (four-member: `HMRC-001`/`HATP-001`/`HSCE-001`/`RAE-001`) semantics is presented for validation once production identity derivation is realigned to v1.2's five-member set | Rejected — `MALFORMED`: the stored record's `contract_versions` mapping lacks the now-required `HBDC-001` key, which HMIC-REQ-031's pre-existing closed-schema discipline (missing required key) already rejects; no new mechanism, no caller-suppliable `legacy_contract_set=True`/`bound_contract_count=4`/`ignore_hbdc=True` override exists or is introduced (HMIC-REQ-067 restated, no exception clause). **Not yet operative**: until production identity derivation is realigned to the v1.2 five-member `contract_versions` set (a distinct future phase — §51), production still computes the four-member set, so this rejection is contractually mandated but not yet mechanically enforced; mirrors attack #33's identical "not yet operative" caveat |
| 37 *(added 149O.20D.1, §52; finding B-149O.20D-1)* | HBDC-001 same-version content drift: `HBDC-001` still declares Contract ID `HBDC-001`, Version `v1.0`, but its normative document bytes are edited (e.g. an environment-lock requirement quietly loosened, an attack-matrix row weakened) without any version-header bump, while a certification created against the pre-edit bytes remains the active pointer | Rejected — `IMPLEMENTATION_MISMATCH`, via `implementation_scope_digest` (HMIC-REQ-050's twenty-fifth entry, `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`, HMIC-REQ-053/058, §31 step 9), the identical mechanism attack #11/#13 already describe for the other twenty-four frozen files, now extended to `HBDC-001`'s own document bytes; this is what closes B-149O.20D-1 (§52), superseding the same-version exception attack #35 previously disclosed. **Not yet operative**: until production identity derivation is realigned to HMIC-REQ-050's twenty-five-file set (a distinct future phase, mirroring attacks #33/#34/#36's identical caveat), production still computes the twenty-four-file digest, so this rejection is contractually mandated but not yet mechanically enforced; no functional readiness decision depends on it today because no stored certification exists on this host for either file count to be compared against (§52) |

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
path safety is frozen (§36); and the 32-scenario attack matrix (§41) and
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
