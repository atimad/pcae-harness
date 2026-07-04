# Phase 113C — Advisory Runtime Prototype (Observation-Only)

## Purpose

Implement the first observation-only Advisory Runtime using the
architecture frozen in 113A and the contracts frozen in 113B. This
phase introduces advisory reasoning only — no authorization, no
execution, no enforcement.

## Scope

- `src/pcae/core/advisory_runtime.py` — the Advisory Runtime module:
  - Four frozen vocabulary tuples (advisory categories, severity
    levels, confidence levels, advisory lifecycle stages)
  - `EvidenceReference` frozen dataclass (4 fields, 113B §3)
  - `AdvisoryResult` frozen dataclass (14 fields, 113B §1)
  - `ADVISORY_INVARIANT` module constant (113B §2)
  - `AdvisoryProvider` Protocol
  - Four initial providers: `RuntimeHealthProvider`,
    `GovernanceProvider`, `RuntimeContextProvider`,
    `RegistryProvider`
  - Aggregation pipeline: collect, normalize, deduplicate, sort,
    assign IDs
  - `build_advisory_results(snapshot)` public entry point
- `tests/test_advisory_runtime.py` — 83 tests across 13 sections
- `docs/PCAE_ADVISORY_RUNTIME_PROTOTYPE.md` — architecture doc
- `docs/PHASE_113_ADVISORY_RUNTIME_PROTOTYPE.md` — this document

No CLI wiring. No execution capability. No mutation of any existing
file outside the allowed file set.

## Implementation Summary

### 1. Advisory Runtime Module

Created `src/pcae/core/advisory_runtime.py` (approximately 1120 lines).
The module follows all existing codebase conventions:

- `from __future__ import annotations` on line 1
- All dataclasses are `frozen=True`
- Collections returned as tuples, never lists
- Module-level frozen vocabulary tuples with `#:` doc comments
- Private helpers prefixed with `_`
- Stdlib imports plus one internal import (`RuntimeSnapshot`)

**Isolation**: The module imports only `RuntimeSnapshot` from
`pcae.core.runtime_snapshot`. No direct dependency on
`permission_broker_foundation`, `runtime_registry`, `command_path_observation`,
`subprocess`, or any execution-adjacent module. Verified by AST-based
import allowlist tests.

### 2. Provider Architecture

Each provider implements the `AdvisoryProvider` Protocol — a
`typing.Protocol` requiring `analyze(self, snapshot: RuntimeSnapshot)
-> tuple[AdvisoryResult, ...]`. Providers are stateless; each `analyze()`
call is a pure function of its snapshot argument.

The four initial providers cover the RuntimeSnapshot domains that have
real, grounded backing data today:

| Provider | Domain | Results | Key invariants checked |
|---|---|---|---|
| RuntimeHealthProvider | `health` | 8 | execution_availability, runtime status, plugin/capability counts, state ceiling |
| GovernanceProvider | `governance` | 4 | non-executing posture, broker status, observation paths, execution capability |
| RuntimeContextProvider | `context` | 2–4+ | None handling, session/task/observation state |
| RegistryProvider | `registry` | 4–6 | registry status, plugin/capability counts, metadata validity |

### 3. Aggregation

Deterministic, pure-function aggregation:

1. All providers are called in fixed order; results collected
2. Shared fields (`timestamp`, `source_snapshot_reference`) set once
3. Deduplication by `(category, evidence domains, evidence field_paths)`
   fingerprint — first occurrence kept
4. Sort by severity rank, then category, then first evidence field_path
5. Stable IDs assigned: `ADV-{category_slug}-{seq:04d}`
6. Returned as immutable tuple

Timestamp is captured once per `build_advisory_results()` call — all
results in one batch share the same timestamp.

### 4. Observation-Only Guarantees

All ten safety rules (113B §7) upheld:
- No execution — module has no `eval`, `exec`, `subprocess`, `os.system`
- No authorization — never calls `PermissionBroker.evaluate()`
- No mutation — snapshot fields unchanged after any provider call
- No CLI wiring — `cli.py` does not reference `advisory_runtime`
- No commands module — `src/pcae/commands/advisory_runtime.py`
  deliberately not created
- `implementation_status` unconditionally `"execution_unavailable"`

### 5. Explainability

Every `AdvisoryResult` realizes the full 8-facet explainability contract
(113B §2): `reasoning_summary` + `rationale` cover what was observed and
why it matters; `evidence_references` with `field_path` pin each finding
to a specific RuntimeSnapshot field; `recommended_action` and
`remediation` give a human concrete next steps; `ADVISORY_INVARIANT`
restates why this is advisory only and why no execution follows.

## Files Added

- `src/pcae/core/advisory_runtime.py`
- `tests/test_advisory_runtime.py`
- `docs/PCAE_ADVISORY_RUNTIME_PROTOTYPE.md`
- `docs/PHASE_113_ADVISORY_RUNTIME_PROTOTYPE.md`
- `tasks/active/20260704-0855-phase-113c-advisory-runtime-prototype.md`

## Files Modified

- `PROJECT_STATUS.md`
- `CHANGELOG.md`
- `tasks/DONE.md`

## Deferred

- CLI/Telegram/REST/dashboard consumers — no presentation layer
- Dedicated Analysis layer between providers and aggregation — the
  five-stage pipeline (113A §2) is partially implemented
- Advisory lifecycle transitions beyond `produced` — the remaining five
  stages (`presented`, `acknowledged`, `superseded`, `resolved`,
  `dismissed`) are named but not implemented
- `advisory_contract_version` field — consistent with 112F/113B's
  decisions not to implement versioning fields during prototype phases
- Provider categories beyond the four initial ones — Plugin
  Compatibility, Configuration, Operational Readiness, and Future
  extensibility remain named but have no providers

## Safety Invariants Upheld

- Runtime state remains `Observed`
- Execution capability remains `unavailable`
- Maximum plugin capability remains `observe`
- `implementation_status` unconditionally `execution_unavailable` on
  every result
- No CLI wiring, no commands module, no argparse
- Import surface limited to stdlib + `RuntimeSnapshot`

## Test Coverage

83 tests in `tests/test_advisory_runtime.py`, organized as:

| Section | Tests | Focus |
|---|---|---|
| 1 — Module & vocabularies | 8 | Import, frozen tuples, invariant constant |
| 2 — EvidenceReference | 8 | Frozen dataclass, 4 fields, validation, immutability |
| 3 — AdvisoryResult | 13 | Frozen dataclass, 14 fields, validation, tuple-not-list |
| 4 — AdvisoryProvider | 5 | Protocol existence, 4 providers structurally match |
| 5 — RuntimeHealthProvider | 6 | Correct category, evidence domain, invariants |
| 6 — GovernanceProvider | 5 | Correct category, evidence domain, specific results |
| 7 — RuntimeContextProvider | 3 | None handling, evidence domain |
| 8 — RegistryProvider | 4 | Correct category, evidence domain, plugin count |
| 9 — Aggregation | 8 | Deterministic, sorted, deduplicated, stable IDs |
| 10 — Module isolation | 7 | AST import allowlist, no broker/shell/network |
| 11 — Observation-only | 6 | No mutation, no CLI, no argparse, no subprocess |
| 12 — Contract compliance | 5 | 14 fields, 4 evidence fields, explainability, reproducibility |
| 13 — Integration | 5 | Real snapshot, minimal snapshot, state preserved |

## Recommended Next Phase

**113D — Advisory Runtime Verification & Compatibility.**
