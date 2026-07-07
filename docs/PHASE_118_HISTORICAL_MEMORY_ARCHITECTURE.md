# Phase 118B - Historical Memory Architecture

## Purpose

Phase 118B defines Historical Memory for Track B: Repository
Intelligence.

Historical Memory is PCAE's deterministic, source-attributed,
inspectable understanding of how repository architecture, capabilities,
contracts, constraints, repairs, releases, and decisions evolved over
time. It is not generic AI memory, model memory, conversation memory, an
autonomous planner, a decision maker, or an execution mechanism.

This phase is architecture only. It does not implement historical memory
extraction, storage, CLI queries, dependency graph work, change impact
analysis, advisory behavior changes, runtime behavior, lifecycle
behavior, execution, enforcement, or repository mutation.

## Track B Context

Track B asks whether PCAE can understand the repository itself. Phase
118A answered the first foundational question by defining Repository
Knowledge as deterministic, inspectable, source-attributed architectural
understanding of repository entities and relationships.

Phase 118B answers the next question: how can PCAE understand the
repository's engineering history?

Historical Memory must emerge from Repository Knowledge rather than
become a separate silo. It is the time-aware layer of Repository
Knowledge: the part that explains when and why architectural entities
appeared, changed, froze, were repaired, were superseded, or entered a
release.

## Relationship to 118A Repository Knowledge

118A defines the shared knowledge primitives: Knowledge Entity,
Knowledge Relationship, Knowledge Claim, Knowledge Source, Knowledge
Evidence Link, and Knowledge Snapshot.

Historical Memory specializes those primitives for time and lineage:

| 118A primitive | Historical specialization |
| --- | --- |
| Knowledge Entity | Historical subject such as a phase, subsystem, contract, capability, report, decision, release, repair, or hardening item. |
| Knowledge Relationship | Historical relationship such as `introduced_by`, `changed_by`, `froze_contract`, `repaired_by`, `supersedes`, `included_in_release`, or `evolved_into`. |
| Knowledge Claim | Source-attributed historical claim about what happened and what it affected. |
| Knowledge Source | Phase reports, completion metadata, architecture docs, task records, changelog entries, commits, tags, release notes, evidence artifacts, and canonical lifecycle artifacts. |
| Knowledge Evidence Link | Bridge from a historical claim to Evidence that used, confirmed, contradicted, or was produced from that claim. |
| Knowledge Snapshot | Versioned historical view over a repository revision and extractor version. |

Historical Memory should therefore be implemented as a profile or view
of Repository Knowledge, not as an independent memory database with its
own source model.

## Definition of Historical Memory

**Historical Memory** is the deterministic, source-attributed,
versioned representation of repository engineering history as structured
entities, events, claims, relationships, and lineage views.

It answers questions such as:

- Which phase introduced this subsystem?
- Which phase changed this architectural contract?
- Which report explains why this capability exists?
- Which decisions led to this boundary?
- Which repairs or hardening phases shaped this component?
- Which release introduced, froze, or published this architecture?
- Which documents, task records, reports, commits, and tags support this
  history?
- Which earlier historical claims were corrected or superseded?

Historical Memory is repository-derived. A model may suggest a candidate
historical interpretation, but that interpretation is not canonical
Historical Memory unless it is grounded in repository artifacts and
converted through a governed, source-attributed path.

## Historical Memory vs Repository Knowledge

Repository Knowledge describes what the repository contains
architecturally and how entities relate. Historical Memory describes how
those entities and relationships evolved over time.

| Concept | Primary question | Scope |
| --- | --- | --- |
| Repository Knowledge | What architectural entities and relationships exist? | Current and source-attributed semantic map. |
| Historical Memory | How did those entities and relationships come to exist, change, freeze, repair, supersede, or release? | Time-aware lineage over the same semantic map. |

Historical Memory does not replace Repository Knowledge. It adds
temporal relationships, event classifications, correction semantics, and
lineage views to Repository Knowledge.

## Historical Memory vs Repository State

Repository State describes current governed condition: clean tree, active
task, phase identity, canonical report trust, push state, runtime state,
and execution availability.

Historical Memory describes past engineering evolution. It may record
that Phase 114C repaired pushed-state reconciliation, but it does not
decide whether the current push state is clean. That remains Repository
State / Repository Transition Validator authority.

