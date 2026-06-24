# Phase 85 Data Model and Storage Design

## 1. Purpose

Define shared data model contracts and storage boundaries for implementing the Phase 85
persistent memory and project intelligence designs (85A–85F). This document specifies the
six core model shapes, their fields, cross-model relationships, JSON output conventions,
storage strategy, and validation rules that all future implementation phases must follow.

## 2. Scope

Data model and storage design only. This artifact defines model contracts and storage
policies. It does not implement models, create storage, modify source code, or add tests.

## 3. Non-Goals

- Implementing any data model in source code.
- Creating `.pcae` storage, generated cache, or machine-readable state files.
- Adding tests.
- Modifying source code, README, or existing design artifacts.
- Backend invocation, prompt sending, capture, intake, or adoption.

## 4. Motivation from 85A–85F and 86A

The Phase 85 design sequence produced six layer designs with a combined 156+ required fields.
The 86A implementation roadmap recommended starting with shared data models before any layer
is implemented. This document fulfills that recommendation by defining:

- Common field conventions shared across all models.
- Complete field specifications for each of the six models.
- Cross-model reference rules.
- JSON output shape conventions for future CLI commands.
- Storage strategy decisions (command-output-first, no cache, no .pcae storage).

---

## 5. Data Model Design Principles

1. Models describe observed governance state, not permission by themselves.
2. Models do not authorize execution.
3. Models do not authorize backend invocation.
4. Models do not authorize adoption.
5. Models do not authorize commit or push.
6. Models must preserve provenance (every claim links to evidence).
7. Models must be read-only first.
8. Models must distinguish `unknown` from `missing`.
9. Models must distinguish observed from authorized.
10. Models must preserve denied/deferred/rejected/accepted-risk state.
11. Models must support offline audit.
12. Models must support idempotent generation.
13. Models must be usable by future JSON CLI outputs.

## 6. Storage Design Principles

1. No storage created in 86B.
2. No `.pcae` storage created in 86B.
3. No generated cache created in 86B.
4. Start implementation with command output, not mutable stored state.
5. Repo artifacts remain source of truth.
6. Generated data must be derived from committed evidence.
7. Generated cache must never become authority by accident.
8. Committed machine-readable state requires separate approval.
9. Write-capable storage requires separate implementation gate.

## 7. Threat Model

| # | Threat | Impact |
|---|--------|--------|
| DM-1 | Model field missing but treated as valid | Incomplete governance record |
| DM-2 | `unknown` treated as `false` | Missing information treated as negative assertion |
| DM-3 | Missing artifact treated as `current` | Non-existent evidence cited |
| DM-4 | Generated cache treated as source of truth | Repo artifacts bypassed |
| DM-5 | Stale generated data used as current | Decisions based on outdated information |
| DM-6 | Memory snapshot implies authorization | Governance boundary crossed |
| DM-7 | Project state snapshot implies execution permission | Unauthorized action proceeds |
| DM-8 | Decision record loses rejection state | Rejected item re-enters pipeline |
| DM-9 | Risk record treats accepted risk as mitigation | Risk assumed resolved |
| DM-10 | Event ordering lost | Causal analysis incorrect |
| DM-11 | Provenance omitted | Claims unverifiable |
| DM-12 | Model contradicts committed artifact | Data integrity failure |
| DM-13 | Model version mismatch ignored | Incompatible data processed |
| DM-14 | Storage introduced without approval | Governance gate bypassed |
| DM-15 | Tests skipped when implementation starts | Implementation unverified |

---

## 8. Shared Model Overview

| Model | Source Design | Purpose |
|-------|-------------|---------|
| `ArtifactRecord` | 85B | Evidence lookup: where artifacts live, type, freshness, authority |
| `MemorySnapshot` | 85A | Entity state: phases, flags, approvals, lifecycle, next actions |
| `GovernanceEvent` | 85C | Temporal ordering: what happened when, causality |
| `DecisionRecord` | 85D | Durable decisions: approvals, denials, deferrals, rejections |
| `RiskRecord` | 85E | Risk state: active, accepted, mitigated, must-never-repeat |
| `ProjectStateSnapshot` | 85F | Integrated answer: all layers composed into project state |

## 9. Common Field Conventions

Fields shared across all or most models:

