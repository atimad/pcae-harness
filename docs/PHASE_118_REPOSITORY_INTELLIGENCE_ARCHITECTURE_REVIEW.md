# Phase 118R - Repository Intelligence Architecture Review

## Purpose

Phase 118R reviews the Track B Repository Intelligence architecture set
defined by Phases 118A through 118E.

This phase asks whether those five architecture documents form one
coherent Repository Intelligence architecture and whether the set is
ready for a future contract-freeze phase. It is review only. It adds no
new architecture subsystem, no contract freeze, no prototype, no
extraction, no graph construction, no advisory behavior change, no
runtime behavior change, no lifecycle redesign, and no execution path.

## Track B Review Context

Track B asks whether PCAE can understand the repository itself without
granting new authority.

The reviewed architecture set establishes:

- Repository Knowledge as the foundational semantic map.
- Historical Memory as the temporal layer inside Repository Knowledge.
- Dependency Knowledge Graph as the relationship layer inside
  Repository Knowledge.
- Change Impact Analysis as read-only, change-scoped reasoning over
  Repository Knowledge, Historical Memory, and dependency
  relationships.
- Advisory Reasoning Expansion as a non-authoritative consumer of
  Repository Intelligence context.

The review checks coherence against the frozen v0.2 authority model:
Repository State owns current governed condition, Evidence is
evaluation-scoped observed fact, Repository Skills produce Evidence
only, Advisory remains non-authoritative, Decision Evaluation and the
Repository Transition Validator remain the only decision path, and
execution remains unavailable.

## Reviewed Documents

Primary Track B documents:

1. `docs/PHASE_118_REPOSITORY_KNOWLEDGE_ARCHITECTURE.md`
2. `docs/PHASE_118_HISTORICAL_MEMORY_ARCHITECTURE.md`
3. `docs/PHASE_118_CHANGE_IMPACT_ANALYSIS_ARCHITECTURE.md`
4. `docs/PHASE_118_DEPENDENCY_KNOWLEDGE_GRAPH_ARCHITECTURE.md`
5. `docs/PHASE_118_ADVISORY_REASONING_EXPANSION_ARCHITECTURE.md`

Supporting PCAE architecture documents inspected:

- `docs/PCAE_REPOSITORY_STATE_KERNEL.md`
- `docs/PCAE_REPOSITORY_EVIDENCE_FRAMEWORK.md`
- `docs/PCAE_DECISION_FRAMEWORK.md`
- `docs/PCAE_REPOSITORY_SKILLS_ARCHITECTURE.md`
- `docs/PCAE_ADVISORY_REPOSITORY_SKILLS_ARCHITECTURE.md`
- `docs/PCAE_ADVISORY_CONTEXT_PACKAGE_CONTRACT.md`
- `docs/PCAE_ADVISORY_RUNTIME_CONTRACT.md`
- `docs/PCAE_RUNTIME_CONTEXT_ARCHITECTURE.md`
- `docs/PHASE_111_RUNTIME_INTROSPECTION_ARCHITECTURE.md`
- `docs/PHASE_92_PHASE_REPORT_ARTIFACT_MODEL.md`
- `docs/PCAE_REPOSITORY_TRANSITION_VALIDATOR.md`
- `docs/RELEASE_NOTES_V0_2_0.md`
- `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md`
- `PROJECT_STATUS.md`
- `CHANGELOG.md`
- `tasks/DONE.md`
- `docs/ROADMAP.md`

## Executive Conclusion

The Track B architecture set is **coherent and ready for contract
freeze with minor clarifications**.

No contradiction was found that requires a repair phase before contract
freeze. The five documents consistently preserve Repository Knowledge
as the foundation, keep Historical Memory and Dependency Knowledge
Graph inside Repository Knowledge, position Change Impact Analysis as
read-only context rather than verdict logic, and position Advisory
Reasoning Expansion as a non-authoritative consumer.

The architecture is not yet ready for implementation. It is ready for a
contract-freeze phase that narrows terminology, freezes shared record
shapes, resolves minor overlaps, and defines the first contract
boundary for Repository Intelligence as a whole.

Recommended next phase: **119A - Repository Intelligence Contract
Freeze**.

## Architecture Stack Summary

