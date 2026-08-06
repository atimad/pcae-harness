# Task Contract

## Task ID

20260806-1821-phase-149o-1r-phase-report-evidence-coherence-validator-suppression-plumbing-repair

## Title

Phase 149O.1R: Phase Report Evidence-Coherence Validator + Suppression Plumbing Repair

## Status

active

## Mode

implementation

## Goal

Repair two source-confirmed defects in the canonical phase-report trust gate: (1) evidence-phase-ID extraction cannot recognize three-or-more-component phase IDs, (2) the documented test_evidence_classification suppression field is dropped before reaching the validator. Enable 149O.1H.1/149O.1H.1R's real evidence to be honestly re-evaluated, and allow the repair phase itself to self-host a trusted canonical report.

## Allowed Files

- src/pcae/core/phase_reports.py
- src/pcae/commands/phase.py
- src/pcae/commands/phase_reports.py
- src/pcae/cli.py
- tests/test_phase_149o_1r_phase_report_evidence_coherence_validator_repair.py
- docs/PHASE_149O_1R_PHASE_REPORT_EVIDENCE_COHERENCE_VALIDATOR_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json
- tasks/active/*.md
- tasks/done/*.md
- tasks/DONE.md

## Forbidden Files

- src/pcae/core/human_approval_trusted_provenance.py
- src/pcae/core/repository_identity.py
- src/pcae/core/hatp_bootstrap.py
- src/pcae/core/rollback_approval_evidence.py
- src/pcae/core/permission_broker.py
- src/pcae/core/permission_broker_foundation.py
- src/pcae/core/mutation_permission.py
- src/pcae/core/agent.py
- src/pcae/commands/agent.py
- docs/contracts/*.md


## Allowed Zones

- TBD

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

- Nested phase IDs (149O.1H.1, 149O.1H.1R) are recognized as their own evidence; no prefix truncation; no phase-specific hardcoding
- test_evidence_classification travels from canonical metadata through both production paths (phase complete, phase-report create) into the validated PhaseReport object
- 149O.1R's own canonical report self-hosts: complete, internal_evidence_coherence present, promoted, without --allow-partial-report
- Zero diff outside phase-report trust plumbing; HATP/RAE/Permission Broker/agent/contract files untouched

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-06T18:21:36.148896+02:00
