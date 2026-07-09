# Phase 121D - Repository Intelligence Query Prototype Plan

## 1. Purpose

Phase 121D defines the definitive implementation plan for the first
Repository Intelligence Query Layer prototype.

The planned prototype will provide deterministic, read-only access to
Repository Knowledge Snapshot artifacts generated during Track 120. It
will consume existing artifacts, evaluate bounded lookup/filter/
projection requests, preserve attribution and limitations, attach
boundary disclosures, and return deterministic results.

This phase defines implementation planning only. It implements no query
engine, query parser, query language, CLI, REST surface, API, Python
model, validator, runtime plugin, Repository Intelligence generator,
repository scanner, graph traversal, dependency analysis, change impact
analysis, Advisory integration, execution planning, or execution
capability.

## 2. Planning Baseline

Initial inspection confirmed:

- `git status --short`: clean before the active 121D task contract was
  created.
- `git status --branch --short`: `main...origin/main`.
- `git log --oneline origin/main..HEAD`: empty.
- `git rev-list --count origin/main..HEAD`: `0`.
- `pcae health`: healthy, idle, required files present, policy valid,
  no active task, agent lock available before phase start, git status
  clean.
- `pcae check`: passed.
- `pcae doctor task-memory`: clean.
- `pcae push check`: clean, nothing to push.
- `pcae runtime inspect`: runtime state `Observed`, maximum plugin
  capability `observe`, execution capability `unavailable`, registry
  empty, plugin count `0`.
- `source ~/.config/pcae/telegram.env && pcae notify status`: Telegram
  configured, enabled, and ready for outbound delivery.
- `pcae phase-report show --latest --trust`: Phase 121C canonical
  report complete and trusted, pushed, `origin/main..HEAD: 0`.

The active 121D task contract was created after baseline inspection:
`tasks/active/20260709-0805-phase-121d-repository-intelligence-query-prototype-plan.md`.

## 3. Prototype Objective

The Phase 121E prototype will implement the first deterministic,
read-only Query Layer capable of querying Repository Knowledge Snapshot
artifacts.

The prototype objective is narrow:

- read an existing Repository Knowledge Snapshot artifact;
- verify that the artifact is a supported snapshot version;
- accept bounded query requests represented without a query language or
  parser grammar;
- evaluate deterministic lookup, filter, and projection requests over
  snapshot content;
- return deterministic logical results;
- preserve provenance for every returned content-bearing record;
- propagate limitations, unknowns/gaps, boundary disclosures,
  disclaimers, and metadata;
- fail closed for invalid, unsupported, missing, corrupted, or
  incompatible inputs.

No additional Repository Intelligence artifact family is included.

## 4. Scope

The prototype operates exclusively on:

- Repository Knowledge Snapshot artifacts conforming to
  `schemas/repository_intelligence/artifacts/repository_knowledge_snapshot.schema.json`.

The first supported executable schema version is:

```text
119O.1.0-json-schema
```

The prototype may read snapshot fields already defined by that schema,
including snapshot identity, architectural entities, capabilities,
subsystems, knowledge claims, relationships, knowledge sources,
Evidence links or evidence-gap markers, unknowns, limitations,
contract references, documentation references, boundary disclosures,
disclaimers, and envelope metadata.

Explicitly deferred:

- Historical Memory Snapshot;
- Dependency Knowledge Graph Snapshot;
- Change Impact Report;
- Advisory Intelligence Context Package;
- Query Result as input;
- Repository Intelligence Package;
- direct repository working tree access;
- direct git history access;
- direct source, test, doc, or schema scanning outside artifact
  compatibility checks;
- runtime state as query input;
- Evidence stores as query input;
- Advisory outputs as query input;
- network sources;
- AI model responses.

## 5. Query Pipeline

The planned logical pipeline has ten stages. These are responsibilities
only, not algorithms, classes, functions, files, or command surfaces.

