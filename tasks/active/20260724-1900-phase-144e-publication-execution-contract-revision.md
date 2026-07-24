# Task Contract

## Task ID

20260724-1900-phase-144e-publication-execution-contract-revision

## Title

Phase 144E: Publication Execution Contract Revision (IWC-001/PEC-001 Provenance-Boundary Closure)

## Status

active

## Mode

documentation

## Goal

Independently re-derive the provenance-boundary inconsistency Phase 144D
identified as F-1/JC-2 (Publication Coordinator cannot produce a
CHGR-001 §10-complete record from a `PublicationReadinessPackage` that
carries only identifier/digest references, never verbatim decision
content), determine root cause by direct re-reading of IWC-001, PEC-001,
CHGR-001, and the actual `interactive_workflow`/`governance/publication`
source, and freeze the minimum additive contract revision to IWC-001
and/or PEC-001 that closes the gap. Contract revision only; no
implementation.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/PHASE_144E_PUBLICATION_EXECUTION_CONTRACT_REVISION.md
- docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md
- docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

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

- No implementation of PublicationCoordinator or any other class
- No CLI implementation
- No CHGR-writing machinery
- No CHGR creation
- No modification of src/pcae/interactive_workflow/**
- No modification of Typed Authority Model or CLTR machinery
- No modification of CHGR-001, TAMC-001, or TAMPC-001
- No runtime capability change
- No redesign beyond the minimum additive revision required

## Acceptance Criteria

- Provenance-boundary inconsistency independently re-derived from contract text and source, not trusted from 144D's own framing
- Root cause demonstrated with contract/source citations (Option A/B/C/D)
- Alternative architectures (Models 1-4) evaluated
- Minimum contract revision frozen (additive, backward-compatible)
- Ownership, ownership matrix, and authority-neutrality preserved
- Compatibility with CHGR-001/TAMC-001/TAMPC-001 demonstrated
- Migration strategy documented
- No implementation occurs; runtime remains Observed/observe/unavailable

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- pcae doctor passes
- pcae push readiness passes
- python -m pytest -m fast_green -n auto passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-24T19:00:00.000000+02:00
