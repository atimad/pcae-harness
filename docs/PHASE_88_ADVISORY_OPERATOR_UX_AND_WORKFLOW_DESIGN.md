# Phase 88Z — Advisory Operator UX and Workflow Design

```
phase_name    = phase_88z_advisory_operator_ux_and_workflow_design
phase_version = 1.0
phase_status  = completed
implementation_status = design_only
recommended_next_phase = 89A_advisory_mode_hardening_false_positive_repair
```

## 1. Purpose

Define the operator-facing UX for PCAE advisory mode: how human operators read, trust, triage, explain, and act on advisory decisions in the current environment where advisory mode is the only visible enforcement layer — no dry-run blocking, no enforcement, no shell interception exists yet.

This document is a **design artifact**. No implementation is performed in 88Z. It serves as the UX specification for future advisory CLI hardening (89A+) and eventual enforcement stages.

## 2. Scope

In scope (design only):

- Operator personas and workflows for advisory mode interaction
- UX principles governing all advisory output
- Human-readable and JSON output design recommendations
- Severity and recommendation language models
- Messaging design for hard blocks, human review, missing evidence, secret redaction, and advisory-only status
- False-positive and false-negative handling workflows
- Operator next-action workflow from advisory output to governed PCAE commands
- Safety invariants for all advisory UX presentation
- Relationship to dry-run blocking simulation and future enforcement
- Future implementation plan for 89A and beyond

Out of scope:

- Implementing advisory UX commands
- Changing existing `pcae advisory check/explain/status` behavior
- Implementing enforcement, blocking, or shell interception
- Installing shell wrappers or modifying shell configuration
- Executing command text, invoking backends, sending prompts, capturing output
- Granting authorization
- Writing persistent advisory/broker/shell-gate state
- Adding persistent cache
- Phase 89A task contract or any phase beyond 88Z

## 3. Non-Goals

88Z must not and does not:

- Implement any advisory UX command changes
- Change existing advisory command behavior
- Implement enforcement or blocking behavior
- Implement shell interception or wrappers
- Modify shell configuration
- Execute requested command text
- Invoke backends
- Send prompts or capture outputs
- Perform intake or adoption
- Grant real authorization
- Persist advisory/broker/shell-gate state
- Add persistent cache

## 4. Starting Point

### 4.1 Advisory Mode Prototype (88X)

Three CLI commands implemented and tested:

```
pcae advisory check --command "<cmd>" [--json] [--action ACTION]
    [--health-passed] [--check-passed]
    [--human-review-present] [--human-approval-present]
    [--accepted-risk-present]

pcae advisory explain --decision <decision> [--json]

pcae advisory status [--json]
```

105 fast-green tests in `tests/test_advisory_mode.py`.

### 4.2 Advisory Test Matrix (88Y)

294 total advisory tests across 10 command categories. CLI JSON stability, human-readable output, decision vocabulary (all 19 values), broker/shell-gate consistency, and false-positive/false-negative review completed.

### 4.3 Known Advisory Findings (from 88Y)

**False positives:**
| Finding | Description |
|---------|-------------|
| `bash` blocked as unknown | Conservative FP — bash not in known-programs list |
| `sh -c 'cmd'` blocked as unknown | sh not in known-programs list |
| `env python` classified as secret_access | 88V.1 over-classifies env/printenv |

**False negative:**
| Finding | Description |
|---------|-------------|
| `env\|grep TOKEN` (no spaces) not redacted | shlex.split produces single token; pipe not detected |

### 4.4 Current Advisory UX Baseline

The existing human-readable output (from `src/pcae/commands/advisory.py` `_print_human_readable`):

```
PCAE Advisory Mode — Non-Authorizing

  Command:       <cmd> [(redacted)]
  Action:        <action>
  Files:         <files>

  Shell Gate:    <category> → <decision>
  Broker:        <broker_decision>
  Advisory:      <advisory_decision>

  Would block:   yes — <reason>
  Hard block:    true/false
  Override:      not possible (hard blocks cannot be overridden)

  Redaction:     applied — <reason>
  Safe to show:  yes

  Operator:      <operator_message>
  Next action:   <next_required_action>

  Authorization: not granted
  Execution:     not authorized
  Enforcement:   not applied

  Advisory mode is non-authorizing. PCAE does not execute, block,
  or intercept commands. Operator retains full authority.
```

The existing JSON envelope (from `build_advisory()` in `src/pcae/core/advisory.py`) contains all fields defined in the 88W advisory output model.

### 4.5 Performance Context

After 88Y.1–88Y.5 performance series:
- Single `build_gate_dry_run()`: ~3.22s (was 20.86s, -85%)
- Advisory check includes full gate dry-run evidence
- Fast-green: ~3,003 tests / ~25s
- Full suite: ~9,068 tests / ~17:39

## 5. Operator Personas

### 5.1 Persona Definitions

| Persona | Role | Primary Advisory Use | Technical Level |
|---------|------|---------------------|-----------------|
| **Task Developer** | Engineer working on a PCAE-governed task | Checks commands before running them; verifies scope compliance | High |
| **Reviewer** | Human reviewer evaluating another operator's proposed actions | Reviews advisory decisions for correctness, false positives, and policy alignment | High |
| **Release Operator** | Operator performing governed commits and pushes | Verifies push readiness before committing; checks that PCAE governance is satisfied | Medium-High |
| **Oncall/Diagnostician** | Operator debugging a failing pipeline or governance state | Uses advisory check/explain/status to understand why commands are blocked or gated | Medium-High |
| **New PCAE User** | Operator new to PCAE governance | Learns PCAE rules through advisory feedback; uses explain to understand decisions | Low-Medium |
| **CI/CD Pipeline** | Automated system consuming JSON advisory output | Parses JSON advisory output for pre-commit hooks, CI governance checks | N/A (machine) |

### 5.2 Persona Needs

| Persona | Needs from Advisory UX |
|---------|----------------------|
| Task Developer | Clear scope boundaries; "what would happen" before committing; fast check loop |
| Reviewer | Clear decision rationale; evidence chain visibility; false-positive flagging path |
| Release Operator | Binary push-readiness signal; blocking condition explanation; governed alternative suggestion |
| Oncall/Diagnostician | Detailed decision trace; governance state visibility; explain for every decision value |
| New PCAE User | Jargon-free explanations; clear next steps; educational operator messages |
| CI/CD Pipeline | Stable JSON schema; machine-parseable decision values; no human-readable-only fields |

## 6. Operator Workflow

### 6.1 Primary Workflow: Command Evaluation

```
┌─────────────────────────────────────────────────────────┐
│ 1. OPERATOR HAS A COMMAND THEY WANT TO RUN              │
│    Example: git push origin main                        │
├─────────────────────────────────────────────────────────┤
│ 2. OPERATOR RUNS ADVISORY CHECK                         │
│    pcae advisory check --command "git push origin main" │
├─────────────────────────────────────────────────────────┤
│ 3. ADVISORY MODE EVALUATES (read-only, no execution)     │
│    - Shell gate classifies command                      │
│    - Broker aggregates evidence and decides             │
│    - Advisory mapper converts to would-* decision       │
│    - Redaction applied per 88V.1 rules                  │
├─────────────────────────────────────────────────────────┤
│ 4. ADVISORY OUTPUT IS PRINTED                           │
│    Human-readable or JSON per --json flag               │
├─────────────────────────────────────────────────────────┤
│ 5. OPERATOR READS AND UNDERSTANDS                       │
│    - What the command category is                       │
│    - What the advisory decision is                      │
│    - Whether it would block, require review, or allow   │
│    - Why the decision was made                          │
│    - What the operator should do next                   │
├─────────────────────────────────────────────────────────┤
│ 6. OPERATOR ACTS                                        │
│    Path A: Use governed alternative (pcae push)         │
│    Path B: Resolve blocking condition                   │
│    Path C: Request human review                         │
│    Path D: Escalate false positive                      │
│    Path E: Run command directly (at own risk)           │
├─────────────────────────────────────────────────────────┤
│ 7. PCAE DOES NOT EXECUTE                                │
│    Advisory mode exits. No command was run.             │
│    No shell was intercepted. No config changed.         │
│    No authorization was granted.                        │
└─────────────────────────────────────────────────────────┘
```

