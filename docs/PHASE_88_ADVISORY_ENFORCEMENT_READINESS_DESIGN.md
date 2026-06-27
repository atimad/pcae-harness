# Phase 88W — Advisory Enforcement Readiness Design

```
advisory_enforcement_readiness_design_name    = phase_88_advisory_enforcement_readiness_design
advisory_enforcement_readiness_design_version = 0.1
advisory_enforcement_readiness_design_status  = draft_documented
implementation_status                         = not_started
recommended_next_phase                        = 88X_advisory_mode_prototype
```

## 1. Purpose

Define PCAE's advisory enforcement readiness layer. This document specifies how
PCAE can present broker + shell gate decisions as advisory warnings,
recommendations, and dry-run enforcement guidance **without** blocking commands,
intercepting shell execution, installing wrappers, mutating shell configuration,
invoking backends, or granting real authorization.

Advisory enforcement is the first visible enforcement mode: PCAE evaluates a
proposed command and tells the operator what *would* happen, but does not
execute, prevent, intercept, mutate, or authorize anything.

This is a design document. Nothing is implemented here. No source files, test
files, shell configuration files, or shell wrappers are modified.

## 2. Scope

In scope (design only):

- Advisory enforcement terminology definitions
- Advisory mode behavior specification
- What advisory mode may display and must not do
- Relationship to broker decisions (BPE_DECISIONS)
- Relationship to shell gate decisions (SGP_DECISIONS)
- Relationship to hard blocks (BPE_HARD_BLOCK_DECISIONS)
- Relationship to human approval and accepted risk
- Relationship to secret redaction (88V.1 rules)
- Relationship to active task state
- Relationship to PCAE health/check/doctor/push governance
- Advisory output JSON model
- Advisory decision vocabulary
- CLI/human-readable output guidance
- No-execution and no-interception guarantees
- Audit/logging boundaries
- Dry-run-only behavior specification
- Operator workflow design
- Disable/rollback expectations for future advisory prototype
- Test requirements for future advisory prototype
- Transition criteria from advisory design to advisory prototype
- Future CLI sketch (not implemented)
- Recommended next phase

Out of scope:

- Implementing advisory mode
- Implementing blocking enforcement
- Implementing shell interception
- Installing shell wrappers
- Modifying shell configuration
- Executing, intercepting, or blocking any command
- Invoking backends
- Sending prompts, capturing outputs, performing intake/adoption
- Granting execution authorization
- Writing persistent broker/shell-gate/advisory state or cache
- Modifying `src/pcae/core/shell_gate.py`
- Modifying `src/pcae/core/permission_broker.py`
- Adding or modifying tests (beyond documentation validation)
- Phase 88X task contract
- Any phase beyond 88W

## 3. Non-Goals

88W must not and does not:

- Implement any enforcement mechanism
- Implement any advisory mode command or CLI
- Install shell wrappers or hooks
- Modify shell configuration (`.bashrc`, `.zshrc`, etc.)
- Execute, intercept, or block any command
- Invoke backends
- Send prompts, capture outputs, perform intake/adoption
- Grant real execution authorization
- Override hard blocks
- Replace human review
- Write persistent broker/shell-gate/advisory storage or cache
- Change broker or shell gate source behavior
- Change any test behavior
- Create Phase 88X task contract
- Start any phase beyond 88W

## 4. Current State After 88V.1

As of 88V.1 completion:

- **Permission Broker** (88R/88T): Read-only decision aggregator. Consumes
  governance evidence (shell gate classification, scope preflight, health/check/
  doctor/push status) and returns a conservative broker decision envelope.
  Decisions include `allow_preflight_only`, `requires_human_review`,
  `blocked_by_shell_gate`, `blocked_by_force_push`, etc. Never executes
  commands, invokes backends, or grants authorization.

- **Shell Gate** (88P/88Q/88T): Read-only command classifier. Categorizes
  proposed shell commands into 24 categories and maps to 26 decision values.
  Detects write operations, secret access, backend invocation, network access,
  environment mutation, and more. Never executes command text.

- **Secret Redaction** (88V.1): Secret-like VAR=val prefixes detected and
  redacted. `env`/`printenv` classified as `secret_access`.
  `broker.requested_command` redacted when `secret_access_detected`.
  Shell-gate `deny` mapped to `blocked_by_shell_gate` (hard block).

- **Enforcement Boundary** (88V): All six enforcement stages defined
  (0: Read-Only Classification, 1: Advisory, 2: Advisory With Warnings,
  3: Blocking Gate, 4: Execution Gate With Human Approval,
  5: Enforcement With Accepted Risk, 6: Full Enforcement). Stage 0 is
  fully implemented. Stage 1 (Advisory) is designed here. Stages 2–6
  are out of scope.

- **All performed/authorization flags**: Unconditionally `False`.

