# PCAE Capability Inventory

Generated: 2026-06-11T11:31:33.024189+00:00
Phase: 64B.0 — Capability Inventory
Total capabilities: 54
Implemented: 52
Dormant: 1
Superseded: 1
Roadmap gaps: 0
Duplicates/overlaps: 0
Prompt capabilities: 2
Assessment status: inventory_complete

## Capability Records

| Capability | Domain | Phase | Status | Commands | Dependencies | Successors |
|---|---|---|---|---|---|---|
| Governed Task Contracts | governance_capabilities | 44A-46J | implemented | pcae task new; pcae task close; pcae task transition | (none) | task_lifecycle_governance |
| Task Lifecycle Governance | task_lifecycle_capabilities | 52A | implemented | pcae task-lifecycle-hardening; pcae task transition | governed_task_contracts | (none) |
| Multi-Agent Roadmap Generation | roadmap_capabilities | 45A-45E | implemented | pcae roadmap; pcae multi-agent-roadmap; pcae roadmap-evidence | governed_task_contracts | capability_inventory |
| Phase Prompt Generation | prompt_generation_capabilities | 45A-45E | implemented | pcae prompt-render; pcae autonomous-prompt-proposal; pcae prompt-validation-design; pcae prompt-governance-design | multi_agent_roadmap_generation | (none) |
| Prompt Recommendation Hardening | prompt_intelligence_capabilities | 64B.3 | implemented | pcae prompt next; pcae prompt phase; pcae prompt validate | capability_and_roadmap_intelligence; roadmap_recommendation_hardening | (none) |
| Skill System Foundation | skill_system_capabilities | 64B.4 | implemented | pcae skill list; pcae skill show; pcae skill validate; pcae skill invoke | capability_and_roadmap_intelligence; prompt_recommendation_hardening | skill_registry_consolidation_hardening |
| Skill Registry Consolidation Hardening | skill_system_capabilities | 64B.4A | implemented | pcae skill list; pcae skill show; pcae skill validate; pcae skill invoke; pcae capability-inventory; pcae roadmap current | skill_system_foundation; capability_and_roadmap_intelligence | skill_invocation_targeting |
| Read-Only Runtime Invocation Governance | runtime_governance_capabilities | 55A-57A | implemented | pcae readonly-invocation; pcae read-only-runtime-invocation; pcae runtime-review-workflow | governed_task_contracts | runtime_approval_gates |
| Invocation Pilot (Legacy) | runtime_governance_capabilities | 46A-46J | superseded | pcae invocation-pilot; pcae multi-runtime-pilot | (none) | read_only_runtime_invocation_governance |
| Controlled Runtime Execution Pilot | runtime_execution_capabilities | 62A | dormant | pcae runtime-execution-pilot | read_only_runtime_invocation_governance | multi_runtime_execution_planning |
| Runtime Audit Persistence | runtime_audit_capabilities | 62C | implemented | pcae runtime-audit-persistence | read_only_runtime_invocation_governance | multi_runtime_audit_chain |
| Runtime Review Decision Record | runtime_review_capabilities | 62F | implemented | pcae runtime-review-decision | runtime_audit_persistence | runtime_approval_gates |
| Runtime Approval Gates | runtime_governance_capabilities | 62G | implemented | pcae runtime-approval-gates | runtime_review_decision_record | multi_runtime_registry |
| Runtime Rollback Boundaries | runtime_governance_capabilities | 62H | implemented | pcae runtime-rollback-boundaries | runtime_approval_gates | runtime_failure_recovery |
| Multi-Runtime Registry | multi_runtime_capabilities | 63A | implemented | pcae multi-runtime-registry | runtime_rollback_boundaries | runtime_selection_engine |
| Runtime Selection Engine | multi_runtime_capabilities | 63B | implemented | pcae runtime-selection-engine | multi_runtime_registry | runtime_arbitration |
| Runtime Arbitration | multi_runtime_capabilities | 63C | implemented | pcae runtime-arbitration | runtime_selection_engine | multi_runtime_audit_chain |
| Multi-Runtime Audit Chain | multi_runtime_capabilities | 63D | implemented | pcae multi-runtime-audit-chain | runtime_arbitration | runtime_failure_recovery |
| Runtime Failure Recovery | multi_runtime_capabilities | 63E | implemented | pcae runtime-failure-recovery | multi_runtime_audit_chain | runtime_quarantine |
| Multi-Runtime Execution Planning | multi_runtime_capabilities | 64A | implemented | pcae multi-runtime-execution-planning | multi_runtime_registry; runtime_selection_engine; runtime_arbitration | multi_runtime_execution_readiness |
| Multi-Runtime Execution Readiness | multi_runtime_capabilities | 64B | implemented | pcae multi-runtime-execution-readiness | multi_runtime_execution_planning | multi_runtime_orchestration_execution |
| Multi-Runtime Orchestration Execution | multi_runtime_capabilities | 64C | implemented | pcae multi-runtime-orchestration-execution; pcae multi-runtime-orchestration-execution --json | multi_runtime_execution_readiness | runtime_coordination_policy |
| Runtime Coordination Policy | multi_runtime_capabilities | 64D | implemented | pcae runtime-coordination-policy; pcae runtime-coordination-policy --json | multi_runtime_orchestration_execution | orchestration_audit_model |
| Orchestration Audit Model | multi_runtime_capabilities | 64E | implemented | pcae orchestration-audit-model; pcae orchestration-audit-model --json | runtime_coordination_policy; multi_runtime_audit_chain | orchestration_readiness_gate |
| Orchestration Readiness Gate | multi_runtime_capabilities | 64F | implemented | pcae orchestration-readiness-gate; pcae orchestration-readiness-gate --json | multi_runtime_orchestration_execution; runtime_coordination_policy; orchestration_audit_model | multi_runtime_execution_dispatch |
| Repository Health Governance | repository_governance_capabilities | 44A | implemented | pcae health; pcae check; pcae status coherence | (none) | task_state_alignment |
| Commands Reference Generation | documentation_capabilities | 53A | implemented | pcae docs commands | (none) | capability_inventory |
| Phase-Scoped Test Selection | testing_capabilities | 44A+ | implemented | python -m pytest -k <phase_id>; python -m pytest -n auto | (none) | (none) |
| Session and Agent Lock Recovery | recovery_capabilities | 52B-52D | implemented | pcae session-recovery; pcae agent-lock-recovery; pcae corruption-recovery | governed_task_contracts | runtime_failure_recovery |
| Runtime Quarantine | multi_runtime_capabilities | 63F | implemented | pcae runtime-quarantine | runtime_failure_recovery | (none) |
| Capability Inventory | documentation_capabilities | 64B.0 | implemented | pcae capability-inventory | (none) | capability_and_roadmap_intelligence |
| Capability and Roadmap Intelligence | capability_intelligence | 64B.1 | implemented | pcae capability list; pcae capability show; pcae capability dependencies; pcae roadmap current; pcae roadmap tracks; pcae roadmap evolution; pcae prompt next; pcae prompt phase | capability_inventory | roadmap_recommendation_hardening |
| Roadmap Recommendation Hardening | capability_intelligence | 64B.2 | implemented | pcae roadmap-recommendation-hardening; pcae roadmap next; pcae prompt next | capability_and_roadmap_intelligence | prompt_recommendation_hardening |
| Capability Projection Consolidation | skill_system_capabilities | 64B.4B | implemented | pcae capability list; pcae capability show; pcae roadmap current | skill_registry_consolidation_hardening | skill_invocation_targeting |
| Skill Invocation Targeting | skill_system_capabilities | 64B.5 | implemented | pcae skill invoke <skill_id> <target_id>; pcae skill invoke <skill_id> --target <target_id>; pcae skill invoke <skill_id> --target-type <type> --target <target_id>; pcae skill validate | skill_registry_consolidation_hardening | prompt_rendering_skill |
| Prompt Rendering Skill | skill_system_capabilities | 64B.6 | implemented | pcae skill invoke phase-implementation <phase_id>; pcae skill invoke phase-validation <phase_id>; pcae skill invoke phase-agent <phase_id>; pcae prompt render --phase <phase_id> --type implementation; pcae prompt render --phase <phase_id> --type validation; pcae prompt render --phase <phase_id> --type agent | skill_invocation_targeting | prompt_rendering_quality_hardening |
| Prompt Rendering Quality Hardening | skill_system_capabilities | 64B.6A | implemented | pcae skill invoke phase-implementation <phase_id>; pcae skill invoke phase-validation <phase_id>; pcae skill invoke phase-agent <phase_id>; pcae prompt render --phase <phase_id> --type implementation; pcae prompt render --phase <phase_id> --type validation; pcae prompt render --phase <phase_id> --type agent | prompt_rendering_skill | dependency_capability_intelligence_rendering |
| Dependency & Capability Intelligence Rendering | skill_system_capabilities | 64B.6B | implemented | pcae skill invoke phase-implementation <phase_id>; pcae skill invoke phase-validation <phase_id>; pcae skill invoke phase-agent <phase_id>; pcae prompt render --phase <phase_id> --type implementation; pcae prompt render --phase <phase_id> --type validation; pcae prompt render --phase <phase_id> --type agent | prompt_rendering_quality_hardening | predecessor_capability_rendering |
| Predecessor Capability Rendering | skill_system_capabilities | 64B.6C | implemented | pcae skill invoke phase-implementation <phase_id>; pcae skill invoke phase-validation <phase_id>; pcae skill invoke phase-agent <phase_id>; pcae prompt render --phase <phase_id> --type implementation; pcae prompt render --phase <phase_id> --type validation; pcae prompt render --phase <phase_id> --type agent | dependency_capability_intelligence_rendering | command_architecture_intelligence_rendering |
| Command & Architecture Intelligence Rendering | skill_system_capabilities | 64B.6D | implemented | pcae skill invoke phase-implementation <phase_id>; pcae skill invoke phase-validation <phase_id>; pcae skill invoke phase-agent <phase_id>; pcae prompt render --phase <phase_id> --type implementation; pcae prompt render --phase <phase_id> --type validation; pcae prompt render --phase <phase_id> --type agent | predecessor_capability_rendering | design_review_intelligence_rendering |
| Design Review Intelligence Rendering | skill_system_capabilities | 64B.6E | implemented | pcae skill invoke phase-implementation <phase_id>; pcae skill invoke phase-agent <phase_id> | command_architecture_intelligence_rendering | capability_inventory_alignment |
| Capability Inventory Alignment | capability_intelligence | 64G | implemented | pcae runtime-coordination-policy; pcae runtime-coordination-policy --json; pcae capability-inventory | runtime_coordination_policy; capability_inventory | strategic_roadmap_governance |
| Strategic Roadmap Governance | strategic_governance | 65A | implemented | pcae strategic-roadmap-governance; pcae strategic-roadmap-governance --json | capability_inventory_alignment; capability_and_roadmap_intelligence | strategic_state_summary |
| Strategic State Summary | strategic_governance | 65B | implemented | pcae strategic-state-summary; pcae strategic-state-summary --json | strategic_roadmap_governance | strategic_governance_registry_alignment |
| Strategic Governance Registry Alignment | strategic_governance | 65C | implemented | (none) | strategic_state_summary | strategic_capability-objective_bulk_mapping_governance |
| Strategic Capability-Objective Bulk Mapping Governance | strategic_governance | 65D | implemented | pcae mapping-review-governance; pcae mapping-review-governance --json | strategic_governance_registry_alignment | governed_write_invocation_design |
| Governed Write Invocation Design | strategic_governance | 65E | implemented | pcae governed-write-invocation-design; pcae governed-write-invocation-design --json | strategic_capability-objective_bulk_mapping_governance; strategic_state_summary | governed_write_invocation_candidate_contract |
| Governed Write Invocation Candidate Contract | strategic_governance | 65F | implemented | pcae governed-write-invocation-candidate; pcae governed-write-invocation-candidate --json | governed_write_invocation_design | write_invocation_approval_gateway |
| Write Invocation Approval Gateway | strategic_governance | 65G | implemented | pcae write-invocation-approval-gateway; pcae write-invocation-approval-gateway --json | governed_write_invocation_candidate_contract | commit_session_continuity_guard |
| Commit Session Continuity Guard | strategic_governance | 65H | implemented | (none) | write_invocation_approval_gateway | strategic_registry_coherence_hardening |
| Strategic Registry Coherence Hardening | strategic_governance | 65I | implemented | (none) | commit_session_continuity_guard; strategic_review_model | strategic_decision_continuity |
| Strategic Decision Continuity | strategic_governance | 65J | implemented | pcae strategic-continuity show current; pcae strategic-continuity history; pcae strategic-continuity validate | strategic_registry_coherence_hardening; strategic_review_model | (none) |
| Independent Review Governance | strategic_governance | 66A | implemented | pcae independent-review-governance; pcae independent-review-governance --json | commit_session_continuity_guard | strategic_review_model |
| Strategic Review Model | strategic_governance | 66B | implemented | pcae strategic-review-governance; pcae strategic-review-governance --json | independent_review_governance | (none) |

## Governance Notes

- 64B.0 creates a capability inventory.
- 64B.3 adds prompt recommendation hardening as an implemented capability.
- 64B.4 adds a first-class skill system as an implemented capability.
- Skill Registry metadata is consolidated with the shared intelligence infrastructure.
- 64B.0 does not modify roadmap behavior.
- 64B.0 does not modify task lifecycle behavior.
- 64B.0 does not modify runtime behavior.
- 64B.0 is prerequisite for 64B.1 Capability and Roadmap Intelligence.

*Phase 64B.0 creates an authoritative inventory of all PCAE capabilities. Discovery and governance only; no behavior modified. capability_count=54. implemented_count=52. dormant_count=1. superseded_count=1. roadmap_gap_count=0. duplicate_count=0. prompt_capability_count=2. assessment_status=inventory_complete. Prerequisite for 64B.1 Capability and Roadmap Intelligence.*
