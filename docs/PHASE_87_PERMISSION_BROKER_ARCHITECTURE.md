# Phase 87 Permission Broker Architecture

## 1. Purpose

Define the architecture for a future PCAE permission broker: a policy mediation layer
that receives proposed actions, reads gate dry-run evidence and project intelligence,
applies policy, returns explicit decisions, and routes high-risk actions to human review.

## 2. Scope

Architecture design only. This artifact defines the broker's role, inputs, outputs,
decision model, relationships, and safety invariants. It does not implement the broker,
create CLI commands, modify source code, or add tests.

## 3. Non-Goals

- Implementing the permission broker.
- Creating CLI commands, source code, or tests.
- Implementing shell gate, storage, or enforcement.
- Modifying existing artifacts.
- Backend invocation, prompt sending, capture, intake, or adoption.

## 4. Starting Point from 87C–87G

Phase 87C–87G delivered dry-run gate evaluators for all 15 gates:

| Phase | Gate Evaluation | Key Fields |
|-------|----------------|------------|
| 87C | All 15 gates (generic) | decision, reason_codes, safety_notes |
| 87D | scope_check_gate | scope_evaluation (scope_status, matched files) |
| 87E | backend_invocation_gate | backend_evaluation (backend_status, requested_backend) |
| 87F | adoption/source/test mutation gates | adoption_evaluation, mutation_evaluation |
| 87G | commit/push gates | commit_evaluation, push_evaluation |

All gates produce dry-run decisions only. No gate produces `allow`. No gate enforces.
No gate authorizes. authorization_granted=false for every gate. 7249 tests pass.

## 5. Broker Architecture Role

The permission broker is:

- A **policy mediation layer** between agent/user intent and governed action execution.
- A **decision point** before backend invocation, shell command execution, mutation,
  adoption, commit, push, rollback, and storage writes.
- A **deny-by-default evaluator** that requires explicit evidence before allowing.
- A **human-review router** for high-risk or ambiguous actions.
- A future **audit-event producer** that logs decisions with evidence.

The broker is NOT:

- A shell command interceptor (that is the shell gate).
- A replacement for human approval.
- A replacement for lifecycle gates.
- An automatic action executor.

## 6. Observation Versus Authorization Boundary

The permission broker is a future mediation layer. It may consume gate dry-run evidence
and project intelligence, but it must produce explicit broker decisions before any action
is allowed. Read-only intelligence, gate dry-run output, and recommendations are not
permission by themselves.

| Input | Role |
|-------|------|
| Gate dry-run output | Evidence for broker decision |
| Project-state recommendations | Context, not permission |
| Risk register | Constraint evidence |
| Decision log | Historical context |
| Human approval | Required for high-risk actions |

## 7. Broker Design Principles

1. **Deny by default.** Missing evidence or ambiguous state results in denial.
2. **Explicit decision required.** Every broker evaluation must produce a decision.
3. **Missing evidence blocks or requires review.** Never allows on absence.
4. **Human authority remains final.** The broker routes to humans; it does not replace them.
5. **High-risk actions require human review.** Backend invocation, adoption, commit, push.
6. **Gate dry-run output informs but does not authorize.** Dry-run evidence is input, not permission.
7. **Project-state recommendations inform but do not authorize.**
8. **Accepted risk is not mitigation.** The broker must check risk_status explicitly.
9. **Must-never-repeat controls are hard constraints.** Cannot be silently overridden.
10. **Broker decisions must be auditable.** Future decisions must cite evidence.
11. **Broker must not silently mutate repo state.**
12. **Broker must not bypass lifecycle gates.**
13. **Broker must not replace shell gate.** Broker decides policy; shell gate controls execution.
14. **Broker must not replace human approval.**

## 8. Threat Model

