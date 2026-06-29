# Phase 95D — Claude Runtime Evidence Import CLI
```
phase_name = phase_95d_claude_runtime_evidence_import_cli
phase_version = 1.0 | phase_status = completed | implementation_status = completed
recommended_next_phase = 95E — Runtime Evidence to Dry-Run Integration
```

## 1. Purpose
`pcae backend adapter runtime-evidence import --from-json <path>` — explicit JSON-only import. Secret scanning rejects tokens/API keys/passwords. Fail-closed validation. Persists with digest. Show/verify preserved. No live detection.

## 2. Files
backend_invocations.py, backend.py, cli.py, tests, docs, PROJECT_STATUS, CHANGELOG, tasks/DONE

## 3. Tests (10)
Test95DImport (7), Test95DImportCLI (3). 550 model total.
