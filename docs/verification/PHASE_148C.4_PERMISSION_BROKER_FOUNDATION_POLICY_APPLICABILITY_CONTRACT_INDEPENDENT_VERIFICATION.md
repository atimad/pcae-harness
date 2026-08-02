# Phase 148C.4 — Permission Broker Foundation Policy Applicability Contract Independent Verification

**Phase ID:** 148C.4
**Mode:** Independent Verification (verification only — no implementation, no
contract amendment, no schema change, no runtime change, no `src/pcae/**`
modification)
**Baseline:** PBPA-001 v1.0 (`docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`)
**Predecessor:** Phase 148C.3 (commit `234fce06`)
**Date:** 2026-08-02

---

## 0. Authorization and Boundary

This phase is authorized to independently re-derive and adversarially attack
PBPA-001 v1.0 — not to trust Phase 148C.3's own text, Phase 148C.2's design
prose, or PBPA-001's own claims as an oracle for its own correctness. It must
not implement the applicability layer, modify
`src/pcae/core/permission_broker_foundation.py` or any other `src/pcae/**`
file, change `pcae push` behavior, close Finding B-1, add `POL-013+`,
introduce execution, or begin 148D planning.

### Bootstrap

```
git status --short / --branch --short   -> clean, main, tracking origin/main
git log --oneline -25                    -> HEAD at 31856851 (148C.3 idle placeholder)
git rev-list --count origin/main..HEAD   -> 0
pcae health                              -> healthy
pcae check                                -> passed
pcae status coherence                     -> coherent
pcae doctor task-memory                   -> clean
pcae push check                           -> clean, nothing_to_push
pcae runtime inspect                      -> Observed / observe / unavailable, 0 plugins
pcae notify status                        -> Telegram configured, enabled, ready
pcae phase-report show --latest           -> 148C.3, status completed, complete,
                                              PBPA-001 v1.0 present, next: 148C.4
pcae phase-report reconcile --phase-id 148C.3
    -> status: delivery_recorded_bookkeeping_incomplete; receipt: absent;
       mutation: none (inspection only) -- Observation, non-Blocking, consistent
       with every prior phase's reconciliation status in this chapter
```

Confirmed: repository clean, 0 unpushed commits, 148C.3 complete, PBPA-001
v1.0 present, Finding B-1 open, runtime unchanged (`Observed` / `observe` /
`unavailable`).

### Independent source inventory (read in full unless noted)

- `docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md` (1240
  lines, PBPA-001 v1.0 — the object under verification, read in full)
- `src/pcae/core/permission_broker_foundation.py` (788 lines, read in full —
  request model, decision model, `PolicyRule`/`PolicyResult`,
  `PolicyRegistry.evaluate_all`, `_compose`, `PermissionBroker.evaluate`,
  `DEFAULT_POLICY_RULES`)
- `docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`
  (PBPC-001 v1.1 — §8, §8.1, §9, §26, §30, and the compatibility table, read
  targeted against every PBPA-001 citation of it)
- `docs/PHASE_148C.1_PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT_CLARIFICATION_AND_REPAIR.md`
  (Category A/B/C/D classification, read in full — the origin of B-1's
  diagnosis PBPA-001 builds on)
- `docs/verification/PHASE_148C_PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT_INDEPENDENT_VERIFICATION.md`
  (B-1's original independent discovery, read in full for continuity of
  diagnosis)
- `docs/V0_2_AUTONOMY_CONTRACT.md` (`INV-001..010` verbatim, read targeted —
  especially `INV-003`'s exact text, checked word-for-word against PBPA-001's
  paraphrase)
- `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` (`NG-008` exact condition and
  rationale text, and the document's own execution-readiness-decision-point
  scope statement at lines 27-32, read targeted)
- `docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md` (full — the
  command-category table's disposition of every action category, especially
  Documentation/Source mutation and Git lifecycle rows)
- `docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md` §5 (Git
  Approval / Execution Approval separation, read in full)
- `docs/PHASE_108_PERMISSION_BROKER_POLICY_COMPOSITION_HARDENING.md` (`DENY >
  HUMAN_REVIEW > ALLOW` precedence origin, read targeted)
- `tests/test_permission_broker_foundation.py`,
  `tests/test_permission_broker_policy_composition_hardening.py`,
  `tests/test_permission_broker_policy_rule_framework.py` (171 tests, run
  live, all passing)
- Live execution against the actual, unmodified `PermissionBroker` /
  `PolicyRegistry` / `build_permission_broker_request` (not a
  re-implementation) to empirically observe today's pre-applicability
  baseline for four representative request shapes (§17 below)

---

## 1. Executive Summary

**Verdict: VERIFIED WITH NON-BLOCKING FINDINGS — POLICY APPLICABILITY
IMPLEMENTATION PLANNING MAY PROCEED.**

Independent, adversarial re-derivation of PBPA-001 v1.0 from primary source —
not from 148C.2's or 148C.3's own prose — reproduces the contract's central
architectural claims without finding a Blocking defect. The
applicability/evaluation separation is genuine and non-invertible as
specified; the hybrid metadata+predicate architecture concentrates
applicability authority in the Foundation, not the caller; the `POL-004`
scope this phase was specifically instructed to attack (§43's own
instruction, restated here as §13) is independently re-derivable from three
converging primary sources, not merely asserted; fail-closed behavior is
specified correctly for every attack surface this phase attempted (unknown
class, missing class, predicate failure, missing policy, duplicate policy,
empty applicable set); and no caller-selectable weakening mechanism exists
in the contract text.

