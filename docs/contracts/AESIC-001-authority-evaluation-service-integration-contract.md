# AESIC-001 v1.3 — Authority Evaluation Service Integration Contract

## Contract identity and status

**Contract:** AESIC-001
**Version:** 1.3
**Status:** FROZEN
**Frozen by:** Phase 147K — Authority Evaluation Integration Contract
Freeze
**Repaired by:** Phase 147L.1 — AESIC-001 Contract Repair (in-place minor
revision correcting Finding 1 and Finding 2 from Phase 147L's independent
verification; see §25); further repaired by Phase 147L.3 — AESIC-001
Final Contract Repair (in-place minor revision correcting the two
Non-Blocking findings from Phase 147L.2's independent verification of the
v1.1 repair — the `stage_1_outcome_ref` interface-channel gap and the
canonical pointer's tamper-evidence gap; see §29); further repaired by
Phase 147L.5 — AESIC-001 Stage 1 Idempotency and Restart-Matrix Contract
Repair (in-place minor revision correcting Finding A and Finding B from
Phase 147L.4's independent verification of the v1.2 repair — the
idempotency-no-op-vs-mandatory-`stage_1_outcome_ref` contradiction and the
missing AER-commit/pointer-write restart-matrix row; see §33)
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
IWPC-001's, and CHGR-001's own amendment discipline (§19 below). This
repair follows AEMIC-001 §25/§26's own precedent exactly: every
requirement number issued in v1.0 (`AESIC-REQ-001`–`AESIC-REQ-117`) is
preserved unchanged in identity; a small number of those entries have
their **text** repaired in place where Phase 147L's findings showed that
text to be internally self-contradictory (never their requirement
number), and four new requirements (`AESIC-REQ-118`–`121`) are introduced,
placed in the sections they most directly extend, continuing the sequence
without reuse or renumbering of anything that came before. Phase 147L.3
(v1.2) repeats this same discipline: every requirement number issued
through v1.1 (`AESIC-REQ-001`–`AESIC-REQ-121`) is preserved unchanged in
identity; a small number of those entries have their text repaired in
place where Phase 147L.2's independent verification showed that text to
leave an unaddressed mechanism-availability or tamper-evidence gap (never
their requirement number), and seven new requirements
(`AESIC-REQ-122`–`128`) are introduced, continuing the sequence without
reuse or renumbering of anything that came before. Phase 147L.5 (v1.3)
repeats this same discipline a third time: every requirement number
issued through v1.2 (`AESIC-REQ-001`–`AESIC-REQ-128`) is preserved
unchanged in identity; a small number of those entries have their text
repaired in place where Phase 147L.4's independent verification showed
that text to leave an unaddressed idempotency/evidence-retention
contradiction or a restart-matrix completeness gap (never their
requirement number), and three new requirements (`AESIC-REQ-129`–`131`)
are introduced, continuing the sequence without reuse or renumbering of
anything that came before.

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
| **`Stage1EvaluationResult`** | A new, AESIC-001-owned, immutable value type (new, Phase 147L.3), the return type of `evaluate_stage_1` and the type of `evaluate_stage_2`'s new, optional `stage_1_result` parameter (§5.2.1). |
| **`pointer_digest`** | The digest field the canonical pointer index (§12.1) carries over its own other content, new Phase 147L.3, mirroring `record_digest`'s own role for the AER (§8.4). |

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

**AESIC-REQ-007 (repaired, Phase 147L.3 — Finding §3.1).** AES SHALL
expose exactly the following public interface shape (types illustrative;
concrete typing is an implementation decision within this shape):

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
    ) -> Stage1EvaluationResult: ...
        # advisory only; never persisted; caller decides how/whether to surface it

    def evaluate_stage_2(
        self,
        *,
        session: Session,
        package_id: str,
        stage_1_result: Optional[Stage1EvaluationResult] = None,
    ) -> AuthorityEvaluationRecord: ...
        # fresh resolution + evaluation; persists and returns an immutable AER
        # stage_1_result, if supplied, SHALL be the unmodified return value of
        # a prior evaluate_stage_1(session=session) call held in the caller's
        # own memory (§5.2.1, AESIC-REQ-122/123) — never fabricated, never
        # sourced from a different session