- **Hard blocks**: 18 broker hard block decisions in
  `BPE_HARD_BLOCK_DECISIONS`, including `blocked_by_shell_gate`,
  `blocked_by_force_push`, `blocked_by_backend_policy`, etc.

- **Test baseline**: 2,709 fast-green, 7,958 quick tier, 8,695 full suite.

## 5. Advisory Enforcement Terminology

| Term | Definition |
|------|-----------|
| **Advisory Mode** | PCAE evaluates a proposed command/action and tells the operator what *would* be the broker and shell gate decisions, but does not execute, prevent, intercept, mutate, or authorize anything. |
| **Advisory Decision** | A would-* decision value indicating what the broker would decide if enforcement were active. Never an authorization. |
| **Advisory Output** | The structured JSON or human-readable text produced by advisory mode. Contains only would-* decisions, never real authorization flags. |
| **Would-Allow** | Advisory indication that a command would pass all governance checks and proceed to preflight-only (still no execution authorization). |
| **Would-Block** | Advisory indication that a command would be blocked by a hard block. The block is not enforced in advisory mode. |
| **Would-Require** | Advisory indication that a command would require additional evidence, human review, preflight, or active task before proceeding. |
| **Would-Deny** | Advisory indication that a command would be unconditionally denied. |
| **Advisory Recommendation** | Human-readable next-action guidance derived from the advisory decision. |
| **Dry-Run-Only** | Advisory mode operates entirely within PCAE's read-only classifiers; it never reaches outside the process to intercept, block, or modify shell behavior. |
| **Operator Workflow** | The sequence of steps an operator follows: propose → evaluate → read advisory output → decide manually. PCAE does not execute. |

## 6. Advisory Mode Definition

Advisory mode is a **read-only, non-authorizing, non-intercepting** evaluation
layer. It sits on top of the existing broker + shell gate infrastructure and
produces structured output that answers the question:

> "If PCAE were enforcing policy, what would happen if I ran this command?"

Advisory mode:

- **May** evaluate proposed commands against shell gate classifier
- **May** evaluate proposed actions against broker decision engine
- **May** display broker decision, shell gate decision, shell gate category
- **May** display reason codes, missing evidence, evidence sources
- **May** display would-block / would-require / would-allow guidance
- **May** display human-readable operator recommendations
- **May** display redacted command summaries
- **Must not** execute any command
- **Must not** intercept or block any shell command
- **Must not** modify shell configuration
- **Must not** install wrappers or hooks
- **Must not** invoke backends
- **Must not** send prompts, capture outputs, perform intake/adoption
- **Must not** grant `execution_authorized = True`
- **Must not** grant `authorization_granted = True`
- **Must not** mutate repository state
- **Must not** write persistent storage or cache

### Advisory Output Vocabulary

Advisory output **may** use these terms:

- `would_allow_read_only`
- `would_allow_governed_preflight_only`
- `would_require_preflight`
- `would_require_human_review`
- `would_require_active_task`
- `would_require_more_evidence`
- `would_block`
- `would_deny`

Advisory output **must not** use these terms:

- `execution_authorized = true`
- `authorization_granted = true`
- `command_executed = true`
- `enforcement_applied = true`
- `shell_intercepted = true`
- `command_blocked = true`

### Advisory Mode Is Non-Authorizing

Every advisory output, whether JSON or human-readable, must explicitly state
that advisory mode is non-authorizing. The operator remains fully responsible
for deciding whether to execute any command. PCAE advisory mode provides
information, not permission.

## 7. Advisory Mode Non-Role

Advisory mode explicitly does **not**:

1. **Replace human judgment.** Advisory output is informational. The operator
   decides. PCAE does not approve, authorize, or bless commands.

2. **Substitute for governance.** Advisory mode does not relax or bypass
   broker/shell gate rules. Hard blocks remain hard blocks in the advisory
   output, even though they are not enforced.

3. **Act as a shell wrapper.** Advisory mode is invoked explicitly by the
   operator (`pcae advisory check`). It does not wrap `bash`, `zsh`, or any
   other shell. It does not intercept commands typed at a prompt.

4. **Provide security guarantees.** Advisory mode tells the operator what PCAE
   *would* decide. It does not prevent the operator from running a blocked
   command directly in the shell. Enforcement requires later stages (88X+).

5. **Store or cache command history.** Advisory mode is stateless. Each
   evaluation is independent. No command history, audit trail, or persistent
   record is written by advisory mode itself.

6. **Become a permission system.** Advisory mode does not grant or deny
   permission. It only reports what the broker would decide. The operator
   always has final authority.

## 8. Relationship to Broker

Advisory mode consumes broker decisions as advisory input:

| Broker Decision | Advisory Interpretation |
|----------------|------------------------|
| `allow_preflight_only` | `would_allow_governed_preflight_only` — command would pass all checks and proceed to preflight authorization (not execution) |
| `requires_human_review` | `would_require_human_review` — command would need explicit human review before proceeding |
| `requires_more_evidence` | `would_require_more_evidence` — additional evidence items are missing |
| `blocked_by_shell_gate` | `would_block` — shell gate classifier found a hard-block condition |
| `blocked_by_scope` | `would_block_by_scope` — scope preflight denied the action |
| `blocked_by_task_contract` | `would_block_by_task_contract` — no active task contract for mutating action |
| `blocked_by_force_push` | `would_block_by_force_push` — force push is permanently blocked |
| `blocked_by_raw_git_push` | `would_block_by_raw_git_push` — raw `git push` without PCAE governance |
| `blocked_by_raw_git_commit` | `would_block_by_shell_gate` — raw `git commit` without PCAE governance (remapped) |
| `blocked_by_backend_policy` | `would_block` — backend invocation blocked by policy |
| `blocked_by_mutation_policy` | `would_block` — mutation blocked by policy |
| `blocked_by_commit_policy` | `would_block` — commit blocked by policy |
| `blocked_by_push_policy` | `would_block` — push blocked by policy |
| `blocked_by_lifecycle_state` | `would_block` — repository lifecycle state prohibits action |
| `blocked_by_risk` | `would_block` — risk register entry blocks action |
| `blocked_by_must_never_repeat` | `would_block` — action is on the must-never-repeat list |
| `blocked_by_failed_health` | `would_block_by_failed_health` — health check is failing |
| `blocked_by_failed_check` | `would_block_by_failed_check` — governance check is failing |
| `blocked_by_failed_doctor` | `would_block_by_failed_doctor` — doctor check is failing |
| `blocked_by_failed_tests` | `would_block` — tests are failing |
| `blocked_by_push_check` | `would_block_by_push_check` — push readiness check failed |
| `blocked_by_test_run_lock` | `would_block_by_test_run_lock` — another test run is active |
| `blocked_by_conflicting_evidence` | `would_block_by_conflicting_evidence` — contradictory evidence detected |
| `deny` | `would_deny` — command is unconditionally denied |
| `unknown` | `would_require_more_evidence` — broker could not determine decision |

Advisory mode must:

- Display the broker decision verbatim
- Display broker reason codes
- Display missing evidence items
- Map broker decision to advisory decision
- Never modify the broker decision
- Never suppress broker hard blocks
- Never convert `blocked_by_*` into `would_allow`

## 9. Relationship to Shell Gate

Advisory mode consumes shell gate evidence as advisory input:

| Shell Gate Decision | Advisory Presentation |
|---------------------|----------------------|
| `allow_read_only` | Command is read-only inspection; would be allowed |
| `allow_governed` | Command is a governed PCAE lifecycle command; would be allowed |
| `allow_test_execution` | Test execution would be allowed with active task |
| `requires_active_task` | Command would require an active task contract |
| `requires_preflight` | Command would require scope preflight |
| `requires_human_review` | Command would require human review |
| `requires_more_evidence` | Additional evidence would be required |
| `blocked_by_*` | Command would be blocked by shell gate classifier |
| `deny` | Command would be unconditionally denied |
| `unknown` | Command category could not be determined; would be blocked |

Advisory mode must display:

- Shell gate command category (`command_category`)
- Shell gate decision (`decision`)
- Shell gate reason codes
- Shell gate detected flags
- Whether the command was redacted (`command_text_redacted`)
- Whether secret access was detected (`secret_access_detected`)

Advisory mode must never:

- Modify shell gate evidence
- Reclassify commands
- Override shell gate decisions
- Execute classified command text

## 10. Relationship to Hard Blocks

Hard blocks are decision values in `BPE_HARD_BLOCK_DECISIONS` that represent
conditions under which a command must never execute. In advisory mode:

- **Hard blocks remain hard blocks.** Advisory mode does not soften, demote,
  or convert hard blocks into warnings or recommendations.

- **Advisory mode may display "would block".** The operator is informed that
  the command would be blocked if enforcement were active, but the block is
  not enforced.

- **Advisory mode must not recommend bypassing hard blocks.** The operator
  message for a hard-block advisory decision must state that the command
  would be blocked and must not suggest workarounds.

- **Human approval must not override hard blocks.** Even with
  `human_approval_present=True` and `human_review_present=True`, hard blocks
  remain blocking. This is already enforced in `_broker_decide` and must be
  reflected in advisory output.

- **Accepted risk must not override hard blocks.** Even with
  `accepted_risk_present=True`, hard blocks remain blocking. This is already
  enforced and must be reflected in advisory output.

### Hard Block Advisory Presentation

For any hard block, advisory output must include:

```json
{
  "hard_block_present": true,
  "hard_block_reason": "<broker_decision>",
  "would_block": true,
  "would_allow": false,
  "operator_message": "This command would be blocked by PCAE policy (<reason>). Advisory mode does not enforce this block. The operator may still run this command directly in the shell, but PCAE policy recommends against it.",
  "can_override": false
}
```

