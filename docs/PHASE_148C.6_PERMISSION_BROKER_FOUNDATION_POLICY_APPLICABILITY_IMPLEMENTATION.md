# Phase 148C.6 — Permission Broker Foundation Policy Applicability Implementation

## 0. Phase Type and Scope

**Production implementation of PBPA-001 v1.0 only.** This phase
implements the applicability layer PBPA-001 froze (Phase 148C.3) and
148C.5 planned, in exactly one production file. It does not modify
`pcae push` production behavior, does not implement PBPC consumption,
does not add `POL-013+`, does not change `POL-001..012` meanings, does
not fabricate approval, does not close Finding B-1, does not change IWC
semantics, does not change Authority Evaluation/AESIC, does not modify
Runtime Enforcement semantics, does not introduce shell/backend
execution, does not elevate runtime capability, and does not begin
148D.

## 1. Production Change Surface

Exactly one production file changed, confirmed by `git diff --stat --
src/pcae/`:

```
src/pcae/core/permission_broker_foundation.py   (+107/-5)
```

`src/pcae/commands/push.py` and every other file 148C.5 identified as
`MUST_NOT_CHANGE` remained untouched (confirmed via `git diff
--name-only -- src/pcae/commands/push.py`, empty).

## 2. Implementation Summary

Following 148C.5's staged plan (types/metadata → registry validation →
predicate → evaluation wiring → explainability), implemented in
`permission_broker_foundation.py`:

1. **Applicability representation.** `PolicyRule.applicable_execution_classes:
   frozenset[str] | None = None` — a frozen class attribute, default
   `None` meaning universal, identical to every rule's pre-PBPA behavior
   (PBPA-REQ-018/044).
2. **Single applicability authority.** One generic, non-overridable
   `PolicyRule.applies_to(request)` predicate — pure, deterministic,
   reading only `self.applicable_execution_classes` and
   `request.execution_class` (PBPA-REQ-050-056). No registry-side scope
   map, no per-command exclusion, no caller-provided policy list
   (PBPA-REQ-021/022).
3. **Applicability state separate from decision.** `PolicyResult.applicable:
   bool = True` (default preserves every pre-PBPA call site).
   `NOT_APPLICABLE` is represented only as `applicable=False`, never a
   fourth broker-level decision value (PBPA-REQ-013/014).
4. **`execution_class` validation.** Unchanged — `POL-006`
   (`UnknownCapabilityRule`) remains universal and DENYs any value
   outside `KNOWN_EXECUTION_CLASSES` before applicability is meaningful
   for any other rule (PBPA-REQ-077, unchanged code).
5. **Classification authenticity.** Unchanged — inherited trust boundary
   (PBPA-REQ-032/033), no new independent re-derivation mechanism added
   (none required by PBPA-001).
6. **`POL-001..012` applicability metadata.** All twelve encoded. Eleven
   remain universal (`None`, unchanged default); `POL-004`
   (`MissingHumanApprovalRule`) is scoped:

   ```python
   applicable_execution_classes = frozenset({
       EXECUTION_CLASS_SHELL, EXECUTION_CLASS_BACKEND,
       EXECUTION_CLASS_ADAPTER, EXECUTION_CLASS_ROLLBACK,
   })
   ```

   `POL-004.evaluate()`'s body is byte-for-byte unmodified — only the
   sibling applicability attribute was added (PBPA-REQ-101).
7. **`POL-004` scope is general, not push-specific.** No
   `if action_type == "push"` branch exists anywhere. The frozen
   frozenset is the sole mechanism; a future `pcae push` request would
   find `POL-004` non-applicable as one instance of the general rule
   applied to `execution_class=mutation` (PBPA-REQ-064).
8. **Evidence independence.** `approval_present` is never read by
   `applies_to()` — applicability is resolved from `execution_class`
   alone, strictly before evaluation (PBPA-REQ-011/012/066/067).
9. **`simulation_only`.** Not read by `applies_to()` and not part of any
   policy's metadata — toggling it has zero effect on the applicable
   policy set (PBPA-REQ-068/069).
10. **Registry validation.** `PolicyRegistry.__init__` now validates, at
    construction time: unique `policy_id` (raises `ValueError` on
    duplicate) and canonical-set completeness against a new,
    independent `POLICY_IDS_CANONICAL` constant (raises `ValueError` if
    any of the twelve canonical ids is absent) — extending fail-closed
    from evaluate-time to construction-time (PBPA-REQ-073/075).
