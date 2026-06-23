# Multi-Agent Adoption Candidate Schema

## Purpose

Define a stable, machine-readable schema for multi-agent adoption candidate metadata. The schema provides structured fields for candidate identity, source findings, candidate status, target file scope, risk level, approval requirements, execution constraints, deferred/rejected classification, and downstream verification requirements.

## Scope

Schema documentation only. This artifact defines field names, types, semantics, validation rules, and an illustrative example. It does not implement validators, CLI commands, or executable schema files.

## Non-Goals

- Schema implementation in code.
- Validator or parser implementation.
- CLI command implementation.
- Backend invocation or prompt sending.
- Output capture, intake, or adoption execution.
- Executable schema files outside docs.

## Motivation from 83I–83K and 84D

Phases 83I–83K performed adoption review, approval, and execution manually: candidates were documented in markdown tables with prose descriptions, approval was recorded as a separate artifact, and execution was verified via git diff inspection. Phase 84D defined the intake schema that feeds into adoption review.

Key gaps the adoption candidate schema addresses:

1. **Structured candidate records** — each candidate is a discrete record with mandatory fields.
2. **Status-driven lifecycle** — candidate status transitions are monotonic and explicitly gated.
3. **Target file binding** — each candidate binds to exactly one target file with scope constraints.
4. **Approval/execution separation** — approval and execution are tracked independently.
5. **Deferred/rejected tracking** — deferred and rejected items are first-class records with reasons.
6. **Verification requirements** — post-execution verification is structured, not ad-hoc.

## Schema Design Principles

1. **One candidate set per lifecycle.** A candidate set groups all candidates from one intake.
2. **One target file per candidate.** Each candidate binds to exactly one target file.
3. **Approval before execution.** No candidate may be executed without explicit approval.
4. **Scope-bound execution.** Execution is constrained to the exact approved scope.
5. **Human-gated.** All approval and execution decisions require human involvement.
6. **No authority inference.** Adoption approval does not imply commit or push authorization.
7. **Deferred/rejected are first-class.** Not just "not approved" — explicitly classified with reasons.
8. **Verification-mandatory.** Every executed candidate must be verified post-execution.

---

## Adoption Candidate Lifecycle State

```
planned → reviewed → approval_pending → approved → execution_pending → executed → closed
                                      ↘ partially_approved ↗
                   ↘ blocked
```

| Status | Description |
|--------|-------------|
| `planned` | Candidate set created, review not yet started |
| `reviewed` | All candidates classified from intake findings |
| `approval_pending` | Candidates identified, awaiting human approval |
| `approved` | All submitted candidates approved |
| `partially_approved` | Some candidates approved, some deferred/rejected |
| `execution_pending` | Approved candidates awaiting execution |
| `executed` | All approved candidates executed |
| `partially_executed` | Some candidates executed, some blocked |
| `blocked` | Candidate set blocked (safety, contract, or policy failure) |
| `closed` | Downstream lifecycle verification complete |

---

## Required Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `adoption_candidate_set_id` | string | yes | Unique candidate set identifier |
| `schema_version` | string | yes | Schema version (e.g., `0.1`) |
| `candidate_set_status` | string | yes | Current lifecycle status |
| `contract_id` | string | yes | Bound multi-agent contract ID |
| `prompt_package_id` | string | yes | Bound prompt package ID |
| `intake_id` | string | yes | Bound intake ID |
| `adoption_review_artifact` | string | yes | Path to adoption review artifact |
| `adoption_approval_artifact` | string/null | no | Path to approval artifact (null until approved) |
| `adoption_execution_artifact` | string/null | no | Path to execution artifact (null until executed) |
| `candidates` | list[Candidate] | yes | Adoption candidate records |
| `deferred_items` | list[DeferredItem] | yes | Deferred item records |
| `rejected_items` | list[RejectedItem] | yes | Rejected item records |
| `aggregate_counts` | AggregateCounts | yes | Summary counts |
| `authorization_flags` | AuthorizationFlags | yes | Authorization state |
| `validation_result` | ValidationResult | yes | Metadata validation outcome |
| `failure_classification` | FailureClassification/null | no | Present if any failure occurred |

---

## Candidate Identity Fields

