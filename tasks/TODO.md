# TODO

## Production v1 Path

See [docs/ROADMAP.md](../docs/ROADMAP.md) for the canonical roadmap.

| Phase | Name | Status |
|-------|------|--------|
| 90A | Permission Broker Enforcement Boundary Design | ✅ Complete |
| 90B | Full-Suite Baseline Inspection and Repair | ✅ Complete |
| 90B.1 | Roadmap Coherence and Production v1 Plan | ✅ Complete |
| 90C | Permission Broker Enforcement Boundary Test Plan | 🔜 Next |
| 91A | Permission Broker Simulation Prototype | Pending |
| 91B | Broker CLI and Decision Explanation | Pending |
| 91C | Hard-Block Policy Readiness | Pending |
| 92A | Phase Report Artifact Model | Pending |
| 92B | Pluggable Notification Foundation | Pending |
| 92C | Telegram Outbound Phase Report Delivery | Pending |
| 92D | Automatic Phase-Finalization Notification Hook | Pending |
| 93A | Narrow Shell Gate Design | Pending |
| 93B | Narrow Shell Gate Prototype | Pending |
| 94A | Governed Backend Invocation Design | Pending |
| 95A | Production v1 Documentation / Install / Demo | Pending |
| 96A | Production v1 Governance Review | Pending |

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
- Stale roadmap detection.
- Governance artifact synchronization.
- Orchestration narrative validation.
- Governance drift detection.
