# Artifact Index Design

## 1. Purpose

Define a searchable, classifiable index of PCAE governance artifacts so that persistent
lifecycle memory (85A) can cite durable evidence rather than relying on ephemeral chat memory.
The artifact index is the evidence layer underneath the memory model.

## 2. Scope

Design only. This artifact defines artifact categories, metadata fields, indexing rules,
freshness policies, source-of-truth precedence, query targets, and validation rules. It does
not implement index storage, create machine-readable files, or add tests.

## 3. Non-Goals

- Implementing index storage or CLI commands.
- Creating `.pcae` index directories or files.
- Adding tests.
- Modifying source code, README, or existing artifacts.
- Backend invocation, prompt sending, capture, intake, or adoption.

## 4. Motivation from 85A

The persistent lifecycle memory model (85A) requires every memory claim to reference an
artifact, command result, or commit. The 5-level provenance priority established in 85A
(repo state > PCAE commands > committed artifacts > human reports > conversation memory)
demands a structured way to locate, classify, and validate artifacts. Without an artifact
index, memory provenance degrades to ad-hoc path references that may become stale or
ambiguous.

The 85A memory model defines an `artifact_record` entity with fields for path, type, status,
version, and evidence level. This 85B design formalizes the rules governing those fields.

---

## 5. Artifact Index Design Principles

1. Artifact index records evidence, not authorization.
2. Artifact index does not authorize execution.
3. Artifact index does not authorize adoption.
4. Artifact index does not authorize commit or push.
5. Artifact index must distinguish current, superseded, deferred, rejected, and unknown artifacts.
6. Artifact index must preserve repository-relative paths.
7. Artifact index must support offline audit.
8. Artifact index must support memory provenance (85A linkage).
9. Artifact index must identify missing or stale artifacts.
10. Artifact index must not embed raw backend output by default.
11. Artifact index must not infer safety from artifact existence alone.
12. Artifact index is secondary to repo state — if index and filesystem disagree, filesystem wins.

## 6. Artifact Index Threat Model

| # | Threat | Impact |
|---|--------|--------|
| AT-1 | Artifact missing but memory claim retained | Memory cites non-existent evidence |
| AT-2 | Artifact moved without index update | Index points to stale path |
| AT-3 | Artifact stale but treated as current | Decisions based on outdated evidence |
| AT-4 | Artifact exists but is not authoritative | Wrong artifact treated as source of truth |
| AT-5 | Chat memory contradicts artifact | Ephemeral claim overrides committed evidence |
| AT-6 | Human report contradicts repo artifact | Conflicting evidence sources |
| AT-7 | Artifact references raw backend output unsafely | Unadopted output treated as evidence |
| AT-8 | Artifact references forbidden file incorrectly | Safety boundary violation |
| AT-9 | Artifact category misclassified | Wrong queries return wrong artifacts |
| AT-10 | Commit evidence missing | Phase completion unverifiable |
| AT-11 | Push evidence missing | Push status unverifiable |
| AT-12 | Approval artifact missing | Approval claim unverifiable |
| AT-13 | Deferred item artifact missing | Deferred status unverifiable |
| AT-14 | Risk source artifact missing | Risk claim unverifiable |
| AT-15 | Baseline artifact stale | Health assessment outdated |

---

## 7. Artifact Categories

