# Decision Log Integration Design

## 1. Purpose

Define how PCAE integrates durable governance decisions — approvals, denials, deferrals,
rejections, human overrides, accepted risks, permission decisions, and lessons that must
never be repeated — into a persistent, auditable decision model. The decision log is the
bridge between the event timeline (85C) and project-state answers.

## 2. Scope

Design only. This artifact defines decision types, fields, lifecycle rules, provenance
requirements, relationships to other 85-series components, and query targets. It does not
implement decision storage, create machine-readable files, or add tests.

## 3. Non-Goals

- Implementing decision log storage or CLI commands.
- Creating `.pcae` decision log directories or files.
- Adding tests.
- Modifying source code, README, or existing artifacts.
- Backend invocation, prompt sending, capture, intake, or adoption.
- Implementing permission broker or shell gate.

## 4. Motivation from 85A, 85B, and 85C

- **85A** (memory model) defines `decision_record`, `approval_record`, and `deferred_item_record`
  entities but does not define decision lifecycle rules or integration semantics.
- **85B** (artifact index) locates decision artifacts (approval docs, adoption docs) but does
  not capture the durable meaning of those decisions.
- **85C** (event timeline) records `approval_granted`, `approval_denied`, `item_deferred`,
  `item_rejected`, and `permission_allowed/blocked/escalated` events but does not define
  how those events become persistent, queryable decisions.

The decision log captures the durable governance meaning: what was decided, by whom, with
what scope, and whether it can ever be changed. It transforms timeline events and artifact
evidence into answers like "What was approved?", "What must never be repeated?", and
"What requires human review?"

---

## 5. Decision Log Design Principles

1. Decision log records governance decisions, not permission by itself.
2. Decision log does not authorize execution.
3. Decision log does not authorize backend invocation.
4. Decision log does not authorize adoption.
5. Decision log does not authorize commit or push.
6. Decision log must distinguish approval, denial, deferral, rejection, override, accepted risk, and unknown.
7. Decision log must preserve irreversible decisions.
8. Decision log must preserve human authority boundaries.
9. Decision log must link every decision to evidence.
10. Decision log must support offline audit.
11. Decision log must support project-state reconstruction.
12. Decision log must support "must never repeat" answers.

## 6. Decision Log Threat Model

| # | Threat | Impact |
|---|--------|--------|
| DT-1 | Approval remembered without evidence | Unauthorized action appears approved |
| DT-2 | Denial forgotten | Denied action proceeds in future |
| DT-3 | Deferred decision treated as approved | Deferred work starts without lifecycle |
| DT-4 | Rejected decision silently reopened | Rejected item re-enters pipeline |
| DT-5 | Human override not recorded | Human authority decision lost |
| DT-6 | Accepted risk treated as resolved | Risk assumed mitigated without evidence |
| DT-7 | Permission decision treated as lifecycle approval | Scope escalation |
| DT-8 | Decision status overwritten without supersession | History lost |
| DT-9 | Decision contradicts event timeline | Inconsistent governance record |
| DT-10 | Decision contradicts artifact index | Evidence sources disagree |
| DT-11 | Decision contradicts memory snapshot | State sources disagree |
| DT-12 | Decision source missing | Unverifiable governance claim |
| DT-13 | Irreversible decision lost | Safety boundary forgotten |
| DT-14 | Unsafe lesson not carried forward | Mistake may be repeated |
| DT-15 | Chat memory overrides committed decision | Ephemeral source overwrites durable decision |

---

## 7. Core Decision Types

