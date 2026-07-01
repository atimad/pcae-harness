# Phase 99B — Governed Execution Attempt Contract Freeze

## 1. Purpose

Freeze the governed execution attempt boundary contract introduced in Phase 99A.
Stabilize the `GovernedExecutionAttemptBoundary` model, artifact schema, attempt
states, denial reasons, hard no-go semantics, prerequisite semantics,
deny/abort/fail-closed behavior, digest behavior, and non-authorization
guarantees so future phases can safely depend on the attempt-boundary vocabulary
and artifact.

**Contract-freeze only. No execution. No enforcement.**

## 2. Scope

- Freeze the `GovernedExecutionAttemptBoundary` dataclass artifact schema
- Freeze the 14 valid attempt states
- Freeze the 26 denial reasons
- Freeze hard no-go semantics
- Freeze prerequisite semantics
- Freeze denial/abort/fail-closed semantics
- Freeze the 12 authorization flags (all False)
- Freeze digest behavior (SHA-256, deterministic)
- Document compatibility rules and allowed future changes
- Add contract-freeze tests

## 3. Non-Goals

99B does **not** add, enable, or authorize:

- real backend invocation
- adapter execution
- subprocess execution
- shell execution
- network calls
- shell interception
- Telegram inbound / Telegram polling
- remote shell
- /run
- enforcement / automatic apply / apply execution
- patch parsing
- commit authorization / push authorization
- real AI backend calls
- executable artifact-only invocation paths
- execution enablement flags / execution availability toggles
- cryptographic signing / remote attestation
- database-backed audit storage
- shell mediation
- rollback execution / file mutation rollback / automatic restore
- git reset/checkout/revert execution

Telegram remains outbound-only. Execution remains unavailable.
All authorization flags must remain False.

## 4. Relationship to Prior Phases

### Phase 97 — Execution Readiness Preflight
Delivers a non-executing execution-readiness preflight layer aggregating
readiness, backend contract, adapter boundary, human approval gate,
audit/rollback readiness, artifact verification, and no-go conditions into one
evidence-only, tamper-detectable assessment. The 99B attempt boundary consumes
Phase 97 preflight evidence via `phase97_preflight_ref` and
`phase97_preflight_digest`.

### Phase 98 — Governed Execution Preflight
Delivers a non-executing governed execution preflight prototype (34 JSON fields,
9 statuses, 8+8 decisions, SHA-256 digest) that consumes Phase 97 preflight
evidence and performs governed-execution-level checks. The 99B attempt boundary
consumes Phase 98 preflight evidence via `phase98_preflight_ref` and
`phase98_preflight_digest`.

### Phase 99A — Governed Execution Attempt Boundary Design
Design-only phase that introduced the `GovernedExecutionAttemptBoundary`
dataclass with 14 attempt states, 26 denial reasons, hard no-go model,
prerequisite model, and denial/abort/fail-closed semantics. 99B freezes
the 99A contract without altering its semantics.

## 5. Frozen Attempt Boundary Model Overview

`GovernedExecutionAttemptBoundary` — design-only, non-executing, non-authorizing,
evidence-only dataclass. Defines the boundary vocabulary and evidence
expectations for a future governed execution attempt. **No execution boundary
exists in the current system.**

Location: `src/pcae/core/backend_invocations.py`

## 6. Frozen Artifact Schema — 33 top-level JSON fields