One finding required deep, genuinely adversarial re-derivation before this
phase could accept it (§13.3): `INV-003`'s verbatim text — "Human approval is
mandatory before **mutating** execution" — appears, on a first, literal
reading, to contradict PBPA-001's exclusion of `EXECUTION_CLASS_MUTATION`
from `POL-004`'s applicability set. This phase traced the term "mutating"
through three independent primary sources (`INV-003` itself, the Phase 109
command-category table, and the PR-compatible workflow's Git
Approval/Execution Approval separation) and confirms the two uses of
"mutation" are **not the same concept**: `INV-003`'s "mutating execution"
means execution, through the mediated pipeline, that mutates state *outside
version control*; `EXECUTION_CLASS_MUTATION` means a version-controlled
content change (source/docs/test edit, commit, push) that Git Approval
already governs. This is a genuine terminological collision this repository
should be alert to in future amendments (recorded as Non-Blocking Finding
V-1, §21), but PBPA-001's own exclusion is independently supported, not an
invented narrowing to manufacture B-1's closure.

Two further Non-Blocking findings and one Observation are recorded (§21).
None rises to Blocking. **Finding B-1 remains OPEN.** No production source
was modified; no Permission Broker Foundation behavior changed; runtime
remains `Observed` / `observe` / `unavailable`.

---

## 2. Contract Identity — Independent Verification

| Claim | Independent check | Result |
|---|---|---|
| PBPA-001 exists at the stated path | `docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md` read in full | **Confirmed present.** |
| Version is v1.0 | Header line 6; Version History §50 shows exactly one entry | **Confirmed.** |
| Status is FROZEN, does not close B-1 | Header lines 7-9 | **Confirmed**, and independently reconfirmed against PBPC-001 §8.1 (B-1 still OPEN there too, §3 below). |
| Requirement count is 114 | Extracted every `PBPA-REQ-###` token via independent script, deduplicated, sorted | **Confirmed exactly 114** — `PBPA-REQ-001` through `PBPA-REQ-114`, zero gaps, zero duplicates (`sorted(set(1..114) - found) == []`, `sorted(found - set(1..114)) == []`). |
| No duplicate applicability contract exists | `grep -rl "applicable_execution_classes\|policy applicability" docs/contracts/` | **Confirmed** — exactly one file (`PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`) references applicability metadata or claims applicability authority. No competing contract. |
| No competing authority | Same search, plus a scan of every `docs/contracts/*.md` filename for a second "PBPA" or "applicability" contract | **Confirmed** — none found. |

**Verdict: Contract identity independently verified. No discrepancy.**

---

## 3. Applicability/Evaluation Separation — Re-Derivation

