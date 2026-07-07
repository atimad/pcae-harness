# Phase 118A - Repository Knowledge Architecture

## Purpose

Phase 118A begins Track B: Repository Intelligence.

Track A answered whether PCAE can trust what the repository says about
its governed state. Track B asks whether PCAE can understand the
repository's software architecture through deterministic, source-
attributed repository knowledge.

This phase is architecture only. It defines Repository Knowledge as a
new read-only understanding layer that can describe architectural
entities, relationships, contracts, tests, documentation, historical
phases, reports, and capability mappings without becoming a decision
maker, execution mechanism, enforcement layer, or second Repository
State Kernel.

No Repository Knowledge implementation is added by this phase.

## Track B Context

PCAE v0.2.0 is released. The v0.2 architecture is frozen around ten
subsystems:

- Repository State Kernel
- Repository Transition Validator
- Canonical Artifact Promotion
- Notification Policy
- Repository Events
- Evidence Framework
- Decision Evaluation
- Repository Skills
- Advisory Provider Framework
- Advisory Context Package

Those subsystems establish how PCAE observes, validates, explains,
promotes, reports, and notifies about governed repository state. They do
not yet give PCAE a structured semantic map of the repository's own
software architecture.

Repository Intelligence is the next architectural chapter. It strengthens
deterministic repository understanding before any future authority is
granted. It is not autonomy, execution, provider orchestration, larger
context, or more capable models.

## Relationship to the v0.2 Repository State Kernel

The Repository State Kernel remains unchanged. Its four primitives are:

| Kernel primitive | Question answered |
| --- | --- |
| Repository State | What exists right now? |
| Repository Transition | What change is proposed? |
| Repository Artifact | What durable evidence or state was recorded? |
| Repository Event | What certified outcome was announced? |

Repository Knowledge is not a fifth kernel primitive. It is a read-only
semantic understanding layer above repository artifacts and repository
content. It can describe the architecture those artifacts document, but
it does not validate transitions, promote artifacts, emit events, or
change kernel state.

The Repository State Kernel owns lifecycle truth. Repository Knowledge
owns architectural description.

## Definition of Repository Knowledge

**Repository Knowledge** is the deterministic, inspectable,
source-attributed representation of what PCAE can know about the
repository's architecture and its relationships.

It answers questions such as:

- What architectural entities exist?
- Which files, tests, documents, reports, and phases describe them?
- Which contracts define their boundaries?
- Which capabilities depend on them?
- Which historical phases introduced or changed them?
- Which evidence items or future evidence candidates reference them?
- Which relationships imply change impact, dependency, ownership, or
  advisory context?

Repository Knowledge is derived from repository sources. A knowledge
item is not valid merely because a model inferred it. It must point back
to source material such as code paths, tests, docs, task records, phase
reports, changelog entries, repository skills, advisory skills, evidence
artifacts, or release records.

## Repository Knowledge vs Repository State

Repository State describes current governed condition. Repository
Knowledge describes architectural meaning.

| Concept | Primary question | Authority |
| --- | --- | --- |
| Repository State | Is the repository clean, healthy, valid, pushed, and lifecycle-consistent right now? | Repository State Kernel / Transition Validator |
| Repository Knowledge | What does the repository contain architecturally, and how are its parts related? | Read-only knowledge derivation |

Repository State can say that `PROJECT_STATUS.md` is present and the
working tree is clean. Repository Knowledge can say that
`PROJECT_STATUS.md` is a lifecycle memory artifact, that it is related
to phase reports, that it informs task bootstrap, and that changes to
its current-phase section affect lifecycle consistency checks.

Repository Knowledge must not duplicate Repository State authority. It
may reference state-derived facts as sources, but it may not determine
whether a transition is acceptable.

## Repository Knowledge vs Evidence

Evidence is evaluation-scoped. Repository Knowledge is a reusable
semantic map.

