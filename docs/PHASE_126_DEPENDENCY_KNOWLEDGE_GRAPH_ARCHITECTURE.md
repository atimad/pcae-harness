# Phase 126A - Dependency Knowledge Graph Architecture

## 1. Purpose

Phase 126A defines the canonical architecture for the Dependency
Knowledge Graph: PCAE's future structural representation of repository
relationships, selected as the next architectural chapter in 125F and
confirmed as the readiness-improving priority in 125G.

Repository Intelligence and the Dependency Knowledge Graph answer two
different questions:

- **Repository Intelligence answers: "What exists?"** Track 120's
  Repository Knowledge Snapshot enumerates architectural entities,
  capabilities, subsystems, and contracts as a flat, source-attributed
  record.
- **Dependency Knowledge Graph answers: "How are those things
  related?"** It represents the structural relationships between
  already-known entities as a graph-shaped view — nodes and edges —
  rather than a flat list.

This is architecture only. It creates no generator, no traversal
implementation, no Query Layer changes, no consumer changes, no schema
modification, no source code, no test code, and no execution
capability. It defines what the graph is, what it may and may not do,
and how future phases (126B contract freeze, 126C contract
verification, 126D plan, 126E implementation, 126F verification) must
build it, without building any of it here.

## 2. Scope

The graph models relationships only.

- It does not perform reasoning.
- It does not make decisions.
- It does not execute actions.
- It does not replace Repository Intelligence artifacts — it is a
  second, complementary artifact family, not a redefinition of
  Repository Knowledge Snapshot.

This document does not implement: a graph builder; graph storage;
graph traversal; graph queries; a graph database; graph serialization;
graph reasoning; source code; test code; schema changes; or any change
to runtime behavior.

## 3. Architectural Objectives

- **Deterministic relationship modeling** — equivalent Repository
  Knowledge Snapshot input must produce equivalent graph output, with
  no randomness, AI inference, or ambient state dependence, matching
  the discipline every Repository Intelligence artifact family has
  held since Track 120.
- **Reproducible graph construction** — a future generator must be
  re-runnable against the same snapshot and produce logically
  identical output.
- **Explainable relationships** — every node and edge must be traceable
  to the Repository Knowledge Snapshot content and derivation rule that
  produced it.
- **Provenance preservation** — every node, edge, and dependency claim
  carries its own source attribution, not just the graph as a whole
  (Section 9).
- **Auditability** — graph construction must produce a canonical,
  inspectable record of what was derived and how, following the same
  phase-report discipline every Repository Intelligence phase has used.
- **Governance compatibility** — the graph must fit governed lifecycle,
  commit, push, report, and notification discipline without requiring
  ungoverned shortcuts.
- **Structural completeness (as claimed, not as fact)** — the graph
  must honestly represent its own completeness state (`graph_
  completeness_state`, already frozen in the 119S/119T schema as one
  of `complete_claimed_by_source`, `partial`, `incomplete`, `unknown`,
  `not_assessed`, `unverifiable`) rather than implying totality it
  cannot support.
- **Compatibility with Repository Intelligence** — the graph must
  consume Repository Intelligence exclusively through the existing
  Track 121 Query Layer boundary, following the Track 122/123
  sibling-consumer pattern, and must not modify any already-frozen
  Track 119-124 file (125B §7, reaffirmed by 125F).

## 4. Conceptual Graph Model

### 4.1 Nodes

The 119S/119T frozen schema already defines a closed `node_type` enum:
`repository`, `package`, `module`, `file`, `document`, `schema`,
`command`, `configuration`, `test`, `task`, `phase`, `release`,
`runtime_component`, `advisory_component`, `evidence_artifact`,
`repository_skill`, `contract`, `unknown`.

126A adopts this frozen enum as the graph's node taxonomy rather than
inventing a parallel one. Mapping the conceptual node categories this
phase was asked to consider onto that frozen enum:

