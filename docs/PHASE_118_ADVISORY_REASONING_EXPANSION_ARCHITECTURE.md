# Phase 118E - Advisory Reasoning Expansion Architecture

## Purpose

Phase 118E defines Advisory Reasoning Expansion for Track B:
Repository Intelligence.

Advisory Reasoning Expansion describes how PCAE Advisory should
eventually consume richer Repository Intelligence context from
Repository Knowledge, Historical Memory, Change Impact Analysis,
Dependency Knowledge Graph, Evidence, Repository Skills, Advisory
Repository Skills, Advisory Context Packages, and canonical lifecycle
artifacts.

The objective is better grounded advisory reasoning, not greater
advisory authority. Advisory may become more informed, more
source-attributed, more inspectable, and more useful to a human or to
Decision Evaluation as context. Advisory must not become more powerful.

This phase is architecture only. It does not implement advisory
behavior changes, Advisory Runtime changes, Advisory Context Package
changes, an advisory CLI, an advisory reasoning engine, model
integration, model selection, provider orchestration, Repository
Knowledge extraction, Historical Memory extraction, Change Impact
Analysis, Dependency Knowledge Graph construction, graph queries,
Evidence subsystem changes, Repository Skills changes, Decision
Evaluation changes, runtime behavior, lifecycle redesign, execution,
enforcement, Permission Broker behavior, REST, Dashboard, Web UI,
Telegram inbound, autonomous coding, automatic patch generation, or
automatic refactoring.

## Track B Context

Track B asks whether PCAE can understand the repository itself.

Phase 118A defined Repository Knowledge as deterministic, inspectable,
source-attributed, read-only architectural understanding of repository
entities, relationships, claims, sources, snapshots, and evidence links.

Phase 118B defined Historical Memory as the deterministic,
source-attributed, versioned temporal layer inside Repository Knowledge.

Phase 118C defined Change Impact Analysis as deterministic,
source-attributed, inspectable, read-only reasoning over Repository
Knowledge and Historical Memory to identify what may be affected by a
proposed or observed change.

Phase 118D defined Dependency Knowledge Graph as the deterministic,
source-attributed, inspectable, versioned relationship structure inside
Repository Knowledge.

Phase 118E answers the next Track B question: how should Advisory use
Repository Intelligence to reason better while remaining
non-authoritative?

Advisory Reasoning Expansion must emerge from the Repository
Intelligence foundation. It must not become autonomous planning,
execution authorization, enforcement, permission brokering, lifecycle
mutation, model orchestration, hidden reasoning authority, or a
replacement for Decision Evaluation.

## Relationship to 118A Repository Knowledge

Repository Knowledge is the broader deterministic architectural
understanding layer. Advisory Reasoning Expansion consumes Repository
Knowledge as structured input: entities, relationships, claims, sources,
evidence links, snapshots, views, and limitations.

Advisory may use Repository Knowledge to explain:

- which subsystem, capability, contract, document, test, phase, report,
  skill, evidence artifact, or no-go boundary a question concerns
- which sources support the architectural claims being considered
- which relationships connect the advisory question to repository
  artifacts
- which knowledge is known, unknown, stale, superseded, or conflicting

Advisory does not own Repository Knowledge. It does not extract,
normalize, validate, or canonize knowledge in this phase. It consumes
bounded, source-attributed knowledge context when such context exists in
future phases.

## Relationship to 118B Historical Memory

Historical Memory explains how repository architecture evolved.
Advisory Reasoning Expansion consumes historical lineage, phase history,
repairs, hardening, releases, supersession, correction events, and
historical limitations.

Advisory may use Historical Memory to say that a recommendation is
grounded in a phase that introduced a boundary, a later phase that
hardened it, a repair phase that corrected it, or a release phase that
published it. Advisory must preserve historical uncertainty: stale
reports, quarantined reports, superseded decisions, corrected claims,
and conflicting historical sources remain visible rather than being
flattened into one confident narrative.

Historical Memory informs Advisory. It does not authorize Advisory to
rewrite history or decide current transitions.

## Relationship to 118C Change Impact Analysis

