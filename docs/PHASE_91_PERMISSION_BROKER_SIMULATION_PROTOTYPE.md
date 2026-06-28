# Phase 91A — Permission Broker Simulation Prototype

```
phase_name    = phase_91a_permission_broker_simulation_prototype
phase_version = 1.0
phase_status  = completed
implementation_status = simulation_only
recommended_next_phase = 91B — Broker CLI and Decision Explanation
```

## 1. Purpose

Implement a simulation-only permission broker decision model (`evaluate_permission_broker()`) as part of the Production v1 path. The broker evaluates proposed governed actions against a 4-outcome decision model (allow, deny, human_review, more_evidence) with explicit hard-block logic, reason codes, operator messages, and audit payloads.

## 2. Scope

In scope:

- `evaluate_permission_broker()` function with 4-outcome decision model
- 8 action types, 9 command classes, hard-block categories
- Hard-block non-overridability invariant (88V §16)
- Fail-closed behavior for unknown/malformed inputs
- Audit payload for every decision
- Comprehensive tests (55 new tests in `TestBrokerDecisionModel91A`)

Out of scope:

- CLI commands (deferred to 91B)
- Shell interception, wrappers, enforcement
- Backend invocation, prompt sending, command execution

## 3. Simulation-Only Boundary

The 91A broker is purely a decision function. It:

- **Evaluates** proposed action metadata (action_type, command_class, paths, task state, approval state, readiness state)
- **Returns** structured decisions with reason codes and audit payloads
- **Never** executes commands, intercepts shell, invokes backends, or grants authorization
- **Never** persists state, writes files, or modifies the repository

All invariant flags are unconditionally true/false:
- `simulation_only: true`
- `no_execution: true`
- `no_enforcement: true`
- `authorization_granted: false`
- `execution_authorized: false`

