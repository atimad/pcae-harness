# Governance Event Timeline Design

## 1. Purpose

Define a chronological event model for PCAE governance actions: approvals, captures, checks,
commits, pushes, blockers, deferrals, closures, and permission decisions. The timeline adds
temporal ordering and causal linkage to the memory model (85A) and artifact index (85B),
enabling PCAE to reconstruct what happened, when, why, and with what evidence.

## 2. Scope

Design only. This artifact defines event types, fields, ordering rules, causality,
provenance, and query targets. It does not implement timeline storage, create
machine-readable files, or add tests.

## 3. Non-Goals

- Implementing timeline storage or CLI commands.
- Creating `.pcae` timeline directories or files.
- Adding tests.
- Modifying source code, README, or existing artifacts.
- Backend invocation, prompt sending, capture, intake, or adoption.
- Implementing the permission broker or shell gate (future direction only).

## 4. Motivation from 85A and 85B

The 85A memory model defines what PCAE should remember (entities, fields, queries). The 85B
artifact index defines how PCAE finds evidence (categories, metadata, freshness). Neither
captures *when* events occurred or *what caused what*. The timeline fills this gap:

- **85A** answers: "What is the current state?" → The timeline answers: "How did we get here?"
- **85B** answers: "Where is the evidence?" → The timeline answers: "When was it produced?"
- **85C** answers: "What happened in what order, and what caused what?"

Together, 85A + 85B + 85C enable project-state reconstruction from committed artifacts.

---

## 5. Governance Event Timeline Design Principles

1. Timeline records observed and authorized governance events, not permission by itself.
2. Timeline does not authorize execution.
3. Timeline does not authorize backend invocation.
4. Timeline does not authorize adoption.
5. Timeline does not authorize commit or push.
6. Timeline must preserve event order.
7. Timeline must preserve causality (what caused what).
8. Timeline must link every event to provenance (artifact, commit, or command output).
9. Timeline must distinguish observed, approved, performed, blocked, deferred, rejected, failed, and superseded.
10. Timeline must support offline audit.
11. Timeline must support project-state reconstruction.
12. Timeline must support next-safe-action analysis without performing actions.

## 6. Governance Event Threat Model

| # | Threat | Impact |
|---|--------|--------|
| GT-1 | Event omitted from timeline | Governance history incomplete |
| GT-2 | Event recorded out of order | Causal analysis incorrect |
| GT-3 | Approval event recorded without artifact | Unverifiable approval claim |
| GT-4 | Performed action recorded without approval | Unauthorized action appears legitimate |
| GT-5 | Blocked event forgotten | Blocked action proceeds in future |
| GT-6 | Deferred event treated as resolved | Deferred work starts without approval |
| GT-7 | Rejected event silently reintroduced | Previously rejected item re-enters pipeline |
| GT-8 | Commit/push event missing evidence | Phase completion unverifiable |
| GT-9 | Backend invocation event missing capture metadata | Capture chain broken |
| GT-10 | Permission decision not audited | Governance gap in permission history |
| GT-11 | Human approval not recorded | Human decision lost between sessions |
| GT-12 | Timeline contradicts artifact index | Evidence sources disagree |
| GT-13 | Timeline contradicts memory snapshot | State sources disagree |
| GT-14 | Stale timeline used for next action | Outdated history drives current decisions |
| GT-15 | Event causality inferred incorrectly | Wrong causal chain leads to wrong conclusions |

---

## 7. Core Event Types

