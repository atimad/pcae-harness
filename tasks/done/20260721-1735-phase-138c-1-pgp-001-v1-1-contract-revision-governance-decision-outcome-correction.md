# Task Contract

## Task ID

20260721-1735-phase-138c-1-pgp-001-v1-1-contract-revision-governance-decision-outcome-correction

## Title

Phase 138C.1: PGP-001 v1.1 Contract Revision (Governance Decision Outcome Correction)

## Status

done

## Mode

documentation

## Goal

Bounded repair of PGP-001's single Blocking finding (138C Finding 1): restore GAC-001 §9 outcome (c) 'Continue advisory use' to the §13 five-outcome enumeration and relocate/re-scope 'Revise protocol' as a distinct PGP-001-specific action, not a GAC-001 Stage 6 outcome. No other section's substance changed. No pilot authorized. No provision of GLP-001 or GAC-001 modified. Runtime remains Observed / observe / unavailable.

## Allowed Files

- docs/contracts/PILOT_GOVERNANCE_PROTOCOL_CONTRACT.md
- docs/PHASE_138C1_PGP_001_V1_1_CONTRACT_REVISION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/20260721-1735-phase-138c-1-pgp-001-v1-1-contract-revision-governance-decision-outcome-correction.md

## Forbidden Files

- docs/contracts/GOVERNANCE_ADOPTION_CONTRACT.md
- docs/contracts/GOVERNANCE_LIFECYCLE_PATTERN_CONTRACT.md


## Allowed Zones

- docs
- tasks

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

- PGP-001 v1.1's §13 enumerates exactly GAC-001's five §9 outcomes, including (c) Continue advisory use
- 'Revise protocol' relocated/re-scoped outside the five-outcome enumeration, explicitly labeled as a distinct PGP-001-specific action
- No other PGP-001 section's substance changed beyond version metadata and required supporting edits
- Findings 2-4 (Non-Blocking) left unchanged unless clarification is unavoidable due to the Blocking repair, in which case documented why
- No pilot authorized, designated, or executed; no provision of GLP-001 or GAC-001 modified; no governance behavior change; runtime remains Observed / observe / unavailable

## Acceptance Checks

- pcae check
- python -m pytest -m fast_green -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-21T17:35:29.057262+02:00
