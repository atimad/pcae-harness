# Project State Snapshot Design

## 1. Purpose

Define how PCAE produces a current project-state answer by integrating the persistent
lifecycle memory model (85A), artifact index (85B), governance event timeline (85C), decision
log (85D), and risk register (85E). The snapshot is the capstone of the Phase 85 design
sequence, answering the original project-intelligence questions:

- What phase are we in?
- What was approved?
- What is blocked?
- What can be safely done next?
- What must never be repeated?

## 2. Scope

Design only. This artifact defines snapshot sections, fields, source layers, freshness
checks, safety boundaries, query outputs, and validation rules. It does not implement
snapshot generation, create machine-readable files, or add tests.

## 3. Non-Goals

- Implementing snapshot generation or CLI commands.
- Creating `.pcae` snapshot storage directories or files.
- Adding tests.
- Modifying source code, README, or existing artifacts.
- Backend invocation, prompt sending, capture, intake, or adoption.

## 4. Motivation from 85A through 85E

| Phase | Layer | What It Provides to Snapshot |
|-------|-------|------------------------------|
| 85A | Persistent Lifecycle Memory | Entity state: phases, approvals, flags, captures, risks |
| 85B | Artifact Index | Evidence lookup: where artifacts live, their freshness and authority |
| 85C | Governance Event Timeline | Temporal ordering: what happened when, causality chains |
| 85D | Decision Log | Durable decisions: approvals, denials, deferrals, rejections, overrides |
| 85E | Risk Register | Risk state: active, accepted, mitigated, deferred, must-never-repeat |

The snapshot synthesizes these five layers into a single coherent answer surface. Without
the snapshot, a consumer would need to query each layer independently and reconcile
conflicting or overlapping results.

---

## 5. Project State Snapshot Design Principles

1. Snapshot reports observed project state, not permission by itself.
2. Snapshot does not authorize execution.
3. Snapshot does not authorize backend invocation.
4. Snapshot does not authorize adoption.
5. Snapshot does not authorize commit or push.
6. Snapshot must distinguish observed state from authorized next action.
7. Snapshot must cite memory, artifacts, events, decisions, and risks.
8. Snapshot must preserve source-of-truth precedence.
9. Snapshot must expose uncertainty and stale signals.
10. Snapshot must include next safe actions and forbidden actions.
11. Snapshot must support human review.
12. Snapshot must support offline audit.
13. Snapshot must be reconstructable after chat/session reset.
14. Snapshot must never silently hide blockers, risks, deferrals, or rejections.

## 6. Project State Snapshot Threat Model

| # | Threat | Impact |
|---|--------|--------|
| ST-1 | Snapshot says ready when blocker exists | Unsafe action proceeds |
| ST-2 | Snapshot omits active risk | Risk invisible to decision-makers |
| ST-3 | Snapshot treats accepted risk as mitigated | Risk assumed resolved |
| ST-4 | Snapshot treats deferred item as approved | Deferred work starts without lifecycle |
| ST-5 | Snapshot treats rejected item as reopened | Rejected item re-enters pipeline |
| ST-6 | Snapshot reports stale phase as current | Agent operates on wrong phase |
| ST-7 | Snapshot relies on chat memory over repo artifacts | Ephemeral source overrides durable |
| ST-8 | Snapshot omits provenance | Claims unverifiable |
| ST-9 | Snapshot conflates permission with lifecycle approval | Scope escalation |
| ST-10 | Snapshot implies execution authorization | Governance boundary crossed |
| ST-11 | Snapshot omits forbidden actions | Forbidden action attempted |
| ST-12 | Snapshot hides human-review requirement | Human review bypassed |
| ST-13 | Snapshot ignores stale validator signals | Stale signals misinterpreted |
| ST-14 | Snapshot ignores origin divergence | Push state incorrect |
| ST-15 | Snapshot ignores dirty working tree | Uncommitted changes missed |
| ST-16 | Snapshot contradicts memory model | State inconsistency |
| ST-17 | Snapshot contradicts artifact index | Evidence inconsistency |
| ST-18 | Snapshot contradicts event timeline | Temporal inconsistency |
| ST-19 | Snapshot contradicts decision log | Decision inconsistency |
| ST-20 | Snapshot contradicts risk register | Risk inconsistency |

