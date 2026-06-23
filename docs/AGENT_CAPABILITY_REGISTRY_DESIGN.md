# Agent Capability Registry Design

## Purpose

Define a structured model for representing AI agents/backends in PCAE, including their capabilities, safety profiles, task-type compatibility, routing constraints, and governance requirements. The registry enables PCAE to reason about which agent is suitable for which task before invocation.

## Scope

This design covers the registry data model and artifact format. It does not implement CLI commands, probe agents, or invoke backends.

## Non-Goals

- Agent probing or capability verification (deferred to 82B).
- Subagent discovery contracts (deferred to 82C).
- Safety profile implementation (deferred to 82D).
- Agent routing execution (deferred to 82E).
- Multi-agent task splitting (deferred to 82F).
- Automatic agent selection without human approval.
- Registry as an execution authority.

## Registry Concepts

The registry is a structured data store describing known agents. It is:

- **Descriptive, not permissive.** Registry entries describe what an agent can do, not what it is allowed to do. Permission requires task contracts, approvals, and governance gates.
- **Conservative by default.** Unknown agents are disabled. Missing or stale verification blocks routing.
- **Separate from execution.** The registry does not invoke agents, approve tasks, or authorize commits/pushes.

## Agent Identity Model

Each registered agent has:

| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | string | Unique identifier (e.g., `claude-local`) |
| `display_name` | string | Human-readable name |
| `backend_command` | string | CLI command to invoke (e.g., `claude`) |
| `backend_family` | string | Provider family (e.g., `anthropic`, `deepseek`) |
| `provider_or_runtime` | string | Provider name or runtime type |
| `enabled` | boolean | Whether the agent is available for routing |
| `locked` | boolean | Whether the agent currently holds the PCAE agent lock |
| `default_for_tasks` | list[string] | Task types this agent is preferred for |
| `last_verified_at` | string/null | ISO timestamp of last capability verification |
| `verification_source` | string/null | How capabilities were last verified |

## Backend Command Model

| Field | Type | Description |
|-------|------|-------------|
| `command` | string | Executable command name |
| `available` | boolean | Whether the command exists on PATH |
| `version` | string/null | Reported version if known |
| `invocation_mode` | string | `stdin_pipe`, `cli_args`, `api`, `unknown` |
| `timeout_default` | integer | Default timeout in seconds |

## Capability Model

| Field | Type | Description |
|-------|------|-------------|
| `can_generate_text` | boolean | Can produce text output |
| `can_edit_code` | boolean | Can produce code edits |
| `can_write_files` | boolean | Can create/modify files directly |
| `can_run_shell` | boolean | Can execute shell commands |
| `can_read_repo` | boolean | Can inspect repository state |
| `can_handle_large_context` | boolean | Supports large input context |
| `can_follow_task_contracts` | boolean | Can work within task contract scope |
| `can_return_markdown` | boolean | Can return markdown output |
| `can_return_patch` | boolean | Can return structured patches |
| `can_explain_changes` | boolean | Can explain what it changed and why |
| `can_self_report_limitations` | boolean | Can identify what it cannot do |

## Safety Profile Model

| Field | Type | Description |
|-------|------|-------------|
| `risk_level` | string | `low`, `medium`, `high`, `unknown` |
| `requires_human_approval` | boolean | Must have operator approval before invocation |
| `requires_prompt_capture` | boolean | Prompt must be captured/recorded |
| `requires_mutation_guard` | boolean | Pre/post git status comparison required |
| `requires_output_intake` | boolean | Output must be classified before use |
| `requires_adoption_review` | boolean | Output must pass safety review before adoption |
| `may_modify_repo_directly` | boolean | Agent can create/modify repo files |
| `may_execute_shell` | boolean | Agent can run shell commands |
| `may_commit` | boolean | Agent can create git commits |
| `may_push` | boolean | Agent can push to remote |
| `allowed_without_backend_execution` | boolean | Can be used for dry-run/planning only |

## Task-Type Compatibility Model

Each agent declares compatibility with task types:

| Task Type | Description |
|-----------|-------------|
| `documentation_only` | Generate/edit markdown documentation |
| `test_only` | Generate/edit test files only |
| `source_code_change` | Modify production source code |
| `refactor` | Restructure code without behavior change |
| `dependency_change` | Modify dependencies/packages |
| `backend_capture` | Serve as a capture target for governed output |
| `multi_agent_review` | Review output from another agent |
| `planning_only` | Design/planning without execution |
| `high_risk_operation` | Operations requiring elevated approval |

## Runtime / Execution Permissions Model

The registry records what governance gates are required, not what is permitted:

| Field | Type | Description |
|-------|------|-------------|
| `requires_task_contract` | boolean | Task contract must exist before invocation |
| `requires_preflight` | boolean | Preflight check must pass |
| `requires_approval_before_send` | boolean | Operator approval required before sending prompt |
| `requires_quarantine_if_mutation` | boolean | Unexpected mutation triggers quarantine |
| `requires_no_auto_apply` | boolean | Output must not be auto-applied |
| `requires_no_auto_commit` | boolean | Commits require separate approval |
| `requires_no_auto_push` | boolean | Pushes require separate approval |

