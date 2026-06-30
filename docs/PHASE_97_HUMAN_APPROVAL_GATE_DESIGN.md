# Phase 97D — Human Approval Gate for Future Execution

```
phase_name = phase_97d_human_approval_gate | phase_status = completed | implementation_status = design_only
recommended_next_phase = 97E — Execution Audit / Rollback Readiness Design
```

## 1. Purpose

Design the human approval gate for future governed execution phases. Define how human approval would eventually be requested, scoped, recorded, verified, expired, revoked, denied, audited, and separated from backend invocation, adapter execution, apply, commit, and push authorization.

**This is an approval-gate design phase only. No execution. No enforcement.**

## 2. Scope

### 2.1 In Scope

- Approval gate conceptual model and role definitions
- Approval request schema (JSON shape, non-executing)
- Approval decision schema (JSON shape, all auth flags forced false)
- Approval scope model (review, preflight, invocation, execution, apply, commit, push — all separated)
- Approval expiry and revocation model
- Approval verification behavior (fail-closed)
- Denial reasons and fail-closed behavior
- Audit expectations (fields, not storage)
- Relationship to 96/97A/97B/97C contracts
- Non-transferability guarantees
- Separation from apply/commit/push authorization

### 2.2 Out of Scope (No-Go)

- Real backend invocation
- Adapter execution
- Subprocess execution
- Shell execution
- Network calls
- Shell interception
- Telegram inbound
- Telegram polling
- Remote shell
- /run
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

## 3. Relationship to Prior Phases

### 3.1 Phase 96 — Connected Automation Chain

Phase 96 delivered a connected, repeatable, verifiable, non-executing automation chain. All Phase 96 artifacts are evidence-only. The 97D approval gate extends this evidence chain with a human intent layer — approval artifacts that capture human authorization intent without enabling execution.

**97D does not break:** connected chain demo, frozen artifact contracts, artifact trust verification, execution-unavailable proof, boundary review expectations.

### 3.2 Phase 97A — Execution Readiness Model

97A defined execution readiness statuses (`unavailable`, `not_ready`, `evidence_incomplete`, `approval_required`, `blocked`, `ready_for_human_review`, `ready_for_preflight_only`, `execution_ready`) and no-go criteria. 97D fills the `approval_required` and `ready_for_human_review` states with actual approval artifacts and verification logic.

**97D adds:** concrete approval request/decision schemas, scope model, expiry/revocation, verification behavior.

**97D does not change:** readiness statuses, no-go criteria list, evidence categories, fail-closed behavior, `execution_available=false` invariant.

### 3.3 Phase 97B — Governed Backend Invocation Contract

97B defined backend invocation request/preflight/denial contracts. The 97D approval gate links to backend invocation requests via `backend_invocation_request_ref` but does not authorize backend invocation in the current phase.

**97D adds:** approval scope that can reference backend invocation requests, denial reasons for missing backend request ref.

**97D does not change:** backend invocation request schema, preflight schema, denial statuses, identity requirements, output capture contract.

### 3.4 Phase 97C — Adapter Invocation Boundary

97C defined adapter identity, capability, request/preflight, and denial boundary with 14 adapter-specific denial reasons. The 97D approval gate links to adapter invocation requests but does not authorize adapter execution.

**97D adds:** approval scope that can reference adapter invocation requests, denial reasons for missing adapter request ref.

**97D does not change:** adapter identity schema, capability declaration schema, adapter invocation request boundary, adapter denial statuses, secret-handling invariants.

## 4. What Is Human Approval?

Human approval is a **non-transferable, scoped, time-bounded, artifact-linked declaration of human intent** that a specific governed action class may proceed to future execution readiness review.

Approval is **evidence of human intent, not execution authorization**. In the current system (97D and all prior phases), approval artifacts are non-executing and non-authorizing. Even an "approved" decision artifact sets `execution_available: false` and `execution_authorized: false`.

### 4.1 What Approval Can Authorize in the Future

- Readiness review advancement
- Preflight assessment execution
- Backend invocation (future, when execution phases exist)
- Adapter execution (future, when execution phases exist)
- Output review (future)
- Apply (future, when apply governance exists)
- Commit (future, when commit governance exists)
- Push (future, when push governance exists)

