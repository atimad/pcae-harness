# Phase 118D - Dependency Knowledge Graph Architecture

## Purpose

Phase 118D defines the Dependency Knowledge Graph for Track B:
Repository Intelligence.

The Dependency Knowledge Graph is PCAE's deterministic,
source-attributed, inspectable relationship layer inside Repository
Knowledge. It represents repository entities as graph nodes,
relationships as graph edges, and dependency assertions as
source-backed claims. It exists so future Repository Intelligence can
inspect architectural, source-code, documentation, test, contract,
evidence, advisory, historical, governance, lifecycle, release,
capability, subsystem, and no-go relationships without becoming a graph
implementation, runtime orchestration system, execution planner,
decision maker, or enforcement layer.

This phase is architecture only. It does not implement dependency graph
construction, a graph database, a graph CLI, a graph query engine, graph
visualization, Repository Knowledge extraction, Historical Memory
extraction, Change Impact Analysis, advisory behavior, Decision
Evaluation behavior, Evidence subsystem behavior, Repository Skills
behavior, runtime behavior, lifecycle redesign, execution, enforcement,
Permission Broker behavior, REST, Dashboard, Web UI, Telegram inbound,
provider selection, multi-model orchestration, autonomous coding,
automatic patch generation, or automatic refactoring.

## Track B Context

Track B asks whether PCAE can understand the repository itself.

Phase 118A defined Repository Knowledge as deterministic, inspectable,
source-attributed, read-only architectural understanding of repository
entities and relationships.

Phase 118B defined Historical Memory as the time-aware layer inside
Repository Knowledge: deterministic, source-attributed, versioned
understanding of how architecture, capabilities, contracts, constraints,
repairs, hardening, releases, and decisions evolved.

Phase 118C defined Change Impact Analysis as deterministic,
source-attributed, inspectable, read-only reasoning over Repository
Knowledge and Historical Memory to identify what may be affected by a
proposed or observed change.

Phase 118D answers the next Track B question: how should PCAE represent
repository dependency relationships as structured knowledge?

The Dependency Knowledge Graph must emerge from Repository Knowledge. It
must not become a separate silo, runtime orchestration graph,
implementation engine, autonomous planner, authorization path, or
execution mechanism.

## Relationship to 118A Repository Knowledge

118A already defines Knowledge Entity, Knowledge Relationship,
Knowledge Claim, Knowledge Source, Knowledge Evidence Link, and
Knowledge Snapshot. The Dependency Knowledge Graph specializes those
primitives for graph-shaped relationship inspection.

| 118A primitive | Dependency graph specialization |
| --- | --- |
| Knowledge Entity | Graph Node: source module, package, command, test, document, contract, phase, report, skill, evidence artifact, release record, no-go boundary, subsystem, capability, or lifecycle artifact. |
| Knowledge Relationship | Graph Edge: typed, directional relationship such as `imports`, `tests`, `documents`, `constrains`, `depends_on`, `introduced_by`, or `supports_decision_context`. |
| Knowledge Claim | Dependency Claim: source-attributed assertion that an edge or path exists with a dependency type, direction, scope, strength, verification state, and limitations. |
| Knowledge Source | Dependency Source: repository artifact supporting a node, edge, claim, path, view, or snapshot. |
| Knowledge Evidence Link | Dependency Evidence Link: bridge from a graph claim to Evidence that used, confirmed, contradicted, or was produced from it. |
| Knowledge Snapshot | Dependency Snapshot: reproducible graph view over a repository revision, source set, relationship taxonomy, and graph builder version. |

The graph is a relationship layer inside Repository Knowledge. It does
not replace the broader semantic map.

## Relationship to 118B Historical Memory

Historical Memory provides temporal edges and lineage context for graph
relationships.

Examples:

- Phase P `introduced_by` capability C.
- Phase P `hardened_by` contract K.
- Report R `repaired_by` phase P.
- Release V `included` subsystem S.
- Decision D `supersedes` earlier decision E.

