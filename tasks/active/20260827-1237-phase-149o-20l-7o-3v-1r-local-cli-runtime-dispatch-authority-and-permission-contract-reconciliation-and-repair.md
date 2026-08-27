# Task Contract

## Task ID

20260827-1237-phase-149o-20l-7o-3v-1r-local-cli-runtime-dispatch-authority-and-permission-contract-reconciliation-and-repair

## Title

Phase 149O.20L.7O.3V.1R: Local-CLI Runtime Dispatch Authority and Permission Contract Reconciliation and Repair

## Status

active

## Mode

contract-repair

## Goal

Repair the two independently-verified BLOCKING contract defects from 3V.1 (RDGO gate-order contradiction with RPAC-REQ-042; PBRD/RDGO missing mandatory attempt_id/idempotency_key binding) via contract-text-only reconciliation, preserving all verified semantics. No implementation, no source changes, no execution activation.

## Allowed Files

- docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md
- docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md
- docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md
- docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md
- docs/PHASE_149O_20L_7O_3V_1R_LOCAL_CLI_RUNTIME_DISPATCH_AUTHORITY_PERMISSION_CONTRACT_RECONCILIATION_AND_REPAIR.md
- tests/test_phase_149o_20l_7o_3v_1r_contract_repair.py
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/done/20260827-1148-idle-awaiting-human-decision-post-149o-20l-7o-3v-1.md
- tasks/active/20260827-1237-phase-149o-20l-7o-3v-1r-local-cli-runtime-dispatch-authority-and-permission-contract-reconciliation-and-repair.md
- tasks/done/20260827-1237-phase-149o-20l-7o-3v-1r-local-cli-runtime-dispatch-authority-and-permission-contract-reconciliation-and-repair.md

## Forbidden Files

- src/pcae/**

## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

## Forbidden Changes

- TBD

## Acceptance Criteria

- Both 3V.1 BLOCKING findings are closed with textual evidence and no new contradictions introduced.
- No production source under src/pcae/** is modified; no runtime_dispatch constant, approval store/validator, RE/Shell Gate wiring, or process launch is added.
- Runtime remains Observed / observe / unavailable; POL-005 and dry path unchanged; API/network boundary unchanged.

## Acceptance Checks

- pcae runtime inspect remains Observed / observe / unavailable.
- git diff --stat shows no changes under src/pcae/

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-27T12:37:36.913936+02:00
