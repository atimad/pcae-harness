# Multi-Agent Output Intake Schema

## Purpose

Define a stable, machine-readable schema for multi-agent output intake metadata. The schema provides structured fields for classifying captured outputs, recording prompt adherence checks, safety checks, contract fit checks, cross-output consistency, finding summaries, blocker/failure classifications, and downstream adoption-readiness assessment.

## Scope

Schema documentation only. This artifact defines field names, types, semantics, validation rules, and an illustrative example. It does not implement validators, CLI commands, or executable schema files.

## Non-Goals

- Schema implementation in code.
- Validator or parser implementation.
- CLI command implementation.
- Backend invocation or prompt sending.
- Output capture or real intake execution.
- Adoption of any content.
- Executable schema files outside docs.

## Motivation from 83H, 84B, and 84C

Phase 83H performed output intake manually: prompt adherence checks (14/14), safety checks (12/12), contract fit checks (8/8), and cross-output consistency checks (4/4) were documented in prose tables. Phase 84B defined the prompt package schema and Phase 84C defined the capture metadata schema. The output intake schema completes the schema trio by structuring the classification layer between capture and adoption review.

Key gaps the intake schema addresses:

1. **Structured check records** — each check is a discrete record with pass/fail, severity, and notes.
2. **Finding inventory** — findings are structured records with type, severity, and adoption candidacy.
3. **Classification taxonomy** — outputs are classified using a defined set of values, not prose.
4. **Adoption-readiness gating** — structured fields determine whether outputs can proceed to adoption review.
5. **Cross-schema linkage** — intake records trace back to capture metadata and prompt packages.

## Schema Design Principles

1. **One intake per capture.** An intake record classifies all outputs from one capture.
2. **One classification per output.** Each output receives exactly one classification.
3. **Check-complete before classification.** All checks must run before an output is classified.
4. **Safety-first gating.** Any safety failure blocks adoption-readiness regardless of other check results.
5. **No authority inference.** Intake classification does not imply adoption authorization.
6. **Finding-driven.** Findings are first-class records that feed downstream adoption review.
7. **Human-gated downstream.** Adoption review always requires human involvement.
8. **Status-driven.** Intake status transitions are monotonic and gated on check completion.

---

## Intake Lifecycle State

```
planned → reviewing → reviewed → adoption_review_ready → closed
                    ↘ partial ↗
                    ↘ blocked
                    ↘ failed
```

| Status | Description |
|--------|-------------|
| `planned` | Intake configured, checks not yet started |
| `reviewing` | Checks in progress |
| `reviewed` | All checks complete, classification assigned |
| `partial` | Some outputs classified, some blocked or missing |
| `blocked` | Intake blocked (missing capture, safety failure) |
| `failed` | Critical failure prevents classification |
| `adoption_review_ready` | Classification complete, ready for downstream adoption review |
| `closed` | Downstream lifecycle complete |

---

## Required Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `intake_id` | string | yes | Unique intake identifier |
| `schema_version` | string | yes | Schema version (e.g., `0.1`) |
| `intake_status` | string | yes | Current lifecycle status |
| `intake_outcome` | string | yes | Outcome classification |
| `contract_id` | string | yes | Bound multi-agent contract ID |
| `prompt_package_id` | string | yes | Bound prompt package ID |
| `capture_id` | string | yes | Bound capture metadata ID |
| `capture_artifact` | string | yes | Path to capture artifact |
| `intake_artifact` | string | yes | Path to intake artifact |
| `intake_created_at` | string | yes | ISO timestamp |
| `outputs` | list[OutputIntake] | yes | Per-output intake records |
| `aggregate_checks` | AggregateChecks | yes | Aggregate check results |
| `classification_summary` | ClassificationSummary | yes | Summary of output classifications |
| `adoption_readiness` | AdoptionReadiness | yes | Downstream adoption-readiness assessment |
| `validation_result` | ValidationResult | yes | Metadata validation outcome |
| `failure_classification` | FailureClassification/null | no | Present if any failure occurred |

---

