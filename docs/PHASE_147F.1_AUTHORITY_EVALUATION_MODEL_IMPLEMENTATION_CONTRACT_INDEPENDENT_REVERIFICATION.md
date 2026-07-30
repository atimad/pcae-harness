# Phase 147F.1 — Authority Evaluation Model Implementation Contract Independent Re-Verification

## Contract identity and status

**Phase:** 147F.1
**Mode:** Independent Contract Re-Verification (documentation-only; no
production code, contract, schema, or test file modified; no
implementation authorized)
**Predecessor:** 147E.1 — Authority Evaluation Model Implementation
Contract Repair (verdict: IMPLEMENTATION CONTRACT REPAIRED, AEMIC-001
v1.0 → v1.1, repairing BF-147F-1)
**Subject:** AEMIC-001 v1.1 — Authority Evaluation Model Implementation
Contract (`docs/contracts/AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT.md`)
**Runtime baseline:** Observed / observe / unavailable — unchanged by
this phase; confirmed at §27 below.

---

## 1. Executive Summary

This phase independently reconstructed BF-147F-1, re-derived the
constraints AEM-001 v1.0 imposes on any repair, reassessed all candidate
repair families, verified the exact v1.0→v1.1 diff line by line, and
attacked the repaired `evaluate()` signature, the `citation_text`
if-and-only-if invariant, the disclosure-only security properties, and
every carried-forward finding — before treating Phase 147E.1's own
account of the repair as anything more than a starting pointer.

**BF-147F-1 itself is correctly and completely repaired.** `citation_text`
is now reachable through `evaluate()`'s own fifth parameter
(AEMIC-REQ-019/072); `MissingCitationTextError` (AEMIC-REQ-064,
AEMIC-REQ-101) closes the `eligible`-without-citation path; the
if-and-only-if invariant (AEMIC-REQ-022) is now satisfiable, and in fact
satisfied, on every path through the sole specified construction
function, for all three `EvaluationResult` values. `EligibleAuthorityDeclaration`'s
AEM-001-frozen six-field shape is untouched. Candidate repair 1 (widening
the Declaration) was correctly rejected as foreclosed by AEM-REQ-007, not
merely inferior. No AEM-001 requirement is narrowed, widened, or
contradicted by the repair.

**However, this phase's own independent reconstruction — performed
directly against AEMIC-001's frozen text, not against Phase 147E.1's or
Phase 147F's account of it — discovered a second, distinct Blocking
defect that predates the repair, is untouched by it, and was not caught
by Phase 147C, Phase 147D, or Phase 147F:** `AuthorityEvaluationOutcome.template_ref`
and `.template_version` are mandatory fields (AEMIC-REQ-021, "Yes," no
conditional) described as "verbatim copy of the evaluation's own input" —
but `evaluate()`'s own five-parameter signature (AEMIC-REQ-019, AEMIC-REQ-072,
unchanged by the 147E.1 repair) never accepts `template_ref` or
`template_version` as a distinct input. For the `eligible`/`ineligible`
branches this can be worked around by deriving the two fields from
`declaration.template_ref`/`declaration.template_version` (both present
on `EligibleAuthorityDeclaration` per AEMIC-REQ-015) — a derivation the
contract never actually states, but at least a value exists to derive
from. **For the `indeterminate` branch (`declaration is None`), no value
exists anywhere in `evaluate()`'s own parameter list or in `declaration`
to populate these two mandatory fields.** This is a defect with the same
shape as BF-147F-1 — a required output field with no data channel into
the sole specified construction path, for at least one of the three
result branches — newly designated **BF-147F.1-1** (§20, §22).

