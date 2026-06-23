# Multi-Agent Task Split Dry-Run

## Purpose

Simulate how PCAE would split hypothetical tasks across multiple agents, including role assignment, dependencies, approval boundaries, guard requirements, output intake, and merge/adoption constraints. This is a documentation-only dry-run — no real splitting, routing, or invocation occurs.

## Scope

Evaluate 10 hypothetical scenarios against the known backend inventory, safety profiles, and routing constraints. Produce advisory split plans only.

## Non-Goals

- Real multi-agent routing or task assignment.
- Backend or subagent invocation.
- Prompt sending.
- Repository modification by agents.
- Implementation of split commands.

## Input Artifacts

| Artifact | Phase |
|----------|-------|
| Agent Capability Registry Design | 82A |
| Agent Identity Capability Probe | 82B |
| Subagent Discovery Contract | 82C |
| Subagent Safety Profile | 82D |
| Agent Routing Dry-Run | 82E |

## Multi-Agent Split Principles

1. **One adoption path at a time.** Only one agent's output may be in the adoption pipeline at any moment.
2. **Executor and reviewer must be separate.** The agent that produces output cannot approve its own adoption.
3. **Each subtask requires its own contract.** No implicit task delegation.
4. **Each agent invocation requires approval.** No auto-routing.
5. **Output from every agent goes through intake.** No trusted agent bypass.
6. **Merge conflicts are resolved by human, not agent.** Agents may suggest; humans decide.
7. **Commit and push remain single-path.** Even with multiple agents, only one governed commit/push sequence at a time.

## Known Agent Inventory

| Agent | Available | Proven | Candidate Roles |
|-------|-----------|--------|-----------------|
| claude | yes | yes | planner, executor, reviewer, doc reviewer |
| claude-deepseek | yes (wrapper) | yes | alternate executor, reviewer |
| claude-kimi | no | no | blocked |
| codex | yes | no | blocked (unverified) |
| subagents | N/A | no | blocked (discovery pending) |

## Role Model

| Role | Description | Risk | Min Agents |
|------|-------------|------|------------|
| planner | Decomposes task into subtasks | low | 1 |
| primary_executor | Produces the main output | varies | 1 |
| reviewer | Reviews executor output for correctness | medium | 1 (must differ from executor) |
| test_reviewer | Reviews test implications | medium | 1 |
| safety_reviewer | Reviews for governance/security issues | high trust | 1 (must differ from executor) |
| documentation_reviewer | Reviews documentation output | low | 1 |
| adoption_reviewer | Reviews output before adoption into repo | medium | 1 (must differ from executor) |
| commit_reviewer | Approves the governed commit | N/A | human operator |
| push_reviewer | Approves the governed push | N/A | human operator |

Commit and push reviewers are always human operators, never agents.

## Task Decomposition Model

Each scenario decomposes into subtasks with:

| Field | Description |
|-------|-------------|
| subtask_id | Unique identifier |
| subtask_type | planning, execution, review, etc. |
| assigned_role | Role from the role model |
| candidate_agent | Agent eligible for this role |
| depends_on | Subtask dependencies |
| approval_required | Whether operator approval is needed |
| output_type | stdout, patch, file, suggestion |
| intake_required | Whether output goes through intake |

## Dependency Model

Subtasks follow a directed acyclic graph:

```
plan -> execute -> review -> adopt -> commit -> push -> verify
                     ^
                     |
              test_review (parallel with review)
```

No subtask may begin until its dependencies are complete and their outputs are reviewed.

## Hypothetical Scenarios

### 1. documentation_update

| Subtask | Role | Agent | Status |
|---------|------|-------|--------|
| Plan doc change | planner | claude | candidate |
| Draft documentation | primary_executor | claude | candidate |
| Review draft | reviewer | claude-deepseek | candidate |
| Adopt into repo | adoption_reviewer | human | required |

**Result:** simulated_candidate_split — two agents can collaborate with human adoption gate.

### 2. documentation_review

