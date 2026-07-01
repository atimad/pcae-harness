# Phase 97G — Execution Readiness Preflight Contract Freeze

## 1. Purpose

Freeze the execution readiness preflight contract introduced in Phase 97F.
Stabilize the preflight model, JSON shape, CLI behavior, digest behavior,
verification behavior, no-go semantics, authorization-flag semantics,
latest/show/verify behavior, and documentation so future phases can safely
depend on the integrated preflight artifact.

**Contract-freeze only. No execution. No enforcement.**

## 2. Scope

- 72 contract-freeze tests asserting structural stability
- Frozen schema documentation (28 top-level fields, 12 auth sub-fields)
- Frozen statuses, no-go conditions, evidence categories
- Frozen digest behavior (SHA-256, deterministic, excludes digest field)
- Frozen CLI contract (preflight/show/verify, JSON/text output)
- Frozen latest/show/verify semantics
- Compatibility rules for future evolution

## 3. Non-Goals

Same as 97F non-goals. Additionally:
- No new model fields
- No new CLI commands
- No status/semantic changes
- No contract-breaking refactors

## 4. Frozen Preflight Schema

### 4.1 Top-level fields (28)

| # | Field | Type | Default |
|---|-------|------|---------|
| 1 | `schema_version` | `str` | `"1.0"` |
| 2 | `preflight_id` | `str` | `erp-{uuid12}` |
| 3 | `phase_id` | `str` | `"97F"` |
| 4 | `task_id` | `str` | `""` |
| 5 | `generated_at_utc` | `str` | ISO timestamp |
| 6 | `readiness_status` | `str` | `"blocked"` |
| 7 | `preflight_status` | `str` | (varies) |
| 8 | `evidence_status` | `str` | (varies) |
| 9 | `backend_invocation_contract_status` | `str` | `"not_ready"` |
| 10 | `adapter_boundary_status` | `str` | `"not_ready"` |
| 11 | `approval_status` | `str` | `"approval_required"` |
| 12 | `audit_readiness_status` | `str` | `"audit_required"` |
| 13 | `rollback_readiness_status` | `str` | `"rollback_required"` |
| 14 | `artifact_verification_status` | `str` | `"failed_verification"` |
| 15 | `execution_boundary_proof_status` | `str` | `"not_ready"` |
| 16 | `no_go_conditions` | `list[str]` | `[]` |
| 17 | `missing_evidence` | `list[str]` | `[]` |
| 18 | `failed_checks` | `list[str]` | `[]` |
| 19 | `warnings` | `list[str]` | `[]` |
| 20 | `evidence_refs` | `list[str]` | `[]` |
| 21 | `approval_refs` | `list[str]` | `[]` |
| 22 | `audit_refs` | `list[str]` | `[]` |
| 23 | `rollback_refs` | `list[str]` | `[]` |
| 24 | `proof_refs` | `list[str]` | `[]` |
| 25 | `authorization_summary` | `dict` | 12 keys (see 4.2) |
| 26 | `simulation_only` | `bool` | `true` |
| 27 | `no_execution` | `bool` | `true` |
| 28 | `digest` | `str` | 64-char hex |

### 4.2 Authorization summary (12 boolean flags, all False)

| Flag | Default |
|------|---------|
| `execution_available` | `false` |
| `execution_authorized` | `false` |
| `backend_invocation_authorized` | `false` |
| `adapter_execution_authorized` | `false` |
| `network_authorized` | `false` |
| `subprocess_authorized` | `false` |
| `shell_authorized` | `false` |
| `mutation_authorized` | `false` |
| `apply_authorized` | `false` |
| `rollback_authorized` | `false` |
| `commit_authorized` | `false` |
| `push_authorized` | `false` |

**All 12 flags must remain False in the current system.** `validate()` and `verify_execution_readiness_preflight()` reject any True flag.

## 5. Frozen Statuses

### 5.1 Valid preflight statuses (10)

| Status | Meaning |
|--------|---------|
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

### 5.2 Future-only / unavailable statuses (6)