| Event Type | Purpose |
|------------|---------|
| `phase_started` | A phase began |
| `phase_completed` | A phase finished |
| `artifact_created` | A governance artifact was created |
| `artifact_updated` | An existing artifact was modified |
| `approval_requested` | Approval was requested for an action |
| `approval_granted` | Approval was granted |
| `approval_denied` | Approval was denied |
| `authorization_flag_set` | An authorization flag was set to true |
| `authorization_flag_cleared` | An authorization flag was set to false |
| `backend_invocation_approved` | Backend invocation was approved for future execution |
| `backend_invocation_performed` | Backend was actually invoked |
| `prompt_package_created` | A prompt package was created |
| `prompt_sent` | A prompt was sent to a backend |
| `capture_created` | Backend output was captured |
| `output_intake_completed` | Captured output was classified |
| `adoption_candidate_created` | An adoption candidate was identified |
| `adoption_approved` | An adoption candidate was approved |
| `adoption_executed` | An adoption candidate was executed |
| `item_deferred` | An item was deferred to a future phase |
| `item_rejected` | An item was rejected |
| `blocker_detected` | A blocking condition was identified |
| `blocker_resolved` | A blocking condition was resolved |
| `risk_identified` | A governance risk was identified |
| `risk_mitigated` | A governance risk was mitigated |
| `commit_created` | A governed commit was created |
| `push_performed` | A governed push was performed |
| `handoff_refreshed` | Handoff state was refreshed |
| `bootstrap_profile_updated` | Bootstrap profile was updated |
| `permission_requested` | An agent requested permission for an action |
| `permission_allowed` | Permission was granted for an action |
| `permission_blocked` | Permission was denied for an action |
| `permission_escalated` | Permission decision was escalated to human |
| `lifecycle_closed` | A lifecycle was formally closed |

## 8. Required Event Fields

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `event_id` | string | yes | Stable unique identifier |
| `event_type` | string | yes | Type from section 7 |
| `event_status` | string | yes | Status from allowed values |
| `event_timestamp` | timestamp | yes | When the event occurred |
| `source_phase` | string | yes | Phase that produced this event |
| `source_artifact` | string | where available | Artifact providing evidence |
| `source_commit` | string | where available | Commit hash providing evidence |
| `actor` | string | yes | Who/what produced the event (human, agent, system) |
| `agent_id` | string | no | Agent involved, if applicable |
| `human_required` | boolean | yes | Whether human review/approval was required |
| `authorization_required` | boolean | yes | Whether governance authorization was required |
| `authorization_status` | string | yes | authorized/unauthorized/not_applicable |
| `affected_files` | list | no | Files affected by this event |
| `related_artifacts` | list | no | Artifact IDs related to this event |
| `related_events` | list | no | Event IDs related to this event |
| `causal_parent_events` | list | no | Event IDs that causally preceded this event |
| `evidence_level` | string | yes | Evidence level from 85B hierarchy |
| `freshness_status` | string | yes | Freshness from 85B rules |
| `safety_notes` | string | no | Safety-relevant notes |

### Event Status Values

| Status | Meaning |
|--------|---------|
| `observed` | Event was observed/recorded |
| `requested` | Action was requested but not yet decided |
| `approved` | Action was approved |
| `denied` | Action was denied |
| `performed` | Action was performed |
| `blocked` | Action was blocked by a condition |
| `deferred` | Action was deferred to a future phase |
| `rejected` | Action was rejected |
| `failed` | Action was attempted but failed |
| `superseded` | Event was superseded by a later event |
| `closed` | Event's lifecycle is complete |
| `unknown` | Status not determined |

## 9. Event Identity Rules

1. `event_id` must be stable across timeline updates.
2. `event_type` must be from known event types or explicitly `unknown`.
3. `source_phase` must be recorded for every event.
4. `source_artifact` or `source_commit` must be recorded where available.
5. Event identity must not depend on chat text alone.
6. Event IDs must not collide within a timeline.

## 10. Event Ordering Rules

Events must follow these ordering constraints:

| Predecessor | Successor | Rule |
|-------------|-----------|------|
| `phase_started` | `phase_completed` | Start precedes completion |
| `approval_requested` | `approval_granted` or `approval_denied` | Request precedes decision |
| `approval_granted` | Approved action event | Approval precedes action |
| `prompt_package_created` | `prompt_sent` | Package precedes send |
| `prompt_sent` | `capture_created` | Send precedes capture |
| `capture_created` | `output_intake_completed` | Capture precedes intake |
| `output_intake_completed` | `adoption_candidate_created` | Intake precedes candidate |
| `adoption_approved` | `adoption_executed` | Approval precedes execution |
| `commit_created` | `push_performed` | Commit precedes push |
| `blocker_detected` | `blocker_resolved` | Detection precedes resolution |
| `permission_requested` | `permission_allowed` or `permission_blocked` or `permission_escalated` | Request precedes decision |

Ordering violations indicate timeline corruption or missing events.

## 11. Causality and Dependency Rules

