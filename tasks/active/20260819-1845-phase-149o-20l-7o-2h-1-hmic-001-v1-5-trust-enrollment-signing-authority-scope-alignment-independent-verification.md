# Task Contract

## Task ID

20260819-1845-phase-149o-20l-7o-2h-1-hmic-001-v1-5-trust-enrollment-signing-authority-scope-alignment-independent-verification

## Title

Phase 149O.20L.7O.2H.1: HMIC-001 v1.5 Trust-Enrollment / Signing Authority-Scope Alignment Independent Verification

## Status

active

## Mode

independent_verification

## Goal

Independently reconstruct and verify HMIC-001 v1.5's 35-member authority-bearing source/content identity, seven-member contract identity, Trust-Enrollment/signing closure limb (d), and the CertificationRecord seven-member closed-schema repair without trusting the 2H/2H.0 reports or tests and without modifying production or normative contracts.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tests/test_phase_149o_20l_7o_2h_1_hmic_trust_enrollment_signing_authority_scope_alignment_independent_verification.py
- docs/PHASE_149O_20L_7O_2H_1_HMIC_TRUST_ENROLLMENT_SIGNING_AUTHORITY_SCOPE_ALIGNMENT_INDEPENDENT_VERIFICATION.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- src/pcae/**
- docs/contracts/**
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

- No production source or normative contract modification
- No real HMIC certification or activation
- No FIDO2 provisioning, Principal/Signer enrollment, or DeploymentBinding creation
- No hac-dell or Protected Root mutation
- No readiness integration, Permission Broker change, PIV, CBV-S10 wiring, or Stream-B work

## Acceptance Criteria

- Independently reconstruct historical HMIC v1.4 30/5, post-2H 35/7/6, and current HMIC v1.5 35/7/7 states from primary evidence
- Verify exact contract/production memberships, limb (d) closure, content dual-binding, CertificationRecord parsing/identity/validation, digest sensitivity, self-binding, and historical defect reproduction
- Run a fresh focused verification suite, appropriate regressions, and Fast Green; adjudicate both entering findings without repairing any Blocking defect
- Complete with an evidence-backed canonical report, project memory updates, and no authority upgrade

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes
- python3 -m pytest tests/test_phase_149o_20l_7o_2h_1_hmic_trust_enrollment_signing_authority_scope_alignment_independent_verification.py -q passes
- scripts/fast_green.sh passes under normal host conditions

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-19T18:45:34.053639+02:00