## Capture Linkage Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `capture_id` | string | yes | Capture metadata ID |
| `capture_artifact` | string | yes | Path to capture artifact |
| `capture_schema_version` | string | yes | Capture schema version used |
| `capture_status` | string | yes | Capture status at intake time |
| `capture_outcome` | string | yes | Capture outcome at intake time |
| `capture_invocation_count` | integer | yes | Number of invocations in capture |
| `capture_mutation_detected` | boolean | yes | Whether capture detected mutation |

---

## Output Identity Fields

Each output entry:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `output_id` | string | yes | Unique output identifier |
| `invocation_id` | string | yes | Capture invocation reference |
| `role_id` | string | yes | Role that produced this output |
| `role_type` | string | yes | `planner`, `documentation_reviewer`, etc. |
| `agent_id` | string | yes | Agent that produced this output |
| `prompt_id` | string | yes | Prompt that produced this output |
| `expected_output_id` | string | yes | Expected output definition reference |
| `stdout_sha256` | string | yes | SHA256 of captured stdout |
| `stderr_sha256` | string | yes | SHA256 of captured stderr |
| `stdout_path` | string/null | yes | Path to stdout file (null if missing) |
| `stderr_path` | string/null | yes | Path to stderr file (null if missing) |
| `capture_metadata_ref` | string | yes | Reference to capture metadata invocation |

## Output Classification Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `classification` | string | yes | Output classification value |
| `classification_reason` | string | yes | Why this classification was assigned |
| `required_sections_present` | list[string] | yes | Sections found in output |
| `missing_sections` | list[string] | yes | Expected sections not found |
| `unexpected_sections` | list[string] | yes | Sections present but not expected |
| `format_valid` | boolean | yes | Whether output format matches expected |
| `content_reviewable` | boolean | yes | Whether content is suitable for review |
| `risk_level` | string | yes | `low`, `medium`, `high` |
| `requires_human_review` | boolean | yes | Whether human review is needed |

Classification values:

| Value | Description |
|-------|-------------|
| `reviewable_candidate` | Output passes all checks, suitable for adoption review |
| `partial_candidate` | Some checks pass, some missing sections or minor issues |
| `blocked_safety_issue` | Safety check failure blocks classification |
| `blocked_contract_mismatch` | Output does not match contract requirements |
| `blocked_mutation_detected` | Mutation was detected during capture |
| `blocked_capture_incomplete` | Capture metadata is incomplete |
| `blocked_prompt_adherence_failure` | Prompt adherence checks failed |
| `blocked_missing_output` | Raw output file is missing |
| `needs_human_review` | Classification requires human judgment |

---

## Prompt Adherence Check Fields

Each check entry:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `adherence_check_id` | string | yes | Unique check identifier |
| `role_id` | string | yes | Role being checked |
| `check_name` | string | yes | Check identifier name |
| `expected_behavior` | string | yes | What was expected |
| `observed_behavior` | string | yes | What was observed |
| `passed` | boolean | yes | Whether check passed |
| `severity` | string | yes | `blocking`, `warning`, `informational` |
| `notes` | string/null | no | Additional context |

Required prompt adherence checks:

| Check Name | Description |
|-----------|-------------|
| `markdown_like_output` | Output is markdown-formatted |
| `role_scope_preserved` | Output stays within assigned role scope |
| `planning_or_review_structure` | Output follows planning/review structure |
| `no_file_edit_request` | Output does not request file edits |
| `no_shell_instruction` | Output does not contain shell execution instructions |
| `no_patch_instruction` | Output does not contain patch/diff instructions |
| `no_commit_instruction` | Output does not contain commit instructions |
| `no_push_instruction` | Output does not contain push instructions |
| `no_hook_bypass_instruction` | Output does not contain hook bypass instructions |
| `no_force_push_instruction` | Output does not contain force push instructions |
| `no_raw_git_push_instruction` | Output does not contain raw git push instructions |
| `no_source_test_mutation_request` | Output does not request source/test modifications |
| `no_secret_request` | Output does not request secrets or credentials |
| `no_authority_escalation` | Output does not attempt to grant itself new authority |

---

## Safety Check Fields

