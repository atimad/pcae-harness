# Task Contract

## Task ID

20260808-2341-phase-149o-18e-cli-legacy-authority-migration-integration

## Title

Phase 149O.18E: CLI + Legacy Authority Migration Integration

## Status

done

## Mode

implementation

## Goal

Phase 149O.18E: CLI + Legacy Authority Migration Integration

## Allowed Files

- src/pcae/cli.py
- src/pcae/commands/agent.py
- src/pcae/core/agent.py
- tests/test_phase_149o_8_hatp_ag3_ag5_production_consumption_signing_ceremony_architecture.py
- tests/test_hatp_cli_migration.py
- tests/test_phase_149o_18e_cli_legacy_authority_migration_integration.py
- docs/PHASE_149O_18E_CLI_LEGACY_AUTHORITY_MIGRATION_INTEGRATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/done/20260808-2250-idle-awaiting-next-governed-phase-post-149o-18d.md
- tasks/active/20260808-2341-phase-149o-18e-cli-legacy-authority-migration-integration.md
- tasks/DONE.md

## Forbidden Files

- TBD


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

2026-08-08T23:41:12.106794+02:00
