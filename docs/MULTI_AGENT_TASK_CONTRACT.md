# Multi-Agent Task Contract Design

## Purpose

Define a formal contract format for PCAE multi-agent tasks: task identity, role assignments, allowed agents, allowed operations, handoff points, review boundaries, approval requirements, mutation/output handling, adoption/commit/push boundaries, and closure requirements.

## Scope

This design defines the contract data model and validation rules. It does not implement parsers, CLI commands, or multi-agent execution.

## Non-Goals

- Contract parsing or validation code (future phase).
- Real multi-agent routing or task splitting.
- Backend or subagent invocation.
- Automatic contract approval.

## Relationship to Existing PCAE Task Contracts

Single-agent PCAE task contracts (used since Phase 69) define allowed files, forbidden files, acceptance criteria, and enforcement mode for one task and one agent. The multi-agent task contract extends this with role assignments, agent eligibility, handoff points, and per-role governance requirements.

## Relationship to Agent Capability Registry

The registry (82A) provides the agent inventory. The contract references agents by `agent_id` and validates against the registry's enabled/verified status.

## Relationship to Routing Dry-Run

The routing dry-run (82E) evaluated which agents are candidates for which task types. The contract binds specific agents to specific roles for a specific task instance.

## Relationship to Subagent Discovery / Safety Profile

Subagents (82C/82D) are assigned through the same role model but require parent agent lock and discovery verification. Subagent roles inherit the parent's safety baseline unless the contract specifies stricter constraints.

## Multi-Agent Contract Principles

1. **Descriptive until approved.** A contract describes intended work; it does not authorize it.
2. **Explicit role separation.** Executor and reviewer must be different agents or humans.
3. **One adoption path.** Only one agent's output enters the adoption pipeline at a time.
4. **No self-approval.** No agent can approve its own output for adoption, commit, or push.
5. **Commit and push are human operations.** No agent may commit or push.
6. **Contract expires.** Stale contracts must be re-validated.

## Contract Lifecycle

```
draft -> validated -> approved -> active -> completed -> closed
                                    |
                                    v
                                 blocked
```

- **draft:** Contract fields populated but not yet validated.
- **validated:** All fields pass validation rules.
- **approved:** Operator has approved the contract for future execution.
- **active:** Subtasks are being executed under governance.
- **completed:** All subtasks finished, outputs reviewed.
- **closed:** Adoption/commit/push completed, contract archived.
- **blocked:** Validation failure, agent unavailable, or policy violation.

## Required Contract Fields

| Field | Type | Description |
|-------|------|-------------|
| `contract_id` | string | Unique identifier |
| `task_title` | string | Human-readable title |
| `task_type` | string | planning_only, documentation_only, code_review, etc. |
| `risk_level` | string | low, medium, high |
| `created_at` | string | ISO timestamp |
| `created_by` | string | Operator or phase that created the contract |
| `parent_task` | string/null | Parent task ID if this is a subtask |
| `allowed_agents` | list[string] | Agent IDs eligible for this contract |
| `forbidden_agents` | list[string] | Agent IDs explicitly excluded |
| `roles` | list[Role] | Role definitions (see below) |
| `role_assignments` | dict | role_id -> agent_id mapping |
| `allowed_operations` | list[string] | Operations permitted |
| `forbidden_operations` | list[string] | Operations explicitly blocked |
| `allowed_files` | list[string] | File paths the contract may touch |
| `forbidden_files` | list[string] | File paths that must not be touched |
| `expected_outputs` | list[string] | What each role should produce |
| `handoff_points` | list[Handoff] | Where work transfers between roles |
| `review_requirements` | dict | Per-role review requirements |
| `approval_requirements` | dict | Per-boundary approval needs |
| `prompt_capture_required` | boolean | Whether prompts must be logged |
| `mutation_guard_required` | boolean | Whether pre/post git status is needed |
| `output_intake_required` | boolean | Whether output must be classified |
| `adoption_review_required` | boolean | Whether adoption needs human review |
| `commit_approval_required` | boolean | Whether commit needs explicit approval |
| `push_approval_required` | boolean | Whether push needs explicit approval |
| `execution_authorized` | boolean | Always false at creation |
| `routing_authorized` | boolean | Always false at creation |
| `expires_at` | string/null | Staleness expiration |
| `status` | string | Current contract status |

## Role Assignment Model

Each role record:

