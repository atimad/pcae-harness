# Phase 94T — Real Backend Adapter Preflight CLI

```
phase_name    = phase_94t_backend_real_adapter_preflight_cli
phase_version = 1.0
phase_status  = completed
implementation_status = completed
recommended_next_phase = 94U — Real Backend Adapter Preflight Artifacts
```

## 1. Purpose

Implement a safe read-only CLI for real backend adapter contract visibility and preflight classification: `pcae backend adapter list/show/preflight`. All commands are model-only and env-presence-only — never invoke backends, subprocesses, shell commands, or network calls.

## 2. Non-Goals

Real backend invocation, adapter execution, subprocess, network, shell wrappers, interception, Telegram inbound, enforcement, automatic apply, apply execution, patch parsing, file mutation

## 3. CLI Commands

### `pcae backend adapter list [--json]`
Lists all adapter contracts. Shows backend_id, backend_type, invocation_mode, supports_artifact_only, requires_secrets. JSON includes `no_real_backend_invoked: true`.

### `pcae backend adapter show --backend <id> [--json]`
Full adapter contract details with safety profile and required env key names (never values). Unknown backend → non-zero exit.

### `pcae backend adapter preflight --backend <id> [--json]`
Model-only + env-presence-only preflight. Returns BackendAdapterPreflightResult. Never prints secret values. Fail-closed on unknown backend or missing env.

## 4. Fail-Closed Behavior

- Unknown backend → non-zero exit
- Missing `--backend` → non-zero exit
- Missing required env → blocked, non-zero exit
- All safety invariants preserved

## 5. Files Changed

- `src/pcae/commands/backend.py` — 3 CLI runners
- `src/pcae/cli.py` — subparser registration
- `tests/test_backend_cli.py` — 21 tests (4 classes)

## 6. Test Coverage (21 tests)

- `Test94TAdapterListCLI` (3): text, JSON, no secrets
- `Test94TAdapterShowCLI` (6): claude, mock, unknown, JSON, missing backend, no secrets
- `Test94TAdapterPreflightCLI` (9): mock ready, claude blocked, unknown, missing backend, JSON, no secrets, env values not printed, no_execution flags
- `Test94TAdapterCLISafety` (3): no subprocess/network/Telegram

## 7. Deferred Work

| Item | Target |
|------|--------|
| Adapter-specific contract specialization | 94U |
| Adapter preflight artifacts | 94U |
| Artifact-only real invocation prototype | Future |

---
*Phase 94T implements read-only adapter CLI only. No real backend invocation was performed.*
