# PCAE Advisory Runtime Prototype

**Implemented by**: Phase 113C | **Status**: prototype, observation-only —
no advisory execution, no command authorization, no command denial, no
Permission Broker enforcement, no runtime execution, no plugin loading,
no plugin instantiation, no plugin invocation, no dependency injection,
no shell mediation, no backend invocation, no adapter invocation, no
execution enablement, no execution capability, no automatic apply, no
audit persistence, no rollback execution, no Telegram inbound, no REST
server, no web UI, no daemon, no background workers.

## Purpose

113A designed the Advisory Runtime — a five-stage pipeline (Runtime
Snapshot → Analysis → Recommendation → Advisory Result → Presentation)
and an eight-category advisory taxonomy. 113B froze the contracts — a
fourteen-field `AdvisoryResult`, a four-field `EvidenceReference`, an
eight-facet explainability contract, severity/confidence semantics, a
six-stage advisory lifecycle, and ten absolute safety rules, all before
any advisory implementation began.

This document describes the first working prototype: the concrete Python
types, the provider framework, the initial four providers, the
aggregation pipeline, and the observation-only guarantees that keep the
Advisory Runtime analytical, not operational.

## Architecture

```
                    build_advisory_results(snapshot)
                              │
                              ▼
              ┌───────────────────────────────┐
              │     Advisory Providers (4)     │
              │                               │
              │  RuntimeHealthProvider         │
              │  GovernanceProvider            │
              │  RuntimeContextProvider        │
              │  RegistryProvider              │
              │                               │
              │  Each: analyze(snapshot)       │
              │       → tuple[AdvisoryResult]  │
              └───────────────┬───────────────┘
                              │ raw results
                              ▼
              ┌───────────────────────────────┐
              │        Aggregation             │
              │                               │
              │  1. Set shared fields          │
              │  2. Deduplicate by fingerprint │
              │  3. Sort by severity/category  │
              │  4. Assign stable advisory IDs │
              └───────────────┬───────────────┘
                              │
                              ▼
                   tuple[AdvisoryResult, ...]
```

The prototype does not implement the full five-stage pipeline (Analysis,
Recommendation, and Presentation are deferred — 113C implements the
provider framework that feeds into those future stages). The providers
perform lightweight, deterministic checks directly against snapshot
fields; future phases may introduce a dedicated Analysis layer that
transforms raw provider findings into richer recommendations.

## Module Location

`src/pcae/core/advisory_runtime.py`

No CLI wiring exists. No `src/pcae/commands/advisory_runtime.py` exists.
The module is a pure library component, importable by tests and, in
future phases, by CLI/Telegram/REST/dashboard consumers.

## AdvisoryResult Model

Fourteen frozen fields, exactly matching 113B §1:

| # | Field | Type | Frozen since | Description |
|---|---|---|---|---|
| 1 | `advisory_id` | `str` | 113A/113B | Stable, never-reused identifier: `ADV-{category_slug}-{seq:04d}` |
| 2 | `category` | `str` | 113A | One of eight advisory categories (open taxonomy) |
| 3 | `severity` | `str` | 113A | One of four: `info`, `advisory`, `warning`, `critical` |
| 4 | `confidence` | `str` | 113A | One of four: `unknown`, `observed`, `validated`, `proven` |
| 5 | `recommended_action` | `str` | 113A | Free-text description of what a human might consider doing |
| 6 | `rationale` | `str` | 113A | Full explanation of why this recommendation was produced |
| 7 | `evidence_references` | `tuple[EvidenceReference, ...]` | 113A/113B | Pointers into the Runtime Snapshot fields that produced this finding |
| 8 | `affected_runtime_objects` | `tuple[str, ...]` | 113A | Identifiers of affected objects |
| 9 | `timestamp` | `str` | 113A | ISO 8601 production timestamp |
| 10 | `source_snapshot_reference` | `str` | 113B | Reference to the exact Runtime Snapshot this result derives from |
| 11 | `reasoning_summary` | `str` | 113B | Concise single-line synthesis of "what was observed and why it matters" |
| 12 | `alternative_considerations` | `tuple[str, ...]` | 113B | Alternative interpretations or actions considered and not recommended |
| 13 | `remediation` | `str` | 113B | Concrete, mechanical steps a human could take |
| 14 | `implementation_status` | `str` | 113B | Unconditionally `"execution_unavailable"` on every result |

