# Task Contract

## Task ID

20260806-1742-phase-149o-1h-1r-hatp-repair-phase-evidence-coherence-canonical-report-trust-repair

## Title

Phase 149O.1H.1R: HATP Repair Phase Evidence-Coherence / Canonical Report Trust Repair

## Status

active

## Mode

documentation

## Goal

Independently investigate and, if governed-lifecycle-legitimate, repair the canonical phase-completion-report trust failure for 149O.1H.1 (missing internal_evidence_coherence trust field); do not modify HATP production code or re-litigate the Wave-3 technical repair itself.

## Allowed Files

- docs/PHASE_149O_1H_1R_HATP_REPAIR_EVIDENCE_COHERENCE_CANONICAL_REPORT_TRUST_REPAIR.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/*.md
- tasks/done/*.md
- tasks/DONE.md

## Forbidden Files

- src/pcae/core/human_approval_trusted_provenance.py
- src/pcae/core/phase_reports.py
- src/pcae/core/phase_id.py
- src/pcae/core/repository_identity.py
- src/pcae/core/hatp_bootstrap.py
- docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md


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

- internal_evidence_coherence trust field either becomes present/trusted via governed regeneration, or a BLOCKING report-validator finding is recorded and canonical trust verdict is NOT REPAIRED
- production diff remains empty (zero files under src/pcae/)

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-06T17:42:41.521022+02:00
