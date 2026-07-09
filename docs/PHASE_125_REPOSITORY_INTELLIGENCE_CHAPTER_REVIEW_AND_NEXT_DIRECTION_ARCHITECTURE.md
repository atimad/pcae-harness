# Phase 125A - Repository Intelligence Chapter Review & Next Direction Architecture

## 1. Purpose

Phase 125A performs a chapter-level architectural review of the
complete Repository Intelligence subsystem — Tracks 119 through 124 —
and defines the architectural direction for the next PCAE chapter.

Tracks 119-124 are now complete. Repository Intelligence Version 1 is
complete. This phase asks: what did that chapter actually build, what
does it deliberately not do yet, how mature is it against PCAE's
governance principles, and what should PCAE consider building next.

125A is architecture-only. It implements no new Repository Intelligence
capability, no new artifact family, no Historical Memory, no
Dependency Knowledge Graph, no Advisory reasoning, no Decision
Evaluation integration, no execution planning, no execution capability,
no runtime plugin, no source code, no test code, and no schema change.
It selects no implementation path for future work — it evaluates
candidates only.

## 2. Repository Intelligence Chapter Review

### 2.1 Track 119 — Executable Schemas

Track 119 (118A-118E, 118R, then 119A through 119AC) built the
conceptual and executable schema foundation. It froze a three-level
contract (conceptual contract 119A/119B, conceptual schema 119C/119D,
artifact contract 119E/119F), then implemented and verified a complete
JSON Schema Draft 2020-12 line: **twelve shared components** (common
artifact envelope, source attribution record, evidence link record,
uncertainty/verification state, boundary disclosure, disclaimer,
limitation record, conflict/supersession record, derivation record,
phase context, release context, repository context) and **eight
artifact-family schemas** (Contract Conformance Record, Repository
Knowledge Snapshot, Historical Memory Snapshot, Dependency Knowledge
Graph Snapshot, Change Impact Report, Advisory Intelligence Context
Package, Query Result, Repository Intelligence Package).

119AC's cross-schema final review confirmed the full twenty-schema set
parses cleanly, uses a single JSON Schema draft, has unique `$id`s and
fully-resolving local `$ref`s, uniformly requires the common envelope,
source attribution, uncertainty state, boundary disclosures, and
disclaimers, uses `additionalProperties: false` on 107 of 108 object
definitions (the one exception is a reviewed, intentional design
choice), and is free of authority-creep language across the entire
set. **Only one of the eight schema families — Repository Knowledge
Snapshot — was ever carried into an actual generator.** The other seven
(Historical Memory Snapshot, Dependency Knowledge Graph Snapshot,
Change Impact Report, Advisory Intelligence Context Package, Query
Result, Repository Intelligence Package, Contract Conformance Record)
remain schema-only vocabulary: verified, frozen, and available for a
future implementation phase, but never populated by generated data.
This is the chapter's most consequential structural fact and shapes
every gap identified in Section 4.

### 2.2 Track 120 — Repository Knowledge Snapshot

Track 120 (120A-120F) turned exactly one of the eight 119 schema
families — Repository Knowledge Snapshot — into a real, deterministic,
read-only generator (`src/pcae/repository_intelligence/
snapshot_generator.py`, `snapshot_builder.py`, `source_inventory.py`,
`persistence.py`), exposed through `pcae repository-intelligence
snapshot generate`. The snapshot derives architectural entities,
capabilities, subsystems, contracts, and source attribution from
already-governed repository sources (source tree, existing docs,
existing contracts) — not from repository scanning, AI inference, or
network access. It is the foundational layer every later track
consumes.

### 2.3 Track 121 — Query Layer

Track 121 (121A-121F) implemented a deterministic, read-only Query
Layer (`src/pcae/repository_intelligence/query/`) over Repository
Knowledge Snapshot artifacts, supporting exactly six query categories:
entity lookup, capability lookup, architectural contract lookup,
attribution lookup, limitation lookup, and boundary lookup — exposed
through `pcae repository-intelligence query`. The Query Layer is the
single sanctioned access boundary into Repository Knowledge Snapshot
content: no later track reads snapshot files directly or reruns the
Track 120 generator. Every query fails closed on unsupported
categories, invalid snapshots, unsupported schema versions, or
malformed requests rather than guessing.

### 2.4 Track 122 — Advisory Context Builder

