# Phase 122B - Repository Intelligence Advisory Consumption Contract Freeze

## 1. Purpose

Phase 122B freezes the canonical Repository Intelligence Advisory
Consumption Contract. This contract governs how the Advisory subsystem
may consume Repository Intelligence while preserving governance
boundaries and architectural separation. It is binding for all later
Track 122 work: 122C (contract verification), 122D (prototype plan),
122E (advisory context prototype), and 122F (prototype verification).

The Advisory consumption layer's purpose is to let an Advisory
consumer read existing, already-queryable Repository Intelligence as
one more source-attributed input among many. It requests Repository
Intelligence exclusively through the Track 121 read-only Query Layer,
selects from returned Query Results, preserves attribution,
limitations, and boundary disclosures unchanged, and assembles a
bounded advisory context package. It does not generate Repository
Intelligence, does not mutate Repository State or Evidence, does not
replace Decision Evaluation, and does not introduce execution
capability.

## 2. Relationship to Phase 122A Architecture

Phase 122A defined the architecture for Advisory consumption of
Repository Intelligence: purpose, relationships to Tracks 119-121 and
to Advisory, Advisory Runtime, Repository State, Evidence, Decision
Evaluation, and Runtime, architectural scope, the nine-stage advisory
consumption pipeline, the context model, attribution/limitation/
boundary architecture, governance architecture, failure architecture,
Track 122 roadmap, and future extensibility.

This phase freezes that architecture into normative contract rules.
Where 122A described architectural intent, 122B makes the constraints
binding. Later Track 122 phases may choose implementation details only
inside the boundaries frozen here.

## 3. Contract Authority

This document is the canonical contract for Advisory consumption of
Repository Intelligence. It governs 122C, 122D, 122E, and 122F unless
explicitly superseded by a future contract-amendment phase.

No later Track 122 phase may silently reinterpret this contract to
authorize Repository Intelligence generation, direct repository
access, a new query path outside the Track 121 Query Layer, graph
traversal, dependency reasoning, change impact reasoning, Decision
Evaluation authority, Repository State mutation, Evidence mutation, or
execution capability.

## 4. Implementation Independence

This contract is implementation-independent. It does not specify:

- programming language;
- classes, functions, modules, or file layout;
- context builder implementation;
- storage format for an assembled context package;
- CLI;
- API;
- persistence implementation;
- serialization format.

122D may later plan implementation details, but only after 122C
verifies this contract and only inside the boundaries frozen here.

## 5. Architectural Relationships

This contract binds the following relationships, unchanged from Phase
122A:

- **Repository Knowledge Snapshot** — the sole Repository Intelligence
  artifact family reachable under this contract. It is never accessed
  directly; it is reachable only through the Repository Intelligence
  Query Layer.
- **Repository Intelligence Query Layer** — the Track 121 frozen,
  deterministic, read-only query surface. It is the exclusive access
  path from Advisory to Repository Intelligence. No direct artifact
  access, generator rerun, or alternate path is permitted.
- **Advisory Runtime** — architecturally distinct from Advisory
  (§5.4). Advisory Runtime reads Runtime Snapshots and produces
  read-only Advisory Results about Runtime operational state; it does
  not read Repository Intelligence and is not a consumer under this
  contract. This contract does not modify Advisory Runtime.
- **Advisory Context** — the `AdvisoryContextPackage` bundle (frozen
  115W 15-section, four-trust-class shape) assembled from Evidence,
  repository summaries, and transition context. A Repository
  Intelligence context element assembled under this contract is a
  future candidate input alongside `deterministic_evidence_summary` or
  `artifact_references`; this contract does not amend
  `AdvisoryContextPackage`'s frozen sections, trust classes, size
  limits, redaction policy, or single allowed advisory question.
- **Repository State** — Repository Intelligence is not Repository
  State. Advisory consumption never mutates Repository State, never
  treats a Query Result as a Repository State transition, and never
  represents Repository Intelligence context as more current than its
  source snapshot's declared generation commit and timestamp.
- **Evidence** — Repository Intelligence is not Evidence. Advisory
  consumption never mutates Evidence, never assigns an Evidence ID to
  Repository Intelligence content, never routes it through the
  Evidence Provider pipeline, and never converts an inherited
  evidence-gap marker into asserted Evidence support.