### 4.2 What Approval Can Never Authorize by Itself

- Override of no-go conditions
- Override of failed artifact verification
- Override of forbidden scope
- Override of bypass-permissions detection
- Raw git commit
- Raw git push
- --no-verify or force push
- Execution without readiness
- Execution without evidence chain
- Execution without artifact verification
- Transfer of approval to another operator
- Reuse for a different task/phase/backend/adapter/action class
- Application to modified artifacts without re-approval

## 5. Approval Roles

| Role | Type | Authorizes |
|------|------|------------|
| Human operator | Identity | Nothing (provides intent) |
| Approval request | Contract | Nothing (declares what is requested) |
| Approval decision | Authorization intent | Nothing in current phase (future: scoped action class) |
| Approval artifact | Evidence | Nothing (records intent) |
| Approval scope | Constraint | Nothing (bounds what can be requested) |
| Approval evidence chain | Evidence | Nothing (links to readiness, backend, adapter) |
| Readiness artifact | Evidence | Nothing (assessed readiness) |
| Backend invocation request | Contract | Nothing (declared backend intent) |
| Adapter invocation request | Contract | Nothing (declared adapter intent) |
| Phase/task contract | Governance | Nothing (bounds scope) |
| Approval verifier | Validation | Nothing (checks correctness) |
| Approval revocation artifact | Evidence | Nothing (negates prior approval) |
| Approval denial artifact | Evidence | Nothing (records denial) |
| Audit record | Evidence | Nothing (records what happened) |

**Key principles:**

- Human approval is required for future execution, but current approval design does not enable execution
- Approval is evidence/authorization intent only until future governed execution phases exist
- Approval for backend invocation is not approval for adapter execution unless explicitly scoped
- Approval for execution is not approval for apply
- Approval for apply is not approval for commit
- Approval for commit is not approval for push
- Approval cannot override no-go conditions
- Approval cannot override failed artifact verification
- Approval cannot override forbidden scope
- Approval cannot override bypass-permissions detection
- Approval cannot authorize raw git commit/push
- Approval cannot authorize --no-verify or force push

## 6. Approval Request Schema (Design)

A future JSON shape for approval requests. Non-executing, non-authorizing.

```
{
  "schema_version": "1.0",
  "approval_request_id": "<uuid>",
  "phase_id": "<phase_id>",
  "task_id": "<task_id>",
  "requested_by": "<operator_identifier>",
  "requested_at_utc": "<ISO 8601>",
  "requested_action_class": "<action_class>",
  "requested_scope": "<scope>",
  "readiness_artifact_ref": "<path_or_hash>",
  "backend_invocation_request_ref": "<path_or_hash_or_null>",
  "adapter_invocation_request_ref": "<path_or_hash_or_null>",
  "evidence_chain_ref": "<path_or_hash>",
  "artifact_verification_ref": "<path_or_hash>",
  "execution_boundary_proof_ref": "<path_or_hash>",
  "no_go_conditions": [],
  "missing_evidence": [],
  "risk_summary": "<text>",
  "requested_authorizations": [],
  "explicitly_not_requested": [],
  "expires_at_utc": "<ISO 8601>",
  "human_review_required": true,
  "approval_status": "pending",
  "execution_available": false,
  "execution_authorized": false,
  "backend_invocation_authorized": false,
  "adapter_execution_authorized": false,
  "apply_authorized": false,
  "commit_authorized": false,
  "push_authorized": false,
  "simulation_only": true,
  "no_execution": true,
  "digest": "<sha256>"
}
```

**Key invariants (all forced false/true):**
- `execution_available: false` — execution remains unavailable
- `execution_authorized: false` — no execution authorization
- `backend_invocation_authorized: false` — no backend call
- `adapter_execution_authorized: false` — no adapter call
- `apply_authorized: false` — no apply
- `commit_authorized: false` — no commit
- `push_authorized: false` — no push
- `simulation_only: true` — simulation/design only
- `no_execution: true` — explicit no-execution guard
- `human_review_required: true` — human must review

