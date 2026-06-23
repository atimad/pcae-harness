# Persistent Lifecycle Memory Model

## 1. Purpose

Define the durable memory model for PCAE lifecycle state, approvals, captures, adoption
decisions, blocked/deferred items, and safe next actions. This model enables PCAE to persist
and reconstruct project state across session boundaries, answering governance questions from
committed artifacts rather than ephemeral conversation memory.

## 2. Scope

Design only. This artifact defines memory entities, fields, relationships, update rules,
query targets, provenance requirements, and safety boundaries. It does not implement
memory storage, create machine-readable files, or add tests.

## 3. Non-Goals

- Implementing memory storage or CLI commands.
- Creating `.pcae` memory directories or snapshot files.
- Adding tests.
- Modifying source code.
- Backend invocation, prompt sending, capture, intake, or adoption.
- Artifact indexing (85B), event timeline (85C), decision log (85D), risk register (85E),
  or project snapshot (85F).

## 4. Motivation from Phase 84 and Roadmap Reconciliation

The original Phase 84 roadmap proposed persistent memory so PCAE could answer:
- What phase are we in?
- What was approved?
- What is blocked?
- What can be safely done next?
- What must never be repeated?

Phase 84 instead produced 10 governance design artifacts defining the lifecycle objects that
memory will track: prompt packages, capture metadata, output intake, adoption candidates,
lifecycle states, command surfaces, invocation guards, storage policies, and deferred items.

Phase 84L (`docs/ROADMAP_RECONCILIATION_PHASE_85_PLAN.md`) formally moved the memory goals
to Phase 85, with 85A (this phase) defining the memory model that underpins the rest of the
85 sequence.

---

## 5. Memory Model Design Principles

1. Memory records observed governance state, not permission by itself.
2. Memory does not authorize execution.
3. Memory does not authorize backend invocation.
4. Memory does not authorize adoption.
5. Memory does not authorize commit or push.
6. Memory must distinguish approved, performed, deferred, rejected, blocked, and unknown.
7. Memory must preserve provenance (link claims to artifacts or commits).
8. Memory must preserve safety boundaries.
9. Memory must support reconstruction after chat/session reset.
10. Memory must support offline audit.
11. Memory must identify next safe actions without performing them.
12. Memory is secondary to repo state — if memory and repo disagree, repo wins.

## 6. Memory Threat Model

| # | Threat | Impact |
|---|--------|--------|
| MT-1 | Stale memory causes unsafe next action recommendation | Agent performs action that was blocked since last memory update |
| MT-2 | Approval remembered without evidence | Action treated as approved without artifact proof |
| MT-3 | Blocked item forgotten | Dangerous action proceeds without guard |
| MT-4 | Rejected item reintroduced | Previously rejected candidate treated as viable |
| MT-5 | Deferred item treated as approved | Implementation starts without approval lifecycle |
| MT-6 | Backend invocation inferred from memory alone | Memory used as authorization for invocation |
| MT-7 | Commit/push authorization inferred from memory alone | Memory used to bypass governance gates |
| MT-8 | Missing artifact silently ignored | Memory claims artifact exists when it does not |
| MT-9 | Phase status misreported | Agent acts on wrong phase assumption |
| MT-10 | Chat memory contradicts repo memory | Conversation claims diverge from committed state |
| MT-11 | Latest phase lost after session reset | New session starts from stale phase |
| MT-12 | Human override not recorded | Operator decision lost between sessions |
| MT-13 | Structural validator warning mistaken for blocker | Non-blocking signal prevents progress |
| MT-14 | Implementation status misreported | Design-only phase treated as implemented |
| MT-15 | Provenance chain broken | Claim cannot be traced to source |

---

## 7. Core Memory Entities

