# Phase 123B - Repository Intelligence Change Impact Contract Freeze

## 1. Purpose

Phase 123B freezes the canonical Repository Intelligence Change Impact
Contract. This contract governs deterministic identification of
potentially affected repository entities from existing Repository
Intelligence while preserving all existing governance boundaries.

This contract is binding for later Track 123 work:

- 123C - Repository Intelligence Change Impact Contract Verification;
- 123D - Repository Intelligence Change Impact Prototype Plan;
- 123E - Repository Intelligence Change Impact Prototype;
- 123F - Repository Intelligence Change Impact Prototype Verification.

The Change Impact layer's purpose is to consume already-queryable
Repository Intelligence through the Track 121 read-only Query Layer,
identify potentially affected entities for a declared change, preserve
attribution, limitations, and boundary disclosures unchanged, and
assemble deterministic Change Impact Reports. It does not generate
Repository Intelligence, does not mutate Repository State or Evidence,
does not recommend actions, does not prioritize changes, does not
replace Advisory reasoning or Decision Evaluation, and does not
introduce execution capability.

## 2. Relationship to Phase 123A Architecture

Phase 123A defined the architecture for Change Impact as a Repository
Intelligence capability: purpose, architectural relationships, scope,
the eight-stage Change Impact pipeline, change request model, Change
Impact Report model, attribution architecture, limitation architecture,
boundary architecture, determinism architecture, governance
architecture, failure architecture, future extensibility, and Track 123
roadmap.

This phase freezes that architecture into normative contract rules.
Where 123A described architectural intent, 123B makes the constraints
binding. Later Track 123 phases may choose implementation details only
inside the boundaries frozen here.

## 3. Contract Authority

This document is the canonical contract for Repository Intelligence
Change Impact. It governs 123C, 123D, 123E, and 123F unless explicitly
superseded by a future contract-amendment phase.

No later Track 123 phase may silently reinterpret this contract to
authorize Repository Intelligence generation, direct Repository
Intelligence artifact access, repository scanning, dependency graph
traversal, Historical Memory correlation, Advisory recommendations,
Decision Evaluation authority, Repository State mutation, Evidence
mutation, execution planning, or execution capability.

## 4. Implementation Independence

This contract is implementation-independent. It does not specify:

- programming language;
- classes, functions, modules, or file layout;
- Change Impact engine implementation;
- Change Impact Report persistence format;
- CLI;
- API;
- storage location;
- serialization format;
- executable schema changes.

123D may later plan implementation details, but only after 123C
verifies this contract and only inside the boundaries frozen here.

## 5. Architectural Relationships

This contract binds the following relationships, unchanged from Phase
123A:

- **Repository Knowledge Snapshot** - the current Repository
  Intelligence artifact family reachable under this contract. It is
  never accessed directly; it is reachable only through the Repository
  Intelligence Query Layer. Change Impact may not rerun the Track 120
  generator, inspect snapshot files directly, or scan the repository to
  supplement snapshot content.
- **Repository Intelligence Query Layer** - the Track 121 frozen,
  deterministic, read-only query surface. It is the exclusive access
  path from Change Impact to Repository Intelligence. Change Impact is
  a consumer of Query Layer results, not a replacement, extension, or
  alternate query path.
- **Advisory Context Builder** - the Track 122 deterministic consumer
  that assembles Repository Intelligence context packages from Query
  Layer results. Change Impact and Advisory Context are sibling
  consumers. Neither reads the other's output by default. A future
  governed phase may choose to let a Change Impact Report become
  Advisory input, but this contract does not authorize that coupling.
- **Change Impact Report** - the deterministic, non-authoritative
  report assembled by the Change Impact layer. It identifies
  potentially affected entities and relationships with attribution,
  limitations, boundary disclosures, and metadata. It is an input for
  human or future governed consumers, never a recommendation,
  approval, risk judgment, or decision.
- **Repository State** - Repository Intelligence is not Repository
  State. Change Impact never mutates Repository State, never treats a
  Change Impact Report as a Repository State transition, and never
  represents impact findings as more current than the source snapshot's
  declared generation commit and timestamp.
- **Evidence** - Repository Intelligence is not Evidence, and a Change
  Impact Report is not Evidence. Change Impact never mutates Evidence,
  never assigns Evidence IDs to impact findings, never routes impact
  findings through the Evidence Provider pipeline, and never converts
  inherited evidence gaps into asserted Evidence support.
