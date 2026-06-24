# Phase 87 Action Gate Taxonomy and Decision Model

## 1. Purpose

Define the formal action-gate taxonomy and decision model for Phase 87. This artifact
specifies gate types, input requirements, decision outputs, denial/blocking reason codes,
human-review triggers, evidence requirements, and safety invariants. It provides the shared
vocabulary and model that all subsequent 87-series phases will reference.

## 2. Scope

Design only. This artifact defines gate types, decision semantics, and contracts. It does
not implement gates, create storage, modify source code, or add tests.

## 3. Non-Goals

- Implementing any action gate, dry-run evaluator, permission broker, or shell gate.
- Creating `.pcae` storage, generated cache, machine-readable schema files, or state files.
- Modifying source code, tests, README, or existing artifacts.
- Backend invocation, prompt sending, capture, intake, or adoption.

## 4. Relationship to 87A

The 87A governed action gates plan defined:

- 12 design principles, 15-threat model, 15 candidate gates, 10 gate decisions,
  10 gate input sources, 13 human approval boundaries, 12 safety invariants,
  10-phase rollout roadmap.

This artifact (87B) refines 87A's candidates into a formal taxonomy with:

- Precise gate definitions, categories, lifecycle states, decision outputs, reason codes,
  input/output models, evidence requirements, deny-by-default rules, validation rules,
  and failure cases.

## 5. Observation Versus Authorization Boundary

Read-only project intelligence can inform an action gate, but it cannot decide permission
by itself. A gate decision must be explicit, evidence-backed, scoped, and deny-by-default.

| Read-Only Intelligence | Action Gate Decision |
|------------------------|---------------------|
| Observes state | Evaluates permission |
| Reports recommendations | Produces allow/deny |
| Cannot authorize | Must explicitly authorize or deny |
| Cannot write | May inform a write decision |
| Cannot invoke | May inform an invocation decision |

---

## 6. Action Gate Design Principles

1. Observation is not authorization.
2. Recommendation is not permission.
3. Gate decisions are explicit (allow/deny/blocked/review).
4. Deny by default when evidence is missing or ambiguous.
5. Missing evidence blocks or requires review — never allows.
6. Human approval required for high-risk actions.
7. Accepted risk is not mitigation.
8. Must-never-repeat controls are enforceable constraints, not suggestions.
9. Read-only commands remain read-only.
10. Gate output must distinguish allow, deny, blocked, and review states.
11. Write-capable gates require later explicit implementation phases.
12. Permission broker and shell gate remain future architecture layers.

## 7. Threat Model

| # | Threat | Impact | Mitigation |
|---|--------|--------|------------|
| GT-1 | project-state recommendation treated as allow | Unauthorized action | Gate must produce independent decision, not consume recommendation |
| GT-2 | decision-log record treated as active approval | Stale approval reused | Gate must check decision freshness and scope |
| GT-3 | Accepted risk treated as mitigation | Risk assumed resolved | Gate must check risk_status; accepted ≠ mitigated |
| GT-4 | Stale signal ignored | Outdated evidence drives decision | Gate must check freshness; stale requires review |
| GT-5 | Must-never-repeat control bypassed | Forbidden pattern repeats | Gate must check must_never_repeat before allow |
| GT-6 | Missing evidence treated as safe | Action proceeds without basis | Missing evidence → deny or requires_more_evidence |
| GT-7 | Scope mismatch ignored | Action exceeds authorized scope | Gate must check task contract allowed/forbidden files |
| GT-8 | Lifecycle state ignored | Action at wrong lifecycle stage | Gate must check lifecycle_state compatibility |
| GT-9 | Human review skipped for high-risk action | Safety boundary bypassed | High-risk gates must require human_review |
| GT-10 | Gate output ambiguity causes unsafe action | Unclear decision acted upon | Gate output must be one of defined decision values |
| GT-11 | Gate silently permits write behavior | Unauthorized mutation | Write-capable gates require explicit implementation phase |
| GT-12 | Read-only command gains write authority | Boundary collapse | Existing commands must remain read-only |
| GT-13 | Permission broker implemented before policy stable | Unscoped authority | Broker requires 87H architecture design first |
| GT-14 | Shell gate implemented before taxonomy stable | Unscoped interception | Shell gate requires 87I architecture design first |
| GT-15 | Storage introduced before storage gate | Uncontrolled state | Storage requires explicit storage gate phase |

