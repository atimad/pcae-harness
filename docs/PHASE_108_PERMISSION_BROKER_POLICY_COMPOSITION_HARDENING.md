# Phase 108C — Permission Broker Policy Composition & Hardening

## Purpose

Harden the Permission Broker policy framework (108A foundation, 108B rule
framework) so decision composition is deterministic, explainable, modular,
and future-pluggable. This phase changes no public behavior for any
previously-tested scenario — `tests/test_permission_broker_foundation.py`
(108A, 60 tests) and `tests/test_permission_broker_policy_rule_framework.py`
(108B, 63 tests) are unmodified and re-verified to pass unchanged. What
changes is what the broker does when circumstances 108A/108B never
exercised: multiple simultaneously-triggered policies of the same
category, a malformed or failing policy rule, and an empty or
misconfigured registry.

## Scope

Broker hardening only, inside
`src/pcae/core/permission_broker_foundation.py`. Adds
`tests/test_permission_broker_policy_composition_hardening.py`. No
runtime execution, shell mediation, subprocess mediation, backend
invocation, adapter invocation, Telegram inbound, audit persistence,
rollback execution, emergency stop implementation, execution enablement,
execution capability, command execution, file mutation beyond this
phase's own governed source/test/doc changes, automatic apply, shell
boundary integration, backend boundary integration, or adapter boundary
integration is implemented.

## Decision Composition

Composition is now fully centralized in one function, `_compose(results)`,
which is the *only* place in the module a `PermissionBrokerDecision` is
ever assembled. `PermissionBroker.evaluate()` itself does nothing but the
structural-validation guard and `return _compose(results)` — verified
directly by a test asserting `evaluate()`'s source contains at most two
`return` statements and calls `_compose(`.

`_compose` takes the *full* tuple of `PolicyResult`s (not just the
triggered ones, unlike 108B) so it can also detect the "no policy was
evaluated at all" case and apply composition uniformly for every input
shape.

## Precedence Rules

Fixed, tested precedence: **DENY > HUMAN_REVIEW > ALLOW**, fail closed.

1. Any triggered `DENY` → wins, regardless of how many `HUMAN_REVIEW` or
   non-triggered rules exist.
2. No `DENY`, but any triggered `HUMAN_REVIEW` → wins.
3. Nothing triggered → `ALLOW` (the default), *only if* at least one
   policy was actually evaluated (see Conflict Handling below).

Ordering within a category is deterministic: rules are evaluated in fixed
registry order (`POL-001..012`, or whatever order a custom registry
declares), so `evaluated_policy_ids`, `triggered_policy_ids`,
`causing_policy_ids`, and `reason_chain` are always in that same order —
verified by a test that calls `evaluate()` 25 times on an identical
request and asserts every result is equal.

## Conflict Handling

| Conflict | Resolution |
|---|---|
| ALLOW + DENY | DENY |
| ALLOW + HUMAN_REVIEW | HUMAN_REVIEW |
| DENY + HUMAN_REVIEW | DENY |
| Multiple DENY rules | DENY; all causes preserved (see below) |
| No applicable policy (empty registry) | DENY, fail-closed |
| Unknown/malformed policy result | DENY, fail-closed |

**Multiple simultaneous causes are preserved, not collapsed.** When two or
more rules trigger the same winning category, `_compose` computes an
order-preserving, deduplicated union of every contributing rule's
`matched_no_go_ids`, `matched_invariants`, `matched_component_ids`, and
`required_remediation` — not just the first rule's. `causing_policy_id`
(singular, first contributor in registry order) is retained for 108B
compatibility; `causing_policy_ids` (plural, Phase 108C) lists every
contributor.

**An empty registry cannot vouch for ALLOW.** If `results` is empty (no
policy was evaluated at all — e.g. a misconfigured `PolicyRegistry(rules=())`),
`_compose` fails closed to `DENY` (`decision_reason="no_applicable_policy"`,
`NG-009`/`INV-004`) rather than defaulting to `ALLOW`. This is a genuine
behavior change from a naive reading of 108B's composition (which would
have silently defaulted to ALLOW on zero results) — no existing 108A/108B
test exercises an empty registry, so this is purely additive hardening,
not a compatibility break.

**A malformed or failing policy rule never crashes evaluation and is
never silently ignored.** `PolicyRegistry.evaluate_all()` wraps every
rule's `evaluate()` call: an exception, a non-`PolicyResult` return value,
or a `triggered=True` result whose `decision` is outside
`ALLOW`/`DENY`/`HUMAN_REVIEW` is converted by `_sanitize_result` into a
synthetic `DENY`-triggering result (`decision_reason="invalid_policy_result"`,
`NG-024`/`INV-004`, still labeled with the offending rule's own
`policy_id` when determinable) before composition ever sees it.

## Reason-Chain Model

Every decision carries `reason_chain: tuple[ReasonChainLink, ...]` — one
`ReasonChainLink` per policy rule that contributed to the winning
category, each with `policy_id`, `no_go_ids`, `invariant_ids`,
`component_ids`. For a single-cause decision this reproduces the brief's
canonical example exactly:

```
POL-003 -> NG-023 -> INV-009 -> COMP-001
```

For a multi-cause decision, `reason_chain` has one link per contributor,
in registry order — machine-readable and directly testable (`len()`,
indexing, field access), with no string-parsing required.

