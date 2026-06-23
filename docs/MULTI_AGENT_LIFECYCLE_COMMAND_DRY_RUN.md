# Multi-Agent Lifecycle Command Dry-Run Design

## Purpose

Design a dry-run command surface for inspecting multi-agent lifecycle state, checking transition guards, showing allowed/blocked transitions, previewing next steps, and summarizing lifecycle status. All commands are read-only and produce JSON output.

## Scope

Command-surface design documentation only. This artifact defines proposed command names, inputs, outputs, JSON shapes, guard checks, and safety constraints. It does not implement commands, modify source code, or create executable files.

## Non-Goals

- Command implementation in code.
- CLI changes or pyproject.toml modifications.
- Backend invocation or prompt sending.
- Output capture, intake, or adoption.
- State machine implementation.
- Executable command files outside docs.

## Motivation from 83A–83L and 84B–84F

The 83A–83L lifecycle was orchestrated manually across 12 phases. The four schemas (84B–84E) structure lifecycle data. The state machine (84F) defines states, transitions, and guards. This command design provides the user-facing interface for querying that state machine, analogous to the existing `pcae lifecycle backend-output-adoption status/next/summary` commands for single-agent lifecycles.

## Command Design Principles

1. **Read-only.** All commands are dry-run; none mutate state.
2. **JSON-first.** All commands support `--json` for machine-readable output.
3. **Guard-transparent.** Commands explain *why* a transition is blocked, not just that it is.
4. **Artifact-aware.** Commands check for required artifacts and report missing ones.
5. **Flag-consistent.** Commands validate authorization flags against the state machine.
6. **Safety-explicit.** `execution_authorized=false` and `dry_run=true` appear in every output.
7. **No inference.** Commands never infer authorization from state — they report what is explicitly set.

---

## Proposed Command Namespace

```
pcae multi-agent lifecycle <subcommand> [options]
```

All subcommands require `--dry-run`. Calling without `--dry-run` blocks with an error explaining that non-dry-run multi-agent lifecycle commands are not yet implemented.

---

## Proposed Dry-Run Commands

| # | Command | Purpose |
|---|---------|---------|
| 1 | `pcae multi-agent lifecycle status --dry-run --json` | Show current lifecycle state |
| 2 | `pcae multi-agent lifecycle next --dry-run --json` | Show allowed next transitions |
| 3 | `pcae multi-agent lifecycle check-transition --from <state> --to <state> --dry-run --json` | Check if a specific transition is allowed |
| 4 | `pcae multi-agent lifecycle explain-blocked --from <state> --to <state> --dry-run --json` | Explain why a transition is blocked |
| 5 | `pcae multi-agent lifecycle required-artifacts --state <state> --dry-run --json` | Show required artifacts for a state |
| 6 | `pcae multi-agent lifecycle flags --state <state> --dry-run --json` | Show authorization flags for a state |
| 7 | `pcae multi-agent lifecycle failures --dry-run --json` | Show failure/quarantine state |
| 8 | `pcae multi-agent lifecycle summary --dry-run --json` | Consolidated lifecycle summary |

---

## Command Input Model

All commands accept:

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| `--dry-run` | flag | yes | Required for all commands |
| `--json` | flag | no | Machine-readable JSON output |
| `--contract-id` | string | no | Filter by contract ID (default: detect from artifacts) |

Commands 3–4 additionally accept:

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| `--from` | string | yes | Source state |
| `--to` | string | yes | Target state |

Commands 5–6 additionally accept:

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| `--state` | string | yes | State to inspect |

## Command Output Model

All commands produce:

| Output Field | Type | Present In |
|-------------|------|-----------|
| `dry_run` | boolean (always true) | all commands |
| `execution_authorized` | boolean (always false) | all commands |
| `command` | string | all commands |
| `state_machine_version` | string | all commands |
| `timestamp` | string | all commands |

---

## JSON Output Conventions