| # | Field | Type | Required | Notes |
|---|-------|------|----------|-------|
| 1 | `schema_version` | `str` | yes | Frozen at `"1.0"` |
| 2 | `attempt_boundary_id` | `str` | yes | Empty by default |
| 3 | `phase_id` | `str` | yes | `"99A"` by default |
| 4 | `task_id` | `str` | yes | Empty by default |
| 5 | `generated_at_utc` | `str` | yes | Empty by default |
| 6 | `attempt_state` | `str` | yes | One of 14 valid states |
| 7 | `attempt_decision` | `str` | yes | `"denied"` by default |
| 8 | `phase97_preflight_ref` | `str` | yes | Reference to Phase 97 preflight artifact |
| 9 | `phase97_preflight_digest` | `str` | yes | SHA-256 digest of Phase 97 preflight |
| 10 | `phase98_preflight_ref` | `str` | yes | Reference to Phase 98 preflight artifact |
| 11 | `phase98_preflight_digest` | `str` | yes | SHA-256 digest of Phase 98 preflight |
| 12 | `approval_ref` | `str` | yes | Reference to human approval artifact |
| 13 | `audit_readiness_ref` | `str` | yes | Reference to audit readiness artifact |
| 14 | `rollback_readiness_ref` | `str` | yes | Reference to rollback readiness artifact |
| 15 | `backend_contract_ref` | `str` | yes | Reference to backend invocation contract |
| 16 | `adapter_boundary_ref` | `str` | yes | Reference to adapter boundary artifact |
| 17 | `artifact_verification_ref` | `str` | yes | Reference to artifact verification |
| 18 | `no_go_review_ref` | `str` | yes | Reference to no-go review |
| 19 | `execution_boundary_proof_ref` | `str` | yes | Reference to execution boundary proof |
| 20 | `hard_no_go_conditions` | `list[str]` | yes | Non-overridable blocking conditions |
| 21 | `missing_prerequisites` | `list[str]` | yes | Missing prerequisite evidence |
| 22 | `failed_checks` | `list[str]` | yes | Failed verification checks |
| 23 | `denial_reasons` | `list[str]` | yes | Reasons for denial (from 26 valid) |
| 24 | `abort_reasons` | `list[str]` | yes | Reasons for abort |
| 25 | `evidence_refs` | `list[str]` | yes | Accumulated evidence references |
| 26 | `warnings` | `list[str]` | yes | Advisory warnings |
| 27 | `authorization_summary` | `dict` | yes | 12 authorization flags (all False) |
| 28 | `simulation_only` | `bool` | yes | Must be `true` |
| 29 | `no_execution` | `bool` | yes | Must be `true` |
| 30 | `evidence_only` | `bool` | yes | Must be `true` |
| 31 | `non_authorizing` | `bool` | yes | Must be `true` |
| 32 | `design_only` | `bool` | yes | Must be `true` |
| 33 | `digest` | `str` | yes | SHA-256 hex digest |

All 33 fields are required in the `to_dict()` output.

## 7. Frozen Attempt States — 14 valid

| # | State | Meaning |
|---|-------|---------|
| 1 | `unavailable` | Attempt concept not available |
| 2 | `not_requested` | No attempt has been requested |
| 3 | `request_drafted` | Attempt request drafted, not yet preflighted |
| 4 | `preflight_required` | Preflight evidence required before consideration |
| 5 | `preflight_failed` | Preflight evidence failed verification |
| 6 | `approval_required` | Human approval required |
| 7 | `audit_required` | Audit readiness required |
| 8 | `rollback_required` | Rollback readiness required |
| 9 | `denied` | Attempt denied (no-go, missing evidence, unsafe) |
| 10 | `aborted_before_execution` | Aborted before any execution boundary |
| 11 | `blocked_by_no_go` | Hard-blocked by no-go conditions |
| 12 | `blocked_by_missing_evidence` | Hard-blocked by missing prerequisites |
| 13 | `blocked_by_failed_verification` | Hard-blocked by failed verification |
| 14 | `ready_for_design_review_only` | Design review ready, not execution ready |

### Future-only states — 9 (never available)

| State | Meaning |
|-------|---------|
| `executing` | Future: actively executing |
| `executed` | Future: execution completed |
| `running` | Future: runtime is running |
| `invoked` | Future: backend/adapter invoked |
| `applied` | Future: changes applied |
| `committed` | Future: changes committed |
| `pushed` | Future: changes pushed |
| `success` | Future: execution succeeded |
| `execution_complete` | Future: execution lifecycle complete |

Future-only states are in `UNAVAILABLE_GEA_STATES` and cause `validate()` to
report `"future-only"`. They are excluded from `VALID_GEA_STATES`.

## 8. Frozen Denial Reasons — 26

| # | Reason | Meaning |
|---|--------|---------|
| 1 | `denied_missing_phase97_preflight` | Phase 97 preflight missing |
| 2 | `denied_invalid_phase97_preflight` | Phase 97 preflight invalid/tampered |
| 3 | `denied_missing_phase98_preflight` | Phase 98 governed preflight missing |
| 4 | `denied_invalid_phase98_preflight` | Phase 98 governed preflight invalid/tampered |
| 5 | `denied_no_go_present` | Hard no-go conditions present |
| 6 | `denied_missing_human_approval` | Human approval missing |
| 7 | `denied_approval_expired` | Human approval expired |
| 8 | `denied_approval_revoked` | Human approval revoked |
| 9 | `denied_missing_audit_readiness` | Audit readiness missing |
| 10 | `denied_missing_rollback_readiness` | Rollback readiness missing |
| 11 | `denied_failed_artifact_verification` | Artifact verification failed |
| 12 | `denied_failed_reference_validation` | Reference validation failed |
| 13 | `denied_unknown_schema` | Unknown schema version |
| 14 | `denied_conflicting_safety_flags` | Conflicting safety flags |
| 15 | `denied_unsafe_authorization_flag` | Unsafe authorization flag set |
| 16 | `denied_requested_backend_invocation` | Backend invocation requested |
| 17 | `denied_requested_adapter_execution` | Adapter execution requested |
| 18 | `denied_requested_subprocess` | Subprocess execution requested |
| 19 | `denied_requested_shell` | Shell execution requested |
| 20 | `denied_requested_network` | Network access requested |
| 21 | `denied_requested_telegram_inbound` | Telegram inbound requested |
| 22 | `denied_requested_apply` | Apply execution requested |
| 23 | `denied_requested_rollback_execution` | Rollback execution requested |
| 24 | `denied_requested_commit_push` | Commit/push execution requested |
| 25 | `denied_bypass_permissions` | Bypass permissions detected |
| 26 | `denied_secret_material_detected` | Secret material detected |