Each candidate entry:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `candidate_id` | string | yes | Unique candidate identifier (e.g., `AC-1`) |
| `candidate_title` | string | yes | Human-readable title |
| `candidate_status` | string | yes | Current candidate status |
| `source_output_id` | string | yes | Output that produced this finding |
| `source_agent_id` | string | yes | Agent that produced this finding |
| `source_finding_id` | string | yes | Finding ID from intake |
| `finding_type` | string | yes | Finding type classification |
| `finding_summary` | string | yes | Brief description of the finding |
| `recommended_action` | string | yes | What should be done |
| `created_from_artifact` | string | yes | Artifact where candidate was identified |

Candidate status values:

| Value | Description |
|-------|-------------|
| `candidate_for_future_adoption` | Identified, not yet approved |
| `approved_for_future_adoption` | Human-approved for future execution |
| `execution_pending` | Approved and awaiting execution |
| `executed` | Successfully executed |
| `deferred` | Deferred to a future phase |
| `rejected` | Rejected with documented reason |
| `blocked` | Blocked by safety or policy failure |
| `needs_more_review` | Requires additional human review |

---

## Source Finding Linkage Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `intake_artifact` | string | yes | Path to intake artifact |
| `adoption_review_artifact` | string | yes | Path to adoption review |
| `source_output_id` | string | yes | Output ID from intake |
| `source_agent_id` | string | yes | Agent ID from intake |
| `source_finding_id` | string | yes | Finding ID from intake |
| `source_stdout_sha256` | string | yes | SHA256 of the output that produced the finding |
| `source_capture_id` | string | yes | Capture ID |
| `source_prompt_package_id` | string | yes | Prompt package ID |

## Candidate Classification Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `classification` | string | yes | Candidate classification |
| `classification_reason` | string | yes | Why this classification was assigned |
| `candidate_type` | string | yes | Type of change proposed |
| `impact_level` | string | yes | `minimal`, `low`, `medium`, `high` |
| `risk_level` | string | yes | `low`, `medium`, `high` |
| `confidence_level` | string | yes | `high` (both agents agree), `medium` (one agent), `low` (uncertain) |
| `requires_human_review` | boolean | yes | Whether human review is needed |

Candidate type values:

| Type | Description |
|------|-------------|
| `risk_rationale` | Add rationale for a risk-level decision |
| `typo_fix` | Fix a typographical error |
| `scope_note` | Add a scope clarification note |
| `clarity_improvement` | Improve unclear wording |
| `governance_boundary_note` | Add governance boundary clarification |
| `capability_model_update` | Update capability model documentation |
| `taxonomy_update` | Update risk/status taxonomy |
| `flag_standardization` | Standardize authorization flag tables |
| `stale_reference_update` | Update stale cross-references |
| `documentation_rewrite` | Broader documentation restructuring |

---

## Target File and Scope Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `target_file` | string | yes | Path to file to be modified |
| `target_file_required` | boolean | yes | Whether the target file must exist |
| `allowed_path_pattern` | string | yes | Glob pattern of allowed target paths |
| `forbidden_path_patterns` | list[string] | yes | Glob patterns that must not be targeted |
| `scope_summary` | string | yes | Brief description of the approved change scope |
| `allowed_change_type` | string | yes | Type of change permitted |
| `max_change_size_policy` | string | yes | `single_line`, `few_lines`, `section`, `unbounded` |
| `raw_backend_text_allowed` | boolean | yes | Whether raw backend output may be pasted (default false) |
| `broad_rewrite_allowed` | boolean | yes | Whether broad rewrite is permitted (default false) |

Allowed change type values:

| Type | Description |
|------|-------------|
| `single_line_fix` | One-line correction (e.g., typo) |
| `small_local_clarification` | 1-3 sentences added inline |
| `small_section_note` | Short note added to a section |
| `bounded_table_update` | Update rows in an existing table |
| `bounded_schema_update` | Update fields in a schema definition |
| `documentation_only_patch` | Broader documentation change (requires elevated approval) |

---

## Risk and Safety Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `risk_level` | string | yes | `low`, `medium`, `high` |
| `risk_reason` | string | yes | Why this risk level was assigned |
| `safety_constraints` | list[string] | yes | Safety constraints that apply |
| `forbidden_changes` | list[string] | yes | Changes explicitly forbidden |
| `requires_scope_check` | boolean | yes | Whether scope must be verified post-execution |
| `requires_forbidden_file_check` | boolean | yes | Whether forbidden files must be verified |
| `requires_boundary_check` | boolean | yes | Whether governance boundaries must be verified |

---

