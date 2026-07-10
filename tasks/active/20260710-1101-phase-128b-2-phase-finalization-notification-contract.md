# Task Contract

## Task ID

20260710-1101-phase-128b-2-phase-finalization-notification-contract

## Title

Phase 128B.2 Phase Finalization Notification Contract

## Status

active

## Mode

documentation

## Goal

Define the canonical Phase Finalization Notification Contract (PFN-001): notification is a governed lifecycle invariant, not an implementation detail. Governance documentation only -- no implementation, no schema changes, no notification implementation changes, no Repository Intelligence or Historical Memory changes.

## Allowed Files

- docs/PHASE_128_PHASE_FINALIZATION_NOTIFICATION_CONTRACT.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260710-1101-phase-128b-2-phase-finalization-notification-contract.md

## Forbidden Files

- TBD


## Allowed Zones

- docs
- tasks

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- Defines PFN-001: every terminal phase outcome produces exactly one trusted canonical phase report delivered to the configured notification sink; silent omission prohibited
- Defines canonical report authority: notification always reflects the trusted canonical report, never console output/temporary summaries/partial metadata/ad hoc messages
- Covers all terminal outcomes: completed, partially completed, incomplete, failed, blocked, governance-aborted, trusted recovery paths
- Defines the finalization lifecycle placing notification inside finalization, not as a post-finalization side effect
- Defines delivery guarantees (exactly-once, trusted-report-only, ordering, path-identical, idempotent, duplicate prevention) and failure guarantees (durable, observable, never invalidates canonical report)
- No implementation, schema, source code, test code, or runtime behavior change; runtime remains Observed/observe/execution-unavailable

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T11:01:36.222171+02:00
