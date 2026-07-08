# Phase 119A - Repository Intelligence Contract Freeze

## Purpose

Phase 119A freezes the initial Repository Intelligence contract for PCAE.
The contract is derived from the Track B architecture set produced in
Phases 118A through 118R. It defines the stable conceptual and structural
rules that future Repository Intelligence work must obey.

This phase is contract-freeze-only. It does not implement Repository
Intelligence extraction, schemas, databases, query engines, Advisory
behavior, runtime behavior, execution, enforcement, or repository
mutation.

## Contract Freeze Context

Track B asks whether PCAE can understand the repository itself. Phases
118A through 118E defined the major Repository Intelligence architecture
surfaces, and Phase 118R reviewed those surfaces as one coherent
architecture set. Phase 118R concluded that the architecture is coherent
and ready for contract freeze with minor clarifications.

Phase 119A freezes the initial contract before any prototype or
implementation work. Future implementation phases may elaborate
concrete schemas or read-only extractors, but they must preserve this
contract unless a later governed contract revision explicitly changes it.

## Reviewed Architecture Basis

This contract is based on:

- Phase 118A - Repository Knowledge Architecture
  (`docs/PHASE_118_REPOSITORY_KNOWLEDGE_ARCHITECTURE.md`): defines
  Repository Knowledge as deterministic, inspectable, source-attributed,
  read-only architectural understanding.
- Phase 118B - Historical Memory Architecture
  (`docs/PHASE_118_HISTORICAL_MEMORY_ARCHITECTURE.md`): defines
  Historical Memory as the deterministic, source-attributed, versioned,
  temporal layer inside Repository Knowledge.
- Phase 118C - Change Impact Analysis Architecture
  (`docs/PHASE_118_CHANGE_IMPACT_ANALYSIS_ARCHITECTURE.md`): defines
  Change Impact Analysis as deterministic, source-attributed, read-only
  reasoning over Repository Knowledge, Historical Memory, and dependency
  relationships.
- Phase 118D - Dependency Knowledge Graph Architecture
  (`docs/PHASE_118_DEPENDENCY_KNOWLEDGE_GRAPH_ARCHITECTURE.md`): defines
  the Dependency Knowledge Graph as the deterministic, source-attributed,
  versioned relationship layer inside Repository Knowledge.
- Phase 118E - Advisory Reasoning Expansion Architecture
  (`docs/PHASE_118_ADVISORY_REASONING_EXPANSION_ARCHITECTURE.md`):
  defines how Advisory may consume Repository Intelligence context while
  remaining non-authoritative.
- Phase 118R - Repository Intelligence Architecture Review
  (`docs/PHASE_118_REPOSITORY_INTELLIGENCE_ARCHITECTURE_REVIEW.md`):
  concludes that the architecture set is coherent and ready for contract
  freeze with minor clarifications.

## Contract Status

This document is the initial Repository Intelligence contract freeze.
It freezes conceptual responsibilities, boundaries, invariants, source
attribution, uncertainty handling, verification expectations, and
allowed future emergence paths.

The contract is implementation-independent. Any future data model,
schema, CLI, report format, skill surface, extractor, graph artifact, or
Advisory context package extension must conform to this contract.

## Repository Intelligence Definition

Repository Intelligence is PCAE's deterministic, source-attributed,
inspectable, versioned, read-only understanding of repository
architecture, history, relationships, impacts, and advisory-relevant
context.

Repository Intelligence describes what the repository contains, how its
entities relate, how those relationships evolved, what a proposed or
observed change may affect, and what context Advisory may explain or
recommend from. It may produce structured context, evidence candidates,
source links, uncertainty statements, and non-decision reports.

Repository Intelligence is not Repository State, Evidence, Decision
Evaluation, Advisory authority, execution planning, model memory, or an
autonomous coding system.

## Repository Knowledge Contract

Repository Knowledge is the foundational architectural understanding
layer for Repository Intelligence.

It freezes these obligations:

- It represents repository-derived entities, relationships, claims,
  sources, evidence links, snapshots, queries, and reports.
- It is deterministic, source-attributed, inspectable, versioned, and
  read-only.
- It provides the conceptual container for Historical Memory and the
  Dependency Knowledge Graph.
- It may support Change Impact Analysis and Advisory context selection.
- It does not mutate Repository State, replace Evidence, decide,
  authorize, enforce, execute, or bypass governance.

## Historical Memory Contract