| Field | Type | Description |
|-------|------|-------------|
| `role_id` | string | Unique role identifier |
| `role_type` | string | planner, primary_executor, reviewer, etc. |
| `assigned_agent_id` | string | Agent assigned to this role |
| `risk_level` | string | Risk level for this role's operations |
| `allowed_operations` | list[string] | What this role may do |
| `allowed_files` | list[string] | Files this role may touch |
| `forbidden_files` | list[string] | Files this role must not touch |
| `requires_prompt_capture` | boolean | Prompt must be logged |
| `requires_output_intake` | boolean | Output must be classified |
| `requires_human_review` | boolean | Human reviews this role's output |
| `may_modify_repo` | boolean | Default false |
| `may_run_shell` | boolean | Default false |
| `may_commit` | boolean | Always false |
| `may_push` | boolean | Always false |

### Role Types

| Type | Description | Can Self-Approve |
|------|-------------|-----------------|
| planner | Decomposes task | No |
| primary_executor | Produces main output | No |
| reviewer | Reviews executor output | No (cannot review own output) |
| test_reviewer | Reviews test implications | No |
| safety_reviewer | Reviews governance/security | No |
| documentation_reviewer | Reviews documentation | No |
| adoption_reviewer | Reviews before repo adoption | No (must differ from executor) |
| commit_reviewer | Approves commit | Human only |
| push_reviewer | Approves push | Human only |

### Role Separation Rules

- `primary_executor` cannot be `adoption_reviewer` for its own output.
- `primary_executor` cannot be `commit_reviewer` or `push_reviewer`.
- `planner` cannot auto-approve execution of its own plan.
- `safety_reviewer` cannot be bypassed for high-risk work.
- `commit_reviewer` and `push_reviewer` are human/governance roles.
- No role can grant itself new authority.

## Agent Eligibility Model

An agent is eligible for a contract role when:

1. Agent is in the capability registry with `enabled=true`.
2. Agent's `last_verified_at` is within staleness threshold.
3. Agent's safety profile allows the role's risk level.
4. Agent is in the contract's `allowed_agents` list.
5. Agent is not in the contract's `forbidden_agents` list.
6. Agent has capabilities matching the role's `allowed_operations`.
7. Role separation rules are satisfied.

## Allowed Operations Model

| Operation | Description | Risk |
|-----------|-------------|------|
| plan | Create a plan/decomposition | low |
| review | Review existing content | low-medium |
| summarize | Summarize content | low |
| generate_suggestions | Produce advisory suggestions | low-medium |
| generate_patch | Produce a structured patch | medium |
| capture_output | Serve as a capture target | governed |
| write_docs | Generate documentation | medium |
| write_tests | Generate test code | high |
| write_source | Generate production code | high |
| run_tests | Execute test suite | high |
| run_shell | Execute shell commands | high |
| adopt_output | Adopt output into repo | governed (human) |
| commit_changes | Create a git commit | governed (human) |
| push_changes | Push to remote | governed (human) |

Operations `adopt_output`, `commit_changes`, and `push_changes` are governance operations performed by PCAE under human approval, not by agents.

## File Scope Model

- `allowed_files`: paths the contract permits modifications to.
- `forbidden_files`: paths that must never be modified (e.g., `docs/REAL_CAPTURED_TASKS.md`, `src/**` for doc-only contracts).
- Per-role `allowed_files` must be a subset of the contract's `allowed_files`.
- Overlap between `allowed_files` and `forbidden_files` invalidates the contract.

## Handoff Model

Each handoff:

| Field | Type | Description |
|-------|------|-------------|
| `handoff_id` | string | Unique identifier |
| `from_role` | string | Role handing off |
| `to_role` | string | Role receiving |
| `artifact` | string | What is being handed off |
| `required_checks` | list[string] | Checks before handoff proceeds |
| `approval_required` | boolean | Operator approval needed |
| `blocking_conditions` | list[string] | Conditions that block handoff |

## Review and Approval Boundaries

| Boundary | Approval | Who |
|----------|----------|-----|
| Routing approval | Required per contract | Operator |
| Invocation approval | Required per agent per subtask | Operator |
| Mutation approval | If mutation guard triggers | Operator |
| Adoption approval | Required before repo modification | Operator |
| Commit approval | Required | Operator (human) |
| Push approval | Required | Operator (human) |
| Lifecycle closure | Required | Operator |

## Prompt Capture Requirements

- Low risk: recommended.
- Medium risk: required.
- High risk: required + reviewed before send.

## Mutation Guard Requirements

