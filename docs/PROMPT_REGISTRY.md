# PCAE Prompt Registry

Generated: 2026-06-09T04:16:12.681143+00:00
Phase: 64B.3 — Prompt Recommendation Hardening
Current phase: 64B.6B
Current track: capability_intelligence
Prompt count: 27
Recommendation count: 7
Validation count: 27
Drift count: 4
Assessment status: quality_governed

## Prompt Registry

| Prompt ID | Phase | Type | Status | Version | Source | Dependency Status |
|---|---|---|---|---|---|---|
| prh-prompt-20260609T041612-01 | 64B.1 | implementation | historical | 64B.1-implementation-v1 | capability_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-02 | 64B.1 | validation | historical | 64B.1-validation-v1 | capability_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-03 | 64B.2 | implementation | historical | 64B.2-implementation-v1 | roadmap_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-04 | 64B.2 | validation | historical | 64B.2-validation-v1 | roadmap_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-05 | 64B.3 | implementation | recommended | 64B.3-implementation-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-06 | 64B.3 | validation | recommended | 64B.3-validation-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-07 | 64B.3 | agent | recommended | 64B.3-agent-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-08 | 64B.4 | implementation | recommended | 64B.4-implementation-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-09 | 64B.4 | validation | recommended | 64B.4-validation-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-10 | 64B.4 | agent | recommended | 64B.4-agent-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-11 | 64B.4A | implementation | recommended | 64B.4A-implementation-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-12 | 64B.4A | validation | recommended | 64B.4A-validation-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-13 | 64B.4A | agent | recommended | 64B.4A-agent-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-14 | 64B.4B | implementation | recommended | 64B.4B-implementation-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-15 | 64B.4B | validation | recommended | 64B.4B-validation-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-16 | 64B.5 | implementation | recommended | 64B.5-implementation-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-17 | 64B.5 | validation | recommended | 64B.5-validation-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-18 | 64B.5 | agent | recommended | 64B.5-agent-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-19 | 64B.6 | implementation | recommended | 64B.6-implementation-v1 | roadmap_registry+capability_registry+skill_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-20 | 64B.6 | validation | recommended | 64B.6-validation-v1 | roadmap_registry+capability_registry+skill_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-21 | 64B.6 | agent | recommended | 64B.6-agent-v1 | roadmap_registry+capability_registry+skill_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-22 | 64B.6A | implementation | recommended | 64B.6A-implementation-v1 | roadmap_registry+capability_registry+skill_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-23 | 64B.6A | validation | recommended | 64B.6A-validation-v1 | roadmap_registry+capability_registry+skill_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-24 | 64B.6A | agent | recommended | 64B.6A-agent-v1 | roadmap_registry+capability_registry+skill_registry | blocked:completed_phase |
| prh-prompt-20260609T041612-25 | 64B.6B | implementation | recommended | 64B.6B-implementation-v1 | roadmap_registry+capability_registry+skill_registry | validated |
| prh-prompt-20260609T041612-26 | 64B.6B | validation | recommended | 64B.6B-validation-v1 | roadmap_registry+capability_registry+skill_registry | validated |
| prh-prompt-20260609T041612-27 | 64B.6B | agent | recommended | 64B.6B-agent-v1 | roadmap_registry+capability_registry+skill_registry | validated |

## Recommendations

| Recommendation ID | Phase | Type | Status | Roadmap Source | Capability Source |
|---|---|---|---|---|---|
| prh-rec-20260609T041612-01 | 64B.6B | implementation | recommended | roadmap_registry_current_phase | Dependency & Capability Intelligence Rendering |
| prh-rec-20260609T041612-02 | 64B.6B | validation | recommended | roadmap_registry_current_phase | Dependency & Capability Intelligence Rendering |
| prh-rec-20260609T041612-03 | 64B.6B | agent | recommended | roadmap_registry_current_phase | Dependency & Capability Intelligence Rendering |
| prh-rec-20260609T041612-04 | 64B.1 | implementation | blocked | roadmap_registry_completed_phase | Capability and Roadmap Intelligence |
| prh-rec-20260609T041612-05 | 64B.2 | implementation | blocked | roadmap_registry_completed_phase | Roadmap Recommendation Hardening |
| prh-rec-20260609T041612-06 | 46A | implementation | blocked | roadmap_registry_superseded_phase | Invocation Pilot (Legacy) |
| prh-rec-20260609T041612-07 | 45A | implementation | blocked | roadmap_registry_track_mismatch | Multi-Agent Roadmap Generation |

## Validation

| Validation ID | Phase | Type | Completeness | Dependency | Roadmap Alignment | Status |
|---|---|---|---|---|---|---|
| prh-val-20260609T041612-01 | 64B.1 | implementation | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-02 | 64B.1 | validation | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-03 | 64B.2 | implementation | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-04 | 64B.2 | validation | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-05 | 64B.3 | implementation | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-06 | 64B.3 | validation | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-07 | 64B.3 | agent | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-08 | 64B.4 | implementation | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-09 | 64B.4 | validation | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-10 | 64B.4 | agent | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-11 | 64B.4A | implementation | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-12 | 64B.4A | validation | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-13 | 64B.4A | agent | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-14 | 64B.4B | implementation | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-15 | 64B.4B | validation | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-16 | 64B.5 | implementation | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-17 | 64B.5 | validation | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-18 | 64B.5 | agent | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-19 | 64B.6 | implementation | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-20 | 64B.6 | validation | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-21 | 64B.6 | agent | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-22 | 64B.6A | implementation | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-23 | 64B.6A | validation | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-24 | 64B.6A | agent | 100 | 0 | 0 | blocked |
| prh-val-20260609T041612-25 | 64B.6B | implementation | 100 | 100 | 100 | valid |
| prh-val-20260609T041612-26 | 64B.6B | validation | 100 | 100 | 100 | valid |
| prh-val-20260609T041612-27 | 64B.6B | agent | 100 | 100 | 100 | valid |

## Quality Requirements

- goal
- scope
- inputs
- models
- governance constraints
- acceptance criteria
- validation commands
- documentation requirements

## Governance Notes

- 64B.3 hardens prompt recommendations.
- Prompt recommendations use the roadmap registry.
- Prompt recommendations use the capability registry.
- Prompt Registry remains aligned with the shared intelligence layer that also exposes the Skill Registry.
- Prompt drift detection is implemented.
- Prompt quality governance is implemented.
- Prompt traceability is implemented.
- No runtime behavior changes occur.
- No orchestration behavior changes occur.
