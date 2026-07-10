# Phase 132E - Repository Intelligence Service Prototype

## 1. Implementation Summary

132E implements the first deterministic, read-only Repository
Intelligence Service prototype exactly as scoped by 132A (architecture),
132B (frozen contract), 132C (independent verification, zero BLOCKING
findings), and 132D (engineering plan). A new, additive package -
`src/pcae/repository_intelligence/service/` - provides the canonical
composition layer over Unified Query (Track 131, independently
verified complete). **No existing Track 119-131 source file or schema
was modified** (confirmed via `git diff --stat`, empty). A governed
CLI command (`pcae repository-intelligence service`) and 50 focused
tests were added; all pass, plus 179 Track 121/122/123/130/131
regression tests and the full 4390-test fast_green suite, both
unchanged.

## 2. Implemented Lifecycle

All nine stages 132D Section 3 planned, no additional ones:

1. **Service request** - `ServiceRequest` (`request.py`): `kind`
   (entity/artifact/scoped/composite), `target`, `families`
   (allow-list), `composite_targets`, `include_evidence`.
2. **Request validation** - `normalize_service_request` validates
   structural shape per kind (entity: no families; artifact: exactly
   one family; scoped: one or more families; composite: no target, at
   least one inner target, no nesting), raising `ValueError`
   (translated to `MalformedServiceRequestError` by the engine).
3. **Unified Query invocation** - `service_engine.py` calls
   `unified_query.execute_unified_query` exclusively, once per
   resolved family, via `FAMILY_TO_CATEGORY`'s mapping onto Unified
   Query's own six real single-family categories.
4. **Response composition** - `_execute_single`/`_execute_composite`
   combine returned `UnifiedQueryResponse` objects, keyed by family,
   in `SIX_ARTIFACT_FAMILIES`'s fixed declared order.
5. **Provenance assembly** - each family's `references` (each carrying
   its own complete six-element provenance, unchanged) are placed
   under that family's key.
6. **Evidence assembly** - each family's `evidence` tuple carried
   forward verbatim, opt-in.
7. **Limitation propagation** - the union of every consumed call's own
   `limitations` plus Service-level composition limitations (skipped/
   failed family disclosures).
8. **Boundary disclosure propagation** - `unified_query.boundary.
   unified_query_boundary_disclosures()`/`unified_query_boundary_
   notes()` called directly - the same real objects, not reconstructed.
9. **Service response** - `ServiceResponse.to_dict()`, deterministic
   throughout.

## 3. Unified Query Integration

`service_engine.py` imports and calls `execute_unified_query` directly
(`from pcae.repository_intelligence.unified_query import ...
execute_unified_query`) - the sole point of contact with Track 131.
**No routing, identity resolution, or artifact loading is duplicated
anywhere in the service package** - confirmed by
`TestIdentityReuse::test_no_identity_derivation_function_in_service_
package`, which asserts no identity-derivation function exists in
`service_engine.py`'s own source. `FAMILY_TO_CATEGORY` maps each of
the six families to Unified Query's own real category name
(`rks_entity_lookup`, `dependency_node_lookup`, etc.) - no new
category is introduced.

## 4. Composition Implementation

For each family in a request's resolved scope (Section 5), the engine:
loads no artifact directly; calls `execute_unified_query` with that
family's own category; on success, records the family's `references`/
`evidence`/`limitations`/`uncertainty` under its own key and appends a
`"queried"` composition-metadata entry; on a missing artifact path,
appends a `"skipped"` entry plus an explicit limitation; on
`SnapshotLoadError`/`SnapshotCompatibilityError`, appends a `"failed"`
entry plus an explicit limitation - **never swallowed, never silently
skipped without disclosure**.

**Composition never reinterprets, infers, strengthens, or creates
knowledge**: the engine only ever relocates already-existing
`UnifiedQueryResponse` fields into a keyed structure - no function
recomputes a value, and the response shape itself (Section 6) is
closed to the categories 132B Section 8 authorizes.

## 5. Composite Request Implementation

