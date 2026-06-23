# Multi-Agent Deferred Item Tracker

## Purpose

Define a tracking policy for deferred items, blocked items, rejected items, carry-forward items, hygiene items, and future implementation tasks in governed multi-agent work. The tracker ensures that items not adopted or implemented immediately are formally recorded with reasons, risk levels, future dispositions, and review requirements so they are not forgotten, silently reintroduced, or implemented without approval.

## Scope

Tracker policy documentation only. This artifact defines item categories, status values, required fields, review cadence, escalation rules, closure conditions, and illustrative examples. It does not implement tracker storage, CLI commands, or executable files.

## Non-Goals

- Tracker implementation in code.
- Machine-readable tracker storage.
- CLI command implementation.
- Backend invocation or prompt sending.
- Output capture, intake, or adoption.
- Task filename hygiene execution.
- Source code or test changes.
- Executable tracker files outside docs.

## Motivation from 83I–83L and 84A–84I

### 83I — Adoption Review

Phase 83I reviewed 11 intaked findings and classified them as 3 adoption candidates (AC-1, AC-2, AC-3), 4 deferred items (DF-1, DF-2, DF-3, DF-4), and 4 rejected items (RJ-1, RJ-2, RJ-3, RJ-4). The deferred and rejected items were carried as prose in the adoption review document. No structured tracking existed.

### 83J–83K — Adoption Approval and Execution

AC-1, AC-2, and AC-3 were approved and executed. DF-1 through DF-4 were explicitly excluded from approval and execution. RJ-1 through RJ-4 remained rejected. The deferred items were mentioned in each phase's document but had no formal tracking mechanism.

### 83L — Final Verification

The final verification confirmed that deferred items were documented and carried forward, but relied on human memory to track them across lifecycle boundaries.

### 84A — Lessons Roadmap

The 84A roadmap identified "Deferred item tracking" (84J) as LOW priority but necessary to prevent forgotten deferrals as lifecycles grow more complex. It explicitly listed DF-1 through DF-4 as carried forward.

### 84B–84I — Design Documentation Suite

The 84-series produced 8 design documents, each with `implementation_status=not_started`. These represent future implementation tasks that need tracking. Additionally, task filename hygiene issues emerged (task filenames with truncated slugs) that need tracking without being fixed in documentation-only phases.

---

## Deferred Item Threat Model

| # | Threat | Risk | Mitigation |
|---|--------|------|-----------|
| T1 | Deferred item forgotten | Governance gap persists indefinitely | Structured tracker with review cadence |
| T2 | Blocked safety issue reopened accidentally | Unsafe work proceeds without proper review | Blocked items require human review and explicit approval before reopening |
| T3 | Rejected item reintroduced | Previously rejected change applied | Rejected items remain rejected unless explicitly reopened with documented reason |
| T4 | Future implementation task loses context | Implementer lacks design rationale | Each item includes source artifact and phase reference |
| T5 | Task hygiene issue remains invisible | Accumulated small issues degrade project quality | Hygiene category with severity and evidence |
| T6 | Deferred item lacks owner | No one responsible for resolution | Review cadence assigns review responsibility at phase boundaries |
| T7 | Deferred item lacks reason | Cannot judge whether deferral is still valid | Reason is a required field |
| T8 | Deferred item lacks target phase | No plan for resolution | Target phase or disposition is a required field |
| T9 | Deferred item becomes stale | Context drifts, item no longer relevant | Stale detection via `last_reviewed_at` and review cadence |
| T10 | Deferred item implemented without approval | Unapproved work enters repo | Implementation requires separate phase with explicit authorization |
| T11 | Deferred item touches forbidden file without explicit scope | Protected file modified without governance | Forbidden-file items require explicit future scope authorization |
| T12 | Deferred item bypasses adoption approval | Backend-originated item applied without review/approval | Adoption pipeline (intake→review→approve→execute) still required |
| T13 | Blocked automation work normalized as allowed | Unsafe automation proceeds without re-evaluation | Blocked items cannot transition to `implemented` without human review |

---

## Tracker Design Principles