| Field | Type | Required | Convention |
|-------|------|----------|------------|
| `*_id` | string | yes | Stable unique identifier; kebab-case slug |
| `model_type` | string | yes | Discriminator: `artifact_record`, `memory_snapshot`, etc. |
| `model_version` | string | yes | Schema version (e.g., `0.1`) |
| `status` | string | yes | From model-specific status enum |
| `source_phase` | string | yes | Phase that produced or last verified this record |
| `source_artifact` | string | where available | Repository-relative path to source artifact |
| `source_commit` | string | where available | Git commit hash |
| `created_at` | string (ISO 8601) | yes | When record was first created |
| `updated_at` | string (ISO 8601) | yes | When record was last updated |
| `evidence_level` | string | yes | From common evidence level enum |
| `freshness_status` | string | yes | From common freshness enum |
| `provenance` | object or string | yes | Source reference chain |
| `safety_notes` | string | no | Safety-relevant notes |

### Common Status Concepts

| Status | Meaning |
|--------|---------|
| `current` | Active and verified |
| `draft_documented` | Designed but not implemented |
| `verified` | Verified by command or audit |
| `closed` | Lifecycle complete |
| `superseded` | Replaced by newer record |
| `deferred` | Deferred to future phase |
| `rejected` | Explicitly rejected |
| `blocked` | Blocked by condition |
| `stale` | Outdated |
| `missing` | Expected but not found |
| `unknown` | Status not determined |

### Common Evidence Levels

| Level | Meaning |
|-------|---------|
| `repo_committed_artifact` | Committed file in docs/ or tasks/ |
| `pcae_command_output` | Output from pcae health/check/doctor/lifecycle |
| `git_commit` | Git commit hash |
| `human_final_report` | Operator-provided summary |
| `conversation_memory` | Chat context (lowest trust) |
| `derived_summary` | Aggregated from other sources |
| `unknown` | Evidence level not assessed |

### Common Freshness Values

| Freshness | Meaning |
|-----------|---------|
| `fresh` | Recently created or verified |
| `acceptable_stale` | Older but still valid |
| `stale_requires_review` | May be outdated |
| `superseded` | Replaced |
| `unknown` | Not assessed |

---

## 10. ArtifactRecord Model

**Purpose:** Represent a governance artifact with its type, location, authority, and freshness.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `artifact_id` | string | yes | Stable identifier |
| `artifact_type` | string | yes | From 85B category enum (24 types) |
| `artifact_path` | string | yes | Repository-relative path |
| `artifact_title` | string | yes | Human-readable title |
| `artifact_status` | string | yes | From common status enum |
| `artifact_version` | string | no | Version if artifact defines one |
| `source_phase` | string | yes | Phase that created this artifact |
| `created_phase` | string | yes | Phase when first created |
| `last_updated_phase` | string | no | Phase when last modified |
| `implementation_status` | string | no | not_started/in_progress/complete |
| `authoritative_for` | list[string] | yes (current) | What this artifact is evidence for |
| `supersedes` | string | no | Artifact ID this supersedes |
| `superseded_by` | string | no | Artifact ID that supersedes this |
| `related_artifacts` | list[string] | no | Related artifact IDs |
| `evidence_level` | string | yes | From common evidence level |
| `freshness_status` | string | yes | From common freshness |
| `hash_or_commit_ref` | string | yes | Commit hash or SHA256 |
| `required_for_memory_queries` | list[string] | no | 85A query names |
| `safety_notes` | string | no | Safety notes |

## 11. MemorySnapshot Model

**Purpose:** Represent the current project memory state derived from all layers.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `memory_snapshot_id` | string | yes | Stable identifier |
| `memory_model_version` | string | yes | Schema version |
| `project_id` | string | yes | Project identifier |
| `repository_path` | string | yes | Repository filesystem path |
| `current_phase` | string | yes | Currently active phase |
| `latest_completed_phase` | string | yes | Most recently completed |
| `current_lifecycle_state` | string | yes | Lifecycle state machine position |
| `roadmap_position` | string | yes | Roadmap sequence position |
| `phase_sequence_position` | string | yes | Position within current series |
| `last_verified_commit` | string | yes | Latest verified commit hash |
| `origin_sync_status` | string | yes | synced/diverged/ahead/behind |
| `health_status` | string | yes | pcae health result |
| `governance_status` | string | yes | Summary governance state |
| `artifact_index_status` | string | yes | Index state |
| `timeline_status` | string | yes | Timeline state |
| `decision_log_status` | string | yes | Decision log state |
| `risk_status` | string | yes | Risk register state |
| `next_safe_actions` | list[string] | yes | Recommended safe actions |
| `forbidden_actions` | list[string] | yes | Explicitly forbidden actions |
| `provenance` | object | yes | Source references |
| `safety_notes` | string | no | Safety notes |

