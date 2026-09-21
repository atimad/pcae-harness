# Task Contract

## Task ID

20260921-1725-phase-150e-n16-5-f-5-tb-helper-admission-configured-agent-repair-reconstruct-configured-agent-admission-requirement-and-repair-authenticate-peer-configured-agent-none-gap

## Title

Phase 150E (N16-5-F-5-TB-HELPER-ADMISSION-CONFIGURED-AGENT-REPAIR): reconstruct configured-agent admission requirement and repair authenticate_peer configured_agent=None gap

## Status

done

## Mode

implementation

## Goal

Reconstruct HPAC-PAWA-HELPER-001 v5.0 §7/§10 configured-agent admission requirement from primary source and repair the disclosed hpac_pawa_helper_os.authenticate_peer configured_agent=None gap if a contract-conformant narrow repair exists; STOP with a documented Blocking Finding if it does not

## Allowed Files

- docs/PHASE_N16_5_F_5_TB_HELPER_ADMISSION_CONFIGURED_AGENT_REPAIR.md
- PROJECT_STATUS.md
- tasks/active/*
- tasks/done/*
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/fast-green-attribution/*
- .pcae/phase-reports/*
- .pcae/phase-reports/quarantine/*

## Forbidden Files

- TBD


## Allowed Zones

- docs
- tasks
- package
- config

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

- Configured-agent admission requirement reconstructed from current primary source (contracts + code), not from Phase 150D prose
- Either a contract-conformant narrow repair is implemented and verified, or a governed STOP with a documented Blocking Finding is recorded
- N-16-5 disposition, N-16-6/N-16-7 untouched status, and runtime posture (Observed/observe/unavailable) explicitly recorded

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-21T17:25:07.723979+02:00
