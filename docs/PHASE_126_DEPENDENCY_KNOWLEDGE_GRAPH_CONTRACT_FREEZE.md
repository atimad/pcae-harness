# Phase 126B - Dependency Knowledge Graph Contract Freeze

## 1. Purpose

Phase 126B freezes the canonical contract for PCAE's Dependency
Knowledge Graph, operationalizing the architecture 126A defined into
binding, normative requirements.

The contract governs structure and behavior, not implementation. It
is binding for:

- 126C - Dependency Knowledge Graph Contract Verification;
- 126D - Dependency Knowledge Graph Plan;
- 126E - Dependency Knowledge Graph Implementation;
- 126F - Dependency Knowledge Graph Verification.

126B is documentation only. It creates no generator, no traversal
implementation, no Query Layer changes, no consumer changes, no schema
modification, no source code, no test code, and no runtime behavior
change.

## 2. Contract Authority

This document is the canonical Track 126 Dependency Knowledge Graph
contract unless explicitly superseded by a future governed
contract-amendment phase. It operates inside, and does not amend, the
125B Next Architecture Direction Contract (still binding per 125B §7's
requirement that any Repository Intelligence extension follow its own
architecture -> contract -> verification -> plan -> implementation ->
verification sequence).

Later Track 126 phases may verify, plan, and implement only inside
this contract's constraints. No later phase may silently reinterpret
this contract as authorizing capability expansion, runtime behavior
change, execution capability, or a schema change without its own
separate, explicitly scoped governed contract-amendment phase.

## 3. Scope

The graph models structural relationships only. It shall not:

- infer unsupported relationships;
- perform reasoning;
- execute traversal algorithms;
- make decisions;
- replace Repository Intelligence;
- replace Advisory;
- replace Change Impact.

The contract applies to the future graph artifact family's structure,
invariants, provenance, limitations, boundary disclosures, determinism,
compatibility, and failure behavior. It does not itself construct,
persist, traverse, query, or reason over a graph — those remain
implementation concerns for 126D-126E, bounded by this contract.

## 4. Node Contract

### 4.1 Canonical Node Responsibilities

A node represents one architectural entity already known to Repository
Intelligence. A node's sole responsibility is to declare, with
provenance, that an entity exists and what kind of entity it is. A
node never asserts a relationship (that is an edge's responsibility),
never asserts truth beyond what its source attribution supports, and
never carries decision, execution, or authority semantics.

### 4.2 Frozen Node Category Vocabulary

The graph's node categories are the already-frozen 119S/119T
`node_type` enum, adopted unchanged by 126A and re-frozen here as
binding for 126C-126F:

`repository`, `package`, `module`, `file`, `document`, `schema`,
`command`, `configuration`, `test`, `task`, `phase`, `release`,
`runtime_component`, `advisory_component`, `evidence_artifact`,
`repository_skill`, `contract`, `unknown`.

### 4.3 Resolving 126A's Flagged Node Taxonomy Gaps

126A (§4.3) explicitly deferred resolving the gap between this frozen
enum and the fuller conceptual node list a future graph might want
(class, function, artifact, plugin, report), assigning that decision to
126B. This contract resolves it as follows, binding for 126C-126F:

- **Artifact** maps to the existing `evidence_artifact` value. No new
  value is needed; this is a reasonable, honest fit per 126A's own
  assessment.
- **Report** maps to the existing `evidence_artifact` value for v1.
  Phase reports are a specific, already-governed artifact type, but
  introducing a dedicated `report` node-type value would be a schema
  change, which this contract does not authorize (Section 16). A
  future schema-extension proposal may introduce a dedicated value if
  concrete need is demonstrated; until then, `evidence_artifact` is the
  frozen v1 mapping.
- **Plugin** maps to the existing `runtime_component` value for v1,
  with the node's own `node_label`/`node_role` fields (already part of
  the frozen node shape) used to distinguish "this runtime_component is
  specifically a registered plugin" from other runtime components. No
  new node-type value is introduced.