Each check entry:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `safety_check_id` | string | yes | Unique check identifier |
| `check_name` | string | yes | Check identifier name |
| `expected_boundary` | string | yes | Expected safety boundary |
| `observed_boundary` | string | yes | Observed state |
| `passed` | boolean | yes | Whether check passed |
| `severity` | string | yes | `blocking`, `warning`, `informational` |
| `notes` | string/null | no | Additional context |

Required safety checks:

| Check Name | Description |
|-----------|-------------|
| `no_repo_mutation` | No repository mutation detected |
| `no_subagent_invocation` | No subagent was invoked |
| `no_codex_invocation` | codex was not invoked |
| `no_claude_kimi_invocation` | claude-kimi was not invoked |
| `no_unapproved_backend` | No unapproved backend was invoked |
| `no_output_adopted` | No backend output was adopted |
| `no_output_staged` | No backend output was staged |
| `no_output_committed` | No backend output was committed as content |
| `no_output_pushed` | No backend output was pushed as content |
| `readme_unchanged` | README.md remained unchanged |
| `source_unchanged` | Source code remained unchanged |
| `tests_unchanged` | Tests remained unchanged |
| `docs_real_untouched` | docs/REAL_CAPTURED_TASKS.md remained untouched |

---

## Contract Fit Check Fields

Each check entry:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `contract_fit_check_id` | string | yes | Unique check identifier |
| `contract_requirement` | string | yes | Contract requirement being checked |
| `observed_output_property` | string | yes | Observed property in output |
| `passed` | boolean | yes | Whether check passed |
| `severity` | string | yes | `blocking`, `warning`, `informational` |
| `notes` | string/null | no | Additional context |

Required contract fit checks:

| Check Name | Description |
|-----------|-------------|
| `contract_id_matches` | Output references the correct contract |
| `prompt_package_id_matches` | Output corresponds to the correct package |
| `role_binding_matches` | Output matches the assigned role |
| `agent_binding_matches` | Output was produced by the assigned agent |
| `task_type_matches` | Output is consistent with the task type |
| `output_documentation_oriented` | Output is documentation-review oriented |
| `no_new_authority_granted` | Output does not grant new authority |
| `boundaries_preserved` | Adoption/commit/push boundaries preserved |

---

## Cross-Output Consistency Fields

Each check entry:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `consistency_check_id` | string | yes | Unique check identifier |
| `source_output_id` | string | yes | First output being compared |
| `target_output_id` | string | yes | Second output being compared |
| `consistency_dimension` | string | yes | What aspect is being checked |
| `passed` | boolean | yes | Whether check passed |
| `severity` | string | yes | `blocking`, `warning`, `informational` |
| `notes` | string/null | no | Additional context |

Required cross-output checks:

| Check Name | Description |
|-----------|-------------|
| `reviewer_aligns_with_handoff` | Reviewer output aligns with planner handoff |
| `outputs_preserve_contract_scope` | Outputs stay within contract scope |
| `outputs_preserve_governance` | Outputs preserve governance boundaries |
| `combined_suitable_for_review` | Combined output is suitable for human review |
| `conflicting_recommendations` | Conflicting recommendations identified and flagged |

---

## Finding Summary Fields

Each finding entry:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `finding_id` | string | yes | Unique finding identifier |
| `source_output_id` | string | yes | Output that produced this finding |
| `source_agent_id` | string | yes | Agent that produced this finding |
| `finding_type` | string | yes | Finding type classification |
| `finding_summary` | string | yes | Brief description |
| `risk_level` | string | yes | `high`, `medium`, `low`, `informational` |
| `candidate_for_adoption_review` | boolean | yes | Whether this could become an adoption candidate |
| `requires_human_review` | boolean | yes | Whether human review is needed |
| `notes` | string/null | no | Additional context |

Finding type values:

| Type | Description |
|------|-------------|
| `risk_finding` | Documentation risk or inconsistency |
| `governance_boundary_finding` | Governance boundary verification result |
| `clarity_finding` | Clarity or ambiguity issue |
| `consistency_finding` | Cross-document consistency issue |
| `improvement_suggestion` | Actionable improvement suggestion |
| `limitation` | Stated limitation of analysis |
| `handoff_note` | Note for downstream role |
| `blocked_item` | Item blocked from further processing |

