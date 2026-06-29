# Phase 93B — Narrow Shell Gate Prototype

```
phase_name    = phase_93b_narrow_shell_gate_prototype
phase_version = 1.0
phase_status  = completed
implementation_status = simulation_only
recommended_next_phase = 93C — Shell Gate Audit Evidence Model
```

## 1. Purpose

Implement a simulation-only, explicit PCAE-mediated shell-gate check command (`pcae shell-gate check --command "..."`) for Production v1. The prototype classifies proposed shell commands, evaluates them via the Phase 91A permission broker, and returns structured simulation decisions — without executing, intercepting, wrapping, or mediating real shell commands.

## 2. Scope

In scope:

- `check_shell_gate()` core function: classify + broker-evaluate a command string
- Command classification via the existing shell gate classifier (`_classify_command` from 88P/88Q/89A)
- Category-to-broker mapping: shell gate category → broker action_type + command_class
- No-verify flag detection and precedence override
- Updated CLI handler (`run_shell_gate_check`) using the broker-integrated function
- Structured output with simulation markers (simulation_only, no_execution, no_enforcement)
- JSON and human-readable text output
- 90 new tests (68 core + 22 CLI)

Out of scope:

- Shell interception, wrappers, command mediation
- Backend invocation, prompt sending, capture, intake, adoption
- Command execution through any PCAE path
- Telegram inbound control, remote shell, /run
- Enforcement, real blocking, shell configuration modification
- Global shell replacement or hook installation

## 3. Explicit-Check-Only Behavior

The prototype implements the **explicit PCAE-mediated check** pattern recommended in Phase 93A Design A:

- The operator (or agent) explicitly asks PCAE: "how would you classify and gate this command?"
- PCAE classifies the command text, evaluates via the broker, and returns a decision
- PCAE **never** intercepts shell input, never wraps shell commands, never blocks real execution
- The operator retains full authority — they can always run commands directly in the shell
- The shell gate is a governance advisory service, not a shell replacement

## 4. Command Classifier

### 4.1 Implementation

The prototype reuses the existing shell gate classifier (`_classify_command` from `src/pcae/core/shell_gate.py`, Phase 88P) for command text classification. The classifier:

- Parses command text using `shlex.split()`
- Detects compound operators (`&&`, `||`, `;`, `|`) and classifies each segment
- Takes the most restrictive classification across compound segments
- Produces a `command_category` from 25 possible categories

### 4.2 Category → Broker Mapping

A new mapping table (`_CATEGORY_TO_BROKER`) maps each shell gate category to broker `(action_type, command_class)` pairs:

| Shell Gate Category | Broker action_type | Broker command_class |
|---|---|---|
| read_only_inspection | read | read_only |
| test_execution | read | read_only |
| pcae_governed_* | read | governed |
| raw_git_commit | commit | raw_git_commit |
| raw_git_push | push | raw_git_push |
| force_push | push | force_push |
| destructive_filesystem | source_mutation | destructive_filesystem |
| backend_invocation | backend_invocation | backend_invocation |
| filesystem_write | source_mutation | read_only |
| unknown | read | unknown |

### 4.3 No-Verify Override

The `_has_no_verify_flag()` helper detects `--no-verify`, `-n`, and `--no-gpg-sign` flags. When detected in a git commit/push context, the `command_class` is overridden to `no_verify` — a hard-block class in the broker. This ensures `git commit --no-verify -m "x"` is classified as `no_verify` (not `raw_git_commit`), per the 93A design.

## 5. Broker Integration

### 5.1 Flow

```
Command text → _classify_command() → command_category
              → _map_to_broker_inputs() → (action_type, command_class)
              → _detect_task_contract() → task_present
              → _extract_paths() → paths
              → evaluate_permission_broker() → decision, hard_block, reason_code, ...
              → Structured output envelope
```

### 5.2 Broker Call

The `check_shell_gate()` function calls `evaluate_permission_broker()` with:
- `action_type` and `command_class` mapped from classification
- `task_present` from task contract detection
- `paths` extracted from command tokens
- Conservative defaults: `approval_present=False`, `accepted_risk_present=False`, `readiness_ready=False`, `enforcement_authorized=False`

These conservative defaults ensure:
- Hard blocks are always enforced (broker checks command_class first)
- Mutating actions without enforcement authorization are blocked
- Human approval and accepted risk are not assumed present

## 6. Decision Output

