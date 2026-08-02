# Phase 148C.6 Complete — Permission Broker Foundation Policy Applicability Implementation

**Phase ID:** 148C.6
**Mode:** Production implementation of PBPA-001 v1.0 only
**Predecessor:** 148C.5 (Permission Broker Foundation Policy Applicability Implementation Plan)
**Date:** 2026-08-02
**Status:** completed
**Pushed:** pushed

This is the lightweight staging header for `pcae phase complete`. The full
phase document
(`docs/PHASE_148C.6_PERMISSION_BROKER_FOUNDATION_POLICY_APPLICABILITY_IMPLEMENTATION.md`)
is the canonical artifact of this phase.

---

## Executive Summary

Phase 148C.6 implements **PBPA-001 v1.0 — Permission Broker Policy
Applicability Contract** in exactly one production file,
`src/pcae/core/permission_broker_foundation.py` (confirmed via `git diff
--stat -- src/pcae/`, one file, +112/-5): a frozen `PolicyRule.applicable_execution_classes`
class attribute (default `None` = universal), one generic
non-overridable `applies_to()` predicate, registry-side applicability
filtering in `PolicyRegistry.evaluate_all`, construction-time registry
validation (`POLICY_IDS_CANONICAL` completeness + duplicate-`policy_id`
rejection, both raising `ValueError`), predicate-failure fail-closed
handling, and two additive `PermissionBrokerDecision` fields
(`applicable_policy_ids`, `non_applicable_policy_ids`) with
`evaluated_policy_ids` redefined per `PBPA-REQ-081` to mean exactly the
applicable set.

`POL-004` (`MissingHumanApprovalRule`) is scoped to `{shell, backend,
adapter, rollback}` exactly as `PBPA-REQ-063` froze it — a general rule,
not a push-specific carve-out; its `evaluate()` body is byte-for-byte
unmodified. The other eleven policies remain universal.

Updated the ~10 P-1 test call sites and replaced the P-2 test
(`test_broker_evaluated_policy_ids_always_all_twelve`) per
`PBPA-REQ-081`. Implementation additionally discovered and repaired a
broader test-change surface than 148C.5's plan enumerated: every ad-hoc
custom-`PolicyRegistry` construction across the existing composition/
rule-framework/verification-compatibility/observation-verification
suites required the canonical `DEFAULT_POLICY_RULES` added, since
construction-time validation (`PBPA-REQ-073`) applies to every
registry, not only the default one; "empty registry" tests were
rewritten to assert `ValueError` at construction rather than `DENY` at
evaluation. Added `tests/test_permission_broker_policy_applicability.py`
(127 new tests: complete `POL-001..012` applicability matrix,
anti-spoofing, missing/duplicate/predicate-failure fail-closed,
explainability, and all four real production consumer shapes).

All existing broker suites (851 tests), the new applicability suite
(127 tests), push regression (84 tests), runtime regression (2305
tests), and `fast_green` (4391 tests) pass with zero failures.

Confirmed via direct observation (not a B-1 closure): a conceptual PBPC
push request (`execution_class=mutation`, `approval_present=False`) now
resolves `POL-004` as non-applicable and the decision is `ALLOW`.
**Finding B-1 remains formally OPEN**, pending 148C.7's independent
implementation verification and a later PBPC-001 v1.2 re-evaluation.

**Verdict: PBPA-001 v1.0 IMPLEMENTED, ZERO BLOCKING FINDINGS.**

This verdict does **not** mean Finding B-1 is closed (it is not), or
Chapter 148D is recommended (it is not).

No `POL-001..012` rule meaning was changed. No `POL-013+` policy was
introduced. No `pcae push` production behavior was changed (`push.py`
unchanged, confirmed via `git diff --name-only -- src/pcae/commands/push.py`,
empty). No approval was fabricated. Runtime remains `Observed / observe
/ unavailable`, unchanged.

Recommended next phase: **148C.7 — Permission Broker Foundation Policy
Applicability Independent Implementation Verification**. **148D is not
recommended.** This recommendation is not an authorization to begin
either.

---

## Appendix: Bootstrap and Governance Validation

Bootstrap (run before this phase began): `pcae session bootstrap
--agent-id claude-local`; `pcae check`/`pcae health`/`pcae status
coherence`/`pcae doctor task-memory`/`pcae runtime inspect`/`pcae push
check`/`pcae notify status`/`pcae phase-report show --latest`/`pcae
phase-report reconcile --phase-id 148C.5` all clean at phase start,
confirming 148C.5 completed with Finding B-1 open and 148C.6
recommended. `pcae task new` opened this phase's own governed task
contract, scoped to `permission_broker_foundation.py`, the six affected
test files, the new phase document, and ordinary status/task
bookkeeping.

Validation performed during this phase: direct source inspection of
`docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`
(full text, both pages) and the current
`permission_broker_foundation.py` (787 lines) before implementing;
every production change traced to a specific `PBPA-REQ-###`
requirement. All existing Permission Broker Foundation suites (851
tests across 10 files, including the two unrelated Phase 88R
`permission_broker.py`/`permission_broker_cli.py` files re-run
unmodified) pass. The new applicability suite (127 tests) passes. Push
regression (`tests/test_push.py`, `test_commit_push_gate.py`,
`test_staged_file_aware_push.py`, `test_push_phase_report_identity_137f1.py`):
84 passed, 0 failed, 250.44s. Runtime regression (2305
runtime/enforcement/registry/introspection/snapshot/context tests): 0
failed. `python -m pytest -m fast_green -n auto -q`: 4391 passed, 0
failed, 105 warnings, 117.90s. `pcae check`/`pcae health`/`pcae status
coherence`/`pcae doctor task-memory`/`pcae runtime inspect`/`pcae push
check` all re-run clean before finalization; `pcae runtime inspect`
reconfirmed `Observed / observe / unavailable`, unchanged before and
after this phase. `git diff --stat -- src/pcae/` confirmed exactly one
production file changed.

**Known, disclosed operational note on this artifact's own trust gate**
(the same self-referential staleness gap Phase 147P's, 147Q's, 147R's,
148A's, 148B's, 148C's, 148C.1's through 148C.5's own canonical reports
each documented in this same appendix section): this phase's `pcae
phase complete` invocation required directly authoring both
`.pcae/phase-completion-metadata.json` and this canonical report
artifact before completion, because the Repository Transition
Validator's `phase_identity_consistency`/`metadata_consistency` checks
compare the *incoming* phase identity (148C.6) against whatever
canonical report/metadata existed on disk — which, before this phase's
own successful completion, was still Phase 148C.5's own canonical
report and structured metadata (`phase_id: "148C.5"`). This is not a
defect in this phase's own work; it is the same pre-existing,
previously-documented self-referential staleness check prior phases'
own appendices described.
