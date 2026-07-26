# Task Contract

## Task ID

20260726-2045-phase-145g-3-decision-session-identity-bound-resumption-contract-and-implementation-repair

## Title

Phase 145G.3: Decision-Session Identity-Bound Resumption Contract and Implementation Repair

## Status

done

## Mode

implementation

## Goal

Close F-145G.2V-1 by adding a required `--as-identity` claim to every mutating `decision-session` command, enforced exactly once by `SessionApplicationService` against the session's bound `owner_identity`, without expanding runtime capability, authority, or execution scope. Runtime remains Observed/observe/unavailable.

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
- src/pcae/interactive_workflow/application/publication_service.py
- src/pcae/interactive_workflow/application/errors.py
- tests/test_phase_145g3_decision_session_identity_binding.py
- tests/test_phase_145g1_decision_session_cli_repair.py
- tests/test_phase_145g2_decision_selection_cli_repair.py
- tests/test_phase_145g_decision_session_cli.py
- tests/test_phase_145g2v_independent_verification.py
- tests/test_phase_145g2v_independent_verification_partial.py
- docs/PHASE_145G3_DECISION_SESSION_IDENTITY_BOUND_RESUMPTION_CONTRACT_AND_IMPLEMENTATION_REPAIR.md
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
- src/pcae/interactive_workflow/models/session.py
- src/pcae/cltr/**
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

advisory

## Forbidden Changes

- TBD

## Acceptance Criteria

- F-145G.2V-1 closed: every mutating decision-session command enforces identity-bound resumption
- Full existing regression and fast_green unaffected

## Acceptance Checks

- pcae check passes
- pytest fast_green passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-26T20:45:00.000000+02:00