- **Class and function** are **explicitly out of scope for the graph's
  first version.** The graph's v1 granularity is bounded to
  `repository`/`package`/`module`/`file` and the other already-frozen
  non-source-code node types — it does not model class- or
  function-level entities. This is a deliberate scope decision, not an
  oversight: Repository Knowledge Snapshot (Track 120) itself does not
  currently extract class/function-level entities, so a graph built
  from it has no source-attributed basis for class/function nodes at
  v1. Introducing class/function granularity would require both a
  Repository Knowledge Snapshot extraction change (outside Track 126's
  own scope, which by 125B §7 must not modify Track 120 without its
  own separate governed phase) and a schema-extension proposal for new
  `node_type` values. Class/function-level graph nodes are therefore
  deferred to a future, separately governed chapter — not something
  126D may plan around or 126E may implement as an interim workaround.

### 4.4 Stable Identity Requirements

Every node's `node_id` must be:

- a deterministic function of the node's underlying Repository
  Knowledge Snapshot source content — never an incidental generation-
  order artifact (e.g. `"node-1"`, `"node-2"`);
- stable across repeated generation from the same snapshot — identical
  snapshot input must produce an identical `node_id` for the same
  underlying entity;
- unique within a single graph artifact.

This contract does not prescribe a specific identifier algorithm
(e.g. a hash function or a namespaced-path scheme) — that is a 126D
planning decision — but any algorithm 126D selects must satisfy the
determinism and stability requirements above.

## 5. Edge Contract

### 5.1 Frozen Relationship Category Vocabulary

The graph's edge categories are the already-frozen 119S/119T
`edge_type` enum, adopted unchanged by 126A and re-frozen here as
binding for 126C-126F:

`depends_on`, `references`, `documents`, `tests`, `configures`,
`governs`, `produces`, `consumes`, `verifies`, `supersedes`,
`related_to`, `derived_from`, `unknown`.

### 5.2 Resolving 126A's Flagged Edge Taxonomy Gaps

126A (§4.2, §4.3) identified conceptual relationship categories without
a clean 1:1 frozen-enum mapping. This contract resolves them, binding
for 126C-126F:

- **imports** maps to `depends_on`.
- **generates** / **produced_by** map to `produces` (direction
  reversed for `produced_by`, using the edge's own `direction` field
  rather than a distinct edge type).
- **validates** / **verifies** map to `verifies`.
- **consumed_by** maps to `consumes` (direction reversed, same pattern
  as `produced_by`).
- **derives_from** maps to `derived_from`.
- **supersedes** maps to `supersedes` directly.
- **documents** maps to `documents` directly.
- **related_to** maps to `related_to` directly.
- **contains** maps to `related_to` for v1. True hierarchical
  containment semantics (distinct from generic structural association)
  are **not** distinguished from other `related_to` relationships at
  v1. This is a deliberate, documented v1 limitation — a future
  generator must record this limitation on every containment-shaped
  relationship it represents via `related_to`, rather than silently
  presenting it as equivalent in precision to a dedicated containment
  edge type. Introducing a dedicated `contains` edge-type value is
  deferred to a future schema-extension proposal.
- **implements** maps to `depends_on` for v1, on the rationale that an
  entity implementing a contract depends on conforming to that
  contract's requirements. This is a considered, not arbitrary, mapping
  — 126D must document this mapping explicitly wherever it is applied,
  since `depends_on` is being asked to carry two conceptually distinct
  relationships (general dependency and contract-implementation) with
  the same edge type.
- **attributed_to** is **not an edge concept.** Attribution is a
  property every node, edge, and dependency claim already carries via
  its own `source_attribution` field (Section 6). It is not itself a
  graph relationship between two nodes and must not be modeled as an
  edge.

### 5.3 Relationship Semantics

An edge asserts a declared, source-attributed relationship between
exactly two nodes (`source_node_id`, `target_node_id`), with a
direction (`directed`, `undirected`, `bidirectional`, `mixed`,
`unknown` — already frozen) and a relationship status drawn from the
same closed vocabulary as node status (`declared`, `known`, `unknown`,
`unverified`, `partially_verified`, `superseded`, `conflicting`).