1. **Deferred is not approved.** Deferring an item does not approve it for future execution. Execution requires its own approval.
2. **Deferred is not rejected.** Deferred items remain candidates for future work. They are explicitly not rejected.
3. **Rejected remains rejected unless explicitly reopened.** Reopening requires documented reason and human approval.
4. **Blocked requires human review before reopening.** Blocked items represent safety or policy concerns that must be resolved before work proceeds.
5. **Every deferred item needs a reason.** The reason explains why the item was not addressed immediately.
6. **Every deferred item needs a future disposition.** The disposition describes when and how the item should be revisited.
7. **Future implementation requires a separate phase.** No deferred item can be implemented within the tracker phase itself.
8. **Tracking does not authorize execution.** Recording an item in the tracker does not grant permission to implement it.
9. **Tracking does not authorize adoption.** Recording an item does not approve adoption of backend output.
10. **Tracking does not authorize commit or push.** Recording an item does not grant commit or push permissions.
11. **Deferred items must survive lifecycle closure.** Items carry forward across lifecycle boundaries and remain trackable.

---

## Deferred Item Entity Model

| Entity | Description |
|--------|-------------|
| `deferred_item` | An item identified for future work but not addressed in the current phase or lifecycle |
| `blocked_item` | An item blocked by a safety, policy, or technical condition |
| `rejected_item` | An item explicitly rejected with documented reason |
| `carry_forward_item` | An item carried from one lifecycle to the next |
| `hygiene_item` | A minor quality or consistency issue that does not affect governance correctness |
| `future_implementation_item` | A design that has been documented but not yet implemented in code |
| `source_finding` | The original finding (from intake, review, or observation) that produced this item |
| `source_artifact` | The document where the item was first identified |
| `target_phase` | The phase or phase range where this item should be addressed |
| `review_record` | A record of when this item was last reviewed |
| `closure_record` | A record of how and why this item was closed |

---

## Deferred Item Categories

| Category | Description | Example |
|----------|-------------|---------|
| `adoption_deferred` | Adoption candidate deferred to future lifecycle | DF-1 stale table update |
| `schema_implementation_deferred` | Schema design documented but not implemented | 84B prompt package schema |
| `state_machine_implementation_deferred` | State machine designed but not implemented | 84F lifecycle state machine |
| `command_implementation_deferred` | Command surface designed but not implemented | 84G command dry-run |
| `guard_implementation_deferred` | Guard design documented but not implemented | 84H invocation guard |
| `storage_implementation_deferred` | Storage policy documented but not implemented | 84I capture storage |
| `backend_integration_deferred` | Backend integration work pending governance | Future governed invocation |
| `subagent_discovery_deferred` | Subagent discovery pending probes | claude-kimi, codex subagents |
| `blocked_agent_deferred` | Agent blocked pending verification or installation | claude-kimi (missing), codex (unverified) |
| `task_hygiene_deferred` | Task file or process hygiene issue | Task filename truncation |
| `documentation_hygiene_deferred` | Documentation quality or consistency issue | Cross-reference accuracy |
| `test_coverage_deferred` | Test coverage for future implementations | Schema parser tests, guard decision tests |

---

## Deferred Item Status Model

| Status | Description |
|--------|-------------|
| `open` | Item identified, not yet reviewed for disposition |
| `review_pending` | Item queued for review at next phase boundary |
| `accepted_for_future_phase` | Item accepted for future work in a named phase |
| `blocked` | Item blocked by safety, policy, or technical condition |
| `rejected` | Item explicitly rejected with documented reason |
| `superseded` | Item replaced by a newer item or approach |
| `implemented` | Item implemented in a separate governed phase |
| `closed_no_action` | Item closed without action, with documented reason |

### Status Transitions

```
open → review_pending → accepted_for_future_phase → implemented → (closed)
                      → blocked → (human review) → accepted_for_future_phase or rejected
                      → rejected → (closed)
                      → superseded → (closed)
                      → closed_no_action
```

- `rejected` → `open` requires explicit reopen approval.
- `blocked` → `accepted_for_future_phase` requires human review.
- `implemented` requires artifact reference to the implementing phase.

---

