# Phase 149O.20L.7O.2U Complete — PCAE v0.3 Release Execution Plan and Critical-Path Freeze

Converted the reconciled Phase 149O.20L.7O.2P v0.3 strategy into a
concrete, short, execution-oriented release plan, per the
149O.20L.7O.2U governed handoff.

**Release baseline**: reconstructed the actual v0.1.0-rc1 (pre-release,
published 2026-07-02) and v0.2.0 (full release, published 2026-07-07)
GitHub release metadata directly via `gh release view`/`gh release
list`/`git tag -l` — not inferred from historical phase prose. Exactly
two tags exist.

**Strategy reuse**: read `docs/PHASE_149O_20L_7O_2P_V0_3_RELEASE_
STRATEGY_AND_CAPABILITY_PRIORITIZATION_REASSESSMENT.md` directly
(confirmed unmodified since authoring, `git log --follow` shows one
commit) and reused its v0.3 headline, primary target user, and
HATP/WebAuthn Enterprise-Extension classification unchanged — current
evidence (live `pcae runtime inspect --json`, `pcae health`, README/CLI
inspection) does not invalidate any of it.

**Capability matrix**: classified current PCAE capability areas as
Released/user-usable (governance kernel, task lifecycle, commit/push
governance, repository intelligence, read-only project-intelligence
stack), architecture-only (Permission Broker, plugin/runtime adapter
model), or Enterprise extension/Deferred (HATP, HMIC, FIDO2, remote
WebAuthn, deployment governance) — live-verified against `pcae runtime
inspect --json` (`Observed` / `execution_unavailable` / `observe` / 0
plugins, unchanged since v0.2.0).

**Execution gap (central finding)**: the 69A–69O approval/audit/
execution-activation/promotion/rollback chain is fully implemented and
human-gated (`pcae promote`/`pcae rollback` are the only two commands
that mutate root, both gated on prior reviewed evidence), but nothing
external currently feeds it a real proposed change from an actual
running AI coding agent. Closing this gap with a narrowly-scoped
reference intake adapter — reusing, not expanding, the existing
promotion/rollback authority — is identified as the top release
blocker, not new autonomy or a weakened safety boundary.

**Release plan frozen**: 3 release blockers (reference intake path,
deny/allow demo, curated onboarding), non-blocking debt, release
acceptance criteria and non-goals, a critical-path DAG, and the next 5
governed phases (149O.20L.7O.2U.1 Reference Adapter Contract Freeze
through 2U.5 Release-Candidate Preparation), applying this repository's
own phase-count-discipline exception (separate phases only for a
materially different authority boundary or a deployment-effect phase).

**Human decisions surfaced, not silently frozen**: (1) which external
agent/tool the reference adapter targets first; (2) confirmation of
`v0.3.0-rc1` as the next release-candidate tag name (the only
applicable precedent in this repo's own release history).

An 8-test suite mechanically verifies the plan's grounding facts: the
exact tag set, the plan document's existence/substance, the 2P strategy
document's integrity, and that no production code or HATP/WebAuthn/FIDO2
file was touched this phase: 8 passed, 0 failed.

No production code (`src/pcae/**`) was modified this phase. No
execution capability was enabled. No release or tag was created. No
HATP/FIDO2/WebAuthn work was performed. No Git history rewritten; no
force push; no raw `git push`.

Full text:
`docs/PHASE_149O_20L_7O_2U_V0_3_RELEASE_EXECUTION_PLAN_AND_CRITICAL_PATH_FREEZE.md`.

Recommended next: 149O.20L.7O.2U.1 — Reference Adapter Contract Freeze,
pending human confirmation of which external agent/tool the reference
adapter targets first.
