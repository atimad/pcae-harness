# Roadmap Reconciliation and Phase 85 Plan

## 1. Purpose

Formally reconcile the original Phase 84 persistent memory/project intelligence roadmap with
the actual Phase 84 multi-agent governance design stream. Define a Phase 85 sequence that
inherits the original memory/intelligence goals, updated to build on the Phase 84 governance
artifacts.

## 2. Scope

Planning documentation only. This artifact defines Phase 85's goals, sequence, inputs,
boundaries, and gates. It does not implement any Phase 85 work.

## 3. Non-Goals

- Implementing persistent memory, artifact index, timeline, decision log, risk register,
  or project snapshot.
- Creating Phase 85 task contracts.
- Modifying source code, tests, README, or existing design artifacts.
- Backend invocation, prompt sending, capture, intake, or adoption.
- Task filename hygiene.

## 4. Original Phase 84 Roadmap

The original Phase 84 plan, defined in `docs/ROADMAP.md` and referenced in
`docs/MULTI_AGENT_GOVERNANCE_SUMMARY.md`, proposed persistent memory and project intelligence:

| Phase | Name | Purpose |
|-------|------|---------|
| 84A | Persistent Lifecycle Memory Model | Durable memory for lifecycle state, approvals, captures, decisions |
| 84B | Artifact Index | Searchable registry of governance artifacts, schemas, traces |
| 84C | Governance Event Timeline | Chronological event model for approvals, captures, commits |
| 84D | Decision Log Integration | Persistent model for approvals, rejections, deferrals |
| 84E | Risk Register | Track active, deferred, accepted, mitigated, blocked risks |
| 84F | Project State Snapshot | Current-state snapshot answering governance questions |

The original expected outcome was that PCAE could answer:
- What phase are we in?
- What was approved?
- What is blocked?
- What can be safely done next?
- What must never be repeated?

## 5. Actual Phase 84 Outcome

Phase 84 became a multi-agent governance design stream after the successful 83A–83L governed
multi-agent lifecycle demonstrated the need for stable lifecycle objects and governance
semantics before persistent memory could be built.

| Phase | Name | Type |
|-------|------|------|
| 84A | Multi-Agent Lifecycle Lessons / Roadmap Update | Documentation |
| 84B | Multi-Agent Prompt Package Schema | Design (v0.1) |
| 84C | Multi-Agent Capture Metadata Schema | Design (v0.1) |
| 84D | Multi-Agent Output Intake Schema | Design (v0.1) |
| 84E | Multi-Agent Adoption Candidate Schema | Design (v0.1) |
| 84F | Multi-Agent Lifecycle State Machine | Design (v0.1) |
| 84G | Multi-Agent Lifecycle Command Dry-Run | Design (v0.1) |
| 84H | Multi-Agent Backend Invocation Guard Hardening | Design (v0.1) |
| 84I | Multi-Agent Prompt Capture Storage Policy | Design (v0.1) |
| 84J | Multi-Agent Deferred Item Tracker | Design (v0.1) |
| 84K | Multi-Agent Governance README Summary | Documentation |
| 84K.1 | Full Health Baseline and Hygiene Assessment | Assessment |
| 84K.2 | Handoff State Refresh and Bootstrap Alignment | Refresh |
| 84K.3 | Re-run Full Health Baseline After Refresh | Assessment |
| 84L | Roadmap Reconciliation and Phase 85 Plan | Planning (this phase) |

Phase 84 produced 10 governance design artifacts, 2 health baselines, 1 handoff refresh,
1 governance summary, and 1 roadmap reconciliation. All are documentation/design only with
`implementation_status=not_started`.

## 6. Why the Roadmap Changed

The successful 83A–83L multi-agent lifecycle exposed a prerequisite: before PCAE can
persistently answer project-state questions, it needs stable lifecycle objects and governance
semantics for multi-agent work. The 83-series demonstrated that:

1. **Prompt packages** need a defined structure before they can be persisted as memory.
2. **Capture metadata** needs a schema before capture events can be indexed.
3. **Output intake** needs classification rules before intake events can be logged.
4. **Adoption candidates** need a formal model before approval decisions can be recorded.
5. **Lifecycle states** need a state machine before state transitions can be tracked.
6. **Command surfaces** need a dry-run design before queries can be answered.
7. **Invocation guards** need hardened rules before invocation events are safe to persist.
8. **Storage policies** need defined paths before artifacts can be stored and indexed.
9. **Deferred items** need structured tracking before they can feed a risk register.

Phase 84 therefore created the concepts that Phase 85's persistent memory will index, store,
query, and report on. Without these concepts, persistent memory would have been built on
unstable or undefined foundations.

## 7. What Phase 84 Completed

| Deliverable | Count | Status |
|-------------|-------|--------|
| Governance design artifacts (84A–84J) | 10 | draft_documented, implementation_status=not_started |
| Governance README summary (84K) | 1 | Complete |
| Full health baselines (84K.1, 84K.3) | 2 | Complete |
| Handoff state refresh (84K.2) | 1 | Complete |
| Roadmap reconciliation (84L) | 1 | This phase |
| Total Phase 84 phases | 15 | All documentation/design/assessment |

## 8. What Remains Deferred

The original Phase 84 goals (persistent memory, artifact index, governance timeline, decision
log, risk register, project snapshot) were deferred — not dropped. They are now the Phase 85
sequence with enriched inputs from the Phase 84 governance design stream.

Additionally, the following items from the deferred item tracker remain open:

| Item | Description | Status | Carry-Forward Target |
|------|-------------|--------|---------------------|
| DF-1 | Stale 83A future phases table | open | 85-series or next tracker touch |
| DF-2 | Dual capability models documentation | open | 85-series or next tracker touch |
| DF-3 | Blocked taxonomy back-reference | open | 85-series or next tracker touch |
| DF-4 | Authorization flag standardization | open | 85-series or next tracker touch |
| HY-1 | Task filename hygiene evidence inaccuracy | open (can be closed_no_action) | Close in 85A or next tracker touch |
| IMPL-1 | Schema implementation (4 schemas) | open | 85-series implementation phases |
| IMPL-2 | Lifecycle command dry-run implementation | open | 85-series implementation phases |
| TEST-1 | Future test coverage for schemas/guards | open | First 85-series implementation phase |

---

## 9. Phase 85 Planning Principles

1. **Build on Phase 84 foundations.** Phase 85 uses the governance design artifacts as inputs,
   not as things to re-derive.
2. **Design before implementation.** Each Phase 85 phase should produce a design artifact first.
   Implementation follows in governed phases.
3. **Maintain governance boundaries.** Persistent memory does not authorize execution. Indexing
   does not authorize adoption. Recording does not authorize commit/push.
4. **Reintroduce tests when implementation begins.** Documentation-only phases may skip tests.
   The first implementation phase must add tests.
5. **Preserve existing safety invariants.** All 84-series safety boundaries carry forward.
6. **No premature integration.** Each Phase 85 component should be independently useful before
   integration is attempted.

## 10. Proposed Phase 85 Sequence

### 85A — Persistent Lifecycle Memory Model

**Purpose:** Define the durable memory model for lifecycle state, approvals, captures,
adoption decisions, blocked/deferred items, and safe next actions.

**Inputs from Phase 84:**
- `docs/MULTI_AGENT_LIFECYCLE_STATE_MACHINE.md` — lifecycle states, transitions, guards
- `docs/MULTI_AGENT_DEFERRED_ITEM_TRACKER.md` — deferred item model and tracking policy
- `docs/FULL_HEALTH_BASELINE_84K3.md` — current project health state

**Expected artifact:** Memory model design document defining entity types, storage format,
query capabilities, lifecycle event capture, and persistence boundaries. May include a future
implementation plan.

**Implementation status:** not_started

**Test expectations:** If 85A is design-only, tests are not required. If 85A includes
implementation, tests must cover memory model parsing, lifecycle event recording, and query
correctness.

