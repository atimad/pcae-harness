# Multi-Agent Capture Metadata Schema

## Purpose

Define a stable, machine-readable schema for multi-agent capture metadata. The schema provides structured fields for each backend invocation capture, including prompt/package linkage, backend identity, stdout/stderr metadata, timing, return code, timeout, mutation guards, storage policy, multi-agent grouping, validation rules, and failure classification.

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

## Motivation from 83G and 84B

Phase 83G captured multi-agent outputs manually: stdout/stderr redirected to `/tmp`, metadata (lines, bytes, SHA256) computed via shell commands, mutation guard run as manual git status checks. Phase 84B defined a prompt package schema that references capture requirements but does not define the capture metadata structure itself.

Lessons from 84A identified capture volatility (volatile `/tmp` storage) and missing machine-enforced metadata validation as risks. A capture metadata schema closes these gaps by providing:

1. **Structured invocation records** — each invocation is a discrete record with mandatory fields.
2. **Hash-verifiable outputs** — stdout/stderr SHA256 hashes enable tamper-detection.
3. **Mutation guard records** — pre/post git state captured as structured fields, not prose.
4. **Storage policy** — explicit rules for where raw outputs live and how long they persist.
5. **Linkage** — every capture record traces back to its prompt package, contract, and role.

## Schema Design Principles

1. **One capture per lifecycle.** A capture record groups all invocations for one prompt package execution.
2. **One invocation per role per prompt.** Each invocation binds to exactly one role and one prompt.
3. **Metadata-first.** The schema captures metadata about outputs, not the outputs themselves.
4. **Hash-mandatory.** Every captured output must have a SHA256 hash recorded.
5. **Mutation-aware.** Mutation guard results are first-class fields, not optional annotations.
6. **Failure-explicit.** Every failure is classified with type, stage, and safe-to-continue assessment.
7. **Status-driven.** Capture status transitions are monotonic and gated on downstream lifecycle events.
8. **No authority inference.** Capture metadata does not imply intake, adoption, or execution authorization.

---

## Capture Lifecycle State

```
planned → running → captured → intaked → closed
                  ↘ partial ↗
                  ↘ failed
                  ↘ blocked
```

| Status | Description |
|--------|-------------|
| `planned` | Capture configured, invocations not yet started |
| `running` | At least one invocation in progress |
| `captured` | All planned invocations complete, metadata recorded |
| `partial` | Some invocations succeeded, some failed or were skipped |
| `blocked` | Capture blocked before any invocation (agent missing, approval missing) |
| `failed` | All invocations failed or critical failure prevents completion |
| `intaked` | Downstream intake phase has processed the captured outputs |
| `closed` | Lifecycle verification complete |

---

## Required Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `capture_id` | string | yes | Unique capture identifier |
| `schema_version` | string | yes | Schema version (e.g., `0.1`) |
| `capture_status` | string | yes | Current lifecycle status |
| `capture_outcome` | string | yes | Outcome classification |
| `contract_id` | string | yes | Bound multi-agent contract ID |
| `prompt_package_id` | string | yes | Bound prompt package ID |
| `route_id` | string/null | no | Routing approval reference |
| `capture_artifact` | string | yes | Path to capture artifact document |
| `capture_created_at` | string | yes | ISO timestamp |
| `invocations` | list[Invocation] | yes | Invocation records |
| `mutation_guard_summary` | MutationGuardSummary | yes | Aggregate mutation guard result |
| `validation_result` | ValidationResult | yes | Metadata validation outcome |
| `failure_classification` | FailureClassification/null | no | Present if any failure occurred |
| `storage_policy` | StoragePolicy | yes | Raw output storage rules |

---

## Invocation Identity Fields

