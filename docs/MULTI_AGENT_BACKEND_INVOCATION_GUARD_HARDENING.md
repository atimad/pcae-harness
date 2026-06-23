# Multi-Agent Backend Invocation Guard Hardening

## Purpose

Define a comprehensive guard design for validating all preconditions before PCAE sends an approved prompt to an approved backend. The guard decides whether a specific backend invocation is safe to proceed, must be blocked, or requires human review. This design hardens the prompt-to-send pipeline by enforcing exact identity matching, command matching, wrapper verification, prompt hash verification, authorization flag checking, blocked-agent prevention, subagent prevention, non-interactive invocation, timeout policy, mutation guard, and capture requirements before any backend is invoked.

## Scope

Guard-design documentation only. This artifact defines check categories, fields, decision logic, validation rules, failure cases, and an illustrative example. It does not implement guards, validators, CLI commands, or executable files.

## Non-Goals

- Guard implementation in code.
- Validator or parser implementation.
- CLI command implementation.
- Backend invocation or prompt sending.
- Output capture, intake, or adoption.
- Executable guard files outside docs.
- Wrapper changes or shell script changes.
- Source code or test changes.

## Motivation from 83G and 84B–84G

Phase 83G proved that PCAE can send approved prompts to two backends and capture output with mutation guard. However, the 83G invocation relied on human discipline for several critical checks:

1. **Agent identity** — the operator manually verified the correct backend was invoked.
2. **Command exactness** — `claude --print` and `claude-deepseek --print` were typed manually; no machine-enforced command matching.
3. **Wrapper verification** — `claude-deepseek` is a wrapper script; its integrity was not machine-verified before invocation.
4. **Prompt hash** — the sent prompt was verified to match the approved draft by human review, not SHA256 comparison.
5. **Timeout enforcement** — timeout was applied manually via shell; no governed timeout policy integration.
6. **Capture completeness** — stdout/stderr/return-code/duration were captured manually; no pre-invocation check ensured capture was configured.

The 84-series schemas (84B–84E) and state machine (84F) formalize the data and lifecycle. The command dry-run (84G) designs the query surface. This guard hardening design (84H) closes the gap between "approved for sending" and "safe to actually invoke" by defining machine-enforceable checks.

The 84A roadmap identified "Hash-verified prompt sending" (84H) as HIGH priority to close the prompt modification risk.

---

## Backend Invocation Threat Model

| # | Threat | Risk | Detection Without Guard | Detection With Guard |
|---|--------|------|------------------------|---------------------|
| T1 | Wrong backend invoked | Agent receives prompt intended for another agent | Human review only | `agent_identity_matches` check blocks mismatch |
| T2 | Blocked backend invoked | Blocked/disabled agent receives prompt | Human discipline | `agent_not_blocked` check blocks invocation |
| T3 | Unknown backend invoked | Unregistered agent receives prompt | Manual PATH check | `unknown_agent_status` check blocks invocation |
| T4 | Wrapper changed after approval | Wrapper script modified between approval and invocation | Not detected | `wrapper_mutation_check_required` blocks if hash/mtime changed |
| T5 | Interactive session opened instead of --print | Agent enters interactive mode, may mutate repo | Manual observation | `non_interactive_mode_required` blocks unless `--print` present |
| T6 | Prompt modified after approval | Sent text differs from approved package | Human comparison | `prompt_hash_matches_approved_package` blocks on SHA256 mismatch |
| T7 | Prompt hash mismatch | Hash of extracted prompt text ≠ approved hash | Not detected pre-send | `hash_match_required` blocks invocation |
| T8 | Unapproved prompt sent | Prompt not in any approved package | Human discipline | `prompt_invocation_approval_exists` blocks invocation |
| T9 | Subagent invocation requested | Parent agent spawns unauthorized subagent | Not detected pre-send | `subagent_invocation_authorized=false` blocks unless explicitly approved |
| T10 | Backend command includes unsafe args | Args beyond approved set passed to backend | Human review | `backend_args_match_exact_approved_args` blocks unexpected args |
| T11 | Timeout omitted | Invocation runs indefinitely | Manual monitoring | `timeout_seconds_present` blocks invocation without timeout |
| T12 | Capture omitted | Output not captured for intake | Manual discipline | `capture_metadata_required` blocks invocation without capture plan |
| T13 | Mutation guard omitted | No pre/post git comparison | Manual discipline | `mutation_guard_required` blocks invocation without mutation plan |
| T14 | Backend mutates repo | Agent creates/modifies files despite `--print` | Post-invocation git diff | Mutation guard detects; but guard hardening ensures guard is planned pre-invocation |
| T15 | Backend output treated as adopted content | Output applied without intake/review/approval | Human discipline | Guard does not authorize adoption; `adoption_authorized=false` enforced |

---

## Guard Design Principles

1. **Block by default.** If any required check fails, block invocation.
2. **Exact matching.** Agent ID, command, args, wrapper, and prompt hash must match exactly — no fuzzy or partial matching.
3. **No inference.** The guard does not infer authorization from state. Every required flag must be explicitly true.
4. **Pre-invocation only.** The guard runs before the backend is invoked, not after.
5. **Human-reviewable decisions.** Guard decisions include human-readable explanations, not just codes.
6. **Composable checks.** Each check category is independent; all must pass for `allow_invocation`.
7. **Evidence-preserving.** Block decisions preserve all evidence (what failed, what was expected, what was found).
8. **No side effects.** The guard itself does not invoke backends, send prompts, or mutate the repository.
9. **Fail-closed.** Missing data (null fields, absent artifacts, unknown agents) is treated as a block condition.
10. **Audit-ready.** Every guard decision produces a structured record suitable for future audit.