Change Impact Analysis identifies what may be affected by a proposed or
observed change. Advisory Reasoning Expansion consumes impact subjects,
impacted entities, impact surfaces, impact paths, impact claims, blast
radius classifications, unknowns, source links, and required evidence.

Advisory may use impact analysis to explain:

- what appears in the likely blast radius
- which tests, documents, contracts, advisory surfaces, historical
  lineages, evidence candidates, lifecycle artifacts, or governance
  boundaries may need review
- which impact claims are direct, indirect, contractual, historical,
  test-related, documentation-related, advisory-related, governance-
  related, unknown, or unverified
- what evidence is missing before Decision Evaluation can reason safely

Impact analysis is structured context. Advisory can summarize and
recommend review based on it. Advisory cannot convert blast radius into
allow/block authority.

## Relationship to 118D Dependency Knowledge Graph

Dependency Knowledge Graph supplies graph-shaped relationship knowledge:
nodes, edges, dependency claims, sources, evidence links, dependency
types, direction, strength, scope, verification states, paths, views,
snapshots, queries, and reports.

Advisory may use graph context to explain which relationships were
followed, why a dependency path matters, what reverse dependencies
exist, which graph view was considered, and what uncertainty attaches
to a path or edge.

The graph remains a relationship layer inside Repository Knowledge.
Advisory does not build it, mutate it, execute over it, or treat graph
reachability as a decision.

## Definition of Advisory Reasoning Expansion

**Advisory Reasoning Expansion** is the architecture by which PCAE
Advisory may consume deterministic, source-attributed Repository
Intelligence context to produce better explanations, recommendations,
uncertainty statements, evidence-gap summaries, and structured handoff
context while remaining read-only and non-authoritative.

It answers questions such as:

- Which Repository Knowledge entities and relationships are relevant to
  this advisory question?
- Which historical phases, repairs, hardening events, releases, or
  supersessions explain this boundary?
- Which impact claims and dependency paths matter for this proposed or
  observed change?
- Which evidence exists, which evidence is missing, and which evidence
  is stale, conflicting, or superseded?
- Which recommendation can be made without deciding?
- Which context should be handed to Decision Evaluation as evidence
  candidates or structured context, without producing a verdict?

Advisory Reasoning Expansion is not a new decision pipeline. It is an
input, trace, and output architecture for non-authoritative reasoning.

## Advisory Reasoning Expansion vs Current Advisory

Current Advisory surfaces in PCAE include multiple distinct subsystems:

- read-only Advisory mode from the earlier advisory/shell-gate work
- Advisory Runtime, which produces runtime capability advisory results
- Advisory Repository Skills, which are model-backed, evidence-only
  Repository Skills
- Advisory Context Packages, which provide bounded, prompt-safe,
  provenance-preserving context for Advisory Repository Skills

The existing architecture already freezes the central boundary: advisory
outputs explain and recommend; they do not authorize, execute, mutate,
or decide.

Advisory Reasoning Expansion does not replace those contracts. It
defines how future Advisory can use Repository Intelligence context
across those advisory surfaces without increasing authority.

Current Advisory can reason from bounded runtime, repository-state, and
evidence context. Expanded Advisory may additionally reason from
Repository Knowledge, Historical Memory, Change Impact Analysis, and
Dependency Knowledge Graph context. The difference is input richness and
traceability, not power.

## Advisory Reasoning Expansion vs Decision Evaluation

Decision Evaluation remains the only component responsible for
allow/block/escalate/more-evidence decisions.

Advisory Reasoning Expansion may:

- explain repository context
- recommend review, tests, documents, contracts, or evidence to inspect
- summarize risks, unknowns, stale knowledge, conflicts, and
  supersessions
- produce advisory-only evidence candidates
- package structured context for Decision Evaluation

Advisory Reasoning Expansion must never:

- accept, reject, quarantine, escalate, or request human review as a
  decision
- declare a transition valid
- authorize commit, push, execution, lifecycle mutation, report
  promotion, artifact promotion, or notification
- bypass the Repository Transition Validator
- override Evidence confidence, freshness, determinism, or invariant
  evaluation

Decision Evaluation consumes Evidence and invariants. Advisory may
support that path only indirectly through structured context or
conforming Evidence.

