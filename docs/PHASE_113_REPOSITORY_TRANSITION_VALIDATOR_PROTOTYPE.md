# Phase 113U — Repository Transition Validator Prototype

**Status:** Complete. Observation-only implementation.

## Purpose

Implement the first working prototype of the Repository Transition
Validator interface frozen in Phase 113T
(`docs/PCAE_REPOSITORY_TRANSITION_VALIDATOR_CONTRACT.md`). The
prototype validates proposed repository transitions structurally, but
is not yet wired into any production lifecycle command — it has zero
effect on `pcae phase complete`, `pcae task finish --commit`, `pcae
push`, or notification dispatch.

## Module

`src/pcae/core/repository_transition_validator.py`.

## Prototype Scope

Implements:

- `RepositoryState` — a structural snapshot dataclass. No agent/model
  identity field exists on it.
- `ProposedTransition` — `kind` (one of the 12 frozen `TransitionKind`
  values) plus an open `payload` dict. `validate_transition` never
  reads an identity field from `payload`, even if a caller puts one
  there for its own bookkeeping.
- `ExpectedTargetState` — the target `artifact_state`/`phase_id` a
  caller proposes.
- `TransitionInvariant` / `InvariantViolation` — the invariant-record
  shapes, carrying `classification` (mandatory/derived/optional/future)
  and `force` (blocking/warning/informational) per 113T's Invariant
  Contract.
- `TransitionVerdict` — exactly the four frozen values: `accept`,
  `reject`, `quarantine`, `requires_human_review`.
- `validate_transition(current_state, proposed_transition,
  expected_target_state, invariants) -> TransitionResult` — pure
  function, deterministic, no I/O.
- `notification_eligible(state) -> (bool, reasons)` — the 5-condition
  eligibility check from 113T Section 7, reusable standalone or via the
  `notify` transition kind.
- `promotion_allowed(current, target) -> bool` — the canonical
  promotion rule from 113T Section 5 as a standalone helper.

## Observation-Only Status

Confirmed by construction, not merely by convention: no file under
`src/pcae/commands/` was modified. `pcae phase complete`, `pcae task
finish --commit`, `pcae push`, and every notification code path are
byte-for-byte unchanged. The only way `validate_transition` executes
is a direct Python call — today, only from
`tests/test_repository_transition_validator.py`.

## Invariants Implemented (Structural Subset)

This prototype implements 7 of 113T's frozen invariant families —
specifically the ones evaluable purely from a `RepositoryState` value
with no live filesystem/git access required:

1. `phase_identity_consistency` — mandatory, blocking. Disagreement
   among active-task/metadata/lifecycle-context phase_id sources
   rejects. A lifecycle-context phase_id marked completed is correctly
   excluded from the comparison (mirrors
   `resolve_canonical_phase_identity`'s own rule).
2. `metadata_consistency` — mandatory, blocking. Metadata phase_id
   disagreeing with the proposed target phase_id rejects — this is the
   exact invariant that would have caught the 113D defect had it
   existed and been wired in at the time.
3. `report_completeness` — mandatory, blocking for "missing evidence"
   (empty/unknown completeness, or no test_results and no commits at
   all); warning-classified (quarantine, not reject) for `"partial"`.
4. `recommended_next_phase_presence` — mandatory, blocking. Empty
   `recommended_next_phase` rejects — the second 113D defect, made
   directly checkable.
5. `canonical_promotion_eligibility` — mandatory, blocking. Proposing
   `ArtifactState.CANONICAL` as a target when current state isn't
   `CERTIFIED` rejects.
6. `notification_eligibility` — mandatory, blocking, evaluated only for
   the `notify` transition kind (a `complete_phase` transition is never
   rejected merely because notification wouldn't currently be
   eligible — eligibility is a property of the `notify` transition
   itself, not a global gate).
7. `no_execution_availability_unless_contracted` — mandatory, blocking.
   `execution_availability != "unavailable"` rejects unconditionally,
   since no execution-enablement contract exists yet.

## What Remains Future Enforcement

Explicitly not done in this phase:

- **Wiring into `pcae phase complete`.** The validator is not called
  by the real finalization path. `validate_finalization_gate()` and
  `validate_phase_identity()` remain the actual enforcement mechanism
  today.
- **Wiring into `pcae task finish --commit`.** The 113T-frozen
  requirement ("there must never exist two independent canonical
  report promotion paths") is not yet satisfied by code — only by
  contract. `_finalize_task_report_and_notify()` still writes
  `latest.json`/`latest.md` independently.
- **Live-state invariants.** `commit_lineage` (checking real git commit
  messages against the report's claimed phase), `architecture_status_consistency`,
  `push_state_consistency` (reading real `git rev-list` output), and
  `test_result_consistency` (reconciling structured fields against a
  live pytest run) all require filesystem/git/subprocess access this
  pure-function prototype deliberately does not have. A future
  verification phase (113V) should determine whether the validator
  gains an I/O-performing adapter layer or whether callers are
  responsible for populating `RepositoryState` from live sources before
  calling it.
- **`requires_human_review`.** The verdict is defined and tested to
  exist, but no structural check in this prototype can produce it — per
  113T's Failure Contract, it is reserved for "validator unavailable"
  (e.g. a required file is missing, an exception is raised) — a
  condition orthogonal to this pure, always-evaluable prototype. A
  future integration phase that wraps live I/O around this validator
  is the natural place for that path to appear.

## Notification Asymmetry — Documented as Future Integration Target

113U's brief flags an additional, distinct asymmetry observed after
113T: repository completion can be canonical while `pcae skill invoke
phase-finalization <phase-id>` (and, by extension, any future
Telegram/REST completion trigger built on the same skill-targeting
registry) reports `target_unresolved` for special phase IDs like every
`113X.*`/`113S`/`113T`/`113U`-style phase this repository has produced.
This is **not fixed in this phase**. It is recorded here as a future
validator integration target: once the validator is wired into real
lifecycle paths (a future phase), it should be the single place that
reconciles "is this phase's canonical report Certified/Canonical" with
"does the skill-invocation targeting registry know about this phase
ID" — today these are two independent, unreconciled questions, and a
`blocked`/`target_unresolved` skill-invocation result must not be
misread as meaning the phase itself is somehow invalid.

## Model-Agnostic Behavior — Verified

`RepositoryState` and `ProposedTransition` carry no agent/model
identity field (verified directly via `dataclasses.fields()` in
`TestModelAgnosticBehavior`). A test confirms that putting an `"agent"`
key in `ProposedTransition.payload` (e.g. `"Claude"` vs.
`"Claude-DeepSeek"` vs. absent) never changes the verdict for an
otherwise-identical `RepositoryState`.

## Tests

`tests/test_repository_transition_validator.py` — 36 tests, all
passing. Covers: validator/helper existence; all four verdicts exist;
accept/reject/quarantine behavior; phase identity mismatch rejection
(including the lifecycle-context-completed exemption and the
metadata-vs-target-phase_id case); all 6 canonical promotion states and
the certified-only-may-become-canonical rule, both as a standalone
helper and through the full validator; notification eligibility's 5
conditions individually and combined, plus confirmation that
non-`notify` transitions are unaffected by notification state;
execution-availability violation rejection; model-agnostic behavior;
determinism (same inputs, repeated calls, stable output).

## No-Go Confirmation

No Advisory Runtime, Runtime Snapshot, Runtime Context, Runtime
Registry, or Permission Broker changes. No execution, authorization,
plugin, Telegram inbound, REST, Web UI changes. No change to any
existing lifecycle enforcement path (`pcae phase complete`, `pcae task
finish --commit`, `pcae push`, notification dispatch all unchanged).
Execution capability remains unavailable.

## Recommended Next Phase

113V — Repository Transition Validator Verification & Compatibility.
