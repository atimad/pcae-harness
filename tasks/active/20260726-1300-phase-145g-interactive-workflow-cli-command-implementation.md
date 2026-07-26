# Task Contract

## Task ID

20260726-1300-phase-145g-interactive-workflow-cli-command-implementation

## Title

Phase 145G: Interactive Workflow CLI Command Implementation

## Status

active

## Mode

implementation

## Goal

Implement the governed CLI/transport adapter for the Interactive Workflow
+ Publication application services (Phase 145F) per IWPC-001 v1.1 §5/§6,
limited to the three commands (`decision-session create`/`status`/
`readiness`, `governance-record publish`) that can be correctly
implemented against the existing 145F application-service boundary.
`evidence`/`clarify`/`preview`/`confirm`/`cancel` are frozen by the
contract but not implemented this phase -- disclosed Blocking finding,
not a silent omission (see `src/pcae/commands/decision_session.py`
module docstring and the Phase 145G report). No contract text changed,
no Phase 145D/145E/145F semantics modified, no engineering execution
capability added, runtime unchanged (Observed / observe / unavailable).

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- src/pcae/commands/decision_session.py
- src/pcae/commands/governance_record.py
- src/pcae/cli.py
- tests/test_phase_145g_decision_session_cli.py
- docs/PHASE_145G_INTERACTIVE_WORKFLOW_CLI_COMMAND_IMPLEMENTATION.md
- docs/COMMANDS.md
- src/pcae/core/docs.py
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/policy.toml

## Forbidden Files

- docs/contracts/INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md
- docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md
- docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md
- docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md
- src/pcae/interactive_workflow/**
- src/pcae/governance/publication/**

## Allowed Zones

- config
- docs
- tasks
- commands
- cli
- tests
- policy
- core

## Forbidden Zones

- interactive_workflow
- governance
- cltr

## Allowed Dependencies

- commands -> interactive_workflow
- commands -> governance
- commands -> core
- commands -> cltr
- commands -> schema_runtime
- cli -> commands
- cli -> core

## Forbidden Dependencies

- TBD

## Enforcement Mode

advisory

## Forbidden Changes

- No modification to IWPC-001, IWC-001, PEC-001, or CHGR-001 contract text.
- No modification to Phase 145D/145E/145F production semantics.
- No engineering execution capability added.
- No runtime capability change.

## Acceptance Criteria

- `decision-session create`/`status`/`readiness` and `governance-record
  publish` implemented, delegating exclusively through
  `SessionApplicationService`/`PublicationApplicationService`.
- Closed exit-code/error-taxonomy mapping implemented per IWPC-001 v1.1 §9/§19.
- Forbidden-import/dependency-boundary tests pass.
- `evidence`/`clarify`/`preview`/`confirm`/`cancel` non-implementation
  disclosed in the phase report as a Blocking finding, not silently omitted.
- Runtime unchanged (Observed / observe / unavailable) before and after.

## Acceptance Checks

- pcae health
- pcae check
- python -m pytest tests/test_phase_145g_decision_session_cli.py -q
- python -m pytest tests/test_phase_145d_session_repository_filesystem_implementation.py tests/test_phase_145e_pending_readiness_store_filesystem_implementation.py tests/test_phase_145f_application_service_boundary.py tests/test_phase_144c_publication_coordinator.py -q
- pcae runtime inspect --json

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-26T13:00:21.347506+02:00
