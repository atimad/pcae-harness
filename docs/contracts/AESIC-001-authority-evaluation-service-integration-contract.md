# AESIC-001 v1.0 — Authority Evaluation Service Integration Contract

## Contract identity and status

**Contract:** AESIC-001
**Version:** 1.0
**Status:** FROZEN
**Frozen by:** Phase 147K — Authority Evaluation Integration Contract
Freeze
**Architecture basis:** Phase 147J — Authority Evaluation Integration
Architecture
(`docs/PHASE_147J_AUTHORITY_EVALUATION_INTEGRATION_ARCHITECTURE.md`),
itself built on Phase 147J.0 — Authority Evaluation Integration
Prerequisite Decision Architecture
(`docs/PHASE_147J0_AUTHORITY_EVALUATION_INTEGRATION_PREREQUISITE_DECISION_ARCHITECTURE.md`)
**Governing predecessors:** AEM-001 v1.0 — Authority Evaluation Model
Contract (`docs/contracts/AUTHORITY_EVALUATION_MODEL_CONTRACT.md`),
FROZEN; AEMIC-001 v1.2 — Authority Evaluation Model Implementation
Contract
(`docs/contracts/AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT.md`),
FROZEN, independently verified through Phase 147F.2; IWC-001 v1.2 —
Interactive Workflow Contract
(`docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md`), FROZEN; IWPC-001
v1.4 — Interactive Workflow + Publication CLI/Transport Contract
(`docs/contracts/INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md`),
FROZEN; PEC-001 v1.1 — Publication Execution Contract
(`docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md`), FROZEN; CHGR-001
v1.3 — Canonical Human Governance Record Contract
(`docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`), FROZEN
**Governed subject:** The **integration-level design** connecting the
verified, standalone `pcae.authority_evaluation` package (AEM-001,
AEMIC-001) to the rest of PCAE's governed decision-publication pipeline:
the Authority Evaluation Service (AES) as sole orchestrator, the Decision
Template Resolution capability, the abstract Authority Registry
interaction contract, the two-stage evaluation lifecycle, the Authority
Evaluation Record (AER), replay, persistence, failure ownership, outcome
consumption, security, observability, and verification requirements —
precise and falsifiable enough for a future, separately-authorized
implementation phase to build against without re-deriving Phase 147J's
own architectural prose, and for a future, separately-authorized
verification phase to attempt to falsify.