| Conceptual category | Frozen `node_type` mapping |
| --- | --- |
| repository | `repository` |
| package, module, file | `package`, `module`, `file` (already distinct) |
| class, function | **not directly represented** — see Section 4.3 |
| schema | `schema` |
| artifact | `evidence_artifact` (closest existing fit) |
| document | `document` |
| phase | `phase` |
| task | `task` |
| command | `command` |
| runtime component | `runtime_component` |
| plugin | **not directly represented** — closest is `runtime_component`, but a plugin is a specific runtime-registry concept (110E), not identical to a generic runtime component |
| test | `test` |
| report | **not directly represented** — closest is `evidence_artifact`, but phase reports are a specific, already-governed artifact type |

Every node conceptually carries: a stable identifier (`node_id`), its
type (from the frozen enum), a name, a status (`declared`, `known`,
`unknown`, `unverified`, `partially_verified`, `superseded`,
`conflicting` — already frozen), source attribution, verification
state, and limitations. 126A does not add, rename, or reinterpret any
`node_type` value.

### 4.2 Edges

The 119S/119T frozen schema already defines a closed `edge_type` enum:
`depends_on`, `references`, `documents`, `tests`, `configures`,
`governs`, `produces`, `consumes`, `verifies`, `supersedes`,
`related_to`, `derived_from`, `unknown`.

126A adopts this frozen enum as the graph's edge taxonomy. Mapping the
conceptual relationship categories this phase was asked to consider
onto that frozen enum:

| Conceptual relationship | Frozen `edge_type` mapping |
| --- | --- |
| contains | **not directly represented** — closest is `related_to`; containment (module contains function, package contains module) is structurally different from dependency and may need its own future value (Section 4.3) |
| imports, depends_on | `depends_on` |
| references | `references` |
| generates, produced_by | `produces` (direction reversed for `produced_by`) |
| validates, verifies | `verifies` |
| implements | **not directly represented** — closest is `depends_on` or `references` depending on the specific relationship; needs case-by-case resolution in 126B, not invention here |
| documents | `documents` |
| supersedes | `supersedes` |
| derives_from | `derived_from` |
| attributed_to | **not an edge concept** — attribution is a property of every node/edge/claim via `source_attribution`, not itself a graph relationship |
| related_to | `related_to` |
| consumed_by | `consumes` (direction reversed) |

Every edge conceptually carries: a stable identifier (`edge_id`), its
type (from the frozen enum), source and target node identifiers,
direction (`directed`, `undirected`, `bidirectional`, `mixed`,
`unknown` — already frozen), a relationship status (same closed
vocabulary as node status), source attribution, verification state,
and limitations. 126A does not add, rename, or reinterpret any
`edge_type` value.

### 4.3 Taxonomy Gaps — Explicitly Deferred, Not Silently Resolved

Sections 4.1 and 4.2 identify concepts (class/function nodes, plugin
nodes, report nodes, contains edges, implements edges) that the
already-frozen 119S/119T schema does not directly represent. 126A does
not resolve these gaps by inventing new enum values, since 126A
performs no schema change (Section 15). Instead:

- Where an existing frozen value is a reasonable, honest fit (e.g.
  `evidence_artifact` for generic artifacts, `related_to` for loose
  structural association), 126B's contract should adopt that mapping
  explicitly rather than leaving it implicit.
- Where no existing value fits honestly (e.g. class/function-level
  granularity, true containment semantics, plugin-specific identity),
  126B/126C must explicitly decide whether the graph's first version
  operates at package/module/file granularity only (deferring
  class/function-level nodes to a later, separately governed schema
  extension) or whether a schema-extension proposal is itself required
  before 126D can plan implementation. This decision belongs to 126B,
  not to this architecture document.

## 5. Graph Invariants

Every future graph artifact must satisfy:

- **Deterministic** — equivalent Repository Knowledge Snapshot input
  produces equivalent node/edge/claim output.
