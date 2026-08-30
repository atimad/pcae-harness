# Runtime Enforcement No-Go Registry

**Schema version**: 1.1 | **Frozen by**: Phase 104B; classification column added by Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 (V-13-3-2) | **Format**: RE-NOGO-NNN

## Purpose

Canonical registry of execution-blocking no-go conditions for the PCAE runtime-enforcement stack. Future phases reference stable IDs instead of copying long prose.

## Registry

**Enforcement class (schema 1.1 — additive; V-13-3-2).** Each entry is one of:

- **per-decision** — projected per runtime-dispatch decision from an authorization/safety flag by the shared design contract `runtime_enforcement_safety_authorization.py` (Phase 104C). These are the ids that populate `Gate7Result.matched_no_go_ids`.
- **environmental-readiness** — an infrastructure-capability gap enforced by the execution-enablement readiness process (`docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md`), not by a per-decision Gate-7 projection.
- **advisory** — non-blocking; informational only.

| ID | Category | Title | Blocks Enforcement | Blocks Execution | Enforcement class (1.1) | Required Resolution |
|---|---|---|---|---|---|---|
| RE-NOGO-001 | runtime_enforcement_absent | No Runtime Enforcement Implementation | Yes | Yes | per-decision | Design separate implementation track |
| RE-NOGO-002 | execution_boundary_absent | No Execution-Capable Boundary | Yes | Yes | per-decision | Design explicit execution boundary |
| RE-NOGO-003 | backend_invocation_absent | No Real Backend Invocation | Yes | Yes | per-decision | Implement governed backend invocation |
| RE-NOGO-004 | adapter_execution_absent | No Adapter Execution | Yes | Yes | per-decision | Implement adapter execution governance |
| RE-NOGO-005 | shell_subprocess_network_absent | No Shell/Subprocess/Network Mediation | Yes | Yes | per-decision | Implement shell/subprocess/network boundary |
| RE-NOGO-006 | apply_patch_absent | No Apply Execution Governance | Yes | Yes | per-decision | Implement apply/change governance |
| RE-NOGO-007 | rollback_execution_absent | No Rollback Execution Governance | Yes | Yes | per-decision | Implement rollback governance |
| RE-NOGO-008 | commit_push_authorization_absent | No Commit/Push Authorization | Yes | Yes | per-decision | Implement commit/push governance |
| RE-NOGO-009 | audit_persistence_absent | No Audit Database or Persistent Trail | Yes | Yes | environmental-readiness | Implement audit persistence |
| RE-NOGO-010 | execution_enablement_absent | No Execution Enablement Design | Yes | Yes | per-decision | Design explicit execution enablement |
| RE-NOGO-011 | end_to_end_safety_proof_absent | No End-to-End Runtime Safety Proof | Yes | Yes | per-decision | Produce end-to-end safety proof |
| RE-NOGO-012 | pre_existing_test_failures | Pre-Existing Fast-Green Failures | Advisory | Advisory | advisory | Resolve Test94UPreflightArtifact, Test94UPreflightArtifactCLI, TestBackendShow |
| RE-NOGO-013 | telegram_inbound_absent | No Telegram Inbound Control | Yes | Yes | environmental-readiness | Design outbound-only confirmation |
| RE-NOGO-014 | task_memory_warnings | pcae_doctor_task_memory Warnings | Advisory | Advisory | advisory | Resolve stale task entries |
| RE-NOGO-015 | emergency_abort_absent | No Emergency Abort Behavior | Yes | Yes | environmental-readiness | Design emergency abort mechanism |
| RE-NOGO-016 | output_capture_absent | No Output Capture/Redaction | Yes | Yes | environmental-readiness | Implement output capture governance |
| RE-NOGO-017 | recovery_procedure_absent | No Recovery for Partial Failure | Yes | Yes | environmental-readiness | Design recovery procedures |

**Scoping (schema 1.1).** Gate 7's `Gate7Result.matched_no_go_ids` projects
only the **per-decision** subset (RE-NOGO-001–008, 010, 011 — the ids the
shared authorization/safety flag→no-go map covers). The
**environmental-readiness** ids (009, 013, 015, 016, 017) are enforced by
the execution-enablement readiness process
(`V0_2_EXECUTION_READINESS_NO_GO_GATES.md`) and are deliberately out of
scope for the per-decision RE projection — not an omission. RE-NOGO-012 /
014 are advisory. Gate-7 progression depends on the authoritative Gate-7
decision, **not** on the completeness of `matched_no_go_ids` (a trusted
ALLOW with a deliberately incomplete no-go list still proceeds; the
per-decision brakes that force DENY are independent). `.1R.13.1` §13's
"sole source" wording is corrected to "the sole source *for the
per-decision projection*".

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

**Schema 1.0 → 1.1 (Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 — V-13-3-2).**
Additive: an "Enforcement class" column (per-decision / environmental-readiness
/ advisory) and a scoping paragraph. No ID, title, category, blocking
verdict, or canonical statement changed; no entry added, removed, or
re-classified as blocking/non-blocking. Purely a classification annotation so
a reader can see that `Gate7Result.matched_no_go_ids`'s scope
(per-decision only) is deliberate.

---
*Frozen by Phase 104B; schema 1.1 classification annotation by Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4. No runtime enforcement. No execution. Registry is evidence/contract only.*