**No-amendment relationship to existing contracts.** AESIC-001 amends
none of AEM-001, AEMIC-001, IWC-001, IWPC-001, PEC-001, or CHGR-001 —
exactly as Phase 147J §1/§22 already determined and this contract's own
§19 reconfirms. AESIC-001 converts Phase 147J's integration architecture
into binding, requirement-numbered obligations one layer more concrete
than that architecture, exactly as Phase 147E converted Phase 147D into
AEMIC-001, Phase 144B converted Phase 144A into PEC-001, Phase 145B
converted Phase 145A into IWPC-001, and Phase 147B converted Phase 147A
into AEM-001. Every AESIC-001 requirement is either a direct,
one-step-more-concrete restatement of a decision Phase 147J (or 147J.0)
already made, or an integration-level decision those architecture phases
explicitly deferred to this Contract Freeze (Phase 147J §18, §20.2,
§20.3) that this contract now resolves unambiguously. AESIC-001 MUST NOT
be read as amending, narrowing, or superseding AEM-001, AEMIC-001,
IWC-001, IWPC-001, PEC-001, CHGR-001, TAMC-001, TAMPC-001, or GAC-001;
where this contract cites any of them, the citation demonstrates
compatibility with an already-frozen provision, never a redefinition of
it (mirrors AEMIC-001 §0's own illustrative-citation discipline).

**Supersession rules.** AESIC-001 v1.0 governs the first integration of
`pcae.authority_evaluation` into PCAE's decision-publication pipeline
only. A future revision of AEM-001 or AEMIC-001 (via their own Amendment
Contracts) that widens or narrows the evaluation model or its
implementation MAY require a corresponding AESIC-001 revision; until such
a revision is frozen, AESIC-001 v1.0 remains the sole normative authority
over this integration's shape. AESIC-001 itself MAY be revised only
through a governed superseding contract revision (§19 below), never
through an implementing phase's own discretion.

**Requirement numbering convention:** Requirements are identified
`AESIC-REQ-001` through the final requirement in this document,
sequential, grouped by the section that introduces them, with no gaps and
no reuse. Once frozen, no requirement identifier is renumbered,
reassigned, or reused — mirroring AEM-001's, AEMIC-001's, PEC-001's,
IWPC-001's, and CHGR-001's own amendment discipline (§19 below).

**Runtime:** State: Observed / Maximum Capability: observe / Execution
Availability: unavailable — unaffected by this contract. Nothing this
contract defines is implemented by this phase; nothing it defines
touches `src/pcae/runtime/**`.

**This is contract text only.** It does not implement the Authority
Evaluation Service, the Decision Template Resolution capability, a
concrete Authority Registry, or the Authority Evaluation Record store;
does not create any module under `src/pcae/**`; does not modify
`src/pcae/**`, `tests/**`, any schema file, or any existing contract; and
does not authorize a future implementation phase to begin merely by this
contract's own freeze (§2, §17, §20 below state this explicitly).

---

## 0. Normative Language

The key words **SHALL**, **SHALL NOT**, **MUST**, **MUST NOT**,
**SHOULD**, **SHOULD NOT**, and **MAY** are normative, with the meanings
given in GLP-001 §0, adopted unchanged here (mirrors AEM-001, AEMIC-001,
PEC-001, IWPC-001, CHGR-001).

Sections 1–19 state the normative rules in narrative form; §21 (the
Requirement/Test Matrix) is the authoritative, falsifiable enumeration
cross-referencing every `AESIC-REQ-###`. Where narrative prose and a
requirement differ in force, the requirement's own text in the section
that introduces it is normative.

---

## 1. Purpose and Independent Reconstruction

### 1.1 Purpose

This contract freezes every architectural decision Phase 147J made about
integrating `pcae.authority_evaluation` into PCAE's governed
decision-publication pipeline, converting that architecture's prose into
binding, falsifiable requirements. A future implementation phase (147M or
later, per §16's roadmap) MUST be able to build the Authority Evaluation
Service, the Decision Template Resolution capability, a concrete
Authority Registry, and Authority Evaluation Record persistence entirely
from this contract's own text, without re-reading Phase 147J's
architecture document for any implementation-critical decision. A future
independent verification phase MUST be able to attempt to falsify this
contract using only this document, the frozen contracts it cites, and the
current, unmodified state of `src/pcae/authority_evaluation/**`,
`src/pcae/interactive_workflow/**`, and `src/pcae/governance/publication/**`.

### 1.2 Classification of Phase 147J's design choices

Every decision this contract freezes falls into exactly one of two
classes, mirroring AEMIC-001 §1.1's own discipline:

1. **Direct restatement** — a decision Phase 147J (or 147J.0) already made
   unambiguously, converted here into `SHALL`/`SHALL NOT` requirement
   form without altering its substance (e.g., "Stage 2 supersedes Stage 1
   unconditionally for citation purposes," Phase 147J §8.3/§8.5).
2. **Deferred-decision resolution** — a decision Phase 147J explicitly
   left open for this Contract Freeze to resolve (Phase 147J §18, §20.2,
   §20.3), resolved here for the first time (e.g., the exact `evaluation_id`
   shape, the mandatory-vs-optional status of `stage_1_outcome_ref`, and
   the identity/template-substitution hardening recommendation of Phase
   147J §16, converted here into a binding constructor-shape requirement).

No decision in this contract falls outside these two classes; this
contract introduces no new architectural choice Phase 147J did not
already make or explicitly defer.

---

## 2. Scope and No-Go Boundary

### 2.1 In scope

This contract governs: the Authority Evaluation Service's (AES) public
interface, error taxonomy, lifecycle, replay behavior, transaction span,
idempotency, and construction rules (§5); the Decision Template
Resolution capability (§6, internal to AES); the abstract Authority
Registry interaction contract (§7); the two-stage evaluation lifecycle
and its sequencing (§8, §9); the Authority Evaluation Record's identity,
immutability, and shape (§10, in prose — no schema); replay guarantees
(§11); the persistence contract (§12); failure ownership (§13); outcome
consumption rules (§14); security requirements (§15); observability
requirements (§16); non-functional requirements (§17); and independent
verification requirements (§18).

**AESIC-REQ-001.** This contract SHALL govern only the integration
surface named in this section; it SHALL NOT govern the internal
implementation of the already-frozen `pcae.authority_evaluation` package
(AEMIC-001's exclusive domain), the internal implementation of Interactive
Workflow's Session/Confirmation/state-machine logic (IWC-001's/IWPC-001's
exclusive domain), or the internal implementation of the Publication
Coordinator (PEC-001's exclusive domain).

### 2.2 Out of scope

- Concrete implementation of any component this contract names (deferred
  to a future Implementation phase, §16).
- JSON Schema definitions for the AER or any other artifact (§10.9
  explicitly forbids introducing one here).
- Amendment of AEM-001, AEMIC-001, IWC-001, IWPC-001, PEC-001, or
  CHGR-001 (none is required; §19).
- Concrete Authority Registry storage layout or write-path security
  (Phase 147J §18 item 3, deferred to a dedicated future Registry
  Implementation Contract).
- The exact call site inside `interactive_workflow/application/**` that
  invokes AES at each stage — this contract freezes the *constraint*
  (§8.2) that the caller sits above both Interactive Workflow and
  Publication, not the specific function.
- Presentation/UX mechanics for surfacing Stage 1/Stage 2 disagreement to
  a human (Phase 147J §8.6; remains future, separately governed work).

**AESIC-REQ-002.** No item listed in §2.2 SHALL be resolved by this
contract; each remains either explicitly out of scope permanently (schema
definitions, amendments) or deferred to a named future contract/phase.

---

## 3. Terminology

| Term | Definition |
|---|---|
| **AES** | Authority Evaluation Service — the sole orchestration component this contract governs (§5). |
| **Resolution** | The Decision Template & Declaration Resolution capability, internal to AES (§6). |
| **Registry** | The abstract `AuthorityRegistry` boundary, already frozen by AEM-001 §4.5 and AEMIC-001 §11 (§7). |
| **Evaluator** | The pure `evaluate()` function in `pcae.authority_evaluation.evaluation`, unmodified by this contract (§4). |
| **Stage 1** | Advisory evaluation, at or before Confirmation, never persisted (§8.1). |
| **Stage 2** | Fresh, publication-freshness evaluation, immediately before CHGR construction, persisted as an AER (§8.3). |
| **AER** | Authority Evaluation Record — the immutable, Stage-2-only persisted artifact this contract names the shape of (§10). |
| **`claimed_identity`** | The identity string AES evaluates, sourced exclusively from `Session.owner_identity` (§5.2, §15). |
| **`citation_text`** | The verbatim `eligible_authority` text of a resolved Decision Template, the only AER field ever cited into CHGR's `authority_basis_claimed` (§6.3, §14). |
| **`package_id`** | The `PublicationReadinessPackage` identifier that keys Stage 2 idempotency and the AER itself (§10.1, §12.4). |
| **`evaluation_id`** | A per-invocation correlation identifier this contract introduces (§16.8), distinct from `package_id` and `record_id`. |

**AESIC-REQ-003.** Every term in §3 SHALL be used throughout this
contract with exactly the meaning given here; no section MAY silently
redefine a term listed in this table.

---

## 4. Components

This contract governs exactly six components, each with a single,
non-overlapping responsibility (Phase 147J §15.2's responsibility matrix,
frozen here unchanged):

| # | Component | Governed by |
|---|---|---|
| 1 | Interactive Workflow | IWC-001, IWPC-001 (unmodified); this contract adds only the prohibition in §5.13/§15.1 |
| 2 | Authority Evaluation Service (AES) | This contract, §5 |
| 3 | Decision Template & Declaration Resolution | This contract, §6 (internal to AES) |
| 4 | Authority Registry | AEM-001 §4.5, AEMIC-001 §11 (ABC shape, unmodified); this contract, §7 (integration-level interaction obligations only) |
| 5 | Evaluator (`evaluate()`) | AEMIC-001 (unmodified); this contract adds no new obligation, §4 below |
| 6 | Publication Coordinator | PEC-001 (unmodified); this contract adds only the citation-only consumption rule, §14 |

**AESIC-REQ-004.** This contract SHALL introduce no seventh component and
SHALL NOT merge any two of the six listed components into one; component
boundaries frozen by §4 of this contract MUST match Phase 147J §4.2's
ownership/data-flow/control-flow matrix exactly.

---

## 5. Authority Evaluation Service (AES)

### 5.1 Role

**AESIC-REQ-005.** AES SHALL be the sole orchestrator of the integration
surface: the sole reader of `Session.owner_identity` for evaluation
purposes, the sole resolver of Decision Templates, the sole caller of
`AuthorityRegistry.resolve()`, and the sole invoker of `evaluate()`.

**AESIC-REQ-006.** No other PCAE component SHALL read `Session.owner_identity`
for the purpose of authority evaluation, call `AuthorityRegistry.resolve()`,
or invoke `evaluate()` directly.

### 5.2 Public interface

**AESIC-REQ-007.** AES SHALL expose exactly the following public
interface shape (types illustrative; concrete typing is an implementation
decision within this shape):

```
class AuthorityEvaluationService:
    def __init__(
        self,
        registry: AuthorityRegistry,
        aer_store: AuthorityEvaluationRecordStore,
    ) -> None: ...

    def evaluate_stage_1(
        self,
        *,
        session: Session,
    ) -> AuthorityEvaluationOutcome: ...
        # advisory only; never persisted; caller decides how/whether to surface it

    def evaluate_stage_2(
        self,
        *,
        session: Session,
        package_id: str,
    ) -> AuthorityEvaluationRecord: ...
        # fresh resolution + evaluation; persists and returns an immutable AER
```

**AESIC-REQ-008 (identity/template-substitution hardening).** Both
`evaluate_stage_1` and `evaluate_stage_2` SHALL accept a `Session` object,
never bare `claimed_identity`/`template_ref`/`template_version` strings.
AES SHALL derive `claimed_identity` from `session.owner_identity`,
`template_ref` from `session.template_ref`, and `template_version` from
`session.template_version` internally, on every call. This resolves the
identity-substitution and template-substitution hardening recommendation
Phase 147J §16 raised as a contract-freeze-level decision: a caller
cannot supply an identity or template pair other than the one already
bound to the session it holds, because no such parameter exists on the
public interface.

**AESIC-REQ-009.** Neither method SHALL accept a `declaration` or
`citation_text` argument from its caller. Both are always resolved
internally, per-invocation, by AES itself (Phase 147J §5.11's
single-resolution-point guarantee, unmodified).

**AESIC-REQ-010.** Both methods SHALL raise only the error taxonomy of
§13, never a bare `Exception` and never a type not named in §13's matrix.

### 5.3 Responsibilities

**AESIC-REQ-011.** AES SHALL, for every invocation:

1. Read `claimed_identity`, `template_ref`, and `template_version` from
   the `Session` object it was given (never re-derive, never
   independently collect).
2. Resolve, exactly once per evaluation attempt, the Decision Template
   document identified by `(template_ref, template_version)`, deriving
   both `citation_text` and the Registry-resolved `declaration` from that
   single resolved document (§6.2).
3. Invoke `evaluate()` (unmodified) with the resolved arguments.
4. For Stage 2 only: produce and persist an immutable AER (§10).
5. Expose its own outcomes for read-only consumption — never push, never
   gate (§14, §15).

### 5.4 Inputs and outputs

**AESIC-REQ-012.** AES's inputs SHALL be exactly: the injected `registry`
and `aer_store` collaborators (construction-time, §5.6); and, per call,
the `Session` object and (Stage 2 only) `package_id`. AES SHALL accept no
other input.

**AESIC-REQ-013.** AES's outputs SHALL be exactly: one
`AuthorityEvaluationOutcome` per invocation (in-memory always); for Stage
2 only, one persisted, immutable AER, referenceable via `{record_id,
record_digest, record_family="authority_evaluation_record"}`; and
diagnostic/log events for every resolution attempt, Registry call, and
evaluation (§16).

### 5.5 Dependencies

**AESIC-REQ-014.** AES SHALL depend on exactly: the unmodified
`pcae.authority_evaluation` package (`models`, `registry` ABC,
`evaluation.evaluate`, `errors`, `serialization`); a concrete
`AuthorityRegistry` implementation (future phase, §7); the Decision
Template Resolution capability (internal to AES, §6); and its own AER
store (§10, §12). AES SHALL NOT depend on `interactive_workflow.session`,
`interactive_workflow.orchestration`, `interactive_workflow.confirmation`,
or `governance.publication.coordinator` internals — it reads only the
`Session` object handed to it by its caller (§8.2).

### 5.6 Construction rules

**AESIC-REQ-015.** AES SHALL be constructed with exactly two collaborators,
both injectable: a concrete `AuthorityRegistry` implementation, and an AER
store. AES SHALL NOT use a global singleton, ambient configuration lookup,
or implicit Session-store access; every input AES needs SHALL be passed
explicitly by its caller.

### 5.7 Error ownership

**AESIC-REQ-016.** AES SHALL translate every failure from its
collaborators into one of its own named outcomes (§13), never a bare
exception:

- A `AuthorityRegistryUnavailableError`/`AuthorityRegistryCorruptError`
  from the Registry SHALL be caught by AES and surfaced as an AES-owned
  `AuthorityEvaluationServiceRegistryUnavailable`/`...RegistryCorrupt`
  condition — never silently swallowed, never retried transparently
  without disclosure.
- A missing/malformed Decision Template from Resolution SHALL be surfaced
  as an AES-owned `DecisionTemplateResolutionFailed` condition, distinct
  from any Registry condition.
- Any `AuthorityEvaluationError` subclass raised by `evaluate()` itself
  SHALL propagate through AES unchanged in type — AES SHALL add no new
  wrapping around the evaluator's own exception taxonomy.

### 5.8 Lifecycle

**AESIC-REQ-017.** AES SHALL be stateless between invocations apart from
the durable AER store it delegates all persistence to. AES SHALL hold no
in-memory session cache, no Registry cache beyond what a future concrete
Registry implementation itself may choose to cache internally, and no
cross-invocation mutable state. Each `evaluate_stage_1`/`evaluate_stage_2`
call SHALL be a self-contained, independently-replayable unit of work.

### 5.9 Replay behavior

**AESIC-REQ-018.** Because `evaluate()` is deterministic and AES adds no
hidden state, any AES invocation MAY be safely repeated from the same
inputs and SHALL produce the same `AuthorityEvaluationOutcome` (modulo
`evaluated_at`, which is metadata, never an evaluation input `evaluate()`
itself branches on). See full replay matrix, §11.

**AESIC-REQ-019.** Stage 2's AER write SHALL use the same `O_CREAT |
O_EXCL` idempotency-marker pattern `PublicationRecordStore.commit_publication`
already uses (`storage.py:8-16`), so a concurrent duplicate Stage 2
attempt for the same `package_id` is detected, never silently
double-written.

### 5.10 Transaction span

**AESIC-REQ-020.** AES's own work (resolution + evaluation + AER write)
SHALL be its own, independent unit — it SHALL NOT be nested inside the
Publication Coordinator's `execute()` transaction, and it SHALL NOT nest
Interactive Workflow's own session-transition transaction inside itself.

**AESIC-REQ-021.** Stage 2 SHALL complete (successfully or with a
disclosed failure) before the Coordinator's `execute()` is invoked. AES's
own write to the AER store SHALL be a separate atomic operation from the
Coordinator's own atomic CHGR write.

### 5.11 Idempotency

**AESIC-REQ-022.** Stage 1 SHALL NOT persist any state; idempotency is
definitionally free — repeating Stage 1 simply recomputes the same
advisory outcome.

**AESIC-REQ-023.** Stage 2 SHALL be idempotent per `package_id`: a second
Stage 2 attempt for the same `package_id` SHALL either (a) return the
already-persisted AER unchanged if evaluation inputs are unchanged, or
(b) be refused or superseded per §11's restart matrix if inputs changed —
it SHALL NOT be silently overwritten.

### 5.12 Internal collaborators

**AESIC-REQ-024.** The Decision Template & Declaration Resolution
capability (§6) and the concrete `AuthorityRegistry` (§7) SHALL be AES's
only internal collaborators. Neither SHALL be separately publicly
callable by any other PCAE component — both SHALL be constructor-injected
into, and used exclusively by, AES.

### 5.13 Isolation from Interactive Workflow and Publication Coordinator

**AESIC-REQ-025.** Interactive Workflow's Session/Confirmation/state-machine
code SHALL NOT import or call AES, Resolution, or `AuthorityRegistry`.

**AESIC-REQ-026.** The Publication Coordinator SHALL NOT import or call
AES, Resolution, or `AuthorityRegistry`; it SHALL consume only an
already-produced AER reference from a readiness package (§14).

---

## 6. Decision Template Resolution

**AESIC-REQ-027.** Resolution SHALL NOT be a separately callable public
component — it SHALL be an internal capability of AES, exercised on every
`evaluate_stage_1`/`evaluate_stage_2` call.

### 6.1 Inputs

**AESIC-REQ-028.** Resolution SHALL accept exactly `(template_ref,
template_version)`, read by AES from `Session` — Resolution SHALL accept
no other input and SHALL NOT independently discover a template outside
the pair supplied.

### 6.2 Outputs

**AESIC-REQ-029.** Resolution SHALL derive exactly two values from **one**
resolved Decision Template document (never two independent reads — the
single-copy-propagation guarantee):

1. `citation_text` — the resolved document's own `eligible_authority`
   field, copied verbatim.
2. The `EligibleAuthorityDeclaration` that `AuthorityRegistry.resolve()`
   returns for the same `(template_ref, template_version)` pair.

### 6.3 Ownership

**AESIC-REQ-030.** Template identity (`template_id`/`version` inside the
resolved document) SHALL be owned by whoever authors/versions Decision
Templates — a governance-authoring act, out of scope for AES itself,
which only reads already-authored templates.

**AESIC-REQ-031.** The resolved document's `eligible_authority` field
SHALL be the sole source of `citation_text`; Resolution SHALL NOT
summarize, truncate, or re-derive it.

**AESIC-REQ-032.** The Registry SHALL own Declaration construction;
Resolution SHALL only consume, never construct, an
`EligibleAuthorityDeclaration`.

### 6.4 Failure model

**AESIC-REQ-033.** Resolution SHALL raise exactly the following, and no
other, failure types:

| Condition | Exception |
|---|---|
| No template document exists for `(template_ref, template_version)` | `DecisionTemplateNotFoundError` |
| Template document exists but fails schema validation | `DecisionTemplateMalformedError` |
| Template document exists, validates, but `eligible_authority` resolves to an empty/whitespace-only string | `DecisionTemplateCitationEmptyError` |
| Registry lookup for the same pair fails | Propagated as the Registry's own §7.3 failure classification, never conflated with a template-resolution failure |

### 6.5 Cache policy

**AESIC-REQ-034.** Resolution SHALL NOT cache across evaluation attempts.
Every Stage 1 and every Stage 2 call SHALL re-resolve from scratch. A
future concrete `AuthorityRegistry` implementation MAY cache internally
(§7), but Resolution itself, and AES's use of it, SHALL NOT assume or
rely on that.

### 6.6 Determinism

**AESIC-REQ-035.** Resolution SHALL be a pure function of `(template_ref,
template_version, <current on-disk template state>)` — deterministic
given fixed storage content at read time.

### 6.7 Versioning

**AESIC-REQ-036.** `template_version` SHALL be part of the resolution
key, never resolved implicitly to "latest." Resolution SHALL always
resolve the exact `(template_ref, template_version)` pair `Session`
carries.

### 6.8 Retry semantics

**AESIC-REQ-037.** Resolution SHALL perform no internal retry — a single
storage read, once, per call. Retry, if ever needed, is the responsibility
of AES's caller, never something Resolution itself hides.

### 6.9 Interaction with Registry

**AESIC-REQ-038.** Resolution SHALL be the Registry's only caller, and
SHALL call it exactly once per stage per evaluation attempt.

### 6.10 Ordering constraint

**AESIC-REQ-039.** Resolution SHALL always complete, successfully or with
a disclosed failure, before `evaluate()` is invoked. `evaluate()` accepts
`declaration` and `citation_text` as already-resolved parameters and
performs no I/O of its own — this is a structural fact about the
already-verified, unmodified evaluator, not a design preference this
contract could override.

---

## 7. Registry Contract

Abstract obligations only — no implementation.

### 7.1 Lookup behavior

**AESIC-REQ-040.** The Registry SHALL expose exactly the one method
already frozen by AEM-001 §4.5 and `registry.py:17-24`:
`resolve(template_ref, template_version) -> Optional[EligibleAuthorityDeclaration]`.
No `create`/`persist`/`delete`/`list`/`enumerate` method SHALL be added to
this ABC by this contract or by any future implementation phase — a
future write path, if one is ever needed, belongs on a separate
authoring-side interface.

**AESIC-REQ-041.** `resolve()` SHALL be a pure function of its two inputs
at any fixed point in time; it SHALL return `None`, never raise, for "no
Declaration exists" — an ordinary, expected outcome, not an error
condition.

### 7.2 Version semantics

**AESIC-REQ-042.** Each `(template_ref, template_version)` pair SHALL
identify at most one Declaration; version SHALL be part of the lookup
key, never resolved implicitly to "latest."

### 7.3 Identity semantics

**AESIC-REQ-043.** The Registry SHALL be keyed by `(template_ref,
template_version)` exactly, with no first-match-among-duplicates
resolution.

### 7.4 Duplicate semantics

**AESIC-REQ-044.** A concrete Registry implementation SHALL raise
`AuthorityRegistryCorruptError` on detecting two conflicting Declarations
for the same key — it SHALL NOT silently pick one.

### 7.5 Failure classifications

**AESIC-REQ-045.** The Registry SHALL expose exactly two failure
classifications, already named and unmodified by this contract:
`AuthorityRegistryUnavailableError` (storage could not be consulted at
all) and `AuthorityRegistryCorruptError` (storage answered but the record
is structurally malformed or a duplicate/conflict was detected). Neither
SHALL be conflated with a legitimate `None` return.

### 7.6 Immutability

**AESIC-REQ-046.** Once written, a Declaration record SHALL never be
mutated in place — a new template version SHALL receive a new Declaration
keyed by the new `(template_ref, template_version)` pair.

### 7.7 Offline behavior

**AESIC-REQ-047.** If the Registry's storage is entirely unavailable,
`resolve()` SHALL raise `AuthorityRegistryUnavailableError`. AES's own
error ownership (§5.7) SHALL translate this into a disclosed, non-gating
failure, never a silent `None`.

### 7.8 Restart guarantees

**AESIC-REQ-048.** A concrete Registry implementation SHALL be
restart-durable with no in-memory-only state to lose; any internal cache
MUST be safe to cold-start empty and repopulate lazily.

### 7.9 Repository interaction

**AESIC-REQ-049.** The Registry SHALL perform no git/repository read —
Decision Templates SHALL remain ordinary on-disk artifacts under
`.pcae`'s own storage tree (or an equivalent future location), never
git-history-derived, mirroring `governance_record_provenance`'s own
already-disclosed limitation.

### 7.10 Why the Registry remains outside the Evaluator

**AESIC-REQ-050.** No future implementation SHALL move Registry lookup
inside `evaluate()` — `evaluate()` SHALL remain free of I/O of any kind
(AEMIC-REQ-073/076/077, unmodified), and the Registry SHALL remain the
one place, outside the evaluator, where "resolve a Declaration" is a
named, testable, independently-swappable operation.

---

## 8. Authority Evaluation Record (AER)

### 8.1 Purpose

**AESIC-REQ-051.** The AER SHALL be the sole persisted output of Stage 2
evaluation, wrapping the `AuthorityEvaluationOutcome` plus stage/replay
metadata. It SHALL be produced for Stage 2 only — Stage 1 SHALL NOT
produce an AER.

### 8.2 Identity

**AESIC-REQ-052.** Each AER SHALL receive its own `record_id` (e.g.
`aer-<uuid4hex>`, mirroring `chgr-<uuid4hex>`/`pubexec-<uuid4hex>` naming
already used in this codebase), unique per Stage 2 evaluation attempt.

**AESIC-REQ-053.** Each AER SHALL be keyed by `package_id` for lookup and
idempotency purposes (§5.11, §12.4).

### 8.3 Immutability

**AESIC-REQ-054.** The AER SHALL be immutable once written — never
mutated in place. A changed evaluation SHALL produce a new AER (with a
new `record_id`), never an edit to an existing one.

### 8.4 Digest requirements

**AESIC-REQ-055.** Each AER SHALL carry a `record_digest`, computed the
same way every other durable record in this codebase computes one
(`compute_record_digest`, already used identically for all four CHGR
artifact families). Digest *matching* verification is a verification-layer
responsibility, not a schema/write-time guarantee, mirroring
`references.schema.json`'s existing documented discipline.

### 8.5 Content shape (prose only — no schema)

**AESIC-REQ-056.** The AER SHALL contain, at minimum: `record_id`,
`record_digest`, `record_family` (fixed value `"authority_evaluation_record"`),
`package_id`, `stage` (fixed value `"stage_2"`), the wrapped
`AuthorityEvaluationOutcome` (unmodified shape, per AEMIC-001 §6), an
`evaluation_id` (§16.8), an `evaluated_at` timestamp, and an optional
`stage_1_outcome_ref` (§8.6). This contract defines no JSON Schema file
for the AER — the concrete schema is future Evaluation Persistence
Contract work (§16 item 4).

### 8.6 Stage 1/Stage 2 relationship

**AESIC-REQ-057.** The AER MUST carry a `stage_1_outcome_ref` field
whenever a Stage 1 evaluation for the same `package_id`/session preceded
Stage 2, so that a disagreement between the two is structurally visible
(both outcomes retrievable, never one silently discarded). Resolving
Phase 147J §20.4 item 2's open question: `stage_1_outcome_ref` SHALL be
**mandatory-when-a-Stage-1-outcome-exists, always-optional-otherwise** —
never a strict, unconditional-presence field, since Stage 1 itself is
never guaranteed to precede every Stage 2 attempt (§8.1's ownership rule
permits a caller to invoke Stage 2 without ever having invoked Stage 1
for that session).

### 8.7 Relationship to CHGR

**AESIC-REQ-058.** Only the AER's `citation_text` SHALL flow forward,
verbatim, into CHGR's `authority_basis_claimed` field. The AER itself,
the wrapped `AuthorityEvaluationOutcome`, `declaration_ref`, or any other
AER field SHALL NOT be embedded into CHGR. A future, separately governed
contract amendment MAY additionally let `governance_record_provenance`
carry an `authority_evaluation_ref` citing the AER directly — this
contract does not decide that (Phase 147J §10.8, §18 item 6).

### 8.8 Relationship to Readiness

**AESIC-REQ-059.** A `PublicationReadinessPackage` MAY carry a reference
to the AER (`authority_evaluation_ref: Optional[{record_id, record_digest,
record_family}]`) — never the AER's payload inline. This mirrors every
other existing readiness-package reference field (`evidence_refs`,
`clarification_refs`, `audit_refs`, `preview_id`/`preview_digest`,
`confirmation_request_id`/`confirmation_response_id`).

### 8.9 Relationship to Session

**AESIC-REQ-060.** No AER, AER reference, Stage 1 outcome, or Stage 2
outcome SHALL ever be written back onto `Session` or `SessionState`.
`Session.owner_identity`, `template_ref`, and `template_version` SHALL
remain read-only inputs to AES, never gaining a corresponding output
field.

### 8.10 Reference-only consumption

**AESIC-REQ-061.** Every consumer of an AER outside AES itself (Readiness,
Publication, CHGR, diagnostics, audit, inspection) SHALL consume it only
via its `{record_id, record_digest, record_family}` reference or, for
Publication/CHGR, its `citation_text` value — never by re-deriving,
re-evaluating, or independently reconstructing an AER's content.

---

## 9. Lifecycle and Sequencing

### 9.1 Stage 1 — Advisory evaluation

**AESIC-REQ-062.** Stage 1 SHALL occur at or before Confirmation
(`SessionState.AWAITING_CONFIRMATION` → `CONFIRMED`).

**AESIC-REQ-063.** Stage 1 SHALL be invoked by AES's caller (§9.2) —
never by Interactive Workflow's own transition logic, and never
automatically triggered by a `SessionState` transition.

**AESIC-REQ-064.** Stage 1's outcome SHALL NOT be persisted — at most
surfaced as advisory Session or Preview *display* state (never a
`Session` field, never a governance artifact).

**AESIC-REQ-065.** Stage 1 is definitionally stale by the time
Publication occurs; this SHALL be treated as expected, disclosed
behavior, never a defect.

### 9.2 Who invokes each stage

**AESIC-REQ-066.** The invoking caller at each stage SHALL be a component
above both Interactive Workflow and Publication — the same caller-side
layer that already orchestrates the interactive-workflow → publication-handoff
→ publication-execution sequence today (e.g.
`interactive_workflow/application/{session_service,publication_service}.py`).
Neither Interactive Workflow nor the Publication Coordinator SHALL invoke
AES as part of their own internal logic (§5.13).

### 9.3 Stage 2 — Publication freshness evaluation

**AESIC-REQ-067.** Stage 2 SHALL occur immediately before CHGR
construction (`build_publication_record`), and strictly outside the
Publication Coordinator's own `execute()` transaction (§5.10). The
Coordinator's caller SHALL run Stage 2, obtain the AER's `citation_text`,
and only then invoke `Coordinator.execute()` with a readiness package
whose `authority_evaluation_ref` field is already populated.

**AESIC-REQ-068.** Stage 2 SHALL be owned exclusively by AES — never the
Coordinator itself.

**AESIC-REQ-069.** Stage 2's inputs and outcome SHALL be persisted
together as one immutable AER (§8).

### 9.4 Ordering and supersession

**AESIC-REQ-070.** Stage 2 SHALL unconditionally supersede Stage 1 for
citation purposes. Only Stage 2's `citation_text` SHALL ever be cited
into `authority_basis_claimed`. Stage 1 SHALL exist solely to inform the
human decision-maker earlier in the workflow.

**AESIC-REQ-071.** Stage 2 SHALL NEVER be merged with Stage 1 through any
reconciliation rule. A Stage 1/Stage 2 disagreement SHALL be surfaced as
a disclosed fact (§8.6, §15), never quietly averaged, voted, or
overridden.

### 9.5 Duplicate publication / publication retry

**AESIC-REQ-072.** If a Publication Execution attempt is retried after a
failure that occurred before the Coordinator's atomic write, a fresh
Stage 2 attempt for the same `package_id` SHALL be permitted. AES's Stage
2 idempotency (§5.11) SHALL govern whether that fresh attempt reuses the
already-persisted AER or produces a new one, per §11's restart matrix.

### 9.6 Human confirmation

**AESIC-REQ-073.** Human confirmation SHALL occur exactly once, at
`decision-session confirm` (unmodified). Stage 1 SHALL precede it
(advisory only, never gating it); Stage 2 SHALL follow it (never
re-triggering or invalidating it).

---

## 10. Registry Contract

*(See §7 — the prompt's structure separates "Registry Contract" (§8) from
"Registry Boundary" naming; both are governed together in §7 above, which
this section cross-references to avoid duplicating normative text.)*

**AESIC-REQ-074.** All Registry obligations SHALL be governed exclusively
by §7 of this contract; no other section SHALL introduce a conflicting
Registry requirement.

---

## 11. Replay Contract

### 11.1 Replay guarantees

**AESIC-REQ-075.** Because `evaluate()` is total, deterministic, and
side-effect-free, and because AES itself holds no hidden state, every AES
invocation SHALL be safely repeatable from its own recorded inputs.
Replay architecture governs only what happens to already-persisted
output when a repeat occurs, never whether recomputation itself is safe.

### 11.2 Restart matrix

**AESIC-REQ-076.** The following restart matrix SHALL bind every future
implementation:

| Restart point | Stage 1 effect | Stage 2 effect |
|---|---|---|
| Before Stage 1 | No effect — Stage 1 simply runs (or doesn't) whenever its caller next invokes it | N/A |
| After Stage 1, before Confirmation | Stage 1's outcome is lost (never persisted) — a fresh Stage 1 recomputation on resumption is equivalent | N/A |
| Before Stage 2 | N/A | Stage 2 has not yet run; resumes normally, reading current Registry/template state |
| After Stage 2, before Publication authorization | N/A | AER already durably persisted; resumption reads the existing AER via `package_id`, never recomputes unless explicitly asked to |
| After Publication authorization, before Coordinator commit | N/A | AER unaffected — already durable before this point; a retried Coordinator `execute()` uses the already-persisted AER's `citation_text` unchanged |
| After Coordinator commit (CHGR exists) | N/A | AER remains as the durable, immutable record of what was cited; never re-evaluated post-publication |
| Publication retry (Coordinator-level) | N/A | Coordinator's own `_check_replay` (unmodified) refuses a second publish for an already-published `package_id` regardless of AES/AER state |
| Duplicate confirmation | N/A (IWC-001's own replay-protected concern) | N/A |
| Duplicate readiness (a second `build_package` call) | N/A | A second readiness package MAY cite a new Stage 2 AER (a fresh `package_id`); AES does not itself deduplicate across distinct `package_id`s |
| Duplicate publication attempt | N/A | Governed entirely by the Coordinator's own idempotency marker, unaffected by AES |
| Registry evolution (Declaration changed between attempts) | N/A | Each Stage 2 attempt SHALL always read the Registry's current state (§6.5) — a changed Declaration produces a genuinely different, freshly-computed outcome, disclosed as such, never silently reconciled with an earlier attempt |
| Decision Template evolution (citation text changed) | N/A | Stage 2 SHALL always re-resolve the template fresh; a changed `eligible_authority` text produces a new `citation_text` in the new AER |
| Citation evolution | N/A | Subsumed by "Decision Template evolution" — citation text is derived from the template, never tracked independently |

### 11.3 Observational equivalence requirement

**AESIC-REQ-077.** For any restart point in §11.2's matrix, a resumption
SHALL produce outcomes observationally equivalent to an uninterrupted
execution with the same inputs — no restart point SHALL introduce a
distinguishable, undisclosed side effect.

---

## 12. Persistence Contract

### 12.1 Persistent artifacts

**AESIC-REQ-078.** Exactly one artifact type SHALL be durably persisted
by AES: the AER (§8), one per Stage 2 evaluation attempt, keyed by
`package_id`.

**AESIC-REQ-079.** The Declaration and resolved-template content that fed
a given AER SHALL NOT be separately persisted by AES — the AER's own
`outcome.declaration_ref` and `citation_text` are sufficient provenance;
the source Declaration/template themselves remain the Registry's own
durable state (§7.6), never AES's to duplicate.

### 12.2 Transient state

**AESIC-REQ-080.** The following SHALL remain transient, never persisted:
every Stage 1 outcome (§9.1); AES's own internal resolution intermediate
state (the resolved Decision Template document object itself, once
`citation_text`/`declaration` are extracted); any in-flight, not-yet-persisted
Stage 2 attempt.

### 12.3 Recomputed state

**AESIC-REQ-081.** Every Stage 1 outcome SHALL be recomputed on each
invocation, never read from a prior persisted value (none exists). A
duplicate Stage 2 attempt for a `package_id` with unchanged inputs SHALL
recompute and find the already-persisted AER unchanged (idempotent
no-op); with changed inputs, §11's restart matrix governs.

### 12.4 Immutable state

**AESIC-REQ-082.** The AER, once written, SHALL be immutable (§8.3). No
future implementation SHALL provide an update or patch operation for an
existing AER.

### 12.5 Digest ownership

**AESIC-REQ-083.** AES SHALL own computing and attaching the AER's
`record_digest` (§8.4). No downstream consumer SHALL recompute or
override it.

### 12.6 Identifier ownership

**AESIC-REQ-084.** AES SHALL own assigning `record_id` (§8.2). No
downstream consumer SHALL assign or reassign it.

### 12.7 Cross-artifact references

**AESIC-REQ-085.** The AER SHALL be referenced from a
`PublicationReadinessPackage`, never embedded (§8.8). CHGR SHALL cite
only `citation_text`, never a reference to the AER itself unless a future,
separately governed contract amendment adds one (§8.7).

### 12.8 Storage mechanics (structural requirement, no implementation)

**AESIC-REQ-086.** A concrete AER store SHALL write using an atomic,
write-once pattern (temp file + fsync + `os.replace`, or an equivalent
mechanism providing the same guarantee), mirroring
`governance/publication/storage.py`'s `_write_atomic_json` and
`PublicationRecordStore`'s `O_CREAT | O_EXCL` idempotency-marker
discipline. This contract does not select the concrete storage backend or
file layout — that is a future Evaluation Persistence Contract's decision
(§16 item 4).

---

## 13. Failure Ownership

**AESIC-REQ-087.** The following failure-ownership matrix SHALL bind
every future implementation. Every failure SHALL name its origin, owner,
recovery owner, user-visible owner, logging owner, and retry owner
exactly as follows:

| Failure type | Origin | Owner | Recovery owner | User-visible owner | Logging owner | Retry owner |
|---|---|---|---|---|---|---|
| Registry unavailable | Registry's storage layer | AES (translates, §5.7) | Whoever operates the Registry's storage (future, out of scope) | AES's caller (§9.2) | AES (every call attempt) | AES's caller — AES itself performs no silent retry |
| Template missing (`DecisionTemplateNotFoundError`) | Resolution (inside AES) | AES | Whoever authors Decision Templates (out of scope) | AES's caller | AES | AES's caller |
| Identity mismatch (`TemplateIdentityMismatchError`, from `evaluate()`) | Evaluator (unmodified) | Evaluator raises; AES propagates unchanged | AES's caller — indicates a Resolution-internal-consistency bug, never a normal runtime condition | AES's caller | AES (logs the propagated exception verbatim) | Not retryable without fixing Resolution's own internal consistency — a programming-error-class failure |
| Duplicate declaration (`AuthorityRegistryCorruptError`) | Registry's storage layer | AES translates, same as "Registry unavailable" | Whoever authors/writes Declarations (future Registry-implementation phase) | AES's caller | AES | Not retryable until the underlying duplicate is repaired at the storage layer |
| Citation mismatch | Not a distinct condition — subsumed by template-identity mismatch above | — | — | — | — | — |
| Stale evaluation | Expected behavior, not a failure (§9.1, §9.4) | AES (produces the disagreement-visible AER, §8.6) | N/A | AES's caller (future UX) | AES (both outcomes logged) | N/A |
| Duplicate publication | Governed entirely by the Coordinator's own existing idempotency marker, unaffected by AES | Publication Coordinator (PEC-001, unmodified) | Coordinator's own retry model | Coordinator's caller | Coordinator | Coordinator's caller |
| Serialization failure (AER `to_payload`-equivalent) | AES's own AER serialization | AES | AES (a serialization defect is AES's own bug to fix) | AES's caller | AES | Not retryable without a code fix |
| Digest mismatch | AER verification-layer check (future) | Verification layer (mirrors `verify --related`) | Operator investigating tampering/corruption | Whoever runs verification | Verification layer | N/A — a digest mismatch on an immutable record indicates corruption or tampering, never a transient condition to retry |
| Restart inconsistency | N/A — §11's restart matrix shows no inconsistency class exists by design | — | — | — | — | — |
| AER write failure (disk-level) | AES's own AER store | AES | Operator (disk/permissions issue) | AES's caller | AES | AES's caller may retry the whole Stage 2 call — the AER write is atomic (§12.8), so a failed write leaves no partial artifact to clean up |
| Missing citation text at evaluator level (`MissingCitationTextError`) | Evaluator (unmodified) — only reachable if Resolution supplies `citation_text=None` while evaluation computes to `ELIGIBLE`, which §6.4 should already have refused as `DecisionTemplateCitationEmptyError` | Evaluator raises; AES propagates | Indicates a Resolution-internal-consistency gap — a Resolution bug | AES's caller | AES | Not retryable without a Resolution code fix |

**AESIC-REQ-088.** No failure type SHALL be introduced by a future
implementation phase without extending this matrix through a governed
contract amendment (§19); an implementation SHALL NOT invent an
undisclosed failure class.

---

## 14. Outcome Consumption

### 14.1 Permitted consumers

**AESIC-REQ-089.** The following consumers SHALL be the only permitted
consumers of `AuthorityEvaluationOutcome`/AER data, and SHALL be
restricted exactly as follows:

| Consumer | Permitted usage | Explicitly prohibited |
|---|---|---|
| Interactive Workflow (advisory, Stage 1) | Reads the outcome to *display* to the human before Confirmation | SHALL NEVER gate, block, or auto-select a transition based on the outcome |
| Readiness (`PublicationReadinessPackage`) | Carries a reference (`{record_id, record_digest, record_family}`) to the Stage 2 AER | SHALL NEVER treat the reference's mere presence as proof of readiness completeness beyond what `PublicationHandoff.is_ready`/`validate_completeness` already require |
| Publication (Coordinator) | Reads only `AER.outcome.citation_text` (via the readiness package's reference), cites it verbatim into `authority_basis_claimed` (PEC-REQ-115) | SHALL NEVER read `evaluation_result`, `declaration_ref`, or any other AER field as a gating input to `execute()`'s own validation sequence |
| CHGR (`build_publication_record`) | `authority_basis_claimed = citation_text` when present; `limitations` entry disclosing its absence otherwise | SHALL NEVER derive `assurance_level` from any AES output — the two remain independent |
| Inspection / Diagnostics / Audit | Read-only queries against the AER store | SHALL NEVER provide a write path — these are exclusively read consumers |

### 14.2 Explicit prohibitions

**AESIC-REQ-090.** `AuthorityEvaluationOutcome` and the AER that wraps it
SHALL NEVER be treated, by any consumer, as: an authorization, a
permission, an execution trigger, or a policy decision — unless a future
contract explicitly amends AEM-001/AEMIC-001/PEC-001/CHGR-001 to grant
that meaning, which no phase to date (147G–147K) has done and this
contract does not propose.

**AESIC-REQ-091.** No consumer named in §14.1 SHALL branch pipeline
control flow (a `SessionState` transition, a `Coordinator.execute()`
validation step, or any CHGR field other than `authority_basis_claimed`)
on an `AuthorityEvaluationOutcome` or AER value.

---

## 15. Security Requirements

**AESIC-REQ-092.** The following mitigations SHALL be contractual — every
future implementation SHALL satisfy each:

| Threat | Contractual mitigation |
|---|---|
| Tampering (AER modified post-write) | AER SHALL be immutable once written (§8.3), digest-covered (§8.4); a verification-layer check SHALL be able to detect a digest mismatch |
| Stale evaluations | Structurally addressed by the two-stage model (§9) — Stage 2 SHALL always supersede Stage 1, and SHALL always re-resolve fresh (§6.5); staleness SHALL be disclosed, never silently treated as current |
| Citation substitution | Prevented by `evaluate()`'s own `TemplateIdentityMismatchError` check (unmodified) — Resolution's derived `declaration` MUST agree with the evaluation's own `(template_ref, template_version)`, or evaluation SHALL refuse before producing an outcome |
| Identity substitution | Prevented structurally by AESIC-REQ-008: AES SHALL accept only a `Session` object, deriving `claimed_identity` from `session.owner_identity` internally — no caller-supplied identity string parameter SHALL exist |
| Template substitution | Prevented structurally by AESIC-REQ-008: AES SHALL derive `template_ref`/`template_version` from the same `Session` object it reads `owner_identity` from — no independent caller-supplied string parameters SHALL exist |
| Registry poisoning | Out of AES's own control surface — a future Registry-implementation phase's write-path security concern; AES itself SHALL NEVER write Declarations, closing this attack-vector class entirely |
| Cross-session reuse | Prevented structurally: the AER SHALL be keyed by `package_id` (§8.2), unique per readiness package per session; a readiness package's `authority_evaluation_ref` SHALL only be populatable with the AER produced for that specific `package_id`; the Coordinator's own package-identity validation (`_validate_authorization_applicability`, unmodified) SHALL be extended by a future implementation to check AER/package binding |
| Stale outcomes | Only the AER (Stage-2-only) SHALL carry a `citation_text` eligible for CHGR consumption (§14.1); Stage 1 outcomes SHALL NEVER be persisted and therefore SHALL have no `record_id`/`record_digest` a readiness package could reference |
| Duplicate publication | Governed entirely by the Coordinator's own existing idempotency marker (PEC-001, unmodified), unaffected by AES |
| Replay attacks (reusing an old, valid AER to publish twice) | Prevented by the Coordinator's own, already-existing replay protection (`_check_replay`, `is_published(package_id)`), entirely independent of AES |
| Authority confusion (mistaking a disclosed evaluation for a granted authorization) | Enforced by §14.2's explicit prohibition and every component's own naming discipline — no field, method, or component name introduced by this contract could be mistaken for an authorization primitive |

**AESIC-REQ-093.** A future implementation phase SHALL NOT weaken any
mitigation in §15's table without a governed contract amendment (§19).

---

## 16. Observability

**AESIC-REQ-094.** AES SHALL log every resolution attempt (success or
failure), every Registry call (success or failure, with the specific
exception class per §13), and every `evaluate()` invocation's outcome
(`ELIGIBLE`/`INELIGIBLE`/`INDETERMINATE`) at both stages.

**AESIC-REQ-095.** Every observability surface (logs, traces,
diagnostics, inspection, audit) SHALL be read-only; none SHALL be a
control surface; none SHALL expose a mechanism by which an observer could
cause AES to skip resolution, skip evaluation, or fabricate an outcome.

**AESIC-REQ-096.** `package_id` SHALL be the primary cross-component
correlation key. AES's own `record_id` SHALL be secondary, scoped to the
AER itself.

**AESIC-REQ-097.** A future implementation SHALL provide a read-only
diagnostic query surface over the AER store (mirroring `pcae runtime
inspect`'s read-only posture), sufficient to answer at minimum: "show
every Stage 2 evaluation for package X" and "show every `INELIGIBLE`
outcome in the last N attempts" — without any additional derived index
beyond the AER's own shape (§8.5).

**AESIC-REQ-098 (evaluation identifiers, resolving Phase 147J §18/§20.4 item 3).**
Each AES invocation SHALL carry its own `evaluation_id`, distinct from
`package_id` and `record_id`, letting a Stage 1 and its corresponding
later Stage 2 be correlated without conflating them. `evaluation_id`
SHALL be present on every AER (§8.5) and SHOULD be surfaced (though never
persisted, per §9.1) alongside any Stage 1 advisory display.

**AESIC-REQ-099.** A future 147K+ implementation phase SHALL require
every Stage 2 attempt, successful or refused, to be durably recorded, not
only successful ones — mirroring the Publication Coordinator's own
"every attempt — accepted or refused — is durably recorded" discipline.

**AESIC-REQ-100.** `AuthorityRegistryUnavailableError` and
`AuthorityRegistryCorruptError` SHALL remain distinguishable in whatever
logging AES performs (§7.5, §13).

---

## 17. Non-Functional Requirements

**AESIC-REQ-101 (determinism).** `evaluate_stage_1` and `evaluate_stage_2`
SHALL produce identical `AuthorityEvaluationOutcome` values for identical
inputs and identical underlying Registry/template state, exactly matching
`evaluate()`'s own AEMIC-REQ-074/075 guarantee, extended unmodified
through Resolution and AES.

**AESIC-REQ-102 (performance expectations).** AES SHALL perform at most
one Decision Template read and at most one Registry call per stage per
evaluation attempt (§6.9) — no future implementation SHALL introduce
unbounded or N+1-style resolution behavior.

**AESIC-REQ-103 (restart tolerance).** Every restart point named in §11.2
SHALL have a defined, safe resumption; no future implementation SHALL
introduce a restart point without an entry in that matrix.

**AESIC-REQ-104 (idempotency).** §5.11 and §12.4's idempotency guarantees
SHALL hold under concurrent duplicate Stage 2 attempts for the same
`package_id` (§5.9's `O_CREAT | O_EXCL` mechanism).

**AESIC-REQ-105 (availability assumptions).** AES SHALL assume the
Registry MAY be unavailable at any call and SHALL handle that condition
per §7.7/§13, never assuming Registry availability as a precondition of
correct AES behavior.

**AESIC-REQ-106 (offline behavior).** AES SHALL require no network
access; Registry and AER-store I/O SHALL be local/filesystem-equivalent
operations only, consistent with this codebase's existing governance
storage precedents.

**AESIC-REQ-107 (immutability).** Every persisted artifact this contract
names (the AER, §8.3; Registry Declarations, §7.6) SHALL be immutable
once written.

**AESIC-REQ-108 (forward compatibility).** The AER's shape (§8.5) SHALL
be additive-extensible — a future Evaluation Persistence Contract MAY add
new optional fields without breaking this contract's own requirements,
provided no existing field's meaning is narrowed.

**AESIC-REQ-109 (backward compatibility).** A `PublicationReadinessPackage`
built without an `authority_evaluation_ref` field SHALL remain valid — the
field SHALL be optional, defaulting to `None`, so no existing caller of
`PublicationHandoff.build_package` breaks (Phase 147J §14).

**AESIC-REQ-110 (testability).** Every requirement in this contract SHALL
be independently testable against either (a) the unmodified,
already-verified `pcae.authority_evaluation` package, or (b) a future
implementation of AES/Resolution/Registry/AER-store built against this
contract — no requirement SHALL depend on untestable, purely subjective
criteria.

---

## 18. Verification Requirements

**AESIC-REQ-111.** A future Independent Contract Verification phase
(147L, per §20 below) SHALL, at minimum, independently re-derive and
attempt to falsify:

1. **Architectural invariants** — every invariant in Phase 147J §3's
   table, cross-checked against this contract's §5–§9 requirements for
   drift.
2. **Lifecycle sequencing** — §9's stage ordering, ownership, and
   supersession rules (AESIC-REQ-062–073).
3. **Replay semantics** — §11's restart matrix, checked for any restart
   point Phase 147J or this contract may have omitted (AESIC-REQ-075–077).
4. **Persistence model** — §12's persistent/transient/recomputed/immutable
   classification, checked for internal consistency (AESIC-REQ-078–086).
5. **Registry boundaries** — §7's abstract obligations, checked against
   AEM-001 §4.5 and AEMIC-001 §11 for any unintended narrowing or
   widening (AESIC-REQ-040–050).
6. **Evaluator purity** — confirmation that no requirement in this
   contract, if implemented literally, would require `evaluate()` itself
   to change (AESIC-REQ-005, §4).
7. **Disclosure-only semantics** — §14's consumption matrix and §14.2's
   explicit prohibitions, checked against every named consumer
   (AESIC-REQ-089–091).
8. **AER immutability** — §8.3/§12.4, checked for any requirement that
   would implicitly require an AER update path (AESIC-REQ-054, 082).
9. **Failure ownership** — §13's matrix, checked for completeness against
   every error type named in §5.7, §6.4, and §7.5 (AESIC-REQ-087–088).
10. **Security invariants** — §15's mitigation table, checked for any
    threat named in Phase 147J §16 this contract may have left
    unaddressed (AESIC-REQ-092–093).

**AESIC-REQ-112.** The verification phase SHALL remain verification-only
— it SHALL make no implementation change and SHALL NOT itself amend this
contract; any inconsistency or unsatisfied requirement it identifies
SHALL be disposed of through a subsequent, separately-authorized contract
repair phase (mirroring AEMIC-001 §21's own Amendment Contract
discipline).

---

## 19. Compatibility

**AESIC-REQ-113.** This contract SHALL require zero amendments to
AEM-001, AEMIC-001, IWC-001, IWPC-001, PEC-001, or CHGR-001 — confirming
Phase 147J §1/§22's own determination unchanged. Every AESIC-REQ in this
contract SHALL be satisfiable without modifying any provision those six
contracts already freeze.

**AESIC-REQ-114.** Where this contract's requirements interact with a
provision of AEM-001, AEMIC-001, IWC-001, IWPC-001, PEC-001, or CHGR-001,
this contract SHALL cite the interacting provision by requirement ID and
SHALL demonstrate compatibility, never redefinition (§0's own citation
discipline).

**AESIC-REQ-115.** Any future revision of this contract SHALL proceed
only through a governed superseding contract revision, following the same
in-place-minor-revision or full-supersession discipline AEM-001, AEMIC-001,
IWC-001, IWPC-001, PEC-001, and CHGR-001 already use for their own
amendments. No implementing phase SHALL revise this contract through its
own discretion.

---

## 20. No-Go Requirements

**AESIC-REQ-116.** This contract's freeze (Phase 147K) SHALL NOT itself
implement: the Authority Evaluation Service; the Decision Template
Resolution capability; a concrete Authority Registry; Authority Evaluation
Record persistence; or any replay mechanism. Phase 147K SHALL NOT modify
`src/pcae/**`, any schema file, any test file, `.pcae/policy.toml`,
Interactive Workflow code, Publication Coordinator code, CHGR construction
code, the evaluator implementation, any CLI command, or any runtime
plugin.

**AESIC-REQ-117.** This contract's own freeze SHALL NOT, by itself,
authorize a future implementation phase to begin — implementation
requires separate, explicit human authorization following this contract's
own Independent Contract Verification (§18, §21).

---

## 21. Requirement / Test Matrix

Every `AESIC-REQ-###` introduced above is listed here with its
introducing section and its primary falsifiability anchor. This matrix is
the authoritative enumeration; narrative sections 1–20 restate these
requirements for readability but this table governs in any conflict.

| Requirement | Section | Falsifiability anchor |
|---|---|---|
| AESIC-REQ-001 – 002 | §2 | Scope boundary — checked against Phase 147J §2/§18/§20.2/§20.3 |
| AESIC-REQ-003 | §3 | Terminology — checked for internal consistency across all sections |
| AESIC-REQ-004 | §4 | Component count/boundary — checked against Phase 147J §15.2 |
| AESIC-REQ-005 – 026 | §5 | AES specification — checked against Phase 147J §5 and, once implemented, against `AuthorityEvaluationService`'s actual public interface |
| AESIC-REQ-027 – 039 | §6 | Resolution specification — checked against Phase 147J §6 |
| AESIC-REQ-040 – 050 | §7 | Registry contract — checked against AEM-001 §4.5, AEMIC-001 §11, `registry.py:17-24` (unmodified) |
| AESIC-REQ-051 – 061 | §8 | AER specification — checked against Phase 147J §10 |
| AESIC-REQ-062 – 073 | §9 | Lifecycle/sequencing — checked against Phase 147J §8, §9 |
| AESIC-REQ-074 | §10 | Cross-reference integrity — checked for contradiction with §7 |
| AESIC-REQ-075 – 077 | §11 | Replay contract — checked against Phase 147J §11 |
| AESIC-REQ-078 – 086 | §12 | Persistence contract — checked against Phase 147J §10, `storage.py` precedents |
| AESIC-REQ-087 – 088 | §13 | Failure ownership — checked against Phase 147J §12 |
| AESIC-REQ-089 – 091 | §14 | Outcome consumption — checked against Phase 147J §13 |
| AESIC-REQ-092 – 093 | §15 | Security requirements — checked against Phase 147J §16 |
| AESIC-REQ-094 – 100 | §16 | Observability — checked against Phase 147J §17 |
| AESIC-REQ-101 – 110 | §17 | Non-functional requirements — checked against Phase 147J's cross-cutting discipline (§5.6–§5.9, §11) |
| AESIC-REQ-111 – 112 | §18 | Verification requirements — checked against this contract's own completeness |
| AESIC-REQ-113 – 115 | §19 | Compatibility — checked against AEM-001/AEMIC-001/IWC-001/IWPC-001/PEC-001/CHGR-001 (all unmodified) |
| AESIC-REQ-116 – 117 | §20 | No-Go boundary — checked against `git status --short` at Phase 147K's finalization |

**AESIC-REQ count: 117, AESIC-REQ-001 through AESIC-REQ-117, sequential,
no gaps, no reuse.**

---

## 22. No-Go Boundary Confirmation

Per the authorizing prompt's explicit No-Go Boundary: `src/pcae/**` was
not modified. No schema was modified. No contract was amended (AEM-001,
AEMIC-001, IWC-001, IWPC-001, PEC-001, CHGR-001 all remain byte-for-byte
unchanged). No test was modified. No Authority Evaluation Service was
implemented. No Registry was implemented. No replay mechanism was
implemented. No persistence mechanism was implemented. No lifecycle code
was changed. Runtime was not modified. No CLI command was added. No
plugin was added. CHGR construction code was not modified. Publication
code was not modified. Interactive Workflow code was not modified. Only
this contract document plus ordinary task/phase bookkeeping files changed
throughout this phase, confirmed by `git status --short` at finalization.

---

## 23. Overall Verdict

**AUTHORITY EVALUATION INTEGRATION CONTRACT FROZEN.**

Every element required for a complete freeze is present: a complete
normative contract (§0–§21), a complete invariant set (§5.13, §14.2,
§15.1-equivalent restated in §5.13/§9.2/§14), a complete lifecycle
specification (§9), a complete replay specification (§11), a complete
persistence specification (§12), complete failure ownership (§13),
complete security requirements (§15), and complete verification
requirements (§18). No architectural decision from Phase 147J was left
unfrozen; every item Phase 147J §18/§20.2/§20.3/§20.4 explicitly deferred
to this Contract Freeze has been resolved (§5.2's `Session`-object
construction rule per AESIC-REQ-008; §8.6's mandatory-when-present
`stage_1_outcome_ref` rule per AESIC-REQ-057; §16's `evaluation_id`
definition per AESIC-REQ-098).

---

## 24. Recommended Next Phase

**147L — Authority Evaluation Integration Contract Independent
Verification.** That phase shall independently re-derive and verify the
complete AESIC-001 contract against the architecture from Phase 147J and
the existing PCAE governance contracts (AEM-001, AEMIC-001, IWC-001,
IWPC-001, PEC-001, CHGR-001). It shall remain verification-only, identify
any inconsistencies or unsatisfied requirements, and make no
implementation change.

**This recommendation is not an authorization.**

---

**End of AESIC-001 v1.0.**