## Advisory Reasoning Expansion vs Model Inference

Expanded Advisory must avoid hidden model inference authority.

A model may help produce advisory text or advisory evidence in future
Advisory Repository Skills, but model-produced content is not canonical
truth. It remains probabilistic/advisory by default, must preserve
limitations, and may never be sole authority for Accept.

Repository Intelligence context is canonical only when it is derived
from repository artifacts and represented as source-attributed
structured knowledge. Hidden model state, conversation memory, prompt
wording, model confidence, and AI-generated prose do not become sources
of truth.

Expanded Advisory may say "this recommendation is based on these
source-attributed claims and this uncertainty." It must not say "the
model believes this, therefore it is true."

## Advisory Reasoning Expansion vs Autonomous Planning

Advisory Reasoning Expansion is not autonomous planning.

Advisory may recommend what should be reviewed, what evidence is
missing, what risks exist, what tests may be relevant, what documents
may need review, what contracts may be implicated, which historical
phases matter, or what Decision Evaluation may need as input.

Advisory must not produce executable plans, patch plans, refactoring
plans, shell-command plans, commit/push plans, or lifecycle transition
plans with authority. A recommendation may be useful to a human or later
workflow, but it does not schedule, authorize, or execute work.

## Core Primitives

The clean primitive set for expanded Advisory is:

| Primitive | Meaning |
| --- | --- |
| Advisory Claim | A source-attributed, non-decision assertion Advisory makes about repository context, risk, relevance, uncertainty, or evidence gaps. |
| Advisory Explanation | Human-readable rendering of why an advisory claim or recommendation was produced, grounded in structured context. |
| Advisory Recommendation | Non-authoritative suggestion for human review, evidence collection, documentation review, test review, contract review, or Decision Evaluation input. |
| Advisory Context Item | One bounded piece of input context available to Advisory, such as a knowledge claim, impact claim, graph path, evidence item, lifecycle artifact, or historical event. |
| Advisory Context Package | A bounded, prompt-safe, provenance-preserving collection of advisory context items, instructions, no-go rules, limitations, and redaction/provenance metadata. |
| Advisory Evidence Link | A reference from an advisory claim, explanation, recommendation, or handoff to Evidence used, produced, confirmed, contradicted, or required. |
| Advisory Source | Repository artifact supporting an advisory claim: source file, test, doc, contract, report, metadata, changelog entry, task record, release note, tag, commit, skill artifact, evidence artifact, or lifecycle artifact. |
| Advisory Uncertainty | Explicit state describing known, unknown, unverified, partially verified, conflicting, stale, superseded, inferred, advisory-only, or decision-required context. |
| Advisory Limitation | Stated boundary of what Advisory did not inspect, could not verify, or must not decide. |
| Advisory Reasoning Trace | Inspectable record of context used, sources referenced, relationships followed, historical facts considered, impact claims considered, dependency paths considered, gaps remaining, uncertainty retained, and decisions not made. |
| Advisory Knowledge Reference | Link to Repository Knowledge entity, relationship, claim, source, snapshot, or view. |
| Advisory Historical Reference | Link to Historical Memory subject, event, claim, lineage, snapshot, or query result. |
| Advisory Impact Reference | Link to Change Impact Analysis subject, surface, entity, path, claim, blast radius, report, or unknown. |
| Advisory Graph Reference | Link to Dependency Knowledge Graph node, edge, claim, path, view, snapshot, or query result. |
| Advisory Handoff | Structured package of advisory context and evidence candidates passed toward Decision Evaluation without a verdict. |
| Advisory Report | Inspectable non-decision artifact summarizing advisory claims, explanations, recommendations, uncertainty, sources, evidence gaps, and handoff context. |

Terms such as Advisory Conflict, Advisory Source Attribution, and
Advisory Report Section are modeled as fields or classifications of
these primitives rather than separate top-level concepts.

## Advisory Input Model

Expanded Advisory may receive structured context from:

| Input source | Advisory use |
| --- | --- |
| Repository Knowledge | Architectural entities, relationships, claims, sources, evidence links, snapshots, and views. |
| Historical Memory | Phase lineage, repairs, hardening, releases, supersession, correction events, historical claims, and stale or conflicting history. |
| Change Impact Analysis | Impact subjects, impacted entities, surfaces, relationships, paths, blast radius, evidence gaps, and unknowns. |
| Dependency Knowledge Graph | Nodes, edges, dependency claims, dependency types, direction, reverse dependencies, paths, graph views, uncertainty, and snapshots. |
| Evidence | Evaluation-scoped observed facts, confidence, freshness, determinism, scope, references, limitations, and conflicts. |
| Repository Skills | Evidence-producing deterministic, reproducible-external, human-assisted, experimental, or advisory skill outputs. |
| Advisory Repository Skills | Model-produced evidence-only outputs, normalized through the existing advisory boundary. |
| Advisory Context Packages | Bounded, prompt-safe, provenance-preserving input packages with trust-class separation and limitations. |
| Canonical lifecycle artifacts | Project status, task contracts, task done records, changelog entries, phase reports, completion metadata, release notes, tags, commits, and no-go documents. |

Inputs must be labelled by source, trust class, determinism, freshness,
confidence, and limitations where available. Repository-derived content
remains untrusted input unless it is PCAE-authored instruction or
deterministic PCAE evidence explicitly labelled as such.

## Advisory Output Model

Expanded Advisory may produce these output types:

| Output type | Meaning |
| --- | --- |
| Explanation | Why a context item, claim, relationship, history, impact, or dependency matters. |
| Recommendation | What a human or future governance path may review, collect, or inspect. |
| Risk summary | Non-decision summary of relevant risks and their grounding. |
| Uncertainty statement | Explicit known/unknown/conflicting/stale/superseded/advisory-only/decision-required status. |
| Evidence gap | Missing evidence needed for stronger advisory or Decision Evaluation reasoning. |
| Impact summary | Summary of impact claims, blast radius, affected entities, and unknowns. |
| Dependency summary | Summary of dependency paths, reverse dependencies, graph views, and graph uncertainty. |
| Historical lineage summary | Summary of phases, decisions, repairs, hardening, releases, and supersession. |
| Contract implication summary | Explanation of contracts or no-go boundaries potentially implicated. |
| Test implication summary | Tests or validation commands that may defend the affected entity. |
| Documentation implication summary | Docs that explain, constrain, or may need review after a change. |
| Governance context summary | Relevant Repository State, lifecycle, report, push, notification, or no-go context. |
| Handoff to Decision Evaluation | Structured, non-verdict package of context and evidence candidates. |

Every output must preserve that it is advisory only. It may guide
attention; it may not authorize action.

## Advisory Reasoning Trace Model

An Advisory Reasoning Trace records:

- advisory question, scope, and context package identity
- context items used and excluded
- sources referenced
- relationships followed
- dependency paths and graph views considered
- historical subjects, events, claims, lineages, repairs, hardening, and
  releases considered
- impact subjects, surfaces, paths, claims, blast radius, and unknowns
  considered
- evidence items referenced
- evidence gaps identified
- conflicts, stale knowledge, superseded knowledge, and unverified
  claims preserved
- limitations and redactions
- recommendations produced
- what Advisory did not decide

The trace should be inspectable enough that a human can understand why a
recommendation was made without trusting a hidden chain of model
reasoning. A trace is not a model scratchpad. It is structured
provenance and decision-boundary metadata.

## Source Attribution Model

Every advisory claim, explanation, recommendation, reasoning trace, and
handoff item must link back to sources where support exists.

Source references may include:

- source files
- tests and validation commands
- documentation
- architecture documents
- contract documents
- verification documents
- phase reports
- phase-completion metadata
- changelog entries
- `tasks/DONE.md`
- active or done task contracts
- release notes
- tags
- commits
- evidence artifacts
- Repository Skills
- Advisory Repository Skills
- Advisory Context Packages
- canonical lifecycle artifacts
- no-go boundary documents

A source reference should identify the artifact path or ID, optional
section, optional line or field, repository revision when relevant,
source type, trust class, freshness, and limitations. Advisory may cite
summaries, but summaries do not replace source references.

## Uncertainty Model

Expanded Advisory must preserve uncertainty rather than hide it.

