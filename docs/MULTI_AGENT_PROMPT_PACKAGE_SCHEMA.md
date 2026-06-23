# Multi-Agent Prompt Package Schema

## Purpose

Define a stable, machine-readable schema for multi-agent prompt packages. The schema provides structured fields for approved prompts, roles, agents, allowed context, expected outputs, forbidden actions, authorization flags, capture requirements, and safety constraints.

## Scope

Schema documentation only. This artifact defines field names, types, semantics, validation rules, and an illustrative example. It does not implement validators, CLI commands, or executable schema files.

## Non-Goals

- Schema implementation in code.
- Validator or parser implementation.
- CLI command implementation.
- Backend invocation or prompt sending.
- Output capture or intake.
- Adoption of any content.
- Executable schema files outside docs.

## Motivation from 83A–83L Lifecycle

The first governed multi-agent lifecycle (contract MULTI-AGENT-DRY-RUN-001) used documentation-only prompt packages stored in markdown. Lessons learned (84A) identified these friction points:

1. **Prompt extraction** — extracting prompt text from markdown code blocks is error-prone.
2. **NOT SEND-AUTHORIZED markers** — markers served their purpose but required manual removal.
3. **Prompt hash verification** — no machine-enforced check that the sent prompt matches the approved package.
4. **Handoff content injection risk** — planner output inserted as raw text into reviewer prompt without structured boundaries.
5. **Status transitions** — package status tracked in prose rather than structured fields.

A machine-readable schema addresses all five friction points by providing structured, hashable, validatable prompt package artifacts.

## Schema Design Principles

1. **Descriptive until approved.** A schema instance describes intended prompts; it does not authorize sending.
2. **One package per contract.** Each prompt package binds to exactly one multi-agent contract.
3. **Explicit role binding.** Every prompt binds to exactly one role; every role binds to exactly one agent.
4. **Hash-verifiable.** Prompt text hashes enable tamper-detection between approval and sending.
5. **Status-driven.** Package status transitions are monotonic and explicitly gated.
6. **Safety-first defaults.** All authorization flags default to false. All forbidden lists default to maximally restrictive.
7. **Capture-mandatory.** Every sent prompt must have capture requirements defined.
8. **Human-gated.** Adoption, commit, and push always require human approval regardless of schema state.

---

## Prompt Package Lifecycle State

```
draft_not_sent → approved_for_future_prompt_sending_only → sent_captured → intaked → reviewed → adoption_approved → adoption_executed → closed
                                                                                                                                        ↑
                                                                                                                              blocked ──┘
```

| Status | Description |
|--------|-------------|
| `draft_not_sent` | Package fields populated, not yet approved for sending |
| `approved_for_future_prompt_sending_only` | Operator approved sending; prompts not yet sent |
| `sent_captured` | Prompts sent, outputs captured with metadata |
| `intaked` | Captured outputs classified through intake |
| `reviewed` | Outputs reviewed for adoption candidacy |
| `adoption_approved` | Adoption candidates approved |
| `adoption_executed` | Approved adoption candidates applied |
| `closed` | Lifecycle complete, verified |
| `blocked` | Validation failure, policy violation, or agent unavailability |

Status transitions are monotonic (forward-only) unless explicitly blocked.

---

## Required Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prompt_package_id` | string | yes | Unique package identifier |
| `schema_version` | string | yes | Schema version (e.g., `0.1`) |
| `package_status` | string | yes | Current lifecycle status |
| `contract_id` | string | yes | Bound multi-agent contract ID |
| `route_id` | string/null | no | Routing approval reference |
| `created_at` | string | yes | ISO timestamp |
| `created_from_artifact` | string | yes | Path to source artifact |
| `approved_by` | string/null | no | Operator who approved sending |
| `approval_artifact` | string/null | no | Path to approval artifact |
| `roles` | list[Role] | yes | Role definitions |
| `prompts` | list[Prompt] | yes | Prompt definitions |
| `allowed_context` | list[Context] | yes | Allowed context files |
| `forbidden_context` | list[ForbiddenContext] | yes | Forbidden context patterns |
| `expected_outputs` | list[ExpectedOutput] | yes | Expected output definitions |
| `forbidden_outputs` | ForbiddenOutputs | yes | Forbidden output categories |
| `safety_constraints` | SafetyConstraints | yes | Safety constraint flags |
| `authorization_flags` | AuthorizationFlags | yes | Authorization state |
| `capture_requirements` | CaptureRequirements | yes | Capture metadata requirements |
| `handoff_requirements` | list[Handoff] | no | Handoff definitions |
| `validation_rules` | list[string] | yes | Rule IDs that must pass |

