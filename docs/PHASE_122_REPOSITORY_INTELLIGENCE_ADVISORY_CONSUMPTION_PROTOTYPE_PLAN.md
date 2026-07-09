# Phase 122D - Repository Intelligence Advisory Consumption Prototype Plan

## 1. Purpose

Phase 122D defines the definitive implementation plan for the first
Repository Intelligence Advisory Consumption prototype.

The planned prototype will implement the first deterministic,
read-only Advisory Context Builder: a component that consumes
Repository Intelligence exclusively through the Track 121 read-only
Query Layer and assembles bounded, source-attributed Advisory context
packages. It consumes existing Query Layer results, selects relevant
records for a declared advisory purpose, preserves attribution,
limitations, and boundary disclosures unchanged, and assembles a
deterministic context package. It never reasons about Repository
Intelligence content, never makes a decision, and never replaces
Decision Evaluation.

This phase defines implementation planning only. It implements no
Advisory Context Builder, no Advisory runtime integration, no
Repository Intelligence generation, no repository scanning, no query
engine modification, no graph traversal, no dependency reasoning, no
change impact reasoning, no runtime plugin, no execution planning, and
no execution capability.

## 2. Planning Baseline

Initial inspection confirmed:

- `git status --short`: clean before the active 122D task contract was
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
- `pcae phase-report show --latest`: Phase 122C canonical report
  complete, pushed, `origin/main..HEAD: 0`, recommended next phase
  122D.

The active 122D task contract was created after baseline inspection:
`tasks/active/20260709-1300-phase-122d-repository-intelligence-advisory-consumption-prototype-plan.md`.

## 3. Prototype Objective

The Phase 122E prototype will implement the first deterministic,
read-only Advisory Context Builder capable of assembling Repository
Intelligence context from Track 121 Query Layer results.

The prototype objective is narrow:

- accept a bounded advisory context request declaring a query category,
  target, and advisory purpose;
- translate that request into one or more Track 121 `QueryRequest`
  calls, using only the six existing supported categories (entity,
  capability, architectural contract, attribution, limitation, boundary
  lookup);
- invoke the existing `execute_query` entry point as the sole access
  path to Repository Intelligence;
- deterministically select relevant records from the returned Query
  Result;
- preserve attribution, limitations, and boundary disclosures for every
  selected record, unchanged;
- assemble a bounded, source-attributed Advisory context package;
- fail closed for missing, unsupported, invalid, corrupted, or
  attribution-incomplete input at every stage.

The builder never performs reasoning, ranking by relevance beyond
declared query scope, inference, or decision making. It is a
consumption and assembly component, not an analysis component.

## 4. Scope

The prototype consumes only:

- Repository Knowledge Snapshot artifacts, conforming to
  `schemas/repository_intelligence/artifacts/repository_knowledge_snapshot.schema.json`,
  supported executable schema version `119O.1.0-json-schema`;
- Track 121 Query Layer results, returned by the existing
  `execute_query` entry point over the six existing supported query
  categories.

All other Repository Intelligence artifact families remain deferred:

- Historical Memory Snapshot;
- Dependency Knowledge Graph Snapshot;
- Change Impact Report;
- Advisory Intelligence Context Package (119W/119X schema) as a
  consumption input — the schema remains a downstream structural
  reference only, per 122B §8 and §16;
- Repository Intelligence Package;
- any Repository Intelligence artifact family not yet queryable through
  Track 121.

Also explicitly out of scope for this prototype:

- direct Repository Knowledge Snapshot artifact access (bypassing the
  Query Layer);
- direct repository working tree access;
- direct git history access;
- runtime state, Evidence stores, or Advisory outputs as builder input;
- network sources;
- AI model responses;
- any query category beyond the six the Query Layer already supports.

## 5. Consumption Pipeline

The planned logical pipeline has nine stages, mirroring 122A §5 and
122B's frozen contract. These are responsibilities only, not
algorithms, classes, functions, files, or command surfaces.

1. **Advisory request intake**: receive a declared, bounded advisory
   context request from a future Advisory consumer, carrying a
   declared advisory purpose and any consumption-specific bound (e.g.
   maximum record count). Intake does not itself touch Repository
   Intelligence; it only establishes that a Repository-Intelligence-
   informed advisory context is being requested and for what purpose.