- **Acyclic where required** — some edge types (e.g. `depends_on`) are
  expected to form a DAG in a well-formed repository; the graph must
  represent a detected cycle honestly (as a `conflicting` or `unknown`
  relationship status, or via a limitation record) rather than silently
  dropping or resolving it. The graph does not enforce acyclicity by
  construction — it reports what it finds.
- **Stable identifiers** — `node_id`/`edge_id` values must be
  deterministic functions of their underlying Repository Intelligence
  source, not incidental generation-order artifacts, so that repeated
  generation produces the same identifiers for the same underlying
  facts.
- **Provenance preserved** — every node, edge, and dependency claim
  carries its own `source_attribution` (already required by the frozen
  schema); the graph as a whole additionally carries
  `dependency_sources`.
- **Relationship attribution preserved** — an edge's attribution must
  cite the specific Repository Knowledge Snapshot content it was
  derived from, not merely "the snapshot" generically.
- **Boundary preservation** — every graph artifact carries `boundary_
  disclosures` and the frozen `dependency_knowledge_graph_snapshot_
  disclaimer` const string, unchanged.
- **Limitation propagation** — snapshot-level limitations inherited
  from the underlying Repository Knowledge Snapshot must propagate into
  the graph unchanged, exactly as Tracks 122 and 123 already propagate
  them into their own outputs.
- **Reproducible construction** — a future generator's own
  `graph_generation_method_disclosure` (Section 9) must describe a
  process that, given the same inputs, is re-runnable to the same
  output.

## 6. Relationship with Repository Intelligence

**Repository Intelligence remains the source of observed facts. The
graph derives structural relationships from Repository Intelligence.
Repository Intelligence remains authoritative. The graph is
derivative.**

Concretely: a future Dependency Knowledge Graph generator's only input
is an existing Repository Knowledge Snapshot artifact, reached
exclusively through the Track 121 Query Layer — never by direct file
access, never by repository scanning, never by rerunning the Track 120
generator itself. The graph does not observe the repository
independently; it re-expresses relationships that Repository
Knowledge Snapshot content already implies (e.g. two entities that
share a source-attributed relationship in the snapshot become a graph
edge), plus relationships derivable from that content by deterministic
rule (e.g. declared import statements already captured in snapshot
source references). The graph introduces no new fact-finding capacity
Repository Intelligence itself does not already possess in
Track 120's source material.

This mirrors exactly the relationship Tracks 122 and 123 already have
with Track 121: consumer, never source; deterministic, never
inferential; bounded by Query Layer access, never by direct snapshot
file reads.

## 7. Relationship with Track 121 Query Layer

The graph is a second content-bearing artifact family alongside
Repository Knowledge Snapshot, and — once implemented — must become
queryable through new Query Layer categories, following the exact
extension pattern Track 121's own architecture anticipated (121A §15
named future consumers without pre-committing to their shape).

Conceptually anticipated future query categories (not implemented
here): node lookup (by id/name/type), edge lookup (by source/target/
type), relationship lookup between two named entities, and boundary/
limitation lookup for the graph artifact itself — mirroring the six
categories the Track 121 Query Layer already supports for Repository
Knowledge Snapshot (entity lookup, capability lookup, contract lookup,
attribution lookup, limitation lookup, boundary lookup). No query
category is implemented, and no existing Query Layer code changes, in
this phase.

## 8. Relationship with Advisory Context

Advisory may eventually consume graph relationships exactly as it
already consumes Repository Knowledge Snapshot content today: through
a bounded Query Layer request, with attribution, limitations, and
boundary disclosures preserved unchanged into the assembled Advisory
context package. The graph would become one more source-attributed
input among many Advisory already reads — it would not out-rank,
override, or substitute for any of them, and it would not grant
Advisory any new authority.

**No Advisory reasoning is implemented, implied, or authorized by this
phase.** Track 122's Advisory Context Builder itself is not modified.

## 9. Relationship with Change Impact

