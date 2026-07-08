# Phase 118C - Change Impact Analysis Architecture

## Purpose

Phase 118C defines Change Impact Analysis for Track B: Repository
Intelligence.

Change Impact Analysis is PCAE's deterministic, source-attributed,
inspectable way to reason about what may be affected by a proposed or
observed repository change. It is grounded in Repository Knowledge and
Historical Memory. It is not prediction by hidden model inference, not
autonomous planning, not enforcement, not permission brokering, not
test execution, not patch generation, and not a decision maker.

This phase is architecture only. It does not implement an impact
analysis engine, extractor, database, CLI, dependency graph, historical
memory extraction, repository knowledge extraction, advisory behavior,
decision evaluation behavior, evidence subsystem behavior, repository
skills behavior, runtime behavior, lifecycle redesign, execution,
enforcement, REST, Dashboard, Web UI, Telegram inbound, provider
selection, multi-model orchestration, autonomous coding, automatic patch
generation, or automatic refactoring.

## Track B Context

Track B asks whether PCAE can understand the repository itself.

Phase 118A answered the first foundational question by defining
Repository Knowledge as deterministic, inspectable, source-attributed,
read-only architectural understanding of repository entities,
relationships, claims, sources, snapshots, and evidence links.

Phase 118B answered the second question by defining Historical Memory as
the time-aware layer inside Repository Knowledge: deterministic,
source-attributed, inspectable, versioned understanding of how
repository architecture, capabilities, contracts, constraints, repairs,
hardening, releases, and decisions evolved.

Phase 118C answers the next question: how can PCAE understand the
architectural blast radius of a proposed change?

Change Impact Analysis must emerge from Repository Knowledge and
Historical Memory. It must not become a separate silo, a planner, an
authorization mechanism, or a runtime capability.

## Relationship to 118A Repository Knowledge

118A defines the shared knowledge primitives: Knowledge Entity,
Knowledge Relationship, Knowledge Claim, Knowledge Source, Knowledge
Evidence Link, and Knowledge Snapshot.

Change Impact Analysis is a view over those primitives:

| 118A primitive | Impact specialization |
| --- | --- |
| Knowledge Entity | Impact entity such as a source module, command, test, document, contract, phase, report, skill, evidence artifact, lifecycle artifact, or no-go boundary. |
| Knowledge Relationship | Impact relationship such as `imports`, `tests`, `documents`, `constrains`, `depends_on`, `introduced_by`, `hardened_by`, `uses_advisory_context`, or `may_affect`. |
| Knowledge Claim | Impact claim about why one entity may be affected by a change to another. |
| Knowledge Source | Repository artifact supporting the impact claim: source file, test, doc, phase report, task record, changelog entry, commit, release note, evidence artifact, skill contract, or lifecycle artifact. |
| Knowledge Evidence Link | Bridge from an impact claim to Evidence that used, confirmed, contradicted, or was produced from the claim. |
| Knowledge Snapshot | Versioned impact view over a repository revision, knowledge snapshot, historical snapshot, and analyzer version. |

Change Impact Analysis consumes Repository Knowledge. It does not
replace the entity model, relationship model, source model, or snapshot
model 118A defined.

## Relationship to 118B Historical Memory

118B defines Historical Memory as temporal lineage inside Repository
Knowledge. Change Impact Analysis uses that lineage to answer why a
change may matter beyond the immediate file or subsystem.

Historical Memory can show that a capability was introduced by one
phase, frozen by another, repaired by a later phase, and included in a
release. Change Impact Analysis can use that lineage to produce impact
claims such as:

- this proposed change touches a subsystem frozen by Phase 116F
- this document explains a boundary repaired by Phase 117E.1
- this skill contract was introduced before the Advisory Context Package
  and may constrain advisory expansion
- this no-go boundary is part of the v0.2 execution-readiness history

Historical Memory informs impact. It does not decide whether the change
is allowed, and Change Impact Analysis does not rewrite history.

## Definition of Change Impact Analysis

**Change Impact Analysis** is the deterministic, source-attributed,
inspectable analysis of which repository entities, relationships,
contracts, tests, documents, historical lineages, advisory surfaces, and
governance boundaries may be affected by a proposed or observed
repository change.

It answers questions such as:

- If this file changes, what architectural entities may be affected?
- Which tests defend the changed entity?
- Which contracts constrain the changed entity?
- Which documents explain or limit the changed behavior?
- Which Repository Skills or Advisory Repository Skills reference this
  area?
- Which phases introduced, verified, hardened, repaired, froze, or
  released this capability?
- Which evidence would be needed before Advisory or Decision Evaluation
  could reason about the change?
- What is known, unknown, unverifiable, stale, superseded, or
  conflicting about the impact?

Impact analysis is structured context. It is not a verdict.

## Change Impact Analysis vs Repository Knowledge

Repository Knowledge describes what the repository contains and how its
entities relate. Change Impact Analysis reasons over that knowledge for
a specific change.

| Concept | Primary question | Role |
| --- | --- | --- |
| Repository Knowledge | What entities and relationships exist? | Reusable semantic map. |
| Change Impact Analysis | What may be affected by this change? | Change-scoped view over the semantic map. |

Repository Knowledge may contain the relationship "test file X tests
contract Y." Change Impact Analysis may use that relationship to claim
"a change to contract Y has test impact on X." The impact claim must
preserve the relationship's original source attribution.

## Change Impact Analysis vs Historical Memory

Historical Memory describes evolution over time. Change Impact Analysis
uses that evolution to identify historical impact.

| Concept | Primary question | Role |
| --- | --- | --- |
| Historical Memory | How did this entity or boundary evolve? | Temporal lineage. |
| Change Impact Analysis | Which historical lineages are implicated by this change? | Change-scoped lineage reasoning. |

Historical Memory may say Phase 115H defined Repository Skills as
evidence-only. Change Impact Analysis may say a proposed Repository
Skill change has historical and contractual impact on that evidence-only
boundary.

## Change Impact Analysis vs Evidence

Evidence is evaluation-scoped observation. Change Impact Analysis is
reusable structured context over Repository Knowledge and Historical
Memory.

Impact claims can become evidence candidates, but they are not
automatically Evidence. To be used in Decision Evaluation, an impact
claim must be converted into conforming Evidence with category,
producer, timestamp, freshness, confidence, determinism, scope,
references, observed value, expected value, explanation, and
limitations.

Impact analysis may say "this change may affect a frozen contract."
Evidence may later say "for transition T, changed path P is linked by
source-attributed relationship R to frozen contract C." The Evidence
Framework still owns evidence shape and semantics.

## Change Impact Analysis vs Decision Evaluation

Decision Evaluation remains the only component responsible for
allow/block/escalate/more-evidence decisions.

Change Impact Analysis:

- identifies impact surfaces
- preserves sources and uncertainty
- produces structured context
- may produce evidence candidates or evidence links
- may support Advisory explanations

Change Impact Analysis never:

- accepts or rejects a transition
- quarantines or promotes an artifact
- requests or grants human review
- authorizes execution
- enforces policy
- bypasses the Repository Transition Validator

Decision Evaluation consumes Evidence and invariants to produce
centralized explanations and verdicts. Impact analysis may inform that
path only indirectly, through structured context or conforming Evidence.

## Change Impact Analysis vs Model Prediction

Change Impact Analysis is not model prediction.

Model prediction may say "this probably affects the CLI" because a model
recognizes a pattern. That is not canonical impact analysis unless it is
converted into source-attributed claims grounded in repository artifacts.

Canonical Change Impact Analysis must be derived from:

- repository paths and structured artifacts
- parsed or declared relationships
- contracts and architecture documents
- tests and validation commands
- phase reports and completion metadata
- changelog and task records
- commits, tags, and release notes
- repository skills and advisory skill contracts
- evidence artifacts and lifecycle artifacts

A model may help draft a candidate interpretation for a human or future
Advisory workflow. Hidden model state, conversation memory, prompt
wording, and AI-generated prose are not sources of truth.

## Core Primitives

The clean primitive set is:

| Primitive | Meaning |
| --- | --- |
| Impact Subject | The proposed or observed change being analyzed: a changed path, diff, task scope, subsystem, contract, command, document, report, phase, release item, or declared change intent. |
| Impact Entity | A Repository Knowledge entity that may be affected by the subject. |
| Impact Surface | A named category of impact such as source, command, test, documentation, contract, historical, advisory, evidence, release, lifecycle, governance, or no-go boundary. |
| Impact Relationship | A typed relationship that explains why impact may exist. |
| Impact Path | An ordered chain of entities and relationships from the subject to an impacted entity. |
| Impact Claim | A source-attributed assertion that the subject has direct, indirect, historical, contractual, test, documentation, advisory, evidence, release, lifecycle, governance, unknown, or unverified impact. |
| Impact Source | The repository artifact supporting an impact claim. |
| Impact Evidence Link | A bridge between an impact claim and Evidence that used, confirmed, contradicted, or was produced from it. |
| Impact Scope | The boundary of the analysis: paths, subsystem, phase, task, revision, source set, and analyzer version. |
| Blast Radius | A conservative classification of the extent and type of possible impact. |
| Impact Query | A deterministic question over impact records. |
| Impact Report | An inspectable, non-decision artifact summarizing the analysis. |

Terms such as Direct Impact, Indirect Impact, Historical Impact,
Contractual Impact, Test Impact, Documentation Impact, Advisory Impact,
Governance Impact, Unknown Impact, and Unverified Impact should be
impact claim types or surface classifications, not separate top-level
primitives.

## Impact Entity Model

An Impact Entity is any Repository Knowledge entity that may be touched,
constrained, explained, defended, or implicated by a change.

The initial entity taxonomy should include:

| Entity type | Examples |
| --- | --- |
| Source module | `src/pcae/core/...`, command modules, package modules, scripts. |
| Package | Python package, CLI package, runtime package, test package. |
| Command or CLI surface | `pcae health`, `pcae check`, `pcae runtime inspect`, lifecycle commands. |
| Test entity | Test file, test class, focused test, validation command, fast-green suite. |
| Documentation entity | Architecture doc, roadmap, release notes, README, install guide. |
| Contract entity | Runtime contract, Evidence contract, Repository Skill contract, Advisory Context Package contract, no-go contract. |
| Report entity | Phase report, canonical latest report, quarantined report, completion metadata. |
| Phase entity | Phase 113S, 115B, 116F, 117E.1, 118A, 118B, 118C. |
| Lifecycle artifact | Task contract, `tasks/DONE.md`, `PROJECT_STATUS.md`, changelog entry, phase-completion metadata. |
| Repository Skill entity | Skill contract, manifest, evidence category, implementation, tests. |
| Advisory Skill entity | Advisory provider, Advisory Repository Skill, Advisory Context Package, prompt boundary. |
| Evidence entity | Evidence provider, evidence item, evidence category, evidence artifact, evidence candidate. |
| Decision input entity | Invariant input, evaluation context, explanation reference, transition metadata. |
| Runtime architecture entity | Runtime state, plugin capability, registry, introspection, context, snapshot. |
| Release entity | Release notes, tag, GitHub Release, release metadata. |
| No-go boundary | Execution-readiness no-go gate, autonomy contract invariant, runtime enforcement no-go item. |

Entity identity must be stable, deterministic, and source-derived.

## Impact Relationship Model

Impact relationships are typed, directional, source-attributed
relationships that can imply impact.

The initial relationship taxonomy should include:

| Relationship | Impact implication |
| --- | --- |
| `imports` | Source change may affect importing or imported modules. |
| `implements` | Source change may affect the documented contract it implements. |
| `command_owns` | Command-surface change may affect lifecycle or operator workflow. |
| `tests` | Changed entity may require test review or rerun. |
| `documents` | Changed entity may require documentation review or update. |
| `references_contract` | Change may implicate a frozen or proposed contract. |
| `constrains` | Contract, invariant, or no-go rule limits allowed behavior. |
| `depends_on` | Consumer may be affected by provider/output/schema changes. |
| `schema_depends_on` | Structured artifact changes may affect parsers, reports, or validation. |
| `introduced_by` | Historical introduction phase is relevant context. |
| `modified_by` | Later historical changes may explain impact. |
| `hardened_by` | Hardening phase may indicate safety-sensitive impact. |
| `repaired_by` | Repair phase may indicate prior defect-prone boundary. |
| `supersedes` | Earlier source may be stale or replaced. |
| `included_in_release` | Change may affect release notes or release posture. |
| `uses_advisory_context` | Change may affect Advisory input packaging or prompt boundaries. |
| `produces_evidence_for` | Change may affect evidence production or evidence candidates. |
| `governs` | Lifecycle/governance artifact constrains a transition or report. |
| `may_affect` | Derived impact relationship with explicit path and limitations. |