- **Decision Evaluation** - Change Impact confers no Decision
  Evaluation authority. Any actual PCAE decision informed by a Change
  Impact Report must still pass through Decision Evaluation and the
  Repository Transition Validator's structural invariants, unchanged.
- **Runtime** - Change Impact operates entirely within the existing
  `Observed` / `observe` / execution-unavailable runtime posture. It
  introduces no runtime plugin, no new plugin capability, no execution
  planning, and no execution capability, and it leaves Runtime Inspect
  output unchanged.

## 6. Change Impact Responsibility Contract

### 6.1 Change Impact may

- consume Repository Intelligence, exclusively as returned by the
  Track 121 read-only Query Layer;
- consume Query Layer results, including bounded results assembled for
  a declared Change Impact request;
- identify potentially affected repository entities by deterministic,
  declared criteria bounded by relationships and references already
  represented in Repository Intelligence;
- preserve attribution for every impacted entity and impact
  relationship, unchanged from the Query Layer result provenance;
- preserve limitations for every impacted entity and relationship,
  unchanged from the Query Layer results, plus any Change-Impact-
  specific limitations added by report assembly;
- preserve boundary disclosures and disclaimers, unchanged from the
  Query Layer results;
- assemble deterministic Change Impact Reports suitable for a human or
  future governed consumer to read alongside other inputs.

### 6.2 Change Impact must never

- generate Repository Intelligence, in whole or in part;
- modify Repository Intelligence, including source Repository
  Knowledge Snapshot artifacts or Query Results derived from them;
- mutate Repository State;
- mutate Evidence;
- recommend actions;
- prioritize changes;
- replace Advisory reasoning;
- replace Decision Evaluation;
- introduce execution capability at any pipeline stage.

## 7. Query Contract

Repository Intelligence shall be accessed only through the Track 121
read-only Query Layer.

- Every Repository Intelligence request Change Impact issues shall be
  expressed through the Track 121 Query Layer contract and evaluated by
  the existing query surface.
- Direct Repository Intelligence access is outside this contract:
  Change Impact shall never read Repository Knowledge Snapshot artifact
  files directly, rerun the Track 120 generator, scan repository
  source/test/doc/schema files, inspect git history, or use any access
  path other than the Track 121 Query Layer.
- Change Impact may consume only the Repository Intelligence facts the
  Query Layer returns. It may not infer missing relationships,
  synthesize graph edges, or treat absence from a Query Result as proof
  of absence from the repository.
- If a later Track 123 implementation needs a query category the
  Track 121 Query Layer does not support, that is a Track 121
  contract-expansion decision. Track 123 may not introduce a new query
  category, query language, grammar, parser, or direct artifact reader
  unilaterally.

## 8. Change Request Contract

A Change Impact request is a bounded conceptual request for impact
identification. This contract defines its required concepts, not an
implementation type or schema.

A valid Change Impact request shall include:

- **change request** - the declared change under consideration,
  including the change kind where known (for example modification,
  removal, addition, rename, or configuration change). The declared
  change is caller-supplied context, not a Repository Intelligence fact
  generated by Change Impact.
- **repository scope** - the repository boundary within which impact
  identification is requested. The scope must be explicit enough to
  prevent cross-repository inference or accidental use of unrelated
  Repository Intelligence artifacts.
- **evaluation scope** - the subset of impact identification the caller
  asks Change Impact to perform, such as entity-level, capability-level,
  or contract-level impact. Evaluation scope bounds the report; it does
  not authorize direct artifact access or unsupported query behavior.
- **target entities** - the declared repository entities that are the
  subject of the change, such as known files, modules, capabilities,
  contracts, commands, schemas, or other entity identifiers already
  represented by Repository Intelligence.

Invalid, ambiguous, unsupported, or underspecified change requests must
fail closed under §14. Change Impact must not repair an invalid request
by guessing intent, broadening scope, or scanning the repository.

## 9. Change Impact Report Contract

A Change Impact Report assembled under this contract shall include:

- **impacted entities** - the deterministic set of repository entities
  identified as potentially affected by the declared change, bounded by
  the Query Layer results and declared evaluation scope;
- **impact relationships** - the deterministic relationships,
  references, or association records that explain why each impacted
  entity appears in the report, as returned by or traceable through the
  Query Layer results;
