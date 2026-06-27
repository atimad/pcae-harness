# Phase 88X — Advisory Mode Prototype

```
phase_name    = phase_88x_advisory_mode_prototype
phase_version = 1.0
phase_status  = completed
implementation_status = completed
recommended_next_phase = 88Y_advisory_mode_test_matrix_and_cli_stability_review
```

## 1. Purpose

Implement the first advisory mode prototype that presents broker + shell gate
decisions as non-authorizing advisory output. Implements `pcae advisory check`,
`pcae advisory explain`, and `pcae advisory status`. Advisory mode never
executes commands, blocks commands, intercepts shell execution, installs
wrappers, invokes backends, or grants authorization.

## 2. Scope

In scope:

- `pcae advisory check --command "<cmd>" [--json]` — evaluates a proposed
  shell command through advisory mode and prints the advisory decision
- `pcae advisory explain --decision <decision> [--json]` — explains an
  advisory decision value
- `pcae advisory status [--json]` — reports advisory prototype status and
  invariants
- Core advisory mapper (`src/pcae/core/advisory.py`) that wraps broker +
  shell gate infrastructure
- Advisory decision vocabulary with 19 values, mapping from 25 broker decisions
- JSON and human-readable output
- 88V.1 secret redaction preserved
- Hard-block preservation
- 105 fast-green tests

Out of scope:

- Blocking enforcement, shell interception, shell wrappers
- Shell configuration modification
- Backend invocation, prompts, capture, intake, adoption
- Real execution authorization
- Override of hard blocks
- Persistent advisory state or cache

## 3. Non-Goals

88X must not and does not:

- Implement enforcement, interception, or shell wrappers
- Execute, block, or intercept any command
- Grant execution authorization
- Write persistent storage or cache
- Override hard blocks

## 4. Relationship to 88W Design

88X implements the advisory mode designed in 88W
(`docs/PHASE_88_ADVISORY_ENFORCEMENT_READINESS_DESIGN.md`). The implementation
follows the 88W JSON envelope model, advisory decision vocabulary, operator
workflow, and all invariant guarantees.

## 5. Implemented Commands

### `pcae advisory check`

```
pcae advisory check --command "<cmd>" [--json] [--action ACTION]
    [--health-passed] [--check-passed]
    [--human-review-present] [--human-approval-present]
    [--accepted-risk-present]
```

Evaluates a proposed shell command through advisory mode. Internally:
1. Shell gate classifies the command
2. Broker aggregates evidence and decides
3. Advisory mapper converts broker decision to would-* advisory decision
4. Output is printed as JSON or human-readable text

### `pcae advisory explain`

```
pcae advisory explain --decision <decision> [--json]
```

Explains an advisory decision value. Returns structured explanation
including summary, meaning, would_block status, and override capability.

### `pcae advisory status`

```
pcae advisory status [--json]
```

Reports advisory prototype availability, version, phase, and invariants.

## 6. JSON Envelope

The advisory JSON envelope (returned by `build_advisory`) contains:

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | `"0.1"` |
| `generated_at` | string | ISO 8601 timestamp |
| `repository_root` | string | Repository path |
| `advisory_mode` | bool | Always `true` |
| `advisory_mode_version` | string | `"0.1"` |
| `requested_action` | string | Action being evaluated |
| `requested_command` | string | Command text or redacted sentinel |
| `requested_command_redacted` | bool | Whether command was redacted |
| `broker_decision` | string | Raw broker decision |
| `shell_gate_decision` | string\|null | Raw shell gate decision |
| `shell_gate_category` | string\|null | Shell gate command category |
| `advisory_decision` | string | Would-* advisory decision |
| `advisory_recommendation` | string | Human-readable recommendation |
| `would_block` | bool | Command would be blocked |
| `would_deny` | bool | Command would be denied |
| `would_require_human_review` | bool | Human review would be required |
| `would_require_preflight` | bool | Preflight would be required |
| `would_require_active_task` | bool | Active task would be required |
| `would_require_more_evidence` | bool | More evidence would be needed |
| `hard_block_present` | bool | Hard block condition present |
| `hard_block_reason` | string\|null | Which hard block applies |
| `hard_block_source` | string\|null | Source (shell_gate/broker/scope) |
| `human_approval_relevant` | bool | Human approval relevant |
| `human_approval_would_change_outcome` | bool | Approval would change outcome |
| `accepted_risk_relevant` | bool | Accepted risk relevant |
| `redaction_applied` | bool | Command text was redacted |
| `redaction_reason` | string\|null | Why redaction was applied |
| `safe_to_display` | bool | Output is safe to display |
| `operator_message` | string | Contextual guidance for operator |
| `next_required_action` | string | Recommended next action |
| `authorization_granted` | bool | Always `false` |
| `execution_authorized` | bool | Always `false` |
| `command_executed` | bool | Always `false` |
| `enforcement_applied` | bool | Always `false` |
| `shell_intercepted` | bool | Always `false` |
| `performed_flags` | object | All 14 flags unconditionally `false` |
| `evidence_sources` | array | Evidence sources consulted |
| `missing_evidence` | array | Missing evidence items |
| `warnings` | array | Warnings |
| `errors` | array | Errors |

## 7. Advisory Decision Mapping