## 12. GovernanceEvent Model

**Purpose:** Represent a single governance event with type, ordering, and causality.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `event_id` | string | yes | Stable identifier |
| `event_type` | string | yes | From 85C event type enum (33 types) |
| `event_status` | string | yes | From 85C status enum (12 values) |
| `event_timestamp` | string | yes | ISO 8601 or ordering anchor |
| `source_phase` | string | yes | Phase that produced this event |
| `source_artifact` | string | where available | Artifact reference |
| `source_commit` | string | where available | Commit reference |
| `actor` | string | yes | Who produced the event |
| `agent_id` | string | no | Agent involved |
| `human_required` | boolean | yes | Whether human review required |
| `authorization_required` | boolean | yes | Whether authorization required |
| `authorization_status` | string | yes | authorized/unauthorized/not_applicable |
| `affected_files` | list[string] | no | Files affected |
| `related_artifacts` | list[string] | no | Artifact IDs |
| `related_events` | list[string] | no | Event IDs |
| `causal_parent_events` | list[string] | no | Causal predecessors |
| `evidence_level` | string | yes | From common evidence level |
| `freshness_status` | string | yes | From common freshness |
| `safety_notes` | string | no | Safety notes |

## 13. DecisionRecord Model

**Purpose:** Represent a durable governance decision with scope, provenance, and lifecycle.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `decision_id` | string | yes | Stable identifier |
| `decision_type` | string | yes | From 85D type enum (13 types) |
| `decision_status` | string | yes | From 85D status enum (11 values) |
| `decision_timestamp` | string | yes | ISO 8601 |
| `source_phase` | string | yes | Phase that produced this |
| `source_artifact` | string | where available | Artifact reference |
| `source_event` | string | where available | Timeline event ID |
| `source_commit` | string | where available | Commit reference |
| `decision_maker` | string | yes | Who made the decision |
| `human_required` | boolean | yes | Whether human authority required |
| `approved_scope` | string | for approvals | What was approved |
| `denied_scope` | string | for denials | What was denied |
| `deferred_scope` | string | for deferrals | What was deferred |
| `rejected_scope` | string | for rejections | What was rejected |
| `affected_files` | list[string] | no | Files affected |
| `affected_agents` | list[string] | no | Agents affected |
| `authorization_flags` | list[string] | no | Flags set or cleared |
| `risk_level` | string | for risk decisions | low/medium/high/critical |
| `supersedes` | string | no | Decision ID this supersedes |
| `superseded_by` | string | no | Decision ID that supersedes this |
| `related_decisions` | list[string] | no | Related decisions |
| `related_artifacts` | list[string] | no | Related artifacts |
| `related_events` | list[string] | no | Related events |
| `evidence_level` | string | yes | From common evidence level |
| `safety_notes` | string | no | Safety notes |

## 14. RiskRecord Model

**Purpose:** Represent a governance risk with severity, likelihood, exposure, and lifecycle.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `risk_id` | string | yes | Stable identifier |
| `risk_type` | string | yes | From 85E type enum (22 types) |
| `risk_status` | string | yes | From 85E status enum (9 values) |
| `risk_title` | string | yes | Short title |
| `risk_description` | string | yes | Description |
| `risk_severity` | string | yes | low/medium/high/critical/unknown |
| `risk_likelihood` | string | yes | unlikely/possible/likely/observed/unknown |
| `risk_exposure` | string | yes | low/medium/high/critical/unknown |
| `source_phase` | string | yes | Phase where identified |
| `source_artifact` | string | where available | Artifact reference |
| `source_event` | string | where available | Timeline event ID |
| `source_decision` | string | where available | Decision ID |
| `source_commit` | string | where available | Commit reference |
| `risk_owner` | string | no | Responsible party |
| `human_review_required` | boolean | yes | Whether human review needed |
| `affected_files` | list[string] | no | Files affected |
| `affected_agents` | list[string] | no | Agents affected |
| `affected_commands` | list[string] | no | Commands affected |
| `blocking_condition` | string | for blocked | What this blocks |
| `mitigation` | string | for mitigated | Mitigation evidence |
| `acceptance_rationale` | string | for accepted | Why accepted |
| `accepted_by` | string | for accepted | Who accepted |
| `supersedes` | string | no | Risk ID this supersedes |
| `superseded_by` | string | no | Risk ID that supersedes this |
| `related_risks` | list[string] | no | Related risks |
| `related_artifacts` | list[string] | no | Related artifacts |
| `related_events` | list[string] | no | Related events |
| `related_decisions` | list[string] | no | Related decisions |
| `evidence_level` | string | yes | From common evidence level |
| `last_reviewed_phase` | string | no | Last review phase |
| `next_review_phase` | string | no | Next review phase |
| `safety_notes` | string | no | Safety notes |