---

## 7. Snapshot Source Layers

| Layer | Source | Trust Level |
|-------|--------|-------------|
| `persistent_lifecycle_memory` | 85A memory entities | High (repo-backed) |
| `artifact_index` | 85B artifact metadata | High (repo-backed) |
| `governance_event_timeline` | 85C event records | High (repo-backed) |
| `decision_log` | 85D decision entries | High (repo-backed) |
| `risk_register` | 85E risk entries | High (repo-backed) |
| `deferred_item_tracker` | 84J deferred items | High (repo-backed) |
| `project_status` | PROJECT_STATUS.md | High (committed) |
| `changelog` | CHANGELOG.md | High (committed) |
| `git_state` | git status, log, rev-list | Highest (ground truth) |
| `pcae_command_outputs` | health, check, doctor, lifecycle | High (runtime verified) |
| `human_final_reports` | Operator-provided summaries | Medium |
| `conversation_memory` | Chat context | Lowest |

## 8. Required Snapshot Sections

| Section | Purpose |
|---------|---------|
| `snapshot_identity` | Unique ID, version, creation time |
| `current_phase` | Active phase and status |
| `latest_completed_phase` | Most recently completed phase |
| `lifecycle_state` | Current lifecycle state machine position |
| `roadmap_position` | Position in roadmap sequence |
| `phase_sequence_position` | Position within current phase series |
| `repository_state` | Clean/dirty, branch, staged files |
| `git_push_state` | Origin sync, unpushed commits |
| `health_check_state` | PCAE health/check/doctor/push results |
| `approval_state` | Active approvals and their scope |
| `authorization_flags` | Current flag values |
| `backend_invocation_state` | Invocation authorization and performance status |
| `prompt_capture_intake_adoption_state` | Pipeline state |
| `blocked_items` | Items currently blocked |
| `deferred_items` | Items currently deferred |
| `rejected_items` | Items currently rejected |
| `accepted_risks` | Risks explicitly accepted |
| `active_risks` | Risks currently active |
| `must_never_repeat_controls` | Permanent safety controls |
| `stale_or_structural_signals` | Persistent stale/structural signals |
| `artifact_evidence` | Key artifacts supporting this snapshot |
| `next_safe_actions` | Recommended safe next actions |
| `forbidden_actions` | Explicitly forbidden actions |
| `human_review_required` | Whether human review is needed |
| `implementation_status` | Implementation state of design artifacts |
| `test_status` | Test state and coverage |

## 9. Required Snapshot Fields

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `snapshot_id` | string | yes | Unique identifier |
| `snapshot_version` | string | yes | Snapshot model version |
| `snapshot_status` | string | yes | Status from allowed values |
| `snapshot_created_at` | timestamp | yes | Creation time |
| `source_phase` | string | yes | Phase that produced this snapshot |
| `latest_completed_phase` | string | yes | Most recently completed phase |
| `current_active_phase` | string | yes | Currently active phase or none |
| `current_lifecycle_state` | string | yes | Current lifecycle state |
| `roadmap_position` | string | yes | Position in roadmap |
| `recommended_next_phase` | string | yes | Recommended next phase |
| `repository_clean` | boolean | yes | Whether working tree is clean |
| `branch` | string | yes | Current branch |
| `origin_sync_status` | string | yes | Synced/diverged/ahead/behind |
| `origin_main_head_count` | integer | yes | Commits ahead of origin |
| `health_status` | string | yes | pcae health result |
| `check_status` | string | yes | pcae check result |
| `doctor_status` | string | yes | pcae doctor task-memory result |
| `push_check_status` | string | yes | pcae push check result |
| `execution_authorized` | boolean | yes | false |
| `backend_invocation_authorized` | boolean | yes | false |
| `prompt_sending_authorized` | boolean | yes | false |
| `capture_authorized` | boolean | yes | false |
| `intake_authorized` | boolean | yes | false |
| `adoption_authorized` | boolean | yes | false |
| `source_mutation_authorized` | boolean | yes | false |
| `test_mutation_authorized` | boolean | yes | false |
| `readme_mutation_authorized` | boolean | yes | false |
| `docs_real_captured_tasks_mutation_authorized` | boolean | yes | false |
| `active_blockers` | list | yes | Currently active blockers |
| `active_deferred_items` | list | yes | Currently deferred items |
| `active_rejected_items` | list | yes | Currently rejected items |
| `active_risks` | list | yes | Currently active risks |
| `accepted_risks` | list | yes | Explicitly accepted risks |
| `must_never_repeat_controls` | list | yes | Permanent safety controls |
| `stale_signals` | list | yes | Persistent stale/structural signals |
| `evidence_artifacts` | list | yes | Key artifact paths |
| `evidence_commits` | list | yes | Key commit hashes |
| `next_safe_actions` | list | yes | Recommended safe actions |
| `forbidden_actions` | list | yes | Explicitly forbidden actions |
| `human_review_required` | boolean | yes | Whether human review is needed |
| `confidence` | string | yes | high/medium/low |
| `safety_notes` | string | no | Safety-relevant notes |