| # | Threat | Impact | Mitigation |
|---|--------|--------|------------|
| PB-1 | Broker treats gate dry-run as allow | Unauthorized action | Broker must produce independent decision |
| PB-2 | Broker treats next_safe_action as allow | Unreviewed action | Recommendations inform, not authorize |
| PB-3 | Broker treats accepted risk as mitigation | Risk assumed resolved | Check risk_status; accepted ≠ mitigated |
| PB-4 | Broker skips human review | Safety boundary bypassed | High-risk actions must route to human |
| PB-5 | Broker grants action on missing evidence | Unverified action | Missing evidence → deny/requires_more |
| PB-6 | Broker converts review into allow silently | Review bypassed | Review decisions must be explicit |
| PB-7 | Broker bypasses task contract scope | Out-of-scope action | Scope check required before allow |
| PB-8 | Broker bypasses must-never-repeat controls | Forbidden pattern repeats | Hard constraint check required |
| PB-9 | Broker invokes backend directly | Unauthorized invocation | Broker decides, does not execute |
| PB-10 | Broker permits shell command without shell gate | Unmediated execution | Shell gate is separate enforcement |
| PB-11 | Broker permits commit/push without lifecycle | Unauthorized repo mutation | Lifecycle evidence required |
| PB-12 | Broker writes storage before storage policy | Uncontrolled state | Storage requires explicit phase |
| PB-13 | Broker decision not auditable | Unverifiable governance | Future audit events required |
| PB-14 | Broker decision not tied to evidence | Groundless permission | Evidence citation required |
| PB-15 | Broker allows raw push or force push | Must-never-repeat violation | Hard block on raw/force push |

## 9. Broker Input Model

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `broker_request_id` | string | yes | Unique request identifier |
| `requested_action` | string | yes | Action being requested |
| `requested_actor` | string | yes | Who is requesting |
| `requested_agent` | string | no | Agent involved |
| `requested_backend` | string | no | Backend target |
| `requested_command` | string | no | Shell command |
| `requested_files` | list[string] | no | Files to be affected |
| `requested_phase` | string | no | Phase context |
| `task_contract` | object | yes | Active task contract |
| `project_state` | object | no | From pcae project-state |
| `gate_dry_run` | object | no | From pcae gate-dry-run |
| `risk_register` | object | no | From pcae risk-register |
| `decision_log` | object | no | From pcae decision-log |
| `governance_timeline` | object | no | From pcae governance-timeline |
| `memory_snapshot` | object | no | From pcae memory-snapshot |
| `artifact_index` | object | no | From pcae artifact-index |
| `git_state` | object | no | Repository state |
| `health_check_state` | object | no | Health/check/doctor results |
| `human_approval` | object | no | Explicit human sign-off |

## 10. Broker Output Model

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `broker_decision_id` | string | yes | Unique decision identifier |
| `decision` | string | yes | From decision values |
| `reason_codes` | list[string] | yes | Denial/blocking reasons |
| `human_review_required` | boolean | yes | Whether human must approve |
| `more_evidence_required` | boolean | yes | Whether more evidence needed |
| `allowed_scope` | string | for allow | What is permitted |
| `denied_scope` | string | for deny | What is refused |
| `required_approvals` | list[string] | no | Approvals still needed |
| `evidence_artifacts` | list[string] | no | Artifacts consulted |
| `evidence_events` | list[string] | no | Events consulted |
| `evidence_decisions` | list[string] | no | Decisions consulted |
| `evidence_risks` | list[string] | no | Risks consulted |
| `safety_notes` | string | no | Safety annotations |
| `audit_event_required` | boolean | yes | Whether audit event needed |
| `generated_at` | string | yes | ISO 8601 timestamp |
| `schema_version` | string | yes | `"0.1"` |

## 11. Decision Model

| Decision | Meaning | Permits Action |
|----------|---------|----------------|
| `allow` | Action may proceed (future only) | yes |
| `deny` | Action is refused | no |
| `requires_human_review` | Human must approve | no (until approved) |
| `requires_more_evidence` | Evidence missing | no |
| `blocked_by_risk` | Active risk prevents | no |
| `blocked_by_scope` | Exceeds scope | no |
| `blocked_by_lifecycle_state` | Wrong lifecycle | no |
| `blocked_by_missing_artifact` | Required artifact absent | no |
| `blocked_by_must_never_repeat_control` | Hard constraint | no |
| `unknown` | Cannot determine; deny | no |

`allow` requires explicit positive evidence and must not be inferred from
recommendation text. `unknown` must never be treated as `allow`.

## 12. Human Review Model

Human review is required for:

| Action | Human Required |
|--------|----------------|
| Backend invocation | yes |
| Prompt sending | yes |
| Source mutation (outside scope) | yes |
| Test mutation (outside scope) | yes |
| Adoption execution | yes |
| Commit | yes |
| Push | yes |
| Rollback | yes |
| Storage writes | yes |
| Accepted-risk override | yes |
| Must-never-repeat override | yes |
| Permission broker activation | yes |
| Shell gate activation | yes |

## 13. Gate Relationship

- The broker **consumes** gate decisions as evidence.
- The broker **does not replace** gates.
- The broker must not treat a dry-run gate result as enforcement.
- The broker may combine gate outputs into a final broker decision.
- The broker must preserve gate evidence and reason codes.