| Decision Type | Purpose |
|---------------|---------|
| `approval_decision` | Explicit approval of a scoped action |
| `denial_decision` | Explicit denial of a requested action |
| `deferral_decision` | Explicit deferral of work to a future phase |
| `rejection_decision` | Explicit rejection of a candidate or proposal |
| `human_override_decision` | Human authority overriding a system-level block or recommendation |
| `accepted_risk_decision` | Explicit acceptance of a known governance risk |
| `permission_decision` | Runtime permission grant/deny/escalation (future shell gate) |
| `blocked_decision` | Decision that an action is blocked by policy or condition |
| `rollback_decision` | Decision to roll back a previously performed action |
| `commit_decision` | Decision to create a governed commit |
| `push_decision` | Decision to perform a governed push |
| `lifecycle_closure_decision` | Decision to close a lifecycle |
| `must_never_repeat_decision` | Decision recording an unsafe pattern or lesson |

## 8. Required Decision Fields

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `decision_id` | string | yes | Stable unique identifier |
| `decision_type` | string | yes | Type from section 7 |
| `decision_status` | string | yes | Status from allowed values |
| `decision_timestamp` | timestamp | yes | When the decision was made |
| `source_phase` | string | yes | Phase that produced this decision |
| `source_artifact` | string | where available | Artifact providing evidence |
| `source_event` | string | where available | Timeline event ID linked to this decision |
| `source_commit` | string | where available | Commit hash providing evidence |
| `decision_maker` | string | yes | Who made the decision (human, agent, system) |
| `human_required` | boolean | yes | Whether human authority was required |
| `approved_scope` | string | for approvals | What was approved |
| `denied_scope` | string | for denials | What was denied |
| `deferred_scope` | string | for deferrals | What was deferred and target/review context |
| `rejected_scope` | string | for rejections | What was rejected and reason |
| `affected_files` | list | no | Files affected by this decision |
| `affected_agents` | list | no | Agents affected by this decision |
| `authorization_flags` | list | no | Flags set or cleared by this decision |
| `risk_level` | string | for risk decisions | Risk level (low/medium/high/critical) |
| `supersedes` | string | no | Decision ID this supersedes |
| `superseded_by` | string | no | Decision ID that supersedes this |
| `related_decisions` | list | no | Related decision IDs |
| `related_artifacts` | list | no | Related artifact IDs from 85B index |
| `related_events` | list | no | Related event IDs from 85C timeline |
| `evidence_level` | string | yes | Evidence level from 85B hierarchy |
| `safety_notes` | string | no | Safety-relevant notes |

## 9. Decision Status Values

| Status | Meaning |
|--------|---------|
| `proposed` | Decision has been proposed but not finalized |
| `approved` | Decision grants approval for a scoped action |
| `denied` | Decision denies a requested action |
| `deferred` | Decision defers work to a future phase |
| `rejected` | Decision rejects a candidate or proposal |
| `accepted_risk` | Decision accepts a known risk |
| `overridden` | Decision was overridden by human authority |
| `blocked` | Decision blocks an action due to policy or condition |
| `superseded` | Decision replaced by a later decision |
| `closed` | Decision's lifecycle is complete |
| `unknown` | Status not determined |

## 10. Decision Identity Rules

1. `decision_id` must be stable across decision log updates.
2. `decision_type` must be from known types or explicitly `unknown`.
3. `source_phase` must be recorded for every decision.
4. `source_artifact` or `source_commit` must be recorded where available.
5. Decision status must not be inferred from filename alone.
6. Decision identity must not depend on chat text alone.
7. Decision IDs must not collide within the decision log.

## 11. Decision Lifecycle Rules

1. Proposed decisions may become approved, denied, deferred, rejected, blocked, or accepted_risk.
2. Approved decisions may be superseded or closed but not silently changed.
3. Denied decisions remain denied unless explicitly superseded by a new decision.
4. Deferred decisions require target phase or review context.
5. Rejected decisions remain rejected unless explicitly reopened by an approved decision.
6. Accepted risks remain accepted_risk until mitigated or superseded.
7. Human overrides must record human authority and reason.
8. Permission decisions do not automatically become lifecycle approvals.
9. Superseded decisions retain their history (not deleted from log).
10. Closed decisions are immutable.

