# Phase 121A - Repository Intelligence Query Layer Architecture

## 1. Purpose

Phase 121A defines the architecture for a future Repository
Intelligence Query Layer: a deterministic, read-only layer for
consuming existing Repository Intelligence artifacts.

Track 120 proved that PCAE can generate a narrow, deterministic,
source-attributed Repository Knowledge Snapshot without execution,
runtime mutation, Advisory authority, Decision Evaluation replacement,
Repository State authority, Evidence replacement, AI inference, or
network access. Track 121 begins the next architectural chapter:
moving from **generated knowledge** to **deterministic knowledge
consumption**.

The Query Layer exists because generated Repository Intelligence is not
useful only as a persisted artifact. Later PCAE subsystems and humans
will need governed ways to ask bounded questions about already
generated artifacts. Without a dedicated query architecture, those
consumers would be tempted to rescan the repository, re-infer facts,
reinterpret artifact contents, or couple directly to artifact internals.
The Query Layer prevents that drift by defining a read-only,
deterministic consumption boundary.

121A is architecture only. It implements no query engine, parser, CLI,
API, validator, model, runtime plugin, repository scanner, generator,
graph traversal, Advisory integration, execution planning, or
execution capability.

## 2. Track 121 Purpose

Track 121's purpose is to define and later prototype governed access
to existing Repository Intelligence artifacts. It is not a second
generation track.

Track 120 answered: "Can PCAE produce a schema-conformant Repository
Knowledge Snapshot from governed sources while preserving read-only,
observe-only, deterministic boundaries?"

Track 121 asks: "How should PCAE read and return information from
already generated Repository Intelligence artifacts without changing,
expanding, reinterpreting, or replacing those artifacts?"

The architectural transition is:

1. Track 119 supplied executable artifact schemas and shared components.
2. Track 120 produced and verified the first artifact instance family,
   Repository Knowledge Snapshot.
3. Track 121 defines deterministic consumption of those existing
   artifacts.

The query layer must therefore treat Repository Intelligence artifacts
as the complete input surface. It may select from them, filter them,
and format bounded results. It may not derive new Repository
Intelligence or read the repository directly to fill gaps.

## 3. Relationship to Previous Tracks

### 3.1 Phase 119 Executable Schemas

Phase 119 defines the schema contract line that any future query
outputs must respect. In particular:

- `query_result.schema.json` already defines the structural shape of a
  possible Query Result artifact.
- Shared components define source attribution, Evidence links,
  uncertainty/verification state, limitations, boundary disclosures,
  disclaimers, and common envelopes.
- 121A does not modify, extend, or reinterpret any schema.
- Future Track 121 implementation phases may read the schemas as
  contracts, but any schema modification requires a separate governed
  schema phase.

The Query Layer architecture is downstream of schemas. It does not
create a new schema authority.

### 3.2 Track 120 Repository Knowledge Snapshot

Track 120 generated and verified the first read-only Repository
Knowledge Snapshot. The Query Layer consumes that snapshot as an
artifact, not as a repository scanner's instruction set.

The Query Layer may read fields such as architectural entities,
subsystems, claims, knowledge sources, unknowns, limitations, boundary
disclosures, and disclaimers from a Repository Knowledge Snapshot. It
may not re-run the snapshot generator, add missing claims, recursively
inspect repository files, infer unstated relationships, or repair the
snapshot.

If a requested fact is absent from the snapshot, the Query Layer must
return a bounded unknown/unsupported/missing-result response rather
than read the repository or invent an answer.

### 3.3 Repository State

Repository Intelligence is not Repository State. Query results may
describe what an artifact says about repository structure, but they do
not decide whether the repository is valid, current, complete, or in a
particular lifecycle state.

The Query Layer must never mutate Repository State, replace Repository
State, or treat a query response as a Repository State transition.

### 3.4 Evidence

