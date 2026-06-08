# PCAE Prompt Registry

Generated: 2026-06-08T18:48:19.913440+00:00
Phase: 64B.3 — Prompt Recommendation Hardening
Current phase: 64B.4A
Current track: capability_intelligence
Prompt count: 13
Recommendation count: 7
Validation count: 13
Drift count: 4
Assessment status: quality_governed

## Prompt Registry

| Prompt ID | Phase | Type | Status | Version | Source | Dependency Status |
|---|---|---|---|---|---|---|
| prh-prompt-20260608T184819-01 | 64B.1 | implementation | historical | 64B.1-implementation-v1 | capability_registry | blocked:completed_phase |
| prh-prompt-20260608T184819-02 | 64B.1 | validation | historical | 64B.1-validation-v1 | capability_registry | blocked:completed_phase |
| prh-prompt-20260608T184819-03 | 64B.2 | implementation | historical | 64B.2-implementation-v1 | roadmap_registry | blocked:completed_phase |
| prh-prompt-20260608T184819-04 | 64B.2 | validation | historical | 64B.2-validation-v1 | roadmap_registry | blocked:completed_phase |
| prh-prompt-20260608T184819-05 | 64B.3 | implementation | recommended | 64B.3-implementation-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260608T184819-06 | 64B.3 | validation | recommended | 64B.3-validation-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260608T184819-07 | 64B.3 | agent | recommended | 64B.3-agent-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260608T184819-08 | 64B.4 | implementation | recommended | 64B.4-implementation-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260608T184819-09 | 64B.4 | validation | recommended | 64B.4-validation-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260608T184819-10 | 64B.4 | agent | recommended | 64B.4-agent-v1 | roadmap_registry+capability_registry | blocked:completed_phase |
| prh-prompt-20260608T184819-11 | 64B.4A | implementation | recommended | 64B.4A-implementation-v1 | roadmap_registry+capability_registry | validated |
| prh-prompt-20260608T184819-12 | 64B.4A | validation | recommended | 64B.4A-validation-v1 | roadmap_registry+capability_registry | validated |
| prh-prompt-20260608T184819-13 | 64B.4A | agent | recommended | 64B.4A-agent-v1 | roadmap_registry+capability_registry | validated |

## Recommendations

| Recommendation ID | Phase | Type | Status | Roadmap Source | Capability Source |
|---|---|---|---|---|---|
| prh-rec-20260608T184819-01 | 64B.4A | implementation | recommended | roadmap_registry_current_phase | Skill Registry Consolidation Hardening |
| prh-rec-20260608T184819-02 | 64B.4A | validation | recommended | roadmap_registry_current_phase | Skill Registry Consolidation Hardening |
| prh-rec-20260608T184819-03 | 64B.4A | agent | recommended | roadmap_registry_current_phase | Skill Registry Consolidation Hardening |
| prh-rec-20260608T184819-04 | 64B.1 | implementation | blocked | roadmap_registry_completed_phase | Capability and Roadmap Intelligence |
| prh-rec-20260608T184819-05 | 64B.2 | implementation | blocked | roadmap_registry_completed_phase | Roadmap Recommendation Hardening |
| prh-rec-20260608T184819-06 | 46A | implementation | blocked | roadmap_registry_superseded_phase | Invocation Pilot (Legacy) |
| prh-rec-20260608T184819-07 | 45A | implementation | blocked | roadmap_registry_track_mismatch | Multi-Agent Roadmap Generation |

## Validation

| Validation ID | Phase | Type | Completeness | Dependency | Roadmap Alignment | Status |
|---|---|---|---|---|---|---|
| prh-val-20260608T184819-01 | 64B.1 | implementation | 100 | 0 | 0 | blocked |
| prh-val-20260608T184819-02 | 64B.1 | validation | 100 | 0 | 0 | blocked |
| prh-val-20260608T184819-03 | 64B.2 | implementation | 100 | 0 | 0 | blocked |
| prh-val-20260608T184819-04 | 64B.2 | validation | 100 | 0 | 0 | blocked |
| prh-val-20260608T184819-05 | 64B.3 | implementation | 100 | 0 | 0 | blocked |
| prh-val-20260608T184819-06 | 64B.3 | validation | 100 | 0 | 0 | blocked |
| prh-val-20260608T184819-07 | 64B.3 | agent | 100 | 0 | 0 | blocked |
| prh-val-20260608T184819-08 | 64B.4 | implementation | 100 | 0 | 0 | blocked |
| prh-val-20260608T184819-09 | 64B.4 | validation | 100 | 0 | 0 | blocked |
| prh-val-20260608T184819-10 | 64B.4 | agent | 100 | 0 | 0 | blocked |
| prh-val-20260608T184819-11 | 64B.4A | implementation | 100 | 100 | 100 | valid |
| prh-val-20260608T184819-12 | 64B.4A | validation | 100 | 100 | 100 | valid |
| prh-val-20260608T184819-13 | 64B.4A | agent | 100 | 100 | 100 | valid |

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