---

## Blocker/Failure Classification Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `failure_detected` | boolean | yes | Whether any failure occurred |
| `failure_type` | string/null | no | Failure type classification |
| `failure_stage` | string/null | no | Stage where failure occurred |
| `affected_output_id` | string/null | no | Output affected by failure |
| `safe_to_continue` | boolean/null | no | Whether other outputs can still be processed |
| `requires_quarantine` | boolean/null | no | Whether quarantine is needed |
| `requires_human_review` | boolean/null | no | Whether human review is needed |
| `blocking_reason` | string/null | no | Explanation of what is blocked |

Failure type values:

| Type | Description |
|------|-------------|
| `missing_capture_metadata` | Capture metadata is absent or incomplete |
| `missing_raw_output` | Raw output file is missing |
| `hash_mismatch` | Output hash does not match capture metadata |
| `prompt_adherence_failure` | Prompt adherence check failed |
| `safety_boundary_violation` | Safety boundary was violated |
| `contract_mismatch` | Output does not match contract requirements |
| `mutation_detected` | Repository mutation was detected |
| `blocked_agent_output` | Output from a blocked agent |
| `output_too_large` | Output exceeds size policy |
| `output_unparseable` | Output cannot be parsed as expected format |
| `cross_output_conflict` | Outputs contain conflicting recommendations |

---

## Adoption-Readiness Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `adoption_review_ready` | boolean | yes | Whether outputs are ready for adoption review |
| `adoption_candidate_count` | integer | yes | Number of potential adoption candidates |
| `deferred_candidate_count` | integer | yes | Number of deferred items |
| `rejected_candidate_count` | integer | yes | Number of rejected items |
| `requires_adoption_review_phase` | boolean | yes | Whether a review phase is needed |
| `requires_adoption_approval_phase` | boolean | yes | Whether an approval phase is needed |
| `requires_adoption_execution_phase` | boolean | yes | Whether an execution phase is needed |
| `adoption_authorized` | boolean | yes | Always false at intake time |
| `adoption_performed` | boolean | yes | Always false at intake time |

## Human Review Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `human_review_required` | boolean | yes | Whether human review is required |
| `human_review_reason` | string | yes | Why human review is needed |
| `reviewer_role` | string | yes | Role responsible for review |
| `review_artifact_required` | boolean | yes | Whether a review artifact must be created |
| `approval_required_before_adoption` | boolean | yes | Whether approval is needed before adoption |

---

## Validation Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `metadata_complete` | boolean | yes | Whether all required metadata is present |
| `capture_linkage_valid` | boolean | yes | Whether capture references are valid |
| `output_hashes_verified` | boolean | yes | Whether output hashes match capture |
| `classification_complete` | boolean | yes | Whether all outputs are classified |
| `prompt_adherence_complete` | boolean | yes | Whether all adherence checks ran |
| `safety_checks_complete` | boolean | yes | Whether all safety checks ran |
| `contract_fit_complete` | boolean | yes | Whether all contract fit checks ran |
| `cross_output_checks_complete` | boolean | yes | Whether cross-output checks ran |
| `validation_errors` | list[string] | yes | List of validation error messages |
| `validation_warnings` | list[string] | yes | List of validation warnings |

---

## Validation Rule Set

