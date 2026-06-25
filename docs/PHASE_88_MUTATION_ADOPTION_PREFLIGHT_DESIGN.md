# Phase 88G Mutation/Adoption Preflight Design

## 1. Purpose

Define the mutation/adoption preflight boundary for PCAE: how PCAE should
evaluate proposed repo mutations and proposed adoption of backend/captured
output before any file modification, output application, adoption review,
adoption approval, adoption execution, commit, or push occurs.

88G defines the mutation/adoption preflight boundary but does not implement
mutation/adoption preflight. No file is modified, no backend output is applied,
no adoption review is performed, no adoption approval is granted, no adoption
execution is performed, and no mutation permission is granted in this phase.

## 2. Scope

Design and planning only. This artifact defines mutation/adoption request
models, preflight output model, decision values, deny-by-default rules,
evidence requirements, adoption lifecycle separation, and safety invariants.

## 3. Non-Goals

- Implementing mutation/adoption preflight.
- Performing mutation, adoption, or output application.
- Implementing commit/push preflight.
- Implementing permission broker or shell gate.
- Creating storage, cache, or `.pcae` persistent state.
- Modifying source code, tests, or existing artifacts.

## 4. Starting Point from 88A–88F

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 88A | First Narrow Enforced Gate Boundary | Design complete |
| 88B | Scope Gate Preflight Prototype | Implemented, 66 tests |
| 88C | Scope Gate Preflight Review | 63 edge-case tests, reviewed |
| 88D | Backend Invocation Preflight Design | Design complete |
| 88D.1 | Test Runtime Tiering | quick/governance/full tiers |
| 88E | Backend Invocation Preflight Prototype | Implemented, 42 tests |
| 88F | Backend Invocation Preflight Review | 47 edge-case tests, reviewed |

Two explicit preflight commands exist: `pcae preflight scope` (file/action
scope evaluation) and `pcae preflight backend` (backend invocation evidence
evaluation). Mutation/adoption preflight extends this foundation by evaluating
whether proposed repo modifications and output adoption have sufficient
evidence to proceed.

## 5. Relationship to Scope Preflight

- Scope preflight evaluates requested file/action boundaries.
- Mutation/adoption preflight consumes scope preflight evidence.
- Scope allow is necessary but not sufficient for mutation.
- Scope denial blocks mutation/adoption.
- Scope unknown requires more evidence or review.

## 6. Relationship to Backend Invocation Preflight

- Backend preflight evaluates whether backend invocation evidence is acceptable.
- Mutation/adoption preflight consumes backend evidence when output originated
  from a backend.
- Backend preflight does not authorize adoption.
- Backend recognition does not authorize mutation.

## 7. Relationship to Existing Output Intake/Review/Adoption Lifecycle

PCAE's existing lifecycle (Phases 55–62, 75–77) defines:

- **Capture**: backend output stored with metadata (prompt hash, backend ID).
- **Intake**: captured output classified for review.
- **Review**: human examines captured output.
- **Approval**: human approves reviewed output for adoption.
- **Execution**: approved output applied to repository.

Mutation/adoption preflight sits before this entire chain — it evaluates
whether there is sufficient evidence to begin the lifecycle, not whether
the lifecycle steps have been completed. Future integration may require
preflight before each lifecycle step.

## 8. Why Mutation/Adoption Is High Risk

1. **Irreversible file changes.** Mutations modify repository files. Once
   committed and pushed, reverting requires explicit rollback.
2. **Scope violation risk.** Mutation could touch files outside task scope.
3. **Backend output trust.** Adopting backend output trusts external AI
   judgment without guaranteed correctness.
4. **Chain effects.** Mutation leads to commit → push — a full persistent chain.
5. **Review bypass risk.** Allowing mutation without evidence creates a path
   to unreviewed changes.
6. **Multi-file complexity.** Multi-file mutations are harder to review and
   may have cross-file dependencies.

## 9. Mutation Request Model

Future inputs:

| Field | Type | Required |
|-------|------|----------|
| `requested_action` | string | yes |
| `requested_files` | list[string] | yes |
| `requested_change_type` | string | no |
| `requested_change_source` | string | no |
| `task_contract_detected` | boolean | yes |
| `task_contract_path` | string | no |
| `scope_preflight_decision` | string | no |
| `backend_preflight_decision` | string | no |
| `captured_output_present` | boolean | no |
| `captured_output_path` | string | no |
| `captured_output_hash` | string | no |
| `diff_present` | boolean | no |
| `diff_hash` | string | no |
| `human_approval` | object | no |
| `risk_register` | object | no |
| `decision_log` | object | no |
| `project_state` | object | no |
| `lifecycle_state` | string | yes |