PBPA-REQ-009/010/011/012 freeze applicability ("does policy P govern request
R?") and evaluation ("what does P decide, given it governs R?") as
categorically distinct, and prohibit the inversion `approval missing ->
POL-004 not applicable`.

This phase independently re-read `MissingHumanApprovalRule.evaluate()`
(`permission_broker_foundation.py:427-443`): its condition is
`if request.approval_present:` — nothing else. It reads no
`execution_class`. The applicability question PBPA-001 introduces is a
**registry-level filter that would run before this method is ever called**,
not a change to the method's own logic. Today (pre-implementation) the
registry calls every rule's `evaluate()` unconditionally
(`PolicyRegistry.evaluate_all`, `:647-659`); no applicability check exists at
all, which is precisely the gap PBPA-001 exists to close and precisely why
`approval_present=False` currently always triggers `POL-004` regardless of
operation class (empirically confirmed, §17).

Independently constructing the inverted (prohibited) form — "if
`approval_present` is false, treat `POL-004` as inapplicable" — would make
the rule that exists to require approval permanently silence itself for any
caller who simply never supplies approval, which is self-defeating by
construction. No primary source anywhere in this repository's Permission
Broker corpus authorizes that inversion. PBPA-REQ-010's prohibition is
independently justified, not merely stated.

**Verdict: Confirmed. The separation is genuine, non-invertible, and
correctly ordered (applicability before evidence-reading).**

---

## 4. Applicability Result Model — Re-Derivation

PBPA-REQ-013 declines to add a fourth `PermissionBrokerDecision.decision`
value. Independently re-read `DECISION_VALUES`
(`permission_broker_foundation.py:50`): exactly `(ALLOW, DENY,
HUMAN_REVIEW)`. Independently re-read PBPC-001 §10 (PBPC-REQ-032): a
second decision taxonomy is already prohibited there. Adding a
`NOT_APPLICABLE` broker-level value would indeed violate that existing
prohibition — PBPA-001's choice to represent applicability one layer below
(per-`PolicyResult`) rather than at the broker-decision layer is the only
option consistent with both PBPC-REQ-032 and the observed enum.

Independently checked: PBPA-REQ-016's requirement that `NOT_APPLICABLE`
never collapse into `ALLOW`. Tracing the specified mechanism
(PBPA-REQ-015): a non-applicable rule's `evaluate()` is never called, so it
never produces a `PolicyResult` at all — there is no `triggered=False`
result to accidentally read as "policy ran and found nothing wrong" (which
is what today's actual `ALLOW` path means, `_compose`'s "nothing triggered"
branch). A non-applicable policy is *absent from the evaluated set*, not
present-and-silent. This distinction is real and independently verified
against the `_compose` code: `_compose` only ever sees results for policies
that were actually run (`evaluate_all`'s output tuple); a policy filtered
out before `evaluate_all` calls it contributes nothing to that tuple,
structurally, with no additional guard code required.

**Verdict: Confirmed.** No fourth decision value is introduced; the
per-policy representation is the only architecture consistent with
PBPC-REQ-032, and the specified mechanism structurally prevents
`NOT_APPLICABLE`/`ALLOW` conflation without relying on a runtime check that
could be forgotten.

---

## 5. Hybrid Architecture — Independent Verification

PBPA-REQ-017/018/019/020 select declarative metadata
(`applicable_execution_classes: frozenset[str] | None`) plus a
policy-owned, trivial set-membership predicate.

Independently assessed responsibility separation:

- **Metadata** is a frozen class attribute belonging to the `PolicyRule`
  subclass — the same trust boundary (source-controlled, code-reviewed) as
  the rule's own `evaluate()` logic. It defines a domain, nothing else.
- **Predicate** (PBPA-REQ-050's specified interface,
  `resolve_applicability`) is a pure set-membership test over
  `(policy.applicable_execution_classes, request.execution_class)`. It
  cannot read `approval_present`, `evidence_available`, or any other
  evidence field by construction — those fields are not parameters to the
  specified interface. It cannot mutate state — the specified interface
  returns `bool`, and no side-effecting operation is described anywhere in
  §14.

This phase attempted to find an overlap or dual-authority scenario: could a
future implementation accidentally let the predicate perform decision
evaluation (blurring §3's separation)? The specified interface signature
(`(policy, request) -> bool`) structurally forecloses this — it has no
access to a `PolicyResult` or `PermissionBrokerDecision` to construct, and
no path back into `_compose`. The only way a future implementation could
violate this is by not following the specification at all, which is an
implementation-conformance question (§44's acceptance criteria), not a
defect in the specification itself.

**Verdict: Confirmed.** Metadata and predicate responsibilities are
unambiguous as specified; no overlap exists in the specified interface.

---

## 6. Applicability Authority — Independent Verification

PBPA-REQ-021/022/023 vest applicability authority in
Foundation-declared-metadata + registry-enforcement, explicitly prohibiting
caller-supplied exclusion mechanisms (`exclude_policies=[...]` or
equivalent).

Independently searched the actual Foundation source for any existing
caller-influence mechanism: `PermissionBrokerRequest`
(`:141-162`) has no field resembling a policy filter, exclusion list, or
profile selector. `build_permission_broker_request`
(`:165-192`) accepts no such keyword argument. `PermissionBroker.__init__`
(`:764-765`) accepts only an optional `registry: PolicyRegistry | None` —
which lets the *calling code that constructs the broker* choose a
registry, but this is a construction-time architectural choice (which
`PolicyRegistry` instance to use), not a per-request, caller-supplied
exclusion parameter; PBPA-REQ-022's prohibited shape is specifically
`broker.evaluate(request, exclude_policies=[...])` — a per-call escape
hatch — which does not exist today and which PBPA-001 correctly prohibits
introducing.

Independently attempted to construct the prohibited threat scenario: could
a caller pass `execution_class="none"` for a real mutation to get a weaker
policy set? Under PBPA-001's matrix (§7 below), `EXECUTION_CLASS_NONE`
already excludes `POL-004`, same as `EXECUTION_CLASS_MUTATION` does — so
this specific substitution would not actually change the outcome for
`POL-004` (both are outside its scope), but it *would* be a genuine
`execution_class` misclassification for any other rule that becomes scoped
in the future (§8 below, PBPA-REQ-089/091's own future-amendment
discipline). PBPA-REQ-032's classification-authenticity requirement (fixed
per integration point by the consuming contract, not caller-discretionary)
is the correct and only mitigation this contract offers for that broader
threat, independently confirmed sufficient for the one currently-governed
integration point (`pcae push`, fixed by PBPC-REQ-034) because no calling
code path exists today that lets a caller choose `execution_class` ad hoc
(confirmed: `push.py` does not construct a `PermissionBrokerRequest` at
all — no production consumption exists, §17).

**Verdict: Confirmed for the currently-governed integration point.**
Structurally sound as a general principle; its real-world strength for any
*future* integration depends entirely on that integration having an
equivalent governing contract, which PBPA-REQ-032 itself requires and which
this phase confirms is the correct requirement to impose (not an
optimistic assumption).

---

## 7. `execution_class` Contract — Independent Verification

Independently re-read `permission_broker_foundation.py:120-134,141-162`:

- `KNOWN_EXECUTION_CLASSES` is exactly the six-member frozenset PBPA-001
  states (`none`, `mutation`, `shell`, `backend`, `adapter`, `rollback`).
  **Confirmed**, byte-for-byte.
- `PermissionBrokerRequest.execution_class: str` carries no default value
  in the dataclass definition. **Confirmed** — construction without it
  raises `TypeError` (independently verified interactively: omitting the
  keyword argument from `build_permission_broker_request` is impossible
  without editing the function signature, since it too has no default for
  this parameter).
- No file/network/environment-variable loading path exists anywhere in the
  module (`grep -n "import\|open(\|os\.environ\|requests\.\|subprocess"` on
  the module returns only the four stdlib imports at the top —
  `__future__`, `uuid`, `dataclasses`, `datetime`). **Confirmed**: this is
  a fixed, in-memory, compiled vocabulary, not externally configurable.

**Verdict: Confirmed**, all sub-claims (PBPA-REQ-024..030) verified against
source directly, not inherited from 148C.2/148C.3's citation of the same
lines.

---

## 8. `POL-001..012` Applicability Matrix — Independent Re-Derivation

Every row was re-derived from primary source independently before this
phase compared its own conclusion against PBPA-001's table (§17 of PBPA-001).

| Policy | Independent re-derivation | Independent conclusion | Matches PBPA-001? |
|---|---|---|---|
| POL-001 | `MissingActiveTaskRule.evaluate()` reads only `request.task_id` (`:374-389`). `NG-001`/`INV-002` carry no operation-class exception in `V0_2_AUTONOMY_CONTRACT.md`/`NO_GO_GATES.md`. | Universal (`None`) | **CONFIRMED** |
| POL-002 | Stub, `evaluate()` unconditionally returns `_not_triggered` (`:566-567`). No field is read; no basis exists to scope a rule with no check. | Universal, moot | **CONFIRMED** |
| POL-003 | `MissingEvidenceRule.evaluate()` reads only `request.evidence_available` (`:399-413`). `INV-009` text carries no class exception. | Universal | **CONFIRMED** |
| POL-004 | See §9-13 below — full independent deep-dive, not a one-line check. | Scoped, `{shell, backend, adapter, rollback}` | **CONFIRMED**, after adversarial re-derivation (§9-13) |
| POL-005 | `ExecutionDisabledRule.evaluate()` reads only `request.simulation_only` (`:458-475`); this question ("does this request claim execution capability the Foundation lacks") is meaningful for every request regardless of class. | Universal (applicability); self-limiting only at the *trigger* level | **CONFIRMED** — and independently confirms PBPA-001's own careful distinction between applicability-universal and trigger-self-limiting (§20 of PBPA-001), which this phase found is not a rhetorical hedge but a real, independently-derivable distinction (§14 below). |
| POL-006 | `UnknownCapabilityRule.evaluate()` validates `action_type` and `execution_class` structurally (`:490-522`); must run before `execution_class` can be trusted by any other rule's applicability resolution. | Universal, and load-bearing precondition for applicability itself | **CONFIRMED** |
| POL-007 | `UnknownComponentRule.evaluate()` validates `requested_component` only (`:532-548`); same structural-precondition logic as POL-006. | Universal | **CONFIRMED** |
| POL-008 | Stub; `INV-007` ("overrides every other authorization") is definitionally global in `V0_2_AUTONOMY_CONTRACT.md:101`. A scoped emergency stop would contradict its own invariant. | Universal, moot | **CONFIRMED** |
| POL-009 | Stub; `INV-005` ("every execution decision produces an audit artifact") states no class exception. | Likely universal, moot | **CONFIRMED** |
| POL-010 | Stub; `INV-006` plausibly implies reads have nothing to roll back, but no primary source commits to a scope today. | Unresolved, out of scope, moot | **CONFIRMED as correctly deferred** — independently, this phase found no primary source that would let it responsibly pre-decide this either. |
| POL-011 | Stub; rule name implies backend-identity check meaningless outside `execution_class=backend`, but undecided. | Unresolved, out of scope, moot | **CONFIRMED as correctly deferred** |
| POL-012 | Stub; same reasoning as POL-011 for `adapter`. | Unresolved, out of scope, moot | **CONFIRMED as correctly deferred** |

**Verdict: All twelve rows independently re-derived and confirmed. No
discrepancy with PBPA-001's own matrix.** The three "unresolved" stub rows
(POL-010/011/012) are correctly left undecided — this phase independently
confirms no primary source exists today that would let a responsible
contract pre-commit their eventual scope, and deferring is the fail-safe
choice (an incorrect premature commitment would itself be a future defect;
a moot stub declining to speculate is not).

---

## 9. `POL-004` Deep Verification — Setting Up the Adversarial Test

PBPA-001 §43 (PBPA-REQ-109) explicitly instructs 148C.4 to independently
re-derive whether `{shell, backend, adapter, rollback}` is the correct
boundary for `POL-004`, "not merely ratify it." This phase treated that
instruction literally: rather than starting from PBPA-001's conclusion and
looking for confirming evidence, this phase first tried to construct the
strongest case *against* PBPA-001's scope, using the primary source PBPA-001
itself cites as `POL-004`'s origin lineage — `NG-008 -> INV-003 -> COMP-003`.

## 10. The Adversarial Case Against PBPA-001's Scope

Independently reading `V0_2_AUTONOMY_CONTRACT.md:170` verbatim:

```
INV-003: Human approval is mandatory before mutating execution.
```

This is the *exact*, word-for-word invariant text — not a paraphrase — and
it uses the word **"mutating"**. PBPA-001's frozen scope
(PBPA-REQ-063) explicitly **excludes** `EXECUTION_CLASS_MUTATION` — the
request-model field whose literal string value is `"mutation"` — from
`POL-004`'s applicable set. Read at face value and in isolation, this is a
direct textual inversion: the invariant that is `POL-004`'s own stated
justification appears to require exactly what the contract excludes.

This is not a contrived attack. If this reading held, PBPA-001 would be
Blocking under this phase's own instructions (§43's list explicitly
includes "primary contracts do not support using `execution_class` for
applicability" and "`POL-004` scoping is invented" as Blocking examples,
restated in the governing prompt for this phase).

## 11. Independent Resolution — Three Converging Primary Sources

This phase traced the term "mutation"/"mutating" through every primary
source that uses it, independently of PBPA-001's own Section 21 argument,
to determine whether `INV-003`'s "mutating execution" and
`EXECUTION_CLASS_MUTATION` denote the same concept.

**Source 1 — `V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md` §5**
(Phase 107E, predates B-1, predates PBPA-001 by five phases). Verbatim:

> Git Approval ... "What it does not authorize: Any runtime action,
> execution, shell command, backend invocation, or **mutation outside
> version control**. Git approval has no bearing on execution
> authorization."

This sentence draws the exact boundary this phase needed: it explicitly
distinguishes "mutation" that stays *inside* version control (a tracked
file edit, a commit, a push — Git Approval's domain) from "mutation
outside version control" (a side effect of a mediated execution action —
Execution Approval's domain, the domain `COMP-003`/`INV-003` govern). The
word "mutation" appears in **both** places in this repository's vocabulary,
but Phase 107E's own frozen text — five phases before B-1 was ever
discovered — already fixes them as two different things.

**Source 2 — `V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md`**
(Phase 109, also predates B-1). The Documentation-mutation and Source-mutation
rows state explicitly: "Git approval only ... no execution approval concept
applies, since this is a Git-tracked content change, not a mediated
execution action." The Git-lifecycle row (commit/push) states: "not
execution approval; committing/pushing tracked content is not a mediated
execution action under `docs/V0_2_AUTONOMY_CONTRACT.md`." This is a second,
independent primary source — pre-dating B-1's discovery by roughly forty
phases of this chapter's numbering — that already drew exactly the boundary
PBPA-001 later freezes. It is not plausible that this table was constructed
to solve a problem (B-1) that did not yet exist when the table was written.

**Source 3 — `V0_2_EXECUTION_READINESS_NO_GO_GATES.md:27-32`**, the
document's own scope statement: "`NG-` gates are scoped specifically to the
execution readiness decision point — the moment just before a proposed
action would move from `READY` to `AWAITING_HUMAN_APPROVAL`." `NG-008`'s own
condition text (`:177-183`) is "the action has reached
`AWAITING_HUMAN_APPROVAL`" — a state in the mediated-execution lifecycle
(`PLANNED -> READY -> AWAITING_HUMAN_APPROVAL -> AUTHORIZED -> EXECUTING ->
...`, PR-workflow §5), not a state that a Git-tracked content edit or commit
ever passes through. A file edit followed by a commit and PR never enters
`AWAITING_HUMAN_APPROVAL`; only a mediated execution attempt would, once
`COMP-002`/`COMP-003` exist.

## 12. Independent Conclusion on `POL-004`'s Scope

`INV-003`'s "mutating execution" is bound, by three independent,
B-1-predating primary sources, to the *mediated execution pipeline*
(`READY -> AWAITING_HUMAN_APPROVAL`, `COMP-002`/`COMP-003`), not to
`execution_class=mutation` (Git-tracked content changes, which is a
different, already-governed concept — Git Approval, PR review). The
apparent textual collision (§10) is real at the surface level — the same
English word is used for two different governed concepts — but is not a
substantive contradiction once traced to primary source. PBPA-001's
exclusion of `EXECUTION_CLASS_MUTATION` from `POL-004`'s scope is
**independently re-derivable from primary sources that predate B-1's
discovery**, which is the strongest available evidence against the
"narrowed to manufacture B-1's closure" concern this phase's governing
instructions explicitly warn about. Had Phase 109's table been silent on
Git-lifecycle actions, or had it been authored *after* B-1's discovery, this
phase's verdict on this point would be materially weaker.

This terminological collision between `INV-003`'s "mutating execution" and
the request model's `execution_class="mutation"` value is nonetheless a real
hazard for future readers and future amendments (a reader who does not
trace all three sources could easily reach §10's inverted, incorrect
conclusion). This is recorded as Non-Blocking Finding V-1 (§21) —
independently identified by this phase, not present in PBPA-001's own
findings table (§45 of PBPA-001) — recommending future amendments name
the two concepts more distinctly (e.g. "content mutation" vs. "mediated
execution") rather than relying on context to disambiguate "mutation."

**Verdict: `POL-004`'s scope (`{shell, backend, adapter, rollback}`,
excluding `mutation` and `none`) is CONFIRMED, independently re-derived,
not merely ratified.** This is the specific adversarial re-examination
PBPA-001 §43 required 148C.4 to perform, and it survived.

## 13. `POL-004` Behavioral Integrity When Applicable

PBPA-REQ-101 requires that when `POL-004` **is** applicable, its behavior is
byte-for-byte unmodified. Independently re-read
`MissingHumanApprovalRule.evaluate()` (`:427-443`) against PBPA-001's own
quoted text: identical. No hypothetical applicability-aware rewrite is
proposed anywhere in the contract; the specified mechanism (§5, §14) filters
*which requests* reach `evaluate()`, never rewrites `evaluate()` itself.

**Verdict: Confirmed.** `POL-004`'s meaning-when-applicable is unchanged;
only its applicable domain is specified.

---

## 14. `simulation_only` — Independent Verification

PBPA-REQ-068/069/070/071 hold that `simulation_only` never influences
applicability, and distinguish "the broker itself executes nothing" from
"the requested operation is non-mutating."

Independently attacked the claim that this distinction is a rationalization
rather than a real one: constructed (mentally, then empirically, §17) two
requests — `execution_class=mutation, simulation_only=True` (a future
`pcae push`, per PBPC-REQ-036) and a hypothetical
`execution_class=mutation, simulation_only=False` (a claim that the broker
itself would carry out the push). Under `POL-005`
(`ExecutionDisabledRule`, `:458-475`), the first does not trigger POL-005
(broker claims nothing about executing); the second triggers POL-005's DENY
unconditionally (no execution boundary exists, `COMP-002`
`not_implemented`). This confirms `simulation_only` genuinely answers a
different, orthogonal question from `execution_class` — one is "would the
Foundation itself carry this out" (always DENY today if `False`, regardless
of class, confirmed empirically §17), the other is "what kind of operation
is this" (the applicability dimension). They cannot be substituted for one
another, and empirically, toggling `simulation_only` while holding
`execution_class` fixed changes `POL-005`'s trigger, never `POL-004`'s
applicability set (which PBPA-001 does not model as implemented yet, but
whose *specification* is confirmed logically independent of
`simulation_only` by inspecting `MissingHumanApprovalRule.evaluate()`'s
actual condition, which reads only `approval_present`).

**Verdict: Confirmed.** The distinction is substantive, not rhetorical;
independently reproducible against the actual `POL-005` trigger condition.

---

## 15. Fail-Closed Attack Surfaces — Independent Adversarial Testing

Each attack below was independently constructed against the contract text,
not copied from PBPA-001's own threat table (§33 of PBPA-001), then checked
against that table for correspondence.

| Attack | Independent analysis | Contract's specified defense | Sufficient? |
|---|---|---|---|
| **Unknown `execution_class`** (e.g. `"quantum"`) | `POL-006` already validates this today (confirmed empirically §17: DENY). PBPA-REQ-036 correctly notes POL-006 is universal and always runs, so no other rule's applicability is ever resolved against an unvalidated class — verified: POL-006 has no `applicable_execution_classes` scoping in the spec (§17 table, `None`), so it cannot itself be filtered out before catching the bad value. | POL-006 DENY, universal, unfilterable | **Yes** |
| **Missing `execution_class`** | Dataclass field has no default (`:154`); construction fails before any policy runs (independently confirmed by attempting construction without the keyword in a REPL — raises `TypeError`). | Not a runtime-reachable state | **Yes, structurally** |
| **Future/new `execution_class`** (7th value, hypothetical) | Every currently-universal policy (`POL-001,003,005,006,007`, and moot stubs) defaults to `None` — a new class is automatically inside their domain with zero amendment (independently confirmed: `None` matches everything by the specified predicate, `policy.applicable_execution_classes is None`). Only `POL-004` (the one scoped rule) would need an explicit amendment decision for the new class, and PBPA-REQ-091 requires that decision be explicit, treating silence as Blocking *for that future amendment* — this phase confirms that is the correct incentive structure: a future author cannot silently ship a new class without confronting `POL-004`'s scope. | Universal-by-default + amendment-forcing rule for the one scoped policy | **Yes** |
| **Applicability predicate failure** (exception/non-bool) | The specified interface (§14, PBPA-REQ-097) requires converting this into the Foundation's existing `_sanitize_result` fail-closed pattern (`:598-629`, independently re-read: any malformed/erroring rule result becomes a DENY-equivalent labeled with the rule's own `policy_id`, never silently dropped). Extending this same pattern to predicate failure is architecturally consistent — it is not inventing a new fail-closed mechanism, it is reusing one already proven in the codebase. | Reuse of existing `_sanitize_result` fail-closed precedent | **Yes, as specified** (implementation-time verification required, §44) |
| **Missing required policy** (canonical `POLICY_IDS` member absent from constructed registry) | Today, an *entirely empty* registry already fails closed to DENY (`_compose`, `:680-691`, independently re-read and empirically reproduced conceptually: `if not results: return DENY`). PBPA-REQ-073 extends this same principle to "any canonical ID absent," which is a strict generalization of an already-existing, already-tested fail-closed behavior, not a new invention. | Generalization of existing empty-registry DENY | **Yes** |
| **Duplicate policy ID** | No existing mechanism handles this today (moot until a `PolicyRegistry` with duplicates is constructed, which no test or code path currently does). PBPA-REQ-075 requires deterministic construction-time rejection, explicitly forbidding first-wins/last-wins/merge. This is a specification for future implementation, not yet testable against running code — this phase can confirm the *specification* forbids the three permissive resolutions, but cannot empirically verify enforcement until implemented. | Specified reject-at-construction; not yet implemented | **Correctly specified; unverified in running code (expected — not yet implemented)** |
| **Empty applicable policy set** (`applicable_policy_ids = ∅`) | Independently checked: is this reachable under v1.0's matrix? Every request's `execution_class` is a member of a 6-value closed set; five of six implemented-or-moot-universal policies apply to every class; `POL-004` narrows only for `{mutation, none}`. For **every** `execution_class` value, at minimum `POL-001, POL-003, POL-005, POL-006, POL-007` remain applicable (all universal) — an empty applicable set is not reachable under v1.0's matrix for any of the six known classes. | Not reachable given current matrix; would need to fail closed if it ever became reachable (no explicit contract text on this exact empty-set case — see Finding V-2, §21) | **Not reachable today; contract text does not explicitly state the fail-closed default for the hypothetical case (Non-Blocking gap, §21)** |
| **Caller-supplied exclusion** (`exclude_policies=[...]`) | Independently confirmed absent from the actual request/broker/registry API surface (§6 above). | No such parameter exists; PBPA-REQ-022 prohibits introducing one | **Yes** |

**Verdict: Every attack surface this phase constructed independently has a
specified, fail-closed defense, with one Non-Blocking gap (empty applicable
set has no explicit contract statement, though it is not reachable under the
current matrix) recorded as Finding V-2 (§21).**

---

## 16. Ordering, Aggregation, Determinism, Explainability

- **Ordering** (PBPA-REQ-076/077/078): Independently re-derived the required
  sequence from first principles (what must be true before what) rather
  than checking PBPA-001's table for consistency with itself: validation of
  `action_type`/`execution_class` (`POL-006`) must precede any
  `execution_class`-dependent applicability decision, or that decision is
  meaningless (garbage-in). This phase's independent ordering matches
  PBPA-001's stated eight-step sequence exactly.
- **Aggregation** (PBPA-REQ-079/080): Independently re-read `_compose`
  (`:662-736`) — precedence `DENY > HUMAN_REVIEW > ALLOW` is unchanged code,
  confirmed byte-for-byte, and confirmed against
  `docs/PHASE_108_PERMISSION_BROKER_POLICY_COMPOSITION_HARDENING.md:45`
  ("Fixed, tested precedence: `DENY > HUMAN_REVIEW > ALLOW`, fail closed").
  PBPA-001's claim that applicability only changes *which results enter*
  `_compose`, never `_compose`'s own logic, is independently confirmed:
  `_compose` operates purely on whatever `results` tuple it receives; a
  filtered-out policy is simply absent from that tuple, requiring no change
  to `_compose` itself.
- **Determinism** (PBPA-REQ-085): The specified predicate is a pure
  set-membership test over two frozen values (a class attribute, a request
  field) — no dict iteration order, no environment read, no clock, no
  randomness is reachable from the specified interface. Independently
  confirmed no existing code path in the module reads
  `os.environ`/`random`/wall-clock time for any decision-relevant purpose
  other than the request's own `timestamp` field (which is never read by
  any policy's `evaluate()` — independently confirmed by grep: no
  `\.timestamp` reference exists in any `PolicyRule` subclass).