## Explainability Model

Every `PermissionBrokerDecision` exposes:

- `evaluated_policy_ids` — every policy that ran (always all registered
  IDs, unaffected by outcome).
- `triggered_policy_ids` — every policy whose condition fired, regardless
  of whether it determined the outcome.
- `causing_policy_id` / `causing_policy_ids` — the primary / all
  contributors to the winning category.
- `matched_no_go_ids`, `matched_invariants`, `matched_component_ids`,
  `required_remediation` — the aggregated union across all contributors.
- `reason_chain` — the same information restructured per-contributor.
- `precedence_reason` — one sentence naming which precedence rule decided
  the outcome (e.g. `"deny_precedence: 2 DENY-triggering policies present"`,
  `"human_review_precedence: 1 HUMAN_REVIEW-triggering policy present"`,
  `"allow_default: no policy triggered a block"`,
  `"fail_closed_no_policies_registered"`, `"fail_closed_invalid_request"`).
- `implementation_status` — unconditionally `"execution_unavailable"` on
  every decision, unchanged since 108A.

## Modular / Pluggable Policy-Rule Architecture

Unchanged from 108B, re-verified under hardening: `PolicyRule`
implementations remain independent (each `evaluate()` takes only
`request`, never inspects another rule); `PolicyRegistry` accepts any rule
tuple, including one larger than the canonical 12, without
`PermissionBroker` requiring any modification (a test constructs a
13-rule registry and confirms the broker handles it transparently); the
broker module has no dependency on shell, backend, adapter, or Telegram
modules (re-verified via AST import inspection, now explicitly including
`adapter` and `subprocess` in the forbidden-substring list alongside
108A's original `shell_gate`/`backend_invocations`/`notifications`); every
policy rule's `evaluate()` returns a `PolicyResult` and only a
`PolicyResult` (verified for all 12 default rules); no policy rule's
source contains `subprocess`, `os.system`, `eval(`, or `exec(`; the module
contains no dynamic plugin-loading machinery (`importlib`, `__import__`,
`pkg_resources`, `entry_points` all absent) — a plain, explicit registry
tuple remains sufficient, per this phase's own design instruction.

## Fail-Closed Behavior

Every new hardening path resolves toward `DENY`, never `ALLOW`, on
anything unknown, unavailable, or unsupported — consistent with 108A's
original design principle 1 and INV-004/INV-009:

- No policy registered at all → `DENY` (`NG-009`/`INV-004`).
- A policy rule raises an exception → `DENY` (`NG-024`/`INV-004`,
  `invalid_policy_result`).
- A policy rule returns a non-`PolicyResult` object → `DENY` (same).
- A policy rule returns `triggered=True` with an unrecognized `decision`
  value → `DENY` (same).
- A structurally invalid request object → `DENY` (`NG-023`/`INV-009`,
  unchanged from 108A).

## Current Non-Executing Status

Unchanged. `implementation_status` remains unconditionally
`"execution_unavailable"` on every decision this broker returns,
including `ALLOW`. The broker still has no dependency on shell execution,
subprocess invocation, real AI backend calls, adapter execution, or
Telegram — this phase strengthens that isolation guarantee (explicit
`adapter` and `subprocess` checks added) rather than relaxing it.
`v0.1.0-rc1` remains non-executing by design; v0.2 remains the autonomy
target (Level 3, not Level 4/5).

## Future Integration Guidance

- **108D — Permission Broker Verification & Compatibility** (recommended
  next phase): a verification pass over the full 108A→108C surface before
  any boundary component is allowed to depend on the broker.
- When `POL-002` (Task Outside Scope) and the other five stub policies
  eventually gain real logic, they slot into the existing
  `DEFAULT_POLICY_RULES` tuple in place — `_compose`'s aggregation and
  fail-closed guards require no change, since they operate on whatever
  `PolicyResult`s the registry produces, not on which specific rules exist.
- Future boundary components (Shell/Backend/Adapter, once implemented in
  their own separately-gated phases) must ask this broker for a decision
  rather than re-implementing any policy condition themselves — this
  phase's isolation tests exist specifically to keep that invariant
  checkable as the codebase grows.
- The `_sanitize_result` fail-closed guard means a future rule author can
  add a new `PolicyRule` with more confidence: any mistake in the new
  rule's return value degrades to a safe `DENY`, not a crash or a silent
  pass-through `ALLOW`.

## No-Go Confirmations

No runtime execution. No shell mediation. No subprocess mediation. No
backend invocation. No adapter invocation. No Telegram inbound. No audit
persistence. No rollback execution. No emergency stop implementation. No
execution enablement. No execution capability. No command execution. No
file mutation beyond this phase's own governed source/test/doc changes.
No automatic apply. No shell boundary integration. No backend boundary
integration. No adapter boundary integration. `implementation_status`
remains unconditionally `"execution_unavailable"`. `ALLOW` never results
in executable behavior. `v0.1.0-rc1` remains non-executing by design; v0.2
remains the autonomy target. GitHub Release for `v0.1.0-rc1` and branch
protection on `main` are unchanged. No new tag. No new GitHub Release. No
PyPI/GitHub Packages publication.

## Recommended Next Phase

**108D — Permission Broker Verification & Compatibility.**
