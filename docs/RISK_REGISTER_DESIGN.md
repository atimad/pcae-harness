# Risk Register Design

## 1. Purpose

Define a persistent risk register for PCAE that tracks active, accepted, mitigated, deferred,
blocked, and closed governance risks. The register connects decisions (85D), events (85C),
artifacts (85B), and memory (85A) so PCAE can answer: What is risky? What was accepted? What
is blocked? What was mitigated? What must never be repeated?

## 2. Scope

Design only. This artifact defines risk types, fields, status/severity/likelihood/exposure
models, lifecycle rules, provenance, relationships, query targets, and validation rules.
It does not implement risk storage, create machine-readable files, or add tests.

## 3. Non-Goals

- Implementing risk register storage or CLI commands.
- Creating `.pcae` risk storage directories or files.
- Adding tests.
- Modifying source code, README, or existing artifacts.
- Backend invocation, prompt sending, capture, intake, or adoption.

## 4. Motivation from 85A, 85B, 85C, and 85D

- **85A** defines `risk_record` entities with fields for type, status, level, source, and mitigation.
- **85B** locates risk source artifacts and classifies their freshness.
- **85C** records `risk_identified`, `risk_mitigated`, `blocker_detected`, and `blocker_resolved` events.
- **85D** defines `accepted_risk_decision`, `blocked_decision`, and `must_never_repeat_decision` types.

The risk register aggregates these inputs into a queryable register that distinguishes active
risks from accepted, mitigated, deferred, blocked, and closed risks.

---

## 5. Risk Register Design Principles

1. Risk register records risk state, not permission by itself.
2. Risk register does not authorize execution.
3. Risk register does not authorize backend invocation.
4. Risk register does not authorize adoption.
5. Risk register does not authorize commit or push.
6. Risk register must distinguish active, accepted, mitigated, deferred, blocked, closed, and unknown risks.
7. Risk register must preserve accepted-risk rationale.
8. Risk register must preserve mitigations separately from acceptance.
9. Risk register must link every risk to evidence.
10. Risk register must support offline audit.
11. Risk register must support project-state reconstruction.
12. Risk register must support must-never-repeat controls.
13. Risk register must support next-safe-action analysis without performing actions.

## 6. Risk Register Threat Model

| # | Threat | Impact |
|---|--------|--------|
| RT-1 | Active risk forgotten | Unsafe action proceeds without awareness |
| RT-2 | Accepted risk treated as mitigated | Risk assumed resolved without evidence |
| RT-3 | Mitigated risk treated as closed without evidence | Premature closure |
| RT-4 | Deferred risk treated as resolved | Risk ignored without review |
| RT-5 | Blocked risk ignored | Blocked action proceeds |
| RT-6 | Risk severity downgraded without decision | Risk underestimated |
| RT-7 | Risk source artifact missing | Risk claim unverifiable |
| RT-8 | Risk contradicts decision log | Inconsistent governance state |
| RT-9 | Risk contradicts event timeline | Temporal inconsistency |
| RT-10 | Risk contradicts artifact index | Evidence source mismatch |
| RT-11 | Risk contradicts memory snapshot | State inconsistency |
| RT-12 | Human override hides original risk | Original risk invisible |
| RT-13 | Permission risk treated as lifecycle approval | Scope escalation |
| RT-14 | Stale validator signal treated as substantive blocker | Progress blocked incorrectly |
| RT-15 | Substantive blocker treated as stale signal | Real risk dismissed |
| RT-16 | Must-never-repeat lesson not carried forward | Unsafe pattern may recur |

---

## 7. Core Risk Types