| Category | Purpose | Example |
|----------|---------|---------|
| `roadmap_artifact` | Roadmap plans and reconciliations | `docs/ROADMAP_RECONCILIATION_PHASE_85_PLAN.md` |
| `memory_model_artifact` | Memory model designs | `docs/PERSISTENT_LIFECYCLE_MEMORY_MODEL.md` |
| `schema_artifact` | Machine-readable schema designs | `docs/MULTI_AGENT_PROMPT_PACKAGE_SCHEMA.md` |
| `state_machine_artifact` | Lifecycle state machine designs | `docs/MULTI_AGENT_LIFECYCLE_STATE_MACHINE.md` |
| `command_design_artifact` | CLI command surface designs | `docs/MULTI_AGENT_LIFECYCLE_COMMAND_DRY_RUN.md` |
| `guard_design_artifact` | Backend invocation guard designs | `docs/MULTI_AGENT_BACKEND_INVOCATION_GUARD_HARDENING.md` |
| `storage_policy_artifact` | Storage policy designs | `docs/MULTI_AGENT_PROMPT_CAPTURE_STORAGE_POLICY.md` |
| `tracker_artifact` | Deferred item tracker designs | `docs/MULTI_AGENT_DEFERRED_ITEM_TRACKER.md` |
| `governance_summary_artifact` | Governance overview summaries | `docs/MULTI_AGENT_GOVERNANCE_SUMMARY.md` |
| `health_baseline_artifact` | Health and hygiene baselines | `docs/FULL_HEALTH_BASELINE_84K3.md` |
| `handoff_refresh_artifact` | Handoff state refresh records | `docs/HANDOFF_STATE_REFRESH_84K2.md` |
| `lifecycle_trace_artifact` | Lifecycle verification and traces | `docs/MULTI_AGENT_LIFECYCLE_FINAL_VERIFICATION.md` |
| `approval_artifact` | Human or system approval records | `docs/MULTI_AGENT_ADOPTION_APPROVAL.md` |
| `capture_artifact` | Backend capture records | `docs/MULTI_AGENT_PROMPT_SEND_CAPTURE.md` |
| `intake_artifact` | Output intake records | `docs/MULTI_AGENT_OUTPUT_INTAKE.md` |
| `adoption_artifact` | Adoption review/execution records | `docs/MULTI_AGENT_ADOPTION_EXECUTION.md` |
| `deferred_item_artifact` | Deferred item tracking evidence | `docs/MULTI_AGENT_DEFERRED_ITEM_TRACKER.md` |
| `risk_artifact` | Risk documentation | Guard/storage/tracker docs |
| `status_artifact` | Project status records | `PROJECT_STATUS.md` |
| `changelog_artifact` | Change history | `CHANGELOG.md` |
| `readme_artifact` | Project overview | `README.md` |
| `task_contract_artifact` | Task contracts (active or completed) | `tasks/active/*.md`, `tasks/completed/*.md` |
| `commit_evidence` | Git commit references | Commit hashes from phase completions |
| `push_evidence` | Git push references | Push records from governed pushes |

## 8. Required Artifact Metadata Fields

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `artifact_id` | string | yes | Stable unique identifier |
| `artifact_type` | string | yes | Category from section 7 |
| `artifact_path` | string | yes | Repository-relative path |
| `artifact_title` | string | yes | Human-readable title |
| `artifact_status` | string | yes | current/draft_documented/verified/closed/superseded/deferred/rejected/stale/missing/unknown |
| `artifact_version` | string | no | Version if applicable |
| `source_phase` | string | yes | Phase that created this artifact |
| `created_phase` | string | yes | Phase when first created |
| `last_updated_phase` | string | no | Phase when last modified |
| `implementation_status` | string | no | not_started/in_progress/complete |
| `authoritative_for` | list | yes (current) | What this artifact is authoritative evidence for |
| `supersedes` | string | no | Artifact ID this supersedes |
| `superseded_by` | string | no | Artifact ID that supersedes this |
| `related_artifacts` | list | no | Related artifact IDs |
| `evidence_level` | string | yes | Level from evidence hierarchy |
| `freshness_status` | string | yes | fresh/acceptable_stale/stale_requires_review/superseded/unknown |
| `hash_or_commit_ref` | string | yes | Commit hash or SHA256 when created/last verified |
| `required_for_memory_queries` | list | no | Memory queries (85A) that depend on this artifact |
| `safety_notes` | string | no | Safety-relevant notes |

## 9. Artifact Identity Rules