## 12. Decision Source-of-Truth Rules

1. Committed decision artifacts outrank chat memory.
2. PCAE command output outranks human final report when both exist.
3. Human final reports may seed decisions but must be reconciled with repo artifacts.
4. Conversation memory is secondary to all committed sources.
5. Derived summaries cannot supersede primary decision artifacts.
6. When sources conflict, the higher-priority source wins (per 85B precedence).

## 13. Provenance and Evidence Policy

Every decision must link to at least one evidence source:

| Evidence Source | Trust Level | When Used |
|-----------------|-------------|-----------|
| Committed decision artifact | Highest | Approval/adoption/review docs |
| Git commit hash | High | Commit/push decisions |
| PCAE command output | High | Health/check/lifecycle decisions |
| Timeline event | High | Event-linked decisions |
| Human report | Medium | Operator-provided decisions |
| Conversation memory | Lowest | Fallback only |

Decisions without provenance are flagged as unverified. Unverified decisions must not drive
next-action recommendations.

---

## 14. Relationship to Persistent Lifecycle Memory

- Decision log feeds `approval_record` in 85A memory.
- Decision log feeds `deferred_item_record` in 85A memory.
- Decision log feeds `risk_record` in 85A memory.
- Decision log feeds `next_safe_actions` in 85A memory.
- Decision log feeds `forbidden_actions` in 85A memory.
- Memory must cite decision log entries rather than infer decisions from prose.

## 15. Relationship to Artifact Index

- 85B artifact index locates decision artifacts (approval docs, review docs, execution docs).
- Decision log references artifact IDs and paths from the index.
- Decision log must preserve source-of-truth precedence from 85B.
- Missing decision artifacts must be classified as `missing`, not `approved`.

## 16. Relationship to Governance Event Timeline

- Decision log entries map to 85C governance events.
- `approval_decision` maps to `approval_granted` or `approval_denied` events.
- `permission_decision` maps to `permission_allowed`, `permission_blocked`, or `permission_escalated`.
- `commit_decision` maps to `commit_created` events.
- `push_decision` maps to `push_performed` events.
- `deferral_decision` maps to `item_deferred` events.
- `rejection_decision` maps to `item_rejected` events.
- Decision log captures the durable meaning of timeline events.

## 17. Relationship to Deferred Item Tracker

- `deferral_decision` creates or updates deferred item memory.
- `rejection_decision` preserves rejected state in the tracker.
- `blocked_decision` may create blocker or deferred item entries.
- Closure decisions must record why the deferred item is closed.
- Deferred items from the tracker (DF-1–DF-4, HY-1, IMPL-1–2, TEST-1) map to deferral decisions.

## 18. Relationship to Future Risk Register

- `accepted_risk_decision` feeds the future 85E risk register.
- Risk mitigation decisions update future risk status.
- `blocked_decision` may create high-risk entries in the register.
- `must_never_repeat_decision` may become permanent risk controls.
- Risk register will consume decision log entries as inputs.

---

## 19. Approval Decision Integration

- Approval decisions require explicit scope (what is approved, for which files/agents/actions).
- Approval decisions require allowed files or action classes.
- Approval decisions require source artifact reference.
- Approval decisions must distinguish authorized from performed.
- Approval decisions expire or supersede only by explicit decision.

## 20. Denial Decision Integration

- Denials must preserve denied scope.
- Denials must not be silently reopened.
- Denials should appear in forbidden-action answers when still relevant.
- Denied scope is explicitly recorded, not inferred from the absence of approval.

## 21. Deferred Decision Integration

- Deferrals require reason.
- Deferrals require target phase or review condition if known.
- Deferrals are not approvals — deferred work must go through its own lifecycle.
- Deferrals must be carried forward until explicitly closed.

## 22. Rejected Decision Integration