## 10. Snapshot Status Values

| Status | Meaning |
|--------|---------|
| `draft_documented` | Snapshot design exists but not yet generated |
| `current` | Snapshot reflects current verified state |
| `stale` | Snapshot is outdated |
| `requires_review` | Snapshot needs human review before use |
| `blocked` | Snapshot cannot be produced due to blockers |
| `superseded` | Replaced by a newer snapshot |
| `unknown` | Status not determined |

## 11. Snapshot Freshness Model

| Freshness | Meaning |
|-----------|---------|
| `fresh` | Produced from current phase with verified sources |
| `acceptable_stale` | Produced recently; sources have not changed materially |
| `stale_requires_review` | Sources have changed since snapshot was produced |
| `blocked_by_stale_signal` | Stale validator or structural signal may affect accuracy |
| `unknown` | Freshness not assessed |

## 12. Snapshot Source-of-Truth Rules

1. Committed repo artifacts outrank chat memory.
2. PCAE command outputs outrank human final reports when both exist.
3. Git state outranks remembered push status.
4. Decision log outranks derived summary for approvals/denials/deferrals/rejections.
5. Risk register outranks derived summary for risks.
6. Artifact index identifies authoritative artifacts.
7. Conversation memory is secondary to all committed sources.
8. Derived summaries cannot silently supersede primary artifacts.

## 13. Snapshot Provenance and Evidence Policy

Every snapshot claim must trace to a source layer:

```
snapshot_claim → source_layer → evidence_artifact_or_command → commit_or_runtime_output
```

Claims without provenance are flagged with `confidence=low`. Snapshot must expose which
claims are fully evidenced and which are derived or uncertain.

---

## 14. Current Phase Section

Answers: What phase are we in? What was most recently completed? What is next?

| Field | Source |
|-------|--------|
| `current_active_phase` | Active task contract in tasks/active/ |
| `latest_completed_phase` | Latest completion commit |
| `recommended_next_phase` | Phase artifact recommendation |
| Phases not yet started | Roadmap artifact |

## 15. Lifecycle State Section

Answers: What is the lifecycle state? What states are reachable? What is blocked?

| Field | Source |
|-------|--------|
| `current_lifecycle_state` | 85A lifecycle_state entity |
| Allowed next states | 85A lifecycle state machine |
| Blocked states | Decision log denials + risk register blockers |

## 16. Roadmap Position Section

Answers: Where are we in the roadmap? What series is active? What comes after?

| Field | Source |
|-------|--------|
| `roadmap_position` | Roadmap reconciliation artifact |
| Phase 85 position | 85A–85F completion status |
| Next roadmap phase | Snapshot recommendation |

## 17. Approval and Authorization Section

Answers: What was approved? What was denied? What is authorized but not performed?

| Field | Source |
|-------|--------|
| Active approvals | Decision log `approval_decision` entries |
| Active denials | Decision log `denial_decision` entries |
| Authorization flags | 85A authorization_flag_record entities |
| Authorized but not performed | Flags true but action not yet taken |
| Not authorized | Flags false (most flags default false) |

## 18. Blocked/Deferred/Rejected Section