---

## 8. Gate Taxonomy

### 8.1 task_start_gate

| Field | Value |
|-------|-------|
| gate_id | `task_start_gate` |
| gate_name | Task Start Gate |
| gate_category | `planning_gate` |
| protected_action | Starting a new task or phase |
| risk_level | medium |
| required_inputs | task_contract, project_state, memory_snapshot |
| required_evidence | completed previous phase, clean push state |
| human_review_required | no (dry-run first) |
| default_decision | `requires_more_evidence` |
| allowed_decisions | allow, deny, requires_human_review, requires_more_evidence, blocked_by_lifecycle_state |
| must_never_repeat_controls | none specific |
| read_only_sources | project-state, memory-snapshot |
| forbidden_side_effects | no file writes, no storage |
| future_implementation_phase | 87D |

### 8.2 scope_check_gate

| Field | Value |
|-------|-------|
| gate_id | `scope_check_gate` |
| gate_name | Scope Check Gate |
| gate_category | `scope_gate` |
| protected_action | Modifying files within task scope |
| risk_level | medium |
| required_inputs | task_contract, requested_files, artifact_index |
| required_evidence | task contract with allowed/forbidden files |
| human_review_required | no |
| default_decision | `deny` |
| allowed_decisions | allow, deny, blocked_by_scope |
| must_never_repeat_controls | mutation outside scope |
| read_only_sources | artifact-index, project-state |
| forbidden_side_effects | no file writes, no storage |
| future_implementation_phase | 87D |

### 8.3 backend_invocation_gate

| Field | Value |
|-------|-------|
| gate_id | `backend_invocation_gate` |
| gate_name | Backend Invocation Gate |
| gate_category | `backend_gate` |
| protected_action | Invoking a backend agent (claude, claude-deepseek, etc.) |
| risk_level | critical |
| required_inputs | task_contract, project_state, risk_register, agent_identity, prompt_hash |
| required_evidence | approved agent, approved prompt, guard checks passed |
| human_review_required | yes |
| default_decision | `deny` |
| allowed_decisions | allow, deny, requires_human_review, blocked_by_risk, blocked_by_must_never_repeat_control |
| must_never_repeat_controls | invocation without guard |
| read_only_sources | project-state, risk-register, decision-log |
| forbidden_side_effects | no file writes, no storage (evaluation only) |
| future_implementation_phase | 87E |

### 8.4 prompt_send_gate

| Field | Value |
|-------|-------|
| gate_id | `prompt_send_gate` |
| gate_name | Prompt Send Gate |
| gate_category | `prompt_gate` |
| protected_action | Sending a prompt to a backend |
| risk_level | critical |
| required_inputs | task_contract, prompt_package, prompt_hash, backend_invocation_gate_decision |
| required_evidence | approved prompt package, backend gate allowed |
| human_review_required | yes |
| default_decision | `deny` |
| allowed_decisions | allow, deny, requires_human_review, blocked_by_risk |
| must_never_repeat_controls | prompt sending without lifecycle authorization |
| read_only_sources | decision-log, risk-register |
| forbidden_side_effects | no file writes, no storage (evaluation only) |
| future_implementation_phase | 87E |

### 8.5 capture_acceptance_gate