- Stable `snake_case` keys.
- Machine-readable booleans (`true`/`false`), never strings.
- Human-readable `explanation` fields alongside machine codes.
- Explicit `dry_run: true` in every response.
- Explicit `execution_authorized: false` in every response.
- Explicit error codes from the blocked/error reason code set.
- Paths as repository-relative strings.
- Hashes as lowercase hex SHA256 strings.
- Counts as integers.
- Missing/unknown values as `null` or explicit `"unknown"` status.
- Lists always present (empty `[]` rather than absent).

---

## 1. State Inspection Command

```
pcae multi-agent lifecycle status --dry-run --json
```

### Output Fields

```json
{
  "command": "multi-agent-lifecycle-status",
  "dry_run": true,
  "execution_authorized": false,
  "state_machine_version": "0.1",
  "current_state": "closed",
  "contract_id": "MULTI-AGENT-DRY-RUN-001",
  "prompt_package_id": "MULTI-AGENT-PROMPT-PACKAGE-DRY-RUN-001",
  "known_artifacts": [
    "docs/MULTI_AGENT_TASK_CONTRACT.md",
    "docs/MULTI_AGENT_ROUTING_APPROVAL.md"
  ],
  "missing_artifacts": [],
  "authorization_flags": {
    "routing_authorized": true,
    "backend_invocation_authorized": true,
    "prompts_authorized": true,
    "prompts_sent": true,
    "adoption_authorized": true,
    "adoption_performed": true,
    "lifecycle_verified": true,
    "lifecycle_closed": true,
    "execution_authorized": false
  },
  "blocked_agents": ["claude-kimi", "codex", "subagents", "unknown"],
  "deferred_items": ["DF-1", "DF-2", "DF-3", "DF-4"],
  "dirty_worktree": false,
  "unpushed_commits": 0
}
```

---

## 2. Next Transition Command

```
pcae multi-agent lifecycle next --dry-run --json
```

### Output Fields

```json
{
  "command": "multi-agent-lifecycle-next",
  "dry_run": true,
  "execution_authorized": false,
  "current_state": "output_intaked",
  "allowed_next_states": ["adoption_reviewed", "blocked"],
  "blocked_next_states": ["adoption_executed", "closed", "prompt_sent_captured"],
  "recommended_next_state": "adoption_reviewed",
  "required_artifacts_for_next_state": ["docs/MULTI_AGENT_ADOPTION_REVIEW.md"],
  "required_authorization_flags": {"adoption_candidates_identified": true},
  "blocked_reasons": []
}
```

---

## 3. Transition Guard Check Command

```
pcae multi-agent lifecycle check-transition --from <state> --to <state> --dry-run --json
```

### Output Fields

```json
{
  "command": "multi-agent-lifecycle-check-transition",
  "dry_run": true,
  "execution_authorized": false,
  "from_state": "prompt_invocation_approved",
  "to_state": "prompt_sent_captured",
  "transition_allowed": true,
  "guard_result": "all_guards_passed",
  "required_artifacts": ["capture metadata (84C schema)"],
  "present_artifacts": [],
  "missing_artifacts": ["capture metadata"],
  "required_authorization_flags": {
    "backend_invocation_authorized": true,
    "prompts_authorized": true
  },
  "forbidden_flags": {"execution_authorized": false},
  "forbidden_file_patterns": ["src/**", "tests/**", "docs/REAL_CAPTURED_TASKS.md"],
  "human_review_required": false,
  "mutation_guard_required": true,
  "capture_metadata_required": true,
  "output_intake_required": false,
  "adoption_approval_required": false,
  "blocked_reasons": []
}
```

---

## 4. Blocked Transition Explanation Command

```
pcae multi-agent lifecycle explain-blocked --from <state> --to <state> --dry-run --json
```

### Output Fields