## Required Deferred Item Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `item_id` | string | yes | Unique identifier (e.g., `DF-1`, `IMPL-1`, `HY-1`) |
| `item_type` | string | yes | Category from the categories list |
| `item_status` | string | yes | Current status |
| `item_title` | string | yes | Short description |
| `source_artifact` | string | yes | Path to the artifact where item was identified |
| `source_phase` | string | yes | Phase where item was identified |
| `source_finding_id` | string/null | no | Finding ID if from adoption review (e.g., `RISK-2`) |
| `deferred_reason` | string | yes | Why the item was deferred |
| `risk_level` | string | yes | `low`, `medium`, `high` |
| `target_phase` | string | yes | Phase or phase range for future resolution |
| `target_artifact_or_area` | string | yes | What artifact or area will be affected |
| `required_approval` | boolean | yes | Whether implementation requires explicit approval |
| `required_authorization_flags` | list[string] | yes | Flags that must be true before implementation |
| `forbidden_actions` | list[string] | yes | Actions that must not occur during implementation |
| `created_at` | string | yes | ISO timestamp or phase reference |
| `last_reviewed_at` | string/null | no | ISO timestamp of last review |
| `closure_status` | string/null | no | How the item was closed (if closed) |

---

## Blocked Item Fields

| Field | Type | Description |
|-------|------|-------------|
| `blocked_reason` | string | Why the item is blocked |
| `blocking_condition` | string | What condition prevents progress |
| `required_resolution` | string | What must happen to unblock |
| `human_review_required` | boolean (always true) | Human must review before unblocking |
| `may_retry` | boolean | Whether retry is possible after resolution |
| `retry_requires_new_approval` | boolean | Whether retry needs fresh approval |
| `quarantine_required` | boolean | Whether quarantine is needed |

---

## Rejected Item Fields

| Field | Type | Description |
|-------|------|-------------|
| `rejection_reason` | string | Why the item was rejected |
| `rejected_by_phase` | string | Phase where rejection occurred |
| `reopen_allowed` | boolean | Whether the item may be reopened |
| `reopen_conditions` | string/null | Conditions under which reopening is allowed |
| `reopen_requires_approval` | boolean (always true) | Reopening requires human approval |

---

## Carry-Forward Item Fields

| Field | Type | Description |
|-------|------|-------------|
| `carry_forward_reason` | string | Why the item is carried forward |
| `origin_lifecycle_id` | string | Lifecycle where the item originated |
| `origin_phase` | string | Phase where the item was identified |
| `destination_phase` | string | Phase where the item should be addressed |
| `destination_scope` | string | What scope the destination phase should include |
| `must_review_before_execution` | boolean (always true) | Item must be reviewed before any execution |

---

## Hygiene Item Fields

| Field | Type | Description |
|-------|------|-------------|
| `hygiene_area` | string | Area affected (e.g., `task_files`, `documentation`, `naming`) |
| `observed_issue` | string | What the issue is |
| `evidence` | string | How the issue was observed |
| `severity` | string | `low`, `medium`, `high` |
| `safe_to_defer` | boolean | Whether deferral is safe |
| `recommended_future_phase` | string | When to address |

---

## Future Implementation Item Fields

| Field | Type | Description |
|-------|------|-------------|
| `implementation_area` | string | What will be implemented (e.g., `schema_parser`, `guard_validator`) |
| `implementation_not_started` | boolean (always true in this phase) | Confirms no implementation has begun |
| `implementation_prerequisites` | list[string] | What must exist before implementation starts |
| `required_tests` | boolean (always true) | Whether tests are required |
| `required_dry_run_first` | boolean | Whether a dry-run phase must precede implementation |
| `forbidden_until_authorized` | boolean (always true) | Implementation forbidden until explicitly authorized |

---

## Review Cadence Policy

| Trigger | Action |
|---------|--------|
| `review_at_phase_boundary` | Review all open/pending items when starting a new phase |
| `review_before_implementation` | Review the specific item before any implementation begins |
| `review_before_lifecycle_closure` | Review all items before closing a lifecycle |
| `review_before_reopening_rejected_item` | Review rejection reason and current context before reopening |
| `review_when_blocking_condition_changes` | Review blocked items when their blocking condition may have changed |

---

## Escalation Policy

| Condition | Escalation |
|-----------|-----------|
| `high_risk_items_require_human_review` | Items with `risk_level=high` must be reviewed by human before any status change |
| `blocked_items_require_human_review` | Blocked items cannot be unblocked without human review |
| `forbidden_file_items_require_explicit_scope` | Items targeting forbidden files (src, tests, README, docs/REAL_CAPTURED_TASKS.md) require explicit scope authorization in their future phase |
| `backend_invocation_items_require_guard_review` | Items involving backend invocation require guard review (84H) |
| `storage_items_require_secret_handling_review` | Items involving storage require secret-handling review (84I) |

---

## Closure Policy

