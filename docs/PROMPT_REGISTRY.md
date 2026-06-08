# PCAE Prompt Registry

Generated: 2026-06-08T17:20:14.659086+00:00
Phase: 64B.3 — Prompt Recommendation Hardening
Current phase: 64B.3
Current track: capability_intelligence
Prompt count: 7
Recommendation count: 7
Validation count: 7
Drift count: 4
Assessment status: quality_governed

## Prompt Registry

| Prompt ID | Phase | Type | Status | Version | Source | Dependency Status |
|---|---|---|---|---|---|---|
| prh-prompt-20260608T172014-01 | 64B.1 | implementation | historical | 64B.1-implementation-v1 | capability_registry | blocked:completed_phase |
| prh-prompt-20260608T172014-02 | 64B.1 | validation | historical | 64B.1-validation-v1 | capability_registry | blocked:completed_phase |
| prh-prompt-20260608T172014-03 | 64B.2 | implementation | historical | 64B.2-implementation-v1 | roadmap_registry | blocked:completed_phase |
| prh-prompt-20260608T172014-04 | 64B.2 | validation | historical | 64B.2-validation-v1 | roadmap_registry | blocked:completed_phase |
| prh-prompt-20260608T172014-05 | 64B.3 | implementation | recommended | 64B.3-implementation-v1 | roadmap_registry+capability_registry | validated |
| prh-prompt-20260608T172014-06 | 64B.3 | validation | recommended | 64B.3-validation-v1 | roadmap_registry+capability_registry | validated |
| prh-prompt-20260608T172014-07 | 64B.3 | agent | recommended | 64B.3-agent-v1 | roadmap_registry+capability_registry | validated |

## Recommendations

| Recommendation ID | Phase | Type | Status | Roadmap Source | Capability Source |
|---|---|---|---|---|---|
| prh-rec-20260608T172014-01 | 64B.3 | implementation | recommended | roadmap_registry_current_phase | Prompt Recommendation Hardening |
| prh-rec-20260608T172014-02 | 64B.3 | validation | recommended | roadmap_registry_current_phase | Prompt Recommendation Hardening |
| prh-rec-20260608T172014-03 | 64B.3 | agent | recommended | roadmap_registry_current_phase | Prompt Recommendation Hardening |
| prh-rec-20260608T172014-04 | 64B.1 | implementation | blocked | roadmap_registry_completed_phase | Capability and Roadmap Intelligence |
| prh-rec-20260608T172014-05 | 64B.2 | implementation | blocked | roadmap_registry_completed_phase | Roadmap Recommendation Hardening |
| prh-rec-20260608T172014-06 | 46A | implementation | blocked | roadmap_registry_superseded_phase | Invocation Pilot (Legacy) |
| prh-rec-20260608T172014-07 | 45A | implementation | blocked | roadmap_registry_track_mismatch | Multi-Agent Roadmap Generation |

## Validation

| Validation ID | Phase | Type | Completeness | Dependency | Roadmap Alignment | Status |
|---|---|---|---|---|---|---|
| prh-val-20260608T172014-01 | 64B.1 | implementation | 100 | 0 | 0 | blocked |
| prh-val-20260608T172014-02 | 64B.1 | validation | 100 | 0 | 0 | blocked |
| prh-val-20260608T172014-03 | 64B.2 | implementation | 100 | 0 | 0 | blocked |
| prh-val-20260608T172014-04 | 64B.2 | validation | 100 | 0 | 0 | blocked |
| prh-val-20260608T172014-05 | 64B.3 | implementation | 100 | 100 | 100 | valid |
| prh-val-20260608T172014-06 | 64B.3 | validation | 100 | 100 | 100 | valid |
| prh-val-20260608T172014-07 | 64B.3 | agent | 100 | 100 | 100 | valid |

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
- Prompt drift detection is implemented.
- Prompt quality governance is implemented.
- Prompt traceability is implemented.
- No runtime behavior changes occur.
- No orchestration behavior changes occur.