Each invocation entry:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `invocation_id` | string | yes | Unique invocation identifier |
| `role_id` | string | yes | Role this invocation serves |
| `role_type` | string | yes | `planner`, `documentation_reviewer`, etc. |
| `agent_id` | string | yes | Agent performing the invocation |
| `backend_command` | string | yes | CLI command invoked |
| `backend_args` | list[string] | yes | Arguments passed (e.g., `["--print"]`) |
| `backend_invocation_authorized` | boolean | yes | Whether invocation was approved |
| `prompt_id` | string | yes | Prompt sent in this invocation |
| `prompt_text_hash` | string | yes | SHA256 of sent prompt text |
| `prompt_sent` | boolean | yes | Whether prompt was actually sent |
| `prompt_sent_at` | string/null | no | ISO timestamp of send |
| `prompt_source_artifact` | string | yes | Path to prompt source |

## Prompt/Package Linkage Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `contract_id` | string | yes | Multi-agent contract ID |
| `prompt_package_id` | string | yes | Prompt package ID |
| `prompt_package_schema_version` | string | yes | Prompt package schema version |
| `prompt_invocation_approval_artifact` | string | yes | Path to invocation approval |
| `prompt_package_artifact` | string | yes | Path to prompt package |
| `route_approval_artifact` | string | yes | Path to routing approval |
| `prompt_id` | string | yes | Prompt ID within the package |
| `role_id` | string | yes | Role ID within the package |
| `expected_output_id` | string | yes | Expected output definition ID |

## Backend Identity Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_id` | string | yes | Agent identifier |
| `agent_display_name` | string | yes | Human-readable name |
| `backend_command` | string | yes | CLI command |
| `backend_args` | list[string] | yes | Command arguments |
| `backend_version` | string/null | no | Reported version if known |
| `backend_status` | string | yes | `available_proven`, `available_unverified`, `missing`, `blocked` |
| `wrapper_path` | string/null | no | Path to wrapper script if applicable |
| `risk_level` | string | yes | `low`, `medium`, `high`, `unknown` |
| `blocked_agent_check` | boolean | yes | Whether blocked-agent check was performed |

---

## stdout Metadata Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `stdout_required` | boolean | yes | Whether stdout capture was required |
| `stdout_path` | string/null | yes | Path to captured stdout file |
| `stdout_storage_location` | string | yes | `external_volatile`, `pcae_managed`, `inline` |
| `stdout_line_count` | integer/null | yes | Line count (null if missing) |
| `stdout_byte_count` | integer/null | yes | Byte count (null if missing) |
| `stdout_sha256` | string/null | yes | SHA256 hash (null if missing) |
| `stdout_truncated` | boolean | yes | Whether output was truncated |
| `stdout_truncation_reason` | string/null | no | Reason if truncated |
| `stdout_format` | string | yes | `markdown`, `json`, `text`, `unknown` |
| `stdout_contains_expected_sections` | boolean/null | no | Whether expected sections were detected |

## stderr Metadata Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `stderr_required` | boolean | yes | Whether stderr capture was required |
| `stderr_path` | string/null | yes | Path to captured stderr file |
| `stderr_storage_location` | string | yes | `external_volatile`, `pcae_managed`, `inline` |
| `stderr_line_count` | integer/null | yes | Line count (null if missing) |
| `stderr_byte_count` | integer/null | yes | Byte count (null if missing) |
| `stderr_sha256` | string/null | yes | SHA256 hash (null if missing) |
| `stderr_truncated` | boolean | yes | Whether stderr was truncated |
| `stderr_truncation_reason` | string/null | no | Reason if truncated |
| `stderr_empty` | boolean | yes | Whether stderr was empty or contained only metadata |
| `stderr_contains_errors` | boolean | yes | Whether stderr contains error messages |

---

## Timing and Return-Code Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `started_at` | string | yes | ISO timestamp of invocation start |
| `completed_at` | string/null | yes | ISO timestamp of completion (null if timed out) |
| `duration_seconds` | number | yes | Wall-clock duration |
| `return_code` | integer/null | yes | Process return code (null if timed out) |
| `return_code_captured` | boolean | yes | Whether return code was captured |
| `success_exit_code` | integer | yes | Expected success code (typically 0) |