1. **Query request intake**: receive a bounded structured request from a
   governed caller or test harness. The intake stage records the
   declared target, scope, filters, projections, and output preferences
   without treating them as permission to inspect the repository,
   invoke inference, or expand authority.
2. **Request validation**: confirm the request names a supported query
   category, supported target, bounded scope, deterministic filter set,
   deterministic projection, and result bound. Invalid, ambiguous,
   authority-seeking, or unsupported requests fail closed before query
   evaluation.
3. **Snapshot loading**: load an existing Repository Knowledge Snapshot
   artifact from a declared artifact location. Loading is read-only and
   does not regenerate, repair, or modify the snapshot.
4. **Snapshot compatibility verification**: verify that the loaded
   artifact declares the Repository Knowledge Snapshot family and the
   supported executable schema version `119O.1.0-json-schema`.
   Unsupported, missing, malformed, or ambiguous version information
   fails closed.
5. **Query evaluation**: perform deterministic lookup, filtering, and
   selection over already-loaded snapshot content. Evaluation returns
   only information already present in the artifact.
6. **Attribution preservation**: ensure every returned content-bearing
   record remains traceable to the snapshot artifact and to embedded
   Source Attribution Records where the snapshot provides them.
7. **Limitation propagation**: carry forward snapshot-level,
   envelope-level, and record-level limitations relevant to returned
   content, and add query-specific limitations for unsupported,
   missing, incomplete, or narrowed results.
8. **Boundary attachment**: attach or preserve boundary disclosures,
   disclaimers, unknown/gap disclosures, and non-authority statements
   so results cannot be mistaken for Repository State, Evidence,
   Advisory output, Decision Evaluation, or execution permission.
9. **Result assembly**: assemble selected records, query metadata,
   artifact metadata, attribution, limitations, unknowns/gaps, and
   boundaries into a deterministic result structure.
10. **Result formatting**: format the result deterministically for the
    planned caller or test surface. Formatting may affect ordering or
    grouping presentation only when logical result content is
    unchanged.

## 6. Planned Components

The prototype should be planned as small conceptual components. This
section names responsibilities, inputs, outputs, and boundaries only;
it does not prescribe classes, modules, source files, or command names.

### 6.1 Request Intake Component

Responsibility:

- accept a bounded structured query request;
- preserve declared request metadata;
- pass the request unchanged to validation.

Inputs:

- structured request object or equivalent in-process representation;
- governed caller context where available.

Outputs:

- normalized request envelope for validation;
- intake limitation if required metadata is absent.

Boundaries:

- no query language;
- no parser grammar;
- no natural-language interpretation;
- no repository access;
- no artifact access.

### 6.2 Request Validation Component

Responsibility:

- verify supported query category, target, scope, filters,
  projections, output preferences, and result bounds;
- reject unsupported authority-seeking requests.

Inputs:

- request envelope from intake;
- supported category and target definitions from the 121B contract.

Outputs:

- validated request;
- fail-closed invalid-request result or limitation.

Boundaries:

- no repository scanning;
- no inference;
- no schema modification;
- no query execution for invalid requests.

### 6.3 Snapshot Access Component

Responsibility:

- read an existing Repository Knowledge Snapshot artifact from a
  declared persisted location;
- expose loaded artifact content for compatibility verification.

Inputs:

- declared snapshot artifact path or artifact handle;
- read-only artifact storage.

Outputs:

- loaded snapshot content;
- missing/corrupted snapshot failure.

Boundaries:

- no snapshot generation;
- no snapshot repair;
- no persistence modification;
- no repository file inspection to compensate for missing data.

### 6.4 Snapshot Compatibility Component

Responsibility:

- verify the loaded artifact is a Repository Knowledge Snapshot;
- verify the first supported executable schema version:
  `119O.1.0-json-schema`;
- preserve source schema-version metadata for result disclosure.

Inputs:

- loaded snapshot content;
- Repository Knowledge Snapshot schema-version expectations.

Outputs:

- compatible snapshot view;
- fail-closed unsupported-version result or limitation.

Boundaries:

- no version inference;
- no silent field mapping;
- no migration;
- no validator authority beyond compatibility gating planned here.

### 6.5 Query Evaluation Component

Responsibility:

- perform deterministic lookup, filtering, and projection over snapshot
  content;
- preserve no-result, unsupported, unknown, incomplete, and conflict
  states without inference.

Inputs:

- validated request;
- compatible snapshot view.

Outputs:

- selected records or bounded no-result/unknown/unsupported outcome;
- deterministic selection metadata.

Boundaries:

- no graph traversal;
- no dependency reasoning;
- no change impact reasoning;
- no Advisory reasoning;
- no AI summarization;
- no new Repository Intelligence claim.

### 6.6 Attribution Component

Responsibility:

- preserve artifact provenance and embedded Source Attribution Records
  for returned content-bearing records;
- detect missing or malformed attribution on content-bearing returns.

Inputs:

- selected records;
- compatible snapshot metadata;
- embedded source attribution records.

Outputs:

- attribution-preserving selected records;
- fail-closed missing-attribution result or limitation-only result.

Boundaries:

- no fabricated attribution;
- no fabricated Evidence;
- no conversion of evidence gaps into Evidence support;
- no attribution removal for brevity.

### 6.7 Limitation and Unknown Component

Responsibility:

- propagate relevant snapshot, envelope, and record limitations;
- represent unknown, unsupported, missing, incomplete, and conflicting
  data as bounded result states.

Inputs:

- selected records or no-result outcome;
- snapshot limitations;
- unknowns/gaps;
- conflict or uncertainty markers where present.

Outputs:

- limitation-bearing result material;
- unknown/gap disclosures.

Boundaries:

- no conflict resolution;
- no inference to fill missing data;
- no limitation suppression.

### 6.8 Boundary Component

Responsibility:

- attach or preserve boundary disclosures and disclaimers;
- disclose that results are context only and not decisions, approvals,
  Evidence, Repository State, Advisory output, or execution authority.

Inputs:

- selected records or bounded failure outcome;
- snapshot boundary disclosures;
- snapshot disclaimers;
- query-specific boundary obligations.

Outputs:

- boundary-complete result material.

Boundaries:

- no authority expansion;
- no execution permission;
- no Decision Evaluation replacement.

### 6.9 Result Assembly Component

Responsibility:

- assemble deterministic result material into a coherent result
  structure;
- include query metadata, artifact metadata, selected records,
  attribution, limitations, unknowns/gaps, boundary disclosures, and
  determinism metadata.

Inputs:

- request metadata;
- compatible snapshot metadata;
- selected or failure result material;
- attribution, limitations, unknowns, and boundaries.

Outputs:

- deterministic logical result.

Boundaries:

- no `query_result.schema.json` artifact generation unless separately
  authorized by the implementation plan and contract;
- no persistence as a query side effect;
- no new Repository Intelligence artifact generation.

### 6.10 Result Formatting Component

Responsibility:

- produce a deterministic presentation of the assembled result for the
  planned caller or tests;
- preserve logical result content exactly.

Inputs:

- assembled result;
- output preferences validated as non-authoritative.

Outputs:

- formatted result.

Boundaries:

- no semantic summarization;
- no AI-generated prose;
- no suppression of attribution, limitations, boundaries, or metadata.

## 7. Query Request Plan

The prototype should use a bounded structured request representation.
No query language, text parser, natural-language interpreter, grammar,
CLI syntax, REST syntax, or API surface is planned in this phase.

Supported conceptual request families:

- **Lookup requests**: select one declared target category such as
  entity, capability, documentation reference, architectural contract
  reference, attribution, limitation, boundary disclosure, unknown/gap,
  or artifact metadata.
- **Filter requests**: apply deterministic predicates over declared
  snapshot fields, such as exact id, type, path, source id, limitation
  type, boundary field, or schema-version metadata.
- **Projection requests**: select deterministic fields or subrecords to
  return while preserving required attribution, limitations, boundary
  disclosures, disclaimers, and metadata.

