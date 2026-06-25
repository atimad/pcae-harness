# Phase 88N Permission Broker Design Reconciliation

## 1. Purpose

Reconcile the Phase 87 permission broker architecture with the concrete Phase 88
explicit preflight layer. The Phase 87 architecture (87H) was designed before the
five explicit preflight commands existed. Now that scope, backend, mutation/adoption,
commit, and push preflights are implemented, tested, and integration-verified (88B–88M),
this document redefines the broker's role in terms of concrete preflight outputs rather
than the abstract gate dry-run layer alone.

This phase is design reconciliation only. The broker is not implemented here.

## 2. Scope

Phase 88N delivers:

- This design reconciliation artifact.
- Updates to `PROJECT_STATUS.md` and `CHANGELOG.md`.

No source implementation changes. No new CLI commands. No new tests. No storage.
No backend invocations. No prompt sending. No capture, intake, adoption, or mutation.

## 3. Non-Goals

- Implementing the permission broker.
- Implementing the shell gate.
- Implementing shell command interception.
- Fixing the 88M task-finish tracked-file bug (see §33; reserved for 88N.1).
- Modifying source files.
- Modifying test files.
- Adding storage, cache, or `.pcae` persistent state.
- Backend invocation, prompt sending, output capture, intake, adoption, mutation.
- Raw git push or force push.
- Any phase beyond 88N.

## 4. Starting Point from 87H and 88A–88M

### Phase 87 baseline (87H)

Phase 87H defined the permission broker architecture against the gate dry-run layer:

| Phase | Contribution |
|-------|-------------|
| 87C | 15 dry-run gate evaluators (generic: decision, reason_codes, safety_notes) |
| 87D | `scope_check_gate` evaluation (scope_status, matched files) |
| 87E | `backend_invocation_gate` evaluation (backend_status) |
| 87F | Adoption/source/test mutation gate evaluations |
| 87G | Commit/push gate evaluations |
| 87H | Permission broker architecture design |

The 87H broker was designed to consume gate dry-run outputs as its primary evidence
source. At that point, there were no explicit preflight commands. The broker input
model in 87H referenced `gate_dry_run` as a single evidence field.

### Phase 88 explicit preflight layer (88A–88M)

Phases 88A–88M delivered explicit, individual preflight commands for each governed
action class:

| Phase | Contribution |
|-------|-------------|
| 88A | First enforced gate boundary (scope gate selected, design only) |
| 88B | Scope gate preflight prototype (66 tests) |
| 88C | Scope gate preflight review (63 tests, no source changes) |
| 88D | Backend invocation preflight design |
| 88E | Backend invocation preflight prototype (42 tests) |
| 88F | Backend invocation preflight review (47 tests, no source changes) |
| 88G | Mutation/adoption preflight design |
| 88H | Mutation/adoption preflight prototype (34 tests) |
| 88I | Mutation/adoption preflight review (36 tests, no source changes) |
| 88J | Commit/push preflight design |
| 88K | Commit/push preflight prototype (33 tests) |
| 88L | Commit/push preflight review (41 tests, no source changes) |
| 88L.1 | Task state reconciliation (corrective, no feature changes) |
| 88M | Preflight integration verification (57 tests, no source changes) |

The explicit preflight layer is now a coherent, read-only, non-authorizing governance
surface. Each command has its own evidence model, decision values, reason codes, and
JSON envelope. The broker must now be reconciled against this concrete layer.

## 5. Current Explicit Preflight Layer

All five preflight commands are implemented and integration-verified:

```
pcae preflight scope   --json --requested-action <action> --requested-file <file>
pcae preflight backend --json --requested-backend <backend> --requested-action <action> [...]
pcae preflight mutation --json --requested-action <action> [--requested-file <file>] [...]
pcae preflight commit  --json --commit-message <msg> [--diff-present] [--tests-passed] [...]
pcae preflight push    --json --push-target <target> [--push-check-passed] [--tests-passed] [...]
```

**Shared JSON envelope (all five commands):**

| Field | Value |
|-------|-------|
| `schema_version` | `"0.1"` |
| `generated_at` | ISO 8601 timestamp |
| `source_command` | `"pcae preflight <type>"` |
| `repository_root` | absolute path |
| `preflight` | dict (command-specific fields) |

**Safety flags invariant (all five commands, all paths):**

| Flag | Value |
|------|-------|
| `authorization_granted` | always `False` |
| `execution_authorized` | always `False` |
| `repo_mutation_performed` | always `False` |
| `storage_written` | always `False` |
| `backend_invocation_performed` | always `False` |
| `commit_performed` | always `False` |
| `push_performed` | always `False` |

No preflight command grants authorization. No preflight command executes the
requested action. The entire layer is read-only and non-authorizing by design.