```

**Repaired-signature rationale (Phase 147L.3).** Phase 147L.2 §3.1
independently found that AESIC-REQ-118's embedded-copy shape (§8.6) had no
defined channel by which the specific, already-computed Stage 1 outcome a
caller received from `evaluate_stage_1` could ever reach the later,
separate `evaluate_stage_2` call that is supposed to embed it —
`evaluate_stage_2`'s v1.1 signature closed every candidate channel
(parameter, `Session`, AES-internal state). This repair opens exactly one
new, explicit, optional channel: a `stage_1_result` parameter on
`evaluate_stage_2` whose type (`Stage1EvaluationResult`, new,
AESIC-REQ-122) is itself the unmodified return type of `evaluate_stage_1`
— the caller supplies back, verbatim, the same object AES already gave
it. No bare `claimed_identity`/`template_ref`/`template_version` string
parameter is introduced (AESIC-REQ-008's hardening intent, §5.2 below,
remains fully intact — see §5.2.1's preservation note), and no new
mandatory input is added — `stage_1_result` defaults to `None` and every
existing caller that never supplies it observes byte-for-byte unchanged
behavior (AESIC-REQ-109's backward-compatibility discipline, extended
here by the same logic).

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
§13, never a bare `Exception` and never a type not named in §13's matrix
(extended, Phase 147L.3, to include AESIC-REQ-124's `Stage1HandoffInvalidError`
and AESIC-REQ-127's `CanonicalPointerCorruptError`; extended, Phase
147L.5, to include AESIC-REQ-131's `CanonicalPointerUpdateFailedError` —
all three remain within "the error taxonomy of §13," not an exception to
this requirement).

### 5.2.1 Stage 1 result handoff (new, Phase 147L.3 — closes Finding §3.1)

**AESIC-REQ-122 (new, Phase 147L.3).** `Stage1EvaluationResult` SHALL be
an immutable, AESIC-001-owned value type — never an AEMIC-001 type, never
a modification of `AuthorityEvaluationOutcome`'s own frozen shape (AEMIC-001
§6, unmodified) — carrying exactly three fields:

1. `outcome` — the unmodified `AuthorityEvaluationOutcome` `evaluate_stage_1`
   itself computed (AEMIC-001 §6 shape, already carrying `evaluated_at`
   verbatim, AEMIC-REQ-021 — no separate `evaluated_at` field is needed on
   `Stage1EvaluationResult` itself).
2. `evaluation_id` — this specific Stage 1 invocation's own `evaluation_id`
   (§16.8, AESIC-REQ-098), previously computed by AES for every invocation
   but, before this repair, never actually returned to the caller through
   any channel `evaluate_stage_1`'s v1.0/v1.1 signature exposed. This
   repair closes that pre-existing surfacing gap as a necessary
   precondition of closing Finding §3.1: a caller cannot hand back an
   `evaluation_id` it was never given.
3. `session_id` — verbatim copy of `session.session_id` (the `Session`
   object's own already-frozen identity field, IWC-001, unmodified,
   independently confirmed to exist and to be already populated at
   `PublicationHandoff.build_package`'s call site — see §12 below) at the
   moment `evaluate_stage_1` was invoked. This is the field that makes
   session-binding validation (AESIC-REQ-123) possible without any
   Stage-1-only persistence: it is carried in-memory, inside the very
   object the caller is required to hand back, never looked up from a
   store.

**AESIC-REQ-123 (new, Phase 147L.3).** When `stage_1_result` is supplied
(non-`None`) to `evaluate_stage_2`, AES SHALL, before using it for
anything, validate it against the `session`/`package_id` of that same
`evaluate_stage_2` call, in this order, refusing (raising
AESIC-REQ-124's `Stage1HandoffInvalidError`, never silently ignoring or
silently proceeding) on the first check that fails:

1. **Structural validity.** `stage_1_result` SHALL be a well-formed
   `Stage1EvaluationResult` (all three AESIC-REQ-122 fields present, of
   the correct type, `outcome` itself a well-formed `AuthorityEvaluationOutcome`
   per AEMIC-001's own construction invariants, AEMIC-REQ-022/023). Failing
   this check classifies as `reason=MALFORMED`.
2. **Session binding.** `stage_1_result.session_id` SHALL equal
   `session.session_id` (the same `Session` object `evaluate_stage_2` was
   given). Failing this check classifies as `reason=SESSION_MISMATCH` —
   this is the check that closes "Stage 1 outcome belongs to another
   Session" (§13 of the authorizing prompt).
3. **Identity binding.** `stage_1_result.outcome.claimed_identity` SHALL
   equal `session.owner_identity` (the same value AES itself would derive
   for this `evaluate_stage_2` call, AESIC-REQ-008). Failing this check
   classifies as `reason=IDENTITY_MISMATCH`.
4. **Decision-template binding.** `stage_1_result.outcome.template_ref`
   and `stage_1_result.outcome.template_version` SHALL each equal the
   corresponding value AES itself would derive from `session` for this
   call (AESIC-REQ-008). Failing this check classifies as
   `reason=TEMPLATE_MISMATCH`.

A `stage_1_result` that passes all four checks SHALL be accepted:
`stage_1_result.outcome` and `stage_1_result.evaluation_id` are then the
exact values `stage_1_outcome_ref`'s three embedded sub-fields
(AESIC-REQ-118) are populated from (`outcome`, `evaluation_id`, and
`evaluated_at` read from `outcome.evaluated_at`). Staleness alone (an old
`outcome.evaluated_at`) is never a validation failure — AESIC-REQ-065
already establishes Stage 1 staleness as expected, disclosed behavior;
these four checks validate **provenance** (whose evaluation this is), not
**freshness**.

**AESIC-REQ-124 (new, Phase 147L.3).** `Stage1HandoffInvalidError` SHALL
be a single new exception type, carrying a closed, four-member `reason`
enumeration exactly matching AESIC-REQ-123's four checks
(`MALFORMED`, `SESSION_MISMATCH`, `IDENTITY_MISMATCH`,
`TEMPLATE_MISMATCH`) — mirroring `EvaluationResult`'s own closed-enumeration
discipline (AEMIC-REQ-024/026), never represented as a bare `str`. AES
SHALL raise it, and `evaluate_stage_2` SHALL produce **no AER** and
**no side effect** (no Registry call, no Resolution attempt, no store
write) when it is raised — validation of a supplied `stage_1_result`
SHALL complete, pass or fail, before any other Stage 2 work begins. This
is a fail-closed design (mirrors PCAE's own "Fail-closed" runtime
principle): a caller-supplied Stage 1 handoff that cannot be verified as
belonging to this session, identity, and template is treated as
untrusted input, never as best-effort advisory content to embed anyway.

**AESIC-REQ-125 (new, Phase 147L.3 — Stage 1 absence semantics).** When
`stage_1_result` is `None` (the default, and the only value any
pre-147L.3 caller can ever pass), `evaluate_stage_2` SHALL proceed exactly
as it did before this repair: `stage_1_outcome_ref` (§8.6) SHALL be
absent from the resulting AER, and no `Stage1HandoffInvalidError` SHALL be
raised — absence of a Stage 1 result is never itself an error (AESIC-REQ-057's
own "always-optional-otherwise" framing, unchanged). `None` (absent) and
a structurally-invalid non-`None` value (`reason=MALFORMED`) are therefore
always distinguishable at the API level — a Python `None` can never
satisfy AESIC-REQ-123 check 1's "well-formed `Stage1EvaluationResult`"
test, and a non-`None` value can never be silently treated as absent.
This is the mandatory choice this contract makes for the question posed
by the authorizing prompt's §6: Stage 2 proceeds with an explicit
`stage_1_result = None` when no Stage 1 evaluation preceded it; it never
refuses for that reason alone, consistent with AESIC-REQ-062/063 (§9.1,
unchanged) already permitting a caller to invoke Stage 2 without ever
having invoked Stage 1.

**AESIC-REQ-128 (new, Phase 147L.3 — complete Stage 2 invocation
contract, closes the authorizing prompt's §5 Public Interface Closure
demand).** The complete set of `evaluate_stage_2` inputs, their source,
and their validator is exactly:

| Input | Supplied directly? | Derived internally? | Loaded from governed state? | Validated by |
|---|---|---|---|---|
| `session` (the `Session` object) | Yes — the only object-shaped direct parameter | `claimed_identity`, `template_ref`, `template_version` derived from it internally (AESIC-REQ-008) | No | AES itself, via AESIC-REQ-008's derivation rule (structural — no separate validation step) |
| `package_id` | Yes | No | No | AES's own idempotency/keying logic (§12.1) — not a content-validity check, a keying operation |
| `registry` / `aer_store` collaborators | No — constructor-injected once (AESIC-REQ-015) | No | No | Construction-time only; not a per-call input |
| `stage_1_result` (optional) | Yes — the only other direct, optional parameter | No — the embedded copy is never recomputed by AES; it is validated-and-copied, never re-derived | No — never loaded from a store, because none exists (AESIC-REQ-064/080, unaffected) | AES itself, via AESIC-REQ-123's four-check sequence, raising AESIC-REQ-124's `Stage1HandoffInvalidError` on the first failing check |
| Decision Template document | No | No | Yes — loaded fresh from the Registry/template store every call (§6.5) | Resolution, per §6.4's failure taxonomy (unchanged) |
| `EligibleAuthorityDeclaration` | No | No | Yes — loaded fresh via `AuthorityRegistry.resolve()` every call (§7) | Registry, per §7.5's failure taxonomy (unchanged) |

No implementer choice remains among: adding an ungoverned extra argument
(closed — the only two direct parameters besides `session`/`package_id`
are exactly `stage_1_result`, nothing else); loading arbitrary external
files (closed — Decision Template/Declaration loading is exhaustively
governed by §6/§7, unchanged); reading ambient process state (closed —
AESIC-REQ-017's statelessness requirement, unaffected by this repair);
resolving Stage 1 through Registry (closed — the Registry's one method,
AESIC-REQ-040, has no Stage-1-outcome-shaped return value and this repair
adds none); or reconstructing Stage 1 from incomplete `Session` data
(closed — AESIC-REQ-060 still forbids writing any Stage 1 outcome onto
`Session`, so no such reconstruction is possible even in principle).
Exactly one ownership and transport model is frozen: `stage_1_result` is a
same-process, same-call-chain, caller-retained parameter, validated by AES
against the concurrently-supplied `session`, never a durable artifact and
never a hidden channel.

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

**AESIC-REQ-012 (repaired, Phase 147L.3 — Finding §3.1).** AES's inputs
SHALL be exactly: the injected `registry` and `aer_store` collaborators
(construction-time, §5.6); and, per call, the `Session` object, (Stage 2
only) `package_id`, and (Stage 2 only, optional) `stage_1_result`
(§5.2.1, AESIC-REQ-122/123). AES SHALL accept no other input. This
repair adds exactly one new, optional, per-call input to `evaluate_stage_2`
and none to `evaluate_stage_1` or to AES's construction-time collaborators
— every other input surface this requirement names is unchanged from
v1.1.

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
- **(New, Phase 147L.3.)** An invalid caller-supplied `stage_1_result`
  SHALL be raised by AES itself as `Stage1HandoffInvalidError`
  (AESIC-REQ-124) — this is not a translated collaborator failure (neither
  the Registry nor Resolution nor `evaluate()` is ever invoked before this
  check completes, AESIC-REQ-124), but an AES-owned input-validation
  refusal, raised before any collaborator is called.
- **(New, Phase 147L.3.)** A canonical-pointer integrity failure detected
  at read time SHALL be raised by AES as `CanonicalPointerCorruptError`
  (AESIC-REQ-127) — an AES-owned condition analogous to
  `AuthorityRegistryCorruptError`'s own "storage answered but the record
  is structurally malformed" framing (§7.5), applied to the pointer
  artifact instead of a Registry Declaration.

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

**AESIC-REQ-019 (repaired, Phase 147L.1 — Finding 2).** Stage 2's AER
write SHALL use the same `O_CREAT | O_EXCL` idempotency-marker pattern
`PublicationRecordStore.commit_publication` already uses
(`storage.py:8-16`), applied to the AER's own compound storage key
`(package_id, evaluation_id)` (AESIC-REQ-119, §12.1) — not to `package_id`
alone. A collision at this exclusive-create step is therefore only
reachable if two Stage 2 attempts somehow presented the identical
`evaluation_id`, an outcome AESIC-REQ-098's own per-invocation uniqueness
guarantee already excludes by construction; this requirement's exclusive-
create check accordingly now serves as a defense-in-depth corruption
guard on that uniqueness invariant, never as the mechanism that decides
whether a duplicate Stage 2 *attempt* (as opposed to a duplicate storage
*write*) is idempotent — that decision is AESIC-REQ-023's own, made
before any write is attempted (§12.3, AESIC-REQ-121).

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

**AESIC-REQ-023 (repaired, Phase 147L.1 — Finding 2; repaired, Phase
147L.5 — Finding A).** Stage 2 SHALL be idempotent per `package_id`: for a
second Stage 2 attempt for the same `package_id`, AES SHALL always perform
a fresh resolution and evaluation first (§6.5, never short-circuited)
and, if a `stage_1_result` was supplied, validate it first per
AESIC-REQ-123 (any validation failure raises `Stage1HandoffInvalidError`
before this comparison is ever reached, unaffected by this repair), then
compare the freshly-computed result — **which, as of this repair,
includes whether a validated `stage_1_result` was supplied and, if so,
its Stage 1 evidence content, per the extended equality procedure of
AESIC-REQ-121/129 (§12.3)** — against `package_id`'s current canonical
AER, and:

(a) if the freshly-computed result is **unchanged** relative to the
    current canonical AER — **which, as of this repair, requires the two
    to also be Stage-1-evidence-equivalent per AESIC-REQ-129, not only
    citation/outcome-equivalent** — return that already-persisted AER
    unchanged — no new AER SHALL be written and the canonical pointer
    (AESIC-REQ-119) SHALL NOT be advanced; or

(b) if the freshly-computed result has **changed** (e.g. Registry or
    Decision Template evolution between attempts, **or, as of this
    repair, a validated `stage_1_result` supplied on this attempt that is
    not Stage-1-evidence-equivalent to the current canonical AER's own
    `stage_1_outcome_ref` per AESIC-REQ-129 — including the case where the
    canonical AER carries no `stage_1_outcome_ref` at all and this attempt
    supplies a valid one**), persist a genuinely new, distinct AER under a
    fresh compound storage key `(package_id, evaluation_id)`
    (AESIC-REQ-119) and then atomically advance `package_id`'s own
    canonical pointer to reference this new AER (AESIC-REQ-119/120) —
    this is the **supersession** this requirement's original text already
    named; it is never a refusal, and the prior AER is never overwritten,
    mutated, or deleted (AESIC-REQ-054/082, unaffected).

Either way, no attempt SHALL be silently overwritten and no attempt
SHALL be silently dropped: (a) is a disclosed no-op returning existing,
already-disclosed content — **now guaranteed, by construction, to also
already carry whatever Stage 1 evidence this attempt supplied, since (a)
is reachable only when that evidence is already Stage-1-evidence-equivalent
to what the returned AER carries (AESIC-REQ-129), closing Finding A**; (b)
is a disclosed, newly-persisted, independently-retrievable record whose
own `stage_1_outcome_ref` reflects this attempt's own supplied evidence
exactly, per AESIC-REQ-057/118.

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

**AESIC-REQ-053 (repaired, Phase 147L.1 — Finding 2).** Each AER SHALL be
keyed for **storage** (the write/exclusive-create key, AESIC-REQ-019) by
the compound key `(package_id, evaluation_id)`, and keyed for
**canonical lookup** (the key any ordinary consumer uses to ask "what is
the current AER for this package") by `package_id` alone, via the
canonical pointer index of AESIC-REQ-119 (§12.1). This two-tier keying
resolves Finding 2 (Phase 147L §14): `package_id` remains, exactly as
this requirement's original text stated, the key every existing consumer
(§14.1, Readiness, Publication, CHGR) already uses and continues to use
unchanged; `evaluation_id` is the additional, previously-unstated
dimension needed for a *superseding* Stage 2 attempt (AESIC-REQ-023(b))
to persist a genuinely new record without violating either the AER's own
immutability (AESIC-REQ-054/082) or `package_id`'s own role as the
lookup convenience key this requirement always named.

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

**AESIC-REQ-056 (repaired, Phase 147L.1 — Finding 1).** The AER SHALL
contain, at minimum: `record_id`, `record_digest`, `record_family` (fixed
value `"authority_evaluation_record"`), `package_id`, `evaluation_id`
(§16.8, this AER's own Stage 2 `evaluation_id`), `stage` (fixed value
`"stage_2"`), the wrapped `AuthorityEvaluationOutcome` (unmodified shape,
per AEMIC-001 §6), an `evaluated_at` timestamp, and an optional
`stage_1_outcome_ref` (§8.6, an **embedded copy**, not a pointer — see
§8.6's repaired text for the exact shape). This contract defines no JSON
Schema file for the AER — the concrete schema is future Evaluation
Persistence Contract work (§16 item 4).

### 8.6 Stage 1/Stage 2 relationship

**AESIC-REQ-057 (repaired, Phase 147L.1 — Finding 1; clarified, Phase
147L.3 — Finding §3.1; clarified, Phase 147L.5 — Finding A).** The AER
MUST carry a `stage_1_outcome_ref` field whenever the caller supplies AES
a valid `stage_1_result` for the same `evaluate_stage_2` call (§5.2.1,
AESIC-REQ-123 — this is the operative, mechanically-checkable meaning, as
of this repair, of "a Stage 1 evaluation for the same `package_id`/session
preceded Stage 2"), so that a disagreement between the two is
structurally visible (both outcomes retrievable, never one silently
discarded). **This guarantee holds for the AER Stage 2 actually returns on
every attempt, including an idempotent no-op** (AESIC-REQ-023(a)): Phase
147L.4's Finding A independently identified that, before this repair, the
idempotency comparison (AESIC-REQ-121) did not account for Stage 1
evidence, so a no-op could return an existing canonical AER lacking this
attempt's own supplied evidence, silently violating this requirement's
"whenever... supplied" clause; AESIC-REQ-121/129 (repaired/new, Phase
147L.5, §12.1) close that gap by making Stage-1-evidence-equivalence
(AESIC-REQ-129) a precondition of the no-op classification itself — a
no-op is now reachable only when the returned AER's own
`stage_1_outcome_ref` already satisfies this requirement for the currently
supplied evidence; any attempt that would violate it is reclassified
"changed" and superseded (AESIC-REQ-023(b)) instead. Resolving Phase 147J §20.4
item 2's open question: `stage_1_outcome_ref` SHALL be
**mandatory-when-a-valid-`stage_1_result`-is-supplied,
always-optional-otherwise** — never a strict, unconditional-presence
field, since Stage 1 itself is never guaranteed to precede every Stage 2
attempt, and a caller MAY invoke Stage 2 without ever having invoked Stage
1, or without retaining/re-supplying Stage 1's result even when it did
(§8.1's ownership rule; §9.6 below, AESIC-REQ-125). This clarification
narrows no prior behavior: every `stage_1_result` that would have made
"a Stage 1 evaluation... preceded" true under the v1.1 text is exactly a
`stage_1_result` that passes AESIC-REQ-123's validation and is therefore
embedded under this text too.

**Repaired content and retrieval semantics (AESIC-REQ-118, §8.6, Phase
147L.1).** Despite its `_ref` suffix — preserved unchanged across this
repair for field-name stability, deliberately, not by oversight —
`stage_1_outcome_ref` SHALL NOT be a pointer, identifier, or lookup key
into any separately-persisted Stage 1 artifact; no such artifact exists or
may ever exist (AESIC-REQ-064, AESIC-REQ-080, unaffected by this repair —
Stage 1's outcome SHALL still never be persisted as its own,
independently-addressable record, with its own `record_id`,
`record_digest`, or store entry). Instead, `stage_1_outcome_ref` SHALL be
an **inline, verbatim, byte-for-byte embedded copy**, written directly
into the AER's own document body at Stage 2 persistence time, containing
exactly:

1. `outcome` — Stage 1's own `AuthorityEvaluationOutcome`, in the same
   unmodified AEMIC-001 §6 shape the AER's own top-level outcome field
   uses (§8.5) — never summarized, truncated, or re-derived.
2. `evaluation_id` — Stage 1's own `evaluation_id` (§16.8), distinct from
   the AER's own top-level `evaluation_id`, closing Phase 147L's Finding 4
   (the two `evaluation_id` values are never the same value: the embedded
   one identifies the Stage 1 invocation being copied, the top-level one
   identifies the Stage 2 invocation producing this AER).
3. `evaluated_at` — Stage 1's own timestamp, copied verbatim.

This resolves Finding 1 (Phase 147L §14) without weakening
AESIC-REQ-064/080: "Stage 1's outcome SHALL NOT be persisted" continues to
mean, exactly as it always meant, that no Stage 1 outcome ever exists as
its **own** separately-persisted, separately-addressable artifact — it
gains no `record_id`, no `record_digest`, and no store entry of its own
at any point, before or after this repair. What changes is only that,
once a Stage 2 evaluation for the same `package_id`/session occurs, a
byte-for-byte copy of an already-computed, in-memory Stage 1 outcome value
becomes, incidentally, part of a *different* artifact's (the AER's) own
already-permitted content (AESIC-REQ-056 already permitted the AER to
carry rich content; this repair only specifies precisely what one of its
optional fields contains). "Both outcomes retrievable" (this
requirement's own original language) is satisfied because both are now
readable directly from the one artifact a reader already has to retrieve
to read Stage 2's own outcome — never through a second, independent
retrieval of Stage 1 state, because no such second retrieval path exists
or is implied. If no Stage 1 evaluation ever occurred for the session,
`stage_1_outcome_ref` remains absent (unaffected by this repair); no
disagreement-visibility guarantee applies because there is nothing to
disagree with.

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

**Stage 1 result retention and absence (new, Phase 147L.3 — closes the
authorizing prompt's §6, "Stage 1 Absence Semantics").** The caller that
invokes `evaluate_stage_1` MAY retain its returned `Stage1EvaluationResult`
(§5.2.1) in memory and later pass it to `evaluate_stage_2` as
`stage_1_result`, or MAY discard it. Neither choice is an error: AES
itself never requires a Stage 1 outcome to exist before Stage 2 may run
(AESIC-REQ-125, §5.2.1). A caller that discards its own Stage 1 result
before invoking Stage 2 — including across a process restart, which
definitionally loses any in-memory value (§11.2's restart matrix, row
"After Stage 1, before Confirmation") — simply invokes `evaluate_stage_2`
with `stage_1_result=None`, and the resulting AER's `stage_1_outcome_ref`
is absent, exactly as if Stage 1 had never been invoked at all.

**AESIC-REQ-064.** Stage 1's outcome SHALL NOT be persisted **as its own,
independently-addressable artifact** — at most surfaced as advisory
Session or Preview *display* state (never a `Session` field, never a
governance artifact with its own `record_id`/`record_digest`). This
requirement's text is unchanged in substance by Phase 147L.1's repair of
AESIC-REQ-057 (§8.6): an inline, embedded, byte-for-byte copy inside a
*different*, already-permitted artifact (the AER) is not "persisting
Stage 1's outcome" in the sense this requirement forbids — see
AESIC-REQ-118 (§8.6) for the precise boundary.

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

**AESIC-REQ-076 (repaired, Phase 147L.3 — adds three rows, closes Finding
§3.1/§3.2 restart/failure coverage; repaired, Phase 147L.5 — adds two
rows, closes Finding B restart-matrix completeness gap).** The following
restart matrix SHALL bind every future implementation:

| Restart point | Stage 1 effect | Stage 2 effect |
|---|---|---|
| Before Stage 1 | No effect — Stage 1 simply runs (or doesn't) whenever its caller next invokes it | N/A |
| After Stage 1, before Confirmation | Stage 1's outcome is lost (never persisted) — a fresh Stage 1 recomputation on resumption is equivalent | N/A |
| Before Stage 2 | N/A | Stage 2 has not yet run; resumes normally, reading current Registry/template state |
| After Stage 2, before Publication authorization | N/A | AER already durably persisted; resumption reads the current canonical AER via `package_id` (AESIC-REQ-119 item 2), never recomputes unless explicitly asked to |
| After Publication authorization, before Coordinator commit | N/A | AER unaffected — already durable before this point; a retried Coordinator `execute()` uses the already-persisted, canonical AER's `citation_text` unchanged |
| After Coordinator commit (CHGR exists) | N/A | AER remains as the durable, immutable record of what was cited; never re-evaluated post-publication |
| Publication retry (Coordinator-level) | N/A | Coordinator's own `_check_replay` (unmodified) refuses a second publish for an already-published `package_id` regardless of AES/AER state |
| Duplicate confirmation | N/A (IWC-001's own replay-protected concern) | N/A |
| Duplicate readiness (a second `build_package` call) | N/A | A second readiness package MAY cite a new Stage 2 AER (a fresh `package_id`); AES does not itself deduplicate across distinct `package_id`s |
| Duplicate publication attempt | N/A | Governed entirely by the Coordinator's own idempotency marker, unaffected by AES |
| Registry evolution (Declaration changed between attempts) | N/A | Each Stage 2 attempt SHALL always read the Registry's current state (§6.5) — a changed Declaration produces a genuinely different, freshly-computed outcome (AESIC-REQ-121's equality check classifies it "changed"), persisted as a **new** AER under a fresh `(package_id, evaluation_id)` compound key and made canonical (AESIC-REQ-023(b), AESIC-REQ-119/120, repaired Phase 147L.1 — Finding 2); the superseded prior AER remains durably retrievable by its own compound key, never silently reconciled with or deleted |
| Decision Template evolution (citation text changed) | N/A | Stage 2 SHALL always re-resolve the template fresh; a changed `eligible_authority` text produces a new `citation_text` in a new, canonical AER via the same AESIC-REQ-023(b)/119/120 mechanism as the row above (repaired Phase 147L.1 — Finding 2) |
| Citation evolution | N/A | Subsumed by "Decision Template evolution" — citation text is derived from the template, never tracked independently |
| **(New, Phase 147L.3)** Restart between Stage 1 and Stage 2 (caller loses its in-memory `Stage1EvaluationResult`) | Stage 1's result is lost, exactly as the "After Stage 1, before Confirmation" row already states | The caller invokes `evaluate_stage_2` with `stage_1_result=None` (AESIC-REQ-125); `stage_1_outcome_ref` is absent from the resulting AER; not an error, not a distinguishable-from-"Stage-1-never-invoked" case, and not required to be — both produce the identical, valid, absent-field AER |
| **(New, Phase 147L.3)** `stage_1_result` supplied but invalid (fails any AESIC-REQ-123 check) | N/A | `evaluate_stage_2` raises `Stage1HandoffInvalidError` (AESIC-REQ-124) before any Registry/Resolution/store work begins; no AER is produced, no partial state is left; the caller may retry by omitting `stage_1_result` (falls back to the row above) or by supplying a corrected value |
| **(New, Phase 147L.3)** Canonical pointer corrupted (detected at a `package_id` lookup, any restart point) | N/A | AES raises `CanonicalPointerCorruptError` (AESIC-REQ-126/127) rather than returning a possibly-wrong AER; every compound-keyed AER for that `package_id` remains intact and independently retrievable (AESIC-REQ-119 item 1), so no data is lost — only the pointer's own convenience-lookup is unavailable until operator-directed recovery |
| **(New, Phase 147L.5)** Crash or interruption after the AER's compound-key commit (AESIC-REQ-119 item 1) but before the canonical pointer's own write (AESIC-REQ-119 item 2) completes — first-ever establishment or supersession alike | N/A | AES treats the committed AER as an uncommitted candidate, never automatically canonical; the caller retries the identical `evaluate_stage_2` call, which recomputes fresh and either finds an existing, Stage-1-evidence-equivalent (AESIC-REQ-129) canonical AER (no-op) or persists another new compound-keyed AER and re-attempts the pointer write (AESIC-REQ-130); the original crash's own uncommitted candidate may remain permanently unreferenced — disclosed, harmless surplus history, never data loss |
| **(New, Phase 147L.5)** Pointer write fails synchronously within the same `evaluate_stage_2` call (not a process crash) immediately after a successful AER commit | N/A | AES raises `CanonicalPointerUpdateFailedError` (AESIC-REQ-131) rather than returning success or a stale result; the already-committed AER is never mutated or deleted; the caller retries per the row above |

### 11.3 Observational equivalence requirement

**AESIC-REQ-077.** For any restart point in §11.2's matrix, a resumption
SHALL produce outcomes observationally equivalent to an uninterrupted
execution with the same inputs — no restart point SHALL introduce a
distinguishable, undisclosed side effect.

---

## 12. Persistence Contract

### 12.1 Persistent artifacts

**AESIC-REQ-078 (repaired, Phase 147L.1 — Finding 2).** Exactly one
artifact type SHALL be durably persisted by AES: the AER (§8), one per
Stage 2 evaluation attempt, stored under the compound key `(package_id,
evaluation_id)` and canonically looked up by `package_id` (AESIC-REQ-053,
AESIC-REQ-119).

**AESIC-REQ-079.** The Declaration and resolved-template content that fed
a given AER SHALL NOT be separately persisted by AES — the AER's own
`outcome.declaration_ref` and `citation_text` are sufficient provenance;
the source Declaration/template themselves remain the Registry's own
durable state (§7.6), never AES's to duplicate.

**AESIC-REQ-119 (new, Phase 147L.1 — Finding 2 repair).** AER persistence
SHALL use a two-tier storage model:

1. **Primary store — immutable, compound-keyed.** Every persisted AER
   SHALL be written once, exclusive-create (AESIC-REQ-019), under its own
   `(package_id, evaluation_id)` compound key. Every such write SHALL be
   atomic, write-once (AESIC-REQ-086, unaffected). No entry in this store
   is ever updated or deleted once written (AESIC-REQ-054/082, unaffected)
   — every AER ever produced for a `package_id`, superseded or not,
   remains durable and independently retrievable by its own compound key
   indefinitely.
2. **Canonical pointer index — mutable, `package_id`-keyed.** A separate,
   small pointer artifact, keyed by `package_id` alone, SHALL record which
   compound-keyed AER is currently canonical for that `package_id` (at
   minimum: the canonical `evaluation_id`, `record_id`, `record_digest`,
   and — **repaired, Phase 147L.3, closes Finding §3.2** — the pointer's
   own `pointer_digest`, AESIC-REQ-126). Every consumer performing an
   ordinary `package_id` lookup (§14.1: Readiness, Publication, CHGR,
   Inspection/Diagnostics/Audit) SHALL read through this pointer to reach
   the AER it references — this is a **read-indirection change only**; no
   consumer-facing requirement in §14 changes as a result, since every
   consumer already consumed the AER only by reference (AESIC-REQ-061),
   never by an assumption about how AES internally locates it. The
   pointer's own write SHALL use the same atomic-replace idiom already
   established at AESIC-REQ-086 (temp file + fsync + `os.replace`, or
   equivalent), so a pointer update is itself never observed partially
   applied.

Establishing the AER for a `package_id` for the first time (no existing
canonical pointer) is the degenerate case of AESIC-REQ-023(b): a first
compound-keyed write, followed by the pointer index's own first,
exclusive-create write (never a replace, since none exists yet).

**AESIC-REQ-120 (new, Phase 147L.1 — Finding 2 repair, concurrency).**
Two Stage 2 attempts running concurrently for the same `package_id`
SHALL each safely persist their own compound-keyed AER without collision,
because AESIC-REQ-098 already guarantees each carries its own distinct
`evaluation_id` (§12.1 item 1, unaffected by concurrency). Only the
canonical pointer index's own update (§12.1 item 2) is a shared
resource between the two attempts; its update SHALL be a single atomic
replace, and SHALL NOT be conditioned on which attempt began first —
whichever atomic replace completes last SHALL be canonical. This is a
disclosed **last-write-wins** semantics for the pointer only, mirroring
the already-frozen, already-accepted precedent that everything upstream
of Publication's own true mutual-exclusion commit point is "not
authority-relevant" and last-write-wins by design (IWPC-REQ-144/147,
cited and independently re-confirmed by Phase 147L §2.10). It never loses
data: every attempted AER remains durably persisted and independently
retrievable by its own compound key regardless of which attempt's pointer
update wins, and it never affects Publication itself, whose own true
mutual exclusion remains solely the Coordinator's `O_CREAT | O_EXCL`
commit marker (§9.5, AESIC-REQ-072, unaffected by this repair).

**AESIC-REQ-121 (new, Phase 147L.1 — Finding 2 repair, also closes Phase
147L Finding 3; repaired, Phase 147L.5 — Finding A).** The "inputs
unchanged" comparison required by AESIC-REQ-023(a) and AESIC-REQ-081
(§12.3) SHALL be performed as follows: AES SHALL compare (1) the freshly
(re-)resolved `citation_text` and every field of the freshly
(re-)computed `AuthorityEvaluationOutcome` — **excluding** `evaluated_at`,
consistent with AESIC-REQ-018's own "modulo `evaluated_at`" framing, since
`evaluated_at` is metadata `evaluate()` never branches on — against the
corresponding fields of `package_id`'s current canonical AER (read via
AESIC-REQ-119 item 2), **and (2), as of this repair, whether this
attempt's own (already-AESIC-REQ-123-validated, if supplied)
`stage_1_result` is Stage-1-evidence-equivalent (AESIC-REQ-129) to the
current canonical AER's own `stage_1_outcome_ref` field (§8.6)**. Every
compared field in (1) matching exactly, **and (2) holding**, SHALL be
classified "unchanged" (AESIC-REQ-023(a)); any compared field in (1)
differing, **or (2) not holding**, SHALL be classified "changed"
(AESIC-REQ-023(b)). This comparison requires exactly one additional
AER-store read (the canonical pointer's own referenced AER) beyond the one
Decision Template read and one Registry call AESIC-REQ-102 (§17) already
budgets per stage per evaluation attempt; AESIC-REQ-102 is repaired
accordingly. **Comparison (2) introduces no additional I/O beyond this
same read**: the canonical AER's own `stage_1_outcome_ref` field (if
present) is part of the same document already retrieved for comparison
(1), and this attempt's own `stage_1_result` (if supplied) is already an
in-memory parameter AES holds for this call (AESIC-REQ-128) — no second
store access is required.

**AESIC-REQ-129 (new, Phase 147L.5 — closes Finding A, Stage 1 evidence
equivalence).** Two Stage 1 evidence states — the current canonical AER's
own `stage_1_outcome_ref` field (§8.6, absent or present) and this
attempt's own (already-AESIC-REQ-123-validated, if non-`None`)
`stage_1_result` — SHALL be classified **Stage-1-evidence-equivalent**
under exactly the following deterministic rule, evaluated in this order:

1. **Both absent.** If the canonical AER carries no `stage_1_outcome_ref`
   and this attempt supplies no `stage_1_result` (`None`), the two SHALL
   be classified equivalent.
2. **One absent, one present.** If exactly one of the two is absent, they
   SHALL be classified **not equivalent** — introducing Stage 1 evidence
   where none existed before (or vice versa, an attempt that supplies
   `None` where the canonical AER carries a `stage_1_outcome_ref`) is
   itself a material change this contract SHALL make visible, never
   silently absorbed into an "unchanged" classification.
3. **Both present.** If both carry Stage 1 evidence, the two SHALL be
   compared field-by-field: `session_id` (trivially equal whenever both
   derive from AESIC-REQ-123's own session-binding check against the same
   `session`, restated here only for completeness), and every field of
   the wrapped `AuthorityEvaluationOutcome` — **excluding** `evaluated_at`,
   for the same reason AESIC-REQ-121's own comparison (1) excludes it: it
   is metadata neither `evaluate()` nor this equivalence test branches on.
   `evaluation_id` is explicitly **excluded** from this comparison — it is
   guaranteed unique per invocation by AESIC-REQ-098's own construction, so
   including it would make every distinct Stage 1 invocation "not
   equivalent" even when its substantive content is identical, defeating
   the purpose of this equivalence test entirely. Every remaining field
   matching exactly SHALL be classified equivalent; any differing SHALL be
   classified not equivalent.

This is the sole and complete definition of "Stage-1-evidence-equivalent"
as used by AESIC-REQ-023/121 (§5.11/§12.1). It relies on no object
identity, no process memory, no timestamp comparison beyond the explicit
`evaluated_at` exclusion above, and no implementation-specific
serialization — every compared field is a plain value already defined by
AEMIC-001 §6 (`AuthorityEvaluationOutcome`) or AESIC-REQ-122
(`Stage1EvaluationResult.session_id`), so the comparison is deterministic
across restart and across independent implementations, exactly as
AESIC-REQ-121's own pre-existing comparison already is.

**AESIC-REQ-130 (new, Phase 147L.5 — closes Finding B, AER-commit/pointer-write
restart point).** A crash or interruption after a Stage 2 attempt's
compound-keyed AER write (AESIC-REQ-119 item 1) completes but before the
corresponding canonical-pointer write (AESIC-REQ-119 item 2) completes
SHALL be governed by exactly the following rule, closing the restart point
named in §11.2's new row (AESIC-REQ-076):

1. **Durable state after the crash.** The compound-keyed AER SHALL exist,
   durable and immutable, exactly as any other entry in the primary store
   (AESIC-REQ-119 item 1) — indistinguishable, at the storage layer, from
   any other AER that has not (yet, or ever) become canonical. The
   canonical pointer SHALL be in exactly the state it was in before this
   attempt began: absent (if this was the `package_id`'s first-ever Stage
   2 attempt) or still naming the previous canonical AER (if this was a
   supersession attempt).
2. **Classification.** Such an AER SHALL be classified an **uncommitted
   candidate** — never automatically canonical merely by existing, and
   never itself corrupt (`CanonicalPointerCorruptError`, AESIC-REQ-127,
   governs a pointer that is present but internally inconsistent; this
   rule governs the pointer's own absence-or-staleness relative to a
   candidate AER that is itself perfectly valid).
3. **Discovery.** A retry of the same `evaluate_stage_2` call for the same
   `package_id`/`session`/`stage_1_result` SHALL discover this state
   exactly as it would discover any other pre-existing state: by
   performing AESIC-REQ-023's own fresh-resolution-and-comparison
   procedure against whatever the canonical pointer currently names (or
   its absence, for the first-ever case) — never by scanning the primary
   store for uncommitted candidates, and never by treating the mere
   existence of an uncommitted candidate as evidence of what the
   canonical answer should be.
4. **Recovery is retry, not reconstruction.** AES SHALL NOT infer that an
   uncommitted candidate is the intended canonical AER for its
   `package_id` merely because it is the most recent compound-keyed entry,
   because no total write-order across restarts is recorded independently
   of the pointer itself (mirroring AESIC-REQ-126 item 4's own reasoning
   for the analogous pointer-corruption case). The sole sanctioned
   recovery path is: the caller retries the identical `evaluate_stage_2`
   call; AES recomputes fresh, reaches the same AESIC-REQ-023(a)/(b)
   classification the original attempt would have reached, and either (a)
   finds an unrelated AER already canonical and Stage-1-evidence-equivalent
   (AESIC-REQ-129) — classifying the retry a no-op — or (b) persists
   **another** new compound-keyed AER (a fresh `evaluation_id`,
   AESIC-REQ-098) and attempts the pointer write again. Case (b) MAY leave
   the original crash's own uncommitted candidate permanently unreferenced
   by any pointer — this is disclosed, harmless surplus history
   (AESIC-REQ-119 item 1's own "no entry... is ever deleted" already
   covers it), never data loss, never a defect requiring cleanup.
5. **Idempotent retry is observationally equivalent.** Once a retry's own
   pointer write succeeds, the observable outcome (the canonical AER for
   this `package_id`, its `citation_text`, its `stage_1_outcome_ref`) is
   identical to what an uninterrupted execution of the same call would
   have produced — satisfying AESIC-REQ-077's own observational-equivalence
   requirement for this restart point.
6. **Concurrency.** Two or more attempts (original-plus-retry, or
   genuinely concurrent callers) racing through this same window are
   governed by the existing, unchanged AESIC-REQ-120 last-write-wins
   pointer semantics — this repair introduces no new concurrency
   mechanism, only a name and a defined outcome for a restart point that
   already existed structurally but had none.
7. **Detected pointer-write failure (same-process, non-crash).** If the
   pointer write itself fails synchronously within the same
   `evaluate_stage_2` call (e.g. a storage-layer I/O error, as opposed to
   a process-level crash that simply never returns) — AES SHALL raise
   `CanonicalPointerUpdateFailedError` (AESIC-REQ-131) rather than
   returning success or returning a stale canonical result: the AER just
   written is disclosed as durably persisted but not yet canonical, and
   the caller retries per items 3–5 above. This SHALL NOT mutate or delete
   the already-committed AER (AESIC-REQ-054/082, unaffected).

**AESIC-REQ-131 (new, Phase 147L.5 — closes Finding B, pointer-establishment
failure ownership).** `CanonicalPointerUpdateFailedError` SHALL be a new
exception type, raised by AES only per AESIC-REQ-130 item 7 (a detected,
same-process pointer-write failure immediately following a successful
compound-keyed AER write), distinct from `CanonicalPointerCorruptError`
(AESIC-REQ-127, which governs a pointer that is present but fails its own
read-time integrity check, §12.1) — this new type instead governs the
disjoint condition of a pointer write that did not complete at all. AES
SHALL log both the successful AER write and the failed pointer write as
two separate, distinguishable events (extending AESIC-REQ-094's own
per-attempt logging obligation) so an operator can observe "AER committed,
pointer not yet advanced" as a distinct, diagnosable state rather than an
undifferentiated failure. Origin: AES's own pointer-write step. Detection
owner: AES, synchronously, within the same call. Recovery owner: AES's
caller, via retry (AESIC-REQ-130 items 3–5) — never an automatic
AES-internal repair, mirroring AESIC-REQ-126 item 4's own operator/retry
discipline for the analogous corruption case. Retry owner: AES's caller.
Logging owner: AES. User-visible owner: AES's caller. No ownership gap or
dual authority exists for this failure, mirroring §13's existing discipline
for every other failure type this contract names.

**AESIC-REQ-126 (new, Phase 147L.3 — closes Finding §3.2, canonical
pointer tamper-evidence).** The canonical pointer index (AESIC-REQ-119
item 2) SHALL itself be tamper-evident, using the smallest addition
consistent with this codebase's own existing digest precedent
(AESIC-REQ-055, `compute_record_digest`), applied to the pointer artifact
rather than to the AER:

1. **Pointer content and digest.** The pointer's own persisted content
   SHALL be exactly `{package_id, evaluation_id, record_id, record_digest,
   pointer_digest}`, where `pointer_digest` SHALL be computed, using the
   same `compute_record_digest` function every other durable record in
   this codebase already uses (AESIC-REQ-055), over the pointer's own
   other four fields (`package_id`, `evaluation_id`, `record_id`,
   `record_digest`). AES SHALL own computing and attaching `pointer_digest`
   at every pointer write (mirroring AESIC-REQ-083's digest-ownership
   discipline, applied here to the pointer instead of the AER); no
   downstream consumer SHALL recompute or override it.
2. **Mandatory read-time verification.** Before treating any canonical
   pointer as authoritative for a `package_id` lookup, AES (or, once
   implemented, the read-only diagnostic surface of AESIC-REQ-097) SHALL
   perform, in order: (a) recompute `pointer_digest` over the pointer's own
   other four fields and compare against the stored `pointer_digest` —
   any mismatch indicates the pointer artifact itself was corrupted or
   edited out-of-band after AES wrote it; (b) retrieve the compound-keyed
   AER the pointer names (`(package_id, evaluation_id)`, cross-checked
   against `record_id`) and compare that AER's own self-carried
   `record_digest` (AESIC-REQ-055) against the pointer's copy of
   `record_digest` — any mismatch indicates the pointer's `record_id`
   and/or `record_digest` fields were corrupted or reassigned to name a
   different (possibly still-valid, possibly superseded) AER. Either
   mismatch SHALL cause AES to raise `CanonicalPointerCorruptError`
   (AESIC-REQ-127) and SHALL NOT return, or allow any consumer to treat as
   canonical, the mismatched pointer's referenced content — a fail-closed
   response, mirroring the §13 table's existing "Digest mismatch"
   disposition for the AER itself, extended here to the pointer.
3. **What this does and does not defend against.** This mechanism detects
   accidental corruption (disk faults, partial writes outside the
   atomic-replace path, implementation bugs that write a syntactically
   valid but semantically wrong pointer) — the same threat class
   AESIC-REQ-055's own digest already defends against for the AER, no
   stronger and no weaker. It does not, and is not claimed to, defend
   against a fully-consistent adversarial forgery that recomputes
   `pointer_digest` correctly over fabricated field values — no digest
   scheme in this codebase (AER, CHGR, or otherwise) makes that claim
   either (AESIC-REQ-055's own scope, unchanged); a stronger threat model
   (cryptographic signing, an HMAC with a secret key) remains explicitly
   out of scope for this contract, exactly as it is for every other
   digest this codebase already computes.
4. **Recovery ownership.** On a detected mismatch, recovery is an
   operator-owned action (mirroring the §13 table's existing "Digest
   mismatch... Operator investigating tampering/corruption" row, applied
   to the pointer) — not an automatic AES-internal repair. AES MAY, as an
   implementation convenience, offer a deterministic pointer-rebuild
   operation that reconstructs a fresh, correctly-digested pointer for a
   `package_id` from an operator-selected compound-keyed entry in the
   primary store (AESIC-REQ-119 item 1, which retains every AER
   indefinitely), but no such rebuild SHALL run automatically or without
   explicit operator action, since automatic selection among multiple
   surviving compound-keyed entries for the same `package_id` is not
   itself a fact AES can determine unassisted (§12.1 item 1 does not
   record a total write-order across restarts beyond what the corrupted
   pointer itself was tracking).

### 12.2 Transient state

**AESIC-REQ-080.** The following SHALL remain transient, never persisted
**as its own, independently-addressable artifact** (see AESIC-REQ-064's
repaired text and AESIC-REQ-118, §8.6, for the precise boundary this
qualification restates): every Stage 1 outcome (§9.1); AES's own internal
resolution intermediate state (the resolved Decision Template document
object itself, once `citation_text`/`declaration` are extracted); any
in-flight, not-yet-persisted Stage 2 attempt.

### 12.3 Recomputed state

**AESIC-REQ-081 (repaired, Phase 147L.1 — Finding 2/3).** Every Stage 1
outcome SHALL be recomputed on each invocation, never read from a prior
persisted value (none exists). A duplicate Stage 2 attempt for a
`package_id` SHALL always recompute fresh (§6.5) and then compare against
the current canonical AER using AESIC-REQ-121's equality procedure: with
unchanged inputs, the comparison finds the already-persisted, canonical
AER equal (idempotent no-op, AESIC-REQ-023(a)); with changed inputs, the
comparison finds it unequal and §11's restart matrix, per AESIC-REQ-023(b)
and AESIC-REQ-119/120, governs the resulting new, canonical AER.

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
| **(New, Phase 147L.3)** Invalid Stage 1 handoff (`Stage1HandoffInvalidError`, any `reason`) | AES's own input validation of a caller-supplied `stage_1_result` (AESIC-REQ-123) | AES | AES's caller — indicates the caller supplied a fabricated, cross-session, cross-identity, cross-template, or structurally malformed `stage_1_result`; never a normal runtime condition when the caller only ever forwards its own `evaluate_stage_1` return value unmodified | AES's caller | AES (logs the specific `reason`) | Not retryable with the same `stage_1_result` — the caller must either correct which value it forwards or omit `stage_1_result` entirely (falls back to AESIC-REQ-125's absence semantics, always valid) |
| **(New, Phase 147L.3)** Canonical pointer corrupt (`CanonicalPointerCorruptError`) | Pointer artifact's own storage (AESIC-REQ-126) | AES (detects at read time, §12.1) | Operator investigating tampering/corruption (mirrors "Digest mismatch," applied to the pointer) | Whoever performs the `package_id` lookup (§14.1 consumers, via AES) | AES | N/A — a pointer-digest or referenced-AER-digest mismatch indicates corruption or tampering, never a transient condition to retry; the underlying compound-keyed AER history remains intact and available for operator-directed pointer reconstruction (AESIC-REQ-126 item 4) |
| **(New, Phase 147L.5)** Canonical pointer update failed (`CanonicalPointerUpdateFailedError`, AESIC-REQ-131) | AES's own pointer-write step, detected synchronously within the same call (AESIC-REQ-130 item 7) | AES | AES's caller, via retry (AESIC-REQ-130 items 3–5) — never an automatic AES-internal repair | AES's caller | AES (logs the successful AER write and the failed pointer write as two distinguishable events) | AES's caller — a retry recomputes fresh and either finds an existing, Stage-1-evidence-equivalent canonical AER (no-op) or persists another new compound-keyed AER and re-attempts the pointer write |

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
| **(New, Phase 147L.3)** Stage 1 outcome fabrication/substitution (caller supplies a `stage_1_result` it did not itself receive from `evaluate_stage_1`, or that belongs to another session/identity/template) | Prevented by AESIC-REQ-123's mandatory four-check validation (structural, session, identity, template), refusing via `Stage1HandoffInvalidError` (AESIC-REQ-124) rather than silently accepting or silently dropping the supplied value |
| **(New, Phase 147L.3)** Canonical pointer tampering/corruption (bit-level corruption or out-of-band edit of the pointer's `record_id`/`record_digest`/`evaluation_id`) | Prevented/detected by AESIC-REQ-126's `pointer_digest` and mandatory read-time cross-check against the referenced AER's own self-carried digest; a mismatch raises `CanonicalPointerCorruptError` (AESIC-REQ-127) and is never silently treated as canonical |

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
persisted, per §9.1) alongside any Stage 1 advisory display. **Repaired,
Phase 147L.1:** the relationship between this `evaluation_id` and
`stage_1_outcome_ref` (§8.6, Phase 147L Finding 4) is now explicit —
AESIC-REQ-118 (§8.6) requires `stage_1_outcome_ref`, when present, to
embed Stage 1's own distinct `evaluation_id` alongside its copied outcome,
so the AER's top-level `evaluation_id` (this Stage 2 attempt's own) and
the embedded `stage_1_outcome_ref.evaluation_id` (the correlated Stage 1
attempt's own) are always two separately readable, never-conflated
values on the same AER. `evaluation_id` uniqueness per invocation
(unchanged by this repair) is also the structural property AESIC-REQ-119
(§12.1) relies on to guarantee collision-free AER storage keys.
**Clarified, Phase 147L.3:** this requirement's own "SHOULD be surfaced...
alongside any Stage 1 advisory display" clause is, as of this repair, made
mechanically concrete rather than left to implementer discretion —
`Stage1EvaluationResult` (AESIC-REQ-122, §5.2.1), `evaluate_stage_1`'s own
return type, carries Stage 1's `evaluation_id` as one of its exactly
three fields, closing the pre-existing gap Phase 147L.2 §2.1 identified
(the caller previously had no channel to receive this value at all, a
necessary precondition this repair's own §5.2.1 resolves as a byproduct of
closing Finding §3.1).

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

**AESIC-REQ-102 (performance expectations; repaired, Phase 147L.1 —
Finding 3; clarified, Phase 147L.3 — Finding §3.2; clarified, Phase
147L.5 — Finding A).** AES SHALL perform at most one Decision Template
read, at most one Registry call, and — for Stage 2 only, to perform
AESIC-REQ-121's own idempotency comparison — at most one canonical
AER-store read, per stage per evaluation attempt (§6.9) — no future
implementation SHALL introduce unbounded or N+1-style resolution
behavior. AESIC-REQ-126's pointer-digest and referenced-AER-digest
verification introduces no additional I/O beyond this budget: both
digest recomputations operate on bytes already read as part of the one
canonical AER-store read this requirement already counts (the pointer's
own small content, and the AER it references), never a separate store
access. AESIC-REQ-121/129's Stage-1-evidence-equivalence comparison
likewise introduces no additional I/O beyond this budget, per
AESIC-REQ-121's own text: the canonical AER's `stage_1_outcome_ref` is
part of the same document this requirement already counts, and the
supplied `stage_1_result` is already an in-memory call parameter, never a
store read.

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

**Discharge note (Phase 147L.1).** Phase 147L performed exactly this
§18 obligation and identified Finding 1 (item 8, AER immutability
checklist — more precisely, item 4's persistence-model check, since
Finding 1 is a persistence/transient-classification contradiction, not an
immutability defect) and Finding 2 (item 4, persistence model, and item
3, replay semantics). Per AESIC-REQ-112's own disposal clause, this repair
phase (Phase 147L.1) is that "subsequent, separately-authorized contract
repair phase." §25 below records the repair; a future Phase 147L.2 is
recommended (§26) to independently re-verify it, mirroring this same
verification-then-repair-then-re-verification discipline AEMIC-001 §21/§25/§26
already established.

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
own discretion. **This v1.1 repair (Phase 147L.1) is itself an exercise of
exactly this requirement** — an in-place minor revision, not an
implementing phase's own discretion, per §25 below.

**Compatibility reconfirmation (Phase 147L.1).** AESIC-REQ-113's "zero
amendments required" claim is independently reconfirmed unchanged by this
repair: every edit this repair makes (§25 below enumerates them
completely) is internal to AESIC-001's own text — a reinterpretation of
one already-optional AER field's content (§8.6), a storage-keying
clarification internal to AES's own persistence mechanics (§12.1), and an
equality-procedure/performance-budget clarification (§12.1, §17). None
touches, narrows, widens, or requires a new provision of AEM-001,
AEMIC-001, IWC-001, IWPC-001, PEC-001, or CHGR-001 — every citation this
repair makes to a predecessor contract (AESIC-REQ-098's own unchanged
per-invocation `evaluation_id` guarantee; AESIC-REQ-072's own unchanged
Coordinator-replay independence) is unchanged from v1.0's own citation of
the same provision. See §25 below for the full compatibility assessment.

**Compatibility reconfirmation (Phase 147L.3).** AESIC-REQ-113's "zero
amendments required" claim is independently reconfirmed unchanged by this
further repair. The one new cross-contract citation this repair
introduces — `Session.session_id` (AESIC-REQ-122, §5.2.1) — cites a field
IWC-001 already freezes and already populates, unmodified: Phase 144D's
independent re-derivation (IWC-001 §26.1, cited directly, not merely
trusted) confirms `PublicationHandoff.build_package` already receives the
full `Session` object "carrying... `owner_identity`, `template_ref`,
`subject_ref`, all populated, unredacted, verbatim," and confirms the
Coordinator's own constructed record already carries `session_id`
(IWC-001 §26.1's own text, "a CHGR built by the Publication Coordinator
today carries `package_id`, `session_id`, `session_state`...") — meaning
`session_id` is already a populated `Session`-adjacent field this
integration surface was already reading from, before this repair, for an
unrelated purpose. This repair adds no new field to `Session`, no new
method to IWC-001, and no new obligation on Interactive Workflow — it only
adds a new *reader* of an already-existing, already-frozen value, exactly
as AESIC-REQ-008 already reads `owner_identity`/`template_ref`/`template_version`
from the same object for an unrelated purpose. No amendment to AEM-001,
AEMIC-001, IWC-001, IWPC-001, PEC-001, or CHGR-001 is required by this
repair — the same zero this contract required at v1.0 and reconfirmed at
v1.1. See §29 below for the full compatibility assessment.

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

**No-Go confirmation (Phase 147L.1).** This repair phase's own no-go
boundary mirrors AESIC-REQ-116/117 exactly: it SHALL NOT implement the
Authority Evaluation Service, the Decision Template Resolution capability,
a concrete Authority Registry, Authority Evaluation Record persistence, or
any replay mechanism; it SHALL NOT modify `src/pcae/**`, any schema file,
any test file, `.pcae/policy.toml`, Interactive Workflow code, Publication
Coordinator code, CHGR construction code, the evaluator implementation,
any CLI command, or any runtime plugin; and it SHALL NOT amend any
contract other than AESIC-001 itself. See §26 for this phase's own
finalization confirmation.

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
| AESIC-REQ-118 | §8.6 (new, Phase 147L.1) | `stage_1_outcome_ref` inline-embedded-copy shape — checked against AESIC-REQ-064/080 for non-contradiction (repairs Finding 1, and Finding 4 via its `evaluation_id` clause) |
| AESIC-REQ-119 | §12.1 (new, Phase 147L.1) | Two-tier AER storage model (compound-keyed primary store + `package_id`-keyed canonical pointer) — checked against AESIC-REQ-054/082 (immutability) and AESIC-REQ-023(b)/§11.2 (supersession) for non-contradiction (repairs Finding 2) |
| AESIC-REQ-120 | §12.1 (new, Phase 147L.1) | Canonical-pointer concurrency (last-write-wins), checked against AESIC-REQ-104's concurrent-idempotency guarantee and IWPC-REQ-144/147's own precedent for non-contradiction (repairs Finding 2) |
| AESIC-REQ-121 | §12.1 (new, Phase 147L.1) | "Inputs unchanged" equality procedure and its one-additional-read performance cost — checked against AESIC-REQ-023(a)/081/102 for non-contradiction (repairs Finding 2's idempotency mechanics and Finding 3 jointly) |
| AESIC-REQ-122 | §5.2.1 (new, Phase 147L.3) | `Stage1EvaluationResult` shape (`outcome`, `evaluation_id`, `session_id`) — checked against AEMIC-001 §6 (unmodified `AuthorityEvaluationOutcome`) and AESIC-REQ-098 (unmodified `evaluation_id` uniqueness) for non-contradiction (repairs Finding §3.1) |
| AESIC-REQ-123 | §5.2.1 (new, Phase 147L.3) | Four-check `stage_1_result` validation sequence (structural, session, identity, template) — checked against AESIC-REQ-008 (identity/template derivation) and AESIC-REQ-065 (staleness is not a validation failure) for non-contradiction (repairs Finding §3.1) |
| AESIC-REQ-124 | §5.7 (new, Phase 147L.3) | `Stage1HandoffInvalidError` closed four-reason taxonomy and no-side-effect refusal — checked against AESIC-REQ-010 (§13's taxonomy is exhaustive) for non-contradiction (repairs Finding §3.1) |
| AESIC-REQ-125 | §9.1 (new, Phase 147L.3) | Stage 1 absence semantics (`None` is always valid, always distinguishable from invalid) — checked against AESIC-REQ-057/062/063 for non-contradiction (repairs Finding §3.1, closes the authorizing prompt's §6) |
| AESIC-REQ-126 | §12.1 (new, Phase 147L.3) | Canonical pointer `pointer_digest` and mandatory read-time verification against the referenced AER's own digest — checked against AESIC-REQ-055/083/119/120 for non-contradiction (repairs Finding §3.2) |
| AESIC-REQ-127 | §13 (new, Phase 147L.3) | `CanonicalPointerCorruptError` failure-ownership row — checked against the existing "Digest mismatch" row for non-contradiction (repairs Finding §3.2) |
| AESIC-REQ-128 | §5.2.1 (new, Phase 147L.3) | Complete Stage 2 invocation contract (input/source/validator closure table) — checked against §5's own no-implementer-choice enumeration for completeness (closes the authorizing prompt's §5) |
| AESIC-REQ-129 | §12.1 (new, Phase 147L.5) | Stage-1-evidence-equivalence definition — checked against AESIC-REQ-121/023 for non-contradiction and against AESIC-REQ-098 (evaluation_id uniqueness, correctly excluded from the comparison) for non-contradiction (repairs Finding A) |
| AESIC-REQ-130 | §11.2 (new, Phase 147L.5) | AER-commit/pointer-write restart point — checked against AESIC-REQ-119 (two-tier storage), AESIC-REQ-120 (concurrency), and AESIC-REQ-077 (observational equivalence) for non-contradiction (repairs Finding B) |
| AESIC-REQ-131 | §13 (new, Phase 147L.5) | `CanonicalPointerUpdateFailedError` failure-ownership row — checked against the existing `CanonicalPointerCorruptError` row for non-contradiction/non-overlap (repairs Finding B) |

**AESIC-REQ count: 131, AESIC-REQ-001 through AESIC-REQ-131, sequential,
no gaps, no reuse.** (117 issued at v1.0 freeze, Phase 147K; 4 added —
AESIC-REQ-118 through AESIC-REQ-121 — at the v1.1 repair, Phase 147L.1; 7
added — AESIC-REQ-122 through AESIC-REQ-128 — at the v1.2 repair, Phase
147L.3; 3 added — AESIC-REQ-129 through AESIC-REQ-131 — at the v1.3
repair, Phase 147L.5; zero renumbered, zero reused across all four
revisions.)

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

## 23. Overall Verdict (Phase 147K, v1.0 — historical)

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

**Superseded by Phase 147L.1's own Overall Verdict, §27 below.** This
§23 is retained unchanged as the historical record of Phase 147K's own
freeze verdict, exactly as AEMIC-001 §20 retains its own pre-repair
Contract Quality Review unchanged alongside its own later repair
sections. It does not restate current status; §27 does.

---

## 24. Recommended Next Phase (Phase 147K, v1.0 — historical)

**147L — Authority Evaluation Integration Contract Independent
Verification.** That phase shall independently re-derive and verify the
complete AESIC-001 contract against the architecture from Phase 147J and
the existing PCAE governance contracts (AEM-001, AEMIC-001, IWC-001,
IWPC-001, PEC-001, CHGR-001). It shall remain verification-only, identify
any inconsistencies or unsatisfied requirements, and make no
implementation change.

**This recommendation is not an authorization.**

**Discharged.** Phase 147L executed exactly this recommendation and
produced the two findings §25 below repairs. §28 below states this
repair's own recommended next phase.

---

## 25. Phase 147L.1 Repair Confirmation

**Version:** 1.1
**Predecessor:** AESIC-001 v1.0 (Phase 147K)
**Repaired by:** Phase 147L.1 — AESIC-001 Contract Repair
**Baseline findings:** Phase 147L — Authority Evaluation Integration
Contract Independent Verification
(`docs/verification/PHASE_147L_AUTHORITY_EVALUATION_INTEGRATION_CONTRACT_INDEPENDENT_VERIFICATION.md`),
verdict AESIC-001 VERIFIED WITH NON-BLOCKING FINDINGS, two Major findings
(Finding 1, Finding 2), one Minor finding (Finding 3), one Informational
finding (Finding 4)

### 25.1 Scope

This repair is narrowly scoped to Phase 147L's own two Major findings
(Finding 1: §8.6/§9.1/§12.2 contradiction; Finding 2: §5.11/§11.2/§12.1
idempotency-vs-supersession gap), per this phase's own authorizing prompt.
Finding 3 (Minor, undefined equality procedure) is resolved as an
unavoidable byproduct of repairing Finding 2 — Finding 2's own repair
cannot state an unambiguous supersession mechanism without also stating
the equality procedure that decides whether supersession or no-op applies
(AESIC-REQ-121, §12.1) — not as separate, independently-motivated scope
expansion. Finding 4 (Informational, `evaluation_id`/`stage_1_outcome_ref`
relationship) is resolved as an unavoidable byproduct of repairing Finding
1 for the identical reason (AESIC-REQ-118's own embedded-copy shape must
state what it contains, and `evaluation_id` is part of that content).
No other AESIC-001 requirement, invariant, component boundary, or
predecessor-contract citation was altered. No implementation, schema, or
runtime change was made (§26 confirms).

### 25.2 Findings Repaired

**Finding 1 — [Major] `stage_1_outcome_ref` cannot deliver "both outcomes
retrievable" given Stage 1's unconditional non-persistence.** Repaired by
AESIC-REQ-118 (§8.6): `stage_1_outcome_ref`, despite its `_ref` suffix
(preserved for field-name stability), is redefined as an inline, verbatim,
byte-for-byte embedded copy of Stage 1's own outcome, `evaluation_id`, and
timestamp, written directly into the AER's own already-permitted document
body at Stage 2 persistence time — never a pointer to separately-persisted
state, because no such state exists or may ever exist. AESIC-REQ-064/080
are correspondingly clarified (not weakened): "Stage 1's outcome SHALL NOT
be persisted" continues to mean "as its own, independently-addressable
artifact" — a meaning both requirements' original text was always
consistent with, now stated explicitly to close the ambiguity Finding 1
identified.

**Finding 2 — [Major] Stage 2 idempotency's "supersede" branch unsatisfiable
under exclusive-create, `package_id`-only persistence.** Repaired by a
two-tier storage model (AESIC-REQ-119, §12.1): AERs are stored under a
compound `(package_id, evaluation_id)` key (collision-free, since
AESIC-REQ-098 already guarantees `evaluation_id` uniqueness per
invocation), with a separate, atomically-updated `package_id`-keyed
canonical pointer index for ordinary lookup. AESIC-REQ-023 is repaired to
state the full decision procedure: recompute fresh, compare against the
canonical AER via the new equality procedure (AESIC-REQ-121), and either
return the canonical AER unchanged (no new write) or persist a genuinely
new AER under a fresh compound key and advance the canonical pointer
(never overwriting, mutating, or deleting the superseded AER).
AESIC-REQ-120 states the concurrency model: concurrent attempts never
collide on AER writes (distinct `evaluation_id`s), and the shared
canonical-pointer update is disclosed, deliberate last-write-wins,
mirroring IWPC-REQ-144/147's own already-frozen precedent for everything
upstream of Publication's own true commit point. AESIC-REQ-019/053/078 are
correspondingly clarified to name the compound key as the storage key and
`package_id` as the lookup convenience key, matching what those
requirements' own original text already intended `package_id`-keying to
mean for an ordinary consumer.

**Finding 3 — [Minor] Undefined equality procedure (resolved as a
byproduct).** AESIC-REQ-121 defines it precisely: field-by-field,
byte-for-byte comparison of the freshly re-resolved `citation_text` and
every field of the freshly recomputed `AuthorityEvaluationOutcome` except
`evaluated_at` (consistent with AESIC-REQ-018's own "modulo `evaluated_at`"
framing), against the canonical AER's corresponding fields. AESIC-REQ-102's
performance budget is correspondingly repaired to include the one
additional canonical-AER-store read this comparison requires.

**Finding 4 — [Informational] `evaluation_id`/`stage_1_outcome_ref`
relationship (resolved as a byproduct).** AESIC-REQ-118 states it
explicitly: the embedded copy carries Stage 1's own distinct
`evaluation_id`, always different from the AER's own top-level
(Stage 2's) `evaluation_id` — the two are never conflated, and both are
independently readable from the same AER.

### 25.3 Candidate Repairs Evaluated

**Finding 1 — candidates considered:**

1. *Rename the field to drop the `_ref` suffix* (e.g. `stage_1_outcome`).
   Rejected: field renames are a wire-shape change a future implementer
   building against v1.0's own already-published shape would need to
   detect and migrate; the repair achieves the same clarity through
   redefinition alone (AESIC-REQ-118's explicit override of the naming
   implication), at lower footprint, mirroring AEMIC-001 §25's own
   candidate-1 rejection reasoning (prefer the minimal-footprint fix that
   achieves full correctness over a larger one that achieves no more).
2. *Weaken "both outcomes retrievable" to "Stage 2's outcome retrievable,
   Stage 1's outcome disclosed as advisory-only and non-authoritative if
   still available at read time."* Rejected: this would not resolve the
   contradiction, only relabel it — "if still available" concedes the
   same unsatisfiable promise Finding 1 identified, merely hedged instead
   of fixed.
3. *Embed a verbatim copy of Stage 1's outcome inside the AER itself*
   (selected, AESIC-REQ-118). This is the repair Phase 147L's own
   Finding 1 disposition (§14.1 of that report) already identified as the
   most direct resolution; independently re-confirmed here as the only
   candidate that satisfies "both outcomes retrievable" literally (both
   are directly readable from the one artifact already being retrieved)
   without weakening AESIC-REQ-064/080 or requiring a second persisted
   artifact type (which AESIC-REQ-078's "exactly one artifact type" would
   then also need repairing to permit — a strictly larger, unwarranted
   change).

**Finding 2 — candidates considered:**

1. *Weaken AESIC-REQ-023(b) to "refused" only, deleting "or superseded."*
   Rejected: this would silently break the §11.2 restart matrix's own
   "Registry evolution"/"Decision Template evolution" rows, which
   Phase 147L §8 independently confirmed describe correct, desired
   behavior ("a changed Declaration produces a genuinely different,
   freshly-computed outcome... never silently reconciled with an earlier
   attempt") — deleting supersession would leave a Stage 2 retry after a
   legitimate Registry/template correction permanently stuck refusing,
   contradicting the pipeline's own already-frozen freshness discipline
   (§6.5, IWPC-REQ-144/147).
2. *Allow AER updates in place for the supersession branch.* Rejected —
   foreclosed by AESIC-REQ-054/082's own immutability guarantee, which
   this repair's own governing prompt (§6, Architectural Preservation)
   requires to remain unchanged; every other durable record type in this
   codebase (CHGR, publication records) is immutable, and creating the
   one exception here would be the actual architectural anomaly, not the
   fix.
3. *Key AER storage by `(package_id, evaluation_id)`, `package_id` as
   canonical-lookup convenience key* (selected, AESIC-REQ-119/120/121).
   This is exactly the resolution Phase 147L §8/§14.2 itself proposed as
   the disposition for Finding 2 — independently re-confirmed here as the
   minimal, additive change: `evaluation_id` (AESIC-REQ-098) already
   exists as a per-invocation-unique value for an unrelated reason
   (observability correlation), so reusing it as the second half of a
   compound storage key introduces no new identifier concept, only a new
   use of one this contract already defines.

### 25.4 Requirement Changes

Text-only repairs (identity preserved): AESIC-REQ-019, AESIC-REQ-023,
AESIC-REQ-053, AESIC-REQ-056, AESIC-REQ-057, AESIC-REQ-064, AESIC-REQ-078,
AESIC-REQ-080, AESIC-REQ-081, AESIC-REQ-098, AESIC-REQ-102. New
requirements: AESIC-REQ-118, AESIC-REQ-119, AESIC-REQ-120, AESIC-REQ-121
(§21's Requirement/Test Matrix records all four). Cross-reference-only
updates (no normative change, citation added for clarity): the §11.2
restart-matrix rows for "Registry evolution" and "Decision Template
evolution". No requirement was deleted. No requirement's number was
reused or reassigned. Every requirement not listed above is unchanged,
byte-for-byte, from v1.0.

### 25.5 Architectural Preservation

Every invariant this repair's governing prompt (§6) named is confirmed
unchanged:

- **AES ownership.** AESIC-REQ-005/006 (§5.1) unchanged — AES remains the
  sole orchestrator; this repair touches only AES's own internal
  persistence mechanics (§12.1), never its public interface (§5.2,
  AESIC-REQ-007/008/009, unchanged) or its ownership boundary.
- **Registry ownership.** §7 unchanged entirely — no requirement in §7
  was touched by this repair.
- **Evaluator purity.** AESIC-REQ-005/§4 unchanged — `evaluate()` itself
  is never mentioned by any repaired or new requirement; the equality
  procedure (AESIC-REQ-121) compares `evaluate()`'s own already-produced
  output, never calls `evaluate()` differently or adds a parameter to it.
- **Disclosure-only semantics.** §14 unchanged entirely — no consumer's
  permitted/prohibited usage (AESIC-REQ-089–091) changed; the canonical
  pointer's read-indirection (AESIC-REQ-119 item 2) is transparent to
  every consumer, which already consumed the AER only by reference
  (AESIC-REQ-061, unchanged).
- **Replay architecture.** §11's framing (AESIC-REQ-075/077) unchanged;
  only two restart-matrix rows gained a citation to the now-satisfiable
  mechanism that already-existing row text described.
- **Persistence architecture.** "Exactly one artifact type... the AER"
  (AESIC-REQ-078) unchanged in substance — still exactly one artifact
  *type*; this repair adds a second, small, non-AER pointer artifact
  (the canonical index, AESIC-REQ-119 item 2), which is infrastructure
  for locating AERs, not a second governed artifact type in the sense
  AESIC-REQ-078 enumerates (it carries no `AuthorityEvaluationOutcome`,
  no `citation_text`, and is never itself referenced by Readiness,
  Publication, or CHGR — §14.1's consumer table is unaffected).
- **AER architecture.** AESIC-REQ-051–055/058–061 unchanged; only
  AESIC-REQ-056/057 (content shape of one optional field) and
  AESIC-REQ-053 (keying) were repaired, both text-only.
- **Lifecycle architecture.** §9 entirely unchanged — no requirement in
  §9 was touched.
- **Stage 2 supersession principle.** Strengthened from unsatisfiable to
  satisfiable, never altered in intent: AESIC-REQ-070/071 (§9.4,
  unconditional citation-purpose supersession) are unchanged; this repair
  only makes AESIC-REQ-023(b)'s own already-stated supersession
  *mechanically achievable*.

### 25.6 Compatibility Assessment

Re-confirming AESIC-REQ-113 (§19, unaffected in substance by this repair):
this repair cites no new provision of AEM-001, IWC-001, PEC-001, or
CHGR-001 beyond what v1.0 already cited, and re-cites AEMIC-001
(`evaluate()`'s purity, AEMIC-REQ-074/075/076) and IWPC-001
(IWPC-REQ-144/147's last-write-wins precedent, already cited by Phase
147L §2.10 and now additionally cited by AESIC-REQ-120) without altering
either citation's own meaning. Zero amendments to AEM-001, AEMIC-001,
IWC-001, IWPC-001, PEC-001, or CHGR-001 are required by this repair — the
same zero this contract required at v1.0.

---

## 26. Phase 147L.1 No-Go Boundary Confirmation

Per this phase's own authorizing prompt's explicit No-Go Boundary:
`src/pcae/**` was not modified. No schema file was modified. No test file
was modified. `.pcae/policy.toml` was not modified. No Authority
Evaluation Service was implemented. No Decision Template Resolution
capability was implemented. No Authority Registry was implemented. No
Authority Evaluation Record persistence was implemented. No replay
mechanism was implemented. Runtime was not modified. No CLI command was
added. No plugin was added. Interactive Workflow code was not modified.
Publication Coordinator code was not modified. CHGR construction code was
not modified. No contract other than AESIC-001 was amended (AEM-001,
AEMIC-001, IWC-001, IWPC-001, PEC-001, CHGR-001 all remain byte-for-byte
unchanged). Only this contract document
(`docs/contracts/AESIC-001-authority-evaluation-service-integration-contract.md`),
the companion verification document
(`docs/verification/PHASE_147L1_CONTRACT_REPAIR.md`), and ordinary
task/phase bookkeeping files changed throughout this phase, confirmed by
`git status --short` at finalization.

---

## 27. Overall Verdict (Phase 147L.1, v1.1 — historical)

**Superseded by Phase 147L.3's own Overall Verdict, §31 below.** This §27
is retained unchanged as the historical record of Phase 147L.1's own
repair verdict, exactly as §23 was retained unchanged alongside this
section when Phase 147L.1 was itself completed. It does not restate
current status; §31 does.

**AESIC-001 v1.1 REPAIRED.**

Both Major findings from Phase 147L (Finding 1, Finding 2) are fully
resolved (§25.2), each by an additive, in-place clarification that
preserves every requirement number, every component boundary, and every
architectural invariant named in this repair's governing prompt (§25.5).
The Minor finding (Finding 3) and the Informational finding (Finding 4)
are resolved as unavoidable byproducts of the two Major repairs, not
independently expanded scope (§25.1). Zero new ambiguities were
introduced: every new requirement (AESIC-REQ-118–121) states a complete,
falsifiable rule, not a partial one, and every repaired requirement's text
was checked against every other requirement it interacts with (§25.4's
enumeration; the companion verification document's §5 restates this
checking in matrix form). Zero cross-contract amendments are required
(§25.6, reconfirming AESIC-REQ-113 unchanged). This contract remains
fully implementable entirely from its own text, exactly as AESIC-REQ-110
(§17) requires.

---

## 28. Recommended Next Phase (Phase 147L.1, historical)

**147L.2 — AESIC-001 Contract Repair Independent Verification.** That
phase shall independently verify that the repairs introduced in this v1.1
revision (§25) resolve Finding 1 and Finding 2 (Phase 147L) without
altering the architecture (§25.5's preserved-invariant list) or
introducing new inconsistencies (§27's own "zero new ambiguities" claim,
independently re-checked, not merely trusted). It shall remain
verification-only and make no implementation change. Only after
successful independent verification should the project proceed to
147M — Authority Evaluation Integration Implementation.

**This recommendation is not an authorization.**

**Discharged.** Phase 147L.2 executed exactly this recommendation
(`docs/verification/PHASE_147L2_AESIC_REPAIR_INDEPENDENT_VERIFICATION.md`),
verdict AESIC-001 v1.1 VERIFIED WITH NON-BLOCKING FINDINGS, confirming
both Finding 1 and Finding 2 fully resolved and surfacing two new
Non-Blocking findings (§3.1, Major — the `stage_1_outcome_ref`
interface-channel gap; §3.2, Minor — the canonical pointer's
tamper-evidence gap) that §29 below repairs. §32 below states this
repair's own recommended next phase.

---

## 29. Phase 147L.3 Repair Confirmation

**Version:** 1.2
**Predecessor:** AESIC-001 v1.1 (Phase 147L.1)
**Repaired by:** Phase 147L.3 — AESIC-001 Final Contract Repair
**Baseline findings:** Phase 147L.2 — AESIC-001 Contract Repair
Independent Verification
(`docs/verification/PHASE_147L2_AESIC_REPAIR_INDEPENDENT_VERIFICATION.md`),
verdict AESIC-001 v1.1 VERIFIED WITH NON-BLOCKING FINDINGS, one new Major
finding (§3.1, interface-channel gap), one new Minor finding (§3.2,
pointer tamper-evidence gap); both findings explicitly Non-Blocking

### 29.1 Scope

This repair is narrowly scoped to Phase 147L.2's own two new findings
(§3.1: `stage_1_outcome_ref` has no defined interface channel into
`evaluate_stage_2`; §3.2: the canonical pointer index has no defined
tamper-evidence mechanism), per this phase's own authorizing prompt. No
other AESIC-001 requirement, invariant, component boundary, or
predecessor-contract citation was altered beyond what closing these two
findings required. No implementation, schema, or runtime change was made
(§30 confirms).

### 29.2 Findings Repaired

**Finding §3.1 — [Major] `stage_1_outcome_ref`'s content has no defined
channel into `evaluate_stage_2`.** Repaired by introducing
`Stage1EvaluationResult` (AESIC-REQ-122, §5.2.1) as the unmodified return
type of `evaluate_stage_1` (repairing AESIC-REQ-007's signature) and as a
new, optional `stage_1_result` parameter on `evaluate_stage_2` (repairing
AESIC-REQ-007/012). The caller supplies back, verbatim, the same object
AES already gave it from a prior `evaluate_stage_1(session=session)`
call — no new persistence, no ambient state, no `Session` field. AES
validates the supplied value against the concurrently-supplied `session`
through a mandatory four-check sequence (AESIC-REQ-123: structural
validity, session binding via the already-frozen `Session.session_id`,
identity binding, decision-template binding), refusing via a new, closed
exception taxonomy (`Stage1HandoffInvalidError`, AESIC-REQ-124) on any
failure, and proceeding with `stage_1_outcome_ref` absent when
`stage_1_result` is `None` (AESIC-REQ-125) — never an error. AESIC-REQ-128
freezes the complete Stage 2 invocation contract this closure requires,
per the authorizing prompt's own §5 demand.

**Finding §3.2 — [Minor] Canonical pointer index has no defined
tamper-evidence mechanism.** Repaired by adding a `pointer_digest` field
to the pointer's own persisted content (repairing AESIC-REQ-119 item 2)
and a new, mandatory read-time verification obligation (AESIC-REQ-126):
recompute `pointer_digest` over the pointer's own other fields, and
cross-check the pointer's copy of `record_digest` against the referenced
AER's own self-carried digest, before treating any pointer as canonical.
Either mismatch raises a new `CanonicalPointerCorruptError`
(AESIC-REQ-127), fail-closed, with recovery an operator-owned action
mirroring the existing "Digest mismatch" disposition (§13).

### 29.3 Candidate Repairs Evaluated

**Finding §3.1 — candidates considered:**

1. *Relax AESIC-REQ-057's "MUST carry... whenever a Stage 1 evaluation...
   preceded" to a caller-provided, best-effort `SHOULD`* (Phase 147L.2's
   own candidate (b)). Rejected: this resolves the contradiction by
   weakening the guarantee Finding 1 (Phase 147L) originally required
   AESIC-REQ-057 to make ("both outcomes retrievable... structurally
   visible"), reintroducing exactly the silent-permanent-vacuity failure
   mode Phase 147L.2 §3.1's own concrete failure scenario, outcome (a),
   already identified as "bad." A `SHOULD` that every real caller can
   never actually satisfy (because the interface still gives it no
   channel) is not a genuine relaxation, only a relabeling of the same gap.
2. *Invent an undisclosed side channel (global, cache, Session-adjacent
   store) inside a future implementation, leaving the contract itself
   silent.* Rejected — foreclosed by this repair's own governing prompt
   (§5: "Do not leave implementers to choose among: adding an ungoverned
   extra argument... reading ambient process state..."), and independently
   rejected on the merits: Phase 147L.2 §3.1's own concrete failure
   scenario, outcome (b), already identified this as producing an
   undisclosed violation of AESIC-REQ-012, AESIC-REQ-017, or AESIC-REQ-060.
3. *Add an optional `stage_1_result: Optional[Stage1EvaluationResult]`
   parameter to `evaluate_stage_2`, sourced from the caller's own
   in-memory retention of `evaluate_stage_1`'s return value* (selected,
   AESIC-REQ-007/122/123/124/125/128). This is exactly the disposition
   Phase 147L.2 §3.1's own candidate (a) identified as "more consistent
   with AESIC-REQ-057's own stated purpose" — independently re-confirmed
   here as the only candidate that closes the gap without weakening
   AESIC-REQ-057's guarantee, without inventing an undisclosed channel,
   and without widening AES's own closed-interface hardening intent
   (AESIC-REQ-008, §15) beyond what disagreement-visibility already
   requires: the new parameter carries only an already-computed outcome
   object back to its own producer, never a bare identity/template
   string, and is validated, never trusted blindly.

**Finding §3.2 — candidates considered:**

1. *Leave the pointer's integrity implicitly covered by the AER's own
   digest.* Rejected — independently re-derived to be false: Phase 147L.2
   §3.2's own second failure variant (a corrupted `record_id` naming a
   different, still-valid, still-self-consistent AER) produces no AER-level
   digest mismatch at all, since the wrongly-referenced AER's own digest
   still matches itself. The AER's digest cannot, by construction, detect
   corruption of a field that lives outside the AER.
2. *Extend the pointer's concurrency treatment (last-write-wins,
   AESIC-REQ-120) to also cover integrity, i.e. treat pointer corruption
   as another disclosed, accepted, non-authority-relevant outcome.*
   Rejected — Phase 147L.2 §3.2 itself distinguishes these: concurrency
   (which write wins) is a disclosed design choice with no wrong answer;
   integrity (whether the pointer's content is internally consistent and
   matches what it claims to reference) is not a design choice, it is a
   correctness property every other durable record in this codebase
   already gets (AESIC-REQ-055 for the AER itself) — treating pointer
   corruption as "accepted" would be a genuine weakening, not a
   clarification, and would violate AESIC-REQ-093's "SHALL NOT weaken any
   mitigation in §15's table."
3. *Add a `pointer_digest` field (computed the same way `record_digest`
   already is) plus a mandatory read-time cross-check against the
   referenced AER's own digest* (selected, AESIC-REQ-119/126/127). This is
   exactly the first of the two candidates Phase 147L.2 §3.2's own
   disposition already named ("requiring the pointer's own write to
   include a digest of its own content... mirroring AESIC-REQ-055's
   pattern") — independently re-confirmed here as the minimal, additive
   change requiring no new I/O beyond the pointer read this contract
   already performs (AESIC-REQ-102, repaired), and as strictly stronger
   than the report's second-named alternative (a read-time
   re-verification step alone, without a pointer-native digest, would not
   detect corruption of the pointer's own `evaluation_id`/`package_id`
   fields, only of `record_id`/`record_digest`) — selecting the candidate
   that detects a strictly larger corruption surface at equal cost.

### 29.4 Requirement Changes

Text-only repairs (identity preserved): AESIC-REQ-007, AESIC-REQ-010,
AESIC-REQ-012, AESIC-REQ-057, AESIC-REQ-076 (three new restart-matrix
rows), AESIC-REQ-102, AESIC-REQ-119 (item 2 gains `pointer_digest`).
New requirements: AESIC-REQ-122, AESIC-REQ-123, AESIC-REQ-124,
AESIC-REQ-125, AESIC-REQ-126, AESIC-REQ-127, AESIC-REQ-128 (§21's
Requirement/Test Matrix records all seven). Table-only additions (new
rows under an existing, unrenumbered requirement — mirrors the
Phase 147L.1 precedent of adding restart-matrix rows without a new
requirement number): two new rows in §13's Failure Ownership matrix
(under AESIC-REQ-087) and two new rows in §15's security mitigation table
(under AESIC-REQ-092). No requirement was deleted. No requirement's
number was reused or reassigned. Every requirement not listed above is
unchanged, byte-for-byte, from v1.1.

### 29.5 Architectural Preservation

Every invariant this repair's governing prompt (§11) named is confirmed
unchanged:

- **AES sole lifecycle orchestrator.** AESIC-REQ-005/006 (§5.1) untouched
  by this repair — `stage_1_result` validation (AESIC-REQ-123) and pointer
  verification (AESIC-REQ-126) are both internal mechanics of AES's own,
  already-owned responsibilities (evaluating, persisting), not a new
  orchestration role or a widening of who orchestrates what.
- **Decision Template Resolution ownership.** §6 entirely untouched — no
  requirement in §6 appears in §29.4's changed list.
- **Registry ownership.** §7 entirely untouched — no requirement in §7
  appears in §29.4's changed list.
- **Evaluator purity/determinism/Registry exclusion.** `evaluate()` is
  never named as an actor in any repaired or new requirement; validation
  of `stage_1_result` (AESIC-REQ-123) compares already-produced outcome
  fields, exactly as AESIC-REQ-121's own equality procedure already does
  for an unrelated purpose — it does not call `evaluate()` differently,
  add a parameter to it, or grant it Registry access.
- **Publication Coordinator publication-only ownership.** PEC-001,
  untouched; §14's consumer table is unaffected by this repair — no
  consumer row was amended.
- **Disclosure-only semantics / non-gating guarantees.** §14 entirely
  untouched by this repair.
- **Stage 1 advisory semantics.** AESIC-REQ-062–065 (§9.1) unchanged in
  substance — the new retention/absence note added there (before
  AESIC-REQ-064) restates, never narrows, the existing rule that Stage 1
  is caller-invoked, caller-held, and non-persisted.
- **Stage 2 unconditional supersession.** AESIC-REQ-070/071 (§9.4)
  byte-for-byte unchanged — untouched by this repair.
- **Immutable AER history.** AESIC-REQ-054/082/119 item 1 unchanged in
  substance — the pointer's own new `pointer_digest` field is metadata
  *about* the pointer, not a change to the AER's own immutability.
- **Two-tier compound-key model.** AESIC-REQ-119/120/121 unchanged in
  their supersession/concurrency/equality logic — only item 2's content
  gained one additional field (`pointer_digest`) and one additional
  mandatory read-time check; the compound-keyed primary store (item 1) is
  untouched.
- **Replay observational equivalence.** AESIC-REQ-075/077 unchanged; the
  three new restart-matrix rows (AESIC-REQ-076) describe newly-defined
  behavior at newly-named restart points, they do not alter any
  previously-defined row's own claim.
- **Zero execution capability.** This repair defines contract text only —
  no requirement introduced or repaired by this phase implements
  anything; §30 confirms no `src/pcae/**`, schema, test, or runtime file
  was touched.

**Falsification attempted:** could AESIC-REQ-123's validation logic be
read as implicitly requiring AES to gain a new Stage-1-outcome persistence
capability (to look something up against) — reopening Finding 1 (Phase
147L) or AESIC-REQ-064/080/078's "exactly one artifact type" framing?
Checked directly: AESIC-REQ-123's four checks compare the *supplied*
`stage_1_result`'s own fields against the *concurrently-supplied*
`session`'s own fields — both already in AES's hands for this one call,
neither requiring a lookup against any store, past evaluation, or Stage-1
persistence of any kind. No widening found.

### 29.6 Compatibility Assessment

Re-confirming AESIC-REQ-113 (§19, unaffected in substance by this
repair): this repair cites exactly one new provision beyond what v1.0/v1.1
already cited — `Session.session_id` (IWC-001, already-frozen,
already-populated at the exact call site this integration already reads
`owner_identity`/`template_ref`/`subject_ref` from) — and re-cites
AEMIC-001 (`AuthorityEvaluationOutcome`'s own unmodified shape,
AEMIC-REQ-021), AESIC-REQ-055/083 (the AER's own digest pattern, now
additionally applied to the pointer), and AESIC-REQ-098 (unmodified
per-invocation `evaluation_id` uniqueness) without altering any of their
own meaning. Zero amendments to AEM-001, AEMIC-001, IWC-001, IWPC-001,
PEC-001, or CHGR-001 are required by this repair — the same zero this
contract required at v1.0 and reconfirmed at v1.1 (§19's own
"Compatibility reconfirmation (Phase 147L.3)" paragraph states this in
full).

---

## 30. Phase 147L.3 No-Go Boundary Confirmation

Per this phase's own authorizing prompt's explicit No-Go Boundary:
`src/pcae/**` was not modified. No schema file was modified. No test file
was modified. No CLI surface was added. No plugin was added. No Authority
Evaluation Service was implemented. No Decision Template Resolution
capability was implemented. No Authority Registry was implemented. No
Authority Evaluation Record persistence was implemented. No canonical
pointer storage was implemented. No replay mechanism was implemented.
Runtime was not modified. Interactive Workflow code was not modified.
Publication Coordinator code was not modified. CHGR construction code was
not modified. No contract other than AESIC-001 was amended (AEM-001,
AEMIC-001, IWC-001, IWPC-001, PEC-001, CHGR-001 all remain byte-for-byte
unchanged). No implementation was authorized by this repair (§20,
AESIC-REQ-116/117, unaffected). Only this contract document
(`docs/contracts/AESIC-001-authority-evaluation-service-integration-contract.md`),
the companion verification document
(`docs/verification/PHASE_147L3_AESIC_FINAL_CONTRACT_REPAIR.md`), and
ordinary task/phase bookkeeping files changed throughout this phase,
confirmed by `git status --short` at finalization.

---

## 31. Overall Verdict (Phase 147L.3, v1.2 — historical)

**Superseded by Phase 147L.5's own Overall Verdict, §35 below.** This §31
is retained unchanged as the historical record of Phase 147L.3's own
repair verdict, exactly as §23 and §27 were retained unchanged alongside
this section when Phase 147L.1 and Phase 147L.3 were themselves
completed. It does not restate current status; §35 does.

**AESIC-001 v1.2 REPAIRED.**

Both Non-Blocking findings from Phase 147L.2 (§3.1 Major,
interface-channel gap; §3.2 Minor, pointer tamper-evidence gap) are fully
resolved (§29.2), each by an additive, in-place repair that preserves
every requirement number, every component boundary, and every
architectural invariant named in this repair's governing prompt (§29.5).
Zero new ambiguities were introduced: every new requirement
(AESIC-REQ-122–128) states a complete, falsifiable rule, and every
repaired requirement's text was checked against every other requirement
it interacts with (§29.4's enumeration). The Stage 2 invocation contract
is now complete and unambiguous (AESIC-REQ-128): every input's source,
derivation, and validator is named, and no implementer choice remains
among the channels the authorizing prompt's §5 explicitly closed. The
canonical pointer is now tamper-evident (AESIC-REQ-126), fail-closed on a
detected mismatch (AESIC-REQ-127), with recovery explicitly an
operator-owned action and the underlying AER history unaffected. Replay
and concurrency semantics remain coherent (§29.5's replay/concurrency
rows). No new contradiction was introduced (§29.5's falsification
attempt). All architectural invariants remain preserved (§29.5). Zero
predecessor-contract amendment is required (§29.6). This contract remains
fully implementable entirely from its own text, exactly as AESIC-REQ-110
(§17) requires.

---

## 32. Recommended Next Phase (Phase 147L.3, historical)

**147L.4 — AESIC-001 Final Contract Repair Independent Verification.**
That phase shall independently verify AESIC-001 v1.2 against the two
findings from Phase 147L.2 (§3.1, §3.2), re-read the complete repaired
contract in full, and perform fresh interface, replay, persistence,
pointer-integrity, concurrency, and cross-contract attacks. It shall
remain verification-only and make no contract or implementation change.
Only after successful 147L.4 verification should the project proceed to
147M — Authority Evaluation Integration Implementation.

**This recommendation is not an authorization.**

**Discharged.** Phase 147L.4 executed exactly this recommendation
(`docs/verification/PHASE_147L4_AESIC_FINAL_REPAIR_INDEPENDENT_VERIFICATION.md`),
verdict AESIC-001 v1.2 VERIFIED WITH NON-BLOCKING FINDINGS, confirming
both Finding §3.1 and Finding §3.2 fully resolved and surfacing two new
Non-Blocking findings (Finding A, Major — the idempotency-no-op-vs.-
mandatory-`stage_1_outcome_ref` contradiction; Finding B, Minor — the
missing AER-commit/pointer-write restart-matrix row) that §33 below
repairs. §36 below states this repair's own recommended next phase.

---

## 33. Phase 147L.5 Repair Confirmation

**Version:** 1.3
**Predecessor:** AESIC-001 v1.2 (Phase 147L.3)
**Repaired by:** Phase 147L.5 — AESIC-001 Stage 1 Idempotency and
Restart-Matrix Contract Repair
**Baseline findings:** Phase 147L.4 — AESIC-001 Final Contract Repair
Independent Verification
(`docs/verification/PHASE_147L4_AESIC_FINAL_REPAIR_INDEPENDENT_VERIFICATION.md`),
verdict AESIC-001 v1.2 VERIFIED WITH NON-BLOCKING FINDINGS, one new Major
finding (Finding A, idempotency/evidence-retention contradiction), one new
Minor finding (Finding B, restart-matrix completeness gap); both findings
explicitly Non-Blocking

### 33.1 Scope

This repair is narrowly scoped to Phase 147L.4's own two new findings
(Finding A: the Stage 2 idempotency no-op branch can silently discard a
validated `stage_1_result`, contradicting AESIC-REQ-057's
mandatory-when-supplied guarantee; Finding B: §11.2's restart matrix has no
row for a crash between the AER's compound-key commit and the canonical
pointer's own write), per this phase's own authorizing prompt. No other
AESIC-001 requirement, invariant, component boundary, or
predecessor-contract citation was altered beyond what closing these two
findings required. No implementation, schema, or runtime change was made
(§34 confirms).

### 33.2 Findings Repaired

**Finding A — [Major] Idempotency no-op can silently discard a validated
`stage_1_result`.** Repaired by extending the "inputs unchanged"
comparison (AESIC-REQ-121, repaired) to also compare Stage 1 evidence,
using a new, deterministic Stage-1-evidence-equivalence definition
(AESIC-REQ-129, new): both absent is equivalent; exactly one absent is
never equivalent; both present are compared field-by-field on the wrapped
`AuthorityEvaluationOutcome` (excluding `evaluated_at` and
`evaluation_id`, for the same reasons AESIC-REQ-121's own pre-existing
comparison already excludes `evaluated_at` and AESIC-REQ-098's own
per-invocation uniqueness makes `evaluation_id` unsuitable as an
equivalence key). AESIC-REQ-023 (repaired) now states explicitly that the
no-op branch (a) is reachable only when the two are also
Stage-1-evidence-equivalent, and the supersession branch (b) now
explicitly includes the case where a validated `stage_1_result` supplied
on this attempt is not equivalent to the canonical AER's own
`stage_1_outcome_ref` — including the case where the canonical AER
carries none at all. AESIC-REQ-057 (clarified) now states explicitly that
its mandatory-when-supplied guarantee holds for the AER actually returned
on every attempt, including a no-op, closing the exact gap Finding A
identified.

**Finding B — [Minor] Missing restart-matrix row for a crash between AER
commit and pointer write.** Repaired by adding two new restart-matrix rows
under AESIC-REQ-076 (mirroring the Phase 147L.3 precedent of adding rows
without a new requirement number) and a new normative rule,
AESIC-REQ-130, defining the complete recovery model: a committed-but-not-
yet-pointed-to AER is an uncommitted candidate, never automatically
canonical; recovery is retry, never reconstruction from the primary
store's own ordering (which does not exist independently of the pointer);
a retry recomputes fresh and either reaches an existing, Stage-1-evidence-
equivalent canonical AER (no-op) or persists another new compound-keyed
AER and re-attempts the pointer write; the original crash's own
uncommitted candidate may remain permanently unreferenced — disclosed,
harmless surplus history, never data loss. A new exception,
`CanonicalPointerUpdateFailedError` (AESIC-REQ-131, new), covers the
distinct, same-process case where the pointer write fails synchronously
(not a process crash) — fail-closed, never returning success or a stale
result, with recovery again via caller retry.

### 33.3 Considered Behavioral Models

**Finding A — models considered (per this phase's own authorizing
prompt §9):**

1. *Model 1 — Stage 1 evidence participates in idempotency equivalence*
   (selected, AESIC-REQ-121/129). A same-outcome no-op is permitted only
   when the existing canonical AER is also Stage-1-evidence-equivalent to
   this attempt's own supplied evidence; otherwise a new, superseding AER
   is required. This reuses the exact mechanism (extend AESIC-REQ-121's
   equality procedure) this contract has already used twice before
   (Phase 147L.1 to define the procedure itself, closing Finding 2/3) —
   the smallest-footprint change consistent with established precedent,
   requiring no new I/O (§12.1) and no new component.
2. *Model 2 — valid newly supplied Stage 1 evidence always causes
   supersession.* On inspection, this is not a distinct mechanism from
   Model 1 but the same normative outcome described from the opposite
   direction ("supersede whenever not equivalent" is the logical
   complement of "no-op only when equivalent"). Adopting Model 1's
   equality-procedure framing subsumes Model 2's own stated behavior
   exactly — both models were found, on independent analysis, to specify
   the same deterministic result for every scenario in §10/§18 of the
   authorizing prompt; Model 1 is retained as the operative framing
   because it fits the contract's own existing structural pattern
   (AESIC-REQ-023 delegates its branch decision to a single named equality
   procedure) rather than introducing a second, parallel supersession
   trigger alongside it.
3. *Model 3 — explicit refusal of late Stage 1 enrichment.* Rejected: a
   refusal does not *represent* the supplied evidence — it discards the
   call outright — failing the authorizing prompt's own completion
   criterion (§22: "valid supplied Stage 1 evidence cannot be silently
   discarded" is satisfied by non-silent discard under Model 3, but the
   stronger, separately-listed §10 requirement "validated Stage 1 evidence
   retention" is not). Model 3 would also introduce a behavioral
   discontinuity absent from Models 1/2: a call pattern that always
   succeeded before this repair (idempotent retry, `stage_1_result`
   supplied or not) would now fail outright for a caller that supplies
   *new, valid* evidence on a retry — a strictly larger, unwarranted
   behavior change for a narrowly-scoped repair.

**Finding B — the authorizing prompt did not offer alternative models**
(§12/§13 specify the required properties directly); this repair verified
those properties are satisfiable by the single recovery model described in
§33.2 above and found no alternative construction that satisfies them at
lower footprint — in particular, any model relying on automatic pointer
reconstruction from the primary store's own AER ordering was rejected for
the same reason AESIC-REQ-126 item 4 already rejected automatic pointer
rebuild for the corruption case: no total write-order across restarts is
recorded independently of the pointer itself.

### 33.4 Selected Idempotency Model

**Model 1, as described in §33.3 above, is frozen**: AESIC-REQ-121's
equality procedure is the sole and exclusive determinant of the
AESIC-REQ-023(a)/(b) branch decision, now covering both
citation/outcome-equivalence (unchanged from v1.2) and Stage-1-evidence-
equivalence (AESIC-REQ-129, new). No second, independent supersession
trigger exists alongside it.

### 33.5 Stage 1 Evidence Identity

Per AESIC-REQ-129 (§12.1): two Stage 1 evidence states are compared on
`session_id` (trivially satisfied whenever both derive from
AESIC-REQ-123's own session-binding check), and every field of the wrapped
`AuthorityEvaluationOutcome` excluding `evaluated_at` (metadata neither
`evaluate()` nor this test branches on) and excluding `evaluation_id`
(guaranteed unique per invocation by AESIC-REQ-098's own construction, and
therefore unsuitable as an equivalence key — including it would make every
distinct-but-substantively-identical Stage 1 invocation "not equivalent,"
defeating the equivalence test's purpose). This basis relies on no object
identity, no process memory, and no implementation-specific
serialization — every compared field is a plain value already defined by
AEMIC-001 §6 or AESIC-REQ-122 — so the comparison is deterministic across
restart and across independent implementations.

### 33.6 Concurrency and Replay Semantics

Two or more Stage 2 attempts for the same `package_id`, some supplying
different Stage 1 evidence, are governed by the same, unchanged
AESIC-REQ-120 last-write-wins pointer semantics: each attempt's own
equivalence classification (AESIC-REQ-129) determines whether it persists
a new AER at all, and the existing concurrency model (no new mechanism)
determines which persisted AER's pointer write completes last and
therefore becomes canonical. A Stage 2 replay for an already-canonical
`package_id` is unaffected by this repair: AESIC-REQ-023(a)'s own no-op
path returns the already-persisted AER without re-invoking or re-validating
any `stage_1_result` (unchanged from v1.2). Malformed or cross-session/
mismatched `stage_1_result` values continue to be rejected by AESIC-REQ-123
before the idempotency comparison is ever reached (unaffected — validation
precedes comparison unconditionally, restated explicitly in AESIC-REQ-023's
own repaired text). A detected pointer-write failure after a new AER
commit (Finding B) is handled per AESIC-REQ-130/131, independent of
Finding A's own idempotency-comparison repair.

### 33.7 Requirement Changes

**Text-only repairs (identity preserved):** AESIC-REQ-010, AESIC-REQ-023,
AESIC-REQ-057, AESIC-REQ-076 (two new restart-matrix rows), AESIC-REQ-102,
AESIC-REQ-121 (extended comparison), AESIC-REQ-087's table (one new row,
`CanonicalPointerUpdateFailedError`, under the existing, unrenumbered
requirement — mirrors the Phase 147L.1/147L.3 precedent of adding rows
without a new requirement number).

**New requirements:** AESIC-REQ-129, AESIC-REQ-130, AESIC-REQ-131 (§21's
Requirement/Test Matrix records all three with falsifiability anchors).

Every requirement the authorizing prompt's §14 named for audit
(AESIC-REQ-019, 023, 053–057, 075–086, 098, 102–104, 118–128) was
individually re-checked: only AESIC-REQ-010, 023, 057, 076, 102, and 121
required a text change; the remainder were confirmed unaffected in
substance — each was re-read and found to already be compatible with, or
entirely orthogonal to, this repair's two new mechanisms. No requirement
was deleted. No requirement's number was reused or reassigned.

### 33.8 Architectural Preservation

Every invariant this repair's governing prompt (§16) named is confirmed
unchanged:

- **AES sole lifecycle orchestrator.** AESIC-REQ-005/006 (§5.1) untouched
  by this repair — the extended equality comparison (AESIC-REQ-121/129)
  and the pointer-establishment retry rule (AESIC-REQ-130) are both
  internal mechanics of AES's own, already-owned responsibilities
  (evaluating, persisting), not a new orchestration role.
- **Decision Template Resolution ownership.** §6 entirely untouched.
- **Registry lookup-only ownership.** §7 entirely untouched.
- **Evaluator purity and determinism / Registry exclusion.** `evaluate()`
  is never named as an actor in any repaired or new requirement;
  AESIC-REQ-129's comparison consumes already-produced `outcome` fields
  only, exactly as AESIC-REQ-121's own pre-existing comparison already
  does.
- **Stage 1 advisory semantics.** AESIC-REQ-062–065 unchanged — Stage 1's
  outcome remains advisory-only; this repair only changes whether *Stage
  2's own idempotency classification* accounts for it, never Stage 1's own
  non-authoritative status.
- **Stage 2 unconditional supersession.** AESIC-REQ-070/071 byte-for-byte
  unchanged — untouched by this repair.
- **Immutable AER history.** AESIC-REQ-054/082/119 item 1 unchanged in
  substance — this repair never mutates, updates, or deletes an AER; a
  supersession triggered by Finding A's repair still produces a genuinely
  new, distinct, immutable AER exactly as AESIC-REQ-023(b) already
  specified.
- **Two-tier compound-key storage model.** AESIC-REQ-119/120 unchanged in
  their own text — only AESIC-REQ-121's comparison logic (item 2's own
  downstream consumer) was extended.
- **Canonical-pointer integrity.** AESIC-REQ-126/127 entirely untouched —
  Finding B's own repair (AESIC-REQ-130/131) governs a disjoint condition
  (a pointer that has not yet been written, or whose write failed) from
  what AESIC-REQ-126/127 govern (a pointer that is present but internally
  inconsistent); the two mechanisms do not overlap or contradict.
- **Replay observational equivalence.** AESIC-REQ-075/077 unchanged; the
  two new restart-matrix rows (AESIC-REQ-076) describe newly-defined
  behavior at a newly-named restart point, and AESIC-REQ-130 item 5
  explicitly ties that behavior back to AESIC-REQ-077's own requirement.
- **Publication Coordinator publication-only ownership.** PEC-001,
  untouched; §14's consumer table is unaffected by this repair.
- **Disclosure-only semantics / non-gating guarantees.** §14 entirely
  untouched by this repair.
- **Unchanged runtime capability.** This repair defines contract text
  only — no requirement introduced or repaired by this phase implements
  anything; §34 confirms no `src/pcae/**`, schema, test, or runtime file
  was touched.

**Falsification attempted:** could AESIC-REQ-129's equivalence comparison
be read as implicitly requiring AES to gain a new Stage-1-outcome
persistence or lookup capability, reopening Finding 1 (Phase 147L) or
AESIC-REQ-064/078/080's "exactly one artifact type" framing? Checked
directly: AESIC-REQ-129 compares only fields already present in AES's
hands for this one call — the canonical AER's own already-retrieved
`stage_1_outcome_ref` (part of the same document AESIC-REQ-121's
comparison (1) already reads) and this attempt's own in-memory
`stage_1_result` parameter — no lookup against any Stage-1-specific store,
past evaluation, or independent persistence of any kind. No widening
found.

### 33.9 Compatibility Assessment

Re-confirming AESIC-REQ-113 (§19, unaffected in substance by this
repair): this repair introduces no new citation of AEM-001, AEMIC-001,
IWC-001, IWPC-001, PEC-001, or CHGR-001 beyond what v1.2 already cited —
AESIC-REQ-129's comparison re-uses the same `AuthorityEvaluationOutcome`
shape (AEMIC-001 §6) and `Session.session_id` field (IWC-001) v1.2's own
AESIC-REQ-122/123 already cite, without altering either citation's own
meaning. Zero amendments to AEM-001, AEMIC-001, IWC-001, IWPC-001,
PEC-001, or CHGR-001 are required by this repair — the same zero this
contract required at v1.0 and reconfirmed at v1.1 and v1.2.

---

## 34. Phase 147L.5 No-Go Boundary Confirmation

Per this phase's own authorizing prompt's explicit No-Go Boundary:
`src/pcae/**` was not modified. No schema file was modified. No test file
was modified. No CLI surface was added. No plugin was added. No Authority
Evaluation Service was implemented. No Stage 1 transport was implemented.
No Authority Evaluation Record persistence was implemented. No pointer
recovery was implemented. No Registry was implemented. Runtime was not
modified. No contract other than AESIC-001 was amended (AEM-001,
AEMIC-001, IWC-001, IWPC-001, PEC-001, CHGR-001 all remain byte-for-byte
unchanged). No implementation was authorized by this repair (§20,
AESIC-REQ-116/117, unaffected). The repair was not broadened beyond
Finding A and Finding B — no other AESIC-001 requirement, invariant, or
component boundary was altered. 147M was not authorized. Only this
contract document
(`docs/contracts/AESIC-001-authority-evaluation-service-integration-contract.md`),
the companion verification document
(`docs/verification/PHASE_147L5_AESIC_IDEMPOTENCY_RESTART_CONTRACT_REPAIR.md`),
and ordinary task/phase bookkeeping files changed throughout this phase,
confirmed by `git status --short` at finalization.

---

## 35. Overall Verdict (Phase 147L.5, v1.3 — current)

**AESIC-001 v1.3 REPAIRED.**

Finding A (Major) is fully resolved: valid supplied Stage 1 evidence can
no longer be silently discarded by the idempotency no-op branch
(AESIC-REQ-121/129, AESIC-REQ-023 repaired); idempotency remains fully
deterministic (AESIC-REQ-129's own closed, ordered comparison rule);
concurrent behavior remains defined (AESIC-REQ-120, unchanged, now
governing a correctly-widened set of "changed" classifications). Finding B
(Minor) is fully represented in the restart matrix (two new rows under
AESIC-REQ-076, plus AESIC-REQ-130/131's own normative rules); crash
recovery is deterministic (retry, never reconstruction; disclosed,
harmless surplus history, never data loss). Immutable AER history and
canonical-pointer integrity (AESIC-REQ-126/127) remain fully preserved and
untouched — Finding B's own repair governs a disjoint failure condition.
No new contradiction was introduced (§33.7's requirement-by-requirement
audit, §33.8's architectural-preservation table, §33.8's own falsification
attempt). No predecessor-contract amendment is required (§33.9). This
contract remains fully implementable entirely from its own text, exactly
as AESIC-REQ-110 (§17) requires.

---

## 36. Recommended Next Phase

**147L.6 — AESIC-001 Idempotency and Restart Repair Independent
Verification.** That phase shall independently verify AESIC-001 v1.3
against the finalized Finding A and Finding B from Phase 147L.4. It shall
independently reconstruct both findings; verify Stage 1 evidence retention
across idempotency, supersession, concurrency, restart, and replay; verify
the post-AER/pre-pointer crash recovery rule; re-read the complete
contract in full; perform fresh adversarial analysis; and make no contract
or implementation change. Only after successful 147L.6 verification should
the project proceed to 147M — Authority Evaluation Integration
Implementation.

**This recommendation is not an authorization.**

---

**End of AESIC-001 v1.3.**
