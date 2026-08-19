# Task Contract

## Task ID

20260819-1942-phase-149o-20l-7o-2h-2-hmic-001-v1-6-paths-source-scope-closure-and-seven-contract-ceremony-consistency-repair

## Title

Phase 149O.20L.7O.2H.2: HMIC-001 v1.6 Paths Source-Scope Closure and Seven-Contract Ceremony Consistency Repair

## Status

active

## Mode

narrow_repair

## Goal

Repair B-149O.20L.7O.2H.1-1 and B-149O.20L.7O.2H.1-2 only: bind every authority-sensitive paths.py behavior reached by HMIC-REQ-052 limb (d), evolve HMIC-001 to v1.6, restore exact seven-contract HMIC-REQ-076 ceremony semantics, and narrow the implicated historical byte-window guard without weakening HMIC-REQ-145.

## Allowed Files

- src/pcae/core/hatp_mandatory_certification.py
- docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md
- tests/test_phase_149o_20l_7l_6_contract_preamble_and_relative_import_guard_repair_independent_verification.py
- tests/test_phase_149o_20l_7o_2h_2_hmic_paths_source_scope_and_ceremony_consistency_repair.py
- docs/PHASE_149O_20L_7O_2H_2_HMIC_PATHS_SOURCE_SCOPE_AND_SEVEN_CONTRACT_CEREMONY_CONSISTENCY_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- tasks/active/20260819-1918-idle-awaiting-next-governed-phase-post-149o-20l-7o-2h-1.md
- tasks/done/20260819-1918-idle-awaiting-next-governed-phase-post-149o-20l-7o-2h-1.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- src/pcae/core/paths.py
- .pcae/certifications/**
- .pcae/hatp/**
- hac-dell/**

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

- No runtime invocation
- No prompt execution
- No source behavior changes outside task/session/handoff governance
- No execution authorization
- No rollback

## Acceptance Criteria

- Exact independently derived source closure is contract/production aligned; current seven-contract ceremony semantics are consistent; historical guard remains effective; no authority upgrade; independent verification remains pending.

## Acceptance Checks

- .venv/bin/python -m pytest -m fast_green -n auto
- .venv/bin/python -m pytest tests/test_phase_149o_20l_7o_2h_2_hmic_paths_source_scope_and_ceremony_consistency_repair.py -q
- pcae health && pcae check && pcae status coherence

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-19T19:42:18.858597+02:00