| Uncertainty state | Meaning |
| --- | --- |
| Known | Source-attributed context supports the claim within the stated scope. |
| Unknown | Required context is missing or unavailable. |
| Unverified | A claim exists but has not been verified by the relevant source or rule. |
| Partially verified | Some sources support the claim, but scope, freshness, or coverage is incomplete. |
| Conflicting | Sources disagree and both sides remain represented. |
| Stale | Context exists but is tied to an older revision, report, phase, or evidence collection. |
| Superseded | Later source-attributed context replaces or narrows an earlier claim. |
| Inferred | Derived through a structured relationship or rule but not directly observed. |
| Advisory-only | Produced by Advisory or model-backed review and not decision-authoritative. |
| Decision-required | Cannot be resolved by Advisory; needs Decision Evaluation or human/governance path. |

False certainty is avoided by requiring explicit uncertainty labels,
source attribution, limitations, and evidence gaps. Advisory must never
inflate confidence because a recommendation sounds plausible.

## Recommendation Model

Advisory may recommend without deciding.

A recommendation may say:

- review this subsystem, contract, document, test, phase, report, or
  skill boundary
- collect or refresh specific evidence
- inspect stale, conflicting, superseded, or unknown context
- consider these risks or limitations
- verify these dependency paths or impact claims
- review these historical phases, repairs, hardening items, or release
  records
- provide these structured inputs to Decision Evaluation

A recommendation must not say:

- an action is authorized, allowed, approved, or accepted
- execution should proceed
- commit or push is permitted
- a lifecycle transition is valid
- report promotion is safe
- enforcement is bypassed
- human approval is unnecessary
- Decision Evaluation will or should produce a specific verdict

Recommendation severity or confidence is attention guidance only. It is
not an enforcement signal and not a transition verdict.

## Handoff Model to Decision Evaluation

Advisory may package context for Decision Evaluation without making the
decision.

An Advisory Handoff should contain:

- advisory question and scope
- advisory claims and recommendations
- source references
- evidence links and evidence candidates
- Repository Knowledge references
- Historical Memory references
- Change Impact Analysis references
- Dependency Knowledge Graph references
- uncertainty states
- conflicts, stale knowledge, superseded knowledge, and limitations
- required evidence or evidence gaps
- explicit non-decision disclaimer

Decision Evaluation may later consume conforming Evidence derived from
this handoff. The handoff itself is not a verdict. It does not request
canonical promotion, approve a transition, or alter Repository State.

## Integration with Repository Knowledge

Advisory consumes Repository Knowledge as structured architectural
context. It may summarize entities, relationships, claims, sources,
snapshots, and views into an Advisory Context Package or Advisory
Report.

Repository Knowledge remains the semantic source. Advisory does not
become a knowledge extractor, catalog owner, or authority over knowledge
validity.

## Integration with Historical Memory

Advisory uses Historical Memory to understand lineage: which phases
introduced, modified, froze, repaired, hardened, verified, superseded,
released, or corrected a capability or boundary.

History-aware Advisory can explain why a boundary exists and which
prior decisions shaped it. It must also surface stale history,
quarantined reports, superseded claims, and corrections.

## Integration with Change Impact Analysis

Advisory uses Change Impact Analysis to reason about proposed or
observed changes. It may summarize direct, indirect, historical,
contractual, test, documentation, advisory, evidence, lifecycle,
release, governance, unknown, and unverified impacts.

Advisory may recommend review or evidence collection based on blast
radius. It must not treat blast radius as an allow/block decision.

## Integration with Dependency Knowledge Graph

Advisory uses graph paths, reverse dependencies, dependency types, edge
direction, graph views, snapshots, and uncertainty states to make its
explanations more traceable.

Graph-aware Advisory can say which path led from a changed entity to an
implicated contract, test, doc, phase, skill, evidence item, release, or
no-go boundary. It must not build the graph, mutate it, execute graph
queries with side effects, or use graph reachability as a verdict.

## Integration with Evidence

Evidence remains evaluation-scoped observed fact. Advisory may reference
Evidence, identify evidence gaps, or produce advisory/model-produced
Evidence through existing Advisory Repository Skills in future
implementation phases.

