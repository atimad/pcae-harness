# Phase 98A — First Governed Execution Preflight Prototype

## 1. Purpose

Prototype the first governed execution preflight workflow using the completed
Phase 96 connected automation chain and the completed Phase 97 execution-readiness
preflight layer. Produces a non-executing preflight decision artifact that
consumes Phase 97 preflight evidence, checks prerequisites, and fails closed.

**Prototype only. No execution. No enforcement.**

## 2. Scope

- `GovernedExecutionPreflightPrototype` dataclass consuming 97F preflight
- 9 prototype statuses, 8 prototype decisions (8 future-only unavailable)
- SHA-256 digest, deterministic
- CLI: `pcae governed-execution preflight/show/verify`
- 25 tests covering non-executing, non-authorizing, source handling, digest, persistence, CLI

## 3. Non-Goals

Same as 97F–97J non-goals. Additionally: no real execution workflow, no
multi-step orchestration, no backend/adapter integration.

## 4. Prototype Model

### 4.1 `GovernedExecutionPreflightPrototype`

Located in `src/pcae/core/backend_invocations.py`.

**Key fields (34 in to_dict()):**
- Identity: schema_version, prototype_id, phase_id, task_id, generated_at_utc
- Source preflight reference (7 fields)
- Prerequisite summaries (8 fields)
- Prototype decision (8 fields)
- Authorization summary (12 flags, all False)
- Safety invariants: simulation_only, no_execution, evidence_only, non_authorizing
- Digest (SHA-256)

### 4.2 Statuses (9)

`unavailable`, `blocked`, `evidence_incomplete`, `approval_required`,
`audit_required`, `rollback_required`, `verification_failed`,
`ready_for_preflight_review`, `preflight_only`

### 4.3 Decisions (8 valid + 8 future-only)

Valid: `deny`, `block`, `require_evidence`, `require_approval`,
`require_audit_readiness`, `require_rollback_readiness`,
`require_verification`, `ready_for_review_only`

Future-only/unavailable: `execute`, `run`, `invoke`, `apply`, `commit`,
`push`, `execution_ready`, `invocation_authorized`

## 5. Fail-Closed Behavior

| Source preflight state | Prototype result |
|---|---|
| Missing | `unavailable` / `block` |
| Invalid (validation issues) | `blocked` / `block` |
| Has no-go conditions | `blocked` / `block` |
| Authorization flag True | `blocked` / `block` |
| no_execution=False | `blocked` / `block` |
| Missing evidence | `evidence_incomplete` / `require_evidence` |
| Approval required | `approval_required` / `require_approval` |
| Audit required | `audit_required` / `require_audit_readiness` |
| All prereqs met | `ready_for_preflight_review` / `ready_for_review_only` |

All 12 authorization flags remain False. Execution remains unavailable.

## 6. CLI

```
pcae governed-execution preflight [--json] [--save] [--task-id ID]
pcae governed-execution show [--latest] [--json]
pcae governed-execution verify [--latest] [--json]
```

## 7. Tests

25 tests in `tests/test_governed_execution_preflight_prototype.py`:
- Non-executing/non-authorizing (4)
- Source preflight handling (6)
- Digest behavior (4)
- Persistence and verification (4)
- CLI contract (3)
- No-execution guard (4)

## 8. Recommended Next Phase

**98B — Governed Execution Preflight Contract Freeze**
