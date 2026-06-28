# Task Contract

## Task ID

20260628-1107-89a-advisory-mode-hardening-false-positive-repair

## Title

89A — Advisory Mode Hardening / False-Positive Repair

## Status

active

## Mode

implementation

## Goal

Fix known advisory/shell-gate classification issues: bash/sh/zsh unknown false positives, env python over-classification, compact pipe/operator tokenizer limitation.

## Allowed Files

- src/pcae/core/shell_gate.py
- src/pcae/core/advisory.py
- src/pcae/commands/advisory.py
- tests/test_shell_gate_matrix.py
- tests/test_broker_shell_gate_integration.py
- tests/test_broker_shell_gate_edge_cases.py
- tests/test_advisory_mode.py
- docs/PHASE_89_ADVISORY_MODE_HARDENING_FALSE_POSITIVE_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**

## Forbidden Files

- src/pcae/core/gate_dry_run.py
- src/pcae/core/gate_dry_run_context.py
- src/pcae/core/project_state.py
- .githooks/**
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md


## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

advisory

## Forbidden Changes

- TBD

## Acceptance Criteria

- Known false positives reproduced and fixed
- Known false negative reproduced and fixed
- Shell command classification improved
- Compact operator handling fixed
- Secret redaction and hard-block preservation verified
- All test tiers green

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-28T11:07:10.435211+02:00