1. `artifact_id` must be stable across index updates (no regeneration).
2. `artifact_path` must be repository-relative (no absolute paths).
3. `artifact_type` must be one of the known categories or explicitly `unknown`.
4. `artifact_version` must be recorded if the artifact defines one.
5. `artifact_status` must not be inferred from filename alone.
6. Artifact authority (`authoritative_for`) must be explicit, not inferred from presence.
7. Two artifacts may not claim authority for the same scope without a supersession chain.

## 10. Artifact Location Rules

| Location | Content |
|----------|---------|
| `docs/` | Design artifacts, schemas, policies, summaries, baselines, traces |
| `tasks/active/` | Active task contracts |
| `tasks/completed/` | Completed task contracts |
| `PROJECT_STATUS.md` | Current project status (root) |
| `CHANGELOG.md` | Change history (root) |
| `README.md` | Project overview (root) |
| `.pcae/` | PCAE internal state (not indexed as governance artifacts) |

Future machine-readable index storage is not created in 85B. Location rules describe
where artifacts live today, not where index files will be stored.

## 11. Artifact Freshness Rules

| Status | Meaning | Trigger |
|--------|---------|---------|
| `fresh` | Artifact is current and recently verified | Created or verified in latest or recent phase |
| `acceptable_stale` | Artifact is older but still valid | Not modified recently but content is still accurate |
| `stale_requires_review` | Artifact may be outdated | Content references superseded state or old phase |
| `superseded` | Replaced by a newer artifact | Newer version or replacement exists |
| `unknown` | Freshness not assessed | Artifact exists but freshness not determined |

Freshness assessment rules:
1. An artifact modified in the current or immediately preceding phase is `fresh`.
2. An artifact not modified in 5+ phases should be assessed for staleness.
3. An artifact whose content references a phase more than 10 phases old should be reviewed.
4. Superseded artifacts retain `superseded` status permanently.
5. Freshness does not imply authority — a fresh artifact is not automatically authoritative.

## 12. Artifact Source-of-Truth Precedence

| Priority | Source | Trust Level |
|----------|--------|-------------|
| 1 | Committed repository artifacts (docs/, tasks/) | Highest — versioned, diffable |
| 2 | PCAE command outputs (health, check, doctor, lifecycle) | High — verified runtime state |
| 3 | Git commit/push evidence (hashes, push records) | High — immutable after push |
| 4 | Human final phase reports (operator-provided summaries) | Medium — reconcile with repo |
| 5 | Conversation memory (chat context) | Lowest — ephemeral, may be stale |
| 6 | Derived summaries (aggregated from other sources) | Lowest — dependent on inputs |

When sources conflict, higher-priority sources win. A committed artifact overrides a chat
memory claim. A PCAE command result overrides a human report about command status.

## 13. Provenance and Evidence Relationships

Every memory claim (85A) should resolve to an artifact index entry. The chain is:

```
memory_claim → artifact_record → artifact_index_entry → filesystem_artifact → commit_evidence
```

Provenance requirements:
1. Memory claims must reference an `artifact_id` from the index.
2. The `artifact_id` must resolve to a valid `artifact_path`.
3. The `artifact_path` must exist on the filesystem (or be explicitly `missing`).
4. The `hash_or_commit_ref` must be verifiable via git.
5. Broken provenance chains invalidate the memory claim.

## 14. Lifecycle Artifact Indexing

Key lifecycle artifacts that must be indexable:

| Artifact | Category | Authoritative For |
|----------|----------|-------------------|
| `docs/MULTI_AGENT_LIFECYCLE_FINAL_VERIFICATION.md` | lifecycle_trace_artifact | 83-series lifecycle closure |
| `docs/FULL_HEALTH_BASELINE_84K1.md` | health_baseline_artifact | Pre-refresh health state |
| `docs/HANDOFF_STATE_REFRESH_84K2.md` | handoff_refresh_artifact | Handoff refresh state |
| `docs/FULL_HEALTH_BASELINE_84K3.md` | health_baseline_artifact | Post-refresh health state |
| `docs/MULTI_AGENT_LIFECYCLE_LESSONS_ROADMAP.md` | roadmap_artifact | 83-series lessons and 84-series roadmap |

