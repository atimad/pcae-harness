# Phase 87 Shell Gate Architecture

## 1. Purpose

Define the architecture for a future PCAE shell gate: a command mediation layer that
controls shell command execution based on broker/gate decisions, task scope, lifecycle
state, command class, and human approval.

## 2. Scope

Architecture design only. This artifact defines the shell gate's role, command taxonomy,
inputs, outputs, decision model, relationships, and safety invariants. It does not
implement shell interception, command mediation, or any code.

## 3. Non-Goals

- Implementing the shell gate, command wrapper, or shell interception.
- Modifying shell config, PATH, aliases, or hook files.
- Creating CLI commands, source code, or tests.
- Implementing permission broker, storage, or enforcement.
- Backend invocation, prompt sending, capture, intake, or adoption.

## 4. Starting Point from 87C–87H

| Phase | Deliverable |
|-------|-------------|
| 87C | Dry-run gate evaluator (15 gates) |
| 87D | Scope gate with task contract evaluation |
| 87E | Backend invocation gate with backend evaluation |
| 87F | Adoption/mutation gate evaluation |
| 87G | Commit/push gate evaluation |
| 87H | Permission broker architecture |

All gate evaluators are dry-run only. No gate enforces. No gate authorizes. The
permission broker architecture defines a future mediation layer between intent and
execution. The shell gate completes the architecture by defining how commands are
actually controlled at the shell level.

## 5. Shell Gate Architecture Role

The shell gate is:

- A future **mediation layer** between approved intent and shell execution.
- A **command classifier** that categorizes commands by risk before execution.
- A **deny-by-default enforcement point** for unsafe command classes.
- A future **blocker** for raw git push, force push, hook bypass, out-of-scope writes,
  unauthorized backend invocation, and unauthorized storage writes.
- A **recorder** of command decision evidence.
- A **separate layer** from the permission broker.

The shell gate is NOT:

- The permission broker (broker decides policy; gate controls execution).
- A replacement for human approval.
- A replacement for PCAE health/check/doctor.
- An automatic command executor.

## 6. Observation Versus Authorization Boundary

The shell gate is a future command mediation layer. It may consume permission broker
decisions, gate dry-run evidence, project intelligence, and task scope, but it must
not execute, block, wrap, or intercept commands until a future implementation phase
explicitly authorizes that behavior.

## 7. Shell Gate Design Principles

1. Deny by default — unknown commands are blocked or require review.
2. Do not execute without explicit decision.
3. Broker decision required for high-risk commands.
4. Unknown command class requires human review.
5. Read-only commands can be lower risk but still audited.
6. Mutating commands require task scope and broker approval.
7. Backend commands require backend invocation gate evidence and human review.
8. Commit and push commands require lifecycle evidence.
9. Raw git push is forbidden (must-never-repeat).
10. Force push is forbidden (must-never-repeat).
11. Hook bypass normalization is forbidden (must-never-repeat).
12. Out-of-scope file writes are forbidden.
13. Must-never-repeat controls are hard constraints.
14. Shell gate decisions must be auditable.
15. Shell gate must not silently mutate repo state.

## 8. Threat Model

