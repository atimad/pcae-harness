# Phase 88D Backend Invocation Preflight Design

## 1. Purpose

Define the backend invocation preflight boundary for PCAE: how PCAE should
evaluate proposed backend invocations before any agent or backend is called.
This covers backend identity, requested action, prompt presence, task contract
evidence, scope relationship, human review requirements, denial/review/
more-evidence decisions, audit requirements, and safety invariants.

88D defines the backend invocation preflight boundary but does not implement
backend invocation preflight. No backend is invoked, no prompt is sent, no
output is captured, and no backend permission is granted in this phase.

## 2. Scope

Design and planning only. This artifact defines the backend invocation
preflight boundary, models, decision values, deny-by-default rules, and
safety invariants. It does not implement any preflight evaluator, CLI command,
or enforcement logic.

## 3. Non-Goals

- Implementing backend invocation preflight.
- Invoking any backend (Claude, Claude DeepSeek, Claude Kimi, Codex, subagents).
- Sending prompts.
- Capturing backend output.
- Implementing permission broker or shell gate.
- Creating storage, cache, or `.pcae` persistent state.
- Modifying source code, tests, or existing artifacts.
- Expanding scope preflight.

## 4. Starting Point from 88A–88C

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 88A | First Narrow Enforced Gate Boundary | Design complete |
| 88B | Scope Gate Preflight Prototype | Implemented, 66 tests |
| 88C | Scope Gate Preflight Tests and False-Positive Review | 63 edge-case tests, readiness=ready_for_backend_invocation_preflight_design |

The scope gate preflight (`pcae preflight scope`) is the first working
preflight command. It evaluates requested action/file scope against the active
task contract. It returns `allow_preflight` only when all requested files match
allowed patterns and the action is scope-decidable. It never sets
`authorization_granted=true` or `execution_authorized=true`.

Backend invocation preflight extends this foundation by evaluating whether a
proposed backend invocation may proceed — a higher-risk gate than scope alone.

## 5. Relationship to Phase 87 Backend Gate Dry-Run

Phase 87E added `backend_evaluation` to `pcae gate-dry-run --json`. The dry-run
evaluator accepts `--requested-backend` and `--prompt-present` flags and
produces `backend_status`, `requested_backend`, `prompt_present`,
`backend_allowed_by_scope`, `backend_approval_detected`, and
`human_approval_detected` fields.

Key differences between 87E dry-run and future 88E preflight:

| Aspect | 87E Dry-Run | Future 88E Preflight |
|--------|-------------|---------------------|
| Purpose | Observation/recommendation | Explicit preflight decision |
| Output | Part of 15-gate evaluation | Standalone JSON envelope |
| Decision | No allow, always dry-run | allow_preflight possible (still non-authorizing) |
| Scope integration | None | Requires scope preflight evidence |
| Prompt validation | prompt_present flag only | Prompt source, hash, scope reference |
| Human review | Not enforced | Required for every backend invocation |

The future backend invocation preflight builds on 87E's evaluation model but
produces an explicit, standalone preflight decision with stricter evidence
requirements.

## 6. Why Backend Invocation Is High Risk

Backend invocation is the highest-risk action in PCAE because:

1. **Irreversible side effects.** A backend call sends a prompt to an external
   system. Once sent, the prompt cannot be unsent.
2. **Output adoption risk.** Backend output may be adopted into the repository,
   creating mutations that are difficult to trace without structured capture.
3. **Scope escalation.** A backend may produce output that modifies files
   outside the task contract scope.
4. **Credential exposure.** Backend invocation may expose API keys, tokens, or
   repository contents to external systems.
5. **Autonomy creep.** Allowing backend invocation without explicit preflight
   creates a path toward uncontrolled agent execution.
6. **Chain effects.** Backend invocation may trigger prompt send → capture →
   intake → adoption → commit → push — a full mutation chain.

## 7. Backend Identity Model