## Timeout Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timeout_seconds` | integer | yes | Configured timeout |
| `timed_out` | boolean | yes | Whether invocation timed out |
| `timeout_policy` | string | yes | `kill_and_capture_partial`, `kill_discard`, `extend` |
| `timeout_action` | string/null | no | Action taken on timeout |
| `partial_output_captured` | boolean | yes | Whether partial output exists after timeout |

---

## Mutation Guard Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mutation_guard_required` | boolean | yes | Whether mutation guard was required |
| `pre_git_status_short` | string | yes | `git status --short` before invocation |
| `pre_git_diff_name_only` | string | yes | `git diff --name-only` before invocation |
| `pre_git_diff_cached_name_only` | string | yes | `git diff --cached --name-only` before invocation |
| `post_git_status_short` | string | yes | `git status --short` after invocation |
| `post_git_diff_name_only` | string | yes | `git diff --name-only` after invocation |
| `post_git_diff_cached_name_only` | string | yes | `git diff --cached --name-only` after invocation |
| `mutation_detected` | boolean | yes | Whether pre/post state differs |
| `mutation_paths` | list[string] | yes | Paths that changed (empty if no mutation) |
| `mutation_classification` | string/null | no | `none`, `expected_untracked`, `unexpected_tracked`, `unexpected_staged` |
| `mutation_action` | string/null | no | `continue`, `block_subsequent`, `quarantine` |

---

## Storage Policy Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `raw_output_storage_policy` | string | yes | `external_volatile`, `pcae_managed`, `metadata_only` |
| `raw_output_repo_storage_allowed` | boolean | yes | Whether raw output may be stored in repo |
| `raw_output_external_path_allowed` | boolean | yes | Whether external paths (e.g., /tmp) are allowed |
| `raw_output_retention_policy` | string | yes | `session_only`, `until_intake`, `until_closure`, `permanent` |
| `hash_required` | boolean | yes | Whether hashes must be recorded |
| `metadata_only_in_repo` | boolean | yes | Whether only metadata (not raw output) goes in repo |
| `large_output_policy` | string | yes | `truncate_with_hash`, `reject`, `external_only` |

---

## Validation Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `metadata_complete` | boolean | yes | Whether all required metadata is present |
| `hashes_present` | boolean | yes | Whether all required hashes are recorded |
| `line_counts_present` | boolean | yes | Whether line counts are recorded |
| `byte_counts_present` | boolean | yes | Whether byte counts are recorded |
| `return_code_present` | boolean | yes | Whether return code is recorded |
| `duration_present` | boolean | yes | Whether duration is recorded |
| `mutation_guard_present` | boolean | yes | Whether mutation guard results are recorded |
| `storage_policy_valid` | boolean | yes | Whether storage policy is consistent |
| `validation_errors` | list[string] | yes | List of validation error messages |
| `validation_warnings` | list[string] | yes | List of validation warnings |

## Failure Classification Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `failure_detected` | boolean | yes | Whether any failure occurred |
| `failure_type` | string/null | no | `backend_missing`, `backend_timeout`, `backend_error`, `mutation_detected`, `capture_incomplete`, `hash_mismatch` |
| `failure_stage` | string/null | no | `pre_invocation`, `during_invocation`, `post_invocation`, `metadata_validation` |
| `failed_invocation_id` | string/null | no | Invocation that failed |
| `safe_to_continue` | boolean/null | no | Whether subsequent invocations may proceed |
| `requires_quarantine` | boolean/null | no | Whether quarantine is needed |
| `requires_human_review` | boolean/null | no | Whether human review is needed |

---