### 6.1 Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `command_text` | str | Original command text |
| `command_category` | str | Shell gate classifier category |
| `command_class` | str | Broker command class |
| `action_type` | str | Broker action type |
| `decision` | str | allow / deny / human_review / more_evidence |
| `hard_block` | bool | Non-overridable block (88V §16) |
| `reason_code` | str | Primary machine-readable reason |
| `reason_codes` | list[str] | All reason codes |
| `message` | str | Human-readable operator message |
| `required_evidence` | list[str] | Evidence needed (empty if allow/deny) |
| `audit_payload` | dict | Audit-relevant fields |
| `simulation_only` | bool | Always true |
| `no_execution` | bool | Always true |
| `no_enforcement` | bool | Always true |

### 6.2 Decision Examples

```
$ pcae shell-gate check --command "git push --force"
Decision: deny, Hard block: True, Reason: blocked_by_force_push

$ pcae shell-gate check --command "git status"
Decision: allow, Hard block: False

$ pcae shell-gate check --command "git commit --no-verify -m x"
Decision: deny, Hard block: True, Reason: blocked_by_no_verify

$ pcae shell-gate check --command "xyzzy123"
Decision: deny, Hard block: True, Reason: blocked_by_unknown_command_class
```

## 7. No-Execution Guarantee

The prototype unconditionally preserves these invariants:

- `simulation_only = True` — every output states simulation mode
- `no_execution = True` — no command is ever executed
- `no_enforcement = True` — no enforcement is applied
- `authorization_granted = False` — no authorization is granted
- `command_executed = False` — the command_executed flag is always false
- `shell_intercepted = False` — no shell interception occurs
- `wrappers_installed = False` — no wrappers are installed
- `backend_invoked = False` — no backends are invoked

## 8. Simulation-Only Boundary

The prototype is **simulation-only** — it classifies and evaluates, but never:

1. Executes any command text (not even echo, ls, or pwd)
2. Intercepts shell input (no PROMPT_COMMAND, no shell hooks)
3. Installs wrappers or modifies shell configuration
4. Blocks real shell commands (operator always has direct shell access)
5. Invokes AI backends
6. Sends prompts, captures output, performs intake/adoption
7. Grants execution authorization
8. Persists audit state to disk

## 9. Relationship to 93A

| 93A Design Element | 93B Implementation |
|---|---|
| Narrow surface: 10 command classes | Implemented: classification + broker mapping for all 10 classes |
| Explicit PCAE-mediated check (Design A) | Implemented: `pcae shell-gate check --command "..."` |
| Hard-block invariant (88V §16) | Preserved: hard-block classes checked first, non-overridable |
| Fail-closed for unknown commands | Implemented: unknown → hard block |
| Broker integration via evaluate_permission_broker() | Implemented: full integration with mapped inputs |
| Audit model (21 fields) | Deferred to 93C |
| Test strategy (~146 tests) | 90 tests this phase; remaining deferred to 93C |

## 10. What Remains for 93C+

- **93C**: Shell gate audit evidence model — disk-based audit records, chain integrity
- **93D+**: Scope preflight integration (extract paths, validate against task contract)
- **Future**: Git hook augmentation, opt-in shell wrapper, agent-specific mediation

## 11. No-Go Conditions

- No shell interception, wrappers, or command mediation
- No backend invocation through PCAE
- No command execution through PCAE
- No Telegram inbound control, remote shell, /run
- No enforcement, real blocking, or shell configuration modification
- No test weakening, xfail, or skip
- No starting 93C

## 12. Test Coverage

| Category | Test Class/File | Count |
|----------|----------------|-------|
| Classification (categories) | TestClassifierCategories | 23 |
| Classification (command classes) | TestClassifierCommandClass | 14 |
| No-verify detection | TestNoVerifyDetection | 4 |
| Hard-block decisions | TestHardBlockDecisions | 7 |
| Allow decisions | TestAllowDecisions | 3 |
| Test execution | TestTestExecution | 2 |
| Backend invocation | TestBackendInvocation | 2 |
| Hard-block non-overridable | TestHardBlockNonOverridable | 3 |
| Output model | TestOutputModel | 7 |
| Non-execution guarantee | TestNoExecutionGuarantee | 4 |
| Edge cases | TestEdgeCases | 5 |
| CLI JSON output | TestJsonOutput | 9 |
| CLI text output | TestTextOutput | 4 |
| CLI non-execution | TestCliNoExecution | 3 |
| **Total** | | **90** |

---

*Phase 93B implements the simulation-only narrow shell gate prototype. 90 new tests pass. No shell interception, wrappers, command mediation, backend invocation, Telegram inbound control, remote shell, /run, enforcement, or command execution path was implemented. Recommended next phase: 93C — Shell Gate Audit Evidence Model.*