1. A performed action must link to an approval event or an explicitly documented no-approval rule.
2. A blocked action must link to a `blocker_detected` event or policy reference.
3. A deferred item must link to the source artifact and its target/review status.
4. A rejected item must link to a rejection reason and decision event.
5. A commit event must link to changed files and the phase that produced it.
6. A push event must link to commit lineage and origin count.
7. A permission decision must link to the request event and the policy basis.
8. Causal chains must be acyclic (no circular dependencies).
9. Missing causal parents indicate an incomplete timeline.

## 12. Provenance and Evidence Policy

Every timeline event must link to at least one evidence source:

| Evidence Source | Trust Level | When Used |
|-----------------|-------------|-----------|
| Committed artifact | Highest | Phase artifacts in docs/, tasks/ |
| Git commit hash | High | Commit/push events |
| PCAE command output | High | Health/check/lifecycle events |
| Human report | Medium | Operator-provided summaries |
| Conversation memory | Lowest | Fallback when no committed source exists |

Events without provenance are flagged as unverified. Unverified events must not be used
as the sole basis for next-action recommendations.

---

## 13. Lifecycle Transition Events

Key lifecycle transitions map to event pairs:

| Transition | Start Event | End Event |
|------------|-------------|-----------|
| Phase execution | `phase_started` | `phase_completed` |
| Lifecycle opening | `phase_started` (first phase) | — |
| Lifecycle closure | — | `lifecycle_closed` |
| Health baseline | `phase_started` | `artifact_created` (baseline doc) |
| Handoff refresh | `phase_started` | `handoff_refreshed` |

## 14. Approval Events

| Event | Prerequisite | Produces |
|-------|-------------|----------|
| `approval_requested` | Active task contract | Pending approval state |
| `approval_granted` | `approval_requested` | Authorization for specific action |
| `approval_denied` | `approval_requested` | Block on requested action |

Approval events must reference the approval artifact and scope. An `approval_granted`
event does not authorize actions beyond its stated scope.

## 15. Authorization Flag Events

| Event | Prerequisite | Effect |
|-------|-------------|--------|
| `authorization_flag_set` | Explicit governance decision | Flag becomes true |
| `authorization_flag_cleared` | Phase completion or explicit reset | Flag becomes false |

Flag events must record `flag_name`, `flag_value`, `flag_source`, and `flag_reason`.
Authorization flags default to false; setting a flag to true requires explicit evidence.

## 16. Backend Invocation and Prompt Events

| Event | Prerequisite | Evidence |
|-------|-------------|---------|
| `backend_invocation_approved` | Approval chain complete | Approval artifact |
| `prompt_package_created` | Active contract with prompt scope | Package artifact |
| `prompt_sent` | `prompt_package_created`, `backend_invocation_approved` | Send record |
| `backend_invocation_performed` | `prompt_sent` | Capture metadata |

Backend invocation events require the full approval chain. An invocation event without
a preceding approval event indicates a governance violation.

## 17. Capture/Intake/Adoption Events

| Event | Prerequisite | Evidence |
|-------|-------------|---------|
| `capture_created` | `backend_invocation_performed` | Capture artifact with SHA256 |
| `output_intake_completed` | `capture_created` | Intake artifact with classification |
| `adoption_candidate_created` | `output_intake_completed` | Candidate artifact |
| `adoption_approved` | `adoption_candidate_created`, human approval | Approval artifact |
| `adoption_executed` | `adoption_approved` | Execution artifact |

The capture → intake → adoption chain must be unbroken. Missing links indicate
governance gaps.

## 18. Deferred/Rejected/Blocker/Risk Events

| Event | Evidence | Preservation Rule |
|-------|----------|-------------------|
| `item_deferred` | Source artifact, target phase | Must persist until explicitly closed |
| `item_rejected` | Rejection reason, decision record | Must persist; silent reopening is a violation |
| `blocker_detected` | Blocking condition, source | Must persist until `blocker_resolved` |
| `blocker_resolved` | Resolution evidence | Must link to original `blocker_detected` |
| `risk_identified` | Risk source artifact | Must persist until mitigated or accepted |
| `risk_mitigated` | Mitigation evidence | Must link to original `risk_identified` |

Deferred and rejected events are never automatically removed from the timeline.

## 19. Commit/Push Events