## Multi-Agent Grouping Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `route_id` | string/null | no | Routing approval reference |
| `sequence_index` | integer | yes | Order within the multi-agent sequence (0-based) |
| `parallel_group_id` | string/null | no | Group ID for parallel invocations (null if sequential) |
| `depends_on_invocation_ids` | list[string] | yes | Invocations that must complete first |
| `handoff_from_invocation_id` | string/null | no | Invocation providing handoff content |
| `handoff_to_invocation_id` | string/null | no | Invocation receiving handoff content |
| `group_capture_status` | string | yes | `all_captured`, `partial`, `blocked`, `failed` |

---

## Validation Rule Set

| # | Rule ID | Description |
|---|---------|-------------|
| 1 | `CAPTURE_CONTRACT_REF` | Every capture must reference exactly one contract ID |
| 2 | `CAPTURE_PACKAGE_REF` | Every capture must reference exactly one prompt package ID |
| 3 | `INVOCATION_ROLE_REF` | Every invocation must reference exactly one role ID |
| 4 | `INVOCATION_PROMPT_REF` | Every invocation must reference exactly one prompt ID |
| 5 | `INVOCATION_BACKEND_ID` | Every invocation must include backend identity fields |
| 6 | `INVOCATION_RETURN_OR_TIMEOUT` | Every invocation must include return code or timeout status |
| 7 | `SUCCESS_STDOUT_REQUIRED` | Every successful invocation must include stdout metadata |
| 8 | `STDERR_ALWAYS_RECORDED` | stderr metadata must be recorded even when stderr is empty |
| 9 | `STDOUT_HASH_REQUIRED` | stdout SHA256 is required when stdout exists |
| 10 | `STDERR_HASH_REQUIRED` | stderr SHA256 is required when stderr exists |
| 11 | `DURATION_REQUIRED` | Duration is required for every attempted invocation |
| 12 | `TIMEOUT_POLICY_REQUIRED` | Timeout policy is required for every attempted invocation |
| 13 | `MUTATION_GUARD_REQUIRED` | Mutation guard is required before and after every backend invocation |
| 14 | `MUTATION_PATHS_RECORDED` | Mutation detection must record affected paths and classification |
| 15 | `MUTATION_BLOCKS_SUBSEQUENT` | If mutation is detected, subsequent invocations must be blocked unless explicitly approved |
| 16 | `CAPTURE_NOT_INTAKE` | Capture metadata must not imply output intake has occurred |
| 17 | `CAPTURE_NOT_ADOPTION` | Capture metadata must not imply adoption approval |
| 18 | `CAPTURE_NOT_MUTATION_AUTH` | Capture metadata must not imply repo mutation authorization |
| 19 | `STORAGE_POLICY_CONSISTENT` | Raw output paths must follow the declared storage policy |
| 20 | `MISSING_OUTPUT_CLASSIFIED` | Missing raw output paths must be classified as `capture_storage_missing` |
| 21 | `PARTIAL_STATUS_ON_MIXED` | A capture with mixed success/failure must use `partial` status |
| 22 | `OUTCOME_MATCHES_INVOCATIONS` | Capture outcome must be consistent with invocation results |
| 23 | `BLOCKED_AGENT_NO_INVOCATION` | Blocked agents must not appear as attempted invocations |
| 24 | `UNKNOWN_AGENT_NO_INVOCATION` | Unknown agents must not appear as attempted invocations |
| 25 | `INTAKED_REQUIRES_ARTIFACT` | Capture cannot transition to `intaked` without an output intake artifact |
| 26 | `CLOSED_REQUIRES_VERIFICATION` | Capture cannot transition to `closed` without lifecycle verification or downstream closure |

---

## Example Schema Instance

Based on the 83G capture (MULTI-AGENT-DRY-RUN-001):