## 6. Permission Broker Role

The future permission broker is a policy mediation layer that:

- **Collects** preflight outputs from all relevant explicit preflight commands.
- **Collects** gate dry-run outputs for non-preflight-covered action classes.
- **Normalizes** evidence from all sources into a unified evidence record.
- **Detects** missing evidence (preflight not run, checks not passed, task absent).
- **Combines** preflight decisions conservatively: the weakest decision wins.
- **Surfaces** required human review items.
- **Surfaces** required additional evidence.
- **Surfaces** hard blocks (raw push, force push, must-never-repeat).
- **Preserves** reason codes from all contributing preflight and gate outputs.
- **Preserves** safety notes from all contributing sources.
- **Preserves** the non-authorizing boundary of each preflight output.
- **Produces** a single broker decision envelope with a unified decision, reason
  codes, safety notes, and evidence citations.
- **Never executes** the requested action.

The broker is an evidence aggregator and conservative policy combiner. It is not
an execution layer.

## 7. Permission Broker Non-Role

The future permission broker must never:

- Invoke backends.
- Send prompts.
- Capture outputs.
- Apply outputs (no adoption).
- Perform intake or intake review.
- Grant adoption approval.
- Perform adoption execution.
- Mutate source files, documentation, or tests.
- Stage files for git.
- Create commits.
- Push to remote.
- Execute raw git push.
- Force push.
- Execute shell commands.
- Bypass `pcae check`.
- Bypass `pcae health`.
- Bypass `pcae doctor`.
- Bypass `pcae push check`.
- Override task contracts.
- Override risk register controls.
- Replace the shell gate (that is a separate enforcement layer).
- Replace human review.
- Convert human approval into automatic authorization.
- Write persistent storage (deferred to a future storage phase).
- Override a hard block because human approval was provided.
- Treat missing evidence as approval.
- Treat unknown state as `allow`.

**Required boundary statement:**
88N reconciles the permission broker design with the explicit preflight layer but does
not implement the broker. The broker must not execute shell commands, create commits,
push, invoke backends, mutate files, apply captured output, perform adoption, bypass
preflight decisions, or convert human approval into automatic authorization.

## 8. Relationship to Scope Preflight

`pcae preflight scope` evaluates whether the requested action and files are within
the active task contract's allowed scope.

| Broker interaction | Rule |
|-------------------|------|
| Scope preflight is a required broker input | Missing scope preflight → `requires_more_evidence` |
| `decision: allow_preflight_only` | Scope passed; not authorization |
| `decision: blocked_by_scope` | Hard block; human approval cannot override |
| `decision: blocked_by_missing_task_contract` | Hard block; task must be active |
| Broker must preserve `scope_notes` | Forward to broker evidence record |
| Broker must preserve `scope_status` | Forward; contributes to `scope_preflight_decision` |
| Scope allow does not authorize backend invocation | Each action class requires its own preflight |

## 9. Relationship to Backend Preflight

`pcae preflight backend` evaluates whether the requested backend is known,
policy-compliant, and accompanied by required evidence (prompt present, prompt hash).

| Broker interaction | Rule |
|-------------------|------|
| Backend preflight is required for backend invocation | Missing → `requires_more_evidence` |
| `decision: allow_preflight_only` | Backend passed; not execution authorization |
| `decision: blocked_by_backend_policy` | Policy violation; hard block |
| `decision: deny_preflight` | Unknown backend; deny |
| `decision: blocked_by_missing_task_contract` | Task required |
| Broker must preserve `backend_notes` | Forward to evidence record |
| Backend allow does not authorize mutation/adoption | Separate preflight required |
| Human review always required for backend invocation | See §24 |

## 10. Relationship to Mutation/Adoption Preflight

`pcae preflight mutation` evaluates whether the requested mutation or adoption action
satisfies scope, capture evidence, and source backend requirements.

| Broker interaction | Rule |
|-------------------|------|
| Mutation preflight required for any repo mutation | Missing → `requires_more_evidence` |
| `decision: allow_preflight_only` | Mutation passed; not execution authorization |
| `decision: blocked_by_mutation_policy` | Policy violation; hard block |
| `decision: blocked_by_missing_capture` | Capture evidence absent; block |
| `decision: blocked_by_missing_task_contract` | Task required |
| Broker must preserve `mutation_notes` | Forward to evidence record |
| Mutation allow does not authorize commit | Commit preflight still required |
| Human review always required for mutation/adoption | See §24 |

## 11. Relationship to Commit/Push Preflight

`pcae preflight commit` evaluates commit evidence (message, diff, tests, health,
check, doctor). `pcae preflight push` evaluates push evidence (target, push check,
tests, health, check, doctor) and hard-blocks raw git push and force push.

