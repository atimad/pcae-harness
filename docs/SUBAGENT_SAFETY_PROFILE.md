# Subagent Safety Profile

## Purpose

Define the safety profile model for PCAE subagents: risk classification, permission boundaries, approval requirements, mutation handling, output intake, quarantine, and forbidden behaviors. The safety profile governs what a subagent may do before, during, and after invocation.

## Scope

This design defines the safety data model and policy rules. It does not implement CLI commands, probe subagents, or invoke backends.

## Non-Goals

- Subagent probing or invocation (deferred to future phases).
- Agent routing execution (deferred to 82E).
- Multi-agent task splitting (deferred to 82F).
- Automatic safety profile assignment without human review.

## Relationship to Subagent Discovery Contract

The discovery contract (82C) defines how subagents are found. The safety profile defines what they are allowed to do once found. Discovery produces identity and capability metadata; the safety profile maps that metadata to governance constraints.

## Relationship to Agent Capability Registry

The capability registry (82A) stores agent/subagent entries. The safety profile is a required field of each entry. An agent without a safety profile is `unknown` risk and disabled for routing.

## Safety Profile Principles

1. **Default deny.** Unknown subagents are disabled. Missing safety profiles block routing.
2. **Capability implies risk, not permission.** A subagent that can write files has high risk — it does not have permission to write files.
3. **Approval is explicit and scoped.** Each invocation requires its own approval tied to a task contract.
4. **Mutation is detected, not prevented.** The mutation guard catches unexpected changes; it does not prevent the agent from trying.
5. **Output is untrusted until reviewed.** All subagent output goes through intake before adoption.
6. **One adoption path at a time.** Only one subagent may modify the repository through the governed lifecycle at any given time.

## Risk Level Taxonomy

| Level | Description | Routing | Execution |
|-------|-------------|---------|-----------|
| `unknown` | Undiscovered or unverified subagent | Disabled | Disabled |
| `low` | Advisory/read-only: summarization, planning, documentation review | Eligible after approval | Stdout capture only |
| `medium` | Suggestions/patches: code review, doc generation | Eligible after approval | Stdout capture + intake |
| `high` | Repo-modifying: code generation, refactoring, shell execution, test modification | Eligible after approval + preflight | Full governance chain |
| `blocked` | Policy violation, stale verification, unexpected mutation, or explicit block | Disabled | Disabled |

## Capability-to-Risk Mapping

| Capability | Default Risk |
|-----------|-------------|
| `can_summarize` | low |
| `can_plan` | low |
| `can_handle_docs` (read-only) | low |
| `can_review_code` | medium |
| `can_handle_docs` (generate) | medium |
| `can_generate_code` | high |
| `can_refactor` | high |
| `can_write_files` | high |
| `can_run_shell` | high |
| `can_analyze_tests` | medium |
| `can_handle_security_sensitive_tasks` | high |
| Unknown capability | unknown (blocked until reviewed) |

A subagent's overall risk level is the highest risk among its declared capabilities.

## Permission Boundaries

| Permission | Default | Low | Medium | High |
|-----------|---------|-----|--------|------|
| `may_receive_prompt` | false | true | true | true |
| `may_read_repo_context` | false | true | true | true |
| `may_generate_suggestions` | false | true | true | true |
| `may_generate_patch` | false | false | true | true |
| `may_write_files` | false | false | false | with approval |
| `may_run_shell` | false | false | false | with approval |
| `may_create_artifacts` | false | false | true | true |
| `may_modify_source` | false | false | false | with approval |
| `may_modify_tests` | false | false | false | with approval |
| `may_modify_docs` | false | true | true | with approval |
| `may_commit` | false | false | false | false |
| `may_push` | false | false | false | false |

`may_commit` and `may_push` are always `false` for subagents. Commits and pushes are governance operations performed by PCAE, not by agents.

## Invocation Approval Requirements

| Gate | Low | Medium | High | Unknown/Blocked |
|------|-----|--------|------|-----------------|
| Task contract exists | required | required | required | N/A (blocked) |
| Parent agent lock held | required | required | required | N/A |
| Operator approval | required | required | required | N/A |
| Prompt captured | recommended | required | required | N/A |
| Preflight check | optional | recommended | required | N/A |

## Prompt Capture Requirements

| Risk | Requirement |
|------|-------------|
| Low | Recommended — capture for audit trail |
| Medium | Required — prompt must be recorded before send |
| High | Required — prompt must be recorded, reviewed, and approved before send |
| Unknown/Blocked | N/A — invocation not allowed |

## Mutation Guard Requirements

| Risk | Pre-invocation | Post-invocation | Unexpected Mutation |
|------|---------------|-----------------|---------------------|
| Low | Capture git status | Compare git status | Quarantine + report |
| Medium | Capture git status | Compare git status | Quarantine + report |
| High | Capture git status + file hashes | Compare git status + file hashes | Quarantine + block + report |
| Unknown/Blocked | N/A | N/A | N/A |

## Output Intake Requirements

| Risk | Capture | Classification | Review | Auto-Apply |
|------|---------|---------------|--------|------------|
| Low | Required | Required | Recommended | Forbidden |
| Medium | Required | Required | Required | Forbidden |
| High | Required | Required | Required + approval | Forbidden |
| Unknown/Blocked | N/A | N/A | N/A | N/A |

## Quarantine Requirements