## 15. ProjectStateSnapshot Model

**Purpose:** Represent the integrated project state answer composed from all layers.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `snapshot_id` | string | yes | Stable identifier |
| `snapshot_version` | string | yes | Schema version |
| `snapshot_status` | string | yes | From 85F status enum |
| `snapshot_created_at` | string | yes | ISO 8601 |
| `source_phase` | string | yes | Phase that produced this |
| `latest_completed_phase` | string | yes | Most recently completed |
| `current_active_phase` | string | yes | Currently active or null |
| `current_lifecycle_state` | string | yes | Lifecycle state |
| `roadmap_position` | string | yes | Roadmap position |
| `recommended_next_phase` | string | yes | Recommended next |
| `repository_clean` | boolean | yes | Working tree clean |
| `branch` | string | yes | Current branch |
| `origin_sync_status` | string | yes | Sync status |
| `origin_main_head_count` | integer | yes | Commits ahead |
| `health_status` | string | yes | pcae health result |
| `check_status` | string | yes | pcae check result |
| `doctor_status` | string | yes | pcae doctor result |
| `push_check_status` | string | yes | pcae push check result |
| `execution_authorized` | boolean | yes | Must be explicit |
| `backend_invocation_authorized` | boolean | yes | Must be explicit |
| `prompt_sending_authorized` | boolean | yes | Must be explicit |
| `capture_authorized` | boolean | yes | Must be explicit |
| `intake_authorized` | boolean | yes | Must be explicit |
| `adoption_authorized` | boolean | yes | Must be explicit |
| `source_mutation_authorized` | boolean | yes | Must be explicit |
| `test_mutation_authorized` | boolean | yes | Must be explicit |
| `readme_mutation_authorized` | boolean | yes | Must be explicit |
| `docs_real_captured_tasks_mutation_authorized` | boolean | yes | Must be explicit |
| `active_blockers` | list | yes | May be empty |
| `active_deferred_items` | list | yes | May be empty |
| `active_rejected_items` | list | yes | May be empty |
| `active_risks` | list | yes | May be empty |
| `accepted_risks` | list | yes | May be empty |
| `must_never_repeat_controls` | list | yes | May be empty |
| `stale_signals` | list | yes | May be empty |
| `evidence_artifacts` | list | yes | Key artifact paths |
| `evidence_commits` | list | yes | Key commit hashes |
| `next_safe_actions` | list | yes | Recommended actions |
| `forbidden_actions` | list | yes | Forbidden actions |
| `human_review_required` | boolean | yes | Whether review needed |
| `confidence` | string | yes | high/medium/low |
| `safety_notes` | string | no | Safety notes |

---

## 16. Cross-Model Relationships

```
ProjectStateSnapshot
  ├── aggregates MemorySnapshot
  ├── references ArtifactRecord[] (evidence_artifacts)
  ├── references GovernanceEvent[] (via timeline layer)
  ├── references DecisionRecord[] (approvals, deferrals, rejections)
  └── references RiskRecord[] (active_risks, accepted_risks, controls)

MemorySnapshot
  ├── references ArtifactRecord[] (artifact_index_status)
  ├── derived from GovernanceEvent[] (timeline_status)
  ├── derived from DecisionRecord[] (decision_log_status)
  └── derived from RiskRecord[] (risk_status)

GovernanceEvent
  ├── references ArtifactRecord (source_artifact)
  ├── may reference DecisionRecord (via related_events linkage)
  └── references other GovernanceEvent[] (causal_parent_events)

DecisionRecord
  ├── references GovernanceEvent (source_event)
  ├── references ArtifactRecord (source_artifact)
  └── references other DecisionRecord[] (supersedes/superseded_by)

RiskRecord
  ├── references DecisionRecord (source_decision)
  ├── references GovernanceEvent (source_event)
  ├── references ArtifactRecord (source_artifact)
  └── references other RiskRecord[] (supersedes/superseded_by)

ArtifactRecord
  └── provides evidence for all other models
```