| Risk Type | Purpose |
|-----------|---------|
| `execution_risk` | Risk from unauthorized or ungoverned execution |
| `backend_invocation_risk` | Risk from backend invocation without approval chain |
| `prompt_sending_risk` | Risk from prompt sending without authorization |
| `capture_integrity_risk` | Risk from missing/corrupted capture evidence |
| `output_intake_risk` | Risk from skipped or incomplete intake |
| `adoption_risk` | Risk from adoption without review/approval chain |
| `source_mutation_risk` | Risk from source code changes outside governance |
| `test_mutation_risk` | Risk from test changes outside governance |
| `commit_risk` | Risk from ungoverned commits |
| `push_risk` | Risk from raw/force pushes |
| `rollback_risk` | Risk from rollback without approval |
| `permission_risk` | Risk from permission decisions outside PCAE governance |
| `shell_gate_risk` | Risk from absent shell gate enforcement |
| `memory_staleness_risk` | Risk from stale memory snapshots |
| `artifact_staleness_risk` | Risk from stale or missing artifacts |
| `timeline_ordering_risk` | Risk from incorrect event ordering |
| `decision_log_risk` | Risk from missing or inconsistent decisions |
| `deferred_item_risk` | Risk from unreviewed deferred items |
| `accepted_risk` | Explicitly accepted governance risk |
| `human_override_risk` | Risk from human override of governance controls |
| `must_never_repeat_risk` | Permanent control for unsafe patterns |
| `documentation_stale_signal_risk` | Risk from persistent stale validator signals |

## 8. Required Risk Fields

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `risk_id` | string | yes | Stable unique identifier |
| `risk_type` | string | yes | Type from section 7 |
| `risk_status` | string | yes | Status from allowed values |
| `risk_title` | string | yes | Short human-readable title |
| `risk_description` | string | yes | Description of the risk |
| `risk_severity` | string | yes | Severity level |
| `risk_likelihood` | string | yes | Likelihood level |
| `risk_exposure` | string | yes | Exposure level (severity × likelihood) |
| `source_phase` | string | yes | Phase where risk was identified |
| `source_artifact` | string | where available | Artifact providing evidence |
| `source_event` | string | where available | Timeline event ID |
| `source_decision` | string | where available | Decision log entry ID |
| `source_commit` | string | where available | Commit hash |
| `risk_owner` | string | no | Responsible party |
| `human_review_required` | boolean | yes | Whether human review is needed |
| `affected_files` | list | no | Files affected by this risk |
| `affected_agents` | list | no | Agents affected |
| `affected_commands` | list | no | Commands affected |
| `blocking_condition` | string | for blocked | What this risk blocks |
| `mitigation` | string | for mitigated | Mitigation description and evidence |
| `acceptance_rationale` | string | for accepted | Why risk was accepted |
| `accepted_by` | string | for accepted | Who accepted the risk |
| `supersedes` | string | no | Risk ID this supersedes |
| `superseded_by` | string | no | Risk ID that supersedes this |
| `related_risks` | list | no | Related risk IDs |
| `related_artifacts` | list | no | Related artifact IDs from 85B |
| `related_events` | list | no | Related event IDs from 85C |
| `related_decisions` | list | no | Related decision IDs from 85D |
| `evidence_level` | string | yes | Evidence level from 85B hierarchy |
| `last_reviewed_phase` | string | no | Phase when last reviewed |
| `next_review_phase` | string | no | Phase for next review |
| `safety_notes` | string | no | Safety-relevant notes |

## 9. Risk Status Values

| Status | Meaning |
|--------|---------|
| `active` | Risk is currently present and unresolved |
| `accepted` | Risk is acknowledged and accepted with rationale |
| `mitigated` | Risk has been reduced with evidence |
| `deferred` | Risk review deferred to a future phase |
| `blocked` | Risk blocks a specific action or phase |
| `closed` | Risk is resolved with evidence |
| `superseded` | Risk replaced by a newer assessment |
| `stale_signal` | Risk is a persistent validator/structural signal, not substantive |
| `unknown` | Risk status not determined |

## 10. Risk Severity Model

| Severity | Meaning |
|----------|---------|
| `low` | Minor governance impact; does not block progress |
| `medium` | Moderate impact; may require review before proceeding |
| `high` | Significant impact; blocks progress until addressed |
| `critical` | Severe impact; requires immediate human review |
| `unknown` | Severity not assessed |

## 11. Risk Likelihood Model

| Likelihood | Meaning |
|------------|---------|
| `unlikely` | Risk is theoretically possible but not expected |
| `possible` | Risk could occur under certain conditions |
| `likely` | Risk is expected to occur without mitigation |
| `observed` | Risk has already been observed in practice |
| `unknown` | Likelihood not assessed |

