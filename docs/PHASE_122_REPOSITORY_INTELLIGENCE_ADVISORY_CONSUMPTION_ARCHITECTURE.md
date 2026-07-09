# Phase 122A - Repository Intelligence Advisory Consumption Architecture

## 1. Purpose

Phase 122A defines the architecture for how the Advisory subsystem may
consume Repository Intelligence as structured advisory context.

Track 119 defined and implemented the executable Repository
Intelligence schema line. Track 120 generated and verified the first
Repository Intelligence artifact instance family, the Repository
Knowledge Snapshot. Track 121 implemented and verified a deterministic,
read-only Query Layer over that artifact. Repository Intelligence can
now be generated and deterministically queried, but nothing in PCAE
today wires that queried content into Advisory reasoning.

Track 122 begins that wiring, at the architecture level only. Repository
Intelligence must become structured advisory context: bounded,
source-attributed, limitation-preserving, boundary-disclosed input that
an Advisory consumer may read alongside its other inputs. Repository
Intelligence must never become Advisory reasoning itself, must never
gain decision authority, and must never bypass the read-only Query
Layer that Track 121 already froze as the only sanctioned access path
into Repository Knowledge Snapshot artifacts.

122A implements no query changes, no Advisory Runtime changes, no
Advisory Context Package changes, no context builder, no Repository
Intelligence generation, no repository scanning, no graph traversal,
no dependency reasoning, no change impact reasoning, no runtime
plugins, no execution planning, and no execution capability.

## 2. Track 122 Purpose

