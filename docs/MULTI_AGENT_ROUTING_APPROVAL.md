# Multi-Agent Routing Approval

## Purpose

Approve future routing for the draft multi-agent contract MULTI-AGENT-DRY-RUN-001, authorizing PCAE to proceed to a later phase that prepares prompt/invocation approval for the approved route. This approval does not authorize backend invocation, prompt sending, execution, adoption, commit, or push.

## Scope

Routing approval only for one specific draft contract instance with known, proven, identity-separated agents in documentation-review roles. All later governance boundaries are preserved.

## Non-Goals

- Backend invocation of any agent.
- Prompt sending to any agent.
- Task execution by any agent.
- Repository mutation by any agent.
- Adoption of any agent output.
- Commit or push authorization.
- Source code or test changes.
- Subagent invocation or discovery probing.
- Implementation of routing commands or contract parsers.

## Input Artifacts

| Artifact | Phase | Path |
|----------|-------|------|
| Agent Capability Registry Design | 82A | `docs/AGENT_CAPABILITY_REGISTRY_DESIGN.md` |
| Agent Identity Capability Probe | 82B | `docs/AGENT_IDENTITY_CAPABILITY_PROBE.md` |
| Subagent Discovery Contract | 82C | `docs/SUBAGENT_DISCOVERY_CONTRACT.md` |
| Subagent Safety Profile | 82D | `docs/SUBAGENT_SAFETY_PROFILE.md` |
| Agent Routing Dry-Run | 82E | `docs/AGENT_ROUTING_DRY_RUN.md` |
| Multi-Agent Task Split Dry-Run | 82F | `docs/MULTI_AGENT_TASK_SPLIT_DRY_RUN.md` |
| Multi-Agent Task Contract Design | 83A | `docs/MULTI_AGENT_TASK_CONTRACT.md` |
| Agent Assignment Approval | 83B | `docs/AGENT_ASSIGNMENT_APPROVAL.md` |
| Multi-Agent Contract Instance Dry-Run | 83C | `docs/MULTI_AGENT_CONTRACT_INSTANCE_DRY_RUN.md` |

## Approved Contract ID

| Field | Value |
|-------|-------|
| contract_id | MULTI-AGENT-DRY-RUN-001 |
| contract_source | `docs/MULTI_AGENT_CONTRACT_INSTANCE_DRY_RUN.md` |
| contract_status | draft |
| contract_validation_result | valid_draft_not_authorized |
| contract_validation_checks | 20/20 passed |

## Approved Task Type

| Field | Value |
|-------|-------|
| task_type | documentation_review |
| risk_level | medium |
| task_title | Review PCAE multi-agent documentation for consistency |

## Approved Route

| Field | Value |
|-------|-------|
| route_type | documentation_review |
| route_scope | review and planning only |
| route_direction | claude-local (planner) -> claude-deepseek (reviewer) -> human/operator (governance) |
| allowed_operations | plan, review, summarize, generate_suggestions |
| forbidden_operations | write_source, write_tests, write_files, run_shell, generate_patch, adopt_output (by agent), commit_changes (by agent), push_changes (by agent), force_push, raw_git_push, modify_docs_directly_by_agent |

## Approved Agents and Roles

| Role | Assigned To | Agent Status | Risk | Justification |
|------|-------------|-------------|------|---------------|
| planner | claude-local | available, proven (81D, 77F) | low | Two governed lifecycle completions, low risk for planning |
| documentation_reviewer | claude-deepseek | available, proven (77F) | low | Proven in first lifecycle, identity-separated from claude-local |
| adoption_reviewer | human/operator | N/A | N/A | Governance role, human only |
| commit_reviewer | human/operator | N/A | N/A | Governance role, human only |
| push_reviewer | human/operator | N/A | N/A | Governance role, human only |

## Blocked Agents

| Agent | Status | Reason |
|-------|--------|--------|
| claude-kimi | blocked | Missing from PATH (82B probe) |
| codex | blocked | Available but unverified for PCAE governance (82B probe) |
| subagents | blocked | Discovery not performed (82C contract defined, probes not executed) |
| unknown agents | disabled | Disabled by default per registry policy (82A/82D) |

No blocked agent may be routed work, invoked, or sent prompts under this approval.

## Routing Validation Checks