Repository Intelligence is not Evidence. A query response may preserve
Evidence links already present in a Repository Intelligence artifact,
including evidence-gap markers. It may not create new Evidence, accept
Evidence, replace Evidence, or certify truth.

If no Evidence link exists in the source artifact, the Query Layer must
preserve that gap rather than fabricate support.

### 3.5 Advisory

The Query Layer is not Advisory and does not perform Advisory
reasoning. Future Advisory consumers may use Query Layer results as
context, but a query result must never be an Advisory approval,
recommendation, permission, enforcement signal, or execution
authorization.

### 3.6 Decision Evaluation

The Query Layer is not Decision Evaluation. It may return context for a
human or future subsystem, but it must never decide, approve, reject,
rank by authority, or replace Decision Evaluation.

Any future consumer that wants to use query output for a PCAE decision
must still pass through Decision Evaluation.

## 4. Architectural Scope

The Query Layer reads existing Repository Intelligence artifacts and
performs deterministic consumption operations only:

- read Repository Intelligence artifacts;
- validate query shape conceptually before evaluation;
- perform deterministic lookup;
- perform deterministic filtering;
- perform deterministic selection;
- assemble deterministic result records;
- preserve attribution, limitations, unknowns, boundary disclosures,
  disclaimers, and metadata;
- format results without changing their meaning.

The Query Layer does not:

- generate Repository Intelligence;
- scan repositories;
- execute repository code;
- invoke shell execution beyond future governed read operations needed
  to load artifact files;
- invoke AI providers;
- infer knowledge;
- summarize using AI;
- reinterpret repository knowledge;
- change Repository Intelligence artifacts;
- modify artifacts;
- perform graph traversal;
- perform dependency analysis;
- perform change impact analysis;
- invoke Advisory;
- make decisions;
- plan or authorize execution.

## 5. Conceptual Query Architecture

The future Query Layer is composed of eight conceptual layers. 121A
defines responsibilities only; it does not define classes, functions,
schemas, commands, syntax, or storage details.

### 5.1 Query Interface Layer

Accepts a future query request from a governed caller. Its job is to
receive the declared query subject, scope, filters, and projection
without interpreting them as permission to inspect the repository or
perform inference.

This layer is not a CLI, API, REST endpoint, prompt interface, or
parser in 121A. Those surfaces are explicitly deferred.

### 5.2 Query Validation Layer

Checks whether the declared request is within the future query
contract:

- supported artifact input type;
- supported query category;
- bounded scope;
- deterministic filters;
- deterministic projection;
- no request for inference, generation, execution, Advisory reasoning,
  change impact reasoning, dependency traversal, or repository
  scanning.

Invalid, unsupported, ambiguous, or authority-seeking requests fail
closed before artifact access.

### 5.3 Snapshot Access Layer

Reads existing Repository Intelligence artifacts from governed
artifact storage. Its initial conceptual input is a Repository
Knowledge Snapshot; future inputs may include Repository Intelligence
Packages that contain or reference multiple artifacts.

This layer does not read repository source files, docs, tests, git
history, runtime state, Evidence stores, Advisory outputs, or network
sources. It reads artifact content only.

### 5.4 Query Evaluation Layer

Performs deterministic lookup, filtering, and selection over the
already loaded artifact content. It may compare exact values, select
records by declared fields, filter arrays by deterministic predicates,
or select known sections of an artifact.

It may not infer missing relationships, compute graph reachability,
rank relevance probabilistically, summarize semantically, or combine
artifact content into a new claim that the source artifact did not
already contain.

### 5.5 Result Assembly Layer

Assembles selected records into a query result shape. Result assembly
is structural: it organizes returned items, source artifact references,
query metadata, unknown/gap entries, limitations, and boundary
disclosures.

It does not create new Repository Intelligence. It returns what the
source artifact already said, with the query operation disclosed.

### 5.6 Attribution Layer

