# Phase 121B - Repository Intelligence Query Contract Freeze

## 1. Purpose

Phase 121B freezes the canonical Repository Intelligence Query
Contract. This contract governs deterministic, read-only access to
existing Repository Intelligence artifacts. It is binding for later
Track 121 work: 121C (contract verification), 121D (prototype plan),
121E (read-only query prototype), and 121F (prototype verification).

The Query Layer's purpose is to provide governed consumption of
Repository Intelligence that already exists. It reads artifacts,
performs deterministic lookup/filtering/selection over artifact
content, preserves attribution and limitations, and returns bounded
results. It does not generate Repository Intelligence, rescan
repositories, infer missing facts, reason with Advisory authority,
perform Decision Evaluation, traverse graphs, or execute anything.

## 2. Relationship to Phase 121A Architecture

Phase 121A defined the architecture for the Query Layer: conceptual
layers, query model, input/output boundaries, supported query
categories, determinism, attribution, failure handling, governance,
and future extensibility.

This phase freezes that architecture into normative contract rules.
Where 121A described architectural intent, 121B makes the constraints
binding. Later Track 121 phases may choose implementation details only
inside the boundaries frozen here.

## 3. Relationship to Track 120

Track 120 produced and verified the first deterministic, read-only
Repository Intelligence artifact: the Repository Knowledge Snapshot.
That artifact is the initial and only supported input source under
this contract.

The Query Layer must treat the Repository Knowledge Snapshot as an
artifact input. It must not rerun the generator, inspect repository
files, inspect git history, parse source code, parse documentation, or
fill gaps by scanning the repository. If information is absent from
the snapshot, the query result must represent absence, unknown,
unsupported scope, or limitation rather than inventing or deriving an
answer.

## 4. Contract Authority

This document is the canonical contract for the first Repository
Intelligence Query Layer track. It governs all later Track 121
implementation work unless explicitly superseded by a future
contract-amendment phase.

No later Track 121 phase may silently reinterpret this contract to
authorize query languages, parsers, CLIs, APIs, validators, runtime
plugins, repository scanning, inference, graph traversal, Advisory
reasoning, Decision Evaluation, or execution.

## 5. Implementation Independence

This contract is implementation-independent. It does not specify:

- programming language;
- classes, functions, modules, or file layout;
- query syntax;
- grammar;
- parser;
- CLI;
- API;
- REST surface;
- storage implementation;
- validator implementation;
- persistence implementation.

121D may later plan implementation details, but only after 121C
verifies this contract and only inside the boundaries frozen here.

## 6. Scope Contract

The Query Layer is frozen as:

- **deterministic** — same artifact plus same query produces the same
  logical result;
- **read-only** — it may not mutate artifacts, repository files,
  runtime state, Evidence, Advisory, Repository State, or lifecycle
  state;
- **artifact-consuming** — it reads existing Repository Intelligence
  artifacts only;
- **observe-only** — it operates within the existing `Observed` /
  `observe` / execution-unavailable runtime posture;
- **non-reasoning** — it shall never become a reasoning engine.

The Query Layer may select, filter, and format existing artifact
content. It may not create new Repository Intelligence claims.

## 7. Supported Artifact Sources

Initial supported input:

- Repository Knowledge Snapshot artifacts conforming to
  `schemas/repository_intelligence/artifacts/repository_knowledge_snapshot.schema.json`.

Future Repository Intelligence artifact families may be supported by
later contract phases. They are outside this contract.

Unsupported initial sources:

- Historical Memory Snapshot;
- Dependency Knowledge Graph Snapshot;
- Change Impact Report;
- Advisory Intelligence Context Package;
- Query Result as input;
- Repository Intelligence Package;
- direct repository working tree;
- git history;
- source/test/doc/schema files outside an artifact;
- runtime state;
- Evidence stores;
- Advisory outputs;
- network services;
- AI model responses.

## 8. Query Request Model