### 6.2 Secondary Workflow: Decision Investigation

```
Operator sees an advisory decision they don't understand
  → pcae advisory explain --decision <decision>
  → Reads explanation (summary, meaning, would_block, can_override, next_step)
  → Understands what to do next
```

### 6.3 Tertiary Workflow: Status Check

```
Operator wants to verify advisory mode is available
  → pcae advisory status
  → Confirms: available, version, phase, invariants
```

### 6.4 Workflow Properties

- **Operator initiates.** Advisory mode is never automatic. The operator explicitly invokes it.
- **Operator decides.** Advisory output is informational. PCAE never makes the decision for the operator.
- **No side effects.** Advisory mode does not modify files, write caches, change shell state, or leave persistent records.
- **Repeatable.** The operator can run advisory checks as many times as desired. Each invocation is independent and stateless.
- **Governed path always suggested.** When a command would be blocked, the advisory output should always suggest the governed PCAE alternative.

## 7. UX Principles

### 7.1 Core Principles

| # | Principle | Meaning |
|---|-----------|---------|
| **P1** | **Non-authorizing clarity** | Every advisory output must make unequivocally clear that nothing was executed, no authorization was granted, and the operator retains full authority. |
| **P2** | **Conservative transparency** | When in doubt, advisory mode errs on the side of caution (would-block rather than would-allow). The operator must know this is a conservative evaluation. |
| **P3** | **Decision traceability** | The operator must be able to trace from advisory decision → broker decision → shell gate decision → evidence. The reasoning chain must be visible. |
| **P4** | **Actionable next steps** | Every advisory output must include a concrete next action the operator can take. "Something is wrong" is insufficient; the operator needs to know what to do. |
| **P5** | **Governed alternative first** | When a command would be blocked, the primary recommendation should be the governed PCAE alternative, not "run it anyway." |
| **P6** | **Severity-appropriate language** | Hard blocks must not be phrased as suggestions. Review requirements must not be phrased as blocks. The language must match the severity. |
| **P7** | **Redaction visibility** | The operator must know when redaction occurred, without revealing what was redacted. The fact of redaction must not be hidden. |
| **P8** | **JSON/human parity** | Every piece of information available in JSON output must be available in human-readable output, and vice versa. No hidden fields in either format. |
| **P9** | **New-user accessible** | Advisory output should be understandable by someone new to PCAE. Jargon should be explained or linked to `pcae advisory explain`. |
| **P10** | **Machine-stable** | JSON output schema must be stable and versioned. Machine consumers (CI/CD) must be able to rely on field names, types, and decision values. |

### 7.2 Anti-Principles

| # | Anti-Principle | Why Avoided |
|---|---------------|-------------|
| **A1** | "Permission granted" language | Advisory mode never grants permission. Words like "approved", "authorized", "allowed" must be qualified as would-* hypotheticals. |
| **A2** | Silent redaction | Operators must know when secrets were redacted. Hidden redaction erodes trust. |
| **A3** | Sugary hard blocks | Hard blocks must not be softened. "We recommend against" is wrong for a hard block — it should be "would block." |
| **A4** | Overwhelming detail by default | Default human-readable output should be scannable. Deep detail belongs in `--verbose` or `advisory explain`. |
| **A5** | Divergent JSON/human content | Both formats must convey the same decisions, same severity, same next actions. JSON must not have hidden fields the human can't see. |

## 8. Advisory Decision Vocabulary — Presentation

### 8.1 Decision Grouping for UX

For presentation purposes, the 19 advisory decisions are grouped into UX categories:

| UX Category | Advisory Decisions | UX Treatment |
|-------------|-------------------|--------------|
| **Would Allow** | `would_allow_read_only`, `would_allow_governed_preflight_only` | Safe/green presentation. Command would pass checks. Still no execution authorization. |
| **Would Require** | `would_require_active_task`, `would_require_preflight`, `would_require_human_review`, `would_require_more_evidence` | Yellow/caution presentation. Command needs something before it can proceed. Not blocked — gated. |
| **Would Block** | `would_block_by_scope`, `would_block_by_task_contract`, `would_block_by_raw_git_push`, `would_block_by_force_push`, `would_block_by_shell_gate`, `would_block_by_test_run_lock`, `would_block_by_failed_health`, `would_block_by_failed_check`, `would_block_by_failed_doctor`, `would_block_by_push_check`, `would_block_by_conflicting_evidence` | Red/block presentation. Command has a hard block. Not enforced in advisory mode, but would be blocked if enforcement were active. |
| **Would Deny** | `would_deny` | Strongest red presentation. Command is unconditionally denied. No workaround. |
| **Unknown** | `unknown` | Gray/unknown presentation. Decision could not be determined. More evidence needed. |

### 8.2 Decision Presentation Attributes

Each advisory decision should be presented with:

| Attribute | Description |
|-----------|-------------|
| **Decision value** | The machine-readable `would_*` string |
| **UX category** | Allow / Require / Block / Deny / Unknown |
| **Summary** | One-line human description |
| **Would block** | Boolean — would this decision block the command? |
| **Would deny** | Boolean — is this an unconditional deny? |
| **Hard block** | Boolean — is a hard block condition present? |
| **Can human override** | Whether human review/approval would change the outcome |
| **Can accepted-risk override** | Whether accepted risk would change the outcome |
| **Governed alternative** | The PCAE-governed command that achieves the same goal |
| **Operator action** | Concrete next step |

## 9. Severity Model

### 9.1 Severity Levels

| Severity | Label | Visual Indicator | When Used |
|----------|-------|-----------------|-----------|
| `info` | ℹ️ INFO | Neutral/dim | Read-only commands that would be allowed; governed PCAE commands |
| `caution` | ⚠️ CAUTION | Yellow | Commands requiring active task, preflight, or more evidence |
| `review_required` | 👁️ REVIEW REQUIRED | Orange | Commands requiring human review; secret-access commands |
| `blocked` | 🚫 WOULD BLOCK | Red | Hard blocks — would block if enforcement were active |
| `unknown` | ❓ UNKNOWN | Gray | Decision could not be determined |

### 9.2 Severity Assignment Rules

| Advisory Decision | Severity |
|-------------------|----------|
| `would_allow_read_only` | `info` |
| `would_allow_governed_preflight_only` | `info` |
| `would_require_active_task` | `caution` |
| `would_require_preflight` | `caution` |
| `would_require_more_evidence` | `caution` |
| `would_require_human_review` | `review_required` |
| `would_block_by_*` | `blocked` |
| `would_deny` | `blocked` |
| `unknown` | `unknown` |

### 9.3 Severity Escalation Rules

1. **Hard blocks always escalate to `blocked`** — even if other evidence is missing or review is required. Hard block takes precedence.
2. **Deny escalates to highest severity** — `would_deny` is the strongest signal and must be presented as the most severe.
3. **Redaction does not escalate severity** — secret redaction is a safety feature, not a severity signal. Redaction status is displayed separately.
4. **Missing evidence escalates from `info` to `caution`** — if a command would be allowed but evidence is missing, the severity should reflect the gap.

## 10. Recommendation Model

### 10.1 Operator Action Vocabulary