Track 122 (122A-122F) implemented the first Query Layer consumer: an
Advisory Context Builder (`src/pcae/advisory/context/`) that issues
bounded Query Layer requests and assembles a
`RepositoryIntelligenceContextPackage` — deliberately named distinct
from the frozen 115W `AdvisoryContextPackage` — preserving attribution,
limitations, and boundary disclosures from the underlying Query
Result. This is the first place Repository Intelligence content
becomes reachable by anything outside the Repository Intelligence
subsystem itself, and it does so without granting Repository
Intelligence any reasoning or decision authority: the context package
is input material, not a verdict.

### 2.5 Track 123 — Change Impact Builder

Track 123 (123A-123F) implemented the second, sibling Query Layer
consumer: a Change Impact Builder
(`src/pcae/repository_intelligence/change_impact/`) that, given a
declared change and target entities, assembles a deterministic,
descriptive `ChangeImpactReport` of already-known related entities —
exposed through `pcae repository-intelligence change-impact`. Like
Track 122, it reaches Repository Intelligence exclusively through the
Track 121 Query Layer, surfaces no fact the Query Layer could not
already return to any other caller, and makes no recommendation,
safety judgment, or risk prediction.

### 2.6 Track 124 — Chapter-Wide Hardening

Track 124 (124A-124F) reviewed Tracks 120-123 as one system rather than
four isolated components, identified two genuine cross-track
duplication seams (JSON serialization, Query Layer consumer
validation), and consolidated them into two small shared internal
modules (`serialization.py`, `consumer_validation.py`) without changing
any externally observable behavior. 124F independently verified this
by diffing every changed line against its pre-hardening form. No
defect was found; no repair was required. Track 124 is the chapter's
consistency and quality closure, not a capability expansion.

### 2.7 Chapter Shape

The completed chapter is a single deterministic pipeline:

```
Track 119 schemas (8 families, 1 implemented)
        |
Track 120 generator -> Repository Knowledge Snapshot (the only generated artifact family)
        |
Track 121 Query Layer (6 read-only query categories, sole access boundary)
        |
   +----+----+
   |         |
Track 122   Track 123
Advisory    Change Impact
Context     Builder
Builder     (sibling consumers, symmetric contracts)
        |
Track 124 hardening (shared serialization + validation helpers, no behavior change)
```

## 3. Architectural Achievements

- A complete, independently verified, twenty-schema executable
  vocabulary for Repository Intelligence (Track 119), reusable by any
  future implementation phase without re-litigating contract design.
- A real, deterministic, source-attributed, read-only generator for one
  content-bearing artifact family (Repository Knowledge Snapshot),
  proving the generation model works end-to-end from governed sources
  to schema-conformant output.
- A single, exclusive, deterministic read-only access boundary (the
  Query Layer) that every downstream consumer — present and future — is
  architecturally required to go through, with fail-closed behavior on
  every unsupported or invalid input.
- Two symmetric, independently implemented Query Layer consumers
  (Advisory Context Builder, Change Impact Builder) proving the
  "sibling consumer" pattern generalizes: both preserve attribution,
  limitations, and boundary disclosures identically, and neither gained
  reasoning or decision authority by consuming Repository Intelligence.
- A demonstrated hardening discipline (Track 124) that can review a
  multi-track pipeline as one system, find real duplication, and
  consolidate it with zero behavior drift — verified independently
  rather than self-certified.
- A stable terminology and structural vocabulary (attribution bundle,
  limitation bundle, boundary disclosure bundle, source artifact,
  unknown/unavailable/incomplete/conflicting) that has held consistently
  across six tracks and eleven phase types without renaming or
  redefinition.
- A CLI surface (`pcae repository-intelligence {snapshot,query,
  change-impact}`) that is coherent, fail-closed, and free of hidden
  generation, scanning, execution, or network access.
- Zero runtime, execution, or Advisory-authority expansion across the
  entire chapter — six tracks, dozens of phases, and the runtime
  posture (`Observed` / `observe` / execution unavailable) has not
  moved once.

## 4. Remaining Architectural Gaps

These are intentionally deferred, not omissions or defects:

- **Historical Memory expansion.** The `historical_memory_snapshot`
  schema (119Q/119R) exists and is verified, but no generator, Query
  Layer support, or consumer for it exists. Repository Intelligence
  today has no temporal/historical dimension — it describes the
  repository at a snapshot, not how it got there.