| Layer | Role | Authority |
| --- | --- | --- |
| Repository State | Current governed repository condition: git, task, phase, report, push, runtime, notification, and lifecycle facts. | Repository State Kernel / Transition Validator. |
| Repository Knowledge | Foundational deterministic architectural understanding layer. | Read-only semantic map. |
| Historical Memory | Temporal layer explaining how architecture, decisions, repairs, releases, and constraints evolved. | Read-only lineage inside Repository Knowledge. |
| Dependency Knowledge Graph | Relationship layer representing nodes, edges, dependency claims, paths, views, snapshots, and uncertainty. | Read-only graph projection inside Repository Knowledge. |
| Change Impact Analysis | Change-scoped reasoning over knowledge, history, and dependency relationships. | Structured context only. |
| Advisory Reasoning Expansion | Non-authoritative consumer of Repository Intelligence context. | Explanation, recommendation, uncertainty, and handoff only. |
| Evidence | Evaluation-scoped observed fact support. | Evidence Framework; not a kernel primitive. |
| Repository Skills | Governed evidence-producing capabilities. | Evidence only; no verdicts. |
| Decision Evaluation | Centralized invariant evaluation over Evidence. | Only decision-making layer with Transition Validator. |

## Confirmed Architecture Decisions

- Repository Intelligence is read-only architecture understanding, not
  autonomy, execution, enforcement, lifecycle mutation, or provider
  orchestration.
- Repository Knowledge is the foundation for Track B.
- Repository Knowledge is not Repository State and not a fifth
  Repository State Kernel primitive.
- Repository Knowledge claims must be deterministic where possible,
  source-attributed, inspectable, and repository-derived.
- Historical Memory is a temporal profile/view inside Repository
  Knowledge, not generic AI memory, model memory, or conversation
  memory.
- Dependency Knowledge Graph is the relationship layer inside
  Repository Knowledge, not a runtime orchestration graph or graph
  database requirement.
- Change Impact Analysis is read-only, change-scoped reasoning over
  Repository Knowledge, Historical Memory, and dependency
  relationships.
- Blast radius, impact claims, graph paths, and historical lineage are
  context, not decisions.
- Advisory Reasoning Expansion consumes Repository Intelligence context
  without gaining authority.
- Evidence candidates from Repository Intelligence must be converted
  into conforming Evidence before Decision Evaluation can use them.
- Repository Skills remain evidence producers only.
- Advisory remains non-authoritative and may not authorize, execute,
  mutate, promote, notify, commit, push, or bypass validation.
- Decision Evaluation and the Repository Transition Validator remain the
  only allow/block/quarantine/requires-human-review path.
- Execution remains unavailable and maximum runtime capability remains
  `observe`.

## Boundary Review

### Repository Knowledge and Repository State

The boundary is clear. Repository State answers what exists now and is
authoritative for lifecycle condition. Repository Knowledge answers what
repository architecture means. 118A explicitly says Repository
Knowledge may cite state-derived facts but may not determine whether a
transition is acceptable.

No contradiction found.

### Repository Knowledge and Evidence

The boundary is clear but requires contract-freeze precision.
Repository Knowledge is reusable semantic context. Evidence is
evaluation-scoped observed fact. All Track B documents consistently
state that knowledge, history, impact, graph, or advisory claims may
produce evidence candidates but are not automatically Evidence.

Required clarification: the contract freeze should name the exact bridge
shape from `Knowledge Evidence Link` or layer-specific evidence links to
conforming Evidence references.

### Repository Knowledge and Repository Skills

The boundary is clear. Repository Skills may inspect or expose
Repository Intelligence context in future phases, but they remain
Evidence producers and never own Repository Knowledge authority merely
because they can consume it.

No contradiction found.

### Repository Knowledge and Advisory Context

The boundary is clear. Repository Knowledge is structured data.
Advisory Context Packages are bounded, prompt-safe, provenance-
preserving packages for advisory use. 118A and 118E both preserve
redaction, trust-class separation, budget, provenance, and untrusted
repository-content labelling.

Required clarification: the contract freeze should decide whether
Repository Intelligence context enters Advisory Context Packages as new
sections, typed context items, or artifact references inside existing
sections.

### Historical Memory and Repository Knowledge

The boundary is coherent. Historical Memory specializes 118A primitives
for time and lineage: subjects, events, claims, sources, lineages,
evidence links, snapshots, and query results. It remains inside
Repository Knowledge and does not become a separate memory database.

No contradiction found.

### Dependency Knowledge Graph and Repository Knowledge

The boundary is coherent with one minor overlap. 118D clearly makes
Graph Node and Graph Edge graph-view aliases/specializations of
Knowledge Entity and Knowledge Relationship. This avoids a separate
authority model.