- **Explainability** (PBPA-REQ-081/082): The proposed additive fields
  (`applicable_policy_ids`, `non_applicable_policy_ids`) are sufficient to
  answer "why did `POL-004` not run" without source inspection, given
  `POL-004`'s own frozen `applicable_execution_classes` is public class
  state. Independently confirmed no sensitive-data leakage risk: the
  reconstructable reason is purely structural (`execution_class` value vs. a
  frozen class attribute), neither of which is secret or user-sensitive.

**Verdict: All four confirmed independently.**

---

## 17. Empirical Baseline — Live Execution Against Unmodified Code

Per this phase's instruction to exercise conceptual cases without changing
production code, the actual, unmodified `PermissionBroker` was invoked live
(read-only; no `src/pcae/**` file touched) for four representative request
shapes, to establish the exact pre-applicability baseline any future
implementation must not regress below and confirm several claims above
empirically rather than by code-reading alone:

```
push-shaped (execution_class=mutation), task+evidence, no approval:
    -> HUMAN_REVIEW, causing=(POL-004,)          [confirms B-1 empirically]

shell-shaped (execution_class=shell), task+evidence, no approval:
    -> HUMAN_REVIEW, causing=(POL-004,)          [today: identical outcome
                                                    to push-shaped -- POL-004
                                                    is NOT yet filtered by
                                                    class, confirming the gap
                                                    PBPA-001 exists to close]

unknown execution_class ("quantum"):
    -> DENY, causing=(POL-006,), triggered=(POL-004, POL-006)
                                                  [confirms POL-006 fires and
                                                   wins precedence even though
                                                   POL-004 also still fires
                                                   today -- pre-applicability,
                                                   nothing filters POL-004 out
                                                   even for a garbage class]

non-simulation push (simulation_only=False):
    -> DENY, causing=(POL-005,)                  [confirms POL-005 is
                                                   unconditional regardless of
                                                   class, independent of
                                                   simulation_only's
                                                   orthogonality to
                                                   execution_class, §14]
```

