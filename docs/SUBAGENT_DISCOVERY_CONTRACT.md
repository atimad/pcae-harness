# Subagent Discovery Contract

## Purpose

Define how PCAE discovers, describes, and governs subagents exposed by registered backends. This contract specifies the metadata, authorization, safety, and routing requirements for subagent discovery without granting execution authority.

## Scope

This contract covers the discovery data model, authorization requirements, and artifact format. It does not implement discovery commands, probe subagents, or invoke backends.

## Non-Goals

- Subagent probing or invocation (deferred to 82D or later).
- Subagent routing execution (deferred to 82E).
- Multi-agent task splitting (deferred to 82F).
- Automatic subagent selection without human approval.
- Granting execution authority through discovery alone.

## Definition of "Subagent"

A **subagent** is a specialized capability or mode exposed by a parent backend that can be addressed separately for task routing. Examples:

- A parent backend may expose specialized modes (e.g., code review, documentation, refactoring).
- A parent backend may delegate to different underlying models or providers depending on configuration.
- A wrapper script (like `claude-deepseek`) may expose a parent backend (`claude`) with alternative model routing.

A subagent is **not** an independent process — it is a governed invocation path through a parent backend that PCAE recognizes and tracks separately.

## Discovery Authorization Model

Discovery requires explicit authorization:

| Requirement | Description |
|-------------|-------------|
| Parent agent must be registered | Only registered backends can expose subagents |
| Parent agent lock must be held | PCAE agent lock must match the parent |
| Operator approval required | Discovery probe requires explicit human sign-off |
| Discovery scope must be bounded | Only metadata probes, not task execution |
| Mutation guard required | Pre/post git status comparison during any probe |
| Discovery output must be reviewed | Results are classified before use |

Discovery does NOT authorize:
- Task routing to discovered subagents.
- Prompt sending to subagents.
- File modification by subagents.
- Automatic registration without review.

## Discovery Input Requirements

Before discovery can proceed for a parent agent:

1. Parent agent exists in the capability registry (82A).
2. Parent agent was probed and verified (82B).
3. Parent agent is `enabled=true` in the registry.
4. Parent agent command is available on PATH.
5. PCAE agent lock matches the parent agent.
6. Operator has approved the discovery scope.

## Discovery Command Constraints

Future discovery probes must:

- Use only non-interactive, metadata-only commands.
- Have bounded timeouts (5-10 seconds).
- Not send natural-language prompts.
- Not open interactive sessions.
- Not modify repository files.
- Not install or update tools.
- Capture stdout/stderr for review.
- Run mutation guard before and after.

## Subagent Identity Model

| Field | Type | Description |
|-------|------|-------------|
| `parent_agent_id` | string | ID of the parent backend |
| `subagent_id` | string | Unique identifier for this subagent |
| `display_name` | string | Human-readable name |
| `description` | string | What this subagent does |
| `source_backend` | string | Backend command used |
| `discovery_method` | string | How this subagent was discovered |
| `discovered_at` | string/null | ISO timestamp of discovery |
| `verification_source` | string/null | Phase or method that verified capabilities |
| `enabled` | boolean | Whether available for routing consideration |
| `routing_authorized` | boolean | Whether routing has been explicitly approved |
| `execution_authorized` | boolean | Always false at discovery time |

## Subagent Capability Model

| Field | Type | Description |
|-------|------|-------------|
| `can_review_code` | boolean | Can review code for correctness |
| `can_generate_code` | boolean | Can generate new code |
| `can_write_files` | boolean | Can create/modify files directly |
| `can_run_shell` | boolean | Can execute shell commands |
| `can_analyze_tests` | boolean | Can analyze test results |
| `can_plan` | boolean | Can create plans/designs |
| `can_summarize` | boolean | Can summarize content |
| `can_refactor` | boolean | Can restructure code |
| `can_handle_docs` | boolean | Can generate/edit documentation |
| `can_handle_security_sensitive_tasks` | boolean | Can work with security-relevant content |
| `can_self_report_limitations` | boolean | Can identify what it cannot do |

## Subagent Safety Model

| Field | Type | Description |
|-------|------|-------------|
| `risk_level` | string | `low`, `medium`, `high`, `unknown` |
| `requires_parent_agent_lock` | boolean | Parent lock must be held |
| `requires_task_contract` | boolean | Task contract required before invocation |
| `requires_prompt_capture` | boolean | Prompt must be captured |
| `requires_mutation_guard` | boolean | Pre/post git status required |
| `requires_output_intake` | boolean | Output must be classified before use |
| `requires_human_approval_before_invocation` | boolean | Operator sign-off needed |
| `may_modify_repo_directly` | boolean | Can change files in the working tree |
| `may_execute_shell` | boolean | Can run shell commands |
| `may_commit` | boolean | Can create git commits |
| `may_push` | boolean | Can push to remote |
| `routing_allowed` | boolean | Whether routing is permitted |