| Action | Meaning | When Recommended |
|--------|---------|-----------------|
| `proceed_at_discretion` | Operator may proceed; no PCAE concerns | Read-only commands, governed PCAE commands |
| `create_or_select_task` | Create or select an active task contract | No active task, or task required for action |
| `run_preflight` | Run scope preflight for the action | Command requires scope verification |
| `provide_missing_evidence` | Provide the listed evidence items | `would_require_more_evidence` |
| `request_human_review` | Obtain human review for the action | `would_require_human_review` |
| `resolve_blocking_condition` | Fix the listed blocking condition | Any `would_block_by_*` |
| `use_governed_alternative` | Use the PCAE-governed command instead | Raw git push, raw git commit, force push |
| `run_pcae_health` | Run `pcae health` to diagnose | `would_block_by_failed_health` |
| `run_pcae_check` | Run `pcae check` to diagnose | `would_block_by_failed_check` |
| `run_pcae_doctor` | Run `pcae doctor` to diagnose | `would_block_by_failed_doctor` |
| `wait_for_test_run` | Wait for active test run to complete | `would_block_by_test_run_lock` |
| `do_not_execute` | Do not run this command | `would_deny`, permanent hard blocks |
| `escalate_false_positive` | Report a potential false positive | Operator believes the block is incorrect |
| `report_false_negative` | Report a potential false negative | Operator believes a command should have been blocked but wasn't |
| `inspect_redaction` | Review redaction to verify no secrets leaked | Redaction was applied; operator should verify |
| `use_governed_commit` | Use `pcae commit implementation` | Raw git commit blocked |
| `use_governed_push` | Use `pcae push` | Raw git push blocked |

### 10.2 Recommendation Priority

When multiple conditions apply, recommendations follow this priority:

1. **`do_not_execute`** — if `would_deny`, this takes precedence over all others
2. **`resolve_blocking_condition`** — if any `would_block_by_*`, address the block first
3. **`use_governed_alternative`** — if a governed PCAE command exists for the blocked action
4. **`request_human_review`** — if human review is required
5. **`run_preflight`** / **`create_or_select_task`** — if preflight or task is needed
6. **`provide_missing_evidence`** — if evidence is missing
7. **`proceed_at_discretion`** — if no concerns

## 11. Human-Readable Output Design

### 11.1 Design Goals

- Scannable in <10 seconds for experienced operators
- Self-explanatory for new operators (with `advisory explain` as fallback)
- Severity-indicated with clear visual hierarchy
- Never buries the advisory decision or next action
- Always ends with the non-authorizing notice

### 11.2 Recommended Human-Readable Layout

```
╔══════════════════════════════════════════════════════════════╗
║  PCAE Advisory Mode — ℹ️ INFO                                ║
║  Advisory only. No command was executed.                     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Command:     git status                                     ║
║  Action:      read                                           ║
║                                                              ║
║  ┌─ Classification ──────────────────────────────────────┐   ║
║  │ Shell Gate   read_only_inspection → allow_read_only   │   ║
║  │ Broker       allow_preflight_only                     │   ║
║  └───────────────────────────────────────────────────────┘   ║
║                                                              ║
║  ┌─ Advisory Decision ───────────────────────────────────┐   ║
║  │ would_allow_read_only                                 │   ║
║  │ This command is read-only inspection.                 │   ║
║  │ It would be allowed without restrictions.             │   ║
║  └───────────────────────────────────────────────────────┘   ║
║                                                              ║
║  Would block:   no                                           ║
║  Would deny:    no                                           ║
║  Hard block:    none                                         ║
║  Redaction:     not applied                                  ║
║                                                              ║
║  ┌─ Next Action ─────────────────────────────────────────┐   ║
║  │ Proceed at your discretion.                            │   ║
║  │ Advisory mode is non-authorizing. You retain           │   ║
║  │ full authority over command execution.                 │   ║
║  └───────────────────────────────────────────────────────┘   ║
║                                                              ║
║  Authorization: not granted  Execution: not authorized       ║
║  Enforcement:   not applied  Interception: not applied       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### 11.3 Severity Header Variation

The severity banner adapts to the advisory decision:

| Severity | Header |
|----------|--------|
| `info` | `PCAE Advisory Mode — ℹ️ INFO` |
| `caution` | `PCAE Advisory Mode — ⚠️ CAUTION` |
| `review_required` | `PCAE Advisory Mode — 👁️ REVIEW REQUIRED` |
| `blocked` | `PCAE Advisory Mode — 🚫 WOULD BLOCK` |
| `unknown` | `PCAE Advisory Mode — ❓ UNKNOWN` |

### 11.4 Block/Hard-Block Section

For blocked decisions, replace the "Would block" line with an expanded block section:

```
  ┌─ Block Detail ─────────────────────────────────────────┐
  │ WOULD BLOCK: raw_git_push                              │
  │                                                        │
  │ This is a HARD BLOCK. It cannot be overridden by       │
  │ human approval or accepted risk.                       │
  │                                                        │
  │ Why: PCAE policy requires all pushes to use the        │
  │ governed pcae push command, which runs pre-push        │
  │ validation (health, check, doctor, test-run lock).     │
  │                                                        │
  │ Governed alternative: pcae push                        │
  └────────────────────────────────────────────────────────┘
```

### 11.5 Review-Required Section

```
  ┌─ Review Required ──────────────────────────────────────┐
  │ HUMAN REVIEW REQUIRED                                  │
  │                                                        │
  │ This command requires explicit human review before     │
  │ it can proceed. Review is not authorization.           │
  │                                                        │
  │ Human review would change outcome: yes                 │
  │                                                        │
  │ To proceed: re-evaluate with                           │
  │   pcae advisory check --command "..." \                │
  │     --human-review-present                             │
  └────────────────────────────────────────────────────────┘
```

### 11.6 Redaction Section

```
  ┌─ Redaction ────────────────────────────────────────────┐
  │ ⚠️ COMMAND TEXT WAS REDACTED                           │
  │                                                        │
  │ Reason: secret_access_detected                         │
  │                                                        │
  │ PCAE detected potential secret material in the         │
  │ command text (e.g., environment variable assignment,   │
  │ secret file access, or secret-access program). The     │
  │ command text has been replaced with a safe sentinel.   │
  │                                                        │
  │ The original command was NOT executed and NOT logged.  │
  │ No secret material is present in this output.           │
  └────────────────────────────────────────────────────────┘
```

### 11.7 Non-Authorizing Footer

Every human-readable advisory output must end with:

```
────────────────────────────────────────────────────────────
⚠️  PCAE Advisory Mode is NON-AUTHORIZING.

    • No command was executed.
    • No shell was intercepted.
    • No authorization was granted.
    • No enforcement was applied.

    The operator retains full and absolute authority over
    all command execution decisions.

    This is advisory information only.
────────────────────────────────────────────────────────────
```

## 12. JSON Output Design

### 12.1 Design Goals

- Machine-parseable, stable schema
- All advisory decisions as structured fields
- No information loss compared to human-readable output
- Versioned schema for forward compatibility
- Suitable for CI/CD pipeline consumption

### 12.2 JSON Envelope Stability

The existing JSON envelope (88W §16, implemented in 88X) is stable and should be preserved. The schema version `"0.1"` should remain until a breaking change is introduced.

### 12.3 JSON Consumer Guidance

JSON output is designed for:

1. **CI/CD pre-commit hooks**: Parse `would_block`, `hard_block_present`, and `advisory_decision` to decide whether to warn or block.
2. **Editor integrations**: Display advisory decision inline in the editor.
3. **Dashboards**: Aggregate advisory decisions across operators or repositories.
4. **Automated governance**: Scripted checks before sensitive operations.

### 12.4 JSON Field Additions (Future Consideration)

The following fields are recommended for future `schema_version` bumps:

| Field | Type | Purpose |
|-------|------|---------|
| `severity` | string | `info` / `caution` / `review_required` / `blocked` / `unknown` |
| `severity_label` | string | Human-readable severity label |
| `governed_alternative` | string\|null | PCAE-governed command that achieves the same goal |
| `operator_actions` | string[] | List of recommended operator actions |
| `decision_ux_category` | string | `allow` / `require` / `block` / `deny` / `unknown` |

These should not be added in 88Z — they are implementation considerations for 89A+.

## 13. `advisory check` UX

### 13.1 Command Interface (Current — Preserved)

```
pcae advisory check --command "<cmd>" [--json]
    [--action ACTION]
    [--health-passed] [--check-passed]
    [--human-review-present] [--human-approval-present]
    [--accepted-risk-present]
