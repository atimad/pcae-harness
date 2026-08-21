# Task Contract

## Task ID

20260821-0220-phase-149o-20l-7o-2n-post-hmic-v1-7-trust-enrollment-real-effect-node-selection-and-fido2-enrollment-authorization

## Title

Phase 149O.20L.7O.2N: Post-HMIC-v1.7 Trust-Enrollment real-effect node selection and FIDO2 enrollment authorization

## Status

active

## Mode

analysis

## Goal

Re-derive post-HMIC-v1.7 Trust-Enrollment DAG, verify actual FIDO2 hardware/provider availability via read-only inspection only, select the unique next real-effect node, and freeze (not execute) a one-credential FIDO2 enrollment authorization envelope if all prerequisites hold. Analysis/authorization-freeze only -- no real enrollment, no Principal/Signer/DeploymentBinding creation, no HMIC change, no redeploy.

## Allowed Files

- tasks/active/20260821-0220-phase-149o-20l-7o-2n-post-hmic-v1-7-trust-enrollment-real-effect-node-selection-and-fido2-enrollment-authorization.md
- docs/PHASE_149O_20L_7O_2N_POST_HMIC_V1_7_TRUST_ENROLLMENT_REAL_EFFECT_NODE_SELECTION_AND_FIDO2_ENROLLMENT_AUTHORIZATION.md
- tests/test_phase_149o_20l_7o_2n_post_hmic_trust_enrollment_dag_and_fido2_authorization.py
- PROJECT_STATUS.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- TBD


## Allowed Zones

- docs
- tests
- tasks
- config

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

- Fresh SSH read-only inspection of hac-dell confirms deployed revision, HMIC v1.7/38 VALID, active certification id, Trust-Enrollment absence, and Class-B sole residual HBDC-REQ-042
- All eight HATP readiness terms freshly enumerated with current value, producer, and remaining predecessor
- FIDO2 device presence/provider availability determined via non-enrolling read-only inspection only; no makeCredential or user-presence ceremony performed
- Unique next real-effect node selected per section 35 verdict taxonomy (A/B/C/D/E) with rejected alternatives documented
- If FIDO2 selected: narrow one-credential future authorization envelope frozen with freshness bindings, prechecks, exact command, postchecks -- not executed
- No real FIDO2 enrollment, Principal/Signer/DeploymentBinding creation, HMIC change, redeploy, or Protected Root mutation performed

## Acceptance Checks

- python -m pytest -n auto

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-21T02:20:41.378352+02:00