| Closure Type | Requirements |
|-------------|-------------|
| `implemented_with_artifact` | Item implemented in a separate phase; artifact reference required |
| `closed_no_action_with_reason` | Item closed without action; documented reason required |
| `superseded_by_new_item` | Item replaced by a newer item; reference to new item required |
| `rejected_with_reason` | Item rejected; rejection reason required |
| `carried_forward_to_named_phase` | Item carried forward; destination phase required |

Every closure must be auditable: who closed it, when, and why.

---

## Relationship to Adoption Candidates

- An adoption candidate (from 84E schema) may become a deferred item if not adopted in the current lifecycle.
- A deferred item may later become an adoption candidate in a future lifecycle.
- A deferred item is not adoption approval — tracking an item does not approve its adoption.
- A deferred item is not adoption execution — tracking an item does not execute any changes.
- A deferred item originating from backend output needs the full adoption pipeline (intake→review→approve→execute) if it is ever implemented.

---

## Relationship to Lifecycle State Machine

- Deferred items survive the `closed` state — they persist across lifecycle boundaries.
- Blocked items may force the lifecycle into `blocked` or `quarantined` state if they represent active safety concerns.
- An implemented deferred item requires either a new lifecycle trace (for backend-originated items) or an explicit phase closure (for documentation/hygiene items).
- Deferred item closure must be auditable from git-tracked metadata.

---

## Relationship to Storage Policy

- Deferred items may reference capture metadata (hashes, invocation IDs) from the storage policy (84I).
- Deferred items may reference output hashes as evidence.
- Deferred items must not embed raw backend output by default — they reference it by hash and capture ID.
- Deferred item storage may be git-tracked when it contains only metadata (IDs, reasons, status).
- Future machine-readable tracker storage (e.g., `.pcae/deferred/`) is not implemented in this phase.

---

## Example Tracker Entries

### DF-1: Stale 83A Future Phases Table

| Field | Value |
|-------|-------|
| item_id | DF-1 |
| item_type | adoption_deferred |
| item_status | accepted_for_future_phase |
| item_title | Update stale future phases table in 83A |
| source_artifact | `docs/MULTI_AGENT_ADOPTION_REVIEW.md` |
| source_phase | 83I |
| source_finding_id | RISK-2 |
| deferred_reason | Updating 83A future phases table after 83-series stabilizes avoids repeated edits |
| risk_level | medium |
| target_phase | Documentation consolidation phase |
| target_artifact_or_area | `docs/MULTI_AGENT_TASK_CONTRACT.md` |
| required_approval | true |
| required_authorization_flags | `["docs_mutation_authorized"]` |
| forbidden_actions | `["source_changes", "test_changes", "backend_invocation"]` |
| created_at | Phase 83I |
| last_reviewed_at | Phase 84A |

### DF-2: Dual Capability Models Relationship

| Field | Value |
|-------|-------|
| item_id | DF-2 |
| item_type | documentation_hygiene_deferred |
| item_status | accepted_for_future_phase |
| item_title | Document relationship between agent (82A) and subagent (82C) capability models |
| source_artifact | `docs/MULTI_AGENT_ADOPTION_REVIEW.md` |
| source_phase | 83I |
| source_finding_id | RISK-6 |
| deferred_reason | Documentation consolidation better done after both models are stable |
| risk_level | medium |
| target_phase | Documentation consolidation phase |
| target_artifact_or_area | `docs/AGENT_CAPABILITY_REGISTRY_DESIGN.md` or `docs/SUBAGENT_DISCOVERY_CONTRACT.md` |
| required_approval | true |
| created_at | Phase 83I |
| last_reviewed_at | Phase 84A |

### DF-3: Blocked Taxonomy Back-Reference

| Field | Value |
|-------|-------|
| item_id | DF-3 |
| item_type | documentation_hygiene_deferred |
| item_status | accepted_for_future_phase |
| item_title | Add back-reference from 82A to 82D blocked risk taxonomy |
| source_artifact | `docs/MULTI_AGENT_ADOPTION_REVIEW.md` |
| source_phase | 83I |
| source_finding_id | RISK-5 |
| deferred_reason | Documentation consolidation phase is more appropriate |
| risk_level | low |
| target_phase | Documentation consolidation phase |
| target_artifact_or_area | `docs/AGENT_CAPABILITY_REGISTRY_DESIGN.md` |
| required_approval | true |
| created_at | Phase 83I |
| last_reviewed_at | Phase 84A |