```

### 13.2 UX Improvements (Design Recommendations for 89A+)

| Recommendation | Rationale |
|---------------|-----------|
| Add `--verbose` flag for detailed evidence trace | Default output should be scannable; deep detail on demand |
| Add `--severity` flag to filter output by severity | CI/CD may want to only see `blocked` and `deny` decisions |
| Add `--governed-alternative` flag to always show PCAE alternative | Helps new users discover governed commands |
| Consider `--explain` as shorthand for check + explain | Reduces two-command workflow to one |
| Exit code should reflect severity: 0=info/caution, 1=blocked/deny, 2=unknown | Enables shell scripting: `pcae advisory check ... && run command` |

### 13.3 Output Structure

The check output should always include these sections in this order:
1. **Severity banner** — immediate visual signal
2. **Command summary** — what was evaluated (redacted if needed)
3. **Classification trace** — shell gate category → decision → broker decision → advisory decision
4. **Advisory decision** — the would-* decision with human description
5. **Block/require/allow status** — would-block, would-deny, would-require flags
6. **Hard block detail** (if present) — reason, source, override impossibility
7. **Redaction status** (if applied) — that redaction occurred, why, safety confirmation
8. **Next action** — concrete operator step
9. **Non-authorizing footer** — always present

### 13.4 Exit Codes

| Exit Code | Meaning |
|-----------|---------|
| 0 | Advisory evaluation completed. Decision: info, caution, or review_required. No hard block. |
| 1 | Advisory evaluation completed. Decision: blocked or deny. Hard block present. |
| 2 | Advisory evaluation error (invalid command text, internal error). |

The current implementation always returns 0. The exit code differentiation above is a design recommendation for 89A+.

## 14. `advisory explain` UX

### 14.1 Command Interface (Current — Preserved)

```
pcae advisory explain --decision <decision> [--json]
```

### 14.2 UX Improvements (Design Recommendations for 89A+)

| Recommendation | Rationale |
|---------------|-----------|
| Support `--decision latest` to explain the last check decision | Reduces need to copy-paste decision strings |
| Add `--verbose` for full evidence chain explanation | Currently explain shows summary; verbose could show the full broker→advisory mapping rationale |
| Support decision value autocomplete | 19 values is a lot to remember |
| Add examples to each explanation | Concrete examples help new users |

### 14.3 Explain Content Per Decision

Every `advisory explain` output should include:

| Field | Content |
|-------|---------|
| `decision` | The advisory decision value |
| `valid` | Whether this is a recognized decision |
| `summary` | One-line human description |
| `meaning` | What this decision means in plain language |
| `severity` | The severity level for this decision |
| `would_block` | Whether the command would be blocked |
| `would_deny` | Whether the command would be unconditionally denied |
| `hard_block` | Whether a hard block condition exists |
| `can_override` | Whether human review/approval can change the outcome |
| `governed_alternative` | The PCAE-governed command to use instead (if applicable) |
| `operator_action` | Concrete next step for the operator |
| `example` | A concrete example of a command that would produce this decision |

### 14.4 Comprehensive Explain Coverage

Currently 7 of 19 decisions have detailed explanations. All 19 should have comprehensive explanations. Unknown decisions receive a safe fallback.

**Recommended explanation additions for 89A:**

| Decision | Explanation Content |
|----------|-------------------|
| `would_require_active_task` | What a task contract is, how to create one, why tasks are required |
| `would_require_preflight` | What scope preflight checks, how to run it, what files to list |
| `would_require_more_evidence` | What evidence is missing, how to provide it, common evidence types |
| `would_block_by_scope` | What scope means, how to check allowed files, how to expand scope |
| `would_block_by_task_contract` | Why task contracts gate mutation, how to create/select a task |
| `would_block_by_raw_git_push` | Why raw git push is blocked, how pcae push works |
| `would_block_by_test_run_lock` | What the test run lock is, how to check status, how to wait |
| `would_block_by_failed_health` | Common health failures and fixes |
| `would_block_by_failed_check` | Common check failures and fixes |
| `would_block_by_failed_doctor` | Common doctor failures and fixes |
| `would_block_by_push_check` | What push readiness check validates |
| `would_block_by_conflicting_evidence` | What conflicting evidence looks like, how to resolve |
| `unknown` | Why unknown happens, how to provide more context |

## 15. `advisory status` UX

### 15.1 Command Interface (Current — Preserved)

```
pcae advisory status [--json]
```

### 15.2 UX Improvements (Design Recommendations for 89A+)

| Recommendation | Rationale |
|---------------|-----------|
| Show recent advisory check summary (last N evaluations) | For diagnostic context |
| Show active task status | Task state affects advisory decisions |
| Show governance health summary | Health affects many would-block decisions |
| Add `--watch` mode for CI/CD monitoring | Continuous status during pipeline execution |

### 15.3 Status Output Sections

```
Advisory mode status
  Available:        yes
  Version:          0.1
  Phase:            phase_88z_advisory_operator_ux_and_workflow_design
  Status:           completed
  Schema version:   0.1

  Active task:      88Z — Advisory Operator UX and Workflow Design
  Governance:       health=healthy, check=passed
  Test run:         clear

  Invariants:
    command_executed:      false
    shell_intercepted:     false
    authorization_granted: false
    execution_authorized:  false
    enforcement_applied:   false
    shell_wrappers:        none
    persistent_state:      none
```

## 16. Hard-Block Messaging

### 16.1 Design Principles

1. **Hard blocks must not be phrased as suggestions.** Use "would block," not "consider avoiding."
2. **Hard blocks must state they cannot be overridden.** Human approval and accepted risk do not override hard blocks.
3. **Hard blocks must explain why.** The operator needs to understand the policy rationale.
4. **Hard blocks must suggest the governed alternative.** When a governed PCAE command exists, it must be the primary recommendation.
5. **Hard blocks must not suggest workarounds.** "Run it directly in your shell" is informational, not a recommendation.

### 16.2 Hard-Block Message Template

```
WOULD BLOCK: <hard_block_reason>

This is a HARD BLOCK. It cannot be overridden by human approval,
accepted risk, or operator discretion.

Why: <policy rationale in plain language>

Governed alternative: pcae <alternative command>

Advisory mode does not enforce this block. You may still run the
command directly in your shell, but PCAE policy recommends against it.
```

### 16.3 Hard-Block Wording by Type

| Hard Block | Message |
|-----------|---------|
| `blocked_by_force_push` | "Force push is permanently blocked. No override exists. Use normal push flow." |
| `blocked_by_raw_git_push` | "Raw git push is blocked. Use `pcae push` which runs pre-push governance validation." |
| `blocked_by_shell_gate` | "This command is blocked by PCAE shell policy. The shell gate classifier determined this command category is not allowed." |
| `blocked_by_test_run_lock` | "A test run is in progress. Commands that could interfere are blocked until it completes." |
| `blocked_by_failed_health` | "PCAE health check is failing. Fix health before proceeding. Run `pcae health` to diagnose." |
| `blocked_by_failed_check` | "PCAE governance check is failing. Run `pcae check` to diagnose." |
| `blocked_by_scope` | "This command targets files outside the active task scope. Check allowed files in the task contract." |
| `blocked_by_task_contract` | "No active task contract. Mutating actions require an active task. Create one with `pcae task new`." |
| `would_deny` | "This command is unconditionally denied by PCAE policy. Do not execute this command." |

### 16.4 Anti-Patterns (Do Not Use)

| ❌ Do Not Use | ✅ Use Instead |
|--------------|---------------|
| "We recommend avoiding this command" | "This command would be blocked" |
| "Consider using pcae push instead" | "Use pcae push instead" |
| "You might want to check your health" | "Run pcae health to diagnose" |
| "This could be a problem" | "This would block execution" |
| "It might be better to..." | "Do not execute this command. Use..." |

## 17. Human-Review Messaging

### 17.1 Design Principles

1. **Human review is not authorization.** Review means a human looked at it, not that it's approved.
2. **Human review can change outcomes for non-hard-blocks.** Make clear when review would help.
3. **Human review cannot override hard blocks.** Never suggest review as a hard-block workaround.
4. **Review is a gate, not a blocker.** It should be presented as "requires" not "blocked by."

### 17.2 Human-Review Message Template

```
HUMAN REVIEW REQUIRED