## Approval Requirement Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `adoption_authorized` | boolean | yes | Whether adoption is authorized |
| `adoption_approval_required` | boolean | yes | Whether explicit approval is needed |
| `adoption_approval_status` | string | yes | `pending`, `approved`, `rejected`, `deferred` |
| `approved_by` | string/null | no | Who approved (null until approved) |
| `approval_reason` | string/null | no | Why approved |
| `approval_artifact` | string/null | no | Path to approval artifact |
| `approval_timestamp` | string/null | no | ISO timestamp of approval |
| `commit_approval_required` | boolean | yes | Whether separate commit approval is needed |
| `push_approval_required` | boolean | yes | Whether separate push approval is needed |

## Execution Constraint Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `adoption_execution_authorized` | boolean | yes | Whether execution is authorized |
| `execution_status` | string | yes | `pending`, `executed`, `blocked`, `skipped` |
| `execution_artifact` | string/null | no | Path to execution artifact |
| `execution_scope` | string/null | no | Description of what was executed |
| `execution_target_files` | list[string] | yes | Files actually modified |
| `execution_diff_summary` | string/null | no | Summary of changes made |
| `execution_verification_required` | boolean | yes | Whether post-execution verification is needed |
| `source_mutation_allowed` | boolean | yes | Default false |
| `test_mutation_allowed` | boolean | yes | Default false |
| `readme_mutation_allowed` | boolean | yes | Default false |
| `docs_real_captured_tasks_mutation_allowed` | boolean | yes | Default false |

---

## Deferred Item Fields

Each deferred item:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `deferred_id` | string | yes | Unique deferred item identifier |
| `source_finding_id` | string | yes | Finding this was derived from |
| `deferred_reason` | string | yes | Why this item is deferred |
| `recommended_future_phase` | string/null | no | Suggested phase to address this |
| `blocking_dependency` | string/null | no | What must happen before this can proceed |
| `risk_level` | string | yes | `low`, `medium`, `high` |
| `status` | string | yes | `deferred` |

## Rejected Item Fields