## 10. Adoption Request Model

Future inputs:

| Field | Type | Required |
|-------|------|----------|
| `adoption_action` | string | yes |
| `captured_output_present` | boolean | yes |
| `captured_output_path` | string | no |
| `captured_output_hash` | string | no |
| `adoption_review_present` | boolean | no |
| `adoption_review_path` | string | no |
| `adoption_approval_present` | boolean | no |
| `adoption_approval_path` | string | no |
| `source_backend` | string | no |
| `source_prompt_hash` | string | no |
| `source_task_contract` | string | no |
| `requested_files` | list[string] | no |
| `scope_preflight_decision` | string | no |
| `backend_preflight_decision` | string | no |
| `human_approval` | object | no |
| `risk_register` | object | no |
| `decision_log` | object | no |
| `lifecycle_state` | string | yes |

## 11. Mutation/Adoption Preflight Decision Model

Future outputs:

| Field | Type | Required |
|-------|------|----------|
| `preflight_type` | string | yes |
| `requested_action` | string | yes |
| `requested_files` | list[string] | yes |
| `decision` | string | yes |
| `reason_codes` | list[string] | yes |
| `task_contract_detected` | boolean | yes |
| `task_contract_path` | string | no |
| `scope_preflight_required` | boolean | yes |
| `scope_preflight_decision` | string | no |
| `backend_preflight_required` | boolean | yes |
| `backend_preflight_decision` | string | no |
| `captured_output_required` | boolean | yes |
| `captured_output_present` | boolean | yes |
| `captured_output_hash_present` | boolean | yes |
| `diff_required` | boolean | yes |
| `diff_present` | boolean | yes |
| `adoption_review_required` | boolean | yes |
| `adoption_review_present` | boolean | yes |
| `adoption_approval_required` | boolean | yes |
| `adoption_approval_present` | boolean | yes |
| `human_review_required` | boolean | yes |
| `more_evidence_required` | boolean | yes |
| `evidence_sources` | list[string] | yes |
| `safety_notes` | string | no |
| `authorization_granted` | boolean | yes |
| `execution_authorized` | boolean | yes |
| `mutation_performed` | boolean | yes |
| `adoption_review_performed` | boolean | yes |
| `adoption_approval_granted` | boolean | yes |
| `adoption_execution_performed` | boolean | yes |
| `backend_invocation_performed` | boolean | yes |
| `prompt_sent` | boolean | yes |
| `capture_performed` | boolean | yes |
| `commit_performed` | boolean | yes |
| `push_performed` | boolean | yes |
| `storage_written` | boolean | yes |

## 12. Decision Values

| Decision | Meaning |
|----------|---------|
| `allow_preflight` | Preflight check passed (future only) |
| `deny_preflight` | Preflight check failed |
| `requires_human_review` | Human must review |
| `requires_more_evidence` | Evidence missing |
| `blocked_by_scope` | Scope denied |
| `blocked_by_backend_policy` | Backend policy violation |
| `blocked_by_missing_task_contract` | No contract |
| `blocked_by_missing_capture` | No captured output |
| `blocked_by_missing_diff` | No diff/patch |
| `blocked_by_missing_adoption_review` | No review record |
| `blocked_by_missing_adoption_approval` | No approval record |
| `blocked_by_lifecycle_state` | Lifecycle wrong |
| `blocked_by_risk` | Active risk |
| `unknown` | Cannot determine; deny |

## 13. Deny-by-Default Rules

1. Missing task contract → deny or requires_more_evidence
2. Missing scope preflight for file mutation → requires_more_evidence
3. Scope preflight denied → deny
4. Missing backend preflight for backend-originated output → requires_more_evidence
5. Backend preflight denied → deny
6. Missing captured output for adoption → blocked_by_missing_capture
7. Missing output hash for adoption → requires_more_evidence
8. Missing diff for patch adoption → blocked_by_missing_diff
9. Missing adoption review before approval → blocked_by_missing_adoption_review
10. Missing adoption approval before execution → blocked_by_missing_adoption_approval
11. Active risk → blocked_by_risk or requires_human_review
12. Must-never-repeat control applies → deny
13. Unknown action → unknown or requires_human_review
14. Unknown file → requires_more_evidence or requires_human_review
15. Forbidden file → blocked_by_scope
16. Human approval without evidence → not enough
17. Accepted risk → not mitigation