### DF-4: Authorization Flag Standardization

| Field | Value |
|-------|-------|
| item_id | DF-4 |
| item_type | documentation_hygiene_deferred |
| item_status | accepted_for_future_phase |
| item_title | Standardize authorization flag naming across 83B, 83C, 83D |
| source_artifact | `docs/MULTI_AGENT_ADOPTION_REVIEW.md` |
| source_phase | 83I |
| source_finding_id | G-1 / S-7 |
| deferred_reason | Flag naming is informational, not a governance blocker |
| risk_level | low |
| target_phase | Documentation consolidation phase |
| target_artifact_or_area | Multiple docs (83B, 83C, 83D) |
| required_approval | true |
| created_at | Phase 83I |
| last_reviewed_at | Phase 84A |

### HY-1: Task Filename Hygiene

| Field | Value |
|-------|-------|
| item_id | HY-1 |
| item_type | task_hygiene_deferred |
| item_status | open |
| item_title | Task files may have truncated slugs in filenames |
| source_artifact | Phase 84H/84I operator reports |
| source_phase | 84I |
| source_finding_id | N/A (observation) |
| deferred_reason | Task filename hygiene is not authorized in documentation-only phases |
| risk_level | low |
| target_phase | Dedicated task hygiene phase |
| target_artifact_or_area | `tasks/active/`, `tasks/completed/` |
| hygiene_area | task_files |
| observed_issue | Some task filenames may have truncated slugs |
| evidence | Operator-reported `tasks/active/84i-.md` and `tasks/completed/84h-.md` |
| severity | low |
| safe_to_defer | true |
| recommended_future_phase | Dedicated task file hygiene phase |
| required_approval | true |
| required_authorization_flags | `["task_filename_hygiene_authorized"]` |
| forbidden_actions | `["source_changes", "test_changes", "backend_invocation"]` |
| created_at | Phase 84J |

### IMPL-1: Schema Implementation

| Field | Value |
|-------|-------|
| item_id | IMPL-1 |
| item_type | schema_implementation_deferred |
| item_status | accepted_for_future_phase |
| item_title | Implement prompt package, capture metadata, output intake, and adoption candidate schema parsers |
| source_artifact | `docs/MULTI_AGENT_PROMPT_PACKAGE_SCHEMA.md`, `docs/MULTI_AGENT_CAPTURE_METADATA_SCHEMA.md`, `docs/MULTI_AGENT_OUTPUT_INTAKE_SCHEMA.md`, `docs/MULTI_AGENT_ADOPTION_CANDIDATE_SCHEMA.md` |
| source_phase | 84B, 84C, 84D, 84E |
| deferred_reason | Design documentation must be complete and reviewed before implementation |
| risk_level | medium |
| target_phase | Schema implementation phase (post-84K) |
| implementation_area | Schema parsing and validation for 4 schemas |
| implementation_not_started | true |
| implementation_prerequisites | All 4 schema designs reviewed and stable |
| required_tests | true |
| required_dry_run_first | true |
| forbidden_until_authorized | true |
| required_approval | true |
| required_authorization_flags | `["schema_implementation_authorized", "source_mutation_authorized", "test_mutation_authorized"]` |
| created_at | Phase 84J |

### IMPL-2: Lifecycle Command Dry-Run Implementation

| Field | Value |
|-------|-------|
| item_id | IMPL-2 |
| item_type | command_implementation_deferred |
| item_status | accepted_for_future_phase |
| item_title | Implement multi-agent lifecycle dry-run commands |
| source_artifact | `docs/MULTI_AGENT_LIFECYCLE_COMMAND_DRY_RUN.md` |
| source_phase | 84G |
| deferred_reason | Command design must be reviewed and guard/storage designs complete before implementation |
| risk_level | medium |
| target_phase | Command implementation phase (post-84K) |
| implementation_area | 8 dry-run commands under pcae multi-agent lifecycle |
| implementation_not_started | true |
| implementation_prerequisites | Command design (84G), state machine (84F), guard (84H), storage (84I) designs stable |
| required_tests | true |
| required_dry_run_first | false (commands are themselves dry-run) |
| forbidden_until_authorized | true |
| required_approval | true |
| required_authorization_flags | `["command_implementation_authorized", "source_mutation_authorized", "test_mutation_authorized"]` |
| created_at | Phase 84J |

### TEST-1: Future Test Coverage

