# Phase 108D — Permission Broker Verification & Compatibility

## Purpose

Verify and harden Permission Broker compatibility after 108A (foundation),
108B (policy rule framework), and 108C (composition hardening) — without
wiring the broker into execution, shell, commit, push, backend, adapter,
Telegram, CI, or PR automation paths. This phase adds no new broker
behavior. It strengthens the test surface proving the broker remains
isolated, contract-traceable, deterministic, and unwired into any command
path, and cross-references the broker's `NG-`/`INV-` outputs directly
against the actual frozen document text rather than only against
hardcoded expected sets.

## Scope

Verification only. Adds
`tests/test_permission_broker_verification_compatibility.py` (44 tests)
and this document. No change to
`src/pcae/core/permission_broker_foundation.py` — this phase's task
contract does not even include the `core` zone, enforcing that boundary
structurally, not just by intent. No runtime execution, shell mediation,
subprocess mediation, backend invocation, adapter invocation, Telegram
inbound, audit persistence, rollback execution, emergency stop
implementation, execution enablement, execution availability toggle,
no-go runtime enforcement, automatic apply, patch execution, PR creation,
PR merge, approval automation, required CI status-check changes, branch
protection changes, hook auto-install, or pre-push hook is implemented.

## Verification Scope

Four areas, matching this phase's four objectives:

1. **Broker isolation** — import allowlist, absence from lifecycle
   command modules, no side effects, `ALLOW` still `execution_unavailable`.
2. **Compatibility with 107B/107C** — every `NG-`/`INV-` ID the broker
   can emit is cross-checked against the *actual current text* of
   `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` and
   `docs/V0_2_AUTONOMY_CONTRACT.md` (parsed with a regex extracting every
   `NG-NNN`/`INV-NNN` occurrence), not merely against a hardcoded set
   that could silently drift from the frozen docs.
3. **Decision composition** — multi-cause DENY/HUMAN_REVIEW, precedence,
   dedup, explainability fields, and every fail-closed path (malformed
   rule, raising rule, empty registry, unknown action, missing evidence,
   ambiguity), re-verified against the real `DEFAULT_POLICY_RULES`
   registry in addition to 108C's synthetic test rules.
4. **Backward compatibility** — 108A/108B/108C test modules import
   cleanly and (via the validation suites below) pass unchanged; the
   public `PermissionBrokerDecision` field set remains a strict superset
   of 108A's original fields; zero-arg `PermissionBroker()` construction
   and the 12-rule default registry are unchanged.

## Broker Isolation Result

**Confirmed clean.** The module's only imports are `__future__`, `uuid`,
`dataclasses`, `datetime` (verified via AST parsing, not string search).
No `subprocess`, no `os`, no `shell_gate`, no `backend_invocations` /
`backend_cli` / `agent_backends` / `agent_invoke`, no `adapter`, no
`notification`/`telegram` substring anywhere in the import list.

**New finding, directly tested:** `src/pcae/commands/commit.py`,
`push.py`, `task.py`, `phase.py`, and `src/pcae/cli.py` were inspected by
source and confirmed to contain **no reference at all** to
`permission_broker_foundation` or `PermissionBroker(`. The broker is not
imported by, called from, or otherwise wired into any real command path
today — this was previously established informally during the pre-108D
repository protection inspection; this phase makes it a permanent,
automatically-checked test rather than a one-time manual finding.

Every decision path was re-confirmed to have zero side effects (no files
created in an isolated `tmp_path` across eight representative scenarios),
and `ALLOW` was re-confirmed to always carry
`implementation_status="execution_unavailable"`.

## Compatibility with Autonomy Contract and No-Go Gates

**Confirmed compatible.** Every `NG-` ID the broker's default rules can
produce across eight triggering scenarios was checked to be a subset of
the 25 `NG-NNN` IDs actually present in
`docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` today. Every `INV-` ID
likewise checked against the 10 `INV-NNN` IDs in
`docs/V0_2_AUTONOMY_CONTRACT.md`. All 10 `COMP-NNN` IDs frozen in 108A
were confirmed to actually appear in the autonomy contract document they
were additively cross-referenced into, and the no-go gate index table was
confirmed to still carry its `Component ID` column.

