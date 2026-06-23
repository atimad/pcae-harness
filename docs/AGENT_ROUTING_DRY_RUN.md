# Agent Routing Dry-Run

## Purpose

Simulate routing decisions for hypothetical task types against the known backend inventory, capability metadata, and safety profiles. This is a documentation-only dry-run — no real routing, no backend invocation, no prompts sent.

## Scope

Evaluate 13 hypothetical task types against 4 known backends. Produce advisory routing results only. This document does not authorize routing, execution, or invocation.

## Non-Goals

- Real agent routing or task assignment.
- Backend or subagent invocation.
- Prompt sending.
- Repository modification by agents.
- Implementation of routing commands.

## Input Artifacts

| Artifact | Phase |
|----------|-------|
| Agent Capability Registry Design | 82A |
| Agent Identity Capability Probe | 82B |
| Subagent Discovery Contract | 82C |
| Subagent Safety Profile | 82D |

## Routing Principles

1. Availability does not imply permission.
2. Capability metadata does not grant execution authority.
3. Every real route requires: task contract + operator approval + parent lock + prompt capture + mutation guard + output intake.
4. No agent may auto-apply, auto-commit, or auto-push.
5. Unknown or unverified agents are blocked.
6. Subagent routing is blocked until governed discovery completes.

## Known Backend Inventory

| Backend | Available | Version | Risk | Proven |
|---------|-----------|---------|------|--------|
| claude | yes | 2.1.186 | low | yes (81D, 77F) |
| claude-deepseek | yes (wrapper) | 2.1.186 | medium | yes (77F) |
| claude-kimi | no | N/A | unknown | no |
| codex | yes | 0.140.0 | high | no |

## Routing Eligibility Matrix

| Task Type | Risk | claude | claude-deepseek | claude-kimi | codex |
|-----------|------|--------|-----------------|-------------|-------|
| planning_only | low | candidate | candidate | blocked (missing) | blocked (unverified) |
| documentation_only | low | candidate | candidate | blocked | blocked |
| documentation_review | low | candidate | candidate | blocked | blocked |
| code_review | medium | candidate | candidate | blocked | blocked |
| test_analysis | medium | candidate | candidate | blocked | blocked |
| source_code_change | high | blocked* | blocked* | blocked | blocked |
| refactor | high | blocked* | blocked* | blocked | blocked |
| dependency_change | high | blocked | blocked | blocked | blocked |
| shell_execution | high | blocked | blocked | blocked | blocked |
| security_sensitive_review | high | blocked* | blocked* | blocked | blocked |
| backend_capture | governed | candidate | candidate | blocked | blocked |
| multi_agent_review | future | blocked | blocked | blocked | blocked |
| multi_agent_task_split | future | blocked | blocked | blocked | blocked |

*blocked = requires future explicit task contract, approval, preflight, mutation guard, output intake, adoption review, and commit/push governance. Not blocked by capability, but blocked by missing governance prerequisites.

## Blocked Routing Cases

| Case | Reason |
|------|--------|
| claude-kimi for any task | Backend missing from PATH |
| codex for any task | Available but unverified for PCAE governance |
| Any agent for source_code_change | High risk; requires full governance chain not yet approved |
| Any agent for refactor | High risk; same as source_code_change |
| Any agent for dependency_change | High risk; blocked by default |
| Any agent for shell_execution | High risk; requires per-invocation approval |
| Any agent for multi_agent_review | Subagent discovery not yet performed |
| Any agent for multi_agent_task_split | Subagent discovery + routing model not yet implemented |
| Any subagent for any task | Subagent discovery blocked (82C contract defined, probes not yet executed) |

## Required Approvals per Task Type

| Task Type | Task Contract | Operator Approval | Prompt Capture | Preflight |
|-----------|---------------|-------------------|----------------|-----------|
| planning_only | required | required | recommended | optional |
| documentation_only | required | required | recommended | optional |
| documentation_review | required | required | recommended | optional |
| code_review | required | required | required | recommended |
| test_analysis | required | required | required | recommended |
| source_code_change | required | required | required | required |
| refactor | required | required | required | required |
| dependency_change | required | required | required | required |
| shell_execution | required | required + per-invocation | required | required |
| security_sensitive_review | required | required | required | required |
| backend_capture | required | required | required | required |

## Required Guards per Task Type

| Task Type | Mutation Guard | Output Intake | Adoption Review | Commit Approval | Push Approval |
|-----------|---------------|---------------|-----------------|-----------------|---------------|
| planning_only | required | required | optional | if adopted | if adopted |
| documentation_only | required | required | required | required | required |
| documentation_review | required | required | recommended | if adopted | if adopted |
| code_review | required | required | required | required | required |
| test_analysis | required | required | required | required | required |
| source_code_change | required | required | required | required | required |
| refactor | required | required | required | required | required |
| dependency_change | required | required | required | required | required |
| shell_execution | required | required | required | required | required |
| security_sensitive_review | required | required | required | required | required |
| backend_capture | required | required | required | required | required |