- Rejections require reason.
- Rejections remain rejected unless explicitly reopened by an approved decision.
- Rejected items must be visible in must-never-repeat or forbidden-action answers when relevant.
- Silent reopening of rejected items is a governance violation.

## 23. Human Override Decision Integration

- Human override requires human authority identification.
- Human override requires reason.
- Human override must not erase the original blocked/denied state.
- Human override must be auditable (who, when, why, what was overridden).
- Human override creates a new decision that supersedes the original, preserving both.

## 24. Accepted-Risk Decision Integration

- Accepted risk requires explicit risk level (low/medium/high/critical).
- Accepted risk requires rationale.
- Accepted risk is not risk mitigation — the risk remains active but acknowledged.
- Accepted risk must feed the future 85E risk register.
- Accepted risk decisions should be reviewed periodically.

## 25. Permission Decision Integration

- Permission decisions from the future shell gate are runtime decisions.
- Permission decisions do not automatically authorize lifecycle actions.
- `permission_allowed` means a command may run under the evaluated policy.
- `permission_blocked` means a command must not run.
- `permission_escalated` means human approval is required.
- Permission decisions are distinct from lifecycle approvals (85C section 22 distinction).

## 26. "Must Never Repeat" Decision Integration

- Captures unsafe patterns, governance violations, bypass exceptions, and lessons learned.
- Must preserve why the action must not repeat.
- Must link to source event, artifact, or commit.
- Must surface in project-state snapshot queries (85F future).
- Must be permanent unless explicitly superseded with documented rationale.
- Examples: force push to main, raw git push bypassing governance, adoption without review.

---

## 27. Query Model

### Q1: what_was_approved

| Field | Value |
|-------|-------|
| Required decision types | `approval_decision` |
| Artifact index dependencies | Approval artifacts |
| Timeline dependencies | `approval_granted` events |
| Memory model dependencies | `approval_record` |
| Expected answer shape | `[{decision_id, approved_scope, source_phase, status}]` |
| Required provenance | Artifact or commit reference |
| Safety caveats | Past approval may be expired or superseded |

### Q2: what_was_denied

| Field | Value |
|-------|-------|
| Required decision types | `denial_decision` |
| Artifact index dependencies | Decision artifacts |
| Timeline dependencies | `approval_denied` events |
| Memory model dependencies | `forbidden_actions` |
| Expected answer shape | `[{decision_id, denied_scope, source_phase, status}]` |
| Required provenance | Decision artifact |
| Safety caveats | Active denials appear in forbidden-action lists |

### Q3: what_was_deferred

| Field | Value |
|-------|-------|
| Required decision types | `deferral_decision` |
| Artifact index dependencies | Deferred item artifacts |
| Timeline dependencies | `item_deferred` events |
| Memory model dependencies | `deferred_item_record` |
| Expected answer shape | `[{decision_id, deferred_scope, target_phase, status}]` |
| Required provenance | Source artifact and phase |
| Safety caveats | Deferred does not mean approved |

### Q4: what_was_rejected

| Field | Value |
|-------|-------|
| Required decision types | `rejection_decision` |
| Artifact index dependencies | Decision artifacts |
| Timeline dependencies | `item_rejected` events |
| Memory model dependencies | `decision_record` |
| Expected answer shape | `[{decision_id, rejected_scope, reason, status}]` |
| Required provenance | Rejection reason and source |
| Safety caveats | Rejected items must not be silently reintroduced |

### Q5: what_was_overridden

| Field | Value |
|-------|-------|
| Required decision types | `human_override_decision` |
| Artifact index dependencies | Override artifacts |
| Timeline dependencies | Related approval/denial events |
| Memory model dependencies | `decision_record` |
| Expected answer shape | `[{decision_id, overridden_decision, reason, authority}]` |
| Required provenance | Human authority and reason |
| Safety caveats | Override must not erase original blocked/denied state |

### Q6: what_risk_was_accepted