| Entity | Purpose |
|--------|---------|
| `project_state` | Top-level snapshot of current project governance state |
| `phase_record` | Record of a completed or active phase |
| `lifecycle_state` | Current lifecycle state machine position |
| `artifact_record` | Metadata about a governance artifact |
| `approval_record` | Record of a human or system approval |
| `authorization_flag_record` | State of a governance authorization flag |
| `backend_invocation_record` | Record of a backend invocation event |
| `capture_record` | Record of an output capture event |
| `intake_record` | Record of an output intake/classification event |
| `adoption_candidate_record` | Record of an adoption candidate and its disposition |
| `deferred_item_record` | Record of a deferred item and its status |
| `risk_record` | Record of an active, mitigated, or blocked risk |
| `decision_record` | Record of a governance decision (approve/reject/defer/block) |
| `commit_record` | Record of a governed commit |
| `push_record` | Record of a governed push |
| `handoff_record` | Record of handoff state and refresh status |
| `bootstrap_record` | Record of bootstrap profile and test configuration |
| `next_action_record` | Advisory record of safe next actions |

## 8. Entity Relationship Model

```
project_state
  ├── phase_record[] (history of all phases)
  ├── lifecycle_state (current state machine position)
  ├── artifact_record[] (known governance artifacts)
  ├── approval_record[] (approval history)
  ├── authorization_flag_record[] (current flag states)
  ├── backend_invocation_record[] (invocation history)
  ├── capture_record[] (capture history)
  ├── intake_record[] (intake history)
  ├── adoption_candidate_record[] (candidate history)
  ├── deferred_item_record[] (deferred items)
  ├── risk_record[] (risk register)
  ├── decision_record[] (decision log)
  ├── commit_record[] (commit history)
  ├── push_record[] (push history)
  ├── handoff_record (current handoff state)
  ├── bootstrap_record (bootstrap profile)
  └── next_action_record[] (advisory next actions)
```

Key relationships:
- `capture_record` references `backend_invocation_record` and `approval_record`.
- `intake_record` references `capture_record`.
- `adoption_candidate_record` references `intake_record` and `decision_record`.
- `deferred_item_record` references `decision_record`.
- `phase_record` references `commit_record` and `push_record`.
- `next_action_record` is derived from all other entities (read-only advisory).

---

## 9. Required Top-Level Memory Fields

| Field | Type | Purpose |
|-------|------|---------|
| `memory_snapshot_id` | string | Unique identifier for this snapshot |
| `memory_model_version` | string | Version of the memory model schema |
| `project_id` | string | Project identifier |
| `repository_path` | string | Repository filesystem path |
| `current_phase` | string | Currently active phase |
| `latest_completed_phase` | string | Most recently completed phase |
| `current_lifecycle_state` | string | Current lifecycle state machine state |
| `roadmap_position` | string | Position in roadmap sequence |
| `phase_85_position` | string | Position within Phase 85 sequence |
| `last_verified_commit` | string | Latest commit verified by PCAE commands |
| `origin_sync_status` | string | Sync status with origin/main |
| `health_status` | string | Latest pcae health result |
| `governance_status` | string | Summary governance state |
| `artifact_index_status` | string | Whether artifact index is current |
| `deferred_item_status` | string | Summary of deferred items |
| `risk_status` | string | Summary risk state |
| `next_safe_actions` | list | Advisory list of safe next actions |
| `forbidden_actions` | list | Explicit list of forbidden actions |
| `provenance` | object | Source references for this snapshot |
| `created_at` | timestamp | When this snapshot was created |
| `updated_at` | timestamp | When this snapshot was last updated |

## 10. Lifecycle State Memory

| Field | Type | Purpose |
|-------|------|---------|
| `current_state` | string | Current lifecycle state (e.g., closed, active, blocked) |
| `previous_state` | string | Previous lifecycle state |
| `allowed_next_states` | list | States reachable from current state |
| `blocked_next_states` | list | States blocked from current state with reasons |
| `state_source_artifact` | string | Artifact providing state evidence |
| `state_machine_version` | string | Version of the lifecycle state machine design |
| `state_last_verified_at` | timestamp | When state was last verified against repo |
| `state_confidence` | string | high/medium/low based on verification recency |

## 11. Approval Memory