This command requires explicit human review before it can proceed.
Review confirms that a human operator has examined the proposed
action and determined it is appropriate.

Human review would change outcome: yes

To proceed: re-evaluate with human review evidence.
  pcae advisory check --command "..." --human-review-present

Note: Human review is not authorization. The operator retains
full responsibility for the command.
```

## 18. Missing-Evidence Messaging

### 18.1 Design Principles

1. **Name the missing items.** "Missing evidence" is unhelpful. "Missing: active task contract" is actionable.
2. **Explain how to provide each item.** Each missing evidence type should link to the PCAE command that provides it.
3. **Distinguish blocking from non-blocking gaps.** Some missing evidence blocks; some only reduces confidence.

### 18.2 Missing-Evidence Message Template

```
MISSING EVIDENCE

The following evidence items are missing or insufficient:

  • active_task_contract — No active task contract found.
    Provide: pcae task new "<title>"

  • scope_preflight — Scope has not been verified for these files.
    Provide: pcae preflight scope <files>

  • health_check — PCAE health status is unknown.
    Provide: pcae health

Until this evidence is provided, the advisory decision is:
  would_require_more_evidence

Severity: caution
```

## 19. Scope/Task-Contract Messaging

### 19.1 Design Principles

1. **Always show the active task (if any).** The operator needs to know which task is active.
2. **Show what the task allows.** When a command is blocked by scope, show the allowed files/zones.
3. **Show what the task forbids.** When a command targets forbidden files, name them.

### 19.2 Scope-Block Message Template

```
SCOPE BLOCK

Active task: 88Z — Advisory Operator UX and Workflow Design
Requested files: src/pcae/core/shell_gate.py

This file is outside the active task scope.

Allowed files:
  • docs/PHASE_88_ADVISORY_OPERATOR_UX_AND_WORKFLOW_DESIGN.md
  • PROJECT_STATUS.md
  • CHANGELOG.md

