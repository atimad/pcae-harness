# Task Contract

## Task ID

20260711-1832-phase-134e-9-report-consistency-derived-correctness-validation

## Title

Phase 134E.9 Report Consistency Derived Correctness Validation

## Status

done

## Mode

implementation

## Goal

Implement the reusable Report Consistency / Derived Correctness validation manifest authoritative per the 134D implementation plan Section 3 (134E.9): check derived report claims against the report's own sealed Architecture Status finalization snapshot, closing the confirmed gap that neither validate_internal_report_coherence() nor validate_finalization_gate() checked Architecture Status freshness/conflicts, and only self-recommendation (not a different already-completed phase) was rejected as a next-phase recommendation. Wire the new validate_derived_correctness() into the existing shared finalization gate (validate_finalization_gate()) and trust-assessment pipeline (_apply_canonical_and_trust()), not a second competing gate. Add a narrow read-only pcae phase-report consistency inspection command. No activation of Canonical Engineering Evidence, Evidence Extraction, Phase Report View, Operator Report View, Rendering Architecture, Delivery Pipeline, or Delivery Receipts. Exactly one ordinary terminal delivery for this phase. Do not begin 134E.9V or 134E.10.

## Allowed Files

- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/phase-metadata-repairs.log
- tasks/DONE.md
- tasks/active
- tasks/active/20260711-1832-phase-134e-9-report-consistency-derived-correctness-validation.md

## Forbidden Files

- TBD


## Allowed Zones

- tasks
- config
- docs

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

- validate_derived_correctness() is wired into the shared finalization gate and blocks on stale/invalid/conflicted Architecture Status and on recommending an already-completed phase
- fast_green passes with only the known pre-existing unrelated failure
- no external test delivery occurs; exactly one ordinary terminal delivery for 134E.9

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-11T18:32:12.997599+02:00
