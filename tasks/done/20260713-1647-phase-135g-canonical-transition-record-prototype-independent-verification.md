# Task Contract

## Task ID

20260713-1647-phase-135g-canonical-transition-record-prototype-independent-verification

## Title

Phase 135G: Canonical Transition Record Prototype Independent Verification

## Status

done

## Mode

verification

## Goal

Independently re-derive and verify Phase 135F against its frozen contract and plan, repair only reproduced Blocking defects inside the prototype boundary, record exact evidence, and complete exactly Phase 135G without production integration.

## Allowed Files

- src/pcae/cltr_prototype/canonicalization.py
- src/pcae/cltr_prototype/comparison.py
- src/pcae/cltr_prototype/generator.py
- src/pcae/cltr_prototype/identity.py
- src/pcae/cltr_prototype/invariants.py
- src/pcae/cltr_prototype/models.py
- src/pcae/cltr_prototype/persistence.py
- src/pcae/cltr_prototype/state_machine.py
- src/pcae/cltr_prototype/verifier.py
- tests/test_cltr_prototype_canonicalization_digest.py
- tests/test_cltr_prototype_comparison.py
- tests/test_cltr_prototype_generator.py
- tests/test_cltr_prototype_identity.py
- tests/test_cltr_prototype_invariants.py
- tests/test_cltr_prototype_models.py
- tests/test_cltr_prototype_persistence.py
- tests/test_cltr_prototype_state_machine.py
- tests/test_cltr_prototype_verifier.py
- tests/fixtures/cltr_prototype/successful_transition.json
- tests/fixtures/cltr_prototype/exact_replay.json
- tests/fixtures/cltr_prototype/contaminated_commit_ownership.json
- docs/PHASE_135_CANONICAL_TRANSITION_RECORD_PROTOTYPE_INDEPENDENT_VERIFICATION.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DECISIONS.md
- tasks/DONE.md
- tasks/active
- tasks/active/20260713-1647-phase-135g-canonical-transition-record-prototype-independent-verification.md
- .pcae/phase-completion-report.md
- .pcae/phase-completion-metadata.json

## Forbidden Files

- src/pcae/cli.py
- src/pcae/core/finalization_transaction.py

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

- All 14 states, all 16 permitted transitions, all forbidden transitions, and all 37 implemented invariant IDs are independently reconciled with the frozen source tables.
- Every reproduced Blocking defect is repaired only inside the prototype boundary and has an adversarial regression test.
- Persistence is contained, symlink-safe, staged atomically, digest-verified before publication, replay-safe, and crash-recoverable.
- Unsupported or unknown semantics, unresolved commit ownership, and inconsistent comparison targets fail closed without strengthening authority.
- No production lifecycle, entry point, finalization, notification, canonical authority, PFN-001, or PFR-001 file changes.
- Final report records exact tests, findings, verdict, runtime posture, governance state, commit identity, and push state.

## Acceptance Checks

- python -m pytest -q tests/test_cltr_prototype_canonicalization_digest.py tests/test_cltr_prototype_comparison.py tests/test_cltr_prototype_generator.py tests/test_cltr_prototype_identity.py tests/test_cltr_prototype_invariants.py tests/test_cltr_prototype_models.py tests/test_cltr_prototype_persistence.py tests/test_cltr_prototype_state_machine.py tests/test_cltr_prototype_verifier.py
- python -m pytest -q -n auto tests/test_cltr_prototype_canonicalization_digest.py tests/test_cltr_prototype_comparison.py tests/test_cltr_prototype_generator.py tests/test_cltr_prototype_identity.py tests/test_cltr_prototype_invariants.py tests/test_cltr_prototype_models.py tests/test_cltr_prototype_persistence.py tests/test_cltr_prototype_state_machine.py tests/test_cltr_prototype_verifier.py
- python -m compileall -q src/pcae
- pcae health
- pcae check
- pcae doctor task-memory

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-13T16:47:00.996893+02:00