---

## Required Pre-Invocation Checks

Every backend invocation must pass all of the following checks before proceeding:

| # | Check | Required Value | Block Condition |
|---|-------|---------------|-----------------|
| 1 | `contract_id_matches` | true | Contract ID in invocation request ≠ approved contract |
| 2 | `prompt_package_id_matches` | true | Package ID in invocation request ≠ approved package |
| 3 | `route_approval_exists` | true | No routing approval artifact for this contract |
| 4 | `prompt_invocation_approval_exists` | true | No invocation approval artifact for this package |
| 5 | `agent_assignment_exists` | true | No agent assignment for the requested role |
| 6 | `agent_not_blocked` | true | Agent has `blocked` or `disabled` status |
| 7 | `agent_available` | true | Agent command not found on PATH |
| 8 | `agent_identity_matches` | true | Agent ID in request ≠ approved agent for role |
| 9 | `backend_command_matches_exact_approved_command` | true | Command in request ≠ approved command for agent |
| 10 | `backend_args_match_exact_approved_args` | true | Args in request ≠ approved args for agent |
| 11 | `wrapper_path_matches_expected_policy` | true | Wrapper path ≠ expected or wrapper unverified |
| 12 | `prompt_hash_matches_approved_package` | true | SHA256 of prompt text ≠ approved hash |
| 13 | `prompts_authorized` | true | `prompts_authorized=false` in authorization flags |
| 14 | `backend_invocation_authorized` | true | `backend_invocation_authorized=false` in authorization flags |
| 15 | `subagent_invocation_authorized` | false (unless explicitly approved) | `subagent_invocation_authorized=true` without explicit approval |
| 16 | `execution_authorized` | false (unless explicitly scoped) | `execution_authorized=true` without explicit scope |
| 17 | `timeout_seconds_present` | true | No timeout configured for this invocation |
| 18 | `capture_metadata_required` | true | No capture plan configured |
| 19 | `mutation_guard_required` | true | No mutation guard plan configured |
| 20 | `non_interactive_mode_required` | true | Invocation mode is not `--print` or equivalent non-interactive flag |

All 20 checks must pass for `allow_invocation`. Any single failure produces `block_invocation`.

---

## Agent Identity Checks

The guard verifies the agent's identity against the approved assignment before invocation.

| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | string | Agent identifier from the invocation request |
| `agent_display_name` | string | Human-readable name for reporting |
| `agent_status` | string | Current status: `available_proven`, `available_unverified`, `missing`, `blocked`, `unknown` |
| `agent_capability_status` | string | `verified`, `unverified`, `stale`, `missing` |
| `agent_probe_artifact` | string/null | Path to the probe artifact (e.g., 82B) |
| `approved_role_id` | string | Role this agent is approved for |
| `approved_route_id` | string | Route approval reference |
| `blocked_agent_status` | boolean | Whether the agent is in the blocked list |
| `unknown_agent_status` | boolean | Whether the agent is unknown/unregistered |

### Identity Check Logic

1. `agent_id` must exactly match the agent assigned to the requested role in the approved route.
2. `agent_status` must be `available_proven` or `available_unverified` (with explicit approval for unverified).
3. `agent_capability_status` must be `verified` or explicitly approved for `unverified`.
4. `blocked_agent_status=true` blocks invocation unconditionally.
5. `unknown_agent_status=true` blocks invocation unconditionally.
6. `agent_probe_artifact` should exist for any non-blocked agent; missing probe is a warning for proven agents, a block for unverified agents.

---

## Backend Command Checks

The guard verifies the exact backend command and arguments against the approved invocation.

| Field | Type | Description |
|-------|------|-------------|
| `approved_backend_command` | string | Approved CLI command (e.g., `claude`) |
| `approved_backend_args` | list[string] | Approved arguments (e.g., `["--print"]`) |
| `actual_backend_command` | string | Command about to be executed |
| `actual_backend_args` | list[string] | Arguments about to be passed |
| `exact_match_required` | boolean (always true) | Whether exact matching is enforced |
| `interactive_mode_blocked` | boolean (always true) | Whether interactive mode is blocked |
| `shell_expansion_blocked` | boolean (always true) | Whether shell expansion in args is blocked |
| `raw_shell_command_blocked` | boolean (always true) | Whether raw shell commands (pipes, redirects in args) are blocked |
| `unexpected_args_blocked` | boolean (always true) | Whether args not in approved list are blocked |

### Command Check Logic

1. `actual_backend_command` must be character-for-character identical to `approved_backend_command`.
2. `actual_backend_args` must be an exact ordered match of `approved_backend_args`.
3. No additional args beyond the approved set are permitted.
4. No missing args from the approved set are permitted.
5. Shell metacharacters (`;`, `|`, `&`, `$()`, backticks) in args block invocation.
6. Interactive-mode flags (`-i`, `--interactive`, absence of `--print`) block invocation.
7. File-writing flags (`-o`, `--output`, `>`) in args block invocation.