| Broker interaction | Rule |
|-------------------|------|
| Commit preflight required for any commit action | Missing → `requires_more_evidence` |
| Push preflight required for any push action | Missing → `requires_more_evidence` |
| `decision: allow_preflight_only` | Evidence passed; not commit/push authorization |
| `decision: blocked_by_commit_policy` | Commit evidence failed; hard block |
| `decision: blocked_by_push_policy` | Push evidence failed; hard block |
| `decision: blocked_by_raw_git_push` | Must-never-repeat; human approval cannot override |
| `decision: blocked_by_force_push` | Must-never-repeat; human approval cannot override |
| Broker must preserve `commit_notes` and `push_notes` | Forward to evidence record |
| Push allow does not authorize push execution | Governed `pcae push` is the execution path |
| Human review always required for commit/push | See §24 |

## 12. Relationship to Gate Dry-Run

`pcae gate-dry-run` evaluates all 15 PCAE gates and produces dry-run decisions for
each. It was the primary evidence source for the 87H broker design.

The reconciled relationship:

| Aspect | Pre-88 (87H) | Post-88 (88N) |
|--------|-------------|---------------|
| Primary evidence | gate dry-run only | explicit preflights + gate dry-run |
| Scope evidence | `scope_check_gate` dry-run | `pcae preflight scope` output |
| Backend evidence | `backend_invocation_gate` dry-run | `pcae preflight backend` output |
| Mutation evidence | mutation gate dry-runs | `pcae preflight mutation` output |
| Commit/push evidence | commit/push gate dry-runs | `pcae preflight commit/push` output |
| Gate dry-run role | primary evidence | supplementary / non-preflight-covered classes |

The broker should prefer explicit preflight outputs over gate dry-run outputs where
both are available, because explicit preflights are more specific, carry richer
evidence fields, and have been integration-verified. Gate dry-run outputs remain
useful for action classes not yet covered by explicit preflight commands.

Gate dry-run outputs are advisory. They do not enforce. They do not authorize.
The broker must not treat a gate dry-run `deny` as a definitive block without
also checking the corresponding explicit preflight output.

## 13. Relationship to Lifecycle State

The broker must evaluate the lifecycle state before issuing any decision.

| Lifecycle state | Broker behavior |
|----------------|----------------|
| Active task present | Required for `allow_preflight_only` or `allow` |
| No active task | `deny` or `requires_more_evidence` for most actions |
| Task status mismatch | `blocked_by_task_contract` |
| Task scope violation | `blocked_by_scope` |
| Phase check mismatch | `blocked_by_failed_check` |
| Session continuity mismatch | `requires_more_evidence` until resolved |

All five preflight commands already detect lifecycle state (`lifecycle_state` field).
The broker must propagate and respect these lifecycle state signals.

## 14. Relationship to Task Contracts

Task contracts define the scope, forbidden files, allowed zones, enforcement mode,
acceptance criteria, and acceptance checks for every active phase.

| Broker interaction | Rule |
|-------------------|------|
| Active task contract is a required broker input | Missing → `deny` |
| Task contract `status != active` | `blocked_by_task_contract` |
| Requested file outside `allowed_files` | `blocked_by_scope` |
| Requested file in `forbidden_files` | `blocked_by_scope` (hard) |
| Forbidden zone violation | `blocked_by_scope` (hard) |
| Enforcement mode `advisory` | Broker surfacesvviolation but does not auto-block in advisory |
| Enforcement mode `enforced` | Broker treats scope violations as hard blocks |

## 15. Relationship to Risk Register

`pcae risk-register` surfaces active risks, their severity, and resolution state.

| Broker interaction | Rule |
|-------------------|------|
| Active risk present | `blocked_by_risk` or `requires_human_review` |
| Risk severity `critical` | `blocked_by_risk` (hard); human review required |
| Risk accepted | Accepted ≠ mitigated; broker must still flag |
| Risk resolved | May allow with other evidence |
| Missing risk register | `requires_more_evidence` for high-risk actions |

Accepted risk is evidence of human awareness, not evidence of resolution. The broker
must not treat accepted risk as clearance.

## 16. Relationship to Decision Log

`pcae decision-log` records past governance decisions.

| Broker interaction | Rule |
|-------------------|------|
| Must-never-repeat control in log | `blocked_by_must_never_repeat` (hard) |
| Prior denial for same action class | Factor in conservative decision |
| Prior approval for same action class | Historical context; does not automatically re-authorize |
| Decision log unavailable | `requires_more_evidence` for high-risk actions |

## 17. Relationship to Project State

`pcae project-state` provides a snapshot of current recommendations, readiness,
and governance posture.