## 12. Risk Exposure Model

Risk exposure combines severity and likelihood:

| Exposure | When Applied |
|----------|-------------|
| `low` | Low severity + unlikely/possible |
| `medium` | Medium severity, or low severity + likely/observed |
| `high` | High severity, or medium severity + likely/observed |
| `critical` | Critical severity, or high severity + observed |
| `unknown` | Either severity or likelihood is unknown |

Exposure is an advisory classification. It does not authorize or block actions by itself.

## 13. Risk Identity Rules

1. `risk_id` must be stable across register updates.
2. `risk_type` must be from known types or explicitly `unknown`.
3. `source_phase` must be recorded for every risk.
4. `source_artifact`, `source_event`, or `source_decision` must be recorded where available.
5. Risk identity must not depend on chat text alone.
6. Risk IDs must not collide within the register.
7. Risk status must not be inferred from filename alone.

## 14. Risk Lifecycle Rules

1. Active risks may become accepted, mitigated, deferred, blocked, superseded, or closed.
2. Accepted risks remain accepted until mitigated or superseded.
3. Accepted risk is not mitigation — acceptance acknowledges the risk; mitigation reduces it.
4. Mitigated risks require mitigation evidence.
5. Deferred risks require target phase or review context.
6. Blocked risks require a blocking condition.
7. Closed risks require closure reason and evidence.
8. `stale_signal` risks require explanation and review trigger.
9. `must_never_repeat` risks remain active controls unless explicitly superseded with rationale.
10. Superseded risks retain their history (not deleted from register).

## 15. Risk Source-of-Truth Rules

1. Committed risk artifacts outrank chat memory.
2. Decision log `accepted_risk_decision` entries feed the risk register.
3. Event timeline `blocker_detected`/`risk_identified` events feed the register.
4. Artifact index identifies source artifacts for risk evidence.
5. Human final reports may seed risks but must be reconciled with repo artifacts.
6. Conversation memory is secondary to all committed sources.
7. Derived summaries cannot silently supersede primary risk evidence.

## 16. Provenance and Evidence Policy

Every risk must link to at least one evidence source:

| Evidence Source | Trust Level | When Used |
|-----------------|-------------|-----------|
| Committed risk/guard/storage artifact | Highest | Design docs with threat models |
| Decision log entry | High | Accepted-risk or blocked decisions |
| Timeline event | High | Risk/blocker events |
| Git commit hash | High | Commit/push risk evidence |
| PCAE command output | High | Health/check/lifecycle risks |
| Human report | Medium | Operator-identified risks |
| Conversation memory | Lowest | Fallback only |

Risks without provenance are flagged as unverified.

---

## 17. Relationship to Persistent Lifecycle Memory

- Risk register feeds `risk_status` in 85A memory.
- Risk register feeds blocker memory.
- Risk register feeds `forbidden_actions` memory.
- Risk register feeds `next_safe_actions` caveats.
- Risk register feeds must-never-repeat answers.
- Memory must cite risk register entries for risk claims.

## 18. Relationship to Artifact Index

- 85B artifact index locates risk source artifacts (guard docs, storage docs, tracker docs).
- Risk register references artifact IDs and paths from the index.
- Missing risk artifacts must be classified as `missing`, not `resolved`.
- Stale artifacts may create `artifact_staleness_risk` entries.

## 19. Relationship to Governance Event Timeline

- `risk_identified` events create or update active risk entries.
- `blocker_detected` events create `active` or `blocked` risk entries.
- `blocker_resolved` events may mitigate or close risks with evidence.
- `risk_mitigated` events update risk status to `mitigated`.
- `permission_blocked` events may create `permission_risk` entries.
- `permission_escalated` events may create human-review risk entries.
- Timeline ordering distinguishes observed risk from mitigated risk.

## 20. Relationship to Decision Log