| # | Check | Result |
|---|-------|--------|
| 1 | Contract ID is MULTI-AGENT-DRY-RUN-001 | PASS |
| 2 | Contract status is draft | PASS |
| 3 | Contract validation result is valid_draft_not_authorized | PASS |
| 4 | Task type is documentation_review | PASS |
| 5 | Risk level is medium | PASS |
| 6 | claude-local is known and available/proven | PASS |
| 7 | claude-deepseek is known and available/proven | PASS |
| 8 | claude-kimi is blocked because missing | PASS |
| 9 | codex is blocked because unverified | PASS |
| 10 | subagents are blocked because discovery pending | PASS |
| 11 | unknown agents are disabled | PASS |
| 12 | planner and documentation_reviewer are distinct | PASS |
| 13 | human/operator owns adoption/commit/push review | PASS |
| 14 | no agent has commit authority | PASS |
| 15 | no agent has push authority | PASS |
| 16 | no role self-approves | PASS |
| 17 | allowed operations are review/planning/suggestions only | PASS |
| 18 | source/test files remain forbidden | PASS |
| 19 | docs/REAL_CAPTURED_TASKS.md remains forbidden | PASS |
| 20 | future invocation still requires explicit approval | PASS |

**Validation: 20/20 checks passed.**

## Role Separation Checks

| Check | Result |
|-------|--------|
| Planner (claude-local) differs from reviewer (claude-deepseek) | PASS |
| Adoption reviewer is human/operator, not planner or reviewer agent | PASS |
| Commit reviewer is human/operator | PASS |
| Push reviewer is human/operator | PASS |
| No agent assigned to commit or push roles | PASS |
| No role can self-approve | PASS |
| Planner cannot auto-approve execution of its own plan | PASS |
| No agent may grant itself new authority | PASS |

## Required Future Invocation Approval

Before any agent may be invoked under this approved route:

1. A future phase must create an explicit invocation approval artifact.
2. Each agent invocation requires separate operator approval.
3. Agent lock must match the agent being invoked.
4. Registry entries must be current (not stale).
5. Invocation approval is scoped to one agent, one subtask, one invocation.
6. No blanket invocation authorization is granted by this routing approval.

## Required Future Prompt Capture

Before any prompt may be sent to any agent:

1. A future phase must establish prompt capture infrastructure.
2. All prompts must be captured and logged before sending.
3. No unlogged prompts are permitted.
4. Prompt content must be reviewed for scope compliance.
5. Prompt capture is required for both planner and documentation_reviewer invocations.

## Required Future Mutation Guard

For any future agent invocation under this route:

1. Pre-invocation git status must be captured.
2. Post-invocation git status must be compared.
3. Unexpected mutations trigger quarantine and block adoption.
4. Mutation guard is required regardless of agent risk level.

## Required Future Output Capture / Intake

For any future agent output under this route:

1. All output must be captured (stdout/stderr).
2. All output must go through intake classification.
3. No auto-apply of any agent output.
4. Output must be reviewed before any adoption consideration.
5. Content safety scan is required before adoption.

## Required Future Adoption / Commit / Push Boundaries

| Boundary | Required | Who | Authorized in 83D |
|----------|----------|-----|-------------------|
| Adoption review | yes | human/operator | no |
| Adoption approval | yes | human/operator | no |
| Adoption execution | yes | human/operator | no |
| Commit approval | yes | human/operator | no |
| Commit execution | yes | governed PCAE | no |
| Push approval | yes | human/operator | no |
| Push execution | yes | governed pcae push | no |

No adoption, commit, or push boundary is weakened or bypassed by this routing approval.

## Authorization Flags

| Flag | Value |
|------|-------|
| routing_authorized | true |
| backend_invocation_authorized | false |
| subagent_invocation_authorized | false |
| prompts_authorized | false |
| execution_authorized | false |
| repo_mutation_authorized | false |
| adoption_authorized | false |
| commit_authorized | false |
| push_authorized | false |

### What routing_authorized=true Means

- PCAE may proceed to a later phase that prepares prompt/invocation approval for the approved route.
- The approved route (claude-local as planner, claude-deepseek as reviewer, human/operator as governance) is recorded as the approved future routing path for MULTI-AGENT-DRY-RUN-001.

### What routing_authorized=true Does NOT Mean

- No backend may be invoked in Phase 83D or as a result of this approval alone.
- No prompts may be sent to any agent.
- No agents may execute any work.
- No agent output may be adopted into the repository.
- No commits or pushes are authorized beyond normal phase implementation/completion commits.
- This approval alone is insufficient to invoke any backend — explicit invocation approval is required in a future phase.

## Approval Outcome

| Field | Value |
|-------|-------|
| multi_agent_routing_approval_status | approved |
| approval_outcome | approved_for_future_routing_only |

## Blockers / Warnings

**Blockers:** none for this routing approval.

**Warnings:**
- claude-kimi is not available and cannot be included in any route.
- codex is available but unverified and cannot be included in any route.
- Subagent discovery has not been performed; subagent routing remains blocked.
- This approval authorizes routing only; all later boundaries require their own approval phases.

## Recommended Next Phase

**83E — Multi-Agent Prompt Package Dry-Run**

83E should prepare the prompt package for the planner/reviewer route as a dry-run artifact only, still without sending prompts or invoking backends.
