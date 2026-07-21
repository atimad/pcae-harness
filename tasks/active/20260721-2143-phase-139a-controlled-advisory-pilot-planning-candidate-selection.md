# Task Contract

## Task ID

20260721-2143-phase-139a-controlled-advisory-pilot-planning-candidate-selection

## Title

Phase 139A: Controlled Advisory Pilot Planning & Candidate Selection

## Status

active

## Mode

governance

## Goal

Identify, evaluate, and select a single Advisory Pilot candidate; define pilot scope, evidence collection plan, governance checkpoints, and success/failure metrics under GLP-001/GAC-001/PGP-001 v1.1/PPA-001; without authorizing, designating, or executing any pilot, modifying governance, or modifying runtime

## Allowed Files

- tasks/active/20260721-2143-phase-139a-controlled-advisory-pilot-planning-candidate-selection.md
- docs/PHASE_139A_CONTROLLED_ADVISORY_PILOT_PLANNING.md
- PROJECT_STATUS.md

## Forbidden Files

- TBD


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

- Exactly one pilot candidate recommended with explicit evidence-based justification and documented rejection rationale for alternatives
- Candidate discovery documents every candidate considered; evaluation uses objective, comparative criteria
- Pilot scope, evidence collection plan, governance checkpoint matrix (mapped to GLP-001/GAC-001/PGP-001/PPA-001), success metrics, failure metrics, measurement framework, and risk assessment are all defined
- No governance artifact modified, no pilot authorized/designated/executed, runtime remains Observed/observe/unavailable

## Acceptance Checks

- pcae check
- python -m pytest -m fast_green -n auto -q
- git status

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-21T21:43:18.099827+02:00