- **Dependency Knowledge Graph expansion.** The
  `dependency_knowledge_graph_snapshot` schema (119S/119T) exists and
  is verified, but no generator, Query Layer support, or consumer
  exists. Change Impact (Track 123) identifies impact only through
  relationships already present in the Repository Knowledge Snapshot's
  flat entity/capability/contract model — it does not traverse a
  dependency graph, because no dependency graph is ever built.
- **Richer Repository Intelligence artifact families.** Five of the
  eight Track 119 schema families (Historical Memory Snapshot,
  Dependency Knowledge Graph Snapshot, Advisory Intelligence Context
  Package, Query Result as a persisted artifact rather than an
  in-memory response, Repository Intelligence Package as an aggregate
  container) remain schema-only. Only Repository Knowledge Snapshot was
  ever generated.
- **Advisory reasoning.** Track 122's Advisory Context Builder supplies
  context; nothing in the chapter reasons over that context, forms a
  recommendation, or evaluates evidence sufficiency. Repository
  Intelligence remains strictly upstream of Advisory reasoning, which
  itself remains out of this chapter's scope.
- **Decision Evaluation integration.** The Advisory Intelligence
  Context Package schema (119W) already defines a
  `decision_evaluation_handoff` structural field, but no Track
  119-124 phase wires Repository Intelligence context, Advisory
  context, or Change Impact reports into the Decision Evaluation
  subsystem. That handoff is a declared field shape only.
- **Execution planning.** No Track 119-124 phase reads, writes, or
  reasons about what a governed execution plan for a change would look
  like. Change Impact identifies affected entities; it does not
  sequence, gate, or plan any action against them.
- **Execution capability.** Runtime state remains `Observed`, maximum
  plugin capability remains `observe`, and execution remains
  unavailable across the entire chapter. No phase in Tracks 119-124
  touched this boundary.

## 5. Maturity Assessment

| Dimension | Assessment |
| --- | --- |
| **Determinism** | Mature. Every generator, query, and consumer produces equivalent logical output for equivalent input; verified by repeated regression execution at every track and independently re-verified in 124F without trusting prior reports. |
| **Governance** | Mature. Every phase across all six tracks used governed lifecycle/commit/push commands; every phase report is complete and metadata-consistent; no raw git commit/push occurred; `origin/main..HEAD = 0` has been the closing state of every phase. |
| **Reproducibility** | Mature for the one generated artifact family. Repository Knowledge Snapshot generation is reproducible from governed sources. Reproducibility for the seven unimplemented schema families is untested, since nothing generates them yet. |
| **Explainability** | Mature. Every artifact and result carries source attribution, and every consumer preserves it unchanged through the pipeline; verified by direct diff in 124F, not just by test pass/fail. |
| **Attribution** | Mature. Source attribution is required at the schema level (Track 119), enforced at generation (Track 120), preserved through query (Track 121), and independently re-validated by both sibling consumers (Tracks 122, 123) with symmetric fail-closed checks. |
| **Limitation propagation** | Mature. Snapshot-level limitations propagate through Query Layer results into both consumers unchanged; Track 124 hardening consolidated but did not alter this behavior, confirmed by independent verification. |
| **Boundary disclosures** | Mature. Every artifact and consumer output carries boundary disclosures distinguishing Repository Intelligence from Repository State, Evidence, Advisory reasoning, and execution authority; the distinction has held across six tracks without blurring. |
| **Maintainability** | Improving, recently exercised. Track 124 demonstrated the chapter can be reviewed and hardened as one system; the resulting shared helpers reduce duplication for any future consumer that needs the same serialization or validation pattern. Maintainability for the five unimplemented schema families is unknown, since no implementation exists to maintain. |

Overall: the **implemented slice** (one schema family, its generator,
the Query Layer, and two sibling consumers) is architecturally mature
against every PCAE governance principle. The **unimplemented slice**
(seven of eight schema families) carries no maturity signal yet,
because it has never been exercised by real code.

## 6. Architectural Readiness

Repository Intelligence Version 1 is ready to serve as a stable
foundation for a next chapter. The chapter has:

- a frozen, verified schema vocabulary that does not need
  re-architecture to support additional artifact families (the
  remaining seven families already have frozen schemas; they need
  generators/consumers, not new contract work);
- a proven generator pattern (Track 120) that a Historical Memory or
  Dependency Knowledge Graph generator could follow without inventing
  new architecture;
- a proven, extensible Query Layer that already anticipates additional
  query categories as new artifact families are added, without
  requiring a new access-boundary design;