The contract freezes the following conceptual query request elements:

- **query request** — a bounded request to read information from a
  supported Repository Intelligence artifact.
- **query scope** — the artifact instance, artifact section, record
  family, field set, and result bound that limit evaluation.
- **query context** — artifact identity, artifact family, executable
  schema version, snapshot identity, snapshot commit, producer metadata,
  and governed caller context.
- **query target** — the record or section category being selected,
  such as entity, capability, documentation reference, source
  attribution, limitation, boundary disclosure, unknown, or metadata.
- **filters** — deterministic predicates over declared artifact fields,
  such as exact id, type, path, source id, limitation type, or boundary
  field.
- **projections** — deterministic selection of fields or subrecords to
  return, always preserving required attribution, limitations, boundary
  disclosures, and metadata.
- **output preferences** — future non-authoritative formatting choices,
  such as grouping or field order, that do not change logical result
  content.

No query syntax, query language, grammar, parser, command, or API is
frozen by this contract.

## 9. Query Result Model

The query result model is frozen as:

- deterministic logical results;
- source artifact metadata;
- query request metadata;
- selected result records;
- result attribution;
- result limitations;
- unknown/gap disclosures where applicable;
- boundary disclosures;
- disclaimers;
- result metadata sufficient for audit and reproducibility.

Every result must preserve provenance. A returned record must remain
traceable to the Repository Knowledge Snapshot that supplied it and to
the embedded source attribution records already present in that
snapshot where applicable.

This contract does not implement or require generation of
`query_result.schema.json` artifacts. It only freezes the conceptual
result obligations that future work must satisfy.

## 10. Supported Query Categories

The initial Query Layer contract supports these categories
architecturally:

- **entity lookup** — select architectural entities already present in
  the Repository Knowledge Snapshot.
- **capability lookup** — select capability records already present in
  the snapshot; if the snapshot contains no capabilities, return a
  bounded gap/limitation.
- **documentation lookup** — select documentation references or
  documentation-related claims already present in the snapshot.
- **architectural contract lookup** — select contract references or
  contract-related claims already present in the snapshot.
- **attribution lookup** — return Source Attribution Records associated
  with selected records.
- **limitation lookup** — return snapshot-level or record-level
  limitation records.
- **boundary lookup** — return boundary disclosures, disclaimers, or
  boundary-related metadata.
- **unknown/gap lookup** — return declared unknowns or gaps already
  present in the artifact.
- **artifact metadata lookup** — return snapshot identity, artifact id,
  schema version, generation commit, and producer metadata.

This contract freezes categories, not syntax. No query language,
grammar, or parser exists as a result of this phase.

## 11. Determinism Contract

The determinism rule is:

> identical Repository Knowledge Snapshot + identical query request
> = identical logical result.

The Query Layer must not use:

- randomness;
- probabilistic scoring;
- AI inference;
- semantic summarization;
- time-dependent result content;
- filesystem ordering;
- ambient runtime state;
- network calls;
- hidden mutable caches;
- non-deterministic tie breaking.

Ordering, filtering, projection, and grouping must be deterministic.
If a request cannot be evaluated deterministically, it must fail
closed.

## 12. Attribution Contract

Every returned record must preserve attribution.

Frozen attribution rules:

- attribution cannot be removed;
- embedded Source Attribution Records must remain attached or directly
  referenced;
- artifact provenance must identify the originating Repository
  Knowledge Snapshot;
- grouped results must preserve per-record attribution;
- missing attribution on a content-bearing result is a contract
  failure;
- the Query Layer may not replace attribution with a vague summary
  label;
- the Query Layer may not fabricate Evidence or convert evidence gaps
  into Evidence support.

If required attribution is absent, malformed, or unsupported, the Query
Layer must fail closed or return a limitation-only result that does not
assert the unattributed fact.

## 13. Boundary Contract

The Query Layer shall never:

- generate Repository Intelligence;
- modify Repository Intelligence;
- scan repositories;
- execute repository code;
- invoke AI providers;
- invoke Advisory;
- perform Decision Evaluation;
- perform graph reasoning;
- perform dependency analysis;
- perform change impact analysis;
- mutate Repository State;
- mutate Evidence;
- mutate runtime state;
- authorize action;
- authorize execution.

Query results are context only. They are not decisions, approvals,
Evidence, Repository State, Advisory outputs, or execution
permissions.

## 14. Failure Contract

The Query Layer must fail closed for:

- missing snapshot;
- invalid snapshot;
- corrupted artifact;
- unsupported schema version;
- invalid query;
- unsupported query;
- malformed query scope;
- unsupported query target;
- missing required attribution;
- request for inference, generation, graph traversal, dependency
  reasoning, change impact reasoning, Advisory reasoning, Decision
  Evaluation, repository scanning, or execution.

Fail-closed behavior may produce a bounded error/limitation result, but
it must not continue by guessing, scanning the repository, or asserting
unsupported facts.

## 15. Governance Contract

The Query Layer must remain compatible with:

- observe-only runtime;
- execution unavailable;
- deterministic engineering;
- auditability;
- explainability;
- reproducibility;
- human-controlled lifecycle;
- governed commit, push, phase-report, and notification discipline.

Future prototypes must be testable with fixed artifact inputs and
fixed query requests. They must not depend on live repository contents,
network availability, AI model output, or mutable runtime state.

## 16. Versioning Contract

The initial contract supports Repository Knowledge Snapshot artifacts
whose schema version is understood by the future query prototype's
contract and plan.

Future compatibility expectations:

- unsupported schema versions fail closed;
- schema-version handling must be explicit, not inferred;
- field mapping across schema versions requires a future contract or
  migration phase;
- a query result must disclose the source artifact schema version;
- future support for other Repository Intelligence artifact families
  requires an explicit contract expansion;
- no implementation may silently treat two schema versions as
  equivalent without a governed compatibility decision.

This phase implements no version negotiation, migration, validator, or
compatibility table.

## 17. Future Extensibility

Future consumers may include:

- Historical Memory Snapshot;
- Dependency Knowledge Graph;
- Change Impact;
- Advisory.

Those consumers remain outside this contract. The Query Layer may later
provide deterministic access to artifacts they consume or produce, but
it must not absorb their reasoning responsibilities or authority.

Advisory may consume future query results as context only. Change
Impact may consume future query results as input only. Dependency
Knowledge Graph work may expose graph artifacts later, but graph
traversal is outside this contract. Historical Memory may later add
artifact inputs, but historical extraction is outside this contract.

## 18. Relationship to Future Phases

- **121C — Query Contract Verification**: independently verify this
  contract for completeness, internal consistency, boundary safety,
  and sufficiency before any plan or prototype.
- **121D — Query Prototype Plan**: plan a narrow read-only query
  prototype after contract verification.
- **121E — Read-Only Query Prototype**: implement only what 121B-121D
  authorize.
- **121F — Query Prototype Verification**: independently verify the
  prototype against this contract, later plans, schemas,
  determinism, attribution, failure behavior, and governance.

No implementation guidance beyond sequencing is provided here.

## 19. Strict Non-Goals

This phase does not implement:

- query engine;
- query parser;
- query language;
- CLI;
- REST;
- API;
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
- source code changes;
- schema changes;
- test code changes.

## 20. Known Inherited Issues

Carried forward unchanged and not repaired in this phase:

- 119Q report-generation-ordering defect: non-blocking.
- 119AB phase-id comparison bug: non-blocking.
- Recurring `pending_final_telegram_delivery` reporting detail:
  non-blocking.

## 21. Acceptance

121B is complete when this contract is frozen, project memory reflects
121B completion, runtime remains `Observed` / `observe` / execution
unavailable, no implementation has occurred, and the recommended next
phase is 121C — Repository Intelligence Query Contract Verification.