---

## Wrapper Verification Checks

For backends invoked through wrapper scripts (e.g., `claude-deepseek`), the guard verifies wrapper integrity.

| Field | Type | Description |
|-------|------|-------------|
| `wrapper_name` | string | Wrapper identifier (e.g., `claude-deepseek`) |
| `wrapper_path` | string | Absolute path to wrapper script |
| `wrapper_exists` | boolean | Whether wrapper file exists at expected path |
| `wrapper_executable` | boolean | Whether wrapper has execute permission |
| `wrapper_expected_target` | string | Expected target binary the wrapper delegates to |
| `wrapper_identity_recorded` | boolean | Whether wrapper identity was recorded in a prior probe |
| `wrapper_mutation_check_required` | boolean (always true) | Whether wrapper must be checked for changes |
| `wrapper_version_or_hash_policy` | string | `sha256_hash`, `mtime_check`, `version_probe`, `none` |
| `wrapper_unverified_blocks_invocation` | boolean (always true) | Whether unverified wrapper blocks invocation |

### Wrapper Check Logic

1. If the backend is a direct binary (no wrapper), wrapper checks are skipped with `wrapper_path=null`.
2. If the backend uses a wrapper, `wrapper_exists` must be true.
3. `wrapper_executable` must be true.
4. `wrapper_path` must match the path recorded in the probe artifact (82B).
5. If `wrapper_version_or_hash_policy=sha256_hash`, the current SHA256 of the wrapper file must match the recorded hash.
6. If `wrapper_version_or_hash_policy=mtime_check`, the modification time must not have changed since approval.
7. `wrapper_unverified_blocks_invocation=true` means any verification failure blocks invocation.
8. Wrapper changes after approval require new invocation approval.

---

## Prompt Package Checks

The guard verifies the prompt package is valid and approved for the requested invocation.

| Field | Type | Description |
|-------|------|-------------|
| `prompt_package_id` | string | Package identifier |
| `prompt_package_schema_version` | string | Schema version of the package |
| `prompt_package_status` | string | Current package status |
| `prompt_id` | string | Prompt identifier within the package |
| `role_id` | string | Role this prompt targets |
| `prompt_source_artifact` | string | Path to the artifact containing the prompt |
| `prompt_text_hash` | string | SHA256 of the approved prompt text |
| `prompt_send_authorized` | boolean | Whether sending this prompt is approved |
| `forbidden_actions_absent` | boolean | Whether the prompt does not request forbidden actions |
| `allowed_context_valid` | boolean | Whether all context files are within the allowed set |
| `forbidden_context_absent` | boolean | Whether no forbidden context is included |
| `expected_output_defined` | boolean | Whether expected output structure is defined |

### Package Check Logic

1. `prompt_package_id` must match the package in the invocation approval artifact.
2. `prompt_package_status` must be `approved_for_future_prompt_sending_only` or later valid status (not `draft_not_sent`, not `blocked`).
3. `prompt_id` must exist in the package and bind to the requested `role_id`.
4. `prompt_send_authorized` must be true.
5. `forbidden_actions_absent` must be true — if the prompt requests any forbidden action, block.
6. `allowed_context_valid` must be true — all context must be within the allowed set.
7. `forbidden_context_absent` must be true — no forbidden context patterns may be present.
8. `expected_output_defined` must be true — the package must define what output is expected.

---

## Prompt Hash Checks

The guard verifies that the prompt text about to be sent matches the approved hash.

| Field | Type | Description |
|-------|------|-------------|
| `approved_prompt_text_hash` | string | SHA256 hash from the approved prompt package |
| `extracted_prompt_text_hash` | string | SHA256 hash of the prompt text about to be sent |
| `hash_algorithm` | string (always `sha256`) | Hash algorithm used |
| `hash_match_required` | boolean (always true) | Whether hash matching is enforced |
| `hash_mismatch_action` | string (always `block_invocation`) | Action on mismatch |
| `prompt_modification_requires_new_approval` | boolean (always true) | Whether any modification requires re-approval |

### Hash Check Logic

1. Compute SHA256 of the exact prompt text that will be sent (after marker removal, after handoff insertion if applicable).
2. Compare `extracted_prompt_text_hash` to `approved_prompt_text_hash`.
3. If hashes differ, `block_invocation` immediately.
4. Hash comparison is byte-exact; whitespace normalization is not applied (the approved hash covers exact text).
5. If the prompt was modified (e.g., handoff content inserted), the modified prompt must have its own approved hash, or the modification must be an explicitly approved transformation (e.g., "insert planner stdout at HANDOFF marker" approved in the invocation approval).
6. Any prompt modification beyond the approved transformations requires a new invocation approval phase.

---

## Authorization Flag Checks

The guard verifies all required authorization flags are in the correct state.

| Flag | Required Value | Block Condition |
|------|---------------|-----------------|
| `routing_authorized` | true | Route not approved |
| `backend_invocation_authorized` | true | Invocation not approved |
| `prompts_authorized` | true | Prompt sending not approved |
| `prompts_sent` | false (pre-invocation) | Prompts already sent for this package |
| `backend_invocation_performed` | false (pre-invocation) | Invocation already performed for this role |
| `repo_mutation_authorized` | false | Repo mutation should not be authorized at invocation time |
| `adoption_authorized` | false | Adoption should not be authorized at invocation time |
| `adoption_execution_authorized` | false | Adoption execution should not be authorized |
| `commit_authorized` | false | Commit should not be authorized at invocation time |
| `push_authorized` | false | Push should not be authorized at invocation time |
| `execution_authorized` | false | Execution should not be authorized |