```json
{
  "capture_id": "MULTI-AGENT-CAPTURE-83G-001",
  "schema_version": "0.1",
  "capture_status": "closed",
  "capture_outcome": "multi_agent_outputs_captured_no_mutation",
  "contract_id": "MULTI-AGENT-DRY-RUN-001",
  "prompt_package_id": "MULTI-AGENT-PROMPT-PACKAGE-DRY-RUN-001",
  "route_id": "MULTI-AGENT-ROUTING-83D",
  "capture_artifact": "docs/MULTI_AGENT_PROMPT_SEND_CAPTURE.md",
  "capture_created_at": "2026-06-23T18:08:00Z",
  "invocations": [
    {
      "invocation_id": "inv-planner-001",
      "role_id": "planner-1",
      "role_type": "planner",
      "agent_id": "claude-local",
      "backend_command": "claude",
      "backend_args": ["--print"],
      "backend_invocation_authorized": true,
      "prompt_id": "planner-prompt-1",
      "prompt_text_hash": "sha256:...",
      "prompt_sent": true,
      "prompt_sent_at": "2026-06-23T18:08:00Z",
      "prompt_source_artifact": "docs/MULTI_AGENT_PROMPT_PACKAGE_DRY_RUN.md",
      "backend_identity": {
        "agent_id": "claude-local",
        "agent_display_name": "Claude (Local CLI)",
        "backend_command": "claude",
        "backend_args": ["--print"],
        "backend_version": "2.1.186",
        "backend_status": "available_proven",
        "wrapper_path": null,
        "risk_level": "low",
        "blocked_agent_check": true
      },
      "stdout": {
        "stdout_required": true,
        "stdout_path": "/tmp/pcae-83g-planner-stdout.txt",
        "stdout_storage_location": "external_volatile",
        "stdout_line_count": 159,
        "stdout_byte_count": 11263,
        "stdout_sha256": "7eea6c4c41c5f6eb24ce3d543ec6aaa2741c36a038167507ede4734c53dea492",
        "stdout_truncated": false,
        "stdout_format": "markdown",
        "stdout_contains_expected_sections": true
      },
      "stderr": {
        "stderr_required": true,
        "stderr_path": "/tmp/pcae-83g-planner-stderr.txt",
        "stderr_storage_location": "external_volatile",
        "stderr_line_count": 1,
        "stderr_byte_count": 157,
        "stderr_sha256": "e705bbf8982385da2b1a03725921d0a6c6730bbaadd22c8f9168522573d067e0",
        "stderr_truncated": false,
        "stderr_empty": false,
        "stderr_contains_errors": false
      },
      "timing": {
        "started_at": "2026-06-23T18:08:00Z",
        "completed_at": "2026-06-23T18:09:44Z",
        "duration_seconds": 104,
        "return_code": 0,
        "return_code_captured": true,
        "success_exit_code": 0
      },
      "timeout": {
        "timeout_seconds": 300,
        "timed_out": false,
        "timeout_policy": "kill_and_capture_partial",
        "partial_output_captured": false
      },
      "mutation_guard": {
        "mutation_guard_required": true,
        "pre_git_status_short": "?? tasks/active/83g-*",
        "pre_git_diff_name_only": "",
        "pre_git_diff_cached_name_only": "",
        "post_git_status_short": "?? tasks/active/83g-*",
        "post_git_diff_name_only": "",
        "post_git_diff_cached_name_only": "",
        "mutation_detected": false,
        "mutation_paths": [],
        "mutation_classification": "none"
      },
      "grouping": {
        "sequence_index": 0,
        "parallel_group_id": null,
        "depends_on_invocation_ids": [],
        "handoff_from_invocation_id": null,
        "handoff_to_invocation_id": "inv-reviewer-001",
        "group_capture_status": "all_captured"
      }
    },
    {
      "invocation_id": "inv-reviewer-001",
      "role_id": "reviewer-1",
      "role_type": "documentation_reviewer",
      "agent_id": "claude-deepseek",
      "backend_command": "claude-deepseek",
      "backend_args": ["--print"],
      "backend_invocation_authorized": true,
      "prompt_id": "reviewer-prompt-1",
      "prompt_text_hash": "sha256:...",
      "prompt_sent": true,
      "prompt_sent_at": "2026-06-23T18:11:00Z",
      "prompt_source_artifact": "docs/MULTI_AGENT_PROMPT_PACKAGE_DRY_RUN.md",
      "backend_identity": {
        "agent_id": "claude-deepseek",
        "agent_display_name": "Claude (DeepSeek Wrapper)",
        "backend_command": "claude-deepseek",
        "backend_args": ["--print"],
        "backend_version": "2.1.186",
        "backend_status": "available_proven",
        "wrapper_path": "/Users/atilamadai/.local/bin/claude-deepseek",
        "risk_level": "low",
        "blocked_agent_check": true
      },
      "stdout": {
        "stdout_required": true,
        "stdout_path": "/tmp/pcae-83g-reviewer-stdout.txt",
        "stdout_storage_location": "external_volatile",
        "stdout_line_count": 330,
        "stdout_byte_count": 20491,
        "stdout_sha256": "f821b0e3771cc7763eb7725cdca6d10a8c2665766dea26f2862d1391aab064c3",
        "stdout_truncated": false,
        "stdout_format": "markdown",
        "stdout_contains_expected_sections": true
      },
      "stderr": {
        "stderr_required": true,
        "stderr_path": "/tmp/pcae-83g-reviewer-stderr.txt",
        "stderr_storage_location": "external_volatile",
        "stderr_line_count": 1,
        "stderr_byte_count": 157,
        "stderr_sha256": "e705bbf8982385da2b1a03725921d0a6c6730bbaadd22c8f9168522573d067e0",
        "stderr_truncated": false,
        "stderr_empty": false,
        "stderr_contains_errors": false
      },
      "timing": {
        "started_at": "2026-06-23T18:11:00Z",
        "completed_at": "2026-06-23T18:13:11Z",
        "duration_seconds": 131,
        "return_code": 0,
        "return_code_captured": true,
        "success_exit_code": 0
      },
      "timeout": {
        "timeout_seconds": 300,
        "timed_out": false,
        "timeout_policy": "kill_and_capture_partial",
        "partial_output_captured": false
      },
      "mutation_guard": {
        "mutation_guard_required": true,
        "pre_git_status_short": "?? tasks/active/83g-*",
        "pre_git_diff_name_only": "",
        "pre_git_diff_cached_name_only": "",
        "post_git_status_short": "?? tasks/active/83g-*",
        "post_git_diff_name_only": "",
        "post_git_diff_cached_name_only": "",
        "mutation_detected": false,
        "mutation_paths": [],
        "mutation_classification": "none"
      },
      "grouping": {
        "sequence_index": 1,
        "parallel_group_id": null,
        "depends_on_invocation_ids": ["inv-planner-001"],
        "handoff_from_invocation_id": "inv-planner-001",
        "handoff_to_invocation_id": null,
        "group_capture_status": "all_captured"
      }
    }
  ],
  "mutation_guard_summary": {
    "any_mutation_detected": false,
    "total_invocations": 2,
    "mutation_free_invocations": 2,
    "mutation_detected_invocations": 0
  },
  "validation_result": {
    "metadata_complete": true,
    "hashes_present": true,
    "line_counts_present": true,
    "byte_counts_present": true,
    "return_code_present": true,
    "duration_present": true,
    "mutation_guard_present": true,
    "storage_policy_valid": true,
    "validation_errors": [],
    "validation_warnings": []
  },
  "failure_classification": null,
  "storage_policy": {
    "raw_output_storage_policy": "external_volatile",
    "raw_output_repo_storage_allowed": false,
    "raw_output_external_path_allowed": true,
    "raw_output_retention_policy": "session_only",
    "hash_required": true,
    "metadata_only_in_repo": true,
    "large_output_policy": "external_only"
  }
}
```