11. **Required policy set / empty applicable set.** Not adopted as a
    separate mechanism (PBPA-REQ-072, not required by v1.0); the
    pre-existing `_compose` empty-`results` DENY branch remains the
    defense-in-depth fallback, exercised directly in the new test suite
    since no currently-constructible registry can reach it (registry
    construction itself now rejects any incomplete rule set first).
12. **Applicability resolution.** `PolicyRegistry.evaluate_all` calls
    `rule.applies_to(request)` before `rule.evaluate(request)`; a
    non-applicable rule is never evaluated — the registry synthesizes
    `PolicyResult(policy_id=..., triggered=False, applicable=False)`
    instead (PBPA-REQ-015).
13. **Predicate failure.** A predicate that raises — including a
    malformed rule object missing `applies_to()` entirely — is caught
    and sanitized through the same fail-closed path as an `evaluate()`
    exception (`_sanitize_result`), never silently treated as
    `NOT_APPLICABLE` (PBPA-REQ-097). This one addition goes slightly
    beyond 148C.5's plan text (which reserved this case as "not
    exercisable" since no override existed at plan time) — it was
    required once an actual malformed-rule test in the existing suite
    (`tests/test_permission_broker_observation_verification.py::test_malformed_policy_result_sanitized_to_fail_closed_deny`)
    exercised a rule object with no `applies_to` method at all.
14. **Decision aggregation.** `_compose` unmodified in logic — it
    already only inspects `r.triggered`, and a non-applicable
    (`triggered=False`) result is structurally indistinguishable from
    "evaluated, did not fire" (PBPA-REQ-079/080).
15. **Explainability.** `PermissionBrokerDecision` gains
    `applicable_policy_ids`/`non_applicable_policy_ids` (additive,
    default `()`). `evaluated_policy_ids` is redefined, per
    PBPA-REQ-081, to mean exactly the applicable set — computed as
    `evaluated_ids = applicable_ids` rather than the unfiltered
    `tuple(r.policy_id for r in results)` 148C.5's plan text described;
    the plan's claim that "no further code change" was needed was
    imprecise (the unfiltered formula does not equal the applicable-only
    set once non-applicable placeholders are included in `results`) —
    this phase implements PBPA-REQ-081's actual requirement directly.

## 3. Discovery Beyond 148C.5's Plan: Registry-Validation Test Impact

148C.5's plan (Section 2) predicted roughly ten test-call-site updates
(the P-1/P-2 findings). Implementing PBPA-REQ-073's construction-time
registry validation exactly as frozen revealed a materially larger test
surface than the plan enumerated: **every** ad-hoc, minimal
`PolicyRegistry(rules=(...))` construction across
`test_permission_broker_policy_composition_hardening.py`,
`test_permission_broker_policy_rule_framework.py`,
`test_permission_broker_verification_compatibility.py`, and
`test_permission_broker_observation_verification.py` — a long-standing
test pattern used to test generic composition/fail-closed mechanics
independent of the real twelve-policy set — newly raises `ValueError` at
construction, since none of those ad-hoc registries contain all twelve
canonical ids.

This is squarely required by PBPA-REQ-073's literal text ("A future
implementation SHALL validate, at `PolicyRegistry` construction
time, that every canonical `POLICY_IDS` member is present in the
constructed rule tuple") — not a bug, and not something this phase is
authorized to soften. Resolution, applied per-test, preserving each
test's actual intent (never weakening an assertion):

- **Minimal custom registries testing composition mechanics**
  (`_DenyRule`/`_HumanReviewRule`/`_NeverTriggers`-style fixtures):
  `DEFAULT_POLICY_RULES + (custom rules...)`. Since every such test's
  request already satisfies all twelve real rules' non-triggering
  conditions, the real rules remain silently non-triggering and the
  custom rule(s) still solely determine the asserted outcome.
- **`test_broker_evaluate_delegates_to_registry`** (Phase 108B): its
  actual intent — "the broker follows whichever registry implementation
  it is given, not hardcoded logic" — required substituting a
  same-named `"POL-001"` implementation into the full canonical set
  (rather than omitting `POL-001` entirely, no longer constructible)
  to prove the point without contradicting PBPA-REQ-073.