| Backend | Identity | Risk Level | Notes |
|---------|----------|------------|-------|
| `claude` | Primary AI agent | Critical | Most capable, broadest mutation potential |
| `claude-deepseek` | Secondary AI agent | Critical | Alternative reasoning model |
| `claude-kimi` | Secondary AI agent | Critical | Alternative reasoning model |
| `codex` | Code generation agent | Critical | Direct code generation |
| `subagent` | Delegated agent | Critical | May invoke further backends |
| `unknown_backend` | Unrecognized | Critical | Must never be treated as allow |

All backends are critical risk. No backend invocation should proceed without
explicit human review and evidence.

## 8. Backend Invocation Request Model

Future inputs for backend invocation preflight:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `requested_backend` | string | yes | Backend identity |
| `requested_action` | string | yes | Action type (e.g., backend_invocation) |
| `requested_phase` | string | no | Phase context for the invocation |
| `requested_files` | list[string] | no | Files the backend may affect |
| `prompt_present` | boolean | yes | Whether a prompt exists |
| `prompt_source` | string | no | Where the prompt originated |
| `prompt_hash` | string | no | Hash of prompt content |
| `task_contract_detected` | boolean | yes | Whether active task contract exists |
| `task_contract_path` | string | no | Path to active task contract |
| `scope_preflight_decision` | string | no | Result of scope preflight for affected files |
| `project_state` | object | no | Current project state snapshot |
| `risk_register` | object | no | Current risk register |
| `decision_log` | object | no | Current decision log |
| `human_approval` | object | no | Human approval evidence |
| `backend_policy` | object | no | Backend-specific policy constraints |
| `lifecycle_state` | string | yes | Current lifecycle state |

## 9. Backend Invocation Preflight Decision Model

Future outputs for backend invocation preflight:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `preflight_type` | string | yes | Always "backend_invocation_preflight" |
| `requested_backend` | string | yes | Backend requested |
| `requested_action` | string | yes | Action type |
| `decision` | string | yes | Preflight decision |
| `reason_codes` | list[string] | yes | Reason codes for decision |
| `backend_known` | boolean | yes | Whether backend is recognized |
| `backend_allowed_by_policy` | boolean | yes | Whether policy permits this backend |
| `prompt_present` | boolean | yes | Whether prompt evidence exists |
| `prompt_required` | boolean | yes | Whether prompt is required |
| `prompt_hash_required` | boolean | yes | Whether prompt hash is required |
| `scope_preflight_required` | boolean | yes | Whether scope preflight is required |
| `scope_preflight_decision` | string | no | Scope preflight result if available |
| `human_review_required` | boolean | yes | Whether human review is needed |
| `more_evidence_required` | boolean | yes | Whether more evidence is needed |
| `task_contract_detected` | boolean | yes | Whether task contract exists |
| `task_contract_path` | string | no | Task contract path |
| `evidence_sources` | list[string] | yes | Evidence consulted |
| `safety_notes` | string | no | Safety context |
| `authorization_granted` | boolean | yes | Always false |
| `execution_authorized` | boolean | yes | Always false |
| `backend_invocation_performed` | boolean | yes | Always false |
| `prompt_sent` | boolean | yes | Always false |
| `capture_performed` | boolean | yes | Always false |
| `repo_mutation_performed` | boolean | yes | Always false |
| `storage_written` | boolean | yes | Always false |

## 10. Decision Values

| Decision | Meaning | Permits Invocation |
|----------|---------|-------------------|
| `allow_preflight` | Preflight check passed (future only) | no (preflight only) |
| `deny_preflight` | Preflight check failed | no |
| `requires_human_review` | Human must review before proceeding | no |
| `requires_more_evidence` | Evidence missing | no |
| `blocked_by_backend_policy` | Backend not permitted by policy | no |
| `blocked_by_missing_task_contract` | No active task contract | no |
| `blocked_by_missing_prompt` | Prompt required but missing | no |
| `blocked_by_scope` | Scope preflight denied | no |
| `blocked_by_lifecycle_state` | Lifecycle state not ready | no |
| `blocked_by_risk` | Active risk blocks invocation | no |
| `unknown` | Cannot determine; deny | no |