## 15. Schema/Design Artifact Indexing

| Artifact | Category | Version |
|----------|----------|---------|
| `docs/MULTI_AGENT_PROMPT_PACKAGE_SCHEMA.md` | schema_artifact | 0.1 |
| `docs/MULTI_AGENT_CAPTURE_METADATA_SCHEMA.md` | schema_artifact | 0.1 |
| `docs/MULTI_AGENT_OUTPUT_INTAKE_SCHEMA.md` | schema_artifact | 0.1 |
| `docs/MULTI_AGENT_ADOPTION_CANDIDATE_SCHEMA.md` | schema_artifact | 0.1 |
| `docs/MULTI_AGENT_LIFECYCLE_STATE_MACHINE.md` | state_machine_artifact | 0.1 |
| `docs/MULTI_AGENT_LIFECYCLE_COMMAND_DRY_RUN.md` | command_design_artifact | 0.1 |
| `docs/MULTI_AGENT_BACKEND_INVOCATION_GUARD_HARDENING.md` | guard_design_artifact | 0.1 |
| `docs/MULTI_AGENT_PROMPT_CAPTURE_STORAGE_POLICY.md` | storage_policy_artifact | 0.1 |
| `docs/MULTI_AGENT_DEFERRED_ITEM_TRACKER.md` | tracker_artifact | 0.1 |
| `docs/PERSISTENT_LIFECYCLE_MEMORY_MODEL.md` | memory_model_artifact | 0.1 |

All have `implementation_status=not_started`.

## 16. Status and Baseline Artifact Indexing

| Artifact | Category | Freshness |
|----------|----------|-----------|
| `README.md` | readme_artifact | Updated in 84K |
| `PROJECT_STATUS.md` | status_artifact | Updated each phase |
| `CHANGELOG.md` | changelog_artifact | Updated each phase |
| `docs/MULTI_AGENT_GOVERNANCE_SUMMARY.md` | governance_summary_artifact | Created 84K |
| `docs/ROADMAP_RECONCILIATION_PHASE_85_PLAN.md` | roadmap_artifact | Created 84L |

## 17. Decision/Approval Artifact Indexing

Key decision and approval artifacts from the 83-series lifecycle:

| Artifact | Category | Decision Type |
|----------|----------|---------------|
| `docs/MULTI_AGENT_ROUTING_APPROVAL.md` | approval_artifact | Routing approval |
| `docs/MULTI_AGENT_PROMPT_INVOCATION_APPROVAL.md` | approval_artifact | Invocation approval |
| `docs/MULTI_AGENT_ADOPTION_APPROVAL.md` | approval_artifact | Adoption approval |
| `docs/MULTI_AGENT_ADOPTION_REVIEW.md` | adoption_artifact | Adoption review (AC/DF/RJ) |
| `docs/MULTI_AGENT_ADOPTION_EXECUTION.md` | adoption_artifact | Adoption execution |

## 18. Deferred/Risk Artifact Indexing

| Source | Items | Category |
|--------|-------|----------|
| `docs/MULTI_AGENT_DEFERRED_ITEM_TRACKER.md` | DF-1–DF-4, HY-1, IMPL-1–2, TEST-1 | deferred_item_artifact |
| `docs/MULTI_AGENT_BACKEND_INVOCATION_GUARD_HARDENING.md` | 15-threat invocation model | risk_artifact |
| `docs/MULTI_AGENT_PROMPT_CAPTURE_STORAGE_POLICY.md` | 15-threat storage model | risk_artifact |
| `docs/PERSISTENT_LIFECYCLE_MEMORY_MODEL.md` | 15-threat memory model | risk_artifact |
| `docs/ARTIFACT_INDEX_DESIGN.md` | 15-threat index model (this doc) | risk_artifact |

## 19. Commit/Push Evidence Indexing

Commit and push evidence is indexed by phase:

| Evidence Type | Fields | Source |
|---------------|--------|--------|
| `commit_evidence` | phase_id, commit_hash, commit_message, commit_type (implementation/completion) | git log |
| `push_evidence` | phase_id, push_method (governed/raw/force), origin_count_before, origin_count_after | pcae push output |

Commit evidence is immutable after push. Push evidence must record the method used
(governed `pcae push` vs raw `git push` vs force push).

---

## 20. Query Model

### Q1: find_artifacts_for_phase

| Field | Value |
|-------|-------|
| Required inputs | `phase_id` |
| Artifact types consulted | All categories |
| Expected output | `[{artifact_id, artifact_path, artifact_type, artifact_status}]` |
| Freshness checks | Return freshness_status for each artifact |
| Provenance requirement | Each artifact must have hash_or_commit_ref |

### Q2: find_latest_completed_phase_artifact

| Field | Value |
|-------|-------|
| Required inputs | None (uses project_state) |
| Artifact types consulted | task_contract_artifact, status_artifact |
| Expected output | `{phase_id, artifact_path, completion_commit}` |
| Freshness checks | Must be fresh (completed in latest phase) |
| Provenance requirement | Completion commit must exist |

### Q3: find_current_roadmap_artifact

| Field | Value |
|-------|-------|
| Required inputs | None |
| Artifact types consulted | roadmap_artifact |
| Expected output | `{artifact_id, artifact_path, roadmap_position}` |
| Freshness checks | Must be current, not superseded |
| Provenance requirement | Must be committed |

### Q4: find_approval_artifacts

| Field | Value |
|-------|-------|
| Required inputs | Optional `approval_type` filter |
| Artifact types consulted | approval_artifact |
| Expected output | `[{artifact_id, approval_type, approval_status, artifact_path}]` |
| Freshness checks | Expired/superseded approvals marked accordingly |
| Provenance requirement | Each must have artifact_path and commit_ref |

### Q5: find_blocked_items

| Field | Value |
|-------|-------|
| Required inputs | None |
| Artifact types consulted | deferred_item_artifact, risk_artifact |
| Expected output | `[{item_id, blocking_condition, source_artifact, risk_level}]` |
| Freshness checks | Source artifact freshness assessed |
| Provenance requirement | Each blocker must cite source artifact |

### Q6: find_deferred_items

| Field | Value |
|-------|-------|
| Required inputs | Optional `status` filter |
| Artifact types consulted | deferred_item_artifact, tracker_artifact |
| Expected output | `[{item_id, item_type, item_status, target_phase, source_artifact}]` |
| Freshness checks | Tracker freshness assessed |
| Provenance requirement | Each item must cite source artifact and phase |

### Q7: find_risk_sources

| Field | Value |
|-------|-------|
| Required inputs | Optional `risk_type` filter |
| Artifact types consulted | risk_artifact, guard_design_artifact, storage_policy_artifact |
| Expected output | `[{risk_id, risk_type, risk_level, source_artifact}]` |
| Freshness checks | Risk artifact freshness assessed |
| Provenance requirement | Risk must cite source artifact |

### Q8: find_health_baselines

| Field | Value |
|-------|-------|
| Required inputs | Optional `phase_id` filter |
| Artifact types consulted | health_baseline_artifact |
| Expected output | `[{artifact_id, artifact_path, source_phase, freshness_status}]` |
| Freshness checks | Required — baselines age quickly |
| Provenance requirement | Must have commit_ref |

### Q9: find_artifacts_supporting_next_safe_action

| Field | Value |
|-------|-------|
| Required inputs | `proposed_action` |
| Artifact types consulted | All relevant categories |
| Expected output | `[{artifact_id, evidence_level, supports_or_blocks, reason}]` |
| Freshness checks | All supporting artifacts must be fresh or acceptable_stale |
| Provenance requirement | Each must be committed and verifiable |

### Q10: find_artifacts_for_forbidden_action