Required clarification: contract freeze should decide whether the
canonical contract names remain `Knowledge Entity` / `Knowledge
Relationship` with graph aliases, or whether graph-facing APIs expose
`Graph Node` / `Graph Edge` as public terms.

### Change Impact Analysis and Dependency Knowledge Graph

The boundary is clear. Dependency Knowledge Graph answers relationship
questions. Change Impact Analysis applies relationships, history, and
uncertainty to a proposed or observed change. 118D explicitly says the
graph does not classify blast radius by itself.

No contradiction found.

### Change Impact Analysis and Decision Evaluation

The boundary is clear. Change Impact Analysis identifies impact
surfaces, claims, paths, unknowns, and evidence gaps. It never accepts,
rejects, quarantines, requests human review as a verdict, authorizes
execution, enforces policy, or bypasses the Repository Transition
Validator.

No contradiction found.

### Advisory and Decision Evaluation

The boundary is clear and repeated consistently. Advisory explains,
recommends, preserves uncertainty, identifies evidence gaps, and may
package handoff context. Decision Evaluation remains the only decision
maker.

No contradiction found.

### Advisory and Model Inference

The boundary is clear. 118E aligns with the Evidence Framework and
Advisory Repository Skills architecture: model-produced content remains
probabilistic/advisory by default and never sole authority for Accept.
Hidden model state, prompt wording, conversation memory, and model
confidence are not canonical sources of truth.

No contradiction found.

### Advisory and Autonomous Planning

The boundary is clear. 118E allows recommendations for review or
evidence collection but forbids authoritative executable plans, patch
plans, refactoring plans, shell-command plans, commit/push plans, and
lifecycle-transition plans.

No contradiction found.

### Repository Intelligence and Execution

The boundary is consistent across all five documents. Repository
Intelligence is read-only. Execution remains unavailable. No Track B
document grants shell mediation, Permission Broker authority, runtime
execution, Telegram inbound, or repository mutation.

No contradiction found.

## Terminology Review

| Term | Review result |
| --- | --- |
| Knowledge | Consistently means source-attributed architectural understanding. |
| Memory | Consistently means historical/temporal repository lineage, not model or conversation memory. |
| Impact | Consistently means change-scoped possible effect context, not prediction or decision. |
| Dependency | Consistently means typed relationship, broader than code dependency. |
| Graph | Consistently means relationship projection/view, not database or orchestrator. |
| Node / Edge | Correctly introduced as graph-facing aliases/specializations of knowledge entity/relationship. Freeze should decide canonical API naming. |
| Claim | Consistently source-attributed assertion in each layer. |
| Source | Consistently repository artifact, path, section, report, task, commit, tag, evidence artifact, skill artifact, or lifecycle artifact. |
| Evidence Link | Consistently a bridge to Evidence used, produced, confirmed, contradicted, or required. Freeze should define one common bridge shape. |
| Lineage | Consistently historical ordered chain of subjects/events. |
| Snapshot | Consistently versioned reproducible view tied to repository revision/source set/tool version. |
| Query | Consistently deterministic question over records/views. |
| Report | Consistently inspectable non-decision artifact. |
| Uncertainty | Consistently preserved and explicitly labelled. |
| Conflict | Consistently represented, not silently resolved. |
| Stale | Consistently preserved and freshness-sensitive. |
| Superseded | Consistently retained as history while replaced by later source-attributed context. |
| Recommendation | Consistently advisory-only suggestion, not authorization. |
| Decision | Consistently reserved for Decision Evaluation / Transition Validator verdicts. |

Terminology is coherent. The main freeze-time cleanup is to identify
which terms are canonical record names and which are view-specific
aliases.

## Primitive Compatibility Review

### Shared primitives

The five documents share the same base pattern:

- entity/subject/node/item
- relationship/edge/path
- claim
- source
- evidence link
- snapshot
- query
- report
- uncertainty or verification state

### Specialized primitives

- Historical Memory specializes entities into Historical Subjects,
  events, and lineages.
- Change Impact Analysis specializes entities into Impact Subjects,
  Impact Entities, Impact Surfaces, Impact Paths, Blast Radius, and
  Impact Reports.
- Dependency Knowledge Graph specializes entities and relationships
  into Graph Nodes, Graph Edges, Dependency Claims, Dependency Paths,
  Dependency Views, and Dependency Snapshots.
- Advisory Reasoning Expansion specializes context consumption into
  Advisory Claims, Recommendations, Reasoning Traces, References,
  Handoffs, and Advisory Reports.

### Overlapping primitives

The overlaps are intentional but should be unified during contract
freeze:

- Claim variants should share a common source/confidence/freshness/
  limitation shape.
