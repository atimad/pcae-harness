# Task Contract

## Task ID

20260724-0130-phase-143i-1-interactive-workflow-contract-state-transition-table-repair

## Title

Phase 143I.1: Interactive Workflow Contract State-Transition Table Repair

## Status

active

## Mode

documentation

## Goal

Bounded repair of IWC-001's single Blocking finding (143I Finding B-1): widen Section 4.4's ten-state transition table to make explicit the Cancelled/Expired/Abandoned exits already required by IWC-REQ-045/046/047/160 and Section 12 from Created, EvidenceReady, AwaitingClarification, DecisionSelected, and AwaitingConfirmation. No state added/removed/merged/renamed. No requirement text changed. No implementation performed. Runtime remains Observed / observe / unavailable.

## Allowed Files

- docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md
- docs/PHASE_143I1_INTERACTIVE_WORKFLOW_CONTRACT_STATE_TRANSITION_TABLE_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/done/20260723-2317-idle-awaiting-next-governed-phase-after-143i.md
- tasks/active/20260724-0130-phase-143i-1-interactive-workflow-contract-state-transition-table-repair.md

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

- Section 4.4's table explicitly lists every Cancelled/Expired/Abandoned exit required by IWC-REQ-045/046/047/160 and Section 12, for all five affected states
- No state added, removed, merged, or renamed; AwaitingDecision and all four terminal states' rows byte-identical to v1.0
- No IWC-REQ text added, removed, renumbered, or reworded
- OBS-1 and OBS-2 explicitly dispositioned, not silently discarded
- No implementation of the Interactive Workflow performed; runtime remains Observed / observe / unavailable

## Acceptance Checks

- pcae check
- python -m pytest -m fast_green -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-24T01:30:10.218453+02:00