## 4. Input Model

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action_type` | str | Yes | One of 8 known actions: read, source_mutation, docs_mutation, test_mutation, backend_invocation, commit, push, rollback |
| `command_class` | str | No (default: unknown) | One of 9 command classes: read_only, governed, raw_git_commit, raw_git_push, force_push, no_verify, destructive_filesystem, backend_invocation, unknown |
| `paths` | tuple[str] | No | File paths affected by the action |
| `task_present` | bool | No (default: False) | Whether an active task contract exists |
| `task_scope_known` | bool | No (default: False) | Whether the task's file scope is known |
| `allowed_paths` | tuple[str] | No | Paths allowed by the task contract |
| `forbidden_paths` | tuple[str] | No | Paths forbidden by the task contract |
| `approval_present` | bool | No (default: False) | Whether human approval exists |
| `approval_fresh` | bool | No (default: True) | Whether approval is not expired/revoked |
| `accepted_risk_present` | bool | No (default: False) | Whether operator has accepted risk |
| `readiness_ready` | bool | No (default: False) | Whether enforcement readiness gates are satisfied |
| `enforcement_authorized` | bool | No (default: False) | Whether enforcement is explicitly authorized |
| `repo_dirty` | bool | No (default: False) | Whether working tree has uncommitted changes |
| `metadata` | dict | No | Reserved for future use |

## 5. Output Model

Every decision returns:

| Field | Type | Description |
|-------|------|-------------|
| `decision` | str | One of: allow, deny, human_review, more_evidence |
| `hard_block` | bool | True if the block is non-overridable (88V §16) |
| `reason_code` | str | Primary machine-readable reason |
| `reason_codes` | list[str] | All reason codes |
| `message` | str | Human-readable operator message |
| `required_evidence` | list[str] | Evidence items needed (empty for allow/deny) |
| `audit_payload` | dict | Audit-relevant fields (event_id, event_type, timestamp, decision, hard_block, overridable, reason_code, message_hash) |
| `simulation_only` | bool | Always true |
| `no_execution` | bool | Always true |
| `no_enforcement` | bool | Always true |
| `authorization_granted` | bool | Always false |
| `execution_authorized` | bool | Always false |
| `schema_version` | str | "1.0" |

## 6. Decision Semantics

### allow

All governance checks passed. The action would proceed to preflight. **Not execution authorization.** The operator retains full authority.

Triggers: read-only actions, governed actions with full evidence (task, scope, readiness, authorization), actions with fresh approval for commit/push.

### deny

Action is blocked. If `hard_block=true`, the block is permanent and non-overridable (88V §16).

Triggers: hard-block command classes (raw_git_commit, raw_git_push, force_push, no_verify, destructive_filesystem, unknown), out-of-scope paths, policy-forbidden files, task-forbidden paths, missing task for mutating actions, enforcement not ready/authorized for mutating actions.

### human_review

Action requires human review before proceeding. Not a hard block — providing valid, fresh approval allows the action.

Triggers: backend invocation, commit/push/rollback without approval, stale approval.

### more_evidence

Additional evidence is required before a decision can be made. The `required_evidence` field lists what's needed.

Triggers: unknown task scope, missing action_type, unknown action_type, dirty repo for commit/push.

## 7. Hard-Block Invariant

**88V §16 permanent invariant:** No human approval, accepted risk, or operator override can override a hard block.

The decision priority ensures hard blocks are evaluated first:
1. Validate inputs (missing/unknown → more_evidence or deny)
2. Hard-block command classes (checked before any evidence)
3. Enforcement readiness (checked before task contract)
4. Task contract (checked before path evaluation)
5. Path/scope (checked before human factors)
6. Backend invocation (requires human review)
7. Human review gates (commit, push, rollback)
8. All checks pass → allow

Human approval and accepted risk are checked only at step 7 — after all hard-block conditions are evaluated. A hard block at any earlier step returns `deny` immediately, never reaching the approval/risk check.

## 8. Fail-Closed Behavior

| Failure | Decision |
|---------|----------|
| Missing action_type | `more_evidence` |
| Unknown action_type | `more_evidence` |
| Unknown command_class | `deny` (hard_block=true) |
| Unknown task scope | `more_evidence` |
| Dirty repo for commit/push | `more_evidence` |

The broker never returns `allow` when:
- Any required input is missing or malformed
- The command class is unknown or ambiguous
- Task scope is unknown for a mutating action
- The repo is dirty for commit/push actions

## 9. Audit Payload Shape

Every decision includes an `audit_payload` dict:

```json
{
  "event_id": "evt-<uuid12>",
  "event_type": "enforcement.blocked|enforcement.allowed|enforcement.gated_review|enforcement.decision",
  "timestamp": "<ISO 8601>",
  "decision": "allow|deny|human_review|more_evidence",
  "hard_block": true|false,
  "overridable": true|false,
  "reason_code": "<primary reason>",
  "message_hash": "<sha256 prefix>",
  "required_evidence": ["..."]
}
```

The audit payload is simulation-only — it is not written to disk, not persisted, and not part of an audit chain. It exists to demonstrate what a future enforcement audit record would contain.

## 10. Relationship to 90A / 90C

| Artifact | Relationship |
|----------|-------------|
| **90A** — Enforcement Boundary Design | 91A implements the broker decision model defined in 90A §9 (broker responsibility, input/output contract). The 4-outcome model maps to 90A's 24 broker decisions through the hard-block classification layer. |
| **90C** — Enforcement Boundary Test Plan | 91A tests cover the categories defined in 90C: broker input model (§3), output model (§4), hard-block invariants (§5), human review (§6), fail-closed (§7), audit evidence (§8). |

## 11. What Remains for 91B

- CLI commands: `pcae broker check`, `pcae broker explain`, `pcae broker status`
- JSON output formatting
- Human-readable decision explanations
- Integration with the existing `build_permission_broker()` function
- `--help` documentation

## 12. Test Coverage

| Category | Tests |
|----------|-------|
| Allow (safe in-scope) | 3 |
| More evidence (unknown scope, missing inputs) | 4 |
| Hard-block (raw commit, push, force, no-verify, destructive) | 6 |
| Hard-block (out-of-scope, forbidden paths) | 3 |
| Human review (backend, commit, push, rollback) | 4 |
| Hard-block (missing task, enforcement readiness) | 4 |
| Hard-block (unknown command class) | 2 |
| Approval allows (non-hard-block) | 2 |
| Approval cannot override hard block | 6 |
| Accepted risk cannot override hard block | 3 |
| Stale approval | 1 |
| Audit payload | 4 |
| Simulation invariants | 6 |
| Messages, reason codes, evidence | 6 |
| Edge cases | 5 |
| **Total** | **55** |

---

*Phase 91A implements the simulation-only permission broker decision model as part of the Production v1 path. No enforcement, shell interception, wrappers, backend invocation, or command execution was implemented. All simulation invariants are preserved. Recommended next phase: 91B — Broker CLI and Decision Explanation.*