- `accepted_risk_decision` entries create `accepted` risks.
- `denial_decision` entries may create forbidden-action or blocked risks.
- `deferral_decision` entries create `deferred` risks.
- `human_override_decision` entries create `human_override_risk`.
- `must_never_repeat_decision` entries create durable controls.
- Risk closure requires a decision or evidence.

## 21. Relationship to Deferred Item Tracker

- Deferred items (DF-1–DF-4, HY-1, IMPL-1–2, TEST-1) may create `deferred_item_risk` entries.
- Deferred risks must preserve target/review context.
- Closure of a deferred item does not automatically close its risk unless evidence supports it.
- HSR-1 (validator stale for doc streams) maps to `documentation_stale_signal_risk`.

---

## 22. Backend and Permission Risks

| Risk | Type | Status |
|------|------|--------|
| Backend invocation without approval chain | `backend_invocation_risk` | active control |
| Prompt sent without authorization | `prompt_sending_risk` | active control |
| Capture missing hash/provenance | `capture_integrity_risk` | active control |
| Mutation during capture | `capture_integrity_risk` | active control |
| Permission allowed treated as lifecycle approval | `permission_risk` | active control |
| Bypass-permissions mode used without explicit exception | `permission_risk` | active control |
| PCAE shell gate not yet implemented | `shell_gate_risk` | deferred |

## 23. Prompt/Capture/Intake/Adoption Risks

| Risk | Type | Status |
|------|------|--------|
| Prompt package not linked to approval | `prompt_sending_risk` | active control |
| Backend output captured without provenance | `capture_integrity_risk` | active control |
| Intake skipped before adoption | `output_intake_risk` | active control |
| Adoption candidate approved without review | `adoption_risk` | active control |
| Adoption executed without approval | `adoption_risk` | active control |
| Deferred/rejected candidate reintroduced | `adoption_risk` | active control |

## 24. Commit/Push/Rollback Risks

| Risk | Type | Status |
|------|------|--------|
| Raw `git push` used | `push_risk` | must_never_repeat control |
| Force push used | `push_risk` | must_never_repeat control |
| Commit created without governed approval | `commit_risk` | active control |
| Push performed without lineage validation | `push_risk` | active control |
| Rollback performed without rollback approval | `rollback_risk` | active control |

## 25. Documentation and Stale-Signal Risks

| Risk | Type | Status |
|------|------|--------|
| Handoff-state-refresh structural signals persist | `documentation_stale_signal_risk` | stale_signal |
| Validator stale for documentation streams | `documentation_stale_signal_risk` | stale_signal |
| HY-1 evidence inaccuracy (non-blocking) | `deferred_item_risk` | stale_signal |
| Documentation-only phases may defer implementation tests | `deferred_item_risk` | accepted |
| Stale summary could mislead next-phase planning | `artifact_staleness_risk` | active control |

## 26. Human Override and Accepted-Risk Handling

- Human override does not erase original risk — both the original risk and the override are preserved.
- Human override must record reason and authority.
- Accepted risk requires explicit rationale and `accepted_by` field.
- Accepted risk remains visible until mitigated or superseded.
- Acceptance is not mitigation; the risk remains active but acknowledged.

## 27. Must-Never-Repeat Controls

| Control | Source | Permanence |
|---------|--------|------------|
| Bypass permissions used without explicit exception | Governance invariant | Permanent |
| Raw `git push` normalized as acceptable | 77-series governance | Permanent |
| Force push without authorization | Governance invariant | Permanent |
| Adoption without approval | 83-series lifecycle rules | Permanent |
| Backend invocation without guard approval | 84H guard design | Permanent |
| Source/test mutation outside active task scope | Task contract governance | Permanent |
| Commit/push boundary collapse | Governance invariant | Permanent |
| Deferred/rejected item silently reintroduced | 83I/84J tracker rules | Permanent |

Must-never-repeat controls remain active unless explicitly superseded with documented rationale.

---

## 28. Query Model

### Q1: what_risks_are_active