### Flag Check Logic

1. `routing_authorized`, `backend_invocation_authorized`, and `prompts_authorized` must all be true.
2. `prompts_sent` and `backend_invocation_performed` must be false (invocation hasn't happened yet).
3. All downstream flags (`repo_mutation_authorized`, `adoption_authorized`, `adoption_execution_authorized`, `commit_authorized`, `push_authorized`, `execution_authorized`) must be false.
4. If any downstream flag is true before invocation, block — it indicates premature authorization.

---

## Blocked-Agent Checks

The guard checks whether the requested agent is in any blocked condition.

| Condition | Detection | Action |
|-----------|-----------|--------|
| `agent_missing` | Agent command not found on PATH | Block invocation; reason `agent_missing` |
| `agent_unknown` | Agent not in the capability registry | Block invocation; reason `unknown_agent` |
| `agent_unverified` | Agent in registry but capability status is `unverified` or `stale` | Block unless explicitly approved for unverified invocation |
| `agent_explicitly_blocked` | Agent has `blocked` status in registry | Block invocation unconditionally; reason `agent_blocked` |
| `claude_kimi_missing` | `claude-kimi` not found on PATH (per 82B probe) | Block invocation; reason `agent_missing` |
| `codex_unverified` | `codex` available but unverified for PCAE governance | Block invocation; reason `agent_unverified` |
| `subagent_discovery_pending` | Subagent discovery has not been performed | Block any subagent invocation; reason `subagent_not_authorized` |
| `unknown_agent_disabled` | Any agent not in the registry is disabled by default | Block invocation; reason `unknown_agent` |

### Blocked-Agent Check Logic

1. Check the agent's status in the registry before invocation.
2. Any of the above conditions produces an immediate `block_invocation`.
3. Blocked agents cannot be "unblocked" by guard logic — only a governed verification phase can change agent status.
4. The guard never modifies agent status; it only reads and enforces.

---

## Subagent Prevention Checks

The guard prevents unauthorized subagent invocation.

| Field | Type | Description |
|-------|------|-------------|
| `subagent_invocation_requested` | boolean | Whether the invocation involves a subagent |
| `subagent_discovery_artifact_exists` | boolean | Whether a discovery artifact exists for this subagent |
| `subagent_approval_exists` | boolean | Whether explicit approval exists for this subagent |
| `parent_agent_may_invoke_subagents` | boolean | Whether the parent agent's role permits subagent invocation |
| `subagent_invocation_authorized` | boolean | Authorization flag state |
| `block_when_false` | boolean (always true) | Block when `subagent_invocation_authorized=false` |

### Subagent Prevention Logic

1. If the invocation targets a known top-level agent (not a subagent), subagent checks pass trivially.
2. If the invocation would cause a parent agent to invoke a subagent, `subagent_invocation_authorized` must be true.
3. `subagent_discovery_artifact_exists` must be true for any subagent invocation.
4. `subagent_approval_exists` must be true.
5. `parent_agent_may_invoke_subagents` must be true in the role definition.
6. In the current lifecycle, `subagent_invocation_authorized=false` always, so all subagent invocations are blocked.

---

## Non-Interactive Invocation Checks

The guard ensures the backend is invoked in non-interactive, stdout-capture mode.

| Field | Type | Description |
|-------|------|-------------|
| `print_mode_required` | boolean (always true) | `--print` or equivalent must be present |
| `interactive_session_blocked` | boolean (always true) | Interactive/conversational mode is blocked |
| `tty_required_false` | boolean (always true) | Backend must not require a TTY |
| `approval_prompt_blocked` | boolean (always true) | Backend must not present approval prompts to the user |
| `unbounded_session_blocked` | boolean (always true) | Open-ended sessions are blocked |
| `background_process_blocked` | boolean (always true) | Background/daemon invocations are blocked |

### Non-Interactive Check Logic

1. The backend args must include `--print` or the backend's documented non-interactive flag.
2. No arg may enable interactive mode (e.g., `-i`, `--interactive`, `--chat`).
3. The invocation must not allocate a TTY.
4. The invocation must not present any interactive prompts (permission prompts, confirmation dialogs).
5. The invocation must have a bounded timeout (see Timeout Policy Checks).
6. Background/daemon mode is blocked — the invocation must be a foreground process with captured stdout/stderr.

---

## Timeout Policy Checks

The guard ensures a timeout is configured and enforced.

| Field | Type | Description |
|-------|------|-------------|
| `timeout_seconds_required` | boolean (always true) | Timeout must be configured |
| `timeout_seconds_max` | integer | Maximum allowed timeout (default 600) |
| `timeout_action` | string | `kill_and_capture_partial`, `kill_discard` |
| `partial_output_policy` | string | `capture_and_classify`, `discard` |
| `timeout_failure_classification` | string | `backend_timeout` |

### Timeout Check Logic

1. `timeout_seconds` must be present and > 0.
2. `timeout_seconds` must not exceed `timeout_seconds_max` (default 600 seconds).
3. `timeout_action` must be defined (what happens when timeout fires).
4. `partial_output_policy` must be defined (what to do with partial output on timeout).
5. Missing timeout blocks invocation with reason `timeout_missing`.

---

## Mutation Guard Checks

The guard ensures a mutation guard plan is in place before invocation.

| Field | Type | Description |
|-------|------|-------------|
| `pre_git_status_required` | boolean (always true) | `git status --short` before invocation |
| `pre_git_diff_required` | boolean (always true) | `git diff --name-only` before invocation |
| `pre_git_diff_cached_required` | boolean (always true) | `git diff --cached --name-only` before invocation |
| `post_git_status_required` | boolean (always true) | `git status --short` after invocation |
| `post_git_diff_required` | boolean (always true) | `git diff --name-only` after invocation |
| `post_git_diff_cached_required` | boolean (always true) | `git diff --cached --name-only` after invocation |
| `mutation_detected_action` | string | `block_subsequent_invocations`, `quarantine` |
| `mutation_preservation_required` | boolean (always true) | Changed files must be preserved as evidence |
| `subsequent_invocations_blocked_on_mutation` | boolean (always true) | Mutation blocks further invocations |
| `quarantine_required_on_mutation` | boolean (always true) | Mutation triggers quarantine state |

### Mutation Guard Check Logic

1. The guard verifies that a mutation guard plan is configured before invocation starts.
2. The plan must include all 6 git state captures (3 pre, 3 post).
3. `mutation_detected_action` must be defined.
4. `subsequent_invocations_blocked_on_mutation=true` means if the first invocation mutates the repo, the second invocation (e.g., reviewer after planner) is blocked.
5. `quarantine_required_on_mutation=true` means mutation transitions the lifecycle to `quarantined` state.
6. Missing mutation guard plan blocks invocation with reason `mutation_guard_missing`.
7. Dirty worktree (pre-invocation git status shows unexpected changes) blocks invocation with reason `dirty_worktree` unless explicitly approved.

---

## Capture Requirement Checks

The guard ensures capture requirements are configured before invocation.

| Field | Type | Description |
|-------|------|-------------|
| `stdout_required` | boolean (always true) | stdout must be captured |
| `stderr_required` | boolean (always true) | stderr must be captured |
| `return_code_required` | boolean (always true) | Return code must be recorded |
| `duration_required` | boolean (always true) | Duration must be recorded |
| `timeout_status_required` | boolean (always true) | Timeout status must be recorded |
| `stdout_hash_required` | boolean (always true) | SHA256 of stdout must be computed |
| `stderr_hash_required` | boolean (always true) | SHA256 of stderr must be computed |
| `capture_artifact_required` | boolean (always true) | Capture metadata artifact must be created |
| `raw_output_storage_policy_required` | boolean (always true) | Storage policy must be defined |
| `metadata_only_repo_policy` | boolean (always true) | Only metadata goes in repo; raw output stays external |

### Capture Check Logic

1. All capture fields must be configured before invocation starts.
2. stdout and stderr capture paths must be defined.
3. Hash computation must be planned.
4. Storage policy must be defined (where raw output goes, how long it persists).
5. Missing capture plan blocks invocation with reason `capture_missing`.
6. `metadata_only_repo_policy=true` means raw output files are never committed to the repo — only metadata (hashes, line counts, byte counts) appears in repo artifacts.

---

## Failure Handling

| # | Failure | Guard Response |
|---|---------|---------------|
| 1 | Approved agent unavailable | `block_invocation`, reason `agent_missing` |
| 2 | Blocked agent requested | `block_invocation`, reason `agent_blocked` |
| 3 | Unknown agent requested | `block_invocation`, reason `unknown_agent` |
| 4 | Wrapper missing | `block_invocation`, reason `wrapper_missing` |
| 5 | Wrapper changed since approval | `block_invocation`, reason `wrapper_unverified`, `require_reapproval` |
| 6 | Command mismatch | `block_invocation`, reason `command_mismatch` |
| 7 | Unexpected command args | `block_invocation`, reason `unexpected_args` |
| 8 | Interactive invocation attempted | `block_invocation`, reason `interactive_mode_requested` |
| 9 | Prompt hash mismatch | `block_invocation`, reason `prompt_hash_mismatch`, `require_reapproval` |
| 10 | Prompt package missing | `block_invocation`, reason `missing_prompt_package` |
| 11 | Prompt approval missing | `block_invocation`, reason `missing_invocation_approval` |
| 12 | Backend invocation approval missing | `block_invocation`, reason `backend_invocation_not_authorized` |
| 13 | Timeout missing | `block_invocation`, reason `timeout_missing` |
| 14 | Capture plan missing | `block_invocation`, reason `capture_missing` |
| 15 | Mutation guard missing | `block_invocation`, reason `mutation_guard_missing` |
| 16 | Dirty worktree | `block_invocation`, reason `dirty_worktree` |
| 17 | Forbidden context included | `block_invocation`, reason `forbidden_context_present` |
| 18 | Forbidden action in prompt | `block_invocation`, reason `forbidden_action_present` |
| 19 | Subagent request detected | `block_invocation`, reason `subagent_not_authorized` |
| 20 | Mutation detected after prior invocation | `block_invocation`, reason `mutation_detected`, `require_quarantine` |

---

## Guard Decision Model

The guard produces exactly one decision per invocation request.

### Possible Decisions

| Decision | Meaning |
|----------|---------|
| `allow_invocation` | All checks passed; invocation may proceed |
| `block_invocation` | One or more checks failed; invocation must not proceed |
| `require_human_review` | Ambiguous condition; human must decide before proceeding |
| `require_reapproval` | A previously approved condition has changed; new approval needed |
| `require_quarantine` | Evidence of a safety violation; quarantine before further action |

### Decision Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `guard_decision` | string | `allow_invocation`, `block_invocation`, `require_human_review`, `require_reapproval`, `require_quarantine` |
| `decision_reason_codes` | list[string] | Machine-readable reason codes |
| `human_readable_explanation` | string | Full explanation of the decision |
| `required_missing_artifacts` | list[string] | Artifacts that must exist but are missing |
| `required_missing_flags` | list[string] | Authorization flags that must be true but are false |
| `blocked_agent_reason` | string/null | Why the agent is blocked (if applicable) |
| `prompt_hash_result` | string | `match`, `mismatch`, `not_checked` |
| `command_match_result` | string | `exact_match`, `mismatch`, `not_checked` |
| `wrapper_verification_result` | string | `verified`, `unverified`, `not_applicable`, `failed` |
| `mutation_guard_plan` | string | `configured`, `missing` |
| `capture_plan` | string | `configured`, `missing` |
| `safe_to_continue` | boolean | Whether invocation may proceed |

### Decision Logic

1. Run all check categories in order: identity → command → wrapper → package → hash → flags → blocked → subagent → non-interactive → timeout → mutation → capture.
2. If all checks pass: `allow_invocation`, `safe_to_continue=true`.
3. If any check fails: `block_invocation`, `safe_to_continue=false`.
4. If a condition is ambiguous (e.g., unverified agent with partial probe data): `require_human_review`.
5. If a previously approved condition changed (wrapper hash, prompt text): `require_reapproval`.
6. If mutation was detected in a prior invocation within the same capture: `require_quarantine`.
7. Multiple failures produce multiple reason codes; the first failure is sufficient to block.

---

## Blocked Reason Codes

| Code | Description |
|------|-------------|
| `missing_contract` | Contract artifact does not exist |
| `missing_prompt_package` | Prompt package artifact does not exist |
| `missing_invocation_approval` | Invocation approval artifact does not exist |
| `agent_missing` | Agent command not found on PATH |
| `agent_blocked` | Agent has `blocked` status |
| `agent_unverified` | Agent capability status is `unverified` or `stale` |
| `unknown_agent` | Agent not in the capability registry |
| `command_mismatch` | Backend command does not match approved command |
| `unexpected_args` | Backend args do not match approved args |
| `interactive_mode_requested` | Interactive mode detected in args or invocation plan |
| `wrapper_missing` | Wrapper script does not exist at expected path |
| `wrapper_unverified` | Wrapper script has changed or could not be verified |
| `prompt_hash_mismatch` | SHA256 of prompt text does not match approved hash |
| `prompts_not_authorized` | `prompts_authorized=false` |
| `backend_invocation_not_authorized` | `backend_invocation_authorized=false` |
| `subagent_not_authorized` | Subagent invocation requested but `subagent_invocation_authorized=false` |
| `timeout_missing` | No timeout configured for the invocation |
| `capture_missing` | No capture plan configured for the invocation |
| `mutation_guard_missing` | No mutation guard plan configured |
| `dirty_worktree` | Working tree has unexpected uncommitted changes |
| `forbidden_context_present` | Prompt includes context from the forbidden list |
| `forbidden_action_present` | Prompt requests a forbidden action |

---

## Example Guard Decision

Based on the 83G route (MULTI-AGENT-DRY-RUN-001), illustrative only:

### Planner Guard Decision

```json
{
  "guard_decision": "allow_invocation",
  "invocation_id": "inv-planner-001",
  "role_id": "planner-1",
  "agent_id": "claude-local",
  "backend_command": "claude",
  "backend_args": ["--print"],
  "decision_reason_codes": ["all_checks_passed"],
  "human_readable_explanation": "All 20 pre-invocation checks passed. Agent claude-local is available_proven, command matches exactly, no wrapper (direct binary), prompt hash matches approved package, all authorization flags correct, agent not blocked, no subagent invocation, non-interactive mode (--print), timeout configured (300s), capture plan configured, mutation guard plan configured.",
  "required_missing_artifacts": [],
  "required_missing_flags": [],
  "blocked_agent_reason": null,
  "prompt_hash_result": "match",
  "command_match_result": "exact_match",
  "wrapper_verification_result": "not_applicable",
  "mutation_guard_plan": "configured",
  "capture_plan": "configured",
  "safe_to_continue": true,
  "check_results": {
    "contract_id_matches": true,
    "prompt_package_id_matches": true,
    "route_approval_exists": true,
    "prompt_invocation_approval_exists": true,
    "agent_assignment_exists": true,
    "agent_not_blocked": true,
    "agent_available": true,
    "agent_identity_matches": true,
    "backend_command_matches_exact_approved_command": true,
    "backend_args_match_exact_approved_args": true,
    "wrapper_path_matches_expected_policy": true,
    "prompt_hash_matches_approved_package": true,
    "prompts_authorized": true,
    "backend_invocation_authorized": true,
    "subagent_invocation_authorized_check": true,
    "execution_authorized_check": true,
    "timeout_seconds_present": true,
    "capture_metadata_required": true,
    "mutation_guard_required": true,
    "non_interactive_mode_required": true
  }
}
```

### Reviewer Guard Decision

```json
{
  "guard_decision": "allow_invocation",
  "invocation_id": "inv-reviewer-001",
  "role_id": "reviewer-1",
  "agent_id": "claude-deepseek",
  "backend_command": "claude-deepseek",
  "backend_args": ["--print"],
  "decision_reason_codes": ["all_checks_passed"],
  "human_readable_explanation": "All 20 pre-invocation checks passed. Agent claude-deepseek is available_proven, command matches exactly, wrapper at /Users/atilamadai/.local/bin/claude-deepseek verified, prompt hash matches approved package (with approved handoff insertion), all authorization flags correct, agent not blocked, no subagent invocation, non-interactive mode (--print), timeout configured (300s), capture plan configured, mutation guard plan configured. Prior planner invocation had no mutation detected.",
  "required_missing_artifacts": [],
  "required_missing_flags": [],
  "blocked_agent_reason": null,
  "prompt_hash_result": "match",
  "command_match_result": "exact_match",
  "wrapper_verification_result": "verified",
  "mutation_guard_plan": "configured",
  "capture_plan": "configured",
  "safe_to_continue": true,
  "check_results": {
    "contract_id_matches": true,
    "prompt_package_id_matches": true,
    "route_approval_exists": true,
    "prompt_invocation_approval_exists": true,
    "agent_assignment_exists": true,
    "agent_not_blocked": true,
    "agent_available": true,
    "agent_identity_matches": true,
    "backend_command_matches_exact_approved_command": true,
    "backend_args_match_exact_approved_args": true,
    "wrapper_path_matches_expected_policy": true,
    "prompt_hash_matches_approved_package": true,
    "prompts_authorized": true,
    "backend_invocation_authorized": true,
    "subagent_invocation_authorized_check": true,
    "execution_authorized_check": true,
    "timeout_seconds_present": true,
    "capture_metadata_required": true,
    "mutation_guard_required": true,
    "non_interactive_mode_required": true
  }
}
```

These are illustrative decisions only. No invocation was performed in 84H.

---

## Validation Rules

| # | Rule ID | Description |
|---|---------|-------------|
| 1 | `GUARD_AGENT_EXACT_MATCH` | Agent ID must exactly match the approved agent for the requested role |
| 2 | `GUARD_COMMAND_EXACT_MATCH` | Backend command must exactly match the approved command |
| 3 | `GUARD_ARGS_EXACT_MATCH` | Backend args must exactly match the approved args (ordered) |
| 4 | `GUARD_BLOCKED_AGENT_PREVENTED` | Agents with `blocked` status cannot be invoked |
| 5 | `GUARD_UNKNOWN_AGENT_PREVENTED` | Agents not in the registry cannot be invoked |
| 6 | `GUARD_MISSING_AGENT_PREVENTED` | Agents not found on PATH cannot be invoked |
| 7 | `GUARD_WRAPPER_VERIFIED` | Wrapper scripts must be verified before invocation |
| 8 | `GUARD_WRAPPER_PATH_MATCHES` | Wrapper path must match the recorded probe path |
| 9 | `GUARD_PROMPT_HASH_VERIFIED` | SHA256 of prompt text must match approved hash |
| 10 | `GUARD_PROMPT_HASH_ALGORITHM_SHA256` | Hash algorithm must be SHA256 |
| 11 | `GUARD_PROMPT_APPROVAL_REQUIRED` | Prompt sending requires `prompts_authorized=true` |
| 12 | `GUARD_INVOCATION_APPROVAL_REQUIRED` | Backend invocation requires `backend_invocation_authorized=true` |
| 13 | `GUARD_NON_INTERACTIVE_REQUIRED` | Invocation must use `--print` or equivalent non-interactive mode |
| 14 | `GUARD_INTERACTIVE_BLOCKED` | Interactive/conversational mode flags are blocked |
| 15 | `GUARD_TIMEOUT_REQUIRED` | Timeout must be configured for every invocation |
| 16 | `GUARD_TIMEOUT_MAX_ENFORCED` | Timeout must not exceed maximum allowed value |
| 17 | `GUARD_CAPTURE_REQUIRED` | Capture plan must be configured before invocation |
| 18 | `GUARD_STDOUT_CAPTURE_REQUIRED` | stdout capture must be configured |
| 19 | `GUARD_STDERR_CAPTURE_REQUIRED` | stderr capture must be configured |
| 20 | `GUARD_MUTATION_GUARD_REQUIRED` | Mutation guard plan must be configured before invocation |
| 21 | `GUARD_PRE_POST_GIT_STATE_REQUIRED` | Pre/post git state captures must be planned |
| 22 | `GUARD_SUBAGENT_BLOCKED_UNLESS_APPROVED` | Subagent invocation is blocked unless `subagent_invocation_authorized=true` |
| 23 | `GUARD_PROMPT_NOT_ADOPTION` | Prompt approval does not imply adoption authorization |
| 24 | `GUARD_INVOCATION_NOT_MUTATION` | Invocation approval does not imply repo mutation authorization |
| 25 | `GUARD_DIRTY_WORKTREE_BLOCKS` | Dirty worktree blocks invocation unless explicitly approved |
| 26 | `GUARD_COMMAND_MISMATCH_BLOCKS` | Command mismatch blocks invocation |
| 27 | `GUARD_HASH_MISMATCH_BLOCKS` | Prompt hash mismatch blocks invocation |
| 28 | `GUARD_MISSING_CAPTURE_BLOCKS` | Missing capture plan blocks invocation |
| 29 | `GUARD_MUTATION_BLOCKS_SUBSEQUENT` | Mutation after invocation blocks subsequent invocations in the same capture |
| 30 | `GUARD_SHELL_METACHAR_BLOCKED` | Shell metacharacters in args block invocation |
| 31 | `GUARD_FILE_WRITE_ARGS_BLOCKED` | File-writing flags in args block invocation |
| 32 | `GUARD_EXECUTION_AUTH_FALSE` | `execution_authorized` must be false at guard check time |
| 33 | `GUARD_ADOPTION_AUTH_FALSE` | `adoption_authorized` must be false at guard check time |
| 34 | `GUARD_COMMIT_PUSH_AUTH_FALSE` | `commit_authorized` and `push_authorized` must be false at guard check time |
| 35 | `GUARD_NO_SIDE_EFFECTS` | The guard itself must not invoke backends, send prompts, or mutate the repository |
| 36 | `GUARD_DECISION_STRUCTURED` | Guard decision must include all required output fields |
| 37 | `GUARD_REASON_CODES_PRESENT` | Block decisions must include at least one reason code |
| 38 | `GUARD_HUMAN_EXPLANATION_PRESENT` | All decisions must include a human-readable explanation |
| 39 | `GUARD_FORBIDDEN_CONTEXT_CHECKED` | Forbidden context patterns must be checked before invocation |
| 40 | `GUARD_FORBIDDEN_ACTION_CHECKED` | Forbidden action patterns must be checked before invocation |

**40 validation rules.**

---

## Failure Cases

| # | Failure | Guard Impact | Handling |
|---|---------|-------------|----------|
| 1 | Approved agent unavailable | `block_invocation` | Report `agent_missing`; cannot proceed until agent is available |
| 2 | Blocked agent requested | `block_invocation` | Report `agent_blocked`; requires governed verification phase to unblock |
| 3 | Unknown agent requested | `block_invocation` | Report `unknown_agent`; requires registry addition and verification |
| 4 | Wrapper missing | `block_invocation` | Report `wrapper_missing`; wrapper must be restored or re-installed |
| 5 | Wrapper changed since approval | `block_invocation` + `require_reapproval` | Report `wrapper_unverified`; new invocation approval required |
| 6 | Command mismatch | `block_invocation` | Report `command_mismatch`; correct the command or update approval |
| 7 | Unexpected command args | `block_invocation` | Report `unexpected_args`; remove unapproved args or update approval |
| 8 | Interactive invocation attempted | `block_invocation` | Report `interactive_mode_requested`; add `--print` flag |
| 9 | Prompt hash mismatch | `block_invocation` + `require_reapproval` | Report `prompt_hash_mismatch`; prompt was modified, new approval required |
| 10 | Prompt package missing | `block_invocation` | Report `missing_prompt_package`; create prompt package first |
| 11 | Prompt approval missing | `block_invocation` | Report `missing_invocation_approval`; create invocation approval first |
| 12 | Backend invocation approval missing | `block_invocation` | Report `backend_invocation_not_authorized`; create invocation approval first |
| 13 | Timeout missing | `block_invocation` | Report `timeout_missing`; configure timeout before invocation |
| 14 | Capture plan missing | `block_invocation` | Report `capture_missing`; configure capture plan before invocation |
| 15 | Mutation guard missing | `block_invocation` | Report `mutation_guard_missing`; configure mutation guard before invocation |
| 16 | Dirty worktree | `block_invocation` | Report `dirty_worktree`; clean worktree or explicitly approve invocation with dirty state |
| 17 | Forbidden context included | `block_invocation` | Report `forbidden_context_present`; remove forbidden context from prompt |
| 18 | Forbidden action in prompt | `block_invocation` | Report `forbidden_action_present`; remove forbidden action request from prompt |
| 19 | Subagent request detected | `block_invocation` | Report `subagent_not_authorized`; subagent invocation requires discovery and explicit approval |
| 20 | Mutation detected after prior invocation | `block_invocation` + `require_quarantine` | Report `mutation_detected`; quarantine and preserve evidence before any further invocations |

**20 failure cases.**

---

## Guard Design Status

| Field | Value |
|-------|-------|
| guard_design_name | multi_agent_backend_invocation_guard |
| guard_design_version | 0.1 |
| guard_design_status | draft_documented |
| guard_implementation_status | not_started |

## Recommended Next Phase

**84I — Multi-Agent Prompt Capture Storage Policy**

84I should document where prompt texts, prompt hashes, stdout/stderr files, capture metadata, and retention policies live, still without implementing storage unless separately scoped. This closes the capture volatility risk (outputs in `/tmp`) identified in 84A.
