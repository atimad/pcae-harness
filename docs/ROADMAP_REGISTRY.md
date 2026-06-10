# PCAE Roadmap Registry

Generated: 2026-06-10T21:37:10.991565+00:00
Phase: 64B.1 — Capability and Roadmap Intelligence
Total phases: 47
Tracks: 8
Superseded: 1
Roadmap gaps: 0
Evolution events: 2
Assessment status: intelligence_available

## Track: governance_core

| Phase | Title | Status | Predecessor | Successor |
|---|---|---|---|---|
| 44A | Governed Task Contracts | completed | — | 52A |
| 52A | Task Lifecycle Hardening | completed | 44A | 62E |
| 62E | Active Task State Repair | completed | 52A | — |

## Track: runtime_governance

| Phase | Title | Status | Predecessor | Successor |
|---|---|---|---|---|
| 55A | Read-Only Runtime Invocation | completed | — | 62A |
| 62A | Controlled Runtime Execution Pilot | completed | 55A | 62C |
| 62C | Runtime Audit Persistence | completed | 62A | 62F |
| 62F | Runtime Review Decision Record | completed | 62C | 62G |
| 62G | Runtime Approval Gates | completed | 62F | 62H |
| 62H | Runtime Rollback Boundaries | completed | 62G | 63A |

## Track: multi_runtime

| Phase | Title | Status | Predecessor | Successor |
|---|---|---|---|---|
| 63A | Multi-Runtime Registry | completed | 62H | 63B |
| 63B | Runtime Selection Engine | completed | 63A | 63C |
| 63C | Runtime Arbitration | completed | 63B | 63D |
| 63D | Multi-Runtime Audit Chain | completed | 63C | 63E |
| 63E | Runtime Failure Recovery | completed | 63D | 63F |
| 63F | Runtime Quarantine | completed | 63E | 64A |
| 64A | Multi-Runtime Execution Planning | completed | 63F | 64B |
| 64B | Multi-Runtime Execution Readiness | completed | 64A | 64C |
| 64C | Multi-Runtime Orchestration Execution | completed | 64B | 64D |
| 64D | Runtime Coordination Policy | completed | 64C | 64E |
| 64E | Orchestration Audit Model | completed | 64D | 64F |
| 64F | Orchestration Readiness Gate | completed | 64E | 64G |

## Track: capability_intelligence

| Phase | Title | Status | Predecessor | Successor |
|---|---|---|---|---|
| 64G | Capability Inventory Alignment Hardening | completed | 64F | 65A |
| 64B.0 | Capability Inventory | completed | — | 64B.1 |
| 64B.1 | Capability and Roadmap Intelligence | completed | 64B.0 | 64B.2 |
| 64B.2 | Roadmap Recommendation Hardening | completed | 64B.1 | 64B.3 |
| 64B.3 | Prompt Recommendation Hardening | completed | 64B.2 | 64B.4 |
| 64B.4 | Skill System Foundation | completed | 64B.3 | 64B.4A |
| 64B.4A | Skill Registry Consolidation Hardening | completed | 64B.4 | 64B.4B |
| 64B.4B | Capability Projection Consolidation | completed | 64B.4A | 64B.5 |
| 64B.5 | Skill Invocation Targeting | completed | 64B.4B | 64B.6 |
| 64B.6 | Prompt Rendering Skill | completed | 64B.5 | 64B.6A |
| 64B.6A | Prompt Rendering Quality Hardening | completed | 64B.6 | 64B.6B |
| 64B.6B | Dependency & Capability Intelligence Rendering | completed | 64B.6A | 64B.6C |
| 64B.6C | Predecessor Capability Rendering | completed | 64B.6B | 64B.6D |
| 64B.6D | Command & Architecture Intelligence Rendering | completed | 64B.6C | 64B.6E |
| 64B.6E | Design Review Intelligence Rendering | active | 64B.6D | — |

## Track: strategic_governance

| Phase | Title | Status | Predecessor | Successor |
|---|---|---|---|---|
| 65A | Strategic Roadmap Governance Design | completed | 64G | 65B |
| 65B | Strategic State Summary | completed | 65A | 65C |
| 65C | Strategic Governance Registry Alignment | completed | 65B | 65D |
| 65D | Strategic Capability-Objective Bulk Mapping Governance | completed | 65C | 65E |
| 65E | Governed Write Invocation Design | completed | 65D | 65F |
| 65F | Governed Write Invocation Candidate Contract | completed | 65E | 65G |
| 65G | Write Invocation Approval Gateway Design | completed | 65F | 65H |
| 65H | Commit Session Continuity Guard | completed | 65G | 66A |

## Track: independent_review_governance

| Phase | Title | Status | Predecessor | Successor |
|---|---|---|---|---|
| 66A | Independent Review Governance Model | active | 65H | — |

## Track: roadmap_intelligence

| Phase | Title | Status | Predecessor | Successor |
|---|---|---|---|---|
| 45A | Roadmap Generation Pipeline | completed | — | — |

## Track: legacy

| Phase | Title | Status | Predecessor | Successor |
|---|---|---|---|---|
| 46A | Invocation Pilot (Legacy) | superseded | — | 63A |

## Roadmap Evolution

- **46A → 63A**: Invocation Pilot (46A-46J) was superseded by Multi-Runtime Registry (63A) which provides governed multi-runtime selection, arbitration, and audit.
- **44A → 52A**: Governed Task Contracts (44A) evolved into Task Lifecycle Hardening (52A) which added session recovery, agent lock recovery, and corruption recovery.

## Governance Notes

- 64B.1 introduces Capability and Roadmap Intelligence.
- 64B.3 hardens prompt recommendations using the roadmap registry and capability registry.
- 64B.4 introduces a first-class skill system in the capability_intelligence track.
- Skill Registry discovery is consolidated into the shared intelligence layer.
- Roadmap evolution is tracked.
- Superseded phases are tracked.
- No runtime behavior changes occur.
