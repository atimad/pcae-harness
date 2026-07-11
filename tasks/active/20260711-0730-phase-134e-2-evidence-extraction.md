# Task Contract

## Task ID

20260711-0730-phase-134e-2-evidence-extraction

## Title

Phase 134E.2 — Evidence Extraction

## Status

active

## Mode

implementation

## Goal

Implement a deterministic, audience-aware, transport-independent Evidence Extraction layer over Canonical Engineering Evidence without activating it in the lifecycle

## Allowed Files

- src/pcae/core/evidence_extraction.py
- tests/test_evidence_extraction_134e2.py
- docs/PHASE_134_EVIDENCE_EXTRACTION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DECISIONS.md
- tasks/DONE.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/**
- tasks/done/**

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

- TBD

## Acceptance Criteria

- Evidence Extraction implemented, isolated from active lifecycle, with Phase Report and Operator Report profiles
- Requirement levels, completeness classification, non-omission, and non-strengthening implemented deterministically
- Findings, repairs, uncertainty, and limitations preserved without history loss
- Existing lifecycle behavior unchanged; fast_green passes except known unrelated failure

## Acceptance Checks

- pcae check
- git diff --check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-11T07:30:58.426980+02:00