| Field | Value |
|-------|-------|
| Required decision types | `accepted_risk_decision` |
| Artifact index dependencies | Risk artifacts |
| Timeline dependencies | `risk_identified` events |
| Memory model dependencies | `risk_record` |
| Expected answer shape | `[{decision_id, risk_level, rationale, status}]` |
| Required provenance | Risk source artifact |
| Safety caveats | Accepted risk is not mitigation |

### Q7: what_permission_decisions_were_made

| Field | Value |
|-------|-------|
| Required decision types | `permission_decision` |
| Artifact index dependencies | Future decision artifacts |
| Timeline dependencies | `permission_allowed/blocked/escalated` events |
| Memory model dependencies | Permission history (future) |
| Expected answer shape | `[{decision_id, command_class, decision_status, policy_basis}]` |
| Required provenance | Policy basis |
| Safety caveats | Permission allowed ≠ lifecycle approval |

### Q8: what_requires_human_review

| Field | Value |
|-------|-------|
| Required decision types | All where `human_required=true` |
| Artifact index dependencies | All related artifacts |
| Timeline dependencies | Events requiring human review |
| Memory model dependencies | Items flagged for human review |
| Expected answer shape | `[{item, reason, urgency, recommended_phase}]` |
| Required provenance | Source of human-review requirement |
| Safety caveats | Advisory only |

### Q9: what_can_be_safely_done_next

| Field | Value |
|-------|-------|
| Required decision types | All active approvals, active blockers, active deferrals |
| Artifact index dependencies | Current artifacts |
| Timeline dependencies | Latest events |
| Memory model dependencies | `next_safe_actions`, `lifecycle_state` |
| Expected answer shape | `[{action, safety_level, prerequisites, provenance}]` |
| Required provenance | Current state evidence |
| Safety caveats | Advisory only; does not authorize execution |

### Q10: what_must_never_be_repeated

| Field | Value |
|-------|-------|
| Required decision types | `must_never_repeat_decision`, `rejection_decision` (permanent) |
| Artifact index dependencies | Decision and risk artifacts |
| Timeline dependencies | Failed/rejected/blocked events |
| Memory model dependencies | `forbidden_actions` |
| Expected answer shape | `[{forbidden_action, reason, source_decision, source_phase}]` |
| Required provenance | Source decision and evidence |
| Safety caveats | Enforcement is separate from reporting |

---

## 28. Decision Update Rules

1. Decision updates only after phase completion or explicit decision capture phase.
2. Decision update must cite artifact, command output, event, or commit.
3. Decision log must not infer approval from plan text.
4. Decision log must preserve denied/deferred/rejected states.
5. Decision log must not delete superseded decisions (mark `superseded`, retain entry).
6. Decision log must preserve human override history.
7. Decision log must be idempotent (same inputs produce same decision log).
8. Decision log must distinguish authorization from performance.
9. Permission decisions must not be treated as lifecycle approvals unless policy explicitly says so.
10. Decision updates must not create new authorization.
11. Decision log must flag decisions without provenance as unverified.
12. Must-never-repeat decisions are permanent unless explicitly superseded with rationale.

---

## 29. Validation Rules

