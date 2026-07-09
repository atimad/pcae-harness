# Phase 125E - Next Architecture Direction Evaluation

## 1. Purpose

Phase 125E executes the evaluation methodology defined in 125D against
every candidate architectural direction recognized by the 125B
contract, producing an evidence-based comparative assessment.

This phase does not select PCAE's next architectural chapter.
Selection remains deferred to 125F, and even 125F may only confirm
whether a candidate is ready to *enter* the 125B §6 three-step
decision sequence — actual selection remains a separate, explicit,
future act under that contract. 125E performs no implementation and
changes no runtime behavior.

## 2. Methodology

Each candidate below was evaluated through 125D's eight-stage pipeline
(candidate identification, architectural fit, governance compatibility,
dependency assessment, risk assessment, readiness assessment,
comparative analysis, recommendation preparation), organized here
candidate-by-candidate per the required report structure. Every rating
cites the governed source it is derived from, consistent with 125D
§10's reproducibility requirement — no rating is an unexplained score.

Evidence for this evaluation was drawn from: the Track 119 schema line
(`schemas/repository_intelligence/`), the Track 120-124 implementation
and verification documents, 125A's chapter review, and direct
inspection of the current repository state, including source files not
previously catalogued in 125A (`src/pcae/core/decision_evaluation.py`,
`src/pcae/core/permission_broker.py`,
`src/pcae/core/permission_broker_foundation.py`).

## 3. Candidate Assessments

### 3.1 Historical Memory

**Architectural fit.** Compatible with PCAE architecture: the
`historical_memory_snapshot.schema.json` (119Q/119R) already defines
its conceptual shape as a temporal specialization of Repository
Knowledge, consistent with 118's original layering (Historical Memory
"emerges from" Repository Knowledge, not a parallel subsystem).
Interaction with Repository Intelligence would follow the proven Track
120 generator -> Track 121 Query Layer pattern directly: a Historical
Memory generator producing a new artifact family, queryable through
new Query Layer categories, consumable by the existing Track 122/123
sibling-consumer pattern or new siblings. Architectural cohesion is
high — Historical Memory was co-designed with Repository Knowledge from
Phase 118 onward, not bolted on later.

**Governance compatibility.** Observe-first: fully compatible — a
Historical Memory generator would read already-committed git/lifecycle
history, not execute anything. Deterministic engineering: compatible
in principle, but git/lifecycle history is a broader, more
heterogeneous source surface (commit history, phase reports, task
lifecycle records) than Track 120's snapshot sources (source tree,
existing docs, existing contracts), so deterministic extraction rules
would need more careful architecture than Track 120 required.
Auditability, reproducibility, explainability: compatible, following
the same source-attribution pattern every other Repository Intelligence
artifact family uses. Fail-closed governance: compatible — an
under-specified historical claim would fail closed to
unknown/unverified exactly as Track 120-123 already do for gaps.

**Technical readiness.** Dependency readiness: high — schema already
frozen and verified (119Q/119R), no new schema-contract work needed
before an architecture phase could begin. Implementation prerequisites:
a new architecture phase (per 125B §6 step 1) would need to define
exactly which git/lifecycle sources are in scope and how the
heterogeneous-source-surface risk (above) is bounded — this is real
prerequisite work, not yet done. Maturity: the underlying pattern
(generator + Query Layer + consumer) is proven four times over (Tracks
120-123); the novel part is source-boundary discipline for a broader
input surface. Implementation complexity: medium — the generation
pattern is known, but defining deterministic rules over git/lifecycle
history (as opposed to a fixed source tree snapshot) is more work than
Track 120's original scope.

**Strategic value.** Long-term architectural benefit: fills a
recognized gap (125A §4) — Repository Intelligence currently describes
a repository snapshot with no temporal dimension. Enablement of future
capabilities: would let Change Impact (Track 123) describe not just
*that* entities relate but historically *why*, and could inform a
future Decision Evaluation integration with historical precedent.
Support for governance objectives: strengthens auditability by making
PCAE's own governed history queryable as Repository Intelligence.
Extensibility: high — establishes a second precedent (after Track 120)
for extending the generator pattern to a new artifact family, directly
useful for evaluating subsequent candidates.

**Risk assessment.**
- Technical risk: medium — broader, more heterogeneous source surface
  than any existing generator has handled; deterministic rule design
  over historical records is unproven at this scope.
- Governance risk: low — fits governed lifecycle discipline; no
  ungoverned shortcut required.
- Maintenance risk: low-medium — follows existing shared patterns
  (Section headers `serialization.py`/`consumer_validation.py` style
  helpers from Track 124 hardening could be reused directly).