## 11. Relationship to Human Approval

Human approval (`human_approval_present=True`) and human review
(`human_review_present=True`) affect broker decisions as follows:

- `requires_human_review` + `human_review_present=True` → `allow_preflight_only`
  (if no other blocks apply)
- Hard block + `human_approval_present=True` → still hard blocked
  (human approval cannot override hard blocks)
- `secret_access` + `human_review_present=True` → `allow_preflight_only`
  (secret access requires review but is not a hard block)

Advisory mode must:

- Display whether human review is relevant for the current decision
- Display whether human approval is relevant for the current decision
- Indicate when human review/approval would change the outcome
- Never claim that human approval overrides hard blocks

## 12. Relationship to Accepted Risk

Accepted risk (`accepted_risk_present=True`) affects the broker as follows:

- Non-hard-block decisions: accepted risk does not change the decision
  (reserved for future enforcement stages)
- Hard-block decisions: accepted risk does not override hard blocks
  (permanent invariant from 88V §16)

Advisory mode must:

- Display whether accepted risk is relevant
- Never claim that accepted risk overrides hard blocks
- Document that accepted risk handling is defined in later enforcement stages

## 13. Relationship to Secret Redaction

All advisory output must apply the 88V.1 redaction rules:

1. **Secret-like VAR=val prefixes** detected as `secret_access` → command text
   replaced with `<redacted_secret_access_command>`.

2. **`env`/`printenv` commands** classified as `secret_access` → command text
   redacted.

3. **Secret file access** (`cat ~/.ssh/id_rsa`, etc.) → command text redacted.

4. **Secret access programs** (`security`, `gpg`, etc.) → command text redacted.

5. **`broker.requested_command`** redacted when `secret_access_detected`.

6. **Shell gate evidence `command_text`** redacted when `secret_access_detected`.

7. **All serialized JSON fields** must not contain raw secret command text.

Advisory mode must additionally:

- Set `redaction_applied: true` when any command text was redacted
- Set `redaction_reason` to indicate which detection triggered redaction
- Set `safe_to_display: true` only when all redactions have been applied
- Never ask the operator to paste secrets into advisory logs
- Never display raw secret-access command text in any output format

## 14. Relationship to Active Task State

Advisory mode behavior varies with active task presence:

### No Active Task (Idle Repository)

| Action Type | Advisory Decision |
|-------------|------------------|
| Read-only inspection | `would_allow_read_only` |
| Test execution (non-expensive) | `would_require_active_task` |
| Governed PCAE lifecycle | `would_allow_governed_preflight_only` (PCAE commands are always governed) |
| Mutating actions (write, commit, push) | `would_block_by_task_contract` |
| Backend invocation | `would_require_human_review` (even without task) |
| Secret access | `would_require_human_review` |
| Hard blocks (force push, etc.) | `would_block` (task-independent) |

### Active Task Present

| Action Type | Advisory Decision |
|-------------|------------------|
| Read-only inspection | `would_allow_read_only` |
| Test execution (non-expensive) | `would_allow` (preflight only) |
| Mutating actions (in scope) | `would_require_preflight` → scope preflight evaluation |
| Mutating actions (out of scope) | `would_block_by_scope` |
| Governed PCAE lifecycle | `would_allow_governed_preflight_only` |
| Hard blocks (force push, etc.) | `would_block` (task-independent) |

Advisory output must include:

- `active_task_detected: true/false`
- `task_contract_path` if detected
- Advisory decision reflecting task state impact

## 15. Relationship to PCAE Health/Check/Doctor/Push

Advisory mode must report governance status:

| Governance Check | Advisory Impact |
|-----------------|-----------------|
| Health: healthy | No blocking impact |
| Health: unhealthy | `would_block_by_failed_health` |
| Check: passed | No blocking impact |
| Check: failed | `would_block_by_failed_check` |
| Doctor: clean | No blocking impact |
| Doctor: failed | `would_block_by_failed_doctor` |
| Push check: passed | No blocking impact (push actions only) |
| Push check: failed | `would_block_by_push_check` (push actions only) |
| Test run: clear | No blocking impact |
| Test run: locked | `would_block_by_test_run_lock` |

Advisory output must include the current governance status so the operator
understands *why* a command would be blocked.

## 16. Advisory Output Model

The advisory output JSON envelope, to be implemented in 88X:

```json
{
  "schema_version": "0.1",
  "generated_at": "<ISO 8601 timestamp>",
  "repository_root": "<path>",
  "advisory_mode": true,
  "advisory_mode_version": "0.1",
  "requested_action": "<action>",
  "requested_command": "<command or redacted sentinel>",
  "requested_command_redacted": false,
  "requested_files": ["<file>", "..."],
  "broker_decision": "<BPE_DECISIONS value>",
  "shell_gate_decision": "<SGP_DECISIONS value or null>",
  "shell_gate_category": "<SGP_CATEGORIES value or null>",
  "advisory_decision": "<advisory decision value>",
  "advisory_recommendation": "<human-readable recommendation>",
  "would_allow_read_only": false,
  "would_allow_governed_preflight_only": false,
  "would_require_active_task": false,
  "would_require_preflight": false,
  "would_require_human_review": false,
  "would_require_more_evidence": false,
  "would_block": false,
  "would_deny": false,
  "hard_block_present": false,
  "hard_block_reason": null,
  "hard_block_source": null,
  "human_approval_relevant": false,
  "human_approval_would_change_outcome": false,
  "accepted_risk_relevant": false,
  "redaction_applied": false,
  "redaction_reason": null,
  "safe_to_display": true,
  "operator_message": "<contextual guidance>",
  "next_required_action": "<recommended operator step>",
  "authorization_granted": false,
  "execution_authorized": false,
  "command_executed": false,
  "enforcement_applied": false,
  "shell_intercepted": false,
  "performed_flags": {
    "authorization_granted": false,
    "execution_authorized": false,
    "command_executed": false,
    "repo_mutation_performed": false,
    "backend_invocation_performed": false,
    "prompt_sent": false,
    "capture_performed": false,
    "intake_performed": false,
    "adoption_performed": false,
    "commit_performed": false,
    "push_performed": false,
    "raw_git_push_performed": false,
    "force_push_performed": false,
    "storage_written": false
  },
  "evidence_sources": ["<source>", "..."],
  "missing_evidence": ["<item>", "..."],
  "warnings": ["<warning>", "..."],
  "errors": []
}
```

### Field Semantics

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Schema version for the advisory envelope |
| `advisory_mode` | bool | Always `true` for advisory output |
| `advisory_mode_version` | string | Version of the advisory mode specification |
| `requested_command` | string\|null | The command being evaluated, or redacted sentinel |
| `requested_command_redacted` | bool | Whether the command was redacted |
| `advisory_decision` | string | The would-* decision (see §17) |
| `advisory_recommendation` | string | Human-readable next-step guidance |
| `would_allow_read_only` | bool | Command would be allowed as read-only inspection |
| `would_allow_governed_preflight_only` | bool | Command would pass checks (preflight only, no execution) |
| `would_require_active_task` | bool | Command would require an active task contract |
| `would_require_preflight` | bool | Command would require scope preflight |
| `would_require_human_review` | bool | Command would require human review |
| `would_require_more_evidence` | bool | Additional evidence would be needed |
| `would_block` | bool | Command would be blocked by a hard block |
| `would_deny` | bool | Command would be unconditionally denied |
| `hard_block_present` | bool | A hard block condition exists |
| `hard_block_reason` | string\|null | Which hard block applies |
| `hard_block_source` | string\|null | Source of the hard block (shell_gate, broker, scope) |
| `human_approval_relevant` | bool | Whether human approval would affect the decision |
| `human_approval_would_change_outcome` | bool | Whether providing human approval would change the decision |
| `accepted_risk_relevant` | bool | Whether accepted risk is relevant to this decision |
| `redaction_applied` | bool | Whether command text was redacted |
| `redaction_reason` | string\|null | Why redaction was applied |
| `safe_to_display` | bool | Whether output is safe to display (no raw secrets) |
| `operator_message` | string | Contextual guidance for the operator |
| `next_required_action` | string | Recommended next action for the operator |
| `performed_flags` | object | All flags unconditionally `false` |
| `evidence_sources` | array | List of evidence sources consulted |
| `missing_evidence` | array | Evidence items that are missing |

## 17. Advisory Decision Vocabulary

The advisory decision vocabulary maps broker decisions to operator-facing
would-* decisions:

| Advisory Decision | Meaning | Broker/SG Source |
|-------------------|---------|-----------------|
| `would_allow_read_only` | Command is read-only; would be allowed without restrictions | `allow_read_only` from SG |
| `would_allow_governed_preflight_only` | Command would pass all checks but execution is not authorized (preflight only) | `allow_preflight_only` from broker |
| `would_require_active_task` | Command requires an active task contract before proceeding | `requires_active_task` from SG, `blocked_by_task_contract` from broker |
| `would_require_preflight` | Command requires scope preflight evaluation | `requires_preflight` from SG |
| `would_require_human_review` | Command requires explicit human review | `requires_human_review` from broker/SG |
| `would_require_more_evidence` | Additional evidence items are missing | `requires_more_evidence` from broker |
| `would_block_by_scope` | Command would be blocked: out of scope for active task | `blocked_by_scope` from broker |
| `would_block_by_task_contract` | Command would be blocked: no active task contract | `blocked_by_task_contract` from broker |
| `would_block_by_raw_git_push` | Command would be blocked: raw git push | `blocked_by_raw_git_push` from broker |
| `would_block_by_force_push` | Command would be blocked: force push | `blocked_by_force_push` from broker |
| `would_block_by_shell_gate` | Command would be blocked: shell gate classifier | `blocked_by_shell_gate` from broker |
| `would_block_by_test_run_lock` | Command would be blocked: test run in progress | `blocked_by_test_run_lock` from broker |
| `would_block_by_failed_health` | Command would be blocked: health check failing | `blocked_by_failed_health` from broker |
| `would_block_by_failed_check` | Command would be blocked: governance check failing | `blocked_by_failed_check` from broker |
| `would_block_by_failed_doctor` | Command would be blocked: doctor check failing | `blocked_by_failed_doctor` from broker |
| `would_block_by_push_check` | Command would be blocked: push readiness check failing | `blocked_by_push_check` from broker |
| `would_block_by_conflicting_evidence` | Command would be blocked: contradictory evidence | `blocked_by_conflicting_evidence` from broker |
| `would_deny` | Command would be unconditionally denied | `deny` from SG/broker |
| `unknown` | Decision could not be determined | `unknown` from broker |