Every request must declare:

- artifact source;
- query category;
- query target;
- bounded scope;
- deterministic filters, if any;
- deterministic projection, if any;
- result bound or no-result behavior;
- output preferences, if any.

Unsupported requests fail closed. A request fails closed if it asks for
inference, generation, repository scanning, graph traversal, dependency
reasoning, change impact reasoning, Advisory reasoning, Decision
Evaluation, execution planning, execution authorization, semantic
summarization, probabilistic ranking, or unstated relationship
discovery.

## 8. Query Result Plan

The planned output is a deterministic logical result that includes:

- query metadata;
- source artifact metadata;
- source artifact schema-version disclosure;
- selected result records or bounded no-result/unknown/unsupported
  outcome;
- preserved attribution;
- limitation records;
- unknown/gap disclosures where applicable;
- boundary disclosures;
- disclaimers;
- determinism metadata;
- failure metadata when fail-closed behavior occurs.

Every content-bearing result must preserve provenance. A returned
record must remain traceable to the Repository Knowledge Snapshot that
supplied it and, when present, to embedded Source Attribution Records.

The planned prototype does not need to persist results. If 121E elects
to align an in-memory structure with
`schemas/repository_intelligence/artifacts/query_result.schema.json`,
that alignment must remain structural and read-only. Persisting a Query
Result artifact is deferred unless explicitly authorized in 121E's
implementation scope.

## 9. Snapshot Compatibility Plan

The first prototype supports Repository Knowledge Snapshot artifacts
with:

```text
executable_schema_version = 119O.1.0-json-schema
```

Compatibility verification should ensure:

- the artifact is a Repository Knowledge Snapshot;
- required identity and envelope fields are present;
- the declared executable schema version is exactly
  `119O.1.0-json-schema`;
- the artifact exposes the source sections needed for requested query
  categories;
- source artifact metadata can be disclosed in the result;
- unsupported schema versions fail closed;
- missing schema-version metadata fails closed;
- ambiguous or silently equivalent schema versions are not accepted.

This plan does not implement a schema validator, migration layer,
compatibility table, or version negotiation. Future schema-version
support requires explicit governed expansion.

## 10. Attribution Plan

Every returned result must preserve provenance.

Planned attribution behavior:

- include artifact provenance for the originating Repository Knowledge
  Snapshot;
- preserve embedded Source Attribution Records for selected records
  where present;
- preserve per-record attribution when results are grouped;
- preserve evidence-gap markers without converting them into Evidence
  support;
- propagate attribution-related limitations;
- fail closed or return limitation-only output if a content-bearing
  record lacks required attribution.

No returned information may lose attribution. Formatting, grouping,
projection, or output preferences cannot remove provenance.

## 11. Unknown Handling Plan

The prototype must preserve unknowns and gaps rather than infer around
them.

Planned handling:

- **Unknown entity**: return bounded no-result or unknown output that
  identifies the queried snapshot and discloses that the entity is not
  present in supported artifact content.
- **Unsupported entity**: fail closed or return unsupported-target
  limitation when the requested entity category is outside the 121B
  contract.
- **Missing data**: return a missing-data limitation or gap disclosure;
  do not scan repository files or generate a replacement fact.
- **Incomplete data**: return available attributed content with
  limitations and unknown/gap disclosures; do not complete the record by
  inference.
- **Conflicting data**: preserve conflict, uncertainty, or limitation
  markers already present in the snapshot; do not resolve conflict or
  rank truth.

No AI inference, semantic summarization, repository scanning, graph
reasoning, or dependency reasoning may be used to resolve unknowns.

## 12. Failure Plan

The prototype must fail closed for:

- invalid requests;
- unsupported requests;
- malformed scope;
- unsupported query target;
- unsupported projection;
- missing snapshot;
- corrupted snapshot;
- unsupported schema version;
- missing schema-version metadata;
- missing required attribution;
- request for inference, generation, graph traversal, dependency
  reasoning, change impact reasoning, Advisory reasoning, Decision
  Evaluation, repository scanning, execution planning, or execution
  capability.

