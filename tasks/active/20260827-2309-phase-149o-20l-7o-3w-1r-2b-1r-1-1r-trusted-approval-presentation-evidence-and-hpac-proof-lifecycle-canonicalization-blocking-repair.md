# Task Contract

## Task ID

20260827-2309-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-trusted-approval-presentation-evidence-and-hpac-proof-lifecycle-canonicalization-blocking-repair

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R: Trusted Approval Presentation Evidence and HPAC Proof-Lifecycle Canonicalization Blocking Repair

## Status

active

## Mode

strict

## Goal

Close exactly original B-3 and B-4 at the contract layer by canonically
freezing trusted approval-presentation evidence and durable HPAC proof
lifecycle/atomic-consumption state. Preserve all other verified contracts,
eleven-gate ordering, POL-005, and the unavailable runtime.

## Allowed Files

- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md
- docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md
- docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md
- docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_TRUSTED_APPROVAL_PRESENTATION_EVIDENCE_HPAC_PROOF_LIFECYCLE_CANONICALIZATION_BLOCKING_REPAIR.md
- tests/test_trusted_approval_presentation_hpac_proof_lifecycle_canonicalization_repair_3w1r2b1r111r.py
- .pcae/session.json
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md

## Forbidden Files

- src/pcae/**
- docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md
- docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md
- docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md


## Allowed Zones

- docs
- tests
- tasks
- config

## Forbidden Zones

No additional architecture-zone names; forbidden files and forbidden changes
below carry the exact boundary.

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

strict

## Forbidden Changes

- No runtime invocation
- No prompt execution
- No production source behavior changes
- No execution authorization
- No rollback
- No hardware, authenticator, keychain, PAM, biometric, provider, credential,
  network, article, or private-research access
- No RPAC, RIASC, PBRD, PB policy, POL-005, Runtime Enforcement, Shell Gate,
  adapter, dry-runtime, or runtime-inspect change

## Acceptance Criteria

- B-3 and B-4 are contract-closed with canonical, non-self-authenticating
  presentation evidence and crash-safe proof/approval consumption semantics.
- The other five original blockers and both MUST-FIX findings remain closed;
  new BLOCKING is zero and N2 is contract-closed.
- Eleven gates and gate 10 first-effect semantics remain unchanged.
- No production source or hardware behavior changes; runtime remains
  Observed / observe / unavailable and v0.4.3 remains unchanged.

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- fresh contract/static repair tests pass
- pcae push check passes and origin/main..HEAD equals zero at close

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-08-27T23:09:21.423259+02:00