**Component ID status:** `COMP-001`–`COMP-010` are already canonical
(frozen in 108A) — this phase did not need to invent new component
mapping. What remains explicitly *not* implemented, and not fabricated by
this phase: the six stub policies (`POL-002`, `POL-008`–`POL-012`) never
trigger, and therefore never assert a `matched_component_ids` value —
verified directly. When a stub eventually gains real logic in a future
phase, it will need to declare its own component mapping at that time;
this phase does not guess one on its behalf.

## Decision Composition Behavior

Re-verified against the real 12-rule `DEFAULT_POLICY_RULES` registry (not
only 108C's synthetic test rules):

- **Multi-cause DENY**: `task_id=None` + unknown `action_type` + unknown
  `requested_component` simultaneously triggers `POL-001`, `POL-006`, and
  `POL-007` together; `causing_policy_ids` and `reason_chain` both list
  all three.
- **Multi-cause HUMAN_REVIEW**: two custom `HUMAN_REVIEW`-triggering
  rules both contribute; `requires_human` remains `True`.
- **DENY precedence over HUMAN_REVIEW**: confirmed again with the real
  registry (`evidence_available=False, approval_present=False` →
  `POL-003` DENY wins over `POL-004` HUMAN_REVIEW).
- **Order-preserving dedup**: `POL-005` and `POL-007` both map to
  `NG-025`/`INV-001`/`COMP-002`; triggering both simultaneously confirms
  each ID appears exactly once in the aggregated output, not duplicated.
- **Explainability fields**: `causing_policy_ids`, `reason_chain` (whose
  policy-id sequence matches `causing_policy_ids` exactly), and
  `precedence_reason` (distinct text per outcome category) all directly
  tested.
- **Remediation preservation**: a two-cause DENY carries at least two
  remediation entries, one per contributing rule.
- **Every fail-closed path**: malformed policy result, a raising policy
  rule, an empty registry, an unknown action, missing evidence, and
  policy ambiguity (unrecognized action/execution class, routed through
  `POL-006`/`NG-024`) were each independently re-confirmed to resolve to
  `DENY`.

## Fail-Closed Compatibility

No fail-closed behavior changed. This phase's tests exist to *prove* the
108C fail-closed guarantees hold under the real default registry and
under fresh test doubles, not to introduce new fail-closed paths. Every
default rule capable of triggering was confirmed to resolve only to
`DENY` or `HUMAN_REVIEW` — never `ALLOW` — across seven independent
triggering scenarios, directly falsifying any accidental fail-open
regression.

## What Remains Intentionally Not Implemented

Everything already true after 108C, unchanged by this phase: real
execution boundary (`COMP-002`), human approval gate enforcement
(`COMP-003`), shell/backend/adapter boundaries (`COMP-004`–`COMP-006`),
audit persistence (`COMP-007`), rollback readiness boundary (`COMP-008`),
emergency stop (`COMP-009`), execution enablement (`COMP-010`). The six
stub policies (`POL-002`, `POL-008`–`POL-012`) remain registered
placeholders with no real logic. The broker itself remains completely
unwired from every real command path — this phase makes that fact
permanently testable rather than changing it.

## Repository Protection Inspection Context

A read-only repository protection inspection was performed immediately
before this phase (no files modified, nothing committed). It found the
repository's branch protection, CODEOWNERS, PR template, and CI workflow
configuration to be transitional but safe to proceed on: `enforce_admins`
is `false` (documented, intentional, already used throughout this
project's governed lifecycle every phase), no required CI status checks
are wired to branch protection yet, and `.githooks/pre-commit` is
opt-in per clone via a manual `pcae hooks install` step rather than
auto-installed by `pcae init`. None of these gaps block 108D, because
108D is broker verification only and does not touch branch protection,
hooks, or CI configuration — per this phase's explicit boundary, none of
those areas were modified here either. The recommended remediation
(pre-push hook, hook auto-install) is scoped to Phase 108E, not this one.

## Recommended Next Phase

**108E — Local Hook / Pre-Push Governance Hardening.**