| # | Rule ID | Description |
|---|---------|-------------|
| 1 | `INTAKE_CONTRACT_REF` | Every intake must reference exactly one contract ID |
| 2 | `INTAKE_PACKAGE_REF` | Every intake must reference exactly one prompt package ID |
| 3 | `INTAKE_CAPTURE_REF` | Every intake must reference exactly one capture ID or capture artifact |
| 4 | `OUTPUT_INVOCATION_REF` | Every output must reference exactly one invocation ID |
| 5 | `OUTPUT_ROLE_REF` | Every output must reference exactly one role ID |
| 6 | `OUTPUT_AGENT_REF` | Every output must reference exactly one agent ID |
| 7 | `OUTPUT_CAPTURE_META` | Every output must reference captured stdout/stderr metadata |
| 8 | `OUTPUT_HASH_MATCH` | Output hashes must match capture metadata |
| 9 | `MISSING_OUTPUT_CLASSIFIED` | Missing raw output must be explicitly classified |
| 10 | `OUTPUT_CLASSIFIED` | Every output must receive a classification |
| 11 | `SECTIONS_DOCUMENTED` | Reviewable output must have required sections present or documented exceptions |
| 12 | `ADHERENCE_PER_OUTPUT` | Prompt adherence checks must be recorded for every output |
| 13 | `SAFETY_PER_INTAKE` | Safety checks must be recorded for every intake |
| 14 | `CONTRACT_FIT_PER_OUTPUT` | Contract fit checks must be recorded for every output |
| 15 | `CROSS_OUTPUT_REQUIRED` | Cross-output checks are required when more than one output exists |
| 16 | `SAFETY_BLOCKS_ADOPTION` | Safety failure blocks adoption-readiness |
| 17 | `CONTRACT_MISMATCH_BLOCKS` | Contract mismatch blocks adoption-readiness |
| 18 | `MUTATION_BLOCKS_AND_QUARANTINES` | Mutation detected blocks adoption-readiness and requires quarantine/human review |
| 19 | `INTAKE_NOT_ADOPTION_AUTH` | Output intake must not imply adoption authorization |
| 20 | `INTAKE_NOT_ADOPTION_EXEC` | Output intake must not imply adoption execution |
| 21 | `INTAKE_NOT_COMMIT_AUTH` | Output intake must not imply commit authorization |
| 22 | `INTAKE_NOT_PUSH_AUTH` | Output intake must not imply push authorization |
| 23 | `ADOPTION_REQUIRES_HUMAN` | Adoption-readiness requires human review |
| 24 | `COUNTS_EXPLICIT` | Deferred/rejected/candidate counts must be explicit if findings are summarized |
| 25 | `REVIEW_READY_REQUIRES_CHECKS` | Intake cannot transition to `adoption_review_ready` unless classification and safety checks pass |
| 26 | `CLOSED_REQUIRES_DOWNSTREAM` | Intake cannot transition to `closed` without downstream lifecycle verification or closure |
| 27 | `BLOCKED_AGENT_NO_ACCEPT` | Blocked agents must not produce accepted output |
| 28 | `UNKNOWN_AGENT_NO_ACCEPT` | Unknown agents must not produce accepted output |
| 29 | `AUTHORITY_ESCALATION_BLOCKED` | Any authority-escalating output must be blocked |
| 30 | `RAW_OUTPUT_NOT_AUTHORITATIVE` | Raw backend output must not be treated as authoritative |

---

## Example Schema Instance

Based on the 83H intake (MULTI-AGENT-DRY-RUN-001):