Each rejected item:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rejected_id` | string | yes | Unique rejected item identifier |
| `source_finding_id` | string | yes | Finding this was derived from |
| `rejection_reason` | string | yes | Why this item was rejected |
| `risk_level` | string | yes | `low`, `medium`, `high` |
| `status` | string | yes | `rejected` |

---

## Human Review Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `human_review_required` | boolean | yes | Whether human review is required |
| `human_review_status` | string | yes | `pending`, `completed`, `not_required` |
| `human_reviewer_role` | string | yes | Role responsible for review |
| `human_review_artifact` | string/null | no | Path to review artifact |
| `approval_required_before_execution` | boolean | yes | Whether approval must precede execution |

## Verification Requirement Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `target_file_verified` | boolean | yes | Whether target file changes match approved scope |
| `scope_verified` | boolean | yes | Whether execution stayed within approved scope |
| `forbidden_files_verified` | boolean | yes | Whether no forbidden files were modified |
| `diff_size_verified` | boolean | yes | Whether diff size matches policy |
| `raw_backend_text_absent` | boolean | yes | Whether no raw backend text was pasted |
| `source_unchanged_verified` | boolean | yes | Whether source code remained unchanged |
| `tests_unchanged_verified` | boolean | yes | Whether tests remained unchanged |
| `readme_unchanged_verified` | boolean | yes | Whether README remained unchanged |
| `docs_real_captured_tasks_untouched_verified` | boolean | yes | Whether docs/REAL_CAPTURED_TASKS.md was untouched |

---

## Validation Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `metadata_complete` | boolean | yes | Whether all required metadata is present |
| `candidate_ids_unique` | boolean | yes | Whether all candidate IDs are unique |
| `source_linkage_valid` | boolean | yes | Whether source finding references are valid |
| `target_files_valid` | boolean | yes | Whether target files are within allowed paths |
| `scope_valid` | boolean | yes | Whether scope descriptions are present |
| `risk_levels_present` | boolean | yes | Whether risk levels are assigned |
| `approval_status_consistent` | boolean | yes | Whether approval status matches authorization |
| `execution_status_consistent` | boolean | yes | Whether execution status matches authorization |
| `counts_match` | boolean | yes | Whether aggregate counts match listed entries |
| `validation_errors` | list[string] | yes | List of validation error messages |
| `validation_warnings` | list[string] | yes | List of validation warnings |

---

## Validation Rule Set

| # | Rule ID | Description |
|---|---------|-------------|
| 1 | `SET_CONTRACT_REF` | Every candidate set must reference exactly one contract ID |
| 2 | `SET_PACKAGE_REF` | Every candidate set must reference exactly one prompt package ID |
| 3 | `CANDIDATE_ID_UNIQUE` | Every candidate must have a unique candidate ID |
| 4 | `CANDIDATE_SOURCE_LINK` | Every candidate must link to a source finding or documented review artifact |
| 5 | `CANDIDATE_STATUS_REQUIRED` | Every candidate must have a status |
| 6 | `CANDIDATE_TARGET_FILE` | Every candidate must have a target file unless deferred or rejected |
| 7 | `TARGET_ALLOWED_PATH` | Target files must match allowed path policy |
| 8 | `TARGET_NOT_FORBIDDEN` | Forbidden path patterns must not be targeted |
| 9 | `NO_SOURCE_TARGET` | Source files must not be targeted unless explicitly authorized |
| 10 | `NO_TEST_TARGET` | Test files must not be targeted unless explicitly authorized |
| 11 | `NO_README_TARGET` | README must not be targeted unless explicitly authorized |
| 12 | `NO_REAL_CAPTURED_TARGET` | docs/REAL_CAPTURED_TASKS.md must not be targeted unless explicitly authorized |
| 13 | `NO_RAW_BACKEND_TEXT` | Raw backend text must not be adopted wholesale unless explicitly approved |
| 14 | `NO_BROAD_REWRITE` | Broad rewrites are invalid unless explicitly approved |
| 15 | `APPROVAL_BEFORE_EXECUTION` | Adoption approval must precede adoption execution |
| 16 | `EXECUTION_REQUIRES_AUTH` | Adoption execution must not occur when `adoption_execution_authorized=false` |
| 17 | `COMMIT_SEPARATE` | Commit approval must remain separate from adoption approval |
| 18 | `PUSH_SEPARATE` | Push approval must remain separate from adoption approval |
| 19 | `DEFERRED_REASON_REQUIRED` | Deferred items must record a deferral reason |
| 20 | `REJECTED_REASON_REQUIRED` | Rejected items must record a rejection reason |
| 21 | `COUNTS_MATCH` | Candidate/deferred/rejected counts must match listed entries |
| 22 | `EXECUTED_HAS_ARTIFACT` | Executed candidates must have execution artifacts |
| 23 | `EXECUTED_TARGET_VERIFIED` | Executed candidates must have target-file verification |
| 24 | `EXECUTED_FORBIDDEN_VERIFIED` | Executed candidates must have forbidden-file verification |
| 25 | `EXECUTED_DIFF_SUMMARY` | Executed candidates must have diff summary |
| 26 | `BLOCKED_FILE_BLOCKS` | Any candidate touching blocked files must be blocked |
| 27 | `STATUS_MONOTONIC` | Candidate status transitions must be monotonic or explicitly blocked |
| 28 | `SAFETY_BLOCKS_APPROVAL` | A safety failure blocks adoption approval |
| 29 | `CONTRACT_MISMATCH_BLOCKS` | A contract mismatch blocks adoption approval |
| 30 | `HUMAN_REVIEW_BEFORE_APPROVAL` | Human review is required before approval |
| 31 | `INTAKE_NOT_ADOPTION_AUTH` | Output intake alone must not create adoption authorization |
| 32 | `APPROVAL_NOT_COMMIT_PUSH` | Adoption approval alone must not create commit/push authorization |

---

## Example Schema Instance

Based on the 83I–83K adoption path (MULTI-AGENT-DRY-RUN-001):

```json
{
  "adoption_candidate_set_id": "MULTI-AGENT-ADOPTION-CANDIDATES-83I-001",
  "schema_version": "0.1",
  "candidate_set_status": "closed",
  "contract_id": "MULTI-AGENT-DRY-RUN-001",
  "prompt_package_id": "MULTI-AGENT-PROMPT-PACKAGE-DRY-RUN-001",
  "intake_id": "MULTI-AGENT-OUTPUT-INTAKE-83H-001",
  "adoption_review_artifact": "docs/MULTI_AGENT_ADOPTION_REVIEW.md",
  "adoption_approval_artifact": "docs/MULTI_AGENT_ADOPTION_APPROVAL.md",
  "adoption_execution_artifact": "docs/MULTI_AGENT_ADOPTION_EXECUTION.md",
  "candidates": [
    {
      "candidate_id": "AC-1",
      "candidate_title": "Add Risk Level Rationale to 83C",
      "candidate_status": "executed",
      "source_output_id": "out-reviewer-001",
      "source_agent_id": "claude-deepseek",
      "source_finding_id": "C-1",
      "finding_type": "risk_rationale",
      "finding_summary": "documentation_review risk level is low in 82D/82E/83A but medium in 83C/83D with no rationale",
      "recommended_action": "Add inline rationale explaining multi-agent complexity elevation",
      "created_from_artifact": "docs/MULTI_AGENT_ADOPTION_REVIEW.md",
      "classification": "candidate_for_future_adoption",
      "classification_reason": "Both agents agree; bounded single-addition change",
      "candidate_type": "risk_rationale",
      "impact_level": "low",
      "risk_level": "low",
      "confidence_level": "high",
      "requires_human_review": true,
      "target_file": "docs/MULTI_AGENT_CONTRACT_INSTANCE_DRY_RUN.md",
      "target_file_required": true,
      "allowed_path_pattern": "docs/*.md",
      "forbidden_path_patterns": ["src/**", "tests/**", "docs/REAL_CAPTURED_TASKS.md"],
      "scope_summary": "Add 1-2 sentences near risk_level field explaining multi-agent complexity elevation",
      "allowed_change_type": "small_local_clarification",
      "max_change_size_policy": "few_lines",
      "raw_backend_text_allowed": false,
      "broad_rewrite_allowed": false,
      "adoption_authorized": true,
      "adoption_approval_status": "approved",
      "adoption_execution_authorized": true,
      "execution_status": "executed",
      "execution_diff_summary": "1 line changed in Identity table",
      "execution_verification_required": true,
      "source_mutation_allowed": false,
      "test_mutation_allowed": false,
      "readme_mutation_allowed": false,
      "docs_real_captured_tasks_mutation_allowed": false
    },
    {
      "candidate_id": "AC-2",
      "candidate_title": "Fix Typo in 83B",
      "candidate_status": "executed",
      "source_output_id": "out-reviewer-001",
      "source_agent_id": "claude-deepseek",
      "source_finding_id": "C-3",
      "finding_type": "typo_fix",
      "finding_summary": "claude-deepseep should be claude-deepseek in 83B line 82",
      "recommended_action": "Fix single-word typo",
      "created_from_artifact": "docs/MULTI_AGENT_ADOPTION_REVIEW.md",
      "classification": "candidate_for_future_adoption",
      "classification_reason": "Trivial correction; both agents identified it",
      "candidate_type": "typo_fix",
      "impact_level": "minimal",
      "risk_level": "low",
      "confidence_level": "high",
      "requires_human_review": true,
      "target_file": "docs/AGENT_ASSIGNMENT_APPROVAL.md",
      "target_file_required": true,
      "allowed_path_pattern": "docs/*.md",
      "forbidden_path_patterns": ["src/**", "tests/**", "docs/REAL_CAPTURED_TASKS.md"],
      "scope_summary": "Change claude-deepseep to claude-deepseek",
      "allowed_change_type": "single_line_fix",
      "max_change_size_policy": "single_line",
      "raw_backend_text_allowed": false,
      "broad_rewrite_allowed": false,
      "adoption_authorized": true,
      "adoption_approval_status": "approved",
      "adoption_execution_authorized": true,
      "execution_status": "executed",
      "execution_diff_summary": "1 line changed in Role Separation Checks table",
      "execution_verification_required": true,
      "source_mutation_allowed": false,
      "test_mutation_allowed": false,
      "readme_mutation_allowed": false,
      "docs_real_captured_tasks_mutation_allowed": false
    },
    {
      "candidate_id": "AC-3",
      "candidate_title": "Add Scope Note to 83C Allowed Files",
      "candidate_status": "executed",
      "source_output_id": "out-reviewer-001",
      "source_agent_id": "claude-deepseek",
      "source_finding_id": "C-4",
      "finding_type": "scope_note",
      "finding_summary": "83C allowed files lists 8 documents but actual review scope is 10",
      "recommended_action": "Add scope clarification note",
      "created_from_artifact": "docs/MULTI_AGENT_ADOPTION_REVIEW.md",
      "classification": "candidate_for_future_adoption",
      "classification_reason": "Bounded clarification; does not change contract semantics",
      "candidate_type": "scope_note",
      "impact_level": "low",
      "risk_level": "low",
      "confidence_level": "high",
      "requires_human_review": true,
      "target_file": "docs/MULTI_AGENT_CONTRACT_INSTANCE_DRY_RUN.md",
      "target_file_required": true,
      "allowed_path_pattern": "docs/*.md",
      "forbidden_path_patterns": ["src/**", "tests/**", "docs/REAL_CAPTURED_TASKS.md"],
      "scope_summary": "Add 1-2 sentences above Allowed Files list noting temporal scope limitation",
      "allowed_change_type": "small_section_note",
      "max_change_size_policy": "few_lines",
      "raw_backend_text_allowed": false,
      "broad_rewrite_allowed": false,
      "adoption_authorized": true,
      "adoption_approval_status": "approved",
      "adoption_execution_authorized": true,
      "execution_status": "executed",
      "execution_diff_summary": "2 lines added above Allowed Files list",
      "execution_verification_required": true,
      "source_mutation_allowed": false,
      "test_mutation_allowed": false,
      "readme_mutation_allowed": false,
      "docs_real_captured_tasks_mutation_allowed": false
    }
  ],
  "deferred_items": [
    {
      "deferred_id": "DF-1",
      "source_finding_id": "C-2",
      "deferred_reason": "Phase progression still ongoing; updating now creates another stale table",
      "recommended_future_phase": "documentation consolidation phase",
      "blocking_dependency": "83-series phase completion",
      "risk_level": "low",
      "status": "deferred"
    },
    {
      "deferred_id": "DF-2",
      "source_finding_id": "C-6",
      "deferred_reason": "Cross-document architecture clarification needs dedicated phase",
      "recommended_future_phase": "documentation consolidation phase",
      "blocking_dependency": null,
      "risk_level": "medium",
      "status": "deferred"
    },
    {
      "deferred_id": "DF-3",
      "source_finding_id": "C-5",
      "deferred_reason": "Well-defined in 82D; back-reference can wait for consolidation",
      "recommended_future_phase": "documentation consolidation phase",
      "blocking_dependency": null,
      "risk_level": "low",
      "status": "deferred"
    },
    {
      "deferred_id": "DF-4",
      "source_finding_id": "G-1",
      "deferred_reason": "Multi-file change with higher risk; flags correct within each document",
      "recommended_future_phase": "documentation consolidation phase",
      "blocking_dependency": null,
      "risk_level": "medium",
      "status": "deferred"
    }
  ],
  "rejected_items": [
    {
      "rejected_id": "RJ-1",
      "source_finding_id": "L-1",
      "rejection_reason": "Wording is technically accurate in context; defense-in-depth belongs in implementation docs",
      "risk_level": "low",
      "status": "rejected"
    },
    {
      "rejected_id": "RJ-2",
      "source_finding_id": "L-2",
      "rejection_reason": "Standard convention with adequate explanation present",
      "risk_level": "low",
      "status": "rejected"
    },
    {
      "rejected_id": "RJ-3",
      "source_finding_id": "L-3",
      "rejection_reason": "Clear in context; validation checklist is a summary, not specification",
      "risk_level": "low",
      "status": "rejected"
    },
    {
      "rejected_id": "RJ-4",
      "source_finding_id": "L-4",
      "rejection_reason": "Conservative defaults are a feature; changing weakens the example",
      "risk_level": "low",
      "status": "rejected"
    }
  ],
  "aggregate_counts": {
    "total_candidates": 3,
    "approved_candidates": 3,
    "executed_candidates": 3,
    "deferred_items": 4,
    "rejected_items": 4,
    "blocked_items": 0,
    "total_items": 11
  },
  "authorization_flags": {
    "adoption_authorized": true,
    "adoption_execution_authorized": true,
    "adoption_performed": true,
    "commit_authorized": false,
    "push_authorized": false,
    "execution_authorized": false
  },
  "validation_result": {
    "metadata_complete": true,
    "candidate_ids_unique": true,
    "source_linkage_valid": true,
    "target_files_valid": true,
    "scope_valid": true,
    "risk_levels_present": true,
    "approval_status_consistent": true,
    "execution_status_consistent": true,
    "counts_match": true,
    "validation_errors": [],
    "validation_warnings": []
  },
  "failure_classification": null
}
```

This is an illustrative example only. No executable schema file is created in 84E.

---

## Failure Cases

| # | Failure | Detection | Handling |
|---|---------|-----------|----------|
| 1 | Candidate missing source finding | `source_finding_id` absent or invalid | Block candidate; `CANDIDATE_SOURCE_LINK` violation |
| 2 | Candidate missing target file | `target_file` null for non-deferred/rejected candidate | Block; `CANDIDATE_TARGET_FILE` violation |
| 3 | Candidate targets forbidden path | Target matches `forbidden_path_patterns` | Block; `TARGET_NOT_FORBIDDEN` violation |
| 4 | Candidate requires source mutation | `source_mutation_allowed=true` without authorization | Block; `NO_SOURCE_TARGET` violation |
| 5 | Candidate requires test mutation | `test_mutation_allowed=true` without authorization | Block; `NO_TEST_TARGET` violation |
| 6 | Candidate requires README mutation | `readme_mutation_allowed=true` without authorization | Block; `NO_README_TARGET` violation |
| 7 | Candidate touches docs/REAL_CAPTURED_TASKS.md | Target is docs/REAL_CAPTURED_TASKS.md | Block; `NO_REAL_CAPTURED_TARGET` violation |
| 8 | Candidate adopts raw backend text | `raw_backend_text_allowed=false` but raw text pasted | Block; `NO_RAW_BACKEND_TEXT` violation |
| 9 | Candidate scope too broad | `broad_rewrite_allowed=false` but broad changes proposed | Block; `NO_BROAD_REWRITE` violation |
| 10 | Candidate lacks human approval | Execution attempted without `adoption_approval_status=approved` | Block; `APPROVAL_BEFORE_EXECUTION` |
| 11 | Candidate executed before approval | `execution_status=executed` but `adoption_approval_status≠approved` | Block; `EXECUTION_REQUIRES_AUTH` |
| 12 | Candidate executed outside scope | Diff exceeds `max_change_size_policy` or touches unapproved areas | Verification failure |
| 13 | Deferred item lacks reason | `deferred_reason` empty | Block; `DEFERRED_REASON_REQUIRED` |
| 14 | Rejected item lacks reason | `rejection_reason` empty | Block; `REJECTED_REASON_REQUIRED` |
| 15 | Candidate counts mismatch | `aggregate_counts` don't match listed entries | Block; `COUNTS_MATCH` |
| 16 | Execution artifact missing | `execution_status=executed` but `execution_artifact=null` | Block; `EXECUTED_HAS_ARTIFACT` |
| 17 | Diff summary missing | `execution_status=executed` but `execution_diff_summary=null` | Block; `EXECUTED_DIFF_SUMMARY` |
| 18 | Commit/push conflated with adoption | Approval implies commit/push authorization | Block; `APPROVAL_NOT_COMMIT_PUSH` |

---

## Migration from 83I–83K Artifacts

The current documentation-only adoption format maps to this schema:

| Current (markdown) | Schema field |
|-------------------|-------------|
| 83I Adoption Candidate List tables | `candidates` array |
| 83I Deferred Item List tables | `deferred_items` array |
| 83I Rejected Item List tables | `rejected_items` array |
| 83I Suggested Future Target Files table | `candidates[].target_file` |
| 83J Approved Candidates sections | `candidates[].adoption_approval_status`, `approved_by` |
| 83J Exact Approval Scope | `candidates[].scope_summary`, `allowed_change_type` |
| 83J Forbidden Changes list | `candidates[].forbidden_path_patterns`, safety constraints |
| 83K Candidate-by-Candidate Execution Summary | `candidates[].execution_status`, `execution_diff_summary` |
| 83K Exact Scope Verification | Verification requirement fields |
| 83K Forbidden Change Verification | `forbidden_files_verified` etc. |
| 83I/83J/83K Authorization Flags tables | `authorization_flags` |
| 83I/83J/83K Review/Approval/Execution Outcome tables | `candidate_set_status` |

A future implementation phase could generate schema instances from existing markdown or populate them during governed adoption review.

---

## Schema Status

| Field | Value |
|-------|-------|
| schema_name | multi_agent_adoption_candidate |
| schema_version | 0.1 |
| schema_status | draft_documented |
| schema_implementation_status | not_started |

## Recommended Next Phase

**84F — Multi-Agent Lifecycle State Machine**

84F should define the documentation-only lifecycle state machine tying the four schemas together: prompt package → capture metadata → output intake → adoption candidates, with explicit state transitions, gating rules, and closure conditions. This completes the schema suite and prepares for command-line orchestration design.