Historical Memory is the temporal layer inside Repository Knowledge.

It freezes these obligations:

- It represents how repository architecture, decisions, capabilities,
  contracts, repairs, hardening, releases, and subsystems evolved.
- It records historical subjects, events, claims, sources, evidence
  links, lineage, snapshots, and query results.
- It preserves corrections, conflicts, stale knowledge, and supersession
  rather than rewriting history.
- It may inform Change Impact Analysis and Advisory context.
- It is not model memory, conversation memory, enforcement, Decision
  Evaluation, or lifecycle mutation.

## Dependency Knowledge Graph Contract

The Dependency Knowledge Graph is the relationship layer inside
Repository Knowledge.

It freezes these obligations:

- It represents graph nodes, graph edges, dependency claims, sources,
  evidence links, dependency types, direction, strength, scope,
  verification state, dependency paths, graph views, graph snapshots,
  queries, and reports.
- Graph nodes and graph edges are graph-facing specializations of
  Repository Knowledge entities and relationships, not an independent
  authority silo.
- It may represent code, command, documentation, test, contract,
  evidence, advisory, historical, governance, lifecycle, release,
  capability, subsystem, and no-go boundary dependencies.
- Directionality must be explicit and inspectable.
- It is not a runtime orchestration graph, graph database implementation,
  command router, execution planner, permission broker, or decision
  maker.

## Change Impact Analysis Contract

Change Impact Analysis is read-only impact reasoning over Repository
Knowledge, Historical Memory, and dependency relationships.

It freezes these obligations:

- It represents impact subjects, impacted entities, surfaces,
  relationships, paths, claims, sources, evidence links, scope, blast
  radius, queries, and reports.
- It identifies what may be affected by a proposed or observed
  repository change.
- It may classify direct, indirect, historical, contractual, test,
  documentation, advisory, governance, unknown, and unverified impacts.
- It may produce evidence candidates or Advisory context.
- It does not predict by hidden model inference, decide, authorize,
  enforce, execute, plan autonomous work, run tests, generate patches, or
  mutate repository artifacts.

## Advisory Reasoning Expansion Contract

Advisory is a non-authoritative consumer of Repository Intelligence
context.

It freezes these obligations:

- Advisory may consume Repository Knowledge, Historical Memory, Change
  Impact Analysis, Dependency Knowledge Graph context, Evidence,
  Repository Skills outputs, Advisory Repository Skills outputs,
  Advisory Context Packages, and canonical lifecycle artifacts.
- Advisory may produce explanations, recommendations, risk summaries,
  uncertainty statements, evidence gaps, impact summaries, dependency
  summaries, lineage summaries, contract/test/documentation/governance
  context, reasoning traces, and handoff packages.
- Advisory recommendations must remain recommendations. They may say
  what should be reviewed or what evidence is missing; they may not say
  an action is allowed, approved, authorized, or safe to execute.
- Advisory may support Decision Evaluation only indirectly through
  structured context or evidence candidates.
- Advisory does not authorize, execute, enforce, mutate, override
  Decision Evaluation, or gain hidden model authority.

## Evidence Relationship Contract

Repository Intelligence may reference Evidence, expose evidence links,
and produce evidence candidates. It does not replace the Evidence
subsystem.

Evidence links must remain bridges from Repository Intelligence claims
to governed evidence artifacts or candidate observations. A Repository
Intelligence evidence link is conforming only when it identifies the
claim, the referenced artifact or observation, the support relationship,
the verification state, and the source attribution needed for inspection.

Evidence candidates produced by Repository Intelligence are not accepted
facts until the Evidence subsystem or the relevant governed validation
path treats them as evidence. Repository Intelligence must preserve
conflicting, stale, unverified, and superseded evidence links.

## Repository Skills Relationship Contract

Repository Skills may later expose Repository Intelligence inspection or
query capabilities. They do not own canonical Repository Intelligence
truth and do not gain decision authority.

Future Repository Skills may:

- inspect Repository Intelligence artifacts;
- answer read-only queries;
- produce EvidenceCollection-compatible observations;
- package source-attributed context for Advisory;
- verify contract conformance.

Future Repository Skills may not mutate repository state, execute
commands as part of Repository Intelligence reasoning, authorize
actions, enforce decisions, bypass Decision Evaluation, or convert
model-inferred content into canonical truth without governed artifacts.

## Decision Evaluation Boundary Contract

