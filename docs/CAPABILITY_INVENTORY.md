# PCAE Capability Inventory

Generated: 2026-06-09T17:59:16.786899+00:00
Phase: 64B.0 — Capability Inventory
Total capabilities: 24
Implemented: 22
Dormant: 1
Superseded: 1
Roadmap gaps: 0
Duplicates/overlaps: 3
Prompt capabilities: 2
Assessment status: inventory_with_duplicates

## Capability Records

| Capability | Domain | Phase | Status | Commands | Dependencies | Successors |
|---|---|---|---|---|---|---|
| Governed Task Contracts | governance_capabilities | 44A-46J | implemented | pcae task new; pcae task close; pcae task transition | (none) | task_lifecycle_governance |
| Task Lifecycle Governance | task_lifecycle_capabilities | 52A | implemented | pcae task-lifecycle-hardening; pcae task transition | governed_task_contracts | (none) |
| Multi-Agent Roadmap Generation | roadmap_capabilities | 45A-45E | implemented | pcae roadmap; pcae multi-agent-roadmap; pcae roadmap-evidence | governed_task_contracts | capability_inventory |
| Phase Prompt Generation | prompt_generation_capabilities | 45A-45E | implemented | pcae prompt-render; pcae autonomous-prompt-proposal; pcae prompt-validation-design; pcae prompt-governance-design | multi_agent_roadmap_generation | (none) |
| Prompt Recommendation Hardening | prompt_intelligence_capabilities | 64B.3 | implemented | pcae prompt next; pcae prompt phase; pcae prompt validate | capability_and_roadmap_intelligence; roadmap_recommendation_hardening | (none) |
| Skill System Foundation | skill_system_capabilities | 64B.4 | implemented | pcae skill list; pcae skill show; pcae skill validate; pcae skill invoke | capability_and_roadmap_intelligence; prompt_recommendation_hardening | skill_registry_consolidation_hardening |
| Skill Registry Consolidation Hardening | skill_system_capabilities | 64B.4A | implemented | pcae skill list; pcae skill show; pcae skill validate; pcae skill invoke; pcae capability-inventory; pcae roadmap current; pcae prompt validate | skill_system_foundation; capability_and_roadmap_intelligence | (none) |
| Read-Only Runtime Invocation Governance | runtime_governance_capabilities | 55A-57A | implemented | pcae readonly-invocation; pcae read-only-runtime-invocation; pcae runtime-review-workflow | governed_task_contracts | runtime_approval_gates |
| Invocation Pilot (Legacy) | runtime_governance_capabilities | 46A-46J | superseded | pcae invocation-pilot; pcae multi-runtime-pilot | (none) | read_only_runtime_invocation_governance |
| Controlled Runtime Execution Pilot | runtime_execution_capabilities | 62A | dormant | pcae runtime-execution-pilot | read_only_runtime_invocation_governance | multi_runtime_execution_planning |
| Runtime Audit Persistence | runtime_audit_capabilities | 62C | implemented | pcae runtime-audit-persistence | read_only_runtime_invocation_governance | multi_runtime_audit_chain |
| Runtime Review Decision Record | runtime_review_capabilities | 62F | implemented | pcae runtime-review-decision | runtime_audit_persistence | runtime_approval_gates |
| Runtime Approval Gates | runtime_approval_capabilities | 62G | implemented | pcae runtime-approval-gates | runtime_review_decision_record | multi_runtime_registry |
| Runtime Rollback Boundaries | runtime_rollback_capabilities | 62H | implemented | pcae runtime-rollback-boundaries | runtime_approval_gates | runtime_failure_recovery |
| Multi-Runtime Execution Planning | multi_runtime_capabilities | 64A | implemented | pcae multi-runtime-execution-planning | multi_runtime_registry; runtime_selection_engine; runtime_arbitration | multi_runtime_execution_readiness |
| Multi-Runtime Orchestration Execution | multi_runtime_capabilities | 64C | implemented | pcae multi-runtime-orchestration-execution; pcae multi-runtime-orchestration-execution --json | multi_runtime_execution_readiness | runtime_coordination_policy |
| Runtime Coordination Policy | multi_runtime_capabilities | 64D | implemented | (none) | multi_runtime_orchestration_execution | orchestration_audit_model |
| Orchestration Audit Model | multi_runtime_capabilities | 64E | implemented | pcae orchestration-audit-model; pcae orchestration-audit-model --json | runtime_coordination_policy; multi_runtime_audit_chain | orchestration_readiness_gate |
| Orchestration Readiness Gate | multi_runtime_capabilities | 64F | implemented | pcae orchestration-readiness-gate; pcae orchestration-readiness-gate --json | multi_runtime_orchestration_execution; runtime_coordination_policy; orchestration_audit_model | multi_runtime_execution_dispatch |
| Repository Health Governance | repository_governance_capabilities | 44A | implemented | pcae health; pcae check; pcae status coherence | (none) | task_state_alignment |
| Commands Reference Generation | documentation_capabilities | 53A | implemented | pcae docs commands | (none) | capability_inventory |
| Phase-Scoped Test Selection | testing_capabilities | 44A+ | implemented | python -m pytest -k <phase_id>; python -m pytest -n auto | (none) | (none) |
| Session and Agent Lock Recovery | recovery_capabilities | 52B-52D | implemented | pcae session-recovery; pcae agent-lock-recovery; pcae corruption-recovery | governed_task_contracts | runtime_failure_recovery |
| Runtime Quarantine Classification | quarantine_capabilities | 63F | implemented | pcae runtime-quarantine | runtime_failure_recovery | (none) |

## Governance Notes

- 64B.0 creates a capability inventory.
- 64B.3 adds prompt recommendation hardening as an implemented capability.
- 64B.4 adds a first-class skill system as an implemented capability.
- Skill Registry metadata is consolidated with the shared intelligence infrastructure.
- 64B.0 does not modify roadmap behavior.
- 64B.0 does not modify task lifecycle behavior.
- 64B.0 does not modify runtime behavior.
- 64B.0 is prerequisite for 64B.1 Capability and Roadmap Intelligence.

*Phase 64B.0 creates an authoritative inventory of all PCAE capabilities. Discovery and governance only; no behavior modified. capability_count=24. implemented_count=22. dormant_count=1. superseded_count=1. roadmap_gap_count=0. duplicate_count=3. prompt_capability_count=2. assessment_status=inventory_with_duplicates. Prerequisite for 64B.1 Capability and Roadmap Intelligence.*
