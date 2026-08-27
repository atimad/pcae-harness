# Task Contract

## Task ID

20260827-1357-phase-149o-20l-7o-3w-runtime-invocation-authority-pb-dispatch-request-foundation-implementation

## Title

Phase 149O.20L.7O.3W: Runtime Invocation Authority + PB Dispatch Request Foundation Implementation

## Status

active

## Mode

implementation

## Goal

Implement RIHAC-001/RIASC-001 authority foundation and PBRD-001 v1.1 runtime_dispatch PB request architecture per 3V.2's blueprint, without activating execution; POL-005 stays hard deny.

## Allowed Files

- src/pcae/core/runtime_authority.py
- src/pcae/core/runtime_invocation_approval_store.py
- src/pcae/core/runtime_dispatch_permission.py
- src/pcae/core/permission_broker_foundation.py
- src/pcae/core/runtime_invocation.py
- tests/_rdw3w_helpers.py
- tests/test_runtime_authority_model.py
- tests/test_runtime_authority_validation.py
- tests/test_runtime_invocation_approval_store.py
- tests/test_runtime_dispatch_permission.py
- tests/test_runtime_dispatch_attempt_idempotency.py
- tests/test_runtime_dispatch_no_external_effect.py
- tests/test_runtime_dispatch_regression_dry_path.py
- tests/test_runtime_dispatch_regression_pb_actions.py
- docs/PHASE_149O_20L_7O_3W_RUNTIME_INVOCATION_AUTHORITY_AND_PB_DISPATCH_REQUEST_FOUNDATION_IMPLEMENTATION.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/DONE.md
- PROJECT_STATUS.md
- tasks/done/20260827-1319-idle-awaiting-human-decision-post-149o-20l-7o-3v-2.md

## Forbidden Files

- TBD


## Allowed Zones

- TBD

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

- RuntimeInvocationApproval model + RIASC-001 validator + canonical store implemented
- runtime_dispatch PB request architecture (Option B) implemented, POL-005 unchanged hard deny
- Zero subprocess/network/credential access in new modules; Fast Green 0 attributable regressions

## Acceptance Checks

- python -m pytest tests/test_runtime_authority_model.py tests/test_runtime_authority_validation.py tests/test_runtime_invocation_approval_store.py tests/test_runtime_dispatch_permission.py tests/test_runtime_dispatch_attempt_idempotency.py tests/test_runtime_dispatch_no_external_effect.py tests/test_runtime_dispatch_regression_dry_path.py tests/test_runtime_dispatch_regression_pb_actions.py -q

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-27T13:57:52.179170+02:00