| Subtask | Role | Agent | Status |
|---------|------|-------|--------|
| Review existing docs | reviewer | claude | candidate |
| Second opinion | reviewer | claude-deepseek | candidate |

**Result:** simulated_candidate_split — parallel review, no execution needed.

### 3. code_change_with_review

| Subtask | Role | Agent | Status |
|---------|------|-------|--------|
| Plan change | planner | claude | candidate |
| Generate code | primary_executor | claude-deepseek | blocked (high risk, no approval) |
| Review code | reviewer | claude | blocked (executor not yet invoked) |

**Result:** blocked_high_risk — code generation requires full governance chain not yet approved.

### 4. test_failure_investigation

| Subtask | Role | Agent | Status |
|---------|------|-------|--------|
| Analyze failure | test_reviewer | claude | candidate |
| Suggest fix | primary_executor | claude-deepseek | blocked (high risk) |

**Result:** blocked_high_risk — analysis is candidate, but fix generation requires governance chain.

### 5. refactor_with_review

| Subtask | Role | Agent | Status |
|---------|------|-------|--------|
| Plan refactor | planner | claude | candidate |
| Execute refactor | primary_executor | any | blocked (high risk) |
| Review refactor | reviewer | any | blocked (depends on execution) |

**Result:** blocked_high_risk — planning is candidate, but execution requires full governance.

### 6. backend_capture_with_review

| Subtask | Role | Agent | Status |
|---------|------|-------|--------|
| Capture output | primary_executor | claude or claude-deepseek | candidate (via lifecycle) |
| Review output | reviewer | alternate agent | candidate |
| Adopt output | adoption_reviewer | human | required |

**Result:** simulated_candidate_split — proven pattern from 77J-77V.1 and 81A-81I lifecycles.

### 7. multi_agent_design_review

| Subtask | Role | Agent | Status |
|---------|------|-------|--------|
| Primary review | reviewer | claude | candidate |
| Secondary review | reviewer | claude-deepseek | candidate |
| Synthesize findings | planner | claude | candidate |

**Result:** simulated_candidate_split — all read-only review roles.

### 8. security_sensitive_change

| Subtask | Role | Agent | Status |
|---------|------|-------|--------|
| Plan change | planner | claude | blocked (high risk) |
| Execute change | primary_executor | any | blocked (high risk) |
| Security review | safety_reviewer | any | blocked (depends on execution) |

**Result:** blocked_high_risk — security-sensitive work requires the highest governance scrutiny.

### 9. dependency_update

| Subtask | Role | Agent | Status |
|---------|------|-------|--------|
| Plan update | planner | claude | candidate |
| Execute update | primary_executor | any | blocked (high risk, dependency change) |

**Result:** blocked_high_risk — dependency changes blocked by default.

### 10. shell_required_task

| Subtask | Role | Agent | Status |
|---------|------|-------|--------|
| Any subtask requiring shell | primary_executor | any | blocked |

**Result:** blocked_high_risk — no agent has per-invocation shell approval.

## Agent Assignment Matrix

| Scenario | claude | claude-deepseek | claude-kimi | codex | subagents |
|----------|--------|-----------------|-------------|-------|-----------|
| documentation_update | planner+executor | reviewer | blocked | blocked | blocked |
| documentation_review | reviewer | reviewer | blocked | blocked | blocked |
| code_change_with_review | planner only | blocked | blocked | blocked | blocked |
| test_failure_investigation | analyst only | blocked | blocked | blocked | blocked |
| refactor_with_review | planner only | blocked | blocked | blocked | blocked |
| backend_capture_with_review | executor or reviewer | executor or reviewer | blocked | blocked | blocked |
| multi_agent_design_review | reviewer | reviewer | blocked | blocked | blocked |
| security_sensitive_change | blocked | blocked | blocked | blocked | blocked |
| dependency_update | planner only | blocked | blocked | blocked | blocked |
| shell_required_task | blocked | blocked | blocked | blocked | blocked |

## Approval Requirements

Every multi-agent split requires:

| Requirement | Scope |
|-------------|-------|
| Task contract per subtask | Each subtask gets its own contract |
| Operator approval per agent invocation | Each invocation requires sign-off |
| Prompt capture per invocation | All prompts logged |
| Mutation guard per invocation | Pre/post git status for each |
| Output intake per agent | Each output classified before use |
| Adoption review | Human reviews before repo adoption |
| Commit approval | Human approves commit |
| Push approval | Human approves push |

## Guard Requirements

| Guard | When |
|-------|------|
| Mutation guard | Before and after every agent invocation |
| Output intake | After every agent invocation |
| Conflict detection | Before merging outputs from multiple agents |
| Adoption review | Before any output enters the repo |
| Content safety scan | Before adoption of any agent output |

## Conflict / Merge Handling

If multiple agents produce output touching the same area:

1. Each output is captured and reviewed independently.
2. Conflicts are identified during adoption review.
3. Human operator resolves conflicts — agents may suggest but cannot decide.
4. Only one resolved output enters the adoption pipeline at a time.
5. No automatic merge.

## Adoption Constraints

- Only one adoption path modifies the repository at a time.
- Adoption follows the full governed lifecycle (intake -> review -> approve -> execute -> commit -> push -> verify).
- Multi-agent output does not bypass any gate.
- Staged-file-aware commands (79A-79C) are available for safe commit/push during multi-agent work.

## Commit / Push Constraints

- Commit and push remain single-path operations.
- Multiple agent outputs are serialized through the adoption pipeline, not parallelized.
- Each commit requires separate approval.
- Each push requires separate approval.
- No force push. No raw push.

## Blocked Cases Summary

| Case | Reason |
|------|--------|
| claude-kimi in any role | Missing from PATH |
| codex in any role | Available but unverified |
| Any subagent in any role | Discovery not performed |
| Code execution by any agent | High risk, no pre-approved governance chain |
| Shell execution by any agent | Blocked by default |
| Security-sensitive work | Requires highest governance scrutiny |
| Dependency changes | Blocked by default |
| Automatic merge of multi-agent output | Forbidden; human resolution required |

## Recommended Future Implementation Model

A future `pcae agent split` or `pcae task split` command should:

1. Accept a task description and decomposition hints.
2. Consult the registry and safety profiles.
3. Propose subtask assignments as advisory recommendations.
4. Require operator approval for each assignment.
5. Track subtask dependencies and completion.
6. Serialize adoption through the governed lifecycle.
7. Never auto-execute, auto-merge, or auto-push.

This command is not implemented in 82F.

## Failure Modes

| Failure | Handling |
|---------|----------|
| No eligible agent for a subtask | Block subtask, report to operator |
| Agent produces conflicting output | Quarantine both, require human merge |
| Agent exceeds subtask scope | Quarantine output, block adoption |
| Dependency cycle in subtasks | Reject split plan |
| Stale agent verification | Block routing for that agent |

## Safety Conclusion

- No real multi-agent task split occurred.
- No real routing occurred.
- No backend or subagent was invoked.
- No prompts were sent.
- No repository mutation occurred.
- No adoption was authorized.
- No commit was authorized.
- No push was authorized.
- All future multi-agent work requires explicit task contracts, role separation, prompt capture, mutation guard, output intake, adoption review, commit approval, and push approval per subtask and per agent.

## Dry-Run Status

| Field | Value |
|-------|-------|
| multi_agent_task_split_dry_run_status | completed |
| split_simulation_only | true |
| real_task_split_performed | false |
| real_routing_performed | false |
| backend_invocation_performed | false |
| subagent_invocation_performed | false |
| prompts_sent | false |
| repo_mutation_by_agent | false |
| routing_authorized | false |
| execution_authorized | false |
| adoption_authorized | false |
| commit_authorized | false |
| push_authorized | false |

## Recommended Next Phase

**83A — Multi-Agent Task Contract** (per roadmap)

83A should define the formal contract model for multi-agent tasks, building on the split model from 82F and the governance constraints from 82A-82E. The 82 stream (agent capability discovery) is now complete.