| Field | Value |
|-------|-------|
| gate_id | `capture_acceptance_gate` |
| gate_name | Capture Acceptance Gate |
| gate_category | `capture_gate` |
| protected_action | Accepting captured backend output for further processing |
| risk_level | high |
| required_inputs | capture_metadata, prompt_hash, backend_invocation_evidence |
| required_evidence | capture hash matches, timing within bounds |
| human_review_required | depends on capture classification |
| default_decision | `requires_more_evidence` |
| allowed_decisions | allow, deny, requires_human_review, requires_more_evidence |
| must_never_repeat_controls | capture without evidence |
| read_only_sources | governance-timeline |
| forbidden_side_effects | no file writes, no storage (evaluation only) |
| future_implementation_phase | 87F |

### 8.6 intake_review_gate

| Field | Value |
|-------|-------|
| gate_id | `intake_review_gate` |
| gate_name | Intake Review Gate |
| gate_category | `review_gate` |
| protected_action | Classifying captured output for adoption review |
| risk_level | high |
| required_inputs | capture_acceptance_gate_decision, intake_classification |
| required_evidence | capture accepted, classification complete |
| human_review_required | depends on finding severity |
| default_decision | `requires_more_evidence` |
| allowed_decisions | allow, deny, requires_human_review, requires_more_evidence |
| must_never_repeat_controls | intake before capture |
| read_only_sources | governance-timeline, decision-log |
| forbidden_side_effects | no file writes, no storage (evaluation only) |
| future_implementation_phase | 87F |

### 8.7 adoption_approval_gate

| Field | Value |
|-------|-------|
| gate_id | `adoption_approval_gate` |
| gate_name | Adoption Approval Gate |
| gate_category | `review_gate` |
| protected_action | Approving an adoption candidate for execution |
| risk_level | critical |
| required_inputs | intake_review_gate_decision, adoption_candidate, task_contract |
| required_evidence | intake reviewed, candidate classified, scope verified |
| human_review_required | yes |
| default_decision | `deny` |
| allowed_decisions | allow, deny, requires_human_review, blocked_by_risk, blocked_by_scope |
| must_never_repeat_controls | adoption without approval |
| read_only_sources | decision-log, risk-register, artifact-index |
| forbidden_side_effects | no file writes, no storage (evaluation only) |
| future_implementation_phase | 87F |

### 8.8 source_mutation_gate

| Field | Value |
|-------|-------|
| gate_id | `source_mutation_gate` |
| gate_name | Source Mutation Gate |
| gate_category | `mutation_gate` |
| protected_action | Modifying source code files |
| risk_level | high |
| required_inputs | task_contract, requested_files, scope_check_gate_decision |
| required_evidence | task contract allows mutation, scope verified |
| human_review_required | yes (outside explicit scope) |
| default_decision | `deny` |
| allowed_decisions | allow, deny, requires_human_review, blocked_by_scope |
| must_never_repeat_controls | mutation outside scope |
| read_only_sources | project-state, artifact-index |
| forbidden_side_effects | no storage (evaluation only) |
| future_implementation_phase | 87F |

### 8.9 test_mutation_gate

| Field | Value |
|-------|-------|
| gate_id | `test_mutation_gate` |
| gate_name | Test Mutation Gate |
| gate_category | `test_gate` |
| protected_action | Modifying test files |
| risk_level | medium |
| required_inputs | task_contract, requested_files, scope_check_gate_decision |
| required_evidence | task contract allows test mutation |
| human_review_required | depends on scope |
| default_decision | `deny` |
| allowed_decisions | allow, deny, requires_human_review, blocked_by_scope |
| must_never_repeat_controls | test mutation outside scope |
| read_only_sources | project-state, artifact-index |
| forbidden_side_effects | no storage (evaluation only) |
| future_implementation_phase | 87F |

### 8.10 commit_gate

| Field | Value |
|-------|-------|
| gate_id | `commit_gate` |
| gate_name | Commit Gate |
| gate_category | `commit_gate` |
| protected_action | Creating a git commit |
| risk_level | high |
| required_inputs | task_contract, project_state, pcae_check_result, pcae_health_result |
| required_evidence | health passes, check passes, scope verified |
| human_review_required | yes |
| default_decision | `deny` |
| allowed_decisions | allow, deny, requires_human_review, blocked_by_lifecycle_state, blocked_by_missing_artifact |
| must_never_repeat_controls | hook bypass |
| read_only_sources | project-state, memory-snapshot |
| forbidden_side_effects | no storage (evaluation only) |
| future_implementation_phase | 87G |

