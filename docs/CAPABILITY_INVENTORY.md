# PCAE Capability Inventory

Generated: 2026-06-10T14:28:25.727924+00:00
Phase: 64B.0 — Capability Inventory
Total capabilities: 46
Implemented: 44
Dormant: 1
Superseded: 1
Roadmap gaps: 0
Duplicates/overlaps: 0
Prompt capabilities: 2
Assessment status: inventory_complete

## Capability Records

| Capability | Domain | Phase | Status | Commands | Dependencies | Successors |
|---|---|---|---|---|---|---|
| Governed Task Contracts | governance_capabilities | 44A-46J | implemented | pcae task new; pcae task close; pcae task transition | (none) | (none) |
| Task Lifecycle Governance | task_lifecycle_capabilities | 52A | implemented | pcae task-lifecycle-hardening; pcae task transition | governed_task_contracts | (none) |
| Multi-Agent Roadmap Generation | roadmap_capabilities | 45A-45E | implemented | pcae roadmap; pcae multi-agent-roadmap; pcae roadmap-evidence | governed_task_contracts | (none) |
| Phase Prompt Generation | prompt_generation_capabilities | 45A-45E | implemented | pcae prompt-render; pcae autonomous-prompt-proposal; pcae prompt-validation-design; ... (4 total) | multi_agent_roadmap_generation | (none) |
| Prompt Recommendation Hardening | prompt_intelligence_capabilities | 64B.3 | implemented | pcae prompt next; pcae prompt phase; pcae prompt validate | capability_and_roadmap_intelligence; roadmap_recommendation_hardening | (none) |
| Skill System Foundation | skill_system_capabilities | 64B.4 | implemented | pcae skill list; pcae skill show; pcae skill validate; ... (4 total) | capability_and_roadmap_intelligence; prompt_recommendation_hardening | (none) |
| Skill Registry Consolidation Hardening | skill_system_capabilities | 64B.4A | implemented | pcae skill list; pcae skill show; pcae skill validate; ... (6 total) | skill_system_foundation; capability_and_roadmap_intelligence | (none) |
| Read-Only Runtime Invocation Governance | runtime_governance_capabilities | 55A-57A | implemented | pcae readonly-invocation; pcae read-only-runtime-invocation; pcae runtime-review-workflow | governed_task_contracts | (none) |
| Invocation Pilot (Legacy) | runtime_governance_capabilities | 46A-46J | superseded | pcae invocation-pilot; pcae multi-runtime-pilot | (none) | (none) |
| Controlled Runtime Execution Pilot | runtime_execution_capabilities | 62A | dormant | pcae runtime-execution-pilot | read_only_runtime_invocation_governance | (none) |
| Runtime Audit Persistence | runtime_audit_capabilities | 62C | implemented | pcae runtime-audit-persistence | read_only_runtime_invocation_governance | (none) |
| Runtime Review Decision Record | runtime_review_capabilities | 62F | implemented | pcae runtime-review-decision | runtime_audit_persistence | (none) |
| Runtime Approval Gates | runtime_governance_capabilities | 62G | implemented | pcae runtime-approval-gates | runtime_review_decision_record | (none) |
| Runtime Rollback Boundaries | runtime_governance_capabilities | 62H | implemented | pcae runtime-rollback-boundaries | runtime_approval_gates | (none) |
| Multi-Runtime Registry | multi_runtime_capabilities | 63A | implemented | pcae multi-runtime-registry | runtime_rollback_boundaries | (none) |
| Runtime Selection Engine | multi_runtime_capabilities | 63B | implemented | pcae runtime-selection-engine | multi_runtime_registry | (none) |
| Runtime Arbitration | multi_runtime_capabilities | 63C | implemented | pcae runtime-arbitration | runtime_selection_engine | (none) |
| Multi-Runtime Audit Chain | multi_runtime_capabilities | 63D | implemented | pcae multi-runtime-audit-chain | runtime_arbitration | (none) |
| Runtime Failure Recovery | multi_runtime_capabilities | 63E | implemented | pcae runtime-failure-recovery | multi_runtime_audit_chain | (none) |
| Multi-Runtime Execution Planning | multi_runtime_capabilities | 64A | implemented | pcae multi-runtime-execution-planning | multi_runtime_registry; runtime_selection_engine... | (none) |
| Multi-Runtime Execution Readiness | multi_runtime_capabilities | 64B | implemented | pcae multi-runtime-execution-readiness | multi_runtime_execution_planning | (none) |
| Multi-Runtime Orchestration Execution | multi_runtime_capabilities | 64C | implemented | pcae multi-runtime-orchestration-execution; pcae multi-runtime-orchestration-execution --json | multi_runtime_execution_readiness | (none) |
| Runtime Coordination Policy | multi_runtime_capabilities | 64D | implemented | pcae runtime-coordination-policy; pcae runtime-coordination-policy --json | multi_runtime_orchestration_execution | (none) |
| Orchestration Audit Model | multi_runtime_capabilities | 64E | implemented | pcae orchestration-audit-model; pcae orchestration-audit-model --json | runtime_coordination_policy; multi_runtime_audit_chain | (none) |
| Orchestration Readiness Gate | multi_runtime_capabilities | 64F | implemented | pcae orchestration-readiness-gate; pcae orchestration-readiness-gate --json | multi_runtime_orchestration_execution; runtime_coordination_policy... | (none) |
| Repository Health Governance | repository_governance_capabilities | 44A | implemented | pcae health; pcae check; pcae status coherence | (none) | (none) |
| Commands Reference Generation | documentation_capabilities | 53A | implemented | pcae docs commands | (none) | (none) |
| Phase-Scoped Test Selection | testing_capabilities | 44A+ | implemented | python -m pytest -k <phase_id>; python -m pytest -n auto | (none) | (none) |
| Session and Agent Lock Recovery | recovery_capabilities | 52B-52D | implemented | pcae session-recovery; pcae agent-lock-recovery; pcae corruption-recovery | governed_task_contracts | (none) |
| Runtime Quarantine | multi_runtime_capabilities | 63F | implemented | pcae runtime-quarantine | runtime_failure_recovery | (none) |
| Capability Inventory | documentation_capabilities | 64B.0 | implemented | pcae capability-inventory | (none) | (none) |
| Capability and Roadmap Intelligence | capability_intelligence | 64B.1 | implemented | pcae capability list; pcae capability show; pcae capability dependencies; ... (8 total) | capability_inventory | (none) |
| Roadmap Recommendation Hardening | capability_intelligence | 64B.2 | implemented | pcae roadmap-recommendation-hardening; pcae roadmap next; pcae prompt next | capability_and_roadmap_intelligence | (none) |
| Capability Projection Consolidation | skill_system_capabilities | 64B.4B | implemented | pcae capability list; pcae capability show; pcae roadmap current | skill_registry_consolidation_hardening | (none) |
| Skill Invocation Targeting | skill_system_capabilities | 64B.5 | implemented | pcae skill invoke <skill_id> <target_id>; pcae skill invoke <skill_id> --target <target_id>; pcae skill invoke <skill_id> --target-type <type> --target <target_id>; ... (4 total) | skill_registry_consolidation_hardening | (none) |
| Prompt Rendering Skill | skill_system_capabilities | 64B.6 | implemented | pcae skill invoke phase-implementation <phase_id>; pcae skill invoke phase-validation <phase_id>; pcae skill invoke phase-agent <phase_id>; ... (6 total) | skill_invocation_targeting | (none) |
| Prompt Rendering Quality Hardening | skill_system_capabilities | 64B.6A | implemented | pcae skill invoke phase-implementation <phase_id>; pcae skill invoke phase-validation <phase_id>; pcae skill invoke phase-agent <phase_id>; ... (6 total) | prompt_rendering_skill | (none) |
| Dependency & Capability Intelligence Rendering | skill_system_capabilities | 64B.6B | implemented | pcae skill invoke phase-implementation <phase_id>; pcae skill invoke phase-validation <phase_id>; pcae skill invoke phase-agent <phase_id>; ... (6 total) | prompt_rendering_quality_hardening | (none) |
| Predecessor Capability Rendering | skill_system_capabilities | 64B.6C | implemented | pcae skill invoke phase-implementation <phase_id>; pcae skill invoke phase-validation <phase_id>; pcae skill invoke phase-agent <phase_id>; ... (6 total) | dependency_capability_intelligence_rendering | (none) |
| Command & Architecture Intelligence Rendering | skill_system_capabilities | 64B.6D | implemented | pcae skill invoke phase-implementation <phase_id>; pcae skill invoke phase-validation <phase_id>; pcae skill invoke phase-agent <phase_id>; ... (6 total) | predecessor_capability_rendering | (none) |
| Design Review Intelligence Rendering | skill_system_capabilities | 64B.6E | implemented | pcae skill invoke phase-implementation <phase_id>; pcae skill invoke phase-agent <phase_id> | command_architecture_intelligence_rendering | (none) |
| Capability Inventory Alignment | capability_intelligence | 64G | implemented | pcae runtime-coordination-policy; pcae runtime-coordination-policy --json; pcae capability-inventory | runtime_coordination_policy; capability_inventory | (none) |
| Strategic Roadmap Governance | strategic_governance | 65A | implemented | pcae strategic-roadmap-governance; pcae strategic-roadmap-governance --json | capability_inventory_alignment; capability_and_roadmap_intelligence | (none) |
| Strategic State Summary | strategic_governance | 65B | implemented | pcae strategic-state-summary; pcae strategic-state-summary --json | strategic_roadmap_governance | (none) |
| Strategic Governance Registry Alignment | strategic_governance | 65C | implemented | (none) | strategic_state_summary | (none) |
| Strategic Capability-Objective Bulk Mapping Governance | strategic_governance | 65D | implemented | pcae mapping-review-governance; pcae mapping-review-governance --json | strategic_governance_registry_alignment | (none) |