---

## Agent/Role Binding Fields

Each role entry:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role_id` | string | yes | Unique role identifier |
| `role_type` | string | yes | `planner`, `documentation_reviewer`, `adoption_reviewer`, `commit_reviewer`, `push_reviewer` |
| `agent_id` | string | yes | Bound agent identifier |
| `backend_command` | string | yes | CLI command to invoke |
| `backend_args` | list[string] | yes | Required arguments (e.g., `["--print"]`) |
| `agent_status` | string | yes | `available_proven`, `available_unverified`, `missing`, `blocked` |
| `risk_level` | string | yes | `low`, `medium`, `high`, `unknown` |
| `may_receive_prompt` | boolean | yes | Whether agent may receive prompts |
| `may_invoke_subagents` | boolean | yes | Default false |
| `may_run_shell` | boolean | yes | Default false |
| `may_edit_files` | boolean | yes | Default false |
| `may_generate_patches` | boolean | yes | Default false |
| `may_commit` | boolean | yes | Always false for non-human roles |
| `may_push` | boolean | yes | Always false for non-human roles |
| `human_reviewer_required` | boolean | yes | Whether human must review this role's output |

---

## Prompt Definition Fields

Each prompt entry:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prompt_id` | string | yes | Unique prompt identifier |
| `role_id` | string | yes | Role this prompt targets |
| `prompt_source_artifact` | string | yes | Path to artifact containing prompt draft |
| `prompt_text_hash` | string | yes | SHA256 of approved prompt text |
| `prompt_text_storage_policy` | string | yes | `inline`, `artifact_reference`, `external_file` |
| `prompt_status` | string | yes | `draft`, `approved`, `sent`, `captured` |
| `prompt_send_authorized` | boolean | yes | Whether sending is approved |
| `prompt_sent` | boolean | yes | Whether prompt has been sent |
| `prompt_sent_at` | string/null | no | ISO timestamp of send |
| `prompt_capture_required` | boolean | yes | Whether capture is mandatory |
| `expected_output_id` | string | yes | Expected output definition reference |
| `forbidden_actions` | list[string] | yes | Actions the prompt must not request |
| `depends_on_prompt_id` | string/null | no | Handoff dependency (must complete first) |

---

## Allowed Context Fields

Each allowed context entry:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `context_id` | string | yes | Unique identifier |
| `path` | string | yes | File path |
| `purpose` | string | yes | Why this context is included |
| `required` | boolean | yes | Whether context must be provided |
| `hash_required` | boolean | no | Whether content hash must be verified |
| `max_size_policy` | string/null | no | Size limit policy |

## Forbidden Context Fields

