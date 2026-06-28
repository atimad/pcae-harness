# Phase 89C — Dry-Run Blocking Simulation Prototype

```
phase_name    = phase_89c_dry_run_blocking_simulation_prototype
phase_version = 1.0
phase_status  = completed
implementation_status = completed
recommended_next_phase = 89d_dry_run_simulation_test_matrix_and_cli_stability_review
```

## 1. Purpose

Implement the first read-only dry-run blocking simulation prototype designed in 89B. The prototype exposes simulation-only commands (`pcae dry-run check/explain/status`) that evaluate command intent through existing advisory/broker/shell-gate logic and report what PCAE would block, allow, require review for, or require evidence for — without executing, intercepting, authorizing, or enforcing anything.

## 2. Scope

In scope:

- `src/pcae/core/dry_run.py` — core simulation module wrapping advisory evidence
- `src/pcae/commands/dry_run.py` — CLI runners for check/explain/status
- `src/pcae/cli.py` — command registration (dry-run group)
- `tests/test_dry_run_simulation.py` — 74 fast-green tests
- JSON output with all invariant fields (simulation_only, authorization_granted=false, etc.)
- Human-readable output with SIMULATED prefix and footer
- Differentiated exit codes (0=allow, 1=blocked/deny)

Out of scope:

- Real blocking, enforcement, shell interception, wrappers
- Executing commands, invoking backends, sending prompts
- Persistent state or cache
- Changing advisory, broker, or shell gate behavior

## 3. Non-Goals

89C must not and does not implement enforcement, blocking beyond advisory decisions, shell interception, wrappers, shell config modification, command execution, backend invocation, prompt sending, output capture, intake/adoption, authorization grants, persistent state, or cache.

## 4. Design Source from 89B

Implements the dry-run blocking simulation designed in `docs/PHASE_89_DRY_RUN_BLOCKING_SIMULATION_DESIGN.md` (89B). Follows the recommended command namespace `pcae dry-run`, the 19-value simulation decision vocabulary, the severity model, and all safety invariants.

## 5. Commands Implemented

### `pcae dry-run check`

```
pcae dry-run check --command "<cmd>" [--json] [--action ACTION]
    [--health-passed] [--check-passed]
    [--human-review-present] [--human-approval-present]
    [--accepted-risk-present]
```

Evaluates a proposed shell command through dry-run simulation. Internally delegates to advisory mode (which delegates to broker + shell gate). Returns differentiated exit codes: 0=allow/caution/review, 1=blocked/deny.

### `pcae dry-run explain`

```
pcae dry-run explain --decision <decision> [--json]
```

Explains a simulation decision value with severity, governed alternative, and enforcement readiness.

### `pcae dry-run status`

```
pcae dry-run status [--json]
```

Reports simulation prototype availability, version, phase, enforcement stage, invariants, and known limitations.

## 6. JSON Schema

The simulation JSON envelope contains 50+ fields including:

| Field | Description |
|-------|-------------|
| `simulation_mode` | Always `true` |
| `simulation_id` | Unique ID per invocation (`sim-` prefix + 12 hex chars) |
| `enforcement_stage` | `"dry_run_simulation"` |
| `simulation_decision` | One of 19 `would_*` values |
| `simulation_severity` | `info`/`caution`/`review_required`/`blocked`/`unknown` |
| `governed_alternative` | PCAE-governed alternative command (or null) |
| `enforcement_readiness` | Human-readable enforcement transition guidance |
| `safety_invariants` | 10 boolean invariants (all true) |
| `known_limitations` | Explicit list of simulation limitations |

All authorization/enforcement/interception fields are unconditionally `false`.

## 7. Human-Readable Output

Human-readable output includes:

- Severity banner: `ℹ️ INFO` / `⚠️ CAUTION` / `👁️ REVIEW REQUIRED` / `🚫 SIMULATED BLOCK` / `❓ UNKNOWN`
- Shell gate → broker → simulation classification chain
- SIMULATED BLOCK section with hard block detail and governed alternative
- REVIEW REQUIRED section with human review guidance
- Enforcement readiness guidance
- "Simulation only. No enforcement occurred." header
- Mandatory non-authorizing simulation footer

## 8. Decision Mapping

Decisions are delegated to advisory mode's broker→advisory mapping:

| Broker Decision | Simulation Decision |
|----------------|---------------------|
| `allow_preflight_only` | `would_allow_governed_preflight_only` |
| `blocked_by_raw_git_push` | `would_block_by_raw_git_push` (severity: blocked) |
| `blocked_by_force_push` | `would_block_by_force_push` (severity: blocked) |
| `requires_human_review` | `would_require_human_review` (severity: review_required) |
| `deny` | `would_deny` (severity: blocked) |

Severity mapping: info (allow), caution (require task/preflight/evidence), review_required (human review), blocked (any would_block_* or would_deny), unknown.

## 9. Safety Invariants

All 11 invariant fields are unconditionally `false` in every simulation output:
- `authorization_granted`, `execution_authorized`, `command_executed`
- `enforcement_applied`, `shell_intercepted`, `wrapper_installed`
- `backend_invoked`, `prompt_sent`, `output_captured`
- `intake_performed`, `adoption_performed`

10 safety_invariants boolean fields are unconditionally `true`.

## 10. Hard-Block Preservation

Hard blocks preserved per 89B design:
- Force push → `would_block_by_force_push` (severity: blocked, no governed alternative)
- Raw git push → `would_block_by_raw_git_push` (governed alternative: `pcae push`)
- Shell gate blocks → corresponding `would_block_by_*`
- Human approval and accepted risk do NOT override hard blocks (`human_approval_cannot_override_hard_block: true`)

## 11. Secret-Redaction Preservation

All 88V.1 and 89A redaction rules preserved:
- Secret VAR=val prefixes → redacted
- env/printenv (secret-like) → redacted
- Secret file access → redacted
- Compact pipe `env|grep TOKEN` → detected and redacted (89A fix)
- `requested_command` field contains `<redacted_secret_access_command>` sentinel
- No raw secret text in any output field

## 12. Tests Added

**74 tests** in `tests/test_dry_run_simulation.py`:

| Class | Tests | Description |
|-------|-------|-------------|
| TestSimulationEnvelope | 3 | Schema, required fields, simulation_mode=true |
| TestSimulationInvariantFalseFields | 33 | All 11 invariant fields false for 3 command types |
| TestSimulationSafetyInvariants | 2 | Safety invariants object and known limitations |
| TestSimulationId | 2 | ID present and unique per invocation |
| TestSimulationDecisionMapping | 7 | Key decisions mapped correctly |
| TestSimulationSeverity | 4 | Severity model mapping |
| TestSimulationEnforcementReadiness | 2 | Readiness field present |
| TestHardBlockPreservation | 3 | Hard blocks preserved, cannot override |
| TestSecretRedaction | 4 | Redaction applied, sentinel used |
| TestSimulationExplain | 4 | Explain works for known and unknown decisions |
| TestSimulationStatus | 3 | Status returns correct invariants |
| TestSimulationDecisionVocabulary | 2 | 19 decisions defined |
| TestSimulationCompoundCommands | 3 | Compound commands use most-restrictive |

## 13. Validation Results

| Suite | Result | Runtime |
|-------|--------|---------|
| Dry-run simulation | 74 passed | ~0.04s |
| Advisory mode | 292 passed | ~4.9s |
| Shell gate matrix | 287 passed | ~0.3s |
| Broker edge cases | 143 passed | ~0.5s |
| Fast-green | 3,075 passed | 24.87s |
| Quick tier | 8,379 passed | 277s (4:37) |
| Full suite | ~9,138 passed + known 3 failures | ~19:00 |

## 14. Known Full-Suite Baseline Issue

The 3 known pre-existing failures from 89A are unchanged:
- 2 in `test_preflight_integration_verification.py` (`test_88m_requires_human_review[backend]`, `[mutation]`)
- 1 flaky `test_project_state_no_repository_files_created`

No new 89C failures introduced.

## 15. Remaining Limitations

1. **Simulation is not enforcement.** Commands are never actually blocked. Operator can always bypass.
2. **No shell integration.** Simulation is explicitly invoked, not wrapped around shell sessions.
3. **Stateless.** No history, audit trail, or persistent records.
4. **Delegates to advisory for core logic.** Simulation adds the simulation envelope but does not add new classification capabilities.
5. **Exit codes advisory only.** Exit code 1 is informational; operator can still proceed.
6. **Single-command evaluation.** One command per invocation.

## 16. Recommended Next Phase

**89D — Dry-Run Blocking Simulation Test Matrix and CLI Stability Review**

Expand simulation test coverage across command categories, review CLI JSON stability, verify simulation output consistency, and prepare for CI/CD integration.