```json
{
  "command": "multi-agent-lifecycle-explain-blocked",
  "dry_run": true,
  "execution_authorized": false,
  "from_state": "output_intaked",
  "to_state": "adoption_executed",
  "blocked": true,
  "blocked_reason_codes": ["forbidden_transition"],
  "human_readable_explanation": "Cannot transition from output_intaked to adoption_executed: adoption review and adoption approval must occur first. The lifecycle requires output_intaked -> adoption_reviewed -> adoption_approved -> adoption_executed.",
  "required_prior_states": ["adoption_reviewed", "adoption_approved"],
  "required_missing_artifacts": [
    "docs/MULTI_AGENT_ADOPTION_REVIEW.md",
    "docs/MULTI_AGENT_ADOPTION_APPROVAL.md"
  ],
  "required_missing_approvals": ["adoption_authorized"],
  "safety_boundary": "Adoption execution requires explicit approval after review. Skipping review and approval is a blocked transition.",
  "suggested_safe_next_steps": [
    "Transition to adoption_reviewed first by creating adoption review artifact",
    "Then transition to adoption_approved by creating adoption approval artifact"
  ]
}
```

---

## 5. Required Artifact Command

```
pcae multi-agent lifecycle required-artifacts --state <state> --dry-run --json
```

### Output Fields

```json
{
  "command": "multi-agent-lifecycle-required-artifacts",
  "dry_run": true,
  "execution_authorized": false,
  "state": "adoption_approved",
  "required_artifacts": [
    {"path": "docs/MULTI_AGENT_ADOPTION_APPROVAL.md", "schema": "83J", "status": "present"},
    {"path": "docs/MULTI_AGENT_ADOPTION_REVIEW.md", "schema": "83I", "status": "present"}
  ],
  "optional_artifacts": [],
  "present_artifacts": 2,
  "missing_artifacts": 0,
  "artifact_status": "all_present"
}
```

---

## 6. Authorization Flag Inspection Command

```
pcae multi-agent lifecycle flags --state <state> --dry-run --json
```

### Output Fields

```json
{
  "command": "multi-agent-lifecycle-flags",
  "dry_run": true,
  "execution_authorized": false,
  "state": "prompt_invocation_approved",
  "allowed_true_flags": [
    "routing_authorized",
    "backend_invocation_authorized",
    "prompts_authorized"
  ],
  "required_false_flags": [
    "prompts_sent",
    "backend_invocation_performed",
    "adoption_authorized",
    "adoption_performed",
    "execution_authorized",
    "subagent_invocation_authorized",
    "commit_authorized",
    "push_authorized"
  ],
  "forbidden_true_flags": [
    "execution_authorized",
    "subagent_invocation_authorized"
  ],
  "current_flags": {},
  "flag_consistency_result": "consistent",
  "violations": []
}
```

---

## 7. Failure/Quarantine Inspection Command

```
pcae multi-agent lifecycle failures --dry-run --json
```

### Output Fields

```json
{
  "command": "multi-agent-lifecycle-failures",
  "dry_run": true,
  "execution_authorized": false,
  "failure_detected": false,
  "failure_type": null,
  "failure_stage": null,
  "quarantine_required": false,
  "blocked_state_required": false,
  "mutation_detected": false,
  "forbidden_files_changed": false,
  "unsafe_agents_detected": false,
  "recovery_options": [],
  "human_review_required": false
}
```

---

## 8. Summary Command

```
pcae multi-agent lifecycle summary --dry-run --json
```

### Output Fields

```json
{
  "command": "multi-agent-lifecycle-summary",
  "dry_run": true,
  "execution_authorized": false,
  "lifecycle_status": "closed",
  "lifecycle_outcome": "closed_successfully",
  "contract_id": "MULTI-AGENT-DRY-RUN-001",
  "prompt_package_id": "MULTI-AGENT-PROMPT-PACKAGE-DRY-RUN-001",
  "current_state": "closed",
  "phase_count": 12,
  "artifact_count": 18,
  "invocation_count": 2,
  "capture_status": "captured",
  "intake_status": "reviewed",
  "adoption_status": "executed",
  "adoption_candidates_executed": 3,
  "deferred_count": 4,
  "rejected_count": 4,
  "boundary_status": "all_preserved",
  "health_status": "healthy",
  "push_status": "clean"
}
```

---

## Global Dry-Run Invariants

Every command output must include:

| Invariant | Value | Reason |
|-----------|-------|--------|
| `dry_run` | `true` | Commands are read-only |
| `execution_authorized` | `false` | No execution occurs |
| `backend_invocation_performed` | `false` | No backends invoked by commands |
| `prompts_sent` | `false` | No prompts sent by commands |
| `repo_mutation_performed` | `false` | No repo changes by commands |
| `adoption_performed` | `false` | No adoption by commands |
| `commit_performed` | `false` | No commits by commands |
| `push_performed` | `false` | No pushes by commands |

---

## Safety Constraints

1. Commands must be read-only — no state mutation, no file creation, no git operations.
2. Commands must not invoke backends.
3. Commands must not send prompts.
4. Commands must not mutate the repository.
5. Commands must not adopt outputs.
6. Commands must not commit or push.
7. Commands must not infer authorization from state alone — they report what is explicitly set.
8. Commands must explain missing approvals with human-readable text.
9. Commands must treat unknown agents as blocked.
10. Commands must require explicit future execution phases for any real work.
11. Non-dry-run invocation must be blocked with an explicit error.

---

## Blocked/Error Reason Codes

| Code | Description |
|------|-------------|
| `missing_required_artifact` | A required artifact does not exist |
| `missing_authorization` | A required authorization flag is not set |
| `forbidden_transition` | The requested transition is not allowed |
| `blocked_agent` | An agent with `blocked` status appears in the route |
| `unknown_agent` | An unregistered agent appears in the route |
| `subagent_not_discovered` | A subagent is referenced without discovery |
| `prompt_hash_mismatch` | Sent prompt hash does not match approved package |
| `capture_metadata_missing` | Capture metadata artifact does not exist |
| `mutation_guard_missing` | Mutation guard was not performed |
| `mutation_detected` | Repository mutation was detected |
| `output_intake_missing` | Output intake artifact does not exist |
| `adoption_approval_missing` | Adoption approval artifact does not exist |
| `forbidden_file_changed` | A forbidden file was modified |
| `dirty_worktree` | Working tree has uncommitted changes |
| `unpushed_commits` | Commits exist that have not been pushed |
| `raw_push_detected` | Raw git push was used instead of governed push |
| `force_push_detected` | Force push was used |
| `execution_not_authorized` | Execution is not authorized |

---

## Validation Rules

| # | Rule ID | Description |
|---|---------|-------------|
| 1 | `CMD_DRY_RUN_REQUIRED` | All commands require `--dry-run` flag |
| 2 | `CMD_NO_BACKEND` | Commands must not invoke backends |
| 3 | `CMD_NO_PROMPT` | Commands must not send prompts |
| 4 | `CMD_NO_MUTATION` | Commands must not mutate repository |
| 5 | `CMD_NO_COMMIT_PUSH` | Commands must not commit or push |
| 6 | `CMD_TRANSITIONS_MATCH_SM` | Transition outputs must match state machine (84F) |
| 7 | `CMD_ARTIFACTS_MATCH_MATRIX` | Required artifacts must match artifact matrix (84F) |
| 8 | `CMD_FLAGS_MATCH_MATRIX` | Flags must match authorization flag matrix (84F) |
| 9 | `CMD_BLOCKED_EXPLAINS` | Blocked transitions must include reason codes and explanation |
| 10 | `CMD_UNKNOWN_AGENTS_BLOCKED` | Unknown agents reported as blocked |
| 11 | `CMD_DIRTY_WORKTREE_REPORTED` | Dirty worktree reported in status |
| 12 | `CMD_UNPUSHED_REPORTED` | Unpushed commits reported in status |
| 13 | `CMD_FORBIDDEN_FILES_REPORTED` | Forbidden file changes reported in failures |
| 14 | `CMD_EXECUTION_NEVER_INFERRED` | `execution_authorized` never set to true by commands |
| 15 | `CMD_JSON_STABLE_KEYS` | JSON uses stable snake_case keys |
| 16 | `CMD_JSON_BOOLEANS` | JSON uses true/false, not string booleans |
| 17 | `CMD_JSON_NULL_FOR_MISSING` | Missing values use null, not absent keys |
| 18 | `CMD_JSON_EMPTY_LISTS` | Empty collections use `[]`, not absent keys |
| 19 | `CMD_GUARD_RESULT_DETAILED` | Guard check includes per-guard pass/fail detail |
| 20 | `CMD_BLOCKED_SUGGESTS_NEXT` | Blocked explanations include suggested safe next steps |
| 21 | `CMD_ARTIFACT_STATUS_PER_ENTRY` | Artifact command reports status per artifact |
| 22 | `CMD_FLAG_VIOLATIONS_LISTED` | Flag command lists any consistency violations |
| 23 | `CMD_FAILURE_RECOVERY_OPTIONS` | Failure command lists recovery options |
| 24 | `CMD_SUMMARY_AGGREGATES` | Summary aggregates all lifecycle dimensions |
| 25 | `CMD_NON_DRY_RUN_BLOCKED` | Non-dry-run invocation returns explicit error |
| 26 | `CMD_CONTRACT_ID_DETECTED` | Contract ID auto-detected from artifacts when not specified |
| 27 | `CMD_STATE_MACHINE_VERSION` | State machine version included in every output |