## 14. Human Review Model

Human review required for:

- Any mutation request
- Any adoption request
- Source mutation
- Test mutation
- Captured output adoption
- Adoption approval
- Adoption execution
- Out-of-scope file
- Forbidden file
- Backend-originated output
- Multi-file mutation
- Diff touches source/tests/governance files
- Accepted-risk override
- Must-never-repeat override
- Missing or stale task contract
- Unknown action or file

## 15. Evidence Model

Evidence required for future mutation/adoption:

- Active task contract with requested files
- Scope preflight decision for affected files
- Backend preflight decision when backend output is involved
- Captured output path/hash when adoption is involved
- Diff/patch hash when mutation applies a patch
- Adoption review record before approval
- Adoption approval record before execution
- Human approval record when required
- Risk/decision/project-state evidence

## 16. Captured Output Relationship

- Captured output is evidence, not authorization.
- Captured output must be reviewed before adoption.
- Captured output must not be applied directly by preflight.
- Captured output hash/provenance should be preserved.
- Captured output from unknown backend must require review or denial.

## 17. Scope Relationship

- Scope preflight evaluates requested file/action boundaries.
- Mutation/adoption preflight consumes scope preflight evidence.
- Scope allow is necessary but not sufficient.
- Scope denial blocks mutation/adoption.
- Scope unknown requires more evidence or review.

## 18. Backend Relationship

- Backend preflight evaluates whether backend invocation evidence is acceptable.
- Mutation/adoption preflight consumes backend evidence when output originated
  from a backend.
- Backend preflight does not authorize adoption.
- Backend recognition does not authorize mutation.

## 19. Diff/Patch Relationship

- Diff presence may be required for adoption.
- Diff must be reviewed before mutation.
- Diff hash/provenance should be preserved.
- Diff touching forbidden files must block.
- Diff touching unknown files requires review.
- Diff application is separate from preflight.

## 20. Test Mutation Relationship

Test mutation requires scope evidence but is lower risk than source mutation.
Still requires human review and task contract scope match.

## 21. Documentation Mutation Relationship

Documentation mutation requires scope evidence. Lower risk than source/test
but still requires task contract scope match and evidence.

## 22. Source Mutation Relationship

Source mutation is the highest-risk mutation type. Requires scope evidence,
backend evidence when output is backend-originated, and always requires
human review.

## 23. Adoption Review/Approval/Execution Separation

- **Adoption review** decides whether output should be examined. Separate gate.
- **Adoption approval** decides whether reviewed output may be applied. Separate gate.
- **Adoption execution** applies approved output. Separate gate.
- Mutation/adoption preflight does not perform any of these.
- Each step must remain separately auditable.

## 24. Commit/Push Relationship

- Mutation/adoption preflight does not authorize commit.
- Mutation/adoption preflight does not authorize push.
- Commit and push remain separate future preflight boundaries (88J–88K).

## 25. Permission Broker Relationship

A future permission broker may combine scope, backend, mutation/adoption,
commit/push, risk, lifecycle, and human review into a final decision.
Mutation/adoption preflight must not claim broker approval.

## 26. Shell Gate Relationship

Actual mutation may happen through shell commands, file writes, patch apply,
or tools. A future shell gate must mediate concrete command execution.
Mutation/adoption preflight alone cannot guarantee shell enforcement.

## 27. Audit Requirements

Future audit events:

| Event | Trigger |
|-------|---------|
| `mutation_preflight_request_received` | Mutation preflight requested |
| `mutation_preflight_decision_recorded` | Decision produced |
| `mutation_preflight_denied` | Mutation denied |
| `mutation_preflight_human_review_required` | Routed to review |
| `mutation_preflight_more_evidence_required` | Evidence missing |
| `adoption_preflight_request_received` | Adoption preflight requested |
| `adoption_preflight_decision_recorded` | Decision produced |
| `adoption_preflight_denied` | Adoption denied |
| `adoption_preflight_human_review_required` | Routed to review |
| `adoption_preflight_more_evidence_required` | Evidence missing |
| `mutation_adoption_preflight_error` | Evaluation failure |

