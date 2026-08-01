# Phase 148C.3: Permission Broker Foundation Policy Applicability Contract Freeze

**Phase ID:** 148C.3
**Mode:** Normative contract freeze only. No implementation, no
`src/pcae/**` modification, no Permission Broker Foundation behavior
change, no `POL-001..012` modification, no `POL-013+` addition, no `pcae
push` modification, no runtime capability change, no closure of Finding
B-1.
**Baseline:** commit `0923b76d` (post-148C.2, repository clean, 0
unpushed).
**Predecessor:** Phase 148C.2 (commits `506cd88a`, `a53b0fe9`) —
architectural recommendation only, not binding; recommended this phase.
**Date:** 2026-08-01

---

## 0. Authorization and Boundary

This phase is authorized to freeze — not implement — the normative
Permission Broker Foundation policy-applicability contract 148C.2
recommended. It may independently re-check the 148C.2 architecture
against primary sources; freeze policy-applicability semantics,
ownership, `execution_class` semantics, metadata, predicates,
policy-selection ordering, failure behavior, backward compatibility,
audit/explainability requirements, versioning, and security invariants;
define downstream implementation/verification requirements; identify
exact upstream contracts requiring amendment or clarification; and update
normal status/changelog/task artifacts. It must not modify `src/pcae/**`,
implement applicability, change current Permission Broker runtime
behavior, change `pcae push`, close B-1, add or fabricate approval,
change `HUMAN_REVIEW`, add `POL-013+`, introduce execution, or begin
148D.

### Bootstrap (initial inspection)

```
git status --short / --branch --short   -> clean, main, tracking origin/main
git log --oneline -25                    -> HEAD at 0923b76d (148C.2 staging)
git log --oneline origin/main..HEAD      -> empty
git rev-list --count origin/main..HEAD   -> 0
pcae health                              -> healthy
pcae check                               -> passed
pcae status coherence                    -> coherent
pcae doctor task-memory                  -> clean
pcae push check                          -> clean, nothing_to_push
pcae runtime inspect                     -> Observed / observe / unavailable, 0 plugins, 0 capabilities
pcae notify status                       -> Telegram configured, enabled, ready
pcae phase-report show --latest          -> 148C.2, recommended next 148C.3
pcae phase-report reconcile --phase-id 148C.2
    -> status: reconciled; promoted generations: 1; marker: already_dispatched;
       checkpoint: completed; receipt: finalized; mutation: none (inspection only)
```

Confirmed: repository clean, 0 unpushed commits, 148C.2 completed, B-1
remains open, 148D not authorized, runtime unchanged (`Observed` /
`observe` / `unavailable`).

### Primary sources independently re-inspected this phase

