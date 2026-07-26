# Task Contract

## Task ID

20260726-2340-phase-145g-3v-decision-session-identity-bound-resumption-independent-verification

## Title

Phase 145G.3V: Decision-Session Identity-Bound Resumption Independent Verification

## Status

active

## Mode

verification

## Goal

Independently verify, without trusting Phase 145G.3's own report or
tests, whether decision-session identity-bound resumption (closing
F-145G.2V-1) was correctly specified, implemented, enforced, and
integrated into the Interactive Workflow lifecycle. No production
behavior changed (no Blocking defect was found). Runtime remained
Observed/observe/unavailable throughout.

## Allowed Files

- docs/PHASE_145G3V_DECISION_SESSION_IDENTITY_BOUND_RESUMPTION_INDEPENDENT_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active/**
- tasks/done/**
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- src/**
- tests/**
- docs/contracts/**
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

- Any change to src/ or tests/ (no Blocking defect was found; no repair authority was exercised)

## Acceptance Criteria

- Independent contract diff, F-145G.2V-1 reproduction, identity model/claim/enforcement/replay/cache-hit/persistence/CLI/application/end-to-end/adversarial/dependency verification, and regression comparison all complete
- Explicit verdict on F-145G.2V-1 closure rendered
- Canonical Phase 145G.3V report produced

## Acceptance Checks

- pcae check passes
- pcae runtime inspect unchanged (Observed/observe/unavailable)
- fast_green passes (4391 passed, matching Phase 145G.3's own recorded baseline)

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-26T21:58:00.000000+02:00
