# Phase 97F — Execution Readiness Preflight Dry-Run

## 1. Purpose

Implement a non-executing execution readiness preflight dry-run that combines
Phase 97A–97E models into one integrated readiness assessment.

This phase produces a deterministic, evidence-only preflight result that evaluates
readiness, backend invocation contract, adapter boundary, human approval gate,
audit readiness, rollback readiness, artifact verification, and no-go conditions.

**Dry-run preflight only. No execution. No authorization.**

## 2. Scope

- Preflight model (`ExecutionReadinessPreflight`) aggregating 97A–97E evidence
- Deterministic SHA-256 digest computation
- Preflight persistence (save to `.pcae/execution-readiness-preflight/`)
- Preflight verification (digest, schema, safety invariants)
- CLI commands: `preflight`, `show`, `verify`
- 63 tests covering non-executing, non-authorizing, fail-closed, digest determinism,
  persistence, verification, and no-call guards

## 3. Non-Goals

- Real backend invocation
- Adapter execution
- Subprocess execution
- Shell execution
- Network calls
- Shell interception
- Telegram inbound
- Telegram polling
- Remote shell
- `/run`
- Enforcement
- Automatic apply
- Apply execution
- Patch parsing
- Commit authorization
- Push authorization
- Real AI backend calls
- Executable artifact-only invocation paths
- Execution enablement flags
- Execution availability toggles
- Cryptographic signing
- Remote attestation
- Database-backed audit storage
- Shell mediation
- Rollback execution
- File mutation rollback
- Automatic restore
- Git reset/checkout/revert execution

## 4. Relationship to Phases 97A–97E

### 4.1 Phase 97A — Execution Readiness Model

97A defines readiness statuses (`unavailable`, `not_ready`, `evidence_incomplete`,
`approval_required`, `blocked`, `ready_for_human_review`, `ready_for_preflight_only`)
and `get_current_execution_readiness()` which returns blocked status with no-go
conditions.

97F consumes 97A's readiness status and no-go conditions as the base for the integrated
preflight.

### 4.2 Phase 97B — Governed Backend Invocation Contract

97B defines `InvocationRequest`, `BackendDefinition`, `check_invocation_readiness()`,
and denial reasons for backend invocation.

97F consumes 97B's `get_backend_invocation_readiness()` to populate the backend
invocation contract status in the preflight.

### 4.3 Phase 97C — Adapter Invocation Boundary

97C defines `BackendAdapterContract`, `BackendAdapterPreflightResult`,
`BackendAdapterSafetyProfile`, and adapter denial reasons.

97F consumes 97C's `get_adapter_invocation_boundary()` to populate the adapter
boundary status in the preflight.

### 4.4 Phase 97D — Human Approval Gate

97D defines `ApprovalRequest`, `ApprovalDecision`, `ApprovalVerificationResult`,
`verify_approval()`, 9 approval scopes, 21 denial reasons, expiry/revocation model.

97F accepts approval gate status as optional input and evaluates expiry/revocation
conditions.

### 4.5 Phase 97E — Audit / Rollback Readiness

97E defines audit denial reasons (`AUDIT_DENIED_*`), abort/failure states, and
`get_audit_rollback_readiness()`.

97F consumes 97E's audit/rollback readiness to populate audit and rollback
statuses in the preflight.

## 5. Preflight Model

### 5.1 Core dataclass: `ExecutionReadinessPreflight`

Located in `src/pcae/core/backend_invocations.py`.

**Fields (52 total):**

| Category | Fields |
|---|---|
| Identity | `schema_version`, `preflight_id`, `phase_id`, `task_id`, `generated_at_utc` |
| Core statuses | `readiness_status`, `preflight_status`, `evidence_status` |
| Domain statuses | `backend_invocation_contract_status`, `adapter_boundary_status`, `approval_status`, `audit_readiness_status`, `rollback_readiness_status`, `artifact_verification_status`, `execution_boundary_proof_status` |
| Aggregated results | `no_go_conditions`, `missing_evidence`, `failed_checks`, `warnings` |
| Evidence references | `evidence_refs`, `approval_refs`, `audit_refs`, `rollback_refs`, `proof_refs` |
| Authorization summary | 12 boolean flags (all `False`) |
| Safety invariants | `simulation_only`, `no_execution` |
| Digest | `digest` (SHA-256) |

### 5.2 Preflight statuses