### 8.11 push_gate

| Field | Value |
|-------|-------|
| gate_id | `push_gate` |
| gate_name | Push Gate |
| gate_category | `push_gate` |
| protected_action | Pushing to remote |
| risk_level | high |
| required_inputs | commit_gate_decision, pcae_push_check_result, task_contract |
| required_evidence | commit gate allowed, push check clean |
| human_review_required | yes |
| default_decision | `deny` |
| allowed_decisions | allow, deny, requires_human_review, blocked_by_lifecycle_state |
| must_never_repeat_controls | raw push, force push |
| read_only_sources | project-state, memory-snapshot |
| forbidden_side_effects | no storage (evaluation only) |
| future_implementation_phase | 87G |

### 8.12 rollback_gate

| Field | Value |
|-------|-------|
| gate_id | `rollback_gate` |
| gate_name | Rollback Gate |
| gate_category | `rollback_gate` |
| protected_action | Rolling back a previous action |
| risk_level | high |
| required_inputs | rollback_target, project_state, evidence_of_original_action |
| required_evidence | original action evidence, rollback payload |
| human_review_required | yes |
| default_decision | `deny` |
| allowed_decisions | allow, deny, requires_human_review, blocked_by_missing_artifact |
| must_never_repeat_controls | rollback of rollback |
| read_only_sources | governance-timeline, decision-log |
| forbidden_side_effects | no storage (evaluation only) |
| future_implementation_phase | 87G |

### 8.13 storage_write_gate

| Field | Value |
|-------|-------|
| gate_id | `storage_write_gate` |
| gate_name | Storage Write Gate |
| gate_category | `storage_gate` |
| protected_action | Writing to persistent storage, cache, or .pcae |
| risk_level | high |
| required_inputs | storage_target, storage_justification, task_contract |
| required_evidence | explicit storage phase approval |
| human_review_required | yes |
| default_decision | `deny` |
| allowed_decisions | allow, deny, requires_human_review |
| must_never_repeat_controls | storage without gate |
| read_only_sources | project-state |
| forbidden_side_effects | none (evaluation only) |
| future_implementation_phase | deferred |

### 8.14 permission_broker_gate

| Field | Value |
|-------|-------|
| gate_id | `permission_broker_gate` |
| gate_name | Permission Broker Gate |
| gate_category | `broker_gate` |
| protected_action | Runtime permission evaluation for proposed shell/agent actions |
| risk_level | critical |
| required_inputs | proposed_action, agent_identity, command_policy, task_contract |
| required_evidence | command policy defined, agent authorized |
| human_review_required | yes |
| default_decision | `deny` |
| allowed_decisions | allow, deny, requires_human_review, blocked_by_risk |
| must_never_repeat_controls | bypass permissions |
| read_only_sources | all six read-only commands |
| forbidden_side_effects | none (evaluation only) |
| future_implementation_phase | 87H (design), later (implementation) |

### 8.15 shell_command_gate

| Field | Value |
|-------|-------|
| gate_id | `shell_command_gate` |
| gate_name | Shell Command Gate |
| gate_category | `shell_gate` |
| protected_action | Executing a shell command |
| risk_level | critical |
| required_inputs | proposed_command, command_classification, task_contract, lifecycle_state |
| required_evidence | command classified, scope verified, lifecycle permits |
| human_review_required | yes (for mutating commands) |
| default_decision | `deny` |
| allowed_decisions | allow, deny, requires_human_review, blocked_by_scope, blocked_by_must_never_repeat_control |
| must_never_repeat_controls | raw push, force push, hook bypass |
| read_only_sources | all six read-only commands |
| forbidden_side_effects | none (evaluation only) |
| future_implementation_phase | 87I (design), later (implementation) |

---

## 9. Gate Categories

