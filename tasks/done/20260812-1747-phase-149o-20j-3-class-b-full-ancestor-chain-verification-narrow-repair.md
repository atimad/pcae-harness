# Task Contract

## Task ID

20260812-1747-phase-149o-20j-3-class-b-full-ancestor-chain-verification-narrow-repair

## Title

Phase 149O.20J.3: Class-B Full Ancestor-Chain Verification Narrow Repair

## Status

done

## Mode

implementation

## Goal

Repair the _ancestor_chain_safe shared primitive (B-149O.20J.2-1) so the ancestor walk inspects every relevant ancestor up to the filesystem-root trust boundary instead of stopping at the first proven-safe ancestor, closing the writable-grandparent bypass, without HMIC scope evolution, Class-B provisioning, or readiness/certification/activation change

## Allowed Files

- src/pcae/core/hatp_class_b_topology_verifier.py
- src/pcae/core/hatp_environment_lock_verifier.py
- src/pcae/core/hatp_class_b_conformance.py
- tests/test_phase_149o_20j_3_class_b_full_ancestor_chain_verification_narrow_repair.py
- tests/test_phase_149o_20j_class_b_deployment_verifier_model_a_environment_lock_independent_implementation_verification.py
- tests/test_phase_149o_20j_2_class_b_deployment_verifier_narrow_defect_repair_independent_verification.py
- tests/test_phase_149o_20i_hatp_class_b_topology_verifier.py
- docs/PHASE_149O_20J_3_CLASS_B_FULL_ANCESTOR_CHAIN_VERIFICATION_NARROW_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

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

- B-149O.20J.2-1 repaired: full ancestor-chain walk to filesystem root, no early stop at first safe ancestor; J-1/J-2/J-3 remain closed; verifier remains read-only, non-authoritative, outside HMIC's frozen 25-source scope; zero production authority consumers

## Acceptance Checks

- pcae status coherence passes
- pcae health passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-12T17:47:52.248917+02:00
