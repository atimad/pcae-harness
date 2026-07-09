# Phase 123D - Repository Intelligence Change Impact Prototype Plan

## 1. Purpose

Phase 123D defines the implementation plan for the first deterministic
Repository Intelligence Change Impact prototype.

This phase performs no implementation. It defines responsibilities,
inputs, outputs, boundaries, acceptance criteria, verification
strategy, risks, and deferred capabilities for 123E.

The prototype planned here is a deterministic, read-only Change Impact
Builder. It identifies potentially affected repository entities from
existing Repository Intelligence, consumes Repository Intelligence
exclusively through the Track 121 Query Layer, and produces
deterministic Change Impact Reports. It performs no reasoning,
prioritization, recommendation, Decision Evaluation, repository
scanning, Repository Intelligence generation, execution planning, or
execution.

## 2. Planning Baseline

This plan is constrained by:

- 123A - Repository Intelligence Change Impact Architecture;
- 123B - Repository Intelligence Change Impact Contract Freeze;
- 123C - Repository Intelligence Change Impact Contract Verification;
- Track 119 executable schemas;
- Track 120 Repository Knowledge Snapshot prototype;
- Track 121 Repository Intelligence Query Layer;
- Track 122 Repository Intelligence Advisory Consumption.

123C verified the contract as complete, internally consistent,
deterministic, architecturally aligned, governance compatible, and
implementation ready. It recorded one planning clarification that binds
this phase: 123D/123E must remain within current Query Layer
capabilities unless a future Track 121 contract amendment is explicitly
introduced. This plan therefore does not introduce relationship query
categories, graph traversal, direct snapshot reads, source scanning, or
any alternate Repository Intelligence access path.

## 3. Prototype Objective

Implement the first deterministic, read-only Change Impact Builder.

The builder shall:

- accept a bounded Change Impact request;
- translate that request into supported Track 121 Query Layer requests;
- consume Query Layer results only;
- identify potentially affected repository entities from the returned
  Repository Intelligence records by deterministic, declared criteria;
- preserve attribution for every impacted entity and relationship;
- propagate limitations unchanged;
- propagate boundary disclosures unchanged;
- assemble a deterministic Change Impact Report;
- deliver the report read-only to the caller.

The builder shall not reason about whether a change is safe, advisable,
approved, risky, or prioritized. It shall not replace Advisory
reasoning or Decision Evaluation.

## 4. Scope

The 123E prototype is scoped to:

- Repository Knowledge Snapshot artifacts supported by the Track 121
  Query Layer;
- Track 121 Query Layer results;
- the current supported Repository Knowledge Snapshot executable schema
  version, `119O.1.0-json-schema`;
- current Track 121 query categories:
  `entity_lookup`, `capability_lookup`,
  `architectural_contract_lookup`, `attribution_lookup`,
  `limitation_lookup`, and `boundary_lookup`;
- deterministic report assembly from Query Layer result content.

The 123E prototype excludes:

- Historical Memory Snapshot consumption;
- Dependency Knowledge Graph Snapshot consumption;
- any other Repository Intelligence artifact family beyond Repository
  Knowledge Snapshot;
- graph traversal;
- relationship inference;
- semantic reasoning;
- AI inference;
- repository scanning;
- direct Repository Intelligence artifact access;
- Query Layer contract expansion.

If 123E cannot identify an impact relationship through current Query
Layer capabilities, it must report the limitation or fail closed. It
must not work around the Query Layer by reading artifacts directly or
adding unsupported query categories.

## 5. Change Impact Pipeline

The 123E prototype should implement the following conceptual pipeline.
This section defines responsibilities only; it does not prescribe
classes, functions, modules, or source layout.

1. **Change request intake** - receive a bounded request describing the
   requested change, repository scope, evaluation scope, and target
   entities. Validate that the request is explicit, supported, and
   deterministic before any query is issued.
2. **Query request preparation** - translate the change request into
   one or more Track 121 Query Layer requests using only supported
   query categories. The translation is deterministic and declared.
3. **Track 121 Query Layer invocation** - invoke the existing Query
   Layer read-only surface. Repository Intelligence is not accessed by
   any other path.