Decision Evaluation remains the only PCAE component responsible for
allow, block, escalate, or more-evidence decisions.

Repository Intelligence may provide context. Repository Intelligence may
identify evidence candidates. Repository Intelligence may describe
relationships, history, impact, uncertainty, and source support.

Repository Intelligence may not decide, authorize, approve, block,
reject, escalate, waive, override, or bypass a decision. It may not
present any report, query result, or advisory recommendation as a
TransitionResult or repository-state authority.

## Advisory Non-Authority Contract

Advisory may explain, summarize, recommend, identify uncertainty, and
package context for Decision Evaluation. Advisory may not authorize,
execute, enforce, mutate, or override Decision Evaluation.

Every future Advisory output that consumes Repository Intelligence must
be inspectable as advisory-only unless Decision Evaluation separately
acts on evidence and produces a governed decision.

## Source Attribution Contract

Every future Repository Intelligence claim, node, edge, lineage item,
impact claim, advisory claim, query result, report assertion, or
verification assertion must be source-attributed or explicitly marked as
unknown, unverified, inferred, or advisory-only.

Minimum source-reference fields are:

- source kind;
- repository path or artifact identifier;
- commit, tag, release, phase, or report identifier when available;
- line, section, heading, object id, or stable locator when available;
- extraction or derivation rule when applicable;
- observed timestamp or snapshot identifier when applicable;
- verification state;
- supersession or staleness marker when applicable.

Valid source categories include source files, tests, documentation,
architecture documents, contract documents, verification documents,
phase reports, phase-completion metadata, changelog entries,
`tasks/DONE.md`, task contracts, release notes, tags, commits, evidence
artifacts, Repository Skills, Advisory Skills, and canonical lifecycle
artifacts.

## Determinism Contract

Canonical Repository Intelligence must be derived from repository
artifacts and structured rules. Given the same repository snapshot,
contract version, and derivation rules, future canonical outputs must be
reproducible.

Model inference may assist drafting, summarization, or explanation, but
it is not canonical truth. Model-generated content becomes canonical
only if it is converted into governed repository artifacts and then
processed under deterministic Repository Intelligence rules.

Hidden model inference, implicit memory, conversation state, provider
selection, or runtime model confidence may not be used as canonical
Repository Intelligence authority.

## Uncertainty, Conflict, and Supersession Contract

Repository Intelligence must preserve uncertainty rather than smoothing
it into false certainty.

The shared vocabulary is:

- known: source-attributed and verified for the current scope;
- unknown: no adequate repository-derived source is available;
- unverified: a claim exists but has not passed the relevant
  verification path;
- partially verified: some required support exists but the claim is not
  fully verified;
- weak: the relationship or claim has limited source support;
- possible: the claim is source-suggested but not strong enough to treat
  as known;
- inferred: the claim is derived by a deterministic rule and must name
  that rule;
- stale: source support may no longer describe the current repository
  snapshot;
- conflicting: two or more source-attributed claims disagree;
- superseded: a later artifact replaces or revises the earlier claim;
- advisory-only: suitable for Advisory explanation or recommendation,
  not canonical decision authority;
- decision-required: Decision Evaluation must resolve the governance
  question before any allow/block/escalate meaning exists.

Conflicting, stale, and superseded claims must remain inspectable. Future
systems may rank, filter, or summarize them, but may not erase them from
the audit trail.

## Versioning and Snapshot Contract

Repository Intelligence snapshots must relate to repository commits,
releases, phase completion artifacts, canonical reports, metadata,
knowledge versions, historical memory versions, dependency graph
snapshots, and impact reports.

Minimum snapshot identity fields are:

- repository identifier;
- commit hash;
- branch or ref when applicable;
- release tag when applicable;
- phase id when applicable;
- source artifact set;
- contract version;
- derivation rule version;
- tool or extractor version when applicable;
- created timestamp;
- verification state;
- supersession relationship to earlier snapshots when applicable.

Snapshots may be conceptual in architecture and contract phases. Future
implementations must not make snapshot identity implicit.

## Verification Contract

Future Repository Intelligence outputs must be verifiable. Contract-level
verification means:

- the cited source exists;
- the cited source supports the claim;
- the relationship type is valid for the source and target entities;
- dependency direction is explicit;
- impact relationship and dependency relationship roles are not
  conflated;
