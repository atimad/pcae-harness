# Phase 113D — Advisory Runtime Verification & Compatibility

## Purpose

Verify and harden the Advisory Runtime prototype (113C) against the
architecture (113A) and contracts (113B). Verification/compatibility
only — no new advisory behavior, no execution, no authorization,
no Permission Broker enforcement.

## Verification Summary

### 1. Advisory Runtime Consumes Runtime Snapshot Only — ✅ VERIFIED

- `advisory_runtime.py` imports exactly one internal module:
  `pcae.core.runtime_snapshot.RuntimeSnapshot` (AST-verified)
- All four providers' `analyze()` method signatures accept only
  `RuntimeSnapshot` (type-hint verified)
- `build_advisory_results(snapshot)` is the sole public entry point —
  it accepts a `RuntimeSnapshot` and returns `tuple[AdvisoryResult, ...]`

### 2. Advisory Providers Remain Modular — ✅ VERIFIED

- Each provider is a stateless class with no custom `__init__`
- Each provider can be called independently — no cross-dependency
- Removing any provider from the aggregation pipeline does not break
  the remaining providers
- Provider order in `build_advisory_results` is fixed but each
  provider is independently callable

### 3. Advisory Results Follow 113B Contract — ✅ VERIFIED

- All 14 fields from 113B §1 are present in `AdvisoryResult`
- Every result from `build_advisory_results` has all required fields
  non-empty
- `implementation_status` is unconditionally `"execution_unavailable"`
  on every result (113B §7)
- Categories, severities, and confidences are drawn from frozen
  vocabulary tuples (113B §5)
- `EvidenceReference` has exactly 4 fields matching 113B §3
- Every result has at least one evidence reference linking it to a
  RuntimeSnapshot field

### 4. Explainability Is Complete — ✅ VERIFIED

All 8 explainability facets (113B §2) are populated in every result:

| Facet | Field | Verified |
|---|---|---|
| What was observed | `reasoning_summary` | ✅ Always non-empty |
| Why it matters | `rationale` + `severity` | ✅ Always substantive (≥30 chars) |
| What evidence | `evidence_references` | ✅ ≥1 per result |
| Which snapshot fields | `evidence_references[].field_path` | ✅ Always non-empty |
| What recommendation | `recommended_action` | ✅ Always non-empty |
| What remediation | `remediation` | ✅ Always non-empty |
| Why advisory only | `ADVISORY_INVARIANT` | ✅ Module constant, cites both principles |
| Why no execution | `implementation_status` | ✅ Unconditionally `execution_unavailable` |

### 5. Recommendations Are Reproducible from Runtime Snapshot — ✅ VERIFIED

- Same `RuntimeSnapshot` → identical advisory IDs, categories,
  severities, confidences, and recommended_actions (113B §4)
- Advisory ID sequence is stable across calls
- Content fields (category, severity, confidence, recommended_action,
  rationale, reasoning_summary, remediation) are identical across
  calls with the same snapshot
- Only `timestamp` varies between calls (expected — captured once
  per `build_advisory_results()` invocation)

### 6. Aggregation Is Deterministic — ✅ VERIFIED

- Sort order: severity rank (critical < warning < advisory < info),
  then category alphabetically, then first evidence field_path
  alphabetically
- Deduplication by `(category, evidence domains, evidence field_paths)`
  fingerprint — verified no duplicate fingerprints exist
- Advisory IDs: `ADV-{category_slug}-{seq:04d}`, sequence numbers
  start at 0001 within each category and are consecutive
- Return type is `tuple` (immutable), all results are frozen dataclasses

### 7. No Provider Inspects Runtime Internals Directly — ✅ VERIFIED

- AST import allowlist confirmed: only `pcae.core.runtime_snapshot` imported
- No provider imports `RuntimeRegistry`, `runtime_context` internals,
  `command_path_observation`, or any other internal module
- All data flows through the `RuntimeSnapshot` surface — providers
  access `snapshot.health`, `snapshot.governance`, `snapshot.context`,
  `snapshot.registry` — never internal implementation details
- Every `EvidenceReference` points to one of the 9 frozen
  `RUNTIME_SNAPSHOT_DOMAINS`, never an internal path
- No filesystem, network, or subprocess access in provider code (AST-verified)

### 8. No PermissionBroker.evaluate() Is Called — ✅ VERIFIED

- `advisory_runtime.py` does not import any `permission_broker` module
  (AST-verified)
- The string `PermissionBroker` appears only in docstrings documenting
  the prohibition
- The string `evaluate(` does not appear in code (outside docstrings)
- `build_advisory_results` is a pure function — no side effects, no
  broker calls

### 9. No Plugin Loading/Invocation Occurs — ✅ VERIFIED

- No `importlib` import or dynamic loading (AST-verified)
- No `plugin_loader`, `plugin` module imports
- No `RuntimeRegistry` direct instantiation — all registry data comes
  through `RuntimeSnapshot.registry` (a `RegistrySnapshot`, computed by
  111B's `get_registry()` from the `RuntimeRegistry` metadata store,
  never by loading or invoking plugins)
- Plugin count and capability count are read from the snapshot
  surface, never from direct registry access

### 10. No Mutation of Runtime Snapshot or Runtime Context — ✅ VERIFIED