| Category | Gates | Purpose |
|----------|-------|---------|
| `planning_gate` | task_start_gate | Phase/task lifecycle |
| `scope_gate` | scope_check_gate | File/scope authorization |
| `backend_gate` | backend_invocation_gate | Agent invocation |
| `prompt_gate` | prompt_send_gate | Prompt sending |
| `capture_gate` | capture_acceptance_gate | Output capture |
| `review_gate` | intake_review_gate, adoption_approval_gate | Classification and approval |
| `mutation_gate` | source_mutation_gate | Source code changes |
| `test_gate` | test_mutation_gate | Test code changes |
| `commit_gate` | commit_gate | Git commits |
| `push_gate` | push_gate | Git pushes |
| `rollback_gate` | rollback_gate | Reversals |
| `storage_gate` | storage_write_gate | Persistent storage writes |
| `broker_gate` | permission_broker_gate | Runtime permission |
| `shell_gate` | shell_command_gate | Shell command execution |

## 10. Gate Lifecycle States

| State | Meaning |
|-------|---------|
| `not_applicable` | Gate does not apply to this action |
| `not_evaluated` | Gate has not been run |
| `evaluated` | Gate has been evaluated (transitional) |
| `allowed` | Gate produced allow decision |
| `denied` | Gate produced deny decision |
| `blocked` | Gate produced a blocked_by_* decision |
| `requires_human_review` | Awaiting human approval |
| `requires_more_evidence` | Missing evidence |
| `superseded` | Gate decision replaced by newer evaluation |
| `unknown` | Gate state could not be determined |

## 11. Gate Decision Outputs

| Decision | Meaning | Permits Action |
|----------|---------|----------------|
| `allow` | Action may proceed | yes |
| `deny` | Action is refused | no |
| `requires_human_review` | Human must approve | no (until approved) |
| `requires_more_evidence` | Evidence missing | no |
| `blocked_by_risk` | Active risk prevents action | no |
| `blocked_by_scope` | Action exceeds scope | no |
| `blocked_by_lifecycle_state` | Lifecycle state wrong | no |
| `blocked_by_missing_artifact` | Required artifact absent | no |
| `blocked_by_must_never_repeat_control` | Must-never-repeat applies | no |
| `unknown` | Cannot determine; defaults to deny | no |

Only `allow` permits action. All other decisions block.

## 12. Gate Reason Codes

| Code | Meaning |
|------|---------|
| `missing_task_contract` | No task contract found |
| `missing_artifact_evidence` | Required artifact not present |
| `scope_not_authorized` | Action outside allowed scope |
| `lifecycle_state_not_ready` | Lifecycle does not permit action |
| `risk_active` | Active risk affects action |
| `risk_accepted_not_mitigated` | Risk accepted but not resolved |
| `stale_signal_requires_review` | Stale signal relevant to action |
| `must_never_repeat_control_applies` | Must-never-repeat boundary |
| `human_approval_required` | Human sign-off needed |
| `backend_invocation_not_authorized` | No backend gate approval |
| `prompt_send_not_authorized` | No prompt gate approval |
| `source_mutation_not_authorized` | Source mutation not scoped |
| `test_mutation_not_authorized` | Test mutation not scoped |
| `commit_not_authorized` | Commit gate not passed |
| `push_not_authorized` | Push gate not passed |
| `rollback_not_authorized` | Rollback gate not passed |
| `storage_write_not_authorized` | Storage gate not passed |
| `permission_broker_not_implemented` | Broker not yet available |
| `shell_gate_not_implemented` | Shell gate not yet available |
| `unknown_state` | State could not be determined |

## 13. Gate Input Model

