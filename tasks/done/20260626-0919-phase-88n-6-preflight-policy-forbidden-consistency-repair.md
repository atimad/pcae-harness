# Task Contract

## Task ID

20260626-0919-phase-88n-6-preflight-policy-forbidden-consistency-repair

## Title

Phase 88N.6 — Preflight Policy-Forbidden Consistency Repair

## Status

done

## Mode

implementation

## Goal

Restore full-suite green baseline by merging _SPF_POLICY_FORBIDDEN_FILES into mutation_preflight, backend_preflight, and gate_dry_run scope evaluation. Fix 10 test failures caused by policy-forbidden files not being enforced consistently.

## Allowed Files

- src/pcae/core/mutation_preflight.py
- src/pcae/core/backend_preflight.py
- src/pcae/core/gate_dry_run.py
- docs/PHASE_88_PREFLIGHT_POLICY_FORBIDDEN_CONSISTENCY_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/DONE.md

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

- TBD

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-26T09:19:23.051997+02:00
