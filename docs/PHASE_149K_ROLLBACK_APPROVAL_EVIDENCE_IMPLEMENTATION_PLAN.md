# Phase 149K — Rollback Approval Evidence Implementation Plan

## 0. Phase Identity

**Phase:** 149K
**Type:** Approval-evidence implementation **planning only**. No `src/pcae/**`
change, no `docs/contracts/**` change, no approval-evidence implementation,
no AG3/AG5 wiring, no production `approval_present=True`.
**Governing contract:** RAE-001 v1.0, FROZEN (Phase 149I), independently
verified with zero BLOCKING findings (Phase 149J,
`docs/PHASE_149J_ROLLBACK_APPROVAL_EVIDENCE_CONTRACT_INDEPENDENT_VERIFICATION.md`).
**Depends on (all unamended):** CHGR-001 v1.0, IWC-001 v1.2, PEC-001,
RWMPC-001 v1.0, PBPA-001 v1.0, PBPC-001 v1.2. Structural precedent only
(never composed): TAMC-001 / TAMPC-001.
**Runtime posture, unaffected:** State **Observed**, maximum capability
**observe**, execution availability **unavailable**.

## 1. RAE-001 Baseline (recap)

149J independently verified 81 sequential, gap-free, duplicate-free RAE
requirements, 0 Blocking findings, 1 PARTIAL threat-model row (structurally
valid but noncanonical record — traced to the repository's pre-existing
STRATEGIC_GAP ceiling, not a new gap). RAE-001 freezes, as normative prose
(not as authored schema/code): the `rollback-approval` Decision Template
(§7), the `rollback_approval_binding` field table (§8), AG3/AG5 operation
identity (§9-§10), task/state binding (§11), the Evidence Validator's
conceptual interface (§12), the `approval_present` derivation rule (§13),
freshness at 24 hours (§14), revocation/supersession (§15), replay
prevention (§16), provenance/integrity (§17), the IWC/AESIC exclusion
(§18), legacy-flag exclusion (§19), and the approval-creation boundary
(§26). This document plans the concrete implementation of all of the
above; it implements none of it.

Two inherited STRATEGIC_GAP findings remain load-bearing for this plan and
are not to be papered over:

1. No stronger-than-self-declared human identity substrate exists in this
   repository (RAE-REQ-005/006).
2. No technical privilege separation between an agent process and a human
   operator exists (RAE-REQ-009).

This plan's identity/authority design (§7, §11 below) is built to the
honest ceiling these two findings establish, not beyond it.

## 2. Required Initial Inspection — Results

```
git status --short                      -> clean
git status --branch --short             -> ## main...origin/main
git rev-list --count origin/main..HEAD  -> 0
```

Latest completed phase: 149J (report: complete, VERIFIED WITH
NON-BLOCKING FINDINGS — RAE-001 v1.0 CONFORMS).
`pcae health` -> healthy. `pcae check` -> passed. `pcae status coherence`
-> coherent. `pcae doctor task-memory` -> clean, no inconsistencies.
`pcae push check` -> clean (nothing_to_push). `pcae runtime inspect` ->
Observed / observe / unavailable / Permission Broker status
`execution_unavailable` / registry empty (0 plugins, 0 capabilities).
`pcae notify status` -> Telegram configured, enabled, ready.
`pcae phase-report show --latest` -> 149J report present, consistent,
notification dispatched (telegram, success).
`pcae phase-report reconcile --phase-id 149J` -> `status:
delivery_recorded_bookkeeping_incomplete`, `receipt: absent`, `mutation:
none (inspection only)`. This is a pre-existing bookkeeping-completeness
observation on 149J's own receipt trail, not a 149J correctness defect
and not something this planning-only phase is scoped to repair; recorded
below as an OBSERVATION (§17), not acted on.

Confirmed: repo clean, ahead count 0, 149J complete, RAE-001 v1.0
verified with zero Blocking findings, AG3/AG5 unimplemented, runtime
unchanged (Observed / observe / unavailable before this phase's own
inspection work, reconfirmed after in §16 below).

## 3. Primary Sources Read

- `docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md` (RAE-001 v1.0,
  read in full, all 33 sections / 81 requirements).
- `docs/contracts/REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md`
  (RWMPC-REQ-013, RWMPC-REQ-022, RWMPC-REQ-023, RWMPC-REQ-027 verified by
  direct line citation).
- `docs/contracts/AUTHORITY_EVALUATION_MODEL_CONTRACT.md` (AEM-REQ-003
  verified by direct line citation).
- `src/pcae/commands/governance_record.py`, `src/pcae/governance/publication/{record.py,coordinator.py,storage.py,chgr_envelope.py,chgr_rendering.py,errors.py}`,
  `src/pcae/interactive_workflow/application/publication_service.py` —
  the live CHGR creation/publication pipeline.
- `src/pcae/schema_resources/chgr/records/*.schema.json` — CHGR record
  shapes, including `decision_template.schema.json`.
- `src/pcae/cltr/authority/authorization_candidate.py` (`HumanAuthorization`
  dataclass, lines 471-758) and
  `src/pcae/schema_resources/cltr_cutover/records/human_authorization.schema.json`
  — TAM structural precedent only (RAE-REQ-003/004), never imported.
- `src/pcae/core/agent.py` — `approve_rollback` (line 5146),
  `execute_rollback` (AG3, line 5234), `build_rollback_review` (line
  5437), `build_rollback_execution` (AG5, line 93895).
- `src/pcae/core/permission_broker_foundation.py` — `PermissionBrokerRequest`
  (lines 142-192), `MissingHumanApprovalRule`/POL-004 (lines 449-486),
  POL-001/005/006/007.
- `src/pcae/core/mutation_permission.py` (Phase 149F) — the repository's
  most recent "core governance integration module" precedent and the
  authoritative statement that it is "the *only* place in the codebase
  permitted to construct a `PermissionBrokerRequest` for a non-`pcae push`
  mutation site" (RWMPC-REQ-013) — load-bearing for §14 below.
- `docs/PHASE_149H_ROLLBACK_APPROVAL_EVIDENCE_ARCHITECTURE.md` — read and
  evaluated for currency (§4 below); its proposed module boundaries are
  **not** assumed current and are explicitly re-derived here.

**149H currency finding:** 149H's proposed shapes were explicitly
non-frozen scaffolding. RAE-001 (149I) froze field-level semantics but
left schema-file paths, the Evidence Validator's concrete algorithm, and
the canonical storage namespace open — exactly the gap this document
closes. Where this plan's module/path choices diverge from 149H's prose,
this plan follows RAE-001's text and the live codebase, not 149H,
consistent with RAE-001's own precedence rule (contract identity block).

## 4. Module Ownership Decision

**Decision: a dedicated new core module,
`src/pcae/core/rollback_approval_evidence.py`.**

Rejected alternatives, with reasons:

- **Existing CHGR module** (`governance/publication/*`) — rejected. CHGR
  code owns generic Decision Template/publication mechanics; RAE-specific
  semantics (Binding model, operation-identity family-locking, TTL,
  revocation, `approval_present` derivation) are not CHGR's concern and
  would contaminate a module that many other Decision Templates also
  depend on (RAE-REQ-001 requires CHGR to remain unmodified/uninterpreted
  by this contract).
- **Existing authority/governance module (TAM/`cltr/authority/*`)** —
  rejected outright. RAE-REQ-003/004 and the CHGR/TAM wall (CHGR-001
  §19.1, TAMC-REQ-024/025/036) forbid composing, subclassing, or wrapping
  the TAM family; a Binding record living inside `cltr/` would risk
  exactly this composition even if unintentional (import-graph risk,
  reviewer risk, future-maintainer risk).
- **`agent.py`** — rejected. `agent.py` is the AG3/AG5 *consumer*
  location, not the evidence *substrate* owner; RAE-REQ-037 requires the
  Evidence Consumer to perform no trust evaluation itself, which forbids
  putting Decision/Binding/validation logic there.
- **`mutation_permission.py`** — rejected as the owner, but noted as the
  *future* single legal call site for constructing a rollback
  `PermissionBrokerRequest` once AG3/AG5 are wired (RWMPC-REQ-013); see
  §21 (integration seam). The evidence module itself must not live there
  because `mutation_permission.py`'s own docstring already scopes it as
  "not a new policy engine... not a Runtime Enforcement adapter," and its
  existing Wave-1 contract explicitly excludes rollback-class sites.
- **`permission_broker_foundation.py`** — rejected. Item 4 of the
  governing phase prompt and RAE-REQ-039/RAE-REQ-066 both require the
  Permission Broker to remain a pure decision boundary; it must never
  gain approval-evidence-resolution logic.

**Chosen shape:** one new file, `src/pcae/core/rollback_approval_evidence.py`,
following the `mutation_permission.py` (Phase 149F) convention:
docstring header naming RAE-001 by ID/path and phase, explicit "owns" /
"is not" statement, `@dataclass(frozen=True)` models, functions grouped
by responsibility, no import of `permission_broker_foundation`,
`agent.py`, or `cltr/authority/*`.

## 5. Recommended Core Module Shape

```
src/pcae/core/rollback_approval_evidence.py
```

Responsibilities (single file, per RAE-001's own single-contract-two-
profiles resolution, RAE-REQ-023):

1. Closed decision vocabulary (`RollbackDecisionType` enum).
2. `RollbackApprovalDecisionRef` — thin, read-only pointer to a published
   CHGR record (never a copy of its content) used inside a Binding.
3. `RollbackApprovalBinding` — the frozen dataclass for RAE-001 §8's
   field table (§7 below).
4. Discriminated AG3/AG5 operation-reference types (§9).
5. Canonical serialization (reuses CHGR canonical-JSON conventions;
   §12).
