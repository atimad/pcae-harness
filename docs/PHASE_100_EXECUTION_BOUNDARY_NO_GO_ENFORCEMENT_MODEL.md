# Phase 100B — Execution Boundary No-Go Enforcement Model

## 1. Purpose

Design and model how hard no-go conditions should block any future
execution-capable boundary. Transform the Phase 100A prerequisite gap analysis
into a clear no-go enforcement model: which conditions are hard-blocking, how
they are evaluated, how conflicts are resolved, how denial/fail-closed evidence
is represented, and how future phases must consume the model without enabling
execution.

**Design/model-only. No runtime enforcement. No execution.**

## 2. Scope

- Define no-go enforcement model
- Build no-go taxonomy (17 categories)
- Map 30 hard no-go conditions from 100A with severity and evidence
- Define severity model (6 severities)
- Define evaluation order (16 steps)
- Design denial/fail-closed evidence JSON shape
- Define future consumer guidance
- Minimal model implementation (enums, dataclass, validation)
- Tests proving design-only, non-authorizing, fail-closed

## 3. Non-Goals

100B does **not** add, enable, or authorize: real backend invocation, adapter
execution, subprocess execution, shell execution, network calls, shell
interception, Telegram inbound, Telegram polling, remote shell, /run, actual
enforcement, automatic apply, apply execution, patch parsing, commit
authorization, push authorization, real AI backend calls, executable
artifact-only invocation path, execution enablement flag, execution
availability toggle, cryptographic signing, remote attestation,
database-backed audit storage, shell mediation, rollback execution, file
mutation rollback, automatic restore, git reset/checkout/revert execution.

Telegram remains outbound-only. Execution remains unavailable.
All authorization flags remain False. All safety flags remain True.

## 4. Definition: No-Go Enforcement Model

The no-go enforcement model is a design/model artifact that defines how future
PCAE execution-capable boundary work must treat hard blockers. It does not
enforce anything at runtime today. It provides the vocabulary, evidence shape,
and fail-closed decision rules that future enforcement phases must implement
before any execution-capable boundary can exist.

Explicitly:
- No runtime enforcement is implemented
- No execution boundary exists
- No execution is enabled
- The model is evidence-only and non-authorizing

## 5. Relationship to Prior Phases

- **100A Gap Analysis**: Source of 30 hard no-go conditions and prerequisite
  classification
- **Phase 99**: Governed Execution Attempt Boundary — provides attempt state
  vocabulary, denial reasons, auth/safety flags, digest pattern
- **Phase 98**: Governed Execution Preflight — provides preflight evidence
  consumption pattern
- **Phase 97**: Execution Readiness Preflight — provides readiness assessment
  pattern

## 6. No-Go Taxonomy — 17 Categories

| # | Category | Scope |
|---|----------|-------|
| 1 | `artifact_trust` | Schema, digest, tamper, reference validation |
| 2 | `prerequisite` | Missing Phase 97/98/99 evidence |
| 3 | `authorization_flag` | Any auth flag True in non-executing artifact |
| 4 | `safety_flag` | Missing or False safety flags |
| 5 | `approval` | Missing, expired, or revoked human approval |
| 6 | `audit` | Missing audit readiness or persistence |
| 7 | `rollback` | Missing rollback readiness or plan |
| 8 | `backend_adapter` | Missing backend allowlist or adapter capability |
| 9 | `shell_subprocess_network` | Missing boundary design |
| 10 | `mutation_apply` | Missing patch validation or apply governance |
| 11 | `commit_push` | Missing commit/push governance |
| 12 | `report_notification` | Missing report completeness or notification |
| 13 | `operator_runtime_mode` | Bypass permissions, raw git, force push |
| 14 | `secret_exposure` | Secret material detected in output |
| 15 | `compatibility_schema` | Unknown schema version |
| 16 | `stale_replay` | Stale or tampered artifact |
| 17 | `unknown_unsupported` | Unknown state, unsupported request |