4. **Candidate impact identification** - identify potentially affected
   entities from the returned Query Layer records using declared,
   deterministic criteria. The prototype may identify the target entity
   itself and records returned by supported lookups; it must not infer
   missing relationships or traverse dependency graphs.
5. **Attribution preservation** - carry attribution for every impacted
   entity and impact relationship into the report unchanged.
6. **Limitation propagation** - carry all inherited limitations into
   the report unchanged and add only strictly additive Change-Impact
   limitations.
7. **Boundary disclosure propagation** - carry boundary disclosures and
   disclaimers into the report unchanged and attach a Change
   Impact-specific non-authority disclosure.
8. **Change Impact Report assembly** - assemble impacted entities,
   impact relationships, attribution bundle, limitation bundle,
   boundary disclosure bundle, and report metadata into a deterministic
   report.
9. **Report delivery** - deliver the report read-only to the caller.
   Delivery confers no recommendation, approval, priority, state
   transition, Evidence status, Decision Evaluation result, execution
   plan, or execution authority.

## 6. Planned Components

The following conceptual components define responsibility, inputs,
outputs, and boundaries. They do not define classes, modules, file
paths, or source layout.

### 6.1 Change Request Intake

- **Responsibility:** accept and validate a bounded Change Impact
  request.
- **Inputs:** requested change, repository scope, evaluation scope,
  target entities.
- **Outputs:** validated conceptual Change Impact request, or
  fail-closed validation error.
- **Boundaries:** no Repository Intelligence access, no repository
  scanning, no free-form interpretation, no AI inference.

### 6.2 Query Preparation

- **Responsibility:** map the validated change request to supported
  Track 121 query requests.
- **Inputs:** validated Change Impact request, supported Query Layer
  category set.
- **Outputs:** deterministic list of Query Layer requests.
- **Boundaries:** no new query category, no query language, no parser,
  no direct artifact reader, no request broadening beyond declared
  evaluation scope.

### 6.3 Query Invocation

- **Responsibility:** invoke the Track 121 Query Layer and collect
  results.
- **Inputs:** repository scope expressed as the supported snapshot path
  or handle, query requests.
- **Outputs:** Query Layer results or fail-closed query failure.
- **Boundaries:** no direct Repository Knowledge Snapshot reads outside
  the Query Layer, no generator rerun, no repository scan, no mutation.

### 6.4 Candidate Impact Identification

- **Responsibility:** select potentially affected entities from Query
  Layer results by deterministic declared criteria.
- **Inputs:** Query Layer records, requested change, evaluation scope.
- **Outputs:** impacted entity candidates and impact relationship
  records.
- **Boundaries:** no dependency traversal, no inferred relationships,
  no scoring, no prioritization, no recommendation. If the Query Layer
  does not return relationship material sufficient for a candidate,
  the component records a limitation or fails closed.

### 6.5 Attribution Preservation

- **Responsibility:** preserve provenance for each impacted entity and
  relationship.
- **Inputs:** Query Layer attribution, source artifact metadata,
  selected records.
- **Outputs:** attribution bundle.
- **Boundaries:** no attribution synthesis, no attribution collapse, no
  unattributed content-bearing report entries.

### 6.6 Limitation Propagation

- **Responsibility:** propagate inherited limitations and add
  Change-Impact-specific limitations where needed.
- **Inputs:** Query Layer limitations, candidate selection constraints,
  report assembly constraints.
- **Outputs:** limitation bundle.
- **Boundaries:** no inherited limitation removal, narrowing,
  rewriting, or confidence-washing.

### 6.7 Boundary Disclosure Propagation

- **Responsibility:** preserve boundary disclosures and attach
  non-authority disclosures.
- **Inputs:** Query Layer boundary disclosures, Query Layer disclaimers,
  Change Impact non-authority wording.
- **Outputs:** boundary disclosure bundle.
- **Boundaries:** no reinterpretation as Repository State, Evidence,
  Advisory output, Decision Evaluation, recommendation, approval, or
  execution authority.

### 6.8 Report Assembly