| Event | Evidence | Fields |
|-------|----------|--------|
| `commit_created` | Git commit hash | commit_type (implementation/completion), changed_files, phase |
| `push_performed` | Push record | push_method (governed/raw/force), origin_count, push_status |

Commit events must distinguish implementation commits from completion commits.
Push events must record whether governed `pcae push` was used.

## 20. Handoff/Bootstrap Events

| Event | Evidence | Fields |
|-------|----------|--------|
| `handoff_refreshed` | Handoff refresh artifact | refresh_status, blocker_count, warning_count |
| `bootstrap_profile_updated` | Bootstrap profile documentation | default_test_command, serial_exceptions |

## 21. Permission Decision Events

| Event | Purpose |
|-------|---------|
| `permission_requested` | An agent requested permission for an action |
| `permission_allowed` | Permission was granted |
| `permission_blocked` | Permission was denied |
| `permission_escalated` | Decision was escalated to human authority |

### Permission Decision Event Fields

| Field | Type | Purpose |
|-------|------|---------|
| `command_class` | string | Class of command (read, write, shell, backend, commit, push) |
| `requested_command_summary` | string | Summary of what was requested |
| `requested_by_agent` | string | Agent that made the request |
| `active_task_contract` | string | Active task contract at time of request |
| `lifecycle_state` | string | Lifecycle state at time of request |
| `allowed_files` | list | Files allowed by active contract |
| `forbidden_files` | list | Files forbidden by active contract |
| `policy_basis` | string | Policy that informed the decision |
| `risk_boundary` | string | Risk classification of the requested action |
| `human_escalation_required` | boolean | Whether human review was required |
| `decision_recorded_by` | string | Who/what recorded the decision |
| `decision_artifact` | string | Artifact recording the decision |

---

## 22. Future Direction: PCAE as Permission Broker / Shell Gate

> `future_direction_only=true`
> `permission_broker_implementation_status=not_started`
> `shell_gate_implementation_status=not_started`

### Current Model

Today, two separate permission layers exist:

1. **Claude CLI runtime permissions**: The Claude CLI asks the human operator whether a shell
   command may run. The human approves or denies each command individually.
2. **PCAE governance approval**: PCAE separately records task contracts, checks repository and
   governance state, and validates that actions comply with governed lifecycle rules.

These layers operate independently. The human must mentally cross-reference PCAE governance
rules with each Claude permission prompt.

### Future PCAE-Native Model

In the future PCAE-native model, agents would ask a PCAE wrapper or gate before shell
execution:

1. Agent requests command/action permission from PCAE gate.
2. PCAE evaluates:
   - Active task contract (allowed/forbidden files, allowed operations)
   - Lifecycle state (current phase, authorization flags)
   - Approved files and forbidden files
   - Command class (read, write, shell, backend, commit, push)
   - Backend invocation state (is invocation approved?)
   - Governance policy (what is the current enforcement mode?)
   - Risk boundary (is this a high-risk action?)
3. PCAE allows, blocks, or escalates to human.
4. Human approval remains required for high-risk boundaries.
5. PCAE records the decision as an audit event in the timeline.
6. Agent executes only if PCAE allows.

### Important Distinction

| Layer | Question | Authority |
|-------|----------|-----------|
| Claude permission | "Can I run this shell command now?" | Human operator |
| PCAE approval | "Is this action authorized by the governed lifecycle?" | PCAE governance policy |

### Long-Term Goal

The human remains the ultimate authority, but PCAE mechanically enforces policy so the human
does not need to manually remember every boundary during agent execution. PCAE becomes a
permission broker that:

- Reduces human cognitive load during agent sessions.
- Prevents governance violations before they occur (not just after).
- Records every permission decision as audit evidence.
- Supports offline review of permission decision history.

### Implementation Note

This subsection describes a future direction only. No permission broker, shell gate, or
enforcement mechanism is implemented in 85C. The permission decision event types defined in
section 21 prepare the timeline model for future integration, but they do not authorize or
enforce anything today.

---

## 23. Query Model

### Q1: what_happened_in_phase

| Field | Value |
|-------|-------|
| Required event types | All events with matching `source_phase` |
| Artifact index dependencies | Artifacts created/updated in the phase |
| Memory model dependencies | `phase_record` entity |
| Expected answer shape | `[{event_id, event_type, event_status, event_timestamp}]` |
| Required provenance | Each event must have source_artifact or source_commit |
| Safety caveats | Timeline is observational, not authorization |

