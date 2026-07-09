# Phase 125F - Next Architecture Direction Decision Review

## 1. Purpose

Phase 125F documents the formal architectural decision for PCAE's next
chapter, using the evidence assembled across 125A-125E and operating
inside the 125B decision contract's Section 6 constraints.

This phase selects exactly one next architectural chapter. It does not
implement it. No source code, test code, or schema changes occur in
this phase. Selection here starts — it does not complete — the 125B §6
three-step sequence: this decision authorizes 126A (architecture) to
begin; it does not itself constitute the architecture, contract, or
verification steps that sequence requires before implementation may
occur.

## 2. Evidence Reviewed

This decision is based on the complete Track 125 evidence chain:

- **Repository Intelligence chapter review** (125A,
  `docs/PHASE_125_REPOSITORY_INTELLIGENCE_CHAPTER_REVIEW_AND_NEXT_DIRECTION_ARCHITECTURE.md`)
  — established that Repository Intelligence Version 1 (Tracks
  119-124) implemented only one of eight frozen schema families
  (Repository Knowledge Snapshot), identified the remaining
  architectural gaps, and evaluated six candidates at an
  architecture-document level.
- **125B decision contract**
  (`docs/PHASE_125_NEXT_ARCHITECTURE_DIRECTION_CONTRACT_FREEZE.md`) —
  froze the candidate domains, nine evaluation principles, and the
  three-step architecture -> contract -> verification decision sequence
  this phase operates inside.
- **125C contract verification**
  (`docs/PHASE_125_NEXT_ARCHITECTURE_DIRECTION_CONTRACT_VERIFICATION.md`)
  — independently confirmed the 125B contract complete, decision-
  neutral, and implementation-ready with zero defects.
- **125D evaluation plan**
  (`docs/PHASE_125_NEXT_ARCHITECTURE_DIRECTION_EVALUATION_PLAN.md`) —
  defined the eight-stage evaluation pipeline, ten measurable criteria,
  and five-category risk methodology this decision's rationale (Section
  4) is structured around.
- **125E candidate evaluation**
  (`docs/PHASE_125_NEXT_ARCHITECTURE_DIRECTION_EVALUATION.md`) —
  executed that methodology against all six candidates with
  evidence grounded in direct inspection of governed sources,
  including previously-uncatalogued existing subsystems
  (`src/pcae/core/decision_evaluation.py`,
  `src/pcae/core/permission_broker.py`). This is the primary evidence
  base for the selection below.

## 3. Candidate Comparison

Restating 125E's comparative findings as the direct input to this
decision:

| Candidate | Architectural fit | Governance risk | Technical readiness | Strategic value | Overall risk |
| --- | --- | --- | --- | --- | --- |
| Historical Memory | High | Low | High (schema frozen; source-boundary design needed) | High (fills temporal gap) | Low-medium |
| Dependency Knowledge Graph | High | Medium (disclaimer boundary must be resolved) | High (schema frozen; traversal is novel) | High (direct Change Impact gap closure) | Medium |
| Repository Intelligence expansion | High (narrow) | Low | Highest (reuses existing assembly logic) | Low (no identified consumer need) | Low |
| Decision Evaluation support | Medium (touches decision authority) | Highest | Medium (mature target, unbuilt integration) | High (if bounded correctly) | High |
| Execution Planning | Low (no existing basis) | High (execution-boundary tension) | Lowest (no schema, no prototype) | Low under current constraints | High |
| Permission Broker evolution | Low-medium (mature target, no defined use case) | Medium | Low (purpose undefined) | Unclear (no concrete use case) | Medium |

125E identified Historical Memory and Dependency Knowledge Graph as
"the two candidates best positioned to next enter 125B §6's
architecture step," without ranking between them. This phase's task is
precisely that remaining choice.

## 4. Selection Rationale

**Selected: Dependency Knowledge Graph.**

Evaluated against all ten required criteria, using 125E's evidence:

- **Governance compatibility**: compatible, with one explicit
  precondition — 125E (§3.2) identified that the existing
  `dependency_knowledge_graph_snapshot.schema.json`'s
  `graph_generation_method_disclosure` field currently disclaims that a
  graph was constructed or traversed by PCAE tooling (per 119T §14),
  and that this disclaimer must be explicitly reconciled, not silently
  reinterpreted, before implementation. This is a governance
  *precondition* for 126A to resolve, not a governance *blocker* — it
  is exactly the kind of question a governed architecture phase exists
  to answer, and 125B §10 already anticipates it ("any change to
  already-frozen Track 119-124 contracts requires its own explicit
  supersession decision").
- **Architectural cohesion**: highest of any candidate alongside
  Historical Memory. Both were co-designed with Repository Knowledge
  since Phase 118 as complementary specializations (temporal vs.
  structural), and 125E's Strategic Observations independently
  reconfirmed 118R's original judgment that this cohesion has held.
  Dependency Knowledge Graph's cohesion is sharpened by having a
  specific, already-built consumer (Track 123's Change Impact Builder)
  whose current flat entity model is the direct target for
  improvement — a more concrete cohesion argument than Historical
  Memory's benefit to "existing consumers" in general.
- **Determinism**: achievable — graph construction from
  already-generated Repository Knowledge Snapshot data requires no
  probabilistic or AI-inferred behavior, following the same
  deterministic-generation discipline as every prior Repository
  Intelligence artifact family.
- **Explainability**: achievable via the same source-attribution
  pattern already proven four times over (Tracks 120-123); graph edges
  would carry the same attribution bundle discipline as flat entities
  do today.
- **Auditability**: achievable — a graph generator would produce the
  same canonical, source-attributed artifact structure as Track 120's
  generator, inspectable through the same Query Layer pattern.
- **Reproducibility**: achievable — graph construction over a fixed
  Repository Knowledge Snapshot input is inherently reproducible,
  matching every existing generator's guarantee.
- **Maintainability**: fits the existing shared patterns (generator +
  Query Layer + consumer) that Tracks 120-124 already established and
  that Track 124 specifically hardened; no parallel, incompatible
  architecture is required. 125E rated this candidate's maintenance
  risk "medium" specifically because graph algorithms carry more
  edge-case surface (cycles, disconnected components) than flat-record
  generation — a real but bounded and well-precedented kind of
  complexity, not an open-ended one.
- **Safety**: compatible — 125E confirmed this candidate does not
  expand authority, decision power, or execution capability; graph
  traversal, if implemented, must remain bounded to description (per
  119T's existing disclaimers), which 126A's own contract-freeze phase
  will make explicit and enforceable exactly as Tracks 120-124 did for
  every prior boundary.
- **Strategic value**: the strongest, most concretely evidenced
  strategic case among all six candidates. 125E's own words: "highest
  concrete capability gain among the candidates for Change Impact
  specifically" and "the most direct, concrete gap-closure of any
  candidate." Unlike Repository Intelligence expansion (no identified
  consumer need) or Permission Broker evolution (undefined purpose),
  Dependency Knowledge Graph has a named, already-built, already-shipped
  consumer (Track 123) whose current limitation (flat entity model,
  no real relationship traversal) this candidate directly addresses.
  Unlike Decision Evaluation support, pursuing this candidate does not
  touch PCAE's actual decision-authority boundary.
- **Implementation readiness**: schema already frozen and independently
  verified (119S/119T) with zero outstanding schema-content defects;
  the generator + Query Layer + consumer pattern is proven four times
  over. The one open item (disclaimer reconciliation) is well-scoped,
  already identified, and squarely inside what an architecture phase
  is for — it does not require new invention the way Historical
  Memory's "bound a broader, more heterogeneous source surface"
  precondition does, or the way Decision Evaluation support's "resolve
  the invariant-family boundary question" precondition does.

**Why Dependency Knowledge Graph over Historical Memory specifically**,
since 125E rated Historical Memory's overall risk marginally lower
(low-medium vs. medium): Historical Memory's technical risk stems from
an open-ended question — how to bound deterministic extraction over a
"broader, more heterogeneous source surface" (git/lifecycle history)
that no existing PCAE pattern has attempted at this scope. Dependency
Knowledge Graph's technical and governance risk both stem from
well-defined, already-identified, single-item preconditions (graph
traversal algorithmic surface; one schema disclaimer) that an
architecture phase can resolve directly, rather than an open design
question requiring its own exploratory work. Combined with Dependency
Knowledge Graph's stronger, more concrete strategic value (a named,
already-built consumer with a named, already-identified limitation),
this makes Dependency Knowledge Graph the candidate with the clearest
path from selection to a well-scoped 126A architecture phase.

This does not diminish Historical Memory's standing. Section 5 confirms
it as the leading deferred alternative, not a rejected candidate.

## 5. Deferred Alternatives

- **Historical Memory** — deferred, not rejected. 125E rated it the
  second-strongest candidate on nearly every criterion, with the
  lowest overall risk among the two frozen-schema-ready candidates.
  Its architectural fit and strategic value remain fully valid; it
  differs from Dependency Knowledge Graph mainly in having a less
  concretely scoped precondition (source-boundary discipline over a
  broad, heterogeneous history surface) rather than a well-defined
  single open item. It remains the clearest candidate for a future
  chapter once Dependency Knowledge Graph establishes a second
  precedent for extending the Track 120 generator pattern to a new
  artifact family (as 125A's original roadmap recommendation §9
  anticipated).
- **Repository Intelligence expansion** — deferred. Lowest risk and
  highest technical readiness of any candidate, but 125E found "no
  identified consumer need" to justify prioritizing it now. Remains
  available whenever a concrete downstream need (e.g. cross-session
  Advisory context reuse) is identified.
- **Decision Evaluation support** — deferred. Highest strategic upside
  of any candidate, but also the highest governance risk, since it is
  the only candidate touching PCAE's actual decision-authority
  boundary (`src/pcae/core/decision_evaluation.py`). 125E's open
  question — which of Decision Evaluation's six invariant families, if
  any, could legitimately consume Repository Intelligence content
  without expanding "Evidence never decides" — remains unresolved and
  requires its own dedicated architecture-only investigation before
  this candidate could responsibly enter the 125B §6 sequence.
  Deferred specifically because that investigation has not yet
  happened, not because the candidate lacks merit.
- **Execution Planning** — deferred, and structurally different from
  every other deferred candidate: its blocker (tension with the
  execution-unavailable boundary) is a standing PCAE constraint, not
  absent infrastructure. 125A §7.5 and 125E both concluded this
  candidate requires its own separate, explicitly scoped
  runtime-capability chapter before it could be meaningfully pursued
  as a Repository-Intelligence-adjacent direction. This decision does
  not open, imply, or schedule such a chapter.
- **Permission Broker evolution** — deferred. Mature target subsystem
  (`src/pcae/core/permission_broker.py`), but 125E found no governed
  document has yet articulated what a Repository Intelligence
  connection to it would accomplish. Deferred pending a concrete use
  case, consistent with 125E's open question on this candidate.
- **Other evaluated candidate chapters** — 125E's Section 3.7 confirmed
  no additional candidate beyond the six above was identified as
  justified for evaluation. None is deferred here because none was
  found to exist as a distinct, evidenced candidate.

## 6. Boundary Confirmation

- **No implementation occurs in 125F.** This phase produces only
  documentation: this decision review, PROJECT_STATUS.md, CHANGELOG.md,
  and task lifecycle files.
- **Execution remains unavailable.** Independently re-confirmed via
  `pcae runtime inspect` in this phase (Section 9).
- **Runtime remains observe-only.** Runtime state `Observed`, maximum
  plugin capability `observe`, Permission Broker status
  `execution_unavailable` — unchanged by this decision.
- **Repository Intelligence remains stable.** This decision selects a
  future architecture phase (126A) to define how Dependency Knowledge
  Graph would extend Repository Intelligence; it does not itself
  modify any Track 119-124 schema, generator, Query Layer, or consumer.
  126A inherits 125B §7's requirement that any such extension proceed
  as an addition through its own architecture -> contract ->
  verification -> plan -> implementation -> verification sequence.
- **Decision Evaluation authority is unchanged.** This decision does
  not select Decision Evaluation support (Section 5); no change to
  `src/pcae/core/decision_evaluation.py` or its authority boundary
  occurs or is implied.
- **Advisory authority is unchanged.** No Advisory reasoning capability
  is introduced, expanded, or implied by this decision; Advisory
  Context Builder (Track 122) remains exactly as frozen and verified.

## 7. Recommended Next Chapter

**Track 126 — Dependency Knowledge Graph.**

High-level intent: extend Repository Intelligence with a deterministic,
read-only Dependency Knowledge Graph layer over Repository Knowledge,
following the same architecture -> contract -> verification -> plan ->
implementation -> verification sequence Tracks 120-124 already proved.
The graph would represent repository relationships (dependency edges,
direction, type, strength, scope) as a specialized structural view
already conceptually schema-defined (119S/119T), queryable through new
Track 121-style Query Layer categories, and consumable primarily by
Track 123's Change Impact Builder to replace its current flat
entity-model impact identification with real relationship traversal —
while preserving every boundary Repository Intelligence has held since
Track 119: read-only, deterministic, source-attributed,
limitation-propagating, boundary-disclosed, non-authoritative, and
observe-only.

Track 126's first responsibility, inherited directly from this
decision's rationale (Section 4), is resolving the
`graph_generation_method_disclosure` disclaimer question explicitly —
not silently — as part of its own architecture and contract-freeze
work.

## 8. Recommended First Phase

**126A — Dependency Knowledge Graph Architecture.**

Architecture-only, following the same non-goals discipline every prior
Track 119-124 architecture phase used: no generator, no traversal
implementation, no Query Layer changes, no consumer changes, no schema
modification, no source code, no test code, and no execution capability
in 126A itself. 126A's scope should explicitly include resolving the
disclaimer-boundary question (Section 4) as part of its own analysis,
before any subsequent contract-freeze phase.

## 9. Roadmap Update

Updating 125A §9's original recommended roadmap sequence with this
decision's outcome:

1. ~~125A-125F (Track 125): chapter review, contract freeze, contract
   verification, evaluation plan, evaluation, decision review~~ —
   **complete as of this phase.**
2. **Track 126 — Dependency Knowledge Graph** (selected by this
   decision): architecture (126A) -> contract freeze -> contract
   verification -> plan -> implementation -> verification, following
   the proven Tracks 120-124 phase-type pattern. This is now the
   active next chapter.
3. **Historical Memory** remains the leading deferred alternative
   (Section 5) for a future chapter once Track 126 establishes a
   second precedent for extending the Track 120 generator pattern to a
   new artifact family — unchanged from 125A's original sequencing
   logic, now with Track 126 (rather than an unspecified candidate)
   as the precedent-setting predecessor.
4. **Repository Intelligence expansion** (persisted Query Result,
   Repository Intelligence Package) remains deferred pending a concrete
   downstream consumer need — unchanged from 125A.
5. **Decision Evaluation support** remains deferred as its own future,
   higher-governance-sensitivity chapter, pending the invariant-family
   boundary investigation identified in Section 5 — unchanged in
   priority ordering from 125A, now with an explicit precondition
   named.
6. **Execution Planning and Permission Broker evolution** remain
   explicitly outside the Repository Intelligence roadmap, each
   requiring its own separately scoped governed chapter — unchanged
   from 125A.

This roadmap update reflects a decision, not an implementation. Track
126 does not begin until 126A is itself governed, scoped, and executed
as its own phase.

## 10. Known Inherited Issues

Carried forward unchanged, not repaired in this phase:

- 119Q report-generation-ordering defect: lifecycle/tooling debt,
  non-blocking for this decision review.
- 119AB phase-id comparison bug: lifecycle/tooling debt, non-blocking
  for this decision review.
- Recurring `pending_final_telegram_delivery` reporting detail:
  lifecycle/tooling debt, non-blocking when final report delivery is
  explicitly verified.
- GitHub main-branch PR-rule bypass notification: repository hosting
  policy reporting detail, non-blocking for governed PCAE push when
  `pcae push` succeeds.
- Missing `PCAE_NOTIFY_ENABLED` during governed push environment:
  notification environment detail, non-blocking when Telegram status
  and explicit report delivery are verified after sourcing the
  environment.

## 11. Strict Non-Goals

This phase does not implement: the selected next chapter (Dependency
Knowledge Graph); Historical Memory; Repository Intelligence expansion;
Decision Evaluation; Execution Planning; execution capability; runtime
plugins; source code; test code; or schema changes.

## 12. Governance Compatibility

This decision is compatible with PCAE governance:

- observe-only runtime remains unchanged;
- execution remains unavailable;
- the decision was made through this governed phase only, citing
  evidence from every prior Track 125 phase;
- the decision selects a next architecture phase (126A) — it does not
  itself constitute architecture, contract freeze, or verification for
  Dependency Knowledge Graph, all of which remain required before any
  implementation may occur (125B §6);
- raw git commit/push, force push, and `--no-verify` remain forbidden
  and were not used;
- canonical reports remain complete and metadata-consistent;
- human-controlled lifecycle authority remains unchanged.

## 13. Confirmations

- **No implementation occurred.** This phase produced only
  documentation.
- **No runtime behavior changed.**
- **Execution remains unavailable.**
- **Next chapter selected.** Dependency Knowledge Graph (Track 126),
  with recommended first phase 126A — Dependency Knowledge Graph
  Architecture.

## 14. Governance Results

- `pcae health`: healthy (idle), all required files present, git
  status clean.
- `pcae check`: passed.
- `pcae doctor task-memory`: clean, no inconsistencies detected.
- `pcae push check`: clean, 0 unpushed commits at inspection time.
- `pcae runtime inspect`: `Observed` / `observe` / execution
  unavailable / zero runtime plugins / registry empty / Permission
  Broker `execution_unavailable`.
- `pcae notify status` (after sourcing
  `~/.config/pcae/telegram.env`): Telegram configured, enabled, and
  ready for outbound delivery.

## 15. Conclusion

This decision review selects Dependency Knowledge Graph as PCAE's next
architectural chapter, based on the complete Track 125 evidence chain:
highest concrete strategic value among all six evaluated candidates
(a named, already-built consumer with a named, already-identified
limitation), frozen and independently verified schema readiness,
architectural cohesion with Repository Intelligence dating to Phase
118's original design, and a well-scoped, well-defined precondition
(disclaimer reconciliation) rather than an open-ended design question.
Historical Memory, Repository Intelligence expansion, Decision
Evaluation support, Execution Planning, and Permission Broker evolution
are all deferred with documented rationale, not rejected. No
implementation occurred in this phase. Execution remains unavailable;
observe-only runtime remains mandatory; Repository Intelligence,
Decision Evaluation authority, and Advisory authority all remain
exactly as previously frozen and verified.

Recommended next phase: 126A — Dependency Knowledge Graph Architecture.