- **Decision Evaluation** — the Advisory consumption layer confers no
  Decision Evaluation authority. Any actual PCAE decision informed by
  Repository-Intelligence-enriched Advisory output must still pass
  through Decision Evaluation and the Repository Transition
  Validator's structural invariants, unchanged.
- **Runtime** — the Advisory consumption layer operates entirely
  within the existing `Observed` / `observe` / execution-unavailable
  runtime posture. It introduces no runtime plugin, no new plugin
  capability, no execution planning, and no execution capability, and
  it leaves Runtime Inspect output unchanged.

## 6. Advisory Responsibility Contract

### 6.1 Advisory may

- request Repository Intelligence, exclusively through the Track 121
  read-only Query Layer, using only its existing supported query
  categories;
- consume Repository Intelligence returned by the Query Layer as one
  more source-attributed input among many;
- reference Repository Intelligence in an assembled advisory context
  package, always traceable to its originating Query Result;
- preserve attribution for every referenced Repository Intelligence
  element, unchanged from the Query Result's own attribution records;
- preserve limitations for every referenced element, unchanged from
  the Query Result's own limitation records, plus any
  consumption-specific limitations the assembly step itself adds;
- preserve boundary disclosures, unchanged from the Query Result's own
  boundary content;
- assemble Repository Intelligence context — select relevant records
  from a Query Result by deterministic, declared criteria and bundle
  them with their attribution, limitations, and boundary disclosures
  into a bounded, declared-purpose context package.

### 6.2 Advisory must never

- generate Repository Intelligence, in whole or in part;
- modify Repository Intelligence, including the source Repository
  Knowledge Snapshot artifact or any Query Result derived from it;
- mutate Repository State;
- mutate Evidence;
- replace Decision Evaluation — an assembled Repository Intelligence
  context element is an input, never a decision, approval, or
  Decision Evaluation output;
- replace Repository State — a Repository Intelligence context
  element never substitutes for, overrides, or asserts a Repository
  State value or transition;
- introduce execution capability, at any pipeline stage.

## 7. Query Contract

Repository Intelligence shall be accessed only through the Track 121
read-only Query Layer.

- Every Repository Intelligence request Advisory issues shall be
  expressed in the Track 121 `QueryRequest` shape (category, target,
  filters, projection) and evaluated by the existing `execute_query`
  entry point.
- Only the Track 121 Query Layer's existing supported query categories
  (entity lookup, capability lookup, architectural contract lookup,
  attribution lookup, limitation lookup, boundary lookup) may be used.
  No new query category, query language, grammar, or parser is
  authorized by this contract.
- Direct Repository Intelligence access is outside this contract:
  Advisory shall never read a Repository Knowledge Snapshot artifact
  file directly, rerun the Track 120 generator, scan repository
  source/test/doc/schema files, inspect git history, or use any access
  path other than the Track 121 Query Layer.
- If a Track 122 implementation phase needs a query category the
  Query Layer's current six do not support, that is a Track 121
  contract-expansion decision. It is outside this contract and outside
  Track 122's authority to introduce unilaterally.

## 8. Context Contract

An Advisory context package assembled under this contract shall
include:

- **selected Repository Intelligence** — the deterministic subset of
  a Query Result's records chosen for inclusion, together with the
  declared selection criteria that produced it;
- **attribution** — the attribution bundle carried forward unchanged
  from the Query Result (§9);
- **limitation bundle** — the full set of inherited and
  consumption-added limitations relevant to the package (§10);
- **boundary disclosure bundle** — the inherited boundary disclosures
  and disclaimers, plus any consumption-specific non-authority
  disclaimer (§11);
- **metadata** — bounded, non-authoritative advisory-facing metadata:
  declared advisory purpose, originating query request(s), assembly
  timestamp, and determinism metadata inherited from the underlying
  Query Result(s).

This contract does not specify a serialization format, storage
location, or Python type for the context package. It does not
authorize placement into a specific `AdvisoryContextPackage` section;
that placement requires an explicit 115W-contract amendment or
extension phase, not this contract.

## 9. Attribution Contract

Every Repository Intelligence element included in Advisory context
must retain provenance. No attribution loss is permitted.