- **Explicit "empty registry" tests**
  (`test_no_applicable_policy_fails_closed`,
  `test_empty_registry_fails_closed`,
  `test_empty_registry_fails_closed_to_deny`): rewritten to assert
  `pytest.raises(ValueError, match="missing canonical policy")` on
  `PolicyRegistry(rules=())`, since PBPA-REQ-073 moves this fail-closed
  behavior from `evaluate()`-time to construction-time — the pre-PBPA
  scenario (construction succeeds, `evaluate()` denies) is no longer
  reachable.
- **`test_command_output_unchanged_when_broker_registry_empty`**
  (parametrized over all four real integrations): could no longer
  literally construct an empty registry to obtain its `DENY` decision
  fixture; the DENY decision is instead obtained from the default,
  fully-valid registry evaluating a request with `task_id=None`
  (`POL-001` DENY) — preserving the test's real intent ("an arbitrary
  DENY decision, substituted as observe()'s return value, leaves
  command output unchanged") without depending on a now-impossible
  construction.

This is recorded as **NON-BLOCKING** — implementation proceeded to
completion with a fully-repaired test suite — but it materially widens
the test-change surface beyond what 148C.5 characterized, and 148C.7
should independently re-verify every one of these test-semantic changes
against PBPA-001's actual text rather than trusting this phase's
characterization of "preserved intent."

## 4. Test Suite Changes

| File | Change |
|---|---|
| `tests/test_permission_broker_foundation.py` | P-1: added `execution_class="shell"` to the HUMAN_REVIEW-asserting call site and two `seen_ng_ids`/`seen_inv_ids` scenario dicts; added a new test proving `execution_class="none"` + `approval_present=False` → `ALLOW`, `POL-004` non-applicable. |
| `tests/test_permission_broker_policy_composition_hardening.py` | Added `DEFAULT_POLICY_RULES` to 11 ad-hoc custom-registry constructions; added `execution_class="shell"` to 4 call sites whose assertions depended on `POL-004` being applicable; rewrote the empty-registry test to assert construction-time `ValueError`. |
| `tests/test_permission_broker_policy_rule_framework.py` | P-2: replaced `test_broker_evaluated_policy_ids_always_all_twelve` with `test_broker_evaluated_policy_ids_equal_applicable_policy_set` (asserts 12 at an in-scope class, 11 at an out-of-scope class) and a new partition test; added `DEFAULT_POLICY_RULES`/`execution_class="shell"` to 6 further call sites; restructured `test_broker_evaluate_delegates_to_registry` to substitute a same-`policy_id` `"POL-001"` implementation into the full canonical set. |
| `tests/test_permission_broker_verification_compatibility.py` | Added `DEFAULT_POLICY_RULES`/`execution_class="shell"` to 7 call sites; rewrote the empty-registry test. |
| `tests/test_permission_broker_observation_verification.py` | Added `DEFAULT_POLICY_RULES` to a malformed-rule registry; rewrote the empty-registry test; replaced the empty-registry decision fixture in the parametrized command-output test with a `task_id=None` DENY fixture from the default registry. |
| `tests/test_permission_broker_policy_applicability.py` (new) | 127 new tests: complete `POL-001..012` applicability matrix across all six execution classes; `POL-004` in-scope/out-of-scope/evidence-independence; anti-spoofing (unknown class, `simulation_only` spoofing, direct invocation); missing/duplicate-policy construction-time rejection; predicate-failure fail-closed; empty-set defense-in-depth; explainability determinism/partition/ordering; all four real production consumer request shapes. |

No test assertion was weakened to accommodate a non-conforming
implementation — every changed assertion traces to a specific
`PBPA-REQ-###` requirement cited in this document or in the test file's
own inline comment.

## 5. Test Results

```
tests/test_permission_broker_foundation.py
tests/test_permission_broker_policy_composition_hardening.py
tests/test_permission_broker_policy_rule_framework.py
tests/test_permission_broker_verification_compatibility.py
tests/test_permission_broker_observation_hardening.py
tests/test_permission_broker_observation_verification.py
tests/test_permission_broker_command_path_prototype.py
tests/test_permission_broker_command_path_design.py
tests/test_permission_broker.py
tests/test_permission_broker_cli.py
tests/test_permission_broker_policy_applicability.py
  851 passed (existing broker suites) + 127 passed (new applicability suite)

tests/test_push.py tests/test_commit_push_gate.py
tests/test_staged_file_aware_push.py tests/test_push_phase_report_identity_137f1.py
  84 passed, 0 failed, 250.44s

Runtime regression (-k "runtime and (inspect or enforcement or registry
or introspection or snapshot or context)")
  2305 passed, 0 failed

python -m pytest -m fast_green -n auto -q
  4391 passed, 0 failed, 105 warnings, 117.90s
```