- `src/pcae/core/permission_broker_foundation.py` (788 lines, read in
  full again — not trusted from 148C.2's own line-number citations).
- `docs/PHASE_148C.2_PERMISSION_BROKER_FOUNDATION_POLICY_APPLICABILITY_MODEL_DESIGN.md`
  (full — the design this phase freezes).
- `docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`
  (PBPC-001 v1.1, full, both pages).
- `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` (targeted — `NG-008`'s
  exact condition text, the document's own execution-readiness-decision-
  point scope statement).
- `docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md` (targeted —
  the full command-category table, not only the "approval where
  applicable" sentence in isolation).
- `docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md` §5 (full —
  Git Approval / Execution Approval separation).
- Repository-wide contract-identifier survey (`grep` across
  `docs/contracts/*.md`) to select a collision-free contract identifier
  matching this repository's established naming convention (initials of
  significant words, excluding "Contract").

Every load-bearing factual claim 148C.2 made was independently
re-confirmed against this primary source, not accepted on 148C.2's own
authority — see `docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`
§3 for the full re-verification table. No discrepancy was found.

---

## 1. Executive Summary

This phase freezes **PBPA-001 v1.0 — Permission Broker Policy
Applicability Contract**
(`docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`),
the normative contract text for the applicability layer 148C.2 designed.

**Contract identifier.** Surveyed every existing `docs/contracts/*.md`
identifier (`PBPC-001`, `AESIC-001`, `AEM-001`, `TAMC-001`, `TAMP-001`,
`TAMPC-001`, `IWPC-001`, `CPIPC-001`, `GAC-001`, `PEC-001`, `PPA-001`,
`GLP-001`, `PGP-001`, `CHGR-001`, `AGOC-001`, and others). Confirmed the
repository's consistent convention: an acronym formed from the initials
of a contract's significant words, excluding the word "Contract" itself
(e.g. "Authority Evaluation Service Integration Contract" -> `AESIC-001`;
"Permission Broker Production Consumption Contract" -> `PBPC-001`).
Applying this convention to "Permission Broker Policy Applicability
Contract" yields **`PBPA-001`** — confirmed collision-free against the
full existing identifier set. `PBA-001` (the brief's alternative
suggestion) was considered and rejected: it drops "Policy," the exact
word distinguishing this contract's subject (which *policies* apply) from
a broader, undifferentiated "Permission Broker Applicability" scope this
contract does not claim.

**Independent re-verification (Section 3 of PBPA-001).** Before freezing
any requirement, this phase re-checked every load-bearing 148C.2 claim
against primary source directly — not trusting 148C.2's own citations.
Every claim checked out: `PolicyRegistry.evaluate_all`'s unconditional
evaluation (`permission_broker_foundation.py:647-659`); the Foundation's
own design principles asserting one decision point, not universal
applicability (`:1-34`); `NG-008`'s scope statement
(`V0_2_EXECUTION_READINESS_NO_GO_GATES.md:27-32`, `:177-190`); the Phase
109 command-category table's "`POL-004` approval where applicable"
(`V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md:163`) and its
Documentation/Source/Git-lifecycle rows' consistent "Git approval only"
disposition; the Git Approval / Execution Approval separation
(`V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md:278-317`);
`MissingHumanApprovalRule`'s unconditional condition
(`permission_broker_foundation.py:416-443`); and every other structural
claim about the Foundation's fail-closed mechanics. No discrepancy was
found. This phase's contract therefore freezes 148C.2's selected
architecture as normative, having independently earned that conclusion
rather than inherited it.

**What PBPA-001 v1.0 freezes.** The applicability/evaluation separation
(applicability is resolved before, and independent of, evidence fields
like `approval_present`); a per-policy `APPLICABLE`/`NOT_APPLICABLE`
result model with no fourth broker-level decision value; the selected
hybrid architecture (declarative `applicable_execution_classes` metadata,
policy-owned, registry-enforced); `execution_class` as the sole
applicability dimension, with a full classification-authenticity and
anti-spoofing model; a complete, independently re-derived `POL-001..012`
applicability matrix (eleven universal or moot, `POL-004` scoped to
`{shell, backend, adapter, rollback}`, three stubs explicitly left
unresolved); fail-closed defaults for every unknown/missing/malformed
condition; determinism, versioning, explainability, and auditability
requirements; a full security threat model; a contract-compatibility
review; and complete verification and future-implementation acceptance
criteria.

**This phase does not close B-1.** No `src/pcae/**` file was modified.
No Permission Broker Foundation behavior changed. `POL-004` continues to
evaluate unconditionally on every real request until a future,
independently-authorized implementation phase actually changes the
source. **Recommended next phase: 148C.4 — Permission Broker Foundation
Policy Applicability Contract Independent Verification** (Section 8).
This document freezes a normative contract, not an implementation.

---

## 2. Scope

In scope: independent re-verification of 148C.2's factual claims against
primary source; contract-identifier selection; freezing the normative
applicability/evaluation separation, result model, hybrid architecture,
ownership, `execution_class` contract, classification-authenticity model,
policy metadata, predicate interface, the complete `POL-001..012`
applicability matrix, fail-closed behavior, security threat model,
determinism/versioning/explainability/auditability requirements,
contract-compatibility review, contract-amendment inventory, requirement
traceability, verification requirements for 148C.4, and future
implementation acceptance criteria; updating `PROJECT_STATUS.md`,
`CHANGELOG.md`, `tasks/DONE.md`, and governed task/finalization
artifacts.

Out of scope: any `src/pcae/**` change; any `POL-001..012` modification;
any `POL-013+` addition; any `pcae push` change; declaring B-1 closed;
`approval_present=True`; a caller-selectable policy-exclusion mechanism;
implementation of the applicability layer; 148D planning.

---

## 3. Independent Re-Verification Summary

See `docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`
§3 for the complete table (nine load-bearing claims, each with the exact
primary-source citation independently re-checked this phase and the
result). Summary: **zero discrepancies found.** 148C.2's factual
substrate is accurate; this contract's refinements relative to 148C.2 are
in normative representation and force (e.g. freezing `PBPA-REQ-###`
identifiers, the explicit anti-inversion requirements of Section 4A/19,
the explicit stub-policy non-resolution of Section 17), not corrections
of a primary-source error 148C.2 made.

---

## 4. Contract Identity Selection

See Executive Summary above and PBPA-001's own "Contract identity and
status" header. `PBPA-001` was selected over the brief's alternative
suggestion `PBPC-001`-lookalike names because it is (a) derived
mechanically from this repository's own established initialism
convention, verified against every existing contract identifier in
`docs/contracts/*.md`, and (b) collision-free.

---

## 5. Applicability vs. Evaluation

Frozen at PBPA-001 §4A (`PBPA-REQ-009..012`). The governing anti-inversion
rule — applicability is resolved from `execution_class` alone, strictly
before any evidence field (`approval_present`, `evidence_available`) is
read — is the single most load-bearing invariant in this contract; it is
restated three times in PBPA-001 (§4A generally, §19 for `POL-004`
specifically, and embedded in §24's ordering) precisely because an
inversion (`approval missing -> POL-004 not applicable`) would silently
defeat the rule `POL-004` exists to enforce.

---

## 6. Applicability Result Model

Frozen at PBPA-001 §5 (`PBPA-REQ-013..016`). No fourth broker-level
`PermissionBrokerDecision.decision` value is introduced — `ALLOW`/`DENY`/
`HUMAN_REVIEW` remain the only three, consistent with PBPC-001 §10's
existing prohibition on a second decision taxonomy. The distinction lives
one layer down, as a new `PolicyResult.applicable: bool` field, resolved
by the registry strictly before a non-applicable policy's own
`evaluate()` is ever called.

---

## 7. Selected Architecture, Ownership, and `execution_class` Contract

Frozen at PBPA-001 §6-§10. The hybrid of Candidate A (policy-owned
applicability) and Candidate B (declarative metadata) is confirmed, not
re-litigated — independent re-verification (Section 3) found no
primary-source basis to prefer a different candidate among 148C.2's four.
Applicability authority is Foundation-declared, registry-enforced; no
caller-selectable exclusion parameter is authorized anywhere in the
public interface. `execution_class`
(`permission_broker_foundation.py:154`, six known values, already
validated by `POL-006`) is the sole applicability dimension; no new
request field is introduced.

---

## 8. `POL-001..012` Applicability Matrix

Frozen at PBPA-001 §17 (`PBPA-REQ-060..062`). Independently re-derived,
not copied from 148C.2's own table without re-checking: `POL-001`,
`POL-003`, `POL-005`, `POL-006`, `POL-007` are universal (five
implemented, universal rules); `POL-004` is scoped to
`{EXECUTION_CLASS_SHELL, EXECUTION_CLASS_BACKEND, EXECUTION_CLASS_ADAPTER,
EXECUTION_CLASS_ROLLBACK}`; `POL-002`, `POL-008`, `POL-009` are moot stubs
whose eventual scope (once implemented) is plausibly universal;
`POL-010`, `POL-011`, `POL-012` are moot stubs whose eventual scope is
plausibly narrower but explicitly left **UNRESOLVED** by this contract —
a deliberate deferral to whichever future phase implements each stub, not
an oversight (PBPA-REQ-061).

`POL-004`'s scope is derived from a general rule ("`POL-004` applies to
execution classes representing mediated execution actions under the
canonical execution lifecycle `NG-008`/`INV-003`/`COMP-003` govern"), not
a push-specific carve-out — PBPA-001 §18 explicitly prohibits encoding
`POL-004 does not apply to push` as special-cased logic anywhere in a
conforming implementation, diagnostic, or future contract text.

---

## 9. Security Threat Model and Fail-Closed Behavior

Frozen at PBPA-001 §9, §33-§36 (classification authenticity, caller
spoofing, applicability metadata integrity) and §11, §22, §23, §30, §34,
§35 (unknown/missing/malformed classification, required policy set,
duplicate policy, new execution classes, predicate failure, unknown
policy). Every threat and every unknown/failure condition resolves
toward evaluating **more** policies, or toward a hard fail-closed
`DENY`-equivalent outcome, never toward silently narrowing the applicable
set. No permissive fallback exists anywhere in this contract.

---

## 10. Determinism, Versioning, Explainability, Auditability

Frozen at PBPA-001 §26-§29 (`PBPA-REQ-081..088`). Applicability
resolution is a pure function of `(request.execution_class, {rule metadata})`
with no environment-dependent component. Applicability metadata versions
with the Permission Broker Foundation contract itself — no separate
artifact/version domain is introduced, matching this repository's stated
preference against unnecessary artifact proliferation. Explainability is
additive (`applicable_policy_ids`/`non_applicable_policy_ids` on
`PermissionBrokerDecision`); no durable audit artifact is authorized by
this contract.

---

## 11. Contract Amendment Inventory and Compatibility

Frozen at PBPA-001 §40-§41. Exactly one existing frozen contract
(Permission Broker Foundation, Phase 108A-C) is normatively amended, and
only additively — no existing behavior, invariant, or rule meaning
changes. PBPC-001 v1.1 is explicitly **not** amended by this contract; a
future v1.2 is identified as required only after Foundation
implementation and its independent verification. No amendment to the
Autonomy Contract, Interactive Workflow Contract, Authority Evaluation/
AESIC, or Runtime Enforcement is required or made.

---

## 12. B-1 Status

**Finding B-1 remains OPEN.** This phase performs step 2 of the closure
path PBPC-001 §8.1 and 148C.2 §25 already state:

```
148C.2 (design, complete)
      |
148C.3 (this phase: contract frozen -- normative text only)
      |
148C.4 -- independent adversarial verification of PBPA-001
      |
Foundation implementation (separately authorized)
      |
independent implementation verification
      |
PBPC-001 v1.2 re-evaluation
      |
B-1 independent re-verification and closure
```

Nothing in this document performs or authorizes any step beyond "148C.3,
frozen."

---

## 13. Confirmations

Finding B-1 remains **OPEN**. No Permission Broker Foundation behavior
was changed. No `POL-001..012` meaning was weakened — `POL-004`'s own
evaluation logic is byte-for-byte unmodified; only a sibling applicability
attribute is specified in contract text, unimplemented. No caller-
selectable policy exclusion was introduced. No approval was fabricated.
No `pcae push` behavior was modified. Interactive Workflow Confirmation
remains independent. Authority Evaluation / AESIC remains
disclosure-only. `HUMAN_REVIEW` remains non-`ALLOW`. No Runtime
Enforcement behavior was changed. Runtime remains Observed, maximum
capability remains observe, and execution availability remains
unavailable (confirmed live, §0 and §15).

---

## 14. Findings

| ID | Finding | Classification |
|---|---|---|
| F-1 | Independent re-verification found zero discrepancies between 148C.2's factual claims and primary source (§3). | Observation |
| F-2 | Three stub policies (`POL-010..012`) have explicitly UNRESOLVED future applicability scope, deliberately deferred (PBPA §17). | Non-Blocking, moot while stub |
| F-3 | No general `action_type -> execution_class` mapping is frozen; classification authenticity relies on per-integration-point contract-fixing (the existing PBPC-001 precedent). | Observation — sufficient for the one known integration point |
| F-4 | This contract, alone, does not and cannot close B-1. | **BLOCKING for 148D and B-1 closure; NOT BLOCKING for this phase's own completion** |
| F-5 | No caller-selectable exclusion mechanism is introduced. | Observation |
| F-6 | The 12-hard-block coverage gap (PBPC-001 §8/§18) is unaffected. | Non-Blocking, unaffected |
| F-7 | A full, unmarked `python -m pytest -n auto` run, attempted three times live in this session, consistently reached ~99% (18760-18835+ of ~19000 collected tests passing, matching the `fast_green`-suite pass rate) before stalling near completion on a single xdist worker with frozen CPU time across repeated checks — an environmental deadlock, most plausibly contention with the real `.pcae/agent-locks/latest.json` this live session holds throughout the run, not a regression this phase introduced (no `src/pcae/**` file was touched, and the `fast_green`-marked suite — this repository's documented regression-check suite, per `docs/DEMO_SCRIPT.md` and prior phase milestone summaries, e.g. Phase 102/103's "fast_green: 4387/4390") passed cleanly and completely. `pytest-timeout` was installed transiently to diagnose this, found thread- and signal-based interruption both destabilize this codebase's own xdist/subprocess-heavy tests (cascading `[gwN] node down` xdist crashes), and was uninstalled afterward, restoring the environment. | Non-Blocking, Observation — not attributable to this phase; recommended for a future session to investigate running the full suite outside an active governed agent-lock session |

No Blocking architectural or contract conflict was found between PBPA-001
and any other frozen contract.

---

## 15. Governance Results (This Phase)

```
pcae check              -> passed
pcae health              -> healthy
pcae status coherence    -> coherent
pcae doctor task-memory  -> clean
pcae push check          -> clean, nothing_to_push
pcae runtime inspect      -> Observed / observe / unavailable, 0 plugins, 0 capabilities
                             (unchanged before and after this phase)
telegram runtime          -> loaded, configured, enabled
production source diff    -> git diff --name-only 0923b76d..HEAD -- src/pcae/ empty
                             (confirmed before this phase's own commits; no src/pcae/**
                             file touched by this phase)
pytest -m fast_green -n auto
                          -> 4391 passed, 0 failed, 0 skipped, 105 warnings, 119.84s
                             (this repository's documented regression-check suite,
                             docs/DEMO_SCRIPT.md; clean pass, no pre-existing failures)
full pytest -n auto (unmarked)
                          -> attempted 3x; consistently ~99% complete (18760-18835+
                             passing) before an environmental near-completion stall
                             tied to this session's live agent lock (F-7 above, not a
                             regression, not attributable to this phase's docs-only diff)
```

---

## 16. Recommended Next Phase

**148C.4 — Permission Broker Foundation Policy Applicability Contract
Independent Verification.** 148C.4 SHALL independently re-derive the
applicability model this contract freezes and attack it adversarially —
not accepting PBPA-001's own text as an oracle, per this repository's
established adversarial-verification discipline (148C.1's own
methodology, restated by 148C.2 §40, restated again by PBPA-001 §49). At
minimum, per PBPA-001 §43, 148C.4 must attack: the complete
`POL-001..012` applicability mapping, especially `POL-004`'s domain;
`execution_class` authenticity and caller-spoofing mitigation;
action/class mismatch handling; simulation spoofing and the
broker-execution/operation-semantics distinction; universal/scoped-policy
defaults; missing/duplicate-policy handling; unknown/future-class
handling; predicate-failure handling; determinism; explainability
sufficiency; backward compatibility; decision-vocabulary preservation;
`HUMAN_REVIEW` preservation; and full contract compatibility. 148C.4 does
not itself authorize implementation; a further, separately authorized
implementation-and-verification sequence remains required before B-1 can
close. **148D remains NOT recommended** while B-1 remains open.