| Broker interaction | Rule |
|-------------------|------|
| `next_safe_action` recommendation | Context; does not authorize |
| `recommended_phase` | Context; does not authorize |
| Readiness signal | Informs but does not replace preflight outputs |
| Project state unavailable | Advisory degradation; broker continues with other evidence |

Project state recommendations are informational. The broker must not convert a
"ready" recommendation into an automatic allow.

## 18. Relationship to Human Review

Human review is a required evidence input for high-risk actions. It is not a bypass
mechanism.

| Human review property | Rule |
|----------------------|------|
| May satisfy `requires_human_review` | Yes, with explicit review record |
| May override hard blocks | No |
| May replace missing preflight outputs | No |
| May replace failed `pcae check` | No |
| May replace failed `pcae health` | No |
| May replace failed `pcae doctor` | No |
| May replace failed tests | No |
| May authorize raw git push | No |
| May authorize force push | No |
| May authorize shell command execution | No (shell gate governs this) |
| May authorize backend invocation without backend preflight | No |
| May authorize mutation/adoption without mutation preflight | No |
| May authorize commit/push without commit/push preflight | No |

## 19. Evidence Model

The broker assembles evidence from multiple sources before reaching a decision.
Evidence is normalized into a unified evidence record with the following properties:

| Property | Description |
|----------|-------------|
| `evidence_sources` | List of artifact IDs / command outputs consulted |
| `missing_evidence` | Required inputs that are absent |
| `conflicting_evidence` | Inputs that produce contradictory signals |
| `preflight_decisions` | Map of preflight type → decision for each run preflight |
| `gate_decisions` | Map of gate name → decision for each evaluated gate |
| `lifecycle_signals` | Lifecycle state from active task, session, health, check |
| `risk_signals` | Active risks from risk register |
| `decision_log_signals` | Must-never-repeat controls, prior decisions |
| `human_review_present` | Whether a human review record is present |
| `human_approval_present` | Whether a human approval record is present |
| `accepted_risk_present` | Whether an accepted-risk record is present |

**Conservative combination rule:** The broker decision is the most restrictive
decision across all evidence sources. A single `deny` or `blocked_by_*` from any
source blocks the action, regardless of positive signals from other sources.

## 20. Broker Input Model

The reconciled broker input model extends the 87H model with explicit preflight fields:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `requested_action` | string | yes | Action being requested |
| `requested_files` | list[string] | no | Files to be affected |
| `active_task_contract` | object | yes | Active task contract |
| `task_contract_path` | string | yes | Path to task contract file |
| `task_contract_status` | string | yes | Must be `active` |
| `lifecycle_state` | string | yes | From pcae health / check |
| `scope_preflight_result` | object | no | `pcae preflight scope` output |
| `backend_preflight_result` | object | no | `pcae preflight backend` output |
| `mutation_preflight_result` | object | no | `pcae preflight mutation` output |
| `commit_preflight_result` | object | no | `pcae preflight commit` output |
| `push_preflight_result` | object | no | `pcae preflight push` output |
| `gate_dry_run_result` | object | no | `pcae gate-dry-run` output |
| `risk_register_state` | object | no | `pcae risk-register` output |
| `decision_log_state` | object | no | `pcae decision-log` output |
| `project_state_snapshot` | object | no | `pcae project-state` output |
| `human_review_record` | object | no | Explicit human review artifact |
| `human_approval_record` | object | no | Explicit human approval artifact |
| `accepted_risk_record` | object | no | Accepted-risk artifact |
| `must_never_repeat_controls` | list | no | From decision log / risk register |
| `git_state` | object | no | Repository state |
| `branch_state` | object | no | Branch / upstream state |
| `test_results` | object | no | Test pass/fail state |
| `pcae_check_result` | object | no | `pcae check` output |
| `pcae_health_result` | object | no | `pcae health` output |
| `doctor_result` | object | no | `pcae doctor` output |
| `push_check_result` | object | no | `pcae push check` output |
| `source_backend` | string | no | Backend used for capture |
| `capture_artifact` | object | no | Capture artifact for adoption |
| `diff_artifact` | object | no | Diff artifact for commit |
| `commit_message` | string | no | For commit actions |

## 21. Broker Output Model

The reconciled broker output model extends the 87H model with explicit preflight
decision fields and full performed-flag inventory:

**Envelope:**

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | `"0.1"` |
| `generated_at` | string | ISO 8601 timestamp |
| `source_command` | string | `"pcae broker evaluate"` (future) |
| `repository_root` | string | Absolute path |
| `broker` | object | Broker decision (see below) |
| `warnings` | list | Non-blocking warnings |
| `errors` | list | Evaluation errors |
| `safety_notes` | string | Safety annotations |

**Broker object:**