| Field | Value |
|-------|-------|
| Required risk types | All types with `status=active` |
| Artifact index dependencies | Source artifacts for each risk |
| Timeline dependencies | `risk_identified` events |
| Decision log dependencies | Related decisions |
| Memory model dependencies | `risk_record` entities |
| Expected answer shape | `[{risk_id, risk_type, severity, exposure, source_phase}]` |
| Required provenance | Source artifact or event |
| Safety caveats | Active risks do not block by themselves unless `blocking_condition` is set |

### Q2: what_risks_are_accepted

| Field | Value |
|-------|-------|
| Required risk types | All with `status=accepted` |
| Decision log dependencies | `accepted_risk_decision` entries |
| Expected answer shape | `[{risk_id, severity, acceptance_rationale, accepted_by}]` |
| Required provenance | Decision log entry with rationale |
| Safety caveats | Accepted is not mitigated |

### Q3: what_risks_are_mitigated

| Field | Value |
|-------|-------|
| Required risk types | All with `status=mitigated` |
| Expected answer shape | `[{risk_id, mitigation, mitigation_evidence}]` |
| Required provenance | Mitigation evidence |
| Safety caveats | Mitigation must be verified, not assumed |

### Q4: what_risks_are_deferred

| Field | Value |
|-------|-------|
| Required risk types | All with `status=deferred` |
| Expected answer shape | `[{risk_id, target_phase, next_review_phase}]` |
| Required provenance | Deferral decision |
| Safety caveats | Deferred is not resolved |

### Q5: what_risks_are_blocked

| Field | Value |
|-------|-------|
| Required risk types | All with `status=blocked` |
| Expected answer shape | `[{risk_id, blocking_condition, affected_actions}]` |
| Required provenance | Blocking condition source |
| Safety caveats | Blocked risks prevent specific actions |

### Q6: what_risks_require_human_review

| Field | Value |
|-------|-------|
| Required risk types | All with `human_review_required=true` |
| Expected answer shape | `[{risk_id, reason, urgency, next_review_phase}]` |
| Required provenance | Source of review requirement |
| Safety caveats | Advisory; human review is not automatic |

### Q7: what_risks_affect_next_safe_action

| Field | Value |
|-------|-------|
| Required risk types | Active, blocked, and accepted risks relevant to proposed actions |
| Expected answer shape | `[{risk_id, affect_type, caveat}]` |
| Required provenance | Current state evidence |
| Safety caveats | Advisory; does not authorize or block by itself |

### Q8: what_must_never_be_repeated

| Field | Value |
|-------|-------|
| Required risk types | `must_never_repeat_risk` |
| Expected answer shape | `[{risk_id, control, source, permanence}]` |
| Required provenance | Source decision or governance invariant |
| Safety caveats | Enforcement is separate from reporting |

### Q9: what_risks_are_stale_signals

| Field | Value |
|-------|-------|
| Required risk types | All with `status=stale_signal` |
| Expected answer shape | `[{risk_id, explanation, review_trigger}]` |
| Required provenance | Classification evidence |
| Safety caveats | Stale signals must be distinguished from substantive blockers |

### Q10: what_risks_have_missing_evidence

| Field | Value |
|-------|-------|
| Required risk types | All where source_artifact is missing from filesystem |
| Expected answer shape | `[{risk_id, missing_artifact, impact}]` |
| Required provenance | Artifact index missing classification |
| Safety caveats | Missing evidence invalidates risk status claims |

---

## 29. Risk Update Rules

1. Risk updates only after phase completion or explicit risk capture phase.
2. Risk update must cite artifact, command output, event, decision, or commit.
3. Risk register must not infer mitigation from acceptance.
4. Risk register must preserve accepted/deferred/blocked states.
5. Risk register must not delete superseded risks (mark `superseded`, retain entry).
6. Risk register must preserve human override history.
7. Risk register must distinguish substantive blocker from stale signal.
8. Risk register must be idempotent (same inputs produce same register).
9. Risk register must distinguish observed risk from authorized action.
10. Risk register must not authorize execution.
11. Risk register must flag risks without provenance as unverified.
12. Must-never-repeat controls are permanent unless explicitly superseded with rationale.

---

## 30. Validation Rules