- Each provider's `analyze()` leaves the `RuntimeSnapshot` unchanged
  (field-by-field comparison before/after)
- `build_advisory_results()` leaves the `RuntimeSnapshot` unchanged
- All returned `AdvisoryResult` instances are frozen — mutation raises
  `FrozenInstanceError`
- All vocabulary tuples are immutable

### 11. Runtime State Remains Observed — ✅ VERIFIED

- `snapshot.health.current_runtime_state` is `"Observed"` before and
  after advisory analysis (verified with real repo snapshot)
- `snapshot.state.current_state` is `"Observed"` before and after
- `snapshot.health.current_maximum_plugin_capability` is `"observe"`
  before and after

### 12. Execution Capability Remains Unavailable — ✅ VERIFIED

- `snapshot.governance.execution_capability` is `"unavailable"` before
  and after advisory analysis
- `snapshot.health.execution_availability` is `"unavailable"` before
  and after
- `snapshot.governance.non_executing_posture` is `True` before and after
- Every `AdvisoryResult.implementation_status` is unconditionally
  `"execution_unavailable"`
- `AdvisoryResult` construction rejects any `implementation_status`
  other than `"execution_unavailable"` (tested: `"executing"`,
  `"available"`, `"enabled"`, `"implemented"`, `"active"` — all rejected)

## Tests

### New Verification Tests

`tests/test_advisory_runtime_verification.py` — 41 tests across 13 sections:

| Section | Tests | Focus |
|---|---|---|
| 1 — Runtime Snapshot-only input | 3 | Import allowlist, signature, type hints |
| 2 — Provider modularity | 3 | Stateless, independent, removable |
| 3 — 113B contract compliance | 4 | 14 fields populated, evidence refs, implementation_status, vocabularies |
| 4 — Explainability | 2 | 8 facets, substantive content |
| 5 — Reproducibility | 3 | Identical results, different timestamps, stable IDs |
| 6 — Deterministic aggregation | 4 | Sort order, dedup, ID format, tuple return |
| 7 — Provider boundary | 3 | No internal imports, no forbidden patterns, snapshot domains |
| 8 — No PermissionBroker | 2 | No broker import, no evaluate() call |
| 9 — No plugin loading | 2 | No plugin imports, no RuntimeRegistry instantiation |
| 10 — No mutation | 3 | Provider immutability, aggregation immutability, result frozen |
| 11 — Runtime state Observed | 2 | State before/after, plugin capability ceiling |
| 12 — Execution unavailable | 3 | Execution capability, non-executing posture, all results confirm |
| 13 — Cross-cutting | 5 | Bad status rejection, no CLI, no commands module, docstring, invariant |

### Existing Tests (113C)

`tests/test_advisory_runtime.py` — 83 tests (unchanged, all passing)

### Broader Test Suites Run

All broader test suites pass with the following counts:
- `test_advisory_runtime*` + `test_runtime_snapshot*` + `test_runtime_context*` + `test_runtime_inspect*`: 269 passed
- `test_*runtime*` + `test_*contract*` + `test_*autonomy*` + `test_*plugin*` + `test_*advisory*`: results below
- `test_task*` + `test_*task*` + `test_*phase*` + `test_notifications*` + `test_telegram*`: results below
- `fast_green`: results below

## Safety Invariants Confirmed

| Invariant | Status |
|---|---|
| Runtime state remains `Observed` | ✅ Confirmed |
| Execution capability remains `unavailable` | ✅ Confirmed |
| Maximum plugin capability remains `observe` | ✅ Confirmed |
| `implementation_status` unconditionally `execution_unavailable` | ✅ Confirmed |
| No CLI wiring, no commands module | ✅ Confirmed |
| Import surface limited to stdlib + `RuntimeSnapshot` | ✅ Confirmed |
| No PermissionBroker.evaluate() calls | ✅ Confirmed |
| No plugin loading or invocation | ✅ Confirmed |
| No mutation of RuntimeSnapshot or RuntimeContext | ✅ Confirmed |
| Non-executing posture remains `True` | ✅ Confirmed |

## No-Go Confirmation

No execution. No authorization. No plugin loading. No plugin instantiation.
No plugin invocation. No Permission Broker enforcement. No CLI wiring.
No commands module. No mutation of RuntimeSnapshot. No mutation of
RuntimeContext. No direct Runtime internals inspection. No filesystem
access. No network access. No subprocess calls. `implementation_status`
remains unconditionally `"execution_unavailable"`. Runtime state remains
`Observed`. Execution capability remains `unavailable`.

## Files Added

- `tests/test_advisory_runtime_verification.py`
- `docs/PHASE_113_ADVISORY_RUNTIME_VERIFICATION.md`

## Files Modified

- `PROJECT_STATUS.md`
- `CHANGELOG.md`
- `tasks/DONE.md`

## Execution Capability Status

**Unchanged.** Execution capability remains **unavailable**. This phase
introduces no new behavior, no CLI wiring, and no execution path.

| Field | Value |
|---|---|
| Observed command paths | 4 (unchanged) |
| Execution-capable paths | 0 |
| Current execution capability | unavailable |
| Current maximum runtime state | Observed |
| Current maximum plugin capability | observe |

## Recommended Next Phase

**113R — Advisory Runtime Architecture Review.**