Answers: What is blocked? What is deferred? What was rejected?

| Field | Source |
|-------|--------|
| `active_blockers` | Risk register blocked risks + decision log blocked decisions |
| `active_deferred_items` | Decision log deferrals + deferred item tracker |
| `active_rejected_items` | Decision log rejections |
| Review requirements | Deferred items with review context |

## 19. Risk and Must-Never-Repeat Section

Answers: What risks are active? What was accepted? What must never be repeated?

| Field | Source |
|-------|--------|
| `active_risks` | Risk register active entries |
| `accepted_risks` | Risk register accepted entries |
| Mitigated risks | Risk register mitigated entries |
| `stale_signals` | Risk register stale_signal entries |
| `must_never_repeat_controls` | Risk register must_never_repeat entries + decision log |

## 20. Artifact/Evidence Section

Answers: What artifacts support these answers? Which are fresh? Which are stale?

| Field | Source |
|-------|--------|
| `evidence_artifacts` | Artifact index current/fresh entries |
| Stale artifacts | Artifact index stale entries |
| Missing artifacts | Artifact index missing entries |
| `evidence_commits` | Phase completion commits |

## 21. Git/Commit/Push Section

Answers: Is the repo clean? Are we synced? What was committed and pushed?

| Field | Source |
|-------|--------|
| `repository_clean` | git status |
| `branch` | git branch --show-current |
| `origin_sync_status` | git status --branch --short |
| `origin_main_head_count` | git rev-list --count origin/main..HEAD |
| Latest commits | git log |
| Push method | pcae push records |

## 22. Handoff/Bootstrap Section

Answers: Is the handoff state current? What bootstrap profile is active?

| Field | Source |
|-------|--------|
| Handoff refresh status | 85A handoff_record |
| Structural signals | Risk register stale_signal entries |
| Default test command | `python -m pytest -n auto` |
| Serial exceptions | 3 retained |
| Runtime execution authorized | false |

## 23. Next Safe Action Section

Answers: What can be safely done next?

- `next_safe_actions` are recommendations, not execution authorization.
- Each action must cite supporting artifacts, decisions, and risks.
- Each action must include safety caveats.
- Next safe action must not imply backend invocation, adoption, commit, or push.
- If blockers or active risks exist, they must be surfaced alongside recommendations.

## 24. Forbidden Action Section

Answers: What must not be done?

- Forbidden actions include actions blocked by task contract, lifecycle state, risk register,
  decision log, or active safety boundaries.
- Forbidden actions must remain visible even when next safe action exists.
- Forbidden actions are not automatically enforced by the snapshot (enforcement is separate).

## 25. Human Review Section

Answers: Does this snapshot require human review?

- `human_review_required` is true when blockers, accepted risks, stale signals, permission
  escalations, or ambiguous evidence require operator judgment.
- Human review does not automatically authorize execution.
- The snapshot surfaces the review requirement; the human decides what to do.

---

## 26. Relationship to Persistent Lifecycle Memory

- Snapshot reads memory state for entity values (phases, flags, approvals, risks).
- Snapshot does not replace memory — it is a read-only view.
- Snapshot must cite memory-derived claims.
- Snapshot must expose missing memory fields as gaps.

## 27. Relationship to Artifact Index

- Snapshot uses artifact index for evidence lookup and freshness assessment.
- Snapshot must cite artifact paths for evidence claims.
- Snapshot must flag missing or stale artifacts.
- Snapshot must respect artifact authority designations.

## 28. Relationship to Governance Event Timeline

- Snapshot uses timeline to explain what happened and in what order.
- Snapshot must preserve causality from timeline.
- Snapshot must not infer decision state from events alone if decision log exists.
- Snapshot uses timeline for "what changed since last snapshot" queries.

## 29. Relationship to Decision Log

- Snapshot uses decision log for approvals, denials, deferrals, rejections, overrides,
  accepted risks, and must-never-repeat decisions.
- Snapshot must distinguish approved from performed.
- Snapshot must preserve denied/deferred/rejected states.
- Snapshot must not silently reopen rejected decisions.

## 30. Relationship to Risk Register

- Snapshot uses risk register for active, accepted, mitigated, deferred, blocked,
  stale-signal, and must-never-repeat risks.