| # | Threat | Impact | Mitigation |
|---|--------|--------|------------|
| SG-1 | Raw git push bypasses pcae push | Ungovemed repo mutation | Block `git push` without gate evidence |
| SG-2 | Force push damages remote history | History loss | Hard block on `--force` |
| SG-3 | Git commit bypasses commit gate | Ungoverned commit | Require commit gate evidence |
| SG-4 | Hook bypass disables governance | Safety checks skipped | Block `--no-verify` |
| SG-5 | Out-of-scope file write | Task boundary violation | Scope check before mutation |
| SG-6 | Backend CLI invoked without gate | Unauthorized invocation | Require backend gate evidence |
| SG-7 | Prompt sent outside prompt gate | Unauthorized prompt | Require prompt gate evidence |
| SG-8 | Capture written outside gate | Unauthorized capture | Require capture gate evidence |
| SG-9 | Adoption applied outside gate | Unauthorized adoption | Require adoption gate evidence |
| SG-10 | Storage written before gate | Unauthorized storage | Require storage gate evidence |
| SG-11 | Unknown command treated as safe | Unsafe action proceeds | Unknown → requires_human_review |
| SG-12 | Read-only command mutates repo | Unexpected side effect | Classify carefully; monitor |
| SG-13 | Shell alias bypasses wrapper | Gate circumvented | Future wrapper must intercept |
| SG-14 | PATH order bypasses gate | Gate circumvented | Future wrapper must be authoritative |
| SG-15 | Human approves what PCAE would block | Override risk | Record override with evidence |

## 9. Command Taxonomy

