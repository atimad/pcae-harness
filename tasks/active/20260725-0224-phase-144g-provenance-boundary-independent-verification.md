# Task Contract

## Task ID

20260725-0224-phase-144g-provenance-boundary-independent-verification

## Title

Phase 144G: Provenance Boundary Independent Verification

## Status

active

## Mode

validation

## Goal

Independently and adversarially re-verify Phase 144F's Provenance Boundary Implementation against IWC-001 v1.2 IWC-REQ-185-190 and PEC-001 v1.1 PEC-REQ-111-117, re-deriving every conclusion directly from IWC-001, PEC-001, CHGR-001, TAMC-001, and TAMPC-001 rather than trusting 144E/144F's own framing. Classify the disclosed authority_basis_claimed and schema-envelope limitations. No production implementation change except a narrowly scoped repair of an independently demonstrated Blocking finding (none found).

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/PHASE_144G_PROVENANCE_BOUNDARY_INDEPENDENT_VERIFICATION.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md
- docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md
- docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md
- docs/contracts/TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md
- docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md
- src/pcae/governance/publication/**
- src/pcae/interactive_workflow/**
- src/pcae/cltr/**


## Allowed Zones

- docs
- tasks
- config

## Forbidden Zones

- governance
- interactive_workflow
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

- IWC-REQ-185-190 and PEC-REQ-111-117 independently verified with direct code/contract evidence
- Package immutability, authority-neutrality, publication-neutrality adversarially tested
- Session/Preview widening judgment call assessed for necessity and sufficiency
- authority_basis_claimed and schema-envelope limitations independently classified
- Runtime confirmed unchanged (Observed/observe/unavailable)
- Findings register produced; any Blocking finding repaired narrowly or escalated

## Acceptance Checks

- pcae check
- pcae health
- pcae doctor
- python -m pytest -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-25T02:24:22.981094+02:00
