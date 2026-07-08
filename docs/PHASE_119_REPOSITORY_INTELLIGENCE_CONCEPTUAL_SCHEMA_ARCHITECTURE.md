# Phase 119C - Repository Intelligence Conceptual Schema Architecture

## Purpose

Phase 119C defines the conceptual schema architecture for future
Repository Intelligence artifacts. It describes the artifact families,
conceptual fields, relationships, boundaries, and invariants that later
Repository Intelligence prototypes should produce, inspect, verify, and
consume.

This phase is architecture only. It creates no executable schema, JSON
Schema, Pydantic model, dataclass, validator, contract verifier, CLI,
test, extractor, graph builder, impact engine, Advisory behavior,
runtime behavior, execution path, or repository mutation.

## Track B Context

Track B asks whether PCAE can understand the repository itself.
Phases 118A through 118E defined the initial Repository Intelligence
architecture stack. Phase 118R reviewed the stack and found it coherent.
Phase 119A froze the Repository Intelligence contract. Phase 119B
verified that contract as internally consistent, testable,
future-enforceable, and ready to constrain conceptual schema
architecture.

Phase 119C now defines the conceptual artifact shapes needed before any
prototype. It preserves the architecture -> contract -> verification ->
conceptual schema sequence.

## Contract Basis

This architecture is based on:

- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_CONTRACT_FREEZE.md`
- `docs/PHASE_119_REPOSITORY_INTELLIGENCE_CONTRACT_VERIFICATION.md`
- `docs/PHASE_118_REPOSITORY_INTELLIGENCE_ARCHITECTURE_REVIEW.md`
- `docs/PHASE_118_REPOSITORY_KNOWLEDGE_ARCHITECTURE.md`
- `docs/PHASE_118_HISTORICAL_MEMORY_ARCHITECTURE.md`
- `docs/PHASE_118_CHANGE_IMPACT_ANALYSIS_ARCHITECTURE.md`
- `docs/PHASE_118_DEPENDENCY_KNOWLEDGE_GRAPH_ARCHITECTURE.md`
- `docs/PHASE_118_ADVISORY_REASONING_EXPANSION_ARCHITECTURE.md`

Supporting boundaries remain Repository State, Evidence, Decision
Evaluation, Repository Skills, Advisory Repository Skills, Advisory
Context Packages, Advisory Runtime, Runtime Context, Runtime Inspect,
canonical lifecycle artifacts, phase reports, release governance,
transition validation, and v0.2 no-go boundaries.

## Definition of Repository Intelligence Artifact

A Repository Intelligence artifact is a read-only, source-attributed,
inspectable, versioned record or report that describes repository
architecture, history, relationships, impact context, Advisory context,
query results, or contract conformance under the Repository Intelligence
contract.

An artifact may summarize or package Repository Intelligence, but it
does not own Repository State, replace Evidence, decide, authorize,
enforce, execute, mutate, or expand Advisory authority.

## Definition of Conceptual Schema

A conceptual schema is an architectural description of an artifact
family: its purpose, conceptual fields, field meanings, relationships,
invariants, and boundary obligations. It is independent of programming
language, storage format, serialization format, validation library, and
runtime implementation.

Conceptual schemas are useful because they let PCAE discuss future
artifact shapes before freezing executable contracts or writing code.

## Conceptual Schema vs Executable Schema

Conceptual schemas are architectural descriptions. Executable schemas
are future implementation artifacts such as JSON Schema files, Pydantic
models, dataclasses, database definitions, validators, or CLI-enforced
contracts.

This phase creates only conceptual schemas. It does not create JSON
Schema, Pydantic models, dataclasses, validators, extractors, CLIs,
tests, or executable conformance logic.

Future executable schemas must not treat this document as generated
code. They must first pass through a governed schema contract freeze and
verification path.

## Common Artifact Envelope

Every future Repository Intelligence artifact should conceptually carry
a common envelope. The envelope is not an executable schema. It defines
the common information needed for inspection, verification, versioning,
and boundary preservation.

Conceptual common fields:

| Field | Purpose |
| --- | --- |
| `artifact_id` | Stable identifier for the artifact instance. |
| `artifact_type` | Artifact family, such as knowledge snapshot or impact report. |
| `schema_family` | Conceptual schema family the artifact belongs to. |
| `schema_concept_version` | Conceptual schema version, not implementation schema version. |
| `repository_root_identity` | Identity of the repository root or repository namespace. |
| `repository_commit` | Commit the artifact describes. |
| `repository_branch` | Branch or ref context when available. |
| `release_context` | Release/tag context when available. |
| `phase_context` | Related PCAE phase, task, report, or lifecycle context. |
| `generated_at_utc` | Artifact creation timestamp. |
| `derivation_method` | Human-readable derivation method or rule family. |
| `source_attribution` | Source Attribution Records supporting the artifact. |
| `evidence_links` | Evidence Link Records or evidence candidates. |
| `verification_state` | Overall verification status. |
| `uncertainty_state` | Known/unknown/unverified/etc. summary. |
| `conflict_state` | Conflict presence and summary. |
| `supersession_state` | Supersession and staleness summary. |
| `read_only_boundary` | Statement that the artifact is descriptive only. |
| `decision_boundary` | Statement that the artifact is not Decision Evaluation. |
| `execution_boundary` | Statement that the artifact does not enable execution. |
| `producer` | Human, phase, tool, skill, or future extractor identity. |
| `non_decision_disclaimer` | Explicit non-decision language. |
| `no_execution_disclaimer` | Explicit no-execution language. |

## Repository Intelligence Package Conceptual Schema

A Repository Intelligence Package is the top-level bundle that may later
group related Repository Intelligence artifacts for one repository
snapshot or analysis context.

Conceptual fields:

- common artifact envelope;
- package subject;
- package scope;
- Repository Knowledge Snapshot reference;
- Historical Memory Snapshot reference;
- Dependency Knowledge Graph Snapshot reference;
- Change Impact Report references;
- Advisory Intelligence Context Package references;
- Contract Conformance Record references;
- package metadata;
- package source set;
- package verification state;
- package limitations;
- package non-decision and no-execution disclaimers.

The package is a container and index. It does not merge component
authority, decide, execute, mutate, or replace the underlying artifacts.

## Repository Knowledge Snapshot Conceptual Schema

A Repository Knowledge Snapshot describes what the repository contains
and how architectural entities relate at a repository snapshot.

Conceptual fields:

- common artifact envelope;
- architectural entities;
- capabilities;
- subsystems;
- commands and CLI surfaces;
- contracts;
- documentation references;
- test references;
- ownership markers;
- knowledge relationships;
- knowledge claims;
- knowledge sources;
- evidence links;
- unknowns;
- verification state;
- uncertainty/conflict/supersession summary;
- snapshot limitations.

This artifact is the foundation for Repository Intelligence. It is not
Repository State and does not decide whether the repository is valid.

## Historical Memory Snapshot Conceptual Schema

A Historical Memory Snapshot describes how repository architecture,
contracts, capabilities, decisions, repairs, hardening, and releases
evolved over time.

Conceptual fields:

- common artifact envelope;
- historical subjects;
- phase events;
- release events;
- decision events;
- repair events;
- hardening events;
- contract freeze events;
- lifecycle/report events;
- lineage records;
- correction records;
- supersession records;
- historical claims;
- historical sources;
- evidence links;
- stale/conflicting history;
- verification state;
- limitations.

Historical Memory is temporal Repository Knowledge. It is not model
memory, conversation memory, or rewritten history.

## Dependency Knowledge Graph Snapshot Conceptual Schema

A Dependency Knowledge Graph Snapshot represents repository
relationships as a graph view inside Repository Knowledge.

Conceptual fields:

- common artifact envelope;
- graph subject and scope;
- nodes;
- edges;
- dependency claims;
- edge direction;
- dependency type;
- dependency strength;
- dependency scope;
- dependency paths;
- graph views;
- graph snapshot metadata;
- source attribution;
- evidence links;
- uncertainty/conflict/supersession state;
- verification state;
- graph limitations.

Graph nodes and edges are graph-facing specializations of Repository
Knowledge entities and relationships. The graph is not runtime
orchestration, command routing, execution planning, or Decision
Evaluation.

## Change Impact Report Conceptual Schema

A Change Impact Report describes what may be affected by a proposed or
observed repository change.

Conceptual fields:

- common artifact envelope;
- proposed or observed change subject;
- impact scope;
- impact subjects;
- impacted entities;
- impact surfaces;
- impact relationships;
- impact paths;
- blast radius;
- direct impacts;
- indirect impacts;
- historical impacts;
- contract impacts;
- test impacts;
- documentation impacts;
- advisory impacts;
- governance impacts;
- unknown impacts;
- required evidence;
- source attribution;
- evidence links;
- uncertainty/conflict/supersession state;
- verification state;
- non-decision disclaimer;
- no-execution disclaimer.

An impact report provides context only. It does not predict by hidden
model inference, authorize change, decide safety, run tests, generate
patches, or execute.

## Advisory Intelligence Context Package Conceptual Schema

An Advisory Intelligence Context Package is a bounded,
provenance-preserving package of Repository Intelligence context for
Advisory use.

Conceptual fields:

- common artifact envelope;
- advisory subject;
- context scope and budget;
- context inputs;
- Repository Knowledge references;
- Historical Memory references;
- Dependency Knowledge Graph references;
- Change Impact Report references;
- evidence links;
- advisory claims;
- advisory explanations;
- advisory recommendations;
- uncertainty statements;
- evidence gaps;
- limitations;
- handoff to Decision Evaluation;
- non-authority disclaimer;
- no-execution disclaimer;
- trust-class and provenance notes.

Advisory may become more informed through this package. Advisory must
not become more authoritative.

## Source Attribution Record Conceptual Schema

A Source Attribution Record links a Repository Intelligence assertion to
its supporting repository or lifecycle source.

Conceptual fields:

- `source_id`;
- `source_type`;
- `source_path`;
- `source_locator`, such as line, section, heading, object id, phase id,
  report id, tag, commit, or evidence id;
- `source_digest_or_commit_reference`;
- `source_claim_relationship`, such as supports, contradicts,
  supersedes, documents, constrains, verifies, references, introduces,
  modifies, or hardens;
- `source_support_level`;
- `source_verification_state`;
- `source_staleness_state`;
- source limitations.

Source Attribution Records are required for canonical claims unless the
claim is explicitly marked unknown, unverified, inferred, or
advisory-only.

## Evidence Link Record Conceptual Schema

An Evidence Link Record bridges Repository Intelligence claims to
Evidence artifacts or evidence candidates. It is not itself accepted
Evidence unless a future governed Evidence path admits it.

Conceptual fields:

- `evidence_id`;
- `evidence_type`;
- `evidence_source`;
- `supported_claim`;
- `support_strength`;
- `verification_state`;
- `limitations`;
- `related_artifacts`;
- `candidate_or_accepted_state`;
- `decision_evaluation_eligibility`.

Evidence links must preserve the boundary between Repository
Intelligence context and the Evidence subsystem.

## Uncertainty / Verification State Conceptual Schema

Uncertainty and verification state records describe what is known,
unknown, verified, inferred, stale, or decision-required.

Conceptual values:

- known;
- unknown;
- unverified;
- partially verified;
- weak;
- possible;
- inferred;
- advisory-only;
- decision-required;
- verified;
- invalid;
- stale;
- superseded;
- conflicting.

Conceptual fields:

- state value;
- reason;
- supporting sources;
- verification method;
- limitations;
- required evidence;
- reviewer or producer when applicable;
- timestamp or snapshot context.

These states prevent false certainty and must remain visible in future
query/report artifacts.

## Conflict / Supersession Record Conceptual Schema

A Conflict / Supersession Record preserves disagreement, staleness, and
replacement history.

Conceptual fields:

- `conflict_id`;
- conflicting claims;
- conflict sources;
- conflict type;
- resolution state;
- superseded artifact or claim;
- `superseded_by`;
- supersession reason;
- preserved history;
- verification state;
- current-context note;
- limitations.

Conflict and supersession are not cleanup chores. They are part of the
inspectable Repository Intelligence record.

## Query Result Conceptual Schema

A Query Result represents a read-only answer to a Repository
Intelligence question.

Conceptual fields:

- common artifact envelope;
- `query_id`;
- query type;
- query subject;
- query scope;
- query inputs;
- result entities;
- result relationships;
- source attribution;
- uncertainty;
- conflicts;
- supersession;
- evidence links;
- result limitations;
- non-decision disclaimer;
- no-execution disclaimer.

Query results may describe and summarize. They may not decide, mutate,
authorize, enforce, or execute.

## Contract Conformance Record Conceptual Schema

A Contract Conformance Record describes whether a future Repository
Intelligence artifact conforms to the 119A/119B contract expectations.

Conceptual fields:

- common artifact envelope;
- artifact under review;
- contract version;
- invariant checks;
- source attribution check;
- determinism check;
- read-only check;
- decision boundary check;
- Advisory non-authority check;
- execution boundary check;
- uncertainty preservation check;
- conflict preservation check;
- supersession preservation check;
- conformance status;
- violations;
- limitations;
- reviewer or verifier identity.

This record is conceptual. 119C does not implement a verifier or
automated conformance logic.

## Conceptual Schema Relationships

Repository Intelligence Package is the top-level bundle. It may contain
or reference Repository Knowledge Snapshots, Historical Memory
Snapshots, Dependency Knowledge Graph Snapshots, Change Impact Reports,
Advisory Intelligence Context Packages, Query Results, and Contract
Conformance Records.

Repository Knowledge Snapshot is foundational. Historical Memory and
Dependency Knowledge Graph are specialized layers inside Repository
Knowledge. Change Impact Reports consume Repository Knowledge,
Historical Memory, and dependency relationships for change-scoped
context. Advisory Intelligence Context Packages consume bounded
Repository Intelligence context for non-authoritative Advisory use.
Query Results expose read-only views over these artifacts. Contract
Conformance Records inspect whether artifacts preserve the contract.

Source Attribution Records, Evidence Link Records, Uncertainty /
Verification State records, and Conflict / Supersession Records are
cross-cutting records used by all artifact families.

## Contract Invariant Mapping

| Contract invariant | Conceptual schema representation |
| --- | --- |
| RI is not Repository State | Artifact envelope marks descriptive role; snapshots cite state as source only. |
| RI is not Evidence | Evidence Link Records are bridge/candidate records, not accepted Evidence. |
| RI is not Decision Evaluation | Non-decision disclaimer and decision boundary fields are required. |
| RI is not Advisory authority | Advisory packages include non-authority disclaimers and handoff-only semantics. |
| RI is not model memory | Source Attribution Records require governed sources or explicit unknown/unverified/advisory-only state. |
| RI is not execution planning | Execution boundary fields and no-execution disclaimers are required. |
| RI is not enforcement | No artifact family has enforcement or blocking authority. |
| RI is read-only | Common envelope carries read-only boundary; future artifacts must not imply side effects. |
| RI preserves uncertainty | Uncertainty / Verification State records are cross-cutting. |
| RI preserves conflict | Conflict records preserve conflicting claims and sources. |
| RI preserves supersession | Supersession records retain replacement history. |
| Decision Evaluation is sole decision maker | Conformance records and reports check absence of verdict semantics. |
| Execution remains unavailable | Every artifact family carries no-execution boundary representation. |

## Determinism and Derivation Model

Future artifacts should describe derivation without implementing
derivation in the schema itself.

Conceptual derivation fields include:

- input artifact set;
- repository commit/ref;
- source set;
- derivation method;
- derivation rule family;
- tool or producer identity when applicable;
- concept version;
- known nondeterminism exclusions;
- inferred/heuristic relationship markers;
- limitations.

The conceptual schema records how an artifact claims to have been
derived. It does not execute extraction or prove determinism by itself.

## Versioning and Snapshot Model

Conceptual versioning should distinguish:

- schema concept version;
- future executable schema version;
- repository commit;
- repository branch/ref;
- release tag;
- phase id;
- phase completion artifact;
- canonical report id;
- artifact snapshot id;
- knowledge snapshot id;
- historical memory snapshot id;
- graph snapshot id;
- impact report id;
- conformance record id;
- producer/tool version when applicable.

Version fields make future artifacts inspectable and comparable without
turning this architecture into an implementation.

## Read-Only and No-Execution Boundary Representation

Every future artifact should conceptually represent:

- no repository mutation;
- no lifecycle mutation;
- no Repository State mutation;
- no Evidence replacement;
- no authorization;
- no enforcement;
- no Decision Evaluation replacement;
- no Advisory authority expansion;
- no execution;
- no shell mediation;
- no backend invocation;
- no command routing;
- no test execution through Repository Intelligence;
- no automatic patch generation;
- no automatic refactoring.

These fields are not decorative. They are required contract-facing
signals for future inspection and conformance checking.

## Non-Normative Examples

Non-normative conceptual example. Not an executable schema.

```text
artifact_type: repository_knowledge_snapshot
repository_commit: <commit>
derivation_method: repository-derived rules
entities: [source module, command, contract document]
source_attribution: [source path + section + commit]
uncertainty_state: known / unknown / unverified
non_decision_disclaimer: descriptive only
no_execution_disclaimer: does not execute
```

Non-normative conceptual example. Not an executable schema.

```text
artifact_type: change_impact_report
change_subject: proposed documentation contract update
blast_radius: documentation + governance context
required_evidence: source references and contract review
decision_boundary: Decision Evaluation remains sole decision maker
execution_boundary: no commands or tests are run by this report
```

## Future Implementation Constraints

Future implementation may:

- create JSON Schema or Python models only after schema contract
  approval;
- create validators only after schema contract freeze;
- create read-only artifacts;
- create tests for schema conformance;
- create read-only extractors after prototype planning;
- create conceptual-to-executable mapping documents.

Future implementation may not:

- execute;
- mutate;
- authorize;
- enforce;
- bypass Decision Evaluation;
- replace Evidence;
- replace Repository State;
- create model-inferred canonical truth;
- turn conceptual schemas into runtime orchestration;
- expand Advisory authority;
- introduce Telegram inbound, REST, Dashboard, Web UI, provider
  orchestration, autonomous coding, automatic patch generation, or
  automatic refactoring under this schema architecture.

## Risks

- Conceptual fields could be mistaken for executable schemas.
- Future schema implementation could overfit to illustrative examples.
- Artifact package terminology could imply new authority rather than
  bundling.
- Evidence links could be mistaken for accepted Evidence.
- Query results could be written with decision-like language.
- Advisory context packages could grow unbounded without trust-class and
  provenance controls.
- Graph snapshots could drift toward orchestration.
- Conformance records could be mistaken for Decision Evaluation.

## Open Questions

- Which artifact family should receive the first executable schema
  contract freeze?
- Should Repository Intelligence Package be materialized before
  individual snapshot artifacts, or only after individual artifacts
  exist?
- What minimum fixture set is needed to exercise source attribution,
  uncertainty, conflict, and supersession?
- How should future Advisory Context Package sections carry Repository
  Intelligence references without unbounded prompt content?
- Which conformance checks should remain manual until an extractor or
  schema implementation exists?

## Recommended Next Phase

Recommended next phase: 119D - Repository Intelligence Conceptual Schema
Review.

Reason: before freezing artifact contracts or planning prototypes, PCAE
should review whether these conceptual schema families are coherent,
complete, and aligned with the 119A/119B contract.
