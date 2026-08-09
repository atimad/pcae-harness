# Phase 149O.19.1 — HATP Mandatory Activation Independent-Verification Certification Architecture

**Phase type:** Architecture / trust-root design only. No `src/pcae/**`
file, no contract file, and no protected-root state was created or
modified to produce this document.

**Depends on (unamended, byte-unchanged):** HMRC-001 v1.0, HATP-001
v1.0, HSCE-001 v1.1, RAE-001 v1.0. **Consumes (read-only, unmodified):**
`src/pcae/core/hatp_mandatory_cutover.py`,
`src/pcae/core/hatp_bootstrap.py`, `src/pcae/core/repository_identity.py`.

---

## 1. Baseline (Confirmed by Direct Inspection, Not Assumed)

Repo clean at phase entry, `origin/main..HEAD = 0`. `pcae health`
healthy, `pcae check` passed, `pcae status coherence` coherent, `pcae
push check` clean (`nothing_to_push`), `pcae runtime inspect` returns
`Observed / observe / unavailable`, `pcae doctor task-memory` shows only
pre-existing, unrelated warnings (7 `tasks/done/` entries missing from
`tasks/DONE.md`, predating this phase). `pcae phase-report show
--latest` and `pcae phase-report reconcile --phase-id 149O.19` both
confirm, with zero mutation, that Phase 149O.19 is `status: completed`,
`report completeness: complete`, at commit `37a2066f`, pushed, with
verdict **VERIFIED WITH NON-BLOCKING FINDINGS** and activation-
certification verdict **Option B**.

## 2. The 149O.19 Result This Phase Builds On

149O.19 independently confirmed, by direct behavioral test, source-
pattern match, and exhaustive negative search, that the
`mandatory_consumption_implementation_independently_verified` term of
`assess_hatp_mandatory_activation_readiness`'s six-item conjunction
(`src/pcae/core/hatp_mandatory_cutover.py:842-853`) is a **literal
Python `False` constant**:

```python
checks.append(
    HATPMandatoryActivationReadinessCheck(
        "mandatory_consumption_implementation_independently_verified",
        False,
        (...),
    )
)
```

It is not derived from `PermissionBroker`, `simulation_only`,
`PROJECT_STATUS.md`, `tasks/TODO.md`, `CHANGELOG.md`,
`.pcae/phase-completion-metadata.json`, `.pcae/phase-completion-
report.md`, `tasks/DONE.md`, `os.environ`, `os.getenv`, or any other
repo-local or environment-derived signal — confirmed by exhaustive
negative grep across the module. There is no CLI, agent, or
environment-variable path that reaches `activate_hatp_mandatory`
(AST-confirmed against `cli.py`, `commands/agent.py`, `core/agent.py`).
`activate_hatp_mandatory`'s only production-reachable call path requires
real OS write access to `HATPTrustStore.production().root`
(`/Library/Application Support/PCAE/HATP/trust-store` on macOS,
`/etc/pcae/hatp/trust-store` on Linux — `hatp_bootstrap.py:222-250`),
which the Agent OS principal does not, by the Class-B topology
149O.1B.1 established, possess.

**B-149O-1..4 status carried forward unchanged:** INDEPENDENTLY
CONFIRMED CLOSED AT SYSTEM IMPLEMENTATION/ENFORCEMENT BOUNDARY —
DEPLOYMENT/OPERATIONAL ACTIVATION DEFERRED. HATP production remains
**NOT READY**. Runtime remains **Observed / observe / unavailable**.
This architecture phase does not reopen or alter any of these findings.

## 3. Why This Ceiling Is Secure Today

The `False` constant is not a bug to be "fixed" casually. It is the
correct fail-closed default in the absence of any protected,
non-agent-writable authority source proving independent verification
occurred. Every alternative signal an implementation *could* have
consulted instead — a passing test suite, a phase-completion report, a
`PROJECT_STATUS.md` entry, a git commit message, a task-lifecycle state,
an environment variable — is either directly agent-writable or
indirectly agent-influenced (the agent authors the tests, writes the
phase report, and drives the task lifecycle). Wiring any of those into
`assess_hatp_mandatory_activation_readiness` would make the agent the
de facto author of its own activation authority: a self-certification
loop. The current hardcoded `False` is therefore a deliberate,
permanent ceiling, not an oversight — precisely mirroring
`hatp_bootstrap.py`'s own stated invariant that "no production,
agent-reachable API exposes `enroll()`, `grant()`, `revoke()`, or
`rotate()`."

## 4. The Gap, Stated Precisely (Semantic Wall)

The missing capability is **not**:

- "detect whether Phase 149O.19 exists" — a phase report is
  agent-authored;
- "detect whether tests passed" — a test suite is agent-authored and
  agent-run;
- "detect whether `PROJECT_STATUS.md` says completed" — that file is
  agent-writable.

The missing capability **is**: a protected certification statement
whose provenance is independent of the agent-writable repository, and
whose scope is bound to the exact deployment/implementation being
activated — not to a phase number, a commit message, or a status file's
prose.

**Frozen semantic wall** (extends HMRC-001 §5 with the additional
distinctions this architecture introduces):

```
phase completed              ≠  independently certified activation state
tests passed                 ≠  certification
commit exists                ≠  certification
repository status            ≠  certification
implementation verified      ≠  deployment activated
certification present        ≠  PB ALLOW
certification present        ≠  runtime execution capability
certification present        ≠  HATP production READY
certification present        ≠  HATP_MANDATORY activated
```

No future implementation, log message, status field, or user-facing
text may collapse any of these distinctions.

## 5. Authority Principal (Selected)