Advisory-produced evidence remains probabilistic/advisory by default,
must carry limitations, must be source-attributed where possible, and
must never be sole authority for Accept.

## Integration with Repository Skills

Repository Skills may later expose advisory-ready Repository
Intelligence context, such as knowledge inspection, historical lineage
inspection, impact summaries, graph path summaries, or evidence-gap
summaries.

Those skills remain evidence producers. They do not decide, authorize,
mutate, promote artifacts, send notifications, execute commands, or
bypass the Repository Transition Validator.

## Integration with Advisory Context Packages

Expanded Advisory should preserve the Advisory Context Package boundary:
bounded size, provenance, redaction, trust-class separation,
prompt-injection defense, limitations, artifact references, and no
unbounded repository dump.

Repository Intelligence context should enter a package as labelled
context items, not as hidden model memory or raw unrestricted repository
content. PCAE-authored instructions remain separate from deterministic
evidence and untrusted repository content.

## Integration with Decision Evaluation

Advisory can support decisions only indirectly through structured
context or conforming Evidence.

Decision Evaluation remains the only decision-making component. The
Repository Transition Validator remains the canonical transition gate.
Advisory cannot accept, reject, quarantine, escalate, promote, notify,
or authorize execution.

## Read-Only and No-Execution Boundary

Expanded Advisory is read-only. It must not:

- mutate repository files
- write canonical artifacts
- promote phase reports
- commit or push
- send notifications
- invoke shell commands as an advisory action
- mediate commands
- broker permissions
- authorize execution
- execute tests
- construct graphs
- run impact engines
- extract Repository Knowledge or Historical Memory
- select models or orchestrate providers
- alter runtime state, Repository State, Evidence, Repository Skills,
  Decision Evaluation, or lifecycle behavior

Execution capability remains unavailable. Runtime state remains
`Observed`. Maximum runtime capability remains `observe`.

## Future Emergence Paths

This architecture supports:

- future Advisory Context Package expansion for Repository Intelligence
  context
- future repository intelligence reports
- future safe pre-change review
- future advisory inspection commands
- future Decision Evaluation context handoff
- future contract-aware Advisory
- future graph-aware Advisory
- future history-aware Advisory

Each future path requires its own explicit phase, scope, contract, and
governance validation. No path is implemented or authorized here.

## Risks

- **Authority creep**: richer advisory explanations may be mistaken for
  decisions unless every output carries a non-decision boundary.
- **False certainty**: Advisory may overstate knowledge if uncertainty,
  stale sources, conflicts, or supersession are not preserved.
- **Prompt-injection exposure**: richer repository context increases the
  need for strict trust-class separation and untrusted-content labelling.
- **Context bloat**: Repository Intelligence context can become too large
  unless bounded packages and deterministic summaries are enforced.
- **Terminology collision**: PCAE has multiple advisory subsystems; future
  work must name which one is being changed.
- **Evidence confusion**: advisory context and evidence candidates must
  not be treated as conforming Evidence until converted through the
  Evidence Framework.

## Open Questions

- What concrete Advisory Context Package fields should carry Repository
  Knowledge, Historical Memory, impact, and graph references?
- Should Repository Intelligence advisory outputs use a new Advisory
  Report artifact or extend existing advisory result presentation?
- Which advisory question should be expanded first after architecture
  review: architecture consistency, safe pre-change review, or contract
  implication review?
- Which Repository Skills should expose read-only Repository
  Intelligence context first?
- What verification fixtures are needed to prove Advisory never confuses
  recommendation with decision?
- How should model-produced advisory reasoning traces be rendered
  without exposing hidden scratchpad or creating false provenance?

## Recommended Next Phase

118R - Repository Intelligence Architecture Review

118A through 118E now define the major Track B architecture surfaces:
Repository Knowledge, Historical Memory, Change Impact Analysis,
Dependency Knowledge Graph, and Advisory Reasoning Expansion. Before
freezing contracts or prototyping extraction/query behavior, PCAE
should review the full Repository Intelligence architecture for
coherence, terminology consistency, authority boundaries, source
attribution, uncertainty handling, and no-go preservation.
