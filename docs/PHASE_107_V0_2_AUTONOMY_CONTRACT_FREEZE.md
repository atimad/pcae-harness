# Phase 107B — v0.2 Autonomy Contract Freeze

## Purpose

Freeze the v0.2 autonomy contract — the Level 3 target, ten
architectural invariants, the canonical execution lifecycle, and the
per-component purpose/responsibilities/current-status breakdown — before
any enforcement or execution implementation begins in Phase 108A.

## Scope

Contract/freeze only. Produces
`docs/V0_2_AUTONOMY_CONTRACT.md` (the frozen contract) and
`tests/test_v0_2_autonomy_contract.py` (tests verifying the contract's
required content). Builds directly on Phase 107A's
`docs/V0_2_AUTONOMY_ROADMAP.md` and
`docs/PHASE_107_V0_2_EXECUTION_CAPABILITY_GAP_ANALYSIS.md`, and on the
existing frozen `docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md`
(Phase 104B). No product/runtime behavior is implemented or changed in
this phase.

## Non-Goals

No runtime enforcement; no autonomous execution; no shell mediation; no
subprocess mediation; no backend invocation; no adapter execution; no
Telegram inbound; no durable audit storage; no rollback execution; no
emergency stop implementation; no execution enablement flag/toggle; no
automatic apply; no patch execution. No network calls outside the
existing Telegram outbound path and ordinary git remote/GitHub
verification used by the governed lifecycle itself. No change to
`v0.1.0-rc1`, its GitHub Release, or branch protection on `main`. No new
tag. No new release. No package publication.

## What Was Frozen

`docs/V0_2_AUTONOMY_CONTRACT.md` freezes:

- **v0.2 autonomy target:** Level 3 — Governed Human-Approved Bounded
  Execution. v0.1 remains Level 0 / non-executing. Execution remains
  unavailable now.
- **Ten architectural invariants** (INV-001 through INV-010), most
  notably INV-008 ("execution capability does not imply execution
  authorization"), which governs every subsequent design/implementation
  phase.
- **The canonical execution lifecycle**: `PLANNED -> READY ->
  AWAITING_HUMAN_APPROVAL -> AUTHORIZED -> EXECUTING -> {COMPLETED |
  FAILED | ABORTED}`.
- **Twelve components**, each with Purpose / Responsibilities / Current
  Status: Permission Broker, Execution Boundary, Human Approval Gate,
  Shell/Subprocess/Network Boundary, Backend Invocation Boundary,
  Adapter Invocation Boundary, Audit Boundary, Rollback Readiness
  Boundary, Emergency Stop Boundary, Execution Enablement Model, No-Go
  Registry, PR/Branch Protection Workflow. Every component not already
  implemented is explicitly marked "Not implemented" with a pointer to
  the future phase responsible for it.
- **Hard no-go conditions**, deferring to and not duplicating
  `docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md` and
  `docs/V0_2_AUTONOMY_ROADMAP.md`.
- **Branch-protected `main` / PR workflow implications**, explicitly
  assigning the `enforce_admins: true`-readiness design to Phase 107D.
- **Explicit out-of-scope items** for this contract and this phase.

## Relationship to 107A

107A produced the roadmap and gap analysis (what's missing, in what
order). 107B does not repeat that analysis — it freezes the specific
contractual commitments (invariants, lifecycle, component
responsibilities) that 107A's roadmap referenced but did not itself fix
as binding. Future implementation phases (108A onward) must satisfy this
contract; they may not silently reinterpret the Level 3 target, the
invariants, or the lifecycle without a dedicated contract-amendment
phase.

## No-Go Confirmations

No runtime enforcement. No autonomous execution. No real backend
invocation. No adapter execution. No subprocess execution beyond
existing lifecycle/test/docs/git-remote-verification command behavior.
No shell execution beyond that same boundary. No network calls outside
the existing Telegram outbound path and ordinary git remote/GitHub
verification. No shell interception. No Telegram inbound. No Telegram
polling. No remote shell. No `/run`. No automatic apply. No apply
execution. No patch parsing for execution. No commit/push authorization
changes beyond the existing governed lifecycle and the already-applied
GitHub branch protection. No real AI backend calls. No executable
artifact-only invocation path. No execution enablement flag or toggle.
No cryptographic signing. No remote attestation. No database-backed
audit storage. No shell mediation. No rollback execution. No file
mutation rollback. No automatic restore. No git reset/checkout/revert
execution. No new tag created. No final `v0.1.0` tag. No new GitHub
Release. No PyPI publication. No GitHub Packages publication.
`.pcae-local/` remains ignored. Telegram outbound-only. Execution
unavailable. All authorization flags remain `False`. All safety flags
(`simulation_only`, `no_execution`, `evidence_only`, `non_authorizing`,
`design_only`) remain `True` where applicable. `v0.1.0-rc1` remains
non-executing by design. v0.2 remains the autonomy target (Level 3, not
Level 4/5). Branch protection on `main` unchanged.

## Recommended Next Phase

107C — Execution Readiness No-Go Gate Freeze.
