# Phase 109A — Permission Broker Command-Path Integration Design

## Purpose

Design the first command-path integration architecture for the
Permission Broker while preserving PCAE's current non-executing
guarantees — the canonical flow, command categories, integration points,
and broker interaction contract that any future integration must satisfy,
before any actual command path is connected to the broker.

## Scope

Architecture/design only. Produces
`docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md` (the frozen
design document) and `tests/test_permission_broker_command_path_design.py`.
Builds on `docs/V0_2_AUTONOMY_CONTRACT.md` (107B), `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md`
(107C), `docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md` (107E),
and the frozen Permission Broker foundation/policy framework/hardening
(108A–108C) plus its confirmed isolation from every real command path
(108D). No source code in `src/pcae/` is touched by this phase — its task
contract does not include the `core`, `commands`, or `cli` zones,
structurally enforcing that boundary the same way 108D's did.

## Non-Goals

No broker command-path integration; no runtime execution; no shell
mediation; no subprocess mediation; no backend invocation; no adapter
invocation; no execution enablement; no execution capability; no audit
persistence; no rollback execution; no emergency stop; no Telegram
inbound; no automatic apply; no command execution; no Permission Broker
enforcement; no shell boundary implementation; no backend boundary
implementation. `v0.1.0-rc1` remains non-executing by design; v0.2
remains the autonomy target (Level 3, not Level 4/5). No change to
`v0.1.0-rc1`, its GitHub Release, or branch protection on `main`. No new
tag. No new release. No package publication.

## What Was Frozen

`docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md` freezes:

- **The canonical command-path integration architecture**: an eight-stage
  flow (AI Agent → Permission Broker → Command Boundary → Execution
  Boundary → Human Approval Gate → Shell/Backend/Adapter Boundary → Audit
  Boundary → Rollback Boundary), with "Command Boundary" explicitly
  named as a design pattern every integration point follows independently
  — not a new `COMP-NNN` component, deliberately not invented by this
  phase.
- **Eleven canonical command categories** (Read-only, Repository
  inspection, Documentation mutation, Source mutation, Test execution,
  Git lifecycle, shell execution as a Git-lifecycle-adjacent high-risk
  category, Backend invocation, Adapter invocation, Network, High-risk),
  each with examples, risk level, broker involvement (today and future),
  future approval requirement, and current implementation status — most
  candidly stating that shell-class actions an AI agent's own tooling
  issues are entirely unmediated by any PCAE component today.
- **Seven integration points** (`pcae commit implementation`, `pcae
  push`, shell mediation, subprocess mediation, backend invocation,
  adapter invocation, a future unified execution API), each with current
  status, future integration description, and rationale — none
  connected.
- **The broker interaction contract**: input/output (the existing,
  unmodified `PermissionBrokerRequest`/`PermissionBrokerDecision`
  models), decision lifecycle (mapped onto 107B's canonical execution
  lifecycle transitions), required metadata, policy evaluation order
  (unchanged from 108B/C), failure behavior (fail-closed, mirroring
  108C's internal `_sanitize_result` discipline), and audit expectations
  (no integration point may persist its own ad hoc audit trail —
  exclusively `COMP-007`'s future responsibility).
- **The canonical execution pipeline**, restated as the authoritative,
  no-boundary-skipped sequence, with every stage's current status
  (`foundation_implemented` for the Permission Broker only;
  `not_implemented` for every stage after it).
- **Design compatibility** with the Autonomy Contract, No-Go Gates,
  Local Governance (108E), Branch Protection (106M/107E), and existing
  lifecycle commands — demonstrating no invariant, gate, hook, or
  protection setting is altered or contradicted.
- **Repository protection implications**: how command-path integration
  would strengthen protection (closing the shell-mediation gap), how it
  differs from hooks (in-process vs. local/bypassable) and from branch
  protection (broader surface, not GitHub-server-side, not merge-scoped),
  and why it remains fail-closed (the broker's own existing guarantees,
  unweakened by being wired in).

## Relationship to 107A–107E and 108A–108E

107A–107E froze the v0.2 roadmap, autonomy contract, no-go gates,
parallel-validation infrastructure, and PR-compatible governed workflow.
108A–108D built, hardened, and verified the Permission Broker itself as
an isolated, evaluate-only policy kernel, confirming it is wired into
nothing. 108E hardened local governance bootstrap (hooks) as a
complementary, non-broker protection layer. 109A takes the next necessary
step before any real integration begins: designing, in one canonical
document, exactly how a future integration would connect to the broker —
without connecting anything yet — so that 109B (the first prototype) has
an unambiguous, already-frozen architecture to build against, the same
role 107C's no-go gates played for 108A's foundation and 107E's workflow
design played for 108's whole broker arc.

## Validation

`tests/test_permission_broker_command_path_design.py` (new) verifies:
both design documents exist; all eleven command categories are defined
with their required fields; the execution pipeline is defined and
ordered correctly; all seven integration points are documented; the
broker interaction contract section covers input, output, decision
lifecycle, required metadata, policy evaluation order, failure behavior,
and audit expectations; the compatibility section addresses all five
named areas; the repository protection implications section addresses
all four required questions; neither document claims execution
capability, command-path integration, or implementation exists; and both
documents recommend **109B — First Command-Path Integration Prototype
(Disabled by Default)** as the next phase.

All test groups were run with `-n auto`, continuing the parallel-
validation posture hardened in 107D. No group required a sequential
fallback; no new xdist collision was introduced or observed.

## No-Go Confirmations

No broker command-path integration. No runtime execution. No shell
mediation. No subprocess mediation. No backend invocation. No adapter
invocation. No execution enablement. No execution capability. No audit
persistence. No rollback execution. No emergency stop. No Telegram
inbound. No automatic apply. No command execution. No Permission Broker
enforcement. No shell boundary implementation. No backend boundary
implementation. No no-go gate runtime enforcement. No commit/push
authorization changes beyond the existing governed lifecycle. No real AI
backend calls. `v0.1.0-rc1` remains non-executing by design. v0.2 remains
the autonomy target (Level 3, not Level 4/5). GitHub Release for
`v0.1.0-rc1` and branch protection on `main` are unchanged. No new tag.
No new GitHub Release. No PyPI/GitHub Packages publication.

## Recommended Next Phase

**109B — First Command-Path Integration Prototype (Disabled by
Default).**