Future gate inputs:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `gate_id` | string | yes | Which gate to evaluate |
| `requested_action` | string | yes | What is being requested |
| `requested_actor` | string | yes | Who is requesting |
| `requested_agent` | string | no | Agent involved |
| `requested_command` | string | no | Command being run |
| `requested_files` | list[string] | no | Files to be affected |
| `requested_phase` | string | no | Phase context |
| `task_contract` | object | yes | Active task contract |
| `project_state` | object | no | From pcae project-state |
| `risk_register` | object | no | From pcae risk-register |
| `decision_log` | object | no | From pcae decision-log |
| `governance_timeline` | object | no | From pcae governance-timeline |
| `memory_snapshot` | object | no | From pcae memory-snapshot |
| `artifact_index` | object | no | From pcae artifact-index |
| `git_state` | object | no | Repository state |
| `pcae_health_state` | object | no | Health/check/doctor results |
| `human_approval` | object | no | Explicit human sign-off |

## 14. Gate Evidence Requirements

| Requirement | Rule |
|-------------|------|
| Every non-deny decision requires evidence | Evidence must be cited |
| `allow` requires explicit positive evidence | Cannot allow on absence |
| `requires_human_review` requires reason | Must explain what needs review |
| `requires_more_evidence` requires missing list | Must specify what is missing |
| `blocked_by_*` requires blocker reason | Must cite specific blocker |
| `deny` requires denial reason | Must cite reason code |
| `unknown` must not be treated as `allow` | Unknown → deny behavior |
| Accepted risk is not evidence of mitigation | accepted ≠ mitigated |
| Stale evidence is not current evidence | stale → requires_review |
| Recommendation is not evidence of permission | recommendation ≠ approval |

## 15. Gate Output Model

Future gate outputs:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `gate_id` | string | yes | Gate that was evaluated |
| `gate_name` | string | yes | Human-readable name |
| `decision` | string | yes | From decision outputs |
| `reason_codes` | list[string] | yes | From reason code taxonomy |
| `human_review_required` | boolean | yes | Whether human must approve |
| `evidence_artifacts` | list[string] | no | Artifacts consulted |
| `evidence_events` | list[string] | no | Events consulted |
| `evidence_decisions` | list[string] | no | Decisions consulted |
| `evidence_risks` | list[string] | no | Risks consulted |
| `allowed_scope` | string | for allow | What is permitted |
| `denied_scope` | string | for deny | What is refused |
| `requested_action` | string | yes | Original request |
| `requested_actor` | string | yes | Who requested |
| `requested_files` | list[string] | no | Files requested |
| `safety_notes` | string | no | Safety annotations |
| `generated_at` | string | yes | ISO 8601 timestamp |
| `schema_version` | string | yes | `"0.1"` |

## 16. Human-Review Triggers

Human review is required when:

1. Backend invocation requested
2. Prompt sending requested
3. Source mutation requested (outside explicit scope)
4. Test mutation outside current task requested
5. Adoption requested
6. Commit requested
7. Push requested
8. Rollback requested
9. Storage write requested
10. Accepted risk override requested
11. Must-never-repeat override requested
12. Permission broker activation requested
13. Shell gate activation requested
14. Missing evidence for non-read-only action
15. Stale signal affects requested action

## 17. Deny-by-Default Rules

1. Missing task contract → deny or requires_human_review
2. Missing evidence → deny or requires_more_evidence
3. Unknown lifecycle state → deny or requires_human_review
4. Active risk relevant to action → deny or requires_human_review
5. Must-never-repeat control applies → deny (unless explicit override process)
6. Write action without explicit scope → deny
7. Backend invocation without gate approval → deny
8. Commit/push without lifecycle/governance support → deny
9. Storage write without storage gate phase → deny
10. Unknown gate state → deny

## 18. Read-Only Source Integration

Future gates may read from:

- `pcae artifact-index --json`
- `pcae memory-snapshot --json`
- `pcae governance-timeline --json`
- `pcae decision-log --json`
- `pcae risk-register --json`
- `pcae project-state --json`

These commands remain read-only. Gates consume their output but must not modify
their behavior or make them authorizing.

## 19. Risk-Aware Decision Rules