| Concept | Lifetime | Role |
| --- | --- | --- |
| Evidence | One evaluation unless persisted in an artifact | Supports governance, advisory, validation, or reporting decisions |
| Repository Knowledge | Versioned repository-derived knowledge snapshot or catalog | Describes architectural entities and relationships |

Repository Knowledge can produce evidence candidates. For example, a
future knowledge extractor may identify that `PCAE_REPOSITORY_STATE_KERNEL.md`
documents the Repository State Kernel and that several tests defend its
invariants. During a transition evaluation, that knowledge may become
Evidence: "this change touches a file linked to a frozen kernel
contract."

The conversion from knowledge to Evidence must preserve Evidence's
contract: category, producer, timestamp, freshness, confidence,
determinism, scope, references, observed value, limitations, and
explanation. Repository Knowledge does not bypass that contract.

## Repository Knowledge vs Advisory Context

Advisory Context Packages are bounded prompt-safe packages assembled for
specific advisory questions. Repository Knowledge is the structured
repository understanding that may later feed such packages.

Repository Knowledge may help select the relevant entities,
relationships, docs, tests, reports, and historical phases for an
Advisory Context Package. The package still owns prompt safety:
bounded size, provenance, redaction, trust-class separation, and
untrusted repository-content labelling.

Repository Knowledge is not a prompt. It is not model-readable context
by default. It is structured data that an advisory package assembler may
summarize deterministically.

## Repository Knowledge vs Repository Skills

Repository Skills produce Evidence. Repository Knowledge describes the
repository architecture those skills may inspect.

A future Repository Knowledge Skill may exist, but it would still be a
Repository Skill: it would observe repository sources, emit Evidence or
knowledge-derived Evidence, and never decide. Repository Skills do not
own Repository Knowledge authority merely because they can consume it.

Repository Knowledge may also define skill-related entities:

- Repository Skill contracts
- Advisory Repository Skill contracts
- skill manifests
- evidence categories a skill can produce
- source files implementing a skill
- tests defending a skill boundary

Those mappings support inspection and advisory reasoning. They do not
grant skills new power.

## Core Primitives

Repository Knowledge should be represented as a layered record model.
The clean primitive set is:

| Primitive | Meaning |
| --- | --- |
| Knowledge Entity | A thing the repository architecture can name: subsystem, component, capability, contract, test, document, phase, report, skill, artifact, or ownership marker. |
| Knowledge Relationship | A typed, directional relationship between entities, such as `documents`, `tests`, `depends_on`, `implements`, `introduced_by`, `changed_by`, `constrains`, or `supports_advisory_context`. |
| Knowledge Claim | A source-attributed assertion about an entity or relationship. Claims carry confidence, determinism, freshness, and limitations. |
| Knowledge Source | The repository artifact, path, section, commit, report, task record, release record, evidence item, or generated registry output from which a claim was derived. |
| Knowledge Evidence Link | A bridge from a knowledge claim to Evidence that used, confirmed, contradicted, or was produced from it. |
| Knowledge Snapshot | A versioned, reproducible set of entities, relationships, claims, sources, and evidence links derived from a specific repository revision and extractor version. |

The suggested terms "Knowledge Node" and "Knowledge Edge" are useful
implementation vocabulary, but they should be aliases for Knowledge
Entity and Knowledge Relationship rather than separate conceptual
primitives. The suggested entity types belong inside Knowledge Entity
taxonomy, not as separate top-level primitives.

## Entity Taxonomy

The initial entity taxonomy should include:

| Entity type | Examples |
| --- | --- |
| Architectural Entity | Repository State Kernel, Decision Evaluation, Advisory Context Package |
| Capability Entity | canonical report promotion, notification certification, task finish validation |
| Contract Entity | frozen subsystem contract documents, no-go boundary documents |
| Implementation Entity | source module, command module, CLI entry point, script |
| Test Entity | test file, test class, focused test case, validation command |
| Documentation Entity | architecture doc, roadmap doc, release notes, whitepaper section |
| Phase Entity | 113S, 115B, 116F, 117E.1, 118A |
| Report Entity | phase report, phase-completion metadata, canonical latest report |
| Skill Entity | Repository Skill, Advisory Repository Skill, skill manifest |
| Evidence Entity | Evidence provider, evidence category, evidence artifact, evidence candidate |
| Ownership Marker | subsystem owner, authority boundary, lifecycle owner, canonical source of truth |