Historical Memory may cite Repository State artifacts as sources, but it
does not become a Repository State Kernel primitive and does not validate
transitions.

## Historical Memory vs Evidence

Evidence is evaluation-scoped. Historical Memory is reusable historical
knowledge.

Historical Memory can produce evidence candidates such as:

- "This file belongs to a subsystem frozen by Phase 116F."
- "This contract was repaired by Phase 117E.1 after stale publication
  metadata was discovered."
- "This advisory boundary was introduced across Phases 115P-115Y."

To influence governance or advisory decisions, a historical claim must be
converted into conforming Evidence. The Evidence Framework remains the
authority for evidence fields, freshness, confidence, determinism, scope,
references, observed value, limitations, and explanation.

## Historical Memory vs Advisory Context

Advisory Context Packages are bounded, prompt-safe context bundles for
advisory workflows. Historical Memory is structured repository history
that may be summarized into such bundles.

Historical Memory can help advisory workflows select relevant phase
history, contract lineage, release context, prior repairs, and known
limitations. The Advisory Context Package still owns budget limits,
redaction, trust-class separation, provenance, and prompt-injection
protection.

Historical Memory is not prompt text. It is structured source-attributed
data that may be rendered into bounded advisory context.

## Historical Memory vs Model and Conversation Memory

Model memory and conversation memory are not canonical PCAE truth.

| Memory type | PCAE treatment |
| --- | --- |
| Model memory | Non-authoritative. May not become a historical source unless the relevant content is captured into repository artifacts through governed lifecycle. |
| Conversation memory | Non-authoritative. May inform a prompt or human workflow, but does not become Historical Memory unless converted into source-attributed repository artifacts. |
| Historical Memory | Repository-derived, deterministic, source-attributed, inspectable, and versioned. |

Historical Memory must never trust hidden model state, conversational
state, prompt wording, or AI-generated prose as canonical history.

## Core Primitives

Historical Memory should refine the prompt's suggested primitive list
into a smaller set that fits 118A's Repository Knowledge architecture:

| Primitive | Meaning |
| --- | --- |
| Historical Subject | The thing whose history is being described: phase, subsystem, capability, contract, report, decision, repair, release, task, document, or source artifact. |
| Historical Event | A source-attributed event that changed or described a subject: introduction, modification, contract freeze, prototype, verification, integration, hardening, repair, release inclusion, supersession, deprecation, or correction. |
| Historical Claim | A source-attributed assertion about an event, subject, lineage, correction, or relationship. |
| Historical Source | The repository artifact supporting a claim: report, metadata, architecture doc, task record, changelog entry, commit, tag, release note, evidence artifact, skill record, or lifecycle artifact. |
| Historical Lineage | An ordered, typed chain of subjects and events showing evolution over time. |
| Historical Evidence Link | A bridge between Historical Memory and Evidence that used, confirmed, contradicted, or was produced from a historical claim. |
| Historical Snapshot | Versioned historical memory view derived from a repository revision, source set, and extractor version. |
| Historical Query Result | Inspectable answer assembled from claims, sources, events, and lineage views, always with provenance and limitations. |

Terms such as Phase Event, Release Event, Decision Event, Repair Event,
Hardening Event, Contract Freeze Event, and Supersession Event should be
event types under Historical Event, not separate top-level primitives.
Architecture Lineage, Capability Lineage, and Subsystem Lineage are
lineage views over the same Historical Lineage primitive.

## Historical Event Taxonomy

The initial event taxonomy should include:

| Event type | Meaning |
| --- | --- |
| `introduced` | A phase first defines a subsystem, contract, capability, or artifact. |
| `modified` | A later phase changes documented behavior, scope, wording, or implementation shape. |
| `contract_frozen` | A phase freezes an interface, invariant set, schema, or architecture boundary. |
| `prototype_added` | A phase introduces an implementation prototype under an existing contract. |
| `verified` | A phase verifies behavior, compatibility, quality, or architecture consistency. |
| `integrated` | A phase wires an already-defined subsystem into lifecycle or other architecture paths. |
| `hardened` | A phase strengthens validation, safety, trust, or failure handling. |
| `repaired` | A phase corrects a defect, stale artifact, publication gap, or metadata inconsistency. |
| `superseded` | A later artifact or decision replaces an earlier historical claim or recommendation. |
| `deprecated` | A subject is retained only as historical reference or superseded planning scratch. |
| `included_in_release` | A release includes a subsystem, capability, contract, or documentation set. |
| `published` | A tag, release, or release note becomes externally visible. |