| Field | Type | Description |
|-------|------|-------------|
| `broker_type` | string | `"permission_broker"` |
| `requested_action` | string | Action evaluated |
| `decision` | string | Unified broker decision (see §22) |
| `reason_codes` | list[string] | All contributing reason codes |
| `active_task_detected` | boolean | Whether active task was found |
| `task_contract_path` | string | Path to task contract |
| `task_contract_status` | string | Task status at evaluation time |
| `lifecycle_state` | string | Lifecycle state signal |
| `scope_preflight_decision` | string | From `pcae preflight scope` |
| `backend_preflight_decision` | string | From `pcae preflight backend` |
| `mutation_preflight_decision` | string | From `pcae preflight mutation` |
| `commit_preflight_decision` | string | From `pcae preflight commit` |
| `push_preflight_decision` | string | From `pcae preflight push` |
| `gate_dry_run_decision` | string | From `pcae gate-dry-run` (relevant gate) |
| `risk_state` | string | Active / resolved / none |
| `decision_log_state` | string | Must-never-repeat present / none |
| `project_state_available` | boolean | Whether project state was present |
| `human_review_required` | boolean | Whether human must review |
| `human_approval_present` | boolean | Whether human approval was provided |
| `human_approval_sufficient` | boolean | Whether approval satisfies requirements |
| `accepted_risk_present` | boolean | Whether accepted-risk record exists |
| `accepted_risk_sufficient` | boolean | Whether accepted risk satisfies requirements |
| `must_never_repeat_applies` | boolean | Whether a must-never-repeat control applies |
| `more_evidence_required` | boolean | Whether additional evidence is needed |
| `hard_block_present` | boolean | Whether any hard block exists |
| `evidence_sources` | list[string] | All consulted evidence sources |
| `missing_evidence` | list[string] | Required evidence not present |
| `conflicting_evidence` | list[string] | Contradictory evidence signals |
| `safety_notes` | string | Aggregated safety annotations |
| `authorization_granted` | boolean | Always `false` in this design phase |
| `execution_authorized` | boolean | Always `false` in this design phase |
| `backend_invocation_performed` | boolean | Always `false` |
| `prompt_sent` | boolean | Always `false` |
| `capture_performed` | boolean | Always `false` |
| `intake_performed` | boolean | Always `false` |
| `adoption_review_performed` | boolean | Always `false` |
| `adoption_approval_granted` | boolean | Always `false` |
| `adoption_execution_performed` | boolean | Always `false` |
| `mutation_performed` | boolean | Always `false` |
| `commit_performed` | boolean | Always `false` |
| `push_performed` | boolean | Always `false` |
| `raw_git_push_performed` | boolean | Always `false` |
| `force_push_performed` | boolean | Always `false` |
| `shell_command_performed` | boolean | Always `false` |
| `repo_mutation_performed` | boolean | Always `false` |
| `storage_written` | boolean | Always `false` |

## 22. Decision Model

The reconciled broker decision model extends 87H with the explicit preflight vocabulary:

| Decision | Meaning | Permits Action |
|----------|---------|----------------|
| `allow_preflight_only` | All preflights passed; not execution authorization | no |
| `deny` | Action refused; no specific blocker category | no |
| `requires_human_review` | Human must provide explicit review/approval | no |
| `requires_more_evidence` | Required evidence absent or insufficient | no |
| `blocked_by_scope` | Exceeds task contract scope | no |
| `blocked_by_backend_policy` | Backend policy violation | no |
| `blocked_by_mutation_policy` | Mutation/adoption policy violation | no |
| `blocked_by_commit_policy` | Commit evidence failed | no |
| `blocked_by_push_policy` | Push evidence failed | no |
| `blocked_by_lifecycle_state` | Lifecycle state incompatible | no |
| `blocked_by_task_contract` | Task contract absent or status mismatch | no |
| `blocked_by_risk` | Active risk in risk register | no |
| `blocked_by_must_never_repeat` | Must-never-repeat control applies | no |
| `blocked_by_failed_check` | `pcae check` failed | no |
| `blocked_by_failed_health` | `pcae health` failed | no |
| `blocked_by_failed_doctor` | `pcae doctor` failed | no |
| `blocked_by_failed_tests` | Test results failed | no |
| `blocked_by_push_check` | `pcae push check` not ready | no |
| `blocked_by_raw_git_push` | Raw git push requested (must-never-repeat) | no |
| `blocked_by_force_push` | Force push requested (must-never-repeat) | no |
| `blocked_by_conflicting_evidence` | Evidence sources contradict | no |
| `unknown` | State cannot be determined; deny | no |

**Key rules:**
- `allow_preflight_only` is not execution authorization.
- `allow_preflight_only` must not set `authorization_granted=true`.
- `allow_preflight_only` must not set `execution_authorized=true`.
- All `performed` flags must remain `false` on `allow_preflight_only`.
- `unknown` must never be treated as `allow`.
- A hard block cannot be overridden by human approval.
- The broker must combine all preflight decisions conservatively.