Entity identity must be stable and source-derived. A future extractor may
assign IDs such as `arch.repository_state_kernel`, `doc.PCAE_REPOSITORY_STATE_KERNEL`,
or `phase.116F`, but IDs must be deterministic and never depend on file
traversal order or model phrasing.

## Relationship Taxonomy

The initial relationship taxonomy should include:

| Relationship | Meaning |
| --- | --- |
| `documents` | A document explains an entity or capability. |
| `implements` | A source artifact implements a documented entity or capability. |
| `tests` | A test artifact defends or verifies an entity, contract, invariant, or capability. |
| `depends_on` | One entity requires another entity's contract or output. |
| `constrains` | A contract, no-go rule, or invariant limits an entity's allowed behavior. |
| `introduced_by` | A phase first introduced an entity or relationship. |
| `changed_by` | A phase changed, froze, repaired, or verified an entity or relationship. |
| `promotes_to` | A lifecycle artifact can move into another artifact state. |
| `produces_evidence_for` | An entity can produce Evidence for a category or evaluation. |
| `supports_advisory_context` | A knowledge item can be summarized into bounded advisory context. |
| `has_impact_on` | A change to one entity may affect another. |

Relationships are typed and directional. If the inverse matters, it is a
query projection, not necessarily a second stored relationship.

## Knowledge Graph Model

Repository Knowledge should eventually resemble a layered knowledge
graph, but the architecture should not force the first implementation to
be a graph database.

The model has four layers:

1. **Source layer**: paths, sections, commits, reports, task records,
   changelog entries, release records, skill records, and evidence
   artifacts.
2. **Claim layer**: deterministic claims extracted from sources.
3. **Entity/relationship layer**: normalized entities and typed
   relationships built from claims.
4. **View layer**: graph views, catalogs, indexes, impact reports,
   dependency maps, historical timelines, and advisory context
   selections.

The storage form may begin as a registry or catalog. Graph behavior
should be a projection over stable records. This avoids prematurely
coupling Track B to a graph database while preserving the ability to ask
graph-shaped questions later.

## Source Attribution Model

Every knowledge claim must cite at least one Knowledge Source. A source
reference should carry:

- path or artifact identifier
- optional section heading or line-range concept
- commit or repository revision when available
- source type
- extractor that read it
- extraction timestamp
- source trust class
- limitations

Accepted source types include:

- source files
- tests
- docs
- phase reports
- `.pcae/phase-completion-metadata.json`
- changelog entries
- task records
- repository skills and advisory skills
- evidence artifacts
- release records
- generated governance registry outputs

Unattributed claims are invalid. Model-generated summaries are not
sources unless they are explicitly stored as probabilistic advisory
Evidence and labelled accordingly.

## Determinism Model

Repository Knowledge must be derived by deterministic repository
inspection. Acceptable extraction methods include:

- parsing structured files such as JSON, TOML, and Markdown headings
- reading known governance artifacts
- inspecting git history and commit metadata
- matching exact document references and canonical file paths
- parsing import relationships or source-level symbols with deterministic
  tools
- reading test names, test file paths, and validation command records
- reading phase reports and task records

The same repository revision, extractor version, configuration, and
input set must produce the same Knowledge Snapshot.

Probabilistic model inference may suggest candidate knowledge for human
review, but candidate knowledge is not accepted into Repository
Knowledge until a deterministic source path and extractor rule can
reproduce it or it is explicitly stored as low-confidence advisory
Evidence outside the deterministic knowledge base.

## Production Model

Repository Knowledge is produced in stages:

1. Source discovery enumerates allowed repository sources.
2. Extractors produce source-attributed claims.
3. Normalization resolves claims into stable entity IDs and relationship
   IDs.
4. Conflict detection preserves contradictory claims rather than choosing
   silently.
5. Snapshot assembly records extractor versions, repository revision,
   source list, and claim/entity/relationship counts.
6. Inspection surfaces render the snapshot for humans and future
   advisory consumers.

Production must be read-only. Extractors may read repository files and
git metadata. They may not rewrite docs, tests, source, task records,
phase reports, or canonical artifacts.

## Inspection Model

Repository Knowledge must be inspectable without model assistance.
Future inspection surfaces may include:

- list entities by type
- show one entity and all source claims
- show documents, tests, reports, and phases linked to an entity
- show relationships by type
- show unresolved or conflicting claims
- show an architecture dependency view
- show a phase-to-subsystem timeline
- show an impact preview for a proposed path change

Inspection output should always expose provenance. A user should be able
to ask "why does PCAE think this test defends this contract?" and receive
the source paths, claims, and relationship that produced the answer.

## Verification Model

Future phases can verify Repository Knowledge extraction through:

- golden fixture repositories with known entities and relationships
- extractor determinism tests across repeated runs
- schema validation for snapshots
- source attribution completeness checks
- contradiction preservation tests
- path rename and missing-source tests
- integration checks against current PCAE governance artifacts
- negative tests proving model prose cannot create accepted knowledge
- read-only tests proving extractors do not mutate repository state

Verification should distinguish extractor correctness from architecture
truth. If a source document is wrong, the extractor may correctly record
the wrong claim with source attribution. A separate evidence or advisory
workflow may flag the contradiction.

## Versioning Model

Repository Knowledge requires versioning at three levels:

| Version | Meaning |
| --- | --- |
| Schema version | Shape of entities, relationships, claims, sources, snapshots, and evidence links. |
| Extractor version | Deterministic logic that produced claims from sources. |
| Repository revision | Git commit or working-tree state used as input. |

Knowledge entity IDs should remain stable across schema versions when
the underlying architectural thing remains the same. Relationship IDs
should remain stable for the same source-derived relationship. If a
schema migration changes identity semantics, the migration must be
explicitly recorded.

Knowledge snapshots are observations, not canonical lifecycle artifacts,
unless a future phase deliberately routes them through Canonical Artifact
Promotion.

## Integration with Evidence

Repository Knowledge integrates with Evidence in three ways:

1. Knowledge can become Evidence when a governance, advisory, validation,
   or reporting evaluation needs a structured observation.
2. Evidence can confirm, contradict, or cite knowledge through Knowledge
   Evidence Links.
3. Evidence Providers and Repository Skills can use Repository Knowledge
   as read-only input for richer, source-attributed observations.

The Evidence Framework remains authoritative for evaluation-scoped
evidence shape. Repository Knowledge cannot create an alternate evidence
path or skip Decision Evaluation.

## Integration with Repository Skills

Repository Skills may later expose knowledge extraction, knowledge
query, or knowledge-to-evidence capabilities.

Examples:

- Architecture Map Skill: produces Evidence about subsystem/document/test
  mappings.
- Contract Coverage Skill: produces Evidence that a contract has or
  lacks linked tests and docs.
- Phase Lineage Skill: produces Evidence about which phases introduced
  or changed a subsystem.
- Impact Candidate Skill: produces Evidence candidates for files touched
  by a transition.

Each remains evidence-only. Skills may read Repository Knowledge, but
they do not own it, decide from it, mutate it, or promote it.

## Integration with Advisory

Repository Knowledge strengthens Advisory by giving advisory workflows
structured, provenance-preserving context before any model is asked to
reason.

Advisory can consume:

- entity summaries
- relationship summaries
- bounded source references
- relevant contracts and tests
- phase lineage
- known limitations and unresolved contradictions
- change impact candidates

Advisory output remains model-produced Evidence. It never becomes
deterministic Repository Knowledge merely because it used Repository
Knowledge as input.

