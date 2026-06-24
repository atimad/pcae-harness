# Phase 88 First Narrow Enforced Gate Boundary

## 1. Purpose

Define the first narrow enforced gate boundary for PCAE: a small, auditable,
reversible, deny-by-default enforcement point that moves beyond dry-run evaluation
toward actual preflight blocking.

## 2. Scope

Design and planning only. This artifact defines the boundary, rollout rules,
safety invariants, test strategy, and acceptance criteria. It does not implement
enforcement.

## 3. Non-Goals

- Implementing any enforced gate.
- Implementing scope preflight.
- Implementing permission broker or shell gate.
- Creating storage, cache, or `.pcae` persistent state.
- Modifying source code, tests, or existing artifacts.
- Backend invocation, prompt sending, capture, intake, or adoption.

## 4. Starting Point from Phase 87

Phase 87 delivered:

| Layer | Status |
|-------|--------|
| Gate dry-run evaluator (15 gates) | Implemented |
| Scope gate with task contract evaluation | Implemented (dry-run) |
| Backend invocation gate | Implemented (dry-run) |
| Adoption/mutation gate | Implemented (dry-run) |
| Commit/push gate | Implemented (dry-run) |
| Permission broker architecture | Designed, not implemented |
| Shell gate architecture | Designed, not implemented |
| Integration tests | 7,278 passing |

All gates produce dry-run decisions only. No gate enforces. No gate authorizes.
`authorization_granted=false` for every gate.

## 5. Why Enforcement Must Start Narrow

Broad enforcement is dangerous:

- Blocking too many actions causes false positives that erode trust.
- Enforcing backend invocation requires the full broker/shell-gate stack.
- Enforcing commit/push requires lifecycle integration that doesn't exist yet.
- Enforcing adoption requires intake/review infrastructure.

Narrow enforcement is safe:

- Start with one gate that has well-understood inputs and outputs.
- Verify false-positive rate before expanding.
- Keep existing dry-run behavior intact.
- Provide a clear rollback path if enforcement causes problems.

## 6. Candidate Enforced Gates

| Gate | Complexity | Dependencies | Risk | Recommendation |
|------|-----------|--------------|------|----------------|
| `scope_gate_preflight` | Low | Task contract, fnmatch | Low | **First candidate** |
| `backend_invocation_preflight` | High | Broker, shell gate | Critical | Defer |
| `adoption_mutation_preflight` | High | Adoption pipeline | High | Defer |
| `commit_preflight` | Medium | Lifecycle, health | High | Defer |
| `push_preflight` | Medium | Lifecycle, upstream | High | Defer |
| `storage_write_preflight` | Medium | Storage gate | High | Defer |
| `rollback_preflight` | Medium | Rollback pipeline | High | Defer |

## 7. Recommended First Enforced Boundary

**`scope_gate_preflight`** — scope-gate enforcement for explicitly requested
file/action combinations.

Rationale:

- Scope gate dry-run already exists and is tested (87D).
- Scope decisions use task contract allowed/forbidden files — well-understood inputs.
- Scope preflight can block out-of-scope file mutations before they happen.
- It operates independently of backend invocation, adoption, commit, push,
  permission broker, and shell gate.
- It can be tested with deterministic inputs and outputs.
- False positives are easy to diagnose (file path vs. task contract pattern).

## 8. Scope Gate Preflight Model

A future command or lifecycle hook asks:

> Is `requested_action` allowed for `requested_file` under the active task contract?

### Future Inputs

| Field | Type | Required |
|-------|------|----------|
| `requested_action` | string | yes |
| `requested_files` | list[string] | yes |
| `active_task_contract` | object | yes |
| `allowed_files` | list[string] | from contract |
| `forbidden_files` | list[string] | from contract |
| `lifecycle_state` | string | yes |
| `human_approval` | object | no |
| `risk_register` | object | no |
| `must_never_repeat_controls` | list | no |
| `project_state` | object | no |

### Future Outputs

| Field | Type | Required |
|-------|------|----------|
| `preflight_decision` | string | yes |
| `reason_codes` | list[string] | yes |
| `matched_allowed_files` | list[string] | yes |
| `matched_forbidden_files` | list[string] | yes |
| `unknown_files` | list[string] | yes |
| `human_review_required` | boolean | yes |
| `more_evidence_required` | boolean | yes |
| `evidence_sources` | list[string] | yes |
| `safety_notes` | string | no |

## 9. Enforcement Decision Model

| Decision | Meaning | Permits Action |
|----------|---------|----------------|
| `allow_preflight` | Action may proceed (future) | yes |
| `deny_preflight` | Action is refused | no |
| `requires_human_review` | Human must approve | no (until approved) |
| `requires_more_evidence` | Evidence missing | no |
| `blocked_by_scope` | File out of scope | no |
| `blocked_by_lifecycle_state` | Lifecycle wrong | no |
| `blocked_by_missing_task_contract` | No contract | no |
| `blocked_by_must_never_repeat_control` | Hard constraint | no |
| `blocked_by_risk` | Active risk | no |
| `unknown` | Cannot determine; deny | no |