| Risk State | Gate Behavior |
|------------|---------------|
| `active` | Block or require human review if relevant |
| `accepted` | Does not permit action (accepted ≠ mitigated) |
| `mitigated` | May permit if mitigation evidence is present |
| `deferred` | Does not permit if relevant to requested action |
| `stale_signal` | Require review if relevant |
| `must_never_repeat` | Block unless superseded by explicit human decision |

## 20. Must-Never-Repeat Controls

Gates must check these before allowing:

| Control | Gate Affected |
|---------|---------------|
| Bypass permissions | permission_broker_gate, shell_command_gate |
| Raw git push | push_gate |
| Force push | push_gate |
| Adoption without approval | adoption_approval_gate |
| Invocation without guard | backend_invocation_gate |
| Mutation outside scope | source_mutation_gate, test_mutation_gate |
| Boundary collapse | all gates |
| Rejected item reintroduced | adoption_approval_gate |

## 21. Accepted-Risk Handling

- Accepted risk has `acceptance_rationale` but no `mitigation`.
- A gate must not treat accepted risk as evidence of resolution.
- If accepted risk is relevant to the requested action, the gate should
  `requires_human_review` rather than `allow`.

## 22. Storage/Cache Policy

- 87B creates no storage, cache, or `.pcae` persistent state.
- Future gate evaluation should start as read-only dry-run (87C) before storage.
- Storage write gates require a later explicit phase.
- Generated cache must never become authoritative.

## 23. Permission Broker Relationship

- Not implemented in 87B.
- Depends on this taxonomy and decision model.
- Must consume explicit gate decisions, not raw project-state output.
- Requires separate design phase (87H) before implementation.

## 24. Shell Gate Relationship

- Not implemented in 87B.
- Depends on command/action taxonomy.
- Must distinguish read-only from mutating commands.
- Requires separate design phase (87I) before implementation.

## 25. Future JSON Schema Sketch

Illustrative only. Not machine-readable schema files.

### GateInput (sketch)

```json
{
  "gate_id": "scope_check_gate",
  "requested_action": "modify_source",
  "requested_actor": "claude-local",
  "requested_files": ["src/pcae/core/example.py"],
  "task_contract": {"allowed_files": ["src/pcae/core/example.py"]},
  "project_state": {"execution_authorized": false}
}
```

### GateDecision (sketch)

```json
{
  "gate_id": "scope_check_gate",
  "gate_name": "Scope Check Gate",
  "decision": "allow",
  "reason_codes": [],
  "human_review_required": false,
  "evidence_artifacts": ["tasks/active/example-task.md"],
  "allowed_scope": "src/pcae/core/example.py",
  "requested_action": "modify_source",
  "requested_actor": "claude-local",
  "safety_notes": "scope_verified_against_task_contract",
  "generated_at": "2026-06-24T12:00:00+00:00",
  "schema_version": "0.1"
}
```

### GateReason (sketch)

```json
{
  "code": "must_never_repeat_control_applies",
  "description": "Raw git push is a must-never-repeat control",
  "gate_id": "push_gate",
  "control_id": "raw_push_exception_risk"
}
```

---

## 26. Validation Rules