Quarantine is triggered when:

- A mutation guard detects unexpected file changes.
- Output intake classifies output as potentially unsafe.
- A subagent produces output outside the expected scope.
- A subagent attempts to modify forbidden files.

Quarantine means:

- Preserve the unexpected state without cleanup.
- Report the quarantine to the operator.
- Block adoption, commit, and push until reviewed.
- Do not delete quarantined content automatically.

## Human Review Requirements

| Action | Review Required |
|--------|----------------|
| Enable a discovered subagent | Yes |
| Assign a safety profile | Yes |
| Upgrade a safety profile (e.g., low to medium) | Yes |
| Authorize routing to a subagent | Yes |
| Approve subagent invocation | Yes |
| Review subagent output | Yes (medium/high) |
| Approve adoption of subagent output | Yes |
| Approve commit of adopted content | Yes |
| Approve push | Yes |

## Routing Eligibility Requirements

A subagent is eligible for routing only when ALL of the following are true:

1. Parent agent is registered and enabled.
2. Subagent has been discovered through a governed probe.
3. Subagent has a safety profile assigned.
4. Safety profile risk level is not `unknown` or `blocked`.
5. `last_verified_at` is within the staleness threshold.
6. Task contract exists and names the subagent.
7. Operator has approved routing for this task.
8. Parent agent lock is held.

## Forbidden Behaviors

The following are unconditionally forbidden for all subagents:

- Auto-routing to unknown subagents.
- Auto-apply of subagent output.
- Auto-commit.
- Auto-push.
- Raw git push.
- Force push.
- Bypassing hooks without documented bounded exception.
- Hidden or unlogged backend invocation.
- Unlogged prompts.
- Unbounded shell execution.
- Source/test mutation without task contract.
- Adoption without intake and review.
- Using stale capability/safety data for routing decisions.
- Modifying `docs/REAL_CAPTURED_TASKS.md` outside the governed adoption lifecycle.

## Allowed Behaviors by Risk Level

### Low Risk

- Receive a bounded prompt via governed capture.
- Return text/markdown on stdout.
- Provide advisory summaries, plans, or documentation reviews.
- No file writes, no shell execution, no repo mutation expected.

### Medium Risk

- All low-risk behaviors.
- Return structured suggestions or patches on stdout.
- Generate documentation snippets.
- Output must go through intake and review before any adoption.

### High Risk

- All medium-risk behaviors.
- May produce code, refactoring suggestions, or test modifications.
- Output must go through full governance chain: intake, review, approval, preflight, execution, commit approval, push approval.
- Shell execution only with explicit per-invocation approval.
- File writes detected by mutation guard and quarantined if unexpected.

### Unknown / Blocked

- No invocation allowed.
- No prompt sending.
- No routing.
- Must be discovered, verified, and assigned a safety profile before any interaction.

## Example Profiles

### Documentation Review Subagent (Low)

```
risk_level: low
may_receive_prompt: true
may_read_repo_context: true
may_generate_suggestions: true
may_write_files: false
may_run_shell: false
may_commit: false
may_push: false
requires_mutation_guard: true
requires_output_intake: true
```

### Code Review Subagent (Medium)

```
risk_level: medium
may_receive_prompt: true
may_read_repo_context: true
may_generate_suggestions: true
may_generate_patch: true
may_write_files: false
may_run_shell: false
may_commit: false
may_push: false
requires_prompt_capture: true
requires_mutation_guard: true
requires_output_intake: true
requires_human_review: true
```

### Code Generation Subagent (High)

```
risk_level: high
may_receive_prompt: true
may_read_repo_context: true
may_generate_suggestions: true
may_generate_patch: true
may_write_files: with_approval
may_run_shell: with_approval
may_commit: false
may_push: false
requires_task_contract: true
requires_prompt_capture: true
requires_preflight: true
requires_mutation_guard: true
requires_output_intake: true
requires_human_review: true
requires_adoption_approval: true
```

### Shell-Capable Subagent (High/Blocked)

```
risk_level: high
may_run_shell: with_explicit_per_invocation_approval
default_routing_status: blocked_until_safety_review
note: "Shell execution requires the highest governance scrutiny."
```

### Unknown Subagent

```
risk_level: unknown
enabled: false
routing_authorized: false
execution_authorized: false
note: "Must be discovered, verified, and assigned a profile."
```

## Failure Modes

| Failure | Handling |
|---------|----------|
| Missing safety profile | Block routing, report `safety_profile_missing` |
| Stale safety profile | Block routing, report `safety_profile_stale` |
| Risk level mismatch with observed behavior | Quarantine output, block adoption, escalate |
| Subagent exceeds declared capabilities | Quarantine, block, report policy violation |
| Mutation guard detects unexpected changes | Quarantine, preserve state, block commit/push |
| Output fails content safety scan | Block adoption, report |

## Future Phases

| Phase | Description |
|-------|-------------|
| 82E | Agent Routing Dry-Run |
| 82F | Multi-Agent Task Split Dry-Run |
| 83A+ | Governed multi-agent orchestration |

## Design Conclusion

The subagent safety profile ensures that no subagent can bypass PCAE governance. Risk is classified conservatively, permissions default to deny, and every invocation requires explicit approval. The safety profile is a required governance input — without it, a subagent is unknown and disabled. No subagent may auto-apply, auto-commit, or auto-push regardless of risk level.