- **Responsibility:** assemble the deterministic Change Impact Report.
- **Inputs:** impacted entities, impact relationships, attribution
  bundle, limitation bundle, boundary disclosure bundle, report
  metadata.
- **Outputs:** Change Impact Report.
- **Boundaries:** no persistence requirement, no executable schema
  change, no Advisory context placement, no Decision Evaluation output.

### 6.9 Report Delivery

- **Responsibility:** return or write the report through the approved
  123E delivery surface.
- **Inputs:** assembled report.
- **Outputs:** delivered report and delivery metadata.
- **Boundaries:** delivery is read-only and non-authoritative; it does
  not mutate Repository State, Evidence, Repository Intelligence, or
  runtime state.

## 7. Change Request Plan

The 123E prototype should support a conceptual request containing:

- **requested change** - the declared change kind and description,
  bounded to supported target entity concepts such as modification,
  removal, addition, rename, or configuration change where the target
  can be expressed in current Query Layer terms;
- **repository scope** - the Repository Knowledge Snapshot evaluated
  by the Query Layer, scoped to one snapshot per report;
- **evaluation scope** - the supported query categories and selection
  bounds used for impact identification;
- **target entities** - one or more declared entity, capability, or
  architectural contract identifiers expressible through current Query
  Layer categories.

The request model must remain implementation independent in this plan.
123E may choose concrete types and CLI/API surfaces only inside this
contract. Invalid, ambiguous, unsupported, unbounded, or
underspecified requests must fail closed before Query Layer invocation.

## 8. Change Impact Report Plan

The 123E prototype should assemble a conceptual report containing:

- **impacted entities** - deterministic impacted entity entries,
  including target identity, source query category, and inclusion
  criteria;
- **impact relationships** - deterministic relationship records
  explaining why each impacted entity appears in the report. For the
  first prototype, relationship records may be limited to declared
  target membership, exact Query Layer match, shared attribution, or
  explicitly returned record/reference material. Unsupported
  relationship discovery must be reported as a limitation or
  fail-closed condition;
- **attribution bundle** - source artifact metadata and per-entry
  provenance returned by the Query Layer;
- **limitation bundle** - inherited Query Layer limitations plus
  strictly additive Change Impact limitations;
- **boundary disclosure bundle** - inherited boundary disclosures and
  disclaimers plus Change Impact non-authority disclosure;
- **report metadata** - change request summary, repository scope,
  evaluation scope, originating query requests, result statuses,
  unknowns, assembly timestamp as metadata only, supported schema
  version, deterministic ordering key, and report generation metadata.

The report must remain descriptive. It must not encode a recommendation,
priority, approval, risk judgment, Advisory answer, Evidence artifact,
Repository State transition, Decision Evaluation output, execution
plan, or execution result.

## 9. Query Interaction Plan

Repository Intelligence shall never be accessed directly.

The 123E prototype should:

- use the existing Track 121 Query Layer entry point;
- construct bounded query requests using only existing supported
  categories;
- rely on the Query Layer for snapshot loading, schema compatibility,
  request validation, attribution collection, limitation propagation,
  boundary disclosure propagation, and fail-closed unsupported/corrupt
  input handling;
- preserve Query Layer result metadata and records without mutation;
- treat Query Layer unknowns and limitations as first-class report
  inputs;
- fail closed if Query Layer results are missing required fields or
  cannot safely support report assembly.

The prototype must not:

- read Repository Knowledge Snapshot artifact files directly;
- rerun the Track 120 generator;
- inspect repository source/test/doc/schema files for impact
  candidates;
- inspect git history for impact candidates;
- add a query category, query parser, query language, or graph
  traversal path;
- use Advisory Context Builder as an alternate Repository Intelligence
  access path.

## 10. Attribution Plan

Every impacted entity and relationship must preserve provenance.

The 123E prototype should:

- carry source artifact metadata from every relevant Query Layer result;
- retain per-record Source Attribution Records where present;
- preserve attribution individually for each impacted entity and each
  relationship;
- include attribution in report metadata only as summary, never as a
  substitute for per-entry provenance;
- fail closed or explicitly exclude with disclosed limitation when
  required attribution is missing and the remaining report still
  satisfies the contract.

No attribution loss is permitted.