This empirically confirms: (a) B-1 is real and reproducible today, exactly
as PBPC-001 §8.1 states; (b) today's Foundation has no applicability
filtering at all — `POL-004` fires identically for `mutation` and `shell`
classes pre-implementation, which is the precise gap PBPA-001's
architecture would close; (c) `POL-005`/`POL-006` behave exactly as their
source and PBPA-001's matrix claim, independent of class or simulation
status.

---

## 18. Backward Compatibility, Versioning, Metadata Integrity

- **Backward compatibility** (PBPA-REQ-040/041/042): Independently confirmed
  no production consumer exists (`grep -rn "PermissionBrokerRequest\|build_permission_broker_request"
  src/pcae/commands/` returns zero matches — `push.py`/`commit.py` do not
  import the Foundation). PBPA-001's own claim that this is "prophylactic,
  not currently observed" is independently confirmed accurate, not an
  overstatement. **Classification: SAFE** (the strongest of the four
  categories this phase's instructions offer) — the default-`None`
  mechanism cannot weaken a consumer that does not exist, and is specified
  correctly for the first real consumer.
- **Versioning** (PBPA-REQ-086/087/088): Independently confirmed no
  separate applicability-version file/field exists anywhere in the
  repository (`grep -rn "applicability_version"` returns only PBPA-001's
  own prose discussing why one is *not* introduced). Versioning-with-the-
  Foundation-module is the simplest correct choice given a single-file,
  non-externally-loaded metadata store.
- **Metadata integrity** (PBPA-REQ-099/100): Independently confirmed
  `applicable_execution_classes` would be a compiled Python class attribute
  in the same file as `evaluate()` — no config file, environment variable,
  or database row exists today, or is proposed, for this purpose. No
  runtime-mutable path for an untrusted caller to alter applicability
  exists in the current module and none is introduced by the specification.

**Verdict: All confirmed.**

---

## 19. B-1 Status and 12-Hard-Block Separation — Independent Confirmation

Independently re-read PBPC-001 §8.1 (verbatim, §3 of this document's source
inventory) and `docs/PHASE_148C.1_..._CLARIFICATION_AND_REPAIR.md`'s
Category C classification (also re-read verbatim). PBPA-001's own §38/§39
claims are independently confirmed:

- **B-1 remains OPEN.** PBPA-001 is normative text only; it changes nothing
  in `src/pcae/core/permission_broker_foundation.py`. Empirically confirmed
  (§17): `POL-004` still fires unconditionally today, for every class,
  including `mutation`. A future `pcae push` request under PBPC-001's fixed
  field values (task+evidence present, `approval_present` fixed `False` per
  PBPC-REQ-046, no legitimate way to set it `True`) still reaches
  `HUMAN_REVIEW`, not `ALLOW`, until the applicability layer is actually
  implemented.
- **12-hard-block coverage is unaffected.** Independently re-confirmed:
  the eleven `HARD_BLOCK_REGISTRY` entries with no `POL-` counterpart
  (`docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`
  §8's "out of scope, not push-relevant" rows) operate at the shell-gate/
  hook layer, entirely outside `PolicyRegistry`/`PolicyRule`. An
  applicability layer over the *existing twelve* `POL-` rules has zero
  interaction with that separate enforcement layer — confirmed by the fact
  that PBPA-001's entire mechanism (§14's predicate) only ever reads
  `PermissionBrokerRequest` fields, never anything from
  `permission_broker.py`'s `HARD_BLOCK_REGISTRY` module.

**Verdict: Confirmed. B-1 open; 12-hard-block gap neutral, neither helped
nor worsened.**

---

## 20. IWC / AESIC / Runtime Enforcement Independence — Independent Spot-Check

- **IWC-REQ-029**: Independently confirmed `permission_broker_foundation.py`
  contains no reference to Decision Session, Confirmation, or Publication
  concepts (`grep -n "Confirmation\|Decision Session\|Publication"` on the
  module: zero matches). PBPA-001 touches none of this.
- **AESIC**: Independently confirmed the module's import list is exactly
  `__future__`, `uuid`, `dataclasses`, `datetime` (`:36-40`) — no
  `authority_evaluation`/`aesic` import exists. PBPA-001 proposes no new
  import.
- **Runtime Enforcement**: Independently confirmed via the same import-list
  check — no `backend_invocations` import exists in the Foundation module,
  consistent with its own module docstring's isolation claim
  (`:8-14`, independently re-read) and with PBPC-001 §25's orthogonality
  finding.

**Verdict: Confirmed, all three, by direct source inspection rather than by
citing PBPA-001's own claim.**

---

## 21. Findings

| ID | Finding | Classification |
|---|---|---|
| V-1 | `INV-003`'s "mutating execution" and the request model's `execution_class="mutation"` value use the same English word for two different governed concepts (mediated-execution-pipeline mutation vs. version-controlled content mutation). This phase independently resolved the apparent collision (§10-12) using three primary sources that predate B-1's discovery, but the terminology itself remains a hazard for a future reader who does not trace all three sources. | **Non-Blocking** — recommend a future amendment rename or explicitly disambiguate the two concepts (e.g. "content mutation" vs. "mediated execution") rather than relying on context; independently identified by this phase, not present in PBPA-001's own findings table. |
| V-2 | PBPA-001's contract text does not explicitly state the fail-closed default for an empty applicable-policy-set outcome (`applicable_policy_ids = ∅`), though this phase independently confirmed the case is not reachable under the current twelve-policy matrix for any of the six known `execution_class` values (§15). | **Non-Blocking** — not reachable today; recommend a future amendment or the implementation phase (148C.4's successor) add an explicit statement for defense-in-depth, since a future amendment narrowing more policies could make this reachable without anyone noticing the gap was never specified. |
| V-3 | `PolicyRegistry.__init__`'s existing `registry: PolicyRegistry | None` parameter on `PermissionBroker` lets *construction-time* calling code substitute an arbitrary rule tuple, including one with fewer or altered rules — a capability that exists today, independent of PBPA-001, and is not itself an applicability-layer concern, but is a pre-existing trust boundary this phase noticed while verifying §6's caller-authority claims. | **Observation** — out of PBPA-001's scope (this contract governs applicability *within* a given registry, not who may construct a `PermissionBroker` with a non-default registry); flagging for awareness only, not attributable to PBPA-001. |
| F-1 (carried forward from PBPA-001 §45) | Three stub policies (`POL-010/011/012`) have unresolved future applicability scope. | **Non-Blocking**, independently reconfirmed correctly deferred (§8). |
| F-4 (carried forward from PBPA-001 §45) | PBPA-001 alone cannot close B-1 — normative text only, unimplemented. | **Blocking for B-1 closure and for 148D; NOT Blocking for this verification phase's own completion** — independently reconfirmed (§19). |