- Snapshot must not treat accepted risk as mitigation.
- Snapshot must surface must-never-repeat controls prominently.
- Snapshot must distinguish stale signals from substantive blockers.

---

## 31. Query Model

### Q1: what_phase_are_we_in

| Field | Value |
|-------|-------|
| Required snapshot sections | current_phase, latest_completed_phase, roadmap_position |
| Memory dependencies | phase_record, lifecycle_state |
| Artifact index dependencies | Phase artifacts, task contracts |
| Timeline dependencies | phase_started, phase_completed events |
| Decision log dependencies | None directly |
| Risk register dependencies | Blockers that may affect phase |
| Expected answer shape | `{current_phase, latest_completed, recommended_next, blocked_by}` |
| Required provenance | Completion commit or active task contract |
| Safety caveats | Advisory; does not authorize starting next phase |

### Q2: what_was_approved

| Field | Value |
|-------|-------|
| Required snapshot sections | approval_state, authorization_flags |
| Decision log dependencies | approval_decision entries |
| Expected answer shape | `[{approval_id, scope, status, phase}]` |
| Required provenance | Decision artifact |
| Safety caveats | Past approval may be expired or superseded |

### Q3: what_was_denied

| Field | Value |
|-------|-------|
| Required snapshot sections | approval_state, forbidden_actions |
| Decision log dependencies | denial_decision entries |
| Expected answer shape | `[{denial_id, scope, status}]` |
| Required provenance | Decision artifact |
| Safety caveats | Active denials feed forbidden action list |

### Q4: what_is_blocked

| Field | Value |
|-------|-------|
| Required snapshot sections | blocked_items, active_risks |
| Risk register dependencies | blocked risks |
| Decision log dependencies | blocked_decision entries |
| Expected answer shape | `[{blocker, condition, source, risk_level}]` |
| Required provenance | Risk or decision source |
| Safety caveats | Distinguish stale signals from substantive blockers |

### Q5: what_is_deferred

| Field | Value |
|-------|-------|
| Required snapshot sections | deferred_items |
| Decision log dependencies | deferral_decision entries |
| Deferred tracker dependencies | DF-1–DF-4, HY-1, IMPL-1–2, TEST-1 |
| Expected answer shape | `[{item_id, scope, target_phase, status}]` |
| Required provenance | Source artifact and phase |
| Safety caveats | Deferred does not mean approved |

### Q6: what_was_rejected

| Field | Value |
|-------|-------|
| Required snapshot sections | rejected_items |
| Decision log dependencies | rejection_decision entries |
| Expected answer shape | `[{item_id, scope, reason, status}]` |
| Required provenance | Rejection decision |
| Safety caveats | Rejected items must not be silently reintroduced |

### Q7: what_risk_was_accepted

| Field | Value |
|-------|-------|
| Required snapshot sections | accepted_risks |
| Risk register dependencies | accepted risk entries |
| Decision log dependencies | accepted_risk_decision entries |
| Expected answer shape | `[{risk_id, severity, rationale, accepted_by}]` |
| Required provenance | Decision with rationale |
| Safety caveats | Accepted is not mitigated |

### Q8: what_requires_human_review

| Field | Value |
|-------|-------|
| Required snapshot sections | human_review_required, stale_signals, accepted_risks |
| All layer dependencies | Items flagged human_review_required=true |
| Expected answer shape | `[{item, reason, urgency}]` |
| Required provenance | Source of review requirement |
| Safety caveats | Advisory; human review does not authorize execution |

### Q9: what_can_be_safely_done_next

| Field | Value |
|-------|-------|
| Required snapshot sections | next_safe_actions, lifecycle_state, authorization_flags |
| All layer dependencies | Current state from all layers |
| Expected answer shape | `[{action, safety_level, prerequisites, provenance}]` |
| Required provenance | Current state evidence |
| Safety caveats | Advisory only; does not authorize execution |

### Q10: what_must_never_be_repeated