An edge never asserts strength, necessity, or importance beyond what
its own `dependency_strength` claim (where present, via a
`dependency_claim` record — already frozen: `required`, `optional`,
`weak`, `inferred`, `possible`, `unknown`, `conflicting`, `stale`,
`superseded`) explicitly states. An edge's mere existence in the graph
is not itself a claim of certainty.

## 6. Graph Invariant Contract

The following invariants are frozen, binding for 126C-126F:

- **Deterministic** — equivalent Repository Knowledge Snapshot input
  must produce equivalent graph structure (node set, edge set,
  identifiers, claims) — no randomness, AI inference, or ambient state
  dependence.
- **Reproducible** — a graph generator must be re-runnable against the
  same snapshot and produce logically identical output across repeated
  runs.
- **Provenance preserving** — every node, edge, and dependency claim
  carries `source_attribution`; the graph as a whole carries
  `dependency_sources`.
- **Limitation preserving** — snapshot-level limitations inherited from
  the underlying Repository Knowledge Snapshot must appear in the graph
  unchanged (Section 8).
- **Boundary preserving** — every graph artifact carries
  `boundary_disclosures` and the frozen
  `dependency_knowledge_graph_snapshot_disclaimer` const string,
  unchanged (Section 9).
- **Stable identifiers** — Section 4.4.
- **Version compatible** — Section 13.
- **Fail closed** — Section 12.

## 7. Provenance Contract

Every node and relationship must preserve, without reinterpretation:

- **Source attribution** — at least one `source_attribution` record
  citing the specific Repository Knowledge Snapshot content the node
  or edge was derived from (not a generic "the snapshot" reference).
- **Derivation** — where a relationship required a transformation
  beyond direct citation (e.g. resolving a declared import statement
  into a `depends_on` edge), the deterministic rule applied should be
  recorded via a `derivation_record` (shared component), distinct from
  source attribution.
- **Evidence chain** — optional `evidence_links` connecting graph
  claims to Evidence Link Records, preserving the established boundary
  that Evidence links are bridge/candidate records, never accepted
  Evidence themselves.
- **Uncertainty** — every node, edge, and claim carries a
  `verification_state` from the shared, already-frozen vocabulary.
- **Limitations** — every node, edge, claim, and the graph snapshot as
  a whole require at least one limitation record.
- **Verification status** — the node/edge `status` fields (`declared`,
  `known`, `unknown`, `unverified`, `partially_verified`, `superseded`,
  `conflicting`) must accurately reflect what the source evidence
  supports, never upgraded for presentation convenience.

No future phase may reinterpret attribution as proof of truth, merge
records in a way that loses per-record provenance, or convert an
evidence gap into evidence support.

## 8. Limitation Contract

Limitations shall propagate without modification. Specifically:

- Snapshot-level limitations inherited from the underlying Repository
  Knowledge Snapshot must appear in the graph artifact unchanged —
  never dropped, weakened, replaced, or masked by additive graph-level
  limitations (125B §7's inherited-limitation rule, restated for the
  graph layer).
- The graph may add its own additional limitations specific to graph
  construction (e.g. the v1 containment/implements-mapping limitations
  named in Section 5.2, or class/function-granularity exclusion named
  in Section 4.3) — these are additive, not substitutive.
- A future consumer of the graph (e.g. a revised Change Impact Builder)
  must itself propagate both the inherited snapshot-level limitations
  and the graph's own added limitations unchanged, exactly as Tracks
  122 and 123 already do for Repository Knowledge Snapshot limitations.

## 9. Boundary Disclosure Contract

Boundary disclosures shall propagate unchanged:

- The graph artifact requires `boundary_disclosures` (shared
  component) with its const-`true` declarations (`read_only`,
  `no_execution`, `non_decision`, `advisory_non_authority`,
  `decision_evaluation_required`, `no_repository_mutation`,
  `no_lifecycle_mutation`, `no_evidence_replacement`,
  `no_repository_state_replacement`) and the frozen
  `dependency_knowledge_graph_snapshot_disclaimer` const string,
  unchanged from the 119S/119T schema.