- Source variants should share a common source reference schema.
- Evidence Link variants should share a common bridge model.
- Snapshot variants should share revision/source-set/tool-version
  fields.
- Query and Report variants should share non-decision disclaimers and
  provenance fields.

### Terms that should remain separate

- Repository State and Repository Knowledge.
- Evidence and Evidence Link.
- Historical Event and Dependency Edge.
- Impact Claim and Decision.
- Advisory Recommendation and Decision Evaluation verdict.

## Source Attribution Review

Source attribution is consistent across Track B. Each layer requires
claims to link to repository artifacts such as source files, tests,
docs, architecture documents, contract documents, verification docs,
phase reports, phase-completion metadata, changelog entries, task
records, release notes, tags, commits, evidence artifacts, skills, and
canonical lifecycle artifacts.

No layer permits canonical truth to be based only on hidden model state
or generated prose.

Required clarification: define one common `Source Reference` contract
with path or artifact ID, source type, optional section/field/line,
revision, freshness, trust class, and limitations.

## Determinism Review

Determinism is consistent. Repository Knowledge, Historical Memory,
Change Impact Analysis, and Dependency Knowledge Graph must be derived
from repository artifacts and structured rules rather than hidden model
inference. Advisory may consume model-produced advisory output only as
advisory/probabilistic context or Evidence under existing boundaries.

No contradiction found.

Required clarification: contract freeze should distinguish deterministic
record construction from deterministic query rendering and from
reproducible-external analysis tools.

## Uncertainty and Conflict Review

The documents consistently preserve:

- known
- unknown
- unverified
- weak
- possible
- inferred
- stale
- conflicting
- superseded

Historical Memory emphasizes correction and supersession. Dependency
Knowledge Graph emphasizes weak/inferred/possible/stale/conflicting
edges. Change Impact Analysis emphasizes unknown/unverified impact and
blast-radius uncertainty. Advisory Reasoning Expansion adds
advisory-only and decision-required states. These are compatible.

Required clarification: a future contract should define a shared
verification/uncertainty enum or mapping table so each layer can expose
specialized terms without drifting.

## Verification Review

Verification is consistently future-facing and read-only. The documents
describe source checks, source attribution inspection, snapshot
reproduction, query/report consistency, lineage validation, graph edge
validation, impact path verification, and advisory trace inspection.

No document requires implementation test suites for this architecture
review. No document suggests test execution through Repository
Intelligence.

Required clarification: contract freeze should define the first
minimal verification target: likely schema validation plus deterministic
source-reference resolution, not extraction correctness.

## Versioning and Snapshot Review

Versioning is aligned across Track B:

- Repository Knowledge snapshots derive from repository revision,
  source set, and extractor/version information.
- Historical Memory snapshots add temporal lineage over repository
  revision and extractor version.
- Impact views reference repository revision, knowledge snapshot,
  historical snapshot, and analyzer version.
- Dependency snapshots reference repository revision, source set,
  relationship taxonomy, and graph builder version.
- Advisory references should cite context package identity, source
  revisions, evidence references, and Repository Intelligence snapshots
  when available.

Required clarification: contract freeze should define common snapshot
identity fields and how snapshots relate to commits, releases, phase
completion artifacts, and canonical phase reports.

## Integration Review

The integration path is coherent:

1. Repository State remains the live governed condition.
2. Repository Knowledge describes architecture from repository sources.
3. Historical Memory and Dependency Knowledge Graph are views/layers
   inside Repository Knowledge.
4. Change Impact Analysis reasons over Repository Knowledge, Historical
   Memory, and dependency relationships for a scoped change.
5. Repository Skills may expose or produce evidence about Repository
   Intelligence without deciding.
6. Evidence remains the evaluation-scoped form Decision Evaluation can
   consume.
7. Advisory consumes bounded Repository Intelligence context for
   explanation, recommendation, uncertainty, and handoff.
8. Decision Evaluation and the Repository Transition Validator remain
   the verdict path.

No hidden decision-making integration was found.

## No-Go Boundary Review

All five Track B documents preserve:

- no execution
- no enforcement
- no authorization
- no shell mediation
- no Permission Broker change
- no lifecycle redesign
- no repository mutation
- no model authority
- no Telegram inbound
- no autonomous coding
- no automatic patch generation
- no automatic refactoring

The no-go boundary is consistent with v0.2 release notes, runtime
context/introspection posture, and execution-readiness no-go gates.

## Gaps, Overlaps, and Contradictions

### Gaps

