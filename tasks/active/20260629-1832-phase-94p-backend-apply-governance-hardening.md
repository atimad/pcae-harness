# Task Contract

## Task ID

20260629-1832-phase-94p-backend-apply-governance-hardening

## Title

Phase 94P — Backend Apply Governance Hardening

## Status

active

## Mode

implementation

## Goal

Harden backend review/apply governance chain against negative cases, stale artifacts,
malformed artifacts, contradictory metadata, unsafe paths, unsafe packages, and
trust/reporting drift. Strengthen validation, tests, and documentation.

## Allowed Files

- src/pcae/core/backend_invocations.py
- src/pcae/commands/backend.py
- tests/test_backend_invocations.py
- tests/test_backend_cli.py
- docs/PHASE_94_BACKEND_APPLY_GOVERNANCE_HARDENING.md
- PROJECT_STATUS.md
- CHANGELOG.md
- pyproject.toml
- tasks/active/20260629-1832-phase-94p-backend-apply-governance-hardening.md
- tasks/done/**
- tasks/DONE.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json

## Forbidden Files

- src/pcae/core/apply_execution.py
- src/pcae/core/patch_parser.py

## Override Protected Files

- pyproject.toml

## Allowed Zones

- core
- commands
- cli
- package
- tests
- docs
- tasks
- config

## Enforcement Mode

advisory

## Forbidden Changes

- No apply execution
- No patch parsing for mutation
- No file mutation outside .pcae/ artifact dirs
- No backend invocation
- No subprocess execution
- No network calls
- No shell interception or wrappers
- No command mediation
- No Telegram inbound commands
- No remote shell or /run
- No enforcement
- No autonomous mutation
- No automatic apply
- No real AI backend calls
- No automatic test execution
- No automatic pcae check
- No commit
- No push
- No commit/push authorization
- No new product features beyond hardening

## Acceptance Criteria

- validate_operation_path() hard-blocks absolute/traversal/empty/forbidden paths
- validate_hash_chain() hard-blocks hash mismatches across all artifact pairs
- approve_review() rejects already-rejected reviews
- package cannot hide hard blocks
- 60+ new tests all pass
- All regressions pass

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest tests/test_backend_invocations.py tests/test_backend_cli.py -q passes

## Created Timestamp

2026-06-29T18:32:46.715387+02:00