| Field | Type | Purpose |
|-------|------|---------|
| `approval_id` | string | Unique approval identifier |
| `approval_type` | string | Type (routing, invocation, adoption, commit, push) |
| `approved_action` | string | What was approved |
| `approved_scope` | string | Scope of approval (files, agents, operations) |
| `approved_files` | list | Files within approval scope |
| `approved_agents` | list | Agents within approval scope |
| `approval_artifact` | string | Path to approval artifact |
| `approval_phase` | string | Phase in which approval was granted |
| `approval_status` | string | active/expired/superseded/revoked |
| `approval_timestamp` | timestamp | When approval was granted |
| `approval_expires_or_superseded_by` | string | Expiry condition or superseding approval |

### Authorization Flag Memory

| Field | Type | Purpose |
|-------|------|---------|
| `flag_name` | string | Flag identifier (e.g., execution_authorized) |
| `flag_value` | boolean | Current value |
| `flag_source` | string | Source of current value (artifact, command, default) |
| `flag_phase` | string | Phase in which flag was last set |
| `flag_reason` | string | Reason for current value |
| `flag_last_verified_at` | timestamp | When flag was last verified |

## 12. Capture Memory

| Field | Type | Purpose |
|-------|------|---------|
| `capture_id` | string | Unique capture identifier |
| `prompt_package_id` | string | Associated prompt package |
| `agent_id` | string | Agent that was invoked |
| `role_id` | string | Role the agent played |
| `stdout_sha256` | string | SHA256 of captured stdout |
| `stderr_sha256` | string | SHA256 of captured stderr |
| `capture_artifact` | string | Path to capture metadata artifact |
| `capture_status` | string | captured/failed/timeout |
| `mutation_detected` | boolean | Whether repo mutation was detected |
| `capture_storage_status` | string | stored/volatile/lost |

## 13. Intake Memory

| Field | Type | Purpose |
|-------|------|---------|
| `intake_id` | string | Unique intake identifier |
| `capture_id` | string | Associated capture |
| `intake_status` | string | completed/blocked/failed |
| `intake_outcome` | string | reviewable_candidate/not_reviewable/blocked |
| `prompt_adherence_result` | string | pass/fail with counts |
| `safety_result` | string | pass/fail with counts |
| `contract_fit_result` | string | pass/fail with counts |
| `cross_output_result` | string | pass/fail with counts |
| `reviewable_candidate_count` | integer | Count of reviewable candidates |
| `blocked_reason` | string | Reason if blocked |

## 14. Adoption Memory

| Field | Type | Purpose |
|-------|------|---------|
| `candidate_set_id` | string | Identifier for the candidate set |
| `candidate_count` | integer | Total candidates identified |
| `approved_candidate_count` | integer | Candidates approved |
| `executed_candidate_count` | integer | Candidates executed/adopted |
| `deferred_count` | integer | Candidates deferred |
| `rejected_count` | integer | Candidates rejected |
| `adoption_approval_artifact` | string | Path to approval artifact |
| `adoption_execution_artifact` | string | Path to execution artifact |
| `adoption_status` | string | pending/approved/executed/closed |

## 15. Deferred Item Memory

| Field | Type | Purpose |
|-------|------|---------|
| `item_id` | string | Deferred item identifier (e.g., DF-1, IMPL-1) |
| `item_type` | string | Category (adoption, schema, command, hygiene, test) |
| `item_status` | string | open/review_pending/accepted/blocked/rejected/closed |
| `source_artifact` | string | Artifact where item was identified |
| `source_phase` | string | Phase where item was identified |
| `risk_level` | string | low/medium/high |
| `target_phase` | string | Phase where item should be addressed |
| `closure_status` | string | open/closed_no_action/implemented/superseded |
| `last_reviewed_at` | timestamp | When item was last reviewed |

## 16. Risk and Blocker Memory