- **attribution bundle** - provenance for every impacted entity and
  impact relationship (§10);
- **limitation bundle** - all inherited and Change-Impact-specific
  limitations relevant to the report (§11);
- **boundary disclosure bundle** - all inherited boundary disclosures
  and Change-Impact-specific non-authority disclosures (§12);
- **report metadata** - bounded non-authoritative metadata, including
  the declared change request, repository scope, evaluation scope,
  originating query request(s), source artifact metadata, assembly
  timestamp, supported schema/version metadata, and determinism
  metadata.

This contract does not specify a serialization format, storage
location, Python type, CLI output shape, or executable schema for the
report. A report is valid only if it preserves all required
attribution, limitations, and boundary disclosures. A report may be
empty when no impacted entities are returned, but an empty report must
still preserve metadata, limitations, boundary disclosures, and the
reason the result is empty.

## 10. Attribution Contract

Every impacted entity and impact relationship must preserve provenance.
Loss of attribution is contract failure.

- Attribution must remain traceable to the originating Repository
  Intelligence artifact and Query Layer result, including artifact id,
  artifact type, snapshot id, executable schema version, and any
  embedded source attribution records returned by the Query Layer.
- Attribution for each impacted entity and each relationship must be
  preserved individually. Aggregating findings into one report is
  structural grouping only; it must never collapse member provenance
  into one vague or unattributed claim.
- Report metadata may summarize source artifact identity, but summary
  metadata is not a substitute for entity-level and relationship-level
  attribution.
- A content-bearing impacted entity or relationship that lacks required
  attribution must not be included unattributed. The request must fail
  closed, or the item must be excluded only if the exclusion and its
  limitation are explicitly disclosed and the remaining report still
  satisfies this contract.

## 11. Limitation Contract

All Repository Intelligence limitations must propagate unchanged.

- Snapshot-level, query-level, record-level, relationship-level, and
  boundary-specific limitations returned by the Query Layer must be
  carried into the Change Impact Report limitation bundle unaltered.
- Change Impact must not silently drop, weaken, reinterpret, shorten,
  or confidence-wash a limitation to make an impact report appear more
  complete, current, or authoritative than its source material permits.
- Change Impact may add strictly additive limitations, such as that the
  report is bounded to a declared repository scope, evaluation scope,
  supported query categories, or source snapshot version. Added
  limitations never replace, narrow, or supersede inherited
  limitations.
- A report with limitations is still a valid deliverable report unless
  §14 requires fail-closed handling.

## 12. Boundary Disclosure Contract

Boundary disclosures must propagate unchanged.

- Every Change Impact Report must carry forward source Repository
  Intelligence boundary disclosures and disclaimers unchanged.
- Change Impact must not reinterpret Repository Intelligence as
  Repository State, Evidence, Advisory output, or Decision Evaluation
  at any pipeline stage.
- A Change Impact Report must disclose its own non-authority: it
  identifies potentially affected entities from already-queryable
  Repository Intelligence; it is not a recommendation, priority list,
  approval, risk evaluation, Advisory answer, Evidence artifact,
  Repository State transition, or Decision Evaluation output.
- No formatting, grouping, projection, summarization, or report
  assembly step may suppress a boundary disclosure or disclaimer.

## 13. Determinism Contract

Equivalent Repository Intelligence input and an equivalent change
request must produce equivalent Change Impact Reports.

- Deterministic equivalence covers impacted entity identity, impact
  relationships, attribution bundle, limitation bundle, boundary
  disclosure bundle, report metadata, ordering, and serialization
  choices made by any future implementation.
- Ordering must be stable and derived from declared deterministic keys,
  not filesystem ordering, dictionary iteration accidents, wall-clock
  timing, random seeds, model output, or network state.
- Change Impact must use no probabilistic behavior, no AI inference,
  no heuristic recommendations, no inferred dependency traversal, and
  no confidence scoring.
- The assembly timestamp, if present, may differ between runs, but it
  must be clearly metadata and must not influence impact membership,
  relationship selection, attribution, limitations, or boundary
  disclosures.

## 14. Failure Contract

Change Impact must fail closed for failures that would otherwise
produce incomplete, unattributed, unsupported, or boundary-blurring
reports. A failed request must not emit a partial report that appears
valid unless the contract explicitly permits disclosed exclusion.

Fail-closed cases include:

- **unsupported snapshot** - the requested Repository Intelligence
  source is absent, unavailable, not a supported artifact family, or not
  reachable through the Track 121 Query Layer.
- **unsupported schema version** - the Repository Intelligence artifact
  or Query Layer result uses a schema version outside the supported
  contract for the implementation phase.
- **invalid change request** - the change request is ambiguous,
  underspecified, internally inconsistent, outside repository scope, or
  missing required target/evaluation information.
- **unsupported entity** - a target entity or impacted entity cannot be
  represented within supported Repository Intelligence/query concepts.
- **corrupted Repository Intelligence** - the Query Layer reports
  corrupted, malformed, unreadable, internally inconsistent, or
  contract-invalid Repository Intelligence.
- **missing attribution** - an impacted entity, relationship, source
  artifact, or content-bearing Query Layer result lacks required
  provenance.
- **missing limitation** - required limitations are absent, malformed,
  or not safely propagatable.
- **missing boundary disclosure** - required boundary disclosures or
  disclaimers are absent, malformed, or not safely propagatable.

Failure reporting may identify the failure class and the boundary that
blocked report assembly. It must not repair corrupted Repository
Intelligence, infer missing attribution, invent missing limitations,
invent missing boundary disclosures, or broaden the query to guess a
successful result.

## 15. Governance Contract

Change Impact must preserve PCAE governance constraints:

- observe-only runtime posture;
- deterministic engineering;
- explainability;
- auditability;
- reproducibility;
- execution unavailable.

Change Impact must remain readable and reviewable as a bounded
Repository Intelligence consumer. Every produced report must be
traceable to declared input, Query Layer request(s), Query Layer
result(s), attribution, limitations, boundary disclosures, and
deterministic assembly rules. Nothing in this contract grants approval
authority, write authority, runtime execution authority, or permission
to bypass PCAE lifecycle governance.

## 16. Compatibility Contract

This contract is compatible with prior Repository Intelligence tracks:

- **Track 119 executable schemas** - Track 123 consumes schema-governed
  Repository Intelligence artifacts and Query Results. This phase does
  not modify schemas, add schemas, or authorize a Change Impact Report
  executable schema.
- **Track 120 Repository Knowledge Snapshot** - Track 123 treats the
  Repository Knowledge Snapshot as the current source artifact family
  available through the Query Layer. It does not rerun the generator or
  modify snapshot persistence.
- **Track 121 Query Layer** - Track 123 accesses Repository
  Intelligence exclusively through the Query Layer and inherits its
  read-only, deterministic, attribution-preserving, limitation-
  preserving, boundary-preserving, fail-closed behavior.
- **Track 122 Advisory Consumption** - Track 123 remains a sibling
  consumer of Query Layer results. It does not alter the Advisory
  Context Builder, modify Advisory context package placement, or
  introduce Advisory recommendations.

If a later phase discovers incompatibility with these tracks, that
phase must fail closed or open a governed contract-amendment path. It
must not silently work around the incompatibility through direct
artifact access or scope expansion.

## 17. Deferred Capabilities

The following capabilities are explicitly deferred and are not
authorized by this contract:

- Dependency Knowledge Graph traversal;
- Historical Memory correlation;
- Advisory recommendations;
- Decision Evaluation;
- execution planning;
- execution capability.

Future phases may propose these capabilities only through explicit
architecture, contract, verification, and governance work. They may not
be inferred from the existence of a Change Impact Report contract.

## 18. Known Inherited Issues

This phase carries forward only the following inherited issues:

- 119Q report-generation-ordering defect;
- 119AB phase-id comparison bug;
- recurring `pending_final_telegram_delivery` reporting detail.

These issues are not repaired in 123B. They remain known inherited
tooling/reporting issues and do not expand Change Impact authority.

## 19. Strict Non-Goals

This phase does not implement:

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

## 20. 123C Readiness

123C should independently verify this contract against 123A, Track 119
schemas, the Track 120 Repository Knowledge Snapshot, the Track 121
Query Layer, the Track 122 Advisory Context Builder, and the current
runtime posture.

Verification should confirm contract completeness, architectural
consistency, strict query exclusivity, attribution preservation,
limitation propagation, boundary disclosure propagation, determinism,
fail-closed coverage, compatibility with prior tracks, inherited issue
handling, deferred capability boundaries, and absence of implementation
or scope expansion.