2. **Repository Intelligence query preparation**: translate the
   declared advisory need into one or more bounded Track 121
   `QueryRequest` shapes (category, target, filters, projection).
   Preparation never invents a query category outside the Query
   Layer's existing six, never constructs a natural-language request,
   and never expresses a query in any new grammar or language.
3. **Read-only Query Layer invocation**: invoke the existing Track 121
   `execute_query` entry point with each prepared request against an
   existing Repository Knowledge Snapshot artifact. This stage performs
   no repository access, no artifact access, and no snapshot generation
   of its own; it is a pure pass-through to the already-verified
   read-only Query Layer.
4. **Context selection**: from each returned Query Result, select
   records relevant to the declared advisory purpose, by deterministic,
   declared criteria bounded by the query's own scope. Selection is not
   a second round of inference or filtering beyond what the Query Layer
   itself already applied.
5. **Attribution preservation**: carry forward every selected record's
   attribution (artifact provenance plus any embedded Source
   Attribution Records) unchanged into the assembled context. No
   selection, grouping, or summarization step may drop or vague-label
   attribution.
6. **Limitation propagation**: carry forward every relevant limitation
   already present in the Query Result (snapshot-level, record-level,
   or query-specific), unchanged. The builder may add new limitations
   of its own (e.g. "only N of M matching records were included"), but
   may never remove or silently narrow an inherited one.
7. **Boundary disclosure propagation**: carry forward the Query
   Result's boundary disclosures and disclaimers unchanged, so a human
   or Advisory consumer reading the assembled context sees the same
   non-authority boundary the Query Layer itself already attached.
8. **Advisory context package assembly**: assemble selected records,
   their attribution, limitations, and boundary disclosures into a
   bounded, declared-purpose Repository Intelligence context element,
   structurally ready for a future Advisory consumer to read alongside
   its other inputs — without this phase or the prototype deciding
   `AdvisoryContextPackage` section placement (deferred per 122B §8 and
   122C §17-18).
9. **Advisory delivery**: make the assembled context element available
   to whichever future Advisory consumer issued the Stage 1 request.
   Delivery is read-only handoff; it confers no authority, and the
   receiving consumer remains bound by every existing Advisory
   non-authority rule.

## 6. Planned Components

The prototype should be planned as small conceptual components. This
section names responsibilities, inputs, outputs, and boundaries only;
it does not prescribe classes, modules, source files, or command
names.

### 6.1 Advisory Request Intake Component

Responsibility:

- accept a bounded advisory context request;
- preserve declared advisory purpose and consumption-specific bounds;
- pass the request unchanged to query preparation.

Inputs:

- structured advisory context request or equivalent in-process
  representation;
- declared advisory purpose.

Outputs:

- normalized advisory request envelope for query preparation;
- intake limitation if required metadata is absent.

Boundaries:

- no Repository Intelligence access;
- no query execution;
- no natural-language interpretation;
- no advisory reasoning.

### 6.2 Query Preparation Component

Responsibility:

- translate a declared advisory request into one or more bounded
  Track 121 `QueryRequest` shapes;
- restrict translation to the Query Layer's six existing supported
  categories.

Inputs:

- normalized advisory request envelope;
- the six supported query categories defined by the Track 121 Query
  Contract.

Outputs:

- validated `QueryRequest` object(s);
- fail-closed rejection if the declared advisory need cannot be
  expressed within the six supported categories.

Boundaries:

- no new query category;
- no query language or grammar;
- no direct artifact access;
- no Query Layer modification.

### 6.3 Query Invocation Component

Responsibility:

- invoke the existing Track 121 `execute_query` entry point with each
  prepared `QueryRequest`;
- receive the returned Query Result unchanged.

Inputs:

- validated `QueryRequest` object(s);
- an existing Repository Knowledge Snapshot artifact, located and
  loaded entirely by the existing Track 121 Query Layer.

Outputs:

- Query Result(s), exactly as returned by `execute_query`;
- fail-closed propagation of any Query Layer failure (missing
  snapshot, unsupported schema version, corrupted artifact, invalid
  request).

Boundaries:

- no direct snapshot file access;
- no snapshot generation or regeneration;
- no repository scanning;
- no modification of Query Layer behavior.

### 6.4 Context Selection Component

Responsibility:

- select records from a returned Query Result relevant to the declared
  advisory purpose, by deterministic, declared criteria;
- preserve the query's own scope as the outer bound on selection.