Only one advisory decision is active per evaluation. The most restrictive
(most blocking) decision takes priority.

## 18. Human-Readable Output Guidance

When advisory mode is invoked without `--json`, it should produce a compact
human-readable summary:

```
PCAE Advisory Mode — Non-Authorizing

Command:      <redacted or safe command text>
Action:       <requested_action>
Files:        <requested_files>

Shell Gate:   <command_category> → <sg_decision>
Broker:       <broker_decision>
Advisory:     <advisory_decision>

Would allow:  no
Would block:  yes — <hard_block_reason>

Hard block:   <hard_block_present>
Override:     not possible (hard blocks cannot be overridden)

Redaction:    <applied/not applied>
Safe to show: yes

Operator:     This command would be blocked by PCAE policy.
              Advisory mode does not enforce this block.
              You may still run this command directly in your shell.

Next action:  Resolve the blocking condition before proceeding.
              See: pcae advisory explain <decision>

Authorization:   not granted
Execution:       not authorized
Enforcement:     not applied
```

The human-readable output must always end with:

```
⚠️  Advisory mode is non-authorizing. PCAE does not execute, block,
   or intercept commands. Operator retains full authority.
```

## 19. JSON Output Guidance

When invoked with `--json`, advisory mode should produce the envelope
defined in §16. The JSON output must:

1. **Always set** `advisory_mode: true`
2. **Always set** `authorization_granted: false`
3. **Always set** `execution_authorized: false`
4. **Always set** `command_executed: false`
5. **Always set** `enforcement_applied: false`
6. **Always set** `shell_intercepted: false`
7. **Always include** all `performed_flags` as `false`
8. **Always include** `safe_to_display`
9. **Always redact** secret-access commands per 88V.1 rules
10. **Always include** `operator_message` and `next_required_action`

The JSON output is designed to be consumed by:
- CI/CD pipeline governance checks
- Pre-commit hooks
- Editor integrations
- Operator dashboards
- Audit/logging systems (future)

## 20. Operator Workflow

The designed operator workflow for advisory mode:

```
┌─────────────────────────────────────────────────────┐
│  1. OPERATOR PROPOSES COMMAND/ACTION                │
│     Operator types: pcae advisory check --command   │
│     "git push origin main"                          │
├─────────────────────────────────────────────────────┤
│  2. ADVISORY MODE EVALUATES                         │
│     - Shell gate classifies the command             │
│     - Broker aggregates evidence and decides        │
│     - Advisory mode maps to would-* decision        │
│     - Redaction applied per 88V.1 rules             │
├─────────────────────────────────────────────────────┤
│  3. ADVISORY MODE PRINTS SAFE SUMMARY               │
│     - Command category and decision                 │
│     - Would-allow / would-block / would-require     │
│     - Hard block status and reason                  │
│     - Redaction status                              │
│     - Operator message and next action              │
├─────────────────────────────────────────────────────┤
│  4. OPERATOR READS ADVISORY OUTPUT                  │
│     Operator sees: "This command would be blocked   │
│     by PCAE policy (blocked_by_raw_git_push)."      │
├─────────────────────────────────────────────────────┤
│  5. OPERATOR DECIDES MANUALLY                       │
│     Option A: Use governed alternative              │
│       pcae push                                     │
│     Option B: Run command directly (at own risk)    │
│       git push origin main                          │
│     Option C: Investigate and resolve block         │
│       pcae advisory explain blocked_by_raw_git_push │
├─────────────────────────────────────────────────────┤
│  6. PCAE DOES NOT EXECUTE                           │
│     Advisory mode exits. No command was run.        │
│     No shell was intercepted. No config changed.    │
└─────────────────────────────────────────────────────┘
```

Key workflow properties:

- **Operator initiates.** Advisory mode is never automatic. The operator must
  explicitly invoke it.

- **Operator decides.** Advisory output is informational. PCAE never makes
  the decision for the operator.