| Field | Value |
|-------|-------|
| item_id | TEST-1 |
| item_type | test_coverage_deferred |
| item_status | accepted_for_future_phase |
| item_title | Add tests for schema parsing, guard decisions, and lifecycle commands |
| source_artifact | 84B–84I design documents |
| source_phase | 84J |
| deferred_reason | Tests require implementation code to test; no implementation exists yet |
| risk_level | medium |
| target_phase | Implementation phases (post-84K) |
| implementation_area | Test suites for schemas, guards, commands, storage |
| implementation_not_started | true |
| implementation_prerequisites | Corresponding implementation code exists |
| required_tests | true (this item IS the test coverage) |
| forbidden_until_authorized | true |
| required_approval | true |
| required_authorization_flags | `["test_mutation_authorized"]` |
| created_at | Phase 84J |

---

## Future Test Coverage

No tests are added in Phase 84J because it is documentation-only and test mutation is not authorized. When tracker implementation begins in a future phase, tests should cover:

1. **Deferred item schema parsing** — validate that tracker entries conform to required fields.
2. **Required field validation** — reject items missing `item_id`, `item_type`, `item_status`, `deferred_reason`, `risk_level`, or `target_phase`.
3. **Status transition validation** — enforce that only allowed status transitions occur (e.g., `rejected` cannot move to `implemented` without going through `open` and approval).
4. **Blocked/rejected reopen rules** — verify that reopening blocked or rejected items requires human approval.
5. **Candidate-to-deferred conversion** — verify that adoption candidates can be tracked as deferred items with proper reference preservation.
6. **Closure rules** — verify that closure requires a reason and (for `implemented`) an artifact reference.
7. **Tracker summary output** — verify that summary commands report correct counts of open, blocked, rejected, and implemented items.
8. **Task filename hygiene detection** — verify that hygiene items can detect and report filename anomalies.

---

## Validation Rules

| # | Rule ID | Description |
|---|---------|-------------|
| 1 | `TRACK_UNIQUE_ID` | Every item must have a unique item_id |
| 2 | `TRACK_HAS_TYPE` | Every item must have an item_type from the categories list |
| 3 | `TRACK_HAS_STATUS` | Every item must have a valid item_status |
| 4 | `TRACK_HAS_SOURCE` | Every item must have a source_artifact or explicit origin reference |
| 5 | `TRACK_HAS_REASON` | Every item must have a deferred_reason, blocked_reason, or rejection_reason |
| 6 | `TRACK_HAS_RISK` | Every item must have a risk_level |
| 7 | `TRACK_HAS_DISPOSITION` | Every item must have a target_phase or closure_status |
| 8 | `TRACK_BLOCKED_HUMAN_REVIEW` | Blocked items require human review before any status change |
| 9 | `TRACK_REJECTED_NO_REOPEN` | Rejected items cannot be reopened without explicit human approval |
| 10 | `TRACK_IMPLEMENTED_HAS_ARTIFACT` | Implemented items must reference the implementing phase and artifact |
| 11 | `TRACK_CLOSURE_HAS_REASON` | Closure requires a documented reason |
| 12 | `TRACK_NO_EXECUTION_AUTH` | Tracking does not authorize execution |
| 13 | `TRACK_NO_ADOPTION_AUTH` | Tracking does not authorize adoption |
| 14 | `TRACK_NO_COMMIT_AUTH` | Tracking does not authorize commits of deferred work |
| 15 | `TRACK_NO_PUSH_AUTH` | Tracking does not authorize pushes |
| 16 | `TRACK_FORBIDDEN_FILE_SCOPE` | Items targeting forbidden files require explicit scope authorization in their future phase |
| 17 | `TRACK_BACKEND_GUARD_REVIEW` | Items involving backend invocation require guard review (84H design) |
| 18 | `TRACK_STORAGE_SECRET_REVIEW` | Items involving storage require secret-handling review (84I design) |
| 19 | `TRACK_NO_RAW_OUTPUT_EMBED` | Tracker entries must not embed raw backend output |
| 20 | `TRACK_NO_MACHINE_STORAGE` | Machine-readable tracker storage is not implemented in this phase |
| 21 | `TRACK_HYGIENE_SEPARATE` | Task filename hygiene is tracked but not fixed in this phase |
| 22 | `TRACK_NO_TESTS_ADDED` | No tests are added in this documentation-only phase |
| 23 | `TRACK_COUNTS_MATCH` | Summary counts must match the listed items |
| 24 | `TRACK_STALE_REVIEW` | Items not reviewed within 2 lifecycle boundaries require review |
| 25 | `TRACK_CLOSURE_AUDITABLE` | Every closure must be auditable (who, when, why) |
| 26 | `TRACK_NO_PHASE_BEYOND` | No phase beyond 84J is started in this phase |
| 27 | `TRACK_STATUS_TRANSITIONS_VALID` | Only allowed status transitions may occur |
| 28 | `TRACK_CARRY_FORWARD_NAMED` | Carry-forward items must name a destination phase |
| 29 | `TRACK_SUPERSEDED_REFERENCES_NEW` | Superseded items must reference their replacement |
| 30 | `TRACK_IMPLEMENTATION_REQUIRES_PHASE` | Implementation items require a separate governed phase |
| 31 | `TRACK_IMPLEMENTATION_REQUIRES_TESTS` | Implementation items must include tests when code is added |
| 32 | `TRACK_BLOCKED_AGENT_TRACKED` | Blocked agents (claude-kimi, codex) are tracked as blocked_agent_deferred items |
| 33 | `TRACK_SUBAGENT_DISCOVERY_TRACKED` | Subagent discovery work is tracked as subagent_discovery_deferred |
| 34 | `TRACK_REVIEW_AT_BOUNDARY` | All open items must be reviewed at phase boundaries |
| 35 | `TRACK_HIGH_RISK_ESCALATION` | High-risk items require escalation per escalation policy |