| Field | Type | Purpose |
|-------|------|---------|
| `risk_id` | string | Risk identifier |
| `risk_type` | string | Category (invocation, adoption, mutation, storage, governance) |
| `risk_status` | string | active/mitigated/accepted/blocked/resolved |
| `risk_level` | string | low/medium/high/critical |
| `source_artifact` | string | Artifact documenting the risk |
| `blocking_condition` | string | What this risk blocks |
| `mitigation` | string | Current or planned mitigation |
| `next_review_phase` | string | Phase for next review |

## 17. Phase History Memory

| Field | Type | Purpose |
|-------|------|---------|
| `phase_id` | string | Phase identifier (e.g., 84L, 85A) |
| `phase_name` | string | Full phase name |
| `phase_status` | string | active/completed/skipped |
| `phase_type` | string | design/implementation/assessment/planning/refresh |
| `artifact_paths` | list | Paths to phase artifacts |
| `implementation_commit` | string | Implementation commit hash |
| `completion_commit` | string | Completion commit hash |
| `pushed_status` | string | pushed/unpushed |
| `tests_added` | boolean | Whether tests were added |
| `source_changed` | boolean | Whether source was modified |
| `docs_changed` | boolean | Whether docs were modified |
| `readme_changed` | boolean | Whether README was modified |
| `forbidden_files_untouched` | boolean | Whether forbidden files remained untouched |

## 18. Commit/Push Memory

| Field | Type | Purpose |
|-------|------|---------|
| `implementation_commit` | string | Implementation commit hash |
| `completion_commit` | string | Completion commit hash |
| `push_method` | string | governed_pcae_push/raw_git_push/not_pushed |
| `origin_main_head_count` | integer | Commits ahead of origin at time of push |
| `raw_git_push_used` | boolean | Whether raw git push was used (should be false) |
| `force_push_used` | boolean | Whether force push was used (should be false) |
| `push_status` | string | pushed/failed/pending |

## 19. Handoff and Bootstrap Memory

| Field | Type | Purpose |
|-------|------|---------|
| `handoff_refresh_status` | string | Current handoff-state-refresh result |
| `handoff_structural_signals` | object | Count and classification of structural signals |
| `bootstrap_profile` | string | Current bootstrap profile state |
| `default_test_command` | string | `python -m pytest -n auto` |
| `serial_test_exceptions` | integer | Count of retained serial exceptions (3) |
| `runtime_execution_authorized` | boolean | Whether runtime execution is authorized (false) |

---

## 20. Query Model

The memory model should eventually answer the original project-intelligence questions:

### Q1: What phase are we in?

| Field | Value |
|-------|-------|
| Required entities | `project_state`, `phase_record` |
| Expected answer shape | `{current_phase, latest_completed_phase, phase_status, phase_type}` |
| Required provenance | `phase_record.completion_commit` or active task contract path |
| Safety caveats | Answer is advisory; does not authorize any action |

### Q2: What was approved?

| Field | Value |
|-------|-------|
| Required entities | `approval_record`, `authorization_flag_record`, `decision_record` |
| Expected answer shape | `[{approval_id, approved_action, approval_status, approval_artifact}]` |
| Required provenance | Each approval must reference an artifact path |
| Safety caveats | Past approval does not imply current authorization; check flag currency |

### Q3: What is blocked?

| Field | Value |
|-------|-------|
| Required entities | `risk_record`, `deferred_item_record`, `lifecycle_state` |
| Expected answer shape | `[{blocked_item, blocking_condition, risk_level, source}]` |
| Required provenance | Each blocker must reference a risk/deferred record |
| Safety caveats | Structural validator signals should be distinguished from substantive blockers |

### Q4: What is deferred?

| Field | Value |
|-------|-------|
| Required entities | `deferred_item_record` |
| Expected answer shape | `[{item_id, item_type, item_status, target_phase}]` |
| Required provenance | Each deferred item must reference source artifact and phase |
| Safety caveats | Deferred does not mean approved; implementation still requires lifecycle |

### Q5: What can be safely done next?

| Field | Value |
|-------|-------|
| Required entities | `next_action_record`, `lifecycle_state`, `authorization_flag_record` |
| Expected answer shape | `[{action, safety_level, prerequisites, provenance}]` |
| Required provenance | Each action must cite lifecycle state and flag state |
| Safety caveats | Advisory only; does not authorize execution; human approval still required |