`allow_preflight` is future-only and must not be implemented in 88D.
`allow_preflight` would only mean the backend invocation preflight check
passed. It would not send a prompt, invoke a backend, or authorize mutation.
`unknown` must never be treated as allow.

## 11. Deny-by-Default Rules

1. Unknown backend → deny or requires_human_review
2. Missing task contract → deny or requires_more_evidence
3. Missing prompt when prompt is required → requires_more_evidence
4. Prompt present but not captured/hashed → requires_more_evidence
5. Backend not listed in policy → deny
6. Backend invocation outside active phase → deny or requires_human_review
7. Scope preflight missing for file-related backend action → requires_more_evidence
8. Scope preflight denied → deny
9. Active risk → blocked_by_risk or requires_human_review
10. Accepted risk → not mitigation
11. Must-never-repeat control applies → deny
12. Human approval without evidence → not enough

## 12. Human Review Model

Human review is required for:

- Any backend invocation request
- Unknown backend
- Backend change from expected backend
- claude-deepseek invocation
- claude-kimi invocation
- codex invocation
- subagent invocation
- Prompt-send request
- File-related backend work
- Adoption-related backend work
- Commit/push-related backend work
- Accepted-risk override
- Must-never-repeat override
- Missing or stale task contract

Human review alone does not authorize backend invocation. Evidence from scope
preflight, task contract, and prompt capture is also required.

## 13. Prompt Handling Model

- Prompt must be explicit — no implicit or auto-generated prompts.
- Prompt source must be recorded (human-authored, template-rendered, etc.).
- Prompt hash should be computed before send for audit traceability.
- Prompt sending is separate from preflight — preflight does not send prompts.
- Preflight does not create prompt files unless a future prompt-capture phase
  authorizes it.
- Prompt must reference task scope and forbidden actions.
- Prompt must not request out-of-scope mutation.

## 14. Capture/Output Handling Model

- Backend output capture is separate from backend invocation preflight.
- Preflight does not capture output.
- Future backend invocation must capture stdout/stderr/return code/duration/hash
  where applicable.
- Captured output must not be adopted automatically.
- Adoption remains separate and gated (review → approval → execution).

## 15. Scope Preflight Relationship

- Scope preflight evaluates requested action/file scope.
- Backend invocation preflight evaluates whether a backend may be called.
- Scope preflight `allow_preflight` is necessary for file-related backend work
  but not sufficient — backend preflight adds backend-specific checks.
- Backend preflight must not bypass scope preflight.
- Backend preflight must preserve scope decision evidence in its output.

## 16. Permission Broker Relationship

- Backend preflight is a lower-level gate that evaluates one dimension
  (backend invocation readiness).
- A future permission broker may combine backend preflight, scope preflight,
  risk register, lifecycle state, and human review into a unified broker
  decision.
- Backend preflight must not claim to be broker approval.
- Backend preflight `allow_preflight` would mean "backend invocation is
  permitted in principle" — not "the broker has approved execution."

## 17. Shell Gate Relationship

- Backend CLI invocation (e.g., `claude --prompt ...`) is ultimately a shell
  command.
- A future shell gate must mediate concrete command execution.
- Backend preflight can decide whether invocation is permitted in principle.
- Backend preflight without shell gate cannot guarantee shell enforcement.
- Backend preflight + shell gate together would provide defense-in-depth:
  preflight checks policy; shell gate controls execution.

## 18. Audit Requirements

Future audit events:

| Event | Trigger |
|-------|---------|
| `backend_preflight_request_received` | Backend preflight evaluation requested |
| `backend_preflight_decision_recorded` | Decision produced |
| `backend_preflight_denied` | Backend invocation denied |
| `backend_preflight_human_review_required` | Routed to human review |
| `backend_preflight_more_evidence_required` | More evidence needed |
| `backend_preflight_error` | Evaluation failure |

## 19. Storage/Cache Policy

- 88D creates no storage, cache, or `.pcae` persistent state.
- Future backend preflight logging/storage requires a separate explicit phase.
- Backend preflight decisions should be reported in command output (stdout/
  stderr), not persisted to files, until a storage gate phase approves
  persistence.

## 20. Failure Handling

| Condition | Preflight Behavior |
|-----------|---------------------|
| Missing task contract | requires_more_evidence or deny |
| Unknown backend | requires_human_review or deny |
| Missing prompt evidence | requires_more_evidence |
| Stale project state | requires_human_review |
| Scope preflight missing | requires_more_evidence |
| Scope preflight denied | deny |
| Risk active | blocked_by_risk or requires_human_review |
| Must-never-repeat control applies | deny |
| Unknown state | unknown (never allow) |

## 21. Safety Invariants

1. 88D does not implement backend preflight.
2. 88D does not invoke backends.
3. 88D does not send prompts.
4. 88D does not capture outputs.
5. 88D does not perform intake.
6. 88D does not perform adoption.
7. 88D does not mutate repo beyond docs/status/task files.
8. 88D does not write storage.
9. Future backend preflight must deny by default.
10. Future backend preflight must require human review for backend invocation.
11. Future backend preflight must not bypass scope preflight.
12. Future backend preflight must not imply prompt send authorization.
13. Future backend preflight must not imply output adoption authorization.
14. Future backend preflight must preserve evidence and reason codes.
15. Future backend preflight must not imply full autonomy.

## 22. Future Test Strategy

Tests for future 88E (not implemented in 88D):

- Known backend request (claude) → requires_human_review
- Unknown backend request → deny or requires_human_review
- Missing task contract → blocked_by_missing_task_contract
- Missing prompt → blocked_by_missing_prompt or requires_more_evidence
- Prompt present but no hash → requires_more_evidence
- Scope preflight missing → requires_more_evidence
- Scope preflight denied → deny or blocked_by_scope
- Scope preflight allow but backend still requires review
- Human approval does not bypass backend policy
- backend_invocation_performed remains false
- prompt_sent remains false
- capture_performed remains false
- repo_mutation_performed remains false
- storage_written remains false
- No cache/state/.pcae files created
- Existing scope preflight still works
- Existing gate-dry-run still works
- Existing read-only intelligence commands still work

## 23. Future Implementation Roadmap

| Phase | Deliverable |
|-------|-------------|
| **88E** | Backend Invocation Preflight Prototype |
| **88F** | Backend Invocation Preflight Tests and False-Positive Review |
| **88G** | Mutation/Adoption Preflight Design |
| **88H** | Commit/Push Preflight Design |
| **88I** | Scope + Backend Preflight Integration Verification |

## 24. Recommended Next Phase

**88E — Backend Invocation Preflight Prototype.**

88E should implement the backend invocation preflight evaluator as an explicit
command (`pcae preflight backend`) that evaluates proposed backend invocations
against task contract, scope preflight evidence, prompt presence, and backend
policy. It must deny by default, require human review for every backend
invocation, and never send a prompt or invoke a backend.

---

backend_preflight_design_name=phase_88_backend_invocation_preflight_design
backend_preflight_design_version=0.1
backend_preflight_design_status=draft_documented
implementation_status=not_started
backend_identities=6
request_model_fields=16
output_model_fields=25
decision_values=11
deny_by_default_rules=12
human_review_triggers=14
audit_event_types=6
failure_conditions=9
safety_invariants=15
future_test_areas=18
recommended_next=88E
backend_invocation_performed=false