- a proven "sibling consumer" pattern (Tracks 122, 123) that any future
  consumer (a third Query Layer consumer, or a Decision Evaluation
  handoff consumer) can replicate with known symmetry requirements;
- a demonstrated hardening/verification discipline (Track 124, and the
  124F/122F/121F precedent of catching real defects by re-deriving from
  source rather than trusting implementation docs) that scales to
  larger future chapters.

Readiness is **structural, not capability-complete**: the chapter is
ready to be *built upon*, not because it has finished everything it
could do, but because what it has built is solid enough not to require
rework before the next chapter begins.

## 7. Candidate Future Directions (Architectural Evaluation Only)

No implementation path is selected here. Each candidate is evaluated
only on architectural fit with the completed chapter.

### 7.1 Historical Memory

**Fit:** High. The schema (119Q/119R) is already frozen and verified.
The Track 120 generator pattern and Track 121 Query Layer extension
pattern both apply directly. Historical Memory would add a temporal
dimension current Repository Intelligence lacks (Section 4), which
could improve Change Impact's ability to describe *why* an entity
relates to another, not just *that* it does.
**Risk:** Historical Memory necessarily reads git/lifecycle history,
which is a larger and more heterogeneous source surface than Track
120's snapshot sources — governed source boundaries would need careful
architecture to avoid drifting toward repository scanning.

### 7.2 Dependency Knowledge Graph

**Fit:** High. The schema (119S/119T) is already frozen and verified.
It would give Change Impact (Track 123) a real graph to traverse
instead of relying solely on the flat Repository Knowledge Snapshot
entity model, directly closing the gap named in Section 4.
**Risk:** Graph construction and traversal are exactly the kind of
capability that can quietly grow toward inference or prediction if not
tightly scoped; 119AC's schema review already confirmed the graph
schema explicitly disclaims traversal/construction by PCAE tooling —
an implementation phase would need equally explicit boundary discipline.

### 7.3 Richer Repository Intelligence (remaining schema families)

**Fit:** Medium-High. Advisory Intelligence Context Package, Query
Result as a persisted artifact, and Repository Intelligence Package are
already schema-frozen. Implementing them would let Repository
Intelligence content be packaged and referenced as first-class
artifacts rather than only produced as in-memory Query Layer/consumer
output.
**Risk:** Lowest marginal capability gain per architectural risk unit
among the seven deferred families, since existing consumers (Tracks
122, 123) already get equivalent content without persistence. Most
valuable only once a downstream reason to persist (e.g. cross-session
Advisory context reuse) is identified.

### 7.4 Decision Evaluation Support

**Fit:** Medium. The Advisory Intelligence Context Package schema
already defines a `decision_evaluation_handoff` field shape (Section
4), so the contract-level hook exists. Wiring Repository Intelligence
context into an actual Decision Evaluation consumer would be the first
time Repository Intelligence content reaches a decision-authoritative
subsystem — even indirectly through Advisory context.
**Risk:** Highest governance sensitivity of the candidates listed here.
Decision Evaluation is PCAE's decision-authority boundary; any
integration must preserve the chapter's repeated invariant that
Repository Intelligence is never itself decision-authoritative, no
matter how many consumers sit between it and Decision Evaluation.

### 7.5 Execution Planning

**Fit:** Low, currently. Nothing in the completed chapter produces
output shaped for execution planning, and PCAE's runtime remains
execution-unavailable by explicit, repeatedly-reconfirmed design
(Section 4). Execution Planning would be architecturally premature
without a separate, explicitly scoped runtime-capability chapter
preceding it.
**Risk:** Conflates two different PCAE boundaries (Repository
Intelligence's read-only boundary and the runtime's execution-
unavailable boundary) if pursued as a Repository Intelligence
extension rather than its own governed chapter.

### 7.6 Permission Broker Evolution

**Fit:** Low, currently, and largely orthogonal to Repository
Intelligence. The Permission Broker already exists as
`execution_unavailable` in the runtime (Section 8), and no Track
119-124 phase touched it. Any evolution there is a runtime/governance
chapter question, not a Repository Intelligence chapter question.
**Risk:** Out of this chapter's natural scope; evaluating it further
here would blur chapter boundaries rather than clarify next direction.

## 8. Preserve Boundaries

Confirmed unchanged by this phase and by the complete Tracks 119-124
chapter:

- **Observe-only runtime**: runtime state remains `Observed`.
- **Execution unavailable**: maximum plugin capability remains
  `observe`; execution capability remains `unavailable`; zero runtime
  plugins are registered; Permission Broker status remains
  `execution_unavailable`.