These are graph edges and historical events at the same time. Historical
Memory explains when, why, and through which sources a relationship
appeared, changed, was hardened, was repaired, was superseded, or
entered a release. The Dependency Knowledge Graph provides the
inspectable relationship structure those temporal queries can traverse.

## Relationship to 118C Change Impact Analysis

Change Impact Analysis needs dependency paths, reverse edges, edge
types, graph views, and uncertainty states to explain possible blast
radius. The Dependency Knowledge Graph supplies that structured
relationship layer.

Impact analysis may ask:

- Which entities depend on this contract?
- Which tests verify this command?
- Which docs describe this subsystem?
- Which historical phases introduced or hardened this capability?
- Which advisory skill consumes this evidence category?
- Which no-go boundary protects this runtime capability?

The graph answers relationship questions. Change Impact Analysis applies
those answers to a proposed or observed change. Neither component
decides whether the change is allowed.

## Definition of Dependency Knowledge Graph

**Dependency Knowledge Graph** is the deterministic, source-attributed,
versioned graph view inside Repository Knowledge that represents
repository entities as nodes and repository-derived relationships as
typed, directional, inspectable edges with dependency claims, sources,
evidence links, verification states, uncertainty, and snapshots.

It answers questions such as:

- What entities exist in a relationship network?
- Which source, test, document, contract, phase, report, skill, release,
  or no-go artifact supports each node or edge?
- What depends on this subsystem, command, contract, or lifecycle
  artifact?
- Which tests, docs, reports, or phases trace to this capability?
- Which dependency paths are direct, indirect, weak, inferred,
  conflicting, stale, unknown, or superseded?
- Which graph view is relevant to advisory, governance, release,
  historical, or impact analysis questions?

## Dependency Knowledge Graph vs Repository Knowledge

Repository Knowledge is broader. It describes architectural entities,
relationships, claims, sources, snapshots, evidence links, views, and
reports.

The Dependency Knowledge Graph is a graph-shaped relationship layer
inside Repository Knowledge.

| Concept | Primary question | Role |
| --- | --- | --- |
| Repository Knowledge | What can PCAE know about repository architecture? | Broad semantic map. |
| Dependency Knowledge Graph | How are repository entities connected by dependency relationships? | Typed relationship projection over the semantic map. |

Repository Knowledge may contain prose claims, catalogs, indexes, and
non-graph views. The Dependency Knowledge Graph focuses on nodes, edges,
paths, views, snapshots, and graph queries.

## Dependency Knowledge Graph vs Historical Memory

Historical Memory is temporal. The Dependency Knowledge Graph is
structural.

| Concept | Primary question | Role |
| --- | --- | --- |
| Historical Memory | How did this entity or relationship evolve? | Time-aware lineage over Repository Knowledge. |
| Dependency Knowledge Graph | Which entities are related, and how? | Typed relationship network over Repository Knowledge. |

The graph may contain temporal edges such as `introduced_by`,
`modified_by`, `hardened_by`, `repaired_by`, `supersedes`, and
`released_in`. Historical Memory interprets those edges as lineage and
event history.

## Dependency Knowledge Graph vs Change Impact Analysis

Change Impact Analysis is reasoning over a specific change. The graph is
the reusable relationship substrate that impact analysis can traverse.

| Concept | Primary question | Role |
| --- | --- | --- |
| Dependency Knowledge Graph | What depends on what? | Relationship structure. |
| Change Impact Analysis | What may be affected by this change? | Change-scoped reasoning over relationships, history, and uncertainty. |

The graph does not classify blast radius by itself. It provides paths,
reverse relationships, dependency types, and uncertainty states that
Change Impact Analysis can use.

## Dependency Knowledge Graph vs Conventional Code Dependency Graph

A conventional code dependency graph usually models code-level
relationships such as imports, calls, packages, modules, and sometimes
runtime dependencies.

