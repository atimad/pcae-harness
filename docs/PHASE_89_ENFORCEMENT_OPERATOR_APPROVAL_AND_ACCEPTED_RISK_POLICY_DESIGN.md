# Phase 89I — Enforcement Operator Approval and Accepted-Risk Policy Design

```
phase_name    = phase_89i_enforcement_approval_and_accepted_risk_policy
phase_version = 1.0
phase_status  = completed
implementation_status = design_only
recommended_next_phase = 89j_enforcement_readiness_gate_checklist
```

## 1. Purpose

Define the operator approval model and accepted-risk policy required before enforcement. Clarify what humans may approve, what they may not approve, how approval is recorded, why hard blocks remain non-overridable, and how human review differs from authorization.

## 2. Scope

In scope (design only): Approval principles, roles, scopes, expiration, evidence; accepted-risk policy with risk levels; hard-block non-overridable rule; human review vs authorization distinction; multi-party approval future model; misuse/failure modes; audit and test requirements.

Out of scope: Implementation, enforcement, blocking, shell interception.

## 3. Non-Goals

89I must not implement enforcement, blocking, shell interception, wrappers, or authorization.

## 4. Starting Point from 89G/89H

89G identified:
- T17: Accepted risk overriding hard blocks (critical — prevented by design)
- T18: Human approval overriding hard blocks (critical — prevented by design)
- T19: Accidental human approval for dangerous action (high — no timeout mechanism)
- A8: Operator approves review without reading (accidental abuse)
- A9: Operator accepts risk without understanding (accidental abuse)
- SC-2: Hard blocks not overridable by accepted risk or human approval
- SC-10: No enforcement without explicit authorization

89G safety claims SC-2 and SC-10 require explicit design. 89I provides it.

## 5. Approval Principles

| # | Principle | Rationale |
|---|-----------|-----------|
| P1 | **Approval is not authorization.** Approval means a human has reviewed and consented. It does not mean PCAE authorizes execution. | 88Z principle: human review is not authorization |
| P2 | **Approval is specific.** Approval names the exact command/action, not a general category. | Prevents "blank check" approvals |
| P3 | **Approval is time-bound.** Every approval expires. The default is 1 hour; configurable per action type. | Prevents stale approvals |
| P4 | **Approval is revocable.** The approver or any operator can revoke an approval. | Safety: operator can always withdraw consent |
| P5 | **Approval is auditable.** Every grant, expiration, and revocation produces an audit record. | Non-repudiation |
| P6 | **Approval never overrides hard blocks.** No human, no matter how authorized, can approve a hard-blocked action. | 88V §16 permanent invariant |
| P7 | **Approval requires explicit action.** Click-through, default-yes, or auto-approval is prohibited. | Prevents A8 accidental approval |

## 6. Approval Roles

| Role | Who | What They Can Approve |
|------|-----|----------------------|
| **Self-Approver** | The operator proposing the action | Read-only commands with uncertain classification (low risk) |
| **Task Owner** | The operator who created the active task | Filesystem writes within task scope (medium risk) |
| **Reviewer** | A different human operator | Backend invocation, network access, adoption (high risk) |
| **Administrator** | Designated PCAE administrator | Enforcement enable/disable, configuration changes (critical) |
| **No One** | No human, no role | Hard blocks — force push, destructive filesystem, policy-forbidden files |

## 7. Approval Scopes

| Scope | Description | Example |
|-------|-------------|---------|
| `single_command` | Approval for one specific command | `git push origin main` (exact text hash) |
| `command_category` | Approval for commands in a category | All `read_only_inspection` commands for 1 hour |
| `file_set` | Approval for mutations to specific files | Write access to `src/pcae/core/example.py` |
| `task_duration` | Approval valid for the duration of the active task | All in-scope file mutations while task is active |
| `session` | Approval valid for the current PCAE session | All governed commands for session duration |

**Default scope:** `single_command`. Broader scopes require explicit operator choice and are audited.

## 8. Approval Expiration

| Scope | Default Expiry | Max Expiry |
|-------|---------------|------------|
| `single_command` | 5 minutes | 1 hour |
| `command_category` | 30 minutes | 4 hours |
| `file_set` | 1 hour | 8 hours |
| `task_duration` | Task end | Task end + 1 hour |
| `session` | Session end | Session end |

All expirations are configurable by the administrator. Expired approvals produce `approval.expired` audit events.

## 9. Approval Evidence Requirements

Every approval must record:

| Field | Description |
|-------|-------------|
| `approval_id` | Unique identifier |
| `approved_by` | Operator username |
| `approved_action` | Human-readable description |
| `approved_command_hash` | SHA-256 of the command text |
| `scope` | One of the 5 scope types |
| `granted_at` | ISO 8601 timestamp |
| `expires_at` | ISO 8601 timestamp |
| `revocable` | Boolean (always true) |
| `revoked_at` | Null until revoked |
| `decision_context` | Original would-* decision before approval |
| `hard_block_present` | Whether a hard block existed (must be false for approval to be valid) |
| `audit_checksum` | SHA-256 integrity checksum |

## 10. Accepted-Risk Policy

### 10.1 Policy Statement

Accepted risk is a mechanism for operators to acknowledge that a proposed action carries known risks, and to proceed despite those risks. Accepted risk is NOT a mechanism to bypass hard blocks or governance rules.

### 10.2 When Accepted Risk Applies