This is an illustrative example only. No executable schema file is created in 84C.

---

## Failure Cases

| # | Failure | Detection | Handling |
|---|---------|-----------|----------|
| 1 | Backend command missing | `backend_status=missing` | Block invocation; `failure_type=backend_missing` |
| 2 | Backend unavailable at runtime | Command exists but fails to start | `failure_type=backend_error`, `failure_stage=pre_invocation` |
| 3 | Blocked agent attempted | Agent has `blocked` status | Block; `BLOCKED_AGENT_NO_INVOCATION` rule violation |
| 4 | Unknown agent attempted | Agent not in registry | Block; `UNKNOWN_AGENT_NO_INVOCATION` rule violation |
| 5 | Prompt hash mismatch | Sent prompt SHA256 ≠ approved hash | Block sending; `failure_type=hash_mismatch` |
| 6 | Prompt not authorized | `prompt_send_authorized=false` | Block sending; `failure_stage=pre_invocation` |
| 7 | stdout missing after invocation | stdout path does not exist | `failure_type=capture_incomplete`, `stdout_path=null` |
| 8 | stderr missing after invocation | stderr path does not exist | `failure_type=capture_incomplete`, `stderr_path=null` |
| 9 | Return code missing | Process killed or unrecoverable | `return_code=null`, `return_code_captured=false` |
| 10 | Timeout without partial output | Timeout with `partial_output_captured=false` | `timed_out=true`, `failure_type=backend_timeout` |
| 11 | Duration missing | Timing not captured | `validation_errors` includes `DURATION_REQUIRED` |
| 12 | stdout hash mismatch | Re-hash of file ≠ recorded hash | `failure_type=hash_mismatch`, quarantine output |
| 13 | stderr hash mismatch | Re-hash of file ≠ recorded hash | `failure_type=hash_mismatch`, quarantine output |
| 14 | Mutation guard missing | No pre/post git state recorded | `validation_errors` includes `MUTATION_GUARD_REQUIRED` |
| 15 | Mutation detected | Pre/post git state differs | `mutation_detected=true`, block subsequent, quarantine |
| 16 | Raw output path missing at intake | File deleted between capture and intake | `failure_type=capture_storage_missing` |
| 17 | Raw output deleted before intake | Volatile storage lost | `failure_type=capture_storage_missing`, rely on hashes |
| 18 | Outcome inconsistent | `capture_outcome` doesn't match invocation results | `validation_errors` includes `OUTCOME_MATCHES_INVOCATIONS` |
| 19 | Partial without classification | Some invocations failed but no failure classification | `validation_errors` includes failure classification requirement |
| 20 | Capture without package ID | `prompt_package_id` missing | `validation_errors` includes `CAPTURE_PACKAGE_REF` |