### Q6: What must never be repeated?

| Field | Value |
|-------|-------|
| Required entities | `decision_record` (rejected), `risk_record` (blocked), `forbidden_actions` |
| Expected answer shape | `[{forbidden_action, reason, source_decision, source_phase}]` |
| Required provenance | Each forbidden action must reference a decision or risk record |
| Safety caveats | Enforcement is separate from reporting; memory reports, gates enforce |

### Q7: What artifacts support this answer?

| Field | Value |
|-------|-------|
| Required entities | `artifact_record`, `provenance` chain from any query |
| Expected answer shape | `[{artifact_path, artifact_type, last_verified}]` |
| Required provenance | Artifact must exist on filesystem when referenced |
| Safety caveats | Missing artifact invalidates claims that depend on it |

### Q8: What changed since last snapshot?

| Field | Value |
|-------|-------|
| Required entities | Previous `project_state` vs current |
| Expected answer shape | `{new_phases, new_approvals, new_risks, flag_changes, new_commits}` |
| Required provenance | Comparison requires two valid snapshots |
| Safety caveats | Drift detection is informational; does not auto-correct |

### Q9: What requires human review?

| Field | Value |
|-------|-------|
| Required entities | `risk_record`, `deferred_item_record`, `handoff_record` |
| Expected answer shape | `[{item, reason, urgency, recommended_phase}]` |
| Required provenance | Each review item must cite source |
| Safety caveats | Human review recommendations are advisory, not mandatory gates |

---

## 21. Update Rules

1. Memory updates only after verified phase completion (commit + push evidence).
2. Memory update must cite source artifact or commit.
3. Memory update must not infer approval from plan text.
4. Memory update must preserve rejected/deferred state (no silent promotion).
5. Memory update must not overwrite failed evidence.
6. Memory update must distinguish latest observed state from authorized next action.
7. Memory update must be idempotent (same input produces same output).
8. Memory update must be reviewable (diff-able against previous snapshot).
9. Memory update must not create new authorization (memory is observational).
10. Memory update must verify artifact existence before recording artifact claims.
11. Memory update must record the update's own provenance (who/what/when/why).
12. Memory update must not rely on chat-only claims when repo artifacts exist.

## 22. Provenance and Evidence Policy

| Priority | Source | Trust Level |
|----------|--------|-------------|
| 1 | Repo state (git status, committed files) | Highest — ground truth |
| 2 | PCAE command outputs (health, check, doctor, lifecycle) | High — verified state |
| 3 | Committed artifacts (docs/, tasks/) | High — versioned evidence |
| 4 | Human final reports (operator-provided phase summaries) | Medium — reconcile with repo |
| 5 | Conversation memory (chat context) | Lowest — ephemeral, may be stale |

Every memory claim must reference an artifact, command result, or commit. Human-reported
phase outputs may be recorded but should be reconciled with repo artifacts when possible.
Chat memory is secondary to repo artifacts. If chat memory contradicts repo state, repo wins.

## 23. Safety Boundaries

1. Persistent memory does not authorize backend invocation.
2. Persistent memory does not authorize prompt sending.
3. Persistent memory does not authorize adoption.
4. Persistent memory does not authorize source/test mutation.
5. Persistent memory does not authorize commit or push.
6. Persistent memory does not override active task contracts.
7. Persistent memory does not override `pcae check` results.
8. Persistent memory does not override human approval boundaries.
9. Memory queries that return "next safe action" are advisory only.
10. Memory cannot grant permissions that governance gates control.
11. A "remembered approval" without an artifact reference is not valid.
12. Memory must never be the sole basis for irreversible actions.

## 24. Storage and Implementation Assumptions

- Storage implementation has not started.
- No `.pcae` memory storage is created in 85A.
- No machine-readable memory file is created in 85A.
- Future implementation may define `.pcae/memory/` storage only in an explicit implementation phase.
- Future implementation must include tests.
- Storage format decisions (JSON, SQLite, flat files) are deferred to implementation.
- Memory snapshots should be reconstructible from repo artifacts (not single-source-of-truth).

