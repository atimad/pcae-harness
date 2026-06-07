# Decisions

## Accepted

- Use Python and `pathlib` for cross-platform filesystem behavior.
- Use Markdown files as the only persistence mechanism for the MVP.
- Defer databases, LLM calls, and vector search.
- Keep commands modular under `src/pcae/commands`.
- Keep `pcae inspect` read-only; reserve enforcement and repair behavior for future commands.
- Treat unvalidated sandbox isolation boundaries as advisory hardening signals that keep execution blocked; Phase 52G may recommend human-reviewed remediation but cannot apply remediation or authorize runtime execution.
- Treat Phase 52M conflict resolution as read-only classification and escalation: preserve conflicting evidence, recommend human-reviewed resolution paths, and keep automatic resolution and execution disabled.
- Keep Phase 61B runtime discovery strictly assessment-only: define discovery readiness requirements and report blockers, but do not probe the host, invoke runtimes, register runtimes, or authorize execution.
- Keep Phase 61C runtime capability inventory strictly assessment-only: classify capability status and trust level from governance inputs, but do not discover hosts, register runtimes, invoke runtimes, or authorize execution.
- Keep Phase 61D runtime trust modeling strictly assessment-only: classify trust signals and prerequisites from governance inputs, but do not assign trust automatically, discover hosts, register runtimes, invoke runtimes, or authorize execution.