- Required for every agent invocation that may touch the repository.
- Pre/post git status comparison.
- Unexpected mutation triggers quarantine.

## Output Intake Requirements

- Required for every agent invocation.
- Output classified before adoption.
- No auto-apply.

## Adoption Boundaries

- Only one agent's output in the adoption pipeline at a time.
- Adoption follows the full governed lifecycle.
- Multi-agent outputs are serialized, not parallelized for adoption.

## Commit Boundaries

- Each commit requires separate human approval.
- No agent may create commits.
- Staged-file-aware commands (79A-79C) are available.

## Push Boundaries

- Each push requires separate human approval.
- No agent may push.
- Governed `pcae push` only.

## Failure / Blocking Conditions

| Condition | Result |
|-----------|--------|
| Unknown agent assigned | Contract invalid |
| Missing safety profile | Contract invalid |
| Role separation violated | Contract invalid |
| High-risk work without safety_reviewer | Contract invalid |
| Commit/push assigned to agent | Contract invalid |
| `execution_authorized=true` without approval | Contract invalid |
| `routing_authorized=true` without routing approval | Contract invalid |
| `allowed_files` overlaps `forbidden_files` | Contract invalid |
| Forbidden agent assigned a role | Contract invalid |
| Stale capability/discovery data | Contract blocked |
| Missing prompt capture for medium/high risk | Contract blocked |
| Missing mutation guard | Contract blocked |
| Missing output intake | Contract blocked |

## Contract Validation Rules

1. All `allowed_agents` must be in the registry with `enabled=true`.
2. All `role_assignments` must reference agents in `allowed_agents`.
3. No agent in `forbidden_agents` may appear in `role_assignments`.
4. Role separation rules must be satisfied.
5. `execution_authorized` must be `false` at contract creation.
6. `routing_authorized` must be `false` at contract creation.
7. `may_commit` must be `false` for all agent roles.
8. `may_push` must be `false` for all agent roles.
9. `allowed_files` and `forbidden_files` must not overlap.
10. High-risk contracts must include a `safety_reviewer` role.
11. `prompt_capture_required` must be `true` for medium/high risk.
12. `mutation_guard_required` must be `true`.
13. `output_intake_required` must be `true`.

## Example Contract

```json
{
  "contract_id": "MAC-003",
  "task_title": "Multi-agent documentation review",
  "task_type": "documentation_review",
  "risk_level": "low",
  "created_at": "2026-06-23T00:00:00Z",
  "created_by": "Phase 83A (design example)",
  "allowed_agents": ["claude-local", "claude-deepseek"],
  "forbidden_agents": ["codex"],
  "roles": [
    {
      "role_id": "planner-1",
      "role_type": "planner",
      "assigned_agent_id": "claude-local",
      "allowed_operations": ["plan", "summarize"],
      "may_modify_repo": false,
      "may_commit": false,
      "may_push": false
    },
    {
      "role_id": "reviewer-1",
      "role_type": "documentation_reviewer",
      "assigned_agent_id": "claude-deepseek",
      "allowed_operations": ["review", "generate_suggestions"],
      "may_modify_repo": false,
      "may_commit": false,
      "may_push": false
    }
  ],
  "allowed_files": ["docs/ROADMAP.md"],
  "forbidden_files": ["src/**", "tests/**", "docs/REAL_CAPTURED_TASKS.md"],
  "prompt_capture_required": true,
  "mutation_guard_required": true,
  "output_intake_required": true,
  "adoption_review_required": true,
  "commit_approval_required": true,
  "push_approval_required": true,
  "execution_authorized": false,
  "routing_authorized": false,
  "status": "draft"
}
```

This is a design example only. No real contract artifact is created in 83A.

## Future Implementation Phases

| Phase | Description |
|-------|-------------|
| 83B | Agent Assignment Approval |
| 83C | Parallel Prompt Package Dry-Run |
| 83D | Multi-Agent Capture |
| 83E | Multi-Agent Output Intake |
| 83F | Conflict Detection |
| 83G | Merge Review |
| 83H | Single Approved Adoption Path |

## Design Conclusion

The multi-agent task contract ensures that multi-agent work in PCAE is governed by the same principles as single-agent work: explicit contracts, role separation, approval gates, mutation guards, output intake, and serialized adoption. Contract creation is descriptive — it does not authorize routing, invocation, execution, adoption, commit, or push. Each of those boundaries requires its own explicit approval in a future governed phase.