## 17. Source-of-Truth and Provenance Rules

1. Committed repo artifacts outrank generated records.
2. PCAE command output outranks human final report when both exist.
3. Git state outranks remembered push status.
4. Human final reports may seed records but must be reconciled with repo artifacts.
5. Conversation memory is secondary to all committed sources.
6. Derived summaries cannot silently supersede primary artifacts.
7. Generated records must cite source artifacts or commands.
8. Every model instance must have at least one provenance reference.

## 18. JSON Output Conventions

Future CLI commands should emit JSON matching these conventions:

| Convention | Rule |
|------------|------|
| Top-level `schema_version` | Present; matches model version |
| Top-level `generated_at` | ISO 8601 timestamp |
| Top-level `source_phase` or `source_command` | Which phase or command produced this |
| Top-level `records` or `snapshot` | Main data payload |
| Top-level `warnings` | List of warnings (may be empty) |
| Top-level `errors` | List of errors (may be empty) |
| Top-level `safety_notes` | Safety-relevant notes |
| Unknown fields | Use `null` or explicit `"unknown"`, never `false` |
| Boolean authorization fields | Must be explicit (`true`/`false`), never `null` |
| Lists | Empty list `[]` when no items, never `null` |
| Provenance | Always present; at least one source reference |

### Example JSON Envelope

```
{
  "schema_version": "0.1",
  "generated_at": "2026-06-24T00:00:00Z",
  "source_command": "pcae artifact-index",
  "records": [...],
  "warnings": [],
  "errors": [],
  "safety_notes": "read-only; does not authorize execution"
}
```

## 19. Storage Strategy

| Option | Recommendation | Status |
|--------|---------------|--------|
| Command-output only | **Start here** | Recommended for 86C–86H |
| Generated `.pcae/cache/` | Defer | Not created until performance demands it |
| Committed machine-readable state | Defer | Requires separate approval gate |
| Hybrid docs + cache | Defer | Not needed in MVP |

### Recommendation

First implementation (86C–86H) should generate all outputs on-the-fly by scanning committed
artifacts, git state, and PCAE command outputs. No files written. No cache persisted.

## 20. Read-Only Command-Output Strategy

Every future command in the 86-series must:
1. Read from committed artifacts, git state, and PCAE command outputs.
2. Print JSON to stdout.
3. Never write files.
4. Never create directories.
5. Never mutate repo state.
6. Never authorize any action.

## 21. Generated Cache Policy

- Generated cache is not created in 86B.
- When eventually introduced (if needed), cache must be:
  - Clearly non-authoritative (metadata: `authoritative=false`).
  - Include `source_commit` and `generated_at`.
  - Invalidated by any source artifact change.
  - Regenerable from committed artifacts.
  - Never override committed artifacts in source-of-truth precedence.
- Cache introduction requires explicit storage gate approval.

## 22. `.pcae` Storage Deferral Policy

- `.pcae` storage remains deferred.
- No `.pcae/memory/`, `.pcae/index/`, `.pcae/timeline/`, `.pcae/decisions/`, `.pcae/risks/`,
  or `.pcae/snapshots/` directories are created in 86B.
- Future `.pcae` storage requires:
  - Explicit storage implementation gate.
  - Tests for storage read/write/invalidation.
  - Evidence that command-output-only is insufficient.

---

## 23. Validation Rules

