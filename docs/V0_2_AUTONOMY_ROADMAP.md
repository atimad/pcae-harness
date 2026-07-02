# PCAE v0.2 Autonomy Roadmap

## Purpose

Start the v0.2 autonomy track by defining, in one place, what "full
autonomy" means for PCAE, what autonomy level v0.2 should realistically
target, and the staged phase sequence required to get there safely. This
document is **roadmap/gap-analysis only** — it implements no runtime
enforcement, no autonomous execution, no execution capability of any
kind. Execution remains unavailable in every code path after this
document is written.

## Release Target

**PCAE v0.2 — Governed Human-Approved Bounded Execution.**

This is the recommended v0.2 target (see "Autonomy Levels" below for the
justification). v0.2 does **not** target unrestricted, broad, or
multi-agent autonomous execution. It targets the narrowest execution
capability that is still meaningfully "autonomy": a single, mediated,
human-approved execution path with a hard-stop and full audit trail —
not a general-purpose autonomous agent runtime.

## Autonomy Definition

For PCAE, "autonomy" means: **an AI agent's proposed action can result in
a real, mediated side effect (shell command, backend call, adapter
invocation, file mutation) without a human manually running that action
themselves outside of PCAE.** Autonomy is not binary — it is a spectrum
of how much mediation, approval, and reversibility sits between "the
agent proposed this" and "this actually happened." PCAE's governance
model (task contracts, no-go registry, report trust, shared safety/
authorization contract) already exists at v0.1; what's missing for
autonomy is the actual *execution boundary* those governance artifacts
would gate.

## Autonomy Levels

| Level | Name | Description | PCAE Status |
|---|---|---|---|
| **0** | Governed non-executing lifecycle harness | Governance, evidence, and design artifacts exist; no code path executes agent-authored commands or invokes a real backend. All authorization flags `False`. | **v0.1 (current, `v0.1.0-rc1`)** |
| **1** | Execution-ready planning with hard no-execution gates | Planning/preflight artifacts model what execution *would* look like (inputs, contracts, evidence) but a hard gate — not just an unset flag — prevents any of it from running. | Largely present already (permission broker prototype, shell gate prototype, evidence bundle, decision engine, coordinator — all evidence-only) |
| **2** | Governed dry-run action proposals | A proposed action is fully modeled, validated against the no-go registry and permission broker decision, and produced as a dry-run artifact — still never actually run. | Partially present (`gate-dry-run`, `governed-execution-dry-run`, `write-preflight-dry-run` families) |
| **3** | Human-approved bounded execution | A human explicitly approves a specific, narrow, mediated action; PCAE executes it through a governed boundary (shell/backend/adapter mediation), audits it, and can roll it back. | **Recommended v0.2 target — does not exist yet** |
| **4** | Policy-brokered autonomous execution in narrow scope | The permission broker can approve/deny certain narrow action classes without a human in the loop for every single action, within a pre-approved policy envelope. | Future (v0.3+); requires Level 3 to be proven safe and audited first |
| **5** | Broader multi-agent autonomous execution | Multiple agents coordinate and execute with reduced per-action human oversight, under strong policy and audit guarantees. | Not planned; far future, requires Level 4 maturity and explicit organizational risk acceptance |

**Explicit statements:**

- **v0.1 is Level 0.** No execution capability exists in `v0.1.0-rc1`.
- **v0.2's target should be Level 3, not Level 5.** Jumping directly to
  broad autonomous execution from a non-executing harness is the single
  biggest risk this roadmap exists to prevent.
- **Full autonomy must be staged.** Each level requires the previous
  level's safety mechanisms to be implemented, tested, and proven before
  the next level is attempted. This document's staged roadmap exists
  specifically so that "full autonomy" is never treated as a single leap.

## v0.1 Baseline: Inherited Capabilities

The following already exist, are tested, and are part of the stable
foundation v0.2 builds on top of — see
`docs/PHASE_107_V0_2_EXECUTION_CAPABILITY_GAP_ANALYSIS.md` for the full
enumeration with evidence pointers:

- Governed task/phase lifecycle (`pcae task`, `pcae phase`).
- Report-trust validator and report-trust hard-fail gates (105A–105D,
  106H trust-gate asymmetry repair).
- `pcae phase-report trust` / `pcae phase-report show --trust` CLI.
- Task-finish report/notification integration (Telegram outbound only).
- The v0.1 golden workflow (`docs/V0_1_GOLDEN_WORKFLOW.md`).
- Packaging/install smoke validation (sdist/wheel build + throwaway-venv
  install).
- GitHub Release publication for `v0.1.0-rc1` (prerelease, sdist+wheel
  attached, checksums verified — 106L).
- GitHub branch protection and PR-first contributor documentation on
  `main` (106M): 1 required approving review, stale-review dismissal,
  force-push/deletion blocked, conversation resolution required, admin
  enforcement off transitionally.
- The runtime-enforcement no-go registry
  (`docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md`, 17 frozen entries,
  RE-NOGO-001 through RE-NOGO-017).
- The shared safety/authorization contract (12 authorization flags, all
  `False`; 5 safety flags, all `True` — `simulation_only`, `no_execution`,
  `evidence_only`, `non_authorizing`, `design_only`).
- Evidence-only runtime-readiness artifacts: permission broker prototype
  (87–91), shell gate prototype (87–95), evidence bundle (101),
  decision engine (102), coordinator (103) — all design/evidence-only,
  `execution_allowed=False` throughout.
- Telegram outbound notification (loaded, configured, enabled;
  categorically no inbound handler exists anywhere in
  `core/notifications.py`).
- `fast_green` 4390/4390 fully green baseline.
- Clean `pcae_doctor_task_memory` and `pcae_push_check`.
- `v0.1.0-rc1` tag (created 106F, unchanged since).
- The post-RC audit/repair/verification cycle (106G/106H/106I) that
  already found and fixed one real cross-command trust-gate bug before
  it reached a release.
- The v0.1 effectiveness evaluation framework (106K) — a scoring rubric
  PCAE can eventually apply to its own v0.2 execution quality.

## v0.2 Goals

1. Define a single, narrow, human-approved execution path (Level 3) with
   a real permission broker enforcement decision (allow / deny /
   human_review), not just a design artifact.
2. Mediate every consequential action (shell/subprocess, backend,
   adapter) through that one boundary — no raw, unmediated execution
   path anywhere in the governed flow.
3. Require durable, persisted audit records for every mediated action
   (not just in-memory or Markdown-report evidence).
4. Require rollback readiness to exist *before* any mutation is allowed,
   and an emergency stop/abort mechanism that works even mid-action.
5. Keep the execution enablement flag/toggle off by default, with
   explicit, documented, reversible operator opt-in.
6. Preserve every v0.1 governance guarantee (task scope, report trust,
   no-go registry, shared safety/authorization contract) unchanged and
   unweakened.
7. Make the contribution workflow (branch-protected `main`, PR-first)
   compatible with v0.2 development from the start, not retrofitted
   later.

## v0.2 Non-Goals

- Full/broad autonomous execution (Level 4/5) — explicitly out of scope
  for v0.2.
- Telegram inbound / polling / remote command reception — out of scope
  unless a dedicated, separately-gated future phase adds it (see
  RE-NOGO-013).
- Multi-agent autonomous orchestration execution — out of scope; the
  coordinator/decision-engine design artifacts remain evidence-only
  until Level 3 is proven.
- Cryptographic signing / remote attestation / database-backed audit
  storage as hard requirements — durable audit persistence does not
  require a database; a structured, append-only, tamper-evident local
  store may suffice for v0.2 (to be decided in 107B/112A).
- Removing or weakening any v0.1 non-executing guarantee.
- Publishing to PyPI or GitHub Packages (unrelated to autonomy; out of
  scope for this track).

## Required Execution Capabilities (Not Yet Implemented)

See the gap analysis for full detail; summarized here:

1. Permission broker **enforcement** (not just simulation/prototype).
2. Shell/subprocess/network mediation — the actual gate, not just the
   narrow shell gate prototype's evidence model.
3. Backend invocation boundary (real AI backend calls, mediated).
4. Adapter invocation boundary (mediated adapter execution).
5. Human approval enforcement (a real gate a human must clear, not an
   advisory flag).
6. Durable audit persistence (survives process restart, is queryable).
7. Rollback execution governance (a real rollback path, not just
   rollback *design*).
8. Emergency stop / abort boundary.
9. Execution sandboxing model (what environment does a mediated action
   actually run in).
10. Output capture/redaction (secrets don't leak into audit records or
    Telegram).
11. Execution enablement flag/toggle — designed explicitly, default off.

## Required Governance Capabilities Already Present (No New Work)

- Task/phase contract scoping and `pcae check` zone/file enforcement.
- Report-trust hard-fail gates.
- The no-go registry as the canonical reference for blocking conditions.
- The shared safety/authorization contract (flags, not yet backed by
  enforcement).
- GitHub-level branch protection on `main`.

## Required Contribution/PR Workflow Adaptations

v0.2 implementation work happens under the same branch-protected `main`
established in 106M:

- Every v0.2 implementation phase (108A onward) must go through the
  governed PCAE lifecycle exactly as v0.1 phases did; `main` remains
  admin-bypassable for the repo owner during the transitional period, but
  the roadmap should not assume that remains true forever.
- **107D** (see staged roadmap below) is dedicated to designing a
  PR-compatible governed development workflow — i.e., what happens to
  `pcae commit implementation` / `pcae task finish --commit` / `pcae
  push` once `enforce_admins: true` is turned on and even the repo owner
  must go through a pull request. This must be solved *before* v0.2
  execution-capability implementation phases begin, not discovered
  midway through 108A.
- No v0.2 phase may bypass branch protection, force-push, or use
  `--no-verify` to work around it.

## Staged Roadmap

See "Recommended Phase Sequence" below for the full list. At a high
level, v0.2 proceeds in four stages:

1. **Contract/design freeze** (107B, 107C, 107D) — freeze what v0.2
   means, freeze the no-go gate model, and design the PR-compatible
   workflow, before any enforcement code exists.
2. **Permission broker enforcement** (108A–108C) — the first real
   enforcement implementation, since every other execution boundary
   depends on it deciding allow/deny/human_review.
3. **Mediation boundaries** (109A–110B) — shell/subprocess mediation,
   then backend invocation, then adapter invocation, each disabled by
   default and gated behind the broker.
4. **Human approval, audit, rollback, emergency stop, and the first
   demo** (111A–115A) — the remaining Level 3 requirements, culminating
   in a single, narrow, human-approved bounded execution demo — not a
   general capability rollout.

## Safety Prerequisites

Before *any* phase in stage 2 (108A) begins:

- 107B (contract freeze) and 107C (no-go gate freeze) must be complete.
- `fast_green` must remain 4390/4390 with no new failures introduced by
  107A/107B/107C's own documentation/test changes.
- The existing no-go registry (RE-NOGO-001 through RE-NOGO-017) must
  remain frozen and referenced, not silently reinterpreted.

Before *any* phase in stage 3 (109A) begins:

- 108A–108C (permission broker enforcement + freeze + hardening) must be
  complete and tested.
- The broker must be able to return `allow` / `deny` / `human_review` for
  realistic inputs, not just simulated fixtures.

Before *any* phase in stage 4 (111A) begins:

- 109A–110B (shell/subprocess + backend + adapter mediation, all
  disabled by default) must be complete and tested.

Before **115A** (the first human-approved bounded execution demo):

- All hard no-go conditions below must be true.

## Hard No-Go Conditions

Execution must remain unavailable until **all** of the following are
true:

1. v0.2 contract frozen (107B).
2. No-go gates frozen (107C).
3. Permission broker enforcement implemented and tested (108A–108C).
4. Shell/backend/adapter boundaries implemented and tested (109A–110B).
5. Human approval enforcement implemented (111A).
6. Audit persistence implemented (112A).
7. Rollback readiness implemented (113A).
8. Emergency stop implemented (114A).
9. Execution enablement flag designed, default off.
10. Dry-run and simulation tests pass.
11. Explicit operator approval exists (a human, not an inferred signal).
12. Release docs state scope and risk plainly — no overclaiming.
13. No hidden fast-green failures.
14. `pcae_check` / `pcae_push_check` / `pcae_doctor_task_memory` all
    clean.
15. Report-trust gates pass.
16. No raw shell bypass path exists anywhere in the PCAE execution flow.
17. The protected-`main`/PR workflow impact on v0.2 development itself is
    understood and documented (107D).

These conditions mirror and extend the existing no-go registry
(`docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md`); they do not replace it.

## Validation Strategy

- Every v0.2 implementation phase adds focused tests for the capability
  it introduces, plus regression runs against the existing fast_green
  suite (4390/4390 must remain the floor, not a ceiling that's allowed to
  regress).
- Enforcement-boundary phases (108A onward) require both unit tests and
  live-CLI verification (the same "not just unit tests" standard 106I
  established for the trust-gate repair) before being considered
  contract-frozen.
- No phase may mark an execution boundary "implemented" while its
  `execution_allowed` flag is anything other than explicitly, narrowly
  `True` under full test coverage — the default for every new capability
  is off.

## Release Criteria (v0.2)

v0.2 may only be tagged/released when:

- All hard no-go conditions above are satisfied.
- The single, narrow, human-approved bounded execution path (Level 3) has
  been demonstrated end-to-end (115A) with a human approving a real,
  narrow, reversible action.
- Every v0.1 guarantee is intact and re-verified (fast_green, report
  trust, no-go registry, shared safety contract, branch protection,
  GitHub Release for `v0.1.0-rc1` unchanged).
- The v0.2 release notes state scope and residual risk as plainly as
  `docs/RELEASE_NOTES_V0_1_RC1.md` did for v0.1 — no overclaiming of
  autonomy beyond what was actually implemented and tested.

## Recommended Phase Sequence

| Phase | Name | Stage |
|---|---|---|
| 107A | v0.2 Full Autonomy Roadmap / Execution Capability Gap Analysis | **This phase — roadmap/gap-analysis only** |
| 107B | v0.2 Autonomy Contract Freeze | Contract/design freeze |
| 107C | Execution Readiness No-Go Gate Freeze | Contract/design freeze |
| 107D | PR-Compatible Governed Development Workflow Design | Contract/design freeze |
| 108A | Permission Broker Enforcement Implementation | Permission broker |
| 108B | Permission Broker Enforcement Contract Freeze | Permission broker |
| 108C | Permission Broker Enforcement Hardening | Permission broker |
| 109A | Shell/Subprocess Mediation Design | Mediation boundaries |
| 109B | Shell/Subprocess Mediation Prototype, disabled by default | Mediation boundaries |
| 109C | Shell/Subprocess Mediation Hardening | Mediation boundaries |
| 110A | Backend Invocation Boundary Implementation, disabled by default | Mediation boundaries |
| 110B | Adapter Invocation Boundary Implementation, disabled by default | Mediation boundaries |
| 111A | Human Approval Enforcement Gate | Approval/audit/rollback/stop |
| 112A | Durable Audit Store | Approval/audit/rollback/stop |
| 113A | Rollback Execution Governance Design | Approval/audit/rollback/stop |
| 114A | Emergency Stop / Abort Boundary | Approval/audit/rollback/stop |
| 115A | First Human-Approved Bounded Execution Demo | First demo |

**The first phases after 107A are contract/freeze/design phases, not
execution implementation.** No phase before 108A introduces any code
path capable of running agent-authored commands or invoking a real
backend.

## Recommended Next Phase

**107B — v0.2 Autonomy Contract Freeze.** After roadmap/gap analysis,
freeze the v0.2 autonomy contract (the Level 3 target, the non-goals, and
the hard no-go conditions defined in this document) before implementing
any enforcement or execution capability.