| # | Rule |
|---|------|
| V-1 | `risk_id` required for every risk entry |
| V-2 | `risk_type` required and must be from known types |
| V-3 | `risk_status` required and must be from allowed values |
| V-4 | `risk_severity` required |
| V-5 | `risk_likelihood` required |
| V-6 | `risk_exposure` required |
| V-7 | `source_phase` required |
| V-8 | `source_artifact` or `source_decision` required where available |
| V-9 | Accepted risk requires `acceptance_rationale` |
| V-10 | Accepted risk is not mitigation |
| V-11 | Mitigated risk requires `mitigation` evidence |
| V-12 | Deferred risk requires review/target context if known |
| V-13 | Blocked risk requires `blocking_condition` |
| V-14 | `stale_signal` risk requires explanation |
| V-15 | Must-never-repeat risk remains durable control |
| V-16 | Risk register does not authorize execution |
| V-17 | Risk register does not authorize backend invocation |
| V-18 | Risk register does not authorize adoption |
| V-19 | Risk register does not authorize commit/push |
| V-20 | Risk links to decision log when risk accepted or overridden |
| V-21 | Risk links to event timeline when risk observed |
| V-22 | Risk links to artifact index for source artifact |
| V-23 | Risk feeds memory but does not override task contract |
| V-24 | Future implementation requires tests |
| V-25 | Design-only phase creates no machine-readable risk register |
| V-26 | No source/test changes in 85E |
| V-27 | No phase beyond 85E started in this phase |
| V-28 | No `.pcae` risk storage created in 85E |
| V-29 | `risk_id` must be stable across register updates |
| V-30 | Risk IDs must not collide |
| V-31 | `risk_title` required |
| V-32 | `risk_description` required |
| V-33 | `human_review_required` required |
| V-34 | `evidence_level` required |
| V-35 | Superseded risks must retain history |
| V-36 | Closed risks require closure reason |
| V-37 | `supersedes`/`superseded_by` must form a valid chain |
| V-38 | Exposure must be consistent with severity × likelihood |
| V-39 | Risks without provenance must be flagged as unverified |
| V-40 | Human override must not erase original risk |
| V-41 | Stale signal must not be confused with substantive blocker |
| V-42 | Substantive blocker must not be dismissed as stale signal |

## 31. Failure Cases

| # | Failure | Impact |
|---|---------|--------|
| F-1 | Risk missing source artifact | Unverifiable risk claim |
| F-2 | Accepted risk treated as mitigated | Risk assumed resolved |
| F-3 | Mitigated risk missing evidence | Mitigation unverifiable |
| F-4 | Deferred risk treated as resolved | Risk ignored |
| F-5 | Blocked risk missing blocking condition | Block unenforceable |
| F-6 | Stale signal treated as substantive blocker | Progress incorrectly blocked |
| F-7 | Substantive blocker treated as stale signal | Real risk dismissed |
| F-8 | Human override erases original risk | Original risk invisible |
| F-9 | Must-never-repeat control forgotten | Unsafe pattern may recur |
| F-10 | Risk contradicts decision log | Inconsistent governance state |
| F-11 | Risk contradicts event timeline | Temporal inconsistency |
| F-12 | Risk contradicts artifact index | Evidence mismatch |
| F-13 | Risk contradicts memory model | State inconsistency |
| F-14 | Risk implementation attempted in design phase | Governance boundary violated |
| F-15 | Tests skipped in implementation phase | Implementation without verification |

---

## 32. Future Implementation Plan

Candidate future phases after this design:

| Phase | Name | Scope |
|-------|------|-------|
| 85E.1 | Risk Register Implementation Plan | Detailed implementation spec |
| 85E.2 | Read-Only Risk Register Prototype | First read-only risk query command |
| 85E.3 | Risk Register Tests | Test suite for risk register model |

No task contracts are created for these phases in 85E.

## 33. Future Test Coverage

No tests are added in 85E because this is design-only. Future implementation must test:

| Test Area | Coverage Target |
|-----------|----------------|
| Risk type parsing | Known types classified correctly |
| Risk status transitions | Lifecycle rules enforced |
| Severity/likelihood/exposure classification | Model applied correctly |
| Accepted-risk preservation | Rationale and accepted_by preserved |
| Mitigation evidence requirement | Mitigation requires evidence |
| Deferred risk carry-forward | Target/review context preserved |
| Blocked risk classification | Blocking condition required |
| Stale signal classification | Distinguished from substantive blockers |
| Must-never-repeat controls | Permanent unless explicitly superseded |
| Artifact index linkage | Risks reference valid artifact IDs |
| Timeline linkage | Risks map to valid timeline events |
| Decision log linkage | Risks link to valid decisions |
| Memory model linkage | Risks feed correct memory entities |
| Idempotent risk extraction | Same input produces same register |

## 34. Example Risk Register Entries

Illustrative markdown only, not an executable format:

```
risk_id: hsr-structural-signals
risk_type: documentation_stale_signal_risk
risk_status: stale_signal
risk_title: Persistent handoff-state-refresh structural signals
risk_description: pcae handoff-state-refresh reports 4 blockers / 6 warnings that persist across 84K.2 and 84K.3; classified as structural validator signals, not substantive governance blockers
risk_severity: low
risk_likelihood: observed
risk_exposure: low
source_phase: 84K.3
source_artifact: docs/FULL_HEALTH_BASELINE_84K3.md
human_review_required: false
evidence_level: repo_committed_artifact
safety_notes: non-blocking; will clear when implementation phases update internal state

risk_id: permission-broker-not-implemented
risk_type: shell_gate_risk
risk_status: deferred
risk_title: PCAE permission broker / shell gate not yet implemented
risk_description: Agents currently ask human for shell permission; PCAE governance layer not yet integrated as permission broker
risk_severity: medium
risk_likelihood: possible
risk_exposure: medium
source_phase: 85C
source_artifact: docs/GOVERNANCE_EVENT_TIMELINE_DESIGN.md
human_review_required: true
mitigation: future PCAE permission broker or shell gate design/implementation
next_review_phase: post-85F

risk_id: raw-push-never-repeat
risk_type: must_never_repeat_risk
risk_status: active
risk_title: Raw git push must not be normalized
risk_description: Direct git push bypassing governed pcae push must not become accepted practice
risk_severity: high
risk_likelihood: possible
risk_exposure: high
source_phase: 77-series
source_decision: governance_invariant
human_review_required: false
evidence_level: repo_committed_artifact
safety_notes: governed pcae push remains required; raw push is a permanent must-never-repeat control
```

---

## 35. Recommended Next Phase

**85F — Project State Snapshot**

85F is the capstone of Phase 85. It should define the project state snapshot design that
integrates 85A (memory model), 85B (artifact index), 85C (event timeline), 85D (decision log),
and 85E (risk register) to answer the original Phase 84 questions:
- What phase are we in?
- What was approved?
- What is blocked?
- What can be safely done next?
- What must never be repeated?

---

## Risk Register Identity

| Field | Value |
|-------|-------|
| risk_register_name | pcae_risk_register |
| risk_register_version | 0.1 |
| risk_register_status | draft_documented |
| risk_register_implementation_status | not_started |

## Authorization Flags for 85E

| Flag | Value |
|------|-------|
| backend_invocation_performed | false |
| new_prompts_sent | false |
| new_capture_performed | false |
| new_intake_performed | false |
| new_adoption_review_performed | false |
| new_adoption_approval_performed | false |
| new_adoption_execution_performed | false |
| repo_mutation_authorized | true_for_risk_register_docs_status_only |
| readme_mutation_authorized | false |
| source_mutation_authorized | false |
| test_mutation_authorized | false |
| docs_real_captured_tasks_mutation_authorized | false |
| persistent_memory_implementation_authorized | false |
| artifact_index_implementation_authorized | false |
| timeline_implementation_authorized | false |
| decision_log_implementation_authorized | false |
| risk_register_implementation_authorized | false |
| permission_broker_implementation_authorized | false |
| shell_gate_implementation_authorized | false |
| project_snapshot_implementation_authorized | false |
| phase_85f_task_contract_authorized | false |
| commit_authorized | false |
| push_authorized | false |
| execution_authorized | false |