| # | Rule |
|---|------|
| V-1 | Every model instance has a stable ID |
| V-2 | Every model instance has `model_version` |
| V-3 | Every model instance has `status` from its allowed enum |
| V-4 | Every model instance has `source_phase` |
| V-5 | Every model instance has provenance (at least one source reference) |
| V-6 | `unknown` is distinct from `false` |
| V-7 | `missing` is distinct from `unknown` |
| V-8 | Observed state is distinct from authorized state |
| V-9 | Authorized is distinct from performed |
| V-10 | Accepted risk is distinct from mitigated risk |
| V-11 | Deferred is not approved |
| V-12 | Rejected remains rejected unless explicitly superseded |
| V-13 | Generated data must cite source artifacts |
| V-14 | Generated records are not authority |
| V-15 | Repo artifacts outrank generated cache |
| V-16 | Command output must be read-only |
| V-17 | Command output must not create files |
| V-18 | Command output must not authorize execution |
| V-19 | `.pcae` storage deferred |
| V-20 | Cache storage deferred |
| V-21 | Committed machine-readable state deferred |
| V-22 | Implementation requires tests |
| V-23 | Source/test changes forbidden in 86B |
| V-24 | README changes forbidden in 86B |
| V-25 | `docs/REAL_CAPTURED_TASKS.md` untouched |
| V-26 | No phase beyond 86B started |
| V-27 | `ArtifactRecord.artifact_path` must be repository-relative |
| V-28 | `ArtifactRecord.authoritative_for` required when status is `current` |
| V-29 | `MemorySnapshot.next_safe_actions` must not imply execution authorization |
| V-30 | `MemorySnapshot.forbidden_actions` must be explicitly populated |
| V-31 | `GovernanceEvent.event_type` must be from known enum |
| V-32 | `GovernanceEvent.causal_parent_events` must not create cycles |
| V-33 | `DecisionRecord.approved_scope` required for approval decisions |
| V-34 | `DecisionRecord.denied_scope` required for denial decisions |
| V-35 | `DecisionRecord.deferred_scope` required for deferral decisions |
| V-36 | `DecisionRecord.rejected_scope` required for rejection decisions |
| V-37 | `RiskRecord.risk_severity` required |
| V-38 | `RiskRecord.risk_likelihood` required |
| V-39 | `RiskRecord.risk_exposure` required |
| V-40 | `RiskRecord.acceptance_rationale` required for accepted risks |
| V-41 | `ProjectStateSnapshot.execution_authorized` must be explicit boolean |
| V-42 | `ProjectStateSnapshot.active_blockers` must be list (may be empty) |
| V-43 | `ProjectStateSnapshot.must_never_repeat_controls` must be list |
| V-44 | `ProjectStateSnapshot.confidence` must be high/medium/low |
| V-45 | `supersedes`/`superseded_by` must form valid chains (no orphans) |
| V-46 | JSON output must include `schema_version` |
| V-47 | JSON output must include `generated_at` |
| V-48 | Boolean authorization fields must never be `null` |

## 24. Failure Cases

| # | Failure | Impact |
|---|---------|--------|
| F-1 | Model missing required ID | Record unidentifiable |
| F-2 | Model missing version | Schema mismatch undetectable |
| F-3 | `unknown` encoded as `false` | Missing information treated as negative assertion |
| F-4 | `missing` encoded as `current` | Non-existent evidence treated as present |
| F-5 | Generated cache treated as source of truth | Repo artifacts bypassed |
| F-6 | Snapshot authorizes execution | Governance boundary crossed |
| F-7 | Decision loses rejection state | Rejected item re-enters pipeline |
| F-8 | Risk accepts mitigation without evidence | Risk assumed resolved |
| F-9 | Event order impossible (cycle in causal chain) | Causal analysis broken |
| F-10 | Artifact provenance missing | Claims unverifiable |
| F-11 | Storage created during design phase | Governance gate bypassed |
| F-12 | Source code changed during design phase | Implementation boundary violated |
| F-13 | Tests skipped during implementation phase | Implementation unverified |
| F-14 | CLI writes files in read-only mode | Read-only contract violated |
| F-15 | Authorization boolean is null instead of explicit | Authorization state ambiguous |

---

## 25. Future Implementation Plan

| Phase | Name | Scope |
|-------|------|-------|
| 86C | Read-Only Artifact Index Prototype | `pcae artifact-index --json` |
| 86D | Persistent Memory Snapshot Prototype | `pcae memory-snapshot --json` |
| 86E | Governance Event Timeline Extraction | `pcae timeline --json` |
| 86F | Decision Log Extraction | `pcae decision-log --json` |
| 86G | Risk Register Extraction | `pcae risk-register --json` |
| 86H | Project State Snapshot CLI | `pcae project-state --json` |
| 86I | Phase 85 Integration Tests | Cross-layer consistency tests |