### Q2: what_changed_since_phase

| Field | Value |
|-------|-------|
| Required event types | All events after the specified phase |
| Artifact index dependencies | Freshness changes since the phase |
| Memory model dependencies | Phase history comparison |
| Expected answer shape | `{new_events_count, event_types, affected_phases}` |
| Required provenance | Each event must have provenance |
| Safety caveats | Changes do not imply new authorization |

### Q3: what_was_approved

| Field | Value |
|-------|-------|
| Required event types | `approval_granted`, `authorization_flag_set` |
| Artifact index dependencies | Approval artifacts |
| Memory model dependencies | `approval_record`, `authorization_flag_record` |
| Expected answer shape | `[{approval_id, approved_action, scope, artifact}]` |
| Required provenance | Each approval must reference artifact |
| Safety caveats | Past approval may be expired or superseded |

### Q4: what_was_blocked

| Field | Value |
|-------|-------|
| Required event types | `blocker_detected`, `approval_denied`, `permission_blocked` |
| Artifact index dependencies | Risk and blocker artifacts |
| Memory model dependencies | `risk_record`, `deferred_item_record` |
| Expected answer shape | `[{blocker, condition, source_phase, resolved}]` |
| Required provenance | Each blocker must cite source |
| Safety caveats | Structural signals vs substantive blockers must be distinguished |

### Q5: what_was_deferred

| Field | Value |
|-------|-------|
| Required event types | `item_deferred` |
| Artifact index dependencies | Deferred item artifacts |
| Memory model dependencies | `deferred_item_record` |
| Expected answer shape | `[{item_id, item_type, target_phase, status}]` |
| Required provenance | Each deferred item must cite source artifact |
| Safety caveats | Deferred does not mean approved for implementation |

### Q6: what_was_rejected

| Field | Value |
|-------|-------|
| Required event types | `item_rejected`, `approval_denied` |
| Artifact index dependencies | Decision artifacts |
| Memory model dependencies | `decision_record` |
| Expected answer shape | `[{item_id, rejection_reason, source_phase}]` |
| Required provenance | Rejection must cite decision record |
| Safety caveats | Rejected items must not be silently reintroduced |

### Q7: what_was_committed

| Field | Value |
|-------|-------|
| Required event types | `commit_created` |
| Artifact index dependencies | Commit evidence |
| Memory model dependencies | `commit_record` |
| Expected answer shape | `[{commit_hash, commit_type, phase, changed_files}]` |
| Required provenance | Commit hash required |
| Safety caveats | Commit does not imply push |

### Q8: what_was_pushed

| Field | Value |
|-------|-------|
| Required event types | `push_performed` |
| Artifact index dependencies | Push evidence |
| Memory model dependencies | `push_record` |
| Expected answer shape | `[{push_method, origin_count, phase}]` |
| Required provenance | Push record required |
| Safety caveats | Only governed push should be used |

### Q9: what_permission_decisions_were_made

| Field | Value |
|-------|-------|
| Required event types | `permission_requested`, `permission_allowed`, `permission_blocked`, `permission_escalated` |
| Artifact index dependencies | Decision artifacts (future) |
| Memory model dependencies | Permission history (future) |
| Expected answer shape | `[{request, decision, policy_basis, agent, command_class}]` |
| Required provenance | Decision must cite policy basis |
| Safety caveats | Permission allowed ≠ lifecycle authorization unless policy explicitly maps them |

### Q10: what_can_be_safely_done_next

| Field | Value |
|-------|-------|
| Required event types | Latest phase events, authorization flag events, blocker events |
| Artifact index dependencies | Current artifacts, freshness status |
| Memory model dependencies | `next_action_record`, `lifecycle_state` |
| Expected answer shape | `[{action, safety_level, prerequisites, provenance}]` |
| Required provenance | Must cite current state evidence |
| Safety caveats | Advisory only; does not authorize execution |

### Q11: what_must_never_be_repeated

| Field | Value |
|-------|-------|
| Required event types | `item_rejected`, `blocker_detected` (unresolved), failed events |
| Artifact index dependencies | Decision and risk artifacts |
| Memory model dependencies | `forbidden_actions` |
| Expected answer shape | `[{forbidden_action, reason, source_event, source_phase}]` |
| Required provenance | Must cite decision or risk record |
| Safety caveats | Enforcement is separate from reporting |