All denial reasons are non-authorizing. Denial reasons cannot be overridden by
approval refs, audit/rollback refs, or Phase 97/98 preflight refs. Denial
reasons do not set any authorization flag true. Denial reason changes affect
the digest.

## 9. Frozen Hard No-Go Semantics

Hard no-go conditions are non-overridable blocking conditions that always result
in denial or blocking:

- Hard no-go conditions cannot be overridden by approval
- Hard no-go conditions cannot be overridden by audit readiness
- Hard no-go conditions cannot be overridden by rollback readiness
- Hard no-go conditions cannot be overridden by Phase 97 preflight
- Hard no-go conditions cannot be overridden by Phase 98 governed-execution preflight
- Hard no-go conditions keep all authorization flags False
- Hard no-go conditions are visible in `hard_no_go_conditions` field
- Hard no-go condition changes affect the digest
- Unknown/unsafe hard no-go behavior is fail-closed

## 10. Frozen Prerequisite Semantics

Missing or invalid prerequisites result in denial or blocking:

- Missing Phase 97 preflight → denies/blocks
- Invalid/tampered Phase 97 preflight → denies/blocks
- Missing Phase 98 governed-execution preflight → denies/blocks
- Invalid/tampered Phase 98 governed-execution preflight → denies/blocks
- Missing approval → denies/blocks
- Missing audit readiness → denies/blocks
- Missing rollback readiness → denies/blocks
- Missing artifact verification → denies/blocks
- Missing execution-boundary proof → denies/blocks
- Missing prerequisites remain evidence, not authorization
- Prerequisite refs cannot imply execution availability
- Missing prerequisites are visible in `missing_prerequisites` field

## 11. Frozen Denial/Abort/Fail-Closed Semantics

- **Denial**: No crossing into execution-capable boundary. Denial artifacts are
  evidence-only and non-authorizing.
- **Abort before execution**: No backend/adapter/shell/network/subprocess path.
  Abort artifacts are evidence-only and non-authorizing.
- **Failed verification**: Always fail-closed — no execution path.
- **Missing evidence**: Always fail-closed — no execution path.
- **Contradictory safety flags**: Always fail-closed — no execution path.
- **Unsafe authorization flag**: Always fail-closed — no execution path.
- Fail-closed path is non-executing and non-authorizing.

## 12. Frozen Authorization Flags — 12 (all False)

| # | Flag | Default | Meaning |
|---|------|---------|---------|
| 1 | `execution_available` | `false` | Execution availability |
| 2 | `execution_authorized` | `false` | Execution authorization |
| 3 | `backend_invocation_authorized` | `false` | Backend invocation |
| 4 | `adapter_execution_authorized` | `false` | Adapter execution |
| 5 | `network_authorized` | `false` | Network access |
| 6 | `subprocess_authorized` | `false` | Subprocess execution |
| 7 | `shell_authorized` | `false` | Shell execution |
| 8 | `mutation_authorized` | `false` | File mutation |
| 9 | `apply_authorized` | `false` | Apply execution |
| 10 | `rollback_authorized` | `false` | Rollback execution |
| 11 | `commit_authorized` | `false` | Commit authorization |
| 12 | `push_authorized` | `false` | Push authorization |

All 12 flags are `false` by default. `validate()` rejects any flag set to
`true` for `execution_available`, `execution_authorized`, and `push_authorized`.
Digest changes if any authorization flag changes.

## 13. Frozen Safety Flags — 5 (all True)

| Flag | Default | Meaning |
|------|---------|---------|
| `simulation_only` | `true` | Artifact is simulation only |
| `no_execution` | `true` | No execution is possible |
| `evidence_only` | `true` | Artifact is evidence only |
| `non_authorizing` | `true` | Artifact grants no authorization |
| `design_only` | `true` | Artifact is design only |