PCAE's Dependency Knowledge Graph is broader and more conservative:

- It includes source-code relationships, but also documentation, tests,
  contracts, evidence, advisory, historical, governance, lifecycle,
  release, capability, subsystem, and no-go relationships.
- It represents source attribution and uncertainty for every node and
  edge.
- It records stale, conflicting, unknown, and superseded dependency
  evidence.
- It is read-only and does not become build orchestration, runtime
  routing, execution planning, test scheduling, or refactoring logic.
- It supports governance-compatible context and evidence candidates, not
  allow/block decisions.

## Core Primitives

The clean primitive set is:

| Primitive | Meaning |
| --- | --- |
| Graph Node | A Repository Knowledge entity included in a graph view. |
| Graph Edge | A typed, directional relationship between two graph nodes. |
| Dependency Claim | A source-attributed assertion that a node, edge, or path exists or may exist. |
| Dependency Source | Repository artifact supporting a graph node, edge, claim, path, or view. |
| Dependency Evidence Link | Bridge between graph claims and Evidence that used, confirmed, contradicted, or was produced from them. |
| Dependency Type | Class of dependency such as code, command, documentation, test, contract, evidence, advisory, historical, governance, lifecycle, release, capability, subsystem, or no-go boundary. |
| Dependency Direction | Explicit source-to-target orientation of an edge. |
| Dependency Strength | Strength label such as required, optional, weak, inferred, possible, unknown, stale, conflicting, or superseded. |
| Dependency Scope | Boundary within which the claim applies: path, package, subsystem, command, phase, release, revision, source set, or query. |
| Dependency Verification State | Whether the claim is verified, unverified, inferred, possible, unknown, conflicting, stale, or superseded. |
| Dependency Path | Ordered chain of nodes and edges connecting one graph node to another. |
| Dependency View | Bounded projection of the graph for a query or audience. |
| Dependency Snapshot | Versioned graph state derived from a repository revision, source set, taxonomy, and graph builder version. |
| Dependency Query | Deterministic question over graph nodes, edges, paths, views, or snapshots. |
| Dependency Report | Inspectable non-decision artifact summarizing graph query results, sources, uncertainty, and limitations. |

Graph Node and Graph Edge are implementation-friendly names for
Repository Knowledge entities and relationships in graph views. They do
not create a separate authority model.

## Node Model

A graph node represents a Repository Knowledge entity that participates
in dependency relationships.

Initial node taxonomy:

| Node type | Examples |
| --- | --- |
| Source module | `src/pcae/core/...`, command module, script. |
| Package | Python package, CLI package, runtime package, test package. |
| Command or CLI surface | `pcae health`, `pcae check`, `pcae runtime inspect`, lifecycle command. |
| Runtime component | Runtime, registry, introspection, context, snapshot, plugin contract. |
| Repository Skill | Skill contract, manifest, evidence-producing skill, deterministic skill. |
| Advisory Skill | Advisory Repository Skill, Advisory Provider, Advisory Context Package. |
| Evidence artifact | Evidence item, evidence category, evidence provider, evidence candidate. |
| Decision evaluation input | Invariant input, explanation reference, evaluation context, transition metadata. |
| Architecture document | Runtime architecture, Repository State Kernel, Track B architecture documents. |
| Contract document | Evidence contract, Repository Skill contract, Advisory Context Package contract, no-go contract. |
| Verification document | Verification report, compatibility report, quality baseline. |
| Phase report | Canonical latest report, timestamped report, quarantined report. |
| Phase metadata | `.pcae/phase-completion-metadata.json`, architecture status. |
| Task contract | Active or done task contract. |
| Changelog entry | User-visible or workflow-visible change record. |
| Test file or suite | Test module, focused suite, full suite, fast-green suite. |
| Release record | Release notes, GitHub Release, release status. |
| Tag or commit | Git tag, commit hash, release commit, repair commit. |
| No-go boundary | Execution-readiness gate, runtime enforcement no-go item, autonomy invariant. |
| Subsystem | Repository State Kernel, Evidence Framework, Advisory Context Package. |
| Capability | Phase completion, report promotion, notification certification, runtime inspection. |
| Architectural contract | Frozen boundary, interface, invariant set, lifecycle contract. |