- Migration risk: low — pure addition; no Track 119-124 file requires
  modification (125B §7).
- Future compatibility risk: low — does not foreclose Dependency
  Knowledge Graph or any other candidate; the two are explicitly
  complementary specializations of Repository Knowledge (119C).

**Repository Intelligence compatibility.** Fully compatible as an
addition. Would consume nothing and modify nothing in Tracks 120-124;
would add a new generator, new Query Layer categories, and optionally
new consumers, all following 125B §7's addition-not-modification
requirement.

**Execution boundary.** Preserves execution unavailable, observe-only
runtime, and governance-first philosophy: a Historical Memory generator
reads already-committed history: no shell execution, no runtime
mutation, no Advisory authority, no Decision Evaluation replacement.

### 3.2 Dependency Knowledge Graph

**Architectural fit.** Compatible with PCAE architecture:
`dependency_knowledge_graph_snapshot.schema.json` (119S/119T) already
defines its conceptual shape as a structural specialization of
Repository Knowledge, parallel to Historical Memory's temporal
specialization. Interaction with Repository Intelligence: would give
Track 123's Change Impact Builder a real graph to traverse instead of
relying solely on the flat Repository Knowledge Snapshot entity model —
this is the most direct, concrete gap-closure of any candidate
(125A §4, §7.2). Architectural cohesion: high, same co-design lineage
as Historical Memory.

**Governance compatibility.** Observe-first: fully compatible — graph
construction from already-generated Repository Knowledge Snapshot data
requires no execution. Deterministic engineering: compatible, but with
a specific discipline requirement the 119AC schema review already
flagged: the frozen schema's `graph_generation_method_disclosure`
field explicitly disclaims that a graph was constructed, traversed, or
queried by PCAE tooling (119T §14) — meaning a real generator/traversal
implementation would need to either update that disclosure through its
own governed contract-freeze phase or design generation/traversal to
remain within what the existing disclaimer permits. Auditability,
reproducibility, explainability: compatible via the same
source-attribution pattern. Fail-closed governance: compatible, with
extra discipline needed specifically around graph traversal — 119AC
Section 27 warned that "graph construction and traversal are exactly
the kind of capability that can quietly grow toward inference or
prediction if not tightly scoped."

**Technical readiness.** Dependency readiness: high — schema already
frozen and verified (119S/119T). Implementation prerequisites: an
architecture phase would need to resolve the disclaimer-boundary
question above before contract freeze, since it directly affects what
the frozen schema currently claims about itself. Maturity: the
generator + Query Layer + consumer pattern is proven; graph
construction/traversal specifically is not — no PCAE subsystem has ever
built or traversed a graph. Implementation complexity: medium-high —
graph construction and traversal are more novel than either a flat
snapshot generator (Track 120) or a temporal extraction (Historical
Memory, Section 3.1); traversal in particular introduces algorithmic
surface (path-finding, cycle handling) none of the four completed
Repository Intelligence tracks needed.

**Strategic value.** Long-term architectural benefit: highest concrete
capability gain among the candidates for Change Impact specifically —
closes a named gap with a direct, already-identified consumer.
Enablement of future capabilities: a real dependency graph is a
plausible prerequisite for more sophisticated future Change Impact
analysis (multi-hop impact, path-based impact) without itself
performing prediction. Support for governance objectives: strengthens
explainability of Change Impact reports by making the underlying
relationship structure inspectable, not just enumerable. Extensibility:
medium-high — but the disclaimer-boundary question above must be
resolved cleanly or it could constrain how far future graph-consuming
candidates can go.

**Risk assessment.**
- Technical risk: medium-high — graph construction and traversal are
  architecturally novel for PCAE; no existing pattern directly covers
  traversal algorithms the way the generator/Query Layer/consumer
  pattern covers everything built so far.
- Governance risk: medium — the existing schema's
  `graph_generation_method_disclosure` disclaimer must be explicitly
  reconciled (not silently reinterpreted) before implementation, per
  125B §10's prohibition on silently redefining already-frozen
  contract terms.
- Maintenance risk: medium — graph algorithms typically carry more
  edge-case surface (cycles, disconnected components, missing nodes)
  than flat-record generation.
- Migration risk: low — pure addition; no Track 119-124 file requires
  modification.
- Future compatibility risk: low — complementary to Historical Memory,
  not competing with it.

**Repository Intelligence compatibility.** Compatible as an addition,
contingent on explicitly resolving the graph-disclaimer boundary
question through its own governed step rather than treating graph
construction as silently already-authorized by the existing schema's
mere existence.

