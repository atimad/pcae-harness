# Task Contract

## Task ID

20260825-1159-phase-149o-20l-7o-3c-2-governed-capability-consumption-integration

## Title

Phase 149O.20L.7O.3C.2: Governed Capability Consumption Integration

## Status

done

## Mode

implementation

## Goal

Phase 149O.20L.7O.3C.2: Governed Capability Consumption Integration

## Allowed Files

- CHANGELOG.md
- PROJECT_STATUS.md
- src/pcae/commands/phase.py
- src/pcae/commands/decision_session.py
- src/pcae/commands/governance_record.py
- src/pcae/commands/governance_auto_publication.py
- src/pcae/commands/publication_permission_gate.py
- src/pcae/core/mutation_permission.py
- src/pcae/interactive_workflow/application/errors.py
- src/pcae/interactive_workflow/application/publication_service.py
- src/pcae/interactive_workflow/application/session_service.py
- src/pcae/interactive_workflow/session/coordinator.py
- docs/PHASE_149O_20L_7O_3C_2_GOVERNED_CAPABILITY_CONSUMPTION_INTEGRATION.md
- tests/test_phase_149o_20l_7o_3c_2_governed_capability_consumption_integration.py
- tests/test_phase_145g_decision_session_cli.py
- tests/test_phase_145g1_decision_session_cli_repair.py
- tests/test_phase_145g2_decision_selection_cli_repair.py
- tests/test_phase_145g2v_independent_verification.py
- tests/test_phase_145h3_independent_verification.py
- tasks/DONE.md
- tasks/active/20260825-1159-phase-149o-20l-7o-3c-2-governed-capability-consumption-integration.md
- tasks/done/20260825-1145-idle-awaiting-human-priority-decision-post-149o-20l-7o-3c-1.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- TBD

## Override Protected Files

- pyproject.toml


## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

## Forbidden Changes

- No runtime invocation
- No prompt execution
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No commit
- No push
- No rollback

## Acceptance Criteria

- TBD

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-25T11:59:33.979212+02:00