| Situation | Accepted Risk? |
|-----------|---------------|
| Command classified as `unknown` but operator knows it's safe | Yes (low risk) |
| Filesystem write outside strict task scope but within project | Yes (medium risk) |
| Network access for known-safe endpoint | Yes (medium risk, with review) |
| Hard block (force push, destructive fs) | **No — never** |
| Policy-forbidden file mutation | **No — never** |
| Backend invocation without task contract | **No — requires review first** |

## 11. Risk Levels

| Level | Description | Required for Acceptance | Max Duration |
|-------|-------------|----------------------|-------------|
| **Low** | Read-only command with uncertain classification | Self-acknowledgment | 1 hour |
| **Medium** | Filesystem write in task scope, network access to known endpoint | Self-acknowledgment + active task | 4 hours |
| **High** | Backend invocation, adoption, push, commit | Human review + acknowledgment | 1 hour |
| **Critical** | Hard blocks, force push, destructive fs | **Cannot be accepted** | N/A |

## 12. Non-Overridable Hard Blocks

### 12.1 Permanent Invariant

```
Accepted risk MUST NOT override hard blocks.
Human approval MUST NOT override hard blocks.
No operator, administrator, or automated system MAY override hard blocks.

This is a permanent, non-negotiable safety invariant.
Source: 88V §16, reaffirmed in 89G SC-2.
```

### 12.2 Hard Blocks (Non-Overridable)

| Hard Block | Reason |
|-----------|--------|
| `blocked_by_force_push` | Force push rewrites shared history |
| `blocked_by_destructive_filesystem` | Cannot undo data loss |
| `blocked_by_policy_forbidden_file` | Policy-forbidden files are never mutable |
| `blocked_by_history_rewrite` | History rewrite defeats audit trail |
| `blocked_by_shell_gate` | Shell gate classification is authoritative |
| `blocked_by_conflicting_evidence` | Cannot proceed with contradictory evidence |
| `deny` | Unconditional deny — no path exists |

### 12.3 Verification

Any code path that applies accepted risk or human approval must:
1. Check `hard_block_present` before applying
2. If `hard_block_present` is true, refuse to apply
3. Log the refusal as an audit event
4. Return the hard block decision unchanged

## 13. Human Review versus Authorization

| Concept | Meaning | PCAE Treatment |
|---------|---------|---------------|
| **Human Review** | A human has examined the proposed action | Gating step: required for high-risk actions |
| **Human Approval** | A human explicitly consents to the action | Recorded decision: time-bound, revocable |
| **Authorization** | PCAE grants permission to execute | PCAE NEVER grants authorization |
| **Execution** | The command actually runs | PCAE NEVER executes commands |

Key distinction: Review and approval are human actions recorded by PCAE. Authorization and execution are PCAE actions — and PCAE never performs them.

## 14. Multi-Party Approval Future Model

### 14.1 When Multi-Party Is Needed

For enforcement Stages 4+ (Execution Gate With Human Approval):

| Action | Required Approvals |
|--------|-------------------|
| Push to main | 1 reviewer |
| Backend invocation (new backend) | 2 reviewers |
| Adoption of backend output | 2 reviewers |
| Rollback execution | 1 reviewer + administrator |
| Enforcement disable | 2 reviewers |

### 14.2 Multi-Party Properties

- Approvals are independent (reviewers don't see each other's decisions)
- All approvals must be active (not expired, not revoked)
- Any single revocation invalidates the approval set
- Approval chain recorded in audit log

### 14.3 Deferred

Multi-party approval is deferred to enforcement Stage 4+. Initial enforcement (Stage 3) uses single-party approval.

## 15. Misuse and Failure Modes

| # | Mode | Mitigation |
|---|------|-----------|
| M1 | Operator approves without reading | Approval requires explicit command text confirmation |
| M2 | Operator accepts risk without understanding risk | Risk description is mandatory and specific |
| M3 | Approval used after expiration | Expiration is enforced in code, not advisory |
| M4 | Revocation not honored due to race condition | Approval check is atomic with enforcement action |
| M5 | Administrator approves hard block | Code refuses: hard_block_present check before applying |
| M6 | Operator shares approval token | Approval is bound to operator identity (username) |
| M7 | Stale approval from previous session | Approvals are session-scoped or time-bound |

## 16. Audit Requirements

Every approval and risk acceptance event produces an audit record per 89H schemas:
- `approval.granted` — when approval is granted
- `approval.expired` — when approval expires naturally
- `approval.revoked` — when approval is manually revoked
- `risk.accepted` — when risk is accepted
- `risk.expired` — when accepted risk expires

All records are checksummed and chain-validated per 89H §13–14.

## 17. Tests Required Before Implementation

| Category | Tests | Description |
|----------|-------|-------------|
| Approval grant | 8 | Correct scope, expiry, audit record |
| Approval expiration | 5 | Expired approvals not honored |
| Approval revocation | 5 | Revoked approvals not honored |
| Hard-block refusal | 8 | Approval/risk cannot override hard blocks |
| Accepted risk levels | 6 | Correct level assignment and gating |
| Multi-party (future) | 0 | Deferred to Stage 4+ |
| Audit integrity | 5 | All approval/risk events in audit chain |
| Misuse prevention | 6 | Expiry, revocation, race conditions |
| **Total** | **~43** | |

## 18. Recommended Next Phase

**89J — Enforcement Readiness Gate Checklist and Go/No-Go Criteria**