No finding in this table is Blocking for PBPA-001's own architectural
soundness. F-4 is Blocking only for the separate question of B-1's closure,
exactly as it was Blocking only for that question in PBPA-001's own table.

---

## 22. Verification Verdict

**VERDICT B — VERIFIED WITH NON-BLOCKING FINDINGS — POLICY APPLICABILITY
IMPLEMENTATION PLANNING MAY PROCEED.**

Justification: zero Blocking findings against PBPA-001's own architecture or
internal coherence; `POL-004`'s scope was independently re-derived (not
ratified) and confirmed correct via three primary sources predating B-1;
classification authenticity is sufficient for the one currently-governed
integration point and correctly conditions any future integration on an
equivalent governing contract; fail-closed behavior is coherently specified
for every attack surface this phase constructed, with one Non-Blocking
textual gap (V-2) and one Non-Blocking terminology hazard (V-1); backward
compatibility is SAFE (the strongest category) because no production
consumer exists to weaken.

This verdict does **not** mean:

- Finding B-1 is closed (it is not — §19).
- Implementation is authorized (it is not — PBPA-001 §43/§44 remain the
  acceptance criteria a future implementation phase must satisfy).
- Chapter 148D is recommended (it is not — §23).

---

## 23. Confirmations

Finding B-1 remains **OPEN**. PBPA-001 v1.0 was independently re-derived and
adversarially attacked rather than trusted — including the one scoping
decision (`POL-004`) this phase's own governing instructions specifically
required be re-derived, not ratified, and which survived that re-derivation.
No Permission Broker applicability behavior was implemented. No Permission
Broker Foundation behavior was modified
(`git diff --name-only 234fce06..HEAD -- src/pcae/` is empty). No
`POL-001..012` policy meaning was changed. No approval was fabricated. No
`pcae push` behavior was changed. No caller-selectable policy bypass was
introduced or found to exist. `HUMAN_REVIEW` remains non-`ALLOW`.
Interactive Workflow Confirmation remains independent. Authority
Evaluation/AESIC remains disclosure-only. No Runtime Enforcement behavior
changed. Runtime remains `Observed`, maximum capability remains `observe`,
and execution availability remains `unavailable`.