Implements exactly the bounded model 132D approved: a composite
request's `composite_targets` are each independently normalized and
composed via `_execute_single` - **no correlation across targets**.
Inner responses are sorted by their own target string
(identifier-lexicographic, matching every other Repository
Intelligence array's ordering discipline) before being wrapped in the
outer `ServiceResponse.composite_responses` tuple.
`TestCompositeRequests::test_composite_never_correlates_across_targets`
directly confirms one target's own miss never influences another's
own independently-computed result. Cross-target reasoning remains
explicitly deferred, per 132D Section 5 - no code path in this
prototype computes a relationship between two composite targets.

## 6. Response Structure

`ServiceResponse` (`response.py`) is a closed dataclass:
`request_metadata`, `families` (dict keyed by family name),
`composition_metadata`, `limitations`, `uncertainty`,
`boundary_disclosures`, `boundary_notes`, `result_status`,
`composite_responses`. `to_dict()` adds a `determinism` block, mirroring
`UnifiedQueryResponse.to_dict()`'s own pattern.
`TestCompatibilityRegression::test_response_is_closed_shape`
independently confirms no field exists outside this set.

## 7. Composition Metadata Implementation

**Directly resolves 132C's independently-confirmed composition-
metadata-boundary finding** (132D Section 6): `composition_metadata`
is a separate, top-level tuple of records
(`{"family", "category", "status", "reason"?, "result_status"?}`),
never nested inside any reference's own `provenance` dict.
`TestProvenancePreservation::test_composition_metadata_never_nested_
in_provenance` and `TestCompositionMetadata::test_composition_
metadata_never_states_entity_content_claims` both independently confirm
this field records only which calls occurred, never a claim about
entity content.

## 8. Provenance Implementation

Provenance is never recomputed by this package - every reference's
`provenance` dict is the exact dict Unified Query's own
`build_provenance` already constructed, carried forward unchanged.
`TestProvenancePreservation::test_provenance_matches_source_unified_
query_call` independently confirms byte-for-byte equality between a
Service-composed reference's provenance and the same target queried
directly through Unified Query.

## 9. Evidence Preservation

Evidence is opt-in (`include_evidence=True`) and, when included, is
the exact tuple Unified Query's own `evidence` field already contains
- no transformation. `TestEvidencePreservation::test_evidence_
verbatim_when_requested` confirms byte-equality against the source
record.

## 10. Boundary Disclosure Implementation

**Reuses the existing object exactly, introduces no new disclosure
model**: `service_engine.py` calls `unified_query.boundary.
unified_query_boundary_disclosures()` directly - the same function
Unified Query's own response-construction stage calls.
`TestBoundaryDisclosurePropagation::test_boundary_disclosures_match_
unified_query_object_exactly` independently confirms the Service's own
`boundary_disclosures` field is `==` to Unified Query's own real
object, not a reconstruction.

## 11. Failure Handling Implementation

| Condition | Implemented behavior |
| --- | --- |
| unsupported request | `UnsupportedServiceRequestError` (new) - raised when a resolved scope is empty |
| malformed request | `MalformedServiceRequestError` (new) wrapping `ValueError` from `normalize_service_request` |
| unresolved entity | explicit uncertainty record (from the underlying Unified Query call itself, carried forward) |
| unresolved composition | the composite response still returns; the failed inner target's own response carries its own explicit uncertainty, never a silent drop |
| missing Repository Intelligence artifact | recorded as an explicit limitation + `"skipped"` composition-metadata entry, composition continues for other families |
| Unified Query failure (`SnapshotCompatibilityError`) | recorded as an explicit limitation + `"failed"` composition-metadata entry, never swallowed |

**No inferred recovery** anywhere: every failure path either raises or
produces an explicit record.

## 12. Silent-Omission Regression Coverage

**Directly re-tests, one layer up, the exact defect class 131F
discovered and 132B Section 15 binds this lineage to treat as
BLOCKING.** Three dedicated tests
(`TestSilentOmissionRegression`): a total miss across all families
never returns `result_status: "ok"` with empty content; a request with
no artifact paths supplied at all never returns a silent `"ok"`; a
composite request's inner miss is always explicit, never silently
dropped from the outer envelope. All three independently verified
passing. The engine itself includes a defensive final check
(`service_engine.py`'s own "no silent omission" block) that forces an
explicit uncertainty record if a single-target request's composition
would otherwise produce zero references, zero uncertainty, and zero
limitations - a structural guarantee, not merely a convention.

## 13. Test Coverage

50 new focused tests in
`tests/test_phase_132e_repository_intelligence_service_prototype.py`,
organized by the phase's own required areas: request validation (10),
scope resolution (3), service lifecycle (3), Unified Query reuse (3),
composite requests (3), deterministic composition (2), provenance
preservation (2), evidence preservation (2), uncertainty/limitation
propagation (2), boundary disclosure propagation (2), composition
metadata (2), identity reuse (2), fail-closed behavior (4), silent-
omission regression (3), read-only guarantees (3), and compatibility/
regression (4). All test fixtures generate real artifacts against the
real repository, generated once via a module-scoped pytest fixture and
shared read-only across all 50 tests - directly applying the
performance lesson 131E's own implementation surfaced (per-test
regeneration is prohibitively slow because Historical Memory
generation walks full git history); this phase's own suite passed on
its first run with no fixture-related fix needed.

## 14. Regression Results

- **New suite**: 50/50 passed.
- **Track 121/122/123/130/131/132 combined regression**: 179/179
  passed, unchanged.
- **fast_green**: 4390/4390 passed, count unchanged by design.
- **compileall**: clean across all of `src/` and `tests/`.

## 15. Compatibility Confirmation

Direct `git diff --stat` scoping at this phase's own finalization
confirms: zero modifications to any of the eight
`schemas/repository_intelligence/**/*.schema.json` files; zero
modifications to any existing file under
`src/pcae/repository_intelligence/query/`,
`src/pcae/repository_intelligence/dependency_graph/`,
`src/pcae/repository_intelligence/historical_memory/`,
`src/pcae/repository_intelligence/change_impact/`,
`src/pcae/advisory/`,
`src/pcae/repository_intelligence/cross_artifact_integration/`, or
`src/pcae/repository_intelligence/unified_query/`. This package only
ever *imports from* `unified_query/` (`execute_unified_query`,
`UnifiedQueryRequest`, `unified_query_boundary_disclosures`,
`unified_query_boundary_notes`, `SIX_ARTIFACT_FAMILIES`), never
modifies it. Two files were edited outside the new package:
`src/pcae/commands/repository_intelligence.py` (added one new command
function, `run_repository_intelligence_service`) and `src/pcae/cli.py`
(added one new subparser block) - both purely additive, no existing
line changed.

## 16. Runtime Behavior Confirmation

**Runtime behavior outside the Repository Intelligence Service did not
change.** `pcae runtime inspect` at this phase's own finalization
re-confirms runtime state `Observed`, execution capability
`unavailable`, maximum plugin capability `observe`, zero registered
runtime plugins. This package performs no execution, no runtime plugin
registration, and no capability expansion.

## 17. Known Limitations

- **CLI does not expose composite requests** - the CLI surface
  (`pcae repository-intelligence service`) supports `entity`,
  `artifact`, and `scoped` kinds; composite requests are only
  reachable via the Python API
  (`pcae.repository_intelligence.service`) in this first prototype -
  correctly deferred, matching 132D's own "start bounded" discipline.
- **No cross-target correlation** - by design (132D Section 5); a
  future phase may revisit this as its own, separately-scoped
  decision.
- **Inherits the Track 122/123 schema/reality divergence** -
  independently discovered in 131E, re-confirmed in 131F/132C: this
  package reaches Change Impact/Advisory Context content exclusively
  through Unified Query, which already handles the real (non-schema-
  conformant) output shape correctly - this prototype introduces no
  new exposure to that gap, and does not repair it (out of scope).

## 18. Deferred Capabilities (Confirmed Absent)

Reasoning, inference, recommendations, ranking, Decision Evaluation,
execution planning, and execution capability were not introduced
anywhere in this package - confirmed by direct code review (no
function named or behaving as any of these verbs exists in any of the
five new modules) and by `TestBoundaryDisclosurePropagation`'s own
assertion that every response carries the `non_decision`/
`no_execution`/`decision_evaluation_required` disclosures as `true`.

## 19. Strict Non-Goals Confirmation

This phase did not: modify Unified Query; modify Repository
Intelligence; modify any schema; introduce networking; introduce REST;
introduce GraphQL; introduce dashboards; introduce Decision Evaluation
changes; introduce Permission Broker changes; introduce execution
planning; introduce execution capability; introduce runtime plugins.

## 20. PFN-001 Confirmation

The Phase Finalization Notification Invariant (128B.2), re-confirmed
still globally binding, unamended by this phase:

- **Every terminal phase outcome** shall produce exactly one trusted
  canonical phase report delivered to the configured notification
  sink. This phase (132E) satisfies this identically to every phase
  since 128B.2.
- **Notification delivery or an explicit durable delivery-failure
  record** remains mandatory; silent omission remains prohibited (a
  fittingly self-referential guarantee, given Section 12's own focus).
- **No amendment.** This phase does not modify PFN-001's own contract
  text.

**PFN-001 remains globally applicable and is satisfied by this
phase.**

## 21. Confirmations

- **Execution remains unavailable.** No execution capability was
  introduced by this phase.
- **No runtime behavior changed outside the Repository Intelligence
  Service.** Confirmed via `pcae runtime inspect` (Section 16).
- **No schema changed.** Confirmed via `git diff` scoping (Section
  15).

## 22. Conclusion

132E implements the first Repository Intelligence Service prototype
exactly as 132A-132D scoped it: a new, additive, read-only package
providing deterministic, governed composition over Unified Query,
reusing Unified Query's own real entry point exclusively rather than
duplicating routing, identity, or artifact-loading logic. It resolves
132C's composition-metadata-boundary finding via a structurally-
separated field, implements the bounded, non-correlating composite-
request model 132D approved, and - critically - directly re-tests the
exact silent-omission defect class 131F discovered one layer down,
confirming this new composition layer does not repeat it. 50 new
focused tests and 179 regression tests pass, plus the full 4390-test
fast_green suite unchanged.

Execution remains unavailable. No runtime behavior changed outside the
Repository Intelligence Service. No schema changed.

Recommended next phase: 132F - Repository Intelligence Service
Independent Verification.
