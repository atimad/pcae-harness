# Phase 96F — Connected Automation Contract Freeze

```
phase_name = phase_96f_contract_freeze | phase_status = completed | implementation_status = contract_freeze
recommended_next_phase = 96G — Connected Automation Artifact Trust / Verification Hardening
```

## 1. Purpose

Freezes the connected automation contract built through 96D and hardened in 96E. Defines exact schema versions, required fields, safety invariants, compatibility rules, and CLI output shapes. All future phases must respect this contract.

## 2. Connected Chain Artifacts

| # | Artifact | Schema Version | Path | Status |
|---|----------|---------------|------|--------|
| 1 | Runtime evidence | _RUNTIME_EVIDENCE_SCHEMA_VERSION (1.0) | .pcae/claude-runtime-evidence/ | Frozen |
| 2 | Broker/shell-gate decision | Dry-run only | Model-level | Frozen |
| 3 | Command boundary | _BOUNDARY_SCHEMA_VERSION (1.0) | .pcae/artifact-only-invocation-boundaries/ | Frozen |
| 4 | Evidence-chain bundle | _BUNDLE_SCHEMA_VERSION (1.0) | .pcae/evidence-chain-bundles/ | Frozen |
| 5 | Orchestration plan | _ORCH_SCHEMA_VERSION (1.0) | .pcae/orchestration-plans/ | Frozen |
| 6 | Execution-adjacent plan | _EA_SCHEMA_VERSION (1.0) | .pcae/execution-adjacent-plans/ | Frozen |
| 7 | Execution-adjacent assessment | _EA_SCHEMA_VERSION (1.0) | .pcae/execution-adjacent-plans/assessments/ | Frozen |
| 8 | Demo report | Deterministic JSON | CLI output | Frozen |
| 9 | Phase report | 92A schema (1.0) | .pcae/phase-reports/ | Existing |

## 3. Frozen JSON Contract (Connected Demo Output)

Required top-level fields: `connected_chain`, `execution_adjacent_plan_id`, `execution_adjacent_assessment_id`, `readiness_decision`, `ready`, `hard_blocks`, `warnings`, `missing_fields`, `failure_classifications`, `verification_status`, `saved_assessment_path`, `latest_pointer_status`.

Required capability flags (all must be `false`): `dry_run_only`, `execution_allowed`, `subprocess_allowed`, `shell_allowed`, `network_allowed`, `backend_invocation_allowed`, `adapter_execution_allowed`, `auto_apply_allowed`, `patch_parsing_allowed`, `commit_push_authorization_allowed`, `telegram_inbound_allowed`, `live_runtime_inspection_allowed`, `command_discovery_allowed`.

Connected chain references: `runtime_evidence_id`, `runtime_evidence_digest`, `broker_decision_id`, `broker_decision`, `shell_gate_decision_id`, `shell_gate_decision`, `command_boundary_id`, `command_boundary_assessment_id`, `command_boundary_decision`, `evidence_chain_bundle_id`, `evidence_chain_bundle_assessment_id`, `evidence_chain_bundle_decision`, `orchestration_id`, `orchestration_assessment_id`, `orchestration_decision`.

## 4. Frozen Safety Invariants (Contract Requirements)

| Invariant | Required Value | Enforcement |
|-----------|---------------|-------------|
| `execution_allowed` | `False` | Hard-block |
| `subprocess_allowed` | `False` | Hard-block |
| `shell_allowed` | `False` | Hard-block |
| `network_allowed` | `False` | Hard-block |
| `backend_invocation_allowed` | `False` | Hard-block |
| `adapter_execution_allowed` | `False` | Hard-block |
| `auto_apply_allowed` | `False` | Hard-block |
| `patch_parsing_allowed` | `False` | Hard-block |
| `commit_push_authorization_allowed` | `False` | Hard-block |
| `telegram_inbound_allowed` | `False` | Hard-block |
| `live_runtime_inspection_allowed` | `False` | Hard-block |
| `command_discovery_allowed` | `False` | Hard-block |
| `dry_run_only` | `True` | Hard-block |

## 5. Compatibility Rules

- Current schema versions are accepted as-is
- Missing `schema_version` fails clearly if present in artifact contract
- Unknown future major version fails clearly (if version parsing exists)
- Unknown extra fields are tolerated unless they enable execution
- Missing required safety fields fail clearly
- Contradictory safety fields fail clearly
- Artifact with any execution-enabling field set to `true` fails verification
- `execution_available = true` is permanently rejected

## 6. Latest/Show/Verify Contract

- `show --latest` reads the latest assessment artifact only
- `verify --latest` verifies the same artifact
- Explicit `--file` never silently falls back to latest
- Stale or missing latest fails clearly
- Path traversal paths are rejected
- Artifact-type mismatch fails clearly
- Tampered artifact fails verification
- Latest update order is deterministic by timestamp

## 7. CLI Contract

```
pcae backend invoke artifact-only execution-adjacent dry-run --plan <path> [--save] [--json]
pcae backend invoke artifact-only execution-adjacent show --latest [--json]
pcae backend invoke artifact-only execution-adjacent verify --latest [--json]
pcae backend invoke artifact-only execution-adjacent demo [--save] [--json]
```

- All commands are read-only (dry-run)
- `execute` is not a recognized subcommand
- Exit code 0 = assessment valid, exit code ≠ 0 = error/hard-block
- JSON output shape is stable
- Text output includes all required safety fields
- `--save` persists assessment deterministically

## 8. Commit Attribution Contract

- Phase reports list phase-owned commits only
- Recent commits are labeled separately if shown
- Prior-phase commits are not attributed to current phase
- `origin/main..HEAD` count matches actual unpushed count

## 9. No-Execution Guarantee

- No subprocess, shell, network, backend invocation, adapter execution
- No Telegram inbound, remote shell, /run
- No enforcement, automatic apply, patch parsing
- No commit/push authorization
- Execute path remains unavailable
- No execution enablement toggles

## 10. Files Changed

- docs/PHASE_96_CONNECTED_AUTOMATION_CONTRACT_FREEZE.md (this document)
- tests/test_backend_cli.py (contract freeze structural tests)
- PROJECT_STATUS.md, CHANGELOG.md, tasks/DONE.md

## 11. Next Phase

**96G — Connected Automation Artifact Trust / Verification Hardening**
