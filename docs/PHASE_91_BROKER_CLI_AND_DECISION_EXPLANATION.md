# Phase 91B — Broker CLI and Decision Explanation

```
phase_name    = phase_91b_broker_cli_and_decision_explanation
phase_version = 1.0
phase_status  = completed
implementation_status = simulation_only
recommended_next_phase = 91C — Hard-Block Policy Readiness
```

## 1. Purpose

Expose the Phase 91A simulation-only permission broker through safe CLI inspection commands and add decision explanation support. All commands are read-only, simulation-only, and never execute actions.

## 2. CLI Command Surface

### pcae permission-broker status

Shows broker availability, simulation-only status, and enforcement state.

```
$ pcae permission-broker status
Permission broker status
  Available:              True
  Simulation only:        True
  Enforcement active:     False
  Enforcement ready:      False
  Enforcement authorized: False
  Decision model:         4-outcome (allow, deny, human_review, more_evidence)
  Phase:                  91B

  ⚠️  Simulation only — no enforcement path is active.
  The operator retains full authority.
```

Supports `--json`.

### pcae permission-broker explain --reason-code <code>

Explains a broker reason code with category, meaning, and overridability.

```
$ pcae permission-broker explain --reason-code blocked_by_force_push
Reason code: blocked_by_force_push
  Summary:     Force push is permanently blocked.
  Category:    hard_block
  Meaning:     Force push rewrites shared history and is never permitted.
  Overridable: no — hard blocks cannot be overridden (88V §16)
```

Unknown reason codes fail with non-zero exit and list known codes. Supports `--json`.

### pcae permission-broker check

Evaluates proposed action metadata through the simulation-only broker.

```
$ pcae permission-broker check --action-type push --command-class force_push
Permission broker check (simulation only)
  Action type:     push
  Command class:   force_push
  Decision:        deny
  Hard block:      True
  Reason:          blocked_by_force_push
  Message:         Hard block: force_push. ...

  ⚠️  Simulation only — PCAE did NOT execute, intercept, or authorize anything.
```

Supports `--json` and 13 metadata flags (`--action-type`, `--command-class`, `--path`, `--task-present`, `--task-scope-known`, `--allowed-path`, `--forbidden-path`, `--approval-present`, `--approval-fresh`, `--accepted-risk-present`, `--readiness-ready`, `--enforcement-authorized`, `--repo-dirty`).

## 3. Reason-Code Explanation Model

24 reason codes are registered in `_REASON_EXPLANATIONS` across 4 categories:

| Category | Count | Example |
|----------|-------|---------|
| hard_block | 12 | blocked_by_force_push, blocked_by_raw_git_push |
| more_evidence | 4 | task_scope_unknown, missing_action_type |
| human_review | 5 | commit_requires_human_review, stale_approval |
| allow | 3 | allow_preflight_only, all_checks_passed |

Each explanation includes: summary, category, meaning, and overridability.

Unknown reason codes fail safely with non-zero exit and a list of known codes.

## 4. Simulation-Only Boundary

All three commands are read-only and simulation-only:
- **status**: reports broker state, never changes it
- **explain**: looks up reason code in a static registry
- **check**: calls `evaluate_permission_broker()` which is a pure function

No command:
- Executes proposed actions
- Intercepts shell commands
- Invokes backends
- Sends prompts
- Grants authorization
- Persists state
- Modifies the repository

## 5. JSON Output

All three commands support `--json` with consistent output:

**status --json**: broker_available, simulation_only, no_enforcement, no_execution, enforcement_ready, enforcement_authorized, decision_model, phase

**explain --json**: reason_code, explanation { summary, category, meaning, overridable }

**check --json**: Full `evaluate_permission_broker()` output including decision, hard_block, reason_code, reason_codes, message, required_evidence, audit_payload, simulation_only, no_execution, no_enforcement, authorization_granted, execution_authorized, schema_version

## 6. Relationship to 91A

91B CLI commands consume the 91A `evaluate_permission_broker()` function. The CLI is a thin presentation layer — all decision logic lives in 91A's core module. The existing 88R `build_permission_broker()` and `pcae permission-broker evaluate` command are unchanged.

## 7. What Remains for 91C

- Hard-block policy readiness: verify all hard blocks are non-overridable across all code paths
- Integration with the readiness reporter (89N)
- Performance and edge-case hardening
- Documentation of the full hard-block policy surface

## 8. No-Go Conditions

- No enforcement implementation until all 89J readiness gates are satisfied
- No shell interception or wrappers
- No backend invocation from broker CLI
- No command execution through any PCAE path

---

*Phase 91B adds safe CLI inspection commands to the simulation-only permission broker. No enforcement, shell interception, wrappers, backend invocation, Telegram control, notification code, or command execution path was implemented. Recommended next phase: 91C — Hard-Block Policy Readiness.*