## 7. Mapped 100A Hard No-Go Conditions — 30

Each condition: identifier, category, severity, trigger, denial reason.

| # | ID | Category | Severity | Denial Reason |
|---|----|----------|----------|---------------|
| 1 | `MISSING_PHASE97_PREFLIGHT` | prerequisite | hard_blocker | `denied_missing_phase97_preflight` |
| 2 | `MISSING_PHASE98_PREFLIGHT` | prerequisite | hard_blocker | `denied_missing_phase98_preflight` |
| 3 | `MISSING_PHASE99_ATTEMPT` | prerequisite | hard_blocker | `denied_missing_attempt_boundary` |
| 4 | `ARTIFACT_TAMPERED` | artifact_trust | critical_blocker | `denied_failed_artifact_verification` |
| 5 | `UNKNOWN_SCHEMA` | compatibility_schema | trust_failure | `denied_unknown_schema` |
| 6 | `STALE_ARTIFACT` | stale_replay | trust_failure | `denied_stale_artifact` |
| 7 | `AUTH_FLAG_TRUE` | authorization_flag | critical_blocker | `denied_unsafe_authorization_flag` |
| 8 | `NO_EXECUTION_FALSE` | safety_flag | critical_blocker | `denied_no_execution_false` |
| 9 | `SIMULATION_ONLY_FALSE` | safety_flag | critical_blocker | `denied_simulation_only_false` |
| 10 | `EVIDENCE_ONLY_FALSE` | safety_flag | hard_blocker | `denied_evidence_only_false` |
| 11 | `NON_AUTHORIZING_FALSE` | safety_flag | hard_blocker | `denied_non_authorizing_false` |
| 12 | `MISSING_APPROVAL_ENFORCEMENT` | approval | hard_blocker | `denied_missing_human_approval` |
| 13 | `MISSING_AUDIT_PERSISTENCE` | audit | hard_blocker | `denied_missing_audit_readiness` |
| 14 | `MISSING_ROLLBACK_PLAN` | rollback | hard_blocker | `denied_missing_rollback_readiness` |
| 15 | `MISSING_DENIAL_ENFORCEMENT` | prerequisite | hard_blocker | `denied_missing_denial_enforcement` |
| 16 | `MISSING_BACKEND_ALLOWLIST` | backend_adapter | hard_blocker | `denied_missing_backend_allowlist` |
| 17 | `MISSING_ADAPTER_ALLOWLIST` | backend_adapter | hard_blocker | `denied_missing_adapter_allowlist` |
| 18 | `MISSING_SHELL_BOUNDARY` | shell_subprocess_network | hard_blocker | `denied_missing_shell_boundary` |
| 19 | `MISSING_OUTPUT_CAPTURE` | prerequisite | hard_blocker | `denied_missing_output_capture` |
| 20 | `MISSING_SECRET_REDACTION` | secret_exposure | critical_blocker | `denied_secret_material_detected` |
| 21 | `MISSING_TIMEOUT_ABORT` | prerequisite | hard_blocker | `denied_missing_timeout_abort` |
| 22 | `MISSING_REPORT_COMPLETENESS` | report_notification | hard_blocker | `denied_missing_report_completeness` |
| 23 | `MISSING_NOTIFICATION_VISIBILITY` | report_notification | reporting_failure | `denied_missing_notification_visibility` |
| 24 | `BYPASS_PERMISSIONS` | operator_runtime_mode | critical_blocker | `denied_bypass_permissions` |
| 25 | `RAW_GIT_OR_FORCE` | operator_runtime_mode | hard_blocker | `denied_requested_commit_push` |
| 26 | `TELEGRAM_INBOUND` | unknown_unsupported | unsupported_request | `denied_requested_telegram_inbound` |
| 27 | `AUTOMATIC_APPLY` | mutation_apply | unsupported_request | `denied_requested_apply` |
| 28 | `ROLLBACK_WITHOUT_GOVERNANCE` | rollback | unsupported_request | `denied_requested_rollback_execution` |
| 29 | `PREMATURE_BACKEND_INVOCATION` | backend_adapter | unsupported_request | `denied_requested_backend_invocation` |
| 30 | `EVIDENCE_AS_AUTHORIZATION` | prerequisite | critical_blocker | `denied_evidence_mistaken_for_authorization` |

