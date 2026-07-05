# Phase 113S — Repository Transition Validator Architecture

**Status:** Complete. Architecture/design only — no implementation.

## Purpose

Turn the 113X/Claude-DeepSeek incident (a cross-agent phase completion
whose canonical report carried stale commits and stale test results
because a metadata file was never rewritten between phases) into a
formal PCAE design principle:

> Model proposes. PCAE validates. Repository advances only through
> valid state transitions.

Full architecture: `docs/PCAE_REPOSITORY_TRANSITION_VALIDATOR.md`.

## What This Phase Defines

1. **Repository State** — 14 independently-observable components (git
   state, working tree, active task, phase identity, project status,
   phase reports, phase-completion metadata, architecture status, test
   results, governance checks, notification state, push state, runtime
   state, execution availability), each with exactly one authoritative
   reader, never derived from another's free text.

2. **Proposed Transition** — 10 recognized transition kinds
   (`start_task`, `modify_files`, `run_validation`, `commit`,
   `finish_task`, `complete_phase`, `push`, `notify`, `update_status`,
   `produce_report`). The proposing agent never has authority to make
   its own proposal canonical.

3. **Transition Validator** — a pure function
   `validate_transition(current_state, proposed, target_state,
   invariants) -> TransitionVerdict`, deliberately blind to which agent
   is proposing.

4. **Invariants** — 15 invariant families, including phase identity
   consistency, active task consistency, allowed file scope, commit
   lineage, report completeness, report trust, metadata consistency,
   architecture status consistency, recommended-next-phase consistency,
   test result consistency, push state consistency, notification
   eligibility, single-final-notification, no-execution-availability,
   and no-canonical-promotion-when-blocked.

5. **Accept/Reject/Quarantine/Human-Review semantics** — four
   exhaustive, mutually exclusive verdicts, each with a precise
   definition of what does and doesn't happen to canonical state.

6. **Canonical artifact promotion** — a 5-state model (Draft → Blocked
   / Quarantined / Certified → Canonical/latest); only Certified
   artifacts may ever become canonical.

7. **Notification eligibility** — 5 simultaneous conditions (finalized,
   certified, push-clean, not-already-dispatched, transport
   configured/enabled); intermediate reports are never externally
   dispatched.

8. **Semantic vs. structural boundary** — models own code design,
   implementation strategy, explanations, remediation, prose; PCAE owns
   identity, lifecycle, scope, reports, commits, pushes, notifications,
   canonical state.

9. **Model-agnostic behavior** — the validator's signature has no field
   for agent identity; the same invariants apply to Claude,
   Claude-DeepSeek, Codex, Qwen, human operators, and future models
   alike.

10. **Future integration** — documented, non-redesigning integration
    points for task lifecycle, phase lifecycle, commit governance, push
    governance, notification runtime, Runtime Snapshot/Advisory
    Runtime, and future intent/approval/execution layers.

## Relationship to Existing Mechanisms

This phase does not replace or modify any existing code path. The
architecture is written so that today's `validate_finalization_gate()`,
`validate_phase_identity()`, `check_task_zone_scope()`/
`check_task_file_scope()`, and `pcae push check` are describable as
*specific, already-implemented instances* of the general validator
model (phase-completion and task-scope invariant families,
specifically) — not as things this phase changes. No source file under
`src/pcae/` was touched.

## Files Added

- `docs/PCAE_REPOSITORY_TRANSITION_VALIDATOR.md` — the architecture
  document (durable contract, mirrors the shape of
  `docs/PCAE_ADVISORY_RUNTIME_CONTRACT.md`).
- `docs/PHASE_113_REPOSITORY_TRANSITION_VALIDATOR_ARCHITECTURE.md` —
  this phase-completion document.
- `tests/test_repository_transition_validator_architecture.py` —
  documentation-completeness tests (verifies the architecture is fully
  specified in writing; does not test any implementation, since none
  exists).

## No-Go Confirmation

No `validate_transition()` implementation. No Advisory Runtime, Runtime
Snapshot, Runtime Context, or Permission Broker changes. No execution,
authorization, plugin, Telegram inbound, REST, Web UI, audit
persistence, or rollback changes. No change to any existing
finalization-gate, phase-identity, or push-check code path. Execution
capability remains unavailable.

## Recommended Next Phase

113T — Repository Transition Validator Contract Freeze.