1. Every gate must have a stable `gate_id`.
2. Every gate must have a `gate_category`.
3. Every gate must have a `protected_action`.
4. Every gate must have a `default_decision`.
5. Default decision must not be `allow` for high-risk gates (critical/high).
6. Default decision must not be `allow` for medium-risk gates without evidence.
7. `allow` requires explicit positive evidence.
8. Missing evidence cannot produce `allow`.
9. `unknown` cannot produce `allow`.
10. Accepted risk cannot produce `allow` by itself.
11. Project-state recommendation cannot produce `allow` by itself.
12. Read-only command output cannot authorize by itself.
13. Human review required for `backend_invocation_gate`.
14. Human review required for `prompt_send_gate`.
15. Human review required for `adoption_approval_gate`.
16. Human review required for `source_mutation_gate` outside explicit scope.
17. Human review required for `commit_gate`.
18. Human review required for `push_gate`.
19. Human review required for `rollback_gate`.
20. Human review required for `storage_write_gate`.
21. Human review required for `permission_broker_gate`.
22. Human review required for `shell_command_gate` for mutating commands.
23. `storage_write_gate` requires explicit storage phase approval.
24. `permission_broker_gate` requires 87H architecture design.
25. `shell_command_gate` requires 87I architecture design.
26. Gate decisions must be from the defined decision output set.
27. Gate reason codes must be from the defined reason code taxonomy.
28. Gate output must include `gate_id`, `decision`, `reason_codes`.
29. Gate output must include `human_review_required` boolean.
30. Gate output must include `generated_at` timestamp.
31. Gate output must include `schema_version`.
32. Must-never-repeat controls must be checked before `allow`.
33. Risk register must be consulted for risk-relevant gates.
34. Stale signals must trigger review, not be silently ignored.
35. Scope check must compare against task contract allowed/forbidden files.
36. Lifecycle state must be compatible with requested action.
37. Gate evaluation must not modify read-only command behavior.
38. Gate evaluation must not create storage or cache.
39. Gate evaluation must not invoke backends.
40. Gate evaluation must not send prompts.
41. No source/test changes in 87B.
42. No storage/cache/.pcae creation in 87B.
43. No phase beyond 87B started from this artifact.
44. Gate taxonomy version must be tracked.

## 27. Failure Cases

| # | Failure | Impact |
|---|---------|--------|
| FC-1 | Gate without stable ID | Cannot track or reference gate |
| FC-2 | Gate without default deny/review posture | Unsafe default behavior |
| FC-3 | Allow decision without evidence | Unauthorized action proceeds |
| FC-4 | Unknown treated as allow | Missing state causes action |
| FC-5 | Project-state recommendation treated as permission | Observation becomes authorization |
| FC-6 | Accepted risk treated as mitigation | Risk assumed resolved |
| FC-7 | Must-never-repeat control ignored | Forbidden pattern repeats |
| FC-8 | Human review skipped for high-risk action | Safety boundary bypassed |
| FC-9 | Storage created in taxonomy phase | Scope creep |
| FC-10 | Permission broker implemented in taxonomy phase | Premature implementation |
| FC-11 | Shell gate implemented in taxonomy phase | Premature implementation |
| FC-12 | Read-only command modified to authorize | Boundary collapse |
| FC-13 | Gate output missing decision field | Ambiguous result |
| FC-14 | Gate output missing reason codes | Unauditable decision |
| FC-15 | Scope check ignores task contract | Unauthorized file mutation |

## 28. Future Rollout Phases

| Phase | Deliverable | Type |
|-------|-------------|------|
| **87C** | Read-Only Gate Evaluation Dry-Run | implementation (read-only) |
| **87D** | Scope Gate Prototype | implementation (read-only) |
| **87E** | Backend Invocation Gate Dry-Run | implementation (read-only) |
| **87F** | Adoption/Mutation Gate Dry-Run | implementation (read-only) |
| **87G** | Commit/Push Gate Dry-Run | implementation (read-only) |
| **87H** | Permission Broker Architecture Design | design |
| **87I** | Shell Gate Architecture Design | design |
| **87J** | Phase 87 Integration Tests | testing |

## 29. Recommended Next Phase

**87C — Read-Only Gate Evaluation Dry-Run.**

87C should implement a read-only gate evaluator that consumes project-state and task
contract inputs, evaluates one or more gates from this taxonomy, and reports decisions
as JSON to stdout — without enforcing, writing, or storing anything.

---

action_gate_taxonomy_name=phase_87_action_gate_taxonomy_decision_model
action_gate_taxonomy_version=0.1
action_gate_taxonomy_status=draft_documented
implementation_status=not_started
gates_defined=15
gate_categories=14
gate_lifecycle_states=10
gate_decision_outputs=10
gate_reason_codes=20
human_review_triggers=15
deny_by_default_rules=10
validation_rules=44
failure_cases=15
recommended_next=87C
backend_invocation_performed=false