## Subagent Routing Implications

Subagent routing is blocked for all task types because:

1. Subagent discovery has not been performed (82C defined contract only).
2. No subagent safety profiles have been assigned from real probes.
3. No subagent-specific task contracts exist.
4. Unknown subagents are disabled by default (82D policy).

Subagent routing will become possible only after:

- 82F or later performs governed subagent discovery probes.
- Discovered subagents are assigned safety profiles.
- Operator approves routing to specific subagents for specific task types.

## Dry-Run Result Summaries

### planning_only

- **Risk:** low
- **Candidates:** claude, claude-deepseek
- **Result:** candidate_future_route
- **Reason:** Both backends proven capable; requires task contract and approval for real route.

### documentation_only

- **Risk:** low
- **Candidates:** claude, claude-deepseek
- **Result:** candidate_future_route
- **Reason:** Proven in both governed lifecycles (77J-77V.1, 81A-81I).

### documentation_review

- **Risk:** low
- **Candidates:** claude, claude-deepseek
- **Result:** candidate_future_route
- **Reason:** Low-risk read-only task; output intake still required.

### code_review

- **Risk:** medium
- **Candidates:** claude, claude-deepseek
- **Result:** candidate_future_route
- **Reason:** Suggestions only; no direct writes; output intake required.

### test_analysis

- **Risk:** medium
- **Candidates:** claude, claude-deepseek
- **Result:** candidate_future_route
- **Reason:** Analysis only; no direct test mutation; output intake required.

### source_code_change

- **Risk:** high
- **Candidates:** none currently approved
- **Result:** blocked_high_risk
- **Reason:** Requires full governance chain; no agent has pre-approved source modification rights.

### refactor

- **Risk:** high
- **Candidates:** none currently approved
- **Result:** blocked_high_risk
- **Reason:** Same as source_code_change.

### dependency_change

- **Risk:** high
- **Candidates:** none
- **Result:** blocked_high_risk
- **Reason:** Blocked by default; requires special approval and safety review.

### shell_execution

- **Risk:** high
- **Candidates:** none
- **Result:** blocked_high_risk
- **Reason:** No agent has per-invocation shell execution approval.

### security_sensitive_review

- **Risk:** high
- **Candidates:** none currently approved
- **Result:** blocked_high_risk
- **Reason:** Requires explicit security-review task contract and approval.

### backend_capture

- **Risk:** governed
- **Candidates:** claude, claude-deepseek
- **Result:** candidate_future_route
- **Reason:** Governed by the backend-output-adoption lifecycle, not ordinary routing.

### multi_agent_review

- **Risk:** future
- **Candidates:** none
- **Result:** blocked_missing_subagent_discovery
- **Reason:** Subagent discovery not yet performed.

### multi_agent_task_split

- **Risk:** future
- **Candidates:** none
- **Result:** blocked_missing_subagent_discovery
- **Reason:** Subagent discovery and task-split model not yet implemented.

## Recommended Future Implementation Model

A future `pcae route` or `pcae agent route` command should:

1. Accept a task type and optional agent preference.
2. Consult the registry for eligible agents.
3. Evaluate safety profiles against the task type.
4. Return an advisory recommendation (not execute).
5. Require explicit approval before any real invocation.
6. Log the routing decision for audit.

This command is not implemented in 82E.

## Failure Modes

| Failure | Handling |
|---------|----------|
| No eligible agent for task type | Report `no_eligible_agent`, block routing |
| Preferred agent missing | Report `agent_unavailable`, suggest alternatives |
| Safety profile missing | Report `safety_profile_missing`, block routing |
| Stale capability data | Report `stale_verification`, block routing |
| Multiple eligible agents | Report candidates, require operator selection |

## Safety Conclusion

- No real routing occurred.
- No backend or subagent was invoked.
- No prompts were sent.
- No repository mutation occurred.
- No routing is authorized by this dry-run.
- All future real routing requires explicit task contract, operator approval, prompt capture, mutation guard, output intake, and separate commit/push governance.

## Dry-Run Status

| Field | Value |
|-------|-------|
| agent_routing_dry_run_status | completed |
| routing_simulation_only | true |
| real_routing_performed | false |
| backend_invocation_performed | false |
| subagent_invocation_performed | false |
| prompts_sent | false |
| repo_mutation_by_agent | false |
| routing_authorized | false |
| execution_authorized | false |

## Recommended Next Phase

**82F — Multi-Agent Task Split Dry-Run**

82F should simulate how a task could be split across multiple agents using the registry, safety profiles, and routing model, without performing real splits or invocations.