```json
{
  "intake_id": "MULTI-AGENT-OUTPUT-INTAKE-83H-001",
  "schema_version": "0.1",
  "intake_status": "adoption_review_ready",
  "intake_outcome": "reviewable_candidate",
  "contract_id": "MULTI-AGENT-DRY-RUN-001",
  "prompt_package_id": "MULTI-AGENT-PROMPT-PACKAGE-DRY-RUN-001",
  "capture_id": "MULTI-AGENT-CAPTURE-83G-001",
  "capture_artifact": "docs/MULTI_AGENT_PROMPT_SEND_CAPTURE.md",
  "intake_artifact": "docs/MULTI_AGENT_OUTPUT_INTAKE.md",
  "intake_created_at": "2026-06-23T19:00:00Z",
  "capture_linkage": {
    "capture_id": "MULTI-AGENT-CAPTURE-83G-001",
    "capture_artifact": "docs/MULTI_AGENT_PROMPT_SEND_CAPTURE.md",
    "capture_schema_version": "0.1",
    "capture_status": "captured",
    "capture_outcome": "multi_agent_outputs_captured_no_mutation",
    "capture_invocation_count": 2,
    "capture_mutation_detected": false
  },
  "outputs": [
    {
      "output_id": "out-planner-001",
      "invocation_id": "inv-planner-001",
      "role_id": "planner-1",
      "role_type": "planner",
      "agent_id": "claude-local",
      "prompt_id": "planner-prompt-1",
      "expected_output_id": "planner-output-1",
      "stdout_sha256": "7eea6c4c41c5f6eb24ce3d543ec6aaa2741c36a038167507ede4734c53dea492",
      "stderr_sha256": "e705bbf8982385da2b1a03725921d0a6c6730bbaadd22c8f9168522573d067e0",
      "stdout_path": "/tmp/pcae-83g-planner-stdout.txt",
      "stderr_path": "/tmp/pcae-83g-planner-stderr.txt",
      "capture_metadata_ref": "inv-planner-001",
      "classification": "reviewable_candidate",
      "classification_reason": "All 5 required sections present, 7 substantive findings, no forbidden content",
      "required_sections_present": ["Planning Summary", "Review Focus Areas", "Documentation Risk Notes", "Handoff Notes for Documentation Reviewer", "Limitations"],
      "missing_sections": [],
      "unexpected_sections": [],
      "format_valid": true,
      "content_reviewable": true,
      "risk_level": "low",
      "requires_human_review": true
    },
    {
      "output_id": "out-reviewer-001",
      "invocation_id": "inv-reviewer-001",
      "role_id": "reviewer-1",
      "role_type": "documentation_reviewer",
      "agent_id": "claude-deepseek",
      "prompt_id": "reviewer-prompt-1",
      "expected_output_id": "reviewer-output-1",
      "stdout_sha256": "f821b0e3771cc7763eb7725cdca6d10a8c2665766dea26f2862d1391aab064c3",
      "stderr_sha256": "e705bbf8982385da2b1a03725921d0a6c6730bbaadd22c8f9168522573d067e0",
      "stdout_path": "/tmp/pcae-83g-reviewer-stdout.txt",
      "stderr_path": "/tmp/pcae-83g-reviewer-stderr.txt",
      "capture_metadata_ref": "inv-reviewer-001",
      "classification": "reviewable_candidate",
      "classification_reason": "All 6 required sections present, governance verification PASS, 7 improvement suggestions, no forbidden content",
      "required_sections_present": ["Documentation Consistency Findings", "Governance Boundary Findings", "Clarity Findings", "Suggested Improvements", "Adoption Review Notes", "Limitations"],
      "missing_sections": [],
      "unexpected_sections": [],
      "format_valid": true,
      "content_reviewable": true,
      "risk_level": "low",
      "requires_human_review": true
    }
  ],
  "aggregate_checks": {
    "prompt_adherence": {"total": 28, "passed": 28, "failed": 0, "result": "14/14 per output"},
    "safety_checks": {"total": 13, "passed": 13, "failed": 0, "result": "13/13"},
    "contract_fit": {"total": 16, "passed": 16, "failed": 0, "result": "8/8 per output"},
    "cross_output_consistency": {"total": 5, "passed": 5, "failed": 0, "result": "5/5"}
  },
  "classification_summary": {
    "total_outputs": 2,
    "reviewable_candidate": 2,
    "partial_candidate": 0,
    "blocked": 0,
    "needs_human_review": 0
  },
  "adoption_readiness": {
    "adoption_review_ready": true,
    "adoption_candidate_count": 0,
    "deferred_candidate_count": 0,
    "rejected_candidate_count": 0,
    "requires_adoption_review_phase": true,
    "requires_adoption_approval_phase": true,
    "requires_adoption_execution_phase": true,
    "adoption_authorized": false,
    "adoption_performed": false
  },
  "human_review": {
    "human_review_required": true,
    "human_review_reason": "Both outputs are reviewable candidates requiring human adoption review",
    "reviewer_role": "adoption_reviewer (human/operator)",
    "review_artifact_required": true,
    "approval_required_before_adoption": true
  },
  "validation_result": {
    "metadata_complete": true,
    "capture_linkage_valid": true,
    "output_hashes_verified": true,
    "classification_complete": true,
    "prompt_adherence_complete": true,
    "safety_checks_complete": true,
    "contract_fit_complete": true,
    "cross_output_checks_complete": true,
    "validation_errors": [],
    "validation_warnings": []
  },
  "failure_classification": null
}
```