| Status | Label |
|--------|-------|
| `execution_ready` | `PREFLIGHT_EXECUTION_READY_FUTURE_ONLY` |
| `execute_now` | `PREFLIGHT_EXECUTE_NOW_FUTURE_ONLY` |
| `invoke_now` | `PREFLIGHT_INVOKE_NOW_FUTURE_ONLY` |
| `apply_now` | `PREFLIGHT_APPLY_NOW_FUTURE_ONLY` |
| `commit_now` | `PREFLIGHT_COMMIT_NOW_FUTURE_ONLY` |
| `push_now` | `PREFLIGHT_PUSH_NOW_FUTURE_ONLY` |

These are excluded from `VALID_PREFLIGHT_STATUSES`. Using any as current status
fails `validate()`.

## 6. Frozen No-Go Conditions (29)

### 6.1 97F-originated (25)

1. `missing_execution_readiness`
2. `missing_backend_invocation_contract`
3. `missing_adapter_boundary`
4. `missing_human_approval`
5. `expired_or_revoked_approval`
6. `missing_audit_readiness`
7. `missing_rollback_readiness`
8. `failed_artifact_verification`
9. `missing_execution_boundary_proof`
10. `stale_latest_pointer`
11. `unknown_schema_version`
12. `conflicting_safety_flags`
13. `forbidden_path_or_scope`
14. `secret_material_detected`
15. `network_requested`
16. `subprocess_requested`
17. `shell_requested`
18. `telegram_inbound_requested`
19. `apply_requested_without_governance`
20. `rollback_execution_requested`
21. `commit_or_push_requested`
22. `raw_git_path_detected`
23. `no_verify_attempt`
24. `force_push_attempt`
25. `bypass_permissions_detected`

### 6.2 97A passthrough (4)

26. `execution_readiness_model_not_implemented`
27. `backend_invocation_never_implemented`
28. `subprocess_mediation_never_implemented`
29. `shell_mediation_never_implemented`

Unknown no-go conditions fail `validate()`. No-go conditions cannot be overridden
by approval, audit readiness, rollback readiness, or artifact references.
No-go conditions cannot set any authorization flag True.

## 7. Frozen Evidence Categories (10)

1. `readiness_model`
2. `backend_invocation_contract`
3. `adapter_invocation_boundary`
4. `human_approval_gate`
5. `audit_readiness`
6. `rollback_readiness`
7. `artifact_verification`
8. `execution_boundary_proof`
9. `phase_finalization_context`
10. `active_task_contract`

Evidence refs are string references only — not executable specs.
Missing evidence does not become authorization.

## 8. Frozen Digest Behavior

- Algorithm: SHA-256
- Encoding: lowercase hex (64 characters)
- Payload: canonical JSON (sorted keys, sorted list values)
- Excludes: only the `digest` field itself
- Deterministic for same field values
- Changes when any of these change:
  - `preflight_status`, `readiness_status`
  - `no_go_conditions`, `missing_evidence`, `failed_checks`
  - Evidence/approval/audit/rollback/proof refs
  - Any authorization flag
  - `simulation_only`, `no_execution`
- Tampered artifact (mismatched digest) fails `verify_execution_readiness_preflight()`

## 9. Frozen CLI Contract

| Command | Behavior |
|---------|----------|
| `pcae execution-readiness preflight` | Text output with status, no-go, auth flags, digest |
| `pcae execution-readiness preflight --json` | JSON with all 28 top-level fields |
| `pcae execution-readiness preflight --save` | Writes to `.pcae/execution-readiness-preflight/` |
| `pcae execution-readiness show [--latest] [--json]` | Displays latest preflight |
| `pcae execution-readiness verify [--latest] [--json]` | Verifies latest preflight integrity |

JSON output shape: stable 28 top-level fields, 12 auth sub-fields.
Text output: includes status, no-go conditions, digest, no-execution confirmation.
All CLI paths: non-executing, non-authorizing, no subprocess beyond python/pytest.

## 10. Frozen Latest/Show/Verify Semantics