6. Canonical persistence (`RollbackApprovalEvidenceStore`; §13).
7. Creation API (`create_rollback_approval_binding`; §17).
8. `RollbackApprovalValidationResult` enum + `ValidatedEvidence`
   dataclass (§19).
9. `resolve_rollback_approval_evidence(operation_context, evidence_id)`
   — the Evidence Validator (§12 of RAE-001; §19 below).
10. `derive_rollback_approval_present(operation_context, evidence_id) ->
    bool` — the narrow derivation API AG3/AG5 will eventually call
    (§21).

Not implemented here (149K is planning only, §0): none of the above is
written as code by this phase.

## 6. Permission Broker Purity (item 4 restated)

`rollback_approval_evidence.py` derives `approval_present: bool` only. It
SHALL NOT import `permission_broker_foundation`, construct a
`PermissionBrokerRequest`, or return `ALLOW`/`DENY`/`HUMAN_REVIEW`. The
future integration seam (§21) is a **caller** of both this module and
`mutation_permission.py`-style adapter code, never a merge of the two.

## 7. Data Model — Decision

RAE-001 deliberately does **not** define a new "Decision" Python type
distinct from the existing `human_governance_record` (RAE-REQ-102 is not
a numbered requirement, but §3's definition of "Rollback Approval
Decision" is explicit: it *is* a published `human_governance_record` +
its three CHGR companion artifacts, produced through the unamended CHGR
pipeline). This plan therefore does **not** introduce a parallel
`Decision` dataclass that duplicates CHGR's own record. It introduces
only a minimal, read-only reference type used by the Binding record to
point at that CHGR record:

```python
@dataclass(frozen=True)
class RollbackApprovalDecisionRef:
    """Family-locked pointer to a published rollback-approval Decision
    (a human_governance_record whose template_ref resolves to
    rollback-approval/1.0.0), never a copy of its content
    (RAE-REQ-018)."""
    record_id: str          # human_governance_record.record_id
    record_digest: str      # governance_record_integrity's content digest
```

This mirrors RAE-001 §8's `governance_record_reference` field exactly
(`{record_id, record_digest}`) and matches the codebase's existing
pattern of a `RecordReference`-shaped pointer used by TAM's
`target_reference`/`request_reference`/`readiness_reference` (structural
precedent only, RAE-REQ-003 — no TAM type is imported; this is an
independently-defined, identically-shaped dataclass).

**Decision Template authorship** (RAE-REQ-011/012/013 field values) is
planned as a new, frozen Python constant inside
`rollback_approval_evidence.py` (e.g. `ROLLBACK_APPROVAL_TEMPLATE:
dict`), consumed as the `template_id`/`template_version`/template-body
input to the existing, unmodified `PublicationReadinessPackage`/
`build_publication_record` pipeline (`governance/publication/record.py:147`).
No new CHGR schema field, registry, or validation hook is required:
`build_publication_record` already treats `template_id`/`template_version`
as opaque caller-supplied strings (§3 research finding). The template's
own JSON shape validates against the existing, unmodified
`decision_template.schema.json` if/when a future phase chooses to persist
it as a standalone artifact for `pcae` tooling to read generically; that
persistence mechanism is explicitly **not** required by RAE-001 and is
left as a `MAY_CHANGE`, not `MUST_CHANGE`, in §20's file budget.

## 8. Data Model — Binding

```python
@dataclass(frozen=True)
class RollbackApprovalBinding:
    evidence_id: str
    governance_record_reference: RollbackApprovalDecisionRef
    rollback_site: RollbackSite                      # enum: AG3 | AG5
    rollback_operation_reference: (
        Ag3OperationReference | Ag5OperationReference  # discriminated, §9
    )
    task_id: str | None
    repository_state_binding: RepositoryStateBinding   # {head_commit_sha, branch}
    created_at: str                                    # RFC3339 UTC, CHGR-style
    expires_at: str                                     # RFC3339 UTC
    state: BindingState                                 # issued|used|revoked|expired
    decision: RollbackDecisionType                      # APPROVE|DENY (denormalized)
    replay_binding: str
    revocation_metadata: RevocationMetadata | None = None
    use_binding: str | None = None                       # opaque outcome-record ref
    content_digest: str = ""                              # computed last (§12)
```

Field-for-field this is RAE-001 §8's table (RAE-REQ-017), independently
re-derived, not copied from `HumanAuthorization`'s Python shape (no
import). `__post_init__` conditional-requirement checks mirror
`HumanAuthorization.__post_init__`'s *pattern* (structural precedent) but
are independently authored against RAE-001's own conditions:
`revocation_metadata` required iff `state == REVOKED`, forbidden
otherwise (RAE-REQ-017 row); `use_binding` required iff `state == USED`,
forbidden otherwise (same row, RAE-REQ-050's transition target — exact
outcome-record family TBD by the implementation phase, since RAE-001
does not freeze what "the consuming rollback attempt's own outcome
record" concretely is; flagged as an OBSERVATION, §17).

Immutability (RAE-REQ-057): once constructed, no code path mutates a
`RollbackApprovalBinding` instance's identity/operation fields in place;
a Python `frozen=True` dataclass enforces this at the language level for
in-memory instances, and the storage layer (§13) enforces it for
persisted artifacts by refusing overwrite (mirroring
`PublicationRecordStore.write_record`'s existing `if path.exists(): raise`
guard — duplicated, not imported, per item 51).

## 9. AG3 / AG5 Operation-Reference Profiles and Family Locking

**Decision: discriminated dataclasses, not an enum + loose dict, not a
single generic dataclass with optional fields.**

```python
@dataclass(frozen=True)
class Ag3OperationReference:
    job_id: str
    original_commit_sha: str

@dataclass(frozen=True)
class Ag5OperationReference:
    per_id: str
    ecp_id: str
```

`RollbackApprovalBinding.rollback_operation_reference`'s static type is
`Ag3OperationReference | Ag5OperationReference` (a Python `Union`), and
`__post_init__` cross-validates that `rollback_site == AG3` implies
`isinstance(rollback_operation_reference, Ag3OperationReference)` and
symmetrically for AG5 (RAE-REQ-022's "mismatched shape is a
schema-validation failure, not a scope-validation failure" — this
Python-level discriminated-union check *is* that schema-validation
failure, raised as a `RollbackApprovalBindingConstructionError` at
construction time, never silently coerced). This directly satisfies item
9's requirement ("prevent an AG3 binding object from being interpreted
as AG5") through the type system itself rather than through a runtime
tag comparison alone — an AG5 binding object is not merely
*tagged*-different, it is a *structurally different Python type*, so an
accidental cross-family field read (e.g. `.job_id` on an AG5 reference)
fails immediately with `AttributeError` rather than returning `None` or
a stale value. No extra broad generic "target" field is added (item 7).

Serialized JSON representation carries `rollback_site` as an explicit
discriminator tag alongside the profile-specific fields, matching
`human_authorization.schema.json`'s own family-locking pattern via
`allOf` + `const` restriction (structural precedent, RAE-REQ-003) —
independently authored, not copied, for a future
`rollback_approval_binding.schema.json` (§12 below).

## 10. Closed Decision Vocabulary

```python
class RollbackDecisionType(str, Enum):
    APPROVE_ROLLBACK = "approve_rollback"
    DENY_ROLLBACK = "deny_rollback"
```

Used both as the Decision Template's `options[].option_id` value (§7,
matching RAE-REQ-013 exactly) and as the Binding record's denormalized
`decision` field value (mapped `APPROVE_ROLLBACK -> "APPROVE"`,
`DENY_ROLLBACK -> "DENY"` per RAE-001 §8's `decision` field, which uses
`APPROVE`/`DENY` — the plan preserves this exact naming distinction
between the CHGR-level `selected_option_id` vocabulary
(`approve_rollback`/`deny_rollback`) and the Binding-level `decision`
vocabulary (`APPROVE`/`DENY`), rather than silently unifying them, since
RAE-001's own field table keeps them textually distinct). Any other
string (e.g. `"approve_everything"`) SHALL raise a construction-time
`ValueError` from the `Enum` lookup itself — no permissive string field
is used anywhere in this model (item 10, item 62 test).

## 11. Canonical Serialization

**Decision: reuse CHGR's existing canonical-JSON conventions (field
ordering, timestamp format via `chgr_timestamp`, UTF-8, no floating
point), not a second serializer.** `rollback_approval_evidence.py` will
import only the already-generic, non-TAM-coupled helper
`chgr_timestamp` from `governance/publication/chgr_envelope.py` (a pure
string-normalization function with no CHGR-record-shape dependency) for
timestamp formatting consistency; it will **not** import
`envelope_for`/`validate_chgr_artifact`, since those are scoped to the
four fixed CHGR `RECORD_FAMILIES` (§3 research finding) and
`rollback_approval_binding` is deliberately not one of them (RAE-REQ-016:
"not a CHGR-001 record family"). A dedicated, independently-authored
canonical-serialization function (`_canonical_bytes(binding) -> bytes`)
is planned, following the same discipline `record.py`/`storage.py`
already apply (stable key order, `json.dumps(..., sort_keys=True,
separators=(",", ":"))`-equivalent), but is new code, not a shared
utility import, to avoid coupling to CHGR's four-family closed list.

## 12. Canonical Storage Location

**Decision: a new, dedicated namespace,**

```
.pcae/rollback-approval-evidence/bindings/<evidence_id>.json
```