Preserves attribution for every returned result item. Returned
information must remain traceable to the originating Repository
Intelligence artifact and, where the source artifact contains deeper
source attribution, to the source attribution records embedded in that
artifact.

The Attribution Layer must never drop attribution to make a result
shorter or cleaner. If attribution is absent or malformed in a source
artifact, the query must fail closed or return a limitation/unknown
record rather than assert an unattributed fact.

### 5.7 Limitation Layer

Carries forward existing limitations from source artifacts and adds
query-specific limitations, such as:

- result limited to a particular snapshot;
- result limited to selected fields;
- unsupported query category;
- missing or corrupted source artifact;
- unsupported schema version;
- no result found in the artifact.

Limitations are not warnings off to the side; they are part of the
result contract.

### 5.8 Result Formatting Layer

Formats the assembled result deterministically for a future caller or
artifact shape. Formatting may choose field order, grouping, and
presentation conventions, but it must not alter meaning, summarize
with AI, suppress limitations, or remove boundary disclosures.

121A does not define output syntax, CLI rendering, JSON shape, API
shape, or storage format beyond the conceptual alignment with the
Phase 119 Query Result schema.

## 6. Query Model

The conceptual query model contains the following elements:

- **Query request** — a declared, bounded request to read information
  from one or more existing Repository Intelligence artifacts.
- **Query context** — the artifact identity, artifact family, schema
  version, snapshot identity, generation commit, and caller/governance
  context relevant to evaluating the request.
- **Query scope** — the explicit artifact family, artifact instance,
  section, record type, field set, or result bound that limits the
  query.
- **Query filters** — deterministic predicates over declared artifact
  fields, such as exact entity id, entity type, claim id, source id,
  limitation type, boundary field, or documentation reference.
- **Query projection** — the requested subset of fields or sections to
  return, preserving required attribution and boundary metadata.
- **Query result** — the deterministic response assembled from the
  source artifact and query metadata.
- **Result attribution** — the source artifact reference and embedded
  source attribution records that support each returned item.
- **Result limitations** — source-artifact limitations and query-time
  limitations that bound interpretation of the result.
- **Result disclaimers** — inherited and query-specific disclaimers
  preserving read-only, non-decision, non-execution, non-Evidence, and
  non-Repository-State boundaries.

This model is conceptual. 121A does not define query syntax.

## 7. Query Input Model

Supported conceptual inputs:

- Repository Knowledge Snapshot artifacts produced by Track 120.
- Future Repository Intelligence Packages, if later tracks define them
  as containers or indexes of Repository Intelligence artifacts.

Explicitly unsupported inputs:

- direct repository working tree access;
- direct source, test, doc, or schema file scanning;
- direct git history inspection;
- runtime state;
- Advisory outputs as authoritative inputs;
- Evidence records as a substitute for Repository Intelligence
  artifacts;
- network services;
- AI model responses.

No direct repository access is permitted. If the needed information is
not in the artifact input, it is outside the query's knowledge boundary.

## 8. Query Output Model

A future Query Layer result is conceptually:

- deterministic;
- read-only;
- source-attributed;
- bounded by query scope;
- explicit about unknowns/gaps;
- explicit about limitations;
- explicit about boundary disclosures;
- metadata-bearing.

Conceptual output elements:

- result identity;
- query subject;
- query scope;
- query category;
- source artifact identity and schema version;
- selected result items;
- result groups or summaries only when they are direct deterministic
  reorganizations of selected artifact content;
- result attribution;
- result limitations;
- unknown/gap entries;
- boundary disclosures;
- disclaimers;
- determinism metadata.

The output model aligns conceptually with
`schemas/repository_intelligence/artifacts/query_result.schema.json`,
but 121A does not produce Query Result artifacts and does not implement
a Query Result generator.

## 9. Query Categories

121A defines supported query categories architecturally, not as syntax:

- **Entity lookup** — select architectural entities by declared fields
  such as `entity_id`, `entity_name`, `entity_type`, or `entity_path`.
- **Capability lookup** — select capability records if present in a
  source artifact; return an explicit gap if the source snapshot does
  not populate capabilities.
- **Architectural contract lookup** — select contract references or
  contract-related claims if present in a source artifact or future
  package.
- **Source attribution lookup** — return attribution records for a
  selected entity, claim, subsystem, or result item.
- **Documentation lookup** — return documentation references or
  documentation-related claims that already exist in the artifact.
- **Limitation lookup** — return snapshot-level, record-level, or
  query-specific limitations.
- **Boundary lookup** — return boundary disclosures and disclaimers
  from the source artifact or query result.
- **Unknown/gap lookup** — return declared unknowns and gaps from the
  source artifact, preserving their uncertainty state where available.
- **Artifact metadata lookup** — return artifact identity, schema
  version, snapshot identity, generation commit, and producer metadata.

Unsupported categories must fail closed. In particular, graph
traversal, dependency impact questions, change impact questions,
Advisory reasoning, and execution-readiness questions are not Query
Layer categories in 121A.

## 10. Determinism Architecture

The Query Layer's determinism guarantee is:

> identical artifact input + identical query request + identical query
> contract = identical logical result.

The architecture requires:

- stable artifact identity and schema version selection;
- deterministic ordering for returned arrays;
- deterministic filter evaluation;
- deterministic projection;
- no randomness;
- no probabilistic scoring;
- no AI inference;
- no filesystem-order dependence;
- no time-dependent result content except future non-substantive
  metadata fields explicitly allowed by a contract phase.

If a query request cannot be evaluated deterministically, it must fail
closed.

## 11. Attribution Architecture

Every returned result must preserve attribution. Attribution has two
levels:

- **Artifact attribution** — the result must identify the Repository
  Intelligence artifact from which it was read.
- **Embedded source attribution** — if the returned artifact record
  carries Source Attribution Records, those records must remain attached
  or referenced in the result.

The Query Layer may not collapse attribution into a vague source label.
It may not remove limitations attached to attribution. It may not turn
an evidence-gap marker into an Evidence claim.

If a future result aggregates multiple selected records, the result
must preserve the attribution for each member record. Aggregation is
structural grouping only, not a new claim.

## 12. Boundary Architecture

The Query Layer must never:

- infer unstated knowledge;
- summarize using AI;
- reinterpret Repository Intelligence;
- correct Repository Intelligence;
- generate Repository Intelligence;
- replace Advisory;
- replace Decision Evaluation;
- replace Evidence;
- replace Repository State;
- authorize action;
- authorize execution;
- mutate artifacts;
- mutate runtime state.

Boundary disclosures and disclaimers must be present in any future
query result shape. The source artifact's own boundary disclosures
must remain visible or traceable so a result cannot be misread as more
authoritative than its source.

## 13. Failure Architecture

The Query Layer fails closed. Conceptual failure handling:

- **Unknown entity** — return a bounded no-result/unknown response with
  attribution to the queried artifact and a limitation explaining that
  the entity is absent from the artifact.
- **Invalid query** — reject before artifact access if the request is
  malformed, unbounded, ambiguous, or authority-seeking.
- **Unsupported query** — reject when the category requires inference,
  graph traversal, change impact reasoning, Advisory reasoning,
  repository scanning, or execution.
- **Missing snapshot** — fail closed and disclose the missing artifact;
  do not rescan the repository to compensate.
- **Corrupted snapshot** — fail closed and mark the artifact unusable
  for query evaluation; do not partially trust malformed content.
- **Unsupported schema version** — fail closed or return an explicit
  unsupported-version limitation; do not guess field mappings.
- **Missing attribution** — fail closed for content-bearing results or
  return a limitation-only response; do not assert unattributed facts.
- **Conflicting source content** — preserve conflict markers already in
  the artifact; do not resolve the conflict.