Structural relationships may eventually let Track 123's Change Impact
Builder replace its current flat entity-model impact identification
with real relationship traversal — directly closing the gap 125A, 125E,
and 125F all identified as Dependency Knowledge Graph's clearest,
most concretely evidenced strategic value. A future Change Impact
Builder revision could ask the graph "what depends on this entity"
rather than only scanning a flat entity list for name matches.

**No impact reasoning, blast-radius computation, or traversal
algorithm is implemented in this phase.** Track 123's Change Impact
Builder itself is not modified.

## 9A. Resolving the `graph_generation_method_disclosure` Question

125F named this 126A's first explicit responsibility: reconciling the
existing schema's `graph_generation_method_disclosure` field (119T
§14) before any generator work proceeds.

Direct inspection of the frozen schema (119S/119T) resolves this
cleanly, without any schema change: `graph_metadata.graph_generation_
method_disclosure` is a required, free-text (`minLength: 1`) field
whose own schema description states only that it "does not assert that
a graph was constructed, traversed, or queried by PCAE tooling." This
is **not** a const-`false` disclaimer that blocks a real generator from
ever existing — it is a guard against a *declared-but-unbuilt* graph
artifact falsely implying automated construction happened when it did
not (e.g. a hand-authored or externally-sourced graph view).