The relationship source matters as much as the relationship type. An
impact relationship without sources is a candidate, not canonical impact
knowledge.

## Impact Path Model

An Impact Path is an ordered explanation of how a subject reaches an
impacted entity.

Example shape:

```
changed path
  -> implements
source module
  -> references_contract
contract document
  -> hardened_by
phase report
  -> constrains
no-go boundary
```

Each step carries:

- relationship type
- source attribution
- confidence or verification state
- limitations
- freshness or supersession state

Impact paths prevent black-box answers. PCAE should be able to explain
not only that a change may affect something, but which relationships and
sources led to that claim.

## Impact Claim Model

An Impact Claim is a source-attributed assertion about impact.

Required conceptual fields:

- claim ID
- impact subject
- impacted entity
- impact surface
- impact type
- impact path
- source references
- verification state
- confidence class
- freshness state
- limitations
- known unknowns
- conflicting or superseding claims
- evidence links, if any

Impact claim types include:

- direct impact
- indirect impact
- historical impact
- contractual impact
- test impact
- documentation impact
- advisory impact
- evidence impact
- release impact
- lifecycle impact
- governance impact
- no-go boundary impact
- unknown impact
- unverified impact

Impact claims are conservative. If a relationship cannot be verified,
the claim must say so rather than disappear or become falsely certain.

## Blast Radius Model

Blast Radius is a conservative classification of the extent and type of
possible impact. It is not a decision.

Initial blast-radius classes:

| Class | Meaning |
| --- | --- |
| `local` | Impact appears limited to the changed entity and immediate tests/docs. |
| `subsystem` | Impact reaches a named subsystem, contract, command family, or skill family. |
| `cross_subsystem` | Impact path crosses subsystem boundaries. |
| `governance` | Impact touches lifecycle, Repository State, Transition Validator, Decision Evaluation, Evidence, no-go, or report-trust boundaries. |
| `advisory` | Impact touches Advisory Repository Skills, Advisory Provider, Advisory Context Package, or model-output normalization boundaries. |
| `documentation_only` | Change is limited to docs, with no identified source/test/runtime behavior impact. |
| `historical_lineage` | Change affects interpretation of historical phases, lineage, release history, or supersession/correction records. |
| `release` | Change affects release notes, tags, package metadata, or release posture. |
| `unknown` | Sources are insufficient to bound the impact. |
| `unverified` | Impact is plausible but not verified by canonical sources. |

Blast radius should carry explanations and sources, not just labels.
When multiple classes apply, the report should preserve all applicable
classes rather than collapse them into one score.

## Source Attribution Model

Every impact claim must cite at least one Impact Source.

Valid sources include:

- source files
- test files
- documentation files
- architecture documents
- contract documents
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
- canonical lifecycle artifacts
- generated registry or runtime-introspection output

A source reference should record:

- path or artifact ID
- optional section, heading, line, or structured field
- commit or repository revision
- source type
- source freshness
- whether the source is canonical, historical, superseded, quarantined,
  or advisory
- extraction or analysis method
- limitations

No unattributed impact claim should be promoted into a canonical impact
report.

## Determinism Model

Future impact analysis should be reproducible from:

1. repository revision
2. Repository Knowledge snapshot
3. Historical Memory snapshot
4. declared impact subject
5. source set
6. analyzer version
7. relationship taxonomy version
8. query parameters

The same inputs should produce the same impact claims, paths, blast
radius classes, unknowns, and limitations.

Determinism means impact analysis derives from repository artifacts and
structured relationships, not from model phrasing. If a future model
suggests an impact path, that path remains non-canonical until a
deterministic process grounds it in sources and records its limitations.

## Uncertainty Model

Change Impact Analysis must avoid false certainty.

Verification states:

| State | Meaning |
| --- | --- |
| `verified` | Sources directly support the claim and path. |
| `derived` | Claim follows from verified relationships but no single source states it directly. |
| `probable` | Multiple relevant sources suggest impact, but the relationship is indirect or incomplete. |
| `possible` | A plausible source-attributed relationship exists, but evidence is weak or partial. |
| `unknown` | PCAE cannot determine whether impact exists. |
| `unverifiable` | Available repository sources are insufficient to verify the claim. |
| `conflicting` | Sources disagree and the conflict is preserved. |
| `stale` | Claim depends on older or superseded evidence. |
| `superseded` | A newer source replaces or corrects the claim. |