Because a new Blocking defect survives independent re-verification (even
though it is unrelated to BF-147F-1's own citation-plumbing repair), this
phase's verdict on AEMIC-001 v1.1 as a whole is:

**Overall Verdict: REPAIR NOT VERIFIED.**

BF-147F-1 specifically is **Repaired, confirmed** (§6, §20). AEMIC-001
v1.1 as a whole is not yet independently verifiable as VERIFIED or
VERIFIED WITH NON-BLOCKING FINDINGS because of BF-147F.1-1, a distinct,
newly-discovered Blocking defect.

Recommended next phase: **147E.2 — Authority Evaluation Model
Implementation Contract Second Repair**, scoped narrowly to BF-147F.1-1
only (§29). This recommendation is not an authorization.

---

## 2. Authorization and Scope

Per the human authorization above this report, this phase is authorized
to independently re-verify AEMIC-001 v1.1 only. It is explicitly
forbidden from repairing AEMIC-001, modifying `src/pcae/**`, implementing
`pcae.authority_evaluation`, creating a Registry or any production model,
modifying any schema, or modifying AEM-001, IWC-001, IWPC-001, PEC-001,
CHGR-001, TAMC-001, TAMPC-001, or GAC-001. No item in that list was
touched by this phase (§25 confirms this as an audited fact, not merely a
forward-looking prohibition).

The repair (BF-147F-1's disposition, Phase 147E.1) is treated throughout
this report as an **untrusted claim**, verified independently rather than
accepted on the strength of Phase 147E.1's or Phase 147F's own account.

---

## 3. Independence Method

Reading and reasoning order actually followed, per the governing prompt's
own independence discipline (§2 of the governing prompt):

1. AEM-001 v1.0 (`docs/contracts/AUTHORITY_EVALUATION_MODEL_CONTRACT.md`)
   — read in full, as the sole governing predecessor contract, before any
   AEMIC-001 text was consulted for this phase's own reconstruction
   purposes.
2. Phase 147B's report — read for the architectural context AEM-001 itself
   was frozen against, and for the AEM-001 §14/§16 disclosure-only
   judgment call's own reasoning.
3. Independent reconstruction of BF-147F-1 (§5 below), performed by
   re-deriving the contradiction directly from AEMIC-001's own text,
   before re-reading Phase 147F's or Phase 147E.1's own account of it a
   second time, for comparison only.
4. Independent reconstruction of the minimum valid repaired evaluator
   interface (§6 below) and the candidate-repair space (§7), before
   reading Phase 147E.1's own candidate evaluation (§7 of that report) a
   second time, for comparison only.
5. AEMIC-001 v1.1 (`docs/contracts/AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT.md`)
   — read in full, section by section, attacking every requirement
   independently rather than accepting §25's own self-reported "Repair
   Confirmation" section as dispositive.
6. Phase 147F's own independent verification report (NOT VERIFIED, one
   Blocking finding) — read in full, used as a floor for what this
   phase's own reconstruction must independently reproduce (§5) and as a
   record of which findings (F-147F-2, F-147F-3) remain open and
   out-of-scope for this repair.
7. Phase 147E.1's own repair report — read in full, used only as a record
   of what was claimed to change, never as proof the change is correct
   (per the human authorization above: "The repair must be treated as an
   untrusted claim").
8. Phase 147D's implementation architecture — consulted for evidence of
   design intent only (never contractual authority), specifically for
   §6.7/§6.8's illustrative sequences, which independently corroborate
   §20 below's finding that `template_ref`/`template_version` were never
   named as explicit `evaluate()` inputs at any point in this chapter's
   own history, including before AEMIC-001 existed.
9. Phase 147C's independent verification of AEM-001 — read for F-147C-1's
   and F-147C-2's own origin and exact text (§21 below).
10. IWC-001, IWPC-001, PEC-001, CHGR-001, TAMC-001, TAMPC-001, GAC-001 —
    consulted via AEM-001's and AEMIC-001's own citations and targeted
    section-header/requirement-ID confirmation, for §11, §17, §19 below.
11. `decision_template.schema.json`, `human_governance_record.schema.json`
    — re-inspected directly for the citation-source reconciliation claims
    (§9, §18).
12. Direct source re-inspection: `src/pcae/interactive_workflow/models/session.py`,
    `src/pcae/governance/publication/coordinator.py`, `record.py`,
    `tests/test_phase_144c_publication_coordinator.py` — to independently
    reconfirm no implementation, Registry, or forbidden-import guard for
    `pcae.authority_evaluation` exists (§4).

`docs/PHASE_147D_AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_ARCHITECTURE.md`
was treated throughout as non-authoritative design evidence, exactly as
Phase 147F's own discipline required, restated here per the governing
prompt's own independence instruction.

---

## 4. Bootstrap (repeated at close)

Run at phase start from `~/repos/pcae-harness`:

- `git status --short`: clean (no output).
- `git branch --show-current`: `main`.
- `git log --oneline --decorate -80`: HEAD at `c0e3bcdc` ("Phase 147E.1:
  close task, sync canonical report, open idle placeholder"), matching
  `origin/main`/`origin/HEAD`.
- `git rev-list --count origin/main..HEAD`: `0`.
- `git rev-list --count HEAD..origin/main`: `0`.
- `pcae session bootstrap --agent-id claude-local --sync-lock`: lock
  already held by `claude-local`; backend lock rehydrated; health
  healthy; check passed; active task was the post-147E.1 idle placeholder
  (expected — the "no active governed phase other than an expected idle
  placeholder" precondition holds); readiness flagged as "blocked" only
  because the idle task predates this phase's own opening and the latest
  handoff predates the latest phase report — both are the ordinary,
  expected state of an idle checkpoint, not new problems.
- `pcae check`: passed.
- `pcae health`: healthy; required PCAE files all present; policy
  validation valid; git status clean.
- `pcae doctor task-memory`: clean, no inconsistencies.
- `pcae runtime inspect`: Runtime status `not_implemented`, Runtime state
  `Observed`, Execution capability `unavailable`, Maximum plugin
  capability `observe`, Registry status `empty`, Plugin count `0`.
- `pcae push check`: clean (`nothing_to_push`); branch `main`, working
  tree clean, health healthy, check passed, task memory clean.

**Confirmed**: repository clean; branch correct; local and remote
synchronized (0/0); no active governed phase beyond the expected idle
placeholder; runtime unchanged from every predecessor phase's own
baseline; policy unchanged; strategic lineage unchanged. `PROJECT_STATUS.md`
was treated as authoritative throughout, consistent with standing
repository precedent.

Re-confirmed identically at phase close (§27).

---

## 5. BF-147F-1 Reproduction (Independent)

Reconstructed directly from AEMIC-001 v1.1's own frozen text, working
backward to what v1.0 must have said, before re-reading Phase 147F's or
Phase 147E.1's own account for comparison.

**Step 1 — locate the outcome-shape invariant.** AEMIC-REQ-022 (§6.1)
requires, "checked at construction time, not left to caller discipline":
`citation_text is not None` **iff** `evaluation_result == ELIGIBLE`.

**Step 2 — locate every construction-time data channel available to the
sole specified producer of `AuthorityEvaluationOutcome`.** AEMIC-REQ-072
names `pcae.authority_evaluation.evaluation.evaluate` as that function.
Its current (v1.1) signature (AEMIC-REQ-072) is five parameters:
`claimed_identity`, `declaration`, `evaluated_at`, `evaluator_version`,
`citation_text`. Confirmed independently, by re-reading §5's table
(AEMIC-REQ-019) a second time without assuming §14's block already
matches it: they agree exactly.

**Step 3 — reconstruct what v1.0 must have lacked.** Per the Phase 147E.1
report's own §7 ("Requirement Changes," an untrusted claim, verified
here), AEMIC-REQ-019/020/031/064/065/072/074/075/077/095 were the ones
touched. Independently confirmed consistent with this phase's own
enumeration: removing `citation_text` from today's five-parameter list
leaves exactly the four parameters Phase 147F's own report (§7) recorded
as v1.0's closed signature — `claimed_identity`, `declaration`,
`evaluated_at`, `evaluator_version`. Under that four-parameter closure,
no value existed anywhere in `evaluate()`'s reachable inputs
(`claimed_identity` — wrong content and a distinct field in its own
right per AEMIC-REQ-021; `declaration`'s own six fields, none of them
`citation_text` per AEMIC-REQ-015/016; `evaluated_at`/`evaluator_version`
— both metadata) that could become `AuthorityEvaluationOutcome.citation_text`
for the `eligible` case. AEMIC-REQ-022's invariant was therefore
unsatisfiable via the contract's own sole sanctioned construction path
for that one branch. This independently reproduces BF-147F-1 exactly as
Phase 147F's own report describes it (§7 of that report), confirming it
was **genuine** (not a reading artifact — no alternate reading of v1.0's
own four-parameter closure dissolves the contradiction), **Blocking**
(no requirement in v1.0 disclosed or safely contained the gap — contrast
with AEMIC-REQ-032/034, which correctly model disclosed, safely-contained
limitations elsewhere in the same contract), **implementation-impossible**
for the `eligible` branch specifically (every well-formed v1.0 call either
violated the closed-parameter rule or produced `citation_text = None` on
an `eligible` result, directly violating AEMIC-REQ-022), and
**security-relevant** (the only practical resolution available to a real
implementer — bypassing `evaluate()` to construct `AuthorityEvaluationOutcome`
directly — reopens exactly the caller-controlled-citation-fabrication risk
AEMIC-REQ-022's "not left to caller discipline" language exists to
foreclose).

**Independent conclusion, reached before re-reading either predecessor
report's own account a second time:** BF-147F-1 as originally identified
was genuine, Blocking, implementation-impossible, and security-relevant.
This matches Phase 147F's own classification exactly (§22, §24 of that
report) and Phase 147E.1's own root-cause account (§3 of that report).
No daylight was found between this phase's own independent reconstruction
and the predecessor reports' account of what BF-147F-1 was.

---

## 6. Minimum Valid Repaired Evaluator Interface (Independent Reconstruction)

Reconstructed before comparing against AEMIC-001 v1.1's actual §5/§14
text.

A repaired `evaluate()` must, at minimum:

1. Preserve `EligibleAuthorityDeclaration`'s AEM-001-frozen six-field
   shape unmodified (AEM-REQ-007 forecloses widening it; any repair that
   requires a seventh field is not a valid AEMIC-001-level repair at
   all — it would require an AEM-001 amendment, out of both AEMIC-001's
   own scope and this phase's own No-Go Boundary).
2. Preserve `evaluation_result`'s determination as a pure function of
   exactly the two evidentiary inputs AEM-REQ-016 names
   (`claimed_identity`, `declaration`) — a repair must not let
   `citation_text` (or any new parameter) influence which of the three
   `EvaluationResult` values is produced, or it would violate AEM-REQ-016's
   "two evidentiary inputs" framing at one level removed.
3. Supply a construction-time-enforced data channel for `citation_text`
   reachable only when `evaluation_result == ELIGIBLE`, satisfying
   AEMIC-REQ-022 for that branch without weakening the invariant itself.
4. Not introduce a second public construction path for
   `AuthorityEvaluationOutcome` (fragmenting the single-enforcement-point
   property BF-147F-1's own security consequence depends on).
5. Remain fully backward-compatible with every AEMIC-001 v1.0 requirement
   this repair does not need to touch (§5, §9, §13.1, §14 at most).

**Independent comparison against AEMIC-001 v1.1's actual repair:**
matches exactly on all five points. The fifth parameter
(`citation_text: str | None = None`) satisfies (3) without touching (1);
AEMIC-REQ-101 explicitly states `evaluation_result` is determined "from
exactly the two evidentiary inputs AEM-REQ-016 names... the `citation_text`
parameter plays no role in this determination," satisfying (2); no new
public type or second construction function was introduced, satisfying
(4); and the diff (§8 below) confirms (5) — no section outside §5, §9,
§13.1, §14, §15, §20, §22, §23 differs from v1.0. **Candidate 2, as
selected, is independently confirmed to be the minimum valid repair**,
not merely an acceptable one (§7 below).

---

## 7. Candidate Repair Reassessment (Independent)

Reassessed independently, against the ten axes named in the governing
prompt, before re-reading Phase 147E.1's own comparison table.

**Candidate A — Add `citation_text` to `EligibleAuthorityDeclaration`.**
Independently rejected on the same decisive ground Phase 147E.1's report
identifies: AEM-REQ-007 closes the Declaration to exactly six fields,
"No other field is defined for v1.0," and AEMIC-001's own Contract
identity section forbids reading AEMIC-001 as amending AEM-001. This is a
**foreclosure**, not merely a design-quality objection — independently
confirmed by direct re-reading of AEM-REQ-007's own text, not merely
Phase 147E.1's characterization of it. Independently, this phase also
confirms the semantic-mismatch objection: a Declaration is authored once
per `(template_ref, template_version)` and reused across every future
`ineligible` evaluation against it, so a `citation_text` field would sit
present-but-irrelevant on the overwhelmingly more common non-`eligible`
path, undermining exactly the "mechanically obvious from the outcome's
own shape" property AEMIC-REQ-022 exists to provide.

**Candidate B — Add `citation_text` to `evaluate()`.** Independently
assessed as satisfying all five minimum-interface criteria (§6). On
purity: `citation_text` carries no evaluative weight, confirmed by direct
re-reading of AEMIC-REQ-101 item 1 ("`citation_text` parameter plays no
role in this determination"), not merely by trusting the requirement's
own self-description — independently traced through AEMIC-REQ-101's own
four-step enforcement algorithm (§9 below) and confirmed the claim holds
mechanically, not just rhetorically. On declaration-shape constraints:
zero impact, `EligibleAuthorityDeclaration` is untouched (AEMIC-REQ-015/016
byte-identical to v1.0, independently confirmed at §8). On API clarity:
a fifth optional parameter, consistent with the existing precedent that
`evaluated_at`/`evaluator_version` are already non-evidentiary pass-through
parameters beyond AEM-REQ-016's own two — independently verified this
precedent genuinely exists in v1.0 (AEM-REQ-018's own field list already
included both before this repair), so Candidate B is not introducing a
new *kind* of parameter, only a new *instance* of an already-accepted
pattern. On citation provenance: unchanged in either direction (§10, §17
below). On single-enforcement-point discipline: preserved — `evaluate()`
remains the sole specified construction path. On Registry abstraction:
zero impact — `evaluate()` has no Registry dependency (AEMIC-REQ-073,
independently reconfirmed unchanged) so a citation-only parameter cannot
touch it. On future integration: zero impact — §17's deferred-integration
boundary (AEMIC-REQ-083-086) does not reference `citation_text` at all.
On testability: directly testable via the existing typed-error pattern
(a fifth named exception slots into the existing table). **Independently
confirmed: uniquely required**, not merely acceptable, once Candidate A
is foreclosed and Candidate C is assessed below.

**Candidate C — Require Registry resolution to return citation text
separately** (e.g., `resolve()` returning a `(Declaration, citation_text)`
tuple, or a widened return type). Independently assessed and rejected:
this would require changing `AuthorityRegistry.resolve`'s own frozen
signature (AEMIC-REQ-042, `resolve(template_ref, template_version) ->
EligibleAuthorityDeclaration | None`), a requirement neither BF-147F-1 nor
its repair touches in the actual v1.1 diff (§8) — and is architecturally
backwards regardless: citation text is sourced from the Decision
Template's own `eligible_authority` schema field (AEMIC-REQ-030), not
from the Authority Registry, which resolves `EligibleAuthorityDeclaration`
objects, a structurally distinct artifact with no `citation_text` field
of its own (§9 below). Widening `resolve()`'s return shape to carry
citation text would conflate two independently-sourced values into one
Registry call, and would also fail purity: `resolve()` is required to be
a pure function of `(template_ref, template_version)` alone
(AEMIC-REQ-043); citation text's own source (the Decision Template
schema, not the Registry's own backing store) is a different data source
entirely, so folding it into `resolve()`'s return would either require
the Registry to also depend on Decision Template storage (a new,
undisclosed coupling) or silently return a value from a source `resolve()`
never touches (a purity violation in spirit). **Rejected, independently,
on stronger architectural grounds than merely "not selected."**

**Candidate D — Provide a resolved Decision Template or immutable
citation-source object to `evaluate()`.** Independently rejected as
introducing a sixth public type (`DecisionTemplate` or an equivalent
citation-source wrapper) that does not exist anywhere in this repository
today (confirmed independently at §4, matching Phase 147D §2.4's and
Phase 147F's own confirmed non-existence) and that AEM-001 itself never
authorizes AEMIC-001 to invent (AEM-001 §2.2 scopes Decision Template
authoring/storage/versioning as out of scope beyond the minimal shape
needed to reference a Declaration deterministically, §4). Introducing a
new domain type to carry a single `str` value the fifth-parameter
approach already carries with zero new types is a strictly larger surface
area for identical effect — independently reaching the same conclusion
Phase 147E.1's own Candidate 3 analysis reaches by a different but
convergent argument (that report frames the rejection around
"single-construction-path" fragmentation; this phase's independent
framing is "unauthorized new public type" — both are independently valid,
non-overlapping objections to the same rejected candidate).

**Candidate E — Move eligible-outcome construction outside `evaluate()`**
(a second function, `construct_eligible_outcome(...)`, taking
`citation_text` directly). Independently assessed as strictly worse than
Candidate B for equal-or-greater cost, on the identical single-
enforcement-point ground Phase 147E.1's own Candidate 3 analysis
reaches — independently re-derived here, not merely copied: fragmenting
"the sole specified construction path" property is precisely the
property whose absence made BF-147F-1's *security* consequence (§18
below) severe in the first place (an attacker/careless-implementer
choosing which of two legitimate paths to use, rather than being forced
through one path with one invariant-enforcement point). This
independently confirms Phase 147E.1's own reasoning was not merely
asserted but is architecturally sound.

**Independent conclusion:** Candidate B (the selected repair) is
**uniquely required**, not merely superior, once Candidate A is correctly
recognized as foreclosed (not just inferior) and Candidates C–E are
independently rejected on their own distinct grounds. This phase's own
independent reassessment reaches the identical selection Phase 147E.1
reached, by partially overlapping and partially independent reasoning,
strengthening confidence the selection is architecturally sound rather
than merely asserted.

---

## 8. Exact Repair Diff Verification

Direct line-by-line comparison of every requirement Phase 147E.1's own
§7 claims was touched, against AEMIC-001 v1.1's actual current text:

| Requirement | Claimed change (147E.1 §7) | Independently verified against current text |
|---|---|---|
| AEMIC-REQ-019 | Parameter table widened 4→5 rows | **Confirmed** — current table (§5) has exactly 5 rows: `claimed_identity`, `declaration`, `evaluated_at`, `evaluator_version`, `citation_text` |
| AEMIC-REQ-020 | Reworded for 5 parameters, non-evidentiary distinction | **Confirmed** — current text explicitly states `evaluation_result` "remains a pure function of exactly the two evidentiary inputs AEM-REQ-016 names... unchanged by this parameter's addition" |
| AEMIC-REQ-031 | Rewritten to remove self-contradiction | **Confirmed** — current text reads "`evaluate` SHALL copy `citation_text` verbatim," not "Declarations SHALL copy," and explicitly states `EligibleAuthorityDeclaration` "does NOT carry a `citation_text` field in v1.0, and this repair does not add one" |
| AEMIC-REQ-032 | One-clause edit ("indirectly" → "directly as evaluate's own fifth parameter") | **Confirmed** — current text reads "how `evaluate`'s caller obtains the Decision Template's `eligible_authority` citation text at the moment it constructs the `evaluate()` call," consistent with the direct-parameter framing |
| AEMIC-REQ-033 | Same edit | **Confirmed** — "this package receives `citation_text` directly as `evaluate`'s own fifth parameter" |
| AEMIC-REQ-064 | New `MissingCitationTextError` row | **Confirmed** — present, condition "`evaluate`'s own internally-computed `evaluation_result` is `ELIGIBLE` but the caller-supplied `citation_text` parameter... is `None`" |
| AEMIC-REQ-065 | New sentence on non-eligible-path non-raising | **Confirmed** — "A non-`None` `citation_text` supplied alongside an `INELIGIBLE` or `INDETERMINATE` result is not a raising condition either (AEMIC-REQ-101)" |
| AEMIC-REQ-072 | Signature widened to 5 parameters | **Confirmed** — code block shows exactly 5 parameters with `citation_text: str | None = None` |
| AEMIC-REQ-074 | New sentence classifying missing-citation as malformed input | **Confirmed** — "a `citation_text` that is `None` when `evaluate`'s own internal determination of `evaluation_result` is `ELIGIBLE` is classified as malformed input" |
| AEMIC-REQ-075 | Determinism tuple extended | **Confirmed** — "identical `(claimed_identity, declaration, evaluated_at, evaluator_version, citation_text)` inputs SHALL always produce a field-identical `AuthorityEvaluationOutcome`" |
| AEMIC-REQ-077 | "four" → "five" named exceptions | **Confirmed** — "`evaluate`'s exception boundary is exactly §13.1's five named exceptions" |
| AEMIC-REQ-095 | First bullet corrected | **Confirmed** — records the v1.0 falsification and its repair in the same bullet |
| AEMIC-REQ-101 | New requirement | **Confirmed present**, §14.1, four-step enforcement algorithm |
| AEMIC-REQ-102 | New requirement | **Confirmed present**, §15, security-disposition statement |
| §22 matrix | Three rows updated | **Confirmed** — rows for AEMIC-REQ-021-023, AEMIC-REQ-072-077/101, AEMIC-REQ-064-071/101 all reference the repaired behavior |
| §23 disposition | Three rows added | **Confirmed** — BF-147F-1 (Repaired), F-147F-2, F-147F-3 all present with disposition text |

**Requirement-identifier hygiene, independently verified:** grepped every
`AEMIC-REQ-\d+` occurrence in the current document; identifiers run
`AEMIC-REQ-001` through `AEMIC-REQ-102` with no gap and no reuse (the
jump from `AEMIC-REQ-095` to `AEMIC-REQ-101` at the numbering level is
explained by the document's own numbering convention — §14.1 and §15's
new requirements were appended after the original `AEMIC-REQ-100`
Finding-Disposition capstone requirement, matching the document's own
"sequential... grouped by the section that introduces them" rule applied
to a mid-document insertion, not a gap). No requirement outside the
fourteen rows above differs from v1.0 in any way this phase could detect
by direct re-reading of every section 1–24 (spot-checked in full at §10
below for the sections most likely to carry a silent side effect: §4,
§6, §7, §11, §13.2, §17, §19, §24 — all confirmed byte-identical in
substance to the account given in both predecessor reports).

**No unrelated requirement was altered. No requirement identifier was
reused. No accidental semantic widening was found** — the five-parameter
signature is the only expansion, and it is confirmed non-evidentiary
(§6, §9 below).

---

## 9. Five-Parameter Evaluator Contract Verification

Exact frozen signature (AEMIC-REQ-072):

```
evaluate(
    claimed_identity: str,
    declaration: EligibleAuthorityDeclaration | None,
    evaluated_at: str,
    evaluator_version: str,
    citation_text: str | None = None,
) -> AuthorityEvaluationOutcome
```

- **Parameter order:** fixed as above; `citation_text` is last, with a
  default, preserving positional-call compatibility with any
  hypothetical pre-repair four-argument caller (though none exists in
  practice, per AEMIC-REQ-004/094's confirmed absence of any
  implementation).
- **Types:** `str` for four params; `EligibleAuthorityDeclaration | None`
  for `declaration`; `str | None` for `citation_text`. All closed,
  unambiguous.
- **Optionality:** only `citation_text` has a default (`None`); the other
  four are mandatory, matching AEMIC-REQ-019's table exactly.
- **Nullability:** `declaration` and `citation_text` are the only
  nullable parameters; independently confirmed this matches the two
  places AEM-001 itself contemplates absence (`declaration` absence =
  "no Declaration exists," AEM-REQ-010; `citation_text` absence = the
  "eligible without citation" failure condition this repair introduces).
- **Normalization/empty-string/whitespace-only behavior for `citation_text`:**
  AEMIC-REQ-033 (unchanged in substance by this repair) requires exact
  text equality, no normalization, no trimming — `citation_text` is
  carried byte-for-byte. An empty string (`""`) is **not** the same as
  `None`: `AEMIC-REQ-101` tests only for `citation_text is None`
  (§14.1 item 2), so a caller supplying `citation_text=""` on an
  `eligible`-yielding call would **not** trigger `MissingCitationTextError`
  and would produce an outcome with `citation_text=""` — non-`None`, so
  it passes AEMIC-REQ-022's own if-and-only-if check (`citation_text is
  not None` is satisfied by `""`). **This is a genuine, narrow gap**: an
  empty-string citation is contractually indistinguishable from a
  missing one in every practical sense (an empty citation discloses
  nothing), yet the contract's own construction-time invariant (AEMIC-REQ-022)
  and its own enforcement mechanism (AEMIC-REQ-101) both treat it as a
  valid, non-`None` citation. This is assessed at §22 as Non-Blocking:
  it fails in the direction of producing a *disclosed, inspectable* empty
  string (never a fabricated non-empty claim), consistent with this
  contract's own fail-closed discipline in spirit (an empty citation is
  trivially recognizable as vacuous by any consumer, unlike a plausible
  but false one), and is unrelated to BF-147F-1 or its repair — a
  pre-existing gap in AEMIC-REQ-033's own "no normalization" text, not
  introduced by this repair. Newly disclosed at §22 as **F-147F.1-2**.
- **Unicode behavior:** unrestricted (AEMIC-REQ-090, unchanged),
  round-tripped byte-for-byte; `citation_text` is explicitly named as
  Unicode-eligible at AEMIC-REQ-090's own text ("carried via
  `AuthorityEvaluationOutcome`, not stored on `EligibleAuthorityDeclaration`
  itself per AEMIC-REQ-031").
- **Deterministic use:** confirmed — AEMIC-REQ-075's tuple now explicitly
  includes `citation_text`, so two calls differing only in `citation_text`
  are contractually permitted to (and, given different `citation_text`
  values, will) produce different outcomes; two calls with identical
  five-tuples are required to produce field-identical outcomes.
- **Accepted in non-eligible paths:** yes, accepted (not rejected) but
  disregarded — AEMIC-REQ-101 item 4 explicitly states a non-`None`
  value supplied alongside `INELIGIBLE`/`INDETERMINATE` is "disregarded,
  not fabricated into the outcome and not treated as caller error."
  Independently attacked whether "disregarded" is itself ambiguous
  (logged? silently dropped? raises a warning?) — the contract's own
  text specifies exactly one observable behavior: "SHALL construct the
  outcome with `citation_text=None` regardless of what value... the
  caller supplied." This is unambiguous at the observable-behavior level
  (the constructed outcome always has `citation_text=None` for these two
  results), even though it does not specify whether an implementation
  MAY additionally log the disregarded value — a harmless implementation
  freedom, not a contract ambiguity (the outcome's own shape is fully
  determined regardless).
- **Unused caller input rejected?** No — by design, per the above; this
  is a deliberate, stated, minimal-repair-scope choice (§25 of AEMIC-001,
  "raising on that direction is not necessary to repair BF-147F-1"),
  independently assessed as reasonable: rejecting would add a new raising
  condition on the two paths AEM-REQ-024 requires to always succeed,
  which would be a narrowing of AEM-REQ-024's own existing guarantee —
  correctly avoided.

**Closed-signature completeness:** with the one caveat named above
(empty-string vs. `None` citation, F-147F.1-2, Non-Blocking) and the
distinct, more serious `template_ref`/`template_version` gap named at
§20 (BF-147F.1-1, Blocking), the five-parameter signature does not
otherwise leave material behavior to implementation discretion for the
`citation_text` channel specifically — the citation-plumbing repair
itself (BF-147F-1) is complete and correctly closed.

---

## 10. AEMIC-REQ-022 and AEMIC-REQ-101 Joint Semantics

Independently verified as a complete if-and-only-if invariant, against
the required behavior table:

| Evaluation state | `citation_text` input | Required behavior | Independently verified |
|---|---|---|---|
| eligible | valid non-empty citation | eligible outcome carrying exact citation | **Confirmed** — AEMIC-REQ-101 item 3 |
| eligible | absent (`None`) | `MissingCitationTextError` | **Confirmed** — AEMIC-REQ-101 item 2 |
| eligible | empty (`""`) | contract does not distinguish from valid — **not rejected** | **Gap, Non-Blocking** — F-147F.1-2 (§9, §22) |
| eligible | whitespace-only | not normalized, treated as a valid non-`None` string (AEMIC-REQ-033: exact equality, no trimming) | **Consistent, by design** — matches the "no normalization anywhere in this package" discipline; a whitespace-only citation is disclosed verbatim, not silently trimmed |
| eligible | malformed type (non-`str`) | not explicitly named as a raising condition distinct from "absent"; Python type-checking would reject at the language boundary for a statically-typed caller, but this contract does not itself specify a runtime `isinstance` check | **Minor gap, Non-Blocking** — consistent with this package's own general "no runtime type-checking beyond what's stated" pattern (e.g. `InvalidClaimedIdentityError`'s own condition names "empty or not a `str`" explicitly, but no equivalent explicit "not a `str`" clause exists for `citation_text` at AEMIC-REQ-064's `MissingCitationTextError` row) — newly disclosed at §22 as **F-147F.1-3** |
| non-eligible | absent | non-eligible outcome without citation | **Confirmed** — AEMIC-REQ-101 item 4 |
| non-eligible | supplied | disregarded, outcome carries `citation_text=None` | **Confirmed** — AEMIC-REQ-101 item 4, AEMIC-REQ-065 |
| Registry error | supplied | infrastructure failure remains authoritative | **Confirmed** — `evaluate()` never touches the Registry (AEMIC-REQ-073); a Registry error can only occur in `resolve()`, before `evaluate()` is ever called, so it cannot be masked by anything `citation_text`-related |
| invalid declaration | supplied | declaration failure remains authoritative | **Confirmed** — declaration structural validity is enforced at `EligibleAuthorityDeclaration` construction time (AEMIC-REQ-017), upstream of any call to `evaluate()`; a malformed declaration cannot reach `evaluate()` in the first place under normal construction discipline |

**Ordering/precedence, independently verified:** AEMIC-REQ-101 item 1
determines `evaluation_result` first, "from exactly the two evidentiary
inputs," with `citation_text` "play[ing] no role in this determination" —
confirmed this ordering cannot let a supplied `citation_text` mask or
pre-empt the `evaluation_result` determination itself, closing the
"early citation validation could mask [other failure]" attack named in
the governing prompt's §12: citation-related raising (item 2) only ever
occurs *after* `evaluation_result` is already fixed to `ELIGIBLE`, so it
can never substitute for or occur instead of a determination that should
have been `INELIGIBLE`/`INDETERMINATE`.

**No eligible outcome can omit citation:** confirmed, by construction
(AEMIC-REQ-101 item 2 raises before any such outcome could be
constructed). **No non-eligible outcome can carry citation unless
explicitly allowed:** confirmed — non-eligible outcomes always carry
`citation_text=None`, never anything else (AEMIC-REQ-101 item 4).
**Supplied citation cannot override an earlier failure:** confirmed — a
`declaration` failure (raised at construction, before `evaluate()` is
ever reached) or a Registry failure (raised in `resolve()`, before
`evaluate()` is ever called) both occur strictly before `citation_text`
is ever examined.

**Every branch of this table is resolved except the two narrow,
Non-Blocking gaps named above (F-147F.1-2, F-147F.1-3).** The invariant
itself is complete, sound, and — critically, the specific property
BF-147F-1 falsified — now **satisfiable and satisfied** by its own sole
construction path.

---

## 11. Citation Provenance and Fabrication Review

- **Who is contractually allowed to supply `citation_text`?** Any caller
  of `evaluate()` — the contract names no access-control layer over the
  function itself (consistent with AEM-001's own zero-enforcement
  design, §16 of AEM-001).
- **What source must that caller use?** AEMIC-REQ-030: "the sole
  citation-text source" is `decision_template.schema.json`'s
  `eligible_authority` field, verbatim.
- **Is exact verbatim copying required?** Yes, at the point the caller
  *sources* the value from the schema field (AEMIC-REQ-030/033) and
  again at the point `evaluate()` *carries* it into the outcome
  (AEMIC-REQ-031, "copy... verbatim... at evaluation time" — now
  correctly grammatically attributed to `evaluate`, not "Declarations,"
  confirmed at §8).
- **Can the evaluator verify provenance?** No — independently confirmed:
  `evaluate()` has no Registry dependency (AEMIC-REQ-073) and no
  dependency on `pcae.schema_resources` (AEMIC-REQ-011), so it has no
  mechanism to check the supplied `citation_text` against the Decision
  Template's own schema field at all. This is the same disclosed,
  unclosed gap AEMIC-REQ-032 names ("there is no `DecisionTemplate`
  Python artifact today"), independently reconfirmed unchanged by this
  repair.
- **Does the evaluator merely enforce shape?** Yes — confirmed: the only
  check performed on `citation_text` is presence/absence (`is None`),
  never content validation, format validation, or cross-reference
  against any external source.
- **Can a malicious or defective caller supply arbitrary text?** Yes,
  unconditionally — nothing in `evaluate()`'s own logic, or anywhere
  else in AEMIC-001, checks `citation_text`'s content against anything.
- **Would such text create a contract-valid eligible outcome?** Yes — an
  arbitrary, non-empty string satisfies AEMIC-REQ-022's own structural
  invariant.
- **Do AEMIC-REQ-032/033 explicitly disclose and bound that limitation?**
  Yes — independently confirmed both requirements name this exact
  limitation by name, not merely by implication, and AEMIC-REQ-102
  (new in this repair) explicitly re-confirms it is "not newly introduced
  or worsened" by the repair.
- **Does AEMIC-REQ-102 adequately prevent the outcome from becoming an
  authority grant?** Independently verified: yes, for the reason AEM-001
  §10 already establishes at one layer up — "no enforcement surface
  exists to attack" (AEM-REQ-003), so even a fabricated `citation_text`
  cannot itself authorize, gate, or grant anything; its worst-case
  consequence is a misleading *disclosure*, never an unauthorized
  *action* (AEM-001 §10's own risk framing, independently re-confirmed
  applicable here by direct comparison: nothing about `citation_text`'s
  addition changes AEM-001's own "worst case is misleading disclosure"
  analysis, since `citation_text` was already going to be part of the
  outcome's shape at the AEM-001 level, AEM-REQ-018, before this
  contract or its repair existed).

**Structural correctness vs. provenance vs. semantic truth vs.
authorization meaning — independently distinguished, per the governing
prompt's own instruction:** `evaluate()` verifies (1) structural
correctness only (is `citation_text` non-`None` when required). It does
**not** verify (2) source provenance (whether the value actually came
from the named schema field), (3) semantic truth (whether the text
correctly describes the actual eligible authority), or (4) authorization
meaning (whether citing this text should permit anything) — and
critically, **AEM-001 itself never requires this package to verify (2),
(3), or (4)**: AEM-REQ-003 forbids this contract family from
constituting an enforcement mechanism at all, so a package that verified
semantic truth or authorization meaning would be *exceeding* its
authorized scope, not merely under-delivering. The absence of (2)–(4) is
therefore correctly disclosed as a limitation, not silently mistaken for
provenance validation anywhere in the contract's own text.

**No new fabrication risk is introduced by this repair.** The risk
predates it (AEMIC-REQ-032/033 already named it in v1.0) and is
unchanged in kind or degree, independently confirmed.

---

## 12. Direct Outcome Construction Review

Independently attacked, per the governing prompt's §10: can
`AuthorityEvaluationOutcome` be constructed directly, bypassing
`evaluate()`, with arbitrary `citation_text`?

- **Are constructors public?** `AuthorityEvaluationOutcome` is specified
  as "an immutable record" (a frozen dataclass or equivalent,
  AEMIC-REQ-018's sibling requirement AEMIC-REQ-023 restates immutability
  for the outcome type) — nothing in AEMIC-001 states its constructor is
  private, hidden, or otherwise access-restricted. **Constructors are, by
  default and by the absence of any stated restriction, public.**
- **Are construction invariants enforced in the model?** Yes —
  AEMIC-REQ-022 explicitly states the if-and-only-if invariant is
  "checked at construction time, not left to caller discipline," meaning
  `AuthorityEvaluationOutcome.__init__` (or equivalent) itself performs
  the check, independent of whether the call originates from `evaluate()`
  or from direct, caller-side construction.
- **Can eligible outcomes be instantiated directly with arbitrary
  citation text?** Yes — a direct call to
  `AuthorityEvaluationOutcome(template_ref=..., template_version=...,
  claimed_identity=..., evaluation_result=EvaluationResult.ELIGIBLE,
  declaration_ref=..., citation_text="anything", evaluated_at=...,
  evaluator_version=..., schema_version="aem-outcome/1.0")` satisfies
  AEMIC-REQ-022's own structural invariant (`citation_text` is
  non-`None`, `evaluation_result` is `ELIGIBLE`) without ever calling
  `evaluate()`, without any Registry lookup, and without any check that
  `claimed_identity` is actually a member of any Declaration's
  `eligible_identities` set.
- **Is `evaluate()` the only authorized construction path?** Narrative
  language throughout AEMIC-001 (e.g. AEMIC-REQ-072's framing, and Phase
  147E.1's own §2 Step 3(a): "no other construction path is specified
  anywhere in AEMIC-001 v1.0") treats `evaluate()` as *the* specified
  path. But **no binding requirement anywhere in AEMIC-001 v1.1 states
  that direct construction is forbidden, or that consumers MUST treat a
  directly-constructed instance as untrusted or non-authoritative.**
  This is a real gap between the contract's own narrative framing
  ("the sole specified construction path") and its actual normative
  text (no `SHALL NOT construct `AuthorityEvaluationOutcome` directly`
  requirement exists).
- **Can serialization deserialize fabricated outcomes?** Yes —
  `from_payload` (AEMIC-REQ-087) round-trips any structurally valid
  payload, including one whose `citation_text` was fabricated by direct
  construction and never touched `evaluate()`. `from_payload` verifies
  `schema_version` and field presence (AEMIC-REQ-091/093), not
  provenance.
- **Are consumers required to validate provenance?** No — AEMIC-001
  defines no provenance-marking mechanism (e.g. a "was this produced by
  `evaluate()`" flag) anywhere on `AuthorityEvaluationOutcome`'s own
  eight-field shape.
- **Does the contract explicitly distinguish valid shape from trusted
  evaluation evidence?** No — this is exactly the gap: AEMIC-REQ-022's
  own invariant establishes valid *shape* (an `eligible` outcome must
  carry a citation) but nothing establishes that a shape-valid instance
  is *evidence of an actual evaluation having occurred* as opposed to a
  hand-constructed value object asserting the same shape.

**Classification, per the governing prompt's own taxonomy (§10):**
independently assessed as **Informational**, not Blocking, for the
following reason, directly paralleling AEM-001 §10's own reasoning
(already applied to this exact question by AEM-001 at one layer up, and
independently re-confirmed applicable here rather than merely assumed):
`AuthorityEvaluationOutcome` is "ordinary immutable value-object
construction," and it is **non-authoritative** by design — AEM-REQ-003's
"no enforcement surface exists to attack" analysis applies identically
whether the outcome was produced by `evaluate()` or by direct
construction, because nothing downstream *within this package's own
scope* treats an `AuthorityEvaluationOutcome` as self-authenticating; any
future consumer (PEC-001/CHGR-001, per the deferred integration boundary,
§17) that chose to trust a bare `AuthorityEvaluationOutcome` without
independently verifying its own provenance (e.g. by requiring it arrive
through a specific, governed channel, as AEMIC-REQ-083-085 already
requires for any future integration) would itself be responsible for
that trust decision — a decision this contract's own §17 boundary
explicitly defers, not one AEMIC-001 silently makes on that future
consumer's behalf. This is **not a binding single-construction-path
requirement being violated** (none exists to violate); it is the
ordinary, expected behavior of an immutable dataclass whose own
construction-time invariant enforces internal shape consistency but was
never intended, at the AEM-001 level, to also enforce *external
authenticity*, a job AEM-001 §10 already assigns to "the worst-case
consequence... is a misleading disclosure, not an unauthorized action."

**Recommendation (non-binding, disclosed, not a repair authorized by
this phase):** a future revision could usefully add an explicit
requirement — "consumers integrating `AuthorityEvaluationOutcome` per
§17's deferred integration boundary SHOULD treat an instance's
provenance (was it produced by `evaluate()`) as their own responsibility
to establish, since this package provides no such marker" — closing the
narrative/normative gap named above. This is named as an observation, not
elevated to Blocking, because AEM-001 §10's own reasoning independently
supports the current design as safe under this contract's own disclosure-
only scope.

---

## 13. `MissingCitationTextError` Verification

- **Exact trigger condition:** `evaluate`'s internally-determined
  `evaluation_result == ELIGIBLE` and the caller-supplied `citation_text`
  parameter `is None` (AEMIC-REQ-064, AEMIC-REQ-101 item 2). Precise and
  unambiguous.
- **Stable error code:** the class name itself (`MissingCitationTextError`)
  — consistent with every other exception in this taxonomy (no separate
  numeric/string error-code field is defined anywhere in AEMIC-001 for
  any exception, so this is consistent, not a new gap).
- **Public exception type:** yes — listed in AEMIC-REQ-064's own table
  alongside the four pre-existing domain exceptions, and re-exported per
  AEMIC-REQ-014 ("the exception hierarchy's public names").
- **Inheritance:** a direct subclass of `AuthorityEvaluationError`
  (AEMIC-REQ-064's own table header: "SHALL define a base
  `AuthorityEvaluationError` and, as its own direct subclasses, at
  minimum" — `MissingCitationTextError` is listed as one of the five).
- **Domain vs. infrastructure classification:** explicitly "Domain
  (caller error)" — correctly classified, since the condition originates
  entirely from what the caller supplied, never from a storage/Registry
  fault.
- **Retryability:** "No" — correct; retrying with the identical
  `citation_text=None` would deterministically raise again (AEMIC-REQ-075's
  determinism guarantee applies here too).
- **Serialization/reporting expectations:** none stated beyond what
  applies to every other exception in this taxonomy (AEMIC-REQ-071:
  mapped at a future CLI/transport surface to that surface's own closed
  taxonomy, never a new vocabulary this package invents) — consistent,
  not a gap unique to this exception.
- **Message requirements:** none stated — consistent with the other four
  §13.1 exceptions, none of which specify a mandated message string
  either; this is a pre-existing, uniform pattern, not a new omission.
- **Confusion with declaration absence:** independently checked —
  `MissingCitationTextError` fires only when `evaluation_result ==
  ELIGIBLE` (a resolved Declaration whose member matched); declaration
  absence produces `INDETERMINATE`, a successful, non-raising result
  (AEMIC-REQ-065). The two conditions are mutually exclusive by
  construction (one requires a Declaration to have resolved and matched;
  the other requires no Declaration to have resolved at all) — **no
  confusion possible**.
- **Confusion with Registry unavailability:** independently checked —
  `evaluate()` never touches the Registry (AEMIC-REQ-073), so
  `MissingCitationTextError` can never be conflated with
  `AuthorityRegistryUnavailableError`, which only a concrete Registry's
  own `resolve()` implementation raises, strictly before `evaluate()` is
  ever invoked. **No confusion possible.**
- **Can it be thrown in non-eligible cases?** No — confirmed by
  AEMIC-REQ-101 item 4's own text: non-eligible cases never raise on
  account of `citation_text`, regardless of what was supplied.

**Six-exception taxonomy consistency:** independently counted —
`AuthorityEvaluationError` (base) plus five §13.1 domain subclasses
(`InvalidClaimedIdentityError`, `InvalidTemplateReferenceError`,
`MalformedDeclarationError`, `UnsupportedSchemaVersionError`,
`MissingCitationTextError`) plus two §13.2 infrastructure subclasses
(`AuthorityRegistryUnavailableError`, `AuthorityRegistryCorruptError`) =
eight total named types (base + five + two), consistent with
AEMIC-REQ-077's own updated "five" count for §13.1 alone (the base class
and the two §13.2 types are counted separately, per AEMIC-REQ-067's own
explicit domain/infrastructure split) — **no miscounted or
inconsistent enumeration found anywhere in the document.**

**No defect found in `MissingCitationTextError` itself.**

---

## 14. Evaluation Ordering

Independently frozen and verified logical order of operations inside
`evaluate()`, per AEMIC-REQ-101's own four-step algorithm, cross-checked
against every other requirement bearing on ordering:

1. Determine `evaluation_result` from `(claimed_identity, declaration)`
   alone (AEMIC-REQ-101 item 1) — this is necessarily first, since every
   subsequent step depends on knowing which of the three results applies.
2. If `ELIGIBLE` and `citation_text is None`: raise
   `MissingCitationTextError` (item 2) — before any outcome object is
   constructed.
3. If `ELIGIBLE` and `citation_text is not None`: construct the outcome
   carrying it verbatim (item 3).
4. If `INELIGIBLE`/`INDETERMINATE`: construct the outcome with
   `citation_text=None` unconditionally (item 4).

**Attacked whether an alternate order is permitted:** the contract's own
text does not explicitly forbid an implementation from, e.g., validating
`citation_text`'s presence *before* determining `evaluation_result` —
but any such reordering would be **observably indistinguishable** from
the specified order for well-formed inputs (since the citation check
only has an externally visible effect — raising — when
`evaluation_result` is already `ELIGIBLE`, computing that first or
deferring its computation produces the same final raise-or-construct
decision either way, given `evaluate()`'s own total/pure/single-call
nature with no intervening state). **No implementation-critical
ambiguity found in ordering itself.**

**Attacked whether early citation validation could mask upstream
failures**, per the governing prompt's own instruction:

- **Registry unavailability:** cannot be masked — occurs in `resolve()`,
  strictly before `evaluate()` is ever called (AEMIC-REQ-073). Confirmed
  structurally impossible for `citation_text` handling to interact with
  this failure mode at all.
- **Declaration corruption:** the same — `MalformedDeclarationError`
  fires at `EligibleAuthorityDeclaration` construction (AEMIC-REQ-017),
  upstream of any `evaluate()` call receiving that declaration.
- **Duplicate ambiguity:** occurs in a concrete Registry's own `resolve()`
  (`AuthorityRegistryCorruptError`, AEMIC-REQ-045/048), strictly upstream
  of `evaluate()`.
- **Version mismatch:** `template_version` is part of the
  `(template_ref, template_version)` tuple used by `resolve()`
  (AEMIC-REQ-042) to select (or fail to select) a Declaration —
  upstream of `evaluate()` entirely; `evaluate()` itself, per §20 below,
  does not even receive `template_ref`/`template_version` as distinct
  parameters, reinforcing (from a different angle) that version-mismatch
  handling cannot occur inside `evaluate()`'s own citation-handling logic
  at all.
- **Invalid request:** `claimed_identity` validation
  (`InvalidClaimedIdentityError`) is not explicitly ordered relative to
  the `citation_text` check by AEMIC-REQ-101's own four-step text (which
  begins from "the resulting `evaluation_result`," implicitly assuming
  `claimed_identity` and `declaration` were already validated). This is
  a minor textual gap — the contract does not explicitly state
  "`claimed_identity`/`declaration` structural validation occurs before
  `evaluation_result` determination, which occurs before the
  `citation_text` check" as a single ordered chain — but it is not
  implementation-critical: no combination of validation orderings
  produces a different externally observable result, since `evaluate()`
  is required to raise (not silently succeed) on any structural
  violation regardless of order (AEMIC-REQ-064's five conditions are
  each independently sufficient to raise their own named exception
  whenever encountered), and no two of the five conditions can both
  apply to the same well-formed-vs-malformed input simultaneously in a
  way that would produce different outcomes under different check
  orders. **Non-Blocking, not independently named as a new finding**
  (this is a documentation-completeness observation, not a defect with a
  distinguishable adversarial consequence).

**Same inputs and Registry state always yield the same public result or
exception:** confirmed, independently, via AEMIC-REQ-075's determinism
guarantee (extended to include `citation_text`) combined with
`resolve()`'s own independently-required purity (AEMIC-REQ-043).

---

## 15. Determinism

AEMIC-REQ-075 (repaired): "identical `(claimed_identity, declaration,
evaluated_at, evaluator_version, citation_text)` inputs SHALL always
produce a field-identical `AuthorityEvaluationOutcome`."

- **Identical tuple → identical result:** confirmed, by direct
  requirement text.
- **Citation differences are materially reflected:** confirmed — two
  calls differing only in `citation_text` (both otherwise identical,
  both yielding `ELIGIBLE`) produce outcomes differing exactly in their
  own `citation_text` field, nothing else — independently traced through
  AEMIC-REQ-101's own algorithm, which never lets `citation_text`
  influence `evaluation_result`, `declaration_ref`, or any other field.
- **Observational fields do not affect semantic equality:** `evaluated_at`
  is explicitly named as the sole "observational" field (AEMIC-REQ-080,
  unchanged by this repair) — two calls differing only in `evaluated_at`
  are both independently valid, correct outcomes, not a determinism
  violation (AEMIC-REQ-080's own text: "not itself part of the
  determinism guarantee AEMIC-REQ-075 requires, since a caller supplies
  it per-call"). Independently confirmed this framing is internally
  consistent even though `evaluated_at` is literally listed inside
  AEMIC-REQ-075's own determinism tuple: the tuple names it as an input
  whose *presence* participates in producing a field-identical output
  (same `evaluated_at` in → same `evaluated_at` out, trivially, since
  it's a verbatim copy), while AEMIC-REQ-080 separately clarifies it
  carries no independent *semantic* weight distinguishing "correct" from
  "incorrect" outcomes — these are two different, compatible claims
  ("verbatim-copied" vs. "not semantically load-bearing"), not a
  contradiction.
- **Timestamps do not alter deterministic identity:** confirmed, same
  reasoning.
- **Registry implementation details do not alter equivalent semantic
  results:** confirmed — `evaluate()` never touches the Registry at all
  (AEMIC-REQ-073); the `declaration` parameter is already a fully
  resolved value object by the time `evaluate()` sees it, so no Registry
  implementation detail (filesystem layout, storage backend) can leak
  into `evaluate()`'s own determinism.
- **Exception ordering is deterministic:** confirmed — every raising
  condition is a pure function of its own inputs (no randomness, no
  external state consulted inside `evaluate()`, per AEMIC-REQ-076's
  no-side-effects guarantee), so which exception (if any) is raised for
  a given input tuple is itself deterministic.

**Adding `citation_text` introduces no unstated source of
nondeterminism.** The determinism guarantee, independently re-derived
from AEM-REQ-009/012/016 (§6 above) and cross-checked against the actual
repaired text, holds completely for the citation-plumbing repair itself.
(The `template_ref`/`template_version`-sourcing gap named at §20 is a
*completeness*, not a *determinism*, defect — it does not make
`evaluate()` non-deterministic; it makes it, for one branch,
under-specified as to what value to use at all, which is a different
kind of defect classified separately at §20/§22.)

---

## 16. Serialization

Conceptually verified (no executable implementation exists to test
against; direct textual analysis per the governing prompt's own §23
allowance) against every listed case:

- **Eligible outcome with citation:** `to_payload` (AEMIC-REQ-087/088)
  emits all eight fields including a non-`None` `citation_text`;
  `from_payload` reconstructs it, verifying `schema_version` first
  (AEMIC-REQ-093).
- **Non-eligible outcome without citation:** `citation_text` field is
  present (all fields are mandatory, AEMIC-REQ-091 — "omitted" and
  "`null`" carry no distinguishing meaning) with value `null`/`None`.
- **Prohibited null citation (eligible case):** cannot arise from
  `evaluate()`'s own output (AEMIC-REQ-101 prevents constructing such an
  outcome in the first place) but **could** arise from a directly
  fabricated payload fed to `from_payload` — `from_payload` itself has
  no stated cross-field validation requirement enforcing AEMIC-REQ-022's
  invariant at deserialization time (it only checks `schema_version` and
  field presence/nullness per-field, per AEMIC-REQ-091/093). **This is a
  genuine, narrow gap**: a hand-crafted or corrupted payload with
  `evaluation_result: "eligible"` and `citation_text: null` would, as
  specified, pass `from_payload`'s own stated checks (every required
  field is present and non-`null` — wait, `citation_text` being `null`
  on an `eligible` payload violates "no required field is missing or
  `null`" only if `citation_text` is unconditionally required; but
  AEMIC-REQ-021 marks `citation_text` "Conditionally" mandatory, not
  unconditionally, so AEMIC-REQ-091's own blanket "every field... is
  mandatory... `from_payload` SHALL raise if any required field is
  missing or `null`" does not cleanly cover a *conditionally*-required
  field. This produces a real ambiguity: does `from_payload` reject a
  `null` `citation_text` on an `eligible` payload, or not?) — **this is
  an implementation-level ambiguity, independently newly discovered,
  distinct from BF-147F-1 and from BF-147F.1-1.** Named at §22 as
  **F-147F.1-4**, classified Non-Blocking (§22 gives the reasoning: it
  affects `from_payload`, a deserialization boundary explicitly deferred
  from strong verification since it operates on payloads this contract
  does not itself produce incorrectly — the risk surface is a corrupted
  or maliciously-crafted payload, not `evaluate()`'s own output, and the
  contract's own disclosure-only design means even an incorrectly
  deserialized `eligible` outcome without a real citation carries no
  enforcement consequence, restating AEM-001 §10's reasoning again).
- **Empty citation:** round-trips as an ordinary non-`None` string (§9's
  F-147F.1-2 gap applies here too, at the serialization boundary as well
  as the construction boundary — same root cause, not a new,
  independent defect).
- **Whitespace citation:** same, no special handling anywhere.
- **Unicode citation:** round-trips byte-for-byte (AEMIC-REQ-090,
  independently confirmed unchanged and explicitly still applicable to
  `citation_text` by name).
- **Round-trip serialization:** sound for every field this repair
  touches; `to_payload`/`from_payload`'s own general contract
  (AEMIC-REQ-087-093) is unchanged by this repair (not among the
  touched requirements per §8's diff verification).
- **Equality:** not explicitly specified anywhere in AEMIC-001 (no
  `__eq__`/dataclass-equality requirement is stated for either record
  type) — a pre-existing gap, unrelated to this repair, and consistent
  with ordinary Python frozen-dataclass semantics (field-wise equality
  by default) being sufficient without an explicit contract statement;
  not elevated to a finding since AEMIC-REQ-075's determinism language
  already implies field-wise comparison is the intended equality notion.
- **Hashing:** not required or discussed; `eligible_identities` is
  already a `frozenset` (hashable) per AEMIC-REQ-015, but neither record
  type's own hashability is specified — again, a pre-existing,
  unelevated gap, not introduced by this repair.
- **Omitted vs. null:** as discussed above, ambiguous specifically for
  *conditionally*-mandatory fields (`citation_text`, `declaration_ref`) —
  F-147F.1-4 (§22).

**No serialized record produced by `evaluate()` itself can represent a
state AEMIC-REQ-022/AEMIC-REQ-101 prohibit** (§9, §10 above) — the gap
found here is specifically about `from_payload`'s own defensive posture
against a payload this package did not itself produce, a narrower and
less severe concern than BF-147F-1 ever was.

---

## 17. Disclosure-Only Security Re-Verification

Independently re-attacked, given the new parameter:

- **`citation_text` is disclosed evidence only:** confirmed — nowhere in
  AEMIC-001 is `citation_text` treated as an input to `evaluation_result`'s
  own determination (§9, §10 above); AEMIC-REQ-020's own restated text
  makes this explicit specifically for the new parameter.
- **Cannot authorize publication:** confirmed — AEMIC-REQ-005/027/028
  (unchanged by this repair, confirmed at §8) foreclose any type or
  function in this package being named, shaped, or documented as an
  authorization primitive; `citation_text` is a `str` field on a
  disclosure-shaped record, not a capability token.
- **Cannot authorize execution:** confirmed — §3.4's forbidden-import
  boundary (AEMIC-REQ-010/012, unchanged) means this package cannot even
  *reach* Runtime/Permission Broker code, regardless of what
  `citation_text` contains.
- **Cannot alter runtime capability:** same reasoning.
- **Cannot change Registry state:** confirmed — the Registry ABC exposes
  no write method (AEMIC-REQ-042, unchanged); `evaluate()` never touches
  the Registry at all (AEMIC-REQ-073).
- **Cannot grant legal or organizational authority:** confirmed, restating
  AEM-001 §10's own analysis, independently re-applied here (§11 above).
- **Cannot bypass human governance:** confirmed — no code path from
  `citation_text` reaches any governance-decision surface (GAC-001,
  TAMC-001/TAMPC-001 remain entirely untouched, per §19 below).
- **Eligible outcome naming does not imply permission:** confirmed —
  `EvaluationResult.ELIGIBLE`'s own wire value (`"eligible"`) and every
  surrounding docstring requirement (AEMIC-REQ-027) forbid
  authorization-shaped naming; independently re-scanned every public
  name touched by this repair (`evaluate`, `citation_text`,
  `MissingCitationTextError`) and found none that could reasonably be
  read as implying authorization — `MissingCitationTextError`'s own name
  describes a data-completeness failure, not an authorization failure.
- **Absence or invalidity does not become a publication gate:** confirmed —
  AEMIC-REQ-005 (unchanged) forecloses this at the package level; this
  repair adds a new *domain* exception
  (`MissingCitationTextError`), but raising an exception from `evaluate()`
  is not the same as gating Publication — nothing in AEMIC-001 requires
  or implies that a future caller must treat a raised
  `MissingCitationTextError` as a Publication-blocking event; that
  remains entirely the deferred integration layer's own decision (§17
  of AEMIC-001, unaffected by this repair per AEMIC-REQ-083's own
  unchanged text).

**Holds. No weakening found.** The repair's own security review claim
(AEMIC-REQ-102) is independently confirmed accurate: caller-controlled
citation fabrication is unchanged in kind (§11 above), and disclosure-only
semantics are fully preserved.

---

## 18. AEM-001 Compatibility

Independently re-verified, requirement by requirement, that AEMIC-001
v1.1 remains within AEM-001's own bounds:

- **`EligibleAuthorityDeclaration` remains the exact frozen shape:**
  confirmed — AEMIC-REQ-015/016 are byte-identical to v1.0 per §8's diff
  verification; AEM-REQ-007's six fields are unchanged.
- **The fifth evaluator parameter is an implementation-interface detail,
  not a new declaration field:** confirmed — `citation_text` is a
  parameter of `evaluate()`, never a field of
  `EligibleAuthorityDeclaration` (§8, §9 above). AEM-001 itself never
  freezes `evaluate()`'s own parameter list at all (AEM-001 §5 describes
  evaluation's inputs narratively, "the sole evidentiary input... is the
  claimed decision-maker identity," AEM-REQ-014, without enumerating a
  closed parameter list) — so AEMIC-001 adding a fifth, non-evidentiary
  parameter at the implementation-contract level does not contradict any
  AEM-001 requirement, since AEM-001 never claimed to close that
  parameter list itself. This is the correct layering: AEM-001 freezes
  the *evidentiary* inputs (two: identity, declaration); AEMIC-001
  freezes the *implementation* signature (which may, and does, include
  additional non-evidentiary pass-through parameters — `evaluated_at`
  and `evaluator_version` already established this pattern in v1.0,
  before `citation_text` was added).
- **The two-evidentiary-input model remains coherent:** confirmed —
  AEM-REQ-016's "total function over its two inputs" is independently
  re-verified unbroken: `evaluation_result` (the substantive output
  AEM-REQ-016 actually describes) is still purely a function of exactly
  `claimed_identity` and `declaration` (§9, §10 above); `citation_text`
  affects only a different field (`citation_text` itself) of a richer
  output type AEM-001 already names (AEM-REQ-018 already listed
  `citation_text` as one of the outcome's own eight fields, populated
  "only when `evaluation_result == eligible`" — AEMIC-001's repair does
  not add a new *field* to the outcome; it adds a new *channel* for a
  field AEM-001 itself already required to exist).
- **No new authority actor is introduced:** confirmed — no new role,
  principal, or identity concept appears anywhere in the repair.
- **No new authority source is introduced:** confirmed — `citation_text`'s
  source remains exactly `decision_template.schema.json`'s
  `eligible_authority` field (AEMIC-REQ-030, unchanged), the same source
  AEM-001 itself anticipated via PEC-REQ-115's own pre-existing citation
  language.
- **No policy judgment is delegated to the evaluator:** confirmed —
  `evaluate()`'s own citation-handling logic performs only a presence
  check (`is None`), never a policy judgment about the citation's
  content, confirmed at §9/§11 above.
- **No gating semantics are introduced:** confirmed at §17 above.

**Independently verified: zero AEM-001 contradiction.** This is the
single most consequential compatibility question this phase attacks, and
it is independently confirmed sound on every sub-point — not merely
because AEMIC-001's own text asserts it, but because each individual
AEM-REQ this phase checked against (007, 014, 016, 018) is independently
confirmed unbroken by direct comparison, not by trusting AEMIC-001's own
self-certification (§20 below evaluates that self-certification's
overall reliability separately, and finds it now correctly resolved for
BF-147F-1 specifically but still overclaiming completeness given
BF-147F.1-1).

---

## 19. Phase 147D Architecture Compatibility

- **Did Phase 147D already imply a citation input but fail to name it?**
  Independently checked — Phase 147D §6.7's own illustrative sequence
  (`evaluate(claimed_identity, declaration)`, two parameters, pre-dating
  even AEMIC-001 v1.0's own four-parameter closure) never named
  `citation_text` at all, confirming Phase 147E.1's own root-cause
  account (§3 of that report: "a 147D-influenced design simplification...
  which itself never named a `citation_text` parameter at all"). This
  independently confirms the repair fills a gap Phase 147D's own
  architecture left open, not one it affirmatively closed differently.
- **Does the five-parameter evaluator fit the designed component
  boundaries?** Yes — `citation_text` is handled entirely within
  `pcae.authority_evaluation.evaluation`, the exact module Phase 147D
  §6.2 already assigns evaluation logic to; no new module or component
  boundary is crossed.
- **Does the repair change module ownership?** No — confirmed at §8 (no
  requirement outside §5/§9/§13.1/§14/§15/§20/§22/§23 differs).
- **Does the repair change Registry responsibilities?** No — the
  Registry never sees `citation_text` (§9, §11 above); Phase 147D §6.4's
  own Registry architecture is entirely untouched.
- **Does the repair change persistence requirements?** No — §12's
  filesystem persistence contract (deferred, AEMIC-REQ-052-063) does not
  reference `citation_text` at all; unaffected.
- **Does the repair change integration sequencing?** No — AEMIC-REQ-084's
  8-step sequence is byte-identical to v1.0 (confirmed at §8's diff
  table, this requirement is not among the touched ones).
- **Is any part of Phase 147D now stale or contradictory?** Independently
  identified: Phase 147D §6.7's own illustrative sequence diagram (line
  598, `evaluate(claimed_identity, declaration)`) is now stale relative
  to the actual five-parameter signature — but Phase 147D is explicitly
  non-authoritative design evidence (§0 of that report, restated
  throughout AEMIC-001 and this phase's own reading discipline, §3
  above), so this is **documentation drift, not implementation-contract
  invalidity** (classified separately per §19's own instruction). No
  action is required or authorized on Phase 147D's own text by this
  phase (out of this phase's No-Go Boundary).

**Independently confirmed: this repair is fully compatible with Phase
147D's architecture, correctly classified as filling a disclosed gap
rather than reversing a design choice, with the sole consequence being
ordinary, expected documentation drift in a non-authoritative
predecessor report — not a defect.**

---

## 20. Registry Boundary Re-Verification — Independent Discovery: BF-147F.1-1

This section is where this phase's own independent attack surfaces a
new, distinct Blocking defect, unrelated to BF-147F-1.

**Confirmed unchanged and sound (restating §9/§11 above from the
Registry's own angle):** `evaluate()` does not obtain `citation_text`
from the Registry (it obtains it from its own fifth parameter, supplied
by the caller); the Registry's `resolve()` signature and return shape
(AEMIC-REQ-042) are unchanged by this repair; Registry-unavailability
behavior (AEMIC-REQ-047-049) is unaffected; duplicate handling
(AEMIC-REQ-045-046) is unaffected; malformed-record behavior
(AEMIC-REQ-048, AEMIC-REQ-058) is unaffected; read-only purity
(AEMIC-REQ-011, AEMIC-REQ-043) is unaffected. **The repair does not
silently expand Registry responsibilities.**

**Independent discovery, made while re-deriving §5's evaluation-inputs
requirement from first principles rather than merely re-reading it as
already-settled:**

`AuthorityEvaluationOutcome` (§6, AEMIC-REQ-021) requires exactly eight
fields, of which `template_ref` and `template_version` are **mandatory
("Yes")**, described as "Verbatim copy of the evaluation's own input."
`evaluate()`'s own frozen five-parameter signature (§14, AEMIC-REQ-072,
unchanged by the 147E.1 repair) is:

```
evaluate(
    claimed_identity: str,
    declaration: EligibleAuthorityDeclaration | None,
    evaluated_at: str,
    evaluator_version: str,
    citation_text: str | None = None,
) -> AuthorityEvaluationOutcome
```

**`template_ref` and `template_version` are not among `evaluate()`'s own
parameters.** The only place these two values could plausibly originate
from `evaluate()`'s own reachable inputs is `declaration.template_ref`/
`declaration.template_version` (both present on
`EligibleAuthorityDeclaration`, per AEMIC-REQ-015's own six-field table)
— a derivation the contract's text never actually states anywhere, but
one that at least has *a* value to draw from when `declaration is not
None` (the `ELIGIBLE`/`INELIGIBLE` branches).

**For the `INDETERMINATE` branch (`declaration is None`, AEMIC-REQ-024),
no value is reachable anywhere in `evaluate()`'s own parameter list, and
`declaration` itself carries no fields to draw from (it is `None`).**
`AuthorityEvaluationOutcome.template_ref`/`.template_version` are
nonetheless still mandatory, unconditional fields for this branch too —
AEMIC-REQ-021's table applies no exception to `INDETERMINATE` for these
two fields the way it correctly does for `declaration_ref` ("Non-`None`
iff a Declaration resolved... `None` iff `indeterminate`") and
`citation_text` ("Conditionally... if and only if `evaluation_result ==
eligible`"). **No well-formed call to `evaluate()` that legitimately
yields `INDETERMINATE` can construct a valid `AuthorityEvaluationOutcome`
under the contract's own text as written**, because two of the outcome's
eight mandatory fields have no data source.

**Independent verification this is genuine, not a reading artifact:**

- Re-read AEMIC-REQ-019's own table (§5) a second time, checking for an
  implicit "source: `declaration.template_ref` if present, otherwise
  [undefined]" note — none exists; the table simply omits
  `template_ref`/`template_version` as parameters entirely.
- Checked AEMIC-REQ-036/037 (§10.1) for an implicit resolution — these
  sections discuss identifier *syntax* and the *canonical identity
  tuple*, not `evaluate()`'s own parameter sourcing; no resolution found.
- Checked Phase 147D's own illustrative sequences (§6.7, §6.8) for a
  wider signature that might reveal the intended design —
  `evaluate(claimed_identity, declaration)` (line 598) is even narrower
  than AEMIC-001's own four-/five-parameter closure and likewise never
  names `template_ref`/`template_version`, confirming this gap predates
  not just the citation-text repair but the entire AEMIC-001 chapter,
  traceable to Phase 147D's own architecture never resolving it either.
- Checked Phase 147F's own independent verification report (§3, its
  reconstructed evaluate() call, line 323 of that report) — it too
  writes `evaluate(claimed_identity, declaration, evaluated_at,
  evaluator_version)`, independently confirming Phase 147F's own
  reconstruction likewise never named `template_ref`/`template_version`
  as inputs, and Phase 147F's own extensive Identity and Versioning
  Verification (§12 of that report) discusses `resolve`'s own two-argument
  signature and adversarial *identifier* inputs at length without ever
  noticing that `evaluate()` itself has no matching parameters for the
  same two values its own output type requires.
- Checked whether `declaration_ref`'s own derivation rule
  (AEMIC-REQ-038: "deterministically derived from the evaluated
  Declaration's own `(template_ref, template_version)` pair") implies
  `template_ref`/`template_version` are always available whenever
  `declaration_ref` is computable — true, but this only covers the
  `ELIGIBLE`/`INELIGIBLE` branches (where `declaration_ref` is itself
  required to be non-`None`); for `INDETERMINATE`, `declaration_ref` is
  correctly permitted to be `None` (no Declaration, nothing to derive
  from) — but `template_ref`/`template_version` are **not** given the
  same conditional exception. This asymmetry, within the very same
  requirement's own table, is itself independent evidence the omission
  is a genuine specification gap rather than an intentional design:
  whoever wrote AEMIC-REQ-021's table correctly reasoned about
  `declaration_ref`'s conditional availability but did not apply the
  same reasoning to `template_ref`/`template_version`, most likely
  because the table's own "Verbatim copy of the evaluation's own input"
  description was written under an implicit, never-stated assumption
  that `template_ref`/`template_version` are direct inputs to
  `evaluate()` — an assumption AEMIC-REQ-019/072's own parameter tables
  do not actually implement.

**This is classified BF-147F.1-1: Blocking**, on the same grounds
BF-147F-1 itself was classified Blocking (§24 of the governing prompt,
restated at §22 below): it is a genuine contract contradiction (a
mandatory output field with a stated "verbatim copy of the evaluation's
own input" sourcing rule, but no such input exists for at least one
required branch), it makes the `INDETERMINATE` branch — one of exactly
three closed `EvaluationResult` values this contract requires
`evaluate()` to support (AEMIC-REQ-024) and the branch AEM-REQ-017
specifically requires evaluation to "deterministically yield" whenever
no Declaration resolves — implementation-impossible as specified, and it
is an unresolved implementation-critical decision no disclosed,
safely-contained limitation anywhere in AEMIC-001 accounts for.

**This defect is entirely independent of BF-147F-1 and this phase's own
repair-verification finding for it.** It was not introduced by the
147E.1 repair (confirmed present in AEMIC-001 v1.0's own four-parameter
signature too, per the reconstruction above and Phase 147F's own
independent, matching reconstruction), and repairing BF-147F.1-1 does
not require reopening or altering anything this phase confirms is
correctly repaired for BF-147F-1 (§5, §9, §13.1, §14.1's own
`citation_text`-specific logic) — it requires adding `template_ref` and
`template_version` (or an equivalent single combined parameter) as
additional, direct `evaluate()` inputs, a change orthogonal to
`citation_text`'s own channel.

---

## 21. Deferred Integration Boundary

Independently re-verified, restating and extending §17/§19's own
findings: the fifth parameter (`citation_text`) does not smuggle
downstream integration into the standalone core. Confirmed, by direct
re-reading of AEMIC-REQ-083 (unchanged, per §8's diff) that the first
implementation still does not: widen `Session`/`PublicationReadinessPackage`;
add any authority field to any IWC-001-owned type; modify
PEC-001/`coordinator.py`/`record.py`; populate `authority_basis_claimed`;
modify any schema; modify verification/inspection; gate anything; or
change Interactive Workflow/CLI behavior. `citation_text`'s own future
caller (a Decision Template authoring/lookup workflow, AEMIC-REQ-032,
unchanged) remains exactly as undefined and exactly as deferred as it
was in v1.0 — this repair changes only *which parameter of `evaluate()`*
that future caller uses, not *whether* a future caller and mechanism
must still be built (§9 above, independently re-confirmed).

**FA-147D-1 remains deferred and explicit**, confirmed unchanged
(AEMIC-REQ-083-085 are not among the touched requirements per §8).

**BF-147F.1-1's own consequence for this boundary:** independently
noted that BF-147F.1-1 does not widen or narrow this boundary either —
it is a defect entirely internal to `pcae.authority_evaluation`'s own
package (how `evaluate()` sources two of its own output's mandatory
fields), with no bearing on any IWC-001/PEC-001/CHGR-001 integration
question. Repairing it requires no change to §17's own text.

---

## 22. Findings Reassessment and New Findings

### 22.1 BF-147F-1

**Fully repaired.** Independently confirmed at §5 (reproduction), §6
(minimum-repair reconstruction, independently matching the selected
repair), §7 (candidate reassessment, independently reaching the same
selection), §8 (exact diff verification), §9–§10 (the repaired
signature and invariant, independently attacked and found sound for the
citation-plumbing question specifically), §17 (security properties,
unweakened). **Not** displaced into another contradiction and **not**
partially repaired — it is completely repaired, on its own narrow terms.
(BF-147F.1-1, discovered independently at §20, is a distinct defect the
147E.1 repair was never scoped to address and does not purport to
address.)

### 22.2 F-147C-1

Independently re-confirmed present and correctly disposed: the dormant
`decision_template.schema.json` `eligible_authority` field remains the
sole citation-text source (AEMIC-REQ-030, unchanged), reconciled at the
textual-source level (confirmed unmodified since Phase 143E, via the
schema file's own unchanged content, cross-checked against Phase 147F's
own §4 confirmation and independently re-confirmed by this phase's own
`grep` of the schema file). Phase 147F's own qualification ("reconciled...
but not correctly specified how it reaches the outcome object") is now
independently confirmed **resolved**: the plumbing gap Phase 147F
identified as reopening F-147C-1 is exactly BF-147F-1, and BF-147F-1 is
repaired (§22.1). F-147C-1 is accordingly **fully reconciled** as of
this phase, both at the textual-source level and at the plumbing level.

### 22.3 F-147C-2

Independently re-confirmed via direct section-header inspection of
`INTERACTIVE_WORKFLOW_CONTRACT.md`: §6 is "Human Responsibility
Contract," §11 is "State Contract" — unchanged. Remains an AEM-001-level
cosmetic citation-precision defect, outside AEMIC-001's own scope and
this phase's own No-Go Boundary. **Unaffected; remains open,
Non-Blocking**, consistent with every predecessor phase's own
disposition.

### 22.4 FA-147D-1

Independently re-confirmed as a real, disclosed, unclosed dependency
(§21 above) — carried forward as AEMIC-REQ-083-085, byte-identical to
v1.0. **Unaffected; remains open by design**, not a defect.

### 22.5 FA-147D-2

Independently re-verified fully closed via direct textual attack: the
`None`/`AuthorityRegistryUnavailableError`/`AuthorityRegistryCorruptError`
three-way split (§11.3, §13.2) is unaffected by this repair and remains
deterministic, testable, and exhaustive of "the Registry was consulted"
outcomes. **Fully closed, unaffected by this repair.**

### 22.6 FA-147D-3

Independently re-confirmed as a real, disclosed, non-mechanically-closed
limitation (AEMIC-REQ-034, unaffected by this repair per §8's diff).
**Retained as a named limitation; unaffected by this repair**, correctly
distinguished from BF-147F-1: FA-147D-3 concerns whether the *text* and
the `eligible_identities` *set* agree with each other (a consistency
question); BF-147F-1 concerned whether the *text* could reach the
outcome object at all (a plumbing question). Repairing one did not
repair the other, confirmed independently — neither AEMIC-REQ-034's own
text nor its disposition changed across the repair.

### 22.7 F-147F-2

Unicode normalization gap in `AEMIC-REQ-036`'s exact-`str`-equality
identity/version matching. Independently re-confirmed unaffected by this
repair (AEMIC-REQ-036 is not among the touched requirements per §8) and
unrelated in substance to `citation_text`. **Unaffected; remains open,
Non-Blocking.**

### 22.8 F-147F-3

`_FORBIDDEN_IMPORT_ROOTS` (in `tests/test_phase_144c_publication_coordinator.py`)
still does not name `pcae.authority_evaluation` — independently
re-confirmed via direct grep of that test file, unchanged since Phase
147F's own confirmation. **Unaffected; remains open, Non-Blocking** — a
future implementation phase's own concern, as before.

### 22.9 New findings, this phase

| # | Finding | Classification |
|---|---|---|
| **BF-147F.1-1** | `AuthorityEvaluationOutcome.template_ref`/`.template_version` (AEMIC-REQ-021, mandatory, unconditional) have "Verbatim copy of the evaluation's own input" as their stated source, but `evaluate()`'s own frozen signature (AEMIC-REQ-019/072) never accepts `template_ref`/`template_version` as parameters. For the `ELIGIBLE`/`INELIGIBLE` branches a value can be derived from `declaration.template_ref`/`.template_version` (undocumented, but at least available); for the `INDETERMINATE` branch (`declaration is None`), no value is reachable anywhere, making a mandatory field's construction impossible for a branch AEM-REQ-017/AEMIC-REQ-024 require `evaluate()` to support. Pre-dates this repair (confirmed present in the reconstructed v1.0 signature and in Phase 147D's own illustrative sequences); untouched by, and unrelated to, the `citation_text` repair. (§20) | **Blocking** — contract contradiction; impossible implementation (for the `indeterminate` path specifically); unresolved implementation-critical decision |
| F-147F.1-2 | `citation_text=""` (empty string, non-`None`) is not distinguished from a valid citation anywhere in AEMIC-REQ-022/AEMIC-REQ-101's own text — an empty citation passes the if-and-only-if invariant's "non-`None`" check trivially, so it is never rejected by `MissingCitationTextError` or any other mechanism, despite disclosing nothing. Fails in a disclosed, inspectable direction (an obviously-vacuous string), not a fabricated-but-plausible one. (§9, §10, §16) | Non-Blocking, newly disclosed Observation |
| F-147F.1-3 | `MissingCitationTextError`'s own condition (AEMIC-REQ-064) names only `citation_text is None`; a non-`str`, non-`None` value (a type violation) is not explicitly named as a distinct raising condition anywhere in §13.1, unlike `InvalidClaimedIdentityError`'s own explicit "empty or not a `str`" condition. (§10) | Non-Blocking, newly disclosed Observation |
| F-147F.1-4 | `from_payload`'s own deserialization contract (AEMIC-REQ-091/093) states every *mandatory* field must be present and non-`null`, but does not resolve whether this blanket rule applies to *conditionally*-mandatory fields (`citation_text`, `declaration_ref`) in a way that would catch a hand-crafted or corrupted payload asserting `evaluation_result: "eligible"` with `citation_text: null` — an invariant `evaluate()` itself can never produce, but that `from_payload` does not explicitly state it re-validates at the cross-field level. (§16) | Non-Blocking, newly disclosed Observation |
| Direct `AuthorityEvaluationOutcome` construction bypassing `evaluate()` | No binding requirement forbids direct, caller-side construction of a shape-valid but never-actually-evaluated `AuthorityEvaluationOutcome`; narrative language ("the sole specified construction path") is not backed by a normative prohibition. Classified Informational per the governing prompt's own taxonomy, since the type is an ordinary, non-authoritative immutable value object and AEM-001 §10's own "no enforcement surface exists to attack" reasoning applies identically regardless of construction path. (§12) | Informational |

**No finding above collapses two materially different concerns into
one.** BF-147F.1-1 is not a restatement of BF-147F-1, F-147C-1,
FA-147D-3, or any other prior finding — it is a distinct defect this
phase's own independent attack on §5/§6/§14 discovered by re-deriving
the evaluation-inputs requirement from first principles rather than
accepting the repaired signature's own completeness as already settled.

---

## 23. Contract Completeness

Attacked, per the governing prompt's own §21 instruction, whether an
implementer can now build the standalone AEM core without deciding any
unresolved material behavior:

| Area | Complete? |
|---|---|
| Citation input (the repair's own subject) | **Yes** — fully resolved (§9, §10, §22.1) |
| Eligible outcome construction | **Yes**, for the citation dimension; **Informational-only** gap for direct-construction bypass (§12, §22.9) |
| Missing citation | **Yes** — `MissingCitationTextError`, fully specified (§13) |
| Non-eligible citation input | **Yes** — disregarded, deterministic (§9, §10) |
| Failure precedence | **Yes**, with one documentation-only ordering gap not rising to a finding (§14) |
| Deterministic evaluation | **Yes** (§15) |
| Error classification | **Yes**, with two narrow, Non-Blocking gaps (F-147F.1-2, F-147F.1-3) |
| Serialization | **Yes**, with one narrow, Non-Blocking gap (F-147F.1-4) |
| Direct construction | **Informational**, not implementation-blocking (§12) |
| Provenance limitations | **Yes**, explicitly disclosed and bounded (§11) |
| **`template_ref`/`template_version` sourcing for `evaluate()`'s own mandatory output fields** | **No — BF-147F.1-1 (§20)** |

**An implementer cannot, as of AEMIC-001 v1.1's current text, build
`evaluate()` such that it correctly and completely produces a valid
`AuthorityEvaluationOutcome` for the `indeterminate` branch**, because
two of that branch's own mandatory output fields have no specified data
source. Every other material behavior this contract's own governing
sections (§2–§18) ask to be resolved unambiguously has, independently
verified, actually been resolved — **except this one**, which survives
independent re-verification as a genuine, implementation-critical,
Blocking gap.

---

## 24. Testability Matrix (Independent)

Independent test matrix, produced before comparing against AEMIC-001's
own §22 matrix, per the governing prompt's own required 20-item minimum:

1. eligible + valid citation — **testable**, sound.
2. eligible + missing citation — **testable**, `MissingCitationTextError`.
3. eligible + empty citation — **testable, but the contract does not
   specify a distinct expected result** (F-147F.1-2) — the test would
   pass trivially (empty string accepted) but does not exercise any
   distinguishing behavior the contract requires.
4. eligible + whitespace citation — **testable**, sound (no
   normalization, disclosed verbatim).
5. eligible + non-string citation — **not cleanly testable as a named
   exception condition** (F-147F.1-3) — would likely raise a `TypeError`
   at a language boundary rather than a named `AuthorityEvaluationError`
   subclass, an untested and unspecified condition.
6. non-eligible + absent citation — **testable**, sound.
7. non-eligible + supplied citation — **testable**, sound
   (`citation_text=None` on the outcome regardless).
8. invalid request + supplied citation — **testable**, sound
   (`InvalidClaimedIdentityError`/`InvalidTemplateReferenceError` fire
   independent of `citation_text`).
9. invalid declaration + supplied citation — **testable**, sound
   (`MalformedDeclarationError` fires at Declaration construction,
   upstream).
10. Registry unavailable + supplied citation — **testable**, sound (the
    Registry failure occurs before `evaluate()` is ever reached).
11. duplicate declaration + supplied citation — **testable**, sound
    (same reasoning, occurs in `resolve()`).
12. unsupported version + supplied citation — **testable in the sense
    that `resolve()` correctly fails to find a Declaration for an
    unrecognized version tuple**, but see item 20 below for the
    `evaluate()`-level consequence.
13. exact citation preservation — **testable**, sound (byte-for-byte
    verbatim copy, AEMIC-REQ-031).
14. Unicode preservation — **testable**, sound.
15. deterministic repeated evaluation — **testable**, sound
    (AEMIC-REQ-075).
16. differing citation produces differing outcome — **testable**, sound.
17. direct fabricated outcome construction — **testable as a
    demonstration that the contract does not forbid it** (§12,
    Informational, not a contract violation to test against, since no
    prohibition exists to falsify).
18. serialization round trip — **testable**, sound, with the
    cross-field-validation ambiguity noted at item 19 below.
19. disclosure-only naming — **testable**, sound (§17 above).
20. **forbidden downstream imports** — **testable**, sound (AEMIC-REQ-010,
    unaffected by this repair).

**Comparison against AEMIC-001's own §22 matrix:** every item above has
a corresponding row, confirmed. **One test that cannot be meaningfully
completed as specified, independently discovered by this phase and not
present in AEMIC-001's own matrix at all:** a positive test constructing
a valid `INDETERMINATE` `AuthorityEvaluationOutcome` via a well-formed
call to `evaluate()` where the outcome's own `template_ref`/
`template_version` fields are populated from a value `evaluate()`'s own
signature does not accept — **this table test cannot be written as
specified**, mirroring exactly the shape of the gap Phase 147F's own §20
identified for BF-147F-1's `eligible`-row incompleteness, now recurring
for BF-147F.1-1's `indeterminate`-row incompleteness. AEMIC-001's own
§22 matrix row for `AEMIC-REQ-072-077, AEMIC-REQ-101` requires a "Table
test over `(claimed_identity, declaration, citation_text)` → expected
outcome for all three results" — this table test, as literally written
in the contract's own matrix, does not even list `template_ref`/
`template_version` as one of the varied inputs, silently assuming they
are available through some channel the matrix itself never names.

---

## 25. No-Go Confirmation

This phase did not modify `src/pcae/**`; did not implement
`pcae.authority_evaluation`; did not create any production model or
Registry; did not modify any schema file; did not modify AEM-001,
AEMIC-001, IWC-001, IWPC-001, PEC-001, CHGR-001, TAMC-001, TAMPC-001, or
GAC-001; did not modify Session, readiness packages, or the Publication
Coordinator; did not construct CHGR records; did not add publication
gating; did not change verification or inspection code; did not enable
execution capability; did not change runtime, policy, or strategic
lineage. `git status --short` immediately before this report was written
showed a clean tree; the only file this phase creates is this report,
plus ordinary governance bookkeeping (task/phase lifecycle files,
`PROJECT_STATUS.md`, `.pcae/phase-completion-*`) at phase close. No
verification-only test was added — direct source and contract textual
analysis, plus a single fast_green regression run (§27), was sufficient
to independently verify BF-147F-1's repair and to discover BF-147F.1-1,
consistent with the governing prompt's own §23 allowance.

---

## 26. Overall Verdict

**REPAIR NOT VERIFIED.**

BF-147F-1, the specific finding Phase 147E.1 was authorized to repair,
**is fully and correctly repaired** — independently re-derived,
re-attacked, and confirmed sound on every axis this phase checked: the
`citation_text` if-and-only-if invariant is now satisfiable and satisfied
via `evaluate()`'s own sole specified construction path for all three
`EvaluationResult` values; `MissingCitationTextError` is coherent and
correctly scoped; `AEM-001` compatibility is fully preserved (the closed
Declaration shape and the two-evidentiary-input purity guarantee are both
untouched); disclosure-only security properties are unweakened; and no
other requirement outside the disclosed §5/§9/§13.1/§14/§15/§20/§22/§23
scope was altered.

**However, this phase's own independent reconstruction — the specific
discipline this phase was authorized to apply, rather than accepting
Phase 147E.1's account — discovered BF-147F.1-1: `AuthorityEvaluationOutcome.template_ref`/
`.template_version` are mandatory output fields with no corresponding
input in `evaluate()`'s own frozen signature for the `indeterminate`
branch.** This defect predates the repair, is untouched by it, and was
not caught by Phase 147C, Phase 147D, or Phase 147F — but its presence
means AEMIC-001 v1.1, taken as a whole, does not yet satisfy the
verification criteria the governing prompt requires for either VERIFIED
outcome: "complete and deterministic public types" and "implementation
completeness" both fail, specifically and only, on account of
BF-147F.1-1 (a defect this phase discovered) — exactly as they
previously failed, specifically and only, on account of BF-147F-1 before
this repair (a defect this phase confirms is now resolved).

Every other independently-checked property holds: the repaired evaluator
API is complete and unambiguous for the `citation_text` channel;
disclosure-only semantics are preserved; the Registry boundary is
unaffected; the deferred-integration boundary is unaffected; every
carried-forward finding (F-147C-1 — now fully reconciled; F-147C-2,
FA-147D-1, FA-147D-3 — unaffected and correctly disposed; F-147F-2,
F-147F-3 — unaffected and correctly disposed) is independently confirmed;
and three additional narrow, Non-Blocking observations were newly
disclosed (F-147F.1-2, F-147F.1-3, F-147F.1-4), none of which rises to
Blocking.

Per the governing prompt's own §28 criteria, a successful verification
requires, among other things, "complete and deterministic public types"
and "implementation completeness" — both remain unmet, on account of
BF-147F.1-1 alone. Repairing BF-147F.1-1 (most directly, by adding
`template_ref: str` and `template_version: str` as two additional direct
parameters to `evaluate()`, alongside a corresponding correction to
AEMIC-REQ-019/020/072's parameter table and signature block, and to
AEMIC-REQ-021's "Verbatim copy of the evaluation's own input" description
so it correctly names the new parameters as the source) would, on this
phase's own independent assessment, very likely restore VERIFIED WITH
NON-BLOCKING FINDINGS status on a subsequent verification pass, since no
other structural defect beyond the three narrow, already-Non-Blocking
observations above was found — but that repair is AEMIC-001's own
affair, not this phase's (§25, No-Go Boundary; repair is explicitly not
authorized here).

---

## 27. Validation

Re-run at the close of this phase, from `~/repos/pcae-harness`:

- `pcae check`: passed.
- `pcae health`: healthy; required PCAE files all present; policy
  validation valid; git status clean.
- `pcae doctor task-memory`: clean, no inconsistencies detected.
- `pcae runtime inspect`: Runtime status `not_implemented`, Runtime state
  `Observed`, Execution capability `unavailable`, Maximum plugin
  capability `observe`, Registry status `empty`, Plugin count `0` —
  identical to §4's start-of-phase reading.
- `pcae push check`: clean (`nothing_to_push`); branch `main`, working
  tree clean, health healthy, check passed, task memory clean.
- `python -m pytest -m fast_green -n auto -q`: **4391 passed**, 0 failed,
  105 warnings (pre-existing, unrelated dataclass-collection warnings),
  in 103.13s. No regression, consistent with this phase touching no
  source file — identical pass count to Phase 147F's own baseline
  (4391/4391).

No environmental condition prevented completion of any command above; no
partial result was recorded.

**Confirmed**: no production source changed; no frozen contract changed
(AEM-001, AEMIC-001, IWC-001, IWPC-001, PEC-001, CHGR-001, TAMC-001,
TAMPC-001, GAC-001 all byte-for-byte unmodified — `git status --short`
shows no change to any file under `docs/contracts/`); no schema changed;
runtime remains Observed / observe / unavailable; Registry remains empty;
plugin count remains zero; repository is clean and synchronized at
completion (`git status --short` empty; `git rev-list --count
origin/main..HEAD` and `..origin/main` both `0` at phase start, to be
re-confirmed identically after this report and ordinary governance
bookkeeping are committed).

---

## 28. Repair-Verification Matrix

| Requirement(s) | Original v1.0 defect | v1.1 repair | Independent verification result | Adversarial test | Finding, if any |
|---|---|---|---|---|---|
| AEMIC-REQ-019/020 (§5) | Closed 4-parameter list, no `citation_text` channel | Widened to 5 parameters, `citation_text: str \| None = None` | **Confirmed correct** — non-evidentiary, matches existing precedent (§6, §9, §18) | Attempted well-formed `eligible` call under old 4-param closure: impossible (§5); under new 5-param signature: succeeds (§9) | — |
| AEMIC-REQ-021/022 (§6/§6.1) | Invariant sound but unsatisfiable via sole construction path | Unchanged text; now satisfiable given §14.1's enforcement | **Confirmed correct** for the citation dimension (§9, §10); **template_ref/template_version dimension independently found still broken** (§20) | Table test for all three `EvaluationResult` values: succeeds for `eligible`/`ineligible` citation dimension; **cannot be completed for `indeterminate`'s template_ref/template_version** | **BF-147F.1-1** |
| AEMIC-REQ-031 (§9) | Self-contradictory: "Declarations SHALL copy..." while confirming no such field/parameter exists | Rewritten: "`evaluate` SHALL copy `citation_text` verbatim" | **Confirmed correct** — grammatical subject now matches an actual data channel (§8, §9) | Re-read for internal contradiction: none found | — |
| AEMIC-REQ-032/033 (§9) | Disclosed limitation (no `DecisionTemplate` artifact) | Light edit only ("indirectly" → "directly as evaluate's own fifth parameter") | **Confirmed correct**, substance unchanged, limitation still real and still safely disclosed (§11) | Attempted to construct a scenario where the limitation is hidden rather than disclosed: none found | — |
| AEMIC-REQ-064 (§13.1) | Missing `MissingCitationTextError` | New row added | **Confirmed correct** — condition, retryability, domain classification all sound (§13) | Confusion with declaration-absence or Registry-unavailability: none found | — |
| AEMIC-REQ-065 (§13.1) | Silent on non-eligible-path citation handling | New sentence: disregarded, not raised, not fabricated | **Confirmed correct** — deterministic, does not narrow AEM-REQ-024 (§10) | Supplied non-`None` citation on `ineligible`/`indeterminate`: outcome correctly carries `citation_text=None` | — |
| AEMIC-REQ-072 (§14) | 4-parameter signature block | 5-parameter signature block | **Confirmed correct**, matches §5's table exactly (§8) | — | — |
| AEMIC-REQ-074/075/077 (§14) | Referenced "four," 4-tuple determinism, no missing-citation classification | "Five," 5-tuple determinism, missing-citation classified as malformed input | **Confirmed correct** on all three points (§8, §14, §15) | Determinism check across repeated calls: sound (§15) | — |
| AEMIC-REQ-101 (§14.1, new) | N/A (did not exist) | Four-step construction-time enforcement algorithm | **Confirmed correct and complete** for the citation dimension (§9, §10, §14) | Full branch table (§10) independently verified against every combination named in the governing prompt | — |
| AEMIC-REQ-102 (§15, new) | N/A (did not exist) | Security-disposition statement: citation fabrication risk unchanged, not worsened | **Confirmed accurate** (§11, §17) | Attempted to show the repair worsens fabrication risk: it does not — the pre-repair alternative (bypass `evaluate()` entirely) was strictly worse (§5, §11) | — |
| AEMIC-REQ-095 (§20) | Self-certification "internally coherent" falsified by BF-147F-1 | Corrected to record and resolve the falsification | **Confirmed accurate for BF-147F-1**; **the surrounding self-certification's broader "complete enough to implement" and "testable" claims are independently found still overclaiming, given BF-147F.1-1** (§18, §23) | Full independent contract-completeness attack (§23) | **BF-147F.1-1** |
| §22 Requirement/Test Matrix | Incomplete for the `eligible` row | Three rows updated | **Confirmed updated correctly for citation-plumbing**; **independently found the matrix's own table test for `AEMIC-REQ-072-077/101` never lists `template_ref`/`template_version` as varied inputs at all**, silently assuming their availability | Independent test-matrix reconstruction (§24) | **BF-147F.1-1** |
| §23 Finding Disposition | Silent on the new defect (BF-147F-1 undiscovered at v1.0 freeze time) | BF-147F-1 marked Repaired; F-147F-2/F-147F-3 marked unaffected | **Confirmed accurate** for all three rows (§22) | Independent re-derivation of each finding's own disposition from primary sources, not accepted on say-so | — |

---

## 29. Recommended Next Phase

Per the governing prompt's own instruction ("If the verdict is REPAIR
NOT VERIFIED, recommend instead: 147E.2 — Authority Evaluation Model
Implementation Contract Second Repair. Name the exact Blocking finding
and restrict the repair to that defect"):

**147E.2 — Authority Evaluation Model Implementation Contract Second
Repair.**

**Exact Blocking finding to repair:** BF-147F.1-1 (§20, §22.9) —
`AuthorityEvaluationOutcome.template_ref`/`.template_version` are
mandatory output fields with no corresponding parameter in `evaluate()`'s
own frozen five-parameter signature, making the `indeterminate` branch's
own outcome construction impossible as specified.

**Scope recommendation (non-binding, for that future phase's own
consideration):** the minimum repair this phase's own independent
reconstruction (§6-equivalent reasoning, applied to this new defect)
suggests is adding `template_ref: str` and `template_version: str` as
two additional direct parameters to `evaluate()` (bringing the total to
seven), with a corresponding correction to AEMIC-REQ-019/020's parameter
table, AEMIC-REQ-072's signature block, AEMIC-REQ-021's field-sourcing
description (removing the now-inaccurate implicit assumption that
`template_ref`/`template_version` are always derivable from
`declaration`), and AEMIC-REQ-075's determinism tuple (which would need
to include the two new parameters). This recommendation is scoping
guidance only, not a pre-authorization of any specific repair approach —
that choice belongs to the repair phase itself, exactly as Phase 147F's
own scope recommendation for BF-147F-1 was advisory only and Phase
147E.1 was free to (and did) select a different specific mechanism than
either of Phase 147F's two suggested options.

A future 147E.2 should **not** re-open, re-litigate, or re-derive
BF-147F-1's own repair (§5, §9, §13.1, §14.1's `citation_text`-specific
logic), which this phase independently confirms is complete and correct
(§22.1) — restating the governing prompt's own discipline of restricting
a repair phase to the named Blocking finding only.

The three narrow, Non-Blocking observations newly disclosed by this
phase (F-147F.1-2, F-147F.1-3, F-147F.1-4, §22.9) are **not** Blocking
and do not require repair before a future 147F.2 re-verification pass,
though a future 147E.2 MAY address them opportunistically if doing so
does not expand that phase's own scope beyond BF-147F.1-1 plus
incidental, clearly-scoped cleanup — a judgment call for that future
phase, not pre-authorized here.

This recommendation is **not an authorization.**

Separately and not folded into Chapter 147: a standalone Phase 107A
execution-capability gap re-derivation, roadmap-tracking reconciliation,
and GLP-PILOT-C6 Stage 3 resumption all remain open, disclosed, and
unscheduled — unaffected by this phase.

---

**End of Phase 147F.1 independent re-verification report.**