## 23. Deny-by-Default Policy

The broker denies by default. An action is blocked unless all required evidence is
present and positive. The following conditions each independently produce a denial:

| Condition | Broker Decision |
|-----------|----------------|
| No active task | `deny` or `requires_more_evidence` |
| Task contract status ≠ `active` | `blocked_by_task_contract` |
| Scope preflight denied | `blocked_by_scope` |
| Unknown backend | `requires_human_review` or `blocked_by_backend_policy` |
| Missing captured output for adoption | `requires_more_evidence` |
| Mutation/adoption preflight denied | `blocked_by_mutation_policy` |
| Commit preflight denied | `blocked_by_commit_policy` |
| Push preflight denied | `blocked_by_push_policy` |
| `pcae check` failed | `blocked_by_failed_check` |
| `pcae health` failed | `blocked_by_failed_health` |
| `pcae doctor` failed | `blocked_by_failed_doctor` |
| Tests failed | `blocked_by_failed_tests` |
| `pcae push check` not ready | `blocked_by_push_check` |
| Raw git push requested | `blocked_by_raw_git_push` |
| Force push requested | `blocked_by_force_push` |
| Active risk present | `blocked_by_risk` or `requires_human_review` |
| Must-never-repeat applies | `blocked_by_must_never_repeat` |
| Conflicting evidence | `blocked_by_conflicting_evidence` |
| Unknown lifecycle state | `unknown` or `requires_more_evidence` |

## 24. Human-Approval Limitations

Human approval is evidence of human decision, not a bypass mechanism. Its limitations:

| Human approval limitation | Rule |
|--------------------------|------|
| Cannot override hard blocks | `blocked_by_raw_git_push`, `blocked_by_force_push`, `blocked_by_must_never_repeat` are hard blocks |
| Cannot replace missing preflight outputs | Missing preflight → `requires_more_evidence` even with approval |
| Cannot replace failed `pcae check` | Check must pass independently |
| Cannot replace failed `pcae health` | Health must pass independently |
| Cannot replace failed `pcae doctor` | Doctor must pass independently |
| Cannot replace failed tests | Tests must pass independently |
| Cannot authorize raw git push | Hard block; no override |
| Cannot authorize force push | Hard block; no override |
| Cannot authorize shell command execution | Shell gate governs this |
| Cannot authorize backend invocation without backend preflight | Preflight required |
| Cannot authorize mutation/adoption without mutation preflight | Preflight required |
| Cannot authorize commit/push without commit/push preflight | Preflight required |
| Cannot convert review into automatic authorization | Approval is evidence; broker still decides |

Human review satisfies `human_review_required` when an explicit review record is
present and its scope matches the requested action.

## 25. Accepted-Risk Limitations

Accepted risk is evidence of human awareness of a risk, not evidence of its resolution.

| Accepted risk limitation | Rule |
|-------------------------|------|
| Accepted ≠ mitigated | Risk register `accepted` status does not clear the risk signal |
| Accepted ≠ approved action | Accepted risk does not authorize the risky action |
| Broker must still flag accepted risk | `accepted_risk_present=true` in output |
| Broker may use accepted risk to downgrade `blocked_by_risk` → `requires_human_review` | Only if risk severity and scope allow |
| Accepted risk does not override other blocks | Other blockers remain active |

## 26. Must-Never-Repeat Controls

Must-never-repeat controls are hard constraints derived from the decision log and
risk register. They cannot be silently overridden by any input.

Current must-never-repeat controls:

| Control | Decision |
|---------|---------|
| Raw git push | `blocked_by_raw_git_push` — no override |
| Force push | `blocked_by_force_push` — no override |
| `--no-verify` on commits | Hard block — `pcae task finish` uses `--no-verify` only for its internal governed commit; external use is forbidden |
| Source mutation without active task contract | Hard block |
| Adoption execution without mutation preflight | Hard block |

Human approval cannot override must-never-repeat controls. Accepted risk cannot
override must-never-repeat controls. The only path to removing a must-never-repeat
control is a governed phase decision that explicitly removes it from the decision log.

## 27. Read-Only vs Execution Boundary

The entire Phase 88 explicit preflight layer is read-only and non-authorizing. This
is the boundary the broker must preserve when consuming preflight outputs.

| Layer | Read-only | Non-authorizing | Does not execute |
|-------|-----------|-----------------|-----------------|
| `pcae preflight scope` | yes | yes | yes |
| `pcae preflight backend` | yes | yes | yes |
| `pcae preflight mutation` | yes | yes | yes |
| `pcae preflight commit` | yes | yes | yes |
| `pcae preflight push` | yes | yes | yes |
| `pcae gate-dry-run` | yes | yes | yes |
| **Permission broker (future)** | yes | yes | yes |