Confidence describes trust in the impact claim, not permission to act.
Low or unknown confidence should be preserved. Conflicting claims should
be shown side by side. Stale and superseded sources must remain
inspectable rather than silently disappearing.

## Verification Model

Future phases can verify impact analysis correctness through:

- golden fixture repositories with known entities and relationships
- deterministic snapshot comparison
- source-attribution completeness checks
- no-unattributed-claim checks
- relationship taxonomy conformance checks
- stale/superseded source handling checks
- conflict-preservation checks
- query reproducibility checks
- documentation-only scope checks
- no-decision/no-execution/no-mutation boundary checks
- cross-checks against actual test/document/contract mappings
- human review of sample reports for explanation quality

Verification should prove that impact analysis is reproducible and
conservative, not that it predicts all possible bugs.

## Query Model

Future Change Impact Analysis should support bounded query classes:

| Query class | Question |
| --- | --- |
| Changed file impact query | What may be affected by this path or diff? |
| Subsystem impact query | What may be affected by changing this subsystem? |
| Contract impact query | Which contracts constrain or are implicated by this change? |
| Test impact query | Which tests defend impacted entities or should be considered? |
| Documentation impact query | Which docs explain, reference, or may need updates for this change? |
| Advisory impact query | Which Advisory or Repository Skill surfaces reference this area? |
| Evidence impact query | Which evidence categories, providers, or candidates may be affected? |
| Historical lineage impact query | Which phases, reports, decisions, repairs, hardening, or releases matter? |
| Release impact query | Which release notes, tags, or release commitments may be implicated? |
| Governance impact query | Which lifecycle, report-trust, no-go, transition, or decision boundaries are implicated? |
| Unknown impact query | What impact could not be bounded or verified? |

Every query result should include sources, paths, limitations, and
non-decision disclaimers.

## Impact Report Model

A future structured Impact Report should contain:

1. report identity and schema version
2. repository revision and analysis scope
3. proposed or observed change
4. input Repository Knowledge snapshot
5. input Historical Memory snapshot
6. impacted entities
7. direct impacts
8. indirect impacts
9. historical impacts
10. contractual impacts
11. test impacts
12. documentation impacts
13. advisory impacts
14. evidence impacts
15. release impacts
16. lifecycle and governance impacts
17. blast radius classification
18. unknowns and unverifiable areas
19. conflicting, stale, and superseded impact evidence
20. required evidence candidates
21. source attribution
22. verification status
23. limitations
24. non-decision disclaimer

The report must state that it does not accept, reject, authorize,
execute, enforce, or mutate anything.

## Integration with Repository Knowledge

Change Impact Analysis consumes Repository Knowledge entities,
relationships, claims, sources, snapshots, and evidence links.

Repository Knowledge remains the semantic map. Change Impact Analysis is
a change-scoped projection over that map. Future implementations should
therefore reuse knowledge identity, source references, relationship
types, and snapshot versioning instead of creating a parallel impact
database with incompatible IDs.

## Integration with Historical Memory

Historical Memory provides introduction, modification, verification,
hardening, repair, release, supersession, correction, and lineage
context.

Change Impact Analysis should use historical lineage to:

- identify why an entity exists
- surface prior repairs and hardening
- show release inclusion
- detect superseded guidance
- preserve corrected history
- explain why a boundary is safety-sensitive

Historical impact must remain source-attributed and append-aware. A
repair phase does not erase the phase it repaired.

## Integration with Evidence

Impact claims can produce:

- evidence candidates
- source references for evidence
- limitations for evidence
- conflict/staleness annotations
- required-evidence lists

They do not automatically become Evidence. A future Evidence Provider or
Repository Skill may convert a verified impact claim into conforming
Evidence for Decision Evaluation. That conversion must preserve the
Evidence Framework's fields and constraints.

## Integration with Repository Skills

Future Repository Skills may expose impact inspection or query
capabilities as evidence-only skills. Such skills may:

- read Repository Knowledge snapshots
- read Historical Memory snapshots
- answer bounded impact queries
- produce evidence candidates or EvidenceCollections
- summarize sources and limitations

They must never decide, authorize, mutate, promote, notify, execute, or
bypass Decision Evaluation.

## Integration with Advisory

Advisory can use Change Impact Analysis for richer explanations and
recommendations.