- **No side effects.** Advisory mode does not modify files, write caches,
  change shell state, or leave persistent records (beyond what the operator's
  shell history already records).

- **Repeatable.** The operator can run advisory checks as many times as
  desired. Each invocation is independent and stateless.

## 21. Audit/Logging Boundary

Advisory mode in its initial prototype (88X) will be **stateless**: it does
not write audit records, logs, or persistent state. Each invocation is
independent.

When audit/logging is introduced in later phases:

- Advisory evaluations **may** be logged to `.pcae/advisory/` for operator
  review
- Logs **must** store only redacted command text (per 88V.1 rules)
- Logs **must** record the advisory decision, timestamp, and repository state
- Logs **must not** store raw secret-access command text
- Logs **must not** store execution results (nothing was executed)
- Logs **must** be human-readable and machine-parseable
- Log retention and rotation **should** follow PCAE governance policy

Advisory mode **must never**:

- Log to external services
- Send telemetry
- Phone home
- Write outside `.pcae/`

## 22. Dry-Run-Only Guarantees

Advisory mode operates entirely within PCAE's read-only classifiers:

1. **No subprocess execution.** Advisory mode calls `_classify_command()` and
   `build_permission_broker()` — both pure Python functions that perform
   string matching and data aggregation. No `subprocess.run()` for command
   execution.

2. **No filesystem mutation.** Advisory mode reads task contracts, governance
   state, and policy configuration. It does not write files.

3. **No shell interaction.** Advisory mode does not spawn a shell, attach to
   a terminal, or intercept keystrokes.

4. **No network access.** Advisory mode does not make HTTP requests, open
   sockets, or communicate with remote services.

5. **No backend invocation.** Advisory mode does not call Claude, Codex,
   DeepSeek, or any other AI backend.

6. **Deterministic output.** Given the same repository state and input,
   advisory mode produces the same output. There is no randomness, no model
   inference, no non-deterministic behavior.

## 23. No-Execution/No-Interception Guarantees

These guarantees are invariant across all advisory mode versions:

| Guarantee | Enforcement |
|-----------|-------------|
| No command execution | Advisory mode never calls `subprocess.run()` or `os.system()` with user-provided command text |
| No shell interception | Advisory mode does not wrap `bash`, `zsh`, or any shell |
| No shell wrapper installation | Advisory mode does not write to `.bashrc`, `.zshrc`, `.profile`, or any shell config |
| No shell configuration modification | Advisory mode does not modify `PATH`, aliases, functions, or environment variables |
| No execution authorization | `execution_authorized` is always `false` |
| No authorization grant | `authorization_granted` is always `false` |
| No enforcement | `enforcement_applied` is always `false` |
| No performed flags | All 14 performed flags are unconditionally `false` |

These guarantees are tested by asserting the invariant fields in every
advisory output, both JSON and human-readable.

## 24. Disable/Rollback Expectations

Advisory mode is designed to be **safe to disable** at any time:

1. **No persistent state.** Since advisory mode is stateless, disabling it
   means simply not invoking the command. No cleanup is needed.

2. **No shell modification.** Since advisory mode does not install wrappers
   or modify shell configuration, there is nothing to roll back.

3. **No dependency.** Other PCAE commands (health, check, broker, shell gate)
   continue to function independently of advisory mode.

4. **Graceful degradation.** If the advisory prototype is removed or disabled,
   the broker and shell gate continue to work as before. Advisory mode is a
   consumer of their output, not a dependency.

5. **Future disable command.** When advisory mode is implemented, a disable
   mechanism should be provided:
   ```
   pcae advisory disable  # Remove advisory CLI (future)
   ```
   This is a future consideration, not implemented in 88W or 88X.

## 25. Future CLI Sketch

The following CLI surface is suggested but **not implemented** in 88W:

### Primary Command

```
pcae advisory check --command "<command>" [--json]
```

Evaluates a proposed shell command through advisory mode and prints the
advisory decision.

Options:
- `--command`, `-c`: The command text to evaluate
- `--json`: Print machine-readable JSON output
- `--action`, `-a`: Override the requested action (default: derived from command)
- `--files`, `-f`: Explicit file list for scope preflight

### Explain Command

```
pcae advisory explain --decision <decision>
```

Prints detailed human-readable explanation of an advisory decision, including:
- What the decision means
- Why it was produced
- What the operator can do next
- Whether human approval or accepted risk would change the outcome
- Whether the decision represents a hard block

### Status Command

```
pcae advisory status
```

Prints the current advisory mode status:
- Advisory mode version
- Whether advisory mode is available
- Current repository governance status
- Whether advisory checks are expected to pass

### Implementation Note

These CLI commands are design sketches. They must not be created in 88W.
Implementation begins in 88X (Advisory Mode Prototype).

## 26. Test Requirements for Advisory Prototype

Before 88X implementation begins, the following test infrastructure must
be in place:

### Unit Tests