**Safety boundaries:**
- Memory model is read-only by default (records state, does not authorize action).
- No execution authorization from memory queries.
- No backend invocation without guard approval.
- No commit/push boundary collapse.

---

### 85B — Artifact Index

**Purpose:** Define a searchable/indexable registry of governance artifacts, schemas,
lifecycle traces, phase outputs, and status documents.

**Inputs from Phase 84:**
- `docs/MULTI_AGENT_GOVERNANCE_SUMMARY.md` — artifact inventory
- `docs/ROADMAP_RECONCILIATION_PHASE_85_PLAN.md` — this document
- All Phase 84 design artifacts (84B–84J schemas and policies)

**Expected artifact:** Artifact index design document defining indexable entities, metadata
fields, search capabilities, freshness tracking, and cross-reference model.

**Implementation status:** not_started

**Test expectations:** If design-only, tests not required. If implementation included, tests
must cover artifact discovery, metadata extraction, index query correctness, and freshness
detection.

**Safety boundaries:**
- Indexing does not authorize adoption or execution.
- Index queries are read-only.
- Index must distinguish observed state from authorized action.

---

### 85C — Governance Event Timeline

**Purpose:** Define a chronological event model for approvals, captures, checks, commits,
pushes, blockers, deferrals, and closures.

**Inputs from Phase 84:**
- `CHANGELOG.md` — chronological phase history
- `PROJECT_STATUS.md` — current and historical phase state
- Commit history (git log)
- Lifecycle artifacts from 83-series and 84-series

**Expected artifact:** Event timeline design document defining event types, temporal ordering,
causal linkage, source attribution, and query capabilities.

**Implementation status:** not_started

**Test expectations:** If design-only, tests not required. If implementation included, tests
must cover event timeline ordering, causal chain validation, and temporal query correctness.

**Safety boundaries:**
- Timeline is an observational record, not an authorization mechanism.
- Timeline entries do not authorize execution.
- Timeline must not be the sole source for governance decisions.

---

### 85D — Decision Log Integration

**Purpose:** Integrate approvals, rejected items, deferred items, and irreversible governance
decisions into a persistent decision model.

**Inputs from Phase 84:**
- `docs/MULTI_AGENT_ADOPTION_CANDIDATE_SCHEMA.md` — adoption candidate model
- `docs/MULTI_AGENT_DEFERRED_ITEM_TRACKER.md` — deferred/rejected item model
- Approval artifacts from 83-series (83F, 83J, 83K)

**Expected artifact:** Decision log design document defining decision types, status
transitions, irreversibility tracking, carry-forward rules, and audit trail.

**Implementation status:** not_started

**Test expectations:** If design-only, tests not required. If implementation included, tests
must cover decision status transitions, irreversibility enforcement, and carry-forward
correctness.

**Safety boundaries:**
- Decision log entries do not authorize commit or push.
- Rejected items cannot be re-approved without explicit new lifecycle.
- Deferred items cannot be silently promoted to approved.
- Decision log is append-only for governance decisions.

---

### 85E — Risk Register

**Purpose:** Track active, deferred, accepted, mitigated, and blocked governance risks.

**Inputs from Phase 84:**
- `docs/MULTI_AGENT_BACKEND_INVOCATION_GUARD_HARDENING.md` — invocation risk model
- `docs/MULTI_AGENT_PROMPT_CAPTURE_STORAGE_POLICY.md` — storage risk model
- `docs/MULTI_AGENT_DEFERRED_ITEM_TRACKER.md` — deferred risk items

**Expected artifact:** Risk register design document defining risk categories, severity
levels, status lifecycle, mitigation tracking, and escalation rules.

**Implementation status:** not_started

**Test expectations:** If design-only, tests not required. If implementation included, tests
must cover risk classification, status transitions, mitigation verification, and escalation
triggering.

**Safety boundaries:**
- Risk register tracking does not resolve risks automatically.
- Risk acceptance requires explicit human approval.
- Mitigated risks remain tracked until verified.
- Blocked risks cannot be silently unblocked.