| Field | Value |
|-------|-------|
| Required inputs | `forbidden_action` |
| Artifact types consulted | decision artifacts, risk artifacts, guard artifacts |
| Expected output | `[{artifact_id, forbids_because, source_phase}]` |
| Freshness checks | Forbidding artifacts must be current (not superseded) |
| Provenance requirement | Each must cite the decision or risk that forbids the action |

---

## 21. Index Update Rules

1. Index updates only after phase completion.
2. Index update must cite artifact path and commit.
3. Index must not mark an artifact `current` without filesystem verification.
4. Index must not delete superseded history (mark `superseded`, retain entry).
5. Index must mark stale artifacts explicitly.
6. Index must distinguish `missing` from `unknown`.
7. Index must preserve deferred/rejected status.
8. Index must not infer authorization from artifact presence.
9. Index update must be idempotent.
10. Index update must be diffable against previous index state.
11. Index must not create entries for artifacts that do not exist on filesystem.
12. Index must update freshness when phases change but artifact content does not.

---

## 22. Validation Rules

| # | Rule |
|---|------|
| V-1 | `artifact_id` required for every index entry |
| V-2 | `artifact_path` required for every index entry |
| V-3 | `artifact_type` required and must be from known categories |
| V-4 | `artifact_status` required |
| V-5 | `source_phase` required |
| V-6 | `artifact_path` must be repository-relative |
| V-7 | `authoritative_for` required for artifacts with status `current` |
| V-8 | `freshness_status` required |
| V-9 | `evidence_level` required |
| V-10 | Missing artifact must be classified as `missing`, not `current` |
| V-11 | Stale artifact must be classified explicitly |
| V-12 | Superseded artifact must retain history (not deleted from index) |
| V-13 | Repo artifact outranks chat memory in source-of-truth |
| V-14 | PCAE command output outranks human report |
| V-15 | Human report cannot overwrite committed artifact silently |
| V-16 | Artifact presence does not authorize execution |
| V-17 | Artifact presence does not authorize adoption |
| V-18 | Artifact presence does not authorize commit/push |
| V-19 | Raw backend output not embedded in index by default |
| V-20 | Deferred/rejected status must be preserved |
| V-21 | Design-only phase creates no machine-readable index |
| V-22 | Future implementation requires tests |
| V-23 | No source/test changes in 85B |
| V-24 | No phase beyond 85B started in this phase |
| V-25 | No `.pcae` index storage created in 85B |
| V-26 | `artifact_id` must be stable across index updates |
| V-27 | Two artifacts may not claim authority for the same scope without supersession |
| V-28 | `hash_or_commit_ref` required for committed artifacts |
| V-29 | `artifact_version` must be recorded when artifact defines one |
| V-30 | `artifact_status` must not be inferred from filename alone |
| V-31 | Index entry for a `task_contract_artifact` must reflect active/completed path |
| V-32 | `related_artifacts` references must resolve to existing index entries |
| V-33 | `supersedes`/`superseded_by` must form a valid chain |
| V-34 | `required_for_memory_queries` must reference valid 85A query names |
| V-35 | Freshness assessment must consider phase distance, not just time |
| V-36 | Index must not contain entries for `.pcae/` internal files |
| V-37 | Index must not contain entries for `src/` or `tests/` files |
| V-38 | `created_phase` must be <= `last_updated_phase` when both present |

## 23. Failure Cases

| # | Failure | Impact |
|---|---------|--------|
| F-1 | Artifact missing from filesystem | Memory claim references non-existent evidence |
| F-2 | Artifact path invalid (absolute, wrong directory) | Index entry unresolvable |
| F-3 | Artifact misclassified | Wrong queries return wrong artifacts |
| F-4 | Artifact stale but treated as current | Decisions based on outdated evidence |
| F-5 | Artifact superseded but not linked to successor | History chain broken |
| F-6 | Artifact authority ambiguous (two claim same scope) | Conflicting evidence |
| F-7 | Memory claim lacks artifact support | Unverifiable claim in memory |
| F-8 | Human report conflicts with committed artifact | Source-of-truth violation |
| F-9 | Chat memory conflicts with repo artifact | Ephemeral source overrides persistent |
| F-10 | Approval artifact missing | Approval claim unverifiable |
| F-11 | Deferred item artifact missing | Deferred status unverifiable |
| F-12 | Risk source artifact missing | Risk claim unverifiable |
| F-13 | Index implementation attempted in design phase | Governance boundary violated |
| F-14 | Tests skipped in implementation phase | Implementation without verification |
| F-15 | Index entry created for non-existent artifact | Phantom evidence |