## 25. Future Implementation Plan

Candidate future phases after this design:

| Phase | Name | Scope |
|-------|------|-------|
| 85A.1 | Persistent Lifecycle Memory Model Implementation Plan | Detailed implementation spec |
| 85A.2 | Memory Snapshot Read-Only Prototype | First read-only memory command |
| 85A.3 | Memory Snapshot Tests | Test suite for memory model |

No task contracts are created for these phases in 85A. They are documented as future
candidates only.

## 26. Future Test Coverage

No tests are added in 85A because this is design-only. Future implementation must test:

| Test Area | Coverage Target |
|-----------|----------------|
| Memory snapshot parsing | Required fields present and typed correctly |
| Phase status reconstruction | Correct phase reported from committed artifacts |
| Approval query answers | Only artifact-backed approvals returned |
| Blocked/deferred/rejected handling | Status distinctions preserved correctly |
| Next safe action query | Advisory only, no execution authorization |
| Forbidden action query | Explicit forbidden list returned |
| Provenance requirement validation | Claims without provenance rejected |
| Idempotent updates | Same input produces same snapshot |
| Stale-memory detection | Drift between memory and repo state flagged |
| Missing artifact handling | Claims about missing artifacts invalidated |

## 27. Example Memory Snapshot

This is illustrative markdown only, not an executable format:

```
memory_snapshot_id: example-85a-001
memory_model_version: 0.1
project_id: pcae-harness
repository_path: /Users/atilamadai/repos/pcae-harness
current_phase: 85A — Persistent Lifecycle Memory Model
latest_completed_phase: 84L — Roadmap Reconciliation and Phase 85 Plan
current_lifecycle_state: closed
roadmap_position: Phase 85 planned, 85A active
phase_85_position: 85A (first phase in sequence)
last_verified_commit: 2478ef81
origin_sync_status: synced
health_status: healthy
governance_status: restrictive (all execution flags false)
artifact_index_status: not_implemented
deferred_item_status: 9 items (DF-1–4, HY-1, IMPL-1–2, TEST-1, HSR-1)
risk_status: no active blockers
next_safe_actions:
  - Complete 85A memory model design
  - Proceed to 85B Artifact Index after 85A completion
forbidden_actions:
  - Backend invocation without guard approval
  - Prompt sending without lifecycle authorization
  - Adoption without intake/review/approval
  - Source/test mutation without implementation phase
  - Commit/push without governed pcae push
  - Force push
  - Raw git push
provenance:
  latest_phase_source: commit 2478ef81
  health_source: pcae health command
  governance_source: pcae lifecycle backend-output-adoption summary
created_at: 2026-06-24T00:00:00Z
updated_at: 2026-06-24T00:00:00Z
```

---

## 28. Validation Rules