| Field | Value |
|-------|-------|
| Required snapshot sections | must_never_repeat_controls, forbidden_actions |
| Risk register dependencies | must_never_repeat_risk entries |
| Decision log dependencies | must_never_repeat_decision entries |
| Expected answer shape | `[{control, reason, source, permanence}]` |
| Required provenance | Source decision or governance invariant |
| Safety caveats | Enforcement is separate from reporting |

### Q11: what_evidence_supports_this_answer

| Field | Value |
|-------|-------|
| Required snapshot sections | artifact_evidence |
| Artifact index dependencies | All referenced artifacts |
| Expected answer shape | `[{artifact_path, evidence_level, freshness}]` |
| Required provenance | Artifact must exist on filesystem |
| Safety caveats | Missing evidence invalidates dependent claims |

### Q12: what_changed_since_last_snapshot

| Field | Value |
|-------|-------|
| Required snapshot sections | All (diff against previous) |
| Timeline dependencies | Events since previous snapshot |
| Expected answer shape | `{new_phases, new_decisions, new_risks, flag_changes}` |
| Required provenance | Two valid snapshots for comparison |
| Safety caveats | Drift detection is informational |

---

## 32. Snapshot Update Rules

1. Snapshot updates only after phase completion or explicit snapshot phase.
2. Snapshot update must cite artifacts, command outputs, decisions, events, risks, or commits.
3. Snapshot must not infer approval from plan text.
4. Snapshot must preserve denied/deferred/rejected states.
5. Snapshot must preserve active/accepted risks.
6. Snapshot must preserve must-never-repeat controls.
7. Snapshot must distinguish observed state from authorized action.
8. Snapshot must be idempotent (same inputs produce same snapshot).
9. Snapshot must expose stale evidence.
10. Snapshot must not authorize execution.
11. Snapshot must flag claims without provenance as low-confidence.
12. Snapshot must include all source layer versions for reproducibility.

---

## 33. Validation Rules

| # | Rule |
|---|------|
| V-1 | `snapshot_id` required |
| V-2 | `snapshot_version` required |
| V-3 | `snapshot_status` required and from allowed values |
| V-4 | `snapshot_created_at` required |
| V-5 | `source_phase` required |
| V-6 | `latest_completed_phase` required |
| V-7 | `current_lifecycle_state` required |
| V-8 | `roadmap_position` required |
| V-9 | `repository_clean` required |
| V-10 | `branch` required |
| V-11 | `origin_sync_status` required |
| V-12 | `health_status` required |
| V-13 | `execution_authorized` required and must be explicit |
| V-14 | `active_blockers` required (may be empty list) |
| V-15 | `active_deferred_items` required (may be empty list) |
| V-16 | `active_risks` required (may be empty list) |
| V-17 | `must_never_repeat_controls` required (may be empty list) |
| V-18 | `next_safe_actions` required (may be empty list) |
| V-19 | `forbidden_actions` required (may be empty list) |
| V-20 | `human_review_required` required |
| V-21 | `confidence` required |
| V-22 | Snapshot does not authorize execution |
| V-23 | Snapshot does not authorize backend invocation |
| V-24 | Snapshot does not authorize adoption |
| V-25 | Snapshot does not authorize commit/push |
| V-26 | Accepted risk must not be reported as mitigated |
| V-27 | Deferred item must not be reported as approved |
| V-28 | Rejected item must not be reported as reopened |
| V-29 | Blocker must not be silently hidden |
| V-30 | Active risk must not be omitted |
| V-31 | Must-never-repeat control must not be omitted |
| V-32 | Forbidden actions must remain visible |
| V-33 | Source-of-truth precedence must be preserved |
| V-34 | Provenance required for each evidence claim |
| V-35 | Stale signals must be surfaced, not hidden |
| V-36 | Origin divergence must be reported |
| V-37 | Dirty working tree must be reported |
| V-38 | Chat memory must not override committed evidence |
| V-39 | Permission allowed must not conflate with lifecycle approval |
| V-40 | Design-only phase creates no machine-readable snapshot |
| V-41 | Future implementation requires tests |
| V-42 | No source/test changes in 85F |
| V-43 | No phase beyond 85F started in this phase |
| V-44 | No `.pcae` snapshot storage created in 85F |

## 34. Failure Cases