- Attribution must remain traceable to the originating Repository
  Knowledge Snapshot: artifact id, artifact type, snapshot id, and
  executable schema version, exactly as returned by the Track 121
  Query Layer's `source_artifact` metadata.
- Embedded Source Attribution Records (`source_attribution` /
  `capability_source` fields) must remain attached to the assembled
  context element, never collapsed into a vague summary label.
- A content-bearing record selected for advisory context that lacks
  required attribution must be excluded from the context package with
  a disclosed limitation, or the whole request must fail closed
  (§13); it must never be included unattributed.
- Aggregating multiple selected records into one context package is
  structural grouping only; attribution for each member record must
  be preserved individually, never merged into one unattributed claim.

## 10. Limitation Contract

Repository Intelligence limitations must propagate unchanged.

- Snapshot-level, record-level, and query-specific limitations already
  present in a Query Result must all be carried into the assembled
  context package's limitation bundle, unaltered.
- Advisory must not silently drop a limitation to make a context
  package shorter, cleaner, or more confident-sounding than its source
  material warrants.
- Advisory may add its own limitations (for example, that context was
  bounded to a declared number of records, or that only a subset of
  supported query categories was requested for a given advisory
  purpose). Additions are strictly additive; they never substitute for
  or narrow an inherited limitation.
- A context package with limitations is still a valid, deliverable
  context package; limitations are part of the contract, not a reason
  to withhold delivery, except where §13's failure contract requires
  fail-closed handling instead.

## 11. Boundary Disclosure Contract

Boundary disclosures must propagate unchanged. Advisory must not
reinterpret Repository Intelligence as authoritative state or
evidence.

- Every context package must carry forward the source Repository
  Knowledge Snapshot's boundary disclosures and disclaimers, unchanged,
  regardless of query category or result status.
- Advisory must not treat a Repository Intelligence context element as
  Evidence (§5), as Repository State (§5), or as a Decision Evaluation
  output (§5) at any pipeline stage — not during selection, not during
  assembly, and not after delivery to a receiving Advisory consumer.
- A context package's advisory-facing metadata must make its
  non-authority explicit: it is context that may inform Advisory
  reasoning, never a conclusion, recommendation, or approval in its
  own right.
- No formatting, grouping, projection, or summarization step anywhere
  in the pipeline may suppress a boundary disclosure or disclaimer for
  brevity.

## 12. Determinism Contract

Equivalent Repository Intelligence input must produce equivalent
Advisory context.

> identical Query Result(s) + identical advisory context request =
> identical logical advisory context package.

The Advisory consumption layer must not use:

- inference;
- probabilistic scoring or behavior;
- AI augmentation or AI model calls;
- semantic summarization;
- randomness;
- time-dependent result content beyond declared assembly-timestamp
  metadata;
- filesystem ordering;
- ambient runtime state;
- network calls;
- hidden mutable caches;
- non-deterministic tie breaking.

Selection, attribution preservation, limitation propagation, boundary
propagation, and assembly must all be deterministic. If an advisory
context request cannot be evaluated deterministically, it must fail
closed.

## 13. Failure Contract

The Advisory consumption layer must fail closed for each of the
following. Fail-closed behavior may produce a bounded error or
limitation-disclosed outcome, but it must never scan the repository,
invoke AI inference, or otherwise compensate for missing or invalid
Repository Intelligence by any means other than the Track 121 Query
Layer.

- **Unsupported snapshot** — if the underlying Query Layer call
  reports the snapshot as unsupported, Advisory must propagate that
  rejection as a disclosed limitation; it must never attempt its own
  version inference or field mapping.
- **Unsupported schema version** — if the Query Layer rejects the
  snapshot's executable schema version, Advisory must propagate that
  rejection unchanged; it must never guess a compatible mapping.
- **Corrupted Repository Intelligence** — if the Query Layer reports a
  corrupted or unparseable snapshot, Advisory must fail closed for
  that snapshot; it must never partially trust malformed content.
- **Missing attribution** — a selected record missing required
  attribution must be excluded from the context package with a
  disclosed limitation, or the whole request must fail closed (§9); it
  must never be included unattributed.
- **Missing limitation** — if the assembly stage cannot establish that
  all relevant inherited limitations were carried forward, the request
  must fail closed rather than deliver a context package with
  unverifiable limitation coverage (§10).