- A future consumer of graph content must not blur the distinction
  between the graph, Repository Intelligence, Repository State,
  Evidence, Advisory context, Change Impact, Decision Evaluation, and
  execution authority — the same distinction every Repository
  Intelligence artifact family has held since Track 119.

## 10. Determinism Contract

Equivalent Repository Intelligence inputs must produce equivalent
graph structure. No nondeterministic relationship creation.

Specifically:

- Given the same Repository Knowledge Snapshot artifact as input, a
  graph generator must produce the same node set, edge set,
  identifiers, and dependency claims on every run.
- No relationship may be created by inference, heuristic guessing,
  probabilistic scoring, or AI-based judgment. Every edge must trace to
  an explicit, deterministic extraction or transformation rule
  (Section 7) applied to explicit Repository Knowledge Snapshot
  content.
- Ordering of nodes/edges within the serialized artifact must be
  deterministic (e.g. stable sort by identifier), consistent with the
  serialization discipline Track 124 already hardened for the rest of
  Repository Intelligence.

## 11. Compatibility Contract

The graph shall remain compatible with:

- **Track 119 executable schemas** — the graph consumes the already-
  frozen `dependency_knowledge_graph_snapshot.schema.json`
  (119S/119T) without modification; this contract authorizes no
  schema change.
- **Track 120 Repository Knowledge Snapshot** — the graph's only
  input; not modified by this contract or by any phase it binds.
- **Track 121 Query Layer** — the graph's only access path into
  Repository Intelligence content; not modified by this contract.
  Future graph-specific query categories are anticipated (126A §7)
  but not implemented or specified here.
- **Track 122 Advisory Context** — not modified by this contract;
  Advisory's eventual consumption of graph content (126A §8) remains
  unscoped and unauthorized by this phase.
- **Track 123 Change Impact** — not modified by this contract;
  Change Impact's eventual consumption of graph content (126A §9)
  remains unscoped and unauthorized by this phase.

Compatibility means the graph is additive to this existing stack. It
does not redefine any Track 119-124 contract, artifact family, schema
authority, Query Layer authority, Advisory authority, Change Impact
authority, or runtime authority.

## 12. Failure Contract

Unknown relationships remain unknown. Missing evidence produces
fail-closed behavior. No inferred edges without evidence.

- If Repository Knowledge Snapshot content does not clearly support a
  candidate node or edge, it must be omitted (with a corresponding
  limitation record) or represented with `unknown`/`unverified` status
  — never silently promoted into a confident-looking node or edge.
- Missing source attribution, missing limitations, missing boundary
  disclosure material, unsupported schema versions, corrupted
  Repository Intelligence input, and invalid Query Layer results must
  all cause graph construction to fail closed — refusing to produce
  output rather than producing an under-evidenced artifact.
- Detected cycles in edge types expected to be acyclic (e.g.
  `depends_on`) must be reported honestly (via `conflicting` status or
  a limitation record), never silently broken or resolved by dropping
  an edge.
- No fail-open path may be introduced by any phase this contract binds.

## 13. Version Compatibility Contract

Conceptual compatibility strategy, frozen for 126C-126F. No storage
format decisions occur in this phase.

- The graph's executable schema version is the already-frozen
  119S/119T version; this contract does not change it.
- Every graph artifact must record which specific Repository Knowledge
  Snapshot (by its own snapshot identity) it was derived from, so a
  graph can never be interpreted independently of its source
  snapshot's own version and limitations (126A §12).
- A future graph consumer must reject an unsupported schema/version
  combination rather than guess compatibility — matching the version-
  compatibility discipline every Track 119-124 consumer already holds.
- Graph regeneration, not incremental mutation, is the frozen model:
  a graph is regenerated fresh from its source snapshot when the
  underlying repository changes (126A §12). No patch/diff-based graph
  mutation model is authorized by this contract.

## 14. Governance Contract

Preserve, binding for every phase this contract governs:

- **Observe-only runtime** — unchanged.
- **Deterministic behavior** — Section 10.
- **Auditability** — every phase produces a complete, metadata-
  consistent canonical phase report; every graph artifact is
  independently inspectable.
- **Explainability** — every node, edge, and claim traces to specific
  Repository Knowledge Snapshot content and an explicit derivation
  rule (Section 7).