Events must be source-attributed and typed. Free-text summaries may
explain the event, but the event type and source links are the durable
historical structure.

## Phase Representation

A Phase Subject represents one governed phase. It should carry:

- phase ID
- phase name/title
- status
- phase type or event role where derivable
- recommended next phase
- source documents
- canonical report links
- completion metadata links
- task records
- commit references
- release or tag references where applicable
- no-go boundaries
- validation summaries
- known limitations

Phase history must remain append-aware. A repair phase does not erase the
phase it repaired. For example, 117E remains release-preparation /
release-attempt history, while 117E.1 is an additive publication repair.

## Report Representation

A Report Subject represents a durable phase-report artifact. Historical
Memory should distinguish:

- canonical latest report
- timestamped report
- quarantined report
- phase-completion metadata
- manually sent notification report
- stale or superseded report

Reports can produce Historical Events such as `verified`, `repaired`,
`superseded`, or `published`. A quarantined report is historical evidence
of a blocked attempt, not canonical phase truth.

## Decision Representation

Historical Memory represents architectural decisions as source-attributed
Decision Subjects and Decision Events.

Sources may include:

- `tasks/DECISIONS.md`
- phase architecture documents
- completion reports
- changelog entries
- task contracts
- release notes

Decision history must preserve reversals and supersessions. A later
decision may supersede an earlier recommendation without deleting the
earlier decision from history. Historical Memory records both the old
claim and the supersession relationship.

Decision Representation is not Decision Evaluation. It describes past
engineering decisions; it does not decide current transitions.

## Repair and Hardening Representation

Repair and hardening events deserve first-class event types because PCAE
often evolves through containment findings, metadata corrections, stale
artifact repairs, notification repairs, and trust-gate hardening.

A repair event should record:

- defect or gap repaired
- affected historical subject
- source that discovered the gap
- source that repaired it
- whether history was rewritten or preserved additively
- new invariant, trust field, or boundary introduced
- validation proving the repair

A hardening event should record:

- risk or failure mode addressed
- boundary strengthened
- invariant or check added
- compatibility impact
- verification scope

Repairs must not erase the repaired event. They create correction
relationships.

## Release Milestone Representation

Release milestones should be represented as Release Subjects and Release
Events linked to:

- tags
- GitHub Releases
- release notes
- package metadata
- release-candidate phases
- publication repair phases
- validation baseline phases
- architecture freeze phases
- explicit non-goals and boundaries

Release history must distinguish release preparation, release candidate
readiness, tag publication, GitHub Release publication, package
publication, and corrective publication repair.

## Lineage Model

Historical Lineage is an ordered, typed chain that links subjects through
events and sources.

Initial lineage classes:

| Lineage class | Example question |
| --- | --- |
| Phase Lineage | What phases led from architecture design to contract freeze, prototype, verification, integration, release, and repair? |
| Subsystem Lineage | Which phases introduced, changed, froze, verified, and released this subsystem? |
| Capability Lineage | Which decisions and artifacts led to this capability? |
| Contract Lineage | Which document froze this contract, and which phases later verified or amended it? |
| Repair Lineage | Which failures or stale artifacts were discovered, repaired, and revalidated? |
| Release Lineage | Which phases and artifacts led to a release milestone? |

Lineage ordering must be deterministic. Preferred ordering is by
explicit phase ordering when available, then by commit ancestry or
timestamped artifact identity, never by filesystem traversal order.

## Source Attribution Model

Every Historical Claim must cite one or more Historical Sources. A source
reference should carry:

- source type
- path or artifact identifier
- optional section/heading
- commit hash, tag, report timestamp, or phase ID when available
- extraction rule or source reader
- source trust class
- limitations

Accepted source types include:

- phase reports
- phase-completion metadata
- architecture documents
- contract documents
- verification documents
- changelog entries
- `tasks/DONE.md`
- task contracts
- `tasks/DECISIONS.md`
- release notes
- tags
- commits
- evidence artifacts
- repository skills
- advisory skills
- canonical lifecycle artifacts