- Latest artifact: `.pcae/execution-readiness-preflight/latest.json`
- Latest cannot escape with `../` traversal
- Latest cannot be absolute external path
- Latest cannot be URL
- `show --latest` and `verify --latest` resolve the same artifact
- No artifact → `show` exits non-zero, `verify` returns `valid: false`
- Invalid JSON in artifact → `load_latest_execution_readiness_preflight()` returns `None`
- Tampered artifact (mismatched digest or unsafe flag) → verify fails

## 11. Compatibility Rules

### Accepted
- Current schema version `"1.0"`
- All valid preflight statuses
- All valid no-go conditions
- Extra unknown fields in JSON (tolerated by `from_dict`)

### Rejected (fail-closed)
- Missing `schema_version`
- Unknown future major schema (e.g., `"2.0"`)
- Any authorization flag True
- Unknown preflight status
- Unknown no-go condition
- `no_execution: false`
- `simulation_only: false`
- Contradictory safety fields

### Allowed Future Additive Changes
- New preflight statuses added to `VALID_PREFLIGHT_STATUSES`
- New no-go conditions added to `VALID_NOGO_CONDITIONS`
- New evidence categories
- New optional fields in JSON (must not alter safety/authorization semantics)
- New CLI flags (must not enable execution)

### Breaking Changes (require schema version bump)
- Removing or renaming top-level fields
- Changing digest algorithm or payload
- Changing authorization flag semantics
- Making any authorization flag True by default
- Adding `execution_ready` or any `*_now` status to valid set

## 12. Tests

72 tests in `tests/test_execution_readiness_preflight_contract.py`:

| Test class | Tests | Focus |
|---|---|---|
| `TestSchemaFieldFreeze` | 11 | All 28 top-level fields present, types stable |
| `TestStatusFreeze` | 9 | 10 valid + 6 future-only, non-authorizing |
| `TestNoGoFreeze` | 7 | 29 conditions stable, unknown rejected |
| `TestEvidenceCategoryFreeze` | 5 | 10 categories stable |
| `TestAuthorizationFlagFreeze` | 5 | 12 flags all False, validate/verify reject True |
| `TestDigestFreeze` | 11 | SHA-256, deterministic, excludes digest, tamper detection |
| `TestCLIContractFreeze` | 10 | JSON shape, text output, save/show/verify, no-artifact behavior |
| `TestLatestShowVerifyFreeze` | 6 | Latest path, show/verify agreement, tamper detection |
| `TestCompatibilityBehavior` | 6 | Schema version, unknown status, flag rejection |
| `TestNoExecutionGuard` | 5 | No execution paths in build/save/verify/CLI |

Plus 63 original 97F tests in `tests/test_execution_readiness_preflight.py` (unchanged).

Total: 135 preflight tests (63 97F + 72 97G).

## 13. Files Changed

| File | Change |
|---|---|
| `tests/test_execution_readiness_preflight_contract.py` | 72 new contract-freeze tests |
| `docs/PHASE_97_EXECUTION_READINESS_PREFLIGHT_CONTRACT_FREEZE.md` | This document |
| `PROJECT_STATUS.md` | Updated |
| `CHANGELOG.md` | Updated |
| `tasks/DONE.md` | Updated |

No changes to `src/` — the contract is frozen as-is from 97F.

## 14. No-Go Boundary Confirmation

97G did NOT implement: real backend invocation, adapter execution, subprocess
execution, shell execution, network calls, shell interception, Telegram inbound,
Telegram polling, remote shell, /run, enforcement, automatic apply, apply
execution, patch parsing, commit/push authorization, real AI backend calls,
executable artifact-only invocation paths, execution enablement flags,
execution availability toggles, cryptographic signing, remote attestation,
database-backed audit storage, shell mediation, rollback execution, file
mutation rollback, automatic restore, or git reset/checkout/revert execution.

Execution remains unavailable. All 12 authorization flags remain False.

## 15. Recommended Next Phase

**97H — Execution Readiness Preflight Artifact Trust Hardening**

97H should add artifact trust verification: proof that preflight artifacts
have not been tampered with outside the governed lifecycle, chain-of-custody
verification, and integration with the existing artifact trust verification
from Phase 96G.