## 11. Limitation Propagation Plan

All Repository Intelligence limitations must propagate unchanged into
the Change Impact Report.

The 123E prototype should:

- carry snapshot-level, query-level, record-level, and candidate-
  selection limitations into the limitation bundle unchanged;
- preserve limitations from unknown or empty Query Layer results;
- add strictly additive limitations for evaluation scope, query
  category coverage, unsupported relationship discovery, bounded
  candidate counts, or source snapshot version;
- fail closed if inherited limitations are absent, malformed, or not
  safely propagatable.

The prototype must not remove, narrow, rewrite, suppress, or
confidence-wash inherited limitations.

## 12. Boundary Propagation Plan

Boundary disclosures must remain attached throughout the pipeline.

The 123E prototype should:

- carry Query Layer boundary disclosures and disclaimers unchanged;
- attach a Change Impact non-authority disclosure to every report;
- ensure delivery surfaces preserve disclosures;
- fail closed if boundary disclosures or disclaimers are absent,
  malformed, or not safely propagatable.

The prototype must not reinterpret Repository Intelligence as
Repository State, Evidence, Advisory output, Decision Evaluation, risk
judgment, recommendation, approval, priority, execution plan, or
execution result.

## 13. Failure Plan

The 123E prototype should fail closed for:

- **invalid change request** - missing target, unsupported change kind,
  unsupported evaluation scope, ambiguous repository scope, unbounded
  request, or unsupported query category mapping;
- **invalid Query Layer result** - missing required fields, malformed
  source artifact metadata, malformed records, malformed status,
  malformed limitations, or malformed boundary content;
- **unsupported snapshot version** - Query Layer rejects the snapshot
  version or source artifact metadata reports an unsupported version;
- **unsupported entity** - target or impacted entity cannot be
  represented through current Query Layer categories;
- **missing attribution** - required provenance for content-bearing
  impacted entities or relationships is absent;
- **missing limitation** - required inherited limitations are absent or
  cannot be safely propagated;
- **missing boundary disclosure** - required boundary disclosures or
  disclaimers are absent or cannot be safely propagated;
- **corrupted Repository Intelligence response** - Query Layer reports
  corrupted, malformed, unreadable, or internally inconsistent
  Repository Intelligence.

Fail-closed handling may produce an explicit failure object or error
surface in 123E, but that surface must not appear to be a valid partial
Change Impact Report unless the contract permits disclosed exclusion.
Failures must not trigger repository scanning, Query Layer bypass,
relationship inference, AI inference, or fallback to Advisory.

## 14. Verification Plan for 123F

Phase 123F should verify the 123E prototype against 123A, 123B, 123C,
and this plan.

123F should verify:

- deterministic report generation from equivalent input;
- query exclusivity through Track 121 only;
- no direct Repository Intelligence artifact access;
- no repository scanning or git history inspection;
- no Repository Intelligence generation/modification;
- attribution preservation for impacted entities and relationships;
- limitation propagation unchanged;
- boundary disclosure propagation unchanged;
- Change Impact Report structure completeness;
- non-authority disclosures;
- fail-closed handling for every planned failure case;
- governance compatibility and runtime posture;
- no Advisory reasoning, recommendations, Decision Evaluation,
  execution planning, or execution capability;
- regression safety for Track 121 Query Layer and Track 122 Advisory
  Context Builder.

Suggested 123F validation commands should include focused prototype
tests, Query Layer regression tests, Advisory Context Builder
regression tests if shared boundaries are touched, `pcae health`,
`pcae check`, `pcae doctor task-memory`, `pcae push check`, and
`pcae runtime inspect`.

## 15. Acceptance Criteria for 123E

123E is complete only when all criteria below are met:

1. A deterministic Change Impact Builder prototype exists.
2. The prototype consumes Repository Intelligence exclusively through
   the Track 121 Query Layer.
3. The prototype supports Repository Knowledge Snapshot input through
   the Query Layer only.
4. The prototype accepts a bounded Change Impact request with requested
   change, repository scope, evaluation scope, and target entities.
