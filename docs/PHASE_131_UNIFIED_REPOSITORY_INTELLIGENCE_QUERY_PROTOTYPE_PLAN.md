# Phase 131D - Unified Repository Intelligence Query Prototype Plan

## 1. Purpose

131A defined the architecture, 131B froze the binding contract, and
131C independently verified that contract against real source with
zero BLOCKING findings. This phase converts the verified contract into
a **deterministic engineering plan** for 131E's implementation - the
bounded set of decisions a builder needs (what module goes where, what
each stage does, what fails closed and how) without writing any of it.

**This phase implements nothing.** No source file, test file, or
schema is created or modified. Every planning decision below traces to
a specific 131B contract clause or a specific 131C verification
finding; nothing here introduces new architectural scope beyond what
131A-131C already authorized.

## 2. Prototype Objectives

### 2.1 Prototype purpose

Build the first deterministic, read-only Unified Query prototype:
a single request/response cycle that locates, correlates, and exposes
content already present in the six covered artifact families
(Repository Knowledge Snapshot, Dependency Knowledge Graph, Historical
Memory, Change Impact, Advisory Context, Cross-Artifact Integration),
governed entirely by 131B's contract.

### 2.2 Implementation boundaries

- **In bounds**: a new `src/pcae/repository_intelligence/unified_query/`
  package; a governed CLI command
  (`pcae repository-intelligence unified-query`, matching the existing
  `run_repository_intelligence_query`/`run_repository_intelligence_
  cross_artifact_integration_generate` naming precedent in
  `src/pcae/commands/repository_intelligence.py`); routing over
  already-declared artifact responsibilities; response assembly from
  already-loaded artifact content; reuse of every existing shared
  schema/module this plan identifies (Sections 6, 9).
- **Out of bounds** (131E may not do any of this without a new
  governed decision): modifying any of the eight
  `schemas/repository_intelligence/artifacts/*.schema.json` or eleven
  `schemas/repository_intelligence/shared/*.schema.json` files;
  modifying `query_request.py`'s `SUPPORTED_QUERY_CATEGORIES` or any
  other Track 121-130 source file (131E is strictly additive - a new
  package, zero edits to existing packages); implementing reasoning,
  inference, ranking, recommendation, Decision Evaluation, execution
  planning, or execution capability (131B Section 6/22).

### 2.3 Implementation sequence

131E should implement in the dependency order this plan's lifecycle
implies (Section 3): (1) request/normalization types, (2) routing,
(3) artifact resolution (reusing `snapshot_loader.py`), (4) response
assembly, (5) provenance attachment, (6) boundary disclosure
attachment, (7) CLI wiring, (8) fail-closed error paths threaded
through every stage above rather than bolted on afterward - matching
Track 130's own precedent where `IntegrationGenerationError` is raised
inline at each validation point in `integration_builder.py`, not in a
separate pass.

### 2.4 Success criteria (for 131E)

- A single-family query (e.g. routed to Repository Knowledge Snapshot
  alone) produces a response containing all six 131B Section 9
  provenance elements, evidence content matching 131B Section 10's
  three prohibitions (never strengthens/transforms/infers), and the
  boundary disclosure bundle from Section 7 below.
- A query naming an unresolvable identifier produces an explicit
  `unresolved identity` record (131B Section 11), never a fuzzy match
  and never a silent omission.
- A query naming an unsupported category, missing artifact, or
  malformed request fails closed with a specific, attributable
  exception (Section 8 below), never a generic catch-all.
- Two runs against identical repository state and an identical request
  produce byte-identical output except approved timestamps (131B
  Section 13).

### 2.5 Completion criteria (for 131E)

131E is complete when: the prototype handles at least one query per
covered artifact family (six single-family cases) plus at least one
cross-artifact case consuming Track 130's integration package (131B
Section 12); every fail-closed condition enumerated in Section 8 below
has a corresponding raising code path; the CLI command is wired and
governed; and 131F's verification strategy (Section 11) can be run
against real generated output.

### 2.6 Confirmed properties

- **Deterministic** - Section 3's lifecycle and Section 10's
  provenance plan both inherit the identifier-lexicographic ordering
  discipline 131C Section 12 already independently confirmed is real,
  working precedent in both `query_engine.py` and
  `integration_builder.py`.