Inputs:

- Query Result(s) from invocation;
- declared advisory purpose and selection bound (e.g. maximum record
  count).

Outputs:

- selected record subset;
- selection-criteria metadata for later assembly.

Boundaries:

- no additional inference or filtering beyond the Query Layer's own
  scope;
- no relevance ranking by anything other than declared, deterministic
  criteria;
- no graph traversal, dependency reasoning, or change impact reasoning.

### 6.5 Attribution Preservation Component

Responsibility:

- carry forward artifact provenance and embedded Source Attribution
  Records for every selected record, unchanged;
- detect missing or malformed attribution on selected content-bearing
  records.

Inputs:

- selected record subset;
- Query Result's attribution metadata.

Outputs:

- attribution-preserving selected records;
- fail-closed missing-attribution exclusion or rejection.

Boundaries:

- no fabricated attribution;
- no fabricated Evidence;
- no conversion of evidence gaps into Evidence support;
- no attribution removal for brevity.

### 6.6 Limitation Propagation Component

Responsibility:

- carry forward all relevant snapshot-level, record-level, and
  query-specific limitations from the Query Result, unchanged;
- add strictly additive consumption-specific limitations where needed.

Inputs:

- selected record subset;
- Query Result's limitation records.

Outputs:

- limitation bundle for the assembled context package.

Boundaries:

- no limitation removal or narrowing;
- no limitation suppression for brevity or confidence.

### 6.7 Boundary Disclosure Propagation Component

Responsibility:

- carry forward the Query Result's boundary disclosures and
  disclaimers, unchanged;
- add a consumption-specific non-authority disclaimer restating that
  the package is not Evidence, not Repository State, and not a
  Decision Evaluation output.

Inputs:

- selected record subset;
- Query Result's boundary disclosures and disclaimers.

Outputs:

- boundary disclosure bundle for the assembled context package.

Boundaries:

- no boundary suppression;
- no reinterpretation of Repository Intelligence as Evidence,
  Repository State, or Decision Evaluation.

### 6.8 Context Package Assembly Component

Responsibility:

- assemble selected records, attribution bundle, limitation bundle,
  boundary disclosure bundle, and advisory-facing metadata into one
  bounded, declared-purpose context package.

Inputs:

- selected records with preserved attribution;
- limitation bundle;
- boundary disclosure bundle;
- declared advisory purpose, originating query request(s), assembly
  timestamp.

Outputs:

- an assembled Advisory context package (§7).

Boundaries:

- no `AdvisoryContextPackage` section placement decision (deferred,
  §7, §16);
- no persistence as an assembly side effect unless separately
  authorized;
- no new Repository Intelligence artifact generation.

### 6.9 Advisory Delivery Component

Responsibility:

- make the assembled context package available to the requesting
  Advisory consumer;
- preserve all Advisory non-authority rules at handoff.

Inputs:

- assembled context package;
- originating advisory request identity.

Outputs:

- delivered context package.

Boundaries:

- no authority grant;
- no Decision Evaluation replacement;
- no Repository State or Evidence mutation.

## 7. Context Package Plan

The planned Advisory Context Package contains exactly the five
elements 122B §8 and 122A §6 define:

- **selected Repository Intelligence** — the deterministic subset of a
  Query Result's records chosen for inclusion, together with the
  declared selection criteria that produced it.
- **attribution bundle** — per-record and package-level provenance
  carried forward from the Query Result: source artifact identity,
  schema version, snapshot identity, and any embedded Source
  Attribution Records.
- **limitation bundle** — the full set of inherited and
  consumption-added limitations relevant to the package.
- **boundary disclosure bundle** — inherited boundary disclosures and
  disclaimers, plus a consumption-specific non-authority disclaimer.
- **advisory metadata** — bounded, non-authoritative metadata: declared
  advisory purpose, originating query request(s), assembly timestamp,
  and determinism metadata inherited from the underlying Query
  Result(s).

This plan does not define a serialization format, storage location,
Python type, class, or file layout for the context package. It does
not decide `AdvisoryContextPackage` section placement (most likely
alongside `deterministic_evidence_summary` or `artifact_references`,
per 122A §3.4); that decision is deferred to a future, explicit 115W-
contract amendment or extension phase, not to 122E.

## 8. Query Interaction Plan