All 5 safety flags are `true` by default. `validate()` rejects
`simulation_only`, `no_execution`, or `design_only` set to `false`.

## 14. Frozen Digest Behavior

- Algorithm: **SHA-256**
- Output: 64-character hex string
- Deterministic: same inputs → same digest
- Excludes: only the `digest` field itself from the payload
- Canonical JSON: `sort_keys=True`, `indent=2`, `ensure_ascii=False`
- Digest changes when any of the following change:
  - `attempt_state`
  - `attempt_decision`
  - `hard_no_go_conditions`
  - `missing_prerequisites`
  - `failed_checks`
  - `denial_reasons`
  - `abort_reasons`
  - `evidence_refs`
  - `warnings`
  - Phase 97/98 preflight refs or digests
  - Any authorization flag
  - Any safety flag (`simulation_only`, `no_execution`, `evidence_only`, `non_authorizing`, `design_only`)
- Digest is stable across equivalent formatting
- Tampered artifact fails verification (digest mismatch)

### Digest payload fields included

The digest computation includes: `schema_version`, `attempt_boundary_id`,
`phase_id`, `task_id`, `generated_at_utc`, `attempt_state`, `attempt_decision`,
`phase97_preflight_ref`, `phase97_preflight_digest`, `phase98_preflight_ref`,
`phase98_preflight_digest`, `denial_reasons`, `abort_reasons`,
`hard_no_go_conditions`, `missing_prerequisites`, `failed_checks`, `warnings`,
`evidence_refs`, `authorization_summary` (with `execution_available`,
`execution_authorized`, `push_authorized`), `simulation_only`, `no_execution`,
`evidence_only`, `non_authorizing`, `design_only`.

Note: `approval_ref`, `audit_readiness_ref`, `rollback_readiness_ref`,
`backend_contract_ref`, `adapter_boundary_ref`, `artifact_verification_ref`,
`no_go_review_ref`, and `execution_boundary_proof_ref` are **not** in the
digest payload per the 99A implementation. The `authorization_summary` in
the digest payload includes only `execution_available`, `execution_authorized`,
and `push_authorized` — not all 12 flags. This is a known design characteristic
frozen as-is from 99A.

## 15. Compatibility Rules

### Current behavior (frozen)
- Schema version `"1.0"` is accepted
- Missing `schema_version` causes `validate()` to report `"unknown schema_version"`
- Unknown future major schema version causes `validate()` to report `"unknown schema_version"`
- Missing required fields in `to_dict()` would cause Python `AttributeError`
- Contradictory safety fields (e.g., `no_execution=False`) fail `validate()`
- Any authorization flag `true` that is checked by `validate()` fails verification
- Unknown `attempt_state` fails `validate()` with `"invalid attempt_state"`
- Unknown `denial_reason` fails `validate()` with `"unknown denial_reason"`

### Allowed future additive changes
- Adding new valid states (appended to `VALID_GEA_STATES`)
- Adding new denial reasons (appended to `VALID_GEA_DENIAL_REASONS`)
- Adding new optional fields with safe defaults
- Adding new evidence refs
- Adding new validation checks (more restrictive)

### Breaking changes (require schema version bump)
- Removing or renaming existing fields
- Changing field types
- Changing digest algorithm or payload
- Removing valid states or denial reasons
- Changing default values of safety/auth flags
- Changing `validate()` to be less restrictive

### Migration/versioning expectations
- Future phases must bump `_GEA_SCHEMA_VERSION` when making breaking changes
- Future phases must document the migration path from `"1.0"`
- Backward compatibility with `"1.0"` artifacts should be maintained or explicitly dropped

## 16. Known Pre-Existing Failures

There are 3 pre-existing fast-green failures unrelated to 99B:

- `Test94UPreflightArtifact`
- `Test94UPreflightArtifactCLI`
- `TestBackendShow`

These are not caused by 99B and are not hidden by 99B.

## 17. Residual Risks

- The model is design-only; no execution boundary validation exists in practice
- Digest payload excludes some reference fields — tampering with those fields
  would not be detected by digest comparison
- The `authorization_summary` in the digest payload includes only 3 of the 12
  auth flags, creating a gap between stored flags and digest-protected flags
- No enforcement mechanism exists to prevent code from ignoring the contract

## 18. Recommended Next Phase

**99C — Governed Execution Attempt Artifact Trust Hardening**

Trust hardening of the 99A/99B attempt boundary: digest coverage expansion,
tamper detection, auth flag trust, reference validation, verification error
contract, no-execution guard hardening, and 99B contract preservation tests.
No execution. No source changes required (test-only phase).