**Selected: `PCAE_BOOTSTRAP_ADMIN_PRINCIPAL`** — the same Class-B
protected administrative/bootstrap principal 149O.1B.1 already
established as `PCAE_BOOTSTRAP_ADMIN_PRINCIPAL` (collapsed with
`PCAE_HUMAN_APPROVER_PRINCIPAL` in the frozen two-principal v1 topology,
149O.1B.1 §5/§7), and the same principal HMRC-REQ-041 already names as
"Protected Activation Authority" for `PREPARED → HATP_MANDATORY`
activation itself. This is a reuse decision, not a new invention: the
certification ceremony and the activation ceremony share one authority
principal, because both require the same property — real OS write
access to the protected trust root that the Agent OS principal
structurally lacks (149O.1B.1 §7-§9's no-sudo-escape invariant).

**Explicitly rejected weaker candidates** (per governing constraint —
do not invent weaker authority): the agent OS principal; any repository
process or CLI invocation running as the agent principal; a normal CLI
user who happens to share the agent's OS account (149O.1B.1 §6's
same-user finding: Class-B is meaningless without distinct OS-user
separation); phase-lifecycle code; a test suite; a git hook; a
`PROJECT_STATUS.md` generator.

**Consequence:** certification requires exactly the same real-world
precondition activation already requires — a human operator with actual
filesystem write access to `/Library/Application Support/PCAE/HATP/
trust-store` (or `/etc/pcae/hatp/trust-store`). Neither this phase nor
any future agent-only phase can create a certification, by the same
mechanism that already prevents an agent-only phase from activating
`HATP_MANDATORY` today.

## 6. Protected Storage Root (Selected)