The prototype interacts with the Track 121 Query Layer exclusively
through its existing `execute_query` entry point.

Planned interaction:

- every Repository Intelligence read the prototype performs is a call
  to `execute_query` with a `QueryRequest` using one of the six
  existing supported categories;
- the prototype never reads a Repository Knowledge Snapshot artifact
  file directly, never reruns the Track 120 generator, never scans
  repository source/test/doc/schema files, and never inspects git
  history;
- the prototype treats every Query Layer failure (missing snapshot,
  unsupported schema version, corrupted artifact, invalid or
  unsupported request) as its own fail-closed condition, propagated
  without repair, guessing, or workaround;
- the prototype introduces no new query category, query language, or
  change to `src/pcae/repository_intelligence/query/`.

Repository Intelligence is never accessed directly by the prototype
under any circumstance.

## 9. Attribution Plan

Every Repository Intelligence element included in Advisory context
must preserve provenance. No attribution loss is permitted.

Planned attribution behavior:

- include artifact provenance (artifact id, artifact type, snapshot id,
  executable schema version) for every selected record, exactly as
  returned by the Query Layer's `source_artifact` metadata;
- preserve embedded Source Attribution Records
  (`source_attribution` / `capability_source` fields) attached to
  selected records, never collapsed into a vague summary label;
- preserve per-record attribution when records are grouped into one
  context package — aggregation is structural grouping only;
- exclude a content-bearing record from the assembled package with a
  disclosed limitation, or fail the whole request closed, if required
  attribution is absent (§12);
- never fabricate attribution and never convert an evidence-gap marker
  into asserted Evidence support.

## 10. Limitation Propagation Plan

All Repository Intelligence limitations must propagate unchanged into
the Advisory context.

Planned limitation behavior:

- carry forward every snapshot-level, record-level, and query-specific
  limitation already present in a Query Result into the assembled
  context package's limitation bundle, unaltered;