Node identity must be stable, deterministic, and source-derived. A graph
node is not valid because a model named it; it must be grounded in a
Dependency Source.

## Edge Model

A graph edge is a typed, directional relationship between two nodes.

Initial edge categories:

| Edge | Meaning |
| --- | --- |
| `imports` | Source module A imports source module B. |
| `calls` | Function, command, or module A calls B. |
| `owns` | Entity A owns or is authoritative for concern B. |
| `exposes` | Entity A exposes command, API, artifact, schema, or report B. |
| `consumes` | Entity A consumes output, evidence, context, or artifact B. |
| `produces` | Entity A produces evidence, report, metadata, artifact, or release B. |
| `verifies` | Test, report, or validation command A verifies entity B. |
| `documents` | Document A explains entity B. |
| `constrains` | Contract, no-go rule, invariant, or boundary A constrains B. |
| `depends_on` | Entity A requires entity B's behavior, contract, output, or existence. |
| `supersedes` | Entity A replaces, corrects, or deprecates entity B. |
| `introduced_by` | Entity A was introduced by phase, report, or commit B. |
| `modified_by` | Entity A was modified by phase, report, or commit B. |
| `hardened_by` | Entity A was hardened by phase, report, or commit B. |
| `repaired_by` | Entity A was repaired by phase, report, or commit B. |
| `released_in` | Entity A was included in release B. |
| `tests` | Test A tests entity B. |
| `references` | Entity A references entity B without necessarily depending on it. |
| `requires_evidence` | Decision, advisory, or governance surface A requires evidence B. |
| `informs_advisory` | Entity A can inform Advisory Context B. |
| `supports_decision_context` | Entity A can become structured context or evidence candidate for Decision Evaluation. |
| `belongs_to_subsystem` | Entity A belongs to subsystem B. |
| `implements_contract` | Entity A implements contract B. |
| `protected_by_no_go_boundary` | Entity A is protected or constrained by no-go boundary B. |

An edge without source attribution is a candidate edge, not a canonical
graph edge.

## Dependency Type Model

Dependency type classifies why an edge matters.

Initial dependency classes:

| Type | Meaning |
| --- | --- |
| Code dependency | Source-level import, call, module, package, or schema relationship. |
| Command dependency | CLI or command behavior depends on another component, artifact, or contract. |
| Documentation dependency | Document explains, constrains, or references an entity. |
| Test dependency | Test verifies, covers, or defends an entity or contract. |
| Contract dependency | Entity depends on or is constrained by a contract or invariant. |
| Evidence dependency | Entity produces, consumes, requires, or explains Evidence. |
| Advisory dependency | Advisory component consumes context, evidence, or graph knowledge. |
| Historical dependency | Entity is introduced, changed, hardened, repaired, superseded, or released by historical source. |
| Governance dependency | Entity depends on lifecycle, report-trust, no-go, transition, or push-state governance. |
| Lifecycle dependency | Entity participates in task, phase, report, promotion, notification, or handoff lifecycle. |
| Release dependency | Entity is included in, documented by, or constrained by release artifacts. |
| Capability dependency | Capability requires, exposes, or constrains another capability. |
| Subsystem dependency | Entity belongs to or depends on a subsystem boundary. |
| No-go boundary dependency | Entity is constrained or protected by a no-go boundary. |

Dependency type is orthogonal to edge type. For example, `documents` may
be a documentation dependency, release dependency, or historical
dependency depending on source and scope.

## Directionality Model

Every graph edge must be directional and inspectable.

Direction examples:

- Source module A `imports` source module B: A depends on B.
- Test X `verifies` component Y: X defends Y; Y has reverse test
  coverage from X.
- Document D `documents` subsystem S: D explains S; S has reverse
  documentation support from D.
- Phase P `introduced_by` capability C should instead be represented as
  capability C `introduced_by` phase P, so the subject points to its
  historical source.
- Contract K `constrains` command Q: K limits Q; Q has reverse
  constraint from K.
- Advisory Skill A `consumes` Repository Skill R evidence: A depends on
  R's evidence output.
- Evidence E `supports_decision_context` claim C: E may support C as
  context, but Decision Evaluation remains the verdict path.

Inverse relationships may be query projections rather than stored edges.
If both directions are stored, each direction must have its own meaning
and source attribution.

## Dependency Strength and Verification

Dependency strength and verification state prevent false certainty.

Strength labels:

| Strength | Meaning |
| --- | --- |
| `required` | Source shows the target is required for the source's behavior, contract, or validity. |
| `optional` | Dependency exists only for optional or conditional behavior. |
| `weak` | Relationship is relevant but not required. |
| `inferred` | Relationship is derived from structured rules and sources but not directly stated. |
| `possible` | Relationship may exist, but sources are partial. |
| `unknown` | PCAE cannot determine whether a dependency exists. |
| `conflicting` | Sources disagree about the dependency. |
| `stale` | Dependency depends on old or stale evidence. |
| `superseded` | Newer source replaces or corrects the dependency. |

Verification states:

- `verified`
- `unverified`
- `inferred`
- `possible`
- `unknown`
- `conflicting`
- `stale`
- `superseded`

Strength describes relationship importance. Verification state describes
source support. Neither authorizes action.

## Source Attribution Model

Every graph node, edge, claim, path, view, and snapshot must link back
to Dependency Sources.

Valid sources include:

- source files
- test files
- documentation files
- architecture documents
- contract documents
- verification documents
- phase reports
- phase-completion metadata
- changelog entries
- `tasks/DONE.md`
- `tasks/DECISIONS.md`
- task contracts
- release notes
- tags
- commits
- evidence artifacts
- Repository Skill records
- Advisory Repository Skill records
- generated registry output
- runtime-introspection output
- canonical lifecycle artifacts

A Dependency Source reference should record:

- source path or artifact ID
- source type
- optional heading, section, line, structured field, or object ID
- repository commit or snapshot revision
- source freshness
- canonical, historical, advisory, quarantined, superseded, or stale
  status
- extraction or derivation method
- limitations

No unattributed edge should be promoted into a canonical graph snapshot.

## Determinism Model

Future graph construction must be reproducible from:

1. repository revision
2. source set
3. Repository Knowledge version
4. Historical Memory snapshot, when temporal edges are included
5. relationship taxonomy version
6. graph builder version
7. graph view/query parameters

The same inputs must produce the same nodes, edges, dependency claims,
paths, uncertainty labels, source references, and graph views.

Model inference is not a deterministic source. A model may suggest
candidate dependencies, but a candidate is not canonical until grounded
in repository artifacts through structured rules and source attribution.

## Uncertainty Model

The graph must preserve uncertainty rather than erase it.

Uncertainty categories:

| Category | Meaning |
| --- | --- |
| `verified_dependency` | Sources directly support the node/edge/path. |
| `unverified_dependency` | Claim is present but lacks sufficient source support. |
| `weak_dependency` | Relationship is relevant but not required. |
| `possible_dependency` | Relationship may exist, but sources are partial or indirect. |
| `inferred_dependency` | Relationship follows from structured rules but is not directly stated. |
| `unknown_dependency` | PCAE cannot determine whether the relationship exists. |
| `conflicting_dependency_evidence` | Sources disagree and the conflict is preserved. |
| `stale_dependency_evidence` | Dependency depends on old source, old report, or stale metadata. |
| `superseded_dependency_evidence` | Newer source replaces, corrects, or deprecates the dependency. |