Track 122 answers the question Track 121 deliberately deferred: 121A
§15 named Advisory as a future consumer of Query Layer output but
explicitly refused to couple implementation to it ("future consumers
may read Query Layer outputs, but they may not make the Query Layer
responsible for their reasoning, authority, or execution behavior").
Track 122 is where that future consumer relationship gets designed.

Repository Intelligence becomes structured advisory context through
exactly one path: an Advisory consumer issues a bounded Repository
Intelligence query request, the Track 121 Query Layer evaluates it
against an existing Repository Knowledge Snapshot artifact and returns
a deterministic Query Result, and an Advisory consumption layer selects
from that result, preserves its attribution/limitations/boundary
disclosures, and assembles them into an advisory context package
element. Nothing about this path lets Repository Intelligence assert a
new fact, resolve an unknown, or upgrade its own authority by being
consumed.

Repository Intelligence may enrich Advisory context. It must never
replace Advisory reasoning or Decision Evaluation. An Advisory consumer
that reads Repository Intelligence context is reading one more
source-attributed input among many (deterministic Evidence summaries,
repository summaries, transition context — see §3.6 below); Repository
Intelligence context does not out-rank, override, or substitute for any
of those existing inputs, and it does not grant the Advisory consumer
any new authority it did not already have.

## 3. Relationship to Previous Tracks and Subsystems

### 3.1 Track 119 Executable Schemas

Track 119 froze and implemented the executable Repository Intelligence
schema line, including two schemas directly relevant to Advisory
consumption:

- `schemas/repository_intelligence/artifacts/repository_knowledge_snapshot.schema.json`
  (119O/119P) — the artifact family Track 121's Query Layer reads.
- `schemas/repository_intelligence/artifacts/advisory_intelligence_context_package.schema.json`
  (119W/119X) — a structural schema for a possible future "Advisory
  Intelligence Context Package" artifact that bundles Repository
  Intelligence references, context items, relevance declarations,
  advisory considerations, and Decision Evaluation handoff
  requirements, each carrying a frozen `advisory_use_boundary` const
  disclaiming decision authority.

122A treats both schemas as downstream structural contracts, not as
new authority. It does not modify either schema. It does not implement
an Advisory Intelligence Context Package generator. It uses the
existing schema's field shape only as an architectural point of
reference for what an assembled Repository Intelligence context
element should be capable of expressing (source references, relevance,
limitations, boundary disclaimers) if a future implementation phase
chooses to align with it.

### 3.2 Track 120 Repository Knowledge Snapshot

Track 120 produced and verified the first deterministic, read-only
Repository Knowledge Snapshot artifact. That artifact remains the
Advisory consumption layer's only reachable source of Repository
Intelligence content, and it remains reachable exclusively through the
Track 121 Query Layer — never by direct file access, never by rerunning
the Track 120 generator, and never by any other means.

### 3.3 Track 121 Query Layer

Track 121 implemented and independently verified (121F) a deterministic,
read-only Query Layer over Repository Knowledge Snapshot artifacts,
supporting exactly six query categories (entity lookup, capability
lookup, architectural contract lookup, attribution lookup, limitation
lookup, boundary lookup) against executable schema version
`119O.1.0-json-schema`, with mandatory attribution preservation,
limitation propagation, boundary disclosure propagation, and fail-closed
behavior for every unsupported, missing, corrupted, or invalid input.

The Advisory consumption layer defined here is a *consumer* of that
Query Layer, not a replacement, extension, or alternate access path.
Every fact the Advisory consumption layer can possibly surface is a
fact the Query Layer could already return to any other caller. 122A
introduces no new query category, no query language, and no change to
`src/pcae/repository_intelligence/query/`. If a future implementation
phase needs a query category the current six do not support, that is a
Track 121 contract-expansion decision, not something Track 122 may
introduce unilaterally.

### 3.4 Advisory (`AdvisoryProvider` / `AdvisoryRequest` / Advisory Context Package)

"Advisory" in the sense relevant to this phase is the subsystem frozen
across Phase 113A(document only)/115P-115Z/118E: a backend-agnostic
`AdvisoryProvider` contract (115Q) that accepts a bounded
`AdvisoryRequest` and returns a `NormalizedAdvisoryResponse`, fed by an
`AdvisoryContextPackage` (115W's frozen 15-section, four-trust-class
shape) that is assembled from deterministic Evidence, repository
summaries, and transition context. Phase 118E ("Advisory Reasoning
Expansion Architecture") already named Repository Knowledge, Historical
Memory, Change Impact Analysis, and Dependency Knowledge Graph as
future Repository Intelligence inputs Advisory should eventually
consume, and established the governing principle this phase inherits
unchanged: "The objective is better grounded advisory reasoning, not
greater advisory authority."

122A is the concrete continuation of that 118E promise for exactly the
Repository Intelligence family Track 121 made queryable: Repository
Knowledge Snapshot. It defines how a Repository Intelligence query
result becomes one more source-attributed input candidate for a future
`AdvisoryContextPackage`, without redefining `AdvisoryContextPackage`'s
already-frozen 15 sections, four trust classes, prompt-injection
boundary, size limits, redaction policy, or single allowed advisory
question (115W §§1-8). Any future phase that wants Repository
Intelligence context to occupy a specific `AdvisoryContextPackage`
section (most likely alongside `deterministic_evidence_summary` or
`artifact_references`) must do so as an explicit 115W-contract
amendment or extension phase; 122A does not authorize that placement by
itself.

### 3.5 Advisory Runtime (Phase 113A)

Advisory Runtime is an architecturally distinct subsystem from the
Advisory described in §3.4, exactly as `docs/PCAE_ADVISORY_RUNTIME.md`
itself disambiguates from IRG Challenge: Advisory Runtime reads one
Runtime Snapshot and produces read-only Advisory Results about the
Runtime's *operational* state (health, consistency, readiness) — it
does not read Repository Intelligence, does not read Evidence, and is
not the consumer described in this phase. 122A does not modify Advisory
Runtime, does not add Repository Intelligence as a Runtime Snapshot
input, and does not blur the two subsystems together. A future phase
could conceivably let Advisory Runtime read Repository Intelligence
query results as additional operational context (e.g. "does the
Repository Knowledge Snapshot's declared architectural entity list
match the Runtime's registered plugin set"), but that would require its
own dedicated architecture decision; it is named here only as a
future-extensibility possibility (§13), not as something this phase
designs or authorizes.

### 3.6 Repository State

Repository Intelligence is not Repository State, and Advisory
consumption of Repository Intelligence does not change that boundary.
An advisory context element built from a Query Result may describe what
a Repository Knowledge Snapshot says about repository structure at
snapshot time; it never decides, asserts, or implies whether the
repository is currently valid, current, complete, or in a particular
lifecycle state. The Advisory consumption layer must never mutate
Repository State, must never treat a query result as a Repository State
transition, and must never let a Repository Intelligence context
element be misread as more current than the snapshot's own declared
generation commit and timestamp.

### 3.7 Evidence

Repository Intelligence is not Evidence. An advisory context element
sourced from a Repository Intelligence query result may sit alongside
`Evidence` in a future `AdvisoryContextPackage`, but it does not become
`Evidence`, does not acquire an `Evidence` ID, does not pass through the
Evidence Provider pipeline, and does not certify truth. Where a
Repository Knowledge Snapshot record already carries an evidence-gap
marker (Track 120/121's existing evidence-gap preservation), the
Advisory consumption layer must preserve that gap rather than convert
it into asserted Evidence support — the same fail-closed rule Track 121
already enforces at the Query Layer (`require_attribution` raising
before an unattributed content-bearing record can be returned) applies
transitively through Advisory consumption: an Advisory consumer must
never do at the consumption layer what the Query Layer already refuses
to do at the query layer.

### 3.8 Decision Evaluation

The Advisory consumption layer is not Decision Evaluation and confers
no Decision Evaluation authority. Repository Intelligence context may
inform a human or a future Advisory recommendation, exactly as Evidence
and repository summaries already do inside an `AdvisoryContextPackage`,
but any future consumer that wants to use Repository-Intelligence-
informed Advisory output for an actual PCAE decision must still pass
through Decision Evaluation and, ultimately, the Repository Transition
Validator's structural invariants — unchanged by this phase.

### 3.9 Runtime

The Advisory consumption layer operates entirely within the existing
`Observed` / `observe` / execution-unavailable runtime posture. It
introduces no runtime plugin, no new plugin capability, no execution
planning, and no execution capability. Repository Intelligence query
execution (via the Track 121 Query Layer) and Advisory context assembly
(as designed here) are both read-only operations that leave Runtime
Inspect output — runtime state, maximum plugin capability, execution
capability, plugin count — unchanged, exactly as Track 121 verified
Query Layer execution itself already leaves Runtime Inspect unchanged.

## 4. Architectural Scope

The Advisory consumption layer may:

- consume Repository Intelligence, exclusively as returned by the
  Track 121 read-only Query Layer;
- issue bounded Repository Intelligence query requests through that
  Query Layer, using only its existing six supported query categories;
- select relevant Repository Intelligence context from a returned Query
  Result, by deterministic, declared criteria (e.g. a query already
  scoped to a specific entity, capability, or contract target);
- preserve attribution for every selected element, unchanged from the
  Query Result's own attribution records;
- preserve limitations for every selected element, unchanged from the
  Query Result's own limitation records, plus any consumption-specific
  limitations the assembly step itself must add (§10);
- preserve boundary disclosures and disclaimers, unchanged from the
  Query Result's own boundary content;
- assemble a Repository Intelligence context package (or context
  package element) suitable for a future Advisory consumer to read
  alongside its other inputs.

The Advisory consumption layer must never:

- generate Repository Intelligence, in whole or in part;
- modify Repository Intelligence, including the source Repository
  Knowledge Snapshot artifact or any Query Result derived from it;
- scan repositories, inspect git history, or read repository source,
  test, doc, or schema files directly (all Repository Intelligence
  access is Query-Layer-mediated only);
- perform graph traversal;
- perform dependency reasoning;
- perform change impact reasoning;
- replace Advisory reasoning — an assembled Repository Intelligence
  context element is an input, never itself a recommendation, claim, or
  conclusion;
- replace Decision Evaluation;
- mutate Repository State;
- mutate Evidence;
- introduce execution capability;
- change runtime behavior, including runtime state, maximum plugin
  capability, or execution availability.

## 5. Advisory Consumption Pipeline

The following nine conceptual stages describe responsibilities only.
122A defines no classes, functions, modules, file layout, CLI surface,
or algorithms for any stage.

1. **Advisory request** — a future Advisory consumer (e.g. an
   `AdvisoryContextPackage` assembler, or a human-triggered advisory
   review workflow) declares that it wants Repository Intelligence
   context for a bounded advisory purpose. This stage does not itself
   touch Repository Intelligence; it only establishes that a
   Repository-Intelligence-informed advisory context is being
   requested, and for what declared purpose.
2. **Repository Intelligence query request** — the Advisory
   consumption layer translates the declared advisory need into one or
   more bounded, structured query requests expressed in the Track 121
   `QueryRequest` shape (category, target, filters, projection) —
   never a new query language, never a natural-language request handed
   directly to the Query Layer.
3. **Read-only Query Layer access** — each query request is evaluated
   by the existing Track 121 `execute_query` entry point against an
   existing Repository Knowledge Snapshot artifact. This stage performs
   no repository access of its own; it is a pure pass-through to the
   already-verified read-only Query Layer.
4. **Context selection** — from each returned Query Result, the
   Advisory consumption layer selects which records are relevant to the
   declared advisory purpose. Selection is deterministic and bounded by
   the query's own scope; it is not a second round of inference or
   filtering beyond what the Query Layer itself already applied.
5. **Attribution preservation** — every selected record's attribution
   (artifact provenance plus any embedded Source Attribution Records)
   is carried forward unchanged into the assembled context. No
   selection, grouping, or summarization step may drop or vague-label
   attribution.
6. **Limitation propagation** — every relevant limitation already
   present in the Query Result (snapshot-level, record-level, or
   query-specific) is carried forward unchanged. The assembly stage may
   add new limitations of its own (e.g. "only N of M matching records
   were included in this advisory context"), but it may never remove or
   silently narrow an inherited one.
7. **Boundary disclosure propagation** — the Query Result's boundary
   disclosures and disclaimers are carried forward unchanged, so that a
   human or Advisory consumer reading the assembled context sees the
   same non-authority boundary the Query Layer itself already attached.
8. **Advisory context package assembly** — selected records, their
   attribution, limitations, and boundary disclosures are assembled
   into a bounded, declared-purpose Repository Intelligence context
   element, structurally ready to be placed into a future
   `AdvisoryContextPackage` section (most likely alongside
   `deterministic_evidence_summary` or `artifact_references`, per §3.4)
   or into a structurally analogous future container — without this
   phase deciding that placement.
9. **Advisory delivery** — the assembled context element is made
   available to whichever future Advisory consumer issued the Stage 1
   request. Delivery is read-only handoff; it confers no authority, and
   the receiving consumer remains bound by every existing Advisory
   non-authority rule (§3.4, §3.8).

## 6. Context Model

The following conceptual elements are defined for future contract and
plan phases. No implementation, class, schema, or storage format is
defined here.

- **Advisory context request** — a declared, bounded request from an
  Advisory consumer for Repository-Intelligence-sourced context,
  carrying a declared advisory purpose, the Repository Intelligence
  query request(s) it will translate to, and any consumption-specific
  bound (e.g. a maximum number of records).
- **Repository Intelligence context selection** — the deterministic
  subset of a Query Result's records chosen for inclusion, together
  with the declared selection criteria that produced it.
- **Context package** — the assembled output of the pipeline (§5,
  Stage 8): selected records plus their attribution bundle, limitation
  bundle, boundary disclosure bundle, and advisory-facing metadata.
- **Attribution bundle** — the per-record and package-level provenance
  carried forward from the Query Result: source artifact identity,
  schema version, snapshot identity, and any embedded Source
  Attribution Records.
- **Limitation bundle** — the full set of inherited and
  consumption-added limitations relevant to the context package,
  preserved as a first-class part of the package contract, never as an
  optional side note.
- **Boundary disclosure bundle** — the inherited boundary disclosures
  and disclaimers, plus any consumption-specific non-authority
  disclaimer (e.g. explicitly restating that the package is not
  Evidence, not Repository State, and not a Decision Evaluation
  output).
- **Advisory-facing metadata** — bounded, non-authoritative metadata
  describing the context package itself for the receiving Advisory
  consumer: declared advisory purpose, originating query request(s),
  assembly timestamp, and determinism metadata inherited from the
  underlying Query Result(s).

## 7. Attribution Architecture

Every advisory context element sourced from Repository Intelligence
must preserve provenance, without exception.

- Attribution must remain traceable to the originating Repository
  Knowledge Snapshot: artifact id, artifact type, snapshot id, and
  executable schema version, exactly as already returned by the Track
  121 Query Layer's `source_artifact` metadata.
- Where a selected record carries embedded Source Attribution Records
  (Track 120/121's `source_attribution` / `capability_source` fields),
  those records must remain attached to the assembled context element,
  never collapsed into a vague summary label.
- If a content-bearing record selected for advisory context lacks
  required attribution, the Advisory consumption layer must fail closed
  or omit that record with a disclosed limitation — it must never do
  what the Query Layer's own `require_attribution` already refuses to
  do (§3.7).
- Aggregating multiple selected records into one context package is
  structural grouping only; it must preserve attribution for each
  member record individually, never merge them into one unattributed
  claim.

## 8. Limitation Architecture

Limitations from Repository Intelligence must propagate unchanged
through Advisory consumption.

- Snapshot-level, record-level, and query-specific limitations already
  present in a Query Result must all be carried into the assembled
  context package's limitation bundle (§6).
- Advisory must not silently drop a limitation to make a context
  package shorter, cleaner, or more confident-sounding than its source
  material warrants.
- The consumption layer may add its own limitations (e.g. "context was
  bounded to N records," "only entity lookup was queried; capability
  and contract context were not requested for this advisory purpose"),
  but additions are strictly additive — they never substitute for or
  narrow an inherited limitation.
- A context package with limitations is still a valid, deliverable
  context package (§5, Stage 9); limitations are part of the contract,
  not a reason to withhold delivery, except where §10's failure
  architecture requires fail-closed handling instead.

## 9. Boundary Architecture

Boundary disclosures must remain attached throughout Advisory
consumption, from the originating Query Result through to final
delivery.

- Every context package must carry forward the source Repository
  Knowledge Snapshot's boundary disclosures and disclaimers, unchanged,
  exactly as the Track 121 Query Layer already guarantees for every
  Query Result regardless of query category or result status.
- Advisory must not treat a Repository Intelligence context element as
  Evidence (§3.7), as Repository State (§3.6), or as a Decision
  Evaluation output (§3.8) at any point in the pipeline — not during
  selection, not during assembly, and not after delivery to a receiving
  Advisory consumer.
- A context package's advisory-facing metadata (§6) must make its
  non-authority explicit: it is context that may inform Advisory
  reasoning, never a conclusion, recommendation, or approval in its own
  right.
- No formatting, grouping, projection, or summarization step anywhere
  in the pipeline may suppress a boundary disclosure or disclaimer for
  brevity.

## 10. Governance Architecture

The Advisory consumption layer must preserve:

- observe-only runtime posture, unchanged from Track 121;
- execution unavailable, unchanged from Track 121;
- maximum plugin capability `observe`, with zero runtime plugins
  introduced;
- deterministic behavior: identical Query Result inputs must produce
  identical assembled context packages, mirroring the Track 121
  determinism guarantee this layer depends on;
- explainability: every context package must be explainable in terms
  of its originating advisory request, the query request(s) it
  translated to, the selected records, and the preserved
  attribution/limitations/boundaries — the same explainability
  standard 121A §14 already established for the Query Layer itself;
- auditability: context package assembly must be traceable back to
  specific Query Layer calls and their inputs;
- reproducibility: a context package assembled twice from the same
  Repository Knowledge Snapshot and the same advisory request must be
  logically identical;
- repository cleanliness: no Advisory consumption operation may leave
  uncommitted, untracked, or stray repository state;
- execution unavailable, restated: no stage of the pipeline (§5) may
  introduce, request, or imply execution capability.

## 11. Failure Architecture

The Advisory consumption layer must fail closed for every one of the
following, mirroring and extending Track 121's own fail-closed
discipline rather than inventing a separate failure model:

- **Missing Repository Intelligence snapshot** — if the underlying
  Query Layer call fails with a missing-snapshot error, the Advisory
  consumption layer must not substitute, guess, or silently omit the
  requested context without disclosure; it must fail closed or return
  an explicit "Repository Intelligence unavailable" limitation.
- **Unsupported snapshot schema version** — if the Query Layer rejects
  the snapshot as an unsupported schema version, the Advisory
  consumption layer must propagate that rejection as a disclosed
  limitation, never attempt its own version inference or field mapping.
- **Unsupported query** — if a translated query request (§5, Stage 2)
  falls outside the Track 121 Query Layer's six supported categories,
  the Advisory consumption layer must reject that request before
  attempting assembly; it must never invent a seventh category to work
  around the boundary.
- **Empty query result** — a Query Result with no matching records (the
  Query Layer's own bounded "unknown" result status) must be
  represented in the context package as an explicit absence, with its
  inherited limitation intact; it must never be treated as license to
  infer or fabricate the missing content.
- **Missing attribution** — a selected record missing required
  attribution must be excluded from the context package with a
  disclosed limitation, or the whole context package request must fail
  closed, mirroring §7's attribution architecture; it must never be
  included unattributed.
- **Corrupted Repository Intelligence artifact** — if the Query Layer
  reports a corrupted or unparseable snapshot, the Advisory consumption
  layer must fail closed for that snapshot, never partially trust
  malformed content.
- **Boundary disclosure mismatch** — if an assembled context package
  would omit or alter a boundary disclosure or disclaimer present in
  its source Query Result, that is treated as an assembly defect: the
  request must fail closed rather than deliver a package with a
  mismatched or missing boundary.
- **Limitation propagation failure** — if the assembly stage cannot
  determine whether all relevant inherited limitations were carried
  forward (e.g. because a future implementation's selection logic
  cannot establish completeness), the request must fail closed rather
  than deliver a context package with unverifiable limitation coverage.

Every one of these failure modes still produces, at most, a bounded,
non-authoritative outcome: a disclosed limitation, an explicit absence,
or a fail-closed rejection. None of them may cause the Advisory
consumption layer to scan the repository, invoke AI inference, or
otherwise compensate for missing Repository Intelligence by any means
other than the Track 121 Query Layer.

## 12. Track 122 Roadmap

Committed Track 122 sequence:

- **122A — Repository Intelligence Advisory Consumption Architecture**:
  architecture only; define purpose, scope, pipeline, context model,
  attribution/limitation/boundary architecture, governance, failure
  handling, and roadmap (this document).
- **122B — Repository Intelligence Advisory Consumption Contract
  Freeze**: freeze the normative contract for advisory context
  requests, Query Layer usage bounds, context package obligations,
  attribution/limitation/boundary preservation, failure behavior, and
  non-goals.
- **122C — Repository Intelligence Advisory Consumption Contract
  Verification**: independently verify the 122B contract before any
  prototype planning.
- **122D — Repository Intelligence Advisory Consumption Prototype
  Plan**: plan a narrow advisory-context-assembly prototype without
  implementation.
- **122E — Repository Intelligence Advisory Context Prototype**:
  implement only the scoped prototype approved by 122B-122D.
- **122F — Repository Intelligence Advisory Consumption Verification**:
  independently verify the prototype against the contract, plan,
  schemas, determinism, attribution, boundary, and governance
  boundaries.

122A recommends 122B as the next phase.

## 13. Future Extensibility

The Advisory consumption layer designed here is a future consumer
boundary for later Repository Intelligence artifact families, but
122A does not couple implementation to them.

Future interactions, documented and explicitly not implemented:

- **Historical Memory Snapshot** — once queryable through a future
  Track 121 contract expansion, could supply historical/temporal
  advisory context (e.g. "this architectural entity was introduced in
  phase X and hardened in phase Y") through the same consumption
  pipeline design, without this phase authorizing that query category.
- **Dependency Knowledge Graph Snapshot** — could supply
  relationship-aware advisory context once its own artifact family is
  queryable, but graph construction and traversal remain outside both
  the Query Layer (121B §17) and this consumption layer (§4).
- **Change Impact Report** — could supply impact-aware advisory context
  once its own artifact family is queryable, but change impact
  reasoning remains outside both layers.
- **Advisory Intelligence Context Package** (119W/119X schema) — a
  future implementation phase could align the context package shape
  defined here (§6) with that schema's structural fields, but 122A does
  not require, assume, or implement that alignment.
- **Future Repository Intelligence artifact families** — any artifact
  family not yet defined may become a future Query Layer input (per a
  Track 121 contract expansion) and, transitively, a future Advisory
  consumption input, without this phase pre-authorizing any of them.

The extension rule mirrors 121A §15: future artifact families and
future Advisory consumers may be added, but they may not make the
Advisory consumption layer responsible for their reasoning, authority,
generation, or execution behavior.

## 14. Known Inherited Issues

Carried forward unchanged and not repaired in this phase:

- 119Q report-generation-ordering defect: non-blocking.
- 119AB phase-id comparison bug: non-blocking.
- Recurring `pending_final_telegram_delivery` reporting detail:
  non-blocking.

## 15. Strict Non-Goals

122A does not implement:

- Advisory integration;
- a context builder;
- Repository Intelligence generation;
- repository scanning;
- query engine changes;
- graph traversal;
- dependency reasoning;
- change impact reasoning;
- runtime plugins;
- execution planning;
- execution capability;
- source code changes;
- test code changes;
- schema changes.

## 16. Acceptance Criteria

122A is complete when:

- the Advisory consumption architecture is documented;
- relationships to Track 119 schemas, Track 120 Repository Knowledge
  Snapshot, Track 121 Query Layer, Advisory (`AdvisoryProvider`/
  `AdvisoryContextPackage`), Advisory Runtime, Repository State,
  Evidence, Decision Evaluation, and Runtime are explicit;
- architectural scope (permitted and forbidden operations) is defined;
- the nine-stage advisory consumption pipeline is defined as
  responsibilities only, with no implementation;
- the context model's conceptual elements are defined, with no
  implementation;
- attribution, limitation, boundary, governance, and failure
  architectures are defined;
- Track 122 roadmap is documented;
- future extensibility is documented without coupling implementation;
- no implementation occurs;
- runtime posture remains `Observed` / `observe` / execution
  unavailable.