## Subagent Routing Restrictions

- No subagent may be routed work solely because it was discovered.
- Routing requires: task contract + approval + parent lock + safety profile.
- No subagent may auto-apply, auto-commit, or auto-push.
- No subagent may execute shell commands without explicit approval.
- No subagent may modify the repository without mutation guard.
- Output from any subagent must go through intake and review.
- Only one adoption path may modify the repository at a time.

## Discovery Result Artifact Format

Proposed future location: `.pcae/agents/subagents/<parent-agent-id>.json`

```json
{
  "parent_agent_id": "claude-local",
  "discovery_version": "1.0",
  "discovered_at": "2026-06-23T00:00:00Z",
  "discovery_method": "metadata_probe",
  "subagents": [
    {
      "subagent_id": "claude-local-docs",
      "display_name": "Claude Documentation Mode",
      "description": "Specialized for documentation tasks",
      "enabled": false,
      "routing_authorized": false,
      "execution_authorized": false,
      "risk_level": "low",
      "capabilities": {
        "can_handle_docs": true,
        "can_generate_code": false
      }
    }
  ]
}
```

This artifact is NOT created in 82C. It documents the proposed format for future implementation.

## Discovery Validation Rules

1. Unknown subagents are **disabled by default**.
2. Missing `discovered_at` blocks routing.
3. Stale discovery (older than policy threshold) blocks routing.
4. Subagent with `enabled=false` cannot be selected.
5. Subagent with `routing_authorized=false` cannot be routed work.
6. `execution_authorized` must be `false` at discovery time.
7. Parent agent lock must be verified before discovery probe.
8. Discovery results must be reviewed before any subagent is enabled.

## Unknown / Missing Subagent Behavior

- If a parent agent has not been probed for subagents: `discovery_status=pending`.
- If a parent agent is missing from PATH: `discovery_status=blocked_parent_missing`.
- If discovery was attempted but failed: `discovery_status=failed`.
- Unknown subagents not in the discovery result are treated as non-existent.

## Stale Discovery Behavior

- Discovery results older than a configurable threshold are marked stale.
- Stale discovery blocks routing but does not disable the parent agent.
- Re-discovery requires a new governed probe phase with approval.

## Registry Integration

Discovery results feed into the agent capability registry (82A design):

- Each discovered subagent becomes a registry entry under its parent.
- Registry entries inherit the parent's safety baseline unless overridden.
- Routing eligibility requires both registry entry and explicit approval.

## Human Approval Requirements

| Action | Approval Required |
|--------|-------------------|
| Initiate discovery probe | Yes |
| Enable a discovered subagent | Yes |
| Authorize routing to a subagent | Yes |
| Send a task to a subagent | Yes (via task contract) |
| Apply subagent output | Yes (via adoption lifecycle) |

## Failure Modes

| Failure | Handling |
|---------|----------|
| Parent agent unavailable | Block discovery, report `blocked_parent_missing` |
| Discovery probe times out | Report `discovery_timeout`, do not retry automatically |
| Probe returns unexpected output | Quarantine result, require manual review |
| Probe modifies repository | Detect via mutation guard, quarantine, report |
| Discovered subagent has unknown risk | Set `risk_level=unknown`, disable by default |

## Example Discovery Records

### claude-local

- **Discovery status:** future probe required
- **Known subagent candidates:** none confirmed; discovery pending
- **Routing authorized:** false
- **Execution authorized:** false
- **Note:** Primary backend. Used for both governed lifecycles. Subagent capability unverified.

### claude-deepseek

- **Discovery status:** future probe required
- **Known subagent candidates:** none confirmed
- **Routing authorized:** false
- **Execution authorized:** false
- **Note:** Wrapper around claude with different model. Must remain identity-separated from claude-local.

### codex

- **Discovery status:** future probe required
- **Known subagent candidates:** none confirmed
- **Routing authorized:** false
- **Execution authorized:** false
- **Note:** OpenAI CLI. Safety profile not yet established for PCAE governance.

### claude-kimi

- **Discovery status:** blocked_parent_missing
- **Note:** Command not found on PATH as of 82B probe. Discovery cannot proceed.

## Future Phases

| Phase | Description |
|-------|-------------|
| 82D | Subagent Safety Profile (establish safety baselines) |
| 82E | Agent Routing Dry-Run (test routing logic without execution) |
| 82F | Multi-Agent Task Split Dry-Run (plan task distribution) |

## Design Conclusion

The subagent discovery contract ensures that PCAE can identify and catalog subagent capabilities without granting execution authority. Discovery is a governed, approval-gated process that produces descriptive metadata — not permission. No subagent can be routed work, modify the repository, or execute tasks solely because it was discovered. Routing requires task contracts, explicit approvals, and the full governance chain.
