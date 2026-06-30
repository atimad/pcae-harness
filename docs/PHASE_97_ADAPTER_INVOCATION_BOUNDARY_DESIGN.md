# Phase 97C — Adapter Invocation Boundary Design

```
phase_name = phase_97c_adapter_boundary | phase_status = completed | implementation_status = design_only
recommended_next_phase = 97D — Human Approval Gate for Future Execution
```

## 1. Purpose

Design the adapter invocation boundary. Define how adapters are identified, constrained, validated, capability-declared, preflighted, denied, and prevented from executing. Design/boundary only.

## 2. Adapter Roles

| Role | Type | Authorizes |
|------|------|------------|
| Adapter identity | Evidence | Nothing |
| Capability declaration | Evidence | Nothing |
| Adapter invocation request | Contract | Nothing |
| Adapter preflight | Assessment | Nothing |
| Adapter denial | Assessment | Nothing |
| Output capture | Evidence | Nothing |
| Credential reference | Redacted presence indicator | Nothing |

## 3. Adapter Identity Schema (Design)

adapter_id, name, type, version, provider_family, backend_family, supported/forbidden operation classes, capability declaration ref, configuration ref, identity digest. No credentials persisted. `simulation_only: true`, `no_execution: true`.

## 4. Capability Declaration Schema (Design)

supported/forbidden operations, input/output artifact types, size policies. All execution flags forced false: network_required, subprocess_required, shell_required, filesystem_mutation_required, apply_supported, commit_supported, push_supported, telegram_inbound_supported. `execution_available: false`, `adapter_execution_available: false`.

## 5. Adapter Invocation Request Boundary

References 97B backend request + readiness + evidence chain. All mutation/network/subprocess/shell/apply/commit/push flags forced false. `adapter_execution_authorized: false`. `simulation_only: true`.

## 6. Adapter Preflight Boundary

Assesses without executing. All authorization flags forced false. No "invoke now" status.

## 7. Denial Statuses (25)

12 from 97B + adapter-specific: denied_missing_adapter_identity, denied_invalid_adapter_identity, denied_missing_capability_declaration, denied_capability_mismatch, denied_forbidden_operation, denied_network_requested, denied_subprocess_requested, denied_shell_requested, denied_mutation_requested, denied_apply_requested, denied_commit_requested, denied_push_requested, denied_telegram_inbound_requested, denied_secret_material_detected.

## 8. Fail-Closed

No adapter/backend call, no subprocess/network/shell, no apply/commit/push. Write non-authorizing denial evidence only.

## 9. Secret-Handling

No credential material persisted. No token/API key in artifacts. Credential ref is redacted presence only. Secret-like values cause denial.

## 10. Next: 97D — Human Approval Gate for Future Execution. No execution.
