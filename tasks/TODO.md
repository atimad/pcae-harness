# TODO

## Pending

- Update `pcae docs commands` to include the `phase`, `status`, and `orchestration` command groups.
- Implement `pcae orchestration select`: given a task type, return the recommended agent from policy.

## Future Explorations (from Phase 32C/32D/32E/32F/32G)

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
- Full governance audit: `pcae governance audit` command.
- Roadmap/provenance coherence validation: detect completed features still in roadmap.
- Stale roadmap detection: automated scan of governance docs against CHANGELOG/DONE history.
- Governance artifact synchronization: keep PROJECT_STATUS.md, TODO.md, CHANGELOG.md coherent.
- Orchestration narrative validation: verify agent-facing guidance matches runtime capabilities.
- Governance drift detection for documentation artifacts beyond PROJECT_STATUS.md.