**not** `.pcae/governance-records/` (that path does not exist in
production; RAE-REQ-056's own text only speculates it as an illustrative
example), and **not** `.pcae/publication-execution/` (that is CHGR's own
namespace, scoped to package/publication-attempt bookkeeping fields this
record type does not have), and **not**
`src/pcae/schema_resources/cltr_cutover/**` (RAE-REQ-003/RAE-REQ-049
forbid this explicitly). This satisfies RAE-REQ-056's requirement
("canonical governance-artifact location... not an arbitrary
caller-specified file path") while giving the Binding record family its
own top-level `.pcae/` sibling directory, exactly mirroring
`.pcae/publication-execution/`'s own existing sibling-directory pattern
(`records/`, `published/`, `attempts/`) without physically nesting
inside it (avoiding any accidental coupling to `PublicationRecordStore`'s
package/marker semantics, which do not apply to Bindings).

Directory shape:
```
.pcae/rollback-approval-evidence/
    bindings/<evidence_id>.json       # one immutable file per Binding
    revocations/<evidence_id>.json    # §15: revocation as a separate
                                       #   immutable record, never an
                                       #   in-place edit of bindings/*.json
```
(No `decisions/` subdirectory: Decision records remain CHGR's own
artifacts, stored under CHGR's existing `.pcae/publication-execution/records/`
path — this plan does not duplicate that storage.)

## 13. Filenames

`bindings/<evidence_id>.json`, where `evidence_id` is a canonical
identifier assigned only at creation (RAE-REQ-017), planned as
`f"rae-{uuid4().hex}"` (mirroring CHGR's own `f"chgr-{uuid4().hex}"` and
PublicationCoordinator's `f"pubauth-{uuid4().hex}"` naming convention,
`coordinator.py:91`/`record.py`). No `latest_*.json`, no mtime-derived
name, no caller-suppliable filename (item 13, item 75).

## 14. Atomic Persistence

**Decision: duplicate, not import, the atomic-write helper.**
`governance/publication/storage.py:_write_atomic_json` is scoped inside a
module that also owns `PublicationRecordStore`'s package/marker/attempt
semantics; importing it would create an unnecessary coupling to CHGR
publication bookkeeping for a record family that isn't CHGR's. Per item
51 ("duplicate generic utility instead of violating the wall" — applied
here even though this isn't the TAM wall specifically, the same
discipline of not coupling record families through shared write paths
applies), the plan is a new, ~15-line
`_write_atomic_binding_json(path: Path, payload: dict) -> None` inside
`rollback_approval_evidence.py`, following the exact same proven
technique already used twice in this codebase
(`cltr/persistence.py:104-116`, `governance/publication/storage.py:42-55`):
`tempfile.mkstemp` in the target directory, write, `fsync`, `os.replace`.
Creation additionally refuses overwrite of an existing `evidence_id` file
(`if path.exists(): raise RollbackApprovalStorageError(...)`, mirroring
`PublicationRecordStore.write_record`'s existing guard) — a partially
written file can never appear at the final path because `os.replace` is
atomic at the filesystem level, and a *pre-existing* complete file is
never silently overwritten.

## 15. Canonicality (validator's canonical/noncanonical distinction)

This is 149J's one PARTIAL threat-model finding (item 15's direct
motivation) and the single hardest design point in this plan.

**Mechanism: creation-path provenance, not schema-shape inspection
alone.** A structurally valid JSON file dropped directly into
`.pcae/rollback-approval-evidence/bindings/` by any means other than
`create_rollback_approval_binding` (§17) is **schema-valid** (item 59's
agent-forgery test will confirm this — schema validation alone cannot
reject it) but is **not canonical**, because canonicality is established
by two independent facts the Evidence Validator checks, neither of which
a forged file can satisfy without also forging a genuine CHGR
publication:

1. **`content_digest` recomputation** (RAE-REQ-055): the Validator
   independently recomputes the Binding's own content-integrity digest
   over its canonical bytes (§11) and compares against the stored
   `content_digest` field. A hand-edited or hand-authored file whose
   `content_digest` doesn't match its own content fails immediately
   (catches naive forgery/tampering, item 73's tampering test).
2. **`governance_record_reference` resolution** (RAE-REQ-018, the
   *load-bearing* check): the Validator resolves
   `governance_record_reference.record_id` against CHGR's own existing
   storage (`.pcae/publication-execution/records/<record_id>.json`,
   read via the same lookup CHGR's own inspection code already uses,
   `governance/inspection.py`'s pattern) and requires the record to
   **actually exist, actually be published, actually resolve
   `template_ref` to `rollback-approval/1.0.0`, and match
   `record_digest` exactly**. A forged Binding file can set this field to
   any string, but cannot cause a *real* `human_governance_record` to
   spring into existence at that `record_id` with a matching digest —
   doing so would require going through the real, unmodified CHGR
   Confirmation → Publication ritual, which is exactly RAE-001's
   intended trust anchor (§5, RAE-REQ-002).

This means canonicality is **not** an independent property of the
Binding file's storage location alone (a forged file *can* be placed at
the correct path, since this plan's storage location is not itself
access-controlled beyond normal filesystem permissions — no stronger
guarantee is claimed, consistent with the STRATEGIC_GAP ceiling, §1). It
is the **conjunction** of (a) being found by an honest lookup by
`evidence_id` (never "scan the directory and trust whatever's newest,"
RAE-REQ-041) and (b) resolving to a genuinely-published CHGR record.
This is recorded explicitly as this plan's answer to 149J's PARTIAL
finding: the residual risk is not eliminated (an attacker with local
filesystem write access to `.pcae/` could, in principle, forge *both* a
Binding file and go through a real CHGR publication with a
self-declared identity — but that is exactly STRATEGIC_GAP #1/#2's
already-disclosed ceiling, not a new gap this plan introduces or hides).

## 16. Canonical Creation Path

```python
def create_rollback_approval_decision(...) -> RollbackApprovalDecisionRef: ...
def create_rollback_approval_binding(
    decision_ref: RollbackApprovalDecisionRef,
    rollback_site: RollbackSite,
    rollback_operation_reference: Ag3OperationReference | Ag5OperationReference,
    task_id: str | None,
    repository_state_binding: RepositoryStateBinding,
    ttl_hours: Literal[24] = 24,          # not caller-overridable, RAE-REQ-043
) -> RollbackApprovalBinding: ...
```

`create_rollback_approval_decision` is planned as a thin orchestration
wrapper around the **existing, unmodified** CHGR
Confirmation→Publication pipeline (`publication_service.py` /
`PublicationCoordinator`), supplying the frozen `rollback-approval`
template (§7) — it does not reimplement CHGR publication. Only this
function pair creates canonical evidence; no other code path in this
plan writes to `.pcae/rollback-approval-evidence/`. `create_rollback_approval_binding`
internally: (1) validates `decision_ref` resolves to a real, published,
correctly-templated record (§15, reusing the Validator's own resolution
check so creation and validation never drift — see item 24); (2) asserts
create-then-bind ordering (item 23: Decision must be resolvable before
Binding is constructed — no forward reference is permitted); (3)
generates `evidence_id`, `replay_binding`, `created_at`/`expires_at`;
(4) computes `content_digest` last (§11); (5) calls the atomic writer
(§14).

## 17. Human Decision Workflow (future, not implemented in 149K)

Owner: the existing Interactive Workflow + Publication pipeline
(`pcae governance-record ...` command family), per RAE-REQ-079 — not a
new parallel command family. A future thin CLI convenience wrapper (e.g.
`pcae rollback approval create --site AG3 --job-id ... --commit-sha
...`) is planned to route through: (1) the full CHGR
Confirmation→Publication ritual against the `rollback-approval` template
(producing the Decision), then (2) `create_rollback_approval_binding`
(producing the Binding) — one governed command, two canonical writes,
never a shortcut that sets a boolean directly (item 18). Not implemented
by 149K (RAE-REQ-080 restated for this phase).

## 18. Actor Identity Capture

Exactly `decision_maker_identity_evidence` at whatever `assurance_level`
CHGR's Confirmation step actually achieves today — `L0`, typed
confirmation only (RAE-REQ-006). No cryptographic signature, no OS-user
lookup, no identity-provider call is planned or fabricated (RAE-REQ-005).
This plan's Binding record captures the caller field **from the
referenced Decision record's own `decision_maker_identity_evidence`**
(RAE-REQ-026/027), never from the invoking process's own OS user, CLI
argument, or environment variable.

## 19. Approval Authority Resolution

**Decision: `eligible_authority` is validated as descriptive text only,
matching RAE-REQ-008(1)'s explicit disclosure that no authority registry
exists.** The Evidence Validator does not — and per RAE-001 cannot —
mechanically verify that the Decision's `decision_maker_identity_evidence`
"is" the single human operator beyond CHGR's own L0 confirmation guarantee
(RAE-REQ-002's list of what CHGR actually guarantees does not include
decision-maker authority, §11 restated). This plan does **not** invent an
authority check beyond what RAE-001 itself authorizes: the
`UNAUTHORIZED_APPROVER` validation outcome (RAE-REQ-036) is planned as a
structural placeholder outcome value in the enum (so the type/API shape
already accommodates a future authority-registry integration per
RAE-REQ-010), but its actual trigger condition, for now, is only "the
`eligible_authority` field's own descriptive text is present and
non-empty on the referenced template" — i.e. a template-shape check, not
an identity check. This plan does not trust a role string carried inside
the Decision record itself as an authority claim (item 20's explicit
prohibition); there is simply no stronger registry to trace to yet, and
this plan says so rather than fabricating one.

## 20. Authority Revalidation

**Decision: creation-time only, not re-validated at consumption beyond
what §19 already checks.** RAE-001 does not freeze a distinct
consumption-time authority re-check separate from validating the
Decision record's continued existence/digest match (which the Validator
already does per RAE-REQ-038(b)/(i) on every resolution, including
retries). Since no authority *registry* exists to re-query (§19), there
is nothing additional a consumption-time re-check could discover that
creation-time validation didn't already establish; this is documented
explicitly as a **design choice bounded by the STRATEGIC_GAP ceiling**,
not an oversight — a future stronger identity-provider integration
(RAE-REQ-010) would be the natural place to add genuine consumption-time
re-authorization.

## 21. Decision Finalization

CHGR Publication is already atomic and immutable (RAE-REQ-054: provenance
and integrity inherited entirely from CHGR-001 §10). This plan adds no
separate "finalization" stage for the Decision layer — publication
finality is CHGR's, reused unchanged.

## 22. Binding Creation Ordering

Decision must resolve (exist, be published, correctly templated) before
`create_rollback_approval_binding` succeeds (§16, item 23). No
"orphan"/forward-reference Binding — construction raises
`RollbackApprovalBindingConstructionError` if the referenced Decision
cannot be resolved at creation time.

## 23. Binding Validates Decision

`create_rollback_approval_binding` performs the same
existence/publication/template/digest checks the Evidence Validator will
later perform at consumption time (§15/§16), sharing one internal helper
(`_resolve_decision_ref(ref) -> ResolvedDecision`) so creation-time and
consumption-time checks cannot drift apart (item 24 directly satisfied by
sharing this one function, not duplicating the logic in two places).

## 24. Multiple Bindings

**Decision: RAE-REQ-019 is followed exactly, not improvised.** At most
one Binding whose `state` is `issued` or `used` may reference a given
Decision at a time; a DENY-decision Binding is permitted per RAE-REQ-019
for audit purposes and carries `decision=DENY`. The creation function
enforces the "at most one active Binding per Decision" rule by resolving
existing Bindings that reference the same `governance_record_reference`
and rejecting creation of a second `issued`/`used` one (planned check,
not yet implemented).

## 25. Evidence Lookup API

```python
def resolve_rollback_approval_evidence(
    operation_context: Ag3RollbackApprovalContext | Ag5RollbackApprovalContext,
    evidence_id: str,
) -> ValidatedEvidence:
```

Always requires an explicit `evidence_id` (RAE-REQ-041) — never a
directory scan, never `sorted(...)[-1]`, never mtime/`max(timestamp)`
(item 75's explicit prohibition, verified by a planned static/grep test,
§26 item 8).

## 26. Operation Context Types

```python
@dataclass(frozen=True)
class Ag3RollbackApprovalContext:
    job_id: str
    original_commit_sha: str
    task_id: str | None
    repository_state: RepositoryStateBinding

@dataclass(frozen=True)
class Ag5RollbackApprovalContext:
    per_id: str
    ecp_id: str
    task_id: str | None
    repository_state: RepositoryStateBinding
```

Exactly the RAE-bound identifiers per RAE-REQ-020/021, no extra fields.

## 27. Validation Result Type

```python
class RollbackApprovalValidationResult(str, Enum):
    VALID = "VALID"
    MISSING = "MISSING"
    INVALID = "INVALID"
    STALE = "STALE"
    REVOKED = "REVOKED"
    UNAUTHORIZED_APPROVER = "UNAUTHORIZED_APPROVER"
    WRONG_SCOPE = "WRONG_SCOPE"
    SUPERSEDED = "SUPERSEDED"

@dataclass(frozen=True)
class ValidatedEvidence:
    result: RollbackApprovalValidationResult
    approval_present: bool
    binding: RollbackApprovalBinding | None
    diagnostic: str | None
```

Exactly RAE-REQ-036's eight-value vocabulary (this plan drops the phase
prompt's illustrative `NONCANONICAL`/`WRONG_FAMILY`/`WRONG_BINDING`
labels in favor of RAE-001's own frozen §36 vocabulary, since the
contract text is normative over the phase prompt's own illustrative
list — `WRONG_SCOPE` already covers wrong-target/wrong-family per
RAE-REQ-024, and a noncanonical record resolves `MISSING` or `INVALID`
depending on which check fails, rather than a ninth dedicated value not
present in the frozen contract). This is flagged explicitly as a
plan-level interpretation choice, not a contract amendment: RAE-REQ-036
is prose-frozen at exactly eight values, and this plan does not add a
ninth. Kept structurally distinct from `permission_broker_foundation`'s
own `DECISION_ALLOW`/`DECISION_DENY`/`DECISION_HUMAN_REVIEW` vocabulary
(RAE-REQ-036 restated, item 28).