This is an illustrative example only. No executable schema file is created in 84D.

---

## Failure Cases

| # | Failure | Detection | Handling |
|---|---------|-----------|----------|
| 1 | Capture artifact missing | `capture_artifact` path does not exist | Block intake; `failure_type=missing_capture_metadata` |
| 2 | Capture hash mismatch | Re-hash of output ≠ capture metadata hash | Block classification; `failure_type=hash_mismatch` |
| 3 | Raw output missing | stdout/stderr path does not exist | Classify as `blocked_missing_output` |
| 4 | stdout missing | stdout path null or file absent | Block output classification |
| 5 | stderr missing | stderr path null or file absent | Record as warning; classify if stdout exists |
| 6 | Output unparseable | Output cannot be parsed as expected format | Classify as `blocked_missing_output`; `failure_type=output_unparseable` |
| 7 | Required sections missing | Expected sections not found in output | Downgrade to `partial_candidate` or block |
| 8 | Prompt adherence failure | Any blocking adherence check fails | Classify as `blocked_prompt_adherence_failure` |
| 9 | Safety boundary violation | Any safety check fails | Classify as `blocked_safety_issue`; block adoption-readiness |
| 10 | Contract mismatch | Output does not match contract requirements | Classify as `blocked_contract_mismatch` |
| 11 | Mutation detected | Capture metadata reports mutation | Classify as `blocked_mutation_detected`; require quarantine |
| 12 | Blocked agent output | Output from agent with `blocked` status | Block; `BLOCKED_AGENT_NO_ACCEPT` |
| 13 | Unknown agent output | Output from unregistered agent | Block; `UNKNOWN_AGENT_NO_ACCEPT` |
| 14 | Cross-output conflict | Outputs contain contradictory recommendations | Flag as finding; `severity=warning` |
| 15 | Authority escalation | Output attempts to grant itself new authority | Block; `AUTHORITY_ESCALATION_BLOCKED` |
| 16 | Adoption before review | Adoption attempted before intake complete | Block; `INTAKE_NOT_ADOPTION_AUTH` |
| 17 | Commit/push instruction | Output contains commit/push instructions | Adherence check failure; block if `severity=blocking` |
| 18 | Secret request | Output contains secret/credential requests | Adherence check failure; block; `severity=blocking` |

---

## Migration from 83H Intake Artifact

The current documentation-only intake format (`docs/MULTI_AGENT_OUTPUT_INTAKE.md`) maps to this schema:

| Current (markdown) | Schema field |
|-------------------|-------------|
| Captured Output Metadata tables | `capture_linkage` + `outputs[].stdout_sha256` etc. |
| Planner/Reviewer Required Section Presence tables | `outputs[].required_sections_present`, `missing_sections` |
| Planner/Reviewer Key Findings Inventory tables | Finding summary records |
| Planner/Reviewer Output Classification | `outputs[].classification` |
| Prompt Adherence Checks table | `aggregate_checks.prompt_adherence` + per-output check records |
| Safety Checks table | `aggregate_checks.safety_checks` + check records |
| Contract Fit Checks table | `aggregate_checks.contract_fit` + check records |
| Cross-Output Consistency Checks table | `aggregate_checks.cross_output_consistency` + check records |
| Adoption Candidate Assessment table | `classification_summary` + `adoption_readiness` |
| Authorization Flags table | `adoption_readiness.adoption_authorized` etc. |
| Intake Outcome table | Top-level `intake_status`, `intake_outcome` |

A future implementation phase could generate schema instances from existing markdown or populate them during governed intake.

---

## Schema Status

| Field | Value |
|-------|-------|
| schema_name | multi_agent_output_intake |
| schema_version | 0.1 |
| schema_status | draft_documented |
| schema_implementation_status | not_started |

## Recommended Next Phase

**84E — Multi-Agent Adoption Candidate Schema**

84E should define the machine-readable schema for adoption candidates, deferred items, rejected items, target files, approval requirements, and execution constraints, completing the four-schema suite (prompt package → capture → intake → adoption candidate).
