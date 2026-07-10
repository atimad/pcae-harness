# Decisions

## Accepted

- Decompose the remaining Track 134 implementation (Phase 134D) into ten
  independently-verified sub-phases (134E.1–134E.10) plus a closing 134F
  whole-lifecycle verification, rather than one monolithic 134E
  implementation phase — each sub-phase implements exactly one
  architectural capability, preserves the Canonical Engineering Evidence
  → Derived Evidence Views → Renderers → Delivery authority chain, and is
  followed by its own independent verification before the next sub-phase
  begins, so implementation never becomes self-certifying. Ordered
  sub-phases by hard dependency (evidence model first, final integration
  last) rather than convenience. Mapped all fourteen 134B §34 debt items
  to a specific closing sub-phase. Did not repair any debt item or
  implement any lifecycle behavior in this planning phase. Do not begin
  134E.1 in this phase.

- Independently verify the Track 134 contract (Phase 134C) by re-deriving
  it from 134A/134B source text rather than trusting any prior report,
  including 134B.1/.2/.3's own. Zero BLOCKING findings; confirmed the
  hardening sequence preserved every frozen invariant (identity authority,
  transport independence, PFN-001, fail-closed behavior, no model-specific
  coupling); confirmed current implementation honestly discloses which of
  the twelve lifecycle stages remain unimplemented rather than silently
  claiming completeness. Recorded one NON-BLOCKING observation
  (`metadata-repair`'s canonical-report-as-ground-truth choice vs. the
  contract's target task-lineage authority) as migration input for
  134D/134E rather than repairing it now. Do not begin 134D.

- Harden three finalization-lifecycle weaknesses (Phase 134B.3) exposed by
  executing 134B.1/134B.2 themselves, rather than folding them into 134C:
  automatic delivery-configuration resolution via one fail-closed,
  channel-agnostic resolver wired into the CLI entrypoint (not a
  per-call-site fix); a narrow, one-direction, auditable
  `pcae phase metadata-repair` tool instead of unconstrained hand-editing
  of phase-completion-metadata.json; and corrected cross-agent incident
  attribution (DeepSeek -> Claude -> Codex reproduction proves a PCAE
  substrate cause, not a DeepSeek-specific one), backed by tests
  parametrized over synthetic caller identities. Confirmed rather than
  rebuilt the existing repository-transition-validator identity-conflict
  invariants, which already failed closed correctly. Did not implement a
  full receipt ledger, a multi-adapter configuration schema, or any Track
  134 lifecycle architecture — classified as debt instead. Do not begin
  134C.

- Independently verify Phase 134B.1 rather than trust its report: re-derive
  the isolation boundary from source and fresh adversarial probes not
  reused from 134B.1's own test file. Found the boundary was a five-name
  environment-variable deny-list plus one call site's master-switch check,
  while a second real dispatch call site (`pcae notify send-report`)
  bypassed that switch entirely. Repair minimally by adding one fail-closed,
  transport-independent authorization gate inside
  `pcae.core.notifications.dispatch()` keyed on an explicit local/no-network
  sink allowlist, so future adapters inherit protection automatically
  without sanitizer-list or per-callsite changes. Do not redesign the
  notification subsystem, implement Track 134's Delivery Adapter
  architecture, or begin 134C. Record the live-integration opt-in's
  dependence on production enablement and the still-missing durable
  per-attempt receipt ledger as transport-neutral Track 134 debt rather than
  repair them in this phase.

- Repair Phase 134B.1 strictly as a pytest environment-isolation defect:
  ordinary tests clear external notification enablement, sink selection,
  Telegram enablement, credentials, and destination before in-process and
  subprocess execution; separately governed live integration remains available
  only through `PCAE_TEST_ALLOW_LIVE_NOTIFICATIONS=1`. Leave production
  notification resolution, PFN-001, idempotency, adapters, and Track 134
  lifecycle architecture unchanged. Record exact external-count reconstruction
  as unavailable because no durable per-attempt Telegram ledger exists; carry
  that observability gap to 134D–134F rather than invent evidence or broaden
  this repair.

- Freeze Phase 134B as the binding contract for twelve strictly ordered,
  non-overlapping finalization stages. Bind one phase identity, Canonical
  Engineering Evidence as sole engineering authority, deterministic Evidence
  Extraction separate from View Composition, PFR-001 and rich Operator Report
  views, decision/informational/semantic-freshness correctness, verifiable
  Architecture Status, presentation-only rendering, transport-only adapters,
  complete delivery and receipts, exactly-once logical completion,
  fail-closed retry/correction, compatibility, governance, and versioning.
  Treat structural, informational, decision, and semantic freshness as four
  independent correctness dimensions. Map all fourteen confirmed debts to
  134D planning, 134E implementation, and 134F verification; repair none in
  134B. Recommended next phase: 134C independent contract verification.

- Treat Phase 134A as the architecture for a single evidence-first,
  transport-independent finalization lifecycle. Official completion occurs
  only after canonical evidence finalization, required view generation and
  rendering, final repository/governance certification, and successful or
  policy-approved durably failed required delivery with append-only receipts.
  Assign exactly one authority per concern; preserve Track 133, PFR-001,
  PFN-001, Runtime Governance, and Repository Intelligence boundaries; define
  exactly-once logical rather than physical delivery; and own stale metadata,
  duplicate identity paths, notification coupling, promotion ordering,
  architecture-status boundaries, and canonical completion-state debt in Track
  134 without repairing them in 134A. Proceed through 134B contract freeze,
  134C verification, 134D implementation plan, 134E implementation, and 134F
  verification. Do not begin 134B during 134A.

- Treat Phase 133G as the definitive planning-only implementation plan for a
  five-stage Engineering Evidence pipeline: Engineering Activity → Canonical
  Engineering Evidence → Derived Evidence Views → Rendering → Delivery
  Adapters. Canonical Engineering Evidence is the sole immutable authority;
  Phase Report, Operator Report, Changelog, Milestone, and Release artifacts
  are deterministic sibling views; renderers are lossless and transport-
  independent; adapters own only channel conversion, segmentation, retry, and
  outcomes. Use reusable manifest-based Derived Correctness validation,
  cumulative PFR structural/informational completeness, append-only delivery
  receipts for PFN-001 linkage, shadow-first activation, and no historical
  rewriting. Sequence implementation as 133H authority-bearing executable
  model, 133I verification, 133J/K views and verification, 133L rendering,
  133M delivery/PFN migration, and 133N end-to-end verification. Recommended
  next phase: 133H - Canonical Engineering Evidence Executable Model
  Implementation.

- Treat Phase 124E as the bounded implementation phase for Repository
  Intelligence Prototype Review & Hardening: consolidate duplicated
  deterministic JSON serialization and Query Layer consumer validation
  into shared internal Repository Intelligence helpers while preserving
  public interfaces, CLI behavior, schemas, serialized output
  compatibility, deterministic behavior, attribution behavior,
  limitation propagation, boundary disclosure propagation,
  fail-closed behavior, read-only behavior, Query Layer exclusivity,
  governance semantics, observe-only runtime, and execution-unavailable
  posture. Add focused tests for the shared hardening helpers and run
  Track 120-123 regressions plus fast-green. Introduce no new
  Repository Intelligence capability, artifact family, Dependency
  Knowledge Graph expansion, Historical Memory expansion, Advisory
  reasoning, recommendation, Decision Evaluation, Repository
  Intelligence generation change, Query Layer capability change, Change
  Impact capability change, execution planning, execution capability,
  runtime plugin, AI provider integration, network access, or schema
  change. Recommended next phase: 124F - Repository Intelligence
  Prototype Review & Hardening Verification.

- Treat Phase 124D as the documentation-only implementation-planning
  phase for Repository Intelligence Prototype Review & Hardening:
  define a bounded 124E plan for behavior-preserving consistency and
  maintainability improvements across Repository Knowledge Snapshot,
  Query Layer, Advisory Context Builder, and Change Impact Builder.
  Preserve deterministic outputs, schemas, CLI compatibility, public
  interfaces, attribution, limitations, boundary disclosures,
  governance semantics, read-only behavior, fail-closed behavior,
  observe-only runtime, and execution-unavailable posture. Require
  regression validation across Tracks 120-123 and independent 124F
  verification. Do not implement hardening, new Repository Intelligence
  capabilities, new artifact families, Dependency Knowledge Graph
  expansion, Historical Memory expansion, Advisory reasoning, Decision
  Evaluation, execution planning, execution capability, runtime
  plugins, source code changes, test code changes, or schema changes.
  Recommended next phase: 124E - Repository Intelligence Prototype
  Review & Hardening Implementation.

- Treat Phase 124C as the independent verification phase for the
  frozen 124B Repository Intelligence Prototype Review & Hardening
  Contract: verify contract completeness, architectural consistency
  with 124A and Tracks 119-123, review/consistency/hardening-only
  scope containment, hardening responsibility boundaries, cross-track
  consistency obligations, determinism, attribution, limitation
  propagation, boundary disclosure preservation, serialization
  compatibility, fail-closed behavior, governance compatibility,
  compatibility with Tracks 119-123, technical debt classification,
  inherited issue handling, strict non-goals, and readiness for
  124D-124F. No contract defect was found; no 124B contract
  modification, implementation hardening, source code change, test code
  change, schema change, runtime behavior change, or execution
  capability occurred. Recommended next phase: 124D - Repository
  Intelligence Prototype Review & Hardening Plan.

- Treat Phase 124B as a documentation-only contract-freeze phase for
  Repository Intelligence prototype review and hardening: freeze a
  binding contract for 124C-124F that permits consistency and quality
  improvements only across Repository Knowledge Snapshot, Query Layer,
  Advisory Context Builder, and Change Impact Builder. Preserve
  deterministic behavior, attribution, limitation propagation, boundary
  disclosures, fail-closed behavior, serialization compatibility,
  observe-only runtime, reproducibility, auditability, explainability,
  and execution-unavailable posture. Classify technical debt only into
  documentation, implementation, testing, governance, and
  lifecycle/tooling categories. Do not implement new Repository
  Intelligence capabilities, new artifact families, Dependency
  Knowledge Graph traversal, Historical Memory correlation, Advisory
  reasoning, Decision Evaluation, execution planning, execution
  capability, runtime plugins, source code, test code, or schema
  changes. Recommended next phase: 124C - Repository Intelligence
  Prototype Review & Hardening Contract Verification.

- Treat Track 124 as review-and-hardening only over the complete
  Repository Intelligence prototype stack: it may classify consistency,
  maintainability, determinism, governance, testing, and lifecycle debt
  across Tracks 120-123, but 124A introduces no new Repository
  Intelligence capability, source/test/schema change, runtime behavior,
  or execution authority.
- Treat Phase 123D as the implementation-planning phase for the first
  deterministic Repository Intelligence Change Impact prototype: plan a
  read-only Change Impact Builder that consumes Repository Intelligence
  exclusively through Track 121 Query Layer results and produces
  deterministic Change Impact Reports, with no reasoning,
  prioritization, recommendations, Decision Evaluation, Repository
  Intelligence generation, repository scanning, runtime plugins,
  execution planning, or execution capability. Scope 123E to Repository
  Knowledge Snapshot and current Query Layer capabilities only; if
  relationship discovery cannot be supported by current Query Layer
  results, the prototype must report a limitation or fail closed rather
  than bypass the Query Layer or expand Track 123 authority. Define the
  pipeline, conceptual components, change request/report plans, query
  interaction plan, attribution/limitation/boundary propagation plans,
  failure plan, 123F verification plan, 123E acceptance criteria,
  risks/mitigations, deferred capabilities, inherited issues, and
  strict non-goals. Introduce no implementation, source code change,
  test code change, or schema change. Recommended next phase: 123E -
  Repository Intelligence Change Impact Prototype.

- Treat Phase 123C as the independent verification phase for the 123B
  Repository Intelligence Change Impact Contract: verify contract
  completeness, architectural consistency against 123A and Tracks
  119-122, deterministic/read-only/descriptive scope containment,
  authority boundaries, Query Layer exclusivity, change request and
  Change Impact Report concepts, attribution preservation, limitation
  propagation, boundary disclosure preservation, determinism,
  fail-closed failure handling, governance compatibility,
  compatibility with prior Repository Intelligence tracks, future
  readiness for 123D-123F, inherited issue handling, and strict
  non-goals. Record one planning clarification: 123D/123E must remain
  within current Query Layer capabilities unless a future Track 121
  contract amendment is explicitly introduced. No contract defect was
  found; no contract modification, implementation, source code change,
  test code change, or schema change occurred. Recommended next phase:
  123D - Repository Intelligence Change Impact Prototype Plan.

- Treat Phase 123B as the contract-freeze phase for Repository
  Intelligence Change Impact: freeze the canonical contract binding for
  123C-123F, covering purpose, contract authority, implementation
  independence, architectural relationships, Change Impact permitted
  and prohibited responsibilities, Track 121 Query Layer exclusive
  access, change request concepts, Change Impact Report concepts,
  attribution preservation, limitation propagation, boundary disclosure
  preservation, determinism, fail-closed failure handling, governance
  compatibility, compatibility with Tracks 119-122, deferred
  capabilities, known inherited issues, and strict non-goals. Introduce
  no implementation, source code change, test code change, or schema
  change. Recommended next phase: 123C - Repository Intelligence Change
  Impact Contract Verification.

- Treat Phase 123A as the architecture-only phase opening Track 123:
  define Change Impact as a Repository Intelligence capability that
  identifies affected repository entities from existing Repository
  Intelligence, exclusively through the Track 121 read-only Query
  Layer, without recommendations or decision making. Define the
  eight-stage Change Impact pipeline, the change request model, the
  Change Impact Report model, attribution/limitation/boundary
  architecture, determinism architecture, governance architecture,
  failure architecture, Track 123 roadmap, and future extensibility
  (Historical Memory, Dependency Knowledge Graph, Advisory Context,
  cross-snapshot comparison) without coupling implementation to any of
  them. Introduce no implementation, source code change, test code
  change, or schema change. Recommended next phase: 123B - Repository
  Intelligence Change Impact Contract Freeze.

- Treat Phase 122F as the independent verification phase for the 122E
  Advisory Context Builder: verify architecture conformance (122A),
  contract conformance (122B), prototype plan conformance (122D), Query
  Layer integration, context package completeness, determinism,
  attribution/limitation/boundary disclosure preservation, read-only
  guarantees, and fail-closed behavior for all seven failure modes.
  During verification, found that 122E never implemented fail-closed
  handling for "missing limitation" despite it being required by 122B
  S13 and planned by 122D S12, symmetric with the already-implemented
  missing-attribution and missing-boundary-disclosure checks. Repaired
  this single genuine defect (one validation function, one call site,
  one regression test) without expanding scope. All regression suites
  (Advisory Context Builder, Query Layer, Repository Knowledge
  Snapshot, fast_green) pass, with one pre-existing, unrelated
  fast_green failure independently confirmed via `git stash` against
  unmodified HEAD. Recommended next phase: 123A - Repository
  Intelligence Change Impact Architecture.

- Treat Phase 122E as the first Track 122 implementation phase:
  implement a deterministic, read-only Advisory Context Builder under
  `src/pcae/advisory/context/`, consuming Repository Intelligence
  exclusively through the existing Track 121 `execute_query` entry
  point (no new query category, no direct artifact access,
  `src/pcae/repository_intelligence/` untouched). Name the assembled
  package `RepositoryIntelligenceContextPackage`, deliberately distinct
  from the frozen 115W `AdvisoryContextPackage`, and decide no section
  placement into it. Preserve attribution and limitations unchanged,
  propagate boundary disclosures plus a package-level non-authority
  disclaimer, and fail closed for invalid request, invalid Query Layer
  result, missing attribution, missing boundary disclosure, unsupported
  schema version, and corrupted Repository Intelligence. Add 21
  focused tests; keep Query Layer and Repository Knowledge Snapshot
  regression suites passing; keep `fast_green` green. Introduce no
  Advisory reasoning, recommendations, or Decision Evaluation
  integration. Recommended next phase: 122F - Repository Intelligence
  Advisory Consumption Verification.

- Treat Phase 122D as the implementation-planning phase for the first
  Repository Intelligence Advisory Consumption prototype: plan a
  deterministic, read-only Advisory Context Builder that consumes
  Repository Intelligence exclusively through the Track 121 Query
  Layer, scoped to Repository Knowledge Snapshot and Query Layer
  results only. Define the nine-stage consumption pipeline, nine
  planned components (responsibility/inputs/outputs/boundaries), the
  context package plan, the query interaction plan, attribution/
  limitation/boundary propagation plans, the seven-mode fail-closed
  failure plan, the 122F verification plan, 13 measurable 122E
  acceptance criteria, risks and mitigations, and deferred
  capabilities, without implementing an Advisory Context Builder,
  Advisory runtime integration, Repository Intelligence generation,
  repository scanning, query engine modifications, graph traversal,
  dependency reasoning, change impact reasoning, runtime plugins,
  execution planning, or execution capability. Recommended next phase:
  122E - Repository Intelligence Advisory Context Prototype.

- Treat Phase 122C as the independent verification phase for the
  Repository Intelligence Advisory Consumption Contract: verify
  contract completeness, architectural consistency against 122A/Track
  121/Track 120/Track 119/Advisory Runtime/observe-only runtime
  principles, scope, Advisory responsibility boundaries, the query
  contract, the context/attribution/limitation/boundary disclosure
  contracts, determinism, the seven-mode fail-closed failure contract,
  governance compatibility, and future phase readiness for 122D-122F.
  Re-derive claims independently from source (query categories, schema
  version constant, AdvisoryContextPackage shape, Advisory Runtime
  disambiguation) rather than trusting prior-phase prose. No contract
  defect found; no contract modification made; no implementation,
  source, test, or schema change occurred. Recommended next phase:
  122D - Repository Intelligence Advisory Consumption Prototype Plan.

- Treat Phase 122B as the contract-freeze phase for Advisory
  consumption of Repository Intelligence: freeze the normative
  Repository Intelligence Advisory Consumption Contract binding for
  122C-122F, covering architectural relationships, the Advisory
  responsibility contract (permitted/prohibited operations), the
  query contract (Track 121 Query Layer exclusive access), the
  context/attribution/limitation/boundary disclosure contracts, the
  determinism contract, the fail-closed failure contract, the
  governance contract, compatibility with Track 119/120/121, deferred
  capabilities, and known inherited issues. Introduce no
  implementation, source code change, test code change, or schema
  change. Recommended next phase: 122C - Repository Intelligence
  Advisory Consumption Contract Verification.

- Treat Phase 121E as the first narrow implementation phase for the
  Repository Intelligence Query Layer: implement deterministic,
  read-only querying of existing Repository Knowledge Snapshot
  artifacts only, with supported executable schema version
  `119O.1.0-json-schema`. Support bounded structured query categories
  for entity, capability, architectural contract, attribution,
  limitation, and boundary lookup, plus the smallest CLI surface
  `pcae repository-intelligence query`. Preserve attribution,
  limitations, boundary disclosures, disclaimers, source metadata,
  deterministic ordering, fail-closed compatibility, and read-only
  behavior. Do not implement other Repository Intelligence artifact
  family queries, query language/parser, graph traversal, dependency
  reasoning, change impact reasoning, Advisory integration, repository
  scanning, Repository Intelligence generation, runtime plugins, AI or
  network integration, execution planning, or execution capability.
  Recommended next phase: 121F - Repository Intelligence Query
  Prototype Verification.

- Treat Phase 121D as a documentation-only implementation-planning
  phase for the first Repository Intelligence Query prototype: plan
  deterministic, read-only querying of existing Repository Knowledge
  Snapshot artifacts only, with first supported executable schema
  version `119O.1.0-json-schema`. Define the query pipeline,
  conceptual components, lookup/filter/projection request model,
  deterministic result obligations, snapshot compatibility, attribution
  preservation, unknown handling, fail-closed failure behavior,
  read-only persistence interaction, 121F verification strategy, 121E
  acceptance criteria, risks, mitigations, deferred capabilities, and
  strict non-goals without implementing a query engine, parser, query
  language, CLI, REST/API, Python models, validators, runtime plugins,
  Repository Intelligence generation, repository scanning, graph
  traversal, dependency analysis, change impact analysis, Advisory
  integration, execution planning, or execution capability.
  Recommended next phase: 121E - Repository Intelligence Read-Only
  Query Prototype.

- Treat Phase 121C as a documentation-only independent verification of
  the frozen Repository Intelligence Query Contract: verify contract
  completeness, architectural consistency, scope, conceptual request
  and result models, supported query categories, determinism,
  attribution preservation, boundary exclusions, fail-closed failure
  behavior, governance compatibility, versioning expectations, and
  future phase readiness before implementation planning. No contract
  modifications are required. Record one future planning clarification:
  121D should choose the exact first supported Repository Knowledge
  Snapshot schema version. Do not implement a query engine, parser,
  query language, CLI, REST/API, Python models, validators, runtime
  plugins, Repository Intelligence generation, repository scanning,
  graph traversal, dependency analysis, change impact analysis,
  Advisory integration, execution planning, or execution capability.
  Recommended next phase: 121D - Repository Intelligence Query
  Prototype Plan.

- Treat Phase 121B as a documentation-only contract freeze for the
  Repository Intelligence Query Layer: freeze deterministic, read-only,
  artifact-consuming, observe-only access to existing Repository
  Intelligence artifacts, with initial support limited to Repository
  Knowledge Snapshot artifacts. Define conceptual query request and
  result models, supported query categories, determinism, attribution,
  boundary, failure, governance, versioning, extensibility, and future
  phase sequencing without implementing syntax, grammar, parser, CLI,
  REST/API, Python models, validators, runtime plugins, repository
  scanning, Repository Intelligence generation, graph traversal,
  dependency analysis, change impact analysis, Advisory integration,
  execution planning, or execution capability. Recommended next phase:
  121C - Repository Intelligence Query Contract Verification.

- Treat Phase 121A as architecture-only for a Repository Intelligence
  Query Layer: define deterministic, read-only consumption of existing
  Repository Intelligence artifacts without implementing a query
  engine, query parser, CLI, API, REST surface, Python models,
  validators, runtime plugins, repository scanning, Repository
  Intelligence generation, graph traversal, dependency analysis, change
  impact analysis, Advisory integration, execution planning, or
  execution capability. The query layer may conceptually read existing
  artifacts, validate bounded requests, perform deterministic lookup,
  filtering, selection, result assembly, attribution preservation,
  limitation preservation, and deterministic formatting only. Preserve
  the boundaries to Repository State, Evidence, Advisory, and Decision
  Evaluation. Recommended next phase: 121B - Repository Intelligence
  Query Contract Freeze.

- Treat Phase 120F as exactly one verification phase for the Phase 120E
  Repository Knowledge Snapshot prototype: independently verify
  architecture conformance, 120B contract conformance, 120C
  verification conclusion preservation, 120D plan conformance, schema
  conformance, determinism, attribution completeness, limitation and
  boundary attachment, unknown handling, persistence, read-only
  behavior, failure behavior, governance compatibility, and regression
  safety. Do not implement Historical Memory Snapshot, Dependency
  Knowledge Graph Snapshot, Change Impact Report, Advisory Context
  Package, query engine, graph traversal, runtime plugins, execution
  planning, execution capability, repository mutation beyond intended
  persistence, AI provider integration, or network access. No
  functional modifications were required. Recommended next phase:
  121A - Repository Intelligence Query Layer Architecture.

- Treat Phase 119Q as a schema-only Historical Memory Snapshot
  implementation phase: implement exactly one new standalone JSON Schema
  Draft 2020-12 artifact-family schema under
  `schemas/repository_intelligence/artifacts/historical_memory_snapshot.schema.json`.
  Build on the verified shared components from 119K/119L, the first
  family pattern verified in 119N, and the Repository Knowledge Snapshot
  pattern verified in 119P. Include the common artifact envelope
  relationship, snapshot identity, historical window, source-attributed
  historical events, historical claims, historical sources, phase
  lineage, release lineage, decision history, repair and hardening
  history, supersession and correction history, historical
  relationships, unknowns and gaps, limitations, boundary disclosures,
  disclaimers, and the Historical Memory Snapshot boundary disclaimer.
  Do not implement another artifact-family schema, validators,
  validation libraries, CLI, automated tests, Python models, Pydantic
  models, dataclasses, Repository Intelligence extraction, Repository
  Knowledge extraction, repository scanning, Historical Memory
  extraction, git history analysis, timeline generation, graph
  construction, impact analysis, Advisory behavior, Evidence behavior,
  Repository Skills behavior, Decision Evaluation behavior, runtime
  behavior, execution, enforcement, lifecycle changes, Permission
  Broker changes, repository mutation outside planned schema/docs/status
  files, automatic patch generation, automatic refactoring, or Telegram
  inbound capability. Recommended next phase: 119R - Repository
  Intelligence Executable Schema Verification: Historical Memory
  Snapshot.

- Treat Phase 119P as Repository Knowledge Snapshot verification only:
  verify
  `schemas/repository_intelligence/artifacts/repository_knowledge_snapshot.schema.json`
  against the 118A Repository Knowledge architecture, 119C conceptual
  schema architecture, 119E artifact contract, 119H executable schema
  contract, 119I verification, 119J implementation plan, 119L shared
  component verification, 119N first-family verification, and 119O
  implementation document. Confirm JSON parsing, schema declarations,
  Draft 2020-12 consistency, `$id` uniqueness, `$ref` targets, shared
  component reuse, common envelope relationship, snapshot identity,
  source-attributed repository knowledge claims, repository entities,
  entity type values, capability/subsystem summaries, knowledge
  relationships, knowledge sources, Evidence links, unknowns,
  uncertainty preservation, contract references, documentation
  references, boundary disclosures, disclaimers, `additionalProperties:
  false`, authority-creep language, documentation clarity, and no-go
  scope. Do not implement a new artifact-family schema, validators,
  validation libraries, CLI, automated tests, Python models, Pydantic
  models, dataclasses, Repository Intelligence extraction, Repository
  Knowledge extraction, repository scanning, historical memory
  extraction, graph construction, impact analysis, Advisory behavior,
  Evidence behavior, Repository Skills behavior, Decision Evaluation
  behavior, runtime behavior, execution, enforcement, lifecycle changes,
  Permission Broker changes, repository mutation outside allowed
  verification docs/status files, automatic patch generation, automatic
  refactoring, or Telegram inbound capability. No corrections were
  required. Recommended next phase: 119Q - Repository Intelligence
  Executable Schema Implementation: Historical Memory Snapshot.

- Treat Phase 119O as a schema-only Repository Knowledge Snapshot
  implementation phase: implement exactly one new standalone JSON Schema
  Draft 2020-12 artifact-family schema under
  `schemas/repository_intelligence/artifacts/repository_knowledge_snapshot.schema.json`.
  Build on the verified shared components from 119K/119L and the first
  family pattern verified in 119N. Include the common artifact envelope
  relationship, snapshot identity, source-attributed knowledge claims,
  architectural entities, capabilities, subsystems, knowledge
  relationships, knowledge sources, Evidence links, unknowns,
  limitations, contract references, documentation references, boundary
  disclosures, disclaimers, and the frozen Repository Knowledge Snapshot
  boundary disclaimer. Do not implement another artifact-family schema,
  validators, validation libraries, CLI, automated tests, Python models,
  Pydantic models, dataclasses, Repository Intelligence extraction,
  Repository Knowledge extraction, repository scanning, historical memory
  extraction, graph construction, impact analysis, Advisory behavior,
  Evidence behavior, Repository Skills behavior, Decision Evaluation
  behavior, runtime behavior, execution, enforcement, lifecycle changes,
  Permission Broker changes, repository mutation outside planned
  schema/docs files, automatic patch generation, automatic refactoring,
  or Telegram inbound capability. Recommended next phase: 119P -
  Repository Intelligence Executable Schema Verification: Repository
  Knowledge Snapshot.

- Treat Phase 119N as first-artifact-family-verification-only: verify
  `schemas/repository_intelligence/artifacts/contract_conformance_record.schema.json`
  against the frozen 119E artifact contract, 119H executable schema
  contract, 119I verification, 119J implementation plan, 119K shared
  components, 119L shared-component verification, and 119M implementation
  document without adding a second artifact-family schema, validators,
  validation libraries, CLI, automated tests, Python models, Pydantic
  models, dataclasses, extraction, graph construction, impact analysis,
  Advisory behavior, Evidence behavior, Repository Skills behavior,
  Decision Evaluation behavior, runtime behavior, execution, enforcement,
  lifecycle changes, Permission Broker changes, repository mutation
  outside planned verification documentation/status files, automatic
  patch generation, automatic refactoring, or Telegram inbound
  capability. Verify JSON parsing, schema declarations, Draft 2020-12
  consistency, `$id` uniqueness, `$ref` targets, shared component reuse,
  common envelope relationship, artifact-under-review and contract-basis
  structures, conformance checks, frozen enum values, violation
  structure, boundary disclosures, disclaimers, `additionalProperties:
  false`, authority-creep language, documentation clarity, and no-go
  scope. No corrections were required. Recommended next phase: 119O -
  Repository Intelligence Executable Schema Implementation: Repository
  Knowledge Snapshot.

- Treat Phase 119M as a narrow first-artifact-family implementation
  phase: implement exactly one standalone JSON Schema Draft 2020-12
  artifact-family schema, the Contract Conformance Record, under
  `schemas/repository_intelligence/artifacts/contract_conformance_record.schema.json`.
  Build on the verified shared components from 119K/119L, preserve the
  frozen 119E Contract Conformance Record vocabulary and disclaimer, and
  keep the schema structural and descriptive only. Update schema
  documentation and phase documentation, but do not implement additional
  artifact-family schemas, validators, validation libraries, CLI,
  automated tests, Python models, Pydantic models, dataclasses,
  extraction, graph construction, impact analysis, Advisory behavior,
  Evidence behavior, Repository Skills behavior, Decision Evaluation
  behavior, runtime behavior, execution, enforcement, lifecycle changes,
  Permission Broker changes, repository mutation outside planned
  schema/docs files, automatic patch generation, automatic refactoring,
  or Telegram inbound capability. Recommended next phase: 119N -
  Repository Intelligence Executable Schema Verification: First Artifact
  Family.

- Treat Phase 119L as shared-component-verification-only: verify the
  JSON Schema Draft 2020-12 shared Repository Intelligence components
  implemented in 119K without adding artifact-family schemas, validators,
  validation libraries, CLI, Python models, Pydantic models, dataclasses,
  fixtures, source code, test code, extraction, graph construction,
  impact analysis, Advisory behavior, Evidence behavior, Repository
  Skills behavior, Decision Evaluation behavior, runtime behavior,
  execution, enforcement, lifecycle redesign, Permission Broker changes,
  repository mutation, automatic patch generation, automatic refactoring,
  or Telegram inbound capability. Recover and document the 119K
  reporting context: the pasted handoff report was partial, but the
  canonical latest 119K report is complete and consistent; the recovered
  implementation commit is
  `b80abef6756281eb0b145bc9870de278dd7ef64a`. Verify JSON parsing,
  schema declarations, Draft 2020-12 consistency, unique `$id` values,
  `$ref` targets, required/optional/conditional field representation,
  frozen enum values, boundary disclosures, source attribution, Evidence
  links, uncertainty/verification states, conflict/supersession,
  derivation disclosure, common envelope composition, authority-creep
  language, documentation clarity, and no-go scope. No corrections were
  required. Recommended next phase: 119M — Repository Intelligence
  Executable Schema Implementation: First Artifact Family.

- Treat Phase 119K as a narrow shared-components implementation phase:
  implement standalone JSON Schema Draft 2020-12 shared components
  outside `src` under `schemas/repository_intelligence/`, following the
  119J implementation plan and preserving the frozen 119H executable
  schema contract verified in 119I and the 119E artifact contract.
  Include only common reusable components: common artifact envelope,
  repository context, phase context, release context, derivation record,
  source attribution record, Evidence link record, uncertainty /
  verification state, conflict / supersession record, boundary
  disclosure, limitation record, and disclaimers. Keep validation scope
  structural: required fields, types, enum membership, object/array
  shape, schema version constants, artifact family declarations,
  boundary disclosure presence, and required disclaimer text. Do not
  implement artifact-family schemas, validators, validation libraries,
  schema verification CLI, automated tests, fixtures, Python models,
  Pydantic models, dataclasses, repository extraction, graph
  construction, impact analysis, Advisory behavior, Evidence behavior,
  Repository Skills behavior, Decision Evaluation behavior, runtime
  behavior, execution, enforcement, lifecycle changes, Permission Broker
  changes, repository mutation outside planned schema/docs files,
  automatic patch generation, automatic refactoring, or Telegram inbound
  capability. Recommended next phase: 119L — Repository Intelligence
  Executable Schema Verification: Shared Components.

- Treat Phase 119J as executable-schema-implementation-plan-only: plan
  how PCAE should later implement Repository Intelligence executable
  schemas while preserving the frozen 119H contract verified in 119I, the
  119E artifact contract, read-only boundary, Decision Evaluation
  boundary, Evidence boundary, Repository State boundary, Advisory
  non-authority, and execution-unavailable posture. Recommend standalone
  JSON Schema outside `src` as the first schema representation, with a
  narrow first implementation slice limited to shared components. Define
  implementation principles, schema language rationale, schema family
  sequencing, future file organization, future module boundaries, staged
  validator plan, future tests, future fixtures, structural validation
  scope, semantic validation deferral, manual/future-governance deferral,
  forbidden-claim handling, versioning, migration/deprecation, artifact
  generation constraints, Repository Skills exposure deferral, Advisory
  consumer deferral, governance integration, no-go preservation, risks,
  rollback/fallback, and first implementation acceptance criteria. Do not
  implement executable schemas, JSON Schema, Pydantic models, dataclasses,
  validators, CLIs, tests, schema directories, extraction, graph
  construction, impact analysis, advisory behavior, Evidence changes,
  Repository Skills changes, Decision Evaluation changes, runtime
  behavior, execution, enforcement, Permission Broker changes, repository
  mutation, automatic patch generation, automatic refactoring, or Telegram
  inbound capability. Recommended next phase: 119K — Repository
  Intelligence Executable Schema Implementation: Shared Components.

- Treat Phase 119I as executable-schema-contract-verification-only:
  verify the frozen 119H Repository Intelligence executable schema
  contract as internally consistent, testable, future-enforceable, and
  safe against validator authority creep before any executable schema
  implementation. Verify all twelve schema families, shared components,
  common envelope expectations, field classification, structural
  validation boundaries, semantic validation boundaries,
  manual/future-governance boundaries, forbidden-claim validation
  boundaries, source attribution validation, evidence link validation,
  uncertainty/verification-state validation, conflict/supersession
  validation, derivation disclosure validation, versioning and
  compatibility, future file organization, future validator boundaries,
  future test expectations, artifact generation constraints, Repository
  Skills integration, Advisory consumer integration, Decision Evaluation
  separation, read-only/no-execution boundaries, validator authority-creep
  risk, and schema-valid artifact authority-creep risk. Do not implement
  executable schemas, JSON Schema, Pydantic models, dataclasses,
  validators, CLIs, tests, schema directories, extraction, graph
  construction, impact analysis, advisory behavior, Evidence changes,
  Repository Skills changes, Decision Evaluation changes, runtime
  behavior, execution, enforcement, Permission Broker changes, repository
  mutation, automatic patch generation, automatic refactoring, or Telegram
  inbound capability. Recommended next phase: 119J — Repository
  Intelligence Executable Schema Implementation Plan.

- Treat Phase 119H as executable-schema-contract-freeze-only: freeze the
  initial Repository Intelligence executable schema contract based on the
  119G executable schema architecture and constrained by the 119E
  artifact contract and 119F artifact-contract verification. Freeze
  executable schema purpose, non-authority, schema family inventory,
  shared schema components, common envelope representation, field
  classification, structural-validation scope, semantic/manual validation
  boundaries, forbidden-claim boundaries, source attribution, evidence
  links, uncertainty/verification, conflict/supersession, derivation,
  versioning/compatibility, validator constraints, test expectations,
  file organization, generator constraints, Repository Skills exposure,
  Advisory consumer constraints, Decision Evaluation boundary, and
  read-only/no-execution boundary. Do not implement executable schemas,
  JSON Schema, Pydantic models, dataclasses, validators, CLIs, tests,
  schema directories, extraction, graph construction, impact analysis,
  advisory behavior, Evidence changes, Repository Skills changes,
  Decision Evaluation changes, runtime behavior, execution, enforcement,
  Permission Broker changes, repository mutation, automatic patch
  generation, automatic refactoring, or Telegram inbound capability.
  Preferred next phase: 119I — Repository Intelligence Executable Schema
  Contract Verification.

- Treat Phase 119G as executable-schema-architecture-only: define how the
  frozen 119E Repository Intelligence artifact contract, verified in
  119F, should later be translated into executable schema artifacts
  without changing contract meaning, adding authority, or enabling
  execution. Future executable schemas may validate artifact structure and
  support conformance checks, but they do not decide, authorize, execute,
  enforce, replace Decision Evaluation, replace Evidence, replace
  Repository State, or expand Advisory authority. Define future schema
  families for all twelve frozen artifact families; shared schema
  components; field classification; structural, semantic, and
  manual/future-governance validation boundaries; forbidden claim, source
  attribution, evidence link, uncertainty/verification,
  conflict/supersession, derivation, versioning, compatibility, file
  organization, validator, test, generator, Repository Skills, and
  Advisory consumer architecture. Do not create executable schemas, JSON
  Schema, Pydantic models, dataclasses, validators, CLIs, tests, schema
  directories, source changes, test changes, extraction, graph
  construction, impact analysis, advisory behavior, Evidence changes,
  Repository Skills changes, Decision Evaluation changes, runtime
  behavior, execution, enforcement, Permission Broker changes, repository
  mutation, automatic patch generation, automatic refactoring, or
  Telegram inbound capability. Recommended next phase: 119H —
  Repository Intelligence Executable Schema Contract Freeze.

- Treat Phase 119F as artifact-contract-verification-only: verify that
  the frozen 119E artifact contract is internally consistent,
  contradiction-free, 119A-invariant-preserving, and ready to constrain
  future executable schema architecture, prototype planning, query/report
  artifacts, Repository Skills exposure, and Advisory consumers. Verify
  all twelve artifact family contracts, common envelope, 27 mandatory
  invariants, source attribution contract, evidence link contract,
  uncertainty/verification contract, conflict/supersession contract,
  derivation disclosure contract, versioning/snapshot contract, 24
  forbidden claims, five conformance states, and 12×10 compatibility
  matrix. Assess readiness for future phases. Include non-conformance
  examples, contract-preserving examples, and future conformance
  checklist. Do not implement executable schemas, JSON Schema, Pydantic
  models, dataclasses, validators, contract verifiers, CLIs, automated
  tests, Repository Intelligence extraction, Repository Knowledge
  extraction, Historical Memory extraction, Change Impact Analysis
  engines, Dependency Knowledge Graph construction, graph query engines,
  Advisory behavior changes, Advisory Runtime changes, Advisory Context
  Package changes, Evidence subsystem changes, Repository Skills changes,
  Decision Evaluation changes, source code, tests, runtime behavior,
  execution, authorization, enforcement, lifecycle behavior, Permission
  Broker behavior, Repository State behavior, Repository Transition
  Validator behavior, Notification Policy behavior, REST, Dashboard, Web
  UI, provider orchestration, autonomous coding, model capability
  expansion, automatic patch generation, automatic refactoring,
  repository mutation, or Telegram inbound capability.
  Recommended next phase: 119G — Repository Intelligence Executable
  Schema Architecture.
  Repository Intelligence artifact contract for all twelve conceptual
  schema families defined in 119C and reviewed in 119D, incorporating the
  six minor clarifications identified by 119D (canonical field names with
  required/optional/conditional classification, embedded-vs-referenced
  cross-cutting convention, package materialization order, Contract
  Conformance Record non-decision wording, source locator vocabulary, and
  artifact reference vocabulary). Freeze the common artifact envelope,
  per-family contracts, mandatory invariants, source attribution contract,
  evidence link contract, uncertainty/verification contract,
  conflict/supersession contract, derivation disclosure contract,
  versioning/snapshot contract, forbidden claims, conformance model,
  compatibility matrix, and future constraints. Do not create executable
  schemas, JSON Schema, Pydantic models, dataclasses, validators, contract
  verifiers, CLIs, automated tests, Repository Intelligence extraction,
  Repository Knowledge extraction, Historical Memory extraction, Change
  Impact Analysis engines, Dependency Knowledge Graph construction, graph
  query engines, Advisory behavior changes, Advisory Runtime changes,
  Advisory Context Package changes, Evidence subsystem changes, Repository
  Skills changes, Decision Evaluation changes, source code, tests, runtime
  behavior, execution, authorization, enforcement, lifecycle behavior,
  Permission Broker behavior, Repository State behavior, Repository
  Transition Validator behavior, Notification Policy behavior, REST,
  Dashboard, Web UI, provider orchestration, autonomous coding, model
  capability expansion, automatic patch generation, automatic
  refactoring, repository mutation, or Telegram inbound capability.
- Treat Phase 119D as conceptual-schema-review-only: review the 119C
  conceptual schema architecture against the 119A contract and 119B
  verification expectations, assess coherence, completeness,
  boundaries, implementation leakage, and artifact-contract-freeze
  readiness, and recommend whether to proceed to artifact contract
  freeze. Do not freeze artifact contracts, create executable schemas,
  JSON Schema, Pydantic models, dataclasses, validators, contract
  verifiers, CLIs, automated tests, extraction, graph construction,
  impact analysis, Advisory behavior changes, runtime behavior changes,
  source/test changes, execution, enforcement, lifecycle redesign,
  Permission Broker changes, repository mutation, provider
  orchestration, autonomous coding, automatic patch generation,
  automatic refactoring, or Telegram inbound capability.
- Treat Phase 119C as conceptual-schema-architecture-only: define
  implementation-independent conceptual artifact families for future
  Repository Intelligence work, including common envelope, knowledge,
  historical, graph, impact, advisory context, source attribution,
  evidence link, uncertainty/verification, conflict/supersession, query
  result, and conformance record shapes. 119C may include
  non-normative conceptual examples but must not implement executable
  schemas, JSON Schema, Pydantic models, dataclasses, validators,
  contract verifiers, CLIs, automated tests, extraction, graph
  construction, impact analysis, Advisory behavior changes, runtime
  behavior changes, source/test changes, execution, enforcement,
  lifecycle redesign, Permission Broker changes, repository mutation,
  provider orchestration, autonomous coding, automatic patch generation,
  automatic refactoring, or Telegram inbound capability.
- Treat Phase 119B as a contract-verification-documentation-only phase:
  verify that the frozen Repository Intelligence contract from 119A is
  internally consistent, testable, future-enforceable, and ready to
  constrain conceptual schema architecture / prototype planning. 119B
  may define conceptual verification checks, invariant matrices,
  non-conformance examples, contract-preserving examples, and a future
  conformance checklist. It must not implement a verifier, CLI,
  automated tests, Repository Intelligence extraction, Repository
  Knowledge extraction, Historical Memory extraction, Change Impact
  Analysis engine, Dependency Knowledge Graph construction, graph query
  engine, Advisory behavior changes, Evidence subsystem changes,
  Repository Skills changes, Decision Evaluation changes, runtime
  behavior changes, source code changes, test code changes, execution,
  shell mediation, Permission Broker changes, lifecycle redesign,
  repository mutation, provider orchestration, autonomous coding,
  automatic patch generation, automatic refactoring, or Telegram inbound
  capability.
- Treat Phase 119A as the contract-freeze-only phase for Track B
  Repository Intelligence: freeze the initial Repository Intelligence
  contract derived from 118A through 118R, including purpose, scope,
  component boundaries, shared primitive families, source attribution,
  determinism, uncertainty/conflict/supersession, versioning/snapshot,
  verification, conceptual query/report expectations, read-only
  boundary, Advisory non-authority, Decision Evaluation boundary,
  execution boundary, contract invariants, compatibility matrix, future
  phase constraints, and the minor clarifications identified by 118R.
  Do not implement extraction, graph construction, impact analysis,
  advisory behavior, schemas as executable models, runtime behavior,
  source changes, test changes, execution, enforcement, lifecycle
  redesign, Permission Broker changes, provider orchestration,
  autonomous coding, automatic patch generation, automatic refactoring,
  repository mutation, or Telegram inbound capability in 119A.
- Treat Phase 118R as the architecture-review-only closure of the
  initial Track B architecture set: 118A through 118E form one coherent
  Repository Intelligence architecture, with Repository Knowledge as the
  foundation, Historical Memory as temporal layer, Dependency Knowledge
  Graph as relationship layer, Change Impact Analysis as read-only
  change-scoped reasoning, and Advisory Reasoning Expansion as a
  non-authoritative consumer. The architecture is ready for contract
  freeze with minor clarifications around shared primitive names, source
  references, evidence links, uncertainty states, snapshot identity,
  dependency-vs-impact relationship views, and Advisory Context Package
  integration. Do not introduce implementation, extraction, graph
  construction, advisory behavior changes, contract freeze, execution,
  lifecycle redesign, or authority changes in 118R.
- Treat Phase 118E as the architecture-only Advisory Reasoning
  Expansion phase for Track B Repository Intelligence: expanded
  Advisory may consume Repository Knowledge, Historical Memory, Change
  Impact Analysis, Dependency Knowledge Graph context, Evidence,
  Repository Skills, Advisory Repository Skills, Advisory Context
  Packages, and canonical lifecycle artifacts to produce better
  explanations, recommendations, uncertainty statements, evidence-gap
  summaries, reasoning traces, and handoff context. Advisory may become
  more informed but must not become more powerful. It must not decide,
  authorize, execute, enforce, broker permissions, mutate lifecycle or
  repository state, orchestrate providers, implement advisory behavior,
  change Advisory Context Packages, implement a reasoning engine, build
  graphs, run impact analysis, extract Repository Knowledge or
  Historical Memory, generate patches, refactor automatically, or bypass
  Decision Evaluation / the Repository Transition Validator.
- Treat Phase 118D as the architecture-only Dependency Knowledge Graph
  phase for Track B Repository Intelligence: the Dependency Knowledge
  Graph is a deterministic, source-attributed, inspectable, versioned,
  read-only relationship layer inside Repository Knowledge that
  represents repository entities as graph nodes, repository-derived
  relationships as typed directional edges, and dependency assertions as
  source-backed claims. It may support Change Impact Analysis,
  Historical Memory, architectural contract mapping, Advisory context,
  repository intelligence reports, subsystem lineage inspection, and
  traceability. It must not become graph construction, a graph database,
  a graph CLI, a graph query engine, graph visualization, runtime
  orchestration, execution planning, command routing, permission
  brokering, enforcement, autonomous planning, lifecycle mutation,
  repository mutation, hidden model inference, test execution,
  automatic patch generation, automatic refactoring, or a bypass around
  Decision Evaluation / the Repository Transition Validator.
- Treat Phase 118C as the architecture-only Change Impact Analysis
  phase for Track B Repository Intelligence: Change Impact Analysis is
  deterministic, source-attributed, inspectable reasoning over
  Repository Knowledge and Historical Memory to identify what may be
  affected by a proposed or observed repository change. It may define
  impact subjects, entities, surfaces, relationships, paths, claims,
  sources, evidence links, scope, blast radius, queries, and reports;
  may produce evidence candidates; and may strengthen Advisory through
  bounded impact context. It must not become model prediction,
  autonomous planning, a decision maker, an enforcement layer, a
  Permission Broker, a lifecycle authority, an execution mechanism, a
  repository mutator, a dependency graph implementation, an impact
  extraction engine, an impact database, an impact CLI, a test runner,
  automatic patch generation, automatic refactoring, or a bypass around
  Decision Evaluation / the Repository Transition Validator.
- Treat Phase 118B as the architecture-only Historical Memory phase for
  Track B Repository Intelligence: Historical Memory is a deterministic,
  source-attributed, inspectable, versioned, read-only temporal layer
  inside Repository Knowledge that describes how repository
  architecture, capabilities, contracts, decisions, repairs, hardening,
  releases, and subsystems evolved over time. It may expose historical
  subjects, events, claims, sources, lineage, snapshots, query results,
  and evidence links; may produce evidence candidates; and may
  strengthen Advisory through bounded historical context. It must not
  become generic model/conversation memory, decide, authorize, execute,
  enforce, mutate repository state, rewrite history, promote artifacts,
  send notifications, replace governance, or bypass Decision Evaluation
  / the Repository Transition Validator.
- Treat Phase 118A as the architecture-only start of Track B
  Repository Intelligence: define Repository Knowledge as a deterministic,
  read-only, source-attributed architectural understanding layer that is
  distinct from Repository State, Evidence, Advisory Context, Repository
  Skills, and Decision Evaluation. Repository Knowledge may describe
  entities, relationships, claims, sources, snapshots, and evidence links;
  may produce evidence candidates; and may strengthen Advisory through
  bounded context selection. It must not decide, authorize, execute,
  enforce, mutate repository state, promote artifacts, send notifications,
  replace governance, or bypass Decision Evaluation / the Repository
  Transition Validator.
- Treat Phase 117E.1 as an additive corrective governance phase, not a
  history rewrite: 117E remains part of the audit trail as release
  preparation / release-attempt history, while 117E.1 verifies the real
  external publication state and publishes only the missing v0.2.0 Git
  tag and GitHub Release. Do not amend or delete historical 117E
  records. No feature, runtime behavior, architecture, execution,
  lifecycle behavior, production source, or test behavior change is
  authorized by this repair.
- Treat Phase 117E as release-only: publish the official `v0.2.0` Git
  tag and GitHub Release using the 117D release notes, update release
  metadata/status, and do not add features, change runtime behavior,
  change architecture, implement execution, modify lifecycle behavior,
  publish to PyPI, or publish packages. Package metadata may be updated
  to `0.2.0` as release metadata; this is not runtime behavior.
- Treat Phase 117D as release preparation only. Draft v0.2.0 release
  notes and refresh release-facing README/install/demo messaging to
  match the frozen v0.2 posture, but do not publish a release, create a
  tag, push a GitHub Release, publish packages, add features, change
  runtime behavior, implement execution, change architecture, or change
  lifecycle behavior. The release message must state that PCAE is
  non-executing by design, runtime state is `Observed`, execution is
  unavailable, advisory evidence does not authorize action, and PCAE is
  not an autonomous coding agent.
- Treat Phase 117C as verification-only with a narrow test-repair
  exception for proven 117B baseline regressions: real-repository
  TODO/bootstrap checks must derive the expected current recommendation
  from authoritative `PROJECT_STATUS.md` rather than hard-code a phase
  id, and 88M preflight decision assertions must use a stable fixture
  task contract rather than the real repository's active task scope. No
  production source, runtime behavior, architecture, lifecycle behavior,
  or release-preparation change is authorized by this verification.
- Treat Phase 117B as test-maintenance only: update stale/legacy test
  expectations documented by 116C/116D to match frozen v0.2 behavior
  without changing production source or weakening safety coverage.
  `PROJECT_STATUS.md` remains authoritative over `tasks/TODO.md`; real
  TODO/bootstrap tests should derive the current recommended phase from
  that source instead of hard-coding a historical phase id. Incomplete
  task-finish report promotion is expected to be quarantined by the
  Repository Transition Validator with notification dispatch skipped.
  The 88M preflight standalone issue remains classified as a
  real-repository fixture-state concern unless it reproduces with an
  active task and proves a product defect.
- Treat Phase 116C as verification-only: Phase 116B introduced no
  runtime/source regression because it changed no `src/` or `tests/`
  files. Six full-suite failures are pre-existing stale expectations.
  One full-suite failure is an intentional changed expectation caused by
  116B's roadmap scratch correction from stale 113Y-era wording to the
  116A/116B/116C v0.2 architecture-freeze track. No 116B
  architecture/runtime repair is required; stale tests may be addressed
  by a future focused test-maintenance phase before freeze if desired.
- Treat Phase 116B as documentation-only v0.2 architecture consolidation:
  structural invariants are the long-term authority for phase identity,
  metadata consistency, report completeness, recommended-next-phase
  presence, canonical promotion eligibility, notification eligibility,
  and execution-unavailability checks; the legacy finalization gate
  remains a v0.2 compatibility/trust gate until its unique
  governance-key and test-result-key checks migrate into first-class
  invariants; shared `RepositoryState` construction is the required
  future implementation shape owned by the Repository Transition
  Validator/integration layer; and Repository Event is frozen as
  policy/taxonomy only for v0.2, not a runtime type, event bus, emitter,
  or consumer subscription API. No runtime behavior, lifecycle behavior,
  execution, authorization, Permission Broker behavior, Repository
  Skill, Advisory Provider, Evidence Provider, Decision Evaluation
  behavior, Repository Transition Validator behavior, Notification
  Policy behavior, Telegram inbound, REST, Dashboard, Web UI, event bus,
  or model integration is authorized by this phase.
- Treat Phase 116A as a review-only v0.2 architecture assessment:
  the architecture is internally coherent and does not require
  significant redesign, but it should be classified as requiring minor
  consolidation before freeze because phase-identity/finalization
  checks overlap, report-completeness/recommended-next-phase
  enforcement is duplicated, `RepositoryState` is constructed at two
  equivalent call sites, and Repository Event remains policy vocabulary
  rather than a runtime type. No runtime capability, execution,
  authorization, Permission Broker change, Repository Skill, Advisory
  Provider, Evidence Provider, Decision Evaluation change, Repository
  Transition Validator change, lifecycle command change, Notification
  Policy change, Telegram inbound, REST, Dashboard, Web UI, or model
  integration is authorized by this review.
- Treat Phase 115B as an architecture-only Evidence contract freeze:
  Evidence is evaluation-scoped, referenceable by explanations, and
  contractually structured, but it does not decide, mutate repository
  state, become a kernel primitive, persist by default, authorize
  canonical mutation, or give Evidence Providers any authority beyond
  producing labelled evidence for centralized evaluation.
- Treat Phase 115A as an architecture-only explainability framework
  phase: Repository Decision remains a centralized computation over
  repository state, proposed transition, evidence, and invariants;
  Evidence becomes a first-class architectural concept but not a kernel
  primitive; Repository Skills are future evidence-only providers that
  never decide, vote, mutate state, authorize transitions, promote
  artifacts, send notifications, bypass the validator, invoke runtime
  execution, or depend on model identity.
- Treat Phase 114A as phase-report promotion hardening only: introduce a
  reusable canonical artifact promotion state machine, route phase-report
  `latest.*` writes through Certified -> Canonical promotion, and keep
  rejected/quarantined artifacts terminal and non-canonical while leaving
  notification enforcement, push check, Runtime Snapshot, Runtime Inspect,
  Permission Broker, REST, Telegram inbound, and execution out of scope.
- Treat Phase 113Z as the second Repository State Kernel enforcement phase:
  `pcae task finish --commit` may finish and commit the governed task closure,
  but canonical phase-report promotion now requires Repository Transition
  Validator acceptance through the same shared phase-report transition adapter
  used by `pcae phase complete`. Partial report evidence quarantines instead
  of writing `latest.*`; notification and push-check commands remain out of
  scope.
- Treat Phase 113Y as the first Repository State Kernel enforcement phase:
  `pcae phase complete` must request a transition from the Repository
  Transition Validator before canonical `latest.*` promotion, while task
  finish, push/check, notification enforcement, Runtime Snapshot, Runtime
  Inspect, Advisory Runtime, Permission Broker, REST, and execution remain out
  of scope.
- Treat Phase 113X as a contract-freeze phase for future Repository Transition
  Validator lifecycle integration: commands remain transition-request front
  ends, the validator is the only certification authority, the Model
  Containment Layer is model-agnostic, and no lifecycle behavior changes until
  later implementation phases.
- Treat Phase 113W as a design-only Repository Transition Validator integration phase: the human phase prompt supersedes the generated transition contract's overly narrow default scope, so 113W may edit integration design docs, documentation-completeness tests, and project memory, while continuing to forbid source behavior changes, lifecycle behavior changes, and raw git operations.
- Treat the Phase 88L task-state mismatch as legacy contract-format reconciliation, not a transition-engine defect: checkbox-based `## Status` content is visible to directory-based health reporting but is not the literal `active` status required by `pcae task transition`; close the completed legacy contract with `pcae task close`, create a separate structured 88L.1 reconciliation contract, and do not create or start 88M until reconciliation is complete.
- Treat Phase 69C agent approval as artifact-authoritative and strict: `gep-gate-006` must use `ApprovedPromptArtifact.approved_agents` as the only authoritative approval source; legacy 69B artifacts without `approved_agents` block with `reason=approved_agents_missing`; approval must not be inferred from runtime registration, installation status, contract presence, prompt approval alone, or recommended runtime.
- Treat Phase 69C as validation-only activation hardening: scope is limited to approved-agent validation (gep-gate-006), invocation-contract availability (gep-gate-007), codex-local contract verification, claude-local contract verification, and runtime contract registry consistency; execution_allowed remains False and no runtime invocation, prompt execution, or execution authorization is introduced.
- Treat IRG Challenge as awareness-only, not authority: it identifies assumptions, blind spots, inconsistencies, counterfactuals, and uncertainty that deserve human attention; it does not recommend approval or rejection, prescribe implementation, emit change lists, alter command outcomes, or create governance gates; automatic surfacing is limited to session bootstrap, phase handoff, and phase completion/control review; full detail is available only through `pcae irg-challenge` and `--json`; no persistence, acknowledgement, override, remediation, or workflow coupling is introduced by default.
- Treat strategic lineage supersession as reference-derived, not status-mutating: historical approved lineage records remain immutable append-only activation evidence even after branch current_phase advances; supersession is inferred from later `supersedes_lineage_id` references, and branch current_phase matching is enforced only for the current non-superseded active lineage record.
- Treat Phase 65J strategic continuity as governed decision lineage, not generic memory: `.pcae/strategic-lineage.json` is append-only authority only for human strategic decisions and rationale; roadmap state remains owned by `_CRI_KNOWN_PHASES`, activation evidence remains owned by provenance, and review findings remain owned by `_IRG_STRATEGIC_REVIEW_REGISTRY`; bootstrap and handoff summaries are derived and bounded; implementation approval does not imply activation approval, commit approval, or push approval; no command may create decisions, infer rationale, approve, activate phases, execute prompts, invoke runtimes, or authorize writes.
- Treat Phase Activation Governance as unresolved roadmap debt exposed by 65J: future governance must represent implementation approval, activation approval, commit approval, and push approval as separate human decisions; until that capability exists, phase activation requires explicit human language and must never be inferred from implementation approval.
- Treat Phase 65I strategic registry coherence as a severity-partitioned validation layer: authoritative registry contradictions (branch current_phase drift, invalid active-phase cardinality, unexplained CRI/CI divergence) are blocking defects that fail `pcae check`, while generated-doc drift remains non-mutating advisory drift surfaced by `pcae status coherence` and warning-only in `pcae check`/`pcae health`.
- Treat Phase 64F Orchestration Readiness Gate as a read-only future-dispatch eligibility layer over 64C orchestration entries, 64D coordination policy entries, and 64E audit records: it evaluates approval/audit/recovery/quarantine readiness and emits governed gate records and signals, but must not authorize execution, duplicate 64B generic readiness, or replace 64E audit structure.
- Treat the 64F phase transition as roadmap and prompt-governance advancement only: mark 64E completed, make 64F the active multi_runtime phase, move 65A behind 64F, and register 64F prompt profiles without introducing new runtime behavior before 64F implementation begins.
- Treat Phase 64E Orchestration Audit Model as a read-only governance layer over 64C orchestration entries and 64D coordination policy entries: it defines audit records, traceability checks, and review readiness, but must not duplicate dispatch logic, policy logic, or authorize execution.
- Treat capability projection as shared infrastructure: capability inventory and capability/roadmap intelligence must materialize their public capability records through one projection helper so IDs, fields, and command/report outputs stay stable while projection logic cannot drift independently.
- Treat Phase 64B.4A skill registry hardening as consolidation work, not a new parallel subsystem: skill discovery, metadata parsing, and registry alignment should reuse the shared intelligence infrastructure that already supports capability, roadmap, and prompt governance.
- Treat Phase 64B.4 skills as first-class governed packages stored under `.pcae/skills`: a skill is metadata plus reusable instructions/workflow references, not merely a rendered prompt, and skill invocation remains read-only with no runtime, orchestration, or write execution.
- Treat Phase 64B.3 prompt recommendations as registry-backed governance artifacts: `pcae prompt next`, `pcae prompt phase`, and `pcae prompt validate` must source phase alignment from the roadmap registry, capability alignment from the capability registry, block historical/completed/superseded/track-mismatch prompt recommendations, and remain read-only with no runtime or orchestration execution.
- Phase 62A (Controlled Runtime Execution Pilot) is the first PCAE phase where execution_allowed=True. Execution is conditionally permitted only when: runtime is shell-local, command is on the allowlist (pwd, ls, ls -la, git status, python --version, python3 --version), command is not on the denylist, no write or network operations are involved, the 30s timeout is enforced, the 100 KB output limit is enforced, and human_review_required=True. All other governance restrictions (no write execution, no network, no AI runtime invocation, no commit/push/rollback) remain in force.
- Use Python and `pathlib` for cross-platform filesystem behavior.
- Use Markdown files as the only persistence mechanism for the MVP.
- Defer databases, LLM calls, and vector search.
- Keep commands modular under `src/pcae/commands`.
- Keep `pcae inspect` read-only; reserve enforcement and repair behavior for future commands.
- Treat unvalidated sandbox isolation boundaries as advisory hardening signals that keep execution blocked; Phase 52G may recommend human-reviewed remediation but cannot apply remediation or authorize runtime execution.
- Treat Phase 52M conflict resolution as read-only classification and escalation: preserve conflicting evidence, recommend human-reviewed resolution paths, and keep automatic resolution and execution disabled.
- Keep Phase 61B runtime discovery strictly assessment-only: define discovery readiness requirements and report blockers, but do not probe the host, invoke runtimes, register runtimes, or authorize execution.
- Keep Phase 61C runtime capability inventory strictly assessment-only: classify capability status and trust level from governance inputs, but do not discover hosts, register runtimes, invoke runtimes, or authorize execution.
- Keep Phase 61D runtime trust modeling strictly assessment-only: classify trust signals and prerequisites from governance inputs, but do not assign trust automatically, discover hosts, register runtimes, invoke runtimes, or authorize execution.
- Keep Phase 61E task lifecycle governance strictly assessment-only: inspect active/done task, roadmap, and session alignment, recommend remediation when needed, but do not move tasks, rewrite session state, or mutate repository state automatically.
- Keep Phase 61F agent handoff modernization strictly assessment-only: inspect continuity requirements, summarize roadmap/runtime/governance posture, and recommend modernization when needed, but do not rewrite handoff artifacts, rewrite session state, or mutate repository state automatically.
- Keep Phase 61G roadmap continuity strictly assessment-only: validate roadmap/task/session/runtime/handoff alignment before runtime work, but do not rewrite roadmap files, rewrite session state, or mutate repository state automatically.
- Keep Phase 61H automated task transition limited to governance lifecycle automation: complete the current task, create the next task, refresh session continuity, update governance memory files, and validate coherence/health/check state, but do not invoke runtimes, execute prompts, authorize execution, commit, push, rollback, or change unrelated source behavior.
# Decisions

- Treat Phase 123F as verification-only: independently verify the
  123E Change Impact Builder against 123A-123E, regression suites, and
  observe-only governance; because no functional defect was found, make
  no source, test, schema, runtime, or behavior changes.
- Treat Phase 123E Change Impact as a Query Layer-only reporting
  implementation: the prototype may identify impacted entities only
  from directly returned Track 121 `entity_lookup` records, preserve
  attribution, propagate inherited limitations and boundary
  disclosures, and serialize deterministic reports; it must fail closed
  instead of using direct artifact access, graph traversal, source
  scanning, Advisory reasoning, recommendations, Decision Evaluation,
  execution planning, runtime plugins, AI providers, or external APIs.
- Accepted: Treat Phase 117D as release preparation only. Draft v0.2.0
  release notes and refresh release-facing README/install/demo
  messaging to match the frozen v0.2 posture, but do not publish a
  release, create a tag, push a GitHub Release, publish packages, add
  features, change runtime behavior, implement execution, change
  architecture, or change lifecycle behavior. The release message must
  state that PCAE is non-executing by design, runtime state is
  `Observed`, execution is unavailable, advisory evidence does not
  authorize action, and PCAE is not an autonomous coding agent.