## 7. Approval Decision Schema (Design)

A future JSON shape for approval decisions. Even an "approved" decision is non-executing in the current phase.

```
{
  "schema_version": "1.0",
  "approval_decision_id": "<uuid>",
  "approval_request_id": "<uuid>",
  "phase_id": "<phase_id>",
  "task_id": "<task_id>",
  "decided_by": "<operator_identifier>",
  "decided_at_utc": "<ISO 8601>",
  "decision": "approved | denied | revoked | expired",
  "approved_action_classes": [],
  "denied_action_classes": [],
  "approval_scope": "<scope>",
  "approval_constraints": [],
  "approval_exclusions": [],
  "expiry": "<ISO 8601>",
  "revocation_ref": "<path_or_null>",
  "readiness_artifact_ref": "<path_or_hash>",
  "backend_invocation_request_ref": "<path_or_hash_or_null>",
  "adapter_invocation_request_ref": "<path_or_hash_or_null>",
  "evidence_chain_ref": "<path_or_hash>",
  "artifact_verification_ref": "<path_or_hash>",
  "human_confirmation_text": "<free_text>",
  "non_transferable": true,
  "no_override_no_go": true,
  "no_override_failed_verification": true,
  "no_override_scope_violation": true,
  "no_raw_git_allowed": true,
  "no_no_verify_allowed": true,
  "no_force_push_allowed": true,
  "execution_available": false,
  "execution_authorized": false,
  "backend_invocation_authorized": false,
  "adapter_execution_authorized": false,
  "apply_authorized": false,
  "commit_authorized": false,
  "push_authorized": false,
  "simulation_only": true,
  "no_execution": true,
  "digest": "<sha256>"
}
```

**Key invariants (all forced regardless of decision):**
- All authorization flags forced `false`
- `non_transferable: true`
- `no_override_no_go: true`
- `no_override_failed_verification: true`
- `no_override_scope_violation: true`
- `no_raw_git_allowed: true`
- `no_no_verify_allowed: true`
- `no_force_push_allowed: true`
- `execution_available: false`
- `simulation_only: true`
- `no_execution: true`

**In this phase, even an "approved" decision artifact must remain non-executing and non-authorizing for real execution.**

## 8. Approval Scope Model

### 8.1 Scope Categories

| Scope | Description | Authorizes (Future) |
|-------|-------------|---------------------|
| `readiness_review` | Review of execution readiness evidence | Advancement to preflight |
| `backend_invocation_preflight_review` | Review of backend invocation preflight | Backend preflight execution |
| `adapter_invocation_preflight_review` | Review of adapter invocation preflight | Adapter preflight execution |
| `backend_invocation` | Backend invocation execution | Real backend call |
| `adapter_execution` | Adapter execution | Real adapter call |
| `output_review` | Review of captured output | Advancement to apply |
| `apply` | Apply reviewed output | File mutation |
| `commit` | Commit applied changes | Git commit |
| `push` | Push committed changes | Git push |

### 8.2 Scope Separation

Each scope is **independent and non-transitive**:

- `readiness_review` approval does not authorize `backend_invocation`
- `backend_invocation_preflight_review` approval does not authorize `adapter_execution`
- `backend_invocation` approval does not authorize `adapter_execution`
- `adapter_execution` approval does not authorize `apply`
- `apply` approval does not authorize `commit`
- `commit` approval does not authorize `push`

**Current 97D artifacts may model these scopes, but cannot activate them.**

## 9. Approval Expiry and Revocation

### 9.1 Expiry

- Approvals **must** have an expiry timestamp
- Expiry is **task-bound** — cannot outlive the task
- Expiry is **phase-bound** — cannot span across phases unless explicitly re-approved
- Expiry is **artifact-bound** — tied to specific artifact digests
- Expiry is **operation-class-bound** — only valid for the approved action class
- Expired approval **must fail verification**
- Default max expiry: task duration + 1 hour buffer

### 9.2 Revocation