Fail-closed behavior may return a bounded error or limitation result,
provided it does not assert unsupported facts. The prototype must not
continue by guessing, scanning the repository, reading external
sources, invoking AI, partially trusting corrupted artifacts, silently
mapping unsupported versions, or producing unattributed content.

## 13. Persistence Interaction

The Query Layer interacts with persisted snapshots as read-only input.

Planned behavior:

- read a declared Repository Knowledge Snapshot artifact from persisted
  storage;
- support the Track 120 persistence shape conceptually, including
  `.pcae/repository-intelligence/latest.json` and timestamped snapshots
  under `.pcae/repository-intelligence/snapshots/`, if 121E chooses
  those as fixture inputs;
- never write, modify, delete, rotate, repair, or regenerate snapshot
  artifacts;
- never treat query execution as a persistence event;
- never use persisted snapshot absence as permission to rerun the Track
  120 generator;
- never update `.pcae/repository-intelligence/` as a query side effect.

Query results are not persisted by default in this plan.

## 14. Verification Plan for 121F

Phase 121F should independently verify the 121E prototype against the
121A architecture, 121B contract, 121C verification conclusions, and
this 121D plan.

Verification surfaces:

- **Deterministic results**: identical supported snapshot plus
  identical request produces identical logical result across repeated
  runs.
- **Attribution preservation**: every content-bearing returned record
  preserves artifact provenance and embedded Source Attribution Records
  where present.
- **Schema compatibility**: supported version
  `119O.1.0-json-schema` is accepted; unsupported, missing, or
  malformed schema-version metadata fails closed.
- **Governance compatibility**: runtime remains `Observed`, maximum
  plugin capability remains `observe`, execution remains unavailable,
  and no runtime plugin is introduced.
- **Boundary preservation**: results do not become Repository State,
  Evidence, Advisory output, Decision Evaluation, execution
  authorization, or Repository Intelligence generation.
- **Failure handling**: invalid requests, unsupported requests, missing
  snapshots, corrupted snapshots, unsupported schema versions, and
  missing attribution fail closed.
- **Read-only behavior**: query evaluation does not modify snapshot
  artifacts, repository files, runtime state, Evidence, Advisory,
  Repository State, lifecycle state, or persistence history.
- **Regression safety**: existing Repository Knowledge Snapshot
  generation and verification behavior remains intact.

## 15. Acceptance Criteria for 121E

Phase 121E is complete when the prototype demonstrably satisfies these
measurable criteria:

1. Implements only the scoped Repository Knowledge Snapshot query
   prototype.
2. Accepts bounded structured lookup, filter, and projection requests
   without implementing a query language or parser grammar.
3. Reads only existing Repository Knowledge Snapshot artifacts as query
   input.
4. Supports exactly `119O.1.0-json-schema` as the first executable
   schema version unless a governed contract change occurs first.
5. Produces deterministic logical results for identical snapshot and
   request inputs.
6. Preserves artifact provenance and embedded Source Attribution
   Records for every returned content-bearing record.
7. Propagates relevant limitations, unknowns/gaps, boundary
   disclosures, disclaimers, and metadata.
8. Fails closed for invalid requests, unsupported requests, missing
   snapshots, corrupted snapshots, unsupported schema versions, and
   missing required attribution.
9. Does not generate or modify Repository Intelligence artifacts.
10. Does not scan repository files, inspect git history, invoke AI
    providers, invoke Advisory, perform Decision Evaluation, traverse
    graphs, analyze dependencies, analyze change impact, plan
    execution, authorize execution, or introduce execution capability.
11. Does not change runtime posture: runtime remains `Observed`,
    maximum plugin capability remains `observe`, execution remains
    unavailable, and zero runtime plugins remain registered unless a
    separate governed runtime phase explicitly changes that.