---

## 24. Future Implementation Plan

Candidate future phases after this design:

| Phase | Name | Scope |
|-------|------|-------|
| 85B.1 | Artifact Index Implementation Plan | Detailed implementation spec |
| 85B.2 | Read-Only Artifact Index Prototype | First read-only index command |
| 85B.3 | Artifact Index Tests | Test suite for artifact index |

No task contracts are created for these phases in 85B.

## 25. Future Test Coverage

No tests are added in 85B because this is design-only. Future implementation must test:

| Test Area | Coverage Target |
|-----------|----------------|
| Artifact metadata parsing | Required fields present and correctly typed |
| Artifact type classification | Category assignment matches artifact content |
| Artifact freshness classification | Freshness rules applied correctly |
| Source-of-truth precedence | Higher-priority sources override lower |
| Missing artifact detection | Missing artifacts classified as `missing` |
| Stale artifact detection | Stale artifacts flagged for review |
| Phase-to-artifact lookup | Correct artifacts returned for phase queries |
| Query output shape | All queries return expected structure |
| Provenance requirement validation | Broken provenance chains flagged |
| Index update idempotency | Same input produces same index state |

## 26. Example Artifact Index Entry

Illustrative markdown only, not an executable format:

```
artifact_id: roadmap-reconciliation-phase-85-plan
artifact_type: roadmap_artifact
artifact_path: docs/ROADMAP_RECONCILIATION_PHASE_85_PLAN.md
artifact_title: Roadmap Reconciliation and Phase 85 Plan
artifact_status: current
artifact_version: 0.1
source_phase: 84L
created_phase: 84L
last_updated_phase: 84L
implementation_status: not_started
authoritative_for:
  - phase_85_plan
  - roadmap_reconciliation
  - phase_85_sequence
supersedes: null
superseded_by: null
related_artifacts:
  - multi-agent-governance-summary
  - persistent-lifecycle-memory-model
evidence_level: repo_committed_artifact
freshness_status: fresh
hash_or_commit_ref: 2478ef81
required_for_memory_queries:
  - what_phase_are_we_in
  - what_can_be_safely_done_next
safety_notes: Planning document only; does not authorize implementation
```

---

## 27. Recommended Next Phase

**85C — Governance Event Timeline**

85C should define a chronological event model for approvals, captures, checks, commits,
pushes, blockers, deferrals, and closures. It builds on 85A (memory model entities) and
85B (artifact index for evidence) by adding temporal ordering and causal linkage.

---

## Artifact Index Identity

| Field | Value |
|-------|-------|
| artifact_index_name | pcae_artifact_index |
| artifact_index_version | 0.1 |
| artifact_index_status | draft_documented |
| artifact_index_implementation_status | not_started |

## Authorization Flags for 85B

| Flag | Value |
|------|-------|
| backend_invocation_performed | false |
| new_prompts_sent | false |
| new_capture_performed | false |
| new_intake_performed | false |
| new_adoption_review_performed | false |
| new_adoption_approval_performed | false |
| new_adoption_execution_performed | false |
| repo_mutation_authorized | true_for_artifact_index_docs_status_only |
| readme_mutation_authorized | false |
| source_mutation_authorized | false |
| test_mutation_authorized | false |
| docs_real_captured_tasks_mutation_authorized | false |
| persistent_memory_implementation_authorized | false |
| artifact_index_implementation_authorized | false |
| phase_85c_task_contract_authorized | false |
| commit_authorized | false |
| push_authorized | false |
| execution_authorized | false |