## 28. `approval_present` Derivation API

```python
def derive_rollback_approval_present(
    operation_context: Ag3RollbackApprovalContext | Ag5RollbackApprovalContext,
    evidence_id: str,
) -> bool:
    return resolve_rollback_approval_evidence(operation_context, evidence_id).approval_present
```

A thin, narrow wrapper — `True` only for `RollbackApprovalValidationResult.VALID`
with `decision == APPROVE`, `False` for every other outcome including
validator-internal error (§29). No caller override parameter exists on
this function's signature (item 29's "no caller override," enforced by
having no such parameter at all, not by ignoring one).

## 29. Validation Failure Behavior — Fail-Closed

**Decision: `False` + structured diagnostic, not a raised exception, at
the `derive_rollback_approval_present` boundary** — matching this
codebase's existing `MutationPermissionResult`/`broker_failure_reason`
convention (`mutation_permission.py`, §5 research finding) rather than
requiring every future AG3/AG5 caller to wrap the call in `try/except`.
Internally, `resolve_rollback_approval_evidence` catches: storage read
errors, JSON parse errors, digest-mismatch, authority-lookup absence, and
any clock-read failure, converting every one of them to
`RollbackApprovalValidationResult.INVALID` (or `MISSING` where the
record simply doesn't exist) with `approval_present=False` and a
diagnostic string — never letting an internal exception propagate past
the module boundary uncaught (RAE-REQ-042).

## 30. TTL — 24 Hours

`expires_at` is computed once, at creation, as `created_at + timedelta(hours=24)`
(RAE-REQ-043's frozen duration, not caller-configurable — `ttl_hours:
Literal[24] = 24` in §16's signature is a type-level lock, not a runtime
default a caller can override with a different literal). Timestamp field:
`expires_at` (ISO-8601, UTC, `Z`-suffixed via the reused `chgr_timestamp`
normalizer, §11). Comparison: `now_utc() >= expires_at` (inclusive
boundary — "at or after 24h is expired," chosen because RAE-001's own
freshness language ("has not passed") is naturally inclusive-at-boundary
and this plan does not invent a permissive one-instant grace window not
in the contract text). This exact boundary choice is flagged as an
OBSERVATION (§17) since RAE-001 itself does not spell out
inclusive/exclusive at the instant of expiry — 149J's own §24 finding
already noted this as an open question this implementation phase must
resolve, which this plan now does, explicitly and conservatively
(fail-closed direction: treat the boundary instant itself as already
expired, never as still-valid).

## 31. Clock / Time Injection

**Finding: no clock-abstraction exists anywhere in this codebase today**
(§3 research: every timestamp call is an uninjected `datetime.now(timezone.utc)`).
This plan adds one, scoped narrowly to this module only:

```python
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)
```

with a module-level, test-only override point (a private
`_CLOCK_OVERRIDE` context-manager/contextvar used exclusively by
`tests/test_rollback_approval_evidence_*.py`, never exposed as a public
API, never reachable from any CLI flag or production code path — item 32
explicit). Production code always calls the real system clock; there is
no production configuration value, environment variable, or CLI flag
that can shift the perceived "now" for a real Binding's freshness
evaluation.

## 32-33. Future-Dated / Malformed Timestamp

Both fail closed: a `created_at` or `expires_at` in the future relative
to `_now_utc()` at validation time, or a timestamp that fails ISO-8601
parsing, resolves `RollbackApprovalValidationResult.INVALID` with
`approval_present=False` (RAE-REQ-042's fail-closed umbrella; no
contract text authorizes a future-dated record as valid under any
condition).

## 34-35. Revocation Model

**Decision: a new, immutable revocation record, not an in-place `state`
mutation of the original Binding file, and not a superseding Decision.**
Consistent with CHGR-001 §13.3's immutability discipline (already
inherited, RAE-REQ-057), the plan does not rewrite
`bindings/<evidence_id>.json` in place when revoking. Instead:
`revocations/<evidence_id>.json` (§12) is written, containing
`{revoked_at, revoked_by, reason_code}` (RAE-REQ-046's exact field set).
The Evidence Validator, on resolution, checks for the *existence* of a
matching revocation record and, if present, returns
`RollbackApprovalValidationResult.REVOKED` regardless of what the
original Binding file's own (immutable, as-created) `state` field says —
i.e. `state` on the persisted Binding is written once at creation as
`issued` and never rewritten; the *effective* state (`issued` -> `used`/
`revoked`/`expired`) is always computed at resolution time from
(original Binding + revocation-record existence + `use_binding`-marker
existence + TTL comparison), never by physically mutating the original
file. This is a deliberate divergence from a literal reading of RAE-001
§8's `state` field as directly-mutable-in-place — recorded here
explicitly as a plan-level design choice, not a contract reinterpretation:
RAE-REQ-057 already requires target/operation fields be immutable and
RAE-REQ-046 requires the transition be "by an eligible Approval
Authority," both of which favor an append-only audit trail over in-place
field mutation, and RAE-001 itself never mandates *physical* in-place
mutation as the only legal implementation of the `state` field's
semantics — it defines `state`'s meaning, not its storage mechanics.

## 36. Supersession Model

Same append-only pattern: a later Binding referencing the same
`rollback_operation_reference` is simply a newer file; no earlier file is
edited. The Validator, resolving an *older* `evidence_id` whose
operation reference has a newer Binding, returns
`RollbackApprovalValidationResult.SUPERSEDED` (RAE-REQ-047) by
comparing `created_at` across all Bindings sharing the same operation
reference — this requires an operation-reference-indexed lookup, planned
as a lightweight in-memory scan of `bindings/*.json` filtered by
matching `rollback_operation_reference` (not by "latest file," but by
explicit operation-reference equality plus `created_at` ordering,
consistent with RAE-REQ-041's ban on a bare "latest" lookup — the scan
is used only to detect superseding records for an *already-identified*
`evidence_id`'s own operation reference, never to select which
`evidence_id` to resolve in the first place).

## 37-38. Deny Decision / Conflicting Decisions

A `DENY`-decision Binding, if resolved as an `evidence_id`, produces
`approval_present=False` via RAE-REQ-038(c) (`selected_option_id` must
be `approve_rollback`, not merely present) — this is a natural
consequence of the derivation conjunction, not a special-cased branch.
RAE-REQ-068 confirms this is sufficient; no separate "explicitly denied"
signal is added to the boolean API. Conflicting approve/deny Bindings for
the same operation reference resolve via the same supersession
`created_at`-ordering rule (§36) — the later-published one is
authoritative for evidence-resolution purposes, "no newest-file
heuristic" (item 38) is honored because ordering is by the *canonical,
digest-verified* `created_at` field inside each resolved record, not by
filesystem mtime.

## 39. Replay Prevention

The Validator rejects a Binding whose `rollback_operation_reference`
does not exactly, field-for-field match the live `operation_context`'s
own identity fields (`job_id`+`original_commit_sha` for AG3,
`per_id`+`ecp_id` for AG5) — `WRONG_SCOPE` on any mismatch, including a
single differing field (RAE-REQ-024).

## 40. Successful Consumption

RAE-001 requires marking evidence `used` only via `use_binding` on
successful mutation (RAE-REQ-050), not on every resolution attempt. This
plan does not invent additional mutable consumption state beyond that —
operation-identity binding (§39) already makes accidental replay against
a *different* operation impossible; the `used`/`replay_binding`
transition exists specifically to stop the *same* evidence being
presented for two *separate successful* attempts against the *same*
operation (a narrower, RAE-001-specified case, item 40 answered: do not
invent broader consumption tracking).

## 41. Failed Rollback Retry

Per RAE-REQ-052, the `issued -> used` transition point is planned to be
wired (in a *future* AG3/AG5 integration phase, not 149K) to fire only on
an RWMPC-confirmed successful mutation — never on Permission Broker
`ALLOW` alone. This plan's Validator therefore supports retry naturally:
as long as a Binding remains `issued` (no `use_binding` marker written),
identical operation identity and unchanged `repository_state_binding`
resolve `VALID` again on a retry after a purely mechanical failure,
requiring no special-cased retry logic in the Validator itself — retry
support is a *consequence* of correctly deferring the `used` transition,
not a separate code path.

## 42-43. Fresh Broker Decision / RWMPC Separation

No caching of any Permission Broker decision anywhere in this module —
it has no import of, or dependency on, `permission_broker_foundation` at
all (§6). No mutation-state freshness logic beyond RAE-001's own
`repository_state_binding` check (§8) is added; RWMPC's own live
freshness re-check at execution time remains entirely RWMPC's/AG3's/AG5's
existing responsibility, untouched and unduplicated by this plan
(RAE-REQ-033 restated).

## 44-45. Schema Requirement and Location

**Decision: yes, a formal JSON Schema is planned**, for two reasons: (1)
repository convention already schema-backs every comparable canonical
record family (CHGR, TAM); (2) a schema gives the Evidence Validator (and
any future external inspection tooling, mirroring `governance/inspection.py`'s
existing CHGR-inspection pattern) a mechanical conformance check
independent of the Python dataclass's own runtime checks. Planned
location:

```
src/pcae/schema_resources/rollback_approval/records/rollback_approval_binding.schema.json
src/pcae/schema_resources/rollback_approval/records/rollback_approval_revocation.schema.json
src/pcae/schema_resources/rollback_approval/manifest.json
```

— a new top-level `schema_resources` package sibling to `chgr/` and
`cltr_cutover/` (not nested inside either), requiring one new small
accessor function `rollback_approval_root()` in
`src/pcae/schema_resources/__init__.py`, following the exact existing
`chgr_root()`/`cltr_cutover_root()` pattern (§3 research finding, lines
43-85 of that file) — this is the one narrow, generic extension this
plan identifies as necessary in a shared file (§20's file budget marks it
`MAY_CHANGE`, future implementation phase). Explicitly **not** placed
inside the `cltr_cutover` schema family (RAE-REQ-003 prohibition, item
45).

## 46-47. CHGR Integration / Extension Hook

**Finding: CHGR-001 §6's existing Decision Template extension point is
sufficient; no new CHGR runtime hook is required.** `build_publication_record`
already accepts any `template_id`/`template_version` as an opaque,
caller-supplied pair with no closed-list validation against a registry
(§3 research finding, confirmed by direct reading of `record.py:147-301`)
— this *is* the generic extension mechanism RAE-001's §7 relies on, and
it already exists, unmodified, in production. Item 47's contingency
("if CHGR lacks a hook, identify minimal code needed, do not rewrite
CHGR architecture") is therefore **not triggered** — no CHGR code change
is planned or required.

## 48. Binding Trust Substrate

Established per §15's two-check mechanism (`content_digest`
recomputation + `governance_record_reference` resolution against real
CHGR storage) — this **is** the chosen mechanism (item 48 answered): the
Binding gains trust not from a separate cryptographic signature (none
exists anywhere in this repository, RAE-REQ-055) but from being
verifiably, digest-anchored to a real CHGR publication that could only
have been produced through the unmodified Confirmation→Publication
ritual. This reuses CHGR's provenance machinery *by reference* (the
digest match), not by physically nesting Binding storage inside CHGR's
own directory tree.

## 49-51. TAM Wall Enforcement

Confirmed by design, not merely by intent: (a) no planned file lives
under `src/pcae/schema_resources/cltr_cutover/**` (§12/§44); (b) no
planned field is named `record_family: "human_authorization"` or any
other TAM `record_family` value — the new schema's own `record_type`
value is planned as `"rollback_approval_binding"`, a distinct, dedicated
name; (c) every structural-reuse point in this plan (§9's discriminated
union pattern, §14's atomic-write technique, §8's conditional-field
pattern) is **independently re-authored** against `human_authorization`'s
*shape as documentation*, never via a Python `import` of any
`cltr.authority.*` or `cltr_cutover` module — verified by the "no `cltr`
import" grep test planned in §26 item 9.

## 52-53. IWC / AESIC Relationship

IWC transports the interactive Confirmation session for the
`rollback-approval` template exactly as it already does for every other
template (RAE-REQ-058) — no plan-level code treats
`ConfirmationRequest`/`ConfirmationResponse` as evidence; only the
resulting published `human_governance_record` is ever referenced
(§7/§16). AESIC output is never a function parameter, field, or input to
any function in `rollback_approval_evidence.py`'s planned API surface —
it may only ever appear, in a *future* UX phase, as advisory prose
rendered into the Decision Template's `consequence_text` at presentation
time (RAE-REQ-059/061), which is entirely outside this module's scope.

## 54. Legacy Flags

`--promotion-authorized`, `--reviewed-by`, `approve_rollback(root,
job_id)` (`agent.py:5146`), `change_approval_state`, `--approve-keep`,
`--approved-by`, `--reason` remain explicitly non-evidence (RAE-REQ-060).
This plan does not deprecate or remove `approve_rollback(root, job_id)`
— it is out of scope for an evidence-substrate-only phase and continues
to set only the pre-existing, already-untrusted
`job["rollback_approval_state"]` flag, which this plan's Validator never
reads. A future phase MAY repurpose `--approved-by`'s CLI slot to carry
an `evidence_id` string (RAE-REQ-060's own allowance) — not planned by
149K's own file budget (§20), since no CLI is implemented by this phase
(RAE-REQ-080).

## 55. Production File Budget

| File | Status | Planned change |
|---|---|---|
| `src/pcae/core/rollback_approval_evidence.py` | MUST_CHANGE (new) | New module: models, storage, creation, validator, derivation API (§5) |
| `src/pcae/schema_resources/rollback_approval/records/rollback_approval_binding.schema.json` | MUST_CHANGE (new) | New schema (§44) |
| `src/pcae/schema_resources/rollback_approval/records/rollback_approval_revocation.schema.json` | MUST_CHANGE (new) | New schema (§34) |
| `src/pcae/schema_resources/rollback_approval/manifest.json` | MUST_CHANGE (new) | Manifest for the two schemas above, mirroring `chgr/manifest.json` shape |
| `src/pcae/schema_resources/__init__.py` | MAY_CHANGE | Add `rollback_approval_root()` accessor (§44), following `chgr_root()`/`cltr_cutover_root()` pattern — additive only, no existing accessor modified |
| CHGR implementation (`governance/publication/*`) | MUST_NOT_CHANGE | Consumed read-only via existing extension point (§46); zero modification |
| `src/pcae/core/agent.py` | MUST_NOT_CHANGE in evidence phase | AG3/AG5 wiring is future work (§21) |
| `src/pcae/core/mutation_permission.py` | MUST_NOT_CHANGE in evidence phase | Future rollback adapter addition is a separate, later phase |
| `src/pcae/core/permission_broker_foundation.py` | MUST_NOT_CHANGE | Never touched by this contract (§6, RAE-REQ-072) |
| CLI / governance command surface | MAY_CHANGE / future | `pcae rollback approval create` convenience wrapper is future work (§17), not this phase's or the next implementation phase's required scope |

This document itself (`docs/PHASE_149K_ROLLBACK_APPROVAL_EVIDENCE_IMPLEMENTATION_PLAN.md`)
is the only file this **planning** phase (149K) actually writes, plus the
governed task-lifecycle/phase-report artifacts (§23). Every row above
describes **149L's** (the next, implementation, phase's) planned diff,
not 149K's own.

## 56. Phase Sequencing

Confirmed, per the phase prompt's own strong preference and RAE-001 §33's
own recommendation chain:

```
149I  Rollback Approval Evidence Contract Freeze            (done)
149J  Rollback Approval Evidence Contract Independent Verification (done)
149K  Rollback Approval Evidence Implementation Plan         (this phase)
149L  Rollback Approval Evidence Implementation              (next)
149M  Rollback Approval Evidence Implementation Independent Verification
  →   AG3/AG5 rollback-integration planning (separately governed, later)
```

No combination of 149L's evidence-substrate implementation with AG3/AG5
wiring is recommended — the evidence substrate is fully testable in
isolation (§57 below), so the strong-preference default (separate
phases) applies with no contrary repository evidence found.

## 57-58. Independent Testability / Real Persistence Tests

All planned tests (§26) exercise `rollback_approval_evidence.py`'s
public API directly, with **zero** import of, or dependency on,
`agent.py`, `permission_broker_foundation.py`, or any AG3/AG5 code path.
Tests use a temporary `.pcae/`-shaped root (a `tmp_path`-based fixture
mirroring the existing pattern already used for CHGR/TAM storage tests —
never the actual project's own `.pcae/` directory); the module's storage
functions accept an explicit root path parameter for exactly this
reason (no hardcoded `Path(".pcae")` inside any function signature that
tests must call — the root is always a parameter, defaulting to the real
repository root only at the CLI-integration layer, which is future work,
§17).

## 59-77. Test Plan (items 57-79 consolidated)

Planned test files (§62 below has the exact file list) will include, at
minimum, one test per phase-prompt item:

| # | Test | Expected result |
|---|---|---|
| 57 | create approve Decision (via CHGR pipeline) + resolve | evidence resolves independent of AG3/AG5 |
| 57 | create canonical Binding | round-trips through storage unchanged |
| 57 | resolve valid evidence | `VALID`, `approval_present=True` |
| 57 | missing Decision | `MISSING`, `False` |
| 57 | missing Binding (`evidence_id` not found) | `MISSING`, `False` |
| 57 | wrong family (AG3 ref validated against AG5 context) | `WRONG_SCOPE`, `False` |
| 57 | wrong operation (differing `job_id`) | `WRONG_SCOPE`, `False` |
| 57 | expired (`expires_at` passed) | `STALE`, `False` |
| 57 | revoked | `REVOKED`, `False` |
| 57 | superseded | `SUPERSEDED`, `False` |
| 57 | deny Decision referenced | `INVALID` (fails RAE-REQ-038(c)), `False` |
| 59 | agent-forgery: hand-authored file placed directly in `bindings/` outside `create_rollback_approval_binding` | validator rejects (§15 mechanism) |
| 60 | claimed actor (`decision_maker_identity_evidence="admin"`, no real CHGR publication behind it) | rejected — no real record to resolve |
| 61 | authority failure: valid shape + canonical persistence but `eligible_authority` template text absent/malformed | `UNAUTHORIZED_APPROVER` |
| 62 | closed vocabulary: unknown template option string | construction-time `ValueError` (Python `Enum`, §10) |
| 63 | cross-family: AG3 evidence against AG5 context and vice versa | `WRONG_SCOPE` both directions |
| 64 | AG3 drift: change `job_id` only, then `original_commit_sha` only | both invalidate independently |
| 65 | AG5 drift: change `per_id` only, then `ecp_id` only | both invalidate independently |
| 66 | TTL boundary: just-before-24h, exactly-24h, just-after-24h | valid, expired (inclusive boundary, §30), expired |
| 67 | future-dated record | rejected fail-closed |
| 68 | revocation | previously-valid evidence becomes `REVOKED` |
| 69 | supersession | old record `SUPERSEDED`, new one `VALID` |
| 70 | deny supersedes prior approve | old approve no longer resolves `VALID` for that operation reference |
| 71 | retry: same operation, Binding still `issued` | `VALID` again; changed operation invalidates |
| 72 | atomic write: simulated interruption (kill before `os.replace`) | no partial file ever visible at final path |
| 73 | tampering: modify a persisted Binding's bytes post-creation | `content_digest` mismatch, `INVALID` |
| 74 | lookup ambiguity: multiple Bindings exist for one operation reference | resolver uses supersession `created_at` ordering, never mtime |
| 75 | no-"latest"-API: static/grep test over module source | asserts no `sorted(...)[-1]`/`mtime`/`max(timestamp)` pattern used for `evidence_id` selection |
| 76 | authority revalidation (documented as creation-time-only, §20) | test documents/asserts this explicitly rather than silently assuming it |
| 77 | validator failure: forced storage/parse exception (monkeypatched read) | never returns `approval_present=True`; always fail-closed |
| 78 | import-graph test | asserts `rollback_approval_evidence` module has zero import of `permission_broker_foundation` |
| 79 | import-graph test | asserts zero import of `pcae.core.agent` |

## 62. Test File Budget

```
tests/test_rollback_approval_evidence_models.py       # §7-10: dataclasses, enums, family locking
tests/test_rollback_approval_evidence_persistence.py  # §12-14, 72-74: storage, atomicity, lookup
tests/test_rollback_approval_evidence_validation.py   # §15, 27-30, 59-71, 77: validator/derivation
tests/test_rollback_approval_evidence_contract.py     # §1 traceability re-check + §78-79 import-graph tests
```

Matches the phase prompt's suggested category names and this repository's
existing `test_<feature>_<aspect>.py` convention (§3 research finding).

## 63-79. Regression Plan

A future implementation phase (149L) is planned to run, at minimum:

- `python -m pytest -k 'chgr' -n auto` (§94, CHGR trust-substrate regression — evidence module reuses `chgr_timestamp` only, §11).
- `python -m pytest -k 'tam or authorization or cltr_cutover' -n auto` (§95, confirms zero accidental TAM composition).
- `python -m pytest -k 'iwc or interactive_workflow' -n auto` (§96, confirms confirmation semantics unchanged).
- `python -m pytest -k 'aesic or authority_evaluation' -n auto` (§97, confirms disclosure-only boundary unchanged).
- `python -m pytest -k 'permission_broker or pol_004 or pol_001 or pol_005' -n auto` (§98, focused Foundation regression — the evidence module makes zero broker calls, but POL-004's own behavior for `EXECUTION_CLASS_ROLLBACK` must remain provably unchanged).
- `pcae runtime inspect` before/after (§99): must remain Observed / observe / unavailable.
- `python -m pytest -m fast_green -n auto -q` (§100): current baseline **4391 passed** (per this phase's governing prompt); 149L must report its own actual post-implementation count, not assume it stays 4391 (new tests will add to it).
- No AG3/AG5 execution test of any kind (§101) — none exists to run since AG3/AG5 remain unimplemented, and none is planned by 149L.

## 80-81. Dependency Direction

```
CHGR / canonical governance substrate (unmodified)
        |  (read-only: template extension point §46, record resolution §15)
        v
rollback_approval_evidence.py  (this plan's module — imports: chgr_timestamp only)
        |  (future: derive_rollback_approval_present() call)
        v
mutation_permission.py-style future rollback adapter  (future phase, RWMPC-REQ-013's
        |   sole-legal-construction-site rule)
        v
PermissionBrokerRequest -> permission_broker_foundation.py  (unmodified)
```

No cycle: `rollback_approval_evidence.py` never imports
`permission_broker_foundation`, `mutation_permission`, or `agent.py`
(§78-79's planned import-graph tests enforce this mechanically, not just
by convention).

## 82. `approval_present` Future Integration Seam (explicit)

```python
# future AG3/AG5 wiring, NOT part of 149K or (per §56) 149L:
approval = derive_rollback_approval_present(operation_context, evidence_id)
# approval: bool
request = build_rollback_permission_request(  # future mutation_permission.py adapter
    ...,
    approval_present=approval,
    execution_class=EXECUTION_CLASS_ROLLBACK,
    simulation_only=True,
)
decision = permission_broker_foundation.evaluate(request)
```

This is the single, explicit seam a future rollback-integration phase
will fill in. Nothing about this plan or 149L pre-builds any part of the
right-hand side of this snippet.

## 83. No Mutation in Evidence Creation

`create_rollback_approval_decision`/`create_rollback_approval_binding`
write only to `.pcae/publication-execution/` (CHGR's existing, unmodified
write path) and the new `.pcae/rollback-approval-evidence/` — both are
governance-state directories already outside source control's
application-code tree (mirroring `.pcae/publication-execution/`'s own
existing `.gitignore`-equivalent treatment, confirmed to be governance
state, not repository rollback mutation, matching this document's own
§0 boundary). No test or planned function stages or commits `src/pcae/**`
changes as a side effect of evidence creation.

## 84. Auditability

Decision records are inspectable via CHGR's existing inspection tooling
(`governance/inspection.py`'s pattern, unchanged). Binding/revocation
records are planned to be inspectable via a thin, future,
read-only `pcae rollback-approval show <evidence_id>` command (not part
of 149K's or 149L's required scope — an OBSERVATION for a later CLI
phase) — no new event log is planned; the append-only
`bindings/`/`revocations/` directories are themselves the audit trail
(§34-36).

## 85. Human Review UX (future)

Minimum data a future approval-creation UX must present, per RAE-REQ-061:
rollback family (AG3/AG5), operation identifier (site-specific), affected
scope (files for AG5, reverted commit for AG3), current task/phase
context if any, current repository context
(`repository_state_binding`). No UI is implemented by 149K or planned as
149L's scope.

## 86-89. Creation Preconditions, Denial, Revocation/Supersession Creation Paths

Mechanical preconditions before Binding creation (§16): the referenced
Decision must resolve (§23); no pre-approval for a nonexistent arbitrary
operation ID is permitted (this plan does not add an
"approve-in-advance-of-existence" mode — RAE-001's own wording never
authorizes one). `deny_rollback` creation is symmetrical to
`approve_rollback` — same Decision Template, same publication pipeline,
different `selected_option_id`, and Binding creation accepts a DENY
reference for audit purposes exactly as RAE-REQ-019 allows (§8's
`decision` field). Revocation/supersession creation paths are the
append-only writers described in §34-36 — never an in-place JSON edit.

## 90-91. Migration Strategy

**No migration is planned or authorized.** `approve_rollback(root,
job_id)`'s existing `job["rollback_approval_state"]="approved"` flag
value is explicitly never imported into the new evidence substrate as a
Binding record (RAE-REQ-060 restated); this plan finds **no historical
approval-shaped state anywhere in this repository that requires
migration**, because the pre-existing flag was never trusted evidence
under RAE-001 or any prior contract — there is nothing legitimate to
carry forward.

## 92-93. Regression / RAE Verification Re-Run

149L (or a following independent-verification phase, 149M) must re-run
149J's own independent-verification test file
(`tests/test_phase_149j_rollback_approval_evidence_contract_independent_verification.py`,
49 tests) unmodified, since RAE-001's contract text itself is unchanged
by implementation — a green re-run confirms the implementation didn't
require (and didn't get) any silent contract reinterpretation.

## 94-100. Regression Plan

Covered in §63-79 above; consolidated list not repeated here to avoid
duplication (item 92-100 map onto the same regression commands already
enumerated).

## 101. No AG3/AG5 Mutation Tests in the Implementation Phase

149L's own test budget (§62) contains zero tests that invoke
`execute_rollback`, `build_rollback_execution`, or any git-mutating or
file-mutating operation — confirmed structurally by the import-graph
tests (§78-79) which assert `rollback_approval_evidence.py` never even
imports `agent.py`, so no test exercising it can transitively reach a
mutation path.

## 102. Implementation Stop Conditions (for 149L)

149L SHALL stop and escalate to a narrower repair/architecture phase,
rather than improvising, if any of the following is discovered during
implementation:

- CHGR runtime cannot in fact legally create a Decision Template instance
  the way §46 assumes (this plan's own confidence here is high, based on
  direct code reading, §3/§46 — but 149L must reconfirm against the real
  `build_publication_record` call path with an actual constructed
  `PublicationReadinessPackage`, not just static reading).
- The digest-resolution mechanism (§15/§48) cannot actually locate a
  published CHGR record by `record_id` through any existing, unmodified
  read path (i.e. if `governance/inspection.py`'s lookup pattern turns
  out not to generalize to an arbitrary `record_id` the way this plan
  assumes).
- The chosen TTL boundary semantics (§30) turn out to be incompatible
  with some existing timestamp-comparison convention elsewhere in the
  repository that 149L discovers and this plan did not find.
- Revocation/supersession cannot be represented without breaking
  RAE-REQ-057's immutability discipline in a way this plan's append-only
  design (§34-36) did not anticipate.
- The Evidence Validator cannot, in practice, distinguish canonical from
  forged records beyond what §15 already discloses as its residual
  STRATEGIC_GAP-bounded risk — i.e. if a *stronger* gap is found (not
  just the already-disclosed one), 149L must stop and report it as a
  new, not-previously-disclosed BLOCKING finding, not silently absorb it.
- RAE-001 is found, during implementation, to actually require identity
  guarantees stronger than the repository ceiling (§1) can supply — 149L
  SHALL NOT weaken RAE-001 to make implementation easier; it SHALL stop
  and recommend a contract-amendment or identity-substrate-prerequisite
  phase instead.

None of the above stop conditions is currently triggered by this
planning phase's own research (§2-§4) — they are documented as 149L's
own escalation criteria, not as findings raised by 149K itself.

## 103. Production Boundary Verification

```
git diff --name-only 318f4b50..HEAD -- src/pcae/
```
(`318f4b50` = 149I's contract-freeze commit, the most recent point before
149J/149K's own commits — used as the pre-149K baseline since 149J made
zero `src/pcae/` changes per its own report, §2/§3.) Expected and
confirmed: **empty** (verified in §16 below, re-run after this document
is written).

## 104. Contract Boundary Verification

```
git diff --name-only 318f4b50..HEAD -- docs/contracts/
```
Expected and confirmed: **empty** — 149K adds a new file under
`docs/PHASE_149K_*.md`, not under `docs/contracts/**`; no contract text
is amended (verified in §16 below).

## 105. Runtime Boundary

`pcae runtime inspect` before this phase's work (§2) and after (§16):
both **Observed / observe / unavailable**, Permission Broker status
`execution_unavailable`, registry empty. Unchanged.

## 106. Validation Commands Run

See §2 (initial) and §16 (final) — `pcae health`, `pcae check`, `pcae
status coherence`, `pcae doctor task-memory`, `pcae push check`, `pcae
runtime inspect`, `pcae notify status` all run at phase start; re-run
after this document is written, before governance finalization.

## 107-108. Findings

Classified per the governing phase prompt's four-way scheme:

- **NON-BLOCKING** — 149J's `phase-report reconcile --phase-id 149J`
  reports `delivery_recorded_bookkeeping_incomplete` / `receipt: absent`.
  Pre-existing, not introduced by 149K, not a defect in RAE-001 or this
  plan; noted for potential future governance-tooling cleanup, out of
  this phase's scope (§2).
- **OBSERVATION** — RAE-REQ-036's frozen 8-value validation vocabulary is
  used verbatim rather than the phase prompt's own illustrative
  9-10-value list (§27); flagged so a reviewer can confirm this
  plan-level interpretation is acceptable before 149L implements it.
- **OBSERVATION** — `use_binding`'s exact referenced "outcome record"
  family is not frozen by RAE-001 text; this plan leaves it as an opaque
  string reference pending 149L's own design of AG3/AG5's execution
  outcome representation (§8), since that representation doesn't exist
  yet.
- **OBSERVATION** — TTL boundary inclusivity (§30) and revocation's
  append-only-vs-in-place storage mechanics (§34-36) are plan-level
  design choices RAE-001's prose permits but does not single out as the
  only legal implementation; both are conservative (fail-closed /
  immutability-preserving) choices, documented explicitly rather than
  silently assumed.
- **DEFERRED** — Authority-registry-backed `UNAUTHORIZED_APPROVER`
  enforcement beyond template-text presence (§19) is deferred to a future
  identity-substrate phase; not a gap this plan can close today given the
  STRATEGIC_GAP ceiling (§1).
- **DEFERRED** — CLI convenience wrapper (`pcae rollback approval
  create`/`pcae rollback-approval show`) is deferred past 149L (§17, §84).

No planning blocker from item 108's list is triggered: canonical
persistence owner is chosen (§12-14); CHGR extension hook already exists,
confirmed live (§46-47); authority resolution is honestly bounded, not
absent (§19); Binding trust is established via digest+resolution (§15,
§48); canonical/noncanonical distinction is implementable (§15); TTL
boundary is resolved (§30); revocation model is chosen (§34); no module
dependency cycle exists by design (§80-81, mechanically enforced by
planned tests).

## 109. Plan Verdict

```
IMPLEMENTATION PLAN COMPLETE — RAE EVIDENCE SUBSTRATE READY
```

## 110. Recommended Next Phase

```
149L — Rollback Approval Evidence Implementation
```

Scope: Decision/Binding models (§7-10), canonical creation/persistence
(§12-17), validation (§15, §19, §27-29), TTL (§30-33), revocation/
supersession (§34-36), `approval_present` derivation (§25-28, §82's
seam stops at the derivation call — nothing past it), tests (§59-62).
Explicitly excludes: AG3/AG5 Permission Broker wiring, rollback mutation
execution changes (both remain a later, separately governed phase per
§56).

## 111-112. Governance Finalization and Required Final Report

Prepared in `.pcae/phase-completion-report.md` /
`.pcae/phase-completion-metadata.json`, bound to Phase 149K, canonical
title "Rollback Approval Evidence Implementation Plan," via the governed
PCAE lifecycle only (`pcae phase complete` / task-transition tooling) —
no raw `git commit`/`git push`, no `--no-verify`, no force push. See
finalization record for the full required-field report (§112's list);
this document (§0-§110 above) is the substantive content that report
summarizes.

## Appendix A: 81-Requirement Traceability Matrix

Independently extracted, by script (`grep -o 'RAE-REQ-[0-9]*'`), all 81
sequential `RAE-REQ-*` anchors from the current frozen contract text —
0 gaps, 0 duplicates, matching 149J's own independent count. Every row
below is either `CODE` (production implementation planned for 149L) or
`DOC` (no-code / documentation-only — e.g. a definitional or
compatibility-confirmation requirement that constrains design but emits
no artifact of its own).

| Req | Component (this plan's §) | Status | Test obligation |
|---|---|---|---|
| RAE-REQ-001 | Module boundary (§4) — consumes CHGR only via extension point | DOC | §78-79 import-graph tests |
| RAE-REQ-002 | Decision model (§7) — no CHGR guarantee overclaimed | DOC | §92 re-run of 149J suite |
| RAE-REQ-003 | Structural-reuse discipline (§4, §9, §14) — inspiration only, never imported | CODE (independently-authored types) | §49-51 TAM-wall tests |
| RAE-REQ-004 | Same as RAE-REQ-003 | DOC | §49-51 |
| RAE-REQ-005 | Identity ceiling (§1, §18) | DOC | none (disclosure) |
| RAE-REQ-006 | Actor identity capture (§18) | CODE (`decision_maker_identity_evidence` passthrough) | test_rollback_approval_evidence_models.py |
| RAE-REQ-007 | Legacy-flag exclusion (§54) | CODE (Validator never reads CLI flags) | §54 (implicit — no flag path exists to test) |
| RAE-REQ-008 | Approval Authority / Approval Event (§19) | CODE (`UNAUTHORIZED_APPROVER` outcome) | test 61 |
| RAE-REQ-009 | STRATEGIC_GAP #2 (§1) | DOC | none (disclosure) |
| RAE-REQ-010 | Field extensibility (§7, §19) | DOC — future-proofing constraint on field shape | none this phase |
| RAE-REQ-011 | Decision Template constant (§7) | CODE (`ROLLBACK_APPROVAL_TEMPLATE`) | test_rollback_approval_evidence_models.py |
| RAE-REQ-012 | Template frozen field values (§7) | CODE | same |
| RAE-REQ-013 | Closed decision vocabulary (§10) | CODE (`RollbackDecisionType` enum) | test 62 |
| RAE-REQ-014 | No-flag-substitution rule (§54) | DOC/CODE (structural — no such code path exists) | test 60 |
| RAE-REQ-015 | Vocabulary separation from broker (§10, §27) | CODE (`RollbackApprovalValidationResult` distinct from broker enum) | test_rollback_approval_evidence_validation.py |
| RAE-REQ-016 | Binding dataclass + schema namespace (§8, §44) | CODE | test_rollback_approval_evidence_models.py |
| RAE-REQ-017 | Binding field table (§8) | CODE | test_rollback_approval_evidence_models.py (field presence/conditional-requirement tests) |
| RAE-REQ-018 | `governance_record_reference` resolution (§15, §23) | CODE (`_resolve_decision_ref`) | test 57 (missing/mismatched digest), test 59 |
| RAE-REQ-019 | At-most-one-active-Binding rule (§24) | CODE (creation-time uniqueness check) | test_rollback_approval_evidence_persistence.py |
| RAE-REQ-020 | AG3 operation identity (§9, §26) | CODE (`Ag3OperationReference`) | test 64 |
| RAE-REQ-021 | AG5 operation identity (§9, §26) | CODE (`Ag5OperationReference`) | test 65 |
| RAE-REQ-022 | Family-locked discriminated union (§9) | CODE | test 63 |
| RAE-REQ-023 | Single contract, two profiles (§5, §9) | DOC — architecture decision | none |
| RAE-REQ-024 | Wrong-target prevention (§39) | CODE (exact-match check in Validator) | test 57 (wrong operation), test 63-65 |
| RAE-REQ-025 | Wrong-payload prevention (§9) | CODE — same exact-match mechanism covers changed payload | test 64-65 |
| RAE-REQ-026 | AG3 Binding profile fields (§9) | CODE | test_rollback_approval_evidence_models.py |
| RAE-REQ-027 | AG5 Binding profile fields (§9) | CODE | test_rollback_approval_evidence_models.py |
| RAE-REQ-028 | No artificial field parity (§9) | DOC | none |
| RAE-REQ-029 | AG5 explicit-invocation-only scope | DOC | none (out of this module's scope — agent.py concern) |
| RAE-REQ-030 | `task_id` binding rule (§8) | CODE (creation-time capture from active task) | test_rollback_approval_evidence_models.py |
| RAE-REQ-031 | No duplicate phase-identity field | DOC | none |
| RAE-REQ-032 | No separate branch field | DOC | none |
| RAE-REQ-033 | Two-layer state binding (§43) | CODE (`repository_state_binding` staleness check, distinct from RWMPC) | test_rollback_approval_evidence_validation.py |
| RAE-REQ-034 | Evidence Validator interface (§25, §5 item 9) | CODE (`resolve_rollback_approval_evidence`) | test_rollback_approval_evidence_validation.py |
| RAE-REQ-035 | Validation inputs bounded (§25) | CODE — function signature enforces this (no AESIC param) | §53 test |
| RAE-REQ-036 | Validation result vocabulary (§27) | CODE (`RollbackApprovalValidationResult`) | full validation suite |
| RAE-REQ-037 | Evidence Consumer performs no trust evaluation | DOC — constrains future 149L+ caller code, not this module | §78-79 (no broker import) |
| RAE-REQ-038 | Central derivation rule (§28-29) | CODE (`derive_rollback_approval_present`, 9-condition conjunction) | full validation suite (tests 57-77) |
| RAE-REQ-039 | No caller-set `approval_present` | CODE — no such parameter exists (§28) | signature inspection / test 62 |
| RAE-REQ-040 | Approval ≠ permission | DOC (restated §6) | none — Permission Broker's own concern |
| RAE-REQ-041 | No "latest" resolution | CODE (`evidence_id`-only lookup) | test 74, 75 (grep test) |
| RAE-REQ-042 | Fail-closed on validator error | CODE (§29) | test 77 |
| RAE-REQ-043 | 24-hour TTL | CODE (§30) | test 66 |
| RAE-REQ-044 | Additional staleness triggers | CODE (§33, §36 — repo-state mismatch, supersession) | test_rollback_approval_evidence_validation.py |
| RAE-REQ-045 | Timestamps are audit metadata only | DOC — no extra TTL invented (§30) | none |
| RAE-REQ-046 | Revocation transition + metadata | CODE (§34) | test 68 |
| RAE-REQ-047 | Supersession rule | CODE (§36) | test 69 |
| RAE-REQ-048 | Independent of CHGR `revoked` state | DOC | none |
| RAE-REQ-049 | Decision-layer replay guard (CHGR's own) | DOC — inherited unchanged | none new |
| RAE-REQ-050 | `issued -> used` + `replay_binding` | CODE (§8, §40-41) | test_rollback_approval_evidence_models.py |
| RAE-REQ-051 | Single-use is not blanket-invented | DOC | none |
| RAE-REQ-052 | Failed-execution retry | CODE (§41 — deferred `used` transition) | test 71 |
| RAE-REQ-053 | Fresh broker evaluation on retry | DOC — future AG3/AG5 caller's own responsibility (§82) | none this module |
| RAE-REQ-054 | Decision provenance inherited from CHGR | DOC | none |
| RAE-REQ-055 | Binding content-integrity digest | CODE (`content_digest`, §11, §15) | test 73 |
| RAE-REQ-056 | Canonical, non-arbitrary storage | CODE (§12) | test_rollback_approval_evidence_persistence.py |
| RAE-REQ-057 | Immutability, no in-place edit | CODE (`frozen=True` + storage no-overwrite guard, §8, §14) | test_rollback_approval_evidence_persistence.py |
| RAE-REQ-058 | IWC transport-only | DOC (§52) | none |
| RAE-REQ-059 | AESIC exclusion | CODE — no AESIC parameter anywhere in API (§53) | signature inspection |
| RAE-REQ-060 | Legacy flag exclusion | DOC (§54) | none |
| RAE-REQ-061 | Human review presentation minimum data | DOC — future UX (§85) | none this phase |
| RAE-REQ-062 | Missing evidence -> `HUMAN_REVIEW` via POL-004 | DOC — Permission Broker's own existing behavior, unchanged | none this module |
| RAE-REQ-063 | Invalid evidence never `True` (strict conjunction) | CODE (§28, §38) | full validation suite |
| RAE-REQ-064 | Evidence-consumption failure ≠ policy failure | DOC | none |
| RAE-REQ-065 | Flow diagram | DOC — architecture, matches §82's seam | none |
| RAE-REQ-066 | Broker remains non-interactive | DOC (§6) | §78-79 |
| RAE-REQ-067 | No automatic evidence creation on `HUMAN_REVIEW` | DOC — no such code path planned | none |
| RAE-REQ-068 | Rejection handling (`deny_rollback`) | CODE — natural consequence of §38 | test 57 (deny referenced) |
| RAE-REQ-069 | Satisfiability matrix (traced by 149J, reconfirmed) | DOC | none — already independently traced |
| RAE-REQ-070 | Live Foundation satisfiability | DOC | none — already independently traced |
| RAE-REQ-071 | RWMPC-001 no amendment | DOC | none |
| RAE-REQ-072 | PBPA-001 no amendment | DOC | none |
| RAE-REQ-073 | PBPC-001 no amendment | DOC | none |
| RAE-REQ-074 | CHGR-001 no amendment | DOC | none |
| RAE-REQ-075 | IWC-001 no amendment | DOC | none |
| RAE-REQ-076 | PEC-001 no amendment | DOC | none |
| RAE-REQ-077 | TAMC-001/TAMPC-001 no amendment | DOC | none |
| RAE-REQ-078 | AESIC-001/AEM-001 no amendment | DOC | none |
| RAE-REQ-079 | Approval-creation-boundary owner (§17) | DOC — future CLI wrapper design constraint | none this phase |
| RAE-REQ-080 | No CLI implemented by contract-only phase | DOC | none — restated, no CLI in 149K or 149L |
| RAE-REQ-081 | Versioning discipline | DOC | none |

No orphan requirement: all 81 rows present, sequential, matching 149J's
own independently-verified count (§28 of RAE-001, restated).

**No-Go confirmations** (explicit, matching the governing phase prompt's
required list): RAE-001 v1.0 remains unchanged. RWMPC-001 v1.0 remains
unchanged. PBPC-001 v1.2 remains unchanged. PBPA-001 v1.0 remains
unchanged. CHGR-001 remains unchanged. IWC remains confirmation-only.
TAM/TAMPC authority semantics remain unchanged. AESIC/AEM remain
disclosure-only. No production source (`src/pcae/**`) was modified by
Phase 149K. No approval evidence implementation was created. No rollback
Permission Broker consumer was implemented. AG3 and AG5 remain
unimplemented. No `approval_present=True` production value was
introduced. No self-declared CLI flag was promoted to trusted approval.
No illegal CHGR/TAM composition was introduced. No POL-001..012 meaning
was changed. No POL-013+ was added. No Runtime Enforcement behavior was
changed. TK1/TK2/TK3 remain deferred. No Prompt Generation, Prompt
Dispatch, or agent invocation capability was implemented. Runtime remains
Observed, maximum capability remains observe, and execution availability
remains unavailable.