Forbidden files:
  • src/**
  • tests/**

Advisory decision: would_block_by_scope

To proceed: update the task contract's allowed files, or select
a task whose scope includes this file.
```

## 20. Secret-Redaction Messaging

### 20.1 Design Principles

1. **Never reveal what was redacted.** The operator must know redaction occurred but not what was hidden.
2. **Never reveal the secret category in excessive detail.** "secret_access_detected" is sufficient; don't say "AWS access key detected."
3. **Always confirm safety.** The output must state that no secret material is present.
4. **Explain why redaction happened.** The operator should understand the detection mechanism.
5. **Never ask the operator to confirm the secret.** "Is this a secret? [y/n]" would leak the secret.

### 20.2 Redaction Message Template

```
⚠️  COMMAND TEXT REDACTED

PCAE detected potential secret material in the command text
and has redacted it from all output fields.

Reason: secret_access_detected
Detection: The shell gate classifier identified this command
as potential secret access (e.g., environment variable
assignment, secret file access, or secret-access program).

Safety: No secret material is present in this output.
The original command was NOT executed and NOT logged.

Advisory decision: would_require_human_review
```

### 20.3 Redaction UX Rules

| Rule | Rationale |
|------|-----------|
| Redaction status always visible | Hidden redaction erodes trust |
| Redacted commands show `<redacted>` sentinel | Consistent machine-parseable sentinel |
| JSON `requested_command` contains sentinel, not original | Never serialize raw secrets |
| Human output never prints original command | Even in error messages |
| Redaction reason uses broad categories | `secret_access_detected`, not `AWS key found` |
| `safe_to_display` always `true` after redaction | Output is safe because secrets were removed |

## 21. "Advisory Only / Not Executed" Messaging

### 21.1 Design Principles

1. **Must be present in every output.** No advisory output should omit this notice.
2. **Must be prominent.** Not buried in fine print. Operators should not miss it.
3. **Must be unambiguous.** "Advisory only" cannot be misinterpreted as "safe to run."
4. **Must list what did NOT happen.** Execution, interception, authorization, enforcement.

### 21.2 Advisory-Only Footer (Mandatory)

```
────────────────────────────────────────────────────────────
⚠️  PCAE Advisory Mode is NON-AUTHORIZING.

    • No command was executed.
    • No shell was intercepted.
    • No authorization was granted.
    • No enforcement was applied.

    The operator retains full and absolute authority over
    all command execution decisions.

    This is advisory information only.
────────────────────────────────────────────────────────────
```

### 21.3 Advisory-Only Wording in Operator Messages

Every operator message should include the advisory-only qualifier:

```
"This command would be blocked by PCAE policy.
Advisory mode does not enforce this block.
You may still run this command directly in your shell."

NOT:
"This command is blocked." ← implies enforcement
```

## 22. False-Positive Workflow

### 22.1 Definition

A false positive occurs when advisory mode reports a `would_block_*` or `would_deny` decision, but the operator believes the command should be allowed.

### 22.2 Known False Positives (from 88Y)

| FP | Command | Advisory Decision | Root Cause |
|----|---------|-------------------|------------|
| FP-1 | `bash` | `would_block_by_shell_gate` | bash not in recognized-programs list |
| FP-2 | `sh -c 'cmd'` | `would_block_by_shell_gate` | sh not in recognized-programs list |
| FP-3 | `env python` | `would_require_human_review` (classified as secret_access) | 88V.1 over-classifies env/printenv |

### 22.3 Operator Workflow for False Positives

```
┌─────────────────────────────────────────────────────────┐
│ 1. OPERATOR RECEIVES would_block_* DECISION             │
│    Operator believes this is a false positive.          │
├─────────────────────────────────────────────────────────┤
│ 2. OPERATOR RUNS EXPLAIN TO UNDERSTAND                  │
│    pcae advisory explain --decision <decision>          │
├─────────────────────────────────────────────────────────┤
│ 3. OPERATOR CHECKS KNOWN FALSE POSITIVES                │
│    Reviews 88Y documented FPs to see if match           │
├─────────────────────────────────────────────────────────┤
│ 4. OPERATOR DECIDES                                     │
│    If known FP:                                          │
│      Acknowledge as documented FP, run command directly  │
│      (at own risk), optionally comment on FP tracking    │
│    If suspected new FP:                                  │
│      Document: command, advisory decision, expected      │
│      decision, evidence for why it should be allowed     │
│      Report via governance channel                       │
├─────────────────────────────────────────────────────────┤
│ 5. FALSE POSITIVE IS RECORDED                            │
│    Added to known-FP list in phase documentation         │
│    Reviewed in next advisory hardening phase (89A)       │
└─────────────────────────────────────────────────────────┘
```

### 22.4 False-Positive Reporting Template

```
False Positive Report
  Command:          <command text>
  Advisory decision: <actual decision>
  Expected decision: <what operator believes is correct>
  Evidence:         <why command should be allowed>
  Shell gate category: <category>
  Broker decision:  <broker_decision>
  Repository state: <health/check/task status>
```

## 23. False-Negative Workflow

### 23.1 Definition

A false negative occurs when advisory mode reports a `would_allow_*` decision, but the operator believes the command should have been blocked or flagged.

### 23.2 Known False Negatives (from 88Y)

| FN | Command | Advisory Decision | Expected | Root Cause |
|----|---------|-------------------|----------|------------|
| FN-1 | `env\|grep TOKEN` (no spaces around pipe) | `would_require_human_review` (but not redacted) | Redaction should apply | shlex.split produces single token `env\|grep`; pipe not detected |

### 23.3 Operator Workflow for False Negatives

```
┌─────────────────────────────────────────────────────────┐
│ 1. OPERATOR NOTICES A COMMAND WAS NOT FLAGGED            │
│    Advisory mode returned would_allow_* but operator     │
│    believes it should have been blocked or flagged.      │
├─────────────────────────────────────────────────────────┤
│ 2. OPERATOR VERIFIES CONCERN                             │
│    Double-checks the command and advisory output         │
├─────────────────────────────────────────────────────────┤
│ 3. OPERATOR DOES NOT RUN THE COMMAND                     │
│    Advisory mode is non-authorizing. The operator's      │
│    own judgment takes precedence.                        │
├─────────────────────────────────────────────────────────┤
│ 4. OPERATOR REPORTS FALSE NEGATIVE                       │
│    Document: command, actual decision, expected           │
│    decision, risk if command were executed                │
│    Report via governance channel                          │
├─────────────────────────────────────────────────────────┤
│ 5. FALSE NEGATIVE IS RECORDED                             │
│    Added to known-FN list in phase documentation          │
│    Reviewed in next advisory hardening phase (89A)        │
│    If critical: may warrant immediate governance action   │
└─────────────────────────────────────────────────────────┘
```

### 23.4 False-Negative Reporting Template

```
False Negative Report
  Command:          <command text>
  Advisory decision: <actual decision>
  Expected decision: <what operator believes is correct>
  Risk if executed: <what harm could occur>
  Shell gate category: <category>
  Broker decision:  <broker_decision>
  Repository state: <health/check/task status>
```

### 23.5 False-Negative Severity

False negatives are more dangerous than false positives:

- **False positive**: Operator is inconvenienced (command blocked, must use alternative). Conservative. Safe.
- **False negative**: Operator might run a dangerous command believing it's safe. Dangerous.

All false negatives should be treated as higher priority than false positives in hardening phases.

## 24. Operator Next-Action Workflow

### 24.1 From Advisory Output to Governed Action

The primary path from advisory check to governed action:

```
pcae advisory check --command "git push origin main"
  → would_block_by_raw_git_push
  → Governed alternative: pcae push
  → Operator runs: pcae push
  → PCAE push performs pre-push validation
  → Push succeeds (or fails with governed error)
```

### 24.2 Decision → Governed Command Mapping

| Advisory Decision | Governed PCAE Command |
|-------------------|----------------------|
| `would_block_by_raw_git_push` | `pcae push` |
| `would_block_by_force_push` | (none — permanently blocked) |
| `would_block_by_failed_health` | `pcae health` |
| `would_block_by_failed_check` | `pcae check` |
| `would_block_by_failed_doctor` | `pcae doctor` |
| `would_block_by_push_check` | `pcae push check` |
| `would_block_by_test_run_lock` | Wait; monitor with `pcae doctor test-run` |
| `would_block_by_task_contract` | `pcae task new "<title>"` |
| `would_block_by_scope` | Update task contract or select different task |
| `would_block_by_shell_gate` | `pcae advisory explain --decision <decision>` |
| `would_require_active_task` | `pcae task new "<title>"` |
| `would_require_preflight` | `pcae preflight scope <files>` |
| `would_require_human_review` | Re-evaluate with `--human-review-present` |
| `would_require_more_evidence` | Provide missing evidence items |

### 24.3 Complete Operator Decision Tree

```
Advisory check result
├── would_allow_read_only
│   └── Proceed at discretion. Command is read-only.
├── would_allow_governed_preflight_only
│   └── Proceed at discretion. Command would pass governance.
├── would_require_*
│   ├── would_require_active_task → pcae task new
│   ├── would_require_preflight → pcae preflight scope
│   ├── would_require_human_review → obtain review, re-evaluate
│   └── would_require_more_evidence → provide evidence, re-evaluate
├── would_block_by_*
│   ├── Governed alternative exists → use governed command
│   ├── Health/check/doctor failure → run diagnostic
│   ├── Scope/task issue → fix task contract
│   ├── Known false positive → run directly (at own risk)
│   └── Suspected false positive → report, decide manually
├── would_deny
│   └── Do not execute. No workaround.
└── unknown
    └── Run pcae advisory explain --decision unknown
```

## 25. Relationship to Governed PCAE Commands

### 25.1 Advisory Mode as Gateway

Advisory mode is the operator's first interaction with PCAE governance for a proposed command. It should serve as a gateway: the operator checks, understands the governance implications, and then either uses the governed alternative or acts at their own discretion.

### 25.2 Governed Command Discovery

Advisory output should teach operators about governed PCAE commands:

| When Advisory Says | Operator Learns |
|-------------------|-----------------|
| `would_block_by_raw_git_push` → "Use pcae push" | `pcae push` exists and is the governed push path |
| `would_block_by_failed_health` → "Run pcae health" | `pcae health` exists for diagnostics |
| `would_require_active_task` → "Run pcae task new" | `pcae task new` creates task contracts |
| `would_require_preflight` → "Run pcae preflight scope" | `pcae preflight` validates scope |
| `would_block_by_test_run_lock` → "Wait or run pcae doctor test-run" | `pcae doctor test-run` checks test status |

### 25.3 Consistency Principle

The recommended governed command in advisory output must match the actual governed command behavior. Advisory mode must not recommend a governed command that doesn't exist or behaves differently than described.

## 26. Relationship to Dry-Run Blocking Simulation

### 26.1 Current State

Dry-run blocking simulation does not exist yet. Advisory mode is the only visible governance layer. There is no enforcement at any level.

### 26.2 Future Relationship

When dry-run blocking is introduced (future phase):

- Advisory mode would report "would block" — and dry-run mode would actually block (in dry-run scope only).
- The advisory UX must clearly distinguish:
  - "This would be blocked if enforcement were active" (advisory mode now)
  - "This IS blocked in dry-run mode" (future dry-run blocking)
  - "This IS blocked in enforcement mode" (future enforcement)
- The severity and messaging models defined here should extend naturally to blocking states.

### 26.3 UX Transition Path

```
Now (88Z):       "would block" — advisory only, not enforced
Dry-run (future): "BLOCKED in dry-run" — blocked in dry-run scope
Enforcement:      "BLOCKED" — blocked in enforcement scope
```

The messaging should make the enforcement level explicit.

## 27. Relationship to Future Enforcement

### 27.1 Enforcement Staging

Per the 88V enforcement staging model:

| Stage | Name | Advisory UX Role |
|-------|------|-----------------|
| 0 | Read-Only Classification | Current baseline: shell gate + broker classify |
| 1 | Advisory | Current state: `pcae advisory check/explain/status` (non-authorizing) |
| 2 | Advisory With Warnings | Advisory mode + warnings for edge cases |
| 3 | Blocking Gate | Dry-run blocking: "would block" becomes "is blocked" in dry-run |
| 4 | Execution Gate With Human Approval | Blocking + human approval can override non-hard-blocks |
| 5 | Enforcement With Accepted Risk | Blocking + accepted risk model |
| 6 | Full Enforcement | Full blocking enforcement |

### 27.2 UX Evolution

As stages advance, the advisory UX should evolve:

- **Stages 1–2**: Advisory-only language. "Would block." "Advisory only."
- **Stages 3–4**: Mixed language. "Would block in production. Blocked in dry-run."
- **Stages 5–6**: Enforcement language. "Blocked." "Denied." (But advisory check remains available for pre-flight evaluation.)

The `pcae advisory check` command should always remain available, even in full enforcement, as a "what-if" evaluation tool.

## 28. Safety Invariants

### 28.1 Permanent Invariants

These invariants must hold for all advisory output, in all formats, at all enforcement stages:

| # | Invariant | Verification |
|---|-----------|-------------|
| **SI-1** | `command_executed` is always `false` | Assert in every test |
| **SI-2** | `shell_intercepted` is always `false` | Assert in every test |
| **SI-3** | `authorization_granted` is always `false` | Assert in every test |
| **SI-4** | `execution_authorized` is always `false` | Assert in every test |
| **SI-5** | `enforcement_applied` is always `false` | Assert in every test |
| **SI-6** | All 14 `performed_flags` are unconditionally `false` | Assert in every test |
| **SI-7** | Redacted commands never appear in any output field | Assert in redaction tests |
| **SI-8** | Non-authorizing notice is present in every human-readable output | Assert in human-readable tests |
| **SI-9** | JSON output contains all required schema fields | Assert schema validation |
| **SI-10** | Advisory mode never invokes subprocess with user command text | Code invariant (no `subprocess.run()` on `requested_command`) |
| **SI-11** | Advisory mode never writes files outside `.pcae/` | Code invariant |
| **SI-12** | Hard blocks are never presented as overridable | Assert `can_override: false` for all hard blocks |
| **SI-13** | Advisory mode never modifies shell configuration | Code invariant (no shell config file writes) |
| **SI-14** | Advisory mode is stateless — each invocation is independent | Test: two calls with same input produce same output |

### 28.2 UX-Specific Safety Invariants

| # | Invariant | Rationale |
|---|-----------|-----------|
| **UX-1** | Adversarial inputs must not cause advisory mode to execute commands | Command text is string data, never evaluated |
| **UX-2** | Unicode/special characters in command text must not break output formatting | Safe output even for unusual inputs |
| **UX-3** | Very long command text must not crash or hang the output formatter | Truncation or safe overflow handling |
| **UX-4** | Null/empty command text must produce a safe, valid advisory output | Handle edge case gracefully |
| **UX-5** | JSON output must be parseable even when command text contains JSON-like characters | Proper escaping |
| **UX-6** | ANSI escape sequences in command text must be sanitized in output | Prevent terminal injection |

## 29. Error Wording Examples

### 29.1 Block Message Examples

```
✅ GOOD:
"Force push is permanently blocked by PCAE policy. Do not force push.
No override exists. Use normal git push with pcae push."

❌ BAD:
"We recommend against force pushing."
"This operation might not be allowed."
"Consider using a different approach."
```

### 29.2 Review Message Examples

```
✅ GOOD:
"This command requires human review before it can proceed. Review
confirms a human operator has examined the proposed action. Human
review is not authorization."

❌ BAD:
"You need someone to approve this."
"Get permission first."
"This needs sign-off."
```

### 29.3 Redaction Message Examples

```
✅ GOOD:
"Command text was redacted: secret_access_detected. PCAE detected
potential secret material in the command and replaced it with a
safe sentinel. No secret material is present in this output."

❌ BAD:
"Your AWS key was removed."
"We hid your password."
"The secret 'abc123' was redacted."
```

### 29.4 Advisory-Only Message Examples

```
✅ GOOD:
"Advisory mode is non-authorizing. No command was executed. No
authorization was granted. The operator retains full authority."

❌ BAD:
"This is just a suggestion."
"Advisory mode says it's probably fine."
"You're cleared to run this."
```

## 30. Example Human-Readable Outputs

### 30.1 Example: Read-Only Command (git status)

```
PCAE Advisory Mode — ℹ️ INFO
Advisory only. No command was executed.

  Command:     git status
  Action:      read

  Shell Gate   read_only_inspection → allow_read_only
  Broker       allow_preflight_only

  Advisory:    would_allow_read_only
  This command is read-only inspection. It would be allowed
  without restrictions.

  Would block: no
  Hard block:  none
  Redaction:   not applied

  Next: Proceed at your discretion.

  Authorization: not granted  Execution: not authorized
  Enforcement:   not applied  Interception: not applied
────────────────────────────────────────────────────────────
⚠️  PCAE Advisory Mode is NON-AUTHORIZING. No command was
   executed. No authorization was granted. Operator retains
   full authority.
────────────────────────────────────────────────────────────
```

### 30.2 Example: Raw Git Push

```
PCAE Advisory Mode — 🚫 WOULD BLOCK
Advisory only. No command was executed.

  Command:     git push origin main
  Action:      push

  Shell Gate   raw_git_push → blocked_by_shell_gate
  Broker       blocked_by_raw_git_push

  Advisory:    would_block_by_raw_git_push

  ┌─ WOULD BLOCK ───────────────────────────────────────┐
  │ WOULD BLOCK: raw_git_push                           │
  │                                                     │
  │ This is a HARD BLOCK. Cannot be overridden.         │
  │                                                     │
  │ Why: PCAE requires all pushes to use the governed   │
  │ pcae push command, which runs pre-push validation   │
  │ (health, check, doctor, test-run lock).             │
  │                                                     │
  │ Governed alternative: pcae push                     │
  └─────────────────────────────────────────────────────┘

  Hard block:  yes — blocked_by_raw_git_push
  Override:    not possible
  Redaction:   not applied

  Next: Use pcae push instead.

  Authorization: not granted  Execution: not authorized
  Enforcement:   not applied  Interception: not applied
────────────────────────────────────────────────────────────
⚠️  PCAE Advisory Mode is NON-AUTHORIZING. No command was
   executed. No authorization was granted. Operator retains
   full authority.
────────────────────────────────────────────────────────────
```

### 30.3 Example: Secret Command (VAR=val cmd)

```
PCAE Advisory Mode — 👁️ REVIEW REQUIRED
Advisory only. No command was executed.

  Command:     <redacted> (redacted)
  Action:      read

  Shell Gate   secret_access → requires_human_review
  Broker       requires_human_review

  Advisory:    would_require_human_review

  ┌─ REDACTION ─────────────────────────────────────────┐
  │ ⚠️  COMMAND TEXT WAS REDACTED                       │
  │ Reason: secret_access_detected                      │
  │ PCAE detected potential secret material. The        │
  │ original command was NOT executed or logged.        │
  │ No secret material is present in this output.       │
  └─────────────────────────────────────────────────────┘

  Would require: human review
  Hard block:   no

  ┌─ REVIEW REQUIRED ───────────────────────────────────┐
  │ HUMAN REVIEW REQUIRED                               │
  │ This command requires human review.                 │
  │ Review is not authorization.                        │
  │                                                     │
  │ To proceed: re-evaluate with                        │
  │   pcae advisory check --command "..." \             │
  │     --human-review-present                          │
  └─────────────────────────────────────────────────────┘

  Next: Obtain human review and re-evaluate.

  Authorization: not granted  Execution: not authorized
  Enforcement:   not applied  Interception: not applied
────────────────────────────────────────────────────────────
⚠️  PCAE Advisory Mode is NON-AUTHORIZING. No command was
   executed. No authorization was granted. Operator retains
   full authority.
────────────────────────────────────────────────────────────
```

## 31. Example JSON Excerpts

### 31.1 JSON: Read-Only Command

```json
{
  "schema_version": "0.1",
  "advisory_mode": true,
  "advisory_mode_version": "0.1",
  "requested_command": "git status",
  "requested_command_redacted": false,
  "broker_decision": "allow_preflight_only",
  "shell_gate_decision": "allow_read_only",
  "shell_gate_category": "read_only_inspection",
  "advisory_decision": "would_allow_read_only",
  "advisory_recommendation": "This command is read-only. It would be allowed without restrictions.",
  "would_block": false,
  "would_deny": false,
  "hard_block_present": false,
  "redaction_applied": false,
  "safe_to_display": true,
  "operator_message": "Advisory evaluation complete. Decision: would_allow_read_only. PCAE advisory mode is non-authorizing. The operator retains full authority.",
  "next_required_action": "Operator may proceed at their own discretion.",
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
  }
}
```

### 31.2 JSON: Hard Block

```json
{
  "requested_command": "git push --force origin main",
  "broker_decision": "blocked_by_force_push",
  "shell_gate_decision": "blocked_by_shell_gate",
  "shell_gate_category": "force_push",
  "advisory_decision": "would_block_by_force_push",
  "advisory_recommendation": "This command would be blocked: force push is permanently blocked.",
  "would_block": true,
  "would_deny": false,
  "hard_block_present": true,
  "hard_block_reason": "blocked_by_force_push",
  "hard_block_source": "broker",
  "human_approval_relevant": false,
  "human_approval_would_change_outcome": false,
  "accepted_risk_relevant": false,
  "operator_message": "This command would be blocked by PCAE policy (blocked_by_force_push). Advisory mode does not enforce this block. The operator may still run this command directly in the shell, but PCAE policy recommends against it.",
  "next_required_action": "Resolve the blocking condition before proceeding. See: pcae advisory explain <decision>"
}
```

### 31.3 JSON: Redacted Secret Command

```json
{
  "requested_command": "<redacted_secret_access_command>",
  "requested_command_redacted": true,
  "broker_decision": "requires_human_review",
  "shell_gate_decision": "requires_human_review",
  "shell_gate_category": "secret_access",
  "advisory_decision": "would_require_human_review",
  "would_block": false,
  "would_deny": false,
  "would_require_human_review": true,
  "hard_block_present": false,
  "redaction_applied": true,
  "redaction_reason": "secret_access_detected",
  "safe_to_display": true,
  "human_approval_relevant": true,
  "human_approval_would_change_outcome": true,
  "operator_message": "This command would require human review. Provide human review evidence and re-evaluate.",
  "next_required_action": "Obtain human review and re-evaluate with --human-review-present."
}
```

## 32. Open UX Questions

The following questions are deferred to implementation phases (89A+):

| # | Question | Context |
|---|----------|---------|
| Q1 | Should advisory check have an exit code convention (0=info, 1=blocked, 2=error)? | Needs implementation discussion |
| Q2 | Should `advisory check` support piping command text from stdin? | `echo "git push" \| pcae advisory check --stdin` |
| Q3 | Should `advisory status` show recent evaluation history? | Requires in-memory or file-based history |
| Q4 | Should there be an `advisory watch` mode for continuous monitoring? | Would need daemon-like behavior |
| Q5 | Should severity emoji be configurable (for terminals that don't support them)? | Accessibility concern |
| Q6 | Should human-readable output support `--no-color` / `--plain` modes? | CI/CD log compatibility |
| Q7 | Should `advisory explain` support `--decision latest` for the last check? | Reduces two-step workflow |
| Q8 | Should the advisory footer be suppressible with `--no-footer`? | For CI/CD consumers who know the footer |
| Q9 | Should there be an `advisory config` command for operator preferences? | Persisting preferences |
| Q10 | How should advisory mode present multi-line command text? | Currently single-line via `--command` |

## 33. Known Lifecycle Issue: Final Task Close to Idle

### 33.1 Issue Description

PCAE currently cannot cleanly commit a final active→done task transition into an empty active-task state. The `pcae check` and `pcae commit` hooks require at least one `.md` task contract in `tasks/active/`. When the last active task is finished, the resulting working tree changes (active file deletion, done file update) cannot be committed through governed PCAE commit because the pre-commit check hook fails with "No active task contract found in tasks/active/."

### 33.2 Impact

- A session that has completed all planned work cannot reach a clean, committed "idle" state without first creating a replacement active task.
- The only governed workaround is to create the next task before closing the current one — meaning `tasks/active/` is never truly empty.
- This conflates "no work to do" (legitimate idle) with "governance violation" (check failure).

### 33.3 Recommendation

Future governance design should address this by either:

1. **Adding a special task-close state** to `pcae check` that permits committing the active→done transition without requiring a replacement active task — the "final task close" is a recognized lifecycle event, not a violation.

2. **Adding `pcae task idle` / `pcae session idle` commands** that explicitly acknowledge the idle state and suppress the "no active task" violation, allowing the commit to proceed.

3. **Introducing an `idle` placeholder task contract** that `pcae task close` auto-creates when closing the last active task — an explicit, governed "no active work" marker.

This issue was discovered during the 88Y.5→88Z transition in the 88Z session and is recorded here for future governance design attention.

## 34. Future Implementation Plan

### 34.1 Recommended Phase Sequencing

| Phase | Name | Type | Description |
|-------|------|------|-------------|
| **89A** | Advisory Mode Hardening / False-Positive Repair | Implementation | Fix known false positives (bash, sh, env python); add known-programs list; address `env\|grep TOKEN` tokenizer limitation |
| **89B** | Advisory Explain Coverage | Implementation | Add comprehensive explanations for all 19 advisory decisions; add examples |
| **89C** | Advisory Output Format Hardening | Implementation | Implement UX design recommendations from 88Z: severity banners, block/redaction sections, non-authorizing footer, improved human-readable layout |
| **89D** | Advisory CI/CD Integration | Implementation | Stable exit codes; `--severity` filter; JSON schema versioning; CI/CD consumer documentation |
| **89E** | Dry-Run Blocking Design | Design | Design dry-run blocking simulation; how advisory mode relates to blocking; operator experience of blocked vs advisory |
| **89F+** | Enforcement Stages 3–6 | Implementation | Graduated enforcement per 88V staging model |

### 34.2 Implementation Priority

1. **False-positive repair (89A)** — highest priority. Known FPs erode operator trust.
2. **Explain coverage (89B)** — high priority. Operators need to understand decisions.
3. **Output format hardening (89C)** — medium priority. Visual improvements to human-readable output.
4. **CI/CD integration (89D)** — medium priority. Enables automated governance.
5. **Dry-run blocking (89E+)** — future phases per enforcement staging.

### 34.3 Backward Compatibility

All UX changes in 89A+ must:
- Preserve the existing JSON schema (`schema_version: "0.1"`) until a breaking change is introduced
- Not change the behavior of existing `pcae advisory check/explain/status` commands except as explicitly designed
- Not change advisory decision vocabulary values (additions are fine, renames are breaking)
- Pass all 294 existing advisory tests

## 35. Recommended Next Phase

**89A — Advisory Mode Hardening / False-Positive Repair**

Fix the three known false positives:
1. Add `bash` and `sh` to a recognized-programs list so they are not classified as unknown
2. Address `env python` over-classification (consider narrowing env/printenv secret_access classification)
3. Investigate `env|grep TOKEN` (no spaces) tokenizer limitation in shlex.split

Additionally:
- Add the known-programs list to shell gate configuration
- Add tests for each FP fix
- Preserve all existing advisory tests
- No enforcement, blocking, or shell interception

## 36. Summary

Phase 88Z defines the operator-facing UX for PCAE advisory mode. Key outcomes:

1. **Five operator personas** defined with specific needs from advisory UX.
2. **Three operator workflows** designed: command evaluation (primary), decision investigation (secondary), status check (tertiary).
3. **Ten UX principles** established, with five anti-principles to avoid.
4. **Five severity levels** defined: info, caution, review_required, blocked, unknown.
5. **15 operator actions** defined with clear when-to-recommend rules.
6. **Human-readable output** redesigned with severity banners, block/review/redaction sections, and mandatory non-authorizing footer.
7. **JSON output** design reviewed with future field recommendations.
8. **Hard-block messaging** defined with templates and anti-patterns.
9. **Human-review messaging** defined — review as gate, not blocker; review as non-authorization.
10. **Missing-evidence messaging** defined with per-item guidance.
11. **Scope/task-contract messaging** defined with allowed/forbidden visibility.
12. **Secret-redaction messaging** defined with safety-first principles.
13. **Advisory-only wording** standardized as mandatory footer and operator-message qualifier.
14. **False-positive workflow** designed with reporting template.
15. **False-negative workflow** designed with severity escalation (FN > FP).
16. **Operator next-action workflow** designed as complete decision tree.
17. **Relationship to governed PCAE commands** defined as teaching/discovery path.
18. **Relationship to dry-run blocking and future enforcement** mapped to 88V staging model.
19. **14 safety invariants** defined plus **6 UX-specific invariants**.
20. **Error wording examples** provided for blocks, reviews, redactions, and advisory-only.
21. **Example outputs** provided for three common scenarios.
22. **Example JSON excerpts** provided for three common scenarios.
23. **10 open UX questions** deferred to implementation phases.
24. **Known lifecycle issue** documented: final task close to idle needs future governance design.
25. **Future implementation plan** mapped across 89A–89F+.
26. **Recommended next phase: 89A** — Advisory Mode Hardening / False-Positive Repair.

This design is a specification. No code was changed. Implementation begins in 89A.
