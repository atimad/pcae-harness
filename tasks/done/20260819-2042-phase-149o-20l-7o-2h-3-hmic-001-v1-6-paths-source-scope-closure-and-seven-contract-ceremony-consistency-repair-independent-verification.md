# Task Contract

## Task ID

20260819-2042-phase-149o-20l-7o-2h-3-hmic-001-v1-6-paths-source-scope-closure-and-seven-contract-ceremony-consistency-repair-independent-verification

## Title

Phase 149O.20L.7O.2H.3: HMIC-001 v1.6 Paths Source-Scope Closure and Seven-Contract Ceremony Consistency Repair Independent Verification

## Status

done

## Mode

independent_verification

## Goal

Independently re-derive and verify the 2H.2 paths source-scope closure, complete limb-(d) transitive identity, seven-contract ceremony consistency, historical HMIC-REQ-145 guard narrowing, certification invalidation, and bounded trust-enrollment/signing preservation from primary evidence without modifying production or normative contracts.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tests/test_phase_149o_20l_7o_2h_3_hmic_paths_source_scope_and_seven_contract_consistency_independent_verification.py
- docs/PHASE_149O_20L_7O_2H_3_HMIC_PATHS_SOURCE_SCOPE_AND_SEVEN_CONTRACT_CONSISTENCY_INDEPENDENT_VERIFICATION.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- src/pcae/**
- docs/contracts/**
- tests/test_phase_149o_20l_7l_6_contract_preamble_and_relative_import_guard_repair_independent_verification.py
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

- TBD

## Acceptance Criteria

- Reproduce the historical paths omission and four-vs-seven contradiction from fixed pre-2H.2 source; independently prove or refute exact current source/contract closure and guard correctness; preserve any Blocking finding without repair.
- Run a fresh focused verification suite, fixed/current failure-node comparison, bounded signing/trust-enrollment regression, Fast Green, and required governance checks.
- Produce a canonical evidence-backed report and memory updates with no certification, provisioning, DeploymentBinding, readiness integration, activation, Permission Broker change, or protected-state mutation.

## Acceptance Checks

- .venv/bin/python -m pytest tests/test_phase_149o_20l_7o_2h_3_hmic_paths_source_scope_and_seven_contract_consistency_independent_verification.py -q
- pcae health
- pcae check
- pcae status coherence

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-19T20:42:51.622217+02:00