**Selected: reuse the existing `HATPTrustStore.production().root`.**
No new protected root is introduced. This is the same fixed,
platform-level, non-`Path.home()`-derived, non-agent-writable directory
`hatp_bootstrap.py::_default_production_trust_root` already resolves,
and the same root under which the Cutover Record and activation marker
already live (HMRC-REQ-043's own precedent: "the same protected storage
family HATP-001 already uses for deployment binding and trust-store
state").

**Rejected alternative:** a second, independent protected root. HMRC-
REQ-043 itself chose *not* to extend `registry.json`'s own schema for
the Cutover Record ("to keep the mandatory-cutover concern independently
auditable and independently corruptible-without-affecting deployment-
binding integrity") — the same reasoning applies here a second time: the
certification concern gets its own file(s) under the *same* root, not a
merge into `registry.json` or `cutover-record.json`, and not a wholly
separate root (which would only multiply the number of OS-permission
boundaries to provision and audit for zero additional security benefit,
since the Agent OS principal already cannot write anywhere under this
root).

## 7. Artifact/Latch Topology (Selected)

Evaluated against the four candidates the governing prompt names:

- **(A) Single immutable certification artifact** — rejected alone:
  cannot support recertification/supersession (§20 below) or
  repository/deployment keying (§17) without inventing file-naming
  conventions from scratch.
- **(B) Monotonic certification latch** — the *cutover mode* concept
  (`LEGACY_COMPATIBLE → PREPARED → HATP_MANDATORY`) is already
  monotonic; certification is a different, prerequisite concern (it can
  exist, be revoked, and be re-created multiple times *before*
  activation ever happens once) and does not itself need to be
  irreversibly monotonic in the same sense.
- **(C) Protected registry entry** — closest fit: mirrors
  `hatp_bootstrap.py`'s own existing `registry.json` shape
  (`principals`/`signers`/`deployment_bindings`/`authorities`, each a
  keyed dict, each entry immutable except for an explicit
  `status`/`revoked_at` pair).
- **(D) Another existing Class-B protected primitive** — none exists
  that already fits (the Cutover Record is mode-only, not
  certification-shaped).

**Selected: (C), instantiated as its own file, `certifications.json`,
under the trust-store root**, structurally parallel to
`registry.json`'s `DeploymentBinding`/`SignerRecord` shape (append-only
keyed entries, immutable fields except `status`/`revoked_at`, own
version field, closed schema) but **not merged into `registry.json`
itself** (§6's independent-auditability reasoning) and **not merged
into `cutover-record.json`** (a certification is evidence a Consumption
Mode transition may rely on, not the transition record itself — HMRC-
001 §18/§19 already separates "what mode is this deployment in" from
"what evidence supports moving it there").

## 8. Certification Identity — Schema Concept (v1, Closed)

Two documents, both under the trust-store root, both schema-versioned
and closed (unknown fields rejected, missing fields rejected, duplicate
JSON keys rejected, boolean `version` rejected — mirroring
`hatp_mandatory_cutover.py`'s and `hatp_bootstrap.py`'s existing
strict-parser discipline exactly):

```
certifications.json                 (append-only certification records)
certification-bindings.json         (explicit active-certification pointer per
                                      repository/deployment key — §12)
```

**`CertificationRecord` (one entry in `certifications.json`):**

```
certification_id             opaque identifier, derived from a canonical
                              digest of the record's own authority-sensitive
                              fields (below) at creation time — never a
                              caller-supplied free-form string (§21)
repository_instance_id        binds to the same identity HATP-001/HMRC-001
                              already use (CRI Model A Layer 1 + Layer 2
                              deployment binding, §14)
canonical_deployment_root     Layer 2 binding, reusing
                              `deployment_binding_matches`'s existing
                              repository_id + canonical_deployment_root
                              conjunction (§14)
implementation_commit         git commit SHA of HEAD at certify time (an
                              identity component, not authority — §15)
implementation_scope_digest   canonical digest over the frozen
                              authority-bearing file set (§15) — the
                              implementation-identity load-bearing field
contract_versions             {"HMRC-001": "1.0", "HATP-001": "1.0",
                              "HSCE-001": "1.1", "RAE-001": "1.0"} — the
                              minimal sufficient contract set (§16)
verification_record_digest    digest of the canonical 149O.19-class
                              phase report this certification attests to
                              (evidentiary metadata only, §22)
certified_at                  strict `YYYY-MM-DDTHH:MM:SS[.ffffff]Z`
                              timestamp (149O.17-plan strict grammar,
                              reusing `hatp_mandatory_cutover.py`'s
                              `_TIMESTAMP_PATTERN` exactly — no Python
                              3.9 `fromisoformat` permissiveness)
certified_by                  protected-authority reference string,
                              caller-supplied with no default and no
                              process/session/environment derivation
                              (mirrors `CutoverRecord.activated_by`
                              exactly, HMRC-REQ-045)
status                        "active" | "revoked" (mirrors
                              `SignerRecord`/`AuthorityRecord`'s existing
                              status vocabulary in `hatp_bootstrap.py`)
revoked_at                    present iff status == "revoked" (mirrors
                              `_require_revoked_at_consistency` exactly)
```

**`CertificationBinding` (one entry in `certification-bindings.json`,
keyed by `(repository_instance_id, canonical_deployment_root)`):**

```
repository_instance_id
canonical_deployment_root
active_certification_id       explicit pointer into certifications.json,
                              or absent (no active certification) — never
                              computed by scanning/sorting/globbing (§13)
```

No field here is left as an authority-sensitive TBD; the exact digest
algorithm and the exact frozen authority-bearing file-set enumeration
are the two items this architecture defers to the future contract-freeze
phase (§16.1, §29), consistent with how HMRC-001 itself froze mechanism
shape before a later implementation phase filled in concrete file lists.

## 9. Implementation Identity (The Hardest Question)

**What exactly is being certified?** A Git commit SHA alone is
explicitly rejected as sufficient (governing constraint item 54): it is
an identifier, not authority, and it says nothing about which files an
attacker might have modified in the working tree after that commit while
still reporting the same `HEAD` SHA to a casual check.

**Selected: `implementation_commit` (git commit SHA) bound together
with `implementation_scope_digest` — a canonical SHA-256 digest computed
over the sorted, concatenated byte contents of an explicit, frozen
"authority-bearing file set"** — the exact production modules and
contract files HMRC-001 itself names as its dependency closure:
`hatp_mandatory_cutover.py`, `hatp_ag_authority.py`,
`hatp_rollback_consumption.py` (Wave B/C/D modules), `hatp_bootstrap.py`,
`human_approval_trusted_provenance.py`, `repository_identity.py`, the
Permission Broker policy modules PBPA-001/PBPC-001 implement, and the
four contract files themselves (HMRC-001, HATP-001, HSCE-001, RAE-001).

**Residual limitation, stated honestly (item 132's transitive-
dependency concern):** a hand-maintained file list can miss a modified
transitive dependency (e.g. a shared utility function these modules
call). This architecture does **not** claim `implementation_scope_digest`
achieves whole-program formal identity. It claims only that it is
strictly stronger than a bare commit SHA, and that it is consistent
with this repository's *existing* trust model elsewhere: the Cutover
Record itself does not cryptographically attest to the entire
interpreter and dependency closure either — it relies on the same
OS-level protected-root permission boundary this certification also
relies on. Requiring more of certification than the repository already
requires of activation itself would be inconsistent, not more secure.

**Working-tree binding (item 134):** `implementation_scope_digest` is
computed from the actual on-disk file contents at certify time, not
from `git show HEAD:<path>` — so a dirty working tree is captured
faithfully rather than compared against a clean commit's blob. At
**validation** time (§18), the same digest is recomputed fresh from the
current on-disk contents of the same file set; any difference — whether
from an intentional edit, an incomplete `git checkout`, or an
uncommitted local change — is a mismatch, fails closed, and requires no
separate "dirty tree" check (a dirty tree that doesn't change the
authority-bearing files still validates; a dirty tree that does, fails,
exactly as it should).

**Architectural prerequisite flagged (item 139, partially resolved, not
a full stop):** PCAE has no canonical "deployment manifest" or
build/wheel identity primitive today (it runs from an editable working
tree). This architecture explicitly recommends that a future,
dedicated deployment-identity contract eventually replace
`implementation_scope_digest`'s hand-maintained file enumeration with a
canonical, automatically-derived manifest — but does not block this
architecture on that not yet existing, because the file-set approach is
no weaker than the trust model activation itself already accepts (§9's
Cutover Record parallel), and inventing a full deployment-manifest
system is explicitly out of scope for a "narrowly-scoped... architecture"
phase (per this phase's own type constraint).

## 10. Repository, Deployment, and Contract Binding

**Repository identity:** `repository_instance_id`, reused exactly as
HATP-001/HMRC-001/RAE-001 already define it (CRI Model A Layer 1, never
path-only identity) — never a new identity system.

**Deployment identity:** `canonical_deployment_root`, reused exactly as
`hatp_bootstrap.py::resolve_canonical_deployment_root` and
`DeploymentBinding` already define it — the same Layer 2 binding that
already defends against a copied `repository_instance_id` being reused
at the wrong physical deployment (HATP-REQ-057-063,
`deployment_binding_matches`). No second, parallel deployment-identity
system is introduced.

**Contract binding — minimal sufficient set:** `HMRC-001` (defines the
consumption chain this certification ultimately gates), `HATP-001`
(proof verification/trust-store semantics the consumption chain
depends on), `HSCE-001` (evidence envelope schema the consumption chain
loads), `RAE-001` (approval-derivation semantics the consumption chain
calls). **Explicitly excluded from the minimal set:** RWMPC-001 (only
classifies AG3/AG5 as `EXECUTION_CLASS_ROLLBACK`; changing it doesn't
change what mandatory-consumption *implementation* looked like at
verification time), PBPA-001/PBPC-001 (PB policy is a separate,
downstream concern from HMRC-001's own scope statement, HMRC-REQ-002-004
— a POL-005 policy change doesn't retroactively invalidate the
verification that the *consumption chain itself* was implemented
correctly). If a future contract-freeze phase judges this exclusion
wrong, it can widen `contract_versions` — but this architecture does not
overbind irrelevant files by default (governing constraint item 12).

## 11. Reused vs. New Primitives (No Duplicate Identity System)

| Concept | Reused from | New? |
|---|---|---|
| Repository identity | `repository_identity.py` (CRI Layer 1) | No |
| Deployment identity | `hatp_bootstrap.py::DeploymentBinding` (CRI Layer 2) | No |
| Protected root | `HATPTrustStore.production().root` | No |
| Strict timestamp grammar | `hatp_mandatory_cutover.py::_TIMESTAMP_PATTERN` | No |
| Atomic write / symlink rejection | `_atomic_write_json`/`_reject_symlink` pattern | No |
| Status/`revoked_at` consistency | `hatp_bootstrap.py::_require_revoked_at_consistency` | No |
| `activated_by`-style caller-supplied authority string | `CutoverRecord.activated_by` | No |
| Certification record schema, binding-pointer file, digest field | — | **Yes (this phase)** |

Per governing constraint item 138 ("no duplicate identity system"),
every identity primitive this architecture needs already exists in this
repository and is reused unmodified. Only the certification record
shape itself is new.

## 12. Explicit Active-Certification Binding (No Implicit Latest)

**Selected:** the `certification-bindings.json` file (§8) is the *only*
way a validator learns which certification, if any, is "active" for a
given `(repository_instance_id, canonical_deployment_root)` pair. A
validator never lists `certifications.json`, sorts by `certified_at`,
and picks the newest — that is exactly the "implicit latest"
anti-pattern the governing prompt names (items 28-30), and exactly the
class of ambiguity this repository has already hardened against
elsewhere (HSCE-001's evidence-ID-must-be-explicit rule, HMRC-REQ-014).

**Consequence:** creating a new `CertificationRecord` does **not**
automatically make it active. Activating it requires a second, explicit
admin write to `certification-bindings.json` (§25's ceremony). Two
separate protected writes for "create a certification" and "make it the
active one" are deliberately not collapsed into one, mirroring HMRC-001
§15's own deliberate decoupling of `PREPARED` (readiness) from
`HATP_MANDATORY` (activation) — "Activation is always an explicit
protected-admin action... readiness and activation are deliberately
decoupled" (HMRC-REQ-042). Certification and "making a certification
active" are decoupled for the identical reason.

## 13. Creation Ceremony

```
1. 149O.19-class independent verification phase completes (agent-authored,
   evidentiary only — never itself authority, §4).
2. Protected-admin principal (§5) reviews the canonical phase report
   out of band (human judgment, not this architecture's concern).
3. Protected-admin principal invokes a *separate, non-agent-writable*
   admin tool (§26-30) — never the ordinary `pcae` CLI surface an agent
   process can reach.
4. The tool itself — never the human, never the agent — computes:
   repository_instance_id (read-only, from repository_identity.py),
   canonical_deployment_root (read-only, from hatp_bootstrap.py),
   implementation_commit (read-only, `git rev-parse HEAD`),
   implementation_scope_digest (read-only, over the frozen file set),
   contract_versions (read-only, by hashing/reading the four frozen
   contract files' own version headers),
   certified_at (read-only, wall-clock at invocation).
5. The tool presents this computed tuple to the human for confirmation
   (a target, not a blank form) together with the verification_record's
   digest.
6. On confirmation, the tool derives certification_id from a canonical
   digest of the tuple and atomically appends a new, immutable
   CertificationRecord to certifications.json under the real
   protected-root transition lock (mirroring
   `hatp_mandatory_cutover.py`'s `fcntl.flock` discipline exactly).
7. Making the new record *active* (§12) is a distinct, explicit step —
   the tool does not do this automatically in the same invocation
   unless the human separately confirms "activate this as current."
```

**Minimized human-entered authority-sensitive input (governing
constraint items 23/89):** the human never types a repository ID,
digest, commit SHA, or "verified=True" boolean. The only human action
is confirming a tool-derived target and providing `certified_by` (their
own identity string) — everything authority-sensitive is
tool-re-derived, never accepted as free-form operator input.

## 14. Admin Tooling Surface (Selected)

**Selected: a separate admin/deployment tool, not the ordinary `pcae`
CLI.** Given the Class-B split-principal architecture, exposing a
`pcae certify ...` subcommand on the same binary/entrypoint an agent
process already invokes for everything else would put the
certification-writing code path in the same process image the agent
principal routinely executes — even if an in-process check tried to gate
it, that gate is exactly the "application-level authority-check
mechanism" `hatp_mandatory_cutover.py`'s own module docstring already
concluded does not, and should not, exist in this codebase (§18A's
"activation-authority scope decision"). The real enforcement boundary is
OS file permissions on the protected root, not a CLI-level check — so
the admin tool's job is only to be a *convenience* invoked by a human
who already possesses real write access, structurally identical to how
`activate_hatp_mandatory` itself is "never invoked anywhere in this
codebase... except via a genuine human operator holding real protected-
root filesystem write access" (18A module docstring, restated).

**Root resolution:** the admin tool resolves the canonical protected
root exactly the way production code does
(`HATPTrustStore.production().root`) — it does **not** accept a
`--root` override in its ordinary invocation mode (governing constraint
item 82), preserving the same "no caller-selectable trust root" property
`HATPTrustStore.production()` itself already guarantees. A test-only
seam (§27) accepting an explicit root exists structurally outside this
production entrypoint, mirroring `HATPTrustStore.__init__`'s own
`_test_only_root` pattern exactly.

## 15. Agent vs. Admin Write Ability (Explicit)

**Agent principal:** MAY read `certifications.json` and
`certification-bindings.json` (public verification material, exactly
the same posture HATP-001 §11 already grants for trust-store public
material). MUST NOT write, create, revoke, or supersede a
`CertificationRecord` or a `CertificationBinding` entry, and possesses
no API that would let it do so — no `mark_independently_verified()`,
`set_certified(True)`, or `write_verification_latch()` exists anywhere
under agent-reachable production code (governing constraint item 43).
The *only* write path is the separate admin tool of §14, itself gated
by the same OS-permission boundary, not by an in-process check.

**Human/admin principal:** owns the write ceremony (§13) exclusively.

## 16. Portability, Signature, Canonical Serialization

**Selected: local-only certification, no import/export.** Portability
(copying a certification between hosts/repositories) only widens attack
surface (§19-20's replay scenarios) for no benefit this architecture's
threat model requires — HMRC-001's own Threat-A model already excludes
cross-host transport as a legitimate operational need. **No
cryptographic signature is added.** The protected-root OS-permission
boundary is already this repository's entire trust boundary for
identically-shaped artifacts (the Cutover Record itself is unsigned);
adding a signature here without also signing the Cutover Record would
be "ceremony theater" (governing constraint item 73) — asymmetric
hardening of one artifact in a system whose actual boundary is
elsewhere. If a future phase decides certification *must* be portable
(e.g. a genuinely separate deployment/build pipeline), that decision
should re-open this choice explicitly, since portability is exactly
when a signature stops being theater and starts being necessary.

**Canonical serialization:** `json.dumps(document, indent=2,
sort_keys=True) + "\n"`, written via the same `mkstemp` +
`fsync` + `os.replace` atomic-write idiom every other protected-record
writer in this codebase already uses
(`repository_identity.py::_write_atomic`,
`hatp_mandatory_cutover.py::_atomic_write_json`). `certification_id` is
derived as a SHA-256 hex digest over this canonical serialization of the
record's authority-sensitive fields (excluding `certification_id`
itself, computed before it is assigned) — deterministic, collision-
resistant, and never caller-suppliable.

## 17. Storage Keying — Multi-Repository Topology

**Explicit finding carried forward:** 149O.18A/149O.19 retained a flat,
single-slot Cutover Record topology (one `cutover-record.json` per
protected root, not per repository) — an acknowledged, documented,
*safe* limitation (a second repository sharing the root fails
closed-unavailable, never unsafe).

**Selected for certification: repository/deployment-keyed storage from
the start**, via `certifications.json`'s and `certification-
bindings.json`'s own keyed-entry structure (§8) — both files are single
files under the shared protected root, but each internally keys entries
by `(repository_instance_id, canonical_deployment_root)`, exactly
mirroring how `registry.json`'s own `deployment_bindings` dict is
already keyed by `repository_id` (`hatp_bootstrap.py:435-440`). This
avoids *worsening* the existing single-slot limitation (governing
constraint item 68) without attempting to repair the Cutover Record's
own topology, which is out of this phase's scope (item 149).

**Cutover/certification interaction:** the Cutover Record remains flat
per HMRC-001 v1.0; a repository-keyed certification underneath a
flat-topology Cutover Record creates no contract conflict, because
certification validation (§18) is a read consulted *by* readiness
assessment, not a rewrite of the Cutover Record's own storage shape.

## 18. Validation Algorithm (Selected)

Executed fresh, in full, on every `assess_hatp_mandatory_activation_
readiness` call (no cache, mirroring HMRC-REQ-052's discipline exactly)
and again inside the lock-held recheck immediately before any future
`activate_hatp_mandatory` write (mirroring `_write_cutover_transition`'s
existing `readiness_check` hook, §23):

```
1. resolve protected root            (HATPTrustStore.production().root)
2. resolve repository_instance_id    (repository_identity.py, read-only)
3. resolve canonical_deployment_root (hatp_bootstrap.py, read-only)
4. load certification-bindings.json  -> active_certification_id, or MISSING
5. load certifications.json          -> CertificationRecord for that id, or MISSING
6. strict-parse both documents       (closed schema, duplicate-key rejection,
                                       strict version/timestamp grammar) -> MALFORMED on any deviation
7. validate repository_instance_id + canonical_deployment_root match  -> WRONG_REPOSITORY / WRONG_DEPLOYMENT
8. validate status == "active"                                         -> REVOKED
9. recompute implementation_commit + implementation_scope_digest fresh
   from the current working tree, compare against the record            -> IMPLEMENTATION_MISMATCH
10. validate contract_versions against the four frozen contracts' own
    current version headers                                             -> CONTRACT_MISMATCH
11. validate certification_id itself re-derives from the record's own
    fields (self-consistency, detects tampering of the file in place)   -> MALFORMED
12. only if every step above passes                                     -> VALID
```

Every non-`VALID` outcome maps to `mandatory_consumption_
implementation_independently_verified = False`. Only `VALID` maps to
`True`. No partial credit, no "close enough" outcome (governing
constraint items 92-94).

## 19. Failure Vocabulary (Typed, Not Yet Fully Frozen)

Conceptual outcomes, matching §18's steps:

```
MISSING | MALFORMED | WRONG_REPOSITORY | WRONG_DEPLOYMENT |
IMPLEMENTATION_MISMATCH | CONTRACT_MISMATCH | REVOKED | VALID
```

Per the governing prompt's own instruction (item 92): this vocabulary
is **not frozen** by this architecture phase. It is presented as a
concept sufficient to prove the design is implementable and
enumerable, and is explicitly deferred to the recommended contract-
freeze phase (§29), the same way HMRC-001 froze `HATPVerificationStatus`
precisely while this document does not attempt to freeze an equally
precise enum here.

## 20. Freshness, TOCTOU, and Activation-Lock Interaction

**No cache, anywhere.** Every readiness assessment and every activation
attempt re-runs §18 in full — this extends HMRC-REQ-052's "no cached
Consumption Mode" discipline to certification validation identically.

**Activation lock interaction (selected):** certification validation
occurs *inside* the same lock-held recheck `_write_cutover_transition`'s
`readiness_check` hook already performs immediately before writing the
Cutover Record (`hatp_mandatory_cutover.py:669-681`) — not as a separate,
earlier, and therefore staler check. This is a direct, minimal extension
of an already-existing hook: `readiness_check` is already a
zero-argument callable invoked fresh under the lock; a future
implementation adds §18's algorithm as one more term inside the existing
`_assess_hatp_mandatory_activation_readiness_at_root` conjunction that
hook already calls. No new lock, no new race window, no new hook
signature.

**Consequence:** if certification is revoked, or the working tree is
modified in a way that changes `implementation_scope_digest`, between an
earlier advisory `assess_hatp_mandatory_activation_readiness()` call and
a later locked `activate_hatp_mandatory()` attempt, the fresh recheck
inside the lock observes the new state and refuses — exactly the
property HMRC-REQ-054/055's existing readiness re-check already
guarantees for every other term in the conjunction.

## 21. Revocation

**Selected mechanism:** the same admin tool (§14) writes `status:
"revoked"` and `revoked_at: <timestamp>` onto the existing
`CertificationRecord` (mirroring `SignerRecord`/`AuthorityRecord`'s
existing `_require_revoked_at_consistency` pattern exactly — status and
`revoked_at` are validated together, never independently). This is a
**field mutation on an otherwise immutable record**, not a deletion —
the record remains present, auditable, and readable as historical
evidence that a certification once existed and was later revoked, which
deletion would destroy.

**No repo-local revocation path exists** — consistent with §15, revoking
requires the same protected-root write access creating did.

**Revocation vs. cutover mode (critical, HMRC-001-consistent):**
revoking a certification that a deployment already used to reach
`HATP_MANDATORY` **does not, and structurally cannot, cause
`HATP_MANDATORY → LEGACY_COMPATIBLE` or `HATP_MANDATORY → PREPARED`**.
The Cutover Record's own transition graph (§17 above; HMRC-REQ-038/039)
has no reverse edge at all — nothing this architecture adds changes
that graph. Post-activation, `assess_hatp_mandatory_activation_
readiness` and any future re-derivation of `mandatory_consumption_
implementation_independently_verified` become operationally irrelevant
to the *mode* itself (mode is already `HATP_MANDATORY`, a settled fact);
a revoked certification instead should feed a **separate, future
operational-readiness/diagnostic signal** ("this deployment is
`HATP_MANDATORY` but its independent-verification certification is
currently invalid") — never an automatic downgrade. This architecture
does not implement that diagnostic signal; it only guarantees the
design does not require or invite mode downgrade to express revocation.

## 22. Supersession and Recertification

**Selected:** recertification creates a *new* `CertificationRecord`
(new `certification_id`, new `implementation_commit`/
`implementation_scope_digest` reflecting the changed implementation) and
requires a *separate*, explicit admin write to `certification-
bindings.json` to make it active (§12's decoupling). The *old* record is
never mutated to reflect the new implementation — it remains, unchanged,
as historical evidence of what was certified and when. Old-implementation
replay (§9's `implementation_scope_digest` mismatch) and old-contract
replay (§10's `contract_versions` mismatch) are both structurally
rejected by §18 step 9/10 without any special-cased "is this
superseded" check — the *comparison against current state* is what
does the rejecting, not a supersession flag.

**No implicit-latest selection anywhere** (§12, restated): even with
multiple `CertificationRecord` entries for the same repository/
deployment key present in `certifications.json`, only the one named by
`certification-bindings.json`'s explicit `active_certification_id`
pointer is ever consulted.

## 23. Concurrency

**Selected:** every write (create, activate, revoke) to
`certifications.json`/`certification-bindings.json` acquires the same
kind of exclusive `fcntl.flock` lock `_write_cutover_transition` already
uses on its own transition-lock file, using a dedicated
`.certification-transition.lock` file under the protected root (a
distinct lock file from the Cutover Record's own
`.cutover-transition.lock`, since the two concerns are independently
auditable per §6/§17 and should not serialize on each other
unnecessarily). Within one lock hold: read current state, validate the
requested transition (recertification race: last confirmed write wins,
deterministically, because both racing writers serialize through the
same lock and the second writer's precondition check — e.g. "does this
`certification_id` already exist" — observes the first writer's
already-committed state), then perform one atomic `os.replace`. No
check-then-replace race window exists, mirroring `_write_cutover_
transition`'s own TOCTOU discipline exactly (§20 above).

**Revocation-race disposition:** a revoke and a concurrent recertify
both serialize through the same lock; whichever completes second
observes the other's already-written state as its starting point, so
"revoke old cert while a new cert is simultaneously being activated"
cannot produce an ambiguous or half-applied result — the lock make it a
strict, observable ordering, not a race.

## 24. Threat Model and Attack Analysis

**Threat-A (this architecture's governing threat, unchanged from
HMRC-001 §28):** the agent/attacker principal CAN edit the repository,
choose evidence, invoke commands, call public Python functions directly,
and modify any repository-local state. It CANNOT write protected Class-B
trust-root state, forge a hardware-backed signature, or downgrade
Consumption Mode. Root/full-host compromise (Threat B) remains
explicitly out of scope, exactly as HMRC-001 already scopes it — this
architecture claims no protection against it.

Attack-by-attack disposition (each rejected structurally, not by
policy prose alone):

| # | Attack | Disposition |
|---|---|---|
| 1 | Agent forges repo-local files (`PROJECT_STATUS`, phase report, fake certification-looking JSON in `.pcae/`) | No effect — certification lives under the protected root, never `.pcae/` (§6) |
| 2 | Agent commits a fabricated commit-SHA-shaped metadata blob | No authority — commit identity is only one of two required implementation-identity terms (§9); `implementation_scope_digest` is independently recomputed from live file contents |
| 3 | Agent copies `149O.19`'s real phase report from repo A into repo B | No effect — `verification_record_digest` is evidentiary metadata only (§8), never authority; repository/deployment binding (§18 step 7) rejects regardless |
| 4 | Cross-repository replay: copy `certifications.json`/`certification-bindings.json` from repo A's protected root into repo B's | Rejected at §18 step 7 — `repository_instance_id` mismatch |
| 5 | Cross-deployment replay: same repository ID, different `canonical_deployment_root` | Rejected at §18 step 7 — deployment-binding mismatch, same defense `deployment_binding_matches` already provides |
| 6 | Cross-implementation replay: valid certification for implementation X presented to authorize activation of modified implementation Y | Rejected at §18 step 9 — `implementation_scope_digest` mismatch. Highest-priority property, explicitly verified structurally sound |
| 7 | Contract-version replay: HMRC-001 revised, old certification silently re-applied to new semantics | Rejected at §18 step 10 — `contract_versions` mismatch unless an explicit future compatibility rule is added (none exists today) |
| 8 | Certification deletion | Absence maps to `MISSING` at §18 step 4/5 -> `False`. No legacy fallback exists to fall back *to* — there was never a "legacy" certification state |
| 9 | Certification corruption (malformed JSON, duplicate keys, unknown fields, boolean version) | Rejected at §18 step 6 -> `MALFORMED` -> `False`, mirroring `hatp_mandatory_cutover.py`'s existing strict-parser discipline |
| 10 | Unknown/future schema version | Fails closed at §18 step 6, same discipline as `CUTOVER_RECORD_SCHEMA_VERSION` mismatch handling |
| 11 | Self-certification: agent attempts to call a certification writer | No such API exists under agent-reachable production code (§15); the only writer is the separate admin tool (§14), itself gated by OS permissions, not an in-process check |
| 12 | Agent points a hypothetical validator at an attacker-controlled alternate root | Production validation always resolves `HATPTrustStore.production().root` internally, never a caller-suppliable override (§6, §14) |
| 13 | Environment-variable root override | No such override exists or is proposed anywhere in this design (§14 explicitly rejects a `--root` flag in ordinary invocation) |
| 14 | Symlink redirection of the certification files or their parent | Rejected via the same `_reject_symlink` discipline `hatp_mandatory_cutover.py`/`repository_identity.py`/`hatp_bootstrap.py` already apply to every protected path they own |
| 15 | Partial/torn write (process killed mid-write) | Atomic `mkstemp` + `fsync` + `os.replace` (§16) guarantees no partially-valid document is ever observable |
| 16 | Protected root itself absent/unreadable | Fails closed at §18 step 1/4 -> `MISSING`-equivalent -> `False`, exactly mirroring the existing `class_b_protected_storage_available` check |
| 17 | Certification revoked between an earlier advisory readiness check and a later locked activation attempt | Refused — fresh lock-held recheck observes the revocation (§20) |
| 18 | Implementation modified (working tree edited) between an earlier check and a later locked activation attempt | Refused — fresh recheck recomputes `implementation_scope_digest` (§20) |
| 19 | Certification revoked *after* `HATP_MANDATORY` is already active | Never causes mode downgrade (§21) — by design, not by omission |
| 20 | Two certifications race to become "active" simultaneously | Deterministic via lock-held ordering (§23), never ambiguous |

## 25. Certify vs. Activate — Separate Ceremonies (Explicit)

`CERTIFY` (§13) and `ACTIVATE` (`activate_hatp_mandatory`, unchanged by
this phase) are, and must remain, separate ceremonies performed by the
same principal but never combined into one action. A protected
administrator MAY certify an implementation and explicitly choose not
to activate it (e.g. certifying well ahead of an intended cutover
window). Certification satisfying §18's `VALID` outcome makes
`mandatory_consumption_implementation_independently_verified = True`
inside the readiness conjunction — it does not, by itself, cause
`PREPARED → HATP_MANDATORY`; every other HMRC-REQ-054 term (Class-B
deployment valid, HATP substrate operational, HSCE signing available,
etc.) must independently also hold, and activation itself remains the
separate, explicit `activate_hatp_mandatory` call HMRC-REQ-042 already
requires.

## 26. Post-Activation Certification Loss (Restated, Frozen)

If, after a deployment reaches `HATP_MANDATORY`, its certification
later becomes invalid (revoked, corrupted, implementation drifted) — the
cutover mode remains `HATP_MANDATORY`. This is not an oversight; it is
the same monotonicity property HMRC-REQ-039/040 already establish for
the mode itself, extended consistently rather than contradicted. What
*may* legitimately change is a separate, future operational-readiness
signal (§21) reporting the certification's current invalidity for
diagnostic/audit purposes — never the mode.

## 27. Test Seam (Selected)

Mirroring every other module this architecture builds on
(`HATPTrustStore.__init__`'s `_test_only_root`,
`_assess_hatp_mandatory_activation_readiness_at_root`'s explicit
`protected_root` parameter): a future implementation's certification
validator and writer each expose an internal, non-production-reachable
function accepting an explicit `protected_root: Path`, used only by
tests constructing isolated fixture roots. The production entrypoints
(`assess_hatp_mandatory_activation_readiness`'s future certification
term, and the admin tool itself) always resolve
`HATPTrustStore.production().root` internally and never accept a
caller-supplied root.

## 28. Privilege Separation and File Mode

This architecture does not invent new Unix permission bits. It
specifies only the same *property* `hatp_bootstrap.py::inspect_
bootstrap_environment` already checks for the trust-store root itself:
the certification files' containing directory (the same protected root)
must not be group- or world-writable, and its owning OS principal must
be the Human/Admin principal, distinct from the Agent OS principal
(149O.1B.1 §6-§9). No certification-specific permission scheme is
introduced beyond what already governs every other file under this
root.

## 29. Contract Freeze Requirement (Recommended)

**Strong expectation: YES**, a dedicated frozen contract is required
before implementation, for the same reason HMRC-001 itself was frozen
before its own implementation began: this is authority-bearing
infrastructure, and an unfrozen, ad hoc implementation risks exactly the
kind of authority-collapsing shortcut (§4's semantic wall) this phase
exists to prevent.

**Recommended scope for `149O.19.2` (or the repository-conventional
equivalent numbering):**

- Freeze the exact `CertificationRecord`/`CertificationBinding` schema
  fields (§8), closed-field enumeration, and strict validation rules.
- Freeze the exact frozen authority-bearing file set and digest
  algorithm for `implementation_scope_digest` (§9).
- Freeze the exact minimal `contract_versions` set (§10) and how a
  future contract-version bump is handled (compatible vs. incompatible).
- Freeze the exact typed failure vocabulary (§19).
- Freeze the exact validation algorithm step ordering (§18) as
  normative, not merely descriptive.
- Freeze revocation/supersession/concurrency semantics (§21-23) as
  normative requirements, mirroring HMRC-REQ-038-053's own level of
  precision.
- Freeze the "no self-certification, no repo-metadata authority, no
  automatic activation" invariants (§4, §15, §25) as explicit,
  numbered, non-negotiable requirements — this document's prose
  equivalents of HMRC-001's `MC-` invariants.

**Recommended future sequencing** (mirroring HMRC-001's own §35
precedent of naming its own next phase):

```
149O.19.1  Certification Architecture                (this phase)
149O.19.2  Certification Contract Freeze
149O.19.3  Independent Contract Verification
149O.19.4  Implementation Plan
149O.19.5  Protected Certification/Latch Implementation
149O.19.6  Independent Implementation Verification
  -- then, separately and only if explicitly authorized --
  deployment provisioning / activation readiness review
  protected certification ceremony (real, out-of-band, human-performed)
  PREPARED transition
  activation
```

Exact numbering is subject to repository convention at the time each
phase is opened; the sequence and gating (no phase skips the one before
it; no implementation begins before its own contract is independently
verified) is what this architecture recommends, not the literal labels.

## 30. Stop-Condition Disposition

Per the governing prompt's four named stop conditions:

- **No executable identity (item 139):** **Not triggered as a full
  stop.** §9 selects an implementation-identity binding
  (`implementation_commit` + `implementation_scope_digest` over a
  frozen file set) that is strictly stronger than a bare commit SHA and
  consistent with this repository's existing trust model, while
  explicitly documenting its residual transitive-dependency limitation
  as a named prerequisite for a *future*, more automated deployment-
  manifest primitive — not invented here, not faked with a bare `git
  rev-parse HEAD` either.
- **No admin writer host (item 140):** **Not triggered.** The existing
  Class-B topology (149O.1B.1) already hosts exactly the kind of
  protected, non-agent-writable, OS-permission-bounded writer this
  design needs — §5-§7 select it directly rather than inventing a
  weaker substitute.
- **Unsafe multi-repo topology (item 141):** **Not triggered.** §17
  selects repository/deployment-keyed storage from the start,
  strictly safer than (and not inheriting) the Cutover Record's own
  flat single-slot limitation.
- **Automatic downgrade on revocation (item 142):** **Not triggered.**
  §21/§26 explicitly design revocation to never downgrade
  `HATP_MANDATORY`, consistent with HMRC-REQ-039/040's monotonicity.
- **Circular trust (item 143):** **Not triggered.** §25 keeps
  `CERTIFY` and `ACTIVATE` as separate ceremonies performed by the same
  pre-existing Protected Activation Authority principal; certification
  authority exists independently of, and prior to, any
  `HATP_MANDATORY` activation — it is never derived from an already-
  activated state.

## 31. Architecture Verdict

```
HATP MANDATORY INDEPENDENT-VERIFICATION CERTIFICATION ARCHITECTURE:
SELECTED — READY FOR CONTRACT FREEZE
```

Authority principal, protected root, artifact/latch model,
implementation-identity binding, repository/deployment/contract binding,
creation ceremony, validation algorithm, revocation model, supersession
model, readiness integration, activation interaction, post-activation
revocation behavior, and multi-repository behavior are each selected
exactly once above, with no authority-sensitive item left open as a
TBD. The one genuine residual limitation (§9's transitive-dependency
coverage of `implementation_scope_digest`) is named explicitly as a
future-hardening item, not hidden, and does not weaken this
architecture below what the repository's existing Cutover-Record trust
model already accepts.

**Recommended next phase:** `149O.19.2` (or repository-conventional
equivalent) — HATP Mandatory Independent-Verification Certification
Contract Freeze.

## 32. HATP Production Readiness and Runtime State (Unchanged)

HATP production remains **NOT READY**. Runtime remains **Observed /
observe / unavailable**. Nothing in this phase changes either fact —
this phase designed a certification mechanism; it did not create one,
and creating a design does not, and could not, cause
`assess_hatp_mandatory_activation_readiness().ready` to become `True`.

---

## 33. Explicit Confirmations (Restated for the Phase Report)

No production source (`src/pcae/**`) was modified. HMRC-001 v1.0,
HSCE-001 v1.1, HATP-001 v1.0, and RAE-001 v1.0 all remain byte-unchanged.
PB contracts/policies (PBPA-001, PBPC-001) remain byte-unchanged. The
current hardcoded `False` readiness ceiling remained unchanged. No
certification artifact/latch was created. No Cutover Record or
activation marker was created or modified. No real `HATP_MANDATORY`
activation occurred. No Class-B provisioning occurred. No Permission
Broker behavior changed. `POL-005` remained unchanged. No `COMP-002`
capability was implemented. `PROJECT_STATUS.md` was not made activation
authority. Phase reports were not made activation authority. Test
results were not made activation authority. A Git commit SHA alone was
not made activation authority — it is named only as one identity
component alongside `implementation_scope_digest` (§9). No automatic
self-certification path was created or proposed as production-reachable
(§15, §25). B-149O-1..4 remain independently closed at the system
implementation/enforcement boundary with deployment/operational
activation deferred, unchanged by this phase. HATP production remains
**NOT READY**. Runtime remains **Observed / observe / unavailable**.