- the claim is not stale unless marked stale;
- supersession is preserved;
- uncertainty is explicit;
- evidence links are bridge references, not replacement evidence;
- Advisory outputs remain advisory-only;
- Decision Evaluation remains the only decision-making component;
- execution boundary is preserved.

The first verification target after this contract freeze should be a
contract-verification phase that checks whether the frozen contract is
internally testable before prototype work begins.

## Query Contract

This contract permits future conceptual Repository Intelligence queries.
It does not implement queries.

Permitted query classes include:

- repository knowledge query;
- historical lineage query;
- dependency path query;
- reverse dependency query;
- impact query;
- advisory context query;
- source attribution query;
- uncertainty query;
- contract implication query;
- test relationship query;
- documentation relationship query;
- governance context query;
- stale or superseded knowledge query;
- conflicting claim query.

Every future query result must preserve source attribution, uncertainty,
verification state, and non-decision boundaries.

## Report Contract

This contract permits future conceptual Repository Intelligence reports.
It does not implement reports.

Future reports should include:

- query or subject;
- relevant entities;
- relevant relationships;
- source attribution;
- confidence or verification state;
- uncertainty;
- conflicts;
- supersession notes;
- evidence links or evidence candidates;
- required evidence when known;
- non-decision disclaimer;
- no-execution disclaimer.

Reports must not authorize action, execute commands, mutate repository
state, or substitute for Decision Evaluation.

## Read-Only Boundary Contract

Repository Intelligence is read-only.

It may inspect repository artifacts, describe architecture, expose
relationships, record lineage, identify impacts, summarize context,
identify uncertainty, identify evidence gaps, and produce
source-attributed reports.

It may not mutate files, repository state, lifecycle state, runtime
state, evidence state, advisory state, decision state, permissions,
notifications, releases, tags, branches, commits, or external systems.

## Execution Boundary Contract

Repository Intelligence does not enable execution.

It may not execute commands, mediate shell access, invoke backends,
route runtime commands, trigger tests, generate patches for application,
perform autonomous coding, automatically refactor, or control Telegram
inbound behavior.

Execution remains unavailable. Maximum runtime capability remains
observe until a separate governed execution track explicitly changes
that boundary.

## Non-Goals

Phase 119A does not implement:

- repository intelligence extraction;
- repository knowledge extraction;
- historical memory extraction;
- change impact analysis engine;
- dependency graph construction;
- graph query engine;
- advisory behavior changes;
- Advisory Runtime changes;
- Advisory Context Package changes;
- Evidence subsystem changes;
- Repository Skills changes;
- Decision Evaluation changes;
- runtime behavior changes;
- source code changes;
- test code changes;
- execution;
- shell mediation;
- Permission Broker changes;
- lifecycle redesign;
- REST;
- Dashboard;
- Web UI;
- Telegram inbound;
- provider selection;
- multi-model orchestration;
- autonomous coding;
- model capability expansion;
- repository mutation;
- runtime plugin changes;
- Repository State changes;
- test execution through Repository Intelligence;
- automatic patch generation;
- automatic refactoring.

## Contract Invariants

Future Repository Intelligence phases must preserve these invariants:

- Repository Intelligence is not Repository State.
- Repository Intelligence is not Evidence.
- Repository Intelligence is not Decision Evaluation.
- Repository Intelligence is not Advisory authority.
- Repository Intelligence is not model memory.
- Repository Intelligence is not execution planning.
- Repository Intelligence is not enforcement.
- Repository Intelligence is not permission brokering.
- Repository Intelligence is not lifecycle mutation.
- Repository Intelligence is source-attributed or explicitly marked
  unknown, unverified, inferred, or advisory-only.
- Repository Intelligence preserves uncertainty.
- Repository Intelligence preserves conflict.
- Repository Intelligence preserves supersession.
- Repository Intelligence is read-only.
- Repository Intelligence cannot authorize repository mutation.
- Repository Intelligence cannot make allow/block/escalate/more-evidence
  decisions.
- Advisory remains non-authoritative.
- Decision Evaluation remains the only decision-making component.
- Execution remains unavailable until a separate governed execution
  track explicitly changes that boundary.

## Contract Compatibility Matrix