Unattributed historical claims are invalid. AI-generated prose is not a
Historical Source unless captured as labelled advisory Evidence or a
governed repository artifact.

## Supersession and Correction Model

Historical Memory must be append-aware and supersession-aware.

It should represent:

- corrected reports
- stale metadata
- superseded architecture
- renamed phases
- repaired lifecycle artifacts
- changed recommendations
- decisions later reversed
- release-publication gaps repaired by later phases

Correction does not delete the original claim. Instead, Historical
Memory records:

1. original claim
2. source of the original claim
3. correction claim
4. correction source
5. correction relationship: `corrects`, `supersedes`, `reclassifies`,
   `repairs`, or `deprecates`
6. current recommended interpretation
7. limitations and unresolved ambiguity

For example, Phase 117E can remain historical release-preparation /
release-attempt work while Phase 117E.1 corrects the publication gap and
publishes the missing external release artifacts.

## Conflict Model

Conflicting historical claims must be preserved, not silently resolved.

Conflict examples:

- task memory says a phase completed, but canonical latest report points
  to an earlier phase
- release metadata says a release was published, but tag/release lookup
  shows missing artifacts
- roadmap scratch marks one phase as next while `PROJECT_STATUS.md`
  recommends another
- report summary and structured metadata disagree

Historical Memory may classify the conflict and cite the current
authoritative source order. It may not rewrite history or choose a truth
without recording the conflict and source basis.

## Determinism Model

Historical Memory must be derived from repository artifacts through
deterministic inspection. Acceptable derivation methods include:

- parsing structured phase-completion metadata
- reading canonical and timestamped phase reports
- parsing known Markdown headings in architecture docs
- reading changelog and task memory entries
- inspecting git commit ancestry, commit messages, tags, and release
  records
- reading release notes and external publication records when captured
  in repository artifacts
- matching explicit phase IDs and document paths
- reading governed task contracts and decisions

The same repository revision, source set, extractor version, and
configuration must produce the same Historical Snapshot.

Probabilistic model inference may suggest candidate history, but it
cannot become accepted Historical Memory without deterministic source
attribution.

## Verification Model

Future phases can verify Historical Memory through:

- fixture repositories with known phase/report/decision/release history
- repeated-run determinism tests
- source attribution completeness checks
- schema validation for Historical Snapshots
- conflict preservation tests
- supersession/correction tests
- stale report and stale metadata fixtures
- release publication repair fixtures
- lineage ordering tests
- read-only mutation tests
- negative tests proving model/conversation memory cannot become
  canonical history

Verification should distinguish extraction correctness from source
truth. An extractor may correctly record a stale historical claim if the
source says it; a separate correction relationship records the later
repair.

## Versioning Model

Historical Memory requires:

| Version | Meaning |
| --- | --- |
| Historical schema version | Shape of subjects, events, claims, sources, lineages, snapshots, and query results. |
| Extractor version | Deterministic rules used to derive history. |
| Repository revision | Commit or working-tree state used as input. |
| Source version | Phase report timestamp, tag, release identifier, or document commit when available. |

Historical IDs should remain stable for the same subject. If an entity is
renamed, the old ID should remain as an alias or superseded subject, not
silently disappear.

## Query Model

Historical Memory should eventually support inspectable query classes:

| Query class | Example |
| --- | --- |
| Phase lineage query | Show the lineage for Phase 115P through 115Y. |
| Subsystem lineage query | Which phases introduced, froze, verified, and released Advisory Context Packages? |
| Decision lineage query | Which decisions led to the no-execution boundary? |
| Contract history query | Which phases froze and verified the Repository Skills contract? |
| Report history query | Which canonical or quarantined reports exist for a phase? |
| Release history query | Which phases prepared, published, or repaired v0.2.0? |
| Repair history query | Which repairs affected phase report trust? |
| Change ancestry query | Which past phases touched the subsystem containing this artifact? |
| Advisory context query | What bounded historical context should be included for this advisory question? |

Every query result must include sources, confidence/verification status,
limitations, and any conflicting or superseded claims involved.

## Integration with Repository Knowledge

Historical Memory extends Repository Knowledge by adding temporal
semantics. It should reuse the same Knowledge Entity, Relationship,
Claim, Source, Evidence Link, and Snapshot concepts from 118A.