1. **Advisory decision mapping**: Every broker decision maps to exactly one
   advisory decision. Test all 25 BPE_DECISIONS values.

2. **Would-* flag consistency**: Exactly one would-* flag is `true` per
   evaluation. Test parametrized across command categories.

3. **Performed flags invariant**: All 14 performed flags are `false` for
   every advisory output. Test across secret, mutation, and read-only commands.

4. **Authorization invariants**: `authorization_granted`, `execution_authorized`,
   `command_executed`, `enforcement_applied`, `shell_intercepted` are always
   `false`.

5. **Redaction propagation**: Secret-access commands produce redacted output
   in all advisory fields. Test GAP-1/GAP-2/GAP-3 scenarios.

6. **Hard block preservation**: Hard blocks are never converted to non-blocking
   advisory decisions. Test all 18 BPE_HARD_BLOCK_DECISIONS values.

7. **Human approval limits**: Human approval does not override hard blocks in
   advisory output.

8. **Accepted risk limits**: Accepted risk does not override hard blocks in
   advisory output.

### Integration Tests

9. **CLI exit code**: `pcae advisory check` exits 0 for advisory evaluation
   (advisory mode never fails; it only reports).

10. **CLI JSON validity**: `--json` output is valid JSON matching the schema.

11. **CLI human-readable output**: Non-JSON output contains required sections
    (Shell Gate, Broker, Advisory, Operator message, non-authorizing notice).

12. **No side effects**: Running advisory check does not modify files, write
    caches, or change repository state.

### Fast-Green Tests

13. All advisory tests must be marked `fast_green` (no subprocess execution,
    no file I/O beyond reading governance state).

### Test File

14. New test file: `tests/test_advisory_mode.py` (created in 88X, not 88W).

## 27. Readiness Checklist Before Advisory Prototype

Before 88X (Advisory Mode Prototype) can begin, confirm:

- [x] 88W design document complete and reviewed
- [x] Advisory mode terminology defined
- [x] Advisory output model specified
- [x] Advisory decision vocabulary defined
- [x] Operator workflow documented
- [x] No-execution/no-interception guarantees specified
- [x] Test requirements documented
- [x] Broker + shell gate infrastructure stable (88V.1 baseline)
- [x] Secret redaction rules in place (88V.1)
- [x] Deny mapping consistent (88V.1)
- [x] All performed/authorization flags unconditionally `False`
- [x] Fast-green: 2,709 passed
- [x] Full suite: 8,695 passed
- [ ] Phase 88X task contract created (future)
- [ ] Advisory prototype implemented (future, 88X)

## 28. Remaining Limitations

1. **Advisory mode is not a shell wrapper.** Operators must explicitly invoke
   `pcae advisory check`. Commands typed directly in the shell are not
   evaluated. Full shell integration requires Stages 3–6 (out of scope).

2. **Advisory mode is stateless.** No history, no audit trail, no persistent
   records. Operators who want to review past advisory evaluations must rely
   on their shell history.

3. **Advisory mode does not prevent execution.** The operator can always run
   a blocked command directly in the shell. Advisory mode informs but does
   not enforce.

4. **No real-time feedback.** Advisory mode is a CLI command, not a continuous
   monitoring daemon. It evaluates one command at a time, on demand.

5. **No contextual learning.** Advisory mode does not adapt based on past
   operator decisions. Each evaluation is independent.

6. **Limited to classified commands.** Advisory mode can only evaluate
   commands that the shell gate classifier recognizes. Truly novel or
   obfuscated commands may return `unknown`.

## 29. Recommended Next Phase

**88X — Advisory Mode Prototype**

Implement the advisory mode CLI as designed in this document:

- `pcae advisory check --command "<cmd>" [--json]`
- `pcae advisory explain --decision <decision>`
- `pcae advisory status`

The prototype must:
- Wrap existing broker + shell gate infrastructure
- Map broker decisions to advisory decisions
- Apply 88V.1 redaction rules
- Preserve all performed/authorization invariants
- Include comprehensive fast-green tests
- Never execute, intercept, block, or authorize

## 30. Summary

Phase 88W defines PCAE's advisory enforcement readiness layer. Key outcomes:

1. **Advisory mode is read-only and non-authorizing.** It tells the operator
   what *would* happen, not what *must* happen.

2. **Advisory mode builds on existing infrastructure.** It consumes broker
   and shell gate output; it does not replace or modify them.

3. **Hard blocks remain hard blocks.** Advisory mode informs about blocks
   but does not enforce or soften them.

4. **Human authority is preserved.** The operator always decides. PCAE
   advisory mode provides information, not permission.

5. **Secret redaction is maintained.** All 88V.1 redaction rules apply to
   advisory output.

6. **No implementation in 88W.** All design, no code. Prototype begins in
   88X.

The advisory mode design is the first step beyond Stage 0 (Read-Only
Classification) toward Stage 1 (Advisory) of the enforcement staging
roadmap defined in 88V.
