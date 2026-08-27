# Task Contract

## Task ID

20260827-1602-phase-149o-20l-7o-3w-1r-runtime-invocation-authority-pb-dispatch-foundation-blocking-repair

## Title

Phase 149O.20L.7O.3W.1R: Runtime Invocation Authority + PB Dispatch Foundation Blocking Repair

## Status

done

## Mode

strict

## Goal

Close exactly the seven independently verified 3W.1 authority/PB blockers under frozen contracts, preserve POL-005 and execution unavailability, verify by fixed-SHA attribution, document and push, then stop for human review

## Allowed Files

- src/pcae/core/runtime_authority.py
- src/pcae/core/runtime_invocation_approval_store.py
- src/pcae/core/runtime_dispatch_permission.py
- src/pcae/core/permission_broker_foundation.py
- tests/_rdw3w_helpers.py
- tests/test_runtime_authority_model.py
- tests/test_runtime_authority_validation.py
- tests/test_runtime_invocation_approval_store.py
- tests/test_runtime_dispatch_permission.py
- tests/test_runtime_dispatch_attempt_idempotency.py
- tests/test_runtime_dispatch_no_external_effect.py
- tests/test_runtime_dispatch_regression_dry_path.py
- tests/test_runtime_dispatch_regression_pb_actions.py
- tests/test_runtime_authority_pb_verification_3w1.py
- tests/test_runtime_authority_pb_repair_3w1r.py
- docs/PHASE_149O_20L_7O_3W_1R_RUNTIME_INVOCATION_AUTHORITY_PB_DISPATCH_FOUNDATION_BLOCKING_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active/20260827-1602-phase-149o-20l-7o-3w-1r-runtime-invocation-authority-pb-dispatch-foundation-blocking-repair.md
- tasks/active/**
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json
- .pcae/session.json

## Forbidden Files

- TBD


## Allowed Zones

- core
- tests
- docs
- tasks
- config
- session

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

- Exactly seven 3W.1 blockers are recovered verbatim, reproduced, and CLOSED without normative contract change
- POL-005 remains byte/source-identical and hard DENY; approval consumption and Runtime Enforcement remain unimplemented
- No runtime subprocess, network/provider, credential, external-runtime, background-runtime, or runtime-source-mutation effects
- UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS = 0 under safe fixed-SHA partitioning
- Canonical report is complete, repository is clean/pushed/zero-ahead, runtime remains Observed/observe/unavailable

## Acceptance Checks

- pytest -q tests/test_runtime_authority_model.py tests/test_runtime_authority_validation.py tests/test_runtime_invocation_approval_store.py tests/test_runtime_dispatch_permission.py tests/test_runtime_dispatch_attempt_idempotency.py tests/test_runtime_dispatch_no_external_effect.py tests/test_runtime_dispatch_regression_dry_path.py tests/test_runtime_dispatch_regression_pb_actions.py tests/test_runtime_authority_pb_verification_3w1.py tests/test_runtime_authority_pb_repair_3w1r.py
- pcae health
- pcae check
- pcae status coherence
- pcae doctor task-memory
- pcae runtime inspect

Lifecycle note: `pcae push check` is the post-closure governance gate because its
phase-identity check requires this task to be in completed state. It remains a
mandatory final check under the acceptance criteria above.

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-27T16:02:14.233464+02:00
