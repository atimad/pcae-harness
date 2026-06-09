# PCAE Skill Registry

Generated: 2026-06-09T04:28:24.740944+00:00
Phase: 64B.5 — Skill Invocation Targeting
Skills root: .pcae/skills
Skill count: 6
Invalid skill count: 0
Governance status: governed

## Skill Registry

| Skill ID | Name | Type | Path | Version | Status | Human Review Required |
|---|---|---|---|---|---|---|
| capability-analysis | Capability Analysis | analysis | .pcae/skills/capability-analysis | 1.0.0 | active | True |
| phase-agent | Phase Agent | agent | .pcae/skills/phase-agent | 1.0.0 | active | True |
| phase-implementation | Phase Implementation | implementation | .pcae/skills/phase-implementation | 1.0.0 | active | True |
| phase-validation | Phase Validation | validation | .pcae/skills/phase-validation | 1.0.0 | active | True |
| roadmap-analysis | Roadmap Analysis | analysis | .pcae/skills/roadmap-analysis | 1.0.0 | active | True |
| task-transition | Task Transition | workflow | .pcae/skills/task-transition | 1.0.0 | active | True |

## Governance Notes

- 64B.4 introduces a first-class skill system.
- 64B.4A hardens skill registry consolidation.
- 64B.4B consolidates capability projections.
- 64B.5 introduces skill invocation targeting.
- 64B.6 introduces prompt rendering through PCAE skills.
- 64B.6A hardens prompt rendering quality: goal accuracy, domain accuracy, completeness scoring, placeholder detection.
- Skills are the first-class prompt rendering interface.
- 'pcae skill invoke phase-implementation <phase_id>' renders a full implementation prompt.
- 'pcae skill invoke phase-validation <phase_id>' renders a full validation prompt.
- 'pcae skill invoke phase-agent <phase_id>' renders a full agent prompt.
- Rendered prompts are detailed, goal-oriented, and agent-ready.
- Prompt quality is checked across 10 domains; quality signals surface inline.
- Skills can now resolve phase, capability, task, and track targets.
- Skills are governed artifacts.
- Skill Registry discovery and metadata are consolidated with the shared intelligence infrastructure.
- Capability Inventory records the skill system as a capability domain.
- Roadmap Registry tracks the 64B.6A capability_intelligence phase.
- Skills support discovery, validation, invocation, target resolution, and prompt rendering.
- No runtime behavior changes occur in 64B.6 or 64B.6A.
- No orchestration behavior changes occur in 64B.6 or 64B.6A.