| # | Rule |
|---|------|
| V-1 | Memory snapshot must have a unique `memory_snapshot_id` |
| V-2 | `memory_model_version` must be present and match a known version |
| V-3 | `latest_completed_phase` must be present |
| V-4 | `current_lifecycle_state` must be present |
| V-5 | `health_status` must be present |
| V-6 | `governance_status` must be present |
| V-7 | Every `approval_record` must have a non-empty `approval_artifact` (provenance) |
| V-8 | Every blocked item must have a `blocking_condition` |
| V-9 | Every `deferred_item_record` must have `target_phase` or `last_reviewed_at` |
| V-10 | Every rejected item must remain rejected unless reopened with explicit approval |
| V-11 | `next_safe_actions` must not imply execution authorization |
| V-12 | `forbidden_actions` must be explicitly populated |
| V-13 | `commit_record` must preserve push governance boundaries |
| V-14 | `backend_invocation_record` must distinguish authorized from performed |
| V-15 | `adoption_candidate_record` must distinguish approved from performed |
| V-16 | Source/test mutation flags must remain false unless explicitly scoped in an implementation phase |
| V-17 | Memory must not rely on chat-only claims when repo artifacts exist |
| V-18 | Memory must not overwrite failed evidence |
| V-19 | Memory update requires phase completion evidence (commit hash) |
| V-20 | Memory implementation requires tests |
| V-21 | Design-only phase creates no storage |
| V-22 | No `.pcae` memory storage created in 85A |
| V-23 | No source/test changes in 85A |
| V-24 | No tests added in design-only 85A |
| V-25 | No phase beyond 85A started in this phase |
| V-26 | `current_phase` must match active task contract |
| V-27 | `origin_sync_status` must be verifiable via git |
| V-28 | `provenance` must contain at least one source reference |
| V-29 | `risk_record` must have `risk_level` from allowed values |
| V-30 | `phase_record.completion_commit` must be a valid git hash |
| V-31 | `authorization_flag_record.flag_value` must be boolean |
| V-32 | `capture_record.stdout_sha256` must be 64 hex characters when present |
| V-33 | `deferred_item_record.item_status` must be from allowed status values |
| V-34 | `next_action_record` must include `prerequisites` |
| V-35 | `handoff_record.handoff_structural_signals` must classify signals as structural or substantive |
| V-36 | `updated_at` must be >= `created_at` |
| V-37 | `memory_snapshot_id` must not collide with previously recorded snapshots |
| V-38 | `lifecycle_state.state_confidence` must be one of high/medium/low |

## 29. Failure Cases

| # | Failure | Impact |
|---|---------|--------|
| F-1 | Memory missing latest phase | Agent operates on stale phase assumption |
| F-2 | Memory missing provenance | Claims cannot be verified |
| F-3 | Approval recorded without artifact | Action treated as approved without evidence |
| F-4 | Blocked item forgotten | Unsafe action proceeds |
| F-5 | Deferred item treated as approved | Implementation starts without lifecycle |
| F-6 | Rejected item reopened silently | Previously rejected work reintroduced |
| F-7 | Next safe action implies execution | Advisory crossed into authorization |
| F-8 | Commit/push authorization inferred from memory | Governance gate bypassed |
| F-9 | Stale handoff-state-refresh signal treated as blocker without context | Progress blocked by structural signal |
| F-10 | Artifact missing but memory claims it exists | Actions based on non-existent evidence |
| F-11 | Source-of-truth conflict unresolved | Memory and repo disagree, no reconciliation |
| F-12 | Memory implementation attempted in design phase | Premature implementation violates governance |
| F-13 | Tests skipped in implementation phase | Implementation without verification |
| F-14 | Memory update without commit evidence | Snapshot based on uncommitted state |
| F-15 | Chat memory overrides repo state | Ephemeral source used over persistent source |

---

## 30. Recommended Next Phase

**85B — Artifact Index**

85B should define a searchable/indexable registry of governance artifacts, schemas, lifecycle
traces, phase outputs, and status documents. It builds on 85A by defining what the memory
model can index and reference.

---

## Memory Model Identity

| Field | Value |
|-------|-------|
| memory_model_name | persistent_lifecycle_memory_model |
| memory_model_version | 0.1 |
| memory_model_status | draft_documented |
| memory_model_implementation_status | not_started |

## Authorization Flags for 85A

| Flag | Value |
|------|-------|
| backend_invocation_performed | false |
| new_prompts_sent | false |
| new_capture_performed | false |
| new_intake_performed | false |
| new_adoption_review_performed | false |
| new_adoption_approval_performed | false |
| new_adoption_execution_performed | false |
| repo_mutation_authorized | true_for_memory_model_docs_status_only |
| readme_mutation_authorized | false |
| source_mutation_authorized | false |
| test_mutation_authorized | false |
| docs_real_captured_tasks_mutation_authorized | false |
| persistent_memory_implementation_authorized | false |
| artifact_index_implementation_authorized | false |
| phase_85b_task_contract_authorized | false |
| commit_authorized | false |
| push_authorized | false |
| execution_authorized | false |
