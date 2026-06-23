# Multi-Agent Contract Instance Dry-Run

## Purpose

Instantiate a draft multi-agent contract for a documentation-review task using the approved 83B assignment model. This is a dry-run only — no routing, prompts, invocation, or execution occurs.

## Scope

Create and validate a draft contract instance. Prove that contract fields, role assignments, and validation rules work. Do not execute the contract.

## Non-Goals

- Real routing or task assignment.
- Backend or subagent invocation.
- Prompt sending.
- Task execution.
- Repository modification by agents.
- Machine-readable contract artifact creation.

## Source Design Artifacts

| Artifact | Phase |
|----------|-------|
| Multi-Agent Task Contract Design | 83A |
| Agent Assignment Approval | 83B |
| Agent Routing Dry-Run | 82E |
| Multi-Agent Task Split Dry-Run | 82F |
| Agent Capability Registry Design | 82A |
| Agent Identity Capability Probe | 82B |

## Approved Assignment Source

`docs/AGENT_ASSIGNMENT_APPROVAL.md` (Phase 83B)

## Draft Contract

### Identity

| Field | Value |
|-------|-------|
| contract_id | MULTI-AGENT-DRY-RUN-001 |
| task_title | Review PCAE multi-agent documentation for consistency |
| task_type | documentation_review |
| risk_level | medium |
| created_at | 2026-06-23 |
| created_by | Phase 83C |
| parent_task | none |
| status | draft |

### Agent Inventory

| Agent | Available | Proven | Assigned |
|-------|-----------|--------|----------|
| claude-local | yes | yes | planner |
| claude-deepseek | yes | yes | documentation_reviewer |
| claude-kimi | no | no | blocked |
| codex | yes | no | blocked |
| subagents | N/A | no | blocked |

### Role Assignments

| Role | Assigned To | Risk | Operations |
|------|-------------|------|------------|
| planner | claude-local | low | plan, summarize |
| documentation_reviewer | claude-deepseek | low | review, generate_suggestions |
| adoption_reviewer | human/operator | N/A | adopt_output (governance) |
| commit_reviewer | human/operator | N/A | commit_changes (governance) |
| push_reviewer | human/operator | N/A | push_changes (governance) |

### Role Separation Checks

| Check | Result |
|-------|--------|
| Planner (claude-local) differs from reviewer (claude-deepseek) | PASS |
| Adoption reviewer is human/operator | PASS |
| Commit reviewer is human/operator | PASS |
| Push reviewer is human/operator | PASS |
| No agent assigned commit authority | PASS |
| No agent assigned push authority | PASS |
| No role can self-approve | PASS |
| Planner cannot auto-approve its own plan execution | PASS |

### Allowed Operations

- plan
- review
- summarize
- generate_suggestions

### Forbidden Operations

- write_source
- write_tests
- write_files
- run_shell
- generate_patch
- adopt_output (by agent)
- commit_changes (by agent)
- push_changes (by agent)
- force_push
- raw_git_push
- modify_docs_directly_by_agent

### Allowed Files (review context)

- `docs/AGENT_CAPABILITY_REGISTRY_DESIGN.md`
- `docs/AGENT_IDENTITY_CAPABILITY_PROBE.md`
- `docs/SUBAGENT_DISCOVERY_CONTRACT.md`
- `docs/SUBAGENT_SAFETY_PROFILE.md`
- `docs/AGENT_ROUTING_DRY_RUN.md`
- `docs/MULTI_AGENT_TASK_SPLIT_DRY_RUN.md`
- `docs/MULTI_AGENT_TASK_CONTRACT.md`
- `docs/AGENT_ASSIGNMENT_APPROVAL.md`

### Forbidden Files

- `src/**`
- `tests/**`
- `.pcae/**`
- `.githooks/**`
- `docs/REAL_CAPTURED_TASKS.md`
- `pyproject.toml`

### Expected Outputs (future, not generated in 83C)

| Role | Output |
|------|--------|
| planner | Planning summary: documentation review scope and subtasks |
| documentation_reviewer | Review notes: consistency findings, governance boundary accuracy, suggested improvements |
| adoption_reviewer | Adoption decision (human) |
| commit_reviewer | Commit approval (human) |
| push_reviewer | Push approval (human) |