- **Read-only** - Section 2.2's implementation boundary permits no
  write call anywhere in the new `unified_query` package; 131E must
  reuse `snapshot_loader.py`'s existing read-only `load_snapshot`
  rather than writing a new loader.
- **Derivative** - Section 5's response assembly plan bounds response
  content to exactly the six element categories 131B Section 8
  already closes the list to; no field may be added outside that set.
- **Governance-compatible** - Section 12 confirms this explicitly.

## 3. Query Lifecycle Plan

Nine conceptual stages, per 131B Section 6 and this phase's own
required scope. **Responsibilities only - no schema, no function
signatures frozen here; 131E's own implementation plan (informed by
this document) makes those concrete decisions.**

1. **Query request** - a client submits a category plus a target,
   structurally analogous to the existing `QueryRequest`
   (`category: str`, `target: str | None`, `filters: dict[str, str]`,
   `projection: tuple[str, ...]` per `query_request.py`). 131E's
   request type is a new, additive dataclass in the new package - it
   does not modify `query_request.py`'s existing `QueryRequest` (that
   type remains Track 121's own, RKS-scoped).
2. **Query normalization** - canonicalize the request into a
   deterministic, hashable form (mirroring `QueryRequest.normalized()`'s
   existing sorted-filters/list-projection pattern) so that
   determinism (131B Section 13) can be checked mechanically: two
   equal normalized requests must be indistinguishable to every later
   stage.
3. **Routing** - resolve the normalized request's category to one or
   more of the six artifact families via the fixed declared mapping
   (Section 4 below). Fails closed (Section 8) on no match.