All fields are validated at construction:
- `category` must be in `ADVISORY_CATEGORIES`
- `severity` must be in `SEVERITY_LEVELS`
- `confidence` must be in `CONFIDENCE_LEVELS`
- `implementation_status` must be exactly `"execution_unavailable"` (fail-closed)
- All required string fields must be non-empty

## EvidenceReference Model

Four fields frozen by 113B §3:

| Field | Type | Description |
|---|---|---|
| `domain` | `str` | One of nine RuntimeSnapshot domains |
| `object_id` | `str \| None` | A specific object ID, or `None` for domain-wide facts |
| `field_path` | `str` | Dot-path to the specific field (e.g. `health.runtime_status`) |
| `evidence_summary` | `str` | Short gloss of what the evidence shows |

Validated at construction: `domain` must be one of `runtime`, `registry`,
`plugins`, `capabilities`, `health`, `governance`, `state`, `version`,
`context`. `field_path` and `evidence_summary` must be non-empty.

No evidence database, no audit persistence — evidence is referenced,
never stored durably (per 113B §3 and 112F §7).

## AdvisoryProvider Protocol

```python
class AdvisoryProvider(Protocol):
    def analyze(self, snapshot: RuntimeSnapshot) -> tuple[AdvisoryResult, ...]:
        ...
```

A `typing.Protocol` for structural subtyping. Any class with an
`analyze(self, snapshot: RuntimeSnapshot) -> tuple[AdvisoryResult, ...]`
method satisfies the contract. No runtime `isinstance` enforcement —
the Protocol exists as a documentation contract and for type-checker
consumption.

Providers must:
- Consume RuntimeSnapshot only
- Never mutate the snapshot
- Never call PermissionBroker.evaluate()
- Never invoke plugins
- Never execute commands
- Never inspect Runtime internals directly

## Provider Catalog

### RuntimeHealthProvider

**Category:** `"Runtime Health"`
**Reads:** `snapshot.health` (HealthInfo — eight fields)

Produces 8 results covering:
- Execution availability (proven: `"unavailable"`)
- Runtime status (proven: `"not_implemented"`)
- Registry status (observed)
- Plugin count (observed: 0 in prototype)
- Capability count (observed: 0 in prototype)
- Metadata validity (observed: `"valid"`)
- Current runtime state (proven: `"Observed"`)
- Maximum plugin capability (proven: `"observe"`)

### GovernanceProvider

**Category:** `"Governance"`
**Reads:** `snapshot.governance` (GovernanceInfo — four fields)

Produces 4 results covering:
- Non-executing posture (proven: `True`)
- Broker implementation status (proven: `"execution_unavailable"`)
- Observed command paths (observed: currently 4)
- Execution capability (proven: `"unavailable"`)

### RuntimeContextProvider

**Category:** `"Context Consistency"`
**Reads:** `snapshot.context` (RuntimeContext | None)

Handles `None` context gracefully — produces an advisory result noting
no session state exists. When context is present, reports:
- Session idle/active status
- Active task details (one result per task)
- Observation integration status

### RegistryProvider

**Category:** `"Registry"`
**Reads:** `snapshot.registry` (RegistrySnapshot — six fields)

Produces 4–6 results covering:
- Registry status (observed)
- Registered plugin count (observed)
- Registered capability count (observed)
- Metadata validity (observed)
- Plugin IDs listing (if any exist)
- Capability IDs listing (if any exist)

## Aggregation Algorithm

1. **Collect**: iterate all providers, collect raw results
2. **Normalize**: set shared `timestamp` (captured once per batch) and
   `source_snapshot_reference` (from session context or timestamp fallback)
3. **Deduplicate**: fingerprint by `(category, evidence domains tuple,
   evidence field_paths tuple)` — keep first occurrence (deterministic
   since provider order is fixed)
4. **Sort**: by severity rank (critical=0, warning=1, advisory=2, info=3),
   then category alphabetically, then first evidence field_path
5. **Assign IDs**: `"ADV-{category_slug}-{seq:04d}"` — sequential within
   each category slug, starting at 0001
6. **Return**: immutable `tuple[AdvisoryResult, ...]`