Impact analysis can help Advisory Context Packages include:

- affected entities
- relevant contracts
- tests and validation commands
- documentation references
- historical lineage
- prior repairs and hardening
- unknowns and limitations
- required evidence

Advisory still receives bounded, provenance-preserving, prompt-safe
context. Repository-derived content remains untrusted unless explicitly
converted into deterministic PCAE summaries. Model output remains
probabilistic evidence at most.

## Integration with Decision Evaluation

Change Impact Analysis supports Decision Evaluation only indirectly.

Decision Evaluation may eventually consume Evidence that was derived
from verified impact claims. It may also consume structured context that
helps explain why more evidence is needed. The decision authority does
not move. Impact analysis never returns Accept, Reject, Quarantine, or
Requires Human Review.

## Read-Only and No-Execution Boundary

Change Impact Analysis is read-only.

Hard no-go conditions:

- no impact analysis engine implementation in this phase
- no impact extraction implementation
- no impact database
- no impact CLI
- no dependency graph implementation
- no historical memory extraction
- no repository knowledge extraction
- no advisory behavior changes
- no decision evaluation changes
- no evidence subsystem changes
- no repository skills changes
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
- no repository mutation by impact analysis
- no runtime plugin changes
- no repository state changes
- no test execution through impact analysis
- no automatic patch generation
- no automatic refactoring

Execution capability remains unavailable. Maximum runtime capability
remains `observe`.

## Future Emergence Paths

### 118D - Dependency Knowledge Graph Architecture

This document prepares 118D by defining impact paths and impact
relationships without implementing a dependency graph. 118D can define
how Repository Knowledge relationships are projected into a dependency
knowledge graph while preserving source attribution, determinism,
uncertainty, and read-only boundaries.

### 118E - Advisory Reasoning Expansion

Impact reports can become a bounded advisory input. 118E can define how
Advisory uses impact knowledge to ask better questions and produce
better evidence without gaining authority.

### Future Architectural Contract Mapping

Contract impact claims require a clearer map from source modules,
commands, tests, docs, and lifecycle artifacts to contract entities.
This phase names the need; it does not implement mapping.

### Future Repository Intelligence Reports

Impact reports can become one report type in Repository Intelligence:
structured, source-attributed, non-decision reports over repository
architecture.

### Future Safe Pre-Change Review

A future pre-change workflow may ask for an impact report before work
begins. That report would help humans and Advisory understand likely
scope and required evidence. It would still not authorize the change.

## Risks

- **False certainty.** Impact reports may look authoritative even when
  sources are incomplete. Mitigation: explicit uncertainty states,
  unknowns, limitations, and no-unattributed-claim checks.
- **Decision leakage.** Blast radius labels may be misread as verdicts.
  Mitigation: non-decision disclaimer and strict Decision Evaluation
  boundary.
- **Graph premature commitment.** Implementers may jump directly to a
  graph database. Mitigation: treat graph behavior as a projection over
  stable Repository Knowledge records.
- **Model inference creep.** Advisory or model summaries may be mistaken
  for source-attributed impact claims. Mitigation: source attribution
  and determinism requirements.
- **Stale historical sources.** Older docs or phase reports may be
  superseded. Mitigation: Historical Memory supersession/correction
  semantics.
- **Over-broad blast radius.** Conservative analysis may mark too much
  as impacted. Mitigation: path explanations, relationship types, and
  confidence/verification states.

## Open Questions

- What is the minimal relationship taxonomy 118D should freeze for
  dependency graph projections?
- Which repository artifacts should become first-class contract
  entities for architectural contract mapping?
- Should impact reports be persisted as Repository Artifacts, Evidence
  artifacts, or a new Repository Intelligence report class?
- What is the first bounded query worth implementing after the
  architecture is frozen: changed-file, contract, test, or governance
  impact?
- How should future impact analysis handle generated files or external
  dependencies if they appear in scope?
- What verification fixtures are sufficient to prove conservative,
  reproducible impact analysis without pretending to predict all bugs?

## Recommended Next Phase

118D - Dependency Knowledge Graph Architecture.

118D should remain architecture-only unless explicitly activated
otherwise. It should define how Repository Knowledge relationships can
be projected into an inspectable, source-attributed dependency knowledge
graph that supports impact paths without becoming an implementation,
execution mechanism, enforcement layer, or decision maker.