## Integration with Decision Evaluation

Repository Knowledge supports Decision Evaluation only indirectly.

Allowed paths:

- Repository Knowledge produces evidence candidates.
- An Evidence Provider or Repository Skill emits conforming Evidence
  derived from Repository Knowledge.
- Decision Evaluation evaluates that Evidence against invariants.
- The Repository Transition Validator remains the transition verdict
  authority.

Forbidden paths:

- Knowledge directly accepts, rejects, quarantines, or requires human
  review.
- Knowledge votes with or against Evidence Providers.
- Knowledge bypasses Decision Evaluation.
- Knowledge mutates a Transition Result.
- Knowledge promotes or quarantines an artifact.

## Read-Only Boundary

Repository Knowledge must never:

- authorize action
- execute commands
- invoke shell mediation
- invoke backend models
- enforce policy
- mutate repository state
- rewrite docs, tests, source, reports, tasks, or metadata
- promote canonical artifacts
- send notifications
- commit
- push
- replace governance
- replace Decision Evaluation
- replace the Repository Transition Validator

Repository Knowledge may read. It may derive. It may expose structured
relationships. It may produce evidence candidates. It may support
advisory context. It may support human inspection.

## Future Capability Emergence

Repository Knowledge is the shared foundation from which several Track B
capabilities can emerge without becoming silos:

| Future phase | Emerges from |
| --- | --- |
| 118B Historical Memory Architecture | Phase entities, report entities, changelog sources, task records, `introduced_by`, and `changed_by` relationships. |
| 118C Change Impact Analysis | Entity/path mappings, dependency relationships, contract relationships, test relationships, and impact relationships. |
| 118D Dependency Knowledge Graph | Normalized entities and typed relationships projected as graph views. |
| 118E Advisory Reasoning Expansion | Bounded advisory context selected from source-attributed knowledge and converted to ordinary advisory Evidence. |

The important constraint is shared foundation first. Dependency mapping,
historical memory, impact analysis, contract mapping, and advisory
reasoning should reuse the same entity, relationship, claim, source, and
snapshot concepts rather than each creating a private map.

## Non-Goals

Phase 118A does not implement:

- Repository Knowledge extraction
- dependency graph implementation
- historical memory implementation
- change impact implementation
- architectural contract mapping implementation
- advisory behavior changes
- source code changes
- test code changes
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
- new runtime capability
- new enforcement capability

Execution capability remains unavailable. Runtime state remains
`Observed`. Maximum runtime capability remains `observe`.

## Risks

| Risk | Containment |
| --- | --- |
| Knowledge becomes a second source of lifecycle truth | Keep lifecycle truth in Repository State Kernel and require all knowledge claims to be descriptive, not authoritative. |
| Knowledge silently incorporates model inference | Require deterministic extraction and source attribution for accepted knowledge. |
| Graph implementation drives architecture prematurely | Treat graph views as projections over stable records, not the initial storage mandate. |
| Knowledge duplicates Evidence | Keep Repository Knowledge reusable and Evidence evaluation-scoped; conversion must pass through Evidence contracts. |
| Impact analysis appears to decide safety | Express impact results as candidates or Evidence only; Decision Evaluation remains sole decision path. |
| Source documents are stale or contradictory | Preserve contradictions as attributed claims and surface them for evidence/advisory review. |

## Open Questions

- What exact snapshot schema should be frozen first?
- Which source classes should the first extractor support: docs only, or
  docs plus tests and phase records?
- Should Knowledge Snapshots become ordinary generated artifacts or
  eventually be promoted through Canonical Artifact Promotion?
- How should stable IDs handle renamed files and renamed subsystems?
- Which relationships are strong enough for deterministic extraction in
  the first prototype?
- Should impact relationships begin as manually curated claims,
  extractor-derived claims, or both with explicit source classes?
- How should future advisory workflows request knowledge slices while
  preserving prompt-injection boundaries?

## Recommended Next Phase

118B - Historical Memory Architecture.