All results in one batch share the same timestamp. Timestamp is captured
once at the top of `build_advisory_results()` — not per-provider, not
per-result.

## Frozen Vocabularies

| Constant | Count | Values |
|---|---|---|
| `ADVISORY_CATEGORIES` | 8 | Runtime Health, Governance, Context Consistency, Registry, Plugin Compatibility, Configuration, Operational Readiness, Future extensibility |
| `SEVERITY_LEVELS` | 4 | info, advisory, warning, critical |
| `CONFIDENCE_LEVELS` | 4 | unknown, observed, validated, proven |
| `ADVISORY_LIFECYCLE_STAGES` | 6 | produced, presented, acknowledged, superseded, resolved, dismissed |
| `RUNTIME_SNAPSHOT_DOMAINS` | 9 | runtime, registry, plugins, capabilities, health, governance, state, version, context |

## Explainability

Every `AdvisoryResult` carries the full 8-facet explainability contract
(113B §2), realized through specific fields:

| Explains | Realized by |
|---|---|
| What was observed | `reasoning_summary` (concise) + `rationale` (full) |
| Why it matters | `severity` + `rationale` |
| What evidence supports it | `evidence_references` |
| What Runtime Snapshot fields were used | `evidence_references.field_path` + `source_snapshot_reference` |
| What recommendation was made | `recommended_action` |
| What remediation is suggested | `remediation` |
| Why this is advisory only | `ADVISORY_INVARIANT` (module constant) |
| Why no authorization/execution follows | Same `ADVISORY_INVARIANT` |

The fixed invariant (113B §2):

> This is an advisory recommendation only. No execution or authorization
> follows automatically from it — a human decides, per "Recommendation
> precedes authorization" (113A) and "Explainability precedes trust"
> (113B).

## Safety Rules

Ten absolute safety rules frozen by 113A/113B:

1. Never executes
2. Never authorizes
3. Never mutates Runtime Context
4. Never mutates Runtime Snapshot
5. Never invokes Permission Broker
6. Never invokes shell
7. Never invokes adapters
8. Never denies
9. Never implies approval
10. Never bypasses human review or future audit

All ten are upheld by this prototype. No execution path exists anywhere
in the module. The import surface is explicitly limited to stdlib plus
`RuntimeSnapshot`, and verified by AST-based tests.

## Execution Integration Status

Unchanged from 113B — this phase adds advisory analysis capability but
no execution:

| Field | Value |
|---|---|
| Observed command paths | **4** (unchanged) |
| Behavior-changing paths | **0** |
| Authorized paths | **0** |
| Execution-capable paths | **0** |
| Current execution capability | **Execution unavailable** |
| Current maximum runtime state | **Observed** (unchanged) |
| Current maximum plugin capability | **`observe`** (unchanged) |

## Limitations

- **No CLI/Telegram/REST consumers** — the module is a pure library
  component; no presentation layer exists. Future phases (post-113D)
  will wire it to consumers.
- **Provider logic is simple and deterministic** — each provider checks
  a fixed set of fields and produces expected-value results. This is
  appropriate for a prototype; richer detection rules are a future
  concern.
- **No Analysis layer** — providers produce results directly rather than
  feeding a dedicated Analysis stage. The five-stage pipeline (113A §2)
  remains partially implemented.
- **No persistence** — advisory results are produced in memory only;
  no evidence database, no result history, no audit trail.
- **No `advisory_contract_version` field** — consistent with 112F's and
  113B's own decisions not to implement versioning fields during
  prototype phases.

## No-Go Confirmations

No advisory execution. No command authorization. No command denial. No
Permission Broker enforcement. No runtime execution. No plugin loading.
No plugin instantiation. No plugin invocation. No dependency injection.
No shell mediation. No backend invocation. No adapter invocation. No
execution enablement. No execution capability. No automatic apply. No
audit persistence. No rollback execution. No Telegram inbound. No REST
server. No web UI. No daemon. No background workers.
`implementation_status` remains unconditionally `"execution_unavailable"`
on every AdvisoryResult. Current maximum runtime state remains
`Observed`. Current maximum plugin capability remains `observe`.
`v0.1.0-rc1` remains non-executing by design. v0.2 remains the autonomy
target (Level 3, not Level 4/5).

## Recommended Next Phase

**113D — Advisory Runtime Verification & Compatibility.**