- Approvals **must** be revocable
- Revocation produces a **revocation artifact** referencing the original approval decision
- Revoked approval **must fail verification**
- Revocation is **immediate** — no grace period
- Revocation is **non-reversible** — requires a new approval request
- Revocation reason must be recorded

### 9.3 Non-Transferability

- Approval is bound to the **requesting operator**
- Approval is bound to the **deciding operator**
- Approval cannot be transferred to another operator
- Approval cannot be reused for a different task/phase/backend/adapter/action class
- Approval cannot apply to modified artifacts unless re-approved (digest must match)

## 10. Approval Verification Behavior

### 10.1 Verification Checks

Verification must check:

1. Schema version is recognized
2. Digest is valid and matches artifact content
3. Task ID matches current task
4. Phase ID matches current phase
5. Approval request ID is present and valid
6. Decision ID is present and valid
7. Decision status is `approved` (not `denied`, `revoked`, `expired`)
8. Scope matches requested action class
9. Expiry has not passed
10. Revocation ref is null (not revoked)
11. Linked readiness artifact ref is valid
12. Linked backend request ref matches (if scope requires it)
13. Linked adapter request ref matches (if scope requires it)
14. Linked evidence chain ref is valid
15. Linked artifact verification ref is valid
16. No-go conditions list is empty
17. Safety flags are consistent (no contradictory flags)
18. Authorization flags are all false (execution unavailable)
19. Approval exclusions do not cover the requested action
20. `non_transferable` is true
21. `no_override_no_go` is true
22. `no_raw_git_allowed` is true
23. `no_no_verify_allowed` is true
24. `no_force_push_allowed` is true

### 10.2 Fail-Closed Triggers

Verification must fail closed (return `False`, no authorization) if:

- Missing approval (no approval artifact at all)
- Stale approval (task/phase mismatch)
- Expired approval (past expiry)
- Revoked approval (revocation ref present)
- Scope mismatch (wrong action class)
- Task mismatch (wrong task ID)
- Phase mismatch (wrong phase ID)
- Backend request mismatch (wrong backend ref)
- Adapter request mismatch (wrong adapter ref)
- Evidence chain mismatch (wrong evidence ref)
- Artifact digest mismatch (tampered or modified)
- No-go condition present
- Failed artifact verification
- Contradictory safety flags
- Unknown schema version

## 11. Approval Denial / Fail-Closed Behavior

### 11.1 Denial Reasons

| Denial Reason | Trigger |
|---------------|---------|
| `denied_missing_readiness` | No readiness artifact linked |
| `denied_missing_backend_request` | Backend invocation scope but no backend request ref |
| `denied_missing_adapter_request` | Adapter execution scope but no adapter request ref |
| `denied_missing_evidence_chain` | No evidence chain linked |
| `denied_missing_artifact_verification` | No artifact verification linked |
| `denied_no_go_condition_present` | Active no-go condition |
| `denied_scope_mismatch` | Requested action not in approved scope |
| `denied_task_mismatch` | Wrong task ID |
| `denied_phase_mismatch` | Wrong phase ID |
| `denied_expired` | Past expiry timestamp |
| `denied_revoked` | Revocation ref present |
| `denied_stale_artifact` | Linked artifact digest mismatch |
| `denied_failed_verification` | Artifact verification failed |
| `denied_forbidden_scope` | Scope is on exclusion list |
| `denied_bypass_permissions` | Bypass-permissions detected |
| `denied_raw_git_path` | Raw git command path detected |
| `denied_no_verify_attempt` | --no-verify flag detected |
| `denied_force_push_attempt` | Force push detected |
| `denied_unknown_schema` | Unrecognized schema version |
| `denied_conflicting_safety_flags` | Contradictory safety flags |
| `denied_requested_authorization_out_of_scope` | Authorization requested beyond approved scope |

### 11.2 Fail-Closed Behavior

When approval verification fails:

- **No backend call** — backend invocation not attempted
- **No adapter call** — adapter execution not attempted
- **No subprocess** — no subprocess spawned
- **No network** — no network connection opened
- **No shell** — no shell command executed
- **No apply** — no file mutation
- **No commit/push** — no git operations
- Write **non-authorizing denial evidence** only if appropriate
- Report missing/failed approval checks
- Preserve audit/report trail

