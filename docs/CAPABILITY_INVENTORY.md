# PCAE Capability Inventory

Generated: 2026-06-08T15:38:38.485880+00:00
Phase: 64B.0 — Capability Inventory
Total capabilities: 18
Implemented: 15
Dormant: 1
Superseded: 1
Roadmap gaps: 1
Duplicates/overlaps: 1
Prompt capabilities: 1
Assessment status: inventory_with_gaps

## Capability Records

| Capability | Domain | Phase | Status | Commands | Dependencies | Successors |
|---|---|---|---|---|---|---|
| Governed Task Contracts | governance_capabilities | 44A-46J | implemented | pcae task new; pcae task close; pcae task transition | (none) | task_lifecycle_governance |
| Task Lifecycle Governance | task_lifecycle_capabilities | 52A | implemented | pcae task-lifecycle-hardening; pcae task transition | governed_task_contracts | (none) |
| Multi-Agent Roadmap Generation | roadmap_capabilities | 45A-45E | implemented | pcae roadmap; pcae multi-agent-roadmap; pcae roadmap-evidence | governed_task_contracts | capability_inventory |
| Phase Prompt Generation | prompt_generation_capabilities | 45A-45E | implemented | pcae prompt-render; pcae autonomous-prompt-proposal; pcae prompt-validation-design; pcae prompt-governance-design | multi_agent_roadmap_generation | (none) |
| Read-Only Runtime Invocation Governance | runtime_governance_capabilities | 55A-57A | implemented | pcae readonly-invocation; pcae read-only-runtime-invocation; pcae runtime-review-workflow | governed_task_contracts | runtime_approval_gates |
| Invocation Pilot (Legacy) | runtime_governance_capabilities | 46A-46J | superseded | pcae invocation-pilot; pcae multi-runtime-pilot | (none) | read_only_runtime_invocation_governance |
| Controlled Runtime Execution Pilot | runtime_execution_capabilities | 62A | dormant | pcae runtime-execution-pilot | read_only_runtime_invocation_governance | multi_runtime_execution_planning |
| Runtime Audit Persistence | runtime_audit_capabilities | 62C | implemented | pcae runtime-audit-persistence | read_only_runtime_invocation_governance | multi_runtime_audit_chain |
| Runtime Review Decision Record | runtime_review_capabilities | 62F | implemented | pcae runtime-review-decision | runtime_audit_persistence | runtime_approval_gates |
| Runtime Approval Gates | runtime_approval_capabilities | 62G | implemented | pcae runtime-approval-gates | runtime_review_decision_record | multi_runtime_registry |
| Runtime Rollback Boundaries | runtime_rollback_capabilities | 62H | implemented | pcae runtime-rollback-boundaries | runtime_approval_gates | runtime_failure_recovery |
| Multi-Runtime Execution Planning | multi_runtime_capabilities | 64A | implemented | pcae multi-runtime-execution-planning | multi_runtime_registry; runtime_selection_engine; runtime_arbitration | multi_runtime_execution_readiness |
| Multi-Runtime Orchestration Execution | orchestration_capabilities | 64C+ | roadmap_gap | (none) | multi_runtime_execution_readiness | (none) |
| Repository Health Governance | repository_governance_capabilities | 44A | implemented | pcae health; pcae check; pcae status coherence | (none) | task_state_alignment |
| Commands Reference Generation | documentation_capabilities | 53A | implemented | pcae docs commands | (none) | capability_inventory |
| Phase-Scoped Test Selection | testing_capabilities | 44A+ | implemented | python -m pytest -k <phase_id>; python -m pytest -n auto | (none) | (none) |
| Session and Agent Lock Recovery | recovery_capabilities | 52B-52D | implemented | pcae session-recovery; pcae agent-lock-recovery; pcae corruption-recovery | governed_task_contracts | runtime_failure_recovery |
| Runtime Quarantine Classification | quarantine_capabilities | 63F | implemented | pcae runtime-quarantine | runtime_failure_recovery | (none) |

## Governance Notes

- 64B.0 creates a capability inventory.
- 64B.0 does not modify roadmap behavior.
- 64B.0 does not modify task lifecycle behavior.
- 64B.0 does not modify runtime behavior.
- 64B.0 is prerequisite for 64B.1 Capability and Roadmap Intelligence.

*Phase 64B.0 creates an authoritative inventory of all PCAE capabilities. Discovery and governance only; no behavior modified. capability_count=18. implemented_count=15. dormant_count=1. superseded_count=1. roadmap_gap_count=1. duplicate_count=1. prompt_capability_count=1. assessment_status=inventory_with_gaps. Prerequisite for 64B.1 Capability and Roadmap Intelligence.*