`allow_preflight` is future-only. `unknown` must never be treated as allow.
Missing evidence must deny or require review. Human approval alone must not
bypass task scope. Dry-run result alone must not become enforcement automatically.

## 10. Deny-by-Default Rules

1. No active task contract → deny or requires_more_evidence
2. Requested file outside allowed_files → deny
3. Requested file matches forbidden_files → deny
4. Unknown requested file → requires_human_review or requires_more_evidence
5. Unknown requested action → requires_human_review
6. Accepted risk → not mitigation, does not authorize
7. Must-never-repeat control applies → deny
8. Lifecycle state not ready → deny
9. Human approval without scope evidence → not enough
10. Dry-run recommendation → not authorization

## 11. Human Review Model

Human review required for:

- Unknown file scope
- Ambiguous file match
- Forbidden path request
- Accepted-risk override
- Must-never-repeat override
- Missing task contract
- Out-of-lifecycle action
- Backend invocation (future)
- Mutation/adoption (future)
- Commit/push (future)
- Storage write (future)
- Rollback (future)

## 12. Failure Handling

| Condition | Preflight Behavior |
|-----------|---------------------|
| Missing task contract | deny or requires_more_evidence |
| Missing project state | requires_more_evidence |
| Stale risk register | requires_human_review |
| Ambiguous glob match | requires_human_review |
| Conflicting allowed/forbidden | deny |
| Invalid requested action | deny |
| Unknown state | unknown (never allow) |

## 13. Rollback/Recovery Strategy

- First enforcement must be reversible.
- Must support disabling enforcement if false positives are found.
- Must log/describe denied action without mutating repo.
- Must preserve existing dry-run command behavior.
- Must not block health/check/doctor/read-only inspection.
- Must not interfere with final governed `pcae push` unless explicitly scoped
  in a later phase.

## 14. Audit Requirements

Future audit events:

| Event | Trigger |
|-------|---------|
| `preflight_request_received` | Preflight evaluation requested |
| `preflight_decision_recorded` | Decision produced |
| `preflight_denied` | Action denied |
| `preflight_human_review_required` | Routed to human review |
| `preflight_more_evidence_required` | More evidence needed |
| `preflight_error` | Evaluation failure |

## 15. Storage/Cache Policy

- 88A creates no storage, cache, or `.pcae` persistent state.
- Future enforcement logging/storage requires a separate explicit phase.
- Preflight decisions should be reported in command output (stdout/stderr),
  not persisted to files, until a storage gate phase approves persistence.

## 16. Test Strategy

Tests for future 88B (not implemented in 88A):

- In-scope file preflight → allow_preflight
- Out-of-scope file preflight → deny_preflight or blocked_by_scope
- Forbidden file preflight → deny_preflight
- Unknown file preflight → requires_human_review or requires_more_evidence
- Missing task contract → deny_preflight or blocked_by_missing_task_contract
- Ambiguous glob match → requires_human_review
- Human approval does not bypass scope
- Accepted risk does not authorize
- Must-never-repeat blocks
- Dry-run command remains non-authorizing
- No-write/no-storage behavior
- Existing read-only commands still work
- Existing dry-run gates still work

## 17. Safety Invariants

1. 88A does not implement enforcement.
2. 88A does not authorize execution.
3. 88A does not mutate repo beyond docs/status/task files.
4. 88A does not invoke backends.
5. 88A does not send prompts.
6. 88A does not capture outputs.
7. 88A does not perform intake, adoption, or mutation.
8. 88A does not stage/commit/push except final phase commits and governed push.
9. Future enforcement starts with one narrow gate only.
10. Future enforcement must deny by default.
11. Future enforcement must be reversible.
12. Future enforcement must preserve dry-run behavior.
13. Future enforcement must not imply full autonomy.
14. Future enforcement must not replace human approval.
15. Future enforcement must not replace lifecycle gates.

## 18. Future Implementation Roadmap

| Phase | Deliverable |
|-------|-------------|
| **88B** | Scope Gate Preflight Prototype |
| **88C** | Scope Gate Preflight Tests and False-Positive Review |
| **88D** | Backend Invocation Preflight Design |
| **88E** | Mutation/Adoption Preflight Design |
| **88F** | Commit/Push Preflight Design |

## 19. Recommended Next Phase

**88B — Scope Gate Preflight Prototype.**

88B should implement the narrow scope-gate preflight evaluator that can return
`allow_preflight` or `deny_preflight` for explicitly requested file/action
combinations against the active task contract. Dry-run behavior must remain
intact. The preflight must be opt-in and reversible.

---

phase_88_boundary_name=phase_88_first_enforced_gate_boundary
phase_88_boundary_version=0.1
phase_88_boundary_status=draft_documented
implementation_status=not_started
recommended_first_enforced_gate=scope_gate_preflight
candidate_gates_evaluated=7
enforcement_decision_values=10
deny_by_default_rules=10
human_review_triggers=12
failure_conditions=7
safety_invariants=15
future_test_areas=13
recommended_next=88B
backend_invocation_performed=false