- add strictly additive consumption-specific limitations where needed
  (e.g. "context was bounded to N records," "only entity lookup was
  queried for this advisory purpose") — additions never substitute for
  or narrow an inherited limitation;
- treat a context package with limitations as a still-valid,
  deliverable package; limitations are part of the contract, not a
  reason to withhold delivery, except where §12's failure plan
  requires fail-closed handling instead;
- never drop a limitation to make a context package shorter, cleaner,
  or more confident-sounding than its source material warrants.

## 11. Boundary Propagation Plan

Boundary disclosures must remain attached throughout the pipeline.

Planned boundary behavior:

- carry forward the source Repository Knowledge Snapshot's boundary
  disclosures and disclaimers, unchanged, from Query Result through
  final delivery (§5, Stages 3-9);
- attach a consumption-specific non-authority disclaimer to every
  assembled context package restating that it is not Evidence, not
  Repository State, and not a Decision Evaluation output;
- never let any selection, grouping, projection, or summarization step
  in the pipeline suppress a boundary disclosure or disclaimer for
  brevity;
- never reinterpret Repository Intelligence as Evidence, Repository
  State, or Decision Evaluation output at any pipeline stage.

## 12. Failure Plan

The prototype must fail closed for exactly the seven modes named by
the 122D phase request, each mapped to a specific pipeline stage:

- **Missing Repository Intelligence** — if the Query Layer invocation
  (§5, Stage 3) fails with a missing-snapshot error, the builder must
  not substitute, guess, or silently omit the requested context without
  disclosure; it must fail closed or return an explicit "Repository
  Intelligence unavailable" limitation.
- **Unsupported snapshot schema** — if the Query Layer rejects the
  snapshot as an unsupported schema version, the builder must propagate
  that rejection as a disclosed limitation, never attempt its own
  version inference or field mapping.
- **Invalid query response** — if a Query Result is malformed,
  incomplete, or otherwise fails the Query Layer's own result
  guarantees, the builder must not use it to assemble a context
  package; the request must fail closed.
- **Missing attribution** — a selected record missing required
  attribution (§9) must be excluded from the context package with a
  disclosed limitation, or the whole request must fail closed.
- **Missing limitation** — if the assembly stage (§5, Stage 8) cannot
  establish that all relevant inherited limitations were carried
  forward, the request must fail closed rather than deliver a context
  package with unverifiable limitation coverage.
- **Missing boundary disclosure** — if an assembled context package
  would omit or alter a boundary disclosure or disclaimer present in
  its source Query Result, that is treated as an assembly defect: the
  request must fail closed rather than deliver a package with a missing
  or mismatched boundary.
- **Corrupted Repository Intelligence artifact** — if the Query Layer
  reports a corrupted or unparseable snapshot, the builder must fail
  closed for that snapshot, never partially trust malformed content.

Every failure mode produces, at most, a bounded, non-authoritative
outcome: a disclosed limitation, an explicit absence, or a fail-closed
rejection — never repository scanning, AI inference, or any other means
of compensating for missing or invalid Repository Intelligence outside
the Track 121 Query Layer.

## 13. Verification Plan for 122F

Phase 122F should independently verify the 122E prototype against the
122A architecture, 122B contract, 122C verification conclusions, and
this 122D plan.

Verification surfaces:

- **Deterministic context generation**: identical Query Result(s) plus
  identical advisory context request produce identical logical context
  package across repeated runs.
- **Attribution preservation**: every content-bearing selected record
  in the assembled package preserves artifact provenance and embedded
  Source Attribution Records where present.
- **Limitation propagation**: every inherited limitation from the
  source Query Result(s) is present, unaltered, in the assembled
  package's limitation bundle; additive limitations do not replace or
  narrow inherited ones.
- **Boundary propagation**: every inherited boundary disclosure and
  disclaimer is present, unaltered, in the assembled package's boundary
  disclosure bundle; the consumption-specific non-authority disclaimer
  is present.
- **Governance compatibility**: runtime remains `Observed`, maximum
  plugin capability remains `observe`, execution remains unavailable,
  and no runtime plugin is introduced.
- **Failure handling**: each of the seven §12 failure modes fails
  closed as planned, verified against real or fixture Query Layer
  outputs (missing snapshot, unsupported schema version, invalid query
  response, missing attribution, missing limitation, missing boundary
  disclosure, corrupted artifact).
- **Read-only behavior**: context assembly does not modify Repository
  Knowledge Snapshot artifacts, Query Layer behavior, repository files,
  runtime state, Evidence, Advisory state, Repository State, or
  lifecycle state.
- **Scope discipline**: no query category beyond the existing six is
  introduced; no direct Repository Intelligence access path is
  introduced; no Historical Memory, Dependency Knowledge Graph, Change
  Impact, or Advisory Intelligence Context Package consumption is
  introduced.

## 14. Acceptance Criteria for 122E

Phase 122E is complete when the prototype demonstrably satisfies these
measurable criteria:

1. Implements only the scoped Advisory Context Builder described in
   this plan.
2. Consumes Repository Intelligence exclusively through the Track 121
   `execute_query` entry point, using only its six existing supported
   query categories.
3. Never reads a Repository Knowledge Snapshot artifact directly,
   never reruns the Track 120 generator, and never scans the
   repository.
4. Produces deterministic logical context packages for identical Query
   Result(s) and identical advisory context requests.
5. Preserves artifact provenance and embedded Source Attribution
   Records for every selected content-bearing record.
6. Propagates every relevant inherited limitation unchanged, adding
   only strictly additive consumption-specific limitations.
7. Propagates every relevant inherited boundary disclosure and
   disclaimer unchanged, plus a consumption-specific non-authority
   disclaimer.
8. Fails closed for all seven modes named in §12: missing Repository
   Intelligence, unsupported snapshot schema, invalid query response,
   missing attribution, missing limitation, missing boundary
   disclosure, and corrupted artifact.
9. Does not generate or modify Repository Intelligence artifacts.
10. Does not perform graph traversal, dependency reasoning, change
    impact reasoning, Advisory reasoning, Decision Evaluation, execution
    planning, or introduce execution capability.
11. Does not decide `AdvisoryContextPackage` section placement or wire
    into any existing Advisory Provider, Repository Skill, Decision
    Evaluation, or lifecycle command.
12. Does not change runtime posture: runtime remains `Observed`,
    maximum plugin capability remains `observe`, execution remains
    unavailable, and zero runtime plugins remain registered.
13. Includes focused tests or verification fixtures sufficient for
    122F to independently evaluate determinism, attribution,
    limitation propagation, boundary propagation, failure handling, and
    read-only behavior.

## 15. Risks and Mitigations

### 15.1 Query Category Overreach

Risk: an advisory context request may need information the six
existing Query Layer categories cannot express, tempting the prototype
to invent a seventh category.

Mitigation: fail closed for any advisory need outside the six existing
categories (§6.2); treat a genuine gap as a Track 121 contract-expansion
decision, never a unilateral Track 122 addition.

### 15.2 Attribution Loss During Assembly

Risk: assembling multiple selected records into one context package
may collapse or drop per-record attribution.

Mitigation: make attribution preservation mandatory and independently
verifiable per record (§6.5, §9); treat missing attribution as
fail-closed or limitation-only exclusion, never silent inclusion.

### 15.3 Determinism Drift

Risk: selection, grouping, or assembly ordering may depend on
filesystem order, dictionary insertion order, timestamps, or ambient
runtime state.

Mitigation: require deterministic ordering and fixed Query Result
fixtures in 122E tests and 122F verification; assembly timestamp
metadata is declared, not load-bearing for logical equality.

### 15.4 AdvisoryContextPackage Placement Creep

Risk: the prototype may be tempted to decide, or silently assume, a
specific `AdvisoryContextPackage` section placement for the assembled
context.

Mitigation: explicitly defer that decision to a future 115W-contract
amendment (§7, §16); 122E's context package remains a standalone,
unplaced structure.

### 15.5 Boundary Suppression for Readability

Risk: a human-facing rendering of the assembled context package may be
tempted to omit boundary disclosures or disclaimers for brevity.

Mitigation: treat boundary disclosure/disclaimer presence as a
mandatory, independently verifiable field of every context package
(§6.7, §11), never optional formatting.

### 15.6 Repository Scanning Temptation on Missing Data

Risk: a missing or unattributed record may tempt the implementation to
inspect repository files or git history to fill the gap.

Mitigation: enforce Query-Layer-only access (§8) and fail-closed
missing-data handling (§12); absence is reported as absence, unknown,
or limitation, never inferred or scanned for.

### 15.7 Reasoning Creep

Risk: context selection criteria may drift from deterministic, declared
filtering into implicit relevance ranking or reasoning about which
records "matter most."

Mitigation: bound selection criteria to declared, deterministic
predicates only (§6.4); any relevance judgment beyond the query's own
scope is out of scope for the builder and remains an Advisory-side
responsibility, not a builder responsibility.

## 16. Deferred Capabilities

Explicitly deferred:

- Historical Memory consumption;
- Dependency Knowledge Graph consumption;
- Change Impact consumption;
- Advisory Intelligence Context Package consumption;
- graph traversal;
- dependency reasoning;
- change impact reasoning;
- execution planning;
- execution capability;
- `AdvisoryContextPackage` section placement decision;
- context package persistence, unless separately authorized by a
  future governed phase;
- any query category beyond the Query Layer's existing six;
- Advisory runtime integration or wiring into any existing Advisory
  Provider, Repository Skill, Decision Evaluation, or lifecycle
  command.

## 17. Strict Non-Goals Confirmed

This phase did not implement:

- Advisory Context Builder;
- Advisory runtime integration;
- Repository Intelligence generation;
- repository scanning;
- query engine modifications;
- graph traversal;
- dependency reasoning;
- change impact reasoning;
- runtime plugins;
- execution planning;
- execution capability;
- source code changes;
- test code changes;
- schema changes.

## 18. Known Inherited Issues

Carried forward unchanged and not repaired in this phase:

- 119Q report-generation-ordering defect: non-blocking inherited
  tooling/reporting issue.
- 119AB phase-id comparison bug: non-blocking inherited
  tooling/reporting issue.
- Recurring `pending_final_telegram_delivery` reporting detail:
  non-blocking inherited reporting detail.

## 19. Relationship to Future Phases

- **122E - Repository Intelligence Advisory Context Prototype**:
  implement only the narrow Advisory Context Builder described in this
  plan.
- **122F - Repository Intelligence Advisory Consumption Verification**:
  independently verify the 122E prototype against 122A, 122B, 122C,
  this plan, determinism, attribution preservation, limitation
  propagation, boundary propagation, governance, and failure handling.

No additional planning or implementation work begins in this phase.

## 20. Acceptance

122D is complete when this implementation plan is documented, project
memory reflects 122D completion, runtime remains `Observed` / `observe`
/ execution unavailable, no implementation has occurred, and the
recommended next phase is 122E - Repository Intelligence Advisory
Context Prototype.