4. **Artifact resolution** - load each routed family's own most
   recent artifact using that family's own existing loader:
   `snapshot_loader.load_snapshot` for Repository Knowledge Snapshot;
   equivalent existing load functions for Dependency Knowledge Graph
   (`graph_builder.py`'s loader), Historical Memory, Change Impact,
   Advisory Context, and Cross-Artifact Integration (each family
   already has its own JSON-load path - `integration_builder.py`'s
   `_load_change_impact_report`/`_load_dependency_graph`/
   `_load_json_artifact` are the direct precedent to reuse rather than
   reimplement). No new persistence mechanism.
5. **Response assembly** - combine resolved records into the closed
   six-category response shape (Section 5).
6. **Provenance attachment** - attach all six mandatory elements
   (Section 6) to every response element before proceeding; incomplete
   provenance fails closed (131B Section 15) rather than reaching
   stage 9.
7. **Evidence preservation** - when evidence content is included
   (only on explicit request, per 131B Section 6's "expose"
   responsibility), copy it verbatim from the loaded artifact - the
   same `dict(record)` pattern `query_engine.py`'s `_select_records`
   already uses, reused not reinvented.
8. **Boundary disclosure attachment** - attach the boundary disclosure
   bundle (Section 7) to the response envelope.
9. **Response delivery** - serialize deterministically (identifier-
   lexicographic ordering, per Section 10) and return to the CLI or
   caller.

## 4. Routing Plan

**Deterministic, based solely on declared artifact responsibilities**
(131B Section 7), planned concretely for 131E:

- **Declared mapping**: a fixed table, one entry per query category,
  naming exactly which of the six artifact families that category
  routes to. 131E should seed this table from the existing six Track
  121 categories where they map cleanly onto Repository Knowledge
  Snapshot (`entity_lookup`, `capability_lookup`,
  `architectural_contract_lookup`, `attribution_lookup`,
  `limitation_lookup`, `boundary_lookup` - all unchanged, per 131C
  Section 16's confirmation these remain untouched) and define new,
  additive categories for the other five families (e.g. a
  `dependency_node_lookup` routing to Dependency Knowledge Graph, an
  `event_lookup` routing to Historical Memory) rather than overloading
  the existing six with new meaning.
- **Single-family queries**: route to exactly one family; resolve via
  stage 4 directly; no cross-artifact consultation needed.
- **Multi-family queries**: route to more than one family only where
  Track 130's own integration package already declares the connecting
  relationship (131B Section 12) - e.g. a query asking for a Change
  Impact entity's corresponding Dependency Knowledge Graph node routes
  to both Change Impact and, via the integration package's
  `entity_resolutions`/`dependency_context` records, Dependency
  Knowledge Graph. **131C's own non-blocking finding (multi-family
  disambiguation, Section 20.2/Section 6 of the verification report)
  is incorporated here, not resolved architecturally**: this plan
  requires that every multi-family category be explicitly enumerated,
  by name, in the declared mapping table before 131E may implement it
  - no category may be "discovered" to be multi-family at
  implementation time and handled ad hoc. If 131E encounters a
  plausible multi-family case not already named in this plan's table,
  it must stop and request a scope decision rather than inventing a
  disambiguation rule inline (this directly satisfies 131B Section 7's
  "no heuristics" and Section 15's "ambiguous routing... fails closed"
  simultaneously).
- **Unresolved routing** (a category that exists but whose target
  cannot be determined for this specific request - e.g. a
  multi-family category where one side's identifier is absent):
  produces an explicit `unresolved identity`-class uncertainty record
  (131B Section 14), not a routing failure - the category itself is
  known; only the specific resolution is incomplete.
- **Unsupported routing** (a category not in the declared mapping at
  all): fails closed with a dedicated exception (Section 8,
  `UnsupportedQueryCategoryError`), mirroring `QueryExecutionError`'s
  existing `unsupported query category` precedent in `query_engine.py`.
- **No optimization, no indexing**: 131E's routing table is a plain
  Python dict/frozenset lookup, matching `SUPPORTED_QUERY_CATEGORIES`'s
  existing `frozenset` pattern exactly - no index structure, no cache,
  no precomputation beyond the fixed table itself.

## 5. Response Assembly Plan

Responses are assembled as a **closed set of six categories** (131B
Section 8), planned as follows:

- **references** - always present; one entry per resolved record,
  each carrying at minimum the provenance elements 1-4 (Section 6).
- **provenance** - attached per stage 6 of Section 3; never optional
  once a reference exists.
- **evidence** - present only when the request's `projection`
  explicitly asks for it (mirroring `QueryRequest.projection`'s
  existing opt-in shape); absent by default, matching 131B Section 6's
  "expose" being a distinct, requestable responsibility rather than an
  always-on behavior.
- **limitations** - the union of every resolved artifact's own
  `snapshot_limitations`/equivalent field (already present in every
  covered family's schema, confirmed by 131C Section 7) plus any
  routing-scoped limitation (e.g. "multi-family disambiguation for
  category X is not yet declared").
- **uncertainty** - one record per applicable category from 131B
  Section 14 (`unknown`, `unavailable`, `incomplete`, `conflicting`,
  `unsupported`, `unresolved identity`); 131E must extend the existing
  `QueryResult.unknowns`/`result_status` pattern to cover all six
  categories explicitly, not just the `"unknown"` status Track 121's
  existing implementation currently supports (this directly addresses
  131C Section 7's finding that today's uncertainty vocabulary is
  incomplete).
- **boundary disclosures** - the bundle from Section 7.

**No synthesized conclusions**: 131E's response-assembly stage may
only ever populate these six categories from already-loaded artifact
content or from the fixed routing/provenance/boundary logic this plan
defines - no field computed by aggregating, scoring, or summarizing
content across records is in scope for 131E. If a future aggregation
convenience field is ever proposed, 131B Section 20.1 (carried forward
unrepaired) already requires it to stop and request explicit
scope review before implementation - this plan does not authorize it
and 131E must not add one.

## 6. Boundary Disclosure Mapping Plan

**Directly addresses 131C Section 15's independently-discovered
finding**: 131B's six conceptual boundary items (derivative, read-only,
no reasoning, no Decision Evaluation, no execution authority, no
execution capability) do not name-match the real, already-frozen,
already-used nine-field `boundary_disclosure.schema.json`
(`read_only`, `no_execution`, `non_decision`, `advisory_non_authority`,
`decision_evaluation_required`, `no_repository_mutation`,
`no_lifecycle_mutation`, `no_evidence_replacement`,
`no_repository_state_replacement`).

**Decision for 131E: reuse the existing nine-field schema verbatim,
do not invent a new one.** This follows Track 130's own precedent
(130D's "architectural simplification" - reusing Change Impact's
existing `dependency_context_reference` shape rather than defining a
parallel one) and is the only option consistent with 131B Section 23's
"do not modify executable schemas" non-goal, which this plan (as a
131D document) is equally bound by.

**Concrete mapping table** (131B conceptual term -> real schema field,
planned for 131E's response-assembly stage to populate mechanically):

| 131B conceptual item | Real `boundary_disclosure.schema.json` field(s) |
| --- | --- |
| read-only | `read_only` (direct) |
| no execution capability | `no_execution` (direct) |
| no reasoning | `non_decision` (closest existing field; 131E must not claim this is a perfect semantic match - `non_decision` denotes "not a decision," which is the closest already-existing boolean to "no reasoning," not an identical concept) |
| no Decision Evaluation | `decision_evaluation_required` (const `true` - declares that *if* a decision is needed, human/Decision-Evaluation review is required, which is the existing schema's way of saying Unified Query itself performs no Decision Evaluation) |
| derivative | `advisory_non_authority` plus `no_evidence_replacement` plus `no_repository_state_replacement` together (no single existing field is named "derivative"; the combination of "not an authority," "does not replace Evidence," and "does not replace Repository State" is the closest existing three-field approximation) |
| no execution authority | `no_repository_mutation` plus `no_lifecycle_mutation` (the existing schema expresses "no execution authority" as two specific mutation-prohibition fields rather than one general authority field) |

**This mapping is planning guidance, not a contract amendment.** 131B's
six-item prose remains the binding contract text (unchanged by this
plan); this table is 131D's answer to "how does 131E's code satisfy
that prose using the one schema that already exists," resolving 131C's
finding without touching 131B's own document or the schema itself.
131E must populate all nine required fields as `true` (matching
`integration_validation.py`'s own `_validate_boundary_disclosures_
present` precedent exactly) - never a subset, and never a value other
than the schema's own `const: true`.

## 7. Boundary Disclosure Bundle (Response Envelope)

Per Section 6's mapping, every Unified Query response's boundary
disclosure bundle is exactly the real nine-field object, reused
verbatim - not a new shape. 131E should build it via a shared helper
(new, additive, in the `unified_query` package) that returns the same
nine-key dict every response uses, mirroring how
`integration_builder.py` presumably centralizes its own boundary
disclosure construction (131E's implementer should locate and reuse
that existing helper if `pcae.repository_intelligence.attribution`
already exposes one, rather than duplicating the nine-key literal).

## 8. Failure Handling Plan

**Deterministic fail-closed behavior, one dedicated condition per
case**, extending (never replacing) the three existing exception
classes 131C Section 14 confirmed are real precedent
(`SnapshotLoadError`, `SnapshotCompatibilityError`,
`QueryExecutionError`) plus `IntegrationGenerationError` for
cross-artifact cases:

| Condition | Planned exception | Precedent reused |
| --- | --- | --- |
| unsupported query (category not in the declared routing table, Section 4) | `UnsupportedQueryCategoryError` (new, additive) | `QueryExecutionError`'s existing `unsupported query category` message pattern |
| missing artifact (a routed family's own persisted artifact file absent) | reuse `SnapshotLoadError` directly | already raised by `snapshot_loader.load_snapshot`; no new class needed |
| unresolved identifier (a query target that does not exactly match any resolved family's stable identifier) | not an exception - an explicit `unresolved identity` uncertainty record (Section 5), matching `integration_builder.py`'s own `unresolved_identities` pattern exactly (a miss is recorded, not raised) |
| routing ambiguity (a multi-family category encountered with no declared disambiguation rule, Section 4) | `RoutingAmbiguityError` (new, additive) - raised, not silently resolved, because an *undeclared* ambiguity is a planning gap, distinct from an *expected* unresolved identifier |
| incompatible artifact (a resolved family's artifact has an unexpected/incompatible `executable_schema_version`) | reuse `SnapshotCompatibilityError` directly | already raised by `snapshot_loader.load_snapshot` for RKS; 131E extends the same check to the other five families' own loaders |
| malformed request (missing category, invalid filter shape, etc.) | reuse the existing `ValueError` -> `QueryExecutionError` translation pattern (`validate_request`'s existing behavior) | direct precedent, no new class needed |

**No inferred recovery**: every row above either raises or produces an
explicit uncertainty record - none silently defaults, retries with a
different family, or substitutes a "best guess" result. This plan
introduces exactly two new exception classes
(`UnsupportedQueryCategoryError`, `RoutingAmbiguityError`); every other
failure mode reuses an already-existing, already-tested exception
class rather than multiplying the exception hierarchy.

## 9. Identity Resolution Plan

**Reuse Track 130's proven pattern exactly** - 131C Section 10
independently confirmed this is the strongest, most directly reusable
piece of evidence anywhere in the codebase for 131B's identity
contract:

- **Exact identifier matching**: 131E's cross-family resolution must
  use the same `candidate = derive_id(...); node = lookup.get
  (candidate)` shape `integration_builder.py`'s entity-resolution loop
  already demonstrates - a deterministic derivation function plus an
  exact dict-key lookup, never a substring, prefix, or similarity
  match.
- **Explicit unresolved state**: on any lookup miss, 131E must append
  an explicit record (matching `unresolved_identities`'s existing
  shape: `entity_id`, `uncertainty_state: "unresolved"`,
  `unresolved_reason`) rather than omitting the entity or raising a
  generic error - the miss is data, not a failure, exactly as Track
  130 already treats it.
- **Reject fuzzy matching, aliases, silent merges, probabilistic
  identity**: 131E introduces no new identity-resolution function of
  its own for cross-family correlation - it calls Track 130's existing
  identity derivation (`_node_id_for_entity` or equivalent per-family
  functions) rather than writing a new one, which mechanically
  prevents 131E from introducing a *different*, potentially
  fuzzier, resolution strategy than the one already proven. Within a
  single family, 131E reuses that family's own existing `_id` field
  lookups (`entity_id`, `node_id`, `event_id`, `context_id`, etc.,
  per 131C Section 10's field inventory) verbatim.

## 10. Provenance Plan

**Directly addresses 131C Section 8's finding**: today's one real
precedent (`query_engine.py`'s `_source_artifact`) supplies elements 1
(authoritative artifact), 3 (source locator), and 4 (schema version)
explicitly, but not element 2 (originating record, only implicit
today), element 5 (derivation path), or element 6 (verification
state).

**131E's concrete plan to close this gap**:

1. **Element 2 (originating record)** - add an explicit
   `originating_record_id` field to every reference, extracted from
   whichever `_id` field that record's own family declares (Section 9's
   field inventory) - promoting what is implicit in `records`' own
   content today into an explicit, always-present provenance field.
2. **Element 5 (derivation path)** - for single-family references,
   the path is trivially "direct" (a fixed constant); for
   cross-artifact references, the path is Track 130's own
   `entity_resolutions`/`dependency_context` chain, reused verbatim -
   131E does not compute a new derivation path, it surfaces the one
   Track 130 already records.
3. **Element 6 (verification state)** - surface each record's own
   `verification_state`/`uncertainty_state` field where the source
   artifact's schema already declares one (confirmed present via the
   shared `uncertainty_verification_state.schema.json` `$ref` pattern
   every family's schema uses); where a specific record has no such
   field (some record types may not carry one), the provenance element
   is explicitly `"unknown"` rather than omitted - satisfying 131B
   Section 9's "all six are mandatory... fails closed on incomplete
   chain" without requiring every source schema to be retrofitted
   first.
4. Elements 1, 3, 4 continue to reuse `_source_artifact`'s existing
   construction pattern unchanged.

**Fails closed on incompleteness**: if any of the six elements cannot
be populated (including via the `"unknown"` fallback for element 6
specifically, which is itself a valid, explicit value - not a missing
one), the reference is not emitted; the query fails closed for that
specific reference per 131B Section 15, recorded as an explicit
uncertainty entry rather than silently dropped.

## 11. Conceptual Query Model

**No schema additions in this phase or in 131E without a separate,
explicitly scoped schema-authoring decision** (per 131B Section 19's
versioning contract, which explicitly defers concrete schema
authorship). The following is conceptual only:

### 11.1 Request model

- **query** - the category (Section 4's declared mapping).
- **scope** - which artifact family/families the category routes to
  (derived, not supplied by the caller).
- **requested artifacts** - optional explicit narrowing (e.g. "only
  Dependency Knowledge Graph, even if the category could also resolve
  against Historical Memory") - additive to, never a replacement for,
  the declared routing table.
- **requested identifiers** - the target identifier(s), reusing each
  family's own existing stable identifier fields (Section 9).

### 11.2 Response model

- **response metadata** - normalized request echo plus generation
  timestamp (the same two-approved-timestamp convention every covered
  family already uses).
- **resolved artifacts** - the `references` category (Section 5).
- **provenance bundle** - Section 10's six elements per reference.
- **evidence bundle** - Section 3 stage 7's opt-in verbatim content.
- **uncertainty bundle** - Section 5's six-category uncertainty
  vocabulary.
- **limitation bundle** - Section 5's union of source + routing-scoped
  limitations.
- **boundary disclosure bundle** - Section 7's real nine-field object.

## 12. Implementation Decomposition (for 131E)

Phased breakdown, one section per implementation concern:

1. **Request handling** - new request dataclass, normalization
   function (Section 3 stages 1-2); reuses
   `QueryRequest.normalized()`'s existing pattern, does not modify it.
2. **Routing** - declared mapping table, single/multi-family
   dispatch, `UnsupportedQueryCategoryError`/`RoutingAmbiguityError`
   (Section 4, Section 8).
3. **Artifact retrieval** - per-family loader reuse (Section 3 stage
   4); extends `SnapshotCompatibilityError` checking to all six
   families' own loaders (Section 8).
4. **Response assembly** - the six-category closed response shape
   (Section 5), boundary disclosure helper (Section 7).
5. **Provenance integration** - the six-element provenance plan
   (Section 10), identity resolution reuse (Section 9).
6. **Failure handling** - the failure table (Section 8), threaded
   through stages 1-5 inline (Section 2.3), not as a separate pass.
7. **Reporting** - CLI command wiring
   (`run_repository_intelligence_unified_query` in
   `src/pcae/commands/repository_intelligence.py`, matching the
   existing `run_repository_intelligence_query` pattern exactly), plus
   whatever governed phase-report/test evidence 131E's own
   finalization requires.

## 13. Verification Strategy (for 131F)

131F must independently verify, against freshly generated real output
(not 131E's own tests, per the "re-derive, do not trust" discipline
131C already applied and 130F applied before it):

- **Deterministic output** - two independent fresh runs against
  identical repository state produce byte-identical output except
  approved timestamps (131C Section 12's methodology, reused).
- **Read-only guarantees** - checksum comparison of every source
  artifact and the repository itself before/after query execution
  (130F's own precedent, directly reusable).
- **Provenance preservation** - independently confirm all six elements
  (Section 10) are present on every reference in real generated
  output, including the `"unknown"` fallback case for element 6.
- **Evidence preservation** - independently confirm evidence content
  is verbatim-identical to its source artifact's own content (130F's
  own checksum-style verification, reusable).
- **Identity preservation** - reuse 130F's own five synthetic
  near-miss identity probes (trailing slash, case-flip, leading
  whitespace, truncated prefix, similar-but-wrong extension),
  confirmed still the standing precedent by 131B Section 11 and 131C
  Section 10.
- **Fail-closed behavior** - independently probe every row of
  Section 8's failure table against real malformed/missing/ambiguous
  input, confirming each raises or records exactly as planned.
- **Governance preservation** - `pcae health`/`check`/`doctor task-
  memory`/`runtime inspect` all clean, and zero runtime plugins
  registered, exactly as every prior verification phase confirms.
- **Boundary disclosure preservation** - confirm every response
  carries the real nine-field object (Section 7) with all fields
  `true`, using the same validation pattern
  `_validate_boundary_disclosures_present` already demonstrates.
- **Compatibility with Tracks 119-130** - confirm, via `git log`
  (131C Section 16's own methodology), that 131E introduced no
  modification to any existing schema or source file outside the new
  `unified_query` package.

## 14. Treatment of 131C Non-Blocking Findings

All five findings are addressed by this plan's design, **not repaired
in this phase**:

1. **Multi-family routing disambiguation** - Section 4's routing plan
   requires every multi-family category to be explicitly enumerated in
   the declared mapping table before implementation; no heuristic
   disambiguation is introduced. Resolved by requiring explicitness,
   not by inventing a general-purpose disambiguation algorithm.
2. **Response uncertainty-vocabulary gap** - Section 5's response
   assembly plan explicitly extends the uncertainty bundle to all six
   131B Section 14 categories, not just today's single `"unknown"`
   status.
3. **Provenance element gaps (2, 5, 6)** - Section 10 gives a concrete,
   field-by-field plan for closing exactly this gap.
4. **Partial fail-closed exception coverage** - Section 8's failure
   table gives every one of 131B's ten enumerated conditions (131B
   Section 15) either a reused or a new dedicated exception/record
   path.
5. **Boundary disclosure six-item/nine-field mapping gap** - Section 6
   gives the concrete mapping table and the "reuse verbatim, do not
   invent a new schema" decision.

**No architectural scope expansion**: every resolution above reuses an
already-existing pattern, module, or schema; none introduces a new
artifact family, a new authority, or a new capability beyond what 131A
architected and 131B froze.

## 15. Strict Non-Goals

This phase does not: implement Unified Query; modify schemas; modify
source code; modify test code; expand Query Layer behavior; introduce
reasoning; introduce execution capability; change runtime behavior.

## 16. Governance Compatibility

- observe-only runtime unchanged;
- execution remains unavailable;
- this plan authorizes no schema change, no source change, no test
  change - confirmed by this phase's own final commit scope
  (`docs/`, `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/` only);
- raw git commit/push, force push, and `--no-verify` remain forbidden
  and were not used;
- PFN-001 remains satisfied (Section 18).

## 17. Confirmations

- **No implementation occurred.** This phase produced only planning
  documentation.
- **No runtime behavior changed.**
- **Execution remains unavailable.**

## 18. PFN-001 Confirmation

The Phase Finalization Notification Invariant (128B.2), re-confirmed
still globally binding, unamended by this phase:

- **Every terminal phase outcome** shall produce exactly one trusted
  canonical phase report delivered to the configured notification
  sink. This phase (131D) satisfies this identically to every phase
  since 128B.2.
- **Notification delivery or an explicit durable delivery-failure
  record** remains mandatory; silent omission remains prohibited.
- **No amendment.** This phase does not modify PFN-001's own contract
  text.

**PFN-001 remains globally applicable and is satisfied by this
phase.**

## 19. Conclusion

131D converts the 131B contract (independently verified with zero
BLOCKING findings by 131C) into a concrete, engineering-ready plan for
131E: a nine-stage query lifecycle, a routing plan that closes 131C's
multi-family-disambiguation finding by requiring explicitness rather
than heuristics, a response assembly plan that closes the uncertainty-
vocabulary gap, a boundary disclosure plan that resolves 131C's
newly-discovered six-item/nine-field mapping gap by reusing the real
schema verbatim, a provenance plan that closes all three missing
elements with concrete field-by-field guidance, a failure handling
plan giving every enumerated condition a dedicated path, an identity
resolution plan that reuses Track 130's already-proven pattern
directly rather than reinventing it, a conceptual (not schema) request/
response model, a phased implementation decomposition, and a
verification strategy 131F can execute against real generated output.
All five 131C non-blocking findings are addressed by design; none are
repaired in this phase, and none required any architectural scope
expansion to resolve.

This phase does not itself implement anything, does not modify any
schema, source code, or test code, and does not take any step toward
Decision Evaluation, Execution Planning, execution authorization, or
execution capability - all of which remain correctly deferred.

No implementation occurred. No schema changed. No runtime behavior
changed. Runtime remains `Observed`/`observe`/execution-unavailable.

Recommended next phase: 131E - Unified Repository Intelligence Query
Prototype.
