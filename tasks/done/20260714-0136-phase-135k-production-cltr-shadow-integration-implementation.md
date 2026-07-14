# Task Contract

## Task ID

20260714-0136-phase-135k-production-cltr-shadow-integration-implementation

## Title

Phase 135K: Production CLTR Shadow Integration Implementation

## Status

done

## Mode

implementation

## Goal

Implement the first production CLTR integration in strict shadow mode: production package (src/pcae/cltr), schema v1.0.1, typed model, 37 invariants, canonicalization/digest, immutable shadow persistence with atomic pointer, 15 representation adapters, integration with all four production finalization entry points behind a feature flag, read-only CLI, and tests.

## Allowed Files

- src/pcae/cltr/**
- src/pcae/commands/cltr_shadow.py
- src/pcae/cli.py
- src/pcae/core/finalization_transaction.py
- src/pcae/commands/phase.py
- src/pcae/commands/task.py
- src/pcae/commands/phase_reports.py
- src/pcae/commands/notifications.py
- tests/test_cltr_*.py
- tests/conftest.py
- docs/PHASE_135_PRODUCTION_CLTR_SHADOW_INTEGRATION_IMPLEMENTATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/**
- .pcae/policy.toml
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- TBD


## Allowed Zones

- core
- commands
- cli
- tests
- docs
- tasks
- cltr
- policy
- config

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

- Production src/pcae/cltr package implements CLTR-SCHEMA-001 v1.0.1 exactly (14 states, 16 transitions, 14 forbidden transitions, 37 invariants, 15 representation kinds)
- Shadow integration attached to all four production finalization entry points via the shared finalization transaction, behind PCAE_CLTR_SHADOW_ENABLED, never gating production success
- No production lifecycle authority, promotion, notification, marker, or receipt control introduced
- Focused CLTR tests, affected lifecycle regression tests, and Fast Green all pass

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-14T01:36:38.052387+02:00
