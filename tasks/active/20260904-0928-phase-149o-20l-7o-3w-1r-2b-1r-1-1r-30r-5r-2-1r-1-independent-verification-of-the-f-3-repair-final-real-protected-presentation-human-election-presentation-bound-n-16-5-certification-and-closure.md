# Task Contract

## Task ID

20260904-0928-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-5r-2-1r-1-independent-verification-of-the-f-3-repair-final-real-protected-presentation-human-election-presentation-bound-n-16-5-certification-and-closure

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1 — Independent Verification of the F-3 Repair + Final Real Protected-Presentation Human Election + Presentation-Bound N-16-5 Certification and Closure

## Status

active

## Mode

verification

## Goal

Independently verify F-3 and, only after all software gates pass, complete the genuine protected-presentation plus FIDO2 N-16-5 certification without production changes.

## Allowed Files

- tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1_*.py
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1_*.md
- .pcae/certification/**
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.json
- .pcae/phase-completion-report.pending.json
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md

## Forbidden Files

- src/pcae/**
- scripts/**
- docs/contracts/**
- pyproject.toml

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

- No runtime invocation
- No prompt execution
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No commit
- No push
- No rollback

## Acceptance Criteria

- F-3 independently verified against immutable Git topology
- Real production helper and genuine human APPROVE certified
- Fresh genuine FIDO2 assertion plus REAL assurance and Gate 5 certified
- N-16-5 closes only if all frozen requirements pass

## Acceptance Checks

- Fresh software IV suite: 55 passed
- F-3 predecessor and repair suites: 116 passed
- Broad sweep: 933 passed, 1 known F-4 failure, 1 obsolete historical node deselected
- Production root/current helper generation absent; ceremony not started

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-04T09:28:58.150451+02:00