---

## Migration from 83G Capture Artifact

The current documentation-only capture format (`docs/MULTI_AGENT_PROMPT_SEND_CAPTURE.md`) maps to this schema:

| Current (markdown) | Schema field |
|-------------------|-------------|
| Planner/Reviewer Invocation Metadata tables | `invocations` array entries |
| stdout/stderr Metadata Summary table | `invocations[].stdout`, `invocations[].stderr` |
| Output Hash Metadata table | `invocations[].stdout.stdout_sha256`, etc. |
| Mutation Guard Results table | `invocations[].mutation_guard` + `mutation_guard_summary` |
| Prompt Send Validation table | Derived from `invocations[].prompt_sent`, `prompt_text_hash` |
| Capture Validation table | `validation_result` |
| Capture Outcome table | Top-level `capture_status`, `capture_outcome` |
| Authorization Flags table | Handled by prompt package schema (84B), not duplicated here |

A future implementation phase could generate schema instances from existing markdown or populate them during governed capture.

---

## Schema Status

| Field | Value |
|-------|-------|
| schema_name | multi_agent_capture_metadata |
| schema_version | 0.1 |
| schema_status | draft_documented |
| schema_implementation_status | not_started |

## Recommended Next Phase

**84D — Multi-Agent Output Intake Schema**

84D should define the machine-readable schema for classifying captured outputs into reviewable candidates, partial candidates, blocked safety issues, contract mismatches, and mutation-detected cases, completing the schema trio (prompt package → capture → intake).