- **Reproducibility** — Section 6, Section 10.
- **Execution unavailable** — runtime state remains `Observed`,
  maximum plugin capability remains `observe`, execution capability
  remains `unavailable`; no phase this contract binds (126C-126F) may
  change this boundary.

## 15. Relationship Contract

Repository Intelligence remains authoritative. Dependency Knowledge
Graph is derivative. The graph shall never become the primary evidence
source.

- The graph's only input is an existing Repository Knowledge Snapshot,
  reached exclusively through the Track 121 Query Layer — never by
  direct file access, never by rerunning the Track 120 generator,
  never by repository scanning.
- The graph introduces no new fact-finding capacity beyond what
  Repository Knowledge Snapshot content already supports; it
  re-expresses and derives structural relationships from already-
  observed facts, it does not observe new facts itself.
- A future consumer (e.g. Change Impact) reading both Repository
  Knowledge Snapshot and the graph must continue to treat Repository
  Knowledge Snapshot as authoritative for entity existence and the
  graph as authoritative only for the structural relationships it
  itself declares — the graph does not override, supersede, or gain
  priority over Repository Intelligence's own content.

## 16. Deferred Capabilities

Explicitly deferred, not authorized by this contract:

- graph builder;
- graph persistence;
- graph traversal;
- graph database;
- graph query engine;
- graph reasoning;
- dependency prediction;
- execution planning;
- execution capability.

Any future work in these areas requires its own separate, explicitly
scoped governed architecture and contract path outside this contract's
authorization. This contract also does not itself authorize any
schema change (Section 11) — the node/edge taxonomy-gap resolutions in
Sections 4.3 and 5.2 operate entirely within the already-frozen
119S/119T schema and introduce no new schema value.

## 17. Technical Debt Classification

This phase classifies inherited technical debt only. It repairs none
of it.

- **Lifecycle/tooling debt**: 119Q report-generation-ordering defect;
  119AB phase-id comparison bug; recurring
  `pending_final_telegram_delivery` reporting detail.
- **Repository hosting policy reporting detail**: GitHub main-branch
  PR-rule bypass notification.
- **Notification environment detail**: missing `PCAE_NOTIFY_ENABLED`
  during governed push environment.

## 18. Known Inherited Issues

Carried forward unchanged and not repaired in this phase:

- 119Q report-generation-ordering defect: lifecycle/tooling debt,
  non-blocking for this contract freeze.
- 119AB phase-id comparison bug: lifecycle/tooling debt, non-blocking
  for this contract freeze.
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

This phase does not implement: graph construction; graph
serialization; graph persistence; graph traversal; graph database;
graph query language; graph reasoning; source code; test code; schema
changes; or any change to runtime behavior.

## 20. Relationship to Future Phases

- **126C - Dependency Knowledge Graph Contract Verification**:
  independently verify this contract before planning implementation
  work.
- **126D - Dependency Knowledge Graph Plan**: define the bounded
  implementation plan inside this contract, including a concrete
  identifier algorithm (Section 4.4) and explicit application of the
  Section 4.3/5.2 taxonomy-gap resolutions wherever they arise in real
  Repository Knowledge Snapshot content.
- **126E - Dependency Knowledge Graph Implementation**: implement only
  the bounded generator authorized by 126B-126D.
- **126F - Dependency Knowledge Graph Verification**: independently
  verify 126E's implementation against this contract and the 126D
  plan.

No 126C work begins in this phase.

## 21. Governance Compatibility

This contract is compatible with PCAE governance:

- observe-only runtime remains unchanged;
- execution remains unavailable;
- implementation remains deferred to a future explicit plan and
  implementation path;
- raw git commit/push, force push, and `--no-verify` remain forbidden;
- canonical reports must remain complete and metadata-consistent;
- human-controlled lifecycle authority remains unchanged.

## 22. Acceptance

126B is complete when this contract is frozen, project memory reflects
126B completion, runtime remains `Observed` / `observe` / execution
unavailable, no implementation has occurred, and the recommended next
phase is 126C - Dependency Knowledge Graph Contract Verification.