**35 validation rules.**

---

## Failure Cases

| # | Failure | Detection | Handling |
|---|---------|-----------|----------|
| 1 | Deferred item missing reason | Required field validation | Block item creation; require reason |
| 2 | Deferred item missing source | Required field validation | Block item creation; require source artifact |
| 3 | Deferred item missing target phase | Required field validation | Block item creation; require disposition |
| 4 | Blocked item reopened without approval | Status transition validation | Block transition; require human approval |
| 5 | Rejected item reintroduced | Duplicate detection against rejected items | Block; require explicit reopen with approval |
| 6 | Deferred item implemented without approval | Implementation audit | Block commit; require phase authorization |
| 7 | Deferred item touches forbidden file | Forbidden file check | Block; require explicit scope in future phase |
| 8 | Deferred item hides raw backend output | Content check | Block; raw output must be referenced by hash only |
| 9 | Tracker counts mismatch | Summary validation | Flag inconsistency; reconcile |
| 10 | Closure without artifact or reason | Closure validation | Block closure; require documentation |
| 11 | Task hygiene issue silently ignored | Review cadence | Flag at phase boundary; escalate if persistent |
| 12 | Future implementation task started in documentation-only phase | Phase authorization check | Block; require implementation-authorized phase |
| 13 | Tests added in documentation-only phase | File change check | Block; tests require test_mutation_authorized |
| 14 | Stale item not reviewed | Stale detection via last_reviewed_at | Flag for review at next phase boundary |
| 15 | Carry-forward item loses origin reference | Required field validation | Block; require origin_lifecycle_id and origin_phase |

**15 failure cases.**

---

## Tracker Summary

| Category | Count | Items |
|----------|-------|-------|
| Adoption deferred | 4 | DF-1, DF-2, DF-3, DF-4 |
| Task hygiene deferred | 1 | HY-1 |
| Schema implementation deferred | 1 | IMPL-1 (covers 4 schemas) |
| Command implementation deferred | 1 | IMPL-2 |
| Test coverage deferred | 1 | TEST-1 |
| **Total tracked** | **8** | |

Additional items not individually tracked but noted as future work:

- State machine implementation (84F design)
- Guard implementation (84H design)
- Storage implementation (84I design)
- Tracker implementation (this design, 84J)
- Blocked agents: claude-kimi (missing), codex (unverified)
- Subagent discovery probes (82C contract defined, probes not executed)

---

## Tracker Policy Status

| Field | Value |
|-------|-------|
| tracker_policy_name | multi_agent_deferred_item_tracker |
| tracker_policy_version | 0.1 |
| tracker_policy_status | draft_documented |
| tracker_implementation_status | not_started |

## Recommended Next Phase

**84K — Multi-Agent Lessons README Summary**

84K should add a short README or project-facing summary of what the multi-agent governance design suite now contains, if README edits are explicitly authorized in that phase. This completes the 84-series roadmap from 84A.
