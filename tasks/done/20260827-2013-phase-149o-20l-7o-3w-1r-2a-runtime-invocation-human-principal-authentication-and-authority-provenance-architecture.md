# Task Contract

## Task ID

20260827-2013-phase-149o-20l-7o-3w-1r-2a-runtime-invocation-human-principal-authentication-and-authority-provenance-architecture

## Title

Phase 149O.20L.7O.3W.1R.2A: Runtime Invocation Human Principal Authentication and Authority Provenance Architecture

## Status

done

## Mode

architecture

## Goal

Read-only architecture/contract-design phase to determine the smallest architecture/contract evolution required for PCAE to establish an authenticated human principal for runtime-invocation approval, resolving finding N2 (caller-manufacturable human-looking provenance is not authenticated human provenance). No production code, tests, or frozen contracts (RIHAC/RIASC/PBRD/RDGO/RPAC) may be modified. Produce architecture document + canonical phase report. Do not implement, activate runtime/Shell Gate, or repair B1/B7/N1.

## Allowed Files

- docs/PHASE_149O_20L_7O_3W_1R_2A_RUNTIME_INVOCATION_HUMAN_PRINCIPAL_AUTHENTICATION_AUTHORITY_PROVENANCE_ARCHITECTURE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DECISIONS.md
- tasks/TODO.md
- tasks/active/**
- tasks/done/**
- .pcae/session.json
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- docs/contracts/RIHAC*
- docs/contracts/RIASC*
- docs/contracts/PBRD*
- docs/contracts/RDGO*
- docs/contracts/RPAC*


## Allowed Zones

- docs
- tasks
- session
- config

## Forbidden Zones

- core
- commands
- cli
- tests

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

## Forbidden Changes

- TBD

## Acceptance Criteria

- Baseline verified clean, 0 ahead, v0.4.3 unchanged, runtime unavailable, no active governed phase before start
- Primary evidence re-read: 3W.1, 3W.1R, 3W.1R.1, 3W.1R.2, 3W.1R.2C docs; RIHAC-001; RIASC-001; PBRD-001; RDGO-001; Typed Authority Model; CHGR; Interactive Workflow Confirmation; HATP/Class-B human-principal sources
- N2 finding recovered verbatim from primary evidence with exact wording, affected source, exploit/construction, contract insufficiency
- Human identity universe enumerated with Matrix A (OS username, Git identity, session identity, TAM, CHGR, IWC, HATP/signing, etc.)
- Threat model documented including mandatory same-user autonomous-agent threat and delegated-agent incident as example only
- At least 4 architecture options (signed key, hardware-backed, OS-auth, external channel) evaluated with comparison Matrix C
- Recommended minimal v1 architecture selected and justified; contract evolution matrix (Matrix D) produced for RIHAC/RIASC/PBRD/RDGO/RPAC
- All 6 required matrices (A-F) present in architecture document
- No src/pcae, tests, or frozen contract files modified; runtime remains Observed/observe/unavailable; POL-005 unchanged; v0.4.3 unchanged; execution not activated
- Canonical phase report and PROJECT_STATUS.md updated identifying next phase as human-principal authentication contract freeze, requiring human authorization; phase ends in STOP/decision-hold, no auto-continuation

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-27T20:13:56.790418+02:00
