# Task Contract

## Task ID

20260728-0627-phase-145h-3r-1-phase-completion-metadata-sequencing-and-finalization-repair

## Title

Phase 145H.3R.1: Phase Completion Metadata Sequencing and Finalization Repair

## Status

active

## Mode

implementation

## Goal

Repair the recurring pcae phase complete finalization defect (recurred at 145G.3, 145H.1, 145H.2, 145H.3): complete_phase() released the agent lock and recorded phase_completed/agent_released provenance unconditionally, before _finalize_report_and_notify()'s validation (canonical identity resolution, finalization gate, Repository Transition Validator, cross-phase commit contamination) ever ran. Reordered run_phase_complete() so complete_phase() is called only after successful finalization; a rejected transition now leaves the lock held, the task active, and no phase_completed/agent_released provenance recorded. Does not authorize 145H.4, 145I, Phase 146, or broader Interactive Workflow chapter certification.

## Allowed Files

- src/pcae/commands/phase.py
- tests/test_phase_145h3r1_lock_sequencing_repair.py
- docs/PHASE_145H3R1_PHASE_COMPLETION_METADATA_SEQUENCING_AND_FINALIZATION_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DECISIONS.md
- tasks/TODO.md
- tasks/DONE.md
- .pcae/phase-completion-metadata.json
- tasks/done/20260727-2234-idle-awaiting-next-governed-phase-post-145h-3r.md

## Forbidden Files

- docs/contracts/**


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

2026-07-28T06:27:36.741912+02:00