## 14. Project Intelligence Relationship

artifact-index, memory-snapshot, governance-timeline, decision-log, risk-register,
and project-state are read-only evidence sources. They inform the broker but do not
authorize actions. The broker must cite evidence from these sources in future decisions.

## 15. Shell Gate Relationship

- Shell gate is a separate future enforcement/mediation layer.
- The broker decides whether an action is allowed in principle.
- The shell gate controls whether a shell command may execute.
- Broker without shell gate cannot guarantee shell enforcement.
- Shell gate without broker lacks full governance context.
- Both are needed for complete mediated execution.

## 16. Backend Invocation Relationship

- The broker may eventually decide whether backend invocation is allowed.
- Backend invocation still requires explicit human review/approval.
- The broker must not invoke backends directly.
- Backend invocation must pass through future gate and shell/command mediation.

## 17. Mutation/Adoption Relationship

- The broker may eventually decide whether mutation/adoption may proceed.
- Scope match is necessary but not sufficient.
- Adoption artifact presence is not approval.
- Human approval flag is not execution.
- Accepted risk is not mitigation.

## 18. Commit/Push Relationship

- The broker may eventually decide whether commit/push may proceed.
- Commit/push require lifecycle evidence, task scope, health/check status, human
  approval, and gate evidence.
- Raw git push and force push remain forbidden (must-never-repeat).

## 19. Storage/Cache Policy

- 87H creates no storage, cache, or `.pcae` persistent state.
- Future broker audit storage requires a separate explicit storage phase.
- Broker design must support auditability but not implement persistence yet.

## 20. Audit/Event Model

Future audit events the broker should produce:

| Event | Trigger |
|-------|---------|
| `broker_request_received` | Action evaluation requested |
| `broker_decision_recorded` | Decision produced |
| `broker_human_review_required` | Routed to human review |
| `broker_denied` | Action denied |
| `broker_more_evidence_required` | More evidence needed |
| `broker_allowed_future` | Action allowed (future only) |
| `broker_error` | Evaluation failure |

## 21. Failure Handling

| Condition | Broker Behavior |
|-----------|----------------|
| Missing input | requires_more_evidence |
| Unknown lifecycle state | requires_human_review or unknown |
| Active risk relevant | blocked_by_risk or requires_human_review |
| Must-never-repeat control | blocked_by_must_never_repeat_control |
| Inconsistent evidence | requires_human_review |
| Unsafe command class | deny |
| Storage unavailable | Do not write; report limitation |

## 22. Safety Invariants

1. Broker is not implemented in 87H.
2. Broker does not authorize in 87H.
3. Broker does not enforce in 87H.
4. Broker does not invoke backends in 87H.
5. Broker does not mediate shell commands in 87H.
6. Broker does not mutate repo in 87H.
7. Broker does not commit or push in 87H.
8. Broker does not write storage in 87H.
9. Future broker must deny by default.
10. Future broker must preserve evidence and reason codes.
11. Future broker must require human review for high-risk actions.
12. Future broker must not override must-never-repeat controls silently.

## 23. Future CLI/API Sketch

Illustrative only. Not implementation.

```
pcae broker evaluate --json --requested-action backend_invocation --requested-backend claude
pcae broker evaluate --json --requested-action source_mutation --requested-file src/example.py
pcae broker evaluate --json --requested-action commit --commit-message-present
pcae broker evaluate --json --requested-action push --push-target origin/main
```

## 24. Future Implementation Roadmap

| Phase | Deliverable |
|-------|-------------|
| **87I** | Shell Gate Architecture Design |
| **87J** | Phase 87 Gate/Broker Integration Tests |
| **87K** | Architecture Overview Refresh |
| **87L** | Installation / Usage Update |
| **87M** | Demo Script |
| **87N** | Governance Lifecycle Diagram |
| **87O** | README Reframe |
| **87P** | LinkedIn Article Draft |
| **88A** | First Narrow Enforced Gate Boundary |

## 25. Recommended Next Phase

**87I — Shell Gate Architecture Design.**

Before implementing a broker, PCAE also needs shell gate architecture because broker
decisions alone do not prevent unsafe shell execution.

---

permission_broker_architecture_name=phase_87_permission_broker_architecture
permission_broker_architecture_version=0.1
permission_broker_architecture_status=draft_documented
implementation_status=not_started
broker_input_fields=19
broker_output_fields=16
broker_decision_values=10
threat_model_entries=15
human_review_actions=13
safety_invariants=12
audit_event_types=7
recommended_next=87I
backend_invocation_performed=false
