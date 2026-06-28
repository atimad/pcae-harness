# Phase 91C — Hard-Block Policy Readiness

```
phase_name    = phase_91c_hard_block_policy_readiness
phase_version = 1.0
phase_status  = completed
implementation_status = simulation_only
recommended_next_phase = 92A — Phase Report Artifact Model
```

## 1. Purpose

Harden the permission broker hard-block policy model with an explicit, auditable registry. Prove that every hard block is non-overridable, explained, tested, and ready for future shell-gate planning.

## 2. Scope

In scope:

- `HardBlockPolicy` frozen dataclass with 10 fields
- `HARD_BLOCK_REGISTRY` — 12 hard-block policy entries
- `validate_hard_block_registry()` — invariant validation
- `get_hard_block_policy()` / `is_hard_block_reason()` — lookup helpers
- CLI: `pcae permission-broker hard-blocks [--json]`
- 30 tests proving all invariants

Out of scope: enforcement, shell interception, wrappers, backends, execution.

## 3. Hard-Block Registry

12 hard blocks, each with:

| Field | Type | Description |
|-------|------|-------------|
| `reason_code` | str | Machine-readable reason code |
| `category` | str | Short category label |
| `title` | str | Human-readable title |
| `explanation` | str | Detailed explanation |
| `override_allowed` | bool | Always `False` (88V §16) |
| `approval_can_override` | bool | Always `False` |
| `accepted_risk_can_override` | bool | Always `False` |
| `future_enforcement_required` | bool | Always `True` |
| `audit_required` | bool | Always `True` |
| `readiness_implication` | str | What must be ready before enforcement |

### Registry Entries

| # | Reason Code | Category |
|---|-----------|----------|
| 1 | `blocked_by_raw_git_commit` | raw_git_commit |
| 2 | `blocked_by_raw_git_push` | raw_git_push |
| 3 | `blocked_by_force_push` | force_push |
| 4 | `blocked_by_no_verify` | no_verify |
| 5 | `blocked_by_destructive_filesystem` | destructive_filesystem |
| 6 | `blocked_by_unknown_command_class` | unknown_class |
| 7 | `blocked_by_out_of_scope` | out_of_scope |
| 8 | `blocked_by_policy_forbidden_file` | forbidden |
| 9 | `blocked_by_forbidden_path` | task_forbidden_path |
| 10 | `blocked_by_missing_task` | missing_task |
| 11 | `blocked_by_enforcement_not_ready` | enforcement_not_ready |
| 12 | `blocked_by_enforcement_not_authorized` | enforcement_not_authorized |

## 4. Non-Overridability Invariant (88V §16)

Every hard block in the registry has:
- `override_allowed = False`
- `approval_can_override = False`
- `accepted_risk_can_override = False`

The registry's `invariant_88v16_preserved` field is `True` — verified by both unit tests and the CLI.

## 5. CLI

```
$ pcae permission-broker hard-blocks
Hard-block policy registry
  Total hard blocks:   12
  Override allowed:    False
  Approval override:   False
  Risk override:       False
  All audit required:  True
  88V §16 preserved:   True
  Registry valid:      True
  ...
```

Supports `--json` with full per-entry detail.

## 6. Tests (30)

| Category | Tests |
|----------|-------|
| Registry structure (12 entries, required fields) | 2 |
| Invariant proofs (override_allowed, approval, risk, audit) | 5 |
| Human-readable content (title, explanation, readiness) | 2 |
| Registry validation passes | 1 |
| Lookup functions (get, is) | 4 |
| Reason code completeness | 1 |
| future_enforcement_required | 1 |
| Immutability | 1 |
| Per-category override proof (6 × approval, 6 × risk, 6 × both) | 3 |
| Contextual hard blocks (out_of_scope, missing_task) | 1 |
| Fail-closed never produces allow | 1 |
| Registry does not introduce enforcement | 1 |

## 7. Relationship to 91A / 91B

- **91A**: `evaluate_permission_broker()` emits hard-block reason codes. 91C adds a registry that describes and validates those codes.
- **91B**: CLI `explain --reason-code` covers individual codes. 91C adds `hard-blocks` that lists the full registry.

## 8. Relationship to Future Shell Gate

The `readiness_implication` field on each hard block describes what the shell gate must support before that hard block can be enforced:
- Classify command patterns (force push variants, destructive commands, no-verify flags)
- Detect scope violations (out-of-scope files, forbidden files)
- Detect missing task contracts
- Check enforcement readiness state

## 9. What Remains for 92A

- Phase report artifact model: durable structured reports for phase completions
- Pluggable notification foundation: adapter interface for delivery channels
- No hard-block changes needed — the registry is complete for Production v1

## 10. No-Go Conditions

- No enforcement implementation until all 89J readiness gates are satisfied
- No shell interception or wrappers
- No backend invocation from broker
- No command execution through any PCAE path

---

*Phase 91C hardens the hard-block policy model. 12 hard blocks are registered, all non-overridable, all audit-required, all explained. The 88V §16 permanent invariant is preserved. No enforcement, shell interception, wrappers, backend invocation, Telegram control, notification code, or command execution path was implemented. Recommended next phase: 92A — Phase Report Artifact Model.*
