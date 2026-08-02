# Phase 148C.5 Complete — Permission Broker Foundation Policy Applicability Implementation Plan

**Phase ID:** 148C.5
**Mode:** Implementation planning only — no implementation, no contract amendment
**Predecessor:** 148C.4 (Permission Broker Foundation Policy Applicability Contract Independent Verification)
**Date:** 2026-08-02
**Status:** completed
**Pushed:** pushed

This is the lightweight staging header for `pcae phase complete`. The full
implementation plan
(`docs/PHASE_148C.5_PERMISSION_BROKER_FOUNDATION_POLICY_APPLICABILITY_IMPLEMENTATION_PLAN.md`)
is the canonical artifact of this phase.

---

## Executive Summary

Phase 148C.5 produces a concrete, bounded, section-by-section
implementation plan for **PBPA-001 v1.0 — Permission Broker Policy
Applicability Contract**, translating its normative text into an
actual, reviewable production change surface without implementing it.
The plan is grounded in direct inspection — not summaries — of
`permission_broker_foundation.py` (787 lines, the sole `MUST_CHANGE`
production file), every real production consumer (`health.py`,
`task.py`, `check.py`, `push.py`, all `action_type="read"`,
`execution_class="none"`, `approval_present=True`), and all ten
Permission-Broker-adjacent test files (two of which,
`test_permission_broker.py`/`test_permission_broker_cli.py`, were found
to target an unrelated Phase 88R module and excluded from scope).

This phase independently discovered two concrete test-change-surface
findings not present in PBPA-001's own text: **P-1**, at least ten
existing test call sites across four files assert `HUMAN_REVIEW` using
the default `execution_class="none"`, outside `POL-004`'s frozen
applicable set (`{shell, backend, adapter, rollback}`), and will need
updating once applicability filtering activates; **P-2**, a named test
(`test_broker_evaluated_policy_ids_always_all_twelve`) directly asserts
an invariant `PBPA-REQ-081` deliberately redefines. Both are Non-
Blocking findings with concrete, specified remediation in the plan
itself (Section 40).

The plan selected Option A — a declarative `applicable_execution_classes`
frozen class attribute plus one generic, non-overridable `applies_to()`
predicate — over a separate applicability object or a registry-level
mapping, matching PBPA-001's own selection while independently
re-deriving why (Section 5/6). It classified every planned API change
(additive, backward-compatible, or documented-semantic-change-only —
`evaluated_policy_ids`'s redefined meaning under `PBPA-REQ-081` is
called out explicitly rather than folded into "additive"). It planned a
six-stage implementation sequence in which every pre-final stage is
individually a zero-behavior-change commit, requiring no feature flag,
and specified a full anti-spoofing/fail-closed/POL-matrix test plan for
the implementation phase to write.

Independent, exhaustive enumeration confirmed zero production impact:
all four real consumers use `execution_class="none"` (already outside
`POL-004`'s narrowed scope) and `approval_present=True` (so `POL-004`
never triggers for them regardless of applicability) — every one of the
twelve `POL-001..012` results for these four call sites is unchanged by
this plan's proposed implementation.

**Verdict: PLANNING COMPLETE, ZERO BLOCKING FINDINGS — IMPLEMENTATION
MAY PROCEED.**

This verdict does **not** mean PBPA-001 is implemented (it is not),
Finding B-1 is closed (it is not), or Chapter 148D is recommended (it is
not).

No `src/pcae/**` file was modified (confirmed via `git diff --name-only
29418796..HEAD -- src/pcae/`, empty). No Permission Broker Foundation
behavior was changed. No `POL-001..012` rule was modified. No `POL-013+`
policy was introduced or implemented. No approval was fabricated.
Runtime remains `Observed / observe / unavailable`, unchanged.

Recommended next phase: **148C.6 — Permission Broker Foundation Policy
Applicability Implementation** — implementing exactly this plan's
Sections 4-25/27-31. **148D is not recommended.** This recommendation is
not an authorization to begin either.

---

## Appendix: Bootstrap and Governance Validation

Bootstrap (run before this phase began): `pcae session bootstrap
--agent-id claude-local`; `pcae check`/`pcae health`/`pcae status
coherence`/`pcae doctor task-memory`/`pcae runtime inspect`/`pcae push
check`/`pcae notify status`/`pcae phase-report show --latest`/`pcae
phase-report reconcile --phase-id 148C.4` all clean at phase start,
confirming 148C.4 completed with Finding B-1 open and 148C.5
recommended. `pcae task new` opened this phase's own governed task
contract, scoped to the new implementation-plan document and ordinary
status/task bookkeeping; `src/pcae/**` explicitly forbidden.

Validation performed during this phase: direct source inspection of the
Permission Broker Foundation module, every real production consumer
call site, and every Permission-Broker-adjacent test file (not planned
from summaries); every design decision traced to a specific
`PBPA-REQ-###` requirement or specific existing source line; complete
production and test change-surface inventories; a full `POL-001..012`
applicability metadata table cross-checked against PBPA-001 §17/18 and
148C.4's own independent re-derivation; a security-invariant checklist
(caller-cannot-select-policy-membership, fail-closed unknown/missing/
duplicate-policy, non-applicable-never-`ALLOW`, `approval_present`/
`simulation_only` cannot control applicability) verified against the
plan's own design, not merely asserted. `tests/test_permission_broker_foundation.py`,
`tests/test_permission_broker_policy_composition_hardening.py`,
`tests/test_permission_broker_policy_rule_framework.py` (171 tests) run
live, unmodified: all passing, confirming this phase's own diff changed
no test behavior. `python -m pytest -m fast_green -n auto -q` run live
twice this session: the first run showed one failure
(`tests/test_backend_cli.py::TestBackendReviewCreate::test_create_persists_to_latest`)
that reproduced as the same parallelization-order flake documented by
148C.4 and earlier phases — it passed in isolation in 0.54s, unrelated
to this phase's diff — and the second run passed cleanly: 4391 passed,
0 failed, 105 warnings, 105.86s. `pcae check`/`pcae health`/`pcae status
coherence`/`pcae doctor task-memory`/`pcae runtime inspect`/`pcae push
check` all re-run clean before finalization; `pcae runtime inspect`
reconfirmed `Observed / observe / unavailable`, unchanged before and
after this phase. `git diff --name-only 29418796..HEAD -- src/pcae/`
confirmed empty — no production source changed by this phase.

**Known, disclosed operational note on this artifact's own trust gate**
(the same self-referential staleness gap Phase 147P's, 147Q's, 147R's,
148A's, 148B's, 148C's, 148C.1's, 148C.2's, 148C.3's, and 148C.4's own
canonical reports each documented in this same appendix section): this
phase's `pcae phase complete` invocation required directly authoring
both `.pcae/phase-completion-metadata.json` and this canonical report
artifact before completion, because the Repository Transition
Validator's `phase_identity_consistency`/`metadata_consistency` checks
compare the *incoming* phase identity (148C.5) against whatever
canonical report/metadata existed on disk — which, before this phase's
own successful completion, was still Phase 148C.4's own canonical
report and structured metadata (`phase_id: "148C.4"`). This is not a
defect in this phase's own work; it is the same pre-existing,
previously-documented self-referential staleness check prior phases'
own appendices described.