The broker is a policy mediation layer, not an execution layer. Even when the broker
produces `allow_preflight_only`, the actual execution of the requested action requires
a separate governed execution path (e.g., `pcae push`, `pcae commit implementation`,
future `pcae exec`).

## 28. Shell Gate Boundary

The shell gate (designed in 87I, not yet implemented) is the enforcement layer that
intercepts shell commands at execution time. The broker and shell gate have distinct
roles:

| Dimension | Permission Broker | Shell Gate |
|-----------|------------------|-----------|
| Role | Policy mediation | Execution enforcement |
| Runs when | Before action is attempted | At execution time |
| Intercepts | Nothing (advisory) | Shell commands |
| Decision | Broker decision envelope | Allow / deny execution |
| Persistent | No (design phase) | Wraps shell |
| Relationship | Broker decision informs gate | Gate enforces broker decisions |

The broker does not replace the shell gate. The shell gate does not replace the
broker. They are complementary layers: the broker decides policy, the shell gate
enforces it.

In the absence of an implemented shell gate, broker decisions are advisory. They
inform humans and governance tooling but do not enforce at the OS level.

## 29. Storage/Cache Policy

Phase 88N creates no storage, cache, or `.pcae` persistent state. This document
defines the future storage model only:

| Storage concern | Policy |
|----------------|--------|
| Broker decision records | Future phase; not in 88N |
| Preflight output caching | No caching permitted; run fresh each evaluation |
| `.pcae/broker/` directory | Not created until a governed storage phase |
| Audit event persistence | Future phase; not in 88N |
| Session state for broker | Not applicable; broker is stateless in this design |

Future broker storage must be introduced through a separate explicit governed phase
following the same lifecycle pattern as Phases 69E (authorization store) and 69F
(audit record store).

## 30. Audit Requirements

The future broker must produce auditable decisions. Future audit events:

| Event | Trigger |
|-------|---------|
| `broker_evaluation_started` | Action evaluation requested |
| `broker_evidence_collected` | Evidence assembly complete |
| `broker_decision_produced` | Decision envelope generated |
| `broker_human_review_required` | Routed to human review |
| `broker_hard_block_triggered` | Must-never-repeat or hard block applied |
| `broker_denied` | Action denied |
| `broker_requires_more_evidence` | Evidence missing or insufficient |
| `broker_allow_preflight_only` | All preflights passed (not authorization) |
| `broker_evaluation_error` | Evaluation failure |

Each audit event must cite the evidence sources consulted and the reason codes that
produced the decision.

## 31. Failure Handling

| Condition | Broker Behavior |
|-----------|----------------|
| Missing required input (task contract) | `deny` |
| Missing optional input (preflight result) | `requires_more_evidence` for that evidence class |
| Unknown lifecycle state | `requires_human_review` or `unknown` |
| Active risk relevant to action | `blocked_by_risk` or `requires_human_review` |
| Must-never-repeat control present | `blocked_by_must_never_repeat` |
| Conflicting evidence signals | `blocked_by_conflicting_evidence` |
| Unsafe action class (raw push, force push) | `blocked_by_raw_git_push` / `blocked_by_force_push` |
| Storage unavailable | Do not write; report limitation in `errors` |
| Preflight command unavailable | `requires_more_evidence` |
| `pcae check` failure | `blocked_by_failed_check` |
| `pcae health` failure | `blocked_by_failed_health` |
| Evaluation exception | `unknown`; do not allow |

Unknown and error states must never produce `allow_preflight_only`. They must
produce `unknown` or the most conservative applicable blocker.

## 32. Safety Invariants

1. The broker is not implemented in 88N. It does not authorize in 88N.
2. The broker does not enforce in 88N.
3. The broker does not invoke backends in 88N.
4. The broker does not mediate shell commands in 88N.
5. The broker does not mutate the repository in 88N.
6. The broker does not commit or push in 88N.
7. The broker does not write storage in 88N.
8. All five explicit preflight commands preserve `authorization_granted=false`.
9. All five explicit preflight commands preserve `execution_authorized=false`.
10. All five explicit preflight commands preserve all performed flags as `false`.
11. Future broker must deny by default.
12. Future broker must combine decisions conservatively: weakest decision wins.
13. Future broker must preserve all reason codes and safety notes from preflights.
14. Future broker must require human review for all high-risk actions.
15. Future broker must not override must-never-repeat controls.
16. Future broker must not treat `allow_preflight_only` as execution authorization.
17. Future broker must not treat missing evidence as approval.
18. Future broker must not treat unknown state as `allow`.
19. Future broker must preserve `authorization_granted=false` until execution is
    explicitly authorized through a separate governed path.