- **Deterministic behavior**: every generator, query, and consumer in
  the chapter produces equivalent logical output for equivalent input,
  independently re-verified as recently as 124F.
- **Governance-first philosophy**: every phase across Tracks 119-124
  used governed lifecycle/commit/push commands; canonical phase reports
  remain complete and metadata-consistent; no raw git commit, raw git
  push, force push, or `--no-verify` occurred in this phase or in the
  reviewed chapter.

## 9. Recommended Roadmap

A high-level sequence for future architectural chapters, in
recommended order:

1. **125A-125F (this track)**: chapter review (125A, this document),
   contract freeze for whichever next direction is selected (125B),
   contract verification (125C), plan (125D), and — if the selected
   direction warrants prototyping rather than remaining
   architecture-only — implementation and verification phases
   following the now-proven 119-124 phase-type pattern.
2. **Recommended first candidate for 125B's contract scope: Dependency
   Knowledge Graph.** Of the candidates in Section 7, it has the
   highest architectural fit (frozen schema, direct gap closure for
   Change Impact) combined with governance risk that is well
   understood and already schema-disclaimed, making it the most
   tractable next capability chapter. This is a recommendation for
   125B's evaluation, not a decision made by 125A.
3. **Historical Memory** as a plausible second capability chapter,
   once Dependency Knowledge Graph (or an alternative selected in 125B)
   establishes a second precedent for extending the Track 120 generator
   pattern and Track 121 Query Layer pattern to a new artifact family.
4. **Richer Repository Intelligence (persisted Query Result,
   Repository Intelligence Package)** only once a concrete downstream
   consumer need is identified — persistence for its own sake is lower
   priority than the two generator-pattern chapters above.
5. **Decision Evaluation support** as its own explicitly scoped,
   higher-governance-sensitivity chapter, deliberately sequenced after
   the lower-risk knowledge-expansion chapters above so that pattern
   discipline is well-established before Repository Intelligence
   content reaches a decision-authoritative subsystem.
6. **Execution Planning and Permission Broker evolution** remain
   explicitly out of Repository Intelligence's roadmap. If PCAE pursues
   either, it should be its own governed chapter outside Track 125,
   preceded by its own architecture phase.

This roadmap is a recommendation for future governed phases to accept,
amend, or reject — it does not itself authorize any of the listed
work.

## 10. Known Inherited Issues

Carried forward unchanged, not repaired in this phase:

- 119Q report-generation-ordering defect.
- 119AB phase-id comparison bug.
- Recurring `pending_final_telegram_delivery` reporting detail.
- GitHub main-branch PR-rule bypass notification.
- Missing `PCAE_NOTIFY_ENABLED` during governed push environment
  (resolved for this session by sourcing
  `~/.config/pcae/telegram.env` before governance validation, per
  established practice).

## 11. Strict Non-Goals

125A does not implement: new Repository Intelligence capabilities; new
artifact families; Historical Memory; Dependency Knowledge Graph;
Advisory reasoning; Decision Evaluation; execution planning; execution
capability; runtime plugins; source code; test code; or schema changes.
125A selects no implementation path among the candidates evaluated in
Section 7 — that selection belongs to a future governed contract-freeze
phase.

## 12. Governance Compatibility

This architecture is compatible with PCAE governance:

- observe-only runtime remains unchanged;
- execution remains unavailable;
- chapter review and roadmap recommendation are scoped through a
  governed architecture phase;
- implementation of any candidate direction is deferred to a future
  explicit contract-freeze and implementation path;
- raw git commit/push, force push, and `--no-verify` remain forbidden
  and were not used;
- canonical reports remain complete and metadata-consistent;
- human-controlled lifecycle authority remains unchanged.

## 13. Conclusion

Repository Intelligence Version 1 (Tracks 119-124) is complete,
architecturally mature for the slice it implemented, and structurally
ready for a next chapter. It built one real generator, one exclusive
query boundary, two symmetric consumers, and a demonstrated hardening
discipline — all without ever touching the runtime's execution
boundary. Seven of eight schema families remain deliberately
unimplemented, along with Historical Memory, Dependency Knowledge
Graph, Advisory reasoning, Decision Evaluation integration, execution
planning, and execution capability. This document evaluates but does
not select among the candidate next directions; that selection belongs
to Phase 125B.

Recommended next phase: 125B — Next Architecture Direction Contract
Freeze.