| # | Rule |
|---|------|
| V-1 | `decision_id` required for every decision |
| V-2 | `decision_type` required and must be from known types |
| V-3 | `decision_status` required and must be from allowed values |
| V-4 | `source_phase` required |
| V-5 | `source_artifact` or `source_commit` required where available |
| V-6 | `decision_type` must be known or explicitly `unknown` |
| V-7 | Approval requires explicit scope |
| V-8 | Denial requires explicit scope |
| V-9 | Deferral requires reason |
| V-10 | Deferral requires target phase or review context if known |
| V-11 | Rejection requires reason |
| V-12 | Human override requires reason and authority |
| V-13 | Accepted risk requires risk level |
| V-14 | Permission decision requires command/action context when implemented |
| V-15 | Approved does not imply performed |
| V-16 | Permission allowed does not imply lifecycle approval |
| V-17 | Deferred does not imply approved |
| V-18 | Rejected remains rejected unless explicitly reopened |
| V-19 | Denied remains denied unless explicitly superseded |
| V-20 | Accepted risk is not mitigation |
| V-21 | Decision log does not authorize execution |
| V-22 | Decision log does not authorize backend invocation |
| V-23 | Decision log does not authorize adoption |
| V-24 | Decision log does not authorize commit/push |
| V-25 | Decision log links to event timeline when available |
| V-26 | Decision log links to artifact index when available |
| V-27 | Decision log feeds memory but does not override task contract |
| V-28 | Future implementation requires tests |
| V-29 | Design-only phase creates no machine-readable decision log |
| V-30 | No source/test changes in 85D |
| V-31 | No phase beyond 85D started in this phase |
| V-32 | `decision_maker` required for every decision |
| V-33 | `human_required` required for every decision |
| V-34 | `evidence_level` required for every decision |
| V-35 | Superseded decisions must retain history |
| V-36 | Closed decisions are immutable |
| V-37 | Must-never-repeat decisions are permanent unless explicitly superseded |
| V-38 | Decision IDs must not collide |
| V-39 | `supersedes`/`superseded_by` must form a valid chain |
| V-40 | Human override must not erase original blocked/denied state |
| V-41 | Unverified decisions must not drive next-action recommendations |
| V-42 | No `.pcae` decision storage created in 85D |

## 30. Failure Cases

| # | Failure | Impact |
|---|---------|--------|
| F-1 | Approval recorded without scope | Unbounded approval |
| F-2 | Approval recorded without artifact | Unverifiable approval |
| F-3 | Denial forgotten | Denied action proceeds |
| F-4 | Deferral treated as approval | Deferred work starts without lifecycle |
| F-5 | Rejection silently reopened | Rejected item re-enters pipeline |
| F-6 | Human override missing reason | Override unauditable |
| F-7 | Accepted risk treated as mitigated | Risk assumed resolved |
| F-8 | Permission allowed treated as lifecycle approval | Scope escalation |
| F-9 | Decision log contradicts timeline | Inconsistent governance record |
| F-10 | Decision log contradicts artifact index | Evidence sources disagree |
| F-11 | Decision log contradicts memory model | State sources disagree |
| F-12 | Decision source missing | Unverifiable governance claim |
| F-13 | Decision implementation attempted in design phase | Governance boundary violated |
| F-14 | Tests skipped in implementation phase | Implementation without verification |
| F-15 | Must-never-repeat lesson lost | Unsafe pattern may recur |

---

## 31. Future Implementation Plan

Candidate future phases after this design:

| Phase | Name | Scope |
|-------|------|-------|
| 85D.1 | Decision Log Integration Implementation Plan | Detailed implementation spec |
| 85D.2 | Read-Only Decision Log Prototype | First read-only decision query command |
| 85D.3 | Decision Log Tests | Test suite for decision log model |

No task contracts are created for these phases in 85D.

## 32. Future Test Coverage

No tests are added in 85D because this is design-only. Future implementation must test:

| Test Area | Coverage Target |
|-----------|----------------|
| Decision type parsing | Known types classified correctly |
| Decision status transitions | Lifecycle rules enforced |
| Approval scope preservation | Scope not silently broadened |
| Denial preservation | Denied actions remain denied |
| Deferred/rejected carry-forward | Status preserved until explicit change |
| Human override audit trail | Authority, reason, and original state preserved |
| Accepted-risk classification | Risk level and rationale preserved |
| Permission decision classification | Request/allow/block/escalate distinguished |
| Must-never-repeat query output | Permanent lessons returned correctly |
| Artifact index linkage | Decisions reference valid artifact IDs |
| Timeline linkage | Decisions map to valid timeline events |
| Memory model linkage | Decisions feed correct memory entities |
| Idempotent decision extraction | Same input produces same decision log |

