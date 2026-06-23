# Agent Assignment Approval

## Purpose

Approve a future documentation-only multi-agent role assignment model, binding allowed agents to specific roles while preserving all governance boundaries. This approval does not authorize routing, invocation, execution, adoption, commit, or push.

## Scope

Approves the role assignment model for a future documentation-review multi-agent contract only. Does not approve code generation, refactoring, shell execution, dependency changes, or security-sensitive work.

## Non-Goals

- Approving real-time agent routing.
- Authorizing backend or subagent invocation.
- Authorizing prompt sending.
- Authorizing execution, adoption, commit, or push.
- Approving high-risk task assignments.
- Approving codex, claude-kimi, or subagent assignments.

## Input Artifacts

| Artifact | Phase |
|----------|-------|
| Agent Capability Registry Design | 82A |
| Agent Identity Capability Probe | 82B |
| Subagent Discovery Contract | 82C |
| Subagent Safety Profile | 82D |
| Agent Routing Dry-Run | 82E |
| Multi-Agent Task Split Dry-Run | 82F |
| Multi-Agent Task Contract Design | 83A |

## Approved Future Assignment Model

| Role | Assigned To | Risk | Status |
|------|-------------|------|--------|
| planner | claude-local | low | approved for future contract |
| documentation_reviewer | claude-deepseek | low | approved for future contract |
| adoption_reviewer | human/operator | N/A | required (governance role) |
| commit_reviewer | human/operator | N/A | required (governance role) |
| push_reviewer | human/operator | N/A | required (governance role) |

## Approved Agents

| Agent | Approved For | Justification |
|-------|-------------|---------------|
| claude-local | planner, documentation reviewer | Available, proven in two lifecycles, low risk for docs/planning |
| claude-deepseek | documentation reviewer, alternate planner | Available, proven in first lifecycle, identity-separated from claude-local |

## Forbidden Agents

| Agent | Reason |
|-------|--------|
| claude-kimi | Missing from PATH (82B probe) |
| codex | Available but unverified for PCAE governance (82B probe) |
| All subagents | Discovery not performed (82C contract defined, probes not executed) |
| Unknown agents | Disabled by default (82A/82D policy) |

## Approved Roles

| Role | Approved |
|------|----------|
| planner | yes (low risk, advisory) |
| documentation_reviewer | yes (low risk, read-only review) |
| adoption_reviewer | yes (human/operator only) |
| commit_reviewer | yes (human/operator only) |
| push_reviewer | yes (human/operator only) |

## Forbidden Roles

| Role | Reason |
|------|--------|
| primary_executor (for code) | High risk, not approved in this assignment |
| test_reviewer | Not needed for documentation-only tasks |
| safety_reviewer (for execution) | Not needed for documentation-only tasks |
| Any agent as commit_reviewer | Agents may never approve commits |
| Any agent as push_reviewer | Agents may never approve pushes |

## Role Separation Checks

| Check | Result |
|-------|--------|
| Planner (claude-local) differs from reviewer (claude-deepseek) | PASS |
| Adoption reviewer is human, not planner or reviewer agent | PASS |
| Commit reviewer is human | PASS |
| Push reviewer is human | PASS |
| No agent assigned to commit or push roles | PASS |
| No role can self-approve | PASS (planner cannot approve its own plan execution) |
| No agent may grant itself new authority | PASS |

## Approval Boundaries Preserved

| Boundary | Preserved |
|----------|-----------|
| Routing approval required before any real route | yes |
| Invocation approval required per agent per subtask | yes |
| Mutation guard required for any invocation | yes |
| Output intake required for any agent output | yes |
| Adoption review required before repo modification | yes |
| Commit approval required (human only) | yes |
| Push approval required (human only) | yes |

## Required Future Contract Fields

Before this approved assignment can be used, a future phase must create a full multi-agent task contract (per 83A design) including:

- contract_id, task_title, task_type, risk_level
- allowed_agents, forbidden_agents
- role assignments matching this approval
- allowed_files, forbidden_files
- prompt_capture_required=true
- mutation_guard_required=true
- output_intake_required=true
- execution_authorized=false (at creation)
- routing_authorized=false (at creation)

## Required Future Preflight Checks

Before any real invocation under this assignment model:

1. Verify agent registry entries are current (not stale).
2. Verify agent lock matches assigned agent.
3. Run routing dry-run for the specific task.
4. Confirm prompt capture mechanism is ready.
5. Confirm mutation guard is active.
6. Confirm output intake pipeline is ready.
7. Obtain explicit operator approval for each invocation.

## Required Future Prompt Capture

All prompts sent to assigned agents must be captured and logged before sending. No unlogged prompts.

## Required Future Output Intake

All agent output must go through intake classification before any adoption consideration. No auto-apply.

## Required Future Human Review

- All agent output must be reviewed by a human before adoption.
- Adoption requires explicit operator approval.
- Commit requires explicit operator approval.
- Push requires explicit operator approval.

## Blocked Cases

| Case | Status |
|------|--------|
| claude-kimi for any role | Blocked (missing) |
| codex for any role | Blocked (unverified) |
| Any subagent for any role | Blocked (discovery pending) |
| Code generation/execution | Not approved in this assignment |
| Shell execution | Not approved |
| Dependency changes | Not approved |
| Security-sensitive work | Not approved |
| Automatic merge | Not approved |
| Automatic adoption | Not approved |
| Automatic commit | Not approved |
| Automatic push | Not approved |

## Authorization Flags

| Flag | Value |
|------|-------|
| assignment_model_approved | true |
| routing_authorized | false |
| backend_invocation_authorized | false |
| subagent_invocation_authorized | false |
| prompts_authorized | false |
| execution_authorized | false |
| adoption_authorized | false |
| commit_authorized | false |
| push_authorized | false |

## Approval Outcome

| Field | Value |
|-------|-------|
| agent_assignment_approval_status | approved |
| approval_outcome | approved_for_future_documentation_review_contract |

## Recommended Next Phase

**83C — Multi-Agent Contract Instance Dry-Run**

83C should instantiate a draft documentation-only multi-agent contract as a dry-run artifact using this approved assignment model, but still not route or invoke agents.