| Status | Meaning |
|---|---|
| `unavailable` | Preflight capability not available |
| `not_ready` | Not ready for preflight |
| `blocked` | Hard-blocked by no-go conditions |
| `evidence_incomplete` | Required evidence missing |
| `approval_required` | Human approval gate not satisfied |
| `audit_required` | Audit readiness not satisfied |
| `rollback_required` | Rollback readiness not satisfied |
| `failed_verification` | Artifact verification failed |
| `ready_for_human_review` | Preflight complete, awaiting human review |
| `ready_for_preflight_only` | Preflight ready (preflight only, not execution) |

**Future-only (never available, never implemented):**
- `execution_ready` — labeled future-only and unavailable
- `execute_now` — labeled future-only and unavailable
- `invoke_now` — labeled future-only and unavailable
- `apply_now` — labeled future-only and unavailable
- `commit_now` — labeled future-only and unavailable
- `push_now` — labeled future-only and unavailable

### 5.3 No-go conditions (29 total)

| Condition | Source |
|---|---|
| `missing_execution_readiness` | 97A |
| `missing_backend_invocation_contract` | 97B |
| `missing_adapter_boundary` | 97C |
| `missing_human_approval` | 97D |
| `expired_or_revoked_approval` | 97D |
| `missing_audit_readiness` | 97E |
| `missing_rollback_readiness` | 97E |
| `failed_artifact_verification` | 97F |
| `missing_execution_boundary_proof` | 97F |
| `stale_latest_pointer` | 97F |
| `unknown_schema_version` | 97F |
| `conflicting_safety_flags` | 97F |
| `forbidden_path_or_scope` | Safety |
| `secret_material_detected` | Safety |
| `network_requested` | Safety |
| `subprocess_requested` | Safety |
| `shell_requested` | Safety |
| `telegram_inbound_requested` | Safety |
| `apply_requested_without_governance` | Safety |
| `rollback_execution_requested` | Safety |
| `commit_or_push_requested` | Safety |
| `raw_git_path_detected` | Safety |
| `no_verify_attempt` | Safety |
| `force_push_attempt` | Safety |
| `bypass_permissions_detected` | Safety |
| +4 passthrough from 97A readiness model | 97A |

### 5.4 Evidence categories

10 evidence categories tracked: `readiness_model`, `backend_invocation_contract`,
`adapter_invocation_boundary`, `human_approval_gate`, `audit_readiness`,
`rollback_readiness`, `artifact_verification`, `execution_boundary_proof`,
`phase_finalization_context`, `active_task_contract`.

## 6. Digest Behavior

- SHA-256 over canonical JSON (sorted keys, deterministic formatting)
- Digest excludes only the `digest` field itself
- Digest changes when: no-go conditions, authorization flags, evidence refs,
  statuses change
- Stable across equivalent formatting (round-trip to_dict/from_dict)
- Tampered artifact fails verification

## 7. Fail-Closed Behavior

If anything required is missing or unsafe:

- `preflight_status` is `blocked`, `not_ready`, `evidence_incomplete`,
  `approval_required`, `audit_required`, `rollback_required`, or `failed_verification`
- `execution_available` remains `False`
- `execution_authorized` remains `False`
- All 10 authorization flags remain `False`
- No execution, no mutation, no backend/network/shell/subprocess calls
- Result explains missing evidence and no-go conditions

## 8. CLI

### 8.1 Commands

```
pcae execution-readiness preflight [--json] [--save] [--task-id ID]
    Run the integrated readiness preflight dry-run (Phase 97F).

pcae execution-readiness show [--latest] [--json]
    Show the latest preflight artifact.

pcae execution-readiness verify [--latest] [--json]
    Verify the latest preflight artifact integrity and safety invariants.
```

### 8.2 Artifact paths

- Latest: `.pcae/execution-readiness-preflight/latest.json`
- Timestamped: `.pcae/execution-readiness-preflight/YYYYMMDD-HHMMSS.json`

## 9. Verification Behavior

`verify_execution_readiness_preflight()` checks:

- Schema version
- Digest integrity
- Preflight status validity
- Authorization flags (all must be `False`)
- Safety invariants (`simulation_only=True`, `no_execution=True`)
- Future-only statuses not used as current
- Contradictory status detection
- No-go condition validity

Fails closed on: tampered digest, missing digest, unknown schema, invalid status,
unsafe authorization flag, missing safety flag.

## 10. No-Execution Guards

