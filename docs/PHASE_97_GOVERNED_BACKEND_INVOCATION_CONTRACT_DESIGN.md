# Phase 97B — Governed Backend Invocation Contract Design

```
phase_name = phase_97b_invocation_contract | phase_status = completed | implementation_status = design_only
recommended_next_phase = 97C — Adapter Invocation Boundary Design
```

## 1. Purpose

Design the governed backend invocation contract. Define how PCAE describes, validates, approves, audits, and constrains backend invocation requests without implementing real backend invocation. Contract/design only.

## 2. Invocation Roles

| Role | Type | Authorizes |
|------|------|------------|
| Backend provider identity | Evidence | Nothing |
| Adapter identity | Evidence | Nothing |
| Invocation request | Contract | Nothing |
| Invocation preflight | Assessment | Nothing |
| Human approval | Authorization | Required before invocation |
| Audit record | Evidence | Nothing |
| Rollback plan | Evidence | Nothing |
| Output capture | Evidence | Nothing |

## 3. Invocation Request Schema (Design)

Key invariants: `execution_requested: false`, `execution_authorized: false`, `mutation_allowed: false`, `network_allowed: false`, `shell_allowed: false`, `apply_allowed: false`, `commit_allowed: false`, `push_allowed: false`, `simulation_only: true`, `no_execution: true`.

## 4. Preflight Schema (Design)

Preflight assesses readiness without executing. All authorization flags default to `False`. No "run now" status exists.

## 5. Denial Statuses

denied_missing_readiness, denied_missing_approval, denied_invalid_backend_identity, denied_invalid_adapter_identity, denied_scope_violation, denied_artifact_verification_failed, denied_no_rollback, denied_no_audit, denied_execution_unavailable, denied_bypass_permissions, denied_unknown_schema, denied_conflicting_flags.

## 6. Fail-Closed

No backend call, no adapter call, no subprocess, no network, no shell, no apply, no commit/push. Write non-authorizing denial evidence only.

## 7. Backend/Adapter Identity Requirements

Identity is evidence, not authorization. Secret/token values never persisted. Identity mismatch fails closed. Current phase does not inspect or call real credentials.

## 8. Output Capture Contract

Raw output quarantined, redacted. No automatic apply, no patch parsing, no mutation from output. Output is evidence until reviewed.

## 9. Approval Requirements

Active task, readiness artifact, verified chain, human approval, explicit operation class approval, backend/adapter identity approval, prompt/output handling approval, rollback/audit confirmation. Approval for invocation ≠ approval for apply/commit/push/shell/Telegram.

## 10. No-Go Criteria (25+)

Readiness unavailable/blocked, missing approval/task/evidence/audit/rollback, identity mismatch, scope violation, tampered artifact, stale pointer, conflicting flags, bypass detected, shell/network/subprocess requested, apply/patch/commit/push requested, Telegram inbound, unknown schema, secrets in artifacts.

## 11. Next: 97C — Adapter Invocation Boundary Design. No execution.