Each forbidden context entry:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path_pattern` | string | yes | Glob or exact path pattern |
| `reason` | string | yes | Why this context is forbidden |
| `enforcement_level` | string | yes | `block` (hard stop) or `warn` |

---

## Expected Output Fields

Each expected output entry:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `output_id` | string | yes | Unique identifier |
| `role_id` | string | yes | Role that produces this output |
| `format` | string | yes | `markdown`, `json`, `text` |
| `required_sections` | list[string] | yes | Section headings that must appear |
| `max_size_policy` | string/null | no | Maximum output size |
| `must_include_limitations` | boolean | yes | Whether output must state limitations |
| `must_include_handoff_notes` | boolean | no | Whether output must include handoff notes |

## Forbidden Output Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `patches` | boolean | true | Patches are forbidden |
| `shell_commands` | boolean | true | Shell execution instructions forbidden |
| `secret_requests` | boolean | true | Secret/credential requests forbidden |
| `commit_instructions` | boolean | true | Commit instructions forbidden |
| `push_instructions` | boolean | true | Push instructions forbidden |
| `hook_bypass_instructions` | boolean | true | Hook bypass forbidden |
| `force_push_instructions` | boolean | true | Force push forbidden |
| `raw_git_push_instructions` | boolean | true | Raw git push forbidden |
| `unauthorized_file_edits` | boolean | true | File edit requests forbidden unless role allows |
| `authority_escalation` | boolean | true | Attempts to grant self new authority forbidden |

All forbidden output fields default to `true` (forbidden). Setting any to `false` requires explicit justification and elevated approval.

---

## Safety Constraint Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `no_repo_mutation` | boolean | true | Agents must not mutate the repository |
| `no_shell_execution` | boolean | true | Agents must not execute shell commands |
| `no_subagent_invocation` | boolean | true | Agents must not invoke subagents |
| `no_source_changes` | boolean | true | No source code changes |
| `no_test_changes` | boolean | true | No test changes |
| `no_readme_changes` | boolean | true | No README changes |
| `no_docs_real_captured_tasks_changes` | boolean | true | No docs/REAL_CAPTURED_TASKS.md changes |
| `no_auto_adoption` | boolean | true | No automatic adoption of output |
| `no_auto_commit` | boolean | true | No automatic commits |
| `no_auto_push` | boolean | true | No automatic pushes |
| `human_adoption_review_required` | boolean | true | Human must review before adoption |

All safety constraints default to `true` (maximally restrictive).

---

## Authorization Flag Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `routing_authorized` | boolean | false | Whether routing has been approved |
| `backend_invocation_authorized` | boolean | false | Whether backend invocation is approved |
| `prompts_authorized` | boolean | false | Whether prompt sending is approved |
| `prompts_sent` | boolean | false | Whether prompts have been sent |
| `backend_invocation_performed` | boolean | false | Whether invocation has occurred |
| `subagent_invocation_authorized` | boolean | false | Whether subagent invocation is approved |
| `subagent_invocation_performed` | boolean | false | Whether subagent invocation occurred |
| `repo_mutation_authorized` | boolean | false | Whether repo mutation is approved |
| `adoption_authorized` | boolean | false | Whether adoption is approved |
| `adoption_execution_authorized` | boolean | false | Whether adoption execution is approved |
| `adoption_performed` | boolean | false | Whether adoption has been executed |
| `commit_authorized` | boolean | false | Whether commit of adopted content is approved |
| `push_authorized` | boolean | false | Whether push is approved |
| `execution_authorized` | boolean | false | Whether execution is approved |

All flags default to `false`.

---

## Capture Requirement Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `stdout_required` | boolean | true | Capture stdout |
| `stderr_required` | boolean | true | Capture stderr |
| `return_code_required` | boolean | true | Capture return code |
| `duration_required` | boolean | true | Capture invocation duration |
| `timeout_required` | boolean | true | Apply timeout |
| `timeout_seconds` | integer | 300 | Timeout in seconds |
| `stdout_hash_required` | boolean | true | Compute SHA256 of stdout |
| `stderr_hash_required` | boolean | true | Compute SHA256 of stderr |
| `mutation_guard_required` | boolean | true | Pre/post git status comparison |
| `capture_artifact_required` | boolean | true | Create capture metadata artifact |
| `raw_output_storage_policy` | string | `external_volatile` | `external_volatile`, `pcae_managed`, `inline_artifact` |

---

## Handoff Fields

Each handoff entry:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `handoff_from_role` | string | yes | Role producing handoff content |
| `handoff_to_role` | string | yes | Role receiving handoff content |
| `handoff_artifact` | string | yes | What is handed off |
| `handoff_required` | boolean | yes | Whether handoff must occur before downstream invocation |
| `handoff_trust_level` | string | yes | `verified_intake` (intaked output), `raw_capture` (unintaked) |
| `handoff_injection_risk` | string | yes | `low`, `medium`, `high` |
| `human_review_required` | boolean | yes | Whether human must review handoff before passing to next role |

---

## Validation Rule Set

| # | Rule ID | Description |
|---|---------|-------------|
| 1 | `PROMPT_ROLE_BINDING` | Every prompt must bind to exactly one role |
| 2 | `ROLE_AGENT_BINDING` | Every role must bind to exactly one approved agent |
| 3 | `UNKNOWN_AGENT_BLOCK` | Unknown agents are blocked by default |
| 4 | `MISSING_AGENT_BLOCK` | Missing agents cannot receive prompts |
| 5 | `UNVERIFIED_AGENT_BLOCK` | Unverified agents cannot receive prompts unless explicitly approved |
| 6 | `SUBAGENT_DISCOVERY_REQUIRED` | Subagents cannot receive prompts without discovery and approval |
| 7 | `PROMPT_SEND_REQUIRES_AUTH` | Prompt sending requires `prompts_authorized=true` |
| 8 | `INVOCATION_REQUIRES_AUTH` | Backend invocation requires `backend_invocation_authorized=true` |
| 9 | `SEND_NOT_ADOPTION` | Prompt sending must not imply `adoption_authorized=true` |
| 10 | `SEND_NOT_MUTATION` | Prompt sending must not imply `repo_mutation_authorized=true` |
| 11 | `FILE_EDIT_ROLE_CHECK` | Prompts with file-edit instructions are invalid unless role allows file edits |
| 12 | `SHELL_ROLE_CHECK` | Prompts with shell instructions are invalid unless role allows shell |
| 13 | `NO_AGENT_COMMIT_PUSH` | Commit/push instructions are invalid for non-human roles |
| 14 | `EXECUTION_NOT_INFERRED` | `execution_authorized=true` must not be inferred from prompt approval |
| 15 | `ADOPTION_REQUIRES_INTAKE` | Adoption requires output intake and review |
| 16 | `ADOPTION_EXEC_REQUIRES_APPROVAL` | Adoption execution requires separate approval |
| 17 | `CAPTURE_MANDATORY` | Capture metadata is mandatory for sent prompts |
| 18 | `MUTATION_GUARD_MANDATORY` | Mutation guard is mandatory for backend invocation |
| 19 | `CONTEXT_NO_OVERLAP` | Forbidden context patterns must not appear in allowed context |
| 20 | `STATUS_MONOTONIC` | Package status transitions must be forward-only unless blocked |
| 21 | `PROMPT_HASH_MATCH` | Sent prompt text must match the approved `prompt_text_hash` |
| 22 | `HANDOFF_DEPENDENCY` | A prompt with `depends_on_prompt_id` cannot be sent until the dependency completes and passes intake |
| 23 | `HUMAN_COMMIT_PUSH` | `commit_authorized` and `push_authorized` require human approval |
| 24 | `BLOCKED_AGENT_NO_PROMPT` | Agents with `agent_status=blocked` or `agent_status=missing` cannot receive prompts |

---

## Example Schema Instance

Based on MULTI-AGENT-PROMPT-PACKAGE-DRY-RUN-001 from the 83A–83L lifecycle:

```json
{
  "prompt_package_id": "MULTI-AGENT-PROMPT-PACKAGE-DRY-RUN-001",
  "schema_version": "0.1",
  "package_status": "closed",
  "contract_id": "MULTI-AGENT-DRY-RUN-001",
  "route_id": "MULTI-AGENT-ROUTING-83D",
  "created_at": "2026-06-23T00:00:00Z",
  "created_from_artifact": "docs/MULTI_AGENT_PROMPT_PACKAGE_DRY_RUN.md",
  "approved_by": "operator",
  "approval_artifact": "docs/MULTI_AGENT_PROMPT_INVOCATION_APPROVAL.md",
  "roles": [
    {
      "role_id": "planner-1",
      "role_type": "planner",
      "agent_id": "claude-local",
      "backend_command": "claude",
      "backend_args": ["--print"],
      "agent_status": "available_proven",
      "risk_level": "low",
      "may_receive_prompt": true,
      "may_invoke_subagents": false,
      "may_run_shell": false,
      "may_edit_files": false,
      "may_generate_patches": false,
      "may_commit": false,
      "may_push": false,
      "human_reviewer_required": true
    },
    {
      "role_id": "reviewer-1",
      "role_type": "documentation_reviewer",
      "agent_id": "claude-deepseek",
      "backend_command": "claude-deepseek",
      "backend_args": ["--print"],
      "agent_status": "available_proven",
      "risk_level": "low",
      "may_receive_prompt": true,
      "may_invoke_subagents": false,
      "may_run_shell": false,
      "may_edit_files": false,
      "may_generate_patches": false,
      "may_commit": false,
      "may_push": false,
      "human_reviewer_required": true
    }
  ],
  "prompts": [
    {
      "prompt_id": "planner-prompt-1",
      "role_id": "planner-1",
      "prompt_source_artifact": "docs/MULTI_AGENT_PROMPT_PACKAGE_DRY_RUN.md",
      "prompt_text_hash": "sha256:...",
      "prompt_text_storage_policy": "artifact_reference",
      "prompt_status": "captured",
      "prompt_send_authorized": true,
      "prompt_sent": true,
      "prompt_sent_at": "2026-06-23T18:08:00Z",
      "prompt_capture_required": true,
      "expected_output_id": "planner-output-1",
      "forbidden_actions": ["file_edit", "shell", "patch", "commit", "push"],
      "depends_on_prompt_id": null
    },
    {
      "prompt_id": "reviewer-prompt-1",
      "role_id": "reviewer-1",
      "prompt_source_artifact": "docs/MULTI_AGENT_PROMPT_PACKAGE_DRY_RUN.md",
      "prompt_text_hash": "sha256:...",
      "prompt_text_storage_policy": "artifact_reference",
      "prompt_status": "captured",
      "prompt_send_authorized": true,
      "prompt_sent": true,
      "prompt_sent_at": "2026-06-23T18:11:00Z",
      "prompt_capture_required": true,
      "expected_output_id": "reviewer-output-1",
      "forbidden_actions": ["file_edit", "shell", "patch", "commit", "push"],
      "depends_on_prompt_id": "planner-prompt-1"
    }
  ],
  "allowed_context": [
    {"context_id": "ctx-82a", "path": "docs/AGENT_CAPABILITY_REGISTRY_DESIGN.md", "purpose": "review target", "required": true},
    {"context_id": "ctx-82b", "path": "docs/AGENT_IDENTITY_CAPABILITY_PROBE.md", "purpose": "review target", "required": true}
  ],
  "forbidden_context": [
    {"path_pattern": "src/**", "reason": "source code out of scope", "enforcement_level": "block"},
    {"path_pattern": "tests/**", "reason": "test code out of scope", "enforcement_level": "block"},
    {"path_pattern": "docs/REAL_CAPTURED_TASKS.md", "reason": "governed adoption artifact", "enforcement_level": "block"},
    {"path_pattern": ".pcae/**", "reason": "internal governance state", "enforcement_level": "block"}
  ],
  "expected_outputs": [
    {
      "output_id": "planner-output-1",
      "role_id": "planner-1",
      "format": "markdown",
      "required_sections": ["Planning Summary", "Review Focus Areas", "Documentation Risk Notes", "Handoff Notes for Documentation Reviewer", "Limitations"],
      "max_size_policy": null,
      "must_include_limitations": true,
      "must_include_handoff_notes": true
    },
    {
      "output_id": "reviewer-output-1",
      "role_id": "reviewer-1",
      "format": "markdown",
      "required_sections": ["Documentation Consistency Findings", "Governance Boundary Findings", "Clarity Findings", "Suggested Improvements", "Adoption Review Notes", "Limitations"],
      "max_size_policy": null,
      "must_include_limitations": true,
      "must_include_handoff_notes": false
    }
  ],
  "forbidden_outputs": {
    "patches": true,
    "shell_commands": true,
    "secret_requests": true,
    "commit_instructions": true,
    "push_instructions": true,
    "hook_bypass_instructions": true,
    "force_push_instructions": true,
    "raw_git_push_instructions": true,
    "unauthorized_file_edits": true,
    "authority_escalation": true
  },
  "safety_constraints": {
    "no_repo_mutation": true,
    "no_shell_execution": true,
    "no_subagent_invocation": true,
    "no_source_changes": true,
    "no_test_changes": true,
    "no_readme_changes": true,
    "no_docs_real_captured_tasks_changes": true,
    "no_auto_adoption": true,
    "no_auto_commit": true,
    "no_auto_push": true,
    "human_adoption_review_required": true
  },
  "authorization_flags": {
    "routing_authorized": true,
    "backend_invocation_authorized": true,
    "prompts_authorized": true,
    "prompts_sent": true,
    "backend_invocation_performed": true,
    "subagent_invocation_authorized": false,
    "subagent_invocation_performed": false,
    "repo_mutation_authorized": false,
    "adoption_authorized": true,
    "adoption_execution_authorized": true,
    "adoption_performed": true,
    "commit_authorized": false,
    "push_authorized": false,
    "execution_authorized": false
  },
  "capture_requirements": {
    "stdout_required": true,
    "stderr_required": true,
    "return_code_required": true,
    "duration_required": true,
    "timeout_required": true,
    "timeout_seconds": 300,
    "stdout_hash_required": true,
    "stderr_hash_required": true,
    "mutation_guard_required": true,
    "capture_artifact_required": true,
    "raw_output_storage_policy": "external_volatile"
  },
  "handoff_requirements": [
    {
      "handoff_from_role": "planner-1",
      "handoff_to_role": "reviewer-1",
      "handoff_artifact": "planner stdout (planning summary + handoff notes)",
      "handoff_required": true,
      "handoff_trust_level": "verified_intake",
      "handoff_injection_risk": "medium",
      "human_review_required": true
    }
  ]
}
```

This is an illustrative example only. No executable schema file is created in 84B.

---

## Failure Cases

| # | Failure | Detection | Handling |
|---|---------|-----------|----------|
| 1 | Agent missing from PATH | `agent_status=missing` | Block prompt sending; report `MISSING_AGENT_BLOCK` |
| 2 | Agent unverified | `agent_status=available_unverified` | Block unless explicitly approved; report `UNVERIFIED_AGENT_BLOCK` |
| 3 | Prompt hash mismatch | Sent text SHA256 ≠ `prompt_text_hash` | Block sending; report `PROMPT_HASH_MATCH` violation |
| 4 | Prompt modified after approval | Hash comparison at send time | Block sending; require re-approval |
| 5 | Forbidden context included | Allowed context path matches forbidden pattern | Block package validation; report `CONTEXT_NO_OVERLAP` |
| 6 | Prompt asks for shell | Prompt text contains shell instructions; role has `may_run_shell=false` | Block sending; report `SHELL_ROLE_CHECK` |
| 7 | Prompt asks for file edits | Prompt text contains edit instructions; role has `may_edit_files=false` | Block sending; report `FILE_EDIT_ROLE_CHECK` |
| 8 | Prompt asks for commit/push | Prompt contains commit/push instructions for non-human role | Block sending; report `NO_AGENT_COMMIT_PUSH` |
| 9 | Subagent requested without discovery | Role attempts subagent invocation; no discovery artifact | Block; report `SUBAGENT_DISCOVERY_REQUIRED` |
| 10 | Capture metadata missing | Prompt sent but no capture artifact created | Block intake; report `CAPTURE_MANDATORY` |
| 11 | Mutation guard missing | Backend invoked without pre/post git status | Block intake; report `MUTATION_GUARD_MANDATORY` |
| 12 | Status transition invalid | Attempt to move from `draft_not_sent` to `intaked` (skipping send) | Block; report `STATUS_MONOTONIC` |
| 13 | Adoption attempted before intake | `adoption_authorized=true` without intake completion | Block; report `ADOPTION_REQUIRES_INTAKE` |

---

## Migration from Current Documentation-Only Package

The current documentation-only prompt package format (`docs/MULTI_AGENT_PROMPT_PACKAGE_DRY_RUN.md`) maps to this schema as follows:

| Current (markdown) | Schema field |
|-------------------|-------------|
| Prompt Package Status table | Top-level `package_status`, `prompt_package_id` |
| Approved Route table | `roles` array |
| Planner Prompt Draft code block | `prompts[0].prompt_text_hash` (hash of block content) |
| Reviewer Prompt Draft code block | `prompts[1].prompt_text_hash` |
| Planner Prompt Constraints table | `roles[0].may_*` fields + `prompts[0].forbidden_actions` |
| Handoff Model table | `handoff_requirements` array |
| Expected Planner Output table | `expected_outputs[0].required_sections` |
| Forbidden Outputs table | `forbidden_outputs` object |
| Allowed Future Context Files | `allowed_context` array |
| Forbidden Future Context | `forbidden_context` array |
| Prompt Capture Requirements | `capture_requirements` object |
| Mutation Guard Requirements | `capture_requirements.mutation_guard_required` |
| Authorization Flags table | `authorization_flags` object |

A future implementation phase could generate schema instances from existing markdown artifacts or vice versa.

---

## Schema Status

| Field | Value |
|-------|-------|
| schema_name | multi_agent_prompt_package |
| schema_version | 0.1 |
| schema_status | draft_documented |
| schema_implementation_status | not_started |

## Recommended Next Phase

**84C — Multi-Agent Capture Metadata Schema**

84C should define the machine-readable schema for capture results (stdout/stderr paths, hashes, line/byte counts, return code, duration, mutation guard results), complementing this prompt package schema.