---

## 24. Governance and Validation

```
git diff --name-only 234fce06..HEAD -- src/pcae/    -> empty
git status --short                                   -> clean (this phase's
                                                          own additions only)
pcae health                                           -> healthy
pcae check                                            -> passed
pcae status coherence                                 -> coherent
pcae doctor task-memory                               -> clean
pcae push check                                       -> clean, nothing_to_push
pcae runtime inspect                                  -> Observed / observe /
                                                          unavailable, unchanged
pcae notify status                                    -> Telegram configured,
                                                          enabled, ready

tests/test_permission_broker_foundation.py
tests/test_permission_broker_policy_composition_hardening.py
tests/test_permission_broker_policy_rule_framework.py
    -> 171 passed, 0 failed

pytest -m fast_green -n auto
    -> 4390 passed, 1 failed, 105 warnings, 118.09s
       failing test (tests/test_backend_cli.py::TestBackendReviewCreate::
       test_create_persists_to_latest) independently re-run in isolation:
       PASSED in 0.60s -- confirmed parallelization-order flake, unrelated
       to this phase (no src/pcae/** file touched, test file untouched,
       feature area (backend review persistence) has no relationship to
       Permission Broker Foundation)
```

---

## 25. Recommended Next Phase

**148C.5 — Permission Broker Foundation Policy Applicability Implementation
Plan.** PBPA-001 v1.0 is independently verified with zero Blocking findings;
per this repository's established discipline (PBPA-001 §49, this phase's own
governing instructions), the next phase is an implementation-*planning*
phase, not direct implementation. A likely subsequent sequence — not
pre-authorized here, subject to whatever the planning phase's own primary-
source re-derivation finds appropriate — is:

```
148C.5 -- Implementation Plan
148C.6 -- Implementation
148C.7 -- Independent Implementation Verification
148C.8 -- PBPC-001 v1.2 Re-Evaluation / B-1 Re-Verification and Closure
```

**148D remains NOT recommended.** Finding B-1 remains open, and the broader
12-hard-block centralization problem (PBPC-001 §8/§18) remains unaddressed
by this applicability layer, as PBPA-001 §39 and this phase's §19
independently confirm. Neither is resolved until the implementation-and-
verification sequence above completes and PBPC-001 is re-evaluated against
an actually-implemented Foundation.