- All authorization flags default to `False`, never set to `True`
- `validate()` hard-rejects any `True` authorization flag
- `build_execution_readiness_preflight()` never calls subprocess, network, shell, or backend
- `save_execution_readiness_preflight()` uses Python filesystem APIs only
- `verify_execution_readiness_preflight()` is pure computation
- Future-only execution statuses (`execute_now`, `invoke_now`, etc.) are not valid
  preflight statuses and are explicitly excluded from `VALID_PREFLIGHT_STATUSES`

## 11. Tests

63 tests in `tests/test_execution_readiness_preflight.py`:

| Test class | Tests | Focus |
|---|---|---|
| `TestPreflightStatusConstants` | 6 | No execute/invoke/apply/commit/push statuses |
| `TestPreflightNonExecuting` | 3 | Preflight is non-executing, non-authorizing |
| `TestPreflightEvidenceAggregation` | 8 | Evidence from 97A–97E correctly aggregated |
| `TestPreflightNoGoConditions` | 4 | No-go conditions valid, deduplicated, sorted |
| `TestPreflightValidation` | 6 | Self-validation invariants |
| `TestDigestDeterminism` | 6 | Digest deterministic and sensitive to changes |
| `TestPreflightPersistence` | 4 | Save/load roundtrip, latest.json, timestamped |
| `TestPreflightVerification` | 5 | Verify integrity, tamper detection, no-execution |
| `TestNoCallGuards` | 5 | No subprocess/network/shell calls |
| `TestAuthorizationFlags` | 4 | All auth flags always False |
| `TestFailClosedBehavior` | 8 | Missing evidence → blocked |
| `TestSchemaVersion` | 3 | Schema version validation |

## 12. Files Changed

| File | Change |
|---|---|
| `src/pcae/core/backend_invocations.py` | Added `ExecutionReadinessPreflight` dataclass, `build_execution_readiness_preflight()`, `save_execution_readiness_preflight()`, `load_latest_execution_readiness_preflight()`, `verify_execution_readiness_preflight()`, constants (~500 lines) |
| `src/pcae/commands/agent.py` | Added `run_execution_readiness_preflight()`, `run_execution_readiness_preflight_show()`, `run_execution_readiness_preflight_verify()` (~190 lines) |
| `src/pcae/cli.py` | Added preflight/show/verify subcommands under `execution-readiness`, updated imports (~60 lines) |
| `tests/test_execution_readiness_preflight.py` | 63 new tests (~700 lines) |
| `docs/PHASE_97_EXECUTION_READINESS_PREFLIGHT_DRY_RUN.md` | This document |

## 13. No-Go Boundary Confirmation

97F did NOT implement:

- Real backend invocation ✗
- Adapter execution ✗
- Subprocess execution ✗
- Shell execution ✗
- Network calls ✗
- Shell interception ✗
- Telegram inbound ✗
- Telegram polling ✗
- Remote shell ✗
- `/run` ✗
- Enforcement ✗
- Automatic apply ✗
- Apply execution ✗
- Patch parsing ✗
- Commit authorization ✗
- Push authorization ✗
- Real AI backend calls ✗
- Executable artifact-only invocation paths ✗
- Execution enablement flags ✗
- Execution availability toggles ✗
- Cryptographic signing ✗
- Remote attestation ✗
- Database-backed audit storage ✗
- Shell mediation ✗
- Rollback execution ✗
- File mutation rollback ✗
- Automatic restore ✗
- Git reset/checkout/revert execution ✗

## 14. Residual Risks

1. **Preflight status is always blocked/failed_verification** — the preflight
   correctly reflects that execution prerequisites are incomplete. This is not a bug;
   it is the correct fail-closed behavior.
2. **97D approval gate is not auto-detected** — the preflight accepts approval data
   as a parameter but does not auto-detect whether a human approval gate exists.
   Future phases (97G) should add auto-detection.
3. **No execution boundary proof exists** — the `execution_boundary_proof` is always
   `not_ready`. This is correct for the preflight-only implementation. Future phases
   should define the boundary proof model.

## 15. Recommended Next Phase

**97G — Execution Readiness Preflight Contract Freeze**

97G should:
1. Freeze the 97F preflight artifact contract (schema, statuses, digest rules).
2. Add auto-detection of 97A–97E evidence from filesystem/pcae state.
3. Add interactive preflight with approval gate integration.
4. Define the execution boundary proof model.
5. Run full governance regression suite.