No task contracts are created for these phases in 86B.

## 26. Future Test Coverage

No tests are added in 86B. Future implementation must test:

| Area | Coverage |
|------|----------|
| Model field completeness | Required fields present and correctly typed |
| Required field validation | Missing required fields rejected |
| Unknown vs missing handling | Distinct semantics preserved |
| Source-of-truth precedence | Higher-priority sources win |
| Artifact record parsing | Type, status, freshness correctly assigned |
| Memory snapshot generation | All fields populated from sources |
| Event ordering | Causal chains acyclic; ordering constraints enforced |
| Decision status preservation | Denied/deferred/rejected states preserved |
| Risk status preservation | Accepted/mitigated distinguished |
| Project state snapshot generation | All sections populated |
| Authorization booleans explicit | Never null; always true or false |
| No file writes | Read-only commands produce no side effects |
| No cache creation | No `.pcae` or cache files created unless explicitly scoped |

## 27. Example Model Records

Illustrative markdown only, not executable:

### ArtifactRecord Example

```
artifact_id: persistent-lifecycle-memory-model
artifact_type: memory_model_artifact
artifact_path: docs/PERSISTENT_LIFECYCLE_MEMORY_MODEL.md
artifact_title: Persistent Lifecycle Memory Model
artifact_status: current
artifact_version: "0.1"
source_phase: 85A
created_phase: 85A
implementation_status: not_started
authoritative_for: [memory_model_design]
evidence_level: repo_committed_artifact
freshness_status: fresh
hash_or_commit_ref: 54ddd644
```

### DecisionRecord Example

```
decision_id: defer-84-memory-roadmap-to-85
decision_type: deferral_decision
decision_status: closed
source_phase: 84L
source_artifact: docs/ROADMAP_RECONCILIATION_PHASE_85_PLAN.md
decision_maker: operator
human_required: true
deferred_scope: original 84 persistent memory roadmap moved to 85A-85F
evidence_level: repo_committed_artifact
```

### RiskRecord Example

```
risk_id: raw-push-never-repeat
risk_type: must_never_repeat_risk
risk_status: active
risk_title: Raw git push must not be normalized
risk_severity: high
risk_likelihood: possible
risk_exposure: high
source_phase: 77-series
human_review_required: false
evidence_level: repo_committed_artifact
safety_notes: governed pcae push remains required
```

---

## 28. Recommended Next Phase

**86C — Read-Only Artifact Index Prototype**

86C should implement the first read-only CLI command (`pcae artifact-index --json`) using the
`ArtifactRecord` model defined in this document. It should scan `docs/` for governance
artifacts, classify them by type, assess freshness, and emit JSON output. It must add tests.

No 86C task contract is created in 86B.

---

## Design Identity

| Field | Value |
|-------|-------|
| data_model_storage_design_name | phase_85_data_model_storage_design |
| data_model_storage_design_version | 0.1 |
| data_model_storage_design_status | draft_documented |
| implementation_status | not_started |
| storage_implementation_status | not_started |

## Authorization Flags for 86B

| Flag | Value |
|------|-------|
| backend_invocation_performed | false |
| new_prompts_sent | false |
| new_capture_performed | false |
| new_intake_performed | false |
| new_adoption_review_performed | false |
| new_adoption_approval_performed | false |
| new_adoption_execution_performed | false |
| repo_mutation_authorized | true_for_data_model_storage_docs_status_only |
| readme_mutation_authorized | false |
| source_mutation_authorized | false |
| test_mutation_authorized | false |
| docs_real_captured_tasks_mutation_authorized | false |
| persistent_memory_implementation_authorized | false |
| artifact_index_implementation_authorized | false |
| timeline_implementation_authorized | false |
| decision_log_implementation_authorized | false |
| risk_register_implementation_authorized | false |
| project_snapshot_implementation_authorized | false |
| permission_broker_implementation_authorized | false |
| shell_gate_implementation_authorized | false |
| storage_implementation_authorized | false |
| cli_implementation_authorized | false |
| cache_creation_authorized | false |
| machine_readable_state_authorized | false |
| phase_86c_task_contract_authorized | false |
| commit_authorized | false |
| push_authorized | false |
| execution_authorized | false |
