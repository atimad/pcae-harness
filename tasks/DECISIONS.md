# Decisions

## Accepted

- Treat capability projection as shared infrastructure: capability inventory and capability/roadmap intelligence must materialize their public capability records through one projection helper so IDs, fields, and command/report outputs stay stable while projection logic cannot drift independently.
- Treat Phase 64B.4A skill registry hardening as consolidation work, not a new parallel subsystem: skill discovery, metadata parsing, and registry alignment should reuse the shared intelligence infrastructure that already supports capability, roadmap, and prompt governance.
- Treat Phase 64B.4 skills as first-class governed packages stored under `.pcae/skills`: a skill is metadata plus reusable instructions/workflow references, not merely a rendered prompt, and skill invocation remains read-only with no runtime, orchestration, or write execution.
- Treat Phase 64B.3 prompt recommendations as registry-backed governance artifacts: `pcae prompt next`, `pcae prompt phase`, and `pcae prompt validate` must source phase alignment from the roadmap registry, capability alignment from the capability registry, block historical/completed/superseded/track-mismatch prompt recommendations, and remain read-only with no runtime or orchestration execution.
- Phase 62A (Controlled Runtime Execution Pilot) is the first PCAE phase where execution_allowed=True. Execution is conditionally permitted only when: runtime is shell-local, command is on the allowlist (pwd, ls, ls -la, git status, python --version, python3 --version), command is not on the denylist, no write or network operations are involved, the 30s timeout is enforced, the 100 KB output limit is enforced, and human_review_required=True. All other governance restrictions (no write execution, no network, no AI runtime invocation, no commit/push/rollback) remain in force.
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
- Keep Phase 61E task lifecycle governance strictly assessment-only: inspect active/done task, roadmap, and session alignment, recommend remediation when needed, but do not move tasks, rewrite session state, or mutate repository state automatically.
- Keep Phase 61F agent handoff modernization strictly assessment-only: inspect continuity requirements, summarize roadmap/runtime/governance posture, and recommend modernization when needed, but do not rewrite handoff artifacts, rewrite session state, or mutate repository state automatically.
- Keep Phase 61G roadmap continuity strictly assessment-only: validate roadmap/task/session/runtime/handoff alignment before runtime work, but do not rewrite roadmap files, rewrite session state, or mutate repository state automatically.
- Keep Phase 61H automated task transition limited to governance lifecycle automation: complete the current task, create the next task, refresh session continuity, update governance memory files, and validate coherence/health/check state, but do not invoke runtimes, execute prompts, authorize execution, commit, push, rollback, or change unrelated source behavior.
