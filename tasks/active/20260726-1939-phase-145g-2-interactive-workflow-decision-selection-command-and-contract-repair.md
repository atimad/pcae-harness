# Task Contract

## Task ID

20260726-1939-phase-145g-2-interactive-workflow-decision-selection-command-and-contract-repair

## Title

Phase 145G.2: Interactive Workflow Decision-Selection Command and Contract Repair

## Status

active

## Mode

implementation

## Goal

Close F-145G.1-1 by adding IWPC-001 v1.2's decision-session select command (domain/application/CLI), repairing preview's DecisionSelected -> AwaitingConfirmation transition, and proving a genuine CLI-only path from create through publication, without redesigning Interactive Workflow architecture or modifying IWC-001/PEC-001/CHGR-001. Runtime remains Observed/observe/unavailable.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/commands/decision_session.py
- src/pcae/cli.py
- src/pcae/interactive_workflow/application/session_service.py
- src/pcae/interactive_workflow/errors.py
- src/pcae/interactive_workflow/models/session.py
- tests/test_phase_145g2_decision_selection_cli_repair.py
- docs/PHASE_145G2_INTERACTIVE_WORKFLOW_DECISION_SELECTION_COMMAND_AND_CONTRACT_REPAIR.md
- docs/COMMANDS.md
- docs/contracts/INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md
- src/pcae/core/docs.py
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md
- docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md
- src/pcae/governance/publication/**
- src/pcae/interactive_workflow/orchestration/**
- src/pcae/interactive_workflow/publication_handoff/**
- src/pcae/interactive_workflow/persistence/**
- .pcae/policy.toml


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

2026-07-26T19:39:28.503319+02:00