Unknown, stale, conflicting, and superseded dependencies must remain
inspectable. They should not be silently dropped or converted into
verified edges.

## Verification Model

Future phases can verify graph correctness through:

- fixture repositories with known nodes, edges, and dependency paths
- deterministic snapshot comparison
- source-attribution completeness checks
- no-unattributed-edge checks
- directionality checks
- relationship taxonomy conformance checks
- stale/superseded source handling checks
- conflict preservation checks
- reverse dependency query checks
- graph view boundary checks
- no-decision/no-execution/no-mutation boundary checks
- cross-checks against known test/document/contract mappings
- human review of sample dependency reports for explanation quality

Verification should prove determinism, source attribution, direction,
uncertainty preservation, and containment. It should not pretend to
prove that every possible bug or dependency has been discovered.

## Versioning and Snapshot Model

A Dependency Snapshot is a versioned graph state.

It should record:

- snapshot ID
- repository commit
- branch or tag context
- source set
- Repository Knowledge version
- Historical Memory snapshot ID, when used
- relationship taxonomy version
- graph builder version
- generated-at timestamp
- included node and edge counts
- query/view parameters, if it is a view snapshot
- known omissions and limitations
- superseded snapshot references

Snapshots should relate to:

- repository commits as deterministic input revisions
- releases as externally meaningful graph milestones
- phase-completion artifacts as governed lifecycle sources
- report metadata as structured phase/report evidence
- Historical Memory snapshots as temporal lineage inputs
- Repository Knowledge versions as the broader semantic map version

Graph snapshots are read-only records. They do not mutate Repository
State.

## Query Model

Future graph queries should be bounded and deterministic.

Query classes:

| Query class | Question |
| --- | --- |
| Dependency path query | Which paths connect node A to node B? |
| Reverse dependency query | What depends on node X? |
| Subsystem dependency query | Which nodes and edges belong to or cross subsystem S? |
| Command dependency query | Which entities does command C depend on or expose? |
| Test coverage relationship query | Which tests verify entity E? |
| Documentation relationship query | Which docs describe, constrain, or reference entity E? |
| Contract relationship query | Which contracts constrain or are implemented by entity E? |
| Historical lineage relationship query | Which phases, reports, commits, or releases introduced, modified, hardened, repaired, superseded, or released entity E? |
| Advisory relationship query | Which advisory components consume, inform, or depend on entity E? |
| Governance boundary query | Which lifecycle, no-go, report-trust, or transition boundaries constrain entity E? |
| Release relationship query | Which release records include or describe entity E? |
| Unknown dependency query | Which relationships are unknown, unverified, conflicting, stale, or superseded? |

Every query result must include source attribution, directionality,
uncertainty, limitations, and a non-decision disclaimer.

## Graph View Model

A graph view is a bounded projection of the graph for a purpose.

Initial graph views:

| View | Purpose |
| --- | --- |
| Subsystem view | Show entities and relationships inside or across a subsystem. |
| Capability view | Show what implements, documents, tests, constrains, and releases a capability. |
| Command view | Show command ownership, implementation, tests, docs, and governance boundaries. |
| Test view | Show what tests verify and which contracts they defend. |
| Documentation view | Show what docs describe, constrain, supersede, or leave unknown. |
| Contract view | Show implementers, constraints, tests, docs, and historical phases for a contract. |
| Evidence view | Show evidence producers, consumers, candidates, and decision-context links. |
| Historical view | Show temporal edges and lineage relationships. |
| Release view | Show release inclusion, tags, notes, and published commitments. |
| Advisory view | Show Advisory Context, advisory skills, evidence sources, and prompt-safe boundaries. |
| Governance view | Show lifecycle artifacts, no-go boundaries, Transition Validator relationships, and report-trust paths. |

Views are projections. They do not create new truth apart from the
underlying source-attributed graph claims.

