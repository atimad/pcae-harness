# Phase 131E - Unified Repository Intelligence Query Prototype

## 1. Implementation Summary

131E implements the first deterministic, read-only Unified Repository
Intelligence Query prototype exactly as scoped by 131A (architecture),
131B (frozen contract), 131C (independent verification, zero BLOCKING
findings), and 131D (engineering plan). A new, additive package -
`src/pcae/repository_intelligence/unified_query/` - provides a single
query interface over all six covered artifact families (Repository
Knowledge Snapshot, Dependency Knowledge Graph, Historical Memory,
Change Impact, Advisory Context, Cross-Artifact Integration). **No
existing Track 119-130 source file or schema was modified.** A
governed CLI command (`pcae repository-intelligence unified-query`)
and 43 focused tests were added; all pass, plus 86 Track 121/122/123/
130 regression tests and the full 4390-test fast_green suite, both
unchanged.

## 2. Implemented Query Lifecycle

All nine stages 131D Section 3 planned, no additional ones:

1. **Query request** - `UnifiedQueryRequest` (`request.py`): category,
   target, `include_evidence`, filters.
2. **Query normalization** - `normalize_request` sorts filters and
   validates structural shape, raising `ValueError` on malformed
   input (translated to `MalformedRequestError` by the engine).
3. **Routing** - `routing.route`: a fixed `ROUTING_TABLE` dict lookup.
4. **Artifact resolution** - `artifact_loading.py`: one loader per
   family, reusing Track 121's `load_snapshot` for Repository
   Knowledge Snapshot directly.
5. **Response assembly** - one handler function per routing-table
   category in `unified_query_engine.py`.
6. **Provenance attachment** - `provenance.build_provenance`, all six
   elements, always.
7. **Evidence preservation** - verbatim `dict(record)` copies, opt-in
   only.
8. **Boundary disclosure attachment** - `boundary.
   unified_query_boundary_disclosures`, the real nine-field schema.
9. **Response delivery** - `UnifiedQueryResponse.to_dict()`,
   deterministic identifier-lexicographic ordering throughout.

## 3. Routing Implementation

`routing.ROUTING_TABLE` declares seven categories: one single-family
lookup per covered artifact family, plus the one explicitly-enumerated
multi-family category (`change_impact_to_dependency_node`, per 131B
Section 12). Multi-family validity is gated by a **second, independent**
constant, `MULTI_FAMILY_CATEGORIES` - deliberately not derived from
`ROUTING_TABLE` itself, so that a hypothetical future table entry with
more than one family that is *not* also added to this independent
allow-list fails closed with `RoutingAmbiguityError` rather than being
silently accepted. This is directly unit-tested
(`test_undeclared_multi_family_category_raises_routing_ambiguity`) by
injecting a synthetic table entry absent from the real allow-list -
the real, shipped `ROUTING_TABLE` never triggers this path itself,
by design, since every entry in it is already vetted.

An unsupported category raises `UnsupportedQueryCategoryError`. No
heuristic, fuzzy, or case-insensitive category matching exists -
confirmed by `test_no_heuristic_matching_of_category_names`.

## 4. Artifact Resolution Implementation

Each of the six families gets a thin, additive loader in
`artifact_loading.py`. Repository Knowledge Snapshot and Dependency
Knowledge Graph loaders validate `executable_schema_version` against
their real frozen values (`119O.1.0-json-schema`,
`119S.1.0-json-schema`) and fail closed
(`SnapshotCompatibilityError`) on mismatch, exactly as Track 121/130's
own existing loaders already do. **Change Impact and Advisory Context
loaders validate against the real generator's actual output shape,
not the frozen schema's nominal field names** - see Section 10.

## 5. Provenance Implementation

`provenance.build_provenance` always populates all six 131B Section 9
elements. Element 6 (verification state) uses the real
`uncertainty_verification_state.schema.json` shape (reusing
`attribution.verification_state` directly) with an explicit
`"unknown"` fallback when a source record carries no verification
state of its own - never an omitted field. This closes the gap 131C
independently identified in the one pre-existing precedent
(`query_engine.py`'s `_source_artifact`, which supplied only elements
1/3/4).

