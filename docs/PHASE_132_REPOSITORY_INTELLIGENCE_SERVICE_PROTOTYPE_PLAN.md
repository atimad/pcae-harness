# Phase 132D - Repository Intelligence Service Prototype Plan

## 1. Purpose

132A defined the architecture, 132B froze the binding contract, and
132C independently verified that contract against real Unified Query
source with zero BLOCKING findings. This phase converts the verified
contract into a **deterministic engineering plan** for 132E's
implementation - the bounded set of decisions a builder needs (what
module goes where, what each stage does, what fails closed and how)
without writing any of it.

**This phase implements nothing.** No source file, test file, or
schema is created or modified. Every planning decision below traces to
a specific 132B contract clause or a specific 132C verification
finding; nothing here introduces new architectural scope beyond what
132A-132C already authorized.

## 2. Prototype Objectives

### 2.1 Implementation goals

Build the first deterministic, read-only Repository Intelligence
Service prototype: a composition layer that issues one or more
Unified Query calls per request and returns a single, coherent,
provenance-complete package - entirely governed by 132B's contract.

### 2.2 Architectural boundaries

- **In bounds**: a new `src/pcae/repository_intelligence/service/`
  package (mirroring `unified_query/`'s own directory-naming
  precedent one layer down); a governed CLI command
  (`pcae repository-intelligence service`, matching the existing
  `pcae repository-intelligence unified-query` naming precedent in
  `src/pcae/commands/repository_intelligence.py`); composition logic
  that calls `execute_unified_query` (Unified Query's own real,
  exported entry point - `from pcae.repository_intelligence.
  unified_query import execute_unified_query`, confirmed present in
  `unified_query/__init__.py`'s own `__all__`) one or more times per
  request.
- **Out of bounds** (132E may not do any of this without a new
  governed decision): modifying any schema file; modifying
  `unified_query/`'s own source (`routing.py`, `identity.py`,
  `artifact_loading.py`, `provenance.py`, `boundary.py`,
  `unified_query_engine.py`) or any other Track 119-131 source file
  (132E is strictly additive - a new package, zero edits to existing
  packages, mirroring 131E's own zero-modification precedent, 132C
  Section 18's independently-verified evidence for this); implementing
  reasoning, inference, ranking, recommendation, Decision Evaluation,
  execution planning, or execution capability (132B Section 2/15).

### 2.3 Implementation sequence

132E should implement in the dependency order this plan's lifecycle
implies (Section 3): (1) service request/validation types, (2) Unified
Query invocation planning (which categories a given request scope
requires), (3) composition (combine multiple `UnifiedQueryResponse`
objects), (4) provenance/evidence/limitation/uncertainty/boundary
carry-forward, (5) CLI wiring, (6) fail-closed error paths threaded
through every stage above rather than bolted on afterward - matching
Unified Query's own precedent where `execute_unified_query` raises
inline at each stage (routing before artifact presence check before
handler dispatch), not in a separate pass.

### 2.4 Acceptance criteria (for 132E)

- An entity request naming one target resolves against every family
  with content for it, returning one composed response containing all
  applicable per-family sections (132A Section 7), each with complete
  six-element provenance (132B Section 10).
- An artifact request naming exactly one family produces a response
  scoped to that family alone - the other five sections absent, not
  fabricated as empty placeholders (132A Section 7's "present only
  when applicable").
- A scoped request's explicit family allow-list is never silently
  exceeded (132B Section 7).
- A request naming an unresolvable entity produces an explicit
  uncertainty record, never a silently-empty `"ok"`-equivalent
  response (132B Section 15's own binding BLOCKING-defect-class
  requirement, Section 9 below).
- Two runs against identical repository state and an identical request
  produce byte-identical output except approved timestamps (132B
  Section 13).

### 2.5 Completion criteria (for 132E)

132E is complete when: the prototype handles at least one entity
request per covered family (mirroring 131D Section 2.5's own "one
query per family" completion bar, one layer up) plus at least one
scoped request and the composite-request shape this plan resolves
(Section 5); every fail-closed condition enumerated in Section 9 below
has a corresponding raising code path; the CLI command is wired and
governed; and 132F's verification strategy (Section 11) can be run
against real composed output.

### 2.6 Confirmed properties

- **Deterministic** - Section 4's composition plan and Section 6's
  provenance plan both inherit the fixed-family-order,
  identifier-lexicographic discipline 132C Section 14 already
  independently confirmed is achievable by straightforward composition
  of Unified Query's own already-deterministic calls.
- **Read-only** - Section 2.2's implementation boundary permits no
  write call anywhere in the new `service` package; 132E must call
  `execute_unified_query` exclusively for all content access, never
  read an artifact file directly.
- **Derivative** - Section 6's response assembly plan bounds response
  content to exactly the categories 132B Section 8 already closes the
  list to; no field may be added outside that set.
- **Non-authoritative** - every composed element is a carried-forward
  Unified Query result; the Service originates no claim of its own
  (132B Section 4).
- **Governance-compatible** - Section 11 confirms this explicitly.

## 3. Service Lifecycle Plan

Nine conceptual stages, per 132B Section 6. **Responsibilities only -
no schema, no function signatures frozen here; 132E's own
implementation is informed by, but not dictated in exact code shape
by, this document.**

1. **Service request** - a consumer submits a target plus a scope,
   structurally analogous to `UnifiedQueryRequest` one layer down
   (`category`, `target`, `include_evidence`, `filters`). 132E's
   request type is a new, additive dataclass in the new package - it
   does not modify `unified_query/request.py`'s existing
   `UnifiedQueryRequest` type.
2. **Request validation** - canonicalize and validate the request
   before any Unified Query call is made, mirroring `normalize_
   request`'s own existing pattern one layer down (raise on malformed
   shape, e.g. an empty scope or an unrecognized family name in a
   scoped request's allow-list).
3. **Unified Query invocation** - resolve the request's scope into the
   set of Unified Query categories that must be called (Section 5),
   then call `execute_unified_query` once per resolved category -
   never fewer (silently skipping a requested family) and never more
   (silently expanding scope, 132B Section 7).
4. **Result composition** - combine the returned
   `UnifiedQueryResponse` objects into one structure, keyed by family,
   in the fixed family order `unified_query.routing.
   SIX_ARTIFACT_FAMILIES` already declares (Section 4).
5. **Provenance assembly** - every composed element's own six-element
   provenance chain (already complete per Unified Query's own
   contract, 132C Section 10's independent re-confirmation) is carried
   into the composed response unchanged (Section 6).
6. **Evidence assembly** - verbatim carry-forward from each consumed
   `UnifiedQueryResponse.evidence` tuple, opt-in exactly as Unified
   Query's own `include_evidence` is opt-in.
7. **Limitation propagation** - the union of every consumed call's own
   `limitations` tuple plus any Service-level composition limitation
   (e.g. "family X was not queried because the request's scope did not
   include it").
8. **Boundary disclosure propagation** - the same real nine-field
   object every consumed `UnifiedQueryResponse.boundary_disclosures`
   already carries - 132E must confirm all consumed calls return an
   identical object (they will, since `boundary.
   unified_query_boundary_disclosures()` is a pure function of no
   input) and propagate it unchanged, never re-deriving it.
9. **Service response** - the composed, deterministic package (Section
   6) is returned to the consumer.

**No additional stage.** 132E must not introduce a tenth stage or a
side effect inside any of these nine (132B Section 6's own binding
"no hidden lifecycle stage" requirement).

## 4. Composition Plan

**Exactly how multiple Unified Query results are composed**, resolving
132B Section 9's "may compose... shall never reinterpret" into
concrete mechanics:

1. For each family the request's resolved scope names (Section 3
   stage 3), call `execute_unified_query` with the category that
   family's own single-family lookup exposes today
   (`rks_entity_lookup`, `dependency_node_lookup`,
   `historical_event_lookup`, `change_impact_entity_lookup`,
   `advisory_context_item_lookup`, `cross_artifact_reference_lookup` -
   the six real categories `routing.ROUTING_TABLE` already declares,
   confirmed present and unchanged since 131F).
2. Collect each call's `UnifiedQueryResponse` **without inspecting or
   transforming its content** beyond reading its own already-public
   fields (`references`, `evidence`, `limitations`, `uncertainty`,
   `boundary_disclosures`, `result_status`).
3. Assemble the composed response's per-family sections by placing
   each call's `references` (and, when requested, `evidence`) under
   that family's own key, in the fixed order `SIX_ARTIFACT_FAMILIES`
   declares - never re-ordered by content, count, or any computed
   property.
4. **Composition shall remain deterministic**: no stage above depends
   on wall-clock time, call latency, or dict/set iteration order
   (matching 132B Section 13's own "no entropy" requirement,
   independently confirmed achievable in 132C Section 14 by pure
   composition of already-deterministic parts).
5. **Composition shall never reinterpret data**: no stage above reads
   a returned `reference`'s content to compute a new fact - only its
   own already-existing fields are relocated, never recomputed.
6. **Composition shall never strengthen evidence**: 132E introduces no
   function that upgrades a `verification_state` or adds a
   `derivation_path` claim beyond what each consumed
   `UnifiedQueryResponse` already carries (132B Section 10's explicit
   prohibition, restated here as an implementation constraint: no
   composition function may write to a `provenance` dict's own
   `verification_state`/`derivation_path` keys after reading them from
   a consumed response).
7. **Composition shall never create knowledge**: the composed
   response's total field set is bounded by Section 6's closed list;
   132E introduces no field computed by aggregating across families
   (e.g. no "entity summary" field synthesizing content from multiple
   families into one new claim - 132B Section 20.1's own
   already-flagged forward deferral, still correctly unresolved by
   this plan, Section 12 below).
8. **Composition shall preserve provenance**: Section 6.
9. **Composition shall preserve uncertainty**: every
   `UnifiedQueryResponse.uncertainty` tuple from every consumed call is
   carried into the composed response's own uncertainty collection
   unchanged, plus one additional record for any family a composite
   request named but which was never queried due to a fail-closed
   condition (Section 9).

## 5. Request Handling Plan

Concrete handling for the four conceptual categories 132A/132B named,
**resolving the composite-request-scope question 132B Section 7
explicitly deferred, without expanding architecture**:

- **entity requests** - resolve against every one of the six families'
  own single-family Unified Query category (Section 4 step 1),
  composing whatever subset returns a match. This is the default,
  unscoped shape.
- **artifact requests** - resolve against exactly one named family's
  own category - a strict subset of the entity-request logic (Section
  4's loop with a resolved-scope set of size one), not a separate code
  path.
- **scoped requests** - an entity or artifact request further narrowed
  by an explicit family allow-list; the resolved-scope set (Section 3
  stage 3) is the intersection of "families with a real category" and
  "families named in the allow-list" - never expanded beyond the
  allow-list, per 132B Section 7's own binding requirement.
- **composite requests** - **resolution for 132E's first prototype**:
  a composite request is planned as **N independent entity/artifact/
  scoped requests, each fully composed per Sections 3-4, then wrapped
  in one outer envelope keyed by target** - not a single fused
  composition. This is the minimal resolution consistent with 132B
  Section 9's "composition shall remain deterministic" (each inner
  request's own composition is already proven deterministic
  individually) and with 132A/132D's own "start bounded, defer the
  rest" discipline (131D Section 2.2's own precedent, applied here):
  **no cross-target correlation is implemented in 132E** - if two
  targets in one composite request are themselves related (e.g. via
  Cross-Artifact Integration), that relationship is only surfaced if
  it already appears within one target's own individual composition,
  never computed across the two independently-composed results. This
  resolves 132B's own open item by scoping composite requests as
  in-bounds for 132E, but explicitly bounded to independent,
  non-correlated composition - a future phase may revisit cross-target
  correlation as its own, separately-scoped decision.

**No schema, no protocol** - these remain conceptual request shapes for
132E's own internal request-handling code, not a frozen wire format.

## 6. Response Assembly Plan

Every response preserves the five categories 132B Section 8 requires,
**addressing 132C's composition-level-metadata-boundary finding**
(Section 19.1 of the 132C verification report) with a concrete
resolution:

- **provenance** - carried forward per-element, unchanged (Section 4
  step 8). **132E's concrete resolution of 132C's open boundary
  question**: composition-level metadata (which Unified Query calls
  were made, in what order, for which family) is recorded as a
  **separate, explicitly-labeled `composition_metadata` field**,
  distinct from and never merged into any per-element `provenance`
  dict. This makes the boundary 132C found unclear now concrete and
  mechanically checkable: a future 132F verification can confirm
  `composition_metadata` never appears nested inside a `provenance`
  dict, and that no field in `composition_metadata` states a claim
  about entity content (only about which calls occurred) - directly
  resolving 132C's own "what exactly counts as composition-level
  metadata versus a synthesized conclusion" question by giving it a
  distinct, structurally-separated home.
- **evidence** - Section 4 step 2, opt-in.
- **uncertainty** - Section 4 step 9.
- **limitations** - Section 3 stage 7.
- **boundary disclosures** - Section 3 stage 8, the real nine-field
  object (Section 7 below).

**No schema changes.** This response shape remains conceptual for
132E's own internal type, exactly as 132B Section 7/8 require -
132D does not authorize a JSON Schema file for it.

## 7. Boundary Disclosure Mapping Plan

**Directly resolves 132C's own independently-confirmed finding**
(132C Section 13): 132B's five-item conceptual boundary list
(derivative, read-only, deterministic, non-authoritative,
non-executing) does not literally name-match the real, frozen
`boundary_disclosure.schema.json`'s nine required fields.

**Decision for 132E: reuse the existing nine-field object verbatim,
exactly as Unified Query's own `boundary.py` already does one layer
down** - `unified_query_boundary_disclosures()` is a pure, no-argument
function returning `dict(BOUNDARY_DISCLOSURES)` (itself imported
verbatim from Track 130's `integration_builder.py`). 132E's own
boundary-propagation stage (Section 3 stage 8) calls this exact same
Unified Query function (or re-exports its result unchanged from a
consumed `UnifiedQueryResponse.boundary_disclosures`) rather than
constructing a new nine-field literal of its own - this is not merely
consistent with 131D's own "reuse verbatim, do not invent a new
schema" resolution one layer down, it is the *same object*, propagated
two layers instead of one.

**Concrete mapping table** (132B conceptual term -> real schema
field(s), restated from 131D's own equivalent table one layer down,
confirmed still accurate by 132C's independent re-derivation):

| 132B conceptual item | Real `boundary_disclosure.schema.json` field(s) |
| --- | --- |
| read-only | `read_only` (direct) |
| non-executing | `no_execution` (direct) |
| non-authoritative | `advisory_non_authority` (closest direct match) |
| derivative | `no_evidence_replacement` + `no_repository_state_replacement` (closest two-field approximation, no single field named "derivative") |
| deterministic | no direct field (this schema was never designed to assert determinism as a boolean property - 132E must not force a mapping where none exists; determinism remains a property this plan and 132F verify independently of the boundary-disclosure object itself) |

**This mapping is planning guidance, not a contract amendment** -
132B's own five-item prose remains binding contract text, unchanged by
this plan.

## 8. Identity Reuse Plan

**Require reuse of Unified Query identity resolution. Do not duplicate
identity logic.**

- 132E introduces **zero** identity-derivation functions of its own.
  Every identifier a composed response cites is one Unified Query
  itself already resolved (via `identity.find_by_id`'s own exact-match
  discipline, independently confirmed by 131F as the strongest
  evidence of any Unified Query dimension, and re-confirmed current by
  132C).
- **Exact identifier reuse**: a composite request's own per-target
  identifiers (Section 5) are passed through to each inner
  `UnifiedQueryRequest.target` unchanged - 132E performs no
  transformation, normalization beyond `normalize_request`'s own
  existing whitespace/type validation, or matching of its own.
- **Explicit unresolved state**: when a target resolves against zero
  families, the composed response's `uncertainty` collection (Section
  4 step 9) carries an explicit record - never a silently-absent
  target with no trace it was requested.
- **Reject aliases/fuzzy matching/probabilistic matching/silent
  merges**: mechanically guaranteed by 132E calling `execute_unified_
  query` exclusively for all identity work (Section 4 step 1) - since
  that function itself already fails closed on any near-miss (131F's
  own five-probe verification), a Service that introduces no
  identity code of its own cannot introduce a fuzzier resolution
  strategy than the one it exclusively delegates to.

## 9. Failure Handling Plan

**Deterministic fail-closed behavior**, one dedicated path per
condition, extending (never duplicating) Unified Query's own exception
model:

| Condition | Planned behavior | Precedent reused |
| --- | --- | --- |
| unsupported request (a scope/shape not in Section 5's four categories) | `UnsupportedServiceRequestError` (new, additive) | mirrors `UnsupportedQueryCategoryError`'s own message pattern |
| unresolved entity (a target that resolves against zero families) | explicit uncertainty record (Section 4 step 9), not an exception | mirrors Unified Query's own `unresolved_identity_record` pattern exactly - reused, not reinvented |
| unresolved composition (a composite request where one inner target fails while others succeed) | the composed response still returns, with the failed target's own inner section replaced by an explicit uncertainty record - never an all-or-nothing failure for the whole composite request, and never a silent drop of the failed target | new pattern, but directly modeled on 131F's own "partial success without disclosure" prohibition (132B Section 15) |
| missing Repository Intelligence artifact | propagated from the underlying `SnapshotLoadError` Unified Query itself raises (reused directly, not caught-and-rewrapped into a new type, preserving Unified Query's own already-correct exception identity) | `SnapshotLoadError` (Track 121, reused) |
| malformed request (an empty target, an unrecognized scope value) | `MalformedServiceRequestError` (new, additive) | mirrors `MalformedRequestError`'s own `ValueError`-translation pattern one layer down |
| unavailable Unified Query response (a category call itself raises `SnapshotCompatibilityError` or a routing error) | propagated directly, never swallowed - the composed response's own limitations collection (Section 3 stage 7) records which family could not be queried and why | `SnapshotCompatibilityError`/`RoutingAmbiguityError` (Track 121/131, reused) |

**No inferred recovery** anywhere in this table: every row either
raises or produces an explicit record; none silently retries, defaults,
or substitutes a best-guess result.

**Explicitly preserve the Track 131/132 silent-omission invariant.**
132B Section 15 binds this lineage to treat "silently return an empty
success for an unsatisfiable request" as a BLOCKING defect class,
naming 131F's own real, independently-discovered defect (one of
Unified Query's seven handlers originally lacked this guarantee for a
`target=None` request) as the concrete precedent. **132E's own
completion criteria (Section 2.4) must include an explicit test of the
exact analogous case one layer up**: a Service-level entity request
with no resolvable target across *any* family must produce
`result_status`-equivalent `"unknown"` with a non-empty uncertainty
collection - never an empty `"ok"`-equivalent composed response. This
plan requires 132E's own implementation to include this specific test
case by name (not merely "some" failure test), and requires 132F to
independently re-probe it fresh rather than trusting 132E's own test
suite alone - directly repeating the exact discipline that caught the
original defect one layer down.

## 10. Implementation Decomposition (for 132E)

Phased breakdown, one section per implementation concern:

1. **Request processing** - new request dataclass, validation function
   (Section 3 stages 1-2); reuses `normalize_request`'s own existing
   pattern, does not modify it.
2. **Unified Query integration** - scope-to-category resolution
   (Section 5), the per-family `execute_unified_query` call loop
   (Section 4 step 1); the sole point of contact with Track 131.
3. **Response composition** - the six-category closed response shape
   (Section 6), fixed family ordering (Section 4 step 3).
4. **Provenance integration** - per-element carry-forward plus the new
   `composition_metadata` field (Section 6), identity reuse (Section
   8).
5. **Boundary integration** - the boundary-propagation helper (Section
   7), reusing Unified Query's own real function/object.
6. **Failure handling** - the failure table (Section 9), threaded
   through stages 1-4 inline (Section 2.3), not as a separate pass.
7. **CLI/service interface** - CLI command wiring
   (`run_repository_intelligence_service` in `src/pcae/commands/
   repository_intelligence.py`, matching the existing
   `run_repository_intelligence_unified_query` pattern exactly), plus
   whatever governed phase-report/test evidence 132E's own
   finalization requires. "Service interface" here means the Python
   function signature future consumers (Section 5 of 132A/132B) will
   eventually call - not a network interface (132B/132D's own strict
   non-goal, unchanged).

## 11. Verification Strategy (for 132F)

132F must independently verify, against freshly generated real
composed output (not 132E's own tests, per the "re-derive, never
trust" discipline 130F/131F/132C all already applied):

- **Lifecycle correctness** - independently confirm all nine stages
  execute in the declared order with no hidden stage, mirroring 131F's
  own real-control-flow trace applied one layer up.
- **Deterministic composition** - two independent fresh runs against
  identical repository state produce byte-identical composed output
  except approved timestamps.
- **Provenance preservation** - independently confirm every composed
  element's six-element provenance chain matches the corresponding
  standalone Unified Query call's own provenance exactly (a direct
  differential check: composed-response element vs. the same target
  queried directly through Unified Query).
- **Evidence preservation** - independently confirm evidence content
  is byte-identical to the corresponding standalone Unified Query
  call's own evidence.
- **Boundary preservation** - independently confirm the composed
  response's `boundary_disclosures` object is field-for-field
  identical to the real, frozen schema's required set (131F's own
  key-for-key diff methodology, reused).
- **Identity reuse** - independently re-probe the same near-miss
  identifier classes 130F/131F already established (trailing slash,
  case-flip, leading whitespace, truncated) against a Service-level
  entity request, confirming zero fuzzy resolution at the composition
  layer.
- **Fail-closed behavior** - independently probe every row of Section
  9's failure table, **specifically re-probing the silent-omission
  case named in Section 9** as its own explicit, separately-reported
  check (not merely bundled into general failure testing).
- **Governance preservation** - `pcae health`/`check`/`doctor task-
  memory`/`runtime inspect` all clean, zero runtime plugins.
- **Compatibility with Tracks 119-132** - confirm via `git log`/`git
  diff --stat` (132C's own methodology) that 132E introduced no
  modification to any existing schema or source file outside the new
  `service` package.

## 12. Treatment of 132C Non-Blocking Findings

Both findings are addressed by this plan's design, **not repaired in
this phase**:

1. **Boundary-disclosure five-item/nine-field conceptual mapping gap**
   - Section 7 gives the concrete mapping table and the "reuse the
   same object, propagated two layers" resolution, directly extending
   131D's own equivalent resolution one layer down.
2. **Composition-level-metadata boundary question** - Section 6 gives
   a concrete resolution: a separate, explicitly-labeled
   `composition_metadata` field, structurally distinguishable from
   per-element `provenance` and mechanically checkable by 132F
   (Section 11).

**No architectural scope expansion**: both resolutions reuse an
already-existing pattern (verbatim schema reuse; structural separation
of metadata from content) rather than inventing a new capability or
authority.

## 13. Strict Non-Goals

This phase does not: implement Repository Intelligence Service; modify
Unified Query; modify Repository Intelligence; modify schemas; modify
source code; modify test code; introduce networking; introduce REST;
introduce GraphQL; introduce execution; introduce Decision Evaluation
changes; introduce Permission Broker changes; introduce runtime
plugins.

## 14. Governance Compatibility

- observe-only runtime unchanged;
- execution remains unavailable;
- this plan authorizes no schema change, no source change, no test
  change - confirmed by this phase's own final commit scope (`docs/`,
  `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/` only);
- raw git commit/push, force push, and `--no-verify` remain forbidden
  and were not used;
- PFN-001 remains satisfied (Section 16).

## 15. Confirmations

- **No implementation occurred.** This phase produced only planning
  documentation.
- **No runtime behavior changed.**
- **Execution remains unavailable.**

## 16. PFN-001 Confirmation

The Phase Finalization Notification Invariant (128B.2), re-confirmed
still globally binding, unamended by this phase:

- **Every terminal phase outcome** shall produce exactly one trusted
  canonical phase report delivered to the configured notification
  sink. This phase (132D) satisfies this identically to every phase
  since 128B.2.
- **Notification delivery or an explicit durable delivery-failure
  record** remains mandatory; silent omission remains prohibited (a
  fittingly self-referential guarantee, given Section 9's own focus).
- **No amendment.** This phase does not modify PFN-001's own contract
  text.

**PFN-001 remains globally applicable and is satisfied by this
phase.**

## 17. Conclusion

132D converts the 132B contract (independently verified with zero
BLOCKING findings by 132C) into a concrete, engineering-ready plan for
132E: a nine-stage lifecycle plan reusing Unified Query's own real
`execute_unified_query` entry point exclusively, a composition plan
that is deterministic and structurally prevented from reinterpreting,
strengthening, or creating knowledge, a request-handling plan that
resolves the composite-request-scope question 132B deferred (bounded
to independent, non-correlated per-target composition, with
cross-target correlation explicitly deferred further), a response
assembly plan that resolves 132C's composition-metadata-boundary
finding via a structurally-separated `composition_metadata` field, a
boundary disclosure plan that reuses the exact same real nine-field
object Unified Query itself already reuses, an identity plan that
introduces zero new resolution logic, a failure handling plan that
explicitly names and requires re-testing the exact silent-omission
case 131F discovered, a phased implementation decomposition, and a
verification strategy 132F can execute against real composed output.
Both 132C non-blocking findings are addressed by design; neither is
repaired in this phase, and neither required any architectural scope
expansion to resolve.

This phase does not itself implement anything, does not modify Unified
Query, Repository Intelligence, or any schema, and does not take any
step toward Decision Evaluation, Execution Planning, execution
authorization, or execution capability - all of which remain correctly
deferred.

No implementation occurred. No schema changed. No runtime behavior
changed. Runtime remains `Observed`/`observe`/execution-unavailable.

Recommended next phase: 132E - Repository Intelligence Service
Prototype.
