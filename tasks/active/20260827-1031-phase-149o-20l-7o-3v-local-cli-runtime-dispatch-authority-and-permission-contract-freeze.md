# Task Contract

## Task ID

20260827-1031-phase-149o-20l-7o-3v-local-cli-runtime-dispatch-authority-and-permission-contract-freeze

## Title

Phase 149O.20L.7O.3V: Local-CLI Runtime Dispatch Authority and Permission Contract Freeze

## Status

active

## Mode

contract-freeze

## Goal

Freeze exactly four separate normative local-CLI-v1 contract artifacts for a future human-authorized real runtime invocation—human authority, PB runtime_dispatch extension, 11-gate ordering, and RuntimeInvocationApproval schema contract—without implementing or activating execution; preserve the existing dry path and all semantic walls.

## Allowed Files

- docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md
- docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md
- docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md
- docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md
- docs/PHASE_149O_20L_7O_3V_LOCAL_CLI_RUNTIME_DISPATCH_AUTHORITY_AND_PERMISSION_CONTRACT_FREEZE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DECISIONS.md
- tasks/DONE.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/20260827-1031-phase-149o-20l-7o-3v-local-cli-runtime-dispatch-authority-and-permission-contract-freeze.md
- tasks/done/20260827-1031-phase-149o-20l-7o-3v-local-cli-runtime-dispatch-authority-and-permission-contract-freeze.md
- tasks/done/20260827-1004-idle-awaiting-human-decision-post-149o-20l-7o-3u.md

## Forbidden Files

- src/pcae/**
- tests/**

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

- No runtime invocation
- No prompt execution
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No ungoverned commit or push; governed phase commit/push is required by acceptance checks
- No rollback

## Acceptance Criteria

- Exactly four separate normative local-CLI-v1 contract artifacts are frozen with consistent identifiers, bindings, freshness, crash/retry, gate ordering, and security invariants.
- API/provider/network contracts remain not frozen; POL-005, dry simulation, runtime state, and v0.4.3 remain unchanged.
- No production source, production tests, executable schema package, runtime dispatch action implementation, approval storage/CLI, or execution activation is introduced.

## Acceptance Checks

- Contract/static verification passes and all required matrices/field counts/gate counts/freshness counts/durable-item counts are present.
- git diff --stat -- src/pcae tests is empty.
- pcae health, check, status coherence, doctor task-memory, push check, runtime inspect, and notify status are recorded; final tree is clean, pushed, and zero ahead.

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-27T10:31:19.305274+02:00