## Dependency Path Model

A Dependency Path is an ordered sequence of nodes and edges connecting a
start node to an end node.

Each path should carry:

- start node
- end node
- ordered edges
- dependency types
- edge directions
- source references
- strength labels
- verification states
- stale/conflicting/superseded markers
- limitations

Paths are the main bridge to Change Impact Analysis: they explain how a
changed node may reach tests, docs, contracts, advisory surfaces,
historical phases, governance boundaries, or release records.

## Dependency Report Model

A future Dependency Report should contain:

1. report identity and schema version
2. repository revision and source set
3. query or view parameters
4. graph snapshot reference
5. nodes included
6. edges included
7. dependency paths
8. dependency types
9. directionality summary
10. source attribution
11. verified dependencies
12. weak, inferred, possible, unknown, stale, conflicting, and
    superseded dependencies
13. evidence candidates or evidence links
14. limitations
15. verification status
16. non-decision disclaimer

The report must state that it does not accept, reject, authorize,
execute, enforce, mutate repository state, or generate patches.

## Integration with Repository Knowledge

The Dependency Knowledge Graph is a relationship layer inside
Repository Knowledge. It should reuse Repository Knowledge entity
identity, relationship taxonomy, claim model, source model, evidence
links, snapshots, and versioning.

It should not create incompatible IDs, duplicate source attribution, or
become an independent memory database.

## Integration with Historical Memory

Historical Memory uses temporal graph edges and dependency paths to
answer lineage questions.

The graph should support:

- introduction lineage
- modification lineage
- verification lineage
- hardening lineage
- repair lineage
- supersession and correction lineage
- release lineage
- subsystem and capability lineage

Historical Memory adds time, event semantics, and append-aware
correction handling to the graph's structural edges.

## Integration with Change Impact Analysis

Change Impact Analysis can consume:

- dependency paths
- reverse edges
- edge types
- dependency types
- graph views
- verification states
- weak/possible/unknown/stale/conflicting/superseded markers
- source attribution
- limitations

The graph helps impact analysis identify likely affected entities and
unknowns. Impact analysis remains the change-scoped reasoning layer, and
neither the graph nor impact analysis makes decisions.

## Integration with Evidence

Graph claims can produce evidence candidates or evidence links.

Examples:

- "Test X verifies command Y."
- "Contract K constrains subsystem S."
- "Phase P introduced capability C."
- "No-go boundary N protects runtime capability R."

To influence Decision Evaluation, a graph claim must be converted into
conforming Evidence with source, category, producer, timestamp,
freshness, confidence, determinism, scope, references, observed value,
expected value, explanation, and limitations.

## Integration with Repository Skills

Future Repository Skills may expose graph inspection/query capabilities
as evidence-only skills. Such skills may:

- inspect graph snapshots
- answer bounded dependency queries
- emit evidence candidates or EvidenceCollections
- identify unknown, stale, or conflicting relationships
- summarize graph paths for Advisory Context

They must never decide, authorize, mutate, promote, notify, execute, or
bypass the Repository Transition Validator.

## Integration with Advisory

Advisory can use graph knowledge for richer explanations and
recommendations.

Graph knowledge can help Advisory Context Packages include:

- relevant entities
- dependency paths
- tests and docs
- contracts and no-go boundaries
- historical lineage
- evidence candidates
- unknowns and limitations

The Advisory Context Package still owns prompt safety, size limits,
provenance, redaction, trust-class separation, and untrusted
repository-content labeling. Advisory output remains evidence at most
and cannot authorize action.

## Integration with Decision Evaluation

The Dependency Knowledge Graph can support decisions only indirectly
through structured context or conforming Evidence.

Decision Evaluation remains the only component responsible for
allow/block/escalate/more-evidence decisions. The graph never emits
Accept, Reject, Quarantine, or Requires Human Review. It never promotes
artifacts, sends notifications, authorizes execution, or bypasses the
Repository Transition Validator.