---

### 85F — Project State Snapshot

**Purpose:** Produce a current-state snapshot answering the original Phase 84 questions:
- What phase are we in?
- What was approved?
- What is blocked?
- What can be safely done next?
- What must never be repeated?

**Inputs from Phase 84 and 85A–85E:**
- 85A memory model (lifecycle state)
- 85B artifact index (artifact availability)
- 85C event timeline (history)
- 85D decision log (approvals/rejections/deferrals)
- 85E risk register (active/blocked risks)

**Expected artifact:** Project state snapshot design document defining snapshot composition,
query interface, safety boundaries, and refresh policy. This is the capstone that integrates
85A–85E outputs.

**Implementation status:** not_started

**Test expectations:** If design-only, tests not required. If implementation included, tests
must cover snapshot composition, query correctness, safety boundary enforcement, and refresh
accuracy.

**Safety boundaries:**
- Snapshot must distinguish observed state from authorized action.
- "What can be safely done next" must not auto-execute.
- "What must never be repeated" must be enforced, not merely reported.
- Snapshot refresh must not bypass governance gates.

---

## 11. Phase 85 Acceptance Boundaries

- Phase 85 must not collapse approval boundaries.
- Persistent memory does not authorize execution.
- Artifact indexing does not authorize adoption.
- Decision log entries do not authorize commit or push.
- Risk register tracking does not resolve risks automatically.
- Project state snapshot must distinguish observed state from authorized action.
- Each Phase 85 deliverable must be independently verifiable.
- No Phase 85 component may bypass the existing lifecycle gate model.

## 12. Phase 85 Test Strategy

Because phases 84A–84L were documentation-only, Phase 85 should reintroduce tests when
implementation begins.

| Principle | Detail |
|-----------|--------|
| Design-only phases | May remain documentation-only if scoped as design. Tests not required. |
| First implementation phase | Must add tests. No implementation without test coverage. |
| Default test command | `python -m pytest -n auto` |
| Serial exceptions | 3 retained: release verification, debugging, compatibility workflows |
| Test targets | Memory model parsing, artifact indexing, event timeline ordering, decision log status transitions, risk register classification, project snapshot outputs |
| Governance tests | Must verify that memory/index/timeline/log/register/snapshot operations remain read-only and do not authorize execution |

## 13. Phase 85 Implementation Gates

- No source implementation without explicit implementation phase.
- No tests skipped for implementation phases.
- No backend invocation unless guard-approved.
- No prompt sending unless approved by lifecycle state.
- No adoption without intake/review/approval.
- No commit/push boundary collapse.
- No `.pcae` storage changes without explicit storage implementation phase.
- No schema implementation without governed schema implementation phase.
- No state machine changes without governed state machine phase.

## 14. Deferred Item Carry-Forward

| Item | Description | Status | Carry-Forward Target |
|------|-------------|--------|---------------------|
| DF-1 | Stale 83A future phases table | open | 85-series or next tracker touch |
| DF-2 | Dual capability models documentation | open | 85-series or next tracker touch |
| DF-3 | Blocked taxonomy back-reference | open | 85-series or next tracker touch |
| DF-4 | Authorization flag standardization | open | 85-series or next tracker touch |
| HY-1 | Task filename hygiene evidence inaccuracy | open → `closed_no_action` | 84K.1 confirmed filenames are NOT truncated; close in first opportunity |
| IMPL-1 | Schema implementation (4 schemas: prompt package, capture metadata, output intake, adoption candidate) | open | 85-series implementation phases |
| IMPL-2 | Lifecycle command dry-run implementation | open | 85-series implementation phases |
| TEST-1 | Future test coverage for schema parsing and guard decisions | open | First 85-series implementation phase |
| HSR-1 | Handoff-state-refresh validator stale for documentation streams | new (carry-forward from 84K.2/84K.3) | Future tooling improvement |

## 15. Handoff-State-Refresh Validator Note

