# Phase 94Y — Real Adapter Invocation Approval Model
```
phase_name = phase_94y_real_adapter_invocation_approval_model
phase_version = 1.0 | phase_status = completed | implementation_status = completed
recommended_next_phase = 94Z — Real Adapter Invocation Plan Artifact
```

## 1. Purpose
RealAdapterInvocationApproval model binding operator decision to exact adapter, backend, request, prompt hash, preflight artifact, invocation mode, and risk level. SHA-256 digest, persistence, verification. CLI show/verify. Create deferred to 94Z.

## 2. Model
RealAdapterInvocationApproval (26 fields). Decisions: approved/rejected/expired/revoked. Hard blocks → approval_effective=False. Accepted risk cannot override.

## 3. Files
- `src/pcae/core/backend_invocations.py` — model, create/validate/persist/verify/load
- `src/pcae/commands/backend.py` — show/verify CLI
- `src/pcae/cli.py` — subparser
- `.pcae/.gitignore` — real-adapter-approvals/
- `tests/test_backend_invocations.py` — 17 tests

## 4. Tests (17)
Test94YApprovalModel (9), Test94YApprovalPersistence (2), Test94YApprovalCLI (3), Test94YNoExecution (3).

## 5. Deferred: approval-create CLI → 94Z