## Read-Only and No-Execution Boundary

The Dependency Knowledge Graph is read-only.

Hard no-go conditions:

- no dependency graph construction in this phase
- no dependency graph database
- no dependency graph CLI
- no graph query engine
- no graph visualization
- no Repository Knowledge extraction
- no Historical Memory extraction
- no Change Impact Analysis engine
- no advisory behavior changes
- no Decision Evaluation changes
- no Evidence subsystem changes
- no Repository Skills changes
- no execution
- no shell mediation
- no Permission Broker changes
- no lifecycle redesign
- no REST
- no Dashboard
- no Web UI
- no Telegram inbound
- no provider selection
- no multi-model orchestration
- no autonomous coding
- no model capability expansion
- no repository mutation
- no runtime plugin changes
- no repository state changes
- no test execution through graph analysis
- no automatic patch generation
- no automatic refactoring

Execution capability remains unavailable. Maximum runtime capability
remains `observe`.

## Future Emergence Paths

### 118E - Advisory Reasoning Expansion Architecture

118E can define how Advisory consumes Repository Knowledge, Historical
Memory, Change Impact Analysis, and graph views as bounded,
provenance-preserving context without gaining authority.

### Future Repository Intelligence Reports

Dependency Reports can become one report family under Repository
Intelligence: structured, source-attributed, non-decision reports over
graph views and dependency paths.

### Future Architectural Contract Mapping

The graph provides the relationship substrate for mapping contracts to
implementers, tests, docs, no-go boundaries, lifecycle artifacts, and
historical phases.

### Future Safe Pre-Change Review

Pre-change review can use graph paths to identify likely affected
entities, required evidence, and unknowns before implementation begins,
without authorizing the change.

### Future Dependency Graph Prototype

A future prototype may construct a small deterministic graph from
bounded sources. That prototype must be preceded by a contract or scope
phase if needed and must preserve read-only, source-attributed,
non-decision behavior.

### Future Graph Verification

Graph verification should prove determinism, attribution,
directionality, view boundaries, uncertainty preservation, and
non-execution containment.

## Risks

- **False completeness.** A graph can look comprehensive even when
  sources are partial. Mitigation: unknowns, limitations, and source-set
  declarations.
- **Decision leakage.** Dependency paths may be mistaken for verdicts.
  Mitigation: non-decision disclaimers and Decision Evaluation boundary.
- **Runtime graph confusion.** A relationship graph may be mistaken for
  an orchestration graph. Mitigation: read-only and no-execution
  boundary.
- **Graph database premature commitment.** Implementers may jump to
  storage technology before freezing records. Mitigation: graph as a
  projection over Repository Knowledge claims and snapshots.
- **Model inference creep.** Model-suggested edges may be treated as
  truth. Mitigation: no canonical edge without source attribution.
- **Stale relationship propagation.** Old docs or metadata may keep
  obsolete edges alive. Mitigation: freshness, supersession, and
  Historical Memory correction semantics.

## Open Questions

- Which bounded source set should a first graph prototype use?
- Should graph snapshots be stored as Repository Knowledge snapshots,
  Repository Intelligence reports, or a separate read-only artifact
  type?
- Which edge categories should be frozen first for a contract phase?
- How should generated files, external dependencies, and package-manager
  metadata be represented when they enter scope?
- What minimal fixture repository can prove directionality,
  attribution, uncertainty, and supersession behavior?
- Should dependency strength be a graph claim field, a relationship
  annotation, or both?

## Recommended Next Phase

118E - Advisory Reasoning Expansion Architecture.

118E should remain architecture-only unless explicitly activated
otherwise. It should define how Advisory consumes Repository Knowledge,
Historical Memory, Change Impact Analysis, and Dependency Knowledge
Graph views as bounded, source-attributed, prompt-safe context while
remaining evidence-producing, non-authorizing, non-mutating, and
non-executing.
