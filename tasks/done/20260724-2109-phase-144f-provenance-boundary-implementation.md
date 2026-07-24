# Task Contract

## Task ID

20260724-2109-phase-144f-provenance-boundary-implementation

## Title

Phase 144F: Provenance Boundary Implementation

## Status

done

## Mode

implementation

## Goal

Implement IWC-001 v1.2 IWC-REQ-185-190 and PEC-001 v1.1 PEC-REQ-111-117: widen PublicationReadinessPackage/Preview/PublicationHandoff.build_package to carry verbatim decision provenance, and update governance/publication/record.py to populate human_governance_record/human_confirmation_evidence/governance_record_provenance from the widened package, then independently re-verify.

## Allowed Files

- src/pcae/interactive_workflow/publication_handoff/models.py
- src/pcae/interactive_workflow/publication_handoff/handoff.py
- src/pcae/interactive_workflow/preview/models.py
- src/pcae/interactive_workflow/preview/builder.py
- src/pcae/interactive_workflow/models/session.py
- src/pcae/interactive_workflow/orchestration/coordinator.py
- src/pcae/interactive_workflow/serialization/publication_handoff_schema.py
- src/pcae/interactive_workflow/serialization/preview_schema.py
- src/pcae/interactive_workflow/serialization/schema.py
- src/pcae/governance/publication/record.py
- tests/test_iwc_143o_session_coordination_publication_handoff.py
- tests/test_phase_144c_publication_coordinator.py
- docs/PHASE_144F_PROVENANCE_BOUNDARY_IMPLEMENTATION.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- docs/contracts/**
- src/pcae/governance/publication/coordinator.py
- src/pcae/governance/publication/models.py
- src/pcae/governance/publication/storage.py
- src/pcae/governance/publication/errors.py
- src/pcae/governance/publication/serialization.py
- src/pcae/cltr/**
- src/pcae/schema_resources/chgr/**


## Allowed Zones

- interactive_workflow
- governance
- tests
- docs
- tasks

## Forbidden Zones

- cltr
- commands
- core

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

## Forbidden Changes

- TBD

## Acceptance Criteria

- PublicationReadinessPackage implements IWC-REQ-185-190
- PublicationCoordinator/record.py implements PEC-REQ-111-117
- CHGR fields populated solely from immutable package content
- No new subsystem dependencies; AST boundary enforcement intact
- Runtime remains unchanged
- Full regression passes

## Acceptance Checks

- pcae check
- pcae health
- pcae doctor
- python -m pytest -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-24T21:09:08.412565+02:00