| Repository Intelligence Layer | Repository State | Evidence | Repository Skills | Advisory | Decision Evaluation | Runtime | Lifecycle | Execution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Repository Knowledge | Describes architecture; does not define governed state | May link to evidence or candidates | May be inspected by future skills | Supplies bounded context | Supplies context only | No runtime change | No lifecycle mutation | No execution |
| Historical Memory | Records temporal architecture; not current state authority | May link historical claims to evidence | May support history queries | Supplies lineage context | Supplies context only | No runtime change | No lifecycle mutation | No execution |
| Dependency Knowledge Graph | Represents relationships; not state condition | May link edges/claims to evidence | May support graph inspection | Supplies dependency context | Supplies context only | No orchestration role | No lifecycle mutation | No execution |
| Change Impact Analysis | Describes possible impact; not state validity | May identify evidence gaps/candidates | May support impact queries | Supplies impact context | Supplies context only | No runtime action | No lifecycle mutation | No execution |
| Advisory Reasoning Expansion | Consumes state context only when provided | References evidence; does not replace it | Consumes skill outputs | Produces advisory-only output | Hands off context only | No runtime action | No lifecycle mutation | No execution |

## Future Phase Constraints

Future phases may:

- define conceptual schemas that conform to this contract;
- create read-only extractors;
- create inspection-only artifacts;
- create verification-only tests;
- create query prototypes;
- create report prototypes with non-decision and no-execution
  disclaimers;
- extend Repository Skills for read-only inspection;
- extend Advisory Context Packages with bounded, source-attributed
  Repository Intelligence context.

Future phases may not:

- execute;
- mutate repository artifacts or repository state;
- authorize, approve, block, or enforce;
- bypass Decision Evaluation;
- replace Evidence;
- replace Repository State;
- create model-inferred canonical truth;
- make graph structure into runtime orchestration;
- make impact analysis into governance decision-making;
- make Advisory more authoritative;
- change Permission Broker, lifecycle, runtime, REST, Dashboard, Web UI,
  Telegram inbound, provider orchestration, or autonomous coding
  behavior under this contract.

## Minor Clarifications from Phase 118R

Phase 118R identified minor clarifications required before or during
contract freeze. This contract addresses them as follows:

- Shared base primitives: claim, source, evidence link, snapshot, query,
  and report are shared base primitives with layer-specific
  specializations.
- Graph node and graph edge naming: graph nodes and edges are
  graph-facing specializations of Repository Knowledge entities and
  relationships.
- Source-reference schema: minimum source-reference fields are frozen in
  the Source Attribution Contract.
- Evidence-link bridge: evidence links are bridge references to Evidence
  artifacts or candidates, not replacement evidence.
- Uncertainty vocabulary: the shared known/unknown/unverified/partial/
  weak/possible/inferred/stale/conflicting/superseded/advisory-only/
  decision-required vocabulary is frozen.
- Snapshot identity: minimum snapshot fields are frozen in the Versioning
  and Snapshot Contract.
- Dependency edge vs impact relationship: dependency edges describe
  repository relationships; impact relationships describe change-scoped
  possible effects and may consume dependency edges.
- Advisory Context Package entry path: Advisory consumes Repository
  Intelligence only through bounded, source-attributed context packages
  or governed skill outputs.
- First verification target: the recommended next phase is contract
  verification before prototype work.
- Report disclaimers: future reports must include non-decision and
  no-execution disclaimers.

## Risks

- Future prototypes may accidentally encode implementation schemas as
  contract truth rather than contract-conforming representations.
- Graph work may drift into runtime orchestration unless the no-execution
  invariant is repeatedly checked.
- Impact analysis may be mistaken for a decision unless report
  disclaimers and Decision Evaluation boundaries remain explicit.
- Advisory may accumulate authority by presentation even when the formal
  contract forbids authority.
- Evidence links may be confused with Evidence subsystem acceptance.
- Source attribution may become too coarse unless minimum locator fields
  are verified early.

## Open Questions

- What concrete source-reference schema should a future implementation
  use while preserving this conceptual contract?
- Which repository artifacts should be included in the first read-only
  Repository Intelligence snapshot?
- What is the minimum useful contract verification suite before any
  extractor prototype?
- Should Repository Intelligence reports be emitted as lifecycle
  artifacts, repository-skill outputs, or both?
- How should stale and superseded Repository Intelligence be surfaced to
  users without obscuring current validated context?

## Recommended Next Phase

Recommended next phase: 119B - Repository Intelligence Contract
Verification.

Reason: before prototyping, PCAE should verify that the frozen contract
is internally testable and can be checked against future phases. This
preserves the pattern of architecture, contract freeze, verification,
then prototype.
