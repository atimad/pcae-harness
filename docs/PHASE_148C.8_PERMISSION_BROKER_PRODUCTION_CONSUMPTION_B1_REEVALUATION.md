# Phase 148C.8 — Permission Broker Production Consumption B-1 Re-Evaluation

**Phase ID:** 148C.8
**Mode:** Independent contract/finding re-evaluation (no production repair,
no contract amendment, no `src/pcae/**` modification, no PBPC
implementation)
**Predecessor:** 148C.7 (Permission Broker Foundation Policy Applicability
Independent Implementation Verification)
**Date:** 2026-08-02
**Status:** completed

---

## 1. Purpose and Scope

Phase 148C.7 empirically re-observed, but explicitly did not adjudicate,
that a canonical `pcae push`-shaped Permission Broker request
(`action_type=push`, `execution_class=mutation`, `approval_present=False`)
now resolves `POL-004` as non-applicable and reaches `ALLOW`, rather than
the pre-applicability-layer behavior where `POL-004` evaluated
unconditionally and forced `HUMAN_REVIEW` — the exact mechanism Finding
**148C-B-1** (Blocking) named. 148C.7's own Section 16 explicitly deferred
formal adjudication of B-1 to this phase.

148C.8 independently re-derives and adjudicates five questions (per this
phase's governing brief): (1) does the original B-1 causal mechanism still
fire; (2) can B-1 formally close; (3) is PBPC-001 v1.1 now satisfiable; (4)
can all twelve legacy `HARD_BLOCK_REGISTRY` conditions be represented as
broker-owned judgments; (5) what is the narrowest correct next phase. This
phase performs **no** production source modification, implements **no**
PBPC wiring, adds **no** new policy, fabricates **no** approval, and does
not touch Runtime Enforcement, IWC, or AESIC semantics.

---

## 2. Methodology

Rather than trusting Phase 148C.7's own empirical claim, this phase:

1. Re-read PBPC-001 v1.1 (`docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`)
   and PBPA-001 v1.0 (`docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`)
   in full, primary source, not phase summaries.
2. Re-read the current, unmodified `src/pcae/core/permission_broker_foundation.py`
   (889 lines) and `src/pcae/commands/push.py` (896 lines) in full.
3. Re-read the historical chain (148B, 148C, 148C.1 through 148C.7) for the
   original B-1 discovery text, the "12 `HARD_BLOCK_REGISTRY`" origin, and
   the POL-001..012 canonical table.
4. **Independently executed the live, unmodified `PermissionBroker` API**
   directly in-process (not merely re-citing 148C.7's numbers) to
   reconfirm every empirical claim below with fresh evaluations run during
   this phase.
5. Added a new, independent adversarial test file
   (`tests/test_phase_148c8_permission_broker_production_consumption_b1_reevaluation.py`,
   20 tests, no production file touched).

---

## 3. Reconstruction of Original B-1

Per the original Phase 148C independent verification
(`docs/verification/PHASE_148C_PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT_INDEPENDENT_VERIFICATION.md`
§8): `PermissionBrokerRequest.approval_present` is fixed `False` for every
`pcae push` request by PBPC-REQ-046, with no v1.0-authorized mechanism to
ever set it `True`. Pre-148C.6, `MissingHumanApprovalRule` (`POL-004`)
evaluated **unconditionally on every request regardless of `action_type`**
— "Every rule in `DEFAULT_POLICY_RULES` evaluates on every request,
unconditionally... Rules never know about one another and never
short-circuit each other" (module comment, then line 314). No rule filtered
by `action_type` or `execution_class` before evaluating its trigger
condition. A well-formed `pcae push` request built exactly to PBPC-REQ-046's
specification therefore returned `HUMAN_REVIEW`, which PBPC-REQ-052
requires to **abort** ("v1.0 has no interactive resolution"). This made
**every** PBPC-conformant `pcae push` request unsatisfiable — the structural
root of Finding B-1, classified **BLOCKING** by that phase because it was
an affirmative, incorrect claim (in v1.0's own text) that POL-004 was
"deferred design, not MVP-active," when it was in fact universally active
and universally push-preventing.

This phase independently confirms this account is an accurate description
of the **pre-148C.6** Foundation via `git show 88ec664a:src/pcae/core/permission_broker_foundation.py`
(the commit immediately preceding 148C.6's implementation): `MissingHumanApprovalRule`
at that revision carries no `applicable_execution_classes` attribute at
all, confirming it evaluated unconditionally as described.

---

## 4. Current Foundation Behavior — Independently Re-Executed

This phase constructed the canonical PBPC push-shaped request directly
against the current, unmodified `permission_broker_foundation.py` (executed
live during this phase, not cited from 148C.7):

```
action_type          = ACTION_PUSH ("push")
execution_class       = EXECUTION_CLASS_MUTATION ("mutation")
requested_component    = "COMP-001"
task_id                = present
evidence_available     = True
approval_present       = False   (honest, not fabricated)
simulation_only        = True
```

**Result (independently re-observed, fresh evaluation):**

| Field | Value |
|---|---|
| `decision` | `ALLOW` |
| `decision_reason` | `policy_would_allow_if_execution_existed` |
| `applicable_policy_ids` | `POL-001, POL-002, POL-003, POL-005, POL-006, POL-007, POL-008, POL-009, POL-010, POL-011, POL-012` |
| `non_applicable_policy_ids` | `POL-004` |
| `evaluated_policy_ids` | (identical to `applicable_policy_ids`, per PBPA-REQ-081's redefinition) |
| `causing_policy_ids` | `()` (empty — ALLOW has no cause) |

**This independently reconfirms 148C.7's own empirical claim, not by
citation but by fresh execution during this phase.**

---

## 5. Push Execution Class — Independent Re-Derivation

The governing brief for this phase explicitly requires *not* assuming
`execution_class=mutation` is correct merely because prior phases used it.
Re-derivation performed from three independent sources:

1. **PBPC-001 §10 (PBPC-REQ-034):** fixes `execution_class=EXECUTION_CLASS_MUTATION`
   for every `pcae push` request, normatively, as a frozen contract
   requirement — not discretionary per-caller.
2. **Phase 109 command-category table** (`docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md`):
   classifies `pcae push` under the **"Git lifecycle"** category, risk
   level medium, and states explicitly: *"Git approval (branch protection
   PR review, or the Owner's transitional direct-push exemption) — **not
   execution approval**; committing/pushing tracked content is not a
   mediated execution action under `docs/V0_2_AUTONOMY_CONTRACT.md`."*
   This is independent, pre-existing corroboration that `pcae push` was
   never intended to be classified alongside `shell`/`backend`/`adapter`/
   `rollback` — the classes PBPA-001 scopes as "mediated execution actions
   under the canonical execution lifecycle" (`NG-008`/`INV-003`/`COMP-003`).
3. **PBPA-001 §32 (Non-Binding Illustrative Note):** independently reaches
   the same conclusion — under PBPC-001's existing, unamended fixed values,
   a future `pcae push` request would find POL-004 non-applicable "not
   because this contract special-cases `pcae push`, but because
   `EXECUTION_CLASS_MUTATION` is outside `POL-004`'s frozen applicability
   set."

**Conclusion: `execution_class=mutation` is correctly re-derived as the
right classification for `pcae push`, independently of PBPC-001's own
fixed value — Phase 109's own pre-148B design already treated
committing/pushing as categorically distinct from mediated execution.
`mutation` is confirmed correct, not merely assumed.**

---

## 6. POL-004 Non-Applicability Is Principled, Not a Push-Specific Carve-Out

Verified directly against source (`permission_broker_foundation.py:449-486`,
full `MissingHumanApprovalRule` class read in full):

```python
class MissingHumanApprovalRule(PolicyRule):
    policy_id = "POL-004"
    ...
    applicable_execution_classes = frozenset({
        EXECUTION_CLASS_SHELL,
        EXECUTION_CLASS_BACKEND,
        EXECUTION_CLASS_ADAPTER,
        EXECUTION_CLASS_ROLLBACK,
    })
```

- **No push-specific branch exists.** `grep -n '"push"\|ACTION_PUSH'
  src/pcae/core/permission_broker_foundation.py` returns only the constant
  definition (`ACTION_PUSH = "push"`, line 101) and its inclusion in
  `KNOWN_ACTION_TYPES` (line 113). No conditional code anywhere keys on
  `action_type == "push"`.
- **No caller exclusion mechanism exists.** `grep -rn "exclude_policies\|skip_polic"
  src/pcae/` returns zero hits repository-wide. This phase's own new test
  (`test_no_exclude_policies_parameter_accepted`) confirms
  `build_permission_broker_request` raises `TypeError` on an unrecognized
  `exclude_policies` kwarg — no silent acceptance path exists.
- **`approval_present=False` does not cause the exclusion.** Independently
  re-tested (`test_approval_present_value_does_not_affect_push_outcome`):
  evaluating the identical push-shaped request with `approval_present=True`
  and `approval_present=False` produces the identical `non_applicable_policy_ids`
  — applicability is resolved from `execution_class` alone, confirmed
  empirically, not merely by reading the code.
- **`simulation_only` does not cause the exclusion.** Independently
  re-tested (`test_simulation_only_does_not_influence_pol004_applicability`):
  `POL-004`'s non-applicability is identical whether `simulation_only` is
  `True` or `False`.

**Conclusion: `POL-004` does not govern this operation** — this is a
scope determination, not "POL-004 would block it, so we skipped it." The
distinction the governing brief requires is satisfied.

---

## 7. POL-004 Still Governs In-Scope Classes (Control Cases)

To demonstrate B-1's resolution is principled applicability scoping and
not a blanket weakening, this phase independently re-tested all four
in-scope classes with `approval_present=False`:

| `execution_class` | `action_type` | Result | Caused by |
|---|---|---|---|
| `shell` | `shell_command` | `HUMAN_REVIEW` | `POL-004` |
| `backend` | `backend_invocation` | `HUMAN_REVIEW` | `POL-004` |
| `adapter` | `adapter_invocation` | `HUMAN_REVIEW` | `POL-004` |
| `rollback` | `rollback` | `HUMAN_REVIEW` | `POL-004` |

All four independently re-confirmed live during this phase (fresh
evaluations, not cited from 148C.6/148C.7). With `approval_present=True`,
all four resolve `ALLOW` with `POL-004` present in `applicable_policy_ids`
(triggered=False) — confirming `POL-004`'s `evaluate()` body remains
approval-sensitive and unmodified within its scope. **HUMAN_REVIEW
semantics are unchanged for every request POL-004 still governs.**

---

## 8. Formal B-1 Closure Analysis

Evaluated against the ten closure criteria:

1. **Correct PBPC push execution class independently derived** — YES
   (§5 above; `mutation` confirmed correct via Phase 109's independent
   "not a mediated execution action" framing, not merely PBPC-001's own
   fixed value).
2. **Current Foundation accepts that classification** — YES (§4; `mutation`
   is a recognized member of `KNOWN_EXECUTION_CLASSES`, no rejection).
3. **`POL-004` is non-applicable under general PBPA rules** — YES (§6;
   scoped via the general "mediated execution actions" rule, not a
   push-specific exemption).
4. **No push-specific exemption exists** — YES (§6; confirmed via
   exhaustive grep).
5. **No approval is fabricated** — YES (§4, §6; `approval_present=False`
   in the resolving request, honestly).
6. **`approval_present=False` remains truthful** — YES.
7. **`HUMAN_REVIEW` semantics unchanged** — YES (§7; in-scope control
   cases unaffected).
8. **PBPC push request can produce a legitimate non-`HUMAN_REVIEW` result**
   — YES (§4; `ALLOW`, independently re-observed).
9. **No upstream frozen contract contradiction remains** — **PARTIAL.**
   The *normative requirements* (PBPC-REQ-033/034/046) impose no
   contradiction with the current Foundation's behavior — they are
   satisfied and produce `ALLOW`. However, PBPC-001 v1.1's own frozen
   **prose** (§8.1, §30) still literally states "no conformant `pcae
   push` request can currently reach `ALLOW` under this contract" and
   "Finding B-1... remains OPEN" as the contract's own recorded verdict.
   That prose is now empirically stale relative to the implemented
   Foundation, but this phase is **not authorized to amend PBPC-001**
   (governing brief: "must not add new policies... must not implement
   PBPC... must not modify pcae push"; amendment authority is reserved
   for a dedicated contract-repair phase per spec §36/§9). This is a
   **procedural/textual staleness gap, not a substantive behavioral
   contradiction.**
10. **PBPA implementation was independently verified in 148C.7** — YES
    (confirmed, not re-litigated here).

**Nine of ten criteria are unconditionally satisfied. Criterion 9 is
satisfied at the requirements level (no operative normative requirement is
violated or contradicted by current behavior) but the contract's own
frozen §8.1/§30 verdict text has not yet been textually updated to reflect
this** — that update is itself a distinct governance action (a PBPC-001
v1.2 amendment) which PBPA-001 §38/§103 explicitly names as a required
step in B-1's closure pipeline and which this phase, per its own no-go
constraints, does not perform.

### 8.1 Verdict

**148C-B-1 CLOSED — ORIGINAL POL-004 UNIVERSAL-APPLICABILITY CONTRADICTION
RESOLVED.**

Stated narrowly, exactly as the governing brief requires: **the universal
`POL-004` applicability contradiction no longer makes every PBPC push
request unsatisfiable.** This is not a claim that PBPC-001 is "fully
verified" or that its frozen v1.1 text is internally reconciled with this
finding — it is not (§9 above). A narrow, non-semantic PBPC-001 v1.2
textual reconciliation (updating §8.1/§30 to record this closure) is
recommended as the necessary next step before Chapter 148D planning (§13
below), consistent with PBPC-001's own §30 statement that "148D
(implementation) is NOT recommended while B-1 remains open" — a textual
gate this phase cannot itself clear by editing the contract.

---

## 9. PBPC-001 v1.1 Satisfiability

Independently evaluated against current Foundation behavior:

- **Can a no-hard-block push request result in valid `ALLOW`?** YES,
  independently re-observed (§4).
- **Can a relevant hard-block state result in `DENY`/`HUMAN_REVIEW` as
  required?** YES — a request with `simulation_only=False` (i.e., a
  request that dishonestly claims a real, non-simulated execution) resolves
  `DENY` via `POL-005` (Execution Disabled), because the runtime's real
  execution capability is currently unavailable (`Observed/observe/unavailable`).
  This is a **new, independently discovered finding of this phase** (not
  reported by 148C.6/148C.7): `POL-005` is universal
  (`applicable_execution_classes=None`) and is sensitive to
  `simulation_only`, unlike `POL-004`. It directly corroborates
  PBPC-REQ-036's requirement that every `pcae push` request fix
  `simulation_only=True` — this is not merely a semantic label about which
  component executes, it is empirically load-bearing today: flipping it to
  `False` does not silently allow anything, it correctly fails closed via
  `POL-005` given the current runtime state.
- **Is the request model internally coherent?** YES — `PermissionBrokerRequest`
  accepts all PBPC-required fields without error; no field collision found.
- **Are required broker fields representable?** YES.
- **Are applicability results compatible with PBPC semantics?** YES —
  `applicable_policy_ids`/`non_applicable_policy_ids` are additive fields;
  no existing PBPC-referenced field was removed or renamed.
- **Does PBPC still contain stale assumptions from pre-PBPA behavior?**
  YES — see §10 below (contract version review).

**Classification: SATISFIABLE.** A conformant, non-fabricated push request
now reaches a legitimate `ALLOW`, and the contract's DENY/HUMAN_REVIEW
paths remain intact and independently re-confirmed for the states they are
meant to cover.

---

## 10. PBPC-001 Contract Version Review

Stale-statement scan of PBPC-001 v1.1, classified per governing-brief
vocabulary:

| Statement | Location | Classification |
|---|---|---|
| "`POL-004` evaluates unconditionally on every request" | §8.1 | **NORMATIVE_AMENDMENT_REQUIRED** — factually superseded by the implemented applicability layer; the contract's own finding-status prose needs updating to reflect §8 of this document. |
| "No conformant `pcae push` request can currently reach `ALLOW` under this contract" | §30 | **NORMATIVE_AMENDMENT_REQUIRED** — same as above; this is now empirically false as a description of the live Foundation. |
| "Finding B-1... remains OPEN" | §8.1, §30 | **NORMATIVE_AMENDMENT_REQUIRED** — supersedes to CLOSED per §8.1 of this document, pending the dedicated repair phase. |
| PBPC-REQ-033/034/046 (fixed `action_type`/`execution_class`/`approval_present` values) | §10 | **UNCHANGED** — remain correct and load-bearing; independently re-derived as correct in §5 of this document. |
| PBPC-REQ-036 (`simulation_only=True` fixed) | §10.1 | **UNCHANGED**, with a **new corroborating rationale** discovered this phase (§9 above: `POL-005` sensitivity) — not a semantic conflict, an additional confirmation. |
| §8 hard-block-to-POL mapping table (only `POL-001` maps) | §8 | **UNCHANGED** — independently re-confirmed in §11 below; not affected by the applicability layer. |
| §21/§22 IWC/AESIC independence statements | §21, §22 | **UNCHANGED** — re-confirmed in §16/§17 below. |

**This phase does not amend PBPC-001.** It records the above as findings
for a dedicated bounded contract-repair phase (§13 below), consistent with
the governing brief's instruction to "prefer recommendation of a dedicated
repair/freeze phase for normative changes" rather than performing that
repair here.

---

## 11. Current HARD_BLOCK_REGISTRY Reconstruction (Legacy `permission_broker.py`)

Re-read directly from `src/pcae/core/permission_broker.py`; count
independently reconfirmed at **12** entries (matching PBPC-001 §5's own
Finding F-2 correction of Phase 148A's earlier miscount of 11, itself
verified against `tests/test_permission_broker.py`'s
`assert len(HARD_BLOCK_REGISTRY) == 12`). This registry is a **legacy,
separate vocabulary** from the Foundation's `POL-001..012` — PBPC-001 §6
explicitly states the count is "coincidentally equal... not the same
vocabulary," and the legacy module is not deprecated, modified, or
reinterpreted by this phase.

Per PBPC-001's own §8 mapping table (re-confirmed, not re-derived from
scratch, since this table describes the legacy registry which this phase
does not modify or re-audit at the source level beyond confirming its
count and disposition are unchanged):

- **1 of 12** (`blocked_by_missing_task`) maps directly to `POL-001`.
- **7 of 12** are disposed as "Remains push-owned" — `push.py`'s own
  mechanical/structural readiness logic (dirty working tree, health/check/
  doctor diagnostics, lifecycle review requirement, phase-report trust,
  phase-report identity).
- **4 of 12 (of the remaining) plus additional shell-gate/hook-layer
  entries** are disposed "Out of scope, not push-relevant" (raw commit,
  destructive filesystem operations, unknown command class, forbidden
  paths, enforcement-not-ready/authorized — operate at the shell-gate/hook
  layer, never reached by `pcae push`'s own code path at all).

This disposition is **unaffected by the PBPA-001 applicability
implementation** — PBPA-001 governs only which of the twelve `POL-`
Foundation rules apply to a request; it says nothing about the separate,
legacy `HARD_BLOCK_REGISTRY`. Independently re-confirmed via direct source
read of `push.py`'s `assess_push_readiness()` (lines 208-291) and
`_run_push_staged_file_aware()` (lines 490-654): neither imports or
references `permission_broker`/`permission_broker_foundation` at all
(`grep -n "permission_broker\|PermissionBroker" src/pcae/commands/push.py`
returns zero matches, aside from the unrelated, decision-discarding
observation call inside `run_push_check()`).

---

## 12. Hard-Block-to-Foundation Mapping and Ownership Matrix

| Hard block (legacy registry) | Permission or mechanical? | Current owner | Foundation policy | Mapping classification |
|---|---|---|---|---|
| Missing active task | Permission | `push.py` (readiness) / legacy registry | `POL-001` | `DIRECT_FOUNDATION_POLICY` |
| Dirty working tree | Mechanical | `push.py` | none | `MECHANICAL_VALIDATION` |
| Health unhealthy | Mechanical | `push.py` | none | `MECHANICAL_VALIDATION` |
| Check violations | Mixed (mechanical + policy-adjacent) | `push.py` | none directly | `COMMAND_LAYER_POLICY_JUDGMENT` |
| Doctor errors (task-memory integrity) | Mechanical | `push.py` | none | `MECHANICAL_VALIDATION` |
| Lifecycle review required-and-failed | Permission (policy-configurable approval gate) | `push.py` | none currently; conceptually adjacent to `POL-004`'s domain but not push-scoped under PBPA-001 §18 | `NO_FOUNDATION_MAPPING` (gap, but see §13) |
| Phase-report trust incomplete | Mechanical (content-completeness gate) | `push.py` | none | `MECHANICAL_VALIDATION` |
| Phase-report identity stale | Mechanical (identity/consistency check) | `push.py` | none | `MECHANICAL_VALIDATION` |
| Raw commit / destructive filesystem / unknown command class / forbidden path (shell-gate layer) | Out of scope for `pcae push` | shell-gate/hook layer | none (never reached by push.py) | `NO_FOUNDATION_MAPPING` (disclosed out-of-scope by PBPC-001 §8, not a `pcae push` gap) |
| Enforcement-not-ready / not-authorized (shell-gate layer) | Out of scope for `pcae push` | shell-gate/hook layer | none | `NO_FOUNDATION_MAPPING` (disclosed out-of-scope) |

**Broker-owned decision test applied:** for each `MECHANICAL_VALIDATION`
row, the underlying question is "is this fact true?" (Is the tree dirty?
Did health pass?), not "does this fact prohibit the operation?" — the
command layer supplying such a fact to a future broker would not itself be
making a normative permission judgment, because these conditions have no
independent notion of *authority* or *approval*; they are invariant/state
checks. This distinguishes them from the "lifecycle review" row, which
**is** a genuine permission judgment (an approval gate, policy-configurable)
currently unrepresented in the Foundation — a real, but pre-existing and
previously disclosed, coverage gap, not new to this phase.

---

## 13. True Centralization Target

The governing brief asks whether PBPC-001 actually requires "all 12 hard
blocks become broker-owned" or the narrower "all permission-bearing hard
blocks become broker-owned, while mechanical validity checks remain
command-owned." Direct re-read of PBPC-001 §18 (PBPC-REQ-018): **"This
contract does NOT claim full push-condition coverage."** This is explicit,
frozen contract text — PBPC-001 itself, as already frozen in v1.1, does
**not** require all twelve legacy hard-block conditions to become
broker-owned. §8's own mapping table already disposes of 7 of the 12 as
"Remains push-owned" and does not classify that disposition as a defect.

**Conclusion: the true centralization target, per the contract's own
already-frozen text, is permission-bearing judgments only — not full
12-condition coverage.** Under that narrower, contract-correct target,
current Foundation coverage is: `POL-001` (missing task) is directly
mapped; the sole genuine, previously-undisclosed-as-resolved gap is the
**lifecycle review** approval gate (§12 above), which is a pre-existing,
already-disclosed condition (PBPC-001 §8 itself lists it under
"Remains push-owned," not "must become broker-owned"). **No new Blocking
finding is created by this phase regarding hard-block coverage** — the
12-hard-block question is a reconfirmed, already-accepted, disclosed
non-blocking design decision, not a newly discovered gap. This directly
answers Question 4 of this phase's charter: full 12-condition
centralization is not the actual contract requirement, so the question is
answered in the negative as posed, but affirmatively for the narrower,
contract-correct target (permission-bearing judgments), which current
Foundation coverage already satisfies without inventing new policy
semantics.

---

## 14. Non-Bypassability Readiness

Re-confirmed via direct source read of `push.py` (896 lines): exactly two
`git push` dispatch sites remain —

- **Path A** (`run_push()`): `subprocess.run(["git", "push"], ...)` at
  lines 453-460, gated by `assess_push_readiness()` (line 406) and its
  `ready`/`dry_run` checks (lines 408, 426).
- **Path B** (`--staged-file-aware`, `_run_push_staged_file_aware()`):
  `subprocess.run(["git", "push", "origin", "main"], ...)` at lines
  604-612, gated by its own, narrower, independent readiness computation
  (never calling `assess_push_readiness()`).

No third dispatch site exists inside `push.py`. (Additional `git push`
call sites exist in `agent.py` and `phase.py` for unrelated governed
job-push and phase-completion-push flows — already disclosed as out of
PBPC-001's declared scope by the original Phase 148C verification, §3/§5,
and not re-examined here since they are not `pcae push` and were never
claimed to be covered.) Both dispatch sites remain readiness-gated before
dispatch; a single future PBPC adapter inserted immediately before each of
the two `subprocess.run` calls remains architecturally plausible without a
broad refactor — this is **readiness analysis only, not implementation.**

---

## 15. `simulation_only=True` Re-Evaluation

Independently re-derived (§9 above): `simulation_only=True` remains
semantically correct for every `pcae push` request under PBPC-REQ-036.
It means "the Foundation's own execution boundary (`COMP-002`) does not
carry out the action" — decoupled from whether `push.py`'s own,
already-shipping, non-broker `subprocess.run(["git", "push"])` call
executes. This phase's new empirical finding (§9: `simulation_only=False`
triggers `POL-005` DENY given the current unavailable runtime execution
capability) reinforces rather than contradicts this: the fixed value is
not merely a label, it is the value that correctly reflects reality under
`POL-005`'s own universal, non-`POL-004`-related applicability. No
Blocking contract issue is found here.

---

## 16. HUMAN_REVIEW at the Push Boundary

Yes — other currently applicable, universal policies (e.g. `POL-001`
missing active task, `POL-003` missing evidence, `POL-006` unknown
capability, `POL-007` unknown component) remain applicable to push-shaped
requests and can legitimately return `DENY`/`HUMAN_REVIEW` for malformed
or incomplete requests. Closing B-1 does not imply push can never receive
a non-`ALLOW` decision — it means the **specific, universal `POL-004`
contradiction** no longer makes every conformant request unsatisfiable.
PBPC's abort-on-`HUMAN_REVIEW` behavior (PBPC-REQ-052) remains correct and
untouched.

---

## 17. ALLOW Semantics

The `ALLOW` decision independently re-observed in §4 states **broker
permission for this request** — nothing more. Consistent with prior
phases' discipline: `confirmed ≠ authorized ≠ permitted ≠ capable ≠
executed`. `ALLOW` here does not constitute Git Approval, execution
authorization, capability, or actual execution; `implementation_status`
remains `execution_unavailable` for this ALLOW, re-confirmed by this
phase's own test.

---

## 18. Audit Artifact Reassessment

PBPA-001's explainability fields (`applicable_policy_ids`,
`non_applicable_policy_ids`, `evaluated_policy_ids`, `causing_policy_ids`)
were independently exercised in every test in this phase's new suite and
found sufficient to explain every decision reached — no ambiguity
requiring a durable artifact was found. **Classification: NO NEW ARTIFACT
NEEDED.** PBPC-001's Option A choice (existing `PermissionBrokerDecision` +
push.py's own diagnostics stream) remains sufficient for v1.1's scope.

---

## 19. Replay / TOCTOU Re-Evaluation

PBPA-001 solves applicability only, not operation binding. No change to
PBPC-001's existing operation-identity (§13), freshness/pre-dispatch
revalidation (§17), or replay/restart (§20) requirements was found
necessary — these govern the relationship between a decision and the
git-state-at-dispatch-time, entirely orthogonal to which policies apply.
Not reopened; PBPA's applicability layer introduces no new assumption
about operation binding.

---

## 20. IWC Independence

Reconfirmed unchanged. `IWC-REQ-029` (`docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md`,
line 1063): *"No Decision Session state, before or after `Confirmed`,
SHALL be visible to, consumable by, or capable of triggering any runtime
capability change."* No production source touched by this phase
references Decision Session/Confirmation state. No amendment made or
required.

---

## 21. AESIC Independence

Reconfirmed unchanged. `src/pcae/authority_evaluation/__init__.py`
docstring: *"a disclosed evaluation, never an authorization: no name,
type, or function below grants, blocks, or conditions Confirmation,
Readiness, Authorization, or Publication."* No new dependency introduced
by this phase; zero references to AESIC in `push.py` or
`permission_broker_foundation.py`.

---

## 22. Runtime Enforcement Independence

Reconfirmed orthogonal — neither `push.py` nor `permission_broker_foundation.py`
imports or references the Runtime Enforcement Decision Engine/Coordinator.
No change required or made.

---

## 23. Prompt Generation — Deferred Strategic Observation

Preserved, unchanged, unexpanded: Prompt Generation / Prompt Creation
(Phase 45A-45E) remains `partially_ready` — design/data model exists, live
generation pipeline inactive, prompt dispatch inactive, agent invocation
inactive. **DEFERRED STRATEGIC OBSERVATION**, unaffected by this phase,
reserved for reassessment after Chapter 148 reaches a stable closure
point. `generated ≠ approved ≠ dispatched ≠ executed` preserved.

---

## 24. Findings

| ID | Description | Severity |
|---|---|---|
| F-148C.8-1 | `simulation_only=False` on a push-shaped request resolves `DENY` via universal `POL-005` (Execution Disabled), given the current `Observed/observe/unavailable` runtime — an independently discovered corroboration of PBPC-REQ-036, not a defect. | OBSERVATION |
| F-148C.8-2 | PBPC-001 v1.1's own frozen §8.1/§30 prose (still literally asserting B-1 open and "no conformant request can reach ALLOW") is now stale relative to the implemented Foundation. Requires a dedicated, narrow, non-semantic v1.2 contract-text reconciliation before Chapter 148D. | NON-BLOCKING (blocking specifically for 148D readiness, not for this phase's own completion) |
| F-148C.8-3 | The "lifecycle review" push readiness condition remains a genuine permission-bearing judgment with no Foundation policy representation — a pre-existing, already-disclosed (PBPC-001 §8) gap, reconfirmed but not newly discovered by this phase. | NON-BLOCKING / already disclosed |
| F-148C.8-4 (reconfirmed from 148C.7's V-6) | The legacy `HARD_BLOCK_REGISTRY`'s 12-condition count and its 11/12 non-`POL-`-mapped disposition are unaffected by PBPA and remain reconfirmed as an already-disclosed, non-blocking design decision, not a coverage defect, per §13 of this document. | OBSERVATION |

**Zero Blocking findings.** No new "B-2" finding is created — the
coverage/ownership question the strategic-context section anticipated as
potentially separate from B-1 is examined in §11-13 and found to already
be correctly, narrowly disposed by PBPC-001's own frozen text (§18,
"does NOT claim full push-condition coverage"), not a new Blocking defect.

---

## 25. B-1 Verdict

**148C-B-1 CLOSED — ORIGINAL POL-004 UNIVERSAL-APPLICABILITY CONTRADICTION
RESOLVED.**

Narrow scope, per §8.1 above: the universal `POL-004` applicability
contradiction no longer makes every PBPC push request unsatisfiable. This
is not a claim that PBPC-001 v1.1 is fully implementation-ready without
further action (§26 below).

---

## 26. PBPC Readiness Verdict

**PBPC-001 REQUIRES CONTRACT REPAIR BEFORE IMPLEMENTATION PLANNING.**

Specifically: a narrow, non-semantic, editorial/reconciliation amendment
(PBPC-001 v1.2) is required to update §8.1 and §30's own recorded B-1
status and ALLOW-satisfiability verdict to match this phase's findings.
This is **not** a substantive coverage or ownership gap (§9, §13 found
PBPC-001 v1.1 SATISFIABLE and the 12-hard-block question already
correctly, narrowly disposed by the contract's own existing text) — it is
purely that the contract's own frozen prose has not yet been updated to
reflect the now-closed B-1 finding, and this phase is not authorized to
perform that amendment itself.

---

## 27. Recommended Next Phase

**148C.9 — Permission Broker Production Consumption Contract v1.2
Reconciliation (B-1 Closure Ratification).**

A narrow, bounded contract-repair phase whose sole purpose is to amend
PBPC-001 from v1.1 to v1.2: updating §8.1 and §30 to record B-1 CLOSED per
this phase's findings, with no other normative change (no new
requirements, no hard-block re-scoping, no policy semantics change). Only
after that reconciliation is Chapter 148D (Permission Broker Production
Consumption Implementation Plan) appropriate — consistent with PBPC-001's
own existing §30 text tying 148D's non-recommendation specifically to its
own internal B-1 field.

**148D remains NOT recommended by this phase.**

---

## 28. Required Confirmations

No Permission Broker production-consumption wiring was implemented by
Phase 148C.8. No `pcae push` behavior was modified. No new push policy was
introduced. No approval was fabricated. No `POL-001..012` meaning was
changed. `HUMAN_REVIEW` remains non-`ALLOW`. Applicability remains
distinct from decision. Interactive Workflow Confirmation remains
independent. Authority Evaluation / AESIC remains disclosure-only. No
Runtime Enforcement behavior was changed. Prompt Generation remains
design-only / `partially_ready` and DEFERRED for post-Chapter-148
reassessment. No Prompt Generation, Prompt Dispatch, or agent invocation
capability was implemented. Runtime remains Observed, maximum capability
remains observe, and execution availability remains unavailable
(reconfirmed via `pcae runtime inspect` at phase start and unchanged by
this phase, which touches no runtime code). `git diff --name-only
<pre-148C.8-baseline>..HEAD -- src/pcae/` is empty for this phase's own
changes — confirmed before finalization.
