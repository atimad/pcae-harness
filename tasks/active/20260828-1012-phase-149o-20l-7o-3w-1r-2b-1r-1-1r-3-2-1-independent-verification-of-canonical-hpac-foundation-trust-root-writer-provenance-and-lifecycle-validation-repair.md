# Task Contract

## Task ID

20260828-1012-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-3-2-1-independent-verification-of-canonical-hpac-foundation-trust-root-writer-provenance-and-lifecycle-validation-repair

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3.2.1: Independent Verification of Canonical HPAC Foundation Trust-Root, Writer-Provenance, and Lifecycle-Validation Repair

## Status

active

## Mode

verification

## Goal

Independently re-derive the frozen HPAC authority requirements and determine
whether the `.3.2` candidate closes all four `.3.1` trust-root defects. Attack
principal, presentation, proof, and lifecycle provenance with fresh tests;
verify runtime/PB isolation and fixed-SHA regression equivalence. Do not repair
production defects, modify contracts, begin Layer 3, or enable execution.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tests/test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_3_2_1_INDEPENDENT_VERIFICATION_CANONICAL_HPAC_TRUST_ROOT_WRITER_PROVENANCE_LIFECYCLE_VALIDATION_REPAIR.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/fast-green-attribution/**
- .pcae/phase-reports/**3-2-1*
- .pcae/finalization-transactions/**3-2-1*

## Forbidden Files

- docs/contracts/**
- src/pcae/**
- scripts/**
- pyproject.toml
- docs/releases/**
- tests/test_hpac_foundation_independent_verification_3w1r2b1r111r31.py
- tests/test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py


## Allowed Zones

- tests
- docs
- tasks
- config

## Forbidden Zones

- core
- commands
- cli
- scripts
- hooks
- package
- policy
- authority_evaluation

## Allowed Dependencies

- tests -> core
- docs -> *
- tasks -> *

## Forbidden Dependencies

- core -> tests
- core -> docs

## Enforcement Mode

strict

## Forbidden Changes

- No normative contract or production implementation modification
- No repair of defects discovered by verification
- No historical `.3`, `.3.1`, or `.3.2` evidence rewrite
- No Layer 3, PB/runtime integration, B1/B7/N1/N2 repair, or real authentication/UI
- No Runtime Enforcement, Shell Gate, provider, network, credential, hardware, subprocess, or external effect
- No release, deployment, Dell, research, or article work
- No raw git commit/push, hook bypass, force push, history rewrite, or rollback
- No delegated commit, phase finalization, or push authority

## Acceptance Criteria

- All four `.3.1` findings are independently adjudicated CLOSED, PARTIALLY CLOSED, or REMAINS OPEN from contract-derived evidence
- Fresh adversarial tests cover caller forgery/copy/upgrade, writer boundaries, alternate chains, forks, canonical-store attacks, and isolation
- Fixed-SHA regression compares exact immutable `.3.2` baseline and current candidate with zero unexplained candidate-only regressions
- Runtime remains Observed / observe / unavailable and the `.3` delegated incident remains UNAUTHORIZED
- The exact next bounded layer is derived from the verified `.2` plan only if all four trust findings close

## Acceptance Checks

- pcae status coherence
- pcae health
- pcae check
- python -m pytest tests/test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py -q

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-28T10:12:26.874442+02:00