## 33. Example Decision Log Entries

Illustrative markdown only, not an executable format:

```
decision_id: approve-83j-adoption-candidates
decision_type: approval_decision
decision_status: approved
source_phase: 83J
source_artifact: docs/MULTI_AGENT_ADOPTION_APPROVAL.md
source_event: approval-83j-granted
decision_maker: operator
human_required: true
approved_scope: AC-1, AC-2, AC-3 documentation adoption only
affected_files:
  - docs/MULTI_AGENT_CONTRACT_INSTANCE_DRY_RUN.md
  - docs/AGENT_ASSIGNMENT_APPROVAL.md
evidence_level: repo_committed_artifact
safety_notes: adoption execution not performed until 83K

decision_id: defer-84-memory-roadmap-to-85
decision_type: deferral_decision
decision_status: closed
source_phase: 84L
source_artifact: docs/ROADMAP_RECONCILIATION_PHASE_85_PLAN.md
source_event: roadmap-reconciliation-completed
decision_maker: operator
human_required: true
deferred_scope: original 84 persistent memory/project intelligence roadmap moved to 85A-85F
evidence_level: repo_committed_artifact

decision_id: reject-rj1-through-rj4
decision_type: rejection_decision
decision_status: rejected
source_phase: 83I
source_artifact: docs/MULTI_AGENT_ADOPTION_REVIEW.md
decision_maker: operator
human_required: true
rejected_scope: RJ-1 through RJ-4 low-impact clarity items
safety_notes: rejected items must not be silently reintroduced

decision_id: permission-broker-future-direction
decision_type: permission_decision
decision_status: deferred
source_phase: 85C
source_artifact: docs/GOVERNANCE_EVENT_TIMELINE_DESIGN.md
decision_maker: operator
human_required: true
deferred_scope: PCAE as permission broker / shell gate
safety_notes: future_direction_only_not_implemented

decision_id: never-repeat-force-push
decision_type: must_never_repeat_decision
decision_status: closed
source_phase: governance_invariant
decision_maker: system
human_required: false
safety_notes: force push to main is permanently forbidden by governance policy
```

---

## 34. Recommended Next Phase

**85E — Risk Register**

85E should define the risk register design, tracking active, deferred, accepted, mitigated,
and blocked governance risks. It builds on 85A (risk memory entities), 85B (risk artifact
indexing), 85C (risk events in timeline), and 85D (accepted-risk and blocked decisions).

---

## Decision Log Integration Identity

| Field | Value |
|-------|-------|
| decision_log_integration_name | pcae_decision_log_integration |
| decision_log_integration_version | 0.1 |
| decision_log_integration_status | draft_documented |
| decision_log_integration_implementation_status | not_started |

## Authorization Flags for 85D

| Flag | Value |
|------|-------|
| backend_invocation_performed | false |
| new_prompts_sent | false |
| new_capture_performed | false |
| new_intake_performed | false |
| new_adoption_review_performed | false |
| new_adoption_approval_performed | false |
| new_adoption_execution_performed | false |
| repo_mutation_authorized | true_for_decision_log_docs_status_only |
| readme_mutation_authorized | false |
| source_mutation_authorized | false |
| test_mutation_authorized | false |
| docs_real_captured_tasks_mutation_authorized | false |
| persistent_memory_implementation_authorized | false |
| artifact_index_implementation_authorized | false |
| timeline_implementation_authorized | false |
| decision_log_implementation_authorized | false |
| permission_broker_implementation_authorized | false |
| shell_gate_implementation_authorized | false |
| risk_register_implementation_authorized | false |
| project_snapshot_implementation_authorized | false |
| phase_85e_task_contract_authorized | false |
| commit_authorized | false |
| push_authorized | false |
| execution_authorized | false |
