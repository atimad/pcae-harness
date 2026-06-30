# Phase 95L — Artifact-Only Invocation Command Boundary CLI Dry-Run

```
phase_name = phase_95l_cli_dry_run
phase_status = completed | implementation_status = completed
recommended_next_phase = 95M — Artifact-Only Invocation Dry-Run Evidence Chain Fixtures
```

## 1. Purpose

Exposed the 95K command boundary model through a read-only/dry-run CLI. Load boundary artifacts, validate, print assessment, optionally persist. Execute remains unavailable.

## 2. CLI Commands

```
pcae backend invoke artifact-only dry-run --boundary <path> [--save] [--json]
pcae backend invoke artifact-only show --latest [--json]
pcae backend invoke artifact-only verify --latest [--json]
```

### Dry-run behavior
- Loads boundary from explicit path only
- Validates schema/digest
- Calls validate_artifact_only_invocation_command_boundary()
- Prints decision, hard blocks, warnings, no-execution flags
- Optionally persists assessment with --save
- Never executes, never spawns subprocess, never calls network

### Show/Verify
- Show: prints latest assessment
- Verify: validates assessment digest integrity

### Execute unavailable
`pcae backend invoke artifact-only execute` is not a recognized subcommand. Returns error.

## 3. Output

Text output includes all no-execution flags: Execution allowed, Execute supported, Dry-run only, Real backend, Adapter executed, Subprocess, Network, Repo mutation, Apply, Patch parsing, Commit/push auth, Telegram inbound.

## 4. Tests (20)

| Class | Tests |
|-------|-------|
| Test95LInvokeArtifactOnlyDryRun | 16 (dry-run, save, show, verify, safety) |
| Test95LInvokeArtifactOnlySafety | 4 (no backend/shell/network/PATH) |

## 5. Files Changed

- `src/pcae/commands/backend.py` — 3 CLI runner functions + helpers
- `src/pcae/cli.py` — Subparser registration under `backend invoke artifact-only`
- `tests/test_backend_cli.py` — 20 CLI tests
- `tests/test_backend_invocations.py` — 1 test fix (telegram_inbound scope)
- `docs/PHASE_95_ARTIFACT_ONLY_INVOCATION_COMMAND_BOUNDARY_CLI_DRY_RUN.md` — this doc

## 6. No-Go

No real backend invocation. No adapter execution. No subprocess. No network. No execute path. No PATH lookup. No command auto-discovery. No Telegram inbound. 95M not started.

## 7. Next

**95M — Artifact-Only Invocation Dry-Run Evidence Chain Fixtures**
