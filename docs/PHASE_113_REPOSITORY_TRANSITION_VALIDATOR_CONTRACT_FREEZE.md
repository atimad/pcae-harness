# Phase 113T — Repository Transition Validator Contract Freeze

**Status:** Complete. Architecture/design only — no implementation.

## Purpose

Freeze the Repository Transition Validator contract introduced in
113S. Establishes the validator as the single authority responsible
for validating repository state transitions before any canonical
repository state may change. Elevates the asymmetry discovered during
113S's own finalization (`pcae phase complete` and `pcae task finish
--commit` each capable of independently writing `latest.json`/
`latest.md`) from an implementation detail into a frozen architectural
invariant.

Full contract: `docs/PCAE_REPOSITORY_TRANSITION_VALIDATOR_CONTRACT.md`.

## What This Phase Freezes

1. **Transition Validator interface** — `validate_transition(current_state,
   proposed_transition, expected_target_state, invariants) ->
   TransitionVerdict`; exactly four verdicts (Accept, Reject,
   Quarantine, Requires Human Review), no fifth value permitted.

2. **Repository State** — every canonical object from 113S's 14-item
   list, now with explicit owner, authoritative source, lifecycle, and
   mutability documented per object.

3. **Transition Contracts** — 12 transition kinds (113S's 10 plus
   `report_generation`/`report_promotion` split out explicitly); no
   command may bypass the validator for any of them.

4. **Canonical Transition Authority (first-class requirement)** — `pcae
   phase complete`, `pcae task finish --commit`, and every future
   automation/scheduler/Telegram/REST/agent/execution-engine completion
   path must pass through exactly the same validation path. There must
   never exist two independent canonical report promotion paths.

5. **Canonical Promotion Contract** — 6 states (Draft, Blocked,
   Rejected, Quarantined, Certified, Canonical); only Certified may
   become Canonical.

6. **Identity Contract** — single identity source, single report
   promotion source, single metadata source, single canonical report
   source. No alternate identity derivation, no alternate promotion
   pipeline.

7. **Notification Contract** — eligibility, idempotency, single
   external notification, notification certification, no intermediate
   external notification.

8. **Invariant Contract** — every invariant family classified as
   mandatory/derived/optional/future and blocking/warning/informational.

9. **Failure Contract** — 9 failure modes, each deterministically
   mapped to Reject, Quarantine, or Requires Human Review. No
   undefined-behavior outcome permitted.

10. **Semantic Boundary** — models perform semantic work; the
    validator certifies structural correctness; models never certify
    themselves.

11. **Future Integration** — scope (not design) frozen for task
    lifecycle, phase lifecycle, Runtime Snapshot, Runtime Inspect,
    Advisory Runtime, Permission Broker, execution runtime, approval
    runtime, and future execution.

## The 113S Asymmetry: Resolution Status

**Not fixed by this phase — deliberately.** This phase is architecture/
design only. What changes here is classification: the asymmetry between
`pcae phase complete`'s identity-resolving write path and `pcae task
finish --commit`'s metadata-only write path is no longer merely an
observed implementation quirk corrected by a careful operator (as
happened live during 113S). It is now a named, frozen contract
violation (§1 and §6 of the contract document) that a future
implementation phase (113U or later) must close by routing both
commands through one promotion function. Until that implementation
phase lands, the same operational discipline used to correct it during
113S (verify `latest.json`'s content after any command that might have
written it, before trusting it) remains necessary in practice.

## Relationship to Existing Mechanisms

No source file under `src/pcae/` was touched. This phase does not
change `pcae phase complete`'s or `pcae task finish --commit`'s actual
behavior — it documents, with contract-level precision, what a future
implementation phase must make true.

## Files Added

- `docs/PCAE_REPOSITORY_TRANSITION_VALIDATOR_CONTRACT.md` — the frozen
  contract.
- `docs/PHASE_113_REPOSITORY_TRANSITION_VALIDATOR_CONTRACT_FREEZE.md` —
  this phase-completion document.
- `tests/test_repository_transition_validator_contract_freeze.py` —
  documentation-completeness tests (verifies the contract is fully
  specified in writing; does not test any implementation, since none
  exists).

## No-Go Confirmation

No `validate_transition()` implementation. No change to `pcae phase
complete` or `pcae task finish --commit` behavior. No Advisory Runtime,
Runtime Snapshot, Runtime Context, Runtime Registry, or Permission
Broker changes. No execution, authorization, plugin, Telegram inbound,
REST, Web UI, or execution-behavior changes. Execution capability
remains unavailable.

## Recommended Next Phase

113U — Repository Transition Validator Prototype.