| # | Failure | Impact |
|---|---------|--------|
| F-1 | Snapshot says ready when blocker exists | Unsafe action proceeds |
| F-2 | Snapshot omits active risk | Risk invisible |
| F-3 | Accepted risk reported as mitigated | Risk assumed resolved |
| F-4 | Deferred item reported as approved | Premature implementation |
| F-5 | Rejected item silently reopened | Rejected work re-enters pipeline |
| F-6 | Stale phase reported as current | Wrong phase assumption |
| F-7 | Chat memory overrides repo artifact | Ephemeral source wins |
| F-8 | Provenance omitted | Claims unverifiable |
| F-9 | Permission conflated with lifecycle approval | Scope escalation |
| F-10 | Execution authorization implied | Governance boundary crossed |
| F-11 | Forbidden actions omitted | Forbidden action attempted |
| F-12 | Human review hidden | Review bypassed |
| F-13 | Snapshot contradicts source layer | Inconsistency |
| F-14 | Snapshot implementation attempted in design phase | Governance violated |
| F-15 | Tests skipped in implementation phase | Implementation unverified |

---

## 35. Future Implementation Plan

Candidate future phases after this design:

| Phase | Name | Scope |
|-------|------|-------|
| 85F.1 | Project State Snapshot Implementation Plan | Detailed implementation spec |
| 85F.2 | Read-Only Project State Snapshot Prototype | First read-only snapshot command |
| 85F.3 | Project State Snapshot Tests | Test suite for snapshot model |

No task contracts are created for these phases in 85F.

## 36. Future Test Coverage

No tests are added in 85F because this is design-only. Future implementation must test:

| Test Area | Coverage Target |
|-----------|----------------|
| Snapshot field completeness | All required fields present |
| Current phase reconstruction | Correct phase from committed evidence |
| Latest completed phase reconstruction | Correct phase from completion commits |
| Approval/authorization answer generation | Only artifact-backed approvals returned |
| Blocked/deferred/rejected answer generation | Status correctly sourced from decision log |
| Risk answer generation | Active/accepted/mitigated correctly classified |
| Must-never-repeat answer generation | Permanent controls surfaced |
| Next safe action answer generation | Advisory with caveats |
| Forbidden action answer generation | All active forbidden actions included |
| Source-of-truth precedence | Higher-priority sources win |
| Stale evidence detection | Stale sources flagged |
| Origin divergence detection | Unpushed commits detected |
| Dirty worktree detection | Uncommitted changes detected |
| Memory/artifact/timeline/decision/risk linkage | All layers correctly referenced |
| Idempotent snapshot generation | Same input produces same snapshot |

## 37. Example Project State Snapshot

Illustrative markdown only, not an executable format:

```
snapshot_id: example-85f-001
snapshot_version: 0.1
snapshot_status: draft_documented
snapshot_created_at: 2026-06-24T00:00:00Z
source_phase: 85F
latest_completed_phase: 85E — Risk Register
current_active_phase: 85F — Project State Snapshot
current_lifecycle_state: closed
roadmap_position: Phase 85 design sequence, 85F active (capstone)
recommended_next_phase: 86A — Phase 85 Implementation Roadmap
repository_clean: true
branch: main
origin_sync_status: synced
origin_main_head_count: 0
health_status: healthy
check_status: passed
doctor_status: clean
push_check_status: nothing_to_push
execution_authorized: false
backend_invocation_authorized: false
prompt_sending_authorized: false
capture_authorized: false
intake_authorized: false
adoption_authorized: false
source_mutation_authorized: false
test_mutation_authorized: false
readme_mutation_authorized: false
docs_real_captured_tasks_mutation_authorized: false
active_blockers: []
active_deferred_items:
  - DF-1 stale table
  - DF-2 capability models
  - DF-3 blocked taxonomy
  - DF-4 flag standardization
  - HY-1 task filename hygiene (can close)
  - IMPL-1 schema implementation
  - IMPL-2 command dry-run implementation
  - TEST-1 future test coverage
  - HSR-1 validator stale for doc streams
active_rejected_items:
  - RJ-1 through RJ-4 (83I, remain rejected)
active_risks:
  - raw-push-never-repeat (must_never_repeat, high)
  - stale-summary-risk (artifact_staleness, low)
accepted_risks:
  - documentation-phases-defer-tests (accepted, low)
must_never_repeat_controls:
  - bypass permissions without exception
  - raw git push
  - force push
  - adoption without approval
  - invocation without guard
  - mutation outside scope
  - boundary collapse
  - rejected item reintroduced
stale_signals:
  - handoff-state-refresh 4B/6W structural signals
evidence_artifacts:
  - docs/PERSISTENT_LIFECYCLE_MEMORY_MODEL.md
  - docs/ARTIFACT_INDEX_DESIGN.md
  - docs/GOVERNANCE_EVENT_TIMELINE_DESIGN.md
  - docs/DECISION_LOG_INTEGRATION_DESIGN.md
  - docs/RISK_REGISTER_DESIGN.md
  - docs/PROJECT_STATE_SNAPSHOT_DESIGN.md
evidence_commits:
  - 9365c011 (85E completion)
next_safe_actions:
  - Complete 85F project state snapshot design
  - Proceed to 86A Phase 85 implementation roadmap
forbidden_actions:
  - Backend invocation without guard approval
  - Prompt sending without lifecycle authorization
  - Adoption without intake/review/approval
  - Source/test mutation without implementation phase
  - Commit/push without governed pcae push
  - Force push
  - Raw git push
human_review_required: false
confidence: high
safety_notes: design-only phase; no implementation authorization
```