Historical Memory should not maintain private copies of subsystem,
contract, document, report, or capability entities. It should attach
events and lineage relationships to those shared entities.

## Integration with Evidence

Historical Memory can produce evidence candidates or evidence links.

Examples:

- `phase` Evidence: a phase introduced or changed a subsystem.
- `architecture` Evidence: a contract was frozen by a named phase.
- `documentation` Evidence: a doc superseded an older recommendation.
- `report` Evidence: a report was quarantined and later corrected.
- `metadata` Evidence: current metadata conflicts with historical
  sources.

Evidence remains evaluation-scoped. Historical facts do not influence
governance until a conforming Evidence item is produced and evaluated.

## Integration with Repository Skills

Future Repository Skills may expose historical inspection or query
capabilities, such as:

- Historical Lineage Skill
- Release History Skill
- Contract History Skill
- Repair History Skill
- Supersession Detection Skill
- Advisory Historical Context Skill

Each skill remains evidence-only. It may read Historical Memory and emit
Evidence, but it may not decide, mutate, promote, notify, commit, push,
finalize, or execute.

## Integration with Advisory

Historical Memory strengthens Advisory by giving advisory workflows
structured historical context:

- why a subsystem exists
- which constraints shaped it
- which repairs or hardening phases matter
- which contracts are frozen
- which release included a capability
- which known limitations or superseded claims apply

Advisory output remains model-produced Evidence. A model response cannot
become Historical Memory merely because it discussed history.

## Integration with Decision Evaluation

Historical Memory supports Decision Evaluation only indirectly:

1. Historical Memory produces structured context or evidence candidates.
2. A Repository Skill or Evidence Provider emits conforming Evidence.
3. Decision Evaluation evaluates the Evidence against invariants.
4. The Repository Transition Validator remains the sole transition
   verdict authority.

Historical Memory never accepts, rejects, quarantines, escalates,
authorizes, or requests more evidence by itself.

## Read-Only and No-Execution Boundary

Historical Memory must never:

- authorize action
- execute commands
- invoke shell mediation
- invoke backend models
- enforce policy
- mutate repository state
- rewrite history
- rewrite docs, tests, source, reports, tasks, metadata, tags, or
  release records
- promote canonical artifacts
- send notifications
- commit
- push
- replace governance
- replace Decision Evaluation
- replace the Repository Transition Validator
- become model memory or conversation memory

Historical Memory may read repository artifacts, derive historical
claims, expose lineage, produce evidence candidates, and support bounded
advisory context.

## Future Emergence Paths

Historical Memory supports later Track B phases:

| Future phase | Historical contribution |
| --- | --- |
| 118C Change Impact Analysis Architecture | Provides phase, repair, contract, and subsystem ancestry for touched artifacts. |
| 118D Dependency Knowledge Graph | Supplies time-aware graph edges such as `introduced_by`, `changed_by`, `supersedes`, and `included_in_release`. |
| 118E Advisory Reasoning Expansion | Supplies bounded, provenance-preserving historical context for advisory reasoning. |

These capabilities should reuse Historical Memory as part of Repository
Knowledge rather than build separate historical indexes.

## Risks

| Risk | Containment |
| --- | --- |
| Historical Memory becomes generic model memory | Require repository-derived sources and reject hidden model/conversation state as canonical history. |
| Historical Memory rewrites uncomfortable history | Preserve original claims and add correction/supersession relationships instead of deleting. |
| Historical lineage silently chooses between conflicts | Preserve conflicts and cite authoritative source order and limitations. |
| Historical Memory becomes a decision maker | Allow only evidence/context output; Decision Evaluation remains the decision path. |
| Historical query results become unbounded advisory context | Route advisory use through Advisory Context Package budgets, provenance, and redaction rules. |
| Historical extractor bugs create false confidence | Require source attribution, extractor versioning, fixture tests, and contradiction checks. |

## Open Questions

- What schema should the first Historical Snapshot freeze?
- Should the first extraction scope be phase reports only, or phase
  reports plus `PROJECT_STATUS.md`, changelog, and task memory?
- How should historical IDs handle phase renames and document renames?
- Which source wins when source precedence must be stated in query
  output?
- Should external release state be represented only after it is captured
  into repository artifacts?
- Which lineage class should 118C consume first for change impact
  analysis?

## Recommended Next Phase

118C - Change Impact Analysis Architecture.