20. Future broker `allow_preflight_only` must not set any performed flag to `true`.

## 33. Known 88M Task-Finish Lifecycle Bug

During 88M completion, `pcae task finish --commit` failed when the active task
contract file in `tasks/active/` had never been tracked by git.

**Observed failure sequence:**

1. `pcae task finish --staged-file-aware --skip-checks --commit "..."` was called.
2. The command moved the task file from `tasks/active/` to `tasks/done/`.
3. The command then attempted to stage the old active path: `git add tasks/active/...md`
4. Because the file was never tracked by git, `git add` failed with:
   `fatal: pathspec 'tasks/active/...md' did not match any files`
5. The commit was never created.
6. The pre-commit hook correctly blocked subsequent raw recovery commit attempts
   because no active task existed after the partial finish.

**Recovery workaround (confirmed effective):**

Commit the active task contract file through the governed path first:

```
pcae commit implementation \
  --path tasks/active/<task-file>.md \
  --message "Track <phase> task contract for governed finish recovery"
```

Then run `pcae task finish` normally. With the task file tracked by git, the
`git add tasks/active/...md` step stages the deletion correctly.

**Scope:**

This bug is not fixed in 88N. It should be fixed in the immediate corrective phase:

> **88N.1 — Task Finish Tracked-File Robustness**

88N.1 should be introduced before any permission broker implementation or shell gate
implementation so that future governed phases can complete without manual recovery.

## 34. Future Test Strategy

When the broker is implemented (88P or later), tests should cover:

| Test area | Description |
|-----------|-------------|
| Conservative combination | Single `deny` blocks despite positive preflights |
| Missing evidence | Each optional input absent → `requires_more_evidence` |
| Hard blocks | Raw push, force push, must-never-repeat → no human override |
| Performed flags invariant | All performed flags `false` on all paths |
| Authorization flags invariant | `authorization_granted=false`, `execution_authorized=false` always |
| Unknown state | `unknown` never produces `allow` |
| Human review | `requires_human_review` satisfied only by explicit review record |
| Accepted risk | Accepted ≠ mitigated; risk still blocks |
| Scope propagation | Scope block from preflight propagates to broker |
| Lifecycle detection | No active task → `deny` |
| Task status mismatch | `done` task → `blocked_by_task_contract` |
| Evidence citation | Broker output cites all consulted evidence sources |
| Reason code preservation | All preflight reason codes preserved in broker output |
| Conflicting evidence | Contradictory signals → `blocked_by_conflicting_evidence` |
| Gate dry-run integration | Gate dry-run supplementary for non-preflight-covered classes |

Tests should follow the Phase 88 pattern: prefer Python-level evaluator calls over
subprocess calls for repeated assertions. Use parametrization to reduce duplication.

## 35. Future Implementation Roadmap

| Phase | Deliverable |
|-------|-------------|
| **88N.1** | Task Finish Tracked-File Robustness (lifecycle bug fix) |
| **88O** | Shell Gate Design Reconciliation |
| **88P** | Permission Broker Prototype |
| **88Q** | Permission Broker Tests and False-Positive Review |
| **88R** | Broker + Shell Gate Integration Design |

**88N.1 must precede 88O and 88P.** The task-finish lifecycle bug discovered in 88M
affects any future governed phase. It should be fixed before additional implementation
phases introduce more complexity.

## 36. Recommended Next Phase

**88N.1 — Task Finish Tracked-File Robustness**

Before implementing broker or shell-gate behavior, fix the lifecycle reliability bug
discovered during 88M so future governed phases can complete without requiring manual
recovery. The fix should make `pcae task finish` handle the case where the active
task file in `tasks/active/` was never tracked by git, by either:

- Auto-committing the task file before staging its deletion, or
- Gracefully handling the pathspec failure and recovering without a partial state.

The 88N.1 fix must follow the same phase lifecycle as all previous phases: task
contract, implementation commit, completion commit, governed push.

---

permission_broker_reconciliation_name=phase_88_permission_broker_reconciliation
permission_broker_reconciliation_version=0.1
permission_broker_reconciliation_status=draft_documented
implementation_status=not_started
recommended_next_phase=88N.1_task_finish_tracked_file_robustness
backend_invocation_performed=false
new_prompts_sent=false
new_capture_performed=false
new_intake_performed=false
new_adoption_review_performed=false
new_adoption_approval_performed=false
new_adoption_execution_performed=false
commit_performed=false_except_required_phase_commits
push_performed=false_except_final_governed_pcae_push
raw_git_push_performed=false
force_push_performed=false
permission_broker_implementation_authorized=false
shell_gate_implementation_authorized=false
task_finish_bugfix_authorized=false
source_mutation_authorized=false
test_mutation_authorized=false
execution_authorized=false