---

## 38. Phase 85 Design Sequence Closure

Phases 85A–85F complete the restored persistent memory/project intelligence design sequence:

| Phase | Layer | Status |
|-------|-------|--------|
| 85A | Persistent Lifecycle Memory Model | draft_documented, not_started |
| 85B | Artifact Index | draft_documented, not_started |
| 85C | Governance Event Timeline | draft_documented, not_started |
| 85D | Decision Log Integration | draft_documented, not_started |
| 85E | Risk Register | draft_documented, not_started |
| 85F | Project State Snapshot | draft_documented, not_started |

All six layers are designed. No implementation has started. The designs define:

- **What** PCAE should remember (85A: 18 entities, 21 fields)
- **Where** evidence lives (85B: 24 categories, 19 metadata fields)
- **When** events happened (85C: 33 event types, 19 fields)
- **What** was decided (85D: 13 decision types, 25 fields)
- **What** risks exist (85E: 22 risk types, 32 fields)
- **How** to produce a project-state answer (85F: 26 sections, 41 fields)

Together they enable PCAE to answer the original project-intelligence questions from
committed artifacts rather than ephemeral conversation memory.

Implementation requires separate governed phases with tests.

## 39. Recommended Next Phase

**86A — Phase 85 Implementation Roadmap**

The Phase 85 design sequence is complete. All six layers (memory, index, timeline, decisions,
risks, snapshot) have documented designs with validation rules and failure cases. The next
step is an implementation roadmap that plans the order, dependencies, test strategy, and
governance gates for implementing these designs.

86A should:
1. Review which 85-series designs should be implemented first.
2. Define implementation dependencies (e.g., memory model before snapshot).
3. Plan test coverage for each implementation phase.
4. Define governance gates for implementation.
5. Decide whether implementation phases should be design+implementation or implementation-only.

No 86A task contract is created in 85F.

---

## Project State Snapshot Identity

| Field | Value |
|-------|-------|
| project_state_snapshot_name | pcae_project_state_snapshot |
| project_state_snapshot_version | 0.1 |
| project_state_snapshot_status | draft_documented |
| project_state_snapshot_implementation_status | not_started |
| phase_85_design_sequence_status | complete |

## Authorization Flags for 85F

| Flag | Value |
|------|-------|
| backend_invocation_performed | false |
| new_prompts_sent | false |
| new_capture_performed | false |
| new_intake_performed | false |
| new_adoption_review_performed | false |
| new_adoption_approval_performed | false |
| new_adoption_execution_performed | false |
| repo_mutation_authorized | true_for_project_snapshot_docs_status_only |
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
| phase_85f1_task_contract_authorized | false |
| phase_86a_task_contract_authorized | false |
| commit_authorized | false |
| push_authorized | false |
| execution_authorized | false |