- No shared source-reference schema is frozen yet.
- No shared claim base schema is frozen yet.
- No shared evidence-link bridge shape is frozen yet.
- No shared snapshot identity schema is frozen yet.
- No first Repository Intelligence contract boundary is selected yet.
- Advisory Context Package expansion shape for Repository Intelligence
  context is not yet frozen.

### Overlaps

- Knowledge Entity / Graph Node and Knowledge Relationship / Graph Edge
  overlap intentionally; freeze should define canonical names and alias
  behavior.
- Impact Relationship and Dependency Edge may describe the same
  underlying relationship in different query contexts; freeze should
  define when an impact relationship is a view over a dependency edge.
- Claim/source/evidence-link/snapshot/query/report primitives recur in
  every layer; freeze should define common base fields.

### Contradictions

No blocking contradictions were found. The documents repeat some
boundaries in different language, but the authority model is consistent:
Repository Intelligence produces context; Evidence carries evaluation
facts; Decision Evaluation decides; execution remains unavailable.

## Contract-Freeze Readiness Assessment

Outcome: **ready for contract freeze with minor clarifications**.

The architecture set is coherent enough for a 119A contract-freeze
phase. A repair phase is not required. A terminology-alignment-only
phase is also not required if 119A explicitly includes terminology and
primitive unification.

The next phase should not freeze only Repository Knowledge in isolation.
Because all later layers specialize the same base primitives, freezing
Repository Intelligence as a coherent contract is preferable. The
contract can still begin with Repository Knowledge primitives and then
define specialized profiles for history, graph, impact, and advisory
references.

## Risks

- Freezing graph-specific terms too early could make Graph Node/Edge
  look like a separate authority model rather than a Repository
  Knowledge view.
- Evidence candidates could be confused with conforming Evidence unless
  the bridge contract is explicit.
- Advisory Context Package expansion could accidentally allow unbounded
  repository dumps unless trust-class and size boundaries are carried
  forward.
- Change Impact Analysis could be mistaken for pre-change approval if
  impact reports do not carry non-decision disclaimers.
- Historical Memory could drift toward model/conversation memory if
  source attribution is weakened.
- Snapshot identity could drift across layers if repository revision,
  source set, and tool/version fields are not shared.
- Contract freeze could overreach into implementation details if it
  tries to specify storage, graph databases, CLIs, or extraction logic.

## Required Clarifications

Before or during contract freeze, clarify:

1. The canonical shared base primitives for claim, source, evidence
   link, snapshot, query, and report.
2. Whether Graph Node/Edge are public contract names or graph-view
   aliases for Knowledge Entity/Relationship.
3. The source-reference schema and minimum required fields.
4. The evidence-link bridge from Repository Intelligence context to
   conforming Evidence.
5. The shared uncertainty/verification vocabulary and layer-specific
   mappings.
6. Snapshot identity fields and relationship to commits, phase reports,
   releases, and extractor/analyzer versions.
7. The boundary between dependency edges and impact relationships.
8. How Repository Intelligence context should enter Advisory Context
   Packages without changing current Advisory behavior.
9. The first verification target for contract conformance.
10. The explicit non-decision disclaimer required on future knowledge,
    history, graph, impact, and advisory reports.

## Recommended Next Phase

119A - Repository Intelligence Contract Freeze

Rationale: 118A through 118E define a coherent architecture stack with
minor clarifications suitable for contract freeze. The next phase should
freeze shared Repository Intelligence primitives, source attribution,
evidence links, uncertainty/verification states, snapshot identity,
non-decision report boundaries, and profile relationships for
Repository Knowledge, Historical Memory, Dependency Knowledge Graph,
Change Impact Analysis, and Advisory Reasoning Expansion.

## Non-Goals Confirmed

This phase did not implement:

- repository intelligence contracts
- repository knowledge extraction
- historical memory extraction
- change impact analysis engine
- dependency graph construction
- graph query engine
- advisory behavior changes
- advisory runtime changes
- advisory context package changes
- evidence subsystem changes
- repository skills changes
- decision evaluation changes
- runtime behavior changes
- execution
- shell mediation
- Permission Broker changes
- lifecycle redesign
- REST
- Dashboard
- Web UI
- Telegram inbound
- provider selection
- multi-model orchestration
- autonomous coding
- model capability expansion
- repository mutation
- runtime plugin changes
- repository state changes
- test execution through repository intelligence
- automatic patch generation
- automatic refactoring

Execution capability remains unavailable. Runtime state remains
`Observed`. Maximum runtime capability remains `observe`.