| Command Class | Examples | Risk |
|---------------|----------|------|
| `read_only_project_intelligence` | pcae artifact-index, project-state | low |
| `read_only_git_inspection` | git status, git log, git diff | low |
| `read_only_filesystem_inspection` | ls, cat, find, grep | low |
| `test_execution` | python -m pytest | medium |
| `health_check` | pcae health, pcae check, pcae doctor | medium |
| `task_lifecycle_command` | pcae task, pcae session | medium |
| `backend_invocation_command` | claude, claude-deepseek, codex | critical |
| `prompt_send_command` | prompt piped to backend | critical |
| `capture_command` | capture-related commands | high |
| `intake_command` | intake-related commands | high |
| `adoption_command` | adoption-related commands | critical |
| `source_mutation_command` | edit src/**, write src/** | high |
| `test_mutation_command` | edit tests/**, write tests/** | high |
| `docs_mutation_command` | edit docs/**, write docs/** | high |
| `commit_command` | git commit, pcae commit | high |
| `push_command` | pcae push, git push | high |
| `rollback_command` | pcae rollback, git reset | high |
| `storage_write_command` | write to .pcae/**, cache | high |
| `hook_bypass_command` | git commit --no-verify | critical |
| `unknown_command` | unclassified command | unknown |

## 10. Command Risk Classes

| Risk Class | Behavior |
|------------|----------|
| `low_read_only` | May be allowed with minimal evidence |
| `medium_validation` | Allowed within task scope |
| `high_mutation` | Requires scope + broker + human review |
| `high_backend` | Requires backend gate + broker + human review |
| `high_commit` | Requires commit gate + lifecycle + human review |
| `high_push` | Requires push gate + lifecycle + human review |
| `high_rollback` | Requires rollback gate + human review |
| `high_storage` | Requires storage gate + human review |
| `critical_bypass` | Hard deny (must-never-repeat) |
| `unknown` | Requires human review |

## 11. Shell Gate Input Model

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `shell_gate_request_id` | string | yes | Unique request ID |
| `requested_command` | string | yes | Full command string |
| `requested_command_args` | list[string] | no | Parsed arguments |
| `requested_working_directory` | string | no | CWD |
| `requested_actor` | string | yes | Who is requesting |
| `requested_agent` | string | no | Agent involved |
| `requested_phase` | string | no | Phase context |
| `requested_files` | list[string] | no | Files affected |
| `command_class` | string | yes | From taxonomy |
| `risk_class` | string | yes | From risk classes |
| `broker_decision` | object | no | Permission broker output |
| `gate_dry_run` | object | no | Gate dry-run output |
| `task_contract` | object | yes | Active task contract |
| `project_state` | object | no | From project-state |
| `risk_register` | object | no | From risk-register |
| `decision_log` | object | no | From decision-log |
| `git_state` | object | no | Repository state |
| `health_check_state` | object | no | Health/check results |
| `human_approval` | object | no | Explicit human sign-off |

## 12. Shell Gate Output Model

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `shell_gate_decision_id` | string | yes | Unique decision ID |
| `decision` | string | yes | From decision values |
| `reason_codes` | list[string] | yes | Reason codes |
| `command_class` | string | yes | Classified command |
| `risk_class` | string | yes | Classified risk |
| `human_review_required` | boolean | yes | Human must approve |
| `execution_allowed` | boolean | yes | May execute (future) |
| `execution_blocked` | boolean | yes | Execution blocked |
| `evidence_artifacts` | list[string] | no | Evidence consulted |
| `evidence_events` | list[string] | no | Events consulted |
| `evidence_decisions` | list[string] | no | Decisions consulted |
| `evidence_risks` | list[string] | no | Risks consulted |
| `safety_notes` | string | no | Safety annotations |
| `audit_event_required` | boolean | yes | Audit event needed |
| `generated_at` | string | yes | ISO 8601 timestamp |
| `schema_version` | string | yes | `"0.1"` |

## 13. Shell Gate Decision Model

| Decision | Meaning | Permits Execution |
|----------|---------|-------------------|
| `allow_execution` | Command may execute (future) | yes |
| `deny_execution` | Command is refused | no |
| `requires_human_review` | Human must approve | no (until approved) |
| `requires_more_evidence` | Evidence missing | no |
| `blocked_by_broker` | Broker denied | no |
| `blocked_by_scope` | Out of scope | no |
| `blocked_by_lifecycle_state` | Wrong lifecycle | no |
| `blocked_by_command_policy` | Command class blocked | no |
| `blocked_by_must_never_repeat_control` | Hard constraint | no |
| `unknown` | Cannot determine; deny | no |

`allow_execution` requires explicit broker decision plus command-policy evidence.
`unknown` must never be treated as `allow_execution`.

## 14. Human Review Model

Human review is required for:

- Backend invocation commands
- Prompt-send commands
- Source mutation commands
- Test mutation commands outside explicit scope
- Adoption commands
- Commit commands
- Push commands
- Rollback commands
- Storage-write commands
- Hook-bypass commands (hard deny, but if override needed, human required)
- Unknown command classes
- Must-never-repeat override

## 15. Permission Broker Relationship

- The broker decides whether an action is allowed in principle.
- The shell gate decides whether a concrete shell command may execute.
- Broker without shell gate cannot guarantee shell enforcement.
- Shell gate without broker lacks full governance context.
- The shell gate must not treat broker absence as allow.
- The shell gate must not treat gate dry-run output as broker approval.
- Both layers are needed for complete mediated execution.

## 16. Gate Dry-Run Relationship

- Gate dry-run output informs the shell gate.
- Gate dry-run output is not enforcement.
- Gate dry-run output is not shell execution permission.
- A future shell gate must distinguish dry-run evidence from explicit broker approval.

## 17. Read-Only Project Intelligence Relationship

artifact-index, memory-snapshot, governance-timeline, decision-log, risk-register,
and project-state are evidence sources. They remain read-only and non-authorizing.
The shell gate may use them to classify risk or require review. They do not authorize
command execution by themselves.

## 18. Backend Invocation Relationship

Backend CLI commands (claude, claude-deepseek, claude-kimi, codex, subagent) are
critical-risk command classes. They require explicit future broker approval and human
review. 87I does not invoke or probe any backend.

## 19. Mutation/Adoption Relationship

Mutation/adoption commands require scope evidence, adoption/mutation gate evidence,
broker approval, and human review. Scope match alone is not shell execution approval.
Human approval flag alone is not execution. Accepted risk is not mitigation.

## 20. Commit/Push Relationship

- git commit and pcae commit require commit gate evidence and broker approval.
- pcae push requires push gate evidence and broker approval.
- Raw git push (`git push`) is forbidden (must-never-repeat).
- Force push (`--force`) is forbidden (must-never-repeat).
- origin/main divergence must be understood before push.

## 21. Rollback Relationship

Rollback commands are high-risk and require future rollback gate evidence. 87I does
not implement rollback gate behavior.

## 22. Storage/Cache Policy

- 87I creates no storage, cache, or `.pcae` persistent state.
- Future shell gate audit storage requires a separate explicit storage phase.
- Shell gate design supports auditability but does not implement persistence.

## 23. Audit/Event Model

Future audit events:

| Event | Trigger |
|-------|---------|
| `shell_gate_request_received` | Command evaluation requested |
| `shell_gate_command_classified` | Command classified by risk |
| `shell_gate_decision_recorded` | Decision produced |
| `shell_gate_execution_denied` | Command denied |
| `shell_gate_human_review_required` | Routed to human review |
| `shell_gate_more_evidence_required` | More evidence needed |
| `shell_gate_allowed_future` | Command allowed (future) |
| `shell_gate_error` | Evaluation failure |

## 24. Failure Handling

| Condition | Shell Gate Behavior |
|-----------|---------------------|
| Missing broker decision | requires_more_evidence or blocked_by_broker |
| Unknown command class | requires_human_review or unknown |
| Unsafe command class | deny_execution |
| Active risk relevant | blocked_by_risk or requires_human_review |
| Must-never-repeat control | blocked_by_must_never_repeat_control |
| Inconsistent evidence | requires_human_review |
| Storage unavailable | Do not write; report limitation |

## 25. Safety Invariants

1. Shell gate is not implemented in 87I.
2. Shell gate does not execute commands in 87I.
3. Shell gate does not intercept commands in 87I.
4. Shell gate does not authorize in 87I.
5. Shell gate does not enforce in 87I.
6. Shell gate does not invoke backends in 87I.
7. Shell gate does not mutate repo in 87I.
8. Shell gate does not commit or push in 87I.
9. Shell gate does not write storage in 87I.
10. Future shell gate must deny by default.
11. Future shell gate must preserve evidence and reason codes.
12. Future shell gate must require broker approval for high-risk commands.
13. Future shell gate must not override must-never-repeat controls silently.

## 26. Future CLI/Wrapper Sketch

Illustrative only. Not implementation.

```
pcae shell-gate evaluate --json --command "git status --short"
pcae shell-gate evaluate --json --command "git push origin main"
pcae shell-gate evaluate --json --command "claude"
pcae shell-gate evaluate --json --command "python -m pytest -n auto"
```

## 27. Future Rollout Roadmap

| Phase | Deliverable |
|-------|-------------|
| **87J** | Phase 87 Gate/Broker/Shell Architecture Integration Tests |
| **87K** | Architecture Overview Refresh |
| **87L** | Installation / Usage Update |
| **87M** | Demo Script |
| **87N** | Governance Lifecycle Diagram |
| **87O** | README Reframe |
| **87P** | LinkedIn Article Draft |
| **88A** | First Narrow Enforced Gate Boundary |
| **88B** | Real Scope Gate Preflight Enforcement |
| **88C** | Backend Invocation Preflight Enforcement |
| **88D** | Mutation/Adoption Preflight Enforcement |
| **88E** | Commit/Push Preflight Enforcement |

## 28. Recommended Next Phase

**87J — Phase 87 Gate/Broker/Shell Architecture Integration Tests.**

After broker and shell gate architecture are documented, Phase 87 should finish
with integration tests/verification across the dry-run gate layer and architecture
documents before public-facing docs or Phase 88 enforcement.

---

shell_gate_architecture_name=phase_87_shell_gate_architecture
shell_gate_architecture_version=0.1
shell_gate_architecture_status=draft_documented
implementation_status=not_started
command_classes=20
risk_classes=10
shell_gate_input_fields=19
shell_gate_output_fields=16
shell_gate_decision_values=10
threat_model_entries=15
safety_invariants=13
audit_event_types=8
recommended_next=87J
backend_invocation_performed=false