- **Missing boundary disclosure** — if an assembled context package
  would omit or alter a boundary disclosure or disclaimer present in
  its source Query Result, that is treated as an assembly defect: the
  request must fail closed rather than deliver a package with a
  missing or mismatched boundary (§11).
- **Invalid query result** — a Query Result that is malformed,
  incomplete, or otherwise fails Track 121's own result guarantees
  must not be used to assemble a context package; the request must
  fail closed.

Every failure mode still produces, at most, a bounded, non-
authoritative outcome: a disclosed limitation, an explicit absence, or
a fail-closed rejection.

## 14. Governance Contract

The Advisory consumption layer must preserve:

- observe-only runtime posture, unchanged from Track 121;
- execution unavailable, unchanged from Track 121;
- maximum plugin capability `observe`, with zero runtime plugins
  introduced;
- deterministic engineering (§12);
- auditability — context package assembly must be traceable back to
  specific Query Layer calls and their inputs;
- explainability — every context package must be explainable in terms
  of its originating advisory request, the query request(s) it
  translated to, the selected records, and the preserved attribution,
  limitations, and boundaries;
- reproducibility — a context package assembled twice from the same
  Repository Knowledge Snapshot and the same advisory request must be
  logically identical;
- human-controlled lifecycle;
- governed commit, push, phase-report, and notification discipline.

## 15. Compatibility Contract

This contract is compatible with, and does not modify:

- **Track 119 schemas** — `repository_knowledge_snapshot.schema.json`
  and `advisory_intelligence_context_package.schema.json` remain
  unmodified. The latter is a downstream structural reference only,
  not an authorized generator target.
- **Track 120 Repository Knowledge Snapshot** — remains the only
  Repository Intelligence artifact family reachable under this
  contract, reachable exclusively through the Track 121 Query Layer.
- **Track 121 Query Layer** — remains the exclusive, unmodified access
  path. This contract introduces no new query category, no query
  language, and no change to
  `src/pcae/repository_intelligence/query/`.

## 16. Deferred Capabilities

The following are explicitly deferred and outside this contract:

- Historical Memory consumption;
- Dependency Knowledge Graph consumption;
- Change Impact consumption;
- Advisory Intelligence Context Package consumption (structural
  alignment with the 119W/119X schema remains a future decision, not
  authorized here);
- graph traversal;
- dependency reasoning;
- change impact reasoning;
- execution planning;
- execution capability.

A future Track 121 contract expansion may make any of the above
artifact families queryable; this contract does not pre-authorize
Advisory consumption of them.

## 17. Known Inherited Issues

Carried forward unchanged and not repaired in this phase:

- 119Q report-generation-ordering defect: non-blocking.
- 119AB phase-id comparison bug: non-blocking.
- Recurring `pending_final_telegram_delivery` reporting detail:
  non-blocking.

## 18. Relationship to Future Phases

- **122C — Repository Intelligence Advisory Consumption Contract
  Verification**: independently verify this contract for completeness,
  internal consistency, boundary safety, and sufficiency before any
  plan or prototype.
- **122D — Repository Intelligence Advisory Consumption Prototype
  Plan**: plan a narrow advisory-context-assembly prototype after
  contract verification, without implementation.
- **122E — Repository Intelligence Advisory Context Prototype**:
  implement only what 122B-122D authorize.
- **122F — Repository Intelligence Advisory Consumption Verification**:
  independently verify the prototype against this contract, the plan,
  schemas, determinism, attribution, boundary, and governance
  boundaries.

No implementation guidance beyond sequencing is provided here.

## 19. Strict Non-Goals

This phase does not implement:

- Advisory context builder;
- Repository Intelligence integration;
- runtime changes;
- source code;
- test code;
- schema changes;
- query changes;
- Repository Intelligence generation;
- repository scanning;
- graph traversal;
- dependency reasoning;
- change impact reasoning;
- execution planning;
- execution capability.

## 20. Acceptance

122B is complete when this contract is frozen, project memory reflects
122B completion, runtime remains `Observed` / `observe` / execution
unavailable, no implementation has occurred, and the recommended next
phase is 122C — Repository Intelligence Advisory Consumption Contract
Verification.