Every broker decision maps to an advisory decision:

| Broker Decision | Advisory Decision |
|----------------|-------------------|
| `allow_preflight_only` | `would_allow_governed_preflight_only` |
| `requires_human_review` | `would_require_human_review` |
| `requires_more_evidence` | `would_require_more_evidence` |
| `blocked_by_scope` | `would_block_by_scope` |
| `blocked_by_task_contract` | `would_block_by_task_contract` |
| `blocked_by_raw_git_push` | `would_block_by_raw_git_push` |
| `blocked_by_force_push` | `would_block_by_force_push` |
| `blocked_by_shell_gate` | `would_block_by_shell_gate` |
| `blocked_by_test_run_lock` | `would_block_by_test_run_lock` |
| `blocked_by_failed_health` | `would_block_by_failed_health` |
| `blocked_by_failed_check` | `would_block_by_failed_check` |
| `blocked_by_failed_doctor` | `would_block_by_failed_doctor` |
| `blocked_by_push_check` | `would_block_by_push_check` |
| `blocked_by_conflicting_evidence` | `would_block_by_conflicting_evidence` |
| Other `blocked_by_*` | `would_block_by_shell_gate` |
| `deny` | `would_deny` |
| `unknown` | `unknown` |

## 8. Human-Readable Output

Non-JSON output follows the 88W design with sections:
- Command, Action, Files
- Shell Gate category → decision
- Broker decision
- Advisory decision
- Would block/deny/require status
- Hard block status
- Redaction status
- Operator message and next action
- Authorization/execution/enforcement status
- Non-authorizing notice

## 9. Secret Redaction Behavior

All 88V.1 redaction rules are preserved in advisory mode:
- Secret-like VAR=val prefixes detected → redacted
- env/printenv classified as secret_access → redacted
- Secret file access → redacted
- `requested_command` redacted in all advisory fields
- JSON output never contains raw secret text
- Human-readable output never contains raw secret text

## 10. Hard-Block Handling

Hard blocks are preserved in advisory mode:
- All 18 broker hard block decisions produce `would_block_*` advisory decisions
- `deny` maps to `would_deny`
- Human approval does not override hard blocks
- Accepted risk does not override hard blocks
- Operator messages clearly state blocks and non-enforcement

## 11. Review/Preflight Handling

- Review-required commands → `would_require_human_review`
- Missing evidence → `would_require_more_evidence`
- Missing task → `would_block_by_task_contract`
- Scope denial → `would_block_by_scope`

## 12. No-Execution/No-Interception Guarantees

| Guarantee | Status |
|-----------|--------|
| No command execution | ✅ `command_executed` always `false` |
| No shell interception | ✅ `shell_intercepted` always `false` |
| No shell wrappers | ✅ No wrapper code |
| No backend invocation | ✅ No backend calls in advisory path |
| No authorization | ✅ `authorization_granted` always `false` |
| No enforcement | ✅ `enforcement_applied` always `false` |

## 13. Authorization/Performed-Flag Invariants

All 14 performed flags are unconditionally `false` in every advisory output.
All 4 authorization/enforcement fields are unconditionally `false`.

## 14. Tests Added

105 fast-green tests in `tests/test_advisory_mode.py`:

- **TestAdvisoryCheckEnvelope** (14 tests): JSON envelope structure, required
  fields, invariant fields, performed flags
- **TestAdvisoryCheckReadOnly** (6 tests): Read-only commands produce safe output
- **TestAdvisoryCheckHardBlocks** (11 tests): Hard blocks map to would_block_*
- **TestAdvisoryCheckReviewPreflight** (6 tests): Review/preflight states
- **TestAdvisoryCheckSecretRedaction** (12 tests): Redaction preserved in all output
- **TestBrokerToAdvisoryMapping** (5 tests): Complete broker→advisory mapping
- **TestAdvisoryExplain** (6 tests): Explain command works
- **TestAdvisoryStatus** (3 tests): Status command works
- **TestAdvisoryCheckCLI** (8 tests): CLI integration (JSON, human-readable,
  exit codes)
- **TestAdvisoryInvariants** (34 parametrized): Cross-cutting invariants

## 15. Validation Results

| Suite | Result | Runtime |
|-------|--------|---------|
| Advisory tests | 105 passed | 1.46s |
| Broker tests | 150 passed | ~1.2s |
| Shell gate tests | 774 passed | ~22s |
| Broker-shell integration | 162 passed | ~0.4s |
| Fast-green | 2,814 passed | 24.67s |
| Quick tier | TBD | |
| Full suite | TBD | |

## 16. Remaining Limitations

1. **No shell integration.** Advisory mode is explicitly invoked; it does not
   wrap or monitor shell sessions.

2. **No persistent state.** Each evaluation is independent and stateless.

3. **Explain coverage.** Not all 19 advisory decisions have detailed
   explanations; unknown decisions get a safe fallback.

4. **Active task sensitivity.** Test behavior varies with active task state;
   tests run against the real repo may reflect the current task state.

## 17. Recommended Next Phase

**88Y — Advisory Mode Test Matrix and CLI Stability Review**

Expand advisory test coverage, review CLI output stability, verify edge cases,
and prepare for the next enforcement stage.
