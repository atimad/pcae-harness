# Task Contract

## Task ID

20260819-1723-phase-149o-20l-7o-2h-0-hmic-v1-5-certificationrecord-contract-version-closed-schema-alignment-repair

## Title

Phase 149O.20L.7O.2H.0: HMIC v1.5 CertificationRecord Contract-Version Closed-Schema Alignment Repair

## Status

active

## Mode

narrow_repair

## Goal

Repair the divergence between HMIC-001 v1.5's normative seven-member contract_versions requirement (HMIC-REQ-067/069/053) and production's six-member _CONTRACT_VERSIONS_REQUIRED_KEYS closed-schema constant, which currently rejects any CertificationRecord.contract_versions mapping containing HBDC-001 -- Finding B-149O.20L.7O.2H-1

## Allowed Files

- src/pcae/core/hatp_mandatory_certification.py
- tests/test_phase_149o_20l_7o_2h_0_hmic_certificationrecord_contract_version_closed_schema_alignment_repair.py
- docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md
- docs/PHASE_149O_20L_7O_2H_0_HMIC_CERTIFICATIONRECORD_CONTRACT_VERSION_CLOSED_SCHEMA_ALIGNMENT_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- tasks/active/20260819-1702-idle-awaiting-next-governed-phase-post-149o-20l-7o-2h.md
- tasks/done/20260819-1702-idle-awaiting-next-governed-phase-post-149o-20l-7o-2h.md
- tasks/active/20260819-1723-phase-149o-20l-7o-2h-0-hmic-v1-5-certificationrecord-contract-version-closed-schema-alignment-repair.md
- tasks/done/20260819-1723-phase-149o-20l-7o-2h-0-hmic-v1-5-certificationrecord-contract-version-closed-schema-alignment-repair.md

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

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- _CONTRACT_VERSIONS_REQUIRED_KEYS re-derived from HMIC-001 v1.5 primary contract text (not assumed), CertificationRecord closed-schema repaired to match, focused test suite covers all required cases, fast_green clean

## Acceptance Checks

- python3 -m pytest tests/test_phase_149o_20l_7o_2h_0_hmic_certificationrecord_contract_version_closed_schema_alignment_repair.py -q

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-19T17:23:25.872613+02:00