Failure responses are still read-only and non-authoritative.

## 14. Governance Architecture

The Query Layer must preserve:

- observe-only runtime posture;
- execution unavailable;
- maximum plugin capability `observe`;
- deterministic behavior;
- auditability;
- reproducibility;
- explainability;
- human-controlled phase progression;
- governed lifecycle, commit, report, and notification discipline.

Future query prototypes must be testable by fixed artifacts and fixed
queries. They must not depend on ambient runtime state, network
availability, current repository contents, AI model output, or hidden
mutable caches.

Query output should be explainable in terms of:

- query request;
- artifact input;
- deterministic filters;
- selected records;
- preserved attribution;
- disclosed limitations.

## 15. Future Extensibility

The Query Layer is a future consumer boundary for later Repository
Intelligence tracks, but 121A does not couple implementation to them.

Future consumers may include:

- **Advisory** — may consume query results as context, without gaining
  authority or replacing Decision Evaluation.
- **Change Impact** — may later ask bounded questions about existing
  Repository Intelligence, but impact reasoning itself is outside the
  Query Layer.
- **Dependency Knowledge Graph** — may later expose graph-derived
  artifacts through query results, but graph construction and traversal
  are outside 121A.
- **Historical Memory** — may later query historical artifacts, but
  history extraction and timeline generation are outside 121A.
- **Repository Intelligence Packages** — may later provide packaged
  artifact indexes for query inputs, but package generation and package
  validation are outside 121A.

The extension rule is: future consumers may read Query Layer outputs,
but they may not make the Query Layer responsible for their reasoning,
authority, or execution behavior.

## 16. Track 121 Roadmap

Committed Track 121 sequence:

- **121A — Repository Intelligence Query Layer Architecture**:
  architecture only; define purpose, scope, layers, boundaries, query
  model, governance, failure handling, and roadmap.
- **121B — Repository Intelligence Query Contract Freeze**: freeze the
  normative contract for query inputs, supported categories,
  deterministic behavior, attribution, limitations, failure behavior,
  and non-goals.
- **121C — Repository Intelligence Query Contract Verification**:
  independently verify the 121B contract before planning any prototype.
- **121D — Repository Intelligence Query Prototype Plan**: plan a
  narrow read-only query prototype without implementation.
- **121E — Read-Only Query Prototype**: implement only the scoped
  prototype approved by 121B-121D.
- **121F — Query Prototype Verification**: independently verify the
  query prototype against the contract, schemas, determinism, and
  governance boundaries.

121A recommends 121B as the next phase.

## 17. Strict Non-Goals

121A does not implement:

- query engine;
- query parser;
- CLI;
- API;
- REST;
- Python models;
- validators;
- runtime plugins;
- repository scanning;
- Repository Intelligence generation;
- graph traversal;
- dependency analysis;
- change impact analysis;
- Advisory integration;
- execution planning;
- execution capability;
- Query Result artifact generation;
- Query Result persistence;
- fixture generation;
- automated tests;
- source code changes;
- schema changes.

## 18. Known Inherited Issues

Carried forward unchanged and not repaired in this phase:

- 119Q report-generation-ordering defect: non-blocking.
- 119AB phase-id comparison bug: non-blocking.
- Recurring `pending_final_telegram_delivery` reporting detail:
  non-blocking.

## 19. Acceptance Criteria

121A is complete when:

- the Query Layer architecture is documented;
- relationships to Phase 119 schemas, Track 120 artifacts, Repository
  State, Evidence, Advisory, and Decision Evaluation are explicit;
- query responsibilities and boundaries are defined;
- conceptual layers, query model, input/output models, categories,
  determinism, attribution, failure, governance, and extensibility are
  defined;
- Track 121 roadmap is documented;
- no implementation occurs;
- runtime posture remains `Observed` / `observe` / execution
  unavailable.