**Resolution:** once a real Track 126 generator exists, honestly
populating this field with a specific, accurate description of that
generator's own deterministic process (e.g. "generated by `pcae
repository-intelligence dependency-graph generate`, deriving edges from
Repository Knowledge Snapshot `<id>`'s existing source-attributed
entity references and import declarations, per the 126B contract's
frozen extraction rules") is fully compliant with the schema exactly
as frozen — not a violation of it, and not something requiring a
schema amendment. The field exists precisely so a real generator has
somewhere honest to say what it did; it does not need to be reconciled
away, worked around, or amended. 126B's contract freeze should adopt
this resolution explicitly, and any future generator (126E) must
populate this field with generator-specific, truthful content rather
than a vague or boilerplate string.

## 10. Provenance Architecture

Every relationship must preserve, unchanged from what the frozen
119S/119T schema already requires:

- **Source attribution** — every node, edge, and dependency claim
  requires at least one `source_attribution` record citing the
  Repository Knowledge Snapshot content it was derived from.
- **Derivation** — the graph's optional `derivation_records` (shared
  component, already used by seven of eight Track 119 artifact
  families) may record the deterministic rule that produced a given
  relationship, distinct from source attribution (which cites *what*
  was read; derivation records describe *how* it was transformed).
- **Evidence chain** — optional `evidence_links` connect graph claims
  to Evidence Link Records exactly as every other Repository
  Intelligence artifact family already does, preserving the
  established boundary that Evidence links are bridge/candidate
  records, never accepted Evidence themselves.
- **Uncertainty** — every node, edge, and claim carries a
  `verification_state` from the shared, already-frozen vocabulary
  (`known`, `unknown`, `unverified`, `partially_verified`, `weak`,
  `possible`, `inferred`, `advisory_only`, `decision_required`,
  `verified`, `invalid`, `stale`, `superseded`, `conflicting`).
- **Limitations** — every node, edge, claim, and the graph snapshot as
  a whole require at least one limitation record, preventing false
  completeness at any level of the artifact.

## 11. Boundary Architecture

Preserved, unchanged from the frozen schema and from the boundary
discipline every Track 119-124 phase has held:

- **Boundary disclosures** — the graph requires `boundary_disclosures`
  (shared component) with its const-`true` declarations (`read_only`,
  `no_execution`, `non_decision`, `advisory_non_authority`,
  `decision_evaluation_required`, `no_repository_mutation`,
  `no_lifecycle_mutation`, `no_evidence_replacement`, `no_repository_
  state_replacement`).
- **Limitation propagation** — snapshot-level limitations inherited
  from the underlying Repository Knowledge Snapshot must appear in the
  graph unchanged; the graph may add its own additional limitations
  but must never drop, weaken, or replace inherited ones (125B §7's
  "inherited limitations cannot be dropped, weakened, replaced, or
  masked by additive consumer limitations" — restated for the graph
  layer specifically).
- **Fail-closed behavior** — an unsupported, ambiguous, or
  under-evidenced relationship must resolve to an honestly-labeled
  `unknown`/`unverified` claim or be omitted with a corresponding
  limitation record — never silently inferred, never guessed into a
  confident-looking edge.
- **Observe-only operation** — graph construction reads an existing
  Repository Knowledge Snapshot and produces a new artifact; it
  performs no repository scanning, no execution, no shell mediation,
  and no runtime state change.

## 12. Versioning Architecture

Conceptual versioning for the graph, mirroring the Track 119
conventions already established for every other artifact family (no
storage implementation occurs in this phase):

- **Schema/contract version** — the graph's executable schema version
  is already frozen as `119S.1.0-json-schema` (or the current
  equivalent per the schema's own `$id`/version metadata); 126B's
  contract freeze must cite this version explicitly, not silently
  assume it.
- **Graph snapshot identity** — each generated graph carries its own
  `snapshot_identity`/`graph_id`, distinct from (but referencing) the
  Repository Knowledge Snapshot it was derived from.
- **Source snapshot reference** — every graph artifact must record
  which specific Repository Knowledge Snapshot (by its own snapshot
  identity) it was derived from, so a graph can never be interpreted
  independently of its source snapshot's own version/limitations.
- **Regeneration, not mutation** — consistent with every existing
  Repository Intelligence artifact family, a graph is regenerated fresh
  from its source snapshot when the underlying repository changes; no
  incremental/patch-based graph mutation model is proposed or assumed.

## 13. Graph Construction Pipeline (Conceptual)

Architecture only — no stage below is implemented in this phase:

1. **Repository Intelligence input** — an existing Repository
   Knowledge Snapshot artifact, reached through the Track 121 Query
   Layer.
2. **Relationship extraction** — deterministic identification of
   candidate node/edge facts from snapshot content (e.g. declared
   entity references, source locators, existing attribution records).
3. **Normalization** — mapping extracted facts onto the frozen
   `node_type`/`edge_type` taxonomy (Section 4), resolving taxonomy
   gaps per whatever 126B decides (Section 4.3), and assigning stable
   identifiers (Section 5).
4. **Graph assembly** — constructing the node/edge/dependency-claim
   collection, computing declared metadata (`node_count`, `edge_count`,
   `graph_completeness_state`), and populating `graph_generation_
   method_disclosure` (Section 9A) honestly.
5. **Consistency validation** — checking the assembled graph against
   the invariants in Section 5 (stable identifiers, provenance
   presence, no orphan edges referencing nonexistent nodes) before
   the artifact is considered complete.
6. **Persistence** — writing the graph artifact following the same
   `persistence.py`-style pattern Track 120 already established, kept
   distinct from the source Repository Knowledge Snapshot artifact.
7. **Reporting** — the graph generation's own canonical phase report,
   following the same discipline every Repository Intelligence
   generation phase has used.

## 14. Failure Architecture

**Graph construction must never infer unsupported relationships.
Unknown relationships remain unknown.**

- If Repository Knowledge Snapshot content does not clearly support a
  candidate relationship, the graph must either omit it entirely (with
  a corresponding limitation record explaining the gap) or represent it
  with `relationship_status: unknown`/`verification_state: unknown` —
  never silently promote an ambiguous signal into a confident-looking
  edge.
- Missing attribution, missing limitations, missing boundary
  disclosure material, unsupported schema versions, corrupted
  Repository Intelligence input, and invalid Query Layer results must
  all fail closed — the graph generator refuses to produce output
  rather than producing an under-evidenced artifact — matching the
  fail-closed discipline every Track 120-124 phase already
  independently established and Track 124 specifically hardened.
- No fail-open path may be introduced. This is not a new principle for
  126A to invent — it is 125B §11's Failure Contract, restated for the
  graph layer specifically, since 125B remains binding for any future
  chapter that extends Repository Intelligence (125B §7).

## 15. Governance Compatibility

This architecture is compatible with PCAE governance:

- **Deterministic behavior** — preserved; Section 3, Section 5.
- **Auditability** — preserved; Section 3, Section 10.
- **Reproducibility** — preserved; Section 3, Section 5, Section 12.
- **Explainability** — preserved; Section 3, Section 10.
- **Execution unavailable** — preserved; runtime state remains
  `Observed`, maximum plugin capability remains `observe`, execution
  capability remains `unavailable`, and no phase in the planned 126A-F
  sequence changes this boundary (mirroring 125B §8's binding
  requirement, still in force).
- Raw git commit/push, force push, and `--no-verify` remain forbidden;
  this phase did not use them.
- Canonical reports remain complete and metadata-consistent.
- Human-controlled lifecycle authority remains unchanged.

## 16. Relationship to Future Chapters

The Dependency Knowledge Graph enables, without itself introducing:

- **Historical Memory** — a future temporal layer could reference
  graph relationships to describe not just that two entities relate,
  but when that relationship was introduced or changed, once both
  layers exist. 126A does not design this integration.
- **Richer Change Impact** — Section 9's traversal-based impact
  identification, once a real generator and Query Layer categories
  exist. 126A does not implement traversal.
- **Stronger Advisory Context** — Section 8's structural-relationship-
  aware context assembly, once wired. 126A does not implement this
  wiring.
- **Future Decision Evaluation** — 125E identified Decision Evaluation
  support as a deferred, higher-governance-sensitivity candidate;
  structural relationship data could eventually inform that
  integration's evidence base, but 126A introduces no Decision
  Evaluation change, and 115E's "Evidence never decides" principle
  remains untouched.
- **Eventual Execution Planning** — 125G's readiness assessment
  identified structural dependency knowledge as the largest concrete
  readiness gap for a future Execution Planning chapter; a real graph
  directly closes that gap once implemented. 126A introduces no
  execution planning, execution capability, or change to the
  execution-unavailable boundary.

None of these future integrations is designed, scoped, or authorized
by this phase. They are named here only to establish why the graph
matters architecturally, consistent with 125G §12's own forward
reference to this document.

## 17. Deferred Capabilities

Explicitly deferred, not implemented by this phase:

- graph implementation (generator);
- graph traversal;
- graph database;
- graph reasoning;
- inference engine;
- dependency prediction;
- execution planning;
- execution capability.

## 18. Known Inherited Issues

Carried forward unchanged, not repaired in this phase:

- 119Q report-generation-ordering defect: lifecycle/tooling debt,
  non-blocking for this architecture phase.
- 119AB phase-id comparison bug: lifecycle/tooling debt, non-blocking
  for this architecture phase.
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

## 19. Strict Non-Goals

This phase does not implement: a graph builder; graph storage; graph
traversal; graph queries; a graph database; graph serialization; graph
reasoning; source code; test code; schema changes; or any change to
runtime behavior.

## 20. Conclusion

Phase 126A defines the Dependency Knowledge Graph as PCAE's future
canonical structural representation of repository relationships — a
second, complementary Repository Intelligence artifact family that
derives from, and remains subordinate to, the authoritative Repository
Knowledge Snapshot. It adopts the already-frozen 119S/119T node and
edge taxonomy rather than inventing a new one, identifies concrete gaps
between that taxonomy and this phase's conceptual node/edge examples
for 126B to resolve explicitly, and defines graph invariants,
provenance architecture, boundary architecture, versioning strategy,
a conceptual construction pipeline, and fail-closed failure behavior —
all without implementing any of it. No implementation occurred. No
runtime behavior changed. Execution remains unavailable.

Recommended next phase: 126B — Dependency Knowledge Graph Contract
Freeze.