No outputs are generated in Phase 83C.

### Handoff Points

| Handoff | From | To | Artifact | Approval |
|---------|------|----|----------|----------|
| H1 | planner | documentation_reviewer | Planning summary | Required |
| H2 | documentation_reviewer | adoption_reviewer | Review notes | Required |
| H3 | adoption_reviewer | commit_reviewer | Adoption decision | Required |
| H4 | commit_reviewer | push_reviewer | Commit confirmation | Required |

### Required Future Approvals

| Approval | Required | Who |
|----------|----------|-----|
| Routing approval | yes | Operator |
| Prompt/invocation approval per agent | yes | Operator |
| Output intake approval | yes | Operator |
| Adoption approval | yes | Operator |
| Commit approval | yes | Operator |
| Push approval | yes | Operator |

### Required Future Guards

| Guard | Required |
|-------|----------|
| Parent agent lock | yes |
| Prompt capture | yes |
| Mutation guard (pre/post) | yes |
| Output capture | yes |
| Output intake classification | yes |
| Human review | yes |
| No auto-apply | yes |
| No auto-commit | yes |
| No auto-push | yes |

### Prompt Capture Requirements

All prompts sent to assigned agents must be captured and logged before sending. This applies to both planner and documentation_reviewer invocations.

### Output Intake Requirements

All agent output must be captured, classified, and reviewed before any adoption consideration. No auto-apply.

### Adoption / Commit / Push Boundaries

- Adoption requires human review and explicit approval.
- Commit requires separate human approval.
- Push requires separate human approval via governed `pcae push`.
- No agent may perform adoption, commit, or push.

## Contract Validation Checklist

| # | Check | Result |
|---|-------|--------|
| 1 | All assigned agents known from 82B probe | PASS |
| 2 | claude-local is available and proven | PASS |
| 3 | claude-deepseek is available and proven | PASS |
| 4 | claude-kimi is not assigned | PASS |
| 5 | codex is not assigned | PASS |
| 6 | Subagents are not assigned | PASS |
| 7 | Planner and reviewer are distinct agents | PASS |
| 8 | Adoption/commit/push reviewers are human | PASS |
| 9 | No agent has commit authority | PASS |
| 10 | No role self-approves | PASS |
| 11 | routing_authorized=false | PASS |
| 12 | execution_authorized=false | PASS |
| 13 | backend_invocation_authorized=false | PASS |
| 14 | prompts_authorized=false | PASS |
| 15 | adoption_authorized=false | PASS |
| 16 | commit_authorized=false | PASS |
| 17 | push_authorized=false | PASS |
| 18 | Allowed files do not overlap forbidden files | PASS |
| 19 | Source/test files are forbidden | PASS |
| 20 | Mutation guard required for future invocation | PASS |

**Validation: 20/20 checks passed.**

## Blockers / Warnings

**Blockers:** none for this dry-run contract instance.

**Warnings:**
- Contract is in draft status and does not authorize any execution.
- Future routing approval phase is required before any agent invocation.

## Authorization Flags

| Flag | Value |
|------|-------|
| contract_instance_created | true |
| routing_authorized | false |
| backend_invocation_authorized | false |
| subagent_invocation_authorized | false |
| prompts_authorized | false |
| execution_authorized | false |
| adoption_authorized | false |
| commit_authorized | false |
| push_authorized | false |
| repo_mutation_authorized | false |

## Dry-Run Outcome

| Field | Value |
|-------|-------|
| multi_agent_contract_instance_dry_run_status | created |
| contract_instance_status | draft |
| validation_result | valid_draft_not_authorized |

## Safety Conclusion

- This is a draft contract instance only.
- No real routing occurred.
- No backend or subagent was invoked.
- No prompts were sent.
- No task execution occurred.
- No repository mutation occurred.
- No adoption, commit, or push is authorized.
- Future execution requires a separate routing approval and invocation approval phase.

## Recommended Next Phase

**83D — Multi-Agent Routing Approval**

83D should approve or reject routing for this draft contract instance, still without invoking agents unless explicitly scoped in a later invocation phase.
