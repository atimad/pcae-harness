# TODO

**Source of truth:** `PROJECT_STATUS.md`'s `## Current Phase` section is
authoritative for "what phase are we on" and "what phase is recommended
next" — never this file. `docs/ROADMAP.md` is the canonical long-term
roadmap and product-direction document. This file is planning scratch
space only: useful for browsing upcoming/candidate work, but never a
source a session should trust over `PROJECT_STATUS.md` if the two
disagree. See the full source-of-truth precedence order and the stale
90-series finding this file previously had in
[docs/PHASE_112_PLANNING_BOOTSTRAP_CONSISTENCY_HARDENING.md](../docs/PHASE_112_PLANNING_BOOTSTRAP_CONSISTENCY_HARDENING.md)
(Phase 112B.1).

## Current Roadmap (112-series — Runtime Context track)

Per `PROJECT_STATUS.md`. Only the phase explicitly named "Recommended
next repo phase" there is confirmed; everything after it is a tentative
candidate, not a committed queue — no phase activation is inferred
ahead of an explicit human decision (`tasks/DECISIONS.md`).

| Phase | Name | Status |
|-------|------|--------|
| 112A | Runtime Context Architecture | ✅ Complete |
| 112B | Runtime Context Contract Freeze | ✅ Complete |
| 112B.1 | Planning & Bootstrap Consistency Hardening | ✅ Complete |
| 112C | Runtime Context Prototype (Observation-Only) | 🔜 Next (per PROJECT_STATUS.md) |
| 112D | Runtime Context Verification & Compatibility | Tentative — candidate only, mirroring the 110C→110D/111A→111B "design → contract → prototype → verification" pattern; confirm scope once 112C lands |
| 112E | Runtime Context Inspect Integration | Tentative — candidate only, if still appropriate once 112C/112D outcomes are known |
| 113A | Advisory Runtime Architecture (or the then-current preferred next major track) | Not yet planned |

## Historical: Production v1 Path (90-series, superseded)

**Historical reference only — this table does not reflect current
work.** It predates the 107–112-series arc (autonomy/no-go →
Permission Broker → observation integrations → Runtime Registry →
Runtime Introspection → Runtime Context) and was left presented as
current in this file long after it was superseded, which is the stale
planning artifact 112B.1 repaired. Kept here, clearly marked, only
because some of its listed phases may still represent real, unstarted
future work once the current 112-series track concludes — not because
90C is upcoming.

| Phase | Name | Status |
|-------|------|--------|
| 90A | Permission Broker Enforcement Boundary Design | ✅ Complete |
| 90B | Full-Suite Baseline Inspection and Repair | ✅ Complete |
| 90B.1 | Roadmap Coherence and Production v1 Plan | ✅ Complete |
| 90C | Permission Broker Enforcement Boundary Test Plan | Historical — not current; re-evaluate scope before resuming |
| 91A | Permission Broker Simulation Prototype | Historical — not current |
| 91B | Broker CLI and Decision Explanation | Historical — not current |
| 91C | Hard-Block Policy Readiness | Historical — not current |
| 92A | Phase Report Artifact Model | ✅ Complete (superseded by later phase-report work; verify against `docs/ROADMAP.md`) |
| 92B | Pluggable Notification Foundation | ✅ Complete (superseded; verify against `docs/ROADMAP.md`) |
| 92C | Telegram Outbound Phase Report Delivery | ✅ Complete (superseded; verify against `docs/ROADMAP.md`) |
| 92D | Automatic Phase-Finalization Notification Hook | ✅ Complete (superseded; verify against `docs/ROADMAP.md`) |
| 93A | Narrow Shell Gate Design | Historical — not current |
| 93B | Narrow Shell Gate Prototype | Historical — not current |
| 94A | Governed Backend Invocation Design | Historical — not current |
| 95A | Production v1 Documentation / Install / Demo | Historical — not current |
| 96A | Production v1 Governance Review | Historical — not current |

## Future v2 / Pluggability

- Notification adapters (Slack, email, webhook, custom)
- Backend adapters (OpenAI, local models, custom)
- Policy modules (per-repo, per-org, per-workflow)
- Audit storage adapters (remote DB, cloud storage)
- Multi-agent orchestration plugins
- Mobile/operator command gateway (post-broker/shell-gate maturity)
- External packaging/release hardening (PyPI, Homebrew, Docker)

## Design

- Design explicit Phase Activation Governance that separates implementation approval, activation approval, commit approval, and push approval so implemented capabilities cannot be made active by inference.

## Future Explorations

- Automatic low-context detection triggering handoff.
- Compact-risk handoff triggering.
- Automatic governed bootstrap on agent initialization (`pcae session bootstrap`).
- Automatic session restoration from provenance timeline.
- Agent context monitoring and governance-aware context health reporting.
- Automatic AI session restart orchestration after bootstrap.
- True interactive next-agent selection from a configured agent roster.
- Auto-detect available agents from lock history or policy configuration.
- Orchestration-aware agent routing based on task type or governance context.
- Heterogeneous agent governance policies (per-agent policy overrides).
- Vendor-neutral agent flexibility.
- Roadmap/provenance coherence validation.
- ~~Stale roadmap detection.~~ Partially addressed by Phase 112B.1 (`tasks/TODO.md` staleness now surfaced in `pcae session bootstrap --compact`); full `docs/ROADMAP.md` "Current State" table refresh remains open — see 112B.1's Limitations.
- Governance artifact synchronization.
- Orchestration narrative validation.
- Governance drift detection.