**27 validation rules.**

---

## Failure Cases

| # | Failure | Command Impact | Handling |
|---|---------|---------------|----------|
| 1 | State cannot be inferred | `status` returns `"current_state": "unknown"` | Report `missing_required_artifact` for all state-determining artifacts |
| 2 | State machine artifact missing | All commands return warning | Report `missing_required_artifact` for state machine doc |
| 3 | Schema artifact missing | `required-artifacts` reports gap | Report specific missing schema |
| 4 | Required artifact missing | `check-transition` blocks transition | Report `missing_required_artifact` |
| 5 | Unknown current state | `status` returns `"unknown"` | List present artifacts to help determine state |
| 6 | Invalid requested transition | `check-transition` returns `"transition_allowed": false` | Report `forbidden_transition` with explanation |
| 7 | Conflicting authorization flags | `flags` returns violations | Report specific flag conflicts |
| 8 | Dirty worktree | `status` reports `"dirty_worktree": true` | Warn but do not block read-only commands |
| 9 | Unpushed commits | `status` reports `"unpushed_commits": N` | Warn; block closure-state detection |
| 10 | Forbidden file modified | `failures` reports `"forbidden_files_changed": true` | Report affected files |
| 11 | Blocked agent in route | `status` reports in `blocked_agents` | Report `blocked_agent` |
| 12 | Prompt package missing | `check-transition` blocks package-dependent transitions | Report `missing_required_artifact` |
| 13 | Capture metadata missing | `check-transition` blocks intake-dependent transitions | Report `capture_metadata_missing` |
| 14 | Output intake missing | `check-transition` blocks adoption-dependent transitions | Report `output_intake_missing` |
| 15 | Adoption approval missing | `check-transition` blocks execution-dependent transitions | Report `adoption_approval_missing` |
| 16 | Quarantine required | `failures` reports `"quarantine_required": true` | Report mutation details and recovery options |

**16 failure cases.**

---

## Implementation Non-Goals

This design explicitly does not:

1. Implement any command in source code.
2. Modify `pyproject.toml` or CLI entry points.
3. Create tests for the proposed commands.
4. Create `.pcae/` state storage for multi-agent lifecycles.
5. Create executable scripts or wrappers.
6. Implement non-dry-run variants of any command.
7. Define how commands interact with the existing single-agent lifecycle commands.

These are deferred to future implementation phases after the command design is reviewed and approved.

---

## Command Design Status

| Field | Value |
|-------|-------|
| command_design_name | multi_agent_lifecycle_command_dry_run |
| command_design_version | 0.1 |
| command_design_status | draft_documented |
| command_implementation_status | not_started |

## Recommended Next Phase

**84H — Multi-Agent Backend Invocation Guard Hardening**

84H should document or design hardening for backend invocation guards: prompt hash verification at send time, mutation guard enforcement, capture metadata validation, and blocked-agent pre-checks. Still documentation-only unless separately scoped for implementation.