---

## 24. Timeline Update Rules

1. Timeline updates only after phase completion or explicit event capture phase.
2. Timeline event must cite artifact, command output, or commit.
3. Timeline must not infer approval from plan text.
4. Timeline must preserve rejected/deferred/blocked events.
5. Timeline must not delete superseded events (mark `superseded`, retain entry).
6. Timeline must preserve chronological order.
7. Timeline must be idempotent (same inputs produce same timeline).
8. Timeline must distinguish observed state from authorized action.
9. Permission events must not be treated as authorization unless PCAE policy explicitly allows.
10. Timeline updates must not create new authorization.
11. Timeline must flag events without provenance as unverified.
12. Timeline must support incremental updates (append, not rebuild).

---

## 25. Validation Rules

| # | Rule |
|---|------|
| V-1 | `event_id` required for every timeline entry |
| V-2 | `event_type` required and must be from known types |
| V-3 | `event_status` required and must be from allowed values |
| V-4 | `source_phase` required |
| V-5 | `source_artifact` or `source_commit` required where available |
| V-6 | `event_timestamp` or ordering anchor required |
| V-7 | `event_type` must be known or explicitly `unknown` |
| V-8 | `approval_requested` must precede `approval_granted` |
| V-9 | `approval_granted` must precede approved action |
| V-10 | `prompt_package_created` must precede `prompt_sent` |
| V-11 | `prompt_sent` must precede `capture_created` |
| V-12 | `capture_created` must precede `output_intake_completed` |
| V-13 | `output_intake_completed` must precede `adoption_candidate_created` |
| V-14 | `adoption_approved` must precede `adoption_executed` |
| V-15 | `commit_created` must precede `push_performed` |
| V-16 | `blocker_detected` must precede `blocker_resolved` |
| V-17 | Rejected item events must be preserved |
| V-18 | Deferred item events must be preserved |
| V-19 | Blocked events must be preserved |
| V-20 | Performed action must link to approval or allowed no-approval rule |
| V-21 | Permission decision must link to request and policy basis |
| V-22 | Permission allowed does not imply lifecycle authorization unless explicitly allowed |
| V-23 | Timeline does not authorize execution |
| V-24 | Timeline does not authorize adoption |
| V-25 | Timeline does not authorize commit/push |
| V-26 | Future permission broker note is not implementation |
| V-27 | Design-only phase creates no machine-readable timeline |
| V-28 | Future implementation requires tests |
| V-29 | No source/test changes in 85C |
| V-30 | No phase beyond 85C started in this phase |
| V-31 | No `.pcae` timeline storage created in 85C |
| V-32 | `actor` required for every event |
| V-33 | `human_required` required for every event |
| V-34 | `authorization_required` required for every event |
| V-35 | `evidence_level` required for every event |
| V-36 | Causal chains must be acyclic |
| V-37 | Missing causal parent events must be flagged |
| V-38 | Events without provenance must be flagged as unverified |
| V-39 | `backend_invocation_performed` must be preceded by `backend_invocation_approved` |
| V-40 | `adoption_executed` must be preceded by full capture → intake → approval chain |
| V-41 | `push_performed` must record push_method |
| V-42 | Permission broker/shell gate fields are design-only, not enforced |

## 26. Failure Cases

| # | Failure | Impact |
|---|---------|--------|
| F-1 | Event missing source artifact | Unverifiable governance claim |
| F-2 | Event missing source phase | Event cannot be placed in history |
| F-3 | Approval/action order inverted | Governance chain violated |
| F-4 | Performed action without approval | Unauthorized action in record |
| F-5 | Push event without commit evidence | Push unverifiable |
| F-6 | Capture event without prompt event | Capture chain broken |
| F-7 | Adoption execution without approval event | Unapproved adoption |
| F-8 | Blocked event forgotten | Blocked action may proceed |
| F-9 | Deferred item treated as resolved | Premature implementation |
| F-10 | Rejected item reopened silently | Previously rejected work re-enters pipeline |
| F-11 | Permission allowed treated as blanket authorization | Scope exceeded |
| F-12 | Permission broker implemented in design phase | Governance boundary violated |
| F-13 | Timeline contradicts artifact index | Evidence sources disagree |
| F-14 | Timeline contradicts memory model | State sources disagree |
| F-15 | Tests skipped in implementation phase | Implementation without verification |