## Output Expectations

| Field | Type | Description |
|-------|------|-------------|
| `preferred_output_format` | string | `markdown`, `patch`, `json`, `text` |
| `allowed_output_formats` | list[string] | Formats the agent can produce |
| `forbidden_output_formats` | list[string] | Formats that must be rejected |
| `max_expected_files` | integer/null | Maximum files expected in output |
| `allow_repo_mutation` | boolean | Whether repo mutation is expected |
| `mutation_handling` | string | `quarantine`, `reject`, `review` |
| `review_required` | boolean | Whether output must be reviewed before use |

## Mutation Risk Classification

| Level | Description | Handling |
|-------|-------------|----------|
| `none` | Agent produces stdout only, no file changes | Standard intake |
| `low` | Agent may create documentation files | Quarantine + review |
| `medium` | Agent may modify source or test files | Quarantine + review + approval |
| `high` | Agent may run shell commands or modify dependencies | Full governance chain required |
| `unknown` | Agent behavior not yet verified | Disabled until verified |

## Registry Artifact Format

Proposed future location: `.pcae/agents/registry.json`

```json
{
  "registry_version": "1.0",
  "agents": {
    "claude-local": {
      "agent_id": "claude-local",
      "display_name": "Claude (Local CLI)",
      "backend_command": "claude",
      "backend_family": "anthropic",
      "enabled": true,
      "capabilities": {
        "can_generate_text": true,
        "can_edit_code": true,
        "can_write_files": false,
        "can_run_shell": false,
        "can_return_markdown": true
      },
      "safety_profile": {
        "risk_level": "low",
        "requires_human_approval": true,
        "requires_mutation_guard": true,
        "may_modify_repo_directly": false,
        "may_commit": false,
        "may_push": false
      },
      "task_types": ["documentation_only", "planning_only", "backend_capture"],
      "routing": {
        "requires_task_contract": true,
        "requires_no_auto_apply": true,
        "requires_no_auto_commit": true,
        "requires_no_auto_push": true
      }
    }
  }
}
```

This artifact is not created in 82A. It is documented here as the proposed format for future implementation.

## Example Registry Entries

### claude-local

- **Enabled:** yes
- **Command:** `claude`
- **Family:** anthropic
- **Task types:** documentation_only, planning_only, backend_capture, multi_agent_review
- **Risk level:** low (stdin pipe, no direct repo modification when used via `--print`)
- **Mutation guard:** required
- **Auto-apply/commit/push:** forbidden

### claude-deepseek

- **Enabled:** if configured
- **Command:** `claude-deepseek` (custom wrapper)
- **Family:** deepseek
- **Task types:** documentation_only, backend_capture, source_code_change (with elevated approval)
- **Risk level:** medium (may produce files or modify repo depending on invocation mode)
- **Mutation guard:** required
- **Auto-apply/commit/push:** forbidden
- **Note:** must remain identity-separated from claude-local

### claude-kimi

- **Enabled:** if configured
- **Command:** `claude-kimi` (custom wrapper)
- **Family:** moonshot
- **Task types:** documentation_only, backend_capture
- **Risk level:** medium
- **Mutation guard:** required
- **Auto-apply/commit/push:** forbidden

### codex (future)

- **Enabled:** no (not yet registered)
- **Command:** `codex`
- **Family:** openai
- **Task types:** source_code_change, refactor, test_only (after capability probe)
- **Risk level:** high (can execute shell, modify files)
- **Mutation guard:** required
- **Safety profile:** requires full governance chain before any invocation
- **Auto-apply/commit/push:** forbidden

## Validation Rules

1. Unknown agents (not in registry) are **disabled by default**.
2. Missing `last_verified_at` blocks routing.
3. Stale verification (older than policy threshold) blocks routing.
4. Agent with `enabled=false` cannot be selected for tasks.
5. Agent lock must match the selected agent before invocation.
6. Task type must be in the agent's `task_types` list.
7. All routing constraints must be satisfied before invocation.
8. Registry does not grant execution authority — task contracts and approval gates do.

## Future Phases

| Phase | Description |
|-------|-------------|
| 82B | Agent Identity / Backend Capability Probe |
| 82C | Subagent Discovery Contract |
| 82D | Subagent Safety Profile |
| 82E | Agent Routing Dry-Run |
| 82F | Multi-Agent Task Split Dry-Run |

## Open Questions

1. Should registry entries be mutable at runtime, or only through governed phases?
2. Should capability verification be automatic (probe on bootstrap) or manual (operator-initiated)?
3. How should the registry handle agents that are available but untrusted?
4. Should routing recommendations be advisory-only, or should they block invocation of unregistered agents?
5. How should multi-agent task splitting interact with the single-adoption-path constraint?

## Design Conclusion

The agent capability registry provides a structured, conservative foundation for multi-agent readiness. It describes agents without granting execution authority, requires verification before routing, and enforces that no agent can auto-apply, auto-commit, or auto-push. The registry is a governance input, not a governance bypass.