12. Includes focused tests or verification fixtures sufficient for
    121F to independently evaluate determinism, attribution,
    compatibility, failure handling, boundaries, and read-only
    behavior.

## 16. Risks and Mitigations

### 16.1 Scope Creep into Query Language

Risk: a structured request representation may drift into a query
language, parser, or CLI syntax.

Mitigation: keep requests as bounded in-process structures or fixtures
for the first prototype, with no grammar, no text parsing, and no public
command surface unless separately governed.

### 16.2 Attribution Loss During Projection

Risk: projections may return compact records that omit source
attribution.

Mitigation: make attribution preservation mandatory for every
content-bearing result and treat missing attribution as fail-closed or
limitation-only output.

### 16.3 Determinism Drift

Risk: result ordering, grouping, or formatting may depend on filesystem
order, dictionary insertion order, timestamps, or ambient state.

Mitigation: require deterministic ordering and fixed artifact/request
fixtures in 121E tests and 121F verification.

### 16.4 Schema Compatibility Ambiguity

Risk: future schema versions may be accidentally accepted as equivalent
to `119O.1.0-json-schema`.

Mitigation: exact version match for the first prototype; unsupported,
missing, or ambiguous versions fail closed until a future governed
compatibility phase expands support.

### 16.5 Repository Scanning Temptation

Risk: missing snapshot facts may tempt the implementation to inspect
repository files or git history.

Mitigation: enforce artifact-only access and fail-closed missing-data
handling. Absence from the snapshot is reported as absence, unknown,
unsupported scope, or limitation.

### 16.6 Result Authority Creep

Risk: query results may be misread as Evidence, Repository State,
Advisory guidance, Decision Evaluation, or execution permission.

Mitigation: preserve boundary disclosures, disclaimers, and
non-authority statements in every result path, including failures and
no-result outcomes.

## 17. Deferred Capabilities

Explicitly deferred:

- query language;
- query parser;
- query grammar;
- CLI;
- REST;
- API;
- Python data models as a contract authority;
- validators as a new authority layer;
- runtime plugins;
- Historical Memory Snapshot queries;
- Dependency Knowledge Graph Snapshot queries;
- Change Impact Report queries;
- Advisory Intelligence Context Package queries;
- Repository Intelligence Package queries;
- graph traversal;
- dependency reasoning;
- change impact reasoning;
- Advisory integration;
- Decision Evaluation replacement;
- execution planning;
- execution capability;
- Query Result persistence;
- Repository Intelligence generation;
- repository scanning.

## 18. Strict Non-Goals Confirmed

This phase did not implement:

- query engine;
- query parser;
- query language;
- CLI;
- REST;
- API;
- Python models;
- validators;
- runtime plugins;
- Repository Intelligence generation;
- repository scanning;
- graph traversal;
- dependency analysis;
- change impact analysis;
- Advisory integration;
- execution planning;
- execution capability;
- source code changes;
- schema changes;
- test code changes.

## 19. Known Inherited Issues

Carried forward unchanged and not repaired in this phase:

- 119Q report-generation-ordering defect: non-blocking inherited
  tooling/reporting issue.
- 119AB phase-id comparison bug: non-blocking inherited
  tooling/reporting issue.
- Recurring `pending_final_telegram_delivery` reporting detail:
  non-blocking inherited reporting detail.

## 20. Relationship to Future Phases

- **121E - Repository Intelligence Read-Only Query Prototype**:
  implement only the narrow Repository Knowledge Snapshot query
  prototype described in this plan.
- **121F - Query Prototype Verification**: independently verify the
  121E prototype against 121A, 121B, 121C, this plan, determinism,
  attribution preservation, schema compatibility, governance,
  boundaries, and failure handling.

No additional planning or implementation work begins in this phase.

## 21. Acceptance

121D is complete when this implementation plan is documented, project
memory reflects 121D completion, runtime remains `Observed` / `observe`
/ execution unavailable, no implementation has occurred, and the
recommended next phase is 121E - Repository Intelligence Read-Only
Query Prototype.