## 28. Storage/Cache Policy

- 88G creates no storage, cache, or `.pcae` persistent state.
- Future mutation/adoption preflight storage/audit requires a separate phase.
- Preflight decisions should be reported in command output, not persisted.

## 29. Failure Handling

| Condition | Behavior |
|-----------|----------|
| Missing task contract | requires_more_evidence or deny |
| Missing scope evidence | requires_more_evidence |
| Scope denied | deny |
| Missing backend evidence for backend output | requires_more_evidence |
| Missing captured output | deny or requires_more_evidence |
| Missing diff | requires_more_evidence |
| Missing review before approval | deny |
| Missing approval before execution | deny |
| Active risk | blocked_by_risk or requires_human_review |
| Must-never-repeat applies | deny |
| Unknown state | unknown, never allow |

## 30. Safety Invariants

1. 88G does not implement mutation/adoption preflight.
2. 88G does not mutate files.
3. 88G does not apply captured output.
4. 88G does not perform adoption review.
5. 88G does not grant adoption approval.
6. 88G does not perform adoption execution.
7. 88G does not invoke backends.
8. 88G does not send prompts.
9. 88G does not capture outputs.
10. 88G does not perform intake.
11. 88G does not stage files except normal docs/status/task commits.
12. 88G does not commit except phase commits.
13. 88G does not push except governed final pcae push.
14. 88G does not write storage/cache/.pcae.
15. Future mutation/adoption preflight must deny by default.
16. Future mutation/adoption preflight must require human review.
17. Future mutation/adoption preflight must not bypass scope preflight.
18. Future mutation/adoption preflight must not bypass backend preflight when
    backend output is involved.
19. Future mutation/adoption preflight must not imply commit/push authorization.
20. Future mutation/adoption preflight must preserve evidence and reason codes.

## 31. Future Test Strategy

Tests for future 88H:

- Docs mutation in scope → requires_human_review
- Source mutation in scope → requires_human_review
- Test mutation in scope → requires_human_review
- Forbidden file mutation → blocked_by_scope
- Unknown file mutation → requires_more_evidence
- Multi-file all allowed
- Multi-file mixed allowed/forbidden
- Multi-file mixed allowed/unknown
- Missing task contract → blocked_by_missing_task_contract
- Missing scope preflight → requires_more_evidence
- Scope denied → deny
- Backend output without backend preflight → requires_more_evidence
- Backend output with backend preflight but no capture → blocked_by_missing_capture
- Capture present but no hash → requires_more_evidence
- Diff missing → requires_more_evidence
- Diff touches forbidden file → blocked_by_scope
- Adoption approval without review → blocked_by_missing_adoption_review
- Adoption execution without approval → blocked_by_missing_adoption_approval
- Human approval does not bypass evidence
- authorization_granted remains false
- execution_authorized remains false
- mutation_performed remains false
- adoption_review_performed remains false
- adoption_approval_granted remains false
- adoption_execution_performed remains false
- commit_performed remains false
- push_performed remains false
- storage_written remains false

## 32. Future Implementation Roadmap

| Phase | Deliverable |
|-------|-------------|
| **88H** | Mutation/Adoption Preflight Prototype |
| **88I** | Mutation/Adoption Preflight Tests and False-Positive Review |
| **88J** | Commit/Push Preflight Design |
| **88K** | Commit/Push Preflight Prototype |
| **88L** | Scope + Backend + Mutation/Adoption Preflight Integration Verification |

## 33. Recommended Next Phase

**88H — Mutation/Adoption Preflight Prototype.**

88H should implement the mutation/adoption preflight evaluator as an explicit
command that evaluates proposed mutations and adoptions against scope, backend,
task contract, captured output, diff, adoption lifecycle, and human review
evidence. It must deny by default and never perform mutation, adoption, or
commit.

---

mutation_adoption_preflight_design_name=phase_88_mutation_adoption_preflight_design
mutation_adoption_preflight_design_version=0.1
mutation_adoption_preflight_design_status=draft_documented
implementation_status=not_started
mutation_actions=10
mutation_request_model_fields=18
adoption_request_model_fields=18
output_model_fields=36
decision_values=14
deny_by_default_rules=17
human_review_triggers=16
audit_event_types=11
failure_conditions=11
safety_invariants=20
future_test_areas=28
recommended_next=88H
backend_invocation_performed=false