## 8. Severity Model — 6 Severities

| Severity | Behavior | Overridable |
|---|---|---|
| `critical_blocker` | Always deny/fail-closed. No path to execution. | Never |
| `hard_blocker` | Always deny/fail-closed. No path to execution. | Never |
| `missing_prerequisite` | Deny until prerequisite is satisfied. | Never |
| `trust_failure` | Deny; artifact chain is compromised. | Never |
| `unsupported_request` | Deny; request is out of scope. | Never |
| `reporting_failure` | Blocks execution-capable boundary until resolved. | Never |

Rules:
- Multiple no-go conditions aggregate — none can cancel another
- All severities are non-overridable
- Approval, audit, rollback, or preflight refs cannot override any severity

## 9. Evaluation Order — 16 Steps

1. Operator/runtime mode safety
2. Schema and compatibility
3. Artifact presence (Phase 97, 98, 99)
4. Artifact trust (digest, tamper, reference)
5. Safety flags
6. Authorization flags
7. Prerequisite completeness
8. Approval validity
9. Audit readiness
10. Rollback readiness
11. Backend/adapter capability availability
12. Shell/subprocess/network boundary availability
13. Mutation/apply boundary availability
14. Commit/push governance availability
15. Report/notification trust
16. Unknown/unsupported request review

Rules:
- Evaluation stops safely on fatal trust failures when further evaluation
  depends on compromised data
- All detected blockers should be recorded when safe to continue
- Fail-closed is default when evaluation cannot complete
- Missing data is never treated as permission

## 10. Denial/Fail-Closed Evidence Model

Design for future JSON evidence artifact (not executable today):

```json
{
  "schema_version": "1.0",
  "no_go_evaluation_id": "",
  "phase_id": "100B",
  "task_id": "",
  "generated_at_utc": "",
  "evaluation_status": "denied",
  "evaluation_decision": "blocked",
  "source_gap_analysis_ref": "",
  "checked_no_go_conditions": [],
  "triggered_no_go_conditions": [],
  "missing_evidence": [],
  "failed_checks": [],
  "denial_reasons": [],
  "severity_summary": {},
  "override_attempts": [],
  "unknown_conditions": [],
  "unsupported_requests": [],
  "warnings": [],
  "execution_available": false,
  "execution_authorized": false,
  "simulation_only": true,
  "no_execution": true,
  "evidence_only": true,
  "non_authorizing": true,
  "design_only": true,
  "digest": ""
}
```

All 12 auth flags False. All 5 safety flags True. Non-executing. Non-authorizing.

## 11. Implementation

- **Model**: `src/pcae/core/backend_invocations.py` — constants for 17 no-go
  categories, 6 severities, 30 no-go conditions, evaluation statuses/decisions;
  `NoGoEnforcementEvidence` dataclass with validation
- **Tests**: `tests/test_execution_boundary_no_go_enforcement_model.py`

## 12. Future Consumer Guidance

Future phases must:
- Treat no-go evidence as blocking, not permission
- Require all relevant no-go conditions to be absent before any execution-capable
  design can proceed
- Never let approval override hard no-go
- Never let evidence artifacts override safety flags
- Fail closed on unknown conditions
- Fail closed on stale/tampered artifacts
- Preserve all authorization flags False until explicitly reviewed
- Not introduce execution enablement without separate design/review/proof track

## 13. Residual Risks

- Model is design-only — no runtime enforcement exists
- 30 conditions are a snapshot; new conditions may be discovered
- Future phases could ignore the model unless contractually bound to it
- 3 pre-existing test failures remain

## 14. Recommended Next Phase

**100C — Execution Boundary No-Go Contract Freeze**