Phases 84K.2 and 84K.3 found persistent handoff-state-refresh blocker/warning signals (4B/6W)
that are structural or validator-stale for documentation streams. They were classified as
`structural_non_blocking` (blockers) and `documentation_refreshed_but_validator_stale` (warnings).

These signals do not block 84L or Phase 85 planning. They reflect that the handoff-state-refresh
validator (phase 61I) checks internal state machine fields designed to be updated by implementation
phases. The 84-series documentation stream intentionally did not update those fields.

A future tooling improvement may teach handoff-state-refresh to recognize refreshed
documentation-only streams (carried as HSR-1 in deferred items above).

## 16. Bootstrap Modernization Note

| Field | Value |
|-------|-------|
| Modern default test command | `python -m pytest -n auto` |
| Battery-conscious alternative | `python -m pytest -n 4` |
| Serial exceptions retained | 3 (release verification, debugging, compatibility) |
| Documentation-only validation | `pcae health/check/doctor/push` + summary commands |
| Implementation phases | Must reintroduce tests using `python -m pytest -n auto` |

## 17. Risk and Safety Notes

1. **Phase 85 designs should not assume implementation.** Each design document is a plan, not
   permission to implement. Implementation requires a separate governed phase.
2. **Persistent memory must not become an execution oracle.** Memory records state. It does not
   authorize action. Querying memory for "what can be done next" must remain advisory.
3. **Cross-component integration requires its own phase.** 85F (Project State Snapshot) depends
   on 85A–85E. If any dependency is incomplete, 85F must block or scope-reduce.
4. **Existing lifecycle gate model is preserved.** Phase 85 adds new capabilities; it does not
   replace or bypass the existing 16-gate lifecycle model.
5. **Source mutation remains gate-controlled.** No Phase 85 design document authorizes source
   modification. Implementation phases must go through the existing commit/push governance.

## 18. Recommended Next Phase

**85A — Persistent Lifecycle Memory Model**

85A should define the durable memory model that will underpin the rest of Phase 85. It should
be scoped as design-only or design-plus-implementation depending on the operator's preference.
If design-only, it does not add tests. If implementation is included, tests are mandatory.

No Phase 85 task contract is created in this phase (84L). The 85A task contract should be
created when 85A begins.

## 19. Validation Checklist

| Check | Status |
|-------|--------|
| Original Phase 84 roadmap documented | YES |
| Actual Phase 84 outcome documented | YES |
| Roadmap change rationale documented | YES |
| Phase 84 completed stream summarized | YES |
| Deferred roadmap carried into Phase 85 | YES |
| Phase 85 sequence defined (85A–85F) | YES |
| Each phase has purpose/inputs/output/status/tests/safety | YES |
| Phase 85 acceptance boundaries defined | YES |
| Phase 85 test strategy defined | YES |
| Phase 85 implementation gates defined | YES |
| Deferred item carry-forward documented | YES |
| Handoff-state-refresh validator note included | YES |
| Bootstrap modernization note included | YES |
| Risk and safety notes included | YES |
| Recommended next phase defined | YES |
| No Phase 85 task contract created | YES |

---

## Reconciliation Identity

| Field | Value |
|-------|-------|
| roadmap_reconciliation_name | phase_84_to_85_reconciliation |
| roadmap_reconciliation_version | 0.1 |
| roadmap_reconciliation_status | documented |
| phase_85_planning_status | documented |
| phase_85_implementation_status | not_started |

## Authorization Flags for 84L

| Flag | Value |
|------|-------|
| backend_invocation_performed | false |
| new_prompts_sent | false |
| new_capture_performed | false |
| new_intake_performed | false |
| new_adoption_review_performed | false |
| new_adoption_approval_performed | false |
| new_adoption_execution_performed | false |
| repo_mutation_authorized | true_for_roadmap_docs_status_only |
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
| phase_85_task_contract_authorized | false |
| commit_authorized | false |
| push_authorized | false |
| execution_authorized | false |