## 6. Evidence Preservation Implementation

Evidence is opt-in (`include_evidence=True`) and, when included, is
an exact `dict(record)` copy - no transformation, no strengthening, no
inference. Confirmed by `test_evidence_verbatim_when_requested`
(byte-equal to the source record) and `test_evidence_omitted_by_default`.

## 7. Boundary Disclosure Implementation

`boundary.py` imports `BOUNDARY_DISCLOSURES`/`BOUNDARY_NOTES` directly
from Track 130's `integration_builder.py` - the exact same nine-field
object, byte-for-byte, resolving 131C's independently-discovered
mapping gap between 131B's six-item conceptual list and the real
schema (131D Section 6's planned resolution). Every response, even an
unresolved one, carries all nine fields set to `true`
(`test_disclosures_present_even_on_unresolved_query`).

## 8. Failure Handling Implementation

| Condition | Exception/behavior | Status |
| --- | --- | --- |
| unsupported query | `UnsupportedQueryCategoryError` (new) | tested |
| unresolved routing (undeclared multi-family) | `RoutingAmbiguityError` (new) | tested |
| missing artifact | `SnapshotLoadError` (reused, Track 121) | tested |
| unresolved identifier | explicit uncertainty record (not an exception) | tested |
| incompatible artifact | `SnapshotCompatibilityError` (reused, Track 121) | tested |
| malformed request | `MalformedRequestError` wrapping `ValueError` (reused pattern) | tested |

No inferred recovery anywhere: every miss either raises or produces an
explicit `unresolved`-state record; no `except: pass`, no silent
default.

## 9. Identity Resolution Integration

`identity.py` imports Track 130's real `_node_id_for_entity` function
directly (no reimplementation) and applies plain exact dict-key
lookups (`find_by_id`) against each family's own already-existing
identifier fields. The multi-family handler
(`_handle_change_impact_to_dependency_node`) consumes Track 130's
already-built `entity_resolutions`/`unresolved_identities` records
directly rather than re-deriving the relationship - the same
`node_id`-derivation logic runs exactly once, inside Track 130's own
generator, never duplicated here.

`TestIdentityResolution::test_exact_match_required_no_fuzzy_resolution`
independently re-applies 130F's own five-class near-miss probe pattern
(trailing slash, uppercase, leading whitespace, truncated) against a
real Dependency Knowledge Graph node identifier - all four probes
correctly resolve to `unresolved`, confirming no fuzzy/alias/
probabilistic/silent-merge behavior exists anywhere in this package.

## 10. Genuine Findings Discovered During Implementation

Independently discovered while implementing artifact loaders against
*real* generator output (not schema prose) - not previously documented
by 130A-131D:

- **Change Impact (Track 123) schema/reality divergence**: the real
  `ChangeImpactReport.to_dict()` emits `impacted_entities`/
  `limitation_bundle`/`boundary_disclosure_bundle`/`report_metadata`
  and carries **no** `report_identity` field and **no**
  `executable_schema_version` field at all - diverging from
  `change_impact_report.schema.json`'s own declared top-level names
  (`affected_entities`/`report_limitations`/`boundary_disclosures`/
  `report_identity`). Track 130's own `integration_builder.py` already
  silently works around this (its own code comment already flagged
  the missing identity/envelope fields specifically); this phase's
  `load_change_impact` follows that same precedent explicitly and
  documents the full divergence for the first time.
- **Advisory Context (Track 122) schema/reality divergence**: the
  same class of gap. The real `RepositoryIntelligenceContextPackage.
  to_dict()` emits `selected_repository_intelligence`/
  `limitation_bundle`/`boundary_disclosure_bundle`/`context_metadata`
  and carries no `package_identity` field - diverging from
  `advisory_intelligence_context_package.schema.json`'s declared
  `package_identity`/`context_items`/`package_scope` shape.
  `selected_repository_intelligence` entries are, in fact, raw
  Repository Knowledge Snapshot records passed through unchanged
  (confirmed by direct reading of `advisory_context_builder.py`).
- **Historical Memory (Track 127) and Dependency Knowledge Graph
  (Track 126) do not exhibit this divergence** - both real generators'
  output matches their own frozen schemas exactly (`snapshot_identity`,
  `historical_events`/`event_id`, `nodes`/`node_id` all confirmed
  present as declared). This appears correlated with chronology: 122
  and 123 are earlier, pre-124-hardening-era tracks; 126 and 127
  received later, more careful schema-conformance treatment.

**Not repaired in this phase** - modifying Track 122/123's schemas or
generators is explicitly out of this phase's scope (Section 17). This
package's loaders are written against the real, current output shape
(matching Track 130's own already-proven working precedent), so this
finding does not block 131E's own correctness; it is recorded here as
a known limitation (Section 15) and as new evidence for a future,
separately-scoped schema-conformance hardening phase to consider.

## 11. Test Coverage

43 new focused tests in
`tests/test_phase_131e_unified_repository_intelligence_query_prototype.py`,
organized by the phase's own required areas: request normalization (4),
routing (6), single-family queries (6, one per covered family),
multi-family queries (2), unresolved/unsupported routing (2), identity
resolution (2), provenance completeness (2), evidence preservation
(2), uncertainty/limitation propagation (2), boundary disclosure
attachment (2), deterministic responses (2), fail-closed behavior (4),
read-only guarantees (2), and compatibility/regression (5). All test
fixtures generate real artifacts against the real repository (mirroring
126E/127E/130E's own established fixture pattern), generated once via
a module-scoped pytest fixture and shared read-only across all 43
tests (not regenerated per test - the original per-test regeneration
design was found, during this phase's own work, to be prohibitively
slow because Historical Memory generation walks full git history; the
module-scoped fixture reduced the suite from an unbounded hang to 37
seconds).

## 12. Regression Results

- **New suite**: 43/43 passed.
- **Track 121/122/123/130 regression** (`test_phase_121e_*.py`,
  `test_phase_122e_*.py`, `test_phase_123e_*.py`,
  `test_phase_130e_*.py`): 86/86 passed, unchanged.
- **fast_green**: 4390/4390 passed, count unchanged by design (this
  package's own new tests are not tagged `fast_green`, consistent
  with prior phases' own convention of keeping fast_green's count
  stable across documentation-adjacent implementation phases unless
  explicitly extending it).
- **compileall**: clean across all of `src/` and `tests/`.

## 13. Compatibility Confirmation

Direct `git diff`/`git status` scoping at this phase's own
finalization confirms: zero modifications to any of the eight
`schemas/repository_intelligence/**/*.schema.json` files; zero
modifications to any existing file under
`src/pcae/repository_intelligence/query/`,
`src/pcae/repository_intelligence/dependency_graph/`,
`src/pcae/repository_intelligence/historical_memory/`,
`src/pcae/repository_intelligence/change_impact/`,
`src/pcae/advisory/context/`, or
`src/pcae/repository_intelligence/cross_artifact_integration/`. This
package only ever *imports from* those modules (Track 130's
`_node_id_for_entity`/`BOUNDARY_DISCLOSURES`, Track 121's
`load_snapshot`/`evaluate_query`/`SnapshotLoadError`/
`SnapshotCompatibilityError`), never modifies them. Two files were
edited outside the new package: `src/pcae/commands/
repository_intelligence.py` (added one new command function,
`run_repository_intelligence_unified_query`) and `src/pcae/cli.py`
(added one new subparser block) - both purely additive, no existing
line changed.

## 14. Runtime Behavior Confirmation

**Runtime behavior outside the query subsystem did not change.**
`pcae runtime inspect` at this phase's own finalization re-confirms
runtime state `Observed`, execution capability `unavailable`, maximum
plugin capability `observe`, zero registered runtime plugins. This
package performs no execution, no runtime plugin registration, and no
capability expansion - it is a new, read-only Python package under
`src/pcae/repository_intelligence/`, invoked only through explicit CLI
calls or direct function calls, never automatically.

## 15. Known Limitations

- **Six single-family categories, one multi-family category**: this
  first prototype implements exactly one query per covered family
  (131D Section 2.5's completion criterion) plus the one relationship
  category Track 130 itself already computes. It does not implement
  every conceivable query shape (e.g. filtering, pagination, or
  additional multi-family relationship categories) - correctly
  deferred, matching Track 130's own "implement exactly one
  relationship category first" precedent.
- **Change Impact / Advisory Context schema divergence** (Section 10)
  - this package's loaders work correctly against real output, but the
  underlying Track 122/123 schema-conformance gap remains unrepaired
  and is now, for the first time, explicitly documented in full.
- **`change_impact_to_dependency_node` requires a pre-built
  Cross-Artifact Integration package** - this category does not
  compute the relationship itself (by design, 131B Section 12); a
  caller must have already run `pcae repository-intelligence
  cross-artifact-integration generate` for the relevant Change Impact/
  Dependency Knowledge Graph pair.
- **No caching or indexing** - each query call re-reads and re-parses
  its artifact file(s) from disk; 131D Section 4 explicitly does not
  require this, and none was added.

## 16. Deferred Capabilities (Confirmed Absent)

Reasoning, inference, recommendations, ranking, Decision Evaluation,
execution planning, and execution capability were not introduced
anywhere in this package - confirmed by direct code review (no
function named or behaving as any of these verbs exists in any of the
nine new modules) and by `TestFailClosedBehavior`/
`TestBoundaryDisclosureAttachment`'s own assertions that every response
carries the `non_decision`/`no_execution`/`decision_evaluation_required`
disclosures as `true`.

## 17. Strict Non-Goals Confirmation

This phase did not: modify any Repository Intelligence schema; modify
any existing Track 119-130 source file; introduce reasoning,
recommendations, ranking, Decision Evaluation, execution planning, or
execution capability; modify runtime state; change governance
behavior; or expand the existing Track 121 Query Layer's own
`SUPPORTED_QUERY_CATEGORIES` contract (it remains untouched, confirmed
by `test_track_121_query_layer_unaffected`).

## 18. PFN-001 Confirmation

The Phase Finalization Notification Invariant (128B.2), re-confirmed
still globally binding, unamended by this phase:

- **Every terminal phase outcome** shall produce exactly one trusted
  canonical phase report delivered to the configured notification
  sink. This phase (131E) satisfies this identically to every phase
  since 128B.2.
- **Notification delivery or an explicit durable delivery-failure
  record** remains mandatory; silent omission remains prohibited.
- **No amendment.** This phase does not modify PFN-001's own contract
  text.

**PFN-001 remains globally applicable and is satisfied by this
phase.**

## 19. Confirmations

- **Execution remains unavailable.** No execution capability was
  introduced by this phase.
- **No runtime behavior changed outside the query subsystem.**
  Confirmed via `pcae runtime inspect` (Section 14).
- **No schema changed.** Confirmed via `git diff` scoping (Section
  13).

## 20. Conclusion

131E implements the first Unified Repository Intelligence Query
prototype exactly as 131A-131D scoped it: a new, additive, read-only
package providing a single deterministic query interface over all six
covered artifact families, reusing Track 121's Query Layer and Track
130's identity-resolution/boundary-disclosure precedents directly
rather than reinventing them, closing all three provenance gaps and
the boundary-disclosure mapping gap 131C independently identified, and
introducing exactly two new exception classes while reusing four
existing ones. 43 new focused tests and 86 regression tests pass, plus
the full 4390-test fast_green suite unchanged. Along the way, this
phase independently discovered and documented (without repairing) a
genuine, previously-undocumented schema/reality divergence in Tracks
122 and 123 - a new, concrete finding for a future hardening phase,
not a defect in this phase's own scope.

Execution remains unavailable. No runtime behavior changed outside the
query subsystem. No schema changed.

Recommended next phase: 131F - Unified Repository Intelligence Query
Independent Verification.