**Execution boundary.** Preserves execution unavailable, observe-only
runtime, and governance-first philosophy: graph construction/traversal
over already-generated data requires no execution, no runtime
mutation, and no Advisory or Decision Evaluation authority — provided
traversal is bounded to description (as 119T's disclaimers require)
rather than drifting into inference or prediction.

### 3.3 Repository Intelligence Expansion (richer artifact families)

**Architectural fit.** Compatible with PCAE architecture: Advisory
Intelligence Context Package, persisted Query Result, and Repository
Intelligence Package schemas (119W/119X, 119Y/119Z, 119AA/119AB) are
already frozen and verified. Interaction with Repository Intelligence:
this candidate is *internal* to Repository Intelligence rather than an
external consumer or new knowledge layer — it persists artifacts that
Tracks 122/123 already produce as in-memory output. Architectural
cohesion: high but narrow — extends existing artifact handling rather
than adding new architectural capability.

**Governance compatibility.** Fully compatible across all six
dimensions (observe-first, deterministic, auditable, reproducible,
explainable, fail-closed) — this candidate does not introduce any new
category of behavior, only persistence of already-computed,
already-governed content.

**Technical readiness.** Dependency readiness: highest of any
candidate — three of the remaining five schema families involved here
are already frozen with no open questions (unlike the Dependency
Knowledge Graph disclaimer issue in 3.2). Implementation prerequisites:
minimal — persistence-layer work (following Track 120's
`persistence.py` pattern) plus wiring existing Track 122/123 output
into it. Maturity: high — nothing genuinely new is required
architecturally. Implementation complexity: low-medium — lowest
implementation complexity of any candidate, since it reuses
already-built assembly logic and only adds a persistence step.

**Strategic value.** Long-term architectural benefit: lowest marginal
capability gain among the six candidates (125A §7.3) — existing
consumers already get equivalent content without persistence.
Enablement of future capabilities: would enable cross-session context
reuse if a concrete downstream need for that ever arises, but no such
need has been identified yet. Support for governance objectives: mild
auditability improvement (persisted artifacts are independently
inspectable after the fact) but does not meaningfully advance
determinism, explainability, or reproducibility beyond what already
exists. Extensibility: low direct extensibility value — this candidate
does not open new architectural surface the way Historical Memory or
Dependency Knowledge Graph would.

**Risk assessment.**
- Technical risk: low — reuses existing, already-verified assembly
  logic.
- Governance risk: low.
- Maintenance risk: low-medium — persisted artifacts add a new
  long-term compatibility surface (schema versioning over time) that
  in-memory-only output does not carry.
- Migration risk: low — pure addition.
- Future compatibility risk: low.

**Repository Intelligence compatibility.** Fully compatible; this
candidate is the most conservative extension of Repository Intelligence
among all six, since it persists rather than newly generates.

**Execution boundary.** Fully preserved; persistence of already-
computed content requires no execution capability.

### 3.4 Decision Evaluation Support

**Architectural fit.** Compatible with PCAE architecture, and grounded
in a materially different starting point than 125A's original
assessment suggested: `src/pcae/core/decision_evaluation.py` (593
lines, Phase 115E) is **not** an empty or hypothetical subsystem — it
is an existing, deterministic, evidence-only evaluation layer between
Evidence Providers and the Repository Transition Validator, explicitly
documented as consuming only `Evidence`/`EvidenceCollection` with "no
Git access, no filesystem access, no subprocesses, no runtime
inspection." Interaction with Repository Intelligence: none currently
exists — Decision Evaluation consumes only Evidence today, not
Repository Intelligence content, and its own docstring states its only
import is `pcae.core.evidence`. The `decision_evaluation_handoff` field
in the Advisory Intelligence Context Package schema (119W) is a
declared field shape, not a wired integration. Architectural cohesion:
this candidate would be the first time Repository Intelligence content
reaches a decision-authoritative subsystem, even indirectly through
Advisory context — a materially different category of integration than
any of the other five candidates.

**Governance compatibility.** Observe-first: compatible in principle,
since Decision Evaluation itself performs no execution — but the
integration point (Repository Intelligence -> Advisory context ->
Decision Evaluation) is exactly the boundary 118 and every subsequent
Repository Intelligence phase repeatedly emphasized must never blur.
Deterministic engineering: Decision Evaluation is already explicitly
deterministic by design ("Evidence never decides. Evaluation is
deterministic.") — compatible, and arguably a *better-suited* consumer
of Repository Intelligence's own deterministic guarantees than a
hypothetical non-deterministic subsystem would be. Auditability,
reproducibility, explainability: Decision Evaluation's existing design
(named invariant families, structured `EvaluationResult`) is already
built for these properties. Fail-closed governance: Decision
Evaluation's docstring explicitly preserves "the Repository Transition
Validator remains the only authority capable of determining repository
state transitions" — any Repository Intelligence integration would
need to preserve this exact non-authority boundary for Repository
Intelligence content specifically, matching what Tracks 122/123 already
enforce for Advisory context.

**Technical readiness.** Dependency readiness: partial — the
`decision_evaluation_handoff` schema field exists, but no Query Layer
category or consumer currently produces Repository-Intelligence-shaped
input for Decision Evaluation's six invariant families. Implementation
prerequisites: would need its own architecture phase examining exactly
which of Decision Evaluation's six invariant families (if any) could
legitimately consume Repository Intelligence content, and how that
consumption would preserve "Evidence never decides." Maturity: the
target subsystem (Decision Evaluation) is highly mature (Phase 115E,
extensively tested per its own line); the *integration surface* between
it and Repository Intelligence is entirely unbuilt. Implementation
complexity: high — not because Decision Evaluation itself is
immature, but because correctly bounding a new input source into an
already-authoritative, already-deterministic subsystem without
expanding its authority is inherently more delicate than adding a new
sibling consumer at the Query Layer's existing boundary (as Tracks 122
and 123 did).

**Strategic value.** Long-term architectural benefit: potentially
significant — would let repository-structural knowledge inform
transition decisions currently based only on Evidence. Enablement of
future capabilities: could be a genuine prerequisite for more
sophisticated governance automation, if pursued carefully. Support for
governance objectives: directly strategic, since Decision Evaluation is
itself a core governance subsystem — but also the candidate most
capable of *undermining* governance objectives if the non-authority
boundary is not held. Extensibility: unclear until the invariant-family
question above is resolved.

**Risk assessment.**
- Technical risk: medium — the target subsystem is mature, but the
  integration pattern is unprecedented.
- Governance risk: **highest of any candidate** (matches 125A's
  original assessment and 125B §4.4's classification) — this is the
  only candidate whose failure mode is not "wasted engineering effort"
  but "authority-boundary erosion in an already-decision-authoritative
  subsystem." Every other candidate's worst-case failure is scope creep
  within Repository Intelligence itself; this candidate's worst-case
  failure touches PCAE's actual decision-making machinery.
- Maintenance risk: medium — Decision Evaluation's six invariant
  families are individually well-scoped; adding a seventh
  Repository-Intelligence-aware family (if that is even the right
  design) would need to preserve that scoping discipline.
- Migration risk: low for Repository Intelligence itself (pure
  addition on that side); but potentially non-trivial for Decision
  Evaluation's own contract, which this candidate does not currently
  propose modifying.
- Future compatibility risk: low for other Repository Intelligence
  candidates (this integration would sit downstream of Advisory
  context, not compete with Historical Memory or Dependency Knowledge
  Graph); but this candidate's own future evolution is harder to
  forecast than the more mechanical candidates (3.1-3.3) precisely
  because it touches decision authority.

**Repository Intelligence compatibility.** Compatible as an addition
on the Repository Intelligence side (would consume via the existing
Query Layer -> Advisory Context Builder path, adding no new access
boundary); compatibility on the Decision Evaluation side is unverified
and would require its own architecture phase to establish.

**Execution boundary.** Preserves execution unavailable, observe-only
runtime: Decision Evaluation itself performs no execution today and
this candidate does not propose changing that. Governance-first
philosophy: this is precisely the principle most directly tested by
this candidate, since it is the closest any candidate comes to PCAE's
actual decision-authority boundary.

### 3.5 Execution Planning

**Architectural fit.** Low current fit, confirmed by direct inspection:
no completed Repository Intelligence track (119-124) produces output
shaped for execution planning, and no `src/pcae/` module implements
execution planning today. Interaction with Repository Intelligence:
none exists, and none of the six completed Repository Intelligence
tracks were designed with execution planning as a consumer.
Architectural cohesion: this candidate would not extend Repository
Intelligence — it would be a new chapter entirely, orthogonal to
everything Tracks 119-124 built.

**Governance compatibility.** Observe-first: **directly in tension**
with this candidate's premise — execution planning is meaningful only
in relation to eventual execution, and PCAE's runtime remains
execution-unavailable by explicit, repeatedly-reconfirmed design across
every phase since at least Phase 92. Deterministic engineering,
auditability, reproducibility, explainability: could in principle be
satisfied by a planning representation that itself performs no
execution — but the candidate's *value proposition* is inherently tied
to a capability PCAE does not have and has not authorized. Fail-closed
governance: compatible only if planning output is treated as strictly
descriptive, non-actionable content — at which point its strategic
value (Section below) becomes questionable, since planning without any
path to execution has limited practical purpose.

**Technical readiness.** Dependency readiness: low — no schema, no
Query Layer support, no consumer exists or was ever proposed for this
candidate anywhere in Tracks 119-124. Implementation prerequisites: a
separate, explicitly scoped runtime-capability chapter would need to
precede any execution planning work, per 125A §7.5's own conclusion.
Maturity: lowest of all six candidates — this is the only candidate
with zero existing schema, zero existing prototype, and zero existing
partial subsystem (unlike Decision Evaluation Support, which builds on
a mature target). Implementation complexity: cannot be meaningfully
estimated without first resolving the runtime-capability precondition.

**Strategic value.** Long-term architectural benefit: potentially high
*if* PCAE ever gains execution capability, but that is a precondition
this candidate cannot itself satisfy. Enablement of future capabilities:
inverted — this candidate depends on a future capability (execution)
rather than enabling one. Support for governance objectives: neutral
to negative under current constraints, since pursuing execution
planning now would create pressure toward the execution boundary this
subsystem review must not create (125B §8). Extensibility: not
meaningfully evaluable while the precondition is unmet.

**Risk assessment.**
- Technical risk: high — no existing pattern to build on.
- Governance risk: high — the clearest risk of any candidate for
  conflating two distinct PCAE boundaries (Repository Intelligence's
  read-only boundary and the runtime's execution-unavailable boundary),
  exactly as 125A §7.5 warned.
- Maintenance risk: not meaningfully evaluable pre-precondition.
- Migration risk: low for Repository Intelligence (would not modify
  it).
- Future compatibility risk: high — pursuing this now, ahead of an
  explicit runtime-capability decision, risks creating pressure toward
  premature execution-boundary changes.

**Repository Intelligence compatibility.** Not applicable in any
meaningful sense — this candidate does not consume or extend
Repository Intelligence; it is architecturally unrelated to it.

**Execution boundary.** This is the one candidate whose entire premise
sits closest to the execution boundary. Confirmed: execution remains
unavailable, observe-only runtime remains mandatory, and this
evaluation does not propose or imply changing that. Any future pursuit
of this candidate requires its own separate, explicitly scoped governed
architecture and contract path that first and explicitly addresses the
execution-unavailable boundary — not something this evaluation, 125D,
or 125B authorizes.

### 3.6 Permission Broker Evolution

**Architectural fit.** Low current fit relative to Repository
Intelligence, but grounded in a materially different starting point
than "orthogonal and untouched": `src/pcae/core/permission_broker.py`
(1163 lines) and `permission_broker_foundation.py` (787 lines, ~1950
lines combined) already implement a substantial, existing "read-only
decision aggregator" (Phase 88R) that "consumes governance evidence and
returns a conservative broker decision envelope," explicitly never
executing commands, invoking backends, or granting real authorization.
Interaction with Repository Intelligence: currently none — the
Permission Broker consumes governance evidence (scope preflight, shell
gate classification, task contracts) not Repository Intelligence
content. Architectural cohesion: like Decision Evaluation Support, this
candidate would connect Repository Intelligence to an existing
governance-adjacent subsystem rather than building something new from
scratch — but unlike Decision Evaluation, no schema field (like
`decision_evaluation_handoff`) currently anticipates this connection.

**Governance compatibility.** Observe-first: compatible — the
Permission Broker's own design principle already matches Repository
Intelligence's ("never executes... grants real authorisation").
Deterministic engineering, auditability, reproducibility,
explainability: the Permission Broker's existing `BPE_DECISIONS`
vocabulary (`allow_preflight_only`, `deny`, `requires_human_review`,
`requires_more_evidence`, `blocked_by_scope`, `blocked_by_backend_policy`,
`blocked_by_mutation_policy`) is itself a deterministic, explainable
decision surface — structurally compatible with how Repository
Intelligence already represents outcomes. Fail-closed governance:
compatible in principle, since the Permission Broker's decisions are
already conservative by design.

**Technical readiness.** Dependency readiness: low specifically for
*this* connection — the Permission Broker's current evidence inputs
(scope preflight, shell gate, task contracts) are lifecycle/execution-
adjacent, not Repository-Intelligence-shaped; no existing field or
Query Layer category was designed to feed it. Implementation
prerequisites: would need an architecture phase defining what
Repository-Intelligence-informed permission decisions would even mean
(e.g. "deny because this entity has no recorded attribution" is a
plausible future rule, but nothing today specifies this). Maturity:
the target subsystem is mature (Phase 88R lineage); the connection
itself is unbuilt and unspecified. Implementation complexity: cannot
be meaningfully estimated without first defining the connection's
purpose, which no governed document currently does.

**Strategic value.** Long-term architectural benefit: unclear pending
a concrete use case — unlike Dependency Knowledge Graph (concrete gap:
Change Impact traversal) or Historical Memory (concrete gap: temporal
context), no completed Track 119-124 phase identified a concrete
permission-decision need that Repository Intelligence content would
address. Enablement of future capabilities: speculative. Support for
governance objectives: potentially positive but undemonstrated.
Extensibility: cannot be assessed without a defined use case.

**Risk assessment.**
- Technical risk: medium — the target subsystem is mature and its
  decision vocabulary is well-structured, which lowers integration
  risk relative to Decision Evaluation Support, but the *purpose* of
  the integration is undefined, which is itself a risk.
- Governance risk: medium — lower than Decision Evaluation Support
  (Permission Broker's decisions are explicitly conservative/
  non-authoritative-in-effect, per its own docstring) but higher than
  the purely-additive candidates (3.1-3.3), since it still touches a
  governance-adjacent decision surface.
- Maintenance risk: medium — undefined purpose makes future scope
  creep harder to bound in advance.
- Migration risk: low for Repository Intelligence (would not modify
  it).
- Future compatibility risk: medium — pursuing this without a defined
  use case risks producing a connection that later needs rework once
  an actual need is identified.

**Repository Intelligence compatibility.** Compatible as a potential
future addition on the Repository Intelligence side; no incompatibility
identified, but no concrete integration has been specified either.

**Execution boundary.** Preserves execution unavailable and
observe-only runtime: the Permission Broker itself already never
executes or grants real authorization, and this evaluation does not
propose changing that. Governance-first philosophy: compatible, though
this candidate's undefined purpose (Strategic Value, above) makes it
harder to fully evaluate governance-first compliance in the concrete
than the better-specified candidates.

### 3.7 Other Future Architectural Chapters

Consistent with 125B §4.7 and 125D §3, this evaluation does not close
the candidate set. No additional candidate beyond Sections 3.1-3.6 was
identified as justified for evaluation in this phase: every
architectural direction referenced across 118, 119A-119AC, 125A's
chapter review, and the 125B contract maps to one of the six candidates
above. If a future phase identifies a genuinely new candidate not
already covered, it must be evaluated against the same 125D
methodology (Section 2) before being compared alongside these six.

## 4. Comparative Analysis

| Candidate | Architectural fit | Governance risk | Technical readiness | Strategic value | Overall risk |
| --- | --- | --- | --- | --- | --- |
| Historical Memory | High | Low | High (schema frozen; source-boundary design needed) | High (fills temporal gap) | Low-medium |
| Dependency Knowledge Graph | High | Medium (disclaimer boundary must be resolved) | High (schema frozen; traversal is novel) | High (direct Change Impact gap closure) | Medium |
| Repository Intelligence expansion | High (narrow) | Low | Highest (reuses existing assembly logic) | Low (no identified consumer need) | Low |
| Decision Evaluation support | Medium (touches decision authority) | **Highest** | Medium (mature target, unbuilt integration) | High (if bounded correctly) | High |
| Execution Planning | Low (no existing basis) | High (execution-boundary tension) | Lowest (no schema, no prototype) | Low under current constraints | High |
| Permission Broker evolution | Low-medium (mature target, no defined use case) | Medium | Low (purpose undefined) | Unclear (no concrete use case) | Medium |

**Strengths, weaknesses, dependencies, and trade-offs:**

- **Historical Memory** and **Dependency Knowledge Graph** are the two
  candidates with the strongest combination of frozen-schema readiness
  and identified architectural gap-closure value. Their trade-off
  against each other is narrow: Historical Memory's main open question
  is source-boundary discipline (how to bound a broader source surface
  deterministically); Dependency Knowledge Graph's main open question
  is the existing schema disclaimer that must be explicitly reconciled
  before any traversal implementation. Neither blocks the other; 125A
  §9 already identified them as complementary specializations, and this
  evaluation confirms that assessment holds under the full 125D
  methodology.
- **Repository Intelligence expansion** trades lowest risk and highest
  technical readiness against lowest strategic value — it is the safest
  candidate to execute but the weakest candidate to prioritize, since no
  concrete consumer need currently justifies it.
- **Decision Evaluation support** trades the highest potential strategic
  value against the highest governance risk of any candidate. Its
  distinguishing characteristic, confirmed by direct source inspection
  in this phase (not previously verified this concretely in 125A), is
  that its *target* subsystem is mature and already deterministic —
  the risk is entirely in the integration surface, not in the maturity
  of what it would connect to.
- **Execution Planning** is the only candidate whose current
  architectural fit is in direct tension with a standing PCAE
  constraint (execution unavailable) rather than merely lacking
  existing infrastructure. Its evaluation is qualitatively different
  from the other five: it cannot be meaningfully de-risked by more
  Repository-Intelligence-side work, because its blocker is external to
  Repository Intelligence.
- **Permission Broker evolution** is the candidate with the least
  concrete evidence available to evaluate, not because its target
  subsystem is immature (it is not — 88R is substantial and mature) but
  because no governed document has yet articulated what a Repository
  Intelligence connection to it would accomplish. This is a distinct
  kind of readiness gap from Execution Planning's: Permission Broker
  evolution's gap is "undefined purpose," not "constraint conflict."

This evaluation does not declare a winner and does not recommend
implementation. Consistent with 125D §4.8 and §9, the comparative
analysis above is evidence for a future phase to read, not a ranking
that resolves candidate selection.

**Candidates that appear most suitable for further architectural
consideration** (observation, not selection, per this phase's explicit
instructions): Historical Memory and Dependency Knowledge Graph both
combine high architectural fit, low-to-medium risk, frozen schema
readiness, and clearly identified strategic value, making them the two
candidates best positioned to next enter 125B §6's architecture step
if a future phase chooses to propose that. Repository Intelligence
expansion is technically the lowest-risk candidate but has the weakest
independently identified strategic justification. Decision Evaluation
support has real strategic upside but carries risk that would need
substantial dedicated architecture work to bound before it could
reasonably enter the decision sequence. Execution Planning and
Permission Broker evolution both have unresolved preconditions
(execution-boundary tension; undefined purpose, respectively) that
would need separate resolution before either is ready for the decision
sequence at all.

## 5. Governance Compatibility Assessment

All six candidates preserve observe-first philosophy in their current,
unimplemented form — evaluation itself involves no execution. Under
eventual implementation, five of six (all but Execution Planning) can
be pursued without any execution-boundary change; Execution Planning's
premise is in direct tension with the boundary and its "compatibility"
is conditional on a separate future runtime-capability decision this
evaluation does not authorize. Deterministic engineering, auditability,
reproducibility, and explainability are compatible for all six
candidates in principle, with varying implementation difficulty
(highest for Dependency Knowledge Graph's traversal logic and Decision
Evaluation support's integration surface). Fail-closed governance is
achievable for all six, contingent on each candidate's own future
contract-freeze phase explicitly defining its failure modes, as every
completed Repository Intelligence track already did.

## 6. Repository Intelligence Compatibility Assessment

Historical Memory, Dependency Knowledge Graph, and Repository
Intelligence expansion are all direct additions to Repository
Intelligence, fully compatible with 125B §7/§10's addition-not-
modification requirement, with Dependency Knowledge Graph carrying one
open item (the existing graph-generation disclaimer) that must be
explicitly resolved rather than silently reinterpreted. Decision
Evaluation support and Permission Broker evolution would consume
Repository Intelligence output through the existing Query Layer/
Advisory Context path without requiring any Repository Intelligence
file to change — compatible on the Repository Intelligence side, with
open questions residing entirely on the consuming subsystem's side.
Execution Planning has no meaningful Repository Intelligence
compatibility relationship in either direction — it is not
represented in the existing schema line and does not propose to be.

## 7. Strategic Observations

- The two candidates directly co-designed alongside Repository
  Knowledge since Phase 118 (Historical Memory, Dependency Knowledge
  Graph) remain the most architecturally ready many phases later,
  confirming 118R's original judgment that Repository Intelligence's
  four specialized layers (Historical Memory, Dependency Knowledge
  Graph, Change Impact, Advisory Reasoning) belong to one coherent
  contract.
- This evaluation's direct inspection of `decision_evaluation.py` and
  `permission_broker.py` surfaced a strategic fact 125A's architecture-
  document-level review did not fully capture: two of the six
  candidates (Decision Evaluation support, Permission Broker evolution)
  are not "build from nothing" propositions — they are "connect
  Repository Intelligence to an already-mature, already-deterministic
  subsystem" propositions. This changes their risk profile from what a
  purely document-level review would suggest: the risk is concentrated
  in the integration boundary, not in target-subsystem immaturity.
- Execution Planning remains structurally different from every other
  candidate: it is the only one whose blocker is a standing PCAE
  constraint rather than absent infrastructure, and it is the only
  candidate where "more Repository Intelligence work" cannot resolve
  its readiness gap.

## 8. Open Questions

- For Historical Memory: exactly which git/lifecycle sources should be
  in scope for a first governed architecture phase, and how should
  deterministic extraction rules bound that broader source surface?
- For Dependency Knowledge Graph: should the existing
  `graph_generation_method_disclosure` disclaimer be updated through a
  governed contract-amendment, or should a future generator be designed
  to remain within what it currently permits?
- For Repository Intelligence expansion: does any concrete downstream
  consumer need (e.g. cross-session Advisory context reuse) exist yet,
  or does this candidate remain speculative until one is identified?
- For Decision Evaluation support: which (if any) of Decision
  Evaluation's six existing invariant families could legitimately
  consume Repository Intelligence content without expanding
  "Evidence never decides" into "Repository Intelligence never
  decides, except when it does"?
- For Permission Broker evolution: what concrete permission decision
  would Repository Intelligence content actually inform, and does that
  use case exist yet?
- For Execution Planning: is a separate runtime-capability chapter
  under consideration at all, and if not, should this candidate remain
  listed as a recognized-but-inactive candidate rather than continuing
  to appear in every future evaluation cycle?

## 9. Preparation Required Before a Decision

Consistent with 125D §9's distinction between preparation and decision,
this evaluation prepares but does not perform the following possible
future preparation steps, listed for a future phase's consideration,
not authorized by this phase:

- Resolving the Dependency Knowledge Graph disclaimer question
  (Section 8) before any architecture phase for that candidate could
  responsibly begin.
- Identifying a concrete consumer need for Repository Intelligence
  expansion, if that candidate is to be prioritized over the two
  higher-strategic-value candidates.
- Scoping a dedicated architecture-only investigation into Decision
  Evaluation's invariant-family boundary question before that
  candidate could responsibly enter 125B §6's architecture step.
- Articulating a concrete use case for Permission Broker evolution.
- Confirming whether a separate runtime-capability chapter is or is not
  under consideration, to resolve Execution Planning's standing status.

None of these steps are performed by this phase. Performing any of them
is itself a future governed act, not an automatic consequence of this
evaluation.

## 10. Deferred Capabilities

Explicitly deferred, unchanged from 125B §11 and 125D §12, regardless
of any candidate's evaluated readiness:

- execution capability;
- autonomous decision making;
- Decision Evaluation authority;
- runtime mutation;
- autonomous repository modification;
- execution planning implementation.

## 11. Known Inherited Issues

Carried forward unchanged, not repaired in this phase:

- 119Q report-generation-ordering defect: lifecycle/tooling debt.
- 119AB phase-id comparison bug: lifecycle/tooling debt.
- Recurring `pending_final_telegram_delivery` reporting detail:
  lifecycle/tooling debt.
- GitHub main-branch PR-rule bypass notification: repository hosting
  policy reporting detail.
- Missing `PCAE_NOTIFY_ENABLED` during governed push environment:
  notification environment detail (resolved for this session by
  sourcing `~/.config/pcae/telegram.env` before governance validation).

## 12. Strict Non-Goals

This phase does not: select the next architectural chapter; begin
implementation of any candidate; implement Historical Memory; implement
Dependency Knowledge Graph; implement Repository Intelligence
expansion; implement Decision Evaluation; implement Execution Planning;
introduce execution capability; modify runtime behavior; modify source
code; modify test code; modify schemas.

## 13. Governance Compatibility

This evaluation is compatible with PCAE governance:

- observe-only runtime remains unchanged;
- execution remains unavailable;
- evaluation is scoped through this governed phase only;
- no implementation path was selected;
- raw git commit/push, force push, and `--no-verify` remain forbidden
  and were not used;
- canonical reports remain complete and metadata-consistent;
- human-controlled lifecycle authority remains unchanged.

## 14. Confirmations

- **No architectural direction was selected.** All six candidates
  remain unselected; Sections 3-4 evaluate and compare without ranking
  a winner.
- **No implementation occurred.** This phase produced only
  documentation.
- **No runtime behavior changed.**
- **Execution remains unavailable.**

## 15. Conclusion

This evaluation executed the full 125D eight-stage methodology against
all six recognized candidate architectural directions, producing an
evidence-based comparative assessment grounded in direct inspection of
governed sources including previously-uncatalogued existing subsystems
(`decision_evaluation.py`, `permission_broker.py`). Historical Memory
and Dependency Knowledge Graph emerge as the two candidates with the
strongest combination of readiness and strategic value; Decision
Evaluation support carries the highest strategic upside alongside the
highest governance risk; Repository Intelligence expansion is
lowest-risk but weakest-justified; Execution Planning and Permission
Broker evolution both have unresolved preconditions. No candidate was
selected, ranked as a declared winner, or implicitly authorized.
Selection remains deferred to a future phase operating under 125B §6's
decision sequence.

Recommended next phase: 125F — Next Architecture Direction Decision
Review.