No failure was suppressed. No `--no-verify` used.

## 6. B-1 Post-Implementation Observation (Not a Closure)

A conceptual PBPC-conformant push request, under PBPC-001's frozen
values (`action_type=ACTION_PUSH`, `execution_class=EXECUTION_CLASS_MUTATION`,
`approval_present=False`), evaluated directly against the implemented
Foundation:

```
decision: ALLOW
applicable_policy_ids: (POL-001, POL-002, POL-003, POL-005, POL-006,
                         POL-007, POL-008, POL-009, POL-010, POL-011,
                         POL-012)
non_applicable_policy_ids: (POL-004,)
```

This is **implementation evidence only**. Finding B-1 (Phase 148C,
Blocking; PBPC-001 §8.1) **remains formally OPEN**. Formal closure
requires 148C.7's independent implementation verification and a later
PBPC-001 v1.2 re-evaluation (PBPA-001 §38's remaining closure path,
unchanged by this phase).

## 7. 12-Hard-Block Boundary

This phase implements which of the twelve `POL-` rules apply to a given
request. It does not address the separate `HARD_BLOCK_REGISTRY`
centralization gap (PBPC-001 §8/§18) — that gap is unaffected, neither
closed nor worsened, exactly as PBPA-001 §39 states.

## 8. Findings

| ID | Finding | Classification |
|---|---|---|
| F-1 | 148C.5's plan Section 16 claim that "`evaluated_policy_ids` already equals `applicable_policy_ids` without any further code change" was imprecise — the unfiltered `results`-based formula does not equal the applicable-only set once non-applicable placeholders are included. Corrected during implementation (Section 2.15 above). | Non-Blocking — caught and fixed before any test asserted incorrect behavior. |
| F-2 | 148C.5's plan (Section 2) materially under-predicted the test-change surface from PBPA-REQ-073's construction-time registry validation — every ad-hoc custom-registry test across four files required updating, not only the ~10 P-1/P-2 sites. | Non-Blocking — fully repaired (Section 3 above); flagged for 148C.7 to independently re-verify. |
| F-3 | A predicate-failure fail-closed path (Section 2.13) was required beyond what 148C.5's plan text anticipated (it described this case as "not exercisable... no override exists" at plan time), once an existing malformed-rule test exercised a rule object lacking `applies_to()` entirely. | Non-Blocking — implemented per PBPA-REQ-097, tested directly. |

No Blocking finding was identified. Implementation proceeded to
completion.

## 9. No-Go Confirmations

PBPA-001 v1.0 was implemented. No `POL-001..012` policy meaning was
changed. No new push permission policy was introduced. No `pcae push`
production consumption was implemented (`push.py` unchanged). No
approval was fabricated. `HUMAN_REVIEW` remains non-`ALLOW`.
Applicability remains distinct from policy decision. `NOT_APPLICABLE` is
not `ALLOW`. No caller-selectable policy exclusion was introduced.
Interactive Workflow Confirmation remains independent. Authority
Evaluation/AESIC remains disclosure-only. No Runtime Enforcement
behavior was changed. Finding B-1 remains formally OPEN pending
independent implementation verification and later PBPC re-evaluation.
No runtime capability was elevated. Runtime remains Observed, maximum
capability remains observe, and execution availability remains
unavailable.

## 10. Recommended Next Phase

**148C.7 — Permission Broker Foundation Policy Applicability
Independent Implementation Verification.** Must independently verify:
source against PBPA-001 (including this document's own characterization
of "preserved test intent," Section 3); all twelve policy metadata rows;
`POL-004` scope; class spoofing; action/class mismatch;
simulation-spoofing; direct Foundation invocation; missing/duplicate
policy; predicate failure; empty set; unknown/future class; determinism;
explainability; backward compatibility; P-1/P-2 disposition; no
policy-meaning drift; current `pcae push` behavior unchanged; B-1
remains formally open. Does not authorize 148D. Does not close B-1.
Does not begin PBPC production wiring.