## 12. Audit Expectations

### 12.1 Future Audit Fields

When audit storage is implemented (future phase), audit records should capture:

- `approval_request_id` — which request
- `approval_decision_id` — which decision
- `operator_identifier` — who acted
- `timestamp` — when
- `task_id` — under which task
- `phase_id` — under which phase
- `artifact_references` — linked artifacts (readiness, backend, adapter, evidence, verification)
- `decision` — approved/denied/revoked/expired
- `scope` — what was approved
- `exclusions` — what was excluded
- `expiry` — when it expires
- `revocation` — if revoked, reference to revocation artifact
- `digest` — content integrity
- `verification_result` — pass/fail
- `no_go_snapshot` — no-go conditions at decision time
- `risk_summary` — risk assessment at decision time

**Do not implement database-backed audit storage in 97D.**

## 13. No-Go Criteria (97D-Specific)

Beyond the no-go criteria inherited from 97A/97B/97C:

- Missing approval artifact
- Stale/expired/revoked approval
- Scope mismatch between approval and requested action
- Task/phase mismatch
- Artifact digest mismatch (tampering)
- Contradictory safety flags in approval decision
- Approval for execution when `execution_available` is `false`
- Approval requested for forbidden action class
- Approval for apply/commit/push without explicit scope
- Approval attempting to override no-go conditions
- Non-transferable flag is false or missing
- `no_override_no_go` flag is false or missing
- `no_raw_git_allowed` flag is false or missing

## 14. Relationship to Future Execution Audit / Rollback Readiness

97E should design:

- Execution audit readiness — what must be auditable before execution
- Rollback readiness — what must be reversible before execution
- Audit artifact schema — shape of audit records
- Rollback preflight expectations — what rollback evidence looks like
- Failure/abort handling — what happens on execution failure
- Evidence retention — how long evidence is kept

97D defines the approval dimension that 97E will reference:
- 97E audit records should reference 97D approval decisions
- 97E rollback preflight should verify approval is still valid
- 97E execution audit should confirm approval was obtained

**Do not implement audit database or rollback execution in 97D.**

## 15. Future Implementation Prerequisites

Before any real approval enforcement can be activated:

1. Execution phases must exist (future 98+)
2. Real backend invocation must be available (future)
3. Real adapter execution must be available (future)
4. Audit storage must be implemented (future)
5. Rollback mechanisms must be implemented (future)
6. All evidence chain artifacts must be verifiable at runtime
7. Operator identity must be verifiable
8. Approval artifact persistence must be available
9. Revocation mechanism must be operational
10. All no-go criteria must be enforceable at runtime

## 16. Residual Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Approval model is too granular → operator fatigue | Medium | Start with coarse scopes, refine later |
| Approval model is too coarse → insufficient control | Medium | Add finer scopes in future phases |
| Approval artifacts could be forged without crypto | High | Add signing in future phase (out of scope for 97D) |
| Approval verification depends on artifact integrity | Medium | Digest checking mitigates; crypto strengthens |
| Human operator may approve without understanding | Medium | Mandatory human confirmation text; audit trail |
| Approval expiry may be too short → workflow disruption | Low | Configurable expiry per scope |
| Approval expiry may be too long → stale authorization | Low | Task/phase binding limits blast radius |

## 17. Recommended Next Phases

97E — Execution Audit / Rollback Readiness Design → 97F — Preflight Dry-Run → 98A — First Governed Execution Preflight Prototype (future).

## 18. No-Go Confirmation

- No real backend invocation
- No adapter execution
- No subprocess execution
- No shell execution
- No network calls
- No shell interception
- No Telegram inbound
- No Telegram polling
- No remote shell
- No /run
- No enforcement
- No automatic apply
- No apply execution
- No patch parsing
- No commit authorization
- No push authorization
- No real AI backend calls
- No executable artifact-only invocation paths
- No execution enablement flags
- No execution availability toggles
- No cryptographic signing
- No remote attestation
- No database-backed audit storage
- No shell mediation
