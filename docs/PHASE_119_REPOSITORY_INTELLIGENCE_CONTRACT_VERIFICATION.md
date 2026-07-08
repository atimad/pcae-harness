# Phase 119B - Repository Intelligence Contract Verification

## Purpose

Phase 119B verifies the frozen Repository Intelligence contract from
Phase 119A. It asks whether the contract is internally consistent,
testable, future-enforceable, and suitable to constrain later Repository
Intelligence prototypes.

This phase verifies the contract, not a built system. There is no
Repository Intelligence implementation yet. This phase does not add a
verifier, CLI, automated tests, extractor, graph builder, impact engine,
Advisory behavior change, runtime behavior change, source code change,
test code change, execution path, or authority expansion.

## Verification Context

Track B asks whether PCAE can understand the repository itself without
granting new authority. Phases 118A through 118E defined the
Repository Intelligence architecture stack. Phase 118R reviewed the set
and found it coherent. Phase 119A froze the initial Repository
Intelligence contract.

Phase 119B makes the frozen contract operationally meaningful before any
prototype planning begins. It defines how future work can prove it
preserves the contract, what must be checked manually today, what could
later be checked automatically, and what would count as a violation.

## Contract Basis

This verification is based on:

- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_CONTRACT_FREEZE.md`
- `docs/PHASE_118_REPOSITORY_INTELLIGENCE_ARCHITECTURE_REVIEW.md`
- `docs/PHASE_118_REPOSITORY_KNOWLEDGE_ARCHITECTURE.md`
- `docs/PHASE_118_HISTORICAL_MEMORY_ARCHITECTURE.md`
- `docs/PHASE_118_CHANGE_IMPACT_ANALYSIS_ARCHITECTURE.md`
- `docs/PHASE_118_DEPENDENCY_KNOWLEDGE_GRAPH_ARCHITECTURE.md`
- `docs/PHASE_118_ADVISORY_REASONING_EXPANSION_ARCHITECTURE.md`

Supporting boundaries come from the Repository State Kernel, Evidence
Framework, Decision Framework, Repository Skills Architecture, Advisory
Repository Skills Architecture, Advisory Context Package Contract,
Advisory Runtime Contract, Runtime Context Architecture, Runtime
Introspection Architecture, Repository Transition Validator, phase
report model, release governance, transition validation, and v0.2
execution-readiness no-go gates.

## Verification Conclusion

The frozen Repository Intelligence contract is **verified and ready for
conceptual schema architecture / prototype planning**.

The contract is internally consistent, has mandatory invariants that can
be checked manually today, and defines enough source attribution,
determinism, uncertainty, snapshot, read-only, Advisory, Decision
Evaluation, and execution-boundary requirements to constrain future
Repository Intelligence work.

No repair is required before prototype planning. Minor future design
work remains: concrete schema names, artifact packaging, fixture shape,
and automated conformance gate placement should be defined during the
next conceptual schema phase or a later verification implementation
phase.

## Contract Invariant Inventory

The mandatory invariants frozen by 119A are:

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
- Repository Intelligence cannot make allow, block, escalate, or
  more-evidence decisions.
- Advisory remains non-authoritative.
- Decision Evaluation remains the only decision-making component.
- Execution remains unavailable until a separate governed execution
  track explicitly changes that boundary.

Future-facing but still contract-relevant expectations are:

- future artifacts should be versioned and snapshot-identifiable;
- future queries and reports should include source attribution,
  uncertainty, verification state, non-decision language, and
  no-execution language;
- future Repository Skills may expose read-only inspection but not own
  canonical truth;
- future Advisory Context Packages may carry Repository Intelligence
  context only as bounded, provenance-preserving, advisory-safe input.

## Invariant Verification Matrix

| Invariant | Contract source | Verification method | Manual today | Future automatic | Required evidence | Violation example | Preservation requirement |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Repository Intelligence is not Repository State | 119A definition and compatibility matrix | Check that RI artifacts describe architecture and cite state only as source/context | yes | yes | artifact type, source refs, no state-transition fields | RI report declares repository clean/valid as authority | State facts remain Repository State / Transition Validator owned |
| Repository Intelligence is not Evidence | Evidence relationship contract | Check that evidence links are bridges/candidates, not accepted Evidence records | yes | yes | evidence-link records and Evidence IDs when available | Knowledge claim is consumed as Evidence without Evidence shape | Conversion to Evidence must use Evidence contracts |
| Repository Intelligence is not Decision Evaluation | Decision boundary contract | Check for absence of allow/block/escalate/more-evidence verdict fields | yes | yes | report/query schema, language scan, handoff shape | Impact report says "allow commit" | RI may provide context only |
| Repository Intelligence is not Advisory authority | Advisory non-authority contract | Check Advisory outputs remain explanation/recommendation/handoff | yes | yes | Advisory report with disclaimer and source refs | Advisory approves push | Advisory remains non-authoritative |
| Repository Intelligence is not model memory | Determinism and Historical Memory contracts | Check claims cite repository artifacts, not conversation/model state | yes | partial | source refs and derivation rules | Historical claim sourced only to chat memory | Canonical truth must come from governed artifacts |
| Repository Intelligence is not execution planning | Execution boundary contract | Check no executable plan, command routing, patch application, or shell mediation | yes | yes | report text, schema fields, runtime inspection | Graph path becomes execution plan | RI may inspect and describe only |
| Repository Intelligence is not enforcement | Read-only and Decision boundary contracts | Check no policy enforcement or blocking semantics | yes | yes | artifact language and lifecycle hooks | Query result blocks phase completion | Enforcement remains outside RI |
| Repository Intelligence is not permission brokering | Contract invariants | Check no broker decision, approval, or permission field | yes | yes | schema/report inspection | RI grants shell permission | Permission Broker remains unchanged/unavailable |
| Repository Intelligence is not lifecycle mutation | Read-only contract | Check no lifecycle state writes, task moves, report promotion, notification dispatch | yes | yes | file diff, lifecycle logs | RI query updates task state | Lifecycle commands remain governed separately |
| Source-attributed or marked unknown | Source attribution contract | Check each claim/node/edge/report assertion has source ref or unknown/unverified/inferred marker | yes | yes | source refs, uncertainty fields | Graph edge lacks source and marker | Unsupported claims must not appear as known |
| Preserves uncertainty | Uncertainty contract | Check uncertainty labels are explicit and not collapsed | yes | yes | known/unknown/etc. fields | Query hides unknown areas | Unknowns remain visible |
| Preserves conflict | Uncertainty/conflict contract | Check conflicting claims are retained and labelled | yes | yes | conflicting source refs | Newer claim silently deletes older conflict | Conflict remains inspectable |
| Preserves supersession | Versioning/supersession contract | Check superseded items retain replacement links | yes | yes | supersession marker and source refs | Historical correction overwrites prior claim | Supersession is additive and traceable |
| Read-only | Read-only contract | Check file diff, allowed file scope, runtime behavior, no mutation code path | yes | yes | git diff, task contract, runtime inspect | Extractor writes repo files as side effect | RI artifacts inspect only |
| Cannot authorize mutation | Decision/read-only contracts | Check no authorization wording or permission fields | yes | yes | report text, schema fields | Report says mutation approved | Authorization remains outside RI |
| Cannot make decisions | Decision boundary contract | Check no TransitionResult/verdict semantics | yes | yes | report/query shape | Query returns block/allow | Decision Evaluation owns verdicts |
| Advisory remains non-authoritative | Advisory contract | Check recommendations are advisory-only and include uncertainty/source context | yes | yes | Advisory output, disclaimer, source refs | Advisory result overrides validator | Advisory can hand off context only |
| Decision Evaluation is sole decision maker | Decision boundary contract | Check future integration path routes decisions through Evidence and Decision Evaluation | yes | yes | integration doc or code review | Graph builder calls transition accept | Decision Evaluation remains sole decision path |
| Execution unavailable | Execution boundary contract | Check runtime inspect, no execution fields, no command mediation | yes | yes | `pcae runtime inspect`, report text | Query invokes shell/test runner | Execution stays unavailable |

## Source Attribution Verification

Future artifacts prove source attribution when:

- the cited source exists in the repository or in a canonical lifecycle
  artifact;
- the source is repository-owned, release-owned, phase-owned, evidence
  owned, skill-owned, or otherwise canonical;
- the source supports the specific claim, node, edge, lineage item,
  impact claim, advisory claim, query result, or report assertion;
- the support relationship is explicit, such as documents, imports,
  verifies, introduced_by, supersedes, constrains, tests, or references;
- unsupported claims are marked unknown, unverified, possible, inferred,
  or advisory-only;
- inferred claims name the deterministic derivation rule;
- model-inferred content is not canonical unless converted into governed
  repository artifacts and then processed by deterministic rules.

Manual verification today can inspect source references in documents and
future conceptual shapes. Future automatic verification could resolve
paths, commit identifiers, headings, line ranges, phase ids, report ids,
Evidence ids, and derivation-rule ids.

## Determinism Verification

Future artifacts prove determinism when:

- output is derived from repository artifacts and structured rules;
- the same repository snapshot, contract version, source set, and
  derivation-rule version produce the same canonical output;
- nondeterministic model output is excluded from canonical truth;
- heuristic or inferred relationships are labelled as inferred,
  possible, weak, or unverified as appropriate;
- the generation process is inspectable and names inputs, rules,
  versions, and limitations;
- rendering variation is separated from canonical record construction.

Manual verification today can check whether a proposed design identifies
inputs and rules. Future automatic verification could re-run a read-only
extractor on a fixture snapshot and compare canonical records.

## Read-Only Verification

Future artifacts prove read-only behavior when they show:

- no repository mutation;
- no lifecycle mutation;
- no Repository State mutation;
- no Evidence subsystem mutation except through governed Evidence paths;
- no Advisory state mutation;
- no Decision Evaluation state mutation;
- no command execution;
- no shell mediation;
- no backend invocation;
- no command routing;
- no authorization;
- no enforcement;
- no notification dispatch;
- no tag, branch, commit, push, release, report promotion, or task move
  side effect.

Manual verification today is by task scope, file diffs, phase reports,
and runtime inspection. Future automatic checks can assert that
Repository Intelligence tools run with read-only file access, emit only
inspection artifacts, and never call lifecycle or execution commands.

## Decision Boundary Verification

Future artifacts prove the Decision Evaluation boundary when:

- no allow, block, escalate, approve, reject, quarantine, waive, or
  more-evidence decision is emitted by Repository Intelligence;
- no approval is issued;
- no action is authorized;
- no commit, push, execution, lifecycle, report promotion, or mutation
  permission is implied;
- no Repository Intelligence artifact is shaped as a TransitionResult;
- any handoff to governance is context or evidence-candidate only;
- conforming Evidence remains the only input Decision Evaluation may
  evaluate;
- Decision Evaluation remains the only decision-making component.

Manual verification can inspect language and conceptual schemas. Future
automatic verification can reject verdict-like fields and reserved
decision vocabulary in Repository Intelligence report/query outputs.

## Advisory Non-Authority Verification

Future Advisory use of Repository Intelligence proves non-authority when:

- advisory outputs are explanations, recommendations, summaries, risks,
  gaps, limitations, reasoning traces, or handoffs;
- advisory outputs do not authorize action;
- advisory outputs do not override Decision Evaluation;
- advisory outputs cite sources, context packages, evidence links, and
  uncertainty states;
- advisory outputs include non-decision disclaimers when they discuss
  risk, impact, readiness, evidence gaps, or future action;
- advisory outputs include no-execution disclaimers when they mention
  execution, commands, tests, patches, refactors, commits, pushes, or
  lifecycle movement;
- advisory handoff packages identify context and evidence candidates
  without producing a verdict.

Advisory may become better grounded. It must not become more powerful.

## Uncertainty, Conflict, and Supersession Verification

Future artifacts must preserve:

- known;
- unknown;
- unverified;
- partially verified;
- weak;
- possible;
- inferred;
- stale;
- conflicting;
- superseded;
- advisory-only;
- decision-required.

Verification checks that every claim has a state, every inferred claim
names a rule, every stale item is marked stale, every conflict keeps all
source-backed sides, and every superseded item links to the superseding
source rather than disappearing.

Future systems may filter or summarize, but canonical records and
reports must not erase uncertainty, conflict, or supersession.

## Versioning and Snapshot Verification

Future Repository Intelligence snapshots should relate to:

- repository commit;
- branch or ref;
- release tag when applicable;
- phase id when applicable;
- phase completion artifact;
- canonical phase report;
- phase metadata;
- source artifact set;
- contract version;
- knowledge version;
- historical memory version;
- dependency graph snapshot;
- impact report;
- derivation-rule version;
- tool or extractor version when applicable;
- created timestamp;
- verification state;
- supersession relationship when applicable.

Manual verification today checks that future designs name these fields.
Future automatic verification can validate field presence and
cross-reference commit/tag/report/metadata existence.

## Query and Report Conformance Verification

Future Repository Intelligence queries and reports should be checked for:

- clear query subject or report subject;
- bounded scope;
- relevant entities and relationships;
- source attribution;
- relationship type validity;
- explicit graph direction when graph relationships are used;
- impact/dependency role separation;
- uncertainty preservation;
- conflict and supersession visibility;
- evidence links or evidence candidates without Evidence replacement;
- non-decision language;
- no-execution language;
- contract compliance statement.

No future query or report may authorize action, imply approval, mutate
state, trigger execution, run tests, apply patches, push commits, or
substitute for Decision Evaluation.

## Layer-Specific Verification

### Repository Knowledge

Verify that Repository Knowledge artifacts represent repository-derived
entities, relationships, claims, sources, evidence links, snapshots,
queries, and reports. They must remain deterministic,
source-attributed, inspectable, versioned, and read-only.

### Historical Memory

Verify that Historical Memory artifacts are temporal views inside
Repository Knowledge. Historical claims must cite source artifacts,
preserve corrections, retain stale/conflicting/superseded history, and
avoid model or conversation memory.

### Dependency Knowledge Graph

Verify that graph nodes and edges are graph-facing specializations of
Knowledge entities and relationships. Edges must be typed, directional,
source-attributed, uncertainty-labelled, and non-orchestrating.

### Change Impact Analysis

Verify that impact artifacts are change-scoped context over Repository
Knowledge, Historical Memory, and dependency relationships. They may
identify blast radius, unknowns, evidence gaps, and affected surfaces;
they may not decide safety or authorize execution.

### Advisory Reasoning Expansion

Verify that Advisory consumes bounded, provenance-preserving Repository
Intelligence context and produces explanation, recommendation,
uncertainty, evidence-gap, trace, or handoff output only.

### Evidence Relationship

Verify that Evidence links are bridge references or candidates. They
must not be treated as accepted Evidence unless they enter the Evidence
subsystem through its governed shape and validation path.

### Repository Skills Relationship

Verify that future Repository Skills expose read-only inspection/query
capabilities, produce EvidenceCollection-compatible observations when
needed, and do not decide, mutate, authorize, enforce, execute, or own
canonical truth.

### Decision Evaluation Boundary

Verify that all future integrations route actual decisions to Decision
Evaluation and the Repository Transition Validator. Repository
Intelligence may supply context or Evidence candidates only.

## Non-Conformance Examples

Future work violates the contract if it:

- builds a graph prototype that authorizes a change;
- emits an impact report that says execution is safe;
- produces an advisory recommendation that approves commit or push;
- records a Historical Memory claim with no source attribution and no
  unknown/unverified marker;
- marks a model-generated dependency as canonical without a governed
  source artifact and deterministic rule;
- implements a Repository Skill that mutates repository state while
  claiming to inspect;
- returns a query result that hides uncertainty, conflicts, stale
  claims, or superseded claims;
- creates a graph edge without direction or source;
- treats an evidence link as accepted Evidence;
- adds a verifier CLI, extractor, graph builder, impact engine, or
  advisory behavior under a verification-only phase;
- calls shell commands, test runners, backend invocations, or lifecycle
  transitions from Repository Intelligence reasoning;
- creates a report with approval, authorization, or TransitionResult
  language.

## Contract-Preserving Examples

Future work preserves the contract if it:

- defines a read-only conceptual schema with non-executable record
  shapes;
- produces a source-attributed graph snapshot that includes explicit
  node/edge sources, direction, uncertainty, and snapshot identity;
- emits an impact report that preserves unknowns, evidence gaps,
  non-decision disclaimers, and no-execution disclaimers;
- creates an Advisory handoff package that passes context and evidence
  candidates to Decision Evaluation without deciding;
- defines a Repository Skill that inspects Repository Intelligence
  artifacts and reports observations without mutating;
- creates a verification-only fixture that checks source attribution;
- labels model-assisted material as advisory-only or unverified unless
  converted into governed artifacts;
- preserves stale and superseded claims in canonical history while
  clearly identifying current context.

## Future Conformance Checklist

Before claiming Repository Intelligence compatibility, a future phase
should confirm:

- the work names which Repository Intelligence layer it touches;
- the work is source-attributed or marks unknown/unverified/inferred/
  advisory-only content;
- deterministic inputs and derivation rules are named;
- uncertainty, conflict, stale knowledge, and supersession are preserved;
- snapshots identify repository revision, source set, contract version,
  derivation rules, and tool versions when applicable;
- query/report outputs include non-decision and no-execution language
  when relevant;
- evidence links remain bridges or candidates;
- Repository Skills remain inspection/evidence surfaces only;
- Advisory remains explanatory and non-authoritative;
- Decision Evaluation remains the only decision maker;
- no execution, shell mediation, backend invocation, command routing,
  lifecycle mutation, repository mutation, enforcement, Permission
  Broker change, Telegram inbound, autonomous coding, automatic patch
  generation, or automatic refactoring is introduced.

## Risks

- Advisory authority creep: richer context may make recommendations look
  like approval.
- Impact-analysis-as-decision leakage: blast radius language may be
  mistaken for safety verdicts.
- Graph-as-orchestrator leakage: graph paths may be misused as runtime
  plans.
- Historical-memory-as-model-memory leakage: unsourced summaries may be
  mistaken for canonical history.
- Evidence duplication: evidence links may be treated as accepted
  Evidence.
- Source attribution weakness: coarse references may not prove claims.
- False certainty: unknowns or weak inferences may be hidden for a
  cleaner report.
- Hidden inference: model-assisted summaries may become canonical by
  presentation.
- Lifecycle mutation leakage: inspection tools may accidentally trigger
  report, task, phase, commit, or push side effects.
- Execution boundary erosion: future prototypes may run tests, commands,
  patches, or backends while claiming to inspect.

## Required Clarifications or Repairs

No repair is required before prototype planning.

Clarifications deferred to the next architecture/prototype-planning
steps are:

- concrete conceptual schema names and field groupings;
- artifact packaging for Repository Intelligence snapshots and reports;
- fixture design for future source-attribution verification;
- placement of future automated conformance gates;
- how Repository Intelligence context will be represented inside
  Advisory Context Packages without unbounded prompt content.

These are design follow-ups, not blockers.

## Prototype Readiness Assessment

PCAE is ready for a conceptual schema architecture phase. The frozen
contract is verified enough to constrain schemas, artifact models,
fixtures, and future read-only prototype planning.

PCAE is not yet ready for extraction, graph construction, impact engine
implementation, Advisory integration, CLI work, or automated validator
implementation. The next phase should define conceptual schema
architecture before any executable Repository Intelligence prototype.

## Recommended Next Phase

Recommended next phase: 119C - Repository Intelligence Conceptual Schema
Architecture.

Reason: after contract verification, PCAE should define conceptual
schemas for Repository Intelligence artifacts before implementing any
extractor, query engine, graph builder, or advisory integration.