---

## 27. Future Implementation Plan

Candidate future phases after this design:

| Phase | Name | Scope |
|-------|------|-------|
| 85C.1 | Governance Event Timeline Implementation Plan | Detailed implementation spec |
| 85C.2 | Read-Only Timeline Extraction Prototype | First read-only timeline command |
| 85C.3 | Governance Event Timeline Tests | Test suite for timeline model |

No task contracts are created for these phases in 85C.

## 28. Future Test Coverage

No tests are added in 85C because this is design-only. Future implementation must test:

| Test Area | Coverage Target |
|-----------|----------------|
| Event type parsing | Known types classified correctly |
| Event ordering | Ordering constraints enforced |
| Phase transition ordering | Start precedes completion |
| Approval/action causality | Approval required before action |
| Blocked/deferred/rejected preservation | Status events never auto-removed |
| Commit/push lineage events | Commit precedes push |
| Permission decision event classification | Request/allow/block/escalate distinguished |
| Artifact index linkage | Events reference valid artifact IDs |
| Memory model linkage | Events map to memory entities |
| Idempotent timeline extraction | Same input produces same timeline |
| Stale timeline detection | Outdated timeline flagged |

## 29. Example Governance Event Timeline

Illustrative markdown only, not an executable format:

```
event_id: phase-85a-started
event_type: phase_started
event_status: observed
source_phase: 85A
source_commit: 54ddd644
actor: operator
evidence_level: git_commit

event_id: artifact-persistent-lifecycle-memory-model-created
event_type: artifact_created
event_status: performed
source_phase: 85A
source_artifact: docs/PERSISTENT_LIFECYCLE_MEMORY_MODEL.md
source_commit: 54ddd644
evidence_level: repo_committed_artifact

event_id: phase-85a-completed
event_type: phase_completed
event_status: closed
source_phase: 85A
source_commit: e3336cfa
actor: operator
evidence_level: git_commit

event_id: phase-85b-completed
event_type: phase_completed
event_status: closed
source_phase: 85B
source_artifact: docs/ARTIFACT_INDEX_DESIGN.md
source_commit: fad1f466
evidence_level: repo_committed_artifact

event_id: permission-broker-future-direction
event_type: permission_escalated
event_status: deferred
source_phase: 85C
source_artifact: docs/GOVERNANCE_EVENT_TIMELINE_DESIGN.md
safety_notes: future_direction_only_not_implemented
```

---

## 30. Recommended Next Phase

**85D — Decision Log Integration**

85D should integrate approvals, rejected items, deferred items, and irreversible governance
decisions into a persistent decision model. It builds on 85A (memory entities for decisions),
85B (artifact index for decision evidence), and 85C (timeline ordering for decision history).

---

## Timeline Identity

| Field | Value |
|-------|-------|
| governance_event_timeline_name | pcae_governance_event_timeline |
| governance_event_timeline_version | 0.1 |
| governance_event_timeline_status | draft_documented |
| governance_event_timeline_implementation_status | not_started |
| permission_broker_future_direction_status | documented |
| permission_broker_implementation_status | not_started |
| shell_gate_implementation_status | not_started |

## Authorization Flags for 85C

| Flag | Value |
|------|-------|
| backend_invocation_performed | false |
| new_prompts_sent | false |
| new_capture_performed | false |
| new_intake_performed | false |
| new_adoption_review_performed | false |
| new_adoption_approval_performed | false |
| new_adoption_execution_performed | false |
| repo_mutation_authorized | true_for_timeline_docs_status_only |
| readme_mutation_authorized | false |
| source_mutation_authorized | false |
| test_mutation_authorized | false |
| docs_real_captured_tasks_mutation_authorized | false |
| persistent_memory_implementation_authorized | false |
| artifact_index_implementation_authorized | false |
| timeline_implementation_authorized | false |
| permission_broker_implementation_authorized | false |
| shell_gate_implementation_authorized | false |
| phase_85d_task_contract_authorized | false |
| commit_authorized | false |
| push_authorized | false |
| execution_authorized | false |
