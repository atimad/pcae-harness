# Runtime Enforcement No-Go Registry

**Schema version**: 1.0 | **Frozen by**: Phase 104B | **Format**: RE-NOGO-NNN

## Purpose

Canonical registry of execution-blocking no-go conditions for the PCAE runtime-enforcement stack. Future phases reference stable IDs instead of copying long prose.

## Registry

| ID | Category | Title | Blocks Enforcement | Blocks Execution | Required Resolution |
|---|---|---|---|---|---|
| RE-NOGO-001 | runtime_enforcement_absent | No Runtime Enforcement Implementation | Yes | Yes | Design separate implementation track |
| RE-NOGO-002 | execution_boundary_absent | No Execution-Capable Boundary | Yes | Yes | Design explicit execution boundary |
| RE-NOGO-003 | backend_invocation_absent | No Real Backend Invocation | Yes | Yes | Implement governed backend invocation |
| RE-NOGO-004 | adapter_execution_absent | No Adapter Execution | Yes | Yes | Implement adapter execution governance |
| RE-NOGO-005 | shell_subprocess_network_absent | No Shell/Subprocess/Network Mediation | Yes | Yes | Implement shell/subprocess/network boundary |
| RE-NOGO-006 | apply_patch_absent | No Apply Execution Governance | Yes | Yes | Implement apply/change governance |
| RE-NOGO-007 | rollback_execution_absent | No Rollback Execution Governance | Yes | Yes | Implement rollback governance |
| RE-NOGO-008 | commit_push_authorization_absent | No Commit/Push Authorization | Yes | Yes | Implement commit/push governance |
| RE-NOGO-009 | audit_persistence_absent | No Audit Database or Persistent Trail | Yes | Yes | Implement audit persistence |
| RE-NOGO-010 | execution_enablement_absent | No Execution Enablement Design | Yes | Yes | Design explicit execution enablement |
| RE-NOGO-011 | end_to_end_safety_proof_absent | No End-to-End Runtime Safety Proof | Yes | Yes | Produce end-to-end safety proof |
| RE-NOGO-012 | pre_existing_test_failures | Pre-Existing Fast-Green Failures | Advisory | Advisory | Resolve Test94UPreflightArtifact, Test94UPreflightArtifactCLI, TestBackendShow |
| RE-NOGO-013 | telegram_inbound_absent | No Telegram Inbound Control | Yes | Yes | Design outbound-only confirmation |
| RE-NOGO-014 | task_memory_warnings | pcae_doctor_task_memory Warnings | Advisory | Advisory | Resolve stale task entries |
| RE-NOGO-015 | emergency_abort_absent | No Emergency Abort Behavior | Yes | Yes | Design emergency abort mechanism |
| RE-NOGO-016 | output_capture_absent | No Output Capture/Redaction | Yes | Yes | Implement output capture governance |
| RE-NOGO-017 | recovery_procedure_absent | No Recovery for Partial Failure | Yes | Yes | Design recovery procedures |

## Categories

- `runtime_enforcement_absent` — Runtime enforcement not implemented
- `execution_boundary_absent` — No execution boundary exists
- `backend_invocation_absent` — No real backend invocation
- `adapter_execution_absent` — No adapter execution
- `shell_subprocess_network_absent` — No shell/subprocess/network
- `apply_patch_absent` — No apply/patch execution
- `rollback_execution_absent` — No rollback execution
- `commit_push_authorization_absent` — No commit/push authorization
- `audit_persistence_absent` — No audit persistence
- `approval_enforcement_absent` — No approval enforcement
- `execution_enablement_absent` — No execution enablement
- `telegram_inbound_absent` — No Telegram inbound
- `report_trust_required` — Report trust checks required
- `artifact_trust_required` — Artifact trust verification required
- `pre_existing_test_failures` — Known test failures
- `task_memory_warnings` — Task memory warnings

## Reference Strategy

Future phases reference entries as: `RE-NOGO-NNN` with optional short title.
Long prose blocks should reference the registry rather than copy.
Historical prose remains valid but should not be duplicated.

## Compatibility

- IDs are stable once frozen
- Titles may be clarified without ID changes
- Canonical statements amended only via versioned change
- Removed entries must remain tombstoned
- Additive only unless dedicated migration phase

---
*Frozen by Phase 104B. No runtime enforcement. No execution. Registry is evidence/contract only.*