5. The prototype emits deterministic Change Impact Reports with
   impacted entities, impact relationships, attribution bundle,
   limitation bundle, boundary disclosure bundle, and metadata.
6. Equivalent input produces equivalent logical reports.
7. Every impacted entity and relationship preserves provenance or the
   request fails closed.
8. Repository Intelligence limitations propagate unchanged.
9. Boundary disclosures propagate unchanged and include a Change
   Impact non-authority disclosure.
10. Unsupported relationship discovery is represented as a limitation
    or fail-closed outcome, not as inferred data.
11. All planned failure cases are covered by focused tests.
12. No direct Repository Intelligence artifact access exists outside
    the Query Layer.
13. No repository scanning, graph traversal, Historical Memory
    correlation, Dependency Knowledge Graph traversal, Advisory
    reasoning, recommendations, Decision Evaluation, execution
    planning, or execution capability is introduced.
14. Runtime remains `Observed` / `observe` / execution unavailable with
    zero runtime plugins.
15. Query Layer regression tests remain passing.
16. Advisory Context Builder regression tests remain passing if any
    shared consumption boundary is touched.
17. Project governance checks pass.

## 16. Risks and Mitigations

- **Risk: relationship discovery exceeds current Query Layer
  capability.** Mitigation: keep 123E within existing categories;
  disclose unsupported relationship discovery as a limitation or fail
  closed. Do not add categories in Track 123.
- **Risk: direct snapshot access appears simpler than Query Layer
  use.** Mitigation: make Query Layer exclusivity an acceptance
  criterion and testable invariant.
- **Risk: impact identification drifts into inference or scoring.**
  Mitigation: require declared deterministic criteria and prohibit
  confidence scores, risk judgments, recommendations, and priorities.
- **Risk: attribution is summarized away during report assembly.**
  Mitigation: require per-entry attribution and fail-closed missing
  attribution tests.
- **Risk: limitations are treated as optional report decoration.**
  Mitigation: require limitation bundle presence and unchanged
  inherited limitation propagation.
- **Risk: boundary disclosures are lost in delivery formatting.**
  Mitigation: verify every output surface includes inherited
  disclosures and Change Impact non-authority disclosure.
- **Risk: Change Impact becomes Advisory input by default.**
  Mitigation: keep Advisory coupling deferred; 123E may produce a
  report but must not place it into an Advisory context package.
- **Risk: implementation changes runtime posture.** Mitigation:
  require `pcae runtime inspect` before completion and verify zero
  runtime plugins and execution unavailable.

## 17. Deferred Capabilities

The following capabilities are explicitly deferred:

- Dependency Knowledge Graph traversal;
- Historical Memory correlation;
- Advisory recommendations;
- Decision Evaluation;
- execution planning;
- execution capability.

Future phases may propose these only through explicit governed
architecture, contract, verification, and implementation planning.
They are not authorized by this prototype plan.

## 18. Known Inherited Issues

This phase carries forward only:

- 119Q report-generation-ordering defect;
- 119AB phase-id comparison bug;
- recurring `pending_final_telegram_delivery` reporting detail;
- GitHub main-branch PR-rule bypass notification;
- missing `PCAE_NOTIFY_ENABLED` during governed push environment.

These are lifecycle/tooling issues, not Change Impact prototype scope.
They are not repaired in 123D.

## 19. Strict Non-Goals

123D does not implement:

- Change Impact engine;
- dependency graph traversal;
- recommendations;
- Advisory reasoning;
- Decision Evaluation;
- Repository Intelligence generation;
- repository scanning;
- runtime plugins;
- execution planning;
- execution capability;
- source code;
- test code;
- schema changes.

## 20. 123E Readiness

The implementation plan is sufficient for 123E to implement the first
deterministic, read-only Change Impact Builder prototype while
preserving the 123A architecture, 123B contract, and 123C verification
constraints.

123E should proceed only within this plan. If implementation discovers
that required relationship identification cannot be done through
current Track 121 Query Layer results, 123E must fail closed, limit the
prototype scope, or defer to a future Track 121 contract-expansion
phase. It must not bypass the Query Layer or expand Track 123
authority.

Recommended next phase: 123E - Repository Intelligence Change Impact
Prototype.

